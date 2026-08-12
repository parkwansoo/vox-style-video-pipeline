#!/usr/bin/env python3
"""두 프레임(2F) 쌍의 제품 실루엣 일관성 검증.

first/end를 독립 생성하면 병 비율이 쌍 안에서 벌어진다 (2026-08-12 실측:
clip17 1.65→2.49). 육안은 최악 쌍도 놓쳤으므로 수치로 잰다.

판정: 노란 오일+금색 칼라 마스크의 bbox로 세로:가로 비율과 화면 내 높이를
비교한다. aspect 차 > 0.15 → FAIL. size_same 쌍은 높이비가 0.85~1.15를
벗어나면 FAIL (size_free 쌍은 높이 자유 — 카메라 접근 컷).

한계 (2026-08-12 실측): 기울어진 병(first)과 세워진 병(end)을 비교하면 bbox
aspect가 왜곡된다 — clip3 쌍이 육안으로는 일치하는데 Δ0.30으로 FAIL했다.
기울기가 다른 쌍은 FAIL이 떠도 반드시 육안으로 재판정한다 (CLAUDE.md 규율 ⑤).

사용: .venv/bin/python3 output/20260810-faceoil-review/check_pair.py
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

RUN = Path(__file__).parent / "ch1"

# (first, end, 크기 규칙)
PAIRS = [
    ("clip3_first", "clip3_end", "size_same"),
    ("clip6b_first", "clip6b_end", "size_same"),
    ("clip17_first", "clip17_end", "size_free"),
]

TH_ASPECT = 0.15
TH_HEIGHT = (0.85, 1.15)


def bottle_box(name):
    p = RUN / f"{name}.png"
    a = np.asarray(Image.open(p).convert("RGB")).astype(int)
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    m = (r > 120) & (g > 100) & (b < r - 40) & (b < g - 20)   # 노란 오일·금색
    ys, xs = np.nonzero(m)
    if len(ys) < 500:
        return None
    h = int(ys.max() - ys.min()); w = int(xs.max() - xs.min())
    return h, w, h / w


def main():
    failed = []
    for f, e, rule in PAIRS:
        bf, be = bottle_box(f), bottle_box(e)
        if not bf or not be:
            print(f"SKIP {f}↔{e}: 마스크 부족"); continue
        d_aspect = abs(bf[2] - be[2])
        h_ratio = be[0] / bf[0]
        bad = []
        if d_aspect > TH_ASPECT:
            bad.append(f"aspect {bf[2]:.2f}→{be[2]:.2f} (Δ{d_aspect:.2f}>{TH_ASPECT})")
        if rule == "size_same" and not (TH_HEIGHT[0] <= h_ratio <= TH_HEIGHT[1]):
            bad.append(f"높이비 {h_ratio:.2f} (허용 {TH_HEIGHT[0]}~{TH_HEIGHT[1]})")
        mark = "FAIL" if bad else "ok"
        print(f"{mark:4s} {f}↔{e}  aspect {bf[2]:.2f}/{be[2]:.2f} · 높이비 {h_ratio:.2f}"
              + (f"  ← {', '.join(bad)}" if bad else ""))
        if bad:
            failed.append(f"{f}↔{e}")
    if failed:
        sys.exit(f"\n쌍 불일치 {len(failed)}건: {', '.join(failed)}")
    print("\n전부 통과")


if __name__ == "__main__":
    main()
