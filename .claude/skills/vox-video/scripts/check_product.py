#!/usr/bin/env python3
"""제품 레퍼런스와 대상 이미지를 같은 마스크로 측정하고 대조 시트를 만든다.

aspect 수치축은 정면·비가림·수직 병 컷에서만 유효하므로 호출자가
--frontal로 선언한다. 다른 구도는 수치 합격/불합격을 만들지 않고
sheet_only 결과와 육안 대조 시트만 남긴다.

Usage:
  .venv/bin/python3 check_product.py --product assets/products/faceoil \
      --image output/<run>/ch1/clip19_end.png --frontal
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps


CONTRACT = "vox-product-check-v1"
DEFAULT_CONFIG = {
    "reference": "reference.png",
    "mask": {
        "red_minus_blue_min": 110,
        "green_minus_blue_min": 60,
        "red_min": 110,
        "min_pixels": 500,
    },
    "aspect_tolerance": 0.35,
}
MANUAL_CHECKS = [
    "라벨 문구·행 수·오탈자",
    "오일 색·수위와 피펫 비침",
    "벌브 흰색·칼라 골드",
    "손이 병이나 라벨을 가리지 않음",
    "배경이 장면 스타일과 일치",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent,
        prefix=f".{path.name}.", delete=False,
    ) as handle:
        handle.write(encoded)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def load_config(product: Path) -> tuple[Path, dict]:
    path = product / "product_check.json"
    if not path.exists():
        atomic_write(path, DEFAULT_CONFIG)
        print(f"[생성] 기본 제품 검사 설정: {path}")
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"product_check.json을 읽을 수 없습니다: {path} ({exc})") from exc
    if not isinstance(config.get("reference"), str) or not config["reference"]:
        raise ValueError(f"reference는 비어 있지 않은 문자열이어야 합니다: {path}")
    mask = config.get("mask")
    required = ("red_minus_blue_min", "green_minus_blue_min", "red_min", "min_pixels")
    if not isinstance(mask, dict) or any(key not in mask for key in required):
        raise ValueError(f"mask 설정 필드가 부족합니다: {path}")
    if any(isinstance(mask[key], bool) or not isinstance(mask[key], (int, float))
           for key in required):
        raise ValueError(f"mask 설정값은 숫자여야 합니다: {path}")
    if mask["min_pixels"] <= 0:
        raise ValueError(f"mask.min_pixels는 양수여야 합니다: {path}")
    tolerance = config.get("aspect_tolerance")
    if (isinstance(tolerance, bool) or not isinstance(tolerance, (int, float))
            or tolerance < 0):
        raise ValueError(f"aspect_tolerance은 0 이상의 숫자여야 합니다: {path}")
    return path, config


def measure(path: Path, config: dict) -> dict | None:
    with Image.open(path) as opened:
        image = opened.convert("RGB")
    width, height = image.size
    mask = config["mask"]
    min_x, min_y, max_x, max_y = width, height, -1, -1
    count = red_sum = green_sum = blue_sum = 0
    pixels = image.load()
    for y in range(height):
        for x in range(width):
            red, green, blue = pixels[x, y]
            if not (red - blue > mask["red_minus_blue_min"]
                    and green - blue > mask["green_minus_blue_min"]
                    and red > mask["red_min"]):
                continue
            min_x, max_x = min(min_x, x), max(max_x, x)
            min_y, max_y = min(min_y, y), max(max_y, y)
            count += 1
            red_sum += red
            green_sum += green
            blue_sum += blue
    if count < int(mask["min_pixels"]):
        return None
    box_width, box_height = max_x - min_x + 1, max_y - min_y + 1
    return {
        "image_size": [width, height],
        "mask_pixels": count,
        "bbox_xyxy": [min_x, min_y, max_x, max_y],
        "bbox_size": [box_width, box_height],
        "aspect": box_height / box_width,
        "masked_rgb_mean": [red_sum // count, green_sum // count, blue_sum // count],
        "fill_ratio": count / (box_width * box_height),
    }


def crop_for_sheet(path: Path, measurement: dict | None) -> Image.Image:
    with Image.open(path) as opened:
        image = opened.convert("RGB")
    if measurement is None:
        return image
    x0, y0, x1, y1 = measurement["bbox_xyxy"]
    pad = max(round((x1 - x0 + 1) * 0.3), 20)
    box = (max(0, x0 - pad), max(0, y0 - pad),
           min(image.width, x1 + pad + 1), min(image.height, y1 + pad + 1))
    return image.crop(box)


def make_sheet(reference: Path, target: Path, reference_measurement: dict,
               target_measurement: dict | None, destination: Path) -> None:
    panel_size = (720, 760)
    header = 44
    panels = []
    for path, measurement, label in (
        (reference, reference_measurement, "REFERENCE"),
        (target, target_measurement, "TARGET"),
    ):
        crop = crop_for_sheet(path, measurement)
        fitted = ImageOps.contain(crop, panel_size, Image.Resampling.LANCZOS)
        panel = Image.new("RGB", (panel_size[0], panel_size[1] + header), "white")
        panel.paste(fitted, ((panel_size[0] - fitted.width) // 2,
                             header + (panel_size[1] - fitted.height) // 2))
        ImageDraw.Draw(panel).text((16, 14), label, fill="black")
        panels.append(panel)
    sheet = Image.new("RGB", (panels[0].width + panels[1].width,
                              max(panel.height for panel in panels)), "white")
    sheet.paste(panels[0], (0, 0))
    sheet.paste(panels[1], (panels[0].width, 0))
    destination.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(destination)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--product", required=True, type=Path)
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--frontal", action="store_true",
                        help="정면·비가림·수직 병 컷에만 aspect 수치축을 적용")
    args = parser.parse_args()

    try:
        product = args.product.resolve(strict=True)
        target = args.image.resolve(strict=True)
        config_path, config = load_config(product)
        reference = (product / config.get("reference", "reference.png")).resolve(strict=True)
        reference_measurement = measure(reference, config)
        if reference_measurement is None:
            raise ValueError(f"레퍼런스에서 제품 마스크를 찾지 못했습니다: {reference}")
        target_measurement = measure(target, config)

        out_dir = target.parent / "_검수"
        stem = target.stem
        sheet_path = out_dir / f"제품검증_{stem}_대조.png"
        result_path = out_dir / f"제품검증_{stem}.json"
        make_sheet(reference, target, reference_measurement, target_measurement, sheet_path)

        delta = None
        if args.frontal:
            if target_measurement is None:
                status = "fail"
                reason = "대상에서 제품 마스크를 찾지 못함"
            else:
                delta = abs(target_measurement["aspect"] - reference_measurement["aspect"])
                if delta <= float(config["aspect_tolerance"]):
                    status, reason = "pass", "정면 수치축 허용 범위 통과"
                else:
                    status = "fail"
                    reason = (f"실루엣 aspect Δ{delta:.3f}가 허용폭 "
                              f"{float(config['aspect_tolerance']):.3f} 초과")
        else:
            status = "sheet_only"
            reason = "정면·비가림·수직 병 컷 선언 없음 — 수치축 미적용, 육안 대조 전용"

        result = {
            "schema_version": 1,
            "contract": CONTRACT,
            "status": status,
            "reason": reason,
            "frontal": args.frontal,
            "product": str(product),
            "config": str(config_path.resolve()),
            "reference": str(reference),
            "image": str(target),
            "image_sha256": sha256_file(target),
            "reference_measurement": reference_measurement,
            "target_measurement": target_measurement,
            "aspect_delta": delta,
            "aspect_tolerance": float(config["aspect_tolerance"]),
            "comparison_sheet": str(sheet_path.resolve()),
            "manual_checks": MANUAL_CHECKS,
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        atomic_write(result_path, result)
        print(f"[{status}] {target.name} — {reason}")
        if target_measurement is not None:
            print(f"  aspect={target_measurement['aspect']:.3f}, "
                  f"reference={reference_measurement['aspect']:.3f}"
                  + (f", Δ={delta:.3f}" if delta is not None else ""))
        print(f"  대조 시트: {sheet_path}")
        print(f"  결과 JSON: {result_path}")
        return 2 if status == "fail" else 0
    except (OSError, ValueError) as exc:
        sys.exit(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
