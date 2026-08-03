#!/usr/bin/env python3
"""Assemble generated clips + narration + music into the final video.

Pipeline:
  1. Trim the first 0.25s off every clip, speed it up to match its narration
     segment, normalize (size/fps/codec/audio).
  2. Concatenate all clips in order.
  3. Audio mix: clip audio kept at low volume (sfx), each narration segment
     placed exactly at its clip's start offset (per-clip sync), one random
     music track from --music-dir looped underneath at low volume.

Manifest JSON format:
{
  "chapters": [
    {
      "narration": "output/run/ch1/narration.mp3",
      "clips": [
        {"file": "output/run/ch1/clip1.mp4", "seg_start": 0.0, "seg_end": 5.6},
        {"file": "output/run/ch1/clip2.mp4", "seg_start": 5.6, "seg_end": 9.3}
      ]
    }
  ]
}
seg_start/seg_end are times in that chapter's narration.mp3 covering the words
spoken during that clip. A clip longer than its segment is sped up to fit
(--no-fit-clips keeps the slack instead); a clip *shorter* than its segment
cannot be fixed here — clips are never slowed down — so keep the segment within
the clip's effective length (clip duration minus the 0.25s trim).

Usage:
  python3 assemble.py --manifest manifest.json --out final.mp4 [--music-dir music]
"""
import argparse
import json
import os
import random
import shutil
import subprocess
import sys


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"명령 실패: {' '.join(cmd)}\n{r.stderr[-2000:]}")
    return r


def ffprobe_duration(path):
    r = run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", path,
    ])
    return float(r.stdout.strip())


def has_audio(path):
    r = run([
        "ffprobe", "-v", "error", "-select_streams", "a",
        "-show_entries", "stream=index", "-of", "csv=p=0", path,
    ])
    return bool(r.stdout.strip())


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--music-dir", default="music")
    p.add_argument("--size", default="1280x720")
    p.add_argument("--fps", type=int, default=24)
    p.add_argument("--trim", type=float, default=0.25)
    p.add_argument("--clip-volume", type=float, default=0.2)
    p.add_argument("--music-volume", type=float, default=0.15)
    p.add_argument("--narration-volume", type=float, default=1.0)
    p.add_argument("--no-fit-clips", dest="fit_clips", action="store_false",
                   help="클립을 나레이션 구간 길이에 맞추지 않는다 (여백을 그대로 둔다)")
    p.add_argument("--max-rate", type=float, default=2.0,
                   help="클립 맞춤 배속의 상한 (기본 2.0). 이 값에 걸리면 경고한다")
    p.add_argument("--keep-temp", action="store_true")
    args = p.parse_args()

    with open(args.manifest, encoding="utf-8") as f:
        manifest = json.load(f)
    w, h = (int(x) for x in args.size.lower().split("x"))

    tmp = os.path.abspath(args.out) + ".work"
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)

    # 1) Trim + normalize every clip, fitting it to its narration segment.
    #
    # Generated clips only come in whole-second sizes (4s/5s/6s/7s depending on
    # the platform) while narration segments land on arbitrary lengths like
    # 3.7s or 5.7s. That mismatch is structural — no amount of clip-splitting
    # makes them line up — so the leftover shows up as dead screen time at the
    # end of every cut. Speeding each clip up to its own segment length removes
    # that and, at the modest rates this produces, reads as extra energy rather
    # than as fast-forward. Rates are per-clip: each cut is matched to the words
    # it carries, not to a global average.
    norm_paths, durations, rates = [], [], []
    vf = (
        f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
        f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,fps={args.fps},format=yuv420p"
    )
    idx = 0
    for ci, ch in enumerate(manifest["chapters"], 1):
        for si, clip in enumerate(ch["clips"], 1):
            src = clip["file"]
            if not os.path.exists(src):
                sys.exit(f"클립 파일 없음: {src}")
            eff = ffprobe_duration(src) - args.trim
            seg = float(clip["seg_end"]) - float(clip["seg_start"])

            rate = 1.0
            if args.fit_clips and seg > 0.05 and eff > seg:
                rate = min(eff / seg, args.max_rate)
                if eff / seg > args.max_rate + 1e-6:
                    print(
                        f"[경고] ch{ci} clip{si}: 맞추려면 {eff / seg:.2f}x가 "
                        f"필요한데 상한 {args.max_rate}x에 걸렸습니다. "
                        f"{eff / rate - seg:.2f}s 여백이 남습니다.",
                        file=sys.stderr,
                    )

            dst = os.path.join(tmp, f"norm_{idx:02d}.mp4")
            cmd = ["ffmpeg", "-y", "-ss", str(args.trim), "-i", src]
            src_has_audio = has_audio(src)
            if not src_has_audio:
                cmd += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-shortest"]
            cmd += ["-vf", vf if rate == 1.0 else f"setpts=PTS/{rate:.5f},{vf}"]
            if src_has_audio and rate != 1.0:
                cmd += ["-af", f"atempo={rate:.5f}"]
            cmd += [
                "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
                dst,
            ]
            run(cmd)
            norm_paths.append(dst)
            durations.append(ffprobe_duration(dst))
            rates.append(round(rate, 3))
            idx += 1

    # 2) Concatenate
    list_path = os.path.join(tmp, "concat.txt")
    with open(list_path, "w") as f:
        for pth in norm_paths:
            f.write(f"file '{pth}'\n")
    base = os.path.join(tmp, "base.mp4")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_path, "-c", "copy", base])

    # 3) Audio mix
    inputs = ["-i", base]
    filters = [f"[0:a]volume={args.clip_volume}[clips]"]
    mix_labels = ["[clips]"]  # first input drives amix duration
    in_idx = 1
    clip_idx = 0
    offset = 0.0
    for ci, ch in enumerate(manifest["chapters"]):
        narration = ch["narration"]
        if not os.path.exists(narration):
            sys.exit(f"나레이션 파일 없음: {narration}")
        for si, clip in enumerate(ch["clips"]):
            seg_start = float(clip["seg_start"])
            seg_end = float(clip["seg_end"])
            eff = durations[clip_idx]
            if seg_end - seg_start > eff + 0.05:
                print(
                    f"[경고] ch{ci + 1} clip{si + 1}: 나레이션 구간({seg_end - seg_start:.2f}s)이 "
                    f"클립 실효 길이({eff:.2f}s)보다 깁니다. 뒷부분이 다음 클립과 겹칩니다.",
                    file=sys.stderr,
                )
            inputs += ["-i", narration]
            off_ms = int(round(offset * 1000))
            chain = (
                f"[{in_idx}:a]atrim=start={seg_start}:end={seg_end},"
                f"asetpts=PTS-STARTPTS,volume={args.narration_volume}"
            )
            if off_ms > 0:
                chain += f",adelay={off_ms}:all=1"
            label = f"[n{ci}_{si}]"
            filters.append(chain + label)
            mix_labels.append(label)
            in_idx += 1
            offset += eff
            clip_idx += 1

    music_file = None
    if os.path.isdir(args.music_dir):
        tracks = [
            os.path.join(args.music_dir, f)
            for f in sorted(os.listdir(args.music_dir))
            if f.lower().endswith((".mp3", ".m4a", ".wav", ".aac", ".flac"))
        ]
        if tracks:
            music_file = random.choice(tracks)
    if music_file:
        inputs += ["-stream_loop", "-1", "-i", music_file]
        filters.append(f"[{in_idx}:a]volume={args.music_volume}[mus]")
        mix_labels.append("[mus]")
        in_idx += 1
    else:
        print("[정보] 음악 파일이 없어 배경음악 없이 합본합니다.", file=sys.stderr)

    filters.append(
        f"{''.join(mix_labels)}amix=inputs={len(mix_labels)}:"
        f"duration=first:dropout_transition=0:normalize=0[aout]"
    )
    run(
        ["ffmpeg", "-y", *inputs,
         "-filter_complex", ";".join(filters),
         "-map", "0:v", "-map", "[aout]",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
         args.out]
    )

    if not args.keep_temp:
        shutil.rmtree(tmp, ignore_errors=True)

    offsets, acc = [], 0.0
    for d in durations:
        offsets.append(round(acc, 3))
        acc += d
    print(json.dumps({
        "out": args.out,
        "duration_seconds": round(ffprobe_duration(args.out), 2),
        "clip_count": len(durations),
        "clip_offsets": offsets,
        "clip_rates": rates,
        "music": music_file,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
