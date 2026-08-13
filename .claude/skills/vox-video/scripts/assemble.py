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
        {"file": "output/run/ch1/clip2.mp4", "seg_start": 5.6, "seg_end": 9.3,
         "in": 1.2, "out": 4.8}
      ]
    }
  ]
}
seg_start/seg_end are times in that chapter's narration.mp3 covering the words
spoken during that clip. A clip longer than its segment is sped up to fit
(--no-fit-clips keeps the slack instead); a clip *shorter* than its segment
cannot be fixed here — clips are never slowed down — so keep the segment within
the clip's effective length (used range minus nothing — see below).

Optional per-clip "in"/"out" (seconds in the source file) select which part of
the generated video to use (keyframe trim, 2026-08-13): generate long (6s),
keep the good part. Defaults: in = --trim (0.25), out = end of file. Two clips
may share one file with different ranges (one-take split across segments).

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


def probe_size(path):
    r = run([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height", "-of", "csv=p=0:s=x", path,
    ])
    return tuple(int(v) for v in r.stdout.strip().split("x")[:2])


def delogo_filter(spec, src):
    """소스 클립 해상도에 맞춘 delogo 필터 문자열.

    합본 뒤가 아니라 여기서 지우는 이유: 줌·셰이크를 켜면 화면 전체가 확대·
    이동하므로 워터마크도 따라 움직여, 고정 좌표 상자가 빗나간다.
    """
    if spec == "auto":
        from remove_flow_watermark import box_for
        b = box_for(*probe_size(src))
    else:
        try:
            x, y, bw, bh = (int(v) for v in spec.split(","))
        except ValueError:
            sys.exit("--delogo 형식은 x,y,w,h 입니다 (예: 575,1134,56,52)")
        b = {"x": x, "y": y, "w": bw, "h": bh}
    return f"delogo=x={b['x']}:y={b['y']}:w={b['w']}:h={b['h']}"


def has_audio(path):
    r = run([
        "ffprobe", "-v", "error", "-select_streams", "a",
        "-show_entries", "stream=index", "-of", "csv=p=0", path,
    ])
    return bool(r.stdout.strip())


def zoom_filter(zoom, shake, w, h, fps, nf, ss, delay=0):
    """편집 줌(+선택 셰이크)을 zoompan 표현식으로 만든다.

    생성 클립은 카메라 무브가 있어도 컷 안에서 한 번뿐이라, 컷이 바뀔 때의
    운동감은 편집에서 얹는 편이 싸다(재생성 크레딧 0). ZDF 계열이 실제로
    쓰는 레버다 — docs/zdf-스타일-조사.md 적용 후보 A.

    떨림 방지로 입력을 ss배 키운 뒤 zoompan이 되돌린다. 720px에 3% 줌이면
    프레임당 0.05px씩 움직이는데, 정수 반올림만 하면 십여 프레임마다 1px씩
    튀어 계단이 보인다. 크게 만들어 놓고 줄이면 그 오차가 1/ss로 준다.

    zoom>0 줌인, zoom<0 줌아웃. shake는 컷 머리에서만 흔들고 잦아든다.
    """
    amp = abs(shake) * ss                      # 셰이크 진폭(확대 좌표계 px)
    margin = (2.0 * amp / (w * ss)) if amp else 0.0   # 흔들 여유를 배율로 확보
    z0 = 1.0 + margin
    span = max(nf - 1, 1)
    if zoom >= 0:
        z = f"{z0:.5f}+{zoom:.5f}*on/{span}"
    else:
        z = f"{z0 + abs(zoom):.5f}-{abs(zoom):.5f}*on/{span}"

    cx, cy = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    if amp:
        # 지속은 0.25s. 더 짧으면(0.18s=4프레임) 진동이 두어 번 만에 끝나 안 보인다.
        # x를 cos으로 두는 이유: sin은 on=0에서 0이라 타격 프레임이 안 흔들린다 —
        # 타격감은 바로 그 첫 프레임에서 나온다.
        # delay는 앞 전환이 겹쳐 있는 동안을 건너뛰기 위한 것이다. 전환 한복판에
        # 흔들면 두 화면이 섞여 있어 타격이 뭉개진다.
        sf = max(int(round(fps * 0.25)), 2)
        t = "on" if delay <= 0 else f"(on-{delay})"
        decay = f"max(0\\,1-{t}/{sf})*gte(on\\,{delay})"
        cx += f"+{amp:.2f}*cos({t}*2.4)*{decay}"
        cy += f"+{amp:.2f}*sin({t}*3.1)*{decay}"
    return (f"zoompan=z='{z}':x='{cx}':y='{cy}':"
            f"d=1:s={w}x{h}:fps={fps}")


def atempo_chain(rate):
    """배속을 atempo 필터 체인으로 만든다.

    atempo는 한 단에 0.5~2.0만 받는다. 그 범위를 벗어나면 곱이 rate가 되도록
    여러 단으로 쪼갠다 (예: 2.34 → atempo=2.0,atempo=1.17). 단일 필터로 넘기면
    범위를 벗어나는 순간 ffmpeg가 그대로 죽는다.
    """
    parts, r = [], rate
    while r > 2.0:
        parts.append(2.0)
        r /= 2.0
    while r < 0.5:
        parts.append(0.5)
        r /= 0.5
    parts.append(r)
    return ",".join(f"atempo={p:.5f}" for p in parts)


def starts_of(durations, xfades):
    """전환 겹침을 반영한 각 클립의 시작 시각.

    xfade는 앞뒤 클립을 겹치므로 클립 i의 시작은 (앞 길이의 합 - 앞 전환의 합)이다.
    나레이션·자막이 전부 이 값을 기준으로 놓이므로, 여기가 틀리면 전편이 밀린다.
    """
    t, acc = [], 0.0
    for i, d in enumerate(durations):
        t.append(round(acc, 3))
        acc += d - (xfades[i] if i < len(xfades) else 0.0)
    return t, round(acc, 3)


def write_timeline(args, w, h, durations, rates, clip_meta, xfades):
    """클립별 offset·rate·실측 길이를 --out 옆 timeline.json에 기록한다."""
    out_dir = os.path.dirname(os.path.abspath(args.out))
    os.makedirs(out_dir, exist_ok=True)
    starts, acc = starts_of(durations, xfades)
    clips = []
    for i, (meta, dur, rate) in enumerate(zip(clip_meta, durations, rates)):
        clips.append({**meta, "rate": rate, "offset": starts[i],
                      "duration": round(dur, 3),
                      "xfade": round(xfades[i], 3) if i < len(xfades) else 0.0})
    path = os.path.join(out_dir, "timeline.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({
            "version": 1,
            "out": args.out,
            "width": w, "height": h, "fps": args.fps, "trim": args.trim,
            "total_duration": round(acc, 3),
            "clips": clips,
        }, f, ensure_ascii=False, indent=1)
    return path


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
    p.add_argument("--xfade", type=float, default=0.0,
                   help="컷 전환 겹침 길이(초). 0이면 하드컷(기존 동작). "
                        "클립별로 manifest의 \"xfade\"로 덮어쓸 수 있다")
    p.add_argument("--transition", default="fade",
                   help="기본 전환 종류 (ffmpeg xfade). fade / smoothleft / "
                        "smoothright / smoothup / smoothdown 등. 클립별 지정은 "
                        "manifest의 \"transition\"")
    p.add_argument("--zoom", type=float, default=0.0,
                   help="컷별 미세 줌 배율 (0.03 = 4%%까지 서서히 확대, 음수면 축소). "
                        "0이면 끔. 컷별로 끄거나 바꾸려면 manifest 클립에 \"zoom\"을 넣는다")
    p.add_argument("--shake", type=float, default=0.0,
                   help="컷 머리 흔들림 진폭(px, 출력 해상도 기준). 0이면 끔. "
                        "manifest 클립의 \"shake\"로 컷별 지정 가능")
    p.add_argument("--delogo", nargs="?", const="auto", default=None,
                   help="클립 단계에서 Flow 워터마크를 지운다. --delogo(=auto)면 "
                        "remove_flow_watermark의 실측 상자를, x,y,w,h를 주면 그 상자를 쓴다. "
                        "줌·셰이크를 켜면 필수 — 합본 뒤 고정 좌표 delogo는 화면이 "
                        "움직여 빗나간다")
    p.add_argument("--keep-temp", action="store_true")
    p.add_argument("--timeline-only", action="store_true",
                   help="합본하지 않고 timeline.json만 갱신한다 (--out 파일은 건드리지 않는다)")
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
    norm_paths, durations, rates, clip_meta = [], [], [], []

    def fit_vf(sw, sh):
        return (f"scale={sw}:{sh}:force_original_aspect_ratio=decrease,"
                f"pad={sw}:{sh}:(ow-iw)/2:(oh-ih)/2,fps={args.fps}")

    ss = 2  # 줌 서브픽셀용 업스케일 배수 (zoom_filter 참조)

    # 1-A) 전환 길이를 먼저 정한다. 전환은 앞뒤 클립을 겹치므로, 겹치는 만큼
    # 클립을 덜 압축해야 나레이션 간격이 유지된다 (목표 길이 = seg + 그 클립의
    # 뒤 전환). 늘릴 수 있는 여유는 원본이 나레이션보다 긴 만큼(slack)뿐이라,
    # 여유가 적은 클립은 전환도 그만큼 짧아진다. 이걸 무시하고 일괄 겹치면
    # 24컷 기준 8초 가까이 밀려 자막까지 전부 어긋난다.
    flat = [(ci, si, clip)
            for ci, ch in enumerate(manifest["chapters"], 1)
            for si, clip in enumerate(ch["clips"], 1)]
    n = len(flat)
    # 키프레임(구간 선택): manifest 클립의 "in"/"out"(초)으로 소스에서 쓸
    # 구간을 고른다. 생성을 길게(6s) 뽑고 좋은 구간만 쓰는 방식의 짝 —
    # 배속 상한에 걸리던 짧은 나레이션 구간도 트림으로 해결된다. 같은 파일을
    # 두 클립이 다른 구간으로 나눠 쓸 수 있다 (원테이크 분배, 2026-08-13).
    # "in" 생략 시 기본 앞트림(args.trim), "out" 생략 시 파일 끝.
    ins, outs, slacks = [], [], []
    for _, _, clip in flat:
        if not os.path.exists(clip["file"]):
            sys.exit(f"클립 파일 없음: {clip['file']}")
        dur = ffprobe_duration(clip["file"])
        t_in = float(clip.get("in", args.trim))
        t_out = float(clip.get("out", dur))
        if not 0 <= t_in < t_out <= dur + 0.05:
            sys.exit(f"{clip['file']}: in/out({t_in}/{t_out})이 파일 길이 {dur:.2f}s와 안 맞습니다")
        eff = min(t_out, dur) - t_in
        seg = float(clip["seg_end"]) - float(clip["seg_start"])
        if eff < seg - 0.02:
            print(f"[경고] {os.path.basename(clip['file'])}: 사용 구간 {eff:.2f}s가 "
                  f"나레이션 구간 {seg:.2f}s보다 짧습니다 — 끝에 빈 화면이 생깁니다. "
                  "out을 늘리거나 in을 당기세요.", file=sys.stderr)
        ins.append(t_in)
        outs.append(min(t_out, dur))
        slacks.append((eff, seg, max(eff - seg, 0.0)))
    xfades = []
    for i in range(n - 1):
        want = float(flat[i][2].get("xfade", args.xfade))
        xfades.append(min(want, slacks[i][2] * 0.95) if want > 0 else 0.0)
    short = [(flat[i][2]["file"], xfades[i]) for i in range(n - 1)
             if 0 < xfades[i] < float(flat[i][2].get("xfade", args.xfade)) - 1e-6]
    for f, x in short:
        print(f"[정보] {os.path.basename(f)}: 여유가 모자라 전환을 {x:.2f}s로 줄였습니다.",
              file=sys.stderr)

    for idx, (ci, si, clip) in enumerate(flat):
        src = clip["file"]
        eff, seg, _ = slacks[idx]
        x_next = xfades[idx] if idx < n - 1 else 0.0
        target = seg + x_next          # 전환 겹침만큼 길게 남긴다

        rate = 1.0
        if args.fit_clips and target > 0.05 and eff > target:
            rate = min(eff / target, args.max_rate)
            if eff / target > args.max_rate + 1e-6:
                print(
                    f"[경고] ch{ci} clip{si}: 맞추려면 {eff / target:.2f}x가 "
                    f"필요한데 상한 {args.max_rate}x에 걸렸습니다. "
                    f"{eff / rate - target:.2f}s 여백이 남습니다.",
                    file=sys.stderr,
                )

        zoom = float(clip.get("zoom", args.zoom))
        shake = float(clip.get("shake", args.shake))

        chain = []
        if args.delogo:
            chain.append(delogo_filter(args.delogo, src))
        if rate != 1.0:
            chain.append(f"setpts=PTS/{rate:.5f}")
        if zoom or shake:
            nf = max(int(round(eff / rate * args.fps)), 1)
            # 앞 전환이 겹쳐 있는 동안은 타격을 미룬다 (zoom_filter의 delay)
            d = int(round((xfades[idx - 1] if idx > 0 else 0.0) * args.fps))
            chain += [fit_vf(w * ss, h * ss),
                      zoom_filter(zoom, shake, w, h, args.fps, nf, ss, d),
                      "setsar=1", "format=yuv420p"]
        else:
            chain += [fit_vf(w, h), "format=yuv420p"]

        dst = os.path.join(tmp, f"norm_{idx:02d}.mp4")
        cmd = ["ffmpeg", "-y", "-ss", str(ins[idx]), "-t", f"{outs[idx] - ins[idx]:.3f}",
               "-i", src]
        src_has_audio = has_audio(src)
        if not src_has_audio:
            cmd += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-shortest"]
        cmd += ["-vf", ",".join(chain)]
        if src_has_audio and rate != 1.0:
            cmd += ["-af", atempo_chain(rate)]
        cmd += [
            "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
            dst,
        ]
        run(cmd)
        norm_paths.append(dst)
        durations.append(ffprobe_duration(dst))
        rates.append(round(rate, 3))
        clip_meta.append({
            "global": idx, "chapter": ci, "clip": si, "file": src,
            "narration": manifest["chapters"][ci - 1]["narration"],
            "seg_start": float(clip["seg_start"]),
            "seg_end": float(clip["seg_end"]),
            "in": round(ins[idx], 3), "out": round(outs[idx], 3),
            "zoom": zoom, "shake": shake,
            "transition": clip.get("transition", args.transition),
        })

    # 자막 등 후속 단계는 클립별 시작 시각(offset)이 필요하다. seg_start를 그대로
    # 쓰면 안 된다 — 정규화는 프레임 단위로 반올림하므로 클립마다 수십 ms씩 밀리고
    # 그 오차가 누적된다(12클립 기준 실측 +0.16s). 실측 길이의 누적합만이 정답이다.
    starts, total = starts_of(durations, xfades)
    write_timeline(args, w, h, durations, rates, clip_meta, xfades)
    if args.timeline_only:
        if not args.keep_temp:
            shutil.rmtree(tmp, ignore_errors=True)
        return

    # 2) 잇기 — 전환이 있으면 xfade 체인, 없으면 무손실 concat
    base = os.path.join(tmp, "base.mp4")
    if any(xfades):
        vf_parts, cur = [], "[v0]"
        for i in range(n):
            # settb: 입력마다 timebase가 미세하게 다르면 xfade가 거부한다
            vf_parts.append(f"[{i}:v]settb=AVTB,fps={args.fps}[v{i}]")
        for k in range(n - 1):
            nxt = "[vout]" if k == n - 2 else f"[x{k}]"
            kind = clip_meta[k]["transition"] if xfades[k] > 0 else "fade"
            dur = max(xfades[k], 1.0 / args.fps)
            vf_parts.append(
                f"{cur}[v{k + 1}]xfade=transition={kind}:"
                f"duration={dur:.3f}:offset={starts[k + 1]:.3f}{nxt}")
            cur = nxt
        run(["ffmpeg", "-y", *sum((["-i", p] for p in norm_paths), []),
             "-filter_complex", ";".join(vf_parts),
             "-map", "[vout]", "-an",
             "-c:v", "libx264", "-preset", "medium", "-crf", "18", base])
    else:
        list_path = os.path.join(tmp, "concat.txt")
        with open(list_path, "w") as f:
            for pth in norm_paths:
                f.write(f"file '{pth}'\n")
        run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_path,
             "-c", "copy", base])

    # 3) Audio mix
    #
    # 전환을 쓰면 base에 오디오가 없다(xfade는 영상만 잇는다). 그래서 클립
    # 오디오도 나레이션과 같은 방식으로 각자의 시작 시각에 놓는다 — 전환
    # 구간에서 두 컷의 효과음이 겹치는데, 화면이 겹치는 구간이라 맞다.
    inputs, filters, mix_labels = [], [], []
    in_idx = 0
    if any(xfades):
        inputs += ["-i", base]
        in_idx = 1
        for i, pth in enumerate(norm_paths):
            inputs += ["-i", pth]
            ch = f"[{in_idx}:a]asetpts=PTS-STARTPTS,volume={args.clip_volume}"
            if starts[i] > 0:
                ch += f",adelay={int(round(starts[i] * 1000))}:all=1"
            filters.append(f"{ch}[c{i}]")
            mix_labels.append(f"[c{i}]")
            in_idx += 1
    else:
        inputs += ["-i", base]
        filters.append(f"[0:a]volume={args.clip_volume}[clips]")
        mix_labels.append("[clips]")
        in_idx = 1

    clip_idx = 0
    for ci, ch_ in enumerate(manifest["chapters"]):
        narration = ch_["narration"]
        if not os.path.exists(narration):
            sys.exit(f"나레이션 파일 없음: {narration}")
        for si, clip in enumerate(ch_["clips"]):
            seg_start = float(clip["seg_start"])
            seg_end = float(clip["seg_end"])
            own = durations[clip_idx] - (xfades[clip_idx] if clip_idx < n - 1 else 0.0)
            if seg_end - seg_start > own + 0.05:
                print(
                    f"[경고] ch{ci + 1} clip{si + 1}: 나레이션 구간({seg_end - seg_start:.2f}s)이 "
                    f"클립 실효 길이({own:.2f}s)보다 깁니다. 뒷부분이 다음 클립과 겹칩니다.",
                    file=sys.stderr,
                )
            inputs += ["-i", narration]
            off_ms = int(round(starts[clip_idx] * 1000))
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
        # 전환 모드에서는 amix가 duration=longest라 무한 루프를 그대로 물면
        # 끝나지 않는다. 총 길이로 잘라서 넣는다.
        cut = f"atrim=0:{total:.3f}," if any(xfades) else ""
        filters.append(f"[{in_idx}:a]{cut}volume={args.music_volume}[mus]")
        mix_labels.append("[mus]")
        in_idx += 1
    else:
        print("[정보] 음악 파일이 없어 배경음악 없이 합본합니다.", file=sys.stderr)

    # 비전환 모드의 첫 입력은 base 전체 오디오라 first가 곧 전체 길이지만,
    # 전환 모드의 첫 입력은 클립 하나뿐이라 first를 쓰면 첫 컷에서 잘린다.
    dur_mode = "longest" if any(xfades) else "first"
    filters.append(
        f"{''.join(mix_labels)}amix=inputs={len(mix_labels)}:"
        f"duration={dur_mode}:dropout_transition=0:normalize=0[aout]"
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

    print(json.dumps({
        "out": args.out,
        "duration_seconds": round(ffprobe_duration(args.out), 2),
        "clip_count": len(durations),
        "clip_offsets": starts,
        "clip_rates": rates,
        "xfades": [round(x, 3) for x in xfades],
        "music": music_file,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
