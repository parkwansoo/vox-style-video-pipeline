#!/usr/bin/env python3
"""회수한 클립의 기계 점검 — 규격·오디오 레벨 + 눈검수용 프레임 추출.

판정하지 않는다. 숫자와 프레임을 내놓을 뿐이고, 결론은 눈이 내린다
(실루엣·라벨 자동 판정은 2026-08-12 흰색 마스크 오탐으로 폐기된 전례가 있다).

무엇을 잡나 (전부 실측 사고 기반):
- 오디오 레벨: Flow는 사람이 말하는 장면에서 목소리를 지어 넣는다.
  기미·페이스오일 편 실측 — 정상 컷은 mean -60dB대, 말소리 생성 컷은
  -26~-30dB. mean이 임계(-45dB)보다 크면 경고를 찍는다. AVOID의
  `no voice-over`로는 막히지 않았다 — 회수 후 재는 수밖에 없다.
- 프레임 추출: 첫·끝 프레임을 원본 해상도로 _검수/프레임/ 에 저장한다.
  라벨 오탈자·실루엣 붕괴·프레이밍 이탈은 여기서 눈으로 읽는다.
  (프레임 시트로 동작·연출을 판정하지 않는다 — 정적 사실만.)

Usage:
  .venv/bin/python3 check_clips.py --run output/<run> --clips 3 6b 17
  .venv/bin/python3 check_clips.py --run output/<run> --clips all
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

VOICE_THRESHOLD_DB = -45.0   # mean이 이보다 크면 "말소리 생성 의심"


def probe(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height",
         "-show_entries", "format=duration", "-of", "json", str(path)],
        capture_output=True, text=True, check=True)
    d = json.loads(r.stdout)
    s = d["streams"][0]
    return s["width"], s["height"], float(d["format"]["duration"])


def audio_level(path):
    r = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(path), "-af", "volumedetect",
         "-f", "null", "/dev/null"],
        capture_output=True, text=True)
    mean = maxv = None
    for line in r.stderr.splitlines():
        m = re.search(r"mean_volume:\s*(-?[\d.]+)", line)
        if m:
            mean = float(m.group(1))
        m = re.search(r"max_volume:\s*(-?[\d.]+)", line)
        if m:
            maxv = float(m.group(1))
    return mean, maxv


def dump_frames(path, out_dir, name, duration):
    out_dir.mkdir(parents=True, exist_ok=True)
    outs = []
    for tag, args in (("first", ["-ss", "0"]),
                      ("end", ["-sseof", "-0.2"])):
        dst = out_dir / f"{name}_{tag}.png"
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", *args, "-i", str(path),
             "-update", "1", "-frames:v", "1", str(dst)], check=True)
        outs.append(dst)
    return outs


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run", required=True, help="output/<run>")
    p.add_argument("--chapter", type=int, default=1)
    p.add_argument("--clips", nargs="+", required=True,
                   help="클립 번호(3 6b 17) 또는 all")
    p.add_argument("--voice-threshold", type=float, default=VOICE_THRESHOLD_DB)
    args = p.parse_args()

    ch_dir = Path(args.run) / f"ch{args.chapter}"
    if not ch_dir.is_dir():
        sys.exit(f"챕터 폴더 없음: {ch_dir}")

    if args.clips == ["all"]:
        files = sorted(ch_dir.glob("clip*.mp4"))
        files = [f for f in files if re.fullmatch(r"clip\d+[a-z]?", f.stem)]
        if not files:
            # 0개를 통과로 끝내면 회수 실패·파일명 오류가 전체 합격으로 보인다
            found = sorted(p.name for p in ch_dir.glob("*.mp4"))
            sys.exit(
                f"검사 대상 클립이 0개다: {ch_dir}\n"
                f"  clip<번호>[a-z].mp4 형식만 검사한다. 폴더의 mp4: "
                + (", ".join(found) if found else "없음")
            )
    else:
        files = [ch_dir / f"clip{c}.mp4" for c in args.clips]
        missing = [f for f in files if not f.is_file()]
        if missing:
            sys.exit("클립 파일 없음: " + ", ".join(str(m) for m in missing))

    frame_dir = Path(args.run) / "_검수" / "프레임"
    warnings = []
    rows = []
    for f in files:
        w, h, dur = probe(f)
        mean, maxv = audio_level(f)
        suspect = mean is not None and mean > args.voice_threshold
        if suspect:
            warnings.append(f.stem)
        dump_frames(f, frame_dir, f.stem, dur)
        rows.append((f.stem, w, h, dur, mean, maxv, suspect))

    print(f"{'클립':10s} {'해상도':>9s} {'길이':>7s} {'mean':>7s} {'max':>7s}")
    for name, w, h, dur, mean, maxv, suspect in rows:
        flag = "  ← 말소리 생성 의심" if suspect else ""
        print(f"{name:10s} {w}x{h:>4d} {dur:6.2f}s {mean:6.1f} {maxv:6.1f}{flag}")
    print(f"\n프레임: {frame_dir}/ (첫·끝, 원본 해상도 — 라벨·실루엣은 여기서 눈으로)")
    if warnings:
        print(f"\n[경고] 오디오 레벨이 {args.voice_threshold}dB보다 큰 클립: "
              f"{', '.join(warnings)}")
        print("       사람이 말하는 장면이면 Flow가 목소리를 지어 넣었을 가능성이 큽니다.")
        print("       들어보고 맞으면: ffmpeg -i in.mp4 -f lavfi -i anullsrc=r=48000:cl=stereo"
              " -map 0:v -map 1:a -c:v copy -c:a aac -shortest out.mp4")
        sys.exit(2)


if __name__ == "__main__":
    main()
