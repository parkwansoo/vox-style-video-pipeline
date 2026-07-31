#!/usr/bin/env python3
"""Generate a video clip.

Models:
  omni      → Gemini API 직접 호출: gemini-omni-flash-preview
              (google-genai Interactions API, 이미지는 Files API로 업로드되는 참조)
  seedance  → Kie.ai: bytedance/seedance-2-fast (공인 클립 전용, 이미지 = 첫 프레임)

Usage:
  .venv/bin/python3 gen_video.py --model omni --prompt-file p.txt --image clip1.png --duration 6 --out clip1.mp4
  .venv/bin/python3 gen_video.py --model seedance --prompt-file p.txt --image clip2.png --duration 4 --out clip2.mp4
"""
import argparse
import json
import mimetypes
import os
import sys
import time
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

DEFAULT_OMNI_MODEL = "gemini-omni-flash-preview"


def gemini_upload(client, path):
    """Upload a local file to the Gemini Files API and wait until ACTIVE."""
    from google.genai import types
    mime = mimetypes.guess_type(path)[0] or "application/octet-stream"
    file_obj = client.files.upload(
        file=path,
        config=types.UploadFileConfig(display_name=os.path.basename(path), mime_type=mime),
    )
    interval = 3.0
    for _ in range(30):
        state = getattr(file_obj.state, "name", str(file_obj.state))
        if state == "ACTIVE":
            return file_obj.uri, mime
        if state == "FAILED":
            raise RuntimeError(f"Files API 처리 실패: {path}")
        time.sleep(interval)
        interval = min(interval * 1.5, 30)
        file_obj = client.files.get(name=file_obj.name)
    raise RuntimeError(f"Files API ACTIVE 대기 타임아웃: {path}")


def download_gemini_video(uri, out_path, api_key):
    sep = "&" if "?" in uri else "?"
    req = urllib.request.Request(f"{uri}{sep}alt=media")
    req.add_header("x-goog-api-key", api_key)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(req, timeout=480) as resp, open(out_path, "wb") as f:
        while True:
            chunk = resp.read(1 << 16)
            if not chunk:
                break
            f.write(chunk)
    return out_path


def generate_omni(prompt, image_path, image_uri, duration, aspect, out_path):
    from google import genai
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        sys.exit("GEMINI_API_KEY가 비어 있습니다. 프로젝트 루트의 .env에 키를 입력하세요.")
    client = genai.Client(api_key=api_key, vertexai=False)

    parts = []
    if image_path:
        uri, mime = gemini_upload(client, image_path)
        parts.append({"type": "image", "uri": uri, "mime_type": mime})
    elif image_uri:
        parts.append({"type": "image", "uri": image_uri, "mime_type": "image/png"})
    parts.append({"type": "text", "text": prompt})

    model = os.environ.get("GEMINI_OMNI_MODEL") or DEFAULT_OMNI_MODEL
    last = None
    for attempt in range(2):
        try:
            print(f"[omni] {model} 생성 요청 (시도 {attempt + 1})…", file=sys.stderr)
            interaction = client.interactions.create(
                model=model,
                input=parts,
                response_format={
                    "type": "video",
                    "aspect_ratio": aspect,
                    "duration": f"{duration}s",
                    "delivery": "uri",
                },
            )
            output_video = interaction.output_video
            if not output_video or not output_video.uri:
                raise RuntimeError(f"응답에 영상이 없습니다 (interaction={interaction.id})")
            download_gemini_video(output_video.uri, out_path, api_key)
            return {"out": out_path, "model": model, "interaction_id": interaction.id}
        except Exception as e:  # SDK 예외 타입이 다양해 광범위 캐치 후 재시도
            last = e
            print(f"[omni] 실패: {e}", file=sys.stderr)
    sys.exit(f"영상 생성 실패(omni): {last}")


def generate_seedance(prompt, image_path, image_url, duration, aspect, resolution, out_path):
    import kie_common
    if not image_url and image_path:
        image_url = kie_common.upload_file(image_path)
    if not image_url:
        sys.exit("seedance는 --image 또는 --image-url 로 첫 프레임 이미지를 지정해야 합니다.")
    if resolution not in ("480p", "720p"):
        sys.exit(f"Seedance 2.0 Fast는 480p/720p만 지원합니다 (지정값: {resolution})")
    payload = {
        "prompt": prompt,
        "first_frame_url": image_url,    # direct first frame
        "duration": duration,            # Seedance expects an integer
        "aspect_ratio": aspect,
        "resolution": resolution,
        "generate_audio": True,
    }
    try:
        out = kie_common.generate("bytedance/seedance-2-fast", payload, out_path, timeout=1200)
    except kie_common.KieError as e:
        sys.exit(f"영상 생성 실패(seedance): {e}")
    return {"out": out, "model": "bytedance/seedance-2-fast", "image_url": image_url}


def main():
    load_dotenv()
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True, choices=["omni", "seedance"])
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--prompt")
    g.add_argument("--prompt-file")
    p.add_argument("--image", help="로컬 이미지 (omni=참조, seedance=첫 프레임)")
    p.add_argument("--image-url", help="이미 업로드된 이미지 URI/URL")
    p.add_argument("--duration", required=True, type=int, choices=[4, 6])
    p.add_argument("--aspect", default="16:9")
    p.add_argument("--resolution", default=os.environ.get("KIE_VIDEO_RESOLUTION") or "720p",
                   help="seedance 전용 (omni는 모델 기본 720p)")
    p.add_argument("--out", required=True)
    args = p.parse_args()

    prompt = args.prompt
    if args.prompt_file:
        with open(args.prompt_file, encoding="utf-8") as f:
            prompt = f.read().strip()

    if args.model == "omni":
        result = generate_omni(prompt, args.image, args.image_url,
                               args.duration, args.aspect, args.out)
    else:
        result = generate_seedance(prompt, args.image, args.image_url,
                                   args.duration, args.aspect, args.resolution, args.out)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
