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
import uuid
from pathlib import Path

# 세로 스타일(9:16 숏폼)도 지원한다. 기본은 16:9이므로 옵션을 주지 않으면
# 기존 호출과 완전히 동일하게 동작한다.
ORIENTATION = {"16:9": "landscape", "9:16": "vertical portrait"}

HEADER = """Use your built-in native image generation tool (NOT the imagegen skill, NOT any external API or API key). Generate ONE {aspect} {orientation} image and save the image file as {name} in the current working directory. Do nothing else — no extra files, no commentary beyond confirming the save."""

# 첨부가 스타일 시트 한 장일 때 (기본)
ATTACH_STYLE_ONLY = """The attached image is a master style sheet: use it for materials and visual language only. Never copy its board layout, its sample words, or the specific props and subjects shown in it — those are samples, not content for this frame."""

# 첨부가 여럿일 때 공통으로 오는 스타일 시트 설명
STYLE_HEAD_MULTI = """The FIRST attached image is a master style sheet: use it for materials and visual language only. Never copy its board layout, its sample words, or the specific props and subjects shown in it — those are samples, not content for this frame."""

# --revise: 같은 컷을 다시 렌더할 때. 구도를 붙잡아 두고 재질·색만 고친다.
# 새로 생성하면 구도가 매번 달라져 이미 통과한 화면 배치를 잃는다.
REVISE_BLOCK = """The NEXT attached image is the previous render of this exact frame. Treat it as the composition reference: keep its camera angle, framing, subject placement, scale, silhouette and overall layout unchanged — this is a re-render of the same shot, not a new scene. Where the style sheet and this previous render disagree with the image prompt below, the image prompt wins: change exactly what it asks to change and leave everything else as it is."""

# 제품 등 정체성 레퍼런스
REFS_BLOCK = """The REMAINING attached image(s) are identity references for a real object that must appear in this frame. Keep each one's recognizable shape, proportions, colour, material and label layout exactly as shown, but render it in the style sheet's visual language rather than copying its original lighting or background. Do not redesign it, do not restyle its label, and do not invent extra text on it."""

WRAPPER = """{header}

{attach}

Image prompt:
{prompt}"""


def main():
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--prompt")
    g.add_argument("--prompt-file")
    p.add_argument("--style-ref", required=True)
    # 제품 등 추가 정체성 레퍼런스. 여러 번 줄 수 있고, 안 주면 기존과 동일하게 동작한다.
    p.add_argument("--ref", action="append", default=[], metavar="PATH",
                   help="스타일 시트 외 추가 참조 이미지 (반복 지정 가능)")
    p.add_argument("--revise", metavar="PATH",
                   help="이전 렌더본. 구도를 유지한 채 프롬프트가 지시한 부분만 고쳐 다시 그린다")
    p.add_argument("--out", required=True)
    p.add_argument("--aspect", default="16:9", choices=["16:9", "9:16"],
                   help="세로 스타일이면 9:16 (기본 16:9)")
    # 실측(stdin 수정 후): 한 장에 약 60초. 420초면 7배 여유다.
    p.add_argument("--timeout", type=int, default=420)
    args = p.parse_args()

    prompt = args.prompt
    if args.prompt_file:
        with open(args.prompt_file, encoding="utf-8") as f:
            prompt = f.read().strip()

    style_ref = Path(args.style_ref).resolve()
    if not style_ref.is_file():
        sys.exit(f"스타일 참조 이미지가 없습니다: {style_ref}")
    revise_ref = None
    if args.revise:
        revise_ref = Path(args.revise).resolve()
        if not revise_ref.is_file():
            sys.exit(f"이전 렌더본이 없습니다: {revise_ref}")
    extra_refs = []
    for raw in args.ref:
        ref = Path(raw).resolve()
        if not ref.is_file():
            sys.exit(f"추가 참조 이미지가 없습니다: {ref}")
        extra_refs.append(ref)
    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # 항상 새 임시 이름으로 생성한 뒤 옮긴다. 목표 파일이 이미 있으면 codex가
    # "이미 있으니 됐다"며 크기만 확인하고 생성을 건너뛴다(재생성이 조용히 무시된다).
    # 점으로 시작하는 숨김 이름을 쓰면 codex가 저장 후 rg로 확인할 때 찾지 못해
    # 헤맨다(rg는 기본적으로 숨김 파일을 건너뛴다). 반드시 보이는 이름을 쓴다.
    tmp_path = out_path.parent / f"{out_path.stem}__gen{uuid.uuid4().hex[:8]}.png"

    codex = os.environ.get("CODEX_BIN", "codex")
    if revise_ref or extra_refs:
        blocks = [STYLE_HEAD_MULTI]
        if revise_ref:
            blocks.append(REVISE_BLOCK)
        if extra_refs:
            blocks.append(REFS_BLOCK)
        attach = "\n\n".join(blocks)
    else:
        attach = ATTACH_STYLE_ONLY
    wrapped = WRAPPER.format(
        header=HEADER.format(name=tmp_path.name, aspect=args.aspect,
                             orientation=ORIENTATION[args.aspect]),
        attach=attach,
        prompt=prompt,
    )
    cmd = [codex, "exec", "--skip-git-repo-check", "-s", "workspace-write",
           "-C", str(out_path.parent), "-i", str(style_ref)]
    # 첨부 순서가 곧 프롬프트의 FIRST/NEXT/REMAINING이다 — 시트, 이전 렌더본, 정체성 레퍼런스
    if revise_ref:
        cmd += ["-i", str(revise_ref)]
    for ref in extra_refs:
        cmd += ["-i", str(ref)]
    # "--" 없이는 변수 개수 옵션인 -i가 프롬프트 인자까지 삼킨다
    cmd += ["--", wrapped]

    last_err = None
    for attempt in range(2):
        try:
            # stdin을 반드시 닫는다. 열려 있으면 codex exec가
            # "Reading additional input from stdin..."에서 무한 대기하다 타임아웃난다.
            # 동시 실행 시엔 자식들이 같은 stdin을 공유해 하나만 통과하는 현상이 생긴다.
            r = subprocess.run(cmd, capture_output=True, text=True,
                               timeout=args.timeout, stdin=subprocess.DEVNULL)
        except subprocess.TimeoutExpired:
            last_err = f"codex exec 타임아웃 ({args.timeout}s)"
            print(f"[image] {last_err} (시도 {attempt + 1})", file=sys.stderr)
            continue
        if tmp_path.is_file() and tmp_path.stat().st_size > 0:
            os.replace(tmp_path, out_path)
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
