#!/usr/bin/env python3
"""gen_image.py의 첨부 순번·역할 자기검사.

참조 종류가 늘어날 때마다 "어느 첨부가 어느 역할인가"가 어긋난다.
2026-08-15 실측: 캐릭터 시트와 체인 프레임을 함께 넘기면 설명이 둘 다
"The NEXT attached image"로 나와 순번이 무너졌다 (제작대장의 이미지 G가
바로 그 조합이다). 그래서 조합마다 아래를 검사한다:

  1. 첨부(-i) 개수와 순서가 지정한 그대로인가
  2. 블록에 박힌 순번이 실제 첨부 위치와 맞는가
  3. 제품 문구가 제품 아닌 참조에 새지 않는가 (실사 렌더 승계의 원인)

codex를 실제로 부르지 않는다 — CODEX_BIN을 가짜 실행기로 바꿔 명령만 받아쓴다.
실행: python3 .claude/skills/vox-video/scripts/selftest_refs.py
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve()
GEN = HERE.parent / "gen_image.py"

FAKE = """#!/bin/sh
for a in "$@"; do printf "%s\\n" "$a"; done > "$ARGS_OUT"
exit 3
"""

# (설명, 옵션 조합, 기대 첨부 순서, 기대 블록 문구)
CASES = [
    ("스타일 시트만", [], ["style"], [("style", None)]),
    ("제품만 (기존 사용법)", ["--ref", "prod"], ["style", "prod"],
     [("style", None), ("REMAINING attached image(s) are identity references", None)]),
    ("캐릭터만", ["--ref-character", "cs"], ["style", "cs"],
     [("style", None), ("a character sheet for the person", 2)]),
    ("캐릭터+체인 (이미지 G 조합)",
     ["--ref-character", "cs", "--ref-chain", "chain"], ["style", "cs", "chain"],
     [("style", None), ("a character sheet for the person", 2),
      ("the frame that comes immediately before", 3)]),
    ("캐릭터+앵커 (이미지 K 조합)",
     ["--ref-character", "cs", "--ref-anchor", "anchor"], ["style", "cs", "anchor"],
     [("style", None), ("a character sheet for the person", 2),
      ("a composition anchor", 3)]),
    ("체인+제품 (이미지 N·M 조합)",
     ["--ref-chain", "chain", "--ref", "prod"], ["style", "chain", "prod"],
     [("style", None), ("the frame that comes immediately before", 2),
      ("REMAINING attached image(s) are identity references", None)]),
    ("전부",
     ["--ref-character", "cs", "--ref-chain", "chain", "--ref-anchor", "anchor",
      "--ref", "prod"], ["style", "cs", "chain", "anchor", "prod"],
     [("style", None), ("a character sheet for the person", 2),
      ("the frame that comes immediately before", 3),
      ("a composition anchor", 4),
      ("REMAINING attached image(s) are identity references", None)]),
]

# 제품 문구가 새면 안 되는 참조들 (실사 렌더·라벨 보존 지시가 인물에 걸린다)
PRODUCT_ONLY = "identity references for a real object"


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="selftest_refs_"))
    imgs = {}
    for name in ("style", "prod", "cs", "chain", "anchor"):
        p = tmp / f"{name}.png"
        p.write_bytes(b"\x89PNG\r\n\x1a\n")  # 존재만 확인하므로 헤더면 충분
        imgs[name] = p
    fake = tmp / "fakecodex"
    fake.write_text(FAKE)
    fake.chmod(0o755)
    args_out = tmp / "args.txt"

    failures = []
    for label, opts, want_order, want_blocks in CASES:
        cmd = [sys.executable, str(GEN), "--prompt", "STILL: selftest.",
               "--style-ref", str(imgs["style"]), "--out", str(tmp / "o.png"),
               "--timeout", "20"]
        for i, o in enumerate(opts):
            cmd.append(o if o.startswith("--") else str(imgs[o]))
        env = dict(os.environ, CODEX_BIN=str(fake), ARGS_OUT=str(args_out))
        if args_out.exists():
            args_out.unlink()
        subprocess.run(cmd, capture_output=True, text=True, env=env)
        if not args_out.exists():
            failures.append(f"{label}: 가짜 codex가 호출되지 않았다")
            continue
        got = args_out.read_text()
        lines = got.splitlines()

        # 1) 첨부 순서
        order = [Path(l).stem for l in lines if l.endswith(".png")]
        order = [o for o in order if o in imgs]
        if order != want_order:
            failures.append(f"{label}: 첨부 순서 {order} ≠ 기대 {want_order}")

        # 2) 블록 문구와 순번
        for phrase, pos in want_blocks:
            if phrase == "style":
                continue
            if phrase not in got:
                failures.append(f"{label}: 블록 없음 — {phrase[:40]}")
                continue
            if pos is not None:
                want = f"Attachment {pos} is"
                idx = got.find(phrase)
                head = got[max(0, idx - 30):idx]
                if want not in head:
                    failures.append(
                        f"{label}: '{phrase[:32]}'의 순번이 틀렸다 — "
                        f"기대 '{want}', 실제 '{head.strip()[-24:]}'")

        # 3) 제품 문구 유출
        if "--ref" not in opts and PRODUCT_ONLY in got:
            failures.append(f"{label}: 제품 문구가 제품 아닌 참조에 붙었다")

    for label, *_ in CASES:
        pass
    if failures:
        print("실패:")
        for f in failures:
            print("  -", f)
        return 1
    print(f"통과: {len(CASES)}개 조합 — 첨부 순서·블록 순번·제품 문구 격리 모두 정상")
    return 0


if __name__ == "__main__":
    sys.exit(main())
