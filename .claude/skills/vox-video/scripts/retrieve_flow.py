#!/usr/bin/env python3
"""Flow 다운로드 파일을 표준 위치로 회수하고 검증·상태 갱신까지 수행한다.

브라우저 다운로드 클릭은 범위 밖이다. 이 스크립트는 다운로드된 한 파일을
ffprobe 검증 → mv → jobs.json recover_crop 적용 → flow_state 갱신 →
check_clips 순서로 처리한다. 기존 파일은 삭제·덮어쓰지 않고 버전명으로 보존한다.

Usage:
  .venv/bin/python3 retrieve_flow.py --run output/<run> --run-name run-v01 \
      --job ch1-clip8 [--src ~/Downloads/video.mp4]
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path


class RetrieveError(Exception):
    def __init__(self, stage: str, message: str):
        super().__init__(message)
        self.stage = stage


def run_command(command: list[str], stage: str) -> subprocess.CompletedProcess:
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        details = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip())
                            if part)
        raise RetrieveError(stage, f"명령 exit {result.returncode}: {' '.join(command)}"
                                   + (f"\n{details}" if details else ""))
    return result


def load_job(run: Path, run_name: str, job_id: str) -> tuple[Path, dict, str, int]:
    match = re.fullmatch(r"ch(\d+)-clip(\d+[a-z]?)", job_id)
    if not match:
        raise RetrieveError("jobs", f"--job 형식은 ch<N>-clip<N>입니다: {job_id}")
    chapter, clip = int(match.group(1)), match.group(2)
    jobs_path = run / "flow-browser-runs" / run_name / f"ch{chapter}" / "jobs.json"
    if not jobs_path.is_file():
        raise RetrieveError("jobs", f"jobs.json이 없습니다: {jobs_path}")
    try:
        manifest = json.loads(jobs_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RetrieveError("jobs", f"jobs.json을 읽을 수 없습니다: {exc}") from exc
    if manifest.get("contract") != "vox-flow-browser-jobs-v1":
        raise RetrieveError("jobs", f"Flow jobs 매니페스트가 아닙니다: {jobs_path}")
    job = next((item for item in manifest.get("jobs", [])
                if item.get("job_id") == job_id), None)
    if job is None:
        raise RetrieveError("jobs", f"jobs.json에 작업이 없습니다: {job_id}")
    return jobs_path, job, clip, chapter


def select_source(explicit: Path | None, downloads_dir: Path) -> Path:
    if explicit is not None:
        source = explicit.expanduser().resolve()
        if not source.is_file():
            raise RetrieveError("source", f"소스 파일이 없습니다: {source}")
        return source
    if not downloads_dir.is_dir():
        raise RetrieveError("source", f"다운로드 폴더가 없습니다: {downloads_dir}")
    cutoff = time.time() - 30 * 60
    candidates = sorted(
        (path for path in downloads_dir.glob("*.mp4")
         if path.is_file() and path.stat().st_mtime >= cutoff),
        key=lambda path: path.stat().st_mtime,
    )
    if len(candidates) != 1:
        names = "\n".join(f"  {path}" for path in candidates) or "  (없음)"
        raise RetrieveError(
            "source",
            f"최근 30분 mp4 후보가 {len(candidates)}개입니다. 정확히 1개여야 합니다:\n{names}",
        )
    return candidates[0].resolve()


def probe_video(path: Path) -> tuple[int, int, float]:
    result = run_command([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height", "-show_entries", "format=duration",
        "-of", "json", str(path),
    ], "ffprobe")
    try:
        data = json.loads(result.stdout)
        stream = data["streams"][0]
        return int(stream["width"]), int(stream["height"]), float(data["format"]["duration"])
    except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise RetrieveError("ffprobe", f"영상 메타데이터를 해석할 수 없습니다: {path}") from exc


def validate_video(path: Path, expected_duration: float) -> tuple[int, int, float]:
    width, height, duration = probe_video(path)
    if (width, height) != (720, 1280):
        raise RetrieveError(
            "ffprobe", f"해상도 불일치: {width}x{height} (기대 720x1280) — {path}"
        )
    if abs(duration - expected_duration) > 0.1:
        raise RetrieveError(
            "ffprobe",
            f"길이 불일치: {duration:.3f}s (기대 {expected_duration:.3f}s ±0.1s) — {path}",
        )
    return width, height, duration


def validate_state_ready(jobs_path: Path, job_id: str) -> None:
    state_path = jobs_path.parent / "state.json"
    if not state_path.is_file():
        raise RetrieveError("state", f"state.json이 없습니다: {state_path}")
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RetrieveError("state", f"state.json을 읽을 수 없습니다: {exc}") from exc
    try:
        jobs = json.loads(jobs_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RetrieveError("state", f"jobs.json을 다시 읽을 수 없습니다: {exc}") from exc
    if state.get("manifest_fingerprint") != jobs.get("fingerprint"):
        raise RetrieveError("state", "state.json과 jobs.json의 fingerprint가 다릅니다")
    stage = state.get("jobs", {}).get(job_id, {}).get("stage")
    if stage != "completed":
        raise RetrieveError(
            "state", f"회수 전 작업 단계는 completed여야 합니다: {job_id}={stage}"
        )


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
    print(f"[보존] {path.name} → {preserved.name}")
    return preserved


def import_clip(raw: Path, canonical: Path, recover_crop: str | None,
                reason: str) -> Path | None:
    preserved = preserve_existing(canonical, reason)
    command = ["ffmpeg", "-v", "error", "-y", "-i", str(raw)]
    if recover_crop:
        command += ["-vf", recover_crop, "-map", "0:v:0", "-map", "0:a?",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                    "-c:a", "copy", str(canonical)]
        print(f"[크롭] {recover_crop} → {canonical}")
    else:
        command += ["-map", "0", "-c", "copy", str(canonical)]
        print(f"[크롭 생략] recover_crop=null — 스트림 복사 → {canonical}")
    run_command(command, "crop")
    return preserved


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--run-name", required=True)
    parser.add_argument("--job", required=True)
    parser.add_argument("--src", type=Path)
    parser.add_argument("--downloads-dir", type=Path, default=Path.home() / "Downloads",
                        help="--src 생략 시 후보 검색 및 잔여 검사 폴더")
    parser.add_argument("--supersede-reason", default="구버전")
    args = parser.parse_args()

    try:
        run = args.run.resolve(strict=True)
        jobs_path, job, clip, chapter = load_job(run, args.run_name, args.job)
        source = select_source(args.src, args.downloads_dir.expanduser())
        width, height, duration = validate_video(
            source, float(job["provider_duration_sec"])
        )
        print(f"[ffprobe] {source.name}: {width}x{height}, {duration:.3f}s")
        validate_state_ready(jobs_path, args.job)

        chapter_dir = run / f"ch{chapter}"
        chapter_dir.mkdir(parents=True, exist_ok=True)
        raw = chapter_dir / f"clip{clip}p_raw.mp4"
        if source == raw.resolve():
            raise RetrieveError("move", f"소스와 이동 대상이 같습니다: {raw}")
        preserve_existing(raw, args.supersede_reason)
        shutil.move(str(source), str(raw))
        print(f"[이동] {source} → {raw}")

        canonical = chapter_dir / f"clip{clip}.mp4"
        import_clip(raw, canonical, job.get("recover_crop"), args.supersede_reason)

        script_dir = Path(__file__).resolve().parent
        state_result = run_command([
            sys.executable, str(script_dir / "flow_state.py"), "set",
            "--jobs", str(jobs_path), "--job", args.job,
            "--stage", "downloaded", "--download", str(raw.resolve()),
        ], "state")
        print(f"[상태] {state_result.stdout.strip()}")

        check_result = run_command([
            sys.executable, str(script_dir / "check_clips.py"),
            "--run", str(run), "--chapter", str(chapter), "--clips", clip,
            "--downloads-dir", str(args.downloads_dir.expanduser()),
        ], "check_clips")
        print(check_result.stdout.rstrip())
        print(f"[완료] {args.job} — raw={raw.name}, clip={canonical.name}, "
              f"길이={duration:.3f}s, 크롭={job.get('recover_crop') or '없음'}, "
              "상태=downloaded, 검사=통과")
        return 0
    except (OSError, KeyError, ValueError, RetrieveError) as exc:
        if isinstance(exc, RetrieveError):
            sys.exit(f"[실패:{exc.stage}] {exc}")
        sys.exit(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
