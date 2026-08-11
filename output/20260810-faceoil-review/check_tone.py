#!/usr/bin/env python3
"""identity ref 컷의 색감 드리프트 검증 — clip1(정본)과 후보를 수치로 비교한다.

근거 사건: clip1 v5(2026-08-10)가 identity ref를 붙이자 배경 채도가 밀려
폐기됐고, 기미 편 ch2에서도 인물 피부톤이 컷마다 미세하게 흔들렸다. 프레임
시트·눈검수로는 이 미세 이탈을 못 잡아 수치 검증을 둔다.

측정 대상은 둘뿐이다:
  배경 — 시클로라마 파랑. 모든 컷에서 같아야 하므로 비교가 항상 유효하다.
  피부 — 살색 범위 픽셀만 골라 잰다. 얼굴이 프레임을 차지하는 비율이 컷마다
         달라도 톤 자체는 비교할 수 있다.

피사체 전체 평균(옷·소품·머리 포함)은 쓰지 않는다. 초판이 그렇게 쟀다가
광대 초근접(clip11b_first)·회색 셔츠(clip14)·파운데이션(clip12a) 같은 정상
컷을 전부 FAIL로 찍었다 — 컷 내용의 차이를 드리프트로 오인한 것이다.

사용:
  .venv/bin/python3 output/20260810-faceoil-review/check_tone.py ch1/clip4.png [...]
  --verbose 를 붙이면 원시값도 출력한다
"""
import sys
import colorsys
from pathlib import Path

from PIL import Image

RUN = Path(__file__).parent
CANON = RUN / "ch1" / "clip1.png"

# 임계값 — clip1 v4(정본)·clip4(재추첨 통과본) vs v5(폐기본) 실측으로 보정
TH_BG_HUE = 3.0      # 도(°)
TH_BG_SAT = 6.0      # %p
TH_SKIN_HUE = 3.0    # 도(°)
TH_SKIN_SAT = 8.0    # %p — 기미·파운데이션이 살색 범위에 들어가 채도를 올린다 (clip4 Δ6.1 정상)
TH_SKIN_VAL = 10.0   # %p

MIN_PIXELS = 300     # 이보다 적으면 그 항목은 판정하지 않는다


def stats(path):
    im = Image.open(path).convert("RGB")
    im.thumbnail((280, 280 * 16 // 9))
    bg = []
    skin = []
    for r, g, b in im.getdata():
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        if 0.50 < h < 0.72 and s > 0.25:                       # 시클로라마 파랑
            bg.append((h, s, v))
        elif 0.02 < h < 0.13 and 0.15 < s < 0.65 and v > 0.35:  # 살색
            skin.append((h, s, v))
    out = {}
    if len(bg) >= MIN_PIXELS:
        out["bg_hue"] = sum(x[0] for x in bg) / len(bg) * 360
        out["bg_sat"] = sum(x[1] for x in bg) / len(bg) * 100
    if len(skin) >= MIN_PIXELS:
        out["skin_hue"] = sum(x[0] for x in skin) / len(skin) * 360
        out["skin_sat"] = sum(x[1] for x in skin) / len(skin) * 100
        out["skin_val"] = sum(x[2] for x in skin) / len(skin) * 100
    out["_n"] = (len(bg), len(skin))
    return out


CHECKS = [
    ("bg_hue", TH_BG_HUE, "°"),
    ("bg_sat", TH_BG_SAT, "%p"),
    ("skin_hue", TH_SKIN_HUE, "°"),
    ("skin_sat", TH_SKIN_SAT, "%p"),
    ("skin_val", TH_SKIN_VAL, "%p"),
]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    verbose = "--verbose" in sys.argv
    if not args:
        sys.exit(__doc__)
    canon = stats(CANON)
    print(f"정본 {CANON.name}: " + " · ".join(
        f"{k} {canon[k]:.1f}" for k, _, _ in CHECKS if k in canon) + "\n")
    failed = []
    for a in args:
        p = Path(a) if Path(a).is_absolute() else RUN / a
        s = stats(p)
        parts, bad = [], []
        for key, th, unit in CHECKS:
            if key not in s or key not in canon:
                parts.append(f"{key} —")
                continue
            d = abs(s[key] - canon[key])
            parts.append(f"{key} Δ{d:.1f}{unit}")
            if d > th:
                bad.append(f"{key} Δ{d:.1f}{unit}>{th}{unit}")
        mark = "FAIL" if bad else "ok"
        line = f"{mark:4s} {p.name:22s} " + " · ".join(parts)
        if verbose:
            line += f"   [bg={s['_n'][0]} skin={s['_n'][1]}]"
        print(line + (f"\n     ← {', '.join(bad)}" if bad else ""))
        if bad:
            failed.append(p.name)
    if failed:
        sys.exit(f"\n색감 이탈 {len(failed)}건: {', '.join(failed)}")
    print("\n전부 통과")


if __name__ == "__main__":
    main()
