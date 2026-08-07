#!/usr/bin/env python3
"""Flow(Omni Flash)로 만든 영상의 워터마크를 지운다.

Flow는 Pro 구독에서도 워터마크를 끌 수 없다. 생성 영상 우하단 안쪽에 4각별이
반투명으로 합성돼 나오며 위치는 고정이다. 광고로 쓰려면 지워야 한다.

ffmpeg `delogo` 필터로 그 사각형을 주변 픽셀로 보간해 메운다. 지울 자리가
원래 얕은 심도로 흐릿한 영역이라 뭉갠 자국이 눈에 띄지 않는다.

Usage:
  .venv/bin/python3 remove_flow_watermark.py --in final.mp4 --out final_wm.mp4
  .venv/bin/python3 remove_flow_watermark.py --in final.mp4 --out final_wm.mp4 --check

**합본 뒤, 자막 앞에 한 번만 돌린다.** 클립마다 돌리면 재인코딩이 한 번 더
들어가 화질이 깎이고, 자막 뒤에 돌리면 글자가 보간에 뭉개진다.
"""
import argparse
import json
import os
import subprocess
import sys

# 720x1280 실측 (2026-08-06). 후보 4개를 비교해 잔상 없이 가장 작은 값을 골랐다.
# 더 줄이면(50x44, 46x40) 별의 위아래 뿔이 삐져나와 세로 줄무늬 잔상이 남는다.
REF_W, REF_H = 720, 1280
BOX = {"x": 575, "y": 1134, "w": 56, "h": 52}


def probe(path):
    r = subprocess.run([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height", "-of", "json", path,
    ], capture_output=True, text=True, check=True)
    s = json.loads(r.stdout)["streams"][0]
    return s["width"], s["height"]


def box_for(w, h):
    """해상도에 맞춰 워터마크 상자를 환산한다.

    720x1280은 실측값을 그대로 쓴다. 다른 해상도는 비례 환산하는데, Flow가
    해상도마다 워터마크를 같은 상대 위치에 넣는지는 아직 확인하지 않았다.
    720x1280이 아니면 --check 로 눈으로 확인할 것.
    """
    if (w, h) == (REF_W, REF_H):
        return dict(BOX)
    sx, sy = w / REF_W, h / REF_H
    return {
        "x": int(round(BOX["x"] * sx)), "y": int(round(BOX["y"] * sy)),
        "w": int(round(BOX["w"] * sx)), "h": int(round(BOX["h"] * sy)),
    }


def make_check_sheet(src, dst, box, out_png):
    """적용 전후의 우하단을 확대해 나란히 붙인다 (눈 검수용)."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("[검수] Pillow가 없어 시트를 건너뜁니다", file=sys.stderr)
        return
    dur = float(subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "csv=p=0", src], capture_output=True, text=True, check=True).stdout)
    times = [round(dur * p, 2) for p in (0.1, 0.35, 0.6, 0.85)]
    pad, gap, lab, size = 12, 8, 26, (330, 300)
    x, y, w, h = box["x"], box["y"], box["w"], box["h"]
    crop = (max(0, x - 40), max(0, y - 40), x + w + 40, y + h + 40)
    rows = []
    for t in times:
        pair = []
        for path, tag in ((src, "be"), (dst, "af")):
            tmp = f"/tmp/.wmchk_{tag}_{t}.png"
            subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", path,
                            "-frames:v", "1", "-q:v", "1", tmp, "-y"], check=True)
            pair.append(Image.open(tmp).convert("RGB").crop(crop).resize(size, Image.NEAREST))
            os.remove(tmp)
        rows.append((t, pair))
    sheet = Image.new("RGB", (pad * 2 + size[0] * 2 + gap,
                              pad * 2 + (size[1] + lab) * len(rows)), (24, 24, 28))
    d = ImageDraw.Draw(sheet)
    for i, (t, (a, b)) in enumerate(rows):
        yy = pad + (size[1] + lab) * i
        d.text((pad, yy + 6), f"{t}s    왼쪽 = 원본        오른쪽 = 제거 후", fill=(230, 230, 235))
        sheet.paste(a, (pad, yy + lab))
        sheet.paste(b, (pad + size[0] + gap, yy + lab))
    sheet.save(out_png)
    print(f"[검수] 시트: {out_png}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="src", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--crf", type=int, default=16,
                   help="재인코딩 품질 (기본 16 — 합본 CRF 18보다 한 단계 높게 잡아 손실을 줄인다)")
    p.add_argument("--check", action="store_true", help="적용 전후 확대 비교 시트를 만든다")
    p.add_argument("--box", help="상자를 직접 지정: x,y,w,h (워터마크 위치가 바뀌었을 때)")
    args = p.parse_args()

    if not os.path.isfile(args.src):
        sys.exit(f"입력 영상이 없습니다: {args.src}")
    w, h = probe(args.src)
    if args.box:
        try:
            bx, by, bw, bh = (int(v) for v in args.box.split(","))
        except ValueError:
            sys.exit("--box 형식은 x,y,w,h 입니다 (예: 575,1134,56,52)")
        box = {"x": bx, "y": by, "w": bw, "h": bh}
    else:
        box = box_for(w, h)
        if (w, h) != (REF_W, REF_H):
            print(f"[주의] {w}x{h}는 실측 해상도({REF_W}x{REF_H})가 아닙니다. "
                  "비례 환산했으니 --check 로 확인하세요.", file=sys.stderr)

    vf = f"delogo=x={box['x']}:y={box['y']}:w={box['w']}:h={box['h']}"
    subprocess.run([
        "ffmpeg", "-v", "error", "-i", args.src, "-vf", vf,
        "-c:v", "libx264", "-preset", "medium", "-crf", str(args.crf),
        "-c:a", "copy", args.out, "-y",
    ], check=True)

    if args.check:
        make_check_sheet(args.src, args.out, box,
                         os.path.splitext(args.out)[0] + "_워터마크확인.png")
    print(json.dumps({"out": args.out, "size": f"{w}x{h}", "box": box, "crf": args.crf},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
