#!/usr/bin/env python3
"""클립 오디오에 나레이션이 섞여 있는지 검사한다 — 합본에서 목소리가 두 겹이 된다.

왜 필요한가 (2026-08-25 실측): 씬 4를 영상 대신 이미지 몽타주로 만들면서
나레이션을 입혀 렌더했다. assemble.py는 클립 오디오를 0.2 볼륨으로 섞으므로
그 구간만 나레이션이 1.2겹이 됐고, **사용자가 귀로 듣고서야 발견했다.**
파형 상관 r=0.999, 합본 기여 19.5%로 확인했다.

시각적 신호가 전혀 없는 결함이다 — 프레임을 아무리 봐도 안 보이고,
check_clips의 오디오 레벨 경고도 "효과음이 큰 것"과 구분하지 못한다
(몽타주는 -15.7dB였는데 정상 컷 clip9도 -19.6dB였다).

판정: 클립 오디오와 그 클립이 놓일 나레이션 구간의 파형 상관계수.
같은 소리면 1.0에 가깝고, 무관한 효과음이면 0 근처다 (실측: 정상 18컷은
전부 |r| < 0.04, 중복 1컷만 0.999 — 임계 0.5는 넉넉하다).

Usage:
  check_audio_dup.py --manifest output/<run>/manifest.json
"""
import argparse
import json
import struct
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

THRESHOLD = 0.5   # 이보다 크면 나레이션이 섞인 것으로 본다
MIN_SAMPLES = 1000


def to_wav(src: Path, out: Path, ss=None, dur=None) -> bool:
    cmd = ["ffmpeg", "-v", "error", "-y"]
    if ss is not None:
        cmd += ["-ss", str(ss)]
    if dur is not None:
        cmd += ["-t", str(dur)]
    cmd += ["-i", str(src), "-vn", "-ac", "1", "-ar", "16000", str(out)]
    return subprocess.run(cmd).returncode == 0


def samples(path: Path):
    with wave.open(str(path)) as w:
        n = w.getnframes()
        return list(struct.unpack(f"{n}h", w.readframes(n)))


def correlation(a, b) -> float:
    n = min(len(a), len(b))
    if n < MIN_SAMPLES:
        return 0.0
    a, b = a[:n], b[:n]
    ma, mb = sum(a) / n, sum(b) / n
    va = sum((x - ma) ** 2 for x in a) ** 0.5
    vb = sum((x - mb) ** 2 for x in b) ** 0.5
    if not va or not vb:
        return 0.0
    return sum((a[i] - ma) * (b[i] - mb) for i in range(n)) / (va * vb)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", required=True, type=Path)
    p.add_argument("--threshold", type=float, default=THRESHOLD)
    args = p.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    # manifest 경로는 프로젝트 루트 기준이다
    root = Path.cwd()
    hits, checked, skipped = [], 0, []

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for chapter in manifest.get("chapters", []):
            narration = root / chapter["narration"]
            if not narration.is_file():
                sys.exit(f"나레이션 파일이 없습니다: {narration}")
            for clip in chapter.get("clips", []):
                src = root / clip["file"]
                name = Path(clip["file"]).name
                if not src.is_file():
                    skipped.append(f"{name} (파일 없음)")
                    continue
                start, end = float(clip["seg_start"]), float(clip["seg_end"])
                clip_wav, narr_wav = tmp / "c.wav", tmp / "n.wav"
                if not to_wav(src, clip_wav):
                    skipped.append(f"{name} (오디오 없음)")
                    continue
                to_wav(narration, narr_wav, ss=start, dur=round(end - start, 3))
                try:
                    r = correlation(samples(clip_wav), samples(narr_wav))
                except Exception as exc:
                    skipped.append(f"{name} ({exc})")
                    continue
                checked += 1
                if abs(r) > args.threshold:
                    hits.append((name, r, start, end))

    print(f"검사 {checked}컷" + (f" · 건너뜀 {len(skipped)}" if skipped else ""))
    for s in skipped:
        print(f"  [알림] {s}")
    if hits:
        print(f"\n[실패] 클립 오디오에 나레이션이 섞인 컷 {len(hits)}건:")
        for name, r, s, e in hits:
            print(f"  {name}  구간 {s:.2f}~{e:.2f}s  상관 r={r:.3f}")
        print("\n  합본에서 목소리가 두 겹으로 들립니다. 클립 쪽 오디오를 무음화하세요:")
        print("  ffmpeg -i in.mp4 -f lavfi -i anullsrc=r=48000:cl=stereo \\")
        print("    -map 0:v -map 1:a -c:v copy -c:a aac -shortest out.mp4")
        return 2
    print("나레이션 중복 없음")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
