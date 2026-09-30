#!/usr/bin/env python3
"""Mux the narration audio (plus optional BGM) into a silent visual video
via FFmpeg post-composition.

Why post-composition is required: the built-in audio track of HyperFrames
gets truncated around 30-32s (see H9), so any video >= 30s must be rendered
silent first, then have its audio merged back with FFmpeg.

Usage:
    python merge_audio.py visual.mp4 narration.wav -o final.mp4
    python merge_audio.py visual.mp4 narration.wav --bgm bgm.wav \
        --bgm-gain -26 -o final.mp4

Mixing rules:
    - The narration audio is authoritative (total audio length == video
      length; the shorter side is padded with anullsrc/apad silence, the
      longer side is trimmed)
    - Optional BGM loops underneath, attenuated via --bgm-gain (dB, negative)
      so it never drowns out the narration audio
    - Output: H.264 + AAC, yuv420p, faststart

Dependencies: ffmpeg / ffprobe (on PATH, or via the FFMPEG/FFPROBE env vars).
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def find_executable(name: str) -> str:
    """Resolve the path of an executable, honoring FFMPEG/FFPROBE-style
    env overrides."""
    env = os.environ.get(name.upper())
    if env and Path(env).exists():
        return env
    return shutil.which(name) or name


def run_ffmpeg(*args: str) -> None:
    """Run ffmpeg with the given arguments, raising CalledProcessError on failure."""
    subprocess.run(
        [find_executable("ffmpeg"), "-y", "-hide_banner", "-loglevel", "error", *args],
        check=True,
    )


def probe_duration(path: str) -> float:
    """Return the media duration in seconds as reported by ffprobe."""
    out = subprocess.run([find_executable("ffprobe"), "-v", "error", "-show_entries",
                          "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True)
    return float(out.stdout.strip())


def main() -> int:
    """Parse CLI arguments and mux the narration audio (and optional BGM)
    into the video."""
    ap = argparse.ArgumentParser(
        description="Mux narration audio (+ optional BGM) into a silent video")
    ap.add_argument("video", help="Silent visual video (mp4)")
    ap.add_argument("narration", help="Narration audio (wav/mp3)")
    ap.add_argument("-o", "--output", default="final.mp4",
                    help="Output video path")
    ap.add_argument("--bgm", default=None, help="Optional background music")
    ap.add_argument("--bgm-gain", type=float, default=-26.0,
                    help="BGM attenuation in dB (default -26, negative)")
    ap.add_argument("--narration-gain", type=float, default=0.0,
                    help="Narration audio gain in dB (default 0)")
    args = ap.parse_args()

    video_duration = probe_duration(args.video)
    narration_duration = probe_duration(args.narration)
    print(f"video={video_duration:.3f}s narration={narration_duration:.3f}s")

    # Align the narration audio to the video length via -filter_complex,
    # optionally mixing in BGM.
    if args.bgm:
        audio_filter = (
            f"[1:a]volume={args.narration_gain}dB,"
            f"apad,atrim=0:{video_duration:.3f}[narr];"
            f"[2:a]volume={args.bgm_gain}dB,"
            f"aloop=loop=-1:size=2e9,atrim=0:{video_duration:.3f}[bgm];"
            f"[narr][bgm]amix=inputs=2:duration=first:dropout_transition=0[aout]"
        )
        cmd = ["-i", args.video, "-i", args.narration, "-i", args.bgm,
               "-filter_complex", audio_filter, "-map", "0:v", "-map", "[aout]"]
    else:
        audio_filter = (f"[1:a]volume={args.narration_gain}dB,"
                        f"apad,atrim=0:{video_duration:.3f}[aout]")
        cmd = ["-i", args.video, "-i", args.narration,
               "-filter_complex", audio_filter, "-map", "0:v", "-map", "[aout]"]

    run_ffmpeg(*cmd,
               "-c:v", "copy",
               "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
               "-shortest", "-movflags", "+faststart",
               args.output)
    output_size = Path(args.output).stat().st_size
    print(f"OK -> {args.output}  size={output_size} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
