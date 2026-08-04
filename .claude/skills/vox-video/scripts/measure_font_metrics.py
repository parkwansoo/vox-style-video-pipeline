#!/usr/bin/env python3
"""자막 폰트의 글자 폭을 실측해 caption-font-metrics.json을 만든다.

자막은 한 줄로 강제되므로(make_captions.mjs) 조각 길이를 렌더 폭으로 재야
하는데, 폰트마다 한글·공백·구두점의 폭이 다르다. 카탈로그의 폰트 파일을
전부 측정해 폰트 키별 메트릭을 기록한다. 폰트를 추가·교체하면 재실행한다.

사용법: .venv/bin/python3 measure_font_metrics.py
"""
import json
import re
import string
from pathlib import Path

from PIL import ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
FONTS_DIR = ROOT / "subtitler" / "public" / "_fonts"
CATALOG = ROOT / "subtitler" / "src" / "font-catalog.mjs"
OUT = HERE / "caption-font-metrics.json"

EM = 1000  # 측정 기준 크기(px) = unitsPerEm 환산 단위
EXTRA = "·…—–‘’“”₂℮°±×÷≤≥"


def parse_catalog():
    """font-catalog.mjs에서 {한글 키: 파일명} 매핑을 뽑는다."""
    text = CATALOG.read_text(encoding="utf-8")
    pairs = re.findall(r"'([^']+)':\s*\{family:\s*'[^']+',\s*file:\s*'([^']+)'\}", text)
    if not pairs:
        raise SystemExit(f"카탈로그 파싱 실패: {CATALOG}")
    return dict(pairs)


def measure(path):
    f = ImageFont.truetype(str(path), EM)
    chars = {}
    for ch in string.printable[:95] + EXTRA:
        if ch.strip() or ch == " ":
            chars[ch] = round(f.getlength(ch))
    return {
        "file": path.name,
        "unitsPerEm": EM,
        "hangul": round(f.getlength("가")),
        "space": round(f.getlength(" ")),
        "chars": chars,
    }


def main():
    catalog = parse_catalog()
    out, missing = {}, []
    for key, filename in catalog.items():
        path = FONTS_DIR / filename
        if not path.is_file():
            missing.append(f"{key} ({filename})")
            continue
        m = measure(path)
        if m["hangul"] <= 0:  # 한글 글리프 없는 폰트(Helvetica 등) 방어
            m["hangul"] = EM
        out[key] = m
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{OUT.name}: {len(out)}종 측정 완료" + (f", 파일 없음 {missing}" if missing else ""))


if __name__ == "__main__":
    main()
