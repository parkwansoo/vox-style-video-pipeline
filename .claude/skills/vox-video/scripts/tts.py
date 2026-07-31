#!/usr/bin/env python3
"""Generate narration with ElevenLabs and extract word-level timestamps.

Usage:
  python3 tts.py --text-file script.txt --out-dir output/run/ch1

Outputs in --out-dir:
  narration.mp3   the narration audio
  alignment.json  raw character-level alignment from the API
  words.json      [{"word": ..., "start": ..., "end": ...}, ...]
Prints a JSON summary (duration, word count) to stdout.
"""
import argparse
import base64
import json
import os
import sys

import requests
from dotenv import load_dotenv

API_BASE = "https://api.elevenlabs.io"
DEFAULT_VOICE = "nPczCjzI2devNBz1zQrb"  # Brian (documentary narrator)


def words_from_alignment(al):
    """Character-level alignment → word-level timestamps (split on whitespace)."""
    words = []
    chars = al["characters"]
    starts = al["character_start_times_seconds"]
    ends = al["character_end_times_seconds"]
    cur, start = "", None
    for i, ch in enumerate(chars):
        if ch.isspace():
            if cur:
                words.append({"word": cur, "start": round(start, 3), "end": round(ends[i - 1], 3)})
                cur, start = "", None
        else:
            if not cur:
                start = starts[i]
            cur += ch
    if cur:
        words.append({"word": cur, "start": round(start, 3), "end": round(ends[-1], 3)})
    return words


def main():
    load_dotenv()
    p = argparse.ArgumentParser()
    p.add_argument("--text-file", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--voice-id", default=os.environ.get("ELEVENLABS_VOICE_ID") or DEFAULT_VOICE)
    p.add_argument("--model-id", default=os.environ.get("ELEVENLABS_MODEL_ID") or "eleven_multilingual_v2")
    p.add_argument("--output-format", default="mp3_44100_128")
    args = p.parse_args()

    key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not key:
        sys.exit("ELEVENLABS_API_KEY가 비어 있습니다. 프로젝트 루트의 .env에 키를 입력하세요.")

    with open(args.text_file, encoding="utf-8") as f:
        text = f.read().strip()
    if not text:
        sys.exit(f"{args.text_file}가 비어 있습니다.")

    url = f"{API_BASE}/v1/text-to-speech/{args.voice_id}/with-timestamps"
    r = requests.post(
        url,
        params={"output_format": args.output_format},
        headers={"xi-api-key": key, "Content-Type": "application/json"},
        json={
            "text": text,
            "model_id": args.model_id,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.0,
                "use_speaker_boost": True,
            },
        },
        timeout=300,
    )
    if r.status_code != 200:
        sys.exit(f"ElevenLabs 오류 HTTP {r.status_code}: {r.text[:500]}")
    data = r.json()

    os.makedirs(args.out_dir, exist_ok=True)
    audio_path = os.path.join(args.out_dir, "narration.mp3")
    with open(audio_path, "wb") as f:
        f.write(base64.b64decode(data["audio_base64"]))

    alignment = data["alignment"]
    with open(os.path.join(args.out_dir, "alignment.json"), "w", encoding="utf-8") as f:
        json.dump(alignment, f, ensure_ascii=False)

    words = words_from_alignment(alignment)
    words_path = os.path.join(args.out_dir, "words.json")
    with open(words_path, "w", encoding="utf-8") as f:
        json.dump(words, f, ensure_ascii=False, indent=1)

    duration = words[-1]["end"] if words else 0.0
    print(json.dumps({
        "narration": audio_path,
        "words": words_path,
        "duration_seconds": duration,
        "word_count": len(words),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
