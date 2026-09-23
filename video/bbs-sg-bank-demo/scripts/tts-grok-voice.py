#!/usr/bin/env python3
"""Narrate the demo video with xAI's text-to-speech API (Grok voice).

Reads narration lines from narration.json, writes one MP3 per line into
assets/audio/, normalizes loudness, and records measured durations in
assets/audio/timings.json (used to size the video's scenes).

Credentials: reuses the signed-in Grok session token in ~/.grok/auth.json when
XAI_API_KEY is not set.

Usage: python3 scripts/tts-grok-voice.py [--voice eve] [--force]
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "assets" / "audio"
VOICE_DEFAULT = "eve"
LANGUAGE = "en"


def api_key() -> str:
    key = os.environ.get("XAI_API_KEY")
    if key:
        return key
    auth = pathlib.Path.home() / ".grok" / "auth.json"
    if auth.exists():
        blob = json.loads(auth.read_text())
        for name, entry in blob.items():
            if name.startswith("https://auth.x.ai") and isinstance(entry, dict):
                if entry.get("key"):
                    return entry["key"]
    raise SystemExit("no XAI_API_KEY and no Grok session token in ~/.grok/auth.json")


def synthesize(text: str, voice: str, token: str) -> bytes:
    body = json.dumps({"text": text, "voice_id": voice, "language": LANGUAGE}).encode()
    req = urllib.request.Request(
        "https://api.x.ai/v1/tts",
        data=body,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read()


def duration(path: pathlib.Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return round(float(out.stdout.strip()), 3)


def normalize(path: pathlib.Path) -> None:
    tmp = path.with_suffix(".norm.mp3")
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(path), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
         "-ar", "44100", "-b:a", "192k", str(tmp)],
        check=True,
    )
    tmp.replace(path)


def main() -> int:
    args = sys.argv[1:]
    voice = VOICE_DEFAULT
    if "--voice" in args:
        voice = args[args.index("--voice") + 1]
    force = "--force" in args

    lines = json.loads((ROOT / "narration.json").read_text())
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    token = api_key()

    timings: dict[str, dict[str, object]] = {}
    for entry in lines:
        line_id, text = entry["id"], entry["text"]
        path = OUT_DIR / f"{line_id}.mp3"
        if force or not path.exists():
            path.write_bytes(synthesize(text, voice, token))
            normalize(path)
            print(f"{line_id}: synthesized ({len(text)} chars)")
        timings[line_id] = {
            "text": text,
            "scene": entry.get("scene"),
            "duration_s": duration(path),
            "path": f"assets/audio/{path.name}",
        }

    (OUT_DIR / "timings.json").write_text(json.dumps(
        {"voice": voice, "lines": timings}, indent=2) + "\n")
    total = sum(float(v["duration_s"]) for v in timings.values())
    print(f"narration total {total:.2f}s across {len(timings)} lines")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
