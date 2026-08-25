#!/usr/bin/env python3
"""마스터 이미지를 편의 비율 박스에 맞춰 Flow 9:16 입력본으로 패딩한다.

first/end 쌍은 first 상단의 실측색을 공통 밴드색으로 쓴다. 출력 이름은
prepare_flow_jobs.py가 인식하는 clip<N>p*.png 규약이다. 기존 출력은
삭제·덮어쓰기하지 않고 _vN_구버전 이름으로 보존한다.

Usage:
  .venv/bin/python3 pad_for_flow.py --run output/<run> --chapter 1 \
      --clip 8 17
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageStat

from prepare_flow_jobs import crop_for_ratio


def load_master_ratio(run: Path) -> tuple[int, int]:
    preflight = run / "preflight.json"
    if not preflight.is_file():
        raise ValueError(f"preflight.json이 없습니다: {preflight}")
    try:
        data = json.loads(preflight.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"preflight.json을 읽을 수 없습니다: {preflight} ({exc})") from exc
    raw = data.get("master_ratio")
    if (not isinstance(raw, list) or len(raw) != 2
            or any(isinstance(value, bool) or not isinstance(value, int) or value <= 0
                   for value in raw)):
        raise ValueError(f"master_ratio는 양의 정수 [W, H] 배열이어야 합니다: {raw}")
    return raw[0], raw[1]


def source_frames(chapter_dir: Path, clip: str) -> list[tuple[str | None, Path]]:
    first = chapter_dir / f"clip{clip}_first.png"
    end = chapter_dir / f"clip{clip}_end.png"
    if first.is_file() and end.is_file():
        return [("first", first), ("end", end)]
    if first.is_file() or end.is_file():
        missing = end if first.is_file() else first
        raise ValueError(f"첫·끝 두 장을 쓰려면 둘 다 있어야 합니다. 없는 파일: {missing}")
    single = chapter_dir / f"clip{clip}.png"
    if not single.is_file():
        raise ValueError(f"필요한 파일이 없습니다: {single}")
    return [(None, single)]


def output_path(chapter_dir: Path, clip: str, role: str | None) -> Path:
    suffix = f"_{role}" if role else ""
    return chapter_dir / f"clip{clip}p{suffix}.png"


def measured_band_colour(path: Path, rows: int) -> tuple[int, int, int]:
    with Image.open(path) as source:
        image = source.convert("RGB")
        sample = image.crop((0, 0, image.width, min(rows, image.height)))
        return tuple(int(value) for value in ImageStat.Stat(sample).median)


def target_height(width: int, content_height: int) -> int:
    nominal = round(width * 16 / 9)
    candidates = [height for height in range(nominal - 2, nominal + 3)
                  if height > content_height and (height - content_height) % 2 == 0]
    if not candidates:
        raise ValueError(
            f"9:16 패딩 높이를 계산할 수 없습니다: 폭 {width}, 콘텐츠 {content_height}"
        )
    return min(candidates, key=lambda height: abs(width / height - 9 / 16))


def preserved_path(path: Path, reason: str) -> Path:
    index = 1
    while True:
        candidate = path.with_name(f"{path.stem}_v{index}_{reason}{path.suffix}")
        if not candidate.exists():
            return candidate
        index += 1


def preserve_existing(path: Path, reason: str) -> Path | None:
    if not path.exists():
        return None
    preserved = preserved_path(path, reason)
    shutil.move(str(path), str(preserved))
    return preserved


def pad_image(source: Path, destination: Path, ratio: tuple[int, int],
              colour: tuple[int, int, int], reason: str) -> dict[str, object]:
    with Image.open(source) as opened:
        image = opened.convert("RGB")
    content_height = round(image.width * ratio[1] / ratio[0])
    normalized = image.resize((image.width, content_height), Image.Resampling.LANCZOS)
    padded_height = target_height(image.width, content_height)
    band = (padded_height - content_height) // 2
    canvas = Image.new("RGB", (image.width, padded_height), colour)
    canvas.paste(normalized, (0, band))
    preserved = preserve_existing(destination, reason)
    canvas.save(destination)
    return {
        "source": str(source),
        "out": str(destination),
        "source_size": list(image.size),
        "content_box": [image.width, content_height],
        "padded_size": [image.width, padded_height],
        "band": band,
        "band_colour": list(colour),
        "recover_crop": crop_for_ratio(ratio),
        "preserved": str(preserved) if preserved else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--chapter", type=int, default=1)
    parser.add_argument("--clip", nargs="+", required=True,
                        help="클립 번호(예: 8 17 6b)")
    parser.add_argument("--sample-rows", type=int, default=20)
    parser.add_argument("--supersede-reason", default="구버전")
    args = parser.parse_args()

    if args.sample_rows < 1:
        sys.exit("--sample-rows는 1 이상이어야 합니다")
    for clip in args.clip:
        if not re.fullmatch(r"\d+[a-z]?", clip):
            sys.exit(f"클립 번호 형식이 잘못됐습니다: {clip}")

    try:
        run = args.run.resolve(strict=True)
        chapter_dir = run / f"ch{args.chapter}"
        if not chapter_dir.is_dir():
            raise ValueError(f"챕터 폴더가 없습니다: {chapter_dir}")
        ratio = load_master_ratio(run)
        results = []
        for clip in args.clip:
            frames = source_frames(chapter_dir, clip)
            # first/end 쌍도 첫 이미지 한 장에서만 실측해 밴드색을 고정한다.
            colour = measured_band_colour(frames[0][1], args.sample_rows)
            for role, source in frames:
                results.append(pad_image(
                    source, output_path(chapter_dir, clip, role), ratio, colour,
                    args.supersede_reason,
                ))
    except (OSError, ValueError) as exc:
        sys.exit(str(exc))

    print(json.dumps({"master_ratio": list(ratio), "outputs": results},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
