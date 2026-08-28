#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""비율 산출물 우하단에 고지 문구를 얹는다 — "보일랑 말랑" 세기로.

파이프라인 9.5단계. export_ratios.py가 만든 `exports/final_<slug>.mp4`를 읽어
`exports/final_<slug>_고지.mp4`를 만든다. 원본은 고치지 않는다.

왜 필요한가: 광고 심의(구글애즈·국내 표시광고법)에서 개인차 고지가 없으면
걸린다. 다만 시청자 시선을 끌면 광고 효과가 깎이므로 **읽히되 튀지 않는**
세기가 요구사항이다. 비율마다 배경 조건이 달라 값이 다르다 —
근거는 config/disclaimer.json 주석에 있다.

  ① 문구 그리기  PIL로 투명 PNG를 만든다 (ffmpeg drawtext는 이 빌드에 없다).
                 그림자는 배경만 눌러 대비를 만든다 — 글자를 밝히지 않는다.
  ② 합성         ffmpeg overlay. 영상만 재인코딩하고 오디오는 복사한다.
  ③ 검증         오디오 스트림이 원본과 같은지 실측하고, --check면 비율×시점
                 우하단을 1:1로 잘라 붙인 시트를 만든다 (눈으로 봐야 한다).

사용법:
  .venv/bin/python3 .claude/skills/vox-video/scripts/add_disclaimer.py \
      --run output/20260826-vgshot-ampoule --check

  # 일부 비율만
  ... --ratios 4:5,1:1
  # 문구를 이 편에서만 다르게
  ... --text "*연출된 화면입니다."
  # 값 튜닝 — 렌더 없이 견본 한 장만
  ... --sample-only
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
PROJECT = SKILL.parent.parent.parent
CONFIG = SKILL / "config" / "disclaimer.json"
RATIOS_CONFIG = SKILL / "config" / "video-ratios.json"


def die(msg: str) -> None:
    print(f"[실패] {msg}", file=sys.stderr)
    sys.exit(1)


def run(cmd, *, label=""):
    """에러를 삼키지 않는다 (CLAUDE.md 규율 ⑤)."""
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stdout)
        sys.stderr.write(r.stderr)
        die(f"{label or cmd[0]} 실패 (exit {r.returncode})")
    return r.stdout


def probe(path: Path, entries: str, stream: str | None = None) -> str:
    cmd = ["ffprobe", "-v", "error"]
    if stream:
        cmd += ["-select_streams", stream]
    cmd += ["-show_entries", entries, "-of", "csv=p=0", str(path)]
    return run(cmd, label="ffprobe").strip()


def hex_rgb(s: str) -> tuple[int, int, int]:
    s = s.lstrip("#")
    if len(s) != 6:
        die(f"색 형식이 #RRGGBB가 아니다: {s}")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def draw_text_png(text, font_path, size, rgb, alpha, sh_alpha, sh_blur, sh_off, out: Path):
    """문구를 투명 PNG로 그린다.

    그림자 번짐이 잘리지 않게 여백(pad)을 두는데, 그 여백만큼 PNG가 커지므로
    overlay 좌표를 그대로 쓰면 문구가 여백만큼 안쪽으로 밀린다. pad를 함께
    돌려주어 호출부가 상쇄한다 — config의 여백은 **글자 실제 가장자리** 기준이다.

    반환: (PNG 폭, PNG 높이, pad, 글자 폭, 글자 높이).
    """
    from PIL import Image, ImageDraw, ImageFont, ImageFilter

    font = ImageFont.truetype(str(font_path), size)
    probe_d = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
    x0, y0, x1, y1 = probe_d.textbbox((0, 0), text, font=font)
    gw, gh = x1 - x0, y1 - y0
    pad = max(4, int(round(sh_blur * 3)) + sh_off + 2) if sh_alpha > 0 else 4
    w, h = gw + pad * 2, gh + pad * 2

    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if sh_alpha > 0:
        sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(sh).text(
            (pad - x0 + sh_off, pad - y0 + sh_off), text, font=font,
            fill=(0, 0, 0, int(round(sh_alpha * 255))))
        im = sh.filter(ImageFilter.GaussianBlur(sh_blur))
    ImageDraw.Draw(im).text(
        (pad - x0, pad - y0), text, font=font, fill=rgb + (int(round(alpha * 255)),))
    im.save(out)
    return w, h, pad, gw, gh


def settings_for(cfg, slug):
    s = dict(cfg["defaults"])
    s.update(cfg["ratios"].get(slug, {}))
    if "size" not in s:
        die(f"'{slug}' 비율의 문구 크기가 config에 없다 — disclaimer.json에 추가할 것")
    return s


def build_sheet(rows, out: Path):
    from PIL import Image, ImageDraw
    ims = [(t, Image.open(p)) for t, p in rows]
    w = max(i.width for _, i in ims)
    h = sum(i.height + 20 for _, i in ims)
    sheet = Image.new("RGB", (w, h), (28, 28, 32))
    d = ImageDraw.Draw(sheet)
    y = 0
    for t, im in ims:
        d.text((6, y + 4), t, fill=(255, 220, 120))
        sheet.paste(im, (0, y + 20))
        y += im.height + 20
    sheet.save(out)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--run", required=True, help="런 폴더 (예: output/20260826-vgshot-ampoule)")
    p.add_argument("--exports-dir", default="exports")
    p.add_argument("--ratios", default="", help="쉼표 구분 (기본: exports에 있는 전부)")
    p.add_argument("--text", default="", help="config의 문구를 이 편에서만 덮어쓴다")
    p.add_argument("--config", default=str(CONFIG))
    p.add_argument("--check", action="store_true", help="비율×시점 우하단 검수 시트를 만든다")
    p.add_argument("--sample-only", action="store_true", help="렌더 없이 견본 정지컷만")
    a = p.parse_args()

    cfg = json.loads(Path(a.config).read_text(encoding="utf-8"))
    text = a.text or cfg["text"]
    font = PROJECT / cfg["font"]
    if not font.is_file():
        die(f"폰트 없음: {font}")

    exports = Path(a.run) / a.exports_dir
    if not exports.is_dir():
        die(f"비율 산출물 폴더 없음: {exports} — 9단계 export_ratios.py를 먼저 돌린다")

    slug_of = {r: v["slug"] for r, v in json.loads(
        RATIOS_CONFIG.read_text(encoding="utf-8"))["ratios"].items()}
    want = [slug_of.get(r.strip(), r.strip()) for r in a.ratios.split(",") if r.strip()]

    # macOS는 파일명을 NFD로 들고 있어 NFC 리터럴과 그냥 비교하면 안 잡힌다.
    def nfc(s: str) -> str:
        return unicodedata.normalize("NFC", s)

    suffix = nfc(cfg.get("output_suffix", "_고지"))
    srcs = sorted(q for q in exports.glob("final_*.mp4") if suffix not in nfc(q.stem))
    if want:
        srcs = [q for q in srcs if nfc(q.stem).replace("final_", "") in want]
    if not srcs:
        die(f"대상 없음: {exports}/final_*.mp4")

    tmp = exports / "_고지문구"
    tmp.mkdir(exist_ok=True)
    results, sheet_rows = [], []

    for src in srcs:
        slug = nfc(src.stem).replace("final_", "")
        s = settings_for(cfg, slug)
        w, h = (int(x) for x in probe(src, "stream=width,height", "v").split(",")[:2])
        # 여백은 1080폭 기준값을 캔버스 폭에 비례시킨다 (config가 명시하면 그 값 우선)
        mx, my = int(s["marginRight"]), int(s["marginBottom"])

        png = tmp / f"{slug}.png"
        pw, ph, pad, tw, th = draw_text_png(
            text, font, int(s["size"]), hex_rgb(s["color"]), float(s["alpha"]),
            float(s["shadowAlpha"]), float(s["shadowBlur"]), int(s["shadowOffset"]), png)
        if tw + mx > w:
            die(f"{slug}: 문구 폭 {tw}px + 여백 {mx}px 가 캔버스 {w}px를 넘는다 — 크기를 줄일 것")
        ox, oy = mx - pad, my - pad          # PNG 여백 상쇄 → 글자 가장자리가 기준

        dst = exports / f"final_{slug}{suffix}.mp4"
        if not a.sample_only:
            run(["ffmpeg", "-v", "error", "-i", str(src), "-i", str(png),
                 "-filter_complex", f"[0:v][1:v]overlay=x=W-w-{ox}:y=H-h-{oy}",
                 "-c:v", "libx264", "-crf", str(cfg.get("crf", 14)),
                 "-preset", cfg.get("preset", "medium"), "-pix_fmt", "yuv420p",
                 "-c:a", "copy", "-movflags", "+faststart", str(dst), "-y"],
                label=f"overlay({slug})")
            a_src = probe(src, "stream=duration,bit_rate", "a")
            a_dst = probe(dst, "stream=duration,bit_rate", "a")
            if a_src != a_dst:
                die(f"{slug}: 오디오가 바뀌었다 (원본 {a_src} / 결과 {a_dst})")

        results.append({"ratio": slug, "canvas": f"{w}x{h}", "size_px": int(s["size"]),
                        "text_px": f"{tw}x{th}", "margin": f"{mx},{my}",
                        "shadow": float(s["shadowAlpha"]), "out": str(dst)})
        print(f"  {slug:5s} {s['size']:>3}px({tw}x{th}) · {s['color']} · "
              f"그림자 {int(float(s['shadowAlpha'])*100)}% · 우{mx} 하{my}"
              + ("" if a.sample_only else f" → {dst.name}"))

        if a.check or a.sample_only:
            look = src if a.sample_only else dst
            cw = int(w * cfg["check"]["cropWidthPct"] / 100)
            chh = int(cfg["check"]["cropHeightPx"] * max(1.0, w / 1080))
            for t in cfg["check"]["timepoints"]:
                o = tmp / f"chk_{slug}_{t}.png"
                vf = (f"[0:v][1:v]overlay=x=W-w-{ox}:y=H-h-{oy}[o];"
                      f"[o]crop={cw}:{chh}:{w-cw}:{h-chh}[c]") if a.sample_only else None
                cmd = ["ffmpeg", "-v", "error", "-ss", str(t), "-i", str(look)]
                if vf:
                    cmd += ["-i", str(png), "-filter_complex", vf, "-map", "[c]"]
                else:
                    cmd += ["-vf", f"crop={cw}:{chh}:{w-cw}:{h-chh}"]
                cmd += ["-frames:v", "1", str(o), "-y"]
                run(cmd, label=f"검수 크롭({slug} {t}s)")
                sheet_rows.append((f"{slug}  {t}s  ({s['size']}px, 그림자 "
                                   f"{int(float(s['shadowAlpha'])*100)}%)", o))

    sheet = None
    if sheet_rows:
        sheet = exports / "고지문구_검수.png"
        build_sheet(sheet_rows, sheet)
        print(f"[검수] 시트: {sheet}  ← 눈으로 확인한다 (읽히되 시선이 가지 않아야 한다)")

    print(json.dumps({"text": text, "count": len(results), "ratios": results,
                      "check_sheet": str(sheet) if sheet else None},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
