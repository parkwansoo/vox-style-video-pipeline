#!/usr/bin/env python3
"""Flow 브라우저 제출의 재개 가능한 상태를 관리한다.

브라우저 자동화는 끊긴다. 끊긴 지점부터 재개할 수 있어야 크레딧과 시간을
낭비하지 않는다. 이 스크립트는 브라우저를 조작하지 않고 상태만 기록하므로,
claude-in-chrome 경로와 Codex 경로가 **같은 state.json을 공유**한다.

단계는 건너뛸 수 없다:
  pending → assets-attached → prompt-ready → submitted
          → generating → completed → downloaded → imported

Usage:
  python3 flow_state.py init   --jobs <jobs.json>
  python3 flow_state.py next   --jobs <jobs.json>
  python3 flow_state.py set    --jobs <jobs.json> --job ch1-clip1 --stage submitted
  python3 flow_state.py status --jobs <jobs.json>
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

STAGES = [
    "pending", "assets-attached", "prompt-ready", "submitted",
    "generating", "completed", "downloaded", "imported",
]
ACTIVE = {"submitted", "generating"}
STATE_CONTRACT = "vox-flow-browser-run-state-v1"


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def atomic_write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent,
        prefix=f".{path.name}.", delete=False,
    ) as handle:
        handle.write(encoded)
        temp_path = Path(handle.name)
    os.replace(temp_path, path)


def load_jobs(jobs_path: Path) -> dict:
    manifest = json.loads(jobs_path.read_text(encoding="utf-8"))
    if manifest.get("contract") != "vox-flow-browser-jobs-v1":
        sys.exit(f"Flow jobs 매니페스트가 아닙니다: {jobs_path}")
    return manifest


def state_path_for(jobs_path: Path) -> Path:
    return jobs_path.parent / "state.json"


def create_state(manifest: dict, path: Path) -> dict:
    settings = manifest.get("settings", {})
    state = {
        "schema_version": 1,
        "contract": STATE_CONTRACT,
        "manifest_fingerprint": manifest["fingerprint"],
        "created_at": now(),
        "updated_at": now(),
        "initial_max_in_flight": settings.get("initial_max_in_flight", 1),
        "max_in_flight": settings.get("max_in_flight", 2),
        "parallel_unlocked": False,
        "submission_order": list(manifest["submission_order"]),
        # 같은 이미지를 Flow에 두 번 올리지 않기 위한 캐시 (sha256 → 애셋 이름)
        "asset_cache": {},
        "jobs": {
            job["job_id"]: {
                "stage": "pending",
                "attempts": 0,
                "edit_id": None,
                "download_path": None,
                "updated_at": now(),
            }
            for job in manifest["jobs"]
        },
    }
    atomic_write(path, state)
    return state


def load_state(manifest: dict, path: Path, *, create: bool = False) -> dict:
    if not path.exists():
        if create:
            return create_state(manifest, path)
        sys.exit(f"상태 파일이 없습니다. 먼저 init 하세요: {path}")
    state = json.loads(path.read_text(encoding="utf-8"))
    if state.get("contract") != STATE_CONTRACT:
        sys.exit(f"유효한 Flow 상태 파일이 아닙니다: {path}")
    if state.get("manifest_fingerprint") != manifest["fingerprint"]:
        sys.exit(
            "기존 상태의 fingerprint가 현재 jobs.json과 다릅니다.\n"
            "프롬프트나 이미지가 바뀌었다는 뜻입니다. 새 --run-name으로 다시 준비하세요."
        )
    return state


def cmd_init(manifest: dict, path: Path) -> dict:
    if path.exists():
        state = load_state(manifest, path)
        return {"state_path": str(path), "created": False,
                "stages": {k: v["stage"] for k, v in state["jobs"].items()}}
    state = create_state(manifest, path)
    return {"state_path": str(path), "created": True,
            "stages": {k: v["stage"] for k, v in state["jobs"].items()}}


def cmd_next(manifest: dict, path: Path) -> dict:
    state = load_state(manifest, path, create=True)
    active = sum(1 for job in state["jobs"].values() if job["stage"] in ACTIVE)
    limit = state["max_in_flight"] if state["parallel_unlocked"] else state["initial_max_in_flight"]
    capacity = max(0, limit - active)
    ready = [
        job_id for job_id in state["submission_order"]
        if state["jobs"].get(job_id, {}).get("stage") == "pending"
    ][:capacity]
    return {
        "next": ready,
        "active": active,
        "limit": limit,
        "parallel_unlocked": state["parallel_unlocked"],
        "reason": ("첫 작업이 완료되기 전에는 동시 1개만 제출합니다."
                   if not state["parallel_unlocked"] else None),
    }


def cmd_set(manifest: dict, path: Path, job_id: str, stage: str,
            edit_id: str | None, download: str | None) -> dict:
    state = load_state(manifest, path)
    job = state["jobs"].get(job_id)
    if job is None:
        sys.exit(f"상태에 없는 작업입니다: {job_id}")
    if stage not in STAGES:
        sys.exit(f"알 수 없는 단계입니다: {stage}")
    current, target = STAGES.index(job["stage"]), STAGES.index(stage)
    if target != current + 1:
        sys.exit(
            f"단계는 순서대로만 바꿉니다: {job['stage']} → {stage} 은(는) 불가.\n"
            f"다음 단계는 {STAGES[current + 1] if current + 1 < len(STAGES) else '(마지막)'} 입니다."
        )
    if stage == "generating" and not edit_id:
        sys.exit("generating 으로 넘어갈 때는 --edit-id 가 필요합니다.")
    if stage == "downloaded" and not download:
        sys.exit("downloaded 로 넘어갈 때는 --download 경로가 필요합니다.")

    job["stage"] = stage
    job["updated_at"] = now()
    if stage == "submitted":
        job["attempts"] = job.get("attempts", 0) + 1
    if edit_id:
        job["edit_id"] = edit_id
    if download:
        job["download_path"] = download
    # 첫 작업이 완료돼야 동시 2개를 연다
    if stage == "completed":
        state["parallel_unlocked"] = True
    state["updated_at"] = now()
    atomic_write(path, state)
    return {"job_id": job_id, "stage": stage, "attempts": job["attempts"],
            "edit_id": job["edit_id"], "download_path": job["download_path"],
            "parallel_unlocked": state["parallel_unlocked"]}


def cmd_status(manifest: dict, path: Path) -> dict:
    state = load_state(manifest, path, create=True)
    by_stage: dict[str, list[str]] = {}
    for job_id, job in state["jobs"].items():
        by_stage.setdefault(job["stage"], []).append(job_id)
    done = len(by_stage.get("downloaded", [])) + len(by_stage.get("imported", []))
    return {
        "total": len(state["jobs"]),
        "downloaded_or_later": done,
        "by_stage": by_stage,
        "parallel_unlocked": state["parallel_unlocked"],
        "edit_ids": {k: v["edit_id"] for k, v in state["jobs"].items() if v["edit_id"]},
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("command", choices=["init", "next", "set", "status"])
    p.add_argument("--jobs", required=True, type=Path)
    p.add_argument("--job")
    p.add_argument("--stage")
    p.add_argument("--edit-id")
    p.add_argument("--download")
    args = p.parse_args()

    jobs_path = args.jobs.resolve(strict=True)
    manifest = load_jobs(jobs_path)
    path = state_path_for(jobs_path)

    if args.command == "init":
        result = cmd_init(manifest, path)
    elif args.command == "next":
        result = cmd_next(manifest, path)
    elif args.command == "status":
        result = cmd_status(manifest, path)
    else:
        if not args.job or not args.stage:
            sys.exit("set 에는 --job 과 --stage 가 필요합니다.")
        result = cmd_set(manifest, path, args.job, args.stage, args.edit_id, args.download)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
