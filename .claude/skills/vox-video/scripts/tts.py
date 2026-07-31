#!/usr/bin/env python3
"""Generate narration with Gemini TTS and word timestamps via local MLX Whisper.

Pipeline: Gemini TTS (PCM) → ffmpeg → narration.mp3
        → mlx-whisper (word_timestamps) → align to script → words.json

Run with the project venv: .venv/bin/python3 (mlx-whisper required).

Usage:
  .venv/bin/python3 tts.py --text-file script.txt --out-dir output/run/ch1

Outputs in --out-dir:
  narration.mp3   the narration audio
  asr.json        raw Whisper word timings (diagnostic)
  words.json      [{"word": ..., "start": ..., "end": ...}, ...] aligned to script
Prints a JSON summary (duration, word count, alignment_ratio) to stdout.
"""
import argparse
import base64
import json
import os
import subprocess
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

from align_words import align

API_BASE = "https://generativelanguage.googleapis.com"
DEFAULT_TTS_MODEL = "gemini-2.5-flash-preview-tts"
DEFAULT_VOICE = "Kore"
DEFAULT_STYLE = (
    "Read the following Korean narration in a calm, authoritative "
    "documentary narrator tone at a natural pace:"
)
WHISPER_REPO = "mlx-community/whisper-large-v3-turbo"


def gemini_tts(text, model, voice, style, api_key, retries=3):
    """Return raw PCM bytes (s16le 24kHz mono). Retries when audio is missing."""
    url = f"{API_BASE}/v1beta/models/{model}:generateContent"
    prompt = f"{style}\n\n{text}" if style else text
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}
            },
        },
    }
    last = None
    for attempt in range(retries):
        r = requests.post(
            url,
            headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
            json=body,
            timeout=300,
        )
        if r.status_code != 200:
            last = f"HTTP {r.status_code}: {r.text[:500]}"
            print(f"[tts] Gemini 오류 (시도 {attempt + 1}): {last}", file=sys.stderr)
            continue
        data = r.json()
        try:
            parts = data["candidates"][0]["content"]["parts"]
        except (KeyError, IndexError):
            parts = []
        inline = next((p["inlineData"] for p in parts if "inlineData" in p), None)
        if inline is None:
            # 문서화된 결함: 간혹 오디오 대신 텍스트가 반환됨 → 재시도
            last = "응답에 오디오가 없습니다 (텍스트 반환됨)"
            print(f"[tts] {last} (시도 {attempt + 1})", file=sys.stderr)
            continue
        return base64.b64decode(inline["data"])
    sys.exit(f"Gemini TTS 실패: {last}")


def resolve_whisper_model():
    """Find the local large-v3-turbo snapshot in the HF cache (offline)."""
    hub = Path.home() / ".cache" / "huggingface" / "hub"
    model_dir = hub / f"models--{WHISPER_REPO.replace('/', '--')}" / "snapshots"
    if model_dir.is_dir():
        for snap in sorted(model_dir.iterdir()):
            if (snap / "config.json").is_file() and (snap / "weights.safetensors").is_file():
                return str(snap)
    # 캐시에 없으면 repo id를 반환해 mlx-whisper가 다운로드하게 둔다
    return WHISPER_REPO


def ffprobe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return float(out)


def main():
    load_dotenv()
    p = argparse.ArgumentParser()
    p.add_argument("--text-file", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--model", default=os.environ.get("GEMINI_TTS_MODEL") or DEFAULT_TTS_MODEL)
    p.add_argument("--voice", default=os.environ.get("GEMINI_TTS_VOICE") or DEFAULT_VOICE)
    p.add_argument("--style", default=os.environ.get("GEMINI_TTS_STYLE") or DEFAULT_STYLE)
    p.add_argument("--language", default="ko")
    args = p.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        sys.exit("GEMINI_API_KEY가 비어 있습니다. 프로젝트 루트의 .env에 키를 입력하세요.")

    with open(args.text_file, encoding="utf-8") as f:
        script = f.read().strip()
    if not script:
        sys.exit(f"{args.text_file}가 비어 있습니다.")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1) Gemini TTS → PCM → mp3
    pcm = gemini_tts(script, args.model, args.voice, args.style, api_key)
    pcm_path = out_dir / "narration.pcm"
    pcm_path.write_bytes(pcm)
    audio_path = out_dir / "narration.mp3"
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "s16le", "-ar", "24000", "-ac", "1",
         "-i", str(pcm_path), "-b:a", "160k", str(audio_path)],
        check=True,
    )
    pcm_path.unlink()
    duration = ffprobe_duration(audio_path)

    # 2) MLX Whisper word timings (local, offline)
    try:
        import mlx_whisper
    except ImportError:
        sys.exit("mlx-whisper가 없습니다. 프로젝트 루트에서 실행: "
                 "python3 -m venv .venv && .venv/bin/pip install -r requirements.txt "
                 "(이 스크립트는 .venv/bin/python3 로 실행해야 합니다)")
    result = mlx_whisper.transcribe(
        str(audio_path),
        path_or_hf_repo=resolve_whisper_model(),
        language=args.language,
        word_timestamps=True,
        condition_on_previous_text=False,
    )
    asr_words = []
    for seg in result.get("segments", []):
        for w in seg.get("words") or []:
            text = str(w.get("word", "")).strip()
            if text:
                asr_words.append({"text": text, "start": float(w["start"]), "end": float(w["end"])})
    with open(out_dir / "asr.json", "w", encoding="utf-8") as f:
        json.dump({"recognized_text": str(result.get("text", "")).strip(),
                   "words": asr_words}, f, ensure_ascii=False, indent=1)

    # 3) 대본(정본)에 Whisper 타이밍 정렬
    words, ratio = align(script, asr_words, duration)
    words_path = out_dir / "words.json"
    with open(words_path, "w", encoding="utf-8") as f:
        json.dump(words, f, ensure_ascii=False, indent=1)

    if ratio < 0.8:
        print(f"[경고] 정렬률 {ratio:.0%} — 낮습니다. asr.json을 확인하고 "
              "필요하면 대본을 다듬어 재생성하세요.", file=sys.stderr)

    print(json.dumps({
        "narration": str(audio_path),
        "words": str(words_path),
        "duration_seconds": round(duration, 2),
        "word_count": len(words),
        "alignment_ratio": ratio,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
