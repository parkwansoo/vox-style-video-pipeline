#!/usr/bin/env python3
"""Extract a shared palette from reference images (k-means over pooled pixels).

Why pooled: a colour that only exists in ONE reference is that image's subject,
not the style. Pooling all images and reporting per-image presence lets the
caller keep only colours that recur — the intersection rule.

Also reports, per colour:
  coverage    fraction of all sampled pixels (→ base fill vs accent)
  present_in  how many of the N images contain it meaningfully (≥1% of that image)
  edge_ratio  fraction of the colour's pixels that sit on high-gradient edges.
              High edge_ratio + low coverage = a stroke/线 colour, not a fill.
              This is the signal behind rules like "red is reserved for strokes".

Usage:
  python3 extract_palette.py refs/*.png [--k 6] [--json out.json]
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter
from sklearn.cluster import KMeans

MAX_SIDE = 400          # downscale for speed; plenty for colour statistics
EDGE_PERCENTILE = 80    # pixels above this gradient percentile count as "edge"
PRESENCE_MIN = 0.01     # a colour must be ≥1% of an image to count as present


def load(path):
    img = Image.open(path).convert("RGB")
    img.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
    return img


def edge_mask(img):
    """Boolean mask of high-gradient pixels (strokes, keylines, type edges)."""
    grad = np.asarray(img.convert("L").filter(ImageFilter.FIND_EDGES), dtype=np.float32)
    if grad.max() <= 0:
        return np.zeros(grad.shape, dtype=bool)
    return grad >= np.percentile(grad, EDGE_PERCENTILE)


def hex_of(rgb):
    return "#{:02X}{:02X}{:02X}".format(*(int(round(c)) for c in rgb))


def luminance(rgb):
    r, g, b = (float(c) / 255 for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def saturation(rgb):
    mx, mn = float(max(rgb)), float(min(rgb))
    return 0.0 if mx == 0 else (mx - mn) / mx


def describe(rgb, coverage, edge_ratio):
    """Heuristic role label. The skill refines this by actually looking at the images.

    Dark tones are checked first: saturation is meaningless near black
    (RGB 31,26,19 computes as sat 0.39 but reads as flat ink).
    """
    sat, lum = saturation(rgb), luminance(rgb)
    if lum <= 0.15:
        return "ink / darkest tone"
    if coverage >= 0.20:
        return "base fill"
    if edge_ratio >= 0.45 and coverage < 0.12:
        return "strokes and linework"
    if sat >= 0.45 and coverage < 0.12:
        return "hot accent"
    if sat < 0.20:
        return "neutral"
    return "secondary accent"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("images", nargs="+")
    p.add_argument("--k", type=int, default=6, help="palette size to extract (default 6)")
    p.add_argument("--json", help="write result JSON here (default: stdout only)")
    args = p.parse_args()

    paths = [Path(x) for x in args.images]
    missing = [str(x) for x in paths if not x.is_file()]
    if missing:
        sys.exit(f"이미지를 찾을 수 없습니다: {', '.join(missing)}")
    if len(paths) < 2:
        print("[경고] 레퍼런스가 1장뿐입니다. 소재와 스타일을 구분하기 어렵습니다 "
              "(2~5장 권장).", file=sys.stderr)

    pools, edges, owners = [], [], []
    for i, path in enumerate(paths):
        img = load(path)
        px = np.asarray(img, dtype=np.float32).reshape(-1, 3)
        pools.append(px)
        edges.append(edge_mask(img).reshape(-1))
        owners.append(np.full(len(px), i, dtype=np.int32))

    pixels = np.concatenate(pools)
    is_edge = np.concatenate(edges)
    owner = np.concatenate(owners)

    k = min(args.k, len(np.unique(pixels, axis=0)))
    km = KMeans(n_clusters=k, n_init=10, random_state=0).fit(pixels)
    labels = km.labels_

    colours = []
    for c in range(k):
        sel = labels == c
        count = int(sel.sum())
        if count == 0:
            continue
        rgb = km.cluster_centers_[c]
        coverage = count / len(pixels)
        edge_ratio = float(is_edge[sel].mean())
        present = sum(
            1 for i in range(len(paths))
            if (sel & (owner == i)).sum() / max(1, (owner == i).sum()) >= PRESENCE_MIN
        )
        colours.append({
            "hex": hex_of(rgb),
            "rgb": [int(round(v)) for v in rgb],
            "coverage": round(coverage, 4),
            "edge_ratio": round(edge_ratio, 3),
            "present_in": present,
            "of_images": len(paths),
            "shared": present >= max(2, (len(paths) + 1) // 2),
            "luminance": round(luminance(rgb), 3),
            "saturation": round(saturation(rgb), 3),
            "suggested_role": describe(rgb, coverage, edge_ratio),
        })

    colours.sort(key=lambda c: -c["coverage"])
    result = {
        "images": [str(x) for x in paths],
        "palette": colours,
        "note": "shared=false 인 색은 그 이미지의 소재일 가능성이 큽니다. "
                "edge_ratio가 높고 coverage가 낮으면 선/스트로크 전용 색입니다. "
                "명도만 다른 인접 색(예: 종이 톤의 밝은/중간/어두운 단계)은 "
                "k-means가 쪼갠 같은 계열이므로 한 색으로 병합해 해석하세요.",
    }
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
