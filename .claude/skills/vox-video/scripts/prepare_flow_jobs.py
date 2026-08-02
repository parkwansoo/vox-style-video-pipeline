#!/usr/bin/env python3
"""Flow 브라우저 제출용 작업 매니페스트를 만든다.

Omni를 API 대신 Google Flow 구독으로 돌릴 때 쓴다. 실제 브라우저 조작은
references/flow-browser.md 절차를 따르고, 이 스크립트는 외부 요청 없이
프롬프트·이미지·해시·제출 순서만 결정한다.

우리 파이프라인은 클립당 이미지가 **한 장**이다(Omni 참조 이미지). first/end
두 장을 쓰는 다른 프로젝트 방식과 다르므로 애셋 수는 항상 1이다.

Usage:
  python3 prepare_flow_jobs.py \\
    --run output/20260802-melasma-causes --chapter 1 \\
    --clip 1:6 2:6 3:6 4:6 5:4 6:4 7:4 8:4 9:4 \\
    --run-name run-v01
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

JOBS_CONTRACT = "vox-flow-browser-jobs-v1"
# Flow의 Omni가 받는 생성 길이. 우리 파이프라인은 4/6만 쓴다.
OMNI_DURATIONS = {4, 6, 8, 10}
PIPELINE_DURATIONS = {4, 6}
PROMPT_MAX = 2600


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def clone_or_copy(source: Path, destination: Path) -> None:
    """APFS clonefile로 복사한다. 이미지 데이터를 중복 저장하지 않는다."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if sha256_file(source) != sha256_file(destination):
            raise ValueError(f"기존 업로드 사본의 SHA가 다릅니다: {destination}")
        return
    result = subprocess.run(
        ["cp", "-c", str(source), str(destination)],
        check=False, capture_output=True, text=True,
    )
    if result.returncode != 0:
        shutil.copy2(source, destination)
    if sha256_file(source) != sha256_file(destination):
        raise ValueError(f"업로드 사본의 SHA 검증에 실패했습니다: {destination}")


def parse_clip_spec(raw: str) -> tuple[int, int]:
    match = re.fullmatch(r"(\d+):(\d+)", raw)
    if not match:
        raise ValueError(f"--clip 형식은 번호:길이 입니다 (예: 3:6). 받은 값: {raw}")
    number, duration = int(match.group(1)), int(match.group(2))
    if number < 1:
        raise ValueError(f"클립 번호는 1 이상이어야 합니다: {raw}")
    if duration not in OMNI_DURATIONS:
        raise ValueError(f"Omni가 지원하지 않는 길이입니다: {duration}s")
    if duration not in PIPELINE_DURATIONS:
        raise ValueError(
            f"이 파이프라인은 4초/6초만 씁니다 (합본 실효 길이 계산 기준): {duration}s"
        )
    return number, duration


def build_job(chapter_dir: Path, run_slug: str, chapter: int,
              number: int, duration: int) -> dict[str, object]:
    prompt_path = chapter_dir / f"clip{number}_vid.txt"
    image_path = chapter_dir / f"clip{number}.png"
    for path in (prompt_path, image_path):
        if not path.is_file():
            raise ValueError(f"필요한 파일이 없습니다: {path}")

    raw_prompt = prompt_path.read_text(encoding="utf-8")
    # Slate 편집기는 줄바꿈을 견디지 못한다. 모든 공백을 단일 공백으로 접는다.
    single_line = re.sub(r"\s+", " ", raw_prompt).strip()
    if not single_line:
        raise ValueError(f"프롬프트가 비어 있습니다: {prompt_path}")
    if len(single_line) > PROMPT_MAX:
        raise ValueError(
            f"정규화 프롬프트가 너무 깁니다 ({len(single_line)}자 > {PROMPT_MAX}): {prompt_path}"
        )
    if re.search(r"[\r\n​﻿]", single_line):
        raise ValueError(f"프롬프트에 숨은 문자가 남아 있습니다: {prompt_path}")

    image_sha = sha256_file(image_path)
    job_id = f"ch{chapter}-clip{number}"
    return {
        "job_id": job_id,
        "chapter": chapter,
        "clip": number,
        "provider_duration_sec": duration,
        # 애셋은 항상 1개다 (Omni 참조 이미지)
        "image": {
            "path": str(image_path.resolve()),
            "sha256": image_sha,
            "upload_name": f"{run_slug}-{job_id}-{image_sha[:8]}.png",
        },
        "prompt_path": str(prompt_path.resolve()),
        "prompt_single_line": single_line,
        "prompt_single_line_sha256": sha256_text(single_line),
        "prompt_single_line_length": len(single_line),
        "prompt_original_sha256": sha256_text(raw_prompt),
    }


def submission_order(jobs: list[dict[str, object]]) -> list[str]:
    """설정이 같은 작업을 묶어 Flow 설정 변경 횟수를 줄인다.

    먼저 등장한 그룹 순서는 보존하므로 대본 순서가 크게 뒤집히지 않는다.
    """
    grouped: dict[int, list[str]] = {}
    for job in jobs:
        grouped.setdefault(int(job["provider_duration_sec"]), []).append(str(job["job_id"]))
    return [job_id for group in grouped.values() for job_id in group]


def atomic_write(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent,
        prefix=f".{path.name}.", delete=False,
    ) as handle:
        handle.write(encoded)
        temp_path = Path(handle.name)
    os.replace(temp_path, path)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--run", required=True, type=Path, help="output/<YYYYMMDD-슬러그>")
    p.add_argument("--chapter", type=int, default=1)
    p.add_argument("--clip", nargs="+", required=True, metavar="번호:길이",
                   help="예: 1:6 2:6 5:4 — 길이는 4 또는 6")
    p.add_argument("--run-name", default="run-v01",
                   help="같은 챕터를 다시 준비할 때 새 이름을 쓴다")
    p.add_argument("--aspect", default="9:16", choices=["16:9", "9:16"])
    args = p.parse_args()

    run_dir = args.run.resolve(strict=True)
    chapter_dir = run_dir / f"ch{args.chapter}"
    if not chapter_dir.is_dir():
        sys.exit(f"챕터 폴더가 없습니다: {chapter_dir}")

    specs: list[tuple[int, int]] = []
    seen: set[int] = set()
    for raw in args.clip:
        number, duration = parse_clip_spec(raw)
        if number in seen:
            sys.exit(f"클립 번호가 중복됩니다: {number}")
        seen.add(number)
        specs.append((number, duration))

    run_slug = run_dir.name
    jobs = [build_job(chapter_dir, run_slug, args.chapter, n, d) for n, d in specs]

    out_dir = run_dir / "flow-browser-runs" / args.run_name
    upload_dir = out_dir / "uploads"
    for job in jobs:
        image = job["image"]
        upload_path = upload_dir / image["upload_name"]
        clone_or_copy(Path(image["path"]), upload_path)
        image["upload_path"] = str(upload_path)

    order = submission_order(jobs)
    fingerprint = sha256_text(json.dumps(
        [[j["job_id"], j["prompt_single_line_sha256"], j["image"]["sha256"],
          j["provider_duration_sec"]] for j in jobs],
        ensure_ascii=False, sort_keys=True,
    ))

    manifest = {
        "schema_version": 1,
        "contract": JOBS_CONTRACT,
        "run": str(run_dir),
        "chapter": args.chapter,
        "fingerprint": fingerprint,
        "settings": {
            "media_type": "video",
            "input_mode": "assets",
            "aspect_ratio": args.aspect,
            "model": "Omni Flash",
            "count": 1,
            "asset_count": 1,
            "poll_interval_sec": 15,
            "slate_selector": '[data-slate-editor="true"]',
            "add_button_accessible_name": "add_2 만들기",
            "create_button_accessible_name": "arrow_forward 만들기",
            "settings_button_name_template": "동영상 · {duration}s crop_9_16 x1",
            "prompt_input_methods": ["press-then-type", "character-press"],
            "forbid_enter": True,
            "initial_max_in_flight": 1,
            "max_in_flight": 2,
            "submit_requires_explicit_flag": True,
        },
        "submission_order": order,
        "jobs": jobs,
    }

    out_path = out_dir / "jobs.json"
    if out_path.exists():
        existing = json.loads(out_path.read_text(encoding="utf-8"))
        if existing.get("fingerprint") != fingerprint:
            sys.exit(
                f"같은 이름의 run이 다른 내용으로 이미 있습니다: {out_path}\n"
                "덮어쓰지 않습니다. --run-name 을 run-v02 처럼 새로 지정하세요."
            )
    atomic_write(out_path, manifest)

    print(json.dumps({
        "jobs_path": str(out_path),
        "uploads": str(upload_dir),
        "job_count": len(jobs),
        "fingerprint": fingerprint[:12],
        "submission_order": order,
        "prompt_lengths": {j["job_id"]: j["prompt_single_line_length"] for j in jobs},
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
