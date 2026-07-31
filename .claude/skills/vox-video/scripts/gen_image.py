#!/usr/bin/env python3
"""Generate a clip image with GPT Image 2 (image-to-image) using the style reference.

Usage:
  python3 gen_image.py --prompt-file prompt.txt --style-url <URL> --out clip1.png
  python3 gen_image.py --prompt "..." --style-ref assets/style_reference.png --out clip1.png

The style reference is always passed as the input image; upload it once with
upload.py and reuse --style-url across clips to avoid repeated uploads.
"""
import argparse
import json
import sys

from dotenv import load_dotenv

import kie_common

MODEL = "gpt-image-2-image-to-image"


def main():
    load_dotenv()
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--prompt")
    g.add_argument("--prompt-file")
    s = p.add_mutually_exclusive_group(required=True)
    s.add_argument("--style-url")
    s.add_argument("--style-ref")
    p.add_argument("--out", required=True)
    p.add_argument("--aspect", default="16:9")
    p.add_argument("--resolution", default="1K", choices=["1K", "2K", "4K"])
    args = p.parse_args()

    prompt = args.prompt
    if args.prompt_file:
        with open(args.prompt_file, encoding="utf-8") as f:
            prompt = f.read().strip()

    style_url = args.style_url or kie_common.upload_file(args.style_ref)

    payload = {
        "prompt": prompt,
        "input_urls": [style_url],
        "aspect_ratio": args.aspect,
        "resolution": args.resolution,
    }
    try:
        out = kie_common.generate(MODEL, payload, args.out, timeout=600)
    except kie_common.KieError as e:
        sys.exit(f"이미지 생성 실패: {e}")
    print(json.dumps({"out": out, "style_url": style_url}))


if __name__ == "__main__":
    main()
