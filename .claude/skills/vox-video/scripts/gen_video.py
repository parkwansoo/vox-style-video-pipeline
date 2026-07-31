#!/usr/bin/env python3
"""Generate a video clip via Kie.ai.

Models:
  omni      → gemini-omni-video      (input image = reference)
  seedance  → bytedance/seedance-2-fast (input image = first frame; for public figures)

Usage:
  python3 gen_video.py --model omni --prompt-file p.txt --image clip1.png --duration 6 --out clip1.mp4
  python3 gen_video.py --model seedance --prompt-file p.txt --image-url <URL> --duration 4 --out clip2.mp4
"""
import argparse
import json
import os
import sys

from dotenv import load_dotenv

import kie_common


def main():
    load_dotenv()
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True, choices=["omni", "seedance"])
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--prompt")
    g.add_argument("--prompt-file")
    p.add_argument("--image")
    p.add_argument("--image-url")
    p.add_argument("--duration", required=True, type=int, choices=[4, 6])
    p.add_argument("--aspect", default="16:9")
    p.add_argument("--resolution", default=os.environ.get("KIE_VIDEO_RESOLUTION") or "720p")
    p.add_argument("--out", required=True)
    args = p.parse_args()

    prompt = args.prompt
    if args.prompt_file:
        with open(args.prompt_file, encoding="utf-8") as f:
            prompt = f.read().strip()

    image_url = args.image_url
    if not image_url and args.image:
        image_url = kie_common.upload_file(args.image)
    if not image_url:
        sys.exit("--image 또는 --image-url 로 입력 이미지를 지정하세요.")

    if args.model == "omni":
        model_id = "gemini-omni-video"
        payload = {
            "prompt": prompt,
            "image_urls": [image_url],       # reference image
            "duration": str(args.duration),  # Omni expects a string
            "aspect_ratio": args.aspect,
            "resolution": args.resolution,
        }
    else:
        if args.resolution not in ("480p", "720p"):
            sys.exit(f"Seedance 2.0 Fast는 480p/720p만 지원합니다 (지정값: {args.resolution})")
        model_id = "bytedance/seedance-2-fast"
        payload = {
            "prompt": prompt,
            "first_frame_url": image_url,    # direct first frame
            "duration": args.duration,       # Seedance expects an integer
            "aspect_ratio": args.aspect,
            "resolution": args.resolution,
            "generate_audio": True,
        }

    try:
        out = kie_common.generate(model_id, payload, args.out, timeout=1200)
    except kie_common.KieError as e:
        sys.exit(f"영상 생성 실패: {e}")
    print(json.dumps({"out": out, "model": model_id, "image_url": image_url}))


if __name__ == "__main__":
    main()
