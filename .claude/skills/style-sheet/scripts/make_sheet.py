#!/usr/bin/env python3
"""Assemble a style-sheet prompt from a style DNA JSON, and optionally render it.

The 11-slot skeleton lives here as one format string so the wording stays
identical across runs — only the slot values change. See
references/slot-template.md for what each slot must contain.

Usage:
  # prompt only
  python3 make_sheet.py --dna assets/style_dna.json --out-prompt assets/style_prompt.txt
  # prompt + render the sheet via Codex (ChatGPT subscription, no API key)
  python3 make_sheet.py --dna assets/style_dna.json --out-prompt assets/style_prompt.txt \
      --render assets/style_reference.png
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

TEMPLATE = """MASTER STYLE SHEET - {system_name} visual system, one 16:9 reference board. A single polished art-direction sheet defining the visual language for a {series_type} explainer series. Editorial grid, consistent margins, section labels. Baked-in typography is intentional here (this is a style guide).
{subjects}
SURFACE & MOOD: {surface}. Mood: {mood}.

TYPE SPECIMEN PANEL: {type_specimen}. Typography {type_quality}, no warped letters.

PALETTE STRIP: labeled swatches - {palette}. {color_rules}.

COMPONENT ZOO PANEL: {components}. All share one construction logic: {construction_logic}.

MINI-SCENE PANEL: 3 small example frames - (a) {scene_a}, (b) {scene_b}, (c) {scene_c}. Same lighting and finish throughout.

MOTION THUMBNAILS: 4 tiny storyboard frames with arrows only: {motion}.
{stage}
FINISH: {finish}. No watermarks, no lorem ipsum, no unrelated logos, no random gibberish text - every visible word is one of the samples above."""

STAGE_LINE = ("\nOne panel shows THE STAGE: {stage}. "
              "No midground elements present in this panel.\n")

# 선택 입력. 사용자가 주제를 주면 이 한 줄만 끼고, 없으면 기존과 동일하다.
SUBJECTS_LINE = "\nSUBJECT THEMES: the sample subjects on this sheet relate to {subjects}.\n"

RENDER_WRAPPER = """Use your built-in native image generation tool (NOT the imagegen skill, NOT any external API or API key). Generate ONE 16:9 landscape image and save the image file as {name} in the current working directory. Do nothing else.

This is a single art-direction reference board — a style guide sheet with labelled panels, not a scene illustration. Render every panel and every labelled swatch described below, and print the sample words exactly as written.

{prompt}"""

REQUIRED = [
    "system_name", "series_type", "surface", "mood", "type_specimen",
    "type_quality", "palette", "color_rules", "components",
    "construction_logic", "mini_scenes", "motion_signature", "finish",
]


def join_list(value, sep=", "):
    return sep.join(value) if isinstance(value, (list, tuple)) else str(value)


def format_palette(palette):
    """[{name, hex}] → 'Archival Tan #C9BB9C, Ink Black #1A1A1A'"""
    if isinstance(palette, str):
        return palette
    parts = []
    for c in palette:
        if isinstance(c, dict):
            name, hex_ = c.get("name", "").strip(), c.get("hex", "").strip()
            parts.append(f"{name} {hex_}".strip())
        else:
            parts.append(str(c))
    return ", ".join(p for p in parts if p)


# 기존 3종(MG-SOFT3D 1782 / MG-BLUEPRINT 1885 / Vox 2258)의 실측 범위.
# 크게 넘으면 시트가 아니라 설명서가 되고 있다는 신호다.
LENGTH_CEILING = 2400


def lint(dna, prompt):
    """Warn about the drift modes that make a sheet balloon into prose."""
    warn = []
    palette = dna.get("palette")
    if isinstance(palette, list) and len(palette) > 5:
        warn.append(f"팔레트가 {len(palette)}색입니다 (권장 2~5). "
                    "명도만 다른 인접 색은 대표색으로 병합하세요.")
    if "mood" in str(dna.get("surface", "")).lower():
        warn.append("surface에 'Mood'가 들어 있습니다 — 템플릿이 Mood를 따로 붙이므로 "
                    "출력에 중복됩니다. surface에서 빼세요.")
    for key in ("components", "mini_scenes", "finish"):
        val = dna.get(key)
        if isinstance(val, list):
            longest = max((len(str(v)) for v in val), default=0)
            if longest > 90:
                warn.append(f"{key}의 한 항목이 {longest}자입니다 — 기존 시트는 짧은 "
                            "명사구입니다. 설명문이 되지 않게 줄이세요.")
    if len(prompt) > LENGTH_CEILING:
        warn.append(f"프롬프트가 {len(prompt)}자입니다 (기존 3종은 1782~2258자). "
                    "슬롯을 더 압축하세요.")
    for w in warn:
        print(f"[경고] {w}", file=sys.stderr)
    return warn


def build_prompt(dna, subjects=None):
    missing = [k for k in REQUIRED if not dna.get(k)]
    if missing:
        sys.exit(f"style DNA에 필수 항목이 없습니다: {', '.join(missing)}\n"
                 "references/slot-template.md의 슬롯을 모두 채우세요.")

    scenes = dna["mini_scenes"]
    if len(scenes) < 3:
        sys.exit("mini_scenes는 3개여야 합니다.")
    motion = dna["motion_signature"]
    if len(motion) < 4:
        sys.exit("motion_signature는 4개여야 합니다.")

    stage = dna.get("stage")
    return TEMPLATE.format(
        subjects=SUBJECTS_LINE.format(subjects=subjects.rstrip(".")) if subjects else "",
        system_name=dna["system_name"],
        series_type=dna["series_type"],
        surface=dna["surface"],
        mood=join_list(dna["mood"]),
        type_specimen=dna["type_specimen"],
        type_quality=join_list(dna["type_quality"]),
        palette=format_palette(dna["palette"]),
        color_rules=dna["color_rules"].rstrip("."),
        components=join_list(dna["components"], "; "),
        construction_logic=dna["construction_logic"].rstrip("."),
        scene_a=scenes[0], scene_b=scenes[1], scene_c=scenes[2],
        motion=join_list(motion, " / "),
        stage=STAGE_LINE.format(stage=stage.rstrip(".")) if stage else "",
        finish=join_list(dna["finish"]).rstrip("."),
    )


def render(prompt, out_path, timeout=600):
    """Render the sheet with Codex's built-in image generation (subscription OAuth)."""
    out_path = Path(out_path).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    codex = os.environ.get("CODEX_BIN", "codex")
    cmd = [
        codex, "exec", "--skip-git-repo-check", "-s", "workspace-write",
        "-C", str(out_path.parent), "--",
        RENDER_WRAPPER.format(name=out_path.name, prompt=prompt),
    ]
    last = None
    for attempt in range(2):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            last = f"codex exec 타임아웃 ({timeout}s)"
            print(f"[sheet] {last} (시도 {attempt + 1})", file=sys.stderr)
            continue
        if out_path.is_file() and out_path.stat().st_size > 0:
            return str(out_path)
        last = f"이미지가 생성되지 않음 (exit {r.returncode}): {(r.stdout + r.stderr)[-500:]}"
        print(f"[sheet] 실패 (시도 {attempt + 1}): {last}", file=sys.stderr)
    sys.exit(f"스타일 시트 렌더 실패: {last}\n"
             "`codex login status`가 ChatGPT 로그인 상태인지 확인하세요.")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dna", required=True, help="style DNA JSON")
    p.add_argument("--out-prompt", help="조립된 프롬프트를 저장할 경로")
    p.add_argument("--render", help="이 경로로 스타일 시트 이미지를 생성")
    p.add_argument("--subjects", help="시트 샘플 소재의 주제 (선택). 없으면 자유 생성")
    args = p.parse_args()

    dna = json.loads(Path(args.dna).read_text(encoding="utf-8"))
    prompt = build_prompt(dna, subjects=args.subjects)
    # 길이 검사는 DNA 슬롯 부풀림을 잡는 용도이므로 주제 줄은 빼고 잰다
    warnings = lint(dna, build_prompt(dna) if args.subjects else prompt)

    if args.out_prompt:
        Path(args.out_prompt).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_prompt).write_text(prompt + "\n", encoding="utf-8")
    else:
        print(prompt)

    result = {"prompt_chars": len(prompt), "warnings": len(warnings)}
    if args.out_prompt:
        result["prompt"] = args.out_prompt
    if args.render:
        result["sheet"] = render(prompt, args.render)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
