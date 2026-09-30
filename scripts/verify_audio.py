#!/usr/bin/env python3
"""Verify final video/audio duration and tail audibility for HyperFrames outputs.

This helper intentionally depends only on Python stdlib plus ffprobe/ffmpeg.
It checks:
- container duration
- audio stream duration when available
- tail segment mean/max volume via ffmpeg volumedetect
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str]) -> str:
    """Run a command and return its captured output."""
    proc = subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"Command failed ({proc.returncode}): {' '.join(cmd)}\n"
            f"{proc.stderr.strip()}"
        )
    return proc.stdout if proc.stdout else proc.stderr


def probe_media(path: Path) -> dict:
    """Probe a media file with ffprobe and return the parsed JSON payload."""
    out = run_command([
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(path),
    ])
    return json.loads(out)


def parse_float(value: object) -> float | None:
    """Convert a value to float, return None when conversion fails."""
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def tail_volume(
    path: Path, start: float, duration: float
) -> tuple[float | None, float | None, str]:
    """Measure tail mean/max volume with ffmpeg volumedetect."""
    proc = subprocess.run([
        "ffmpeg",
        "-ss", f"{max(0, start):.3f}",
        "-t", f"{duration:.3f}",
        "-i", str(path),
        "-af", "volumedetect",
        "-f", "null",
        "/dev/null",
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    text = proc.stdout + proc.stderr
    mean_match = re.search(r"mean_volume:\s*(-?\d+(?:\.\d+)?)\s*dB", text)
    max_match = re.search(r"max_volume:\s*(-?\d+(?:\.\d+)?)\s*dB", text)
    mean_db = float(mean_match.group(1)) if mean_match else None
    max_db = float(max_match.group(1)) if max_match else None
    return mean_db, max_db, text


def collect_stream_durations(
    probe_data: dict,
) -> tuple[list[float], list[float]]:
    """Collect audio and video stream durations from an ffprobe payload."""
    audio_durations: list[float] = []
    video_durations: list[float] = []
    for stream in probe_data.get("streams", []):
        duration = parse_float(stream.get("duration"))
        if stream.get("codec_type") == "audio" and duration is not None:
            audio_durations.append(duration)
        if stream.get("codec_type") == "video" and duration is not None:
            video_durations.append(duration)
    return audio_durations, video_durations


def collect_failures(
    args: argparse.Namespace,
    duration: float,
    audio_durations: list[float],
    video_durations: list[float],
    mean_db: float | None,
    max_db: float | None,
) -> list[str]:
    """Collect every verification failure message for the probed media."""
    failures: list[str] = []
    if args.min_duration is not None and duration + 0.1 < args.min_duration:
        failures.append(
            f"duration {duration:.3f}s < expected {args.min_duration:.3f}s"
        )

    if audio_durations and video_durations:
        drift = abs(max(audio_durations) - max(video_durations))
        if drift > args.max_av_drift:
            failures.append(
                f"audio/video duration drift {drift:.3f}s"
                f" > {args.max_av_drift:.3f}s"
            )
    elif not audio_durations:
        failures.append("no audio stream duration found")

    if mean_db is None or max_db is None:
        failures.append("unable to read tail volume with ffmpeg volumedetect")
    elif mean_db < args.min_tail_mean_db:
        failures.append(
            f"tail mean_volume {mean_db:.1f} dB"
            f" < threshold {args.min_tail_mean_db:.1f} dB"
        )

    return failures


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Verify audio coverage and tail audibility in a rendered video."
    )
    parser.add_argument("file", type=Path, help="Final MP4/MOV file to verify")
    parser.add_argument(
        "--min-duration",
        type=float,
        default=None,
        help="Minimum expected duration in seconds",
    )
    parser.add_argument(
        "--tail-seconds",
        type=float,
        default=12.0,
        help="Tail duration to analyze",
    )
    parser.add_argument(
        "--min-tail-mean-db",
        type=float,
        default=-60.0,
        help="Fail if tail mean_volume is below this dB",
    )
    parser.add_argument(
        "--max-av-drift",
        type=float,
        default=0.15,
        help="Allowed audio/video duration drift in seconds",
    )
    return parser


def main() -> int:
    """Parse CLI arguments, run all checks, and report the result."""
    args = build_parser().parse_args()

    if not args.file.exists():
        print(f"FAIL: file not found: {args.file}", file=sys.stderr)
        return 2

    try:
        probe_data = probe_media(args.file)
        format_duration = parse_float(probe_data.get("format", {}).get("duration"))
        audio_durations, video_durations = collect_stream_durations(probe_data)

        duration = format_duration or max(audio_durations + video_durations + [0.0])
        if duration <= 0:
            print("FAIL: unable to determine media duration", file=sys.stderr)
            return 3

        tail_start = max(0.0, duration - args.tail_seconds)
        mean_db, max_db, _ = tail_volume(args.file, tail_start, args.tail_seconds)
        failures = collect_failures(
            args, duration, audio_durations, video_durations, mean_db, max_db
        )

        print(f"file={args.file}")
        print(f"duration={duration:.3f}s")
        if video_durations:
            print(f"video_duration={max(video_durations):.3f}s")
        if audio_durations:
            print(f"audio_duration={max(audio_durations):.3f}s")
        print(f"tail_start={tail_start:.3f}s tail_seconds={args.tail_seconds:.3f}s")
        print(f"tail_mean_volume={mean_db if mean_db is not None else 'NA'} dB")
        print(f"tail_max_volume={max_db if max_db is not None else 'NA'} dB")

        if failures:
            print("FAIL:")
            for item in failures:
                print(f"- {item}")
            return 1

        print("PASS: audio duration and tail audibility checks passed")
        return 0
    except Exception as exc:  # noqa: BLE001 - CLI helper must report every failure
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
