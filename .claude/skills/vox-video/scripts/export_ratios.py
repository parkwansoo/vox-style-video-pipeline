#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""완성 영상을 여러 출력 비율로 내보낸다 — 크롭 없이(contain + 블러 확대 배경).

파이프라인 9단계. 1~8단계 산출물은 읽기만 하고 고치지 않는다.

  ① 정렬 검증  자막 없는 영상(--video)과 BGM 완성본(--audio)이 같은 타임라인인지
               여러 지점 PSNR로 대조한다. 어긋나면 렌더 전에 실패한다.
  ② 패딩       비율별 캔버스에 원본 전체를 contain으로 얹고 남는 공간은
               원본을 확대·블러한 배경으로 채운다 (한 픽셀도 잘리지 않는다).
  ③ 자막       그 캔버스 위에 자막·헤드카피를 재렌더한다
               (subtitler/scripts/render.mjs — 입력 해상도를 그대로 따른다).
  ④ 검증       해상도·오디오·길이에 더해, 출력 중앙에서 원본을 되꺼내 PSNR로
               "잘리지 않았음"을 실측한다.

사용법:
  .venv/bin/python3 .claude/skills/vox-video/scripts/export_ratios.py \
      --run output/20260813-melasma-oil \
      --video final.mp4 --audio "0818 (1).mp4"

  # 자막 없이 패딩만
  ... --no-captions
  # 일부 비율만
  ... --ratios 4:5,16:9
"""
from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
PROJECT = SKILL.parent.parent.parent
CONFIG = SKILL / "config" / "video-ratios.json"
RENDER_MJS = PROJECT / "subtitler" / "scripts" / "render.mjs"


# ── 공용 ────────────────────────────────────────────────────────────────────
def die(msg: str) -> None:
    print(f"[실패] {msg}", file=sys.stderr)
    sys.exit(1)


def run(cmd, *, capture=False, label=""):
    """에러를 삼키지 않는다 (CLAUDE.md 규율 ⑤). 실패하면 stderr를 그대로 보여준다."""
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stdout)
        sys.stderr.write(r.stderr)
        die(f"{label or cmd[0]} 실패 (exit {r.returncode})")
    return r.stdout if capture else None


def even(n: float, cap: int | None = None) -> int:
    """가장 가까운 짝수 (h264 요구). cap이 있으면 넘지 않는다."""
    n = int(round(n))
    if n % 2:
        n += 1
    if cap is not None and n > cap:
        n = cap - (cap % 2)
    return max(2, n)


def probe(path: Path) -> dict:
    out = run(["ffprobe", "-v", "error", "-show_entries",
               "stream=index,codec_type,width,height,avg_frame_rate,duration",
               "-show_entries", "format=duration", "-of", "json", str(path)],
              capture=True, label=f"ffprobe {path.name}")
    d = json.loads(out)
    v = next((s for s in d["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in d["streams"] if s["codec_type"] == "audio"), None)
    if not v:
        die(f"{path.name}: 영상 스트림이 없습니다")
    num, den = (v.get("avg_frame_rate") or "0/1").split("/")
    fps = float(num) / float(den) if float(den) else 0.0
    if abs(fps - round(fps)) < 0.2:          # concat 산물은 29.86처럼 흔들린다 (props.mjs와 같은 규칙)
        fps = float(round(fps))
    return {"width": v["width"], "height": v["height"], "fps": fps,
            "duration": float(d["format"]["duration"]), "has_audio": a is not None}


def frame_band(src: Path, t: float, out: Path, *, top=0.30, span=0.28, size=(180, 120)) -> None:
    """자막·헤드가 없는 세로 구간만 잘라 그레이 축소본으로 뽑는다 (대조 전용)."""
    run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.4f}", "-i", str(src), "-frames:v", "1",
         "-vf", f"crop=iw:ih*{span}:0:ih*{top},scale={size[0]}:{size[1]},format=gray",
         str(out)], label="ffmpeg 프레임 추출")


def psnr(a: Path, b: Path) -> float:
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(a), "-i", str(b),
                        "-lavfi", "psnr=stats_file=-", "-f", "null", "-"],
                       capture_output=True, text=True)
    line = [x for x in (r.stdout + r.stderr).splitlines() if "psnr_avg" in x]
    if not line:
        return 0.0
    tok = line[0].split("psnr_avg:")[1].split()[0]
    return math.inf if tok == "inf" else float(tok)


# ── ① 정렬 검증 ─────────────────────────────────────────────────────────────
def verify_alignment(video: Path, other: Path, points, fps: float, tmp: Path,
                     *, min_psnr=25.0, max_shift_frames=3) -> list[dict]:
    """--video 와 --audio 소스가 같은 타임라인인지 확인한다.

    캡컷에서 BGM만 얹었다면 두 영상은 같은 그림이라 PSNR이 높게 붙는다.
    자르기·순서 변경을 했다면 여기서 걸려 무성의한 오디오 어긋남을 막는다.
    """
    rows = []
    for t in points:
        ref = tmp / "align_ref.png"
        frame_band(other, t, ref)
        best = (None, -1.0)
        for k in range(-max_shift_frames, max_shift_frames + 1):
            cand = tmp / f"align_{k}.png"
            frame_band(video, max(0.0, t + k / fps), cand)
            v = psnr(ref, cand)
            if v > best[1]:
                best = (k, v)
        rows.append({"t": t, "shift_frames": best[0], "psnr": round(best[1], 2)})
    bad = [r for r in rows if r["psnr"] < min_psnr]
    return rows, bad


# ── ② 패딩 ──────────────────────────────────────────────────────────────────
def fit_size(sw: int, sh: int, cw: int, ch: int) -> tuple[int, int]:
    """contain — 원본 전체가 들어가는 최대 크기 (크롭 없음)."""
    s = min(cw / sw, ch / sh)
    return even(sw * s, cap=cw), even(sh * s, cap=ch)


def pad_filter(src: dict, cw: int, ch: int, bg: dict, fps: float) -> tuple[str, int, int]:
    fw, fh = fit_size(src["width"], src["height"], cw, ch)
    ds = int(bg.get("blurDownscale", 4))
    zoom = float(bg.get("bgZoom", 1.08))
    bright = float(bg.get("bgBrightness", 0.72))
    sigma = float(bg["blurSigma"]) * ch / float(bg.get("blurRefHeight", 1920))

    # 배경: 캔버스보다 zoom배 큰 상자를 덮도록 확대 → 캔버스 크기로 중앙 크롭 → 블러 → 감광.
    # 블러는 축소본에서 걸고 되키운다 (같은 결과, 훨씬 빠름).
    bw_s, bh_s = even(cw * zoom / ds), even(ch * zoom / ds)
    cw_s, ch_s = even(cw / ds), even(ch / ds)
    cw_s, ch_s = min(cw_s, bw_s), min(ch_s, bh_s)
    f = (
        f"[0:v]fps={fps:g},setsar=1,split=2[s0][s1];"
        f"[s0]scale={bw_s}:{bh_s}:force_original_aspect_ratio=increase,"
        f"crop={cw_s}:{ch_s},gblur=sigma={max(sigma / ds, 0.5):.3f}:steps=3,"
        f"scale={cw}:{ch}:flags=bicubic,"
        f"colorchannelmixer=rr={bright}:gg={bright}:bb={bright}[bg];"
        f"[s1]scale={fw}:{fh}:flags=lanczos[fg];"
        f"[bg][fg]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]"
    )
    return f, fw, fh


def pad_ratio(video: Path, audio_src: Path | None, out: Path, src: dict,
              cw: int, ch: int, bg: dict, fps: float, crf: int) -> tuple[int, int]:
    filt, fw, fh = pad_filter(src, cw, ch, bg, fps)
    cmd = ["ffmpeg", "-y", "-v", "error", "-stats", "-i", str(video)]
    if audio_src is not None:
        cmd += ["-i", str(audio_src)]
    cmd += ["-filter_complex", filt, "-map", "[v]"]
    cmd += ["-map", "1:a" if audio_src is not None else "0:a?"]
    cmd += ["-c:v", "libx264", "-crf", str(crf), "-preset", "medium",
            "-pix_fmt", "yuv420p", "-r", f"{fps:g}", "-c:a", "copy", "-shortest", str(out)]
    run(cmd, label="ffmpeg 패딩")
    return fw, fh


# ── ③ 자막 재렌더 ───────────────────────────────────────────────────────────
def render_captions(run_dir: Path, rel_in: str, rel_out: str, crf: int, codec: str, preset: str) -> None:
    cmd = ["node", str(RENDER_MJS), "--run", str(run_dir),
           "--video", rel_in, "--out", rel_out,
           "--crf", str(crf), "--codec", codec, "--preset", preset]
    r = subprocess.run(cmd, text=True)
    if r.returncode != 0:
        die(f"자막 렌더 실패: {rel_out} (render.mjs exit {r.returncode})")


# ── ④ 검증 ──────────────────────────────────────────────────────────────────
def verify_output(out: Path, src_video: Path, cw: int, ch: int, fw: int, fh: int,
                  points, tmp: Path, *, min_psnr=22.0) -> dict:
    info = probe(out)
    problems = []
    if (info["width"], info["height"]) != (cw, ch):
        problems.append(f"해상도 {info['width']}x{info['height']} ≠ {cw}x{ch}")
    if not info["has_audio"]:
        problems.append("오디오 스트림 없음")

    # 크롭 여부 실측 — 출력 중앙에서 원본이 놓인 사각형만 되꺼내 원본과 대조한다.
    x, y = (cw - fw) // 2, (ch - fh) // 2
    checks = []
    for t in points:
        a, b = tmp / "vr_out.png", tmp / "vr_src.png"
        run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.4f}", "-i", str(out), "-frames:v", "1",
             "-vf", (f"crop={fw}:{fh}:{x}:{y},"
                     f"crop=iw:ih*0.28:0:ih*0.30,scale=180:120,format=gray"), str(a)],
            label="ffmpeg 출력 크롭")
        frame_band(src_video, t, b)
        checks.append(round(psnr(a, b), 2))
    worst = min(checks) if checks else 0.0
    if worst < min_psnr:
        problems.append(f"원본 대조 PSNR 최저 {worst} < {min_psnr} — 잘렸거나 어긋났을 수 있음")
    return {"width": info["width"], "height": info["height"],
            "duration_s": round(info["duration"], 3), "has_audio": info["has_audio"],
            "inner_box": f"{fw}x{fh}@{x},{y}",
            "margin_px": {"x": x, "y": y},
            "no_crop_psnr": checks, "problems": problems}


# ── main ────────────────────────────────────────────────────────────────────
def main() -> int:
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    p = argparse.ArgumentParser(description="완성 영상을 여러 비율로 크롭 없이 내보낸다")
    p.add_argument("--run", required=True, help="런 폴더 (예: output/20260813-melasma-oil)")
    p.add_argument("--video", default="final.mp4", help="자막 없는 영상 소스 (기본 final.mp4)")
    p.add_argument("--audio", default=None,
                   help="오디오를 가져올 완성본 (캡컷 BGM본). 생략하면 --video 자체 오디오")
    p.add_argument("--ratios", default=",".join(cfg["ratios"]), help="쉼표 구분 (기본 전부)")
    p.add_argument("--outdir", default="exports", help="런 폴더 아래 출력 폴더명")
    p.add_argument("--fps", type=float, default=None, help="출력 fps (기본: 소스 실측)")
    p.add_argument("--crf", type=int, default=14)
    p.add_argument("--pad-crf", type=int, default=12, help="중간 패딩본 crf (자막 렌더의 입력)")
    p.add_argument("--codec", default="h264", choices=["h264", "h265"])
    p.add_argument("--preset", default="vox-기본", help="자막 프리셋")
    p.add_argument("--no-captions", action="store_true", help="자막 재렌더 없이 패딩만")
    p.add_argument("--keep-intermediates", action="store_true")
    p.add_argument("--align-points", default="3,8,18,25,32,38")
    p.add_argument("--skip-align-check", action="store_true",
                   help="정렬 검증 생략 (어긋난 소스를 알면서 강행할 때만)")
    a = p.parse_args()

    run_dir = Path(a.run).resolve()
    if not run_dir.is_dir():
        die(f"런 폴더가 없습니다: {run_dir}")
    video = run_dir / a.video
    if not video.exists():
        die(f"영상 소스가 없습니다: {video}")
    audio_src = (run_dir / a.audio) if a.audio else None
    if audio_src is not None and not audio_src.exists():
        die(f"오디오 소스가 없습니다: {audio_src}")

    captions = run_dir / "captions.json"
    if not a.no_captions and not captions.exists():
        die(f"captions.json이 없습니다: {captions} (7.5단계 make_captions.mjs를 먼저 실행)")

    want = [r.strip() for r in a.ratios.split(",") if r.strip()]
    unknown = [r for r in want if r not in cfg["ratios"]]
    if unknown:
        die(f"모르는 비율: {unknown} (가능: {list(cfg['ratios'])})")

    src = probe(video)
    fps = a.fps if a.fps else (src["fps"] or 30.0)
    out_dir = run_dir / a.outdir
    out_dir.mkdir(exist_ok=True)
    tmp = out_dir / ".tmp"
    tmp.mkdir(exist_ok=True)

    print(f"소스   {video.name}  {src['width']}x{src['height']}  "
          f"{src['fps']:g}fps  {src['duration']:.3f}s  오디오={'있음' if src['has_audio'] else '없음'}")
    if audio_src is not None:
        asrc = probe(audio_src)
        print(f"오디오 {audio_src.name}  {asrc['width']}x{asrc['height']}  "
              f"{asrc['fps']:g}fps  {asrc['duration']:.3f}s")
    print(f"출력   fps={fps:g}  crf={a.crf}  codec={a.codec}  "
          f"자막={'끔' if a.no_captions else a.preset}  비율={want}")

    points = [float(x) for x in a.align_points.split(",") if x.strip()]
    points = [t for t in points if t < min(src["duration"], 1e9) - 0.5]

    # ① 정렬 검증
    if audio_src is not None and not a.skip_align_check:
        print("\n[1/4] 정렬 검증 — 영상 소스와 오디오 소스가 같은 타임라인인가")
        rows, bad = verify_alignment(video, audio_src, points, fps, tmp)
        for r in rows:
            print(f"   {r['t']:5.1f}s  shift {r['shift_frames']:+d}f  PSNR {r['psnr']:6.2f}")
        if bad:
            die("두 소스의 타임라인이 어긋납니다 — 위 PSNR이 낮은 지점을 보세요.\n"
                "       캡컷에서 자르기·순서 변경을 했다면 이 경로는 쓸 수 없습니다.\n"
                "       (자막 없는 BGM본을 캡컷에서 직접 내보내 --video로 주고 --audio를 빼세요)")
        shifts = [r["shift_frames"] for r in rows]
        if len(shifts) > 1 and abs(shifts[-1] - shifts[0]) > 2:
            die(f"시간 드리프트 감지 (처음 {shifts[0]:+d}f → 끝 {shifts[-1]:+d}f) — 속도가 다릅니다")
        print("   → 정렬 확인. 오디오를 옮겨도 안전합니다.")
    elif audio_src is not None:
        print("\n[1/4] 정렬 검증 생략 (--skip-align-check)")
    else:
        print("\n[1/4] 정렬 검증 불필요 (--audio 없음, 소스 자체 오디오 사용)")

    results = {}
    for i, ratio in enumerate(want, 1):
        spec = cfg["ratios"][ratio]
        cw, ch, slug = spec["width"], spec["height"], spec["slug"]
        pad = out_dir / f".pad_{slug}.mp4"
        final = out_dir / f"final_{slug}.mp4"

        print(f"\n[2/4] {ratio} ({cw}x{ch}) 패딩 — {i}/{len(want)}")
        fw, fh = pad_ratio(video, audio_src, pad, src, cw, ch, cfg["background"], fps, a.pad_crf)
        print(f"   원본 {fw}x{fh} 중앙 배치, 좌우 여백 {(cw-fw)//2}px · 상하 {(ch-fh)//2}px")

        if a.no_captions:
            shutil.move(str(pad), str(final))
        else:
            print(f"[3/4] {ratio} 자막·헤드카피 재렌더")
            render_captions(run_dir, f"{a.outdir}/.pad_{slug}.mp4",
                            f"{a.outdir}/final_{slug}.mp4", a.crf, a.codec, a.preset)

        print(f"[4/4] {ratio} 검증")
        results[ratio] = verify_output(final, video, cw, ch, fw, fh, points, tmp)
        for k in ("width", "height", "duration_s", "inner_box", "no_crop_psnr", "problems"):
            print(f"   {k}: {results[ratio][k]}")

        if not a.keep_intermediates and pad.exists():
            pad.unlink()

    if not a.keep_intermediates:
        shutil.rmtree(tmp, ignore_errors=True)

    report = out_dir / "export-report.json"
    report.write_text(json.dumps({
        "source": {"video": a.video, "audio": a.audio, **{k: src[k] for k in ("width", "height", "fps", "duration")}},
        "fps": fps, "crf": a.crf, "codec": a.codec,
        "captions": (None if a.no_captions else a.preset),
        "ratios": results,
    }, ensure_ascii=False, indent=1), encoding="utf-8")

    failed = [r for r, v in results.items() if v["problems"]]
    print(f"\n리포트: {report}")
    if failed:
        print(f"[실패] 문제 있는 비율: {failed}", file=sys.stderr)
        return 1
    print(f"[완료] {len(results)}개 비율 — {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
