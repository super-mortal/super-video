#!/usr/bin/env python3
"""Generate a simple full-length ambient BGM WAV for HyperFrames projects.

Use only when the user explicitly requests generated background music or when
there is no source audio to preserve. The script uses Python stdlib only.
"""

from __future__ import annotations

import argparse
import math
import random
import struct
import wave
from pathlib import Path


def clamp(value: float, low: float = -1.0, high: float = 1.0) -> float:
    """Clamp *value* to the inclusive range [low, high]."""
    return max(low, min(high, value))


def note_envelope(
    time_sec: float,
    note_start: float,
    note_length_sec: float,
    attack: float = 0.05,
    release: float = 0.25,
) -> float:
    """Return the linear attack/release envelope of a note at *time_sec*.

    Returns 0.0 outside the note span, a linear ramp up over *attack*
    seconds, a linear ramp down over *release* seconds, and 1.0 in between.
    """
    local = time_sec - note_start
    if local < 0 or local > note_length_sec:
        return 0.0
    if local < attack:
        return local / max(attack, 1e-6)
    if local > note_length_sec - release:
        return max(0.0, (note_length_sec - local) / max(release, 1e-6))
    return 1.0


def sine(frequency: float, time_sec: float) -> float:
    """Return a sine-wave sample of the given frequency at *time_sec*."""
    return math.sin(2.0 * math.pi * frequency * time_sec)


def synthesize_track(
    output_path: Path,
    duration_sec: float,
    bpm: float,
    sample_rate: int,
    volume: float,
    seed: int,
) -> None:
    """Synthesize the ambient BGM track and write it to *output_path*.

    Renders a 16-bit stereo WAV at *sample_rate*, layering pad chords,
    sub bass, a half-beat arpeggio, a sparse lead melody and deterministic
    noise, with 3-second fade-in/out scaled by *volume*.
    """
    rng = random.Random(seed)
    beat = 60.0 / bpm
    chords = [
        (261.63, 329.63, 392.00),  # C
        (220.00, 261.63, 329.63),  # Am
        (174.61, 220.00, 261.63),  # F
        (196.00, 246.94, 293.66),  # G
    ]
    lead_notes = [523.25, 587.33, 659.25, 783.99, 659.25, 587.33]

    total = int(duration_sec * sample_rate)
    with wave.open(str(output_path), "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)

        for sample_index in range(total):
            time_sec = sample_index / sample_rate
            bar = int(time_sec // (beat * 4))
            chord = chords[bar % len(chords)]

            # Soft pad chord
            pad = 0.0
            for frequency in chord:
                pad += 0.18 * sine(frequency, time_sec) + 0.08 * sine(
                    frequency * 2.0, time_sec
                )
            pad *= 0.45

            # Sub bass on each beat
            beat_pos = time_sec % beat
            kick_env = max(0.0, 1.0 - beat_pos / 0.18) if beat_pos < 0.18 else 0.0
            bass = 0.18 * sine(chord[0] / 2.0, time_sec) + 0.18 * kick_env * sine(
                55.0, time_sec
            )

            # Gentle arpeggio every half-beat
            step = int((time_sec / (beat / 2.0)))
            arp_freq = chord[step % len(chord)] * (2.0 if step % 4 else 1.0)
            arp_env = note_envelope(
                time_sec, step * (beat / 2.0), beat / 2.0, attack=0.01, release=0.18
            )
            arp = 0.15 * arp_env * sine(arp_freq, time_sec)

            # Sparse lead every 2 bars
            lead = 0.0
            phrase_len = beat * 8
            phrase_pos = time_sec % phrase_len
            if phrase_pos < beat * 6:
                lead_step = int(phrase_pos // beat)
                lead_start = (time_sec // phrase_len) * phrase_len + lead_step * beat
                lead_env = note_envelope(
                    time_sec, lead_start, beat * 0.8, attack=0.02, release=0.25
                )
                lead = 0.08 * lead_env * sine(
                    lead_notes[lead_step % len(lead_notes)], time_sec
                )

            # Very low deterministic noise for texture
            noise = 0.015 * (rng.random() * 2.0 - 1.0)

            fade_in = min(1.0, time_sec / 3.0)
            fade_out = min(1.0, max(0.0, (duration_sec - time_sec) / 3.0))
            amp = volume * fade_in * fade_out
            sample = clamp((pad + bass + arp + lead + noise) * amp)

            # Slight stereo width
            left = int(clamp(sample * 0.95) * 32767)
            right = int(clamp(sample * 1.05) * 32767)
            wav.writeframes(struct.pack("<hh", left, right))


def main() -> int:
    """Parse CLI arguments, synthesize the BGM track and report the result."""
    parser = argparse.ArgumentParser(
        description="Generate a simple full-length ambient BGM WAV."
    )
    parser.add_argument("output", type=Path, help="Output WAV path")
    parser.add_argument(
        "--duration", type=float, required=True, help="Duration in seconds"
    )
    parser.add_argument("--bpm", type=float, default=110.0, help="Tempo in BPM")
    parser.add_argument("--sample-rate", type=int, default=44100, help="Sample rate")
    parser.add_argument(
        "--volume", type=float, default=0.25, help="Overall volume, 0.0-1.0"
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="Deterministic random seed"
    )
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    synthesize_track(
        output_path=args.output,
        duration_sec=args.duration,
        bpm=args.bpm,
        sample_rate=args.sample_rate,
        volume=args.volume,
        seed=args.seed,
    )
    print(f"Generated {args.output} ({args.duration:.2f}s, {args.bpm:.1f} BPM)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
