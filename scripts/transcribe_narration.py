#!/usr/bin/env python3
"""Word-level transcription with faster-whisper, providing timestamps
for forced alignment.

Usage:
    python transcribe_narration.py narration_16k.wav -o narration_words.json \
        --model small --lang zh
    python transcribe_narration.py .super-video/my-task/audio/narration_16k.wav \
        --workdir .super-video/my-task

Outputs:
    narration_words.json           word-level [{id,text,start,end}, ...]
    narration_words_segments.json  segment-level [{start,end,text}, ...]

    With --workdir the default output becomes
    <workdir>/audio/narration_words.json.

Dependency: pip install faster-whisper
Note: for Chinese always pass --lang zh; never use .en models
(they translate instead of transcribing).
Note: whisper's Chinese default often emits Traditional characters,
which makes build_timeline.py report a falsely low similarity
(~0.6 even on a perfect match). The default --initial-prompt biases
decoding toward Simplified; keep it unless you really want Traditional.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from task_paths import resolve_output


def transcribe_audio(
    model: object, audio_path: str, lang: str, initial_prompt: str = ""
) -> tuple[list[dict], list[dict], str]:
    """Run word-level transcription and collect words and segments.

    Args:
        model: A ready-to-use faster-whisper WhisperModel instance.
        audio_path: Path to the narration audio file.
        lang: Language code for recognition (e.g. ``zh``).
        initial_prompt: Optional prompt biasing decoding. For Chinese,
            pass a Simplified-Chinese sentence to make the model emit
            Simplified characters (its default is often Traditional,
            which badly lowers the downstream alignment similarity).

    Returns:
        A tuple ``(words, segments, language)`` where ``words`` holds
        word-level entries with ``w{N}`` ids, ``segments`` holds
        segment-level entries, and ``language`` is the detected language.
    """
    kwargs = dict(language=lang, word_timestamps=True,
                  vad_filter=True, beam_size=5)
    if initial_prompt:
        kwargs["initial_prompt"] = initial_prompt
    raw_segments, info = model.transcribe(audio_path, **kwargs)

    words: list[dict] = []
    segments: list[dict] = []
    for segment in raw_segments:
        segments.append({
            "start": round(segment.start, 3),
            "end": round(segment.end, 3),
            "text": segment.text.strip(),
        })
        for idx, word in enumerate(
            (word for word in (segment.words or []) if word.word.strip()),
            start=len(words),
        ):
            words.append({
                "id": f"w{idx}",
                "text": word.word.strip(),
                "start": round(word.start, 3),
                "end": round(word.end, 3),
            })
    return words, segments, info.language


def write_word_files(output: str, words: list[dict], segments: list[dict]) -> None:
    """Write word-level and segment-level results as JSON files.

    Args:
        output: Path of the word-level output JSON file.
        words: Word-level entries to write.
        segments: Segment-level entries to write next to the word file
            with a ``_segments`` suffix before the extension.
    """
    output_path = Path(output)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(words, f, ensure_ascii=False, indent=2)
    segments_path = output_path.with_name(
        output_path.name.replace(".json", "_segments.json"))
    with segments_path.open("w", encoding="utf-8") as f:
        json.dump(segments, f, ensure_ascii=False, indent=2)


def main() -> int:
    """Parse CLI arguments, run transcription, and write output files."""
    ap = argparse.ArgumentParser(
        description="Word-level transcription with faster-whisper")
    ap.add_argument("audio", help="path to the narration audio file")
    ap.add_argument("--model", default="small",
                    help="tiny/base/small/medium/large-v3")
    ap.add_argument("--lang", default="zh", help="language code, e.g. zh")
    ap.add_argument(
        "--initial-prompt", default="以下是普通话的句子，请用简体中文转写。",
        help="decoding prompt; the Chinese default biases output toward "
             "Simplified characters. Pass empty string to disable.")
    ap.add_argument("--device", default="cpu", help="cpu or cuda")
    ap.add_argument("--compute-type", default="int8", help="compute type")
    ap.add_argument("-o", "--output", default=None,
                    help="output word-level JSON file path (default: "
                         "<workdir>/audio/narration_words.json, or "
                         "./narration_words.json when --workdir is omitted)")
    ap.add_argument("--workdir", default=None,
                    help="Task directory, e.g. .super-video/my-task; when set, "
                         "the default output lands in <workdir>/audio/")
    args = ap.parse_args()

    from faster_whisper import WhisperModel

    model = WhisperModel(args.model, device=args.device,
                         compute_type=args.compute_type)
    words, segments, language = transcribe_audio(
        model, args.audio, args.lang, args.initial_prompt)
    output_path = resolve_output(args.output, args.workdir, "audio",
                                 "narration_words.json")
    write_word_files(str(output_path), words, segments)

    print(f"OK words={len(words)} segments={len(segments)} lang={language}")
    print(f"written: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
