#!/usr/bin/env python3
"""Whole-passage narration synthesis via the MiniMax TTS t2a_v2 API.

Core principle: synthesize the whole narration script in ONE request, never
sentence-by-sentence concatenation -- stitching sentences inserts fixed
silence between them and sounds unnatural (pitfalls recorded in
references/narration-sync-pipeline.md).

Usage:
    python minimax_narrate.py script.txt -o narration \
        --model speech-2.8-hd --voice female-shaonv
    python minimax_narrate.py .super-video/my-task/script.txt \
        --workdir .super-video/my-task

Credentials (resolved in order, first hit wins):
    1. --api-key CLI argument (per-run, never stored)
    2. MINIMAX_API_KEY environment variable
    3. config file ~/.config/minimax/api_key
       (Windows: C:\\Users\\<user>\\.config\\minimax\\api_key)
       Plain UTF-8 text: the bare key, or a single "MINIMAX_API_KEY=sk-..."
       line; blank lines and "#" comments are ignored.
When none is found the script prints a three-option guide: provide the key
directly, save it to the config file, or fall back to free Edge-TTS.

Optional environment variables:
    MINIMAX_BASE_URL  t2a endpoint, default https://api.minimaxi.com/v1/t2a_v2
    FFMPEG / FFPROBE  executable paths, resolved from PATH by default

Outputs:
    <out>.mp3           raw synthesized narration audio
    <out>.wav           44.1 kHz stereo WAV (for final mixdown)
    <out>_16k.wav       16 kHz mono WAV (for faster-whisper transcription)

    <out> defaults to narration (in the current directory). With --workdir it
    defaults to <workdir>/audio/narration instead, so every artefact of one
    job stays inside the task directory.

Exit codes: 0 success; non-zero on failure (missing key / API error / no audio).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

from task_paths import resolve_output

DEFAULT_BASE = "https://api.minimaxi.com/v1/t2a_v2"
CONFIG_KEY_PATH = Path.home() / ".config" / "minimax" / "api_key"


def find_executable(name: str) -> str:
    """Resolve an executable: env variable first, then PATH, else the raw name."""
    env = os.environ.get(name.upper())
    if env and Path(env).exists():
        return env
    found = shutil.which(name)
    return found or name


def synthesize_speech(text: str, mp3_path: str, model: str, voice_id: str,
                      base_url: str, api_key: str, timeout: int = 180) -> bool:
    """Call the MiniMax t2a_v2 endpoint and write the hex audio to mp3_path.

    Returns True on success, False when the API reports an error or no audio.
    """
    body = json.dumps({
        "model": model,
        "text": text,
        "stream": False,
        "language_boost": "Chinese",
        "output_format": "hex",
        "voice_setting": {"voice_id": voice_id, "speed": 1.0, "vol": 1.0, "pitch": 0},
        "audio_setting": {
            "sample_rate": 32000,
            "bitrate": 128000,
            "format": "mp3",
            "channel": 1,
        },
    }).encode("utf-8")

    req = urllib.request.Request(base_url, data=body, headers={
        "Authorization": "Bearer " + api_key,
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req, timeout=timeout) as response:
        data = json.loads(response.read().decode("utf-8"))

    base_resp = data.get("base_resp", {})
    if base_resp.get("status_code") != 0:
        print("FAIL base_resp:", base_resp, file=sys.stderr)
        print("HINT: verify that MINIMAX_API_KEY is valid; use the China "
              "endpoint api.minimaxi.com; the model name must be lowercase "
              "with an exact version (e.g. speech-2.8-hd).", file=sys.stderr)
        return False
    hex_audio = (data.get("data") or {}).get("audio")
    if not hex_audio:
        print("NO AUDIO:", json.dumps(data)[:500], file=sys.stderr)
        return False
    with open(mp3_path, "wb") as f:
        f.write(bytes.fromhex(hex_audio))
    return True


def synthesize_narration(text: str, out_prefix: str, model: str,
                         voice_id: str, base_url: str,
                         api_key: str) -> Path | None:
    """Synthesize the narration script and convert the MP3 into WAV deliverables.

    Writes <out_prefix>.mp3, <out_prefix>.wav (44.1 kHz stereo) and
    <out_prefix>_16k.wav (16 kHz mono). Returns the 44.1 kHz WAV path,
    or None when synthesis fails.
    """
    mp3_path = Path(out_prefix + ".mp3")
    wav_path = Path(out_prefix + ".wav")
    wav_16k_path = Path(out_prefix + "_16k.wav")

    if not synthesize_speech(text, mp3_path, model, voice_id, base_url, api_key):
        return None
    print(f"mp3: {mp3_path} {mp3_path.stat().st_size} bytes")

    ffmpeg = find_executable("ffmpeg")
    subprocess.run([ffmpeg, "-y", "-i", mp3_path, "-ac", "2", "-ar", "44100",
                    "-c:a", "pcm_s16le", wav_path], check=True)
    subprocess.run([ffmpeg, "-y", "-i", mp3_path, "-ac", "1", "-ar", "16000",
                    "-c:a", "pcm_s16le", wav_16k_path], check=True)
    print(f"wav : {wav_path}")
    return wav_path


def report_result(wav_path: str, text: str, model: str, voice_id: str) -> None:
    """Print the final status lines: WAV duration, char count, model and voice."""
    ffprobe = find_executable("ffprobe")
    probe_result = subprocess.run([ffprobe, "-v", "error", "-show_entries",
                                   "format=duration", "-of", "csv=p=0", wav_path],
                                  capture_output=True, text=True)
    print("DURATION:", probe_result.stdout.strip())
    print("CHARS:", len(text))
    print("MODEL:", model, "VOICE:", voice_id)


def read_config_key(path: Path) -> str:
    """Read the API key from a config file.

    Accepts a bare key or a ``MINIMAX_API_KEY=...`` line; blank lines and
    ``#`` comments are ignored. Returns an empty string when unavailable.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("MINIMAX_API_KEY="):
            line = line.split("=", 1)[1].strip()
        if line:
            return line
    return ""


def resolve_api_key(cli_key: str | None, env_key: str | None) -> tuple[str, str]:
    """Resolve the API key: CLI arg, then env var, then config file.

    Returns ``(key, source)``; source is empty when nothing was found.
    """
    if cli_key and cli_key.strip():
        return cli_key.strip(), "--api-key"
    if env_key and env_key.strip():
        return env_key.strip(), "env MINIMAX_API_KEY"
    config_key = read_config_key(CONFIG_KEY_PATH)
    if config_key:
        return config_key, str(CONFIG_KEY_PATH)
    return "", ""


def report_missing_key() -> None:
    """Print the three-option guide shown when no API key can be found."""
    print("ERROR: 未找到 MiniMax API 密钥"
          "（已检查 --api-key 参数、环境变量 MINIMAX_API_KEY、"
          f"配置文件 {CONFIG_KEY_PATH}）。", file=sys.stderr)
    print("请选择其一：", file=sys.stderr)
    print("  1) 直接把密钥发给 AI 助手，由其以 --api-key 方式传入本次运行；",
          file=sys.stderr)
    print("  2) 把密钥保存到配置文件（推荐，一次配置长期有效）：", file=sys.stderr)
    print(f"       {CONFIG_KEY_PATH}", file=sys.stderr)
    print("     UTF-8 纯文本，内容为密钥本身，或一行 MINIMAX_API_KEY=sk-...；",
          file=sys.stderr)
    print("  3) 不用 MiniMax，改用免费 Edge-TTS（无需密钥，仍走同一管线：",
          file=sys.stderr)
    print("       pip install edge-tts", file=sys.stderr)
    print("       edge-tts --voice zh-CN-XiaoyiNeural --text \"...\" "
          "--write-media out.mp3）", file=sys.stderr)


def main() -> int:
    """Parse CLI arguments and orchestrate synthesis plus result reporting."""
    ap = argparse.ArgumentParser(
        description="MiniMax whole-passage narration synthesis")
    ap.add_argument("script", help="Narration script txt file (UTF-8)")
    ap.add_argument("-o", "--out", default=None,
                    help="Output prefix (default: <workdir>/audio/narration, "
                         "or ./narration when --workdir is omitted)")
    ap.add_argument("--workdir", default=None,
                    help="Task directory, e.g. .super-video/my-task; when set, "
                         "outputs default to <workdir>/audio/")
    ap.add_argument("--model", default="speech-2.8-hd",
                    help="Model name, lowercase with exact version "
                         "(default: speech-2.8-hd)")
    ap.add_argument("--voice", default="female-shaonv",
                    help="Voice id (default: female-shaonv)")
    ap.add_argument("--api-key", default=None,
                    help="MiniMax API key for this run only (overrides env "
                         "var and config file; never stored)")
    ap.add_argument("--base-url",
                    default=os.environ.get("MINIMAX_BASE_URL", DEFAULT_BASE))
    args = ap.parse_args()

    api_key, key_source = resolve_api_key(args.api_key,
                                          os.environ.get("MINIMAX_API_KEY"))
    if not api_key:
        report_missing_key()
        return 2
    print(f"api key source: {key_source}")

    text = Path(args.script).read_text(encoding="utf-8").strip()
    if not text:
        print("ERROR: narration script is empty.", file=sys.stderr)
        return 2

    out_prefix = resolve_output(args.out, args.workdir, "audio", "narration")
    wav_path = synthesize_narration(text, str(out_prefix), args.model,
                                    args.voice, args.base_url, api_key)
    if wav_path is None:
        return 1
    report_result(wav_path, text, args.model, args.voice)
    return 0


if __name__ == "__main__":
    sys.exit(main())
