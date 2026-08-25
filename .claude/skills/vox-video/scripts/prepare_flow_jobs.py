#!/usr/bin/env python3
"""Flow 브라우저 제출용 작업 매니페스트를 만든다.

Omni를 API 대신 Google Flow 구독으로 돌릴 때 쓴다. 실제 브라우저 조작은
references/flow-browser.md 절차를 따르고, 이 스크립트는 외부 요청 없이
프롬프트·이미지·해시·제출 순서만 결정한다.

입력은 두 모드다. clip<N>.png 한 장이면 Flow "프레임" 모드,
clip<N>_first.png + clip<N>_end.png 두 장이면 "애셋" 모드다. 대응하는
clip<N>p*.png 패딩본이 있으면 실제 업로드는 패딩본을 쓰고 4:5 마스터는
master_path로 함께 기록한다. 회수 크롭은 개별 이미지 치수가 아니라 편의
preflight.json master_ratio를 정본으로 계산한다.

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

from PIL import Image

JOBS_CONTRACT = "vox-flow-browser-jobs-v1"
# Flow의 Omni가 받는 생성 길이. 우리 파이프라인은 4/6만 쓴다.
OMNI_DURATIONS = {4, 6, 8, 10}
PIPELINE_DURATIONS = {4, 6}
# Flow 입력창 상한 실측 근거: 기미 오일 편(20260813) jobs.json에 3597자 프롬프트가
# 통과해 영상 생성·회수까지 완료됐다. 도입값 2600(08-02)은 근거 미기록 —
# 2026-08-24 사용자 승인으로 상향. 4000 초과분은 파일럿 제출의 SHA 대조로 검증.
PROMPT_MAX = 4000
# 카메라 가속 어휘. 카메라 문형만 잡는다 — 나이브한 "accelerat" 검색은 소품
# 가속(clip1 시계 바늘 "hands accelerate")을 오탐한다(2026-08-25 실측).
# 카메라 가속은 내부↔외부 전환 컷에만 쓴다 (2026-08-25 사용자 확정).
CAMERA_ACCEL = re.compile(r"RUSHES|accelerating hard|camera accelerates")


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


def parse_clip_spec(raw: str) -> tuple[str, int]:
    # 번호에 접미사를 허용한다(1b 등). 기존 클립 사이에 새 컷을 끼울 때 뒤 번호를
    # 전부 밀지 않고 clip1b로 넣을 수 있다.
    match = re.fullmatch(r"(\d+[a-z]?):(\d+)", raw)
    if not match:
        raise ValueError(f"--clip 형식은 번호:길이 입니다 (예: 3:6, 1b:4). 받은 값: {raw}")
    number, duration = match.group(1), int(match.group(2))
    if int(re.match(r"\d+", number).group()) < 1:
        raise ValueError(f"클립 번호는 1 이상이어야 합니다: {raw}")
    if duration not in OMNI_DURATIONS:
        raise ValueError(f"Omni가 지원하지 않는 길이입니다: {duration}s")
    if duration not in PIPELINE_DURATIONS:
        raise ValueError(
            f"이 파이프라인은 4초/6초만 씁니다 (합본 실효 길이 계산 기준): {duration}s"
        )
    return number, duration


def padded_path(master: Path) -> Path:
    match = re.fullmatch(r"clip(\d+[a-z]?)(_first|_end)?\.png", master.name)
    if not match:
        raise ValueError(f"패딩본 이름을 계산할 수 없습니다: {master}")
    suffix = match.group(2) or ""
    return master.with_name(f"clip{match.group(1)}p{suffix}.png")


def resolve_images(chapter_dir: Path, number: str) -> tuple[str, list[dict[str, object]]]:
    """이 클립이 이미지 1장인지 첫·끝 2장인지 파일 존재로 정하고, Flow 화면에서
    눌러야 할 입력 모드를 함께 돌려준다.

    반환하는 모드는 **Flow UI의 라벨 그대로**다. 역할 이름(첫 프레임/끝 프레임)과
    화면 설정 이름이 엇갈리므로 여기서 화면 기준으로 통일한다 (2026-08-06 실측):

    - 1장 → "프레임" : 시작 슬롯에만 넣어 그 이미지를 첫 프레임으로 고정한다.
    - 2장 → "애셋"   : Omni Flash는 프레임 모드의 종료 슬롯을 지원하지 않는다.
                        애셋 모드에 두 장을 순서대로 붙이면 첫·끝 프레임이 된다.

    clip<N>_first.png 와 clip<N>_end.png 가 둘 다 있으면 2장, 아니면 clip<N>.png
    1장이다. 한쪽만 있으면 실수이므로 세운다.
    """
    first = chapter_dir / f"clip{number}_first.png"
    end = chapter_dir / f"clip{number}_end.png"
    if first.is_file() and end.is_file():
        mode, masters = "애셋", [("first", first), ("end", end)]
    elif first.is_file() or end.is_file():
        missing = end if first.is_file() else first
        raise ValueError(f"첫·끝 두 장을 쓰려면 둘 다 있어야 합니다. 없는 파일: {missing}")
    else:
        single = chapter_dir / f"clip{number}.png"
        if not single.is_file():
            raise ValueError(f"필요한 파일이 없습니다: {single}")
        mode, masters = "프레임", [("first", single)]

    padded = [(role, master, padded_path(master)) for role, master in masters]
    found = [pad.is_file() for _, _, pad in padded]
    if any(found) and not all(found):
        missing = [str(pad) for (_, _, pad), exists in zip(padded, found) if not exists]
        raise ValueError("한 작업의 패딩본은 전부 있거나 전부 없어야 합니다. 없는 파일: "
                         + ", ".join(missing))
    return mode, [
        {"role": role, "path": pad if all(found) else master,
         "master_path": master if all(found) else None}
        for role, master, pad in padded
    ]


def load_master_ratio(run_dir: Path) -> tuple[int, int] | None:
    preflight_path = run_dir / "preflight.json"
    if not preflight_path.is_file():
        return None
    try:
        preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"preflight.json을 읽을 수 없습니다: {preflight_path} ({exc})") from exc
    raw = preflight.get("master_ratio")
    if raw is None:
        return None
    if (not isinstance(raw, list) or len(raw) != 2
            or any(isinstance(value, bool) or not isinstance(value, int) or value <= 0
                   for value in raw)):
        raise ValueError(f"master_ratio는 양의 정수 [W, H] 배열이어야 합니다: {raw}")
    return raw[0], raw[1]


def crop_for_ratio(ratio: tuple[int, int], out_w: int = 720,
                   out_h: int = 1280) -> str:
    ratio_w, ratio_h = ratio
    crop_h = round(out_w * ratio_h / ratio_w)
    if crop_h % 2:
        crop_h -= 1
    if crop_h <= 0 or crop_h > out_h:
        raise ValueError(f"제공자 프레임에 들어갈 수 없는 master_ratio입니다: {ratio_w}:{ratio_h}")
    crop_y = (out_h - crop_h) // 2
    return f"crop={out_w}:{crop_h}:0:{crop_y}"


def warn_ratio_drift(master: Path, ratio: tuple[int, int]) -> None:
    with Image.open(master) as image:
        width, height = image.size
    expected = ratio[0] / ratio[1]
    actual = width / height
    drift = abs(actual - expected) / expected
    if drift > 0.01:
        print(f"[경고] {master.name}: 마스터 종횡비 {width}:{height}가 "
              f"master_ratio {ratio[0]}:{ratio[1]}에서 {drift * 100:.2f}% 이탈",
              file=sys.stderr)


def build_job(chapter_dir: Path, run_slug: str, chapter: int,
              number: str, duration: int,
              master_ratio: tuple[int, int] | None = None) -> dict[str, object]:
    prompt_path = chapter_dir / f"clip{number}_vid.txt"
    if not prompt_path.is_file():
        raise ValueError(f"필요한 파일이 없습니다: {prompt_path}")
    flow_input_mode, image_specs = resolve_images(chapter_dir, number)

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
    # 지시-금지 모순 검사: 프리앰블 "slow and continuous"와 카메라 가속이 한
    # 프롬프트에 공존하면 지시가 서로 싸운다. 08-24·08-25 두 번 손으로 교정한
    # 재발 유형이라(clip8·9, clip5 잔존) 문서가 아니라 여기서 기계로 막는다.
    if "slow and continuous" in single_line and CAMERA_ACCEL.search(single_line):
        raise ValueError(
            f"지시-금지 모순: 'slow and continuous'와 카메라 가속"
            f"({CAMERA_ACCEL.search(single_line).group()})이 한 프롬프트에 있습니다: "
            f"{prompt_path}\n  가속 컷은 프리앰블에서 'slow and'를 지우세요 "
            f"(카메라 가속은 내부↔외부 전환 컷 전용 — 2026-08-25 사용자 확정)."
        )

    job_id = f"ch{chapter}-clip{number}"
    images = []
    padded = any(spec["master_path"] is not None for spec in image_specs)
    if padded and master_ratio is None:
        raise ValueError(
            f"clip{number}에 패딩본이 있지만 preflight.json에 master_ratio가 없습니다"
        )
    for spec in image_specs:
        role, path = str(spec["role"]), Path(spec["path"])
        sha = sha256_file(path)
        image = {
            "role": role,
            "path": str(path.resolve()),
            "sha256": sha,
            "upload_name": f"{run_slug}-{job_id}-{role}-{sha[:8]}.png",
        }
        if spec["master_path"] is not None:
            master = Path(spec["master_path"])
            image["master_path"] = str(master.resolve())
            warn_ratio_drift(master, master_ratio)
        images.append(image)
    job: dict[str, object] = {
        "job_id": job_id,
        "chapter": chapter,
        "clip": number,
        "provider_duration_sec": duration,
        # Flow 설정 팝업에서 눌러야 할 입력 모드 라벨 그대로 ("프레임" / "애셋")
        "flow_input_mode": flow_input_mode,
        "asset_count": len(images),
        "recover_crop": crop_for_ratio(master_ratio) if padded else None,
        # 첨부 순서가 곧 첫 프레임 → 끝 프레임 순서다
        "images": images,
        "prompt_path": str(prompt_path.resolve()),
        "prompt_single_line": single_line,
        "prompt_single_line_sha256": sha256_text(single_line),
        "prompt_single_line_length": len(single_line),
        "prompt_original_sha256": sha256_text(raw_prompt),
    }
    return job


def submission_order(jobs: list[dict[str, object]]) -> list[str]:
    """설정이 같은 작업을 묶어 Flow 설정 변경 횟수를 줄인다.

    길이와 입력 모드가 둘 다 같아야 설정을 그대로 두고 이어 제출할 수 있다.
    먼저 등장한 그룹 순서는 보존하므로 대본 순서가 크게 뒤집히지 않는다.
    """
    grouped: dict[tuple[int, str], list[str]] = {}
    for job in jobs:
        key = (int(job["provider_duration_sec"]), str(job["flow_input_mode"]))
        grouped.setdefault(key, []).append(str(job["job_id"]))
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

    specs: list[tuple[str, int]] = []
    seen: set[str] = set()
    for raw in args.clip:
        number, duration = parse_clip_spec(raw)
        if number in seen:
            sys.exit(f"클립 번호가 중복됩니다: {number}")
        seen.add(number)
        specs.append((number, duration))

    run_slug = run_dir.name
    try:
        master_ratio = load_master_ratio(run_dir)
        jobs = [build_job(chapter_dir, run_slug, args.chapter, n, d, master_ratio)
                for n, d in specs]
    except ValueError as exc:
        sys.exit(str(exc))

    # 챕터마다 따로 준비하므로 경로에 챕터를 넣는다. 안 넣으면 ch2가 ch1의
    # 매니페스트를 덮어쓰려다 fingerprint 불일치로 거부당한다.
    out_dir = run_dir / "flow-browser-runs" / args.run_name / f"ch{args.chapter}"
    upload_dir = out_dir / "uploads"
    for job in jobs:
        for image in job["images"]:
            upload_path = upload_dir / image["upload_name"]
            clone_or_copy(Path(image["path"]), upload_path)
            image["upload_path"] = str(upload_path)

    order = submission_order(jobs)
    fingerprint = sha256_text(json.dumps(
        [[j["job_id"], j["prompt_single_line_sha256"], j["recover_crop"],
          [i["sha256"] for i in j["images"]],
          j["provider_duration_sec"], j["flow_input_mode"]] for j in jobs],
        ensure_ascii=False, sort_keys=True,
    ))
    modes = {str(j["flow_input_mode"]) for j in jobs}

    manifest = {
        "schema_version": 1,
        "contract": JOBS_CONTRACT,
        "run": str(run_dir),
        "chapter": args.chapter,
        "fingerprint": fingerprint,
        "settings": {
            "media_type": "video",
            # 섞여 있으면 작업마다 job의 flow_input_mode / asset_count 를 보고 설정한다
            "flow_input_mode": modes.pop() if len(modes) == 1 else "mixed",
            "aspect_ratio": args.aspect,
            "model": "Omni Flash",
            "count": 1,
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
        # 화면에서 눌러야 할 입력 모드를 작업별로 보여준다 (1장=프레임, 2장=애셋)
        "flow_input_mode": {j["job_id"]: f'{j["flow_input_mode"]}({j["asset_count"]}장)'
                            for j in jobs},
        "prompt_lengths": {j["job_id"]: j["prompt_single_line_length"] for j in jobs},
        "recover_crop": {j["job_id"]: j["recover_crop"] for j in jobs},
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
