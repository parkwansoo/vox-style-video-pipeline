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
REVISE_TMPL = """{who} the previous render of this exact frame. Treat it as the composition reference: keep its camera angle, framing, subject placement, scale, silhouette and overall layout unchanged — this is a re-render of the same shot, not a new scene. Where the style sheet and this previous render disagree with the image prompt below, the image prompt wins: change exactly what it asks to change and leave everything else as it is."""

# 캐릭터 시트. 제품용(아래 REFS_BLOCK)을 그대로 쓰면 시트가 "실물 사물"이 되고
# "재질을 그대로 유지하라"가 실사 렌더 보존 명령이 된다 — 2026-08-14 A·D·F1
# 실사화의 원인.
CHARACTER_TMPL = """{who} a character sheet for the person in this frame. Take ONLY their identity from it - face, hairstyle, body proportions and age. Do NOT take its rendering, lighting, grid layout, panel arrangement, backdrop, framing, or the expressions and poses of panels other than the one this prompt names. It is a reference sheet, not a photograph of a real object: render the person fresh in the style sheet's visual language."""

# 체인 프레임(앞 클립의 마지막 프레임, 또는 쌍의 first). 세계를 승계한다.
#
# 2026-08-15: `same lighting`과 `the same state of anything carried over`를
# 뺐다. 이 래퍼는 **모든 체인 컷에 자동으로 붙는데** 조명·상태는 컷마다
# 다르다 — 6쌍 전수 대조에서 location 6/6·materials 6/6이 같은 반면,
# lighting은 2쌍(I→N, L→M)이 다르고 state는 **1쌍(L→M)만** 같았다.
# 체인은 "시간이 흐른 다음 프레임"이라 상태가 진행하는 것이 정상이고,
# `same state`는 체인의 본질과 모순이었다. 씬 13 M의 "L보다 조명을 더
# 강하게"와는 정면으로 싸웠다.
# 지난 편은 조명 승계를 컷마다 손으로 판단했다(clip17·clip9b의 SCENE MATCH).
# 래퍼는 그럴 수 없으므로 **항상 참인 것만** 말하고, 컷마다 다른 것은
# 본문 SCENE MATCH/CONTINUITY 블록이 말한다.
# 지우기만 하면 부족하다 — ref는 침묵한 속성을 끌고 온다(2026-08-12 표정
# 실측, pipeline-rules 7절). 그래서 조명·상태를 **명시적 제외 목록**에 넣었다.
CHAIN_TMPL = """{who} the frame that comes immediately before this one in the film. Keep the world continuous with it - same location, same materials. It is a starting point, not a composition to copy: this frame's camera, framing, subject placement, lighting and the state of everything in it are set by the image prompt below."""

# 구도 앵커. 각도·크롭·거리만 가져오고 조명·상태·표정은 명시적으로 버린다.
# 체인과 섞으면 안 된다 — 대구 컷(G→K)은 각도는 같고 조명·상태는 반대다.
ANCHOR_TMPL = """{who} a composition anchor from an earlier frame in this film. Take ONLY its camera geometry - the angle, the crop, the distance to the subject and where the subject sits in the frame - so this frame reads as its counterpart. Do NOT take its lighting, colour, mood, or the state and expression of the subject; those are defined by the image prompt below and are deliberately different from the anchor."""

# 제품 등 정체성 레퍼런스. 제품은 항상 마지막에 붙으므로 REMAINING이 어떤
# 조합에서도 성립한다 (이 문구는 검증된 원문이라 손대지 않는다).
REFS_BLOCK = """The REMAINING attached image(s) are identity references for a real object that must appear in this frame. Keep each one's recognizable shape, proportions, colour, material and label layout exactly as shown, but render it in the style sheet's visual language rather than copying its original lighting or background. Do not redesign it, do not restyle its label, and do not invent extra text on it."""


def _who(start, count):
    """첨부 순번을 실제 위치로 박는다. 종류가 여럿일 때 'NEXT'를 반복하면
    어느 이미지인지 무너진다 (2026-08-15 실측: 캐릭터+체인 동시 사용 시
    NEXT가 두 번 나왔다)."""
    if count == 1:
        return f"Attachment {start} is"
    return f"Attachments {start}-{start + count - 1} are"

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
                   help="제품 등 실물 정체성 레퍼런스 (반복 지정 가능)")
    # 참조 종류를 나눈다 — 종류마다 첨부 설명이 다르다. 제품용 문구를 캐릭터
    # 시트에 쓰면 시트의 실사 렌더가 그대로 승계된다 (2026-08-14 실측).
    p.add_argument("--ref-character", action="append", default=[], metavar="PATH",
                   help="캐릭터 시트 — 정체성만 가져오고 렌더·그리드·배경은 제외")
    p.add_argument("--ref-chain", action="append", default=[], metavar="PATH",
                   help="직전 프레임(체인·쌍의 first) — 시간 연속성을 가져온다")
    p.add_argument("--ref-anchor", action="append", default=[], metavar="PATH",
                   help="구도 앵커 — 각도·크롭·거리만. 조명·상태·표정은 제외")
    p.add_argument("--revise", metavar="PATH",
                   help="이전 렌더본. 구도를 유지한 채 프롬프트가 지시한 부분만 고쳐 다시 그린다")
    p.add_argument("--out", required=True)
    p.add_argument("--aspect", default="16:9", choices=["16:9", "9:16"],
                   help="세로 스타일이면 9:16 (기본 16:9)")
    # 실측(stdin 수정 후): 한 장에 약 60초. 420초면 7배 여유다.
    p.add_argument("--model", default="",
                   help="codex 모델. 빈 문자열이면 ~/.codex/config.toml 기본값 사용")
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
    def _resolve(paths, label):
        out = []
        for raw in paths:
            ref = Path(raw).resolve()
            if not ref.is_file():
                sys.exit(f"{label} 이미지가 없습니다: {ref}")
            out.append(ref)
        return out

    char_refs = _resolve(args.ref_character, "캐릭터 시트 참조")
    chain_refs = _resolve(args.ref_chain, "직전 프레임 참조")
    anchor_refs = _resolve(args.ref_anchor, "구도 앵커 참조")
    extra_refs = _resolve(args.ref, "추가 참조")
    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # 항상 새 임시 이름으로 생성한 뒤 옮긴다. 목표 파일이 이미 있으면 codex가
    # "이미 있으니 됐다"며 크기만 확인하고 생성을 건너뛴다(재생성이 조용히 무시된다).
    # 점으로 시작하는 숨김 이름을 쓰면 codex가 저장 후 rg로 확인할 때 찾지 못해
    # 헤맨다(rg는 기본적으로 숨김 파일을 건너뛴다). 반드시 보이는 이름을 쓴다.
    tmp_path = out_path.parent / f"{out_path.stem}__gen{uuid.uuid4().hex[:8]}.png"

    codex = os.environ.get("CODEX_BIN", "codex")
    if revise_ref or char_refs or chain_refs or anchor_refs or extra_refs:
        # 블록 순서 = 첨부 순서이고, 각 블록에 실제 첨부 순번을 박는다.
        # 제품은 항상 마지막이라 REFS_BLOCK의 "REMAINING"이 어떤 조합에서도 맞는다.
        blocks = [STYLE_HEAD_MULTI]
        pos = 2  # 1번은 스타일 시트
        for group, tmpl in ((([revise_ref] if revise_ref else []), REVISE_TMPL),
                            (char_refs, CHARACTER_TMPL),
                            (chain_refs, CHAIN_TMPL),
                            (anchor_refs, ANCHOR_TMPL)):
            if group:
                blocks.append(tmpl.format(who=_who(pos, len(group))))
                pos += len(group)
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
           "-C", str(out_path.parent)]
    # --model을 주면 ~/.codex/config.toml의 기본 모델 대신 그 값을 쓴다(개인 설정 불변).
    # 2026-08-12: config 기본 모델이 ChatGPT 계정에서 400 not supported를 내 21장이
    # 실패한 사건이 있었다. 다만 그때는 어떤 모델을 지정해도 같은 에러라 계정 문제였다.
    if args.model:
        cmd += ["-m", args.model]
    cmd += ["-i", str(style_ref)]
    # 첨부 순서가 곧 블록의 순번이다 — 시트(1), 이전 렌더본, 캐릭터 시트,
    # 직전 프레임, 구도 앵커, 제품(항상 마지막). 위 블록 조립과 같은 순서.
    if revise_ref:
        cmd += ["-i", str(revise_ref)]
    for ref in char_refs + chain_refs + anchor_refs + extra_refs:
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
