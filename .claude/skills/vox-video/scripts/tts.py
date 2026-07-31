#!/usr/bin/env python3
"""Generate narration with the local clone-voice TTS backend (Gemini voices)
and word timestamps via local MLX Whisper.

Pipeline: ensure_tts.sh(백엔드 자동 기동) → POST /api/tts → narration.mp3
        → mlx-whisper (word_timestamps) → 대본 정렬 → words.json

20_숏츠 자동화 프로젝트의 TTS 구성을 이식: Gemini 음색 이름(Charon, Kore 등)을
백엔드 프로필 id로 자동 변환하고, 톤 프롬프트로 화자 성격을 지정한다.
API 키 불필요 — 외장 SSD(Samsung_T5)의 clone-voice 백엔드(8930)를 사용.

Run with the project venv: .venv/bin/python3 (mlx-whisper required).

Usage:
  .venv/bin/python3 tts.py --text-file script.txt --out-dir output/run/ch1
  # 표현태그 삽입본을 따로 쓸 때 (정렬은 항상 --text-file 원본 기준):
  .venv/bin/python3 tts.py --text-file script.txt --tagged-file script-tagged.txt --out-dir ...

Outputs in --out-dir:
  narration.mp3   the narration audio
  asr.json        raw Whisper word timings (diagnostic)
  words.json      [{"word": ..., "start": ..., "end": ...}, ...] aligned to script
Prints a JSON summary (duration, word count, alignment_ratio) to stdout.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

from align_words import align

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_BASE_URL = "http://127.0.0.1:8930"
DEFAULT_VOICE = "Charon"
DEFAULT_TONE = (
    "차분하고 신뢰감 있는 40대 한국 남성 다큐멘터리 내레이터, 감정이 풍부함. "
    "웃음소리 등 비언어 소리는 실제로 내지 말고 말투·억양으로만 감정을 표현"
)
WHISPER_REPO = "mlx-community/whisper-large-v3-turbo"


def ensure_backend():
    r = subprocess.run(["bash", str(SCRIPT_DIR / "ensure_tts.sh")],
                       capture_output=True, text=True)
    print(r.stdout.strip(), file=sys.stderr)
    if r.returncode != 0:
        sys.exit("TTS 백엔드 기동 실패: 외장 SSD(Samsung_T5) 연결을 확인하세요.\n"
                 + (r.stdout + r.stderr).strip()[-300:])


def resolve_voice_id(voice, base_url):
    """음색 이름(예: Charon) → 백엔드 프로필 id. 이미 id면 그대로."""
    if re.fullmatch(r"[0-9a-f]{32}", voice, re.IGNORECASE):
        return voice
    r = requests.get(f"{base_url}/api/voices", timeout=30)
    r.raise_for_status()
    data = r.json()
    voices = data if isinstance(data, list) else data.get("voices", [])
    lc = voice.lower()
    hit = next(
        (v for v in voices
         if f"gemini-voice:{voice}" in (v.get("tags") or [])
         or v.get("name") == voice
         or (isinstance(v.get("name"), str) and v["name"].lower().startswith(lc + " "))),
        None,
    )
    if hit is None:
        names = [v.get("name") for v in voices
                 if any(str(t).startswith("gemini-voice:") for t in (v.get("tags") or []))]
        sys.exit(f"음색 프로필을 찾지 못했습니다: \"{voice}\". "
                 f"사용 가능한 Gemini 프리셋: {', '.join(filter(None, names)) or '(없음 — clone-voice 앱에서 프리셋 생성 필요)'}")
    return hit["id"]


def synthesize(text, voice_id, tone, base_url, out_wav, language="ko"):
    try:
        r = requests.post(
            f"{base_url}/api/tts",
            json={"text": text, "language": language, "model_id": "gemini",
                  "voice_id": voice_id, "tone_prompt": tone},
            timeout=600,
        )
    except requests.ConnectionError as e:
        sys.exit(f"TTS 서버({base_url}) 연결 실패 — SSD 연결 확인 필요. ({e})")
    if r.status_code != 200:
        sys.exit(f"TTS 생성 실패 HTTP {r.status_code}: {r.text[:500]}")
    data = r.json()
    wav = requests.get(f"{base_url}{data['audio_url']}", timeout=300)
    wav.raise_for_status()
    Path(out_wav).write_bytes(wav.content)
    return data


def resolve_whisper_model():
    """Find the local large-v3-turbo snapshot in the HF cache (offline)."""
    hub = Path.home() / ".cache" / "huggingface" / "hub"
    model_dir = hub / f"models--{WHISPER_REPO.replace('/', '--')}" / "snapshots"
    if model_dir.is_dir():
        for snap in sorted(model_dir.iterdir()):
            if (snap / "config.json").is_file() and (snap / "weights.safetensors").is_file():
                return str(snap)
    return WHISPER_REPO  # 캐시에 없으면 mlx-whisper가 다운로드


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
    p.add_argument("--text-file", required=True, help="원본 대본 (정렬 정본)")
    p.add_argument("--tagged-file", help="표현태그 삽입본 (TTS 입력용, 없으면 원본 사용)")
    p.add_argument("--out-dir", required=True)
    p.add_argument("--voice", default=os.environ.get("VOX_TTS_VOICE") or DEFAULT_VOICE)
    p.add_argument("--tone", default=os.environ.get("VOX_TTS_TONE") or DEFAULT_TONE)
    p.add_argument("--base-url", default=os.environ.get("TTS_BASE_URL") or DEFAULT_BASE_URL)
    p.add_argument("--language", default="ko")
    args = p.parse_args()

    with open(args.text_file, encoding="utf-8") as f:
        script = f.read().strip()
    if not script:
        sys.exit(f"{args.text_file}가 비어 있습니다.")
    tts_input = script
    if args.tagged_file:
        with open(args.tagged_file, encoding="utf-8") as f:
            tts_input = f.read().strip()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1) 로컬 clone-voice 백엔드로 음성 생성
    ensure_backend()
    voice_id = resolve_voice_id(args.voice, args.base_url)
    wav_path = out_dir / "narration.wav"
    synthesize(tts_input, voice_id, args.tone, args.base_url, wav_path,
               language=args.language)
    audio_path = out_dir / "narration.mp3"
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(wav_path),
         "-b:a", "160k", str(audio_path)],
        check=True,
    )
    wav_path.unlink()
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

    # 3) 대본(정본)에 Whisper 타이밍 정렬 — 태그본이 아니라 항상 원본 기준
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
        "voice": args.voice,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
