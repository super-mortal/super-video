#!/usr/bin/env python3
"""Align narration script characters to faster-whisper word-level timestamps.

Why this exists: whole-paragraph synthesis via MiniMax contains no
inter-sentence silence, so true sentence boundaries can only be recovered
from the audio itself. This script aligns the narration script character
sequence to the whisper character sequence with difflib.SequenceMatcher,
takes the timestamps of the equal blocks, and fills the gaps by linear
interpolation to obtain accurate per-word times.

Usage:
    python build_timeline.py script.txt narration_words.json narration.wav \
        -o timeline.json

Inputs:
    script.txt            narration script (one sentence per line)
    narration_words.json  faster-whisper word-level output [{text,start,end}, ...]
    narration.wav         44.1kHz synthesized narration audio (its total
                          duration drives the tail alignment)

Output:
    timeline.json  { total, audio, scenes:[{id,text,start,end,words:[[tok,s,e],...]}] }

build_composition.py later reads timeline.json to build index.html.
"""
from __future__ import annotations

import argparse
import difflib
import json
import shutil
import subprocess
import sys
from pathlib import Path

from text_units import CJK_RE, LATIN_RE, tokenize


def is_content_char(char: str) -> bool:
    """Return True if the character counts as content (CJK or Latin)."""
    return bool(CJK_RE.match(char)) or bool(LATIN_RE.match(char))


def normalize_chars(text: str) -> list[str]:
    """Lowercase the text and keep only its content characters."""
    return [char.lower() for char in text if is_content_char(char)]


def probe_duration(path: str) -> float:
    """Return the media duration in seconds via ffprobe."""
    ffprobe = shutil.which("ffprobe") or "ffprobe"
    probe_result = subprocess.run(
        [ffprobe, "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path],
        capture_output=True, text=True)
    return float(probe_result.stdout.strip())


def build_whisper_chars(words: list[dict]) -> list[tuple[str, float, float]]:
    """Spread every whisper word evenly across its own characters."""
    whisper_chars = []
    for word in words:
        chars = normalize_chars(word["text"])
        if not chars:
            continue
        word_duration = word["end"] - word["start"]
        for k, char in enumerate(chars):
            whisper_chars.append(
                (char,
                 word["start"] + word_duration * k / len(chars),
                 word["start"] + word_duration * (k + 1) / len(chars)))
    return whisper_chars


def align_char_times(
    script_lines: list[str],
    whisper_chars: list[tuple[str, float, float]],
    audio_duration: float,
) -> tuple[list, float]:
    """Align script chars to whisper chars and interpolate unmatched gaps.

    Returns the per-character (start, end) list plus the alignment similarity.
    """
    script_seq = [char
                  for line in script_lines
                  for char in normalize_chars(line)]
    whisper_seq = [char for char, _, _ in whisper_chars]

    matcher = difflib.SequenceMatcher(None, script_seq, whisper_seq,
                                      autojunk=False)
    char_time = [None] * len(script_seq)
    for tag, i1, i2, j1, _ in matcher.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                char_time[i1 + k] = (whisper_chars[j1 + k][1],
                                     whisper_chars[j1 + k][2])

    # Fill unmatched chars by linear interpolation between matched neighbours
    char_count = len(char_time)
    if char_count and char_time[0] is None:
        first = next((entry for entry in char_time if entry), (0.0, 0.0))
        for i in range(char_count):
            if char_time[i] is not None:
                break
            char_time[i] = (0.0, first[0])
    i = 0
    while i < char_count:
        if char_time[i] is None:
            j = i
            while j < char_count and char_time[j] is None:
                j += 1
            left = char_time[i - 1] if i > 0 else (0.0, 0.0)
            right = (char_time[j] if j < char_count
                     else (audio_duration, audio_duration))
            gap_count = j - i
            for k in range(gap_count):
                time_sec = (left[1]
                            + (right[0] - left[1]) * (k + 1) / (gap_count + 1))
                char_time[i + k] = (time_sec, time_sec)
            i = j
        else:
            i += 1

    return char_time, matcher.ratio()


def assign_token_times(script_lines: list[str], char_time: list) -> list[dict]:
    """Cut each line into caption units and stamp the aligned times on them."""
    scenes = []
    cursor = 0
    for line_index, line in enumerate(script_lines):
        tokens = tokenize(line)
        token_times, last_t = [], 0.0
        for token in tokens:
            k = len(normalize_chars(token))
            matched = [entry for entry in char_time[cursor:cursor + k] if entry]
            cursor += k
            if matched:
                start_sec = min(entry[0] for entry in matched)
                end_sec = max(entry[1] for entry in matched)
            else:
                start_sec = end_sec = last_t
            start_sec = max(start_sec, last_t)
            end_sec = max(end_sec, start_sec + 0.05)
            token_times.append([token, round(start_sec, 3), round(end_sec, 3)])
            last_t = end_sec
        scenes.append({"id": f"s{line_index}", "text": line,
                       "sent_start": token_times[0][1],
                       "sent_end": token_times[-1][2], "words": token_times})
    return scenes


def apply_scene_cuts(scenes: list[dict], audio_duration: float,
                     lead: float, tail: float) -> None:
    """Derive scene start/end cut points, in place.

    Each scene starts `lead` seconds before its first word; the last scene
    runs `tail` seconds past the end of the audio.
    """
    cut_points = [0.0]
    for scene in scenes[1:]:
        cut_points.append(round(max(0.0, scene["sent_start"] - lead), 3))
    total = round(audio_duration + tail, 3)
    for idx, scene in enumerate(scenes):
        scene["start"] = cut_points[idx]
        scene["end"] = (round(cut_points[idx + 1], 3)
                        if idx + 1 < len(cut_points) else total)


def print_scene_progress(scenes: list[dict]) -> None:
    """Print one alignment progress line per scene."""
    for line_index, scene in enumerate(scenes):
        token_times = scene["words"]
        print(f"s{line_index:2d} {token_times[0][1]:6.2f}"
              f"-{token_times[-1][2]:6.2f}"
              f"  toks={len(token_times):2d}  {scene['text'][:26]}")


def build_timeline(script_lines: list[str], words: list[dict],
                   audio_duration: float, lead: float, tail: float) -> dict:
    """Align, assign word times, cut scenes, and return the timeline dict."""
    whisper_chars = build_whisper_chars(words)
    char_time, similarity = align_char_times(script_lines, whisper_chars,
                                             audio_duration)

    print(f"align: script_chars={len(char_time)} "
          f"whisper_chars={len(whisper_chars)} "
          f"audio={audio_duration:.2f}s similarity={similarity:.3f}")

    scenes = assign_token_times(script_lines, char_time)
    apply_scene_cuts(scenes, audio_duration, lead, tail)
    print_scene_progress(scenes)

    return {
        "total": round(audio_duration + tail, 3),
        "audio": round(audio_duration, 3),
        "scenes": [{"id": scene["id"], "text": scene["text"],
                    "start": scene["start"], "end": scene["end"],
                    "words": scene["words"]} for scene in scenes],
    }


def write_timeline(output_path: str, timeline: dict) -> None:
    """Serialize the timeline dict to a JSON file at output_path."""
    Path(output_path).write_text(
        json.dumps(timeline, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    """Parse CLI args, run the alignment, and write timeline.json."""
    parser = argparse.ArgumentParser(
        description="Force-align narration script chars to whisper word times")
    parser.add_argument("script",
                        help="narration script text file (one sentence per line)")
    parser.add_argument("words",
                        help="faster-whisper word-level JSON [{text,start,end}, ...]")
    parser.add_argument("audio",
                        help="44.1kHz synthesized narration audio (WAV)")
    parser.add_argument("-o", "--output", default="timeline.json",
                        help="output JSON path (default: timeline.json)")
    parser.add_argument("--lead", type=float, default=0.12,
                        help="lead time before scene cuts in seconds (default: 0.12)")
    parser.add_argument("--tail", type=float, default=0.9,
                        help="extra video tail after the audio ends, in seconds "
                             "(default: 0.9)")
    args = parser.parse_args()

    script_lines = [line.strip()
                    for line in
                    Path(args.script).read_text(encoding="utf-8").splitlines()
                    if line.strip()]
    words = json.loads(Path(args.words).read_text(encoding="utf-8"))
    audio_duration = probe_duration(args.audio)

    timeline = build_timeline(script_lines, words, audio_duration,
                              lead=args.lead, tail=args.tail)
    write_timeline(args.output, timeline)

    print(f"\nTOTAL(audio)={audio_duration:.2f}s  video={timeline['total']:.2f}s"
          f"  scenes={len(timeline['scenes'])}")
    print(f"written: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
