#!/usr/bin/env python3
"""Generate a clip image via Codex CLI's built-in image generation (ChatGPT 구독 OAuth).

No API key needed — requires `codex login` with a ChatGPT Plus+ account.
The style reference image is attached to the prompt; gpt-image-2 uses it as a
style guide.

Usage:
  python3 gen_image.py --prompt-file prompt.txt --style-ref assets/style_reference.png --out clip1.png
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# 세로 스타일(9:16 숏폼)도 지원한다. 기본은 16:9이므로 옵션을 주지 않으면
# 기존 호출과 완전히 동일하게 동작한다.
ORIENTATION = {"16:9": "landscape", "9:16": "vertical portrait"}

WRAPPER = """Use your built-in native image generation tool (NOT the imagegen skill, NOT any external API or API key). Generate ONE {aspect} {orientation} image and save the image file as {name} in the current working directory. Do nothing else — no extra files, no commentary beyond confirming the save.

The attached image is a master style sheet: use it for materials and visual language only. Never copy its board layout, its sample words, or the specific props and subjects shown in it — those are samples, not content for this frame.

Image prompt:
{prompt}"""


def main():
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--prompt")
    g.add_argument("--prompt-file")
    p.add_argument("--style-ref", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--aspect", default="16:9", choices=["16:9", "9:16"],
                   help="세로 스타일이면 9:16 (기본 16:9)")
    p.add_argument("--timeout", type=int, default=420)
    args = p.parse_args()

    prompt = args.prompt
    if args.prompt_file:
        with open(args.prompt_file, encoding="utf-8") as f:
            prompt = f.read().strip()

    style_ref = Path(args.style_ref).resolve()
    if not style_ref.is_file():
        sys.exit(f"스타일 참조 이미지가 없습니다: {style_ref}")
    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    codex = os.environ.get("CODEX_BIN", "codex")
    cmd = [
        codex, "exec",
        "--skip-git-repo-check",
        "-s", "workspace-write",
        "-C", str(out_path.parent),
        "-i", str(style_ref),
        # "--" 없이는 변수 개수 옵션인 -i가 프롬프트 인자까지 삼킨다
        "--",
        WRAPPER.format(name=out_path.name, prompt=prompt,
                       aspect=args.aspect, orientation=ORIENTATION[args.aspect]),
    ]

    last_err = None
    for attempt in range(2):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=args.timeout)
        except subprocess.TimeoutExpired:
            last_err = f"codex exec 타임아웃 ({args.timeout}s)"
            print(f"[image] {last_err} (시도 {attempt + 1})", file=sys.stderr)
            continue
        if out_path.is_file() and out_path.stat().st_size > 0:
            print(json.dumps({"out": str(out_path)}, ensure_ascii=False))
            return
        tail = (r.stdout + r.stderr)[-800:]
        last_err = f"이미지 파일이 생성되지 않음 (exit {r.returncode}): {tail}"
        print(f"[image] 실패 (시도 {attempt + 1}): {last_err}", file=sys.stderr)
    sys.exit(f"이미지 생성 실패: {last_err}\n"
             "확인: `codex login status`가 ChatGPT 로그인 상태인지, "
             "구독 사용량이 남아 있는지 점검하세요.")


if __name__ == "__main__":
    main()
