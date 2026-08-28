#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""완성 영상을 여러 출력 비율로 내보낸다 — 크롭 없이(contain + 블러 확대 배경).

파이프라인 9단계. 1~8단계 산출물은 읽기만 하고 고치지 않는다.

  ⓪ 글자 기하  자막·훅·라벨이 캔버스에서 잘리거나 두 줄로 터지지 않는지
               렌더 전에 계산한다. 고장은 실패, 취향은 경고(--strict로 승격).
               --check-only로 렌더 없이 크기만 튜닝할 수 있다.
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
      --video final_wm.mp4 --audio "0818 (1).mp4"   # 워터마크 제거본을 준다

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
# 훅 자동 배율의 하한. 이보다 내리면 헤드가 자막 크기에 근접해 위계가 뒤집힌다
# (2026-08-28 실측: 0.86에서 16:9의 헤드/자막 비가 0.99가 됐다).
HOOK_SCALE_FLOOR = 0.90
METRICS = HERE / "caption-font-metrics.json"
PROPS_MJS = PROJECT / "subtitler" / "scripts" / "props.mjs"


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
def render_captions(run_dir: Path, rel_in: str, rel_out: str, crf: int, codec: str, preset: str,
                    hook_scale: float = 1.0) -> None:
    cmd = ["node", str(RENDER_MJS), "--run", str(run_dir),
           "--video", rel_in, "--out", rel_out,
           "--crf", str(crf), "--codec", codec, "--preset", preset,
           "--headline-scale", f"{hook_scale:.4f}"]
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


# ── ⓪ 글자 기하 프리플라이트 ────────────────────────────────────────────────
# 렌더 한 벌이 1분 이상이라, 손으로 계산하던 것을 앞으로 당겨 몇 초에 잡는다.
# **고장은 막고 취향은 막지 않는다** — 글자 크기는 편마다 바뀌는 값이라
# 하드 실패는 "무슨 값을 넣든 화면이 깨지는 것"에만 건다.
#   실패: 자막이 두 줄로 터짐 · 훅/라벨이 가로로 잘림 · 훅 블록이 상하로 잘림
#   경고: 훅이 원본 영상을 덮음 · 헤드가 자막보다 작음 · override 없음
# 경고를 실패로 올리려면 --strict.

def em_width(text: str, m: dict) -> float:
    """폰트 실측 폭을 em으로. make_captions.mjs:112와 같은 식."""
    u = 0
    for ch in text:
        u += m["space"] if ch == " " else m["chars"].get(ch, m["hangul"])
    return u / m["unitsPerEm"]


def resolve_presets(preset_name: str, sizes) -> list:
    """비율별 병합 프리셋을 props.mjs에서 받아온다.

    병합 로직을 파이썬에 복사하면 두 정의가 갈라진다 (20번에서 실제로 난 사고 —
    LAYOUT_RATIOS 하드코딩 평행 정의). props.mjs를 단일 정본으로 둔다.
    """
    script = (
        f"import {{ loadPreset, resolvePresetForRatio }} from {json.dumps(PROPS_MJS.as_uri())};\n"
        f"const raw = loadPreset({json.dumps(preset_name)});\n"
        f"const out = [];\n"
        f"for (const [w, h] of {json.dumps(list(sizes))}) {{\n"
        f"  const {{ preset, ratio }} = resolvePresetForRatio(raw, w, h);\n"
        f"  out.push({{ ratio, preset,\n"
        f"    hasOverride: Boolean(raw.ratioOverrides && ratio && raw.ratioOverrides[ratio]) }});\n"
        f"}}\n"
        f"console.log(JSON.stringify(out));\n"
    )
    r = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stdout); sys.stderr.write(r.stderr)
        die("프리셋 해석 실패 (props.mjs)")
    return json.loads(r.stdout)


def preflight(run_dir, want, cfg, preset_name, src, hook_cover_max, strict):
    """렌더 전에 자막·헤드·라벨의 기하를 계산해 깨질 조합을 걸러낸다."""
    caps_p, head_p = run_dir / "captions.json", run_dir / "headline.json"
    metrics_all = json.loads(METRICS.read_text(encoding="utf-8"))
    caps = json.loads(caps_p.read_text(encoding="utf-8"))
    head = json.loads(head_p.read_text(encoding="utf-8")) if head_p.exists() else {}
    hook_lines = (head.get("hook") or {}).get("lines") or []
    label_text = (head.get("label") or {}).get("text") or ""
    # 편별 훅 배율. headline.json에 fontScale을 직접 적었으면 그 값이 최우선이고,
    # 없으면 문구 길이에서 **자동 산출**한다 (편마다 문구가 달라 고정값이 안 맞는다).
    _fs = (head.get("hook") or {}).get("fontScale")
    explicit_scale = float(_fs) if isinstance(_fs, (int, float)) and _fs > 0 else None

    sizes = [(cfg["ratios"][r]["width"], cfg["ratios"][r]["height"]) for r in want]
    resolved = resolve_presets(preset_name, sizes)

    metrics_for = lambda pr: metrics_all.get(pr["fontKey"])
    hook_em_all = 0.0
    if hook_lines:
        m0 = metrics_for(resolved[0]["preset"])
        if m0:
            hook_em_all = max(em_width(t, m0) for t in hook_lines)

    hook_scale = explicit_scale if explicit_scale is not None else 1.0
    auto_scale = None
    if hook_lines and explicit_scale is None and hook_em_all:
        # 각 비율에서 허용되는 최대 배율을 풀고 가장 빡빡한 것을 택한다.
        limits = []
        for r, (W, H), res in zip(want, sizes, resolved):
            pr = res["preset"]
            base_px = pr["headlineFontSizePct"] / 100 * H       # 배율 1일 때 글자 크기
            if base_px <= 0:
                continue
            fw, _fh = fit_size(src["width"], src["height"], W, H)
            safe_w = W * (100 - 2 * pr["safeMarginPct"]) / 100
            safe_t = pr["safeMarginPct"] / 100 * H
            limits.append(safe_w / (hook_em_all * base_px))                    # 가로 폭
            if fw:
                limits.append(hook_cover_max * fw / (hook_em_all * base_px))   # 영상 폭 대비
            # 세로: top = YPct*H - (줄수 × px × 1.2)/2 ≥ 안전선
            head_top = pr["headlineYPct"] / 100 * H
            denom = len(hook_lines) * base_px * 1.2 / 2
            if denom > 0:
                limits.append((head_top - safe_t) / denom)
        if limits:
            auto_scale = math.floor(min(1.0, min(limits)) * 100) / 100
            if auto_scale < HOOK_SCALE_FLOOR:
                die(f"훅이 너무 길다 — 배율 {auto_scale:.2f}까지 줄여야 들어가는데 "
                    f"하한은 {HOOK_SCALE_FLOOR:.2f}다 (그 아래로 내리면 헤드가 자막보다 "
                    f"작아져 훅 구실을 못 한다). 문구를 줄이거나 hook.lines의 줄 나눔을 "
                    f"바꾸세요 — 현재 {len(hook_lines)}줄, 최장 {hook_em_all:.2f}em")
            hook_scale = auto_scale

    fails, warns, rows = [], [], []
    for r, (W, H), res in zip(want, sizes, resolved):
        pr = res["preset"]
        m = metrics_all.get(pr["fontKey"])
        if not m:
            die(f"폰트 메트릭 없음: {pr['fontKey']} — measure_font_metrics.py를 실행하세요")
        cap_em = max((em_width(c["text"], m) for c in caps), default=0.0)
        hook_em = max((em_width(t, m) for t in hook_lines), default=0.0)
        lab_em = em_width(label_text, m) if label_text else 0.0

        fw, fh = fit_size(src["width"], src["height"], W, H)
        safe_w = W * (100 - 2 * pr["safeMarginPct"]) / 100
        safe_t = pr["safeMarginPct"] / 100 * H

        # 자막 — 예산은 make_captions.mjs:52-55와 같은 식
        cap_px = pr["fontSizePct"] / 100 * H
        cap_avail = pr["captionMaxWidthPct"] / 100 * W - W * 0.0185
        budget = cap_avail / cap_px if cap_px else 0.0
        if cap_em and budget < cap_em:
            fails.append(f"{r}: 자막 한 줄 예산 {budget:.2f}em < 최장 {cap_em:.2f}em — 화면에서 두 줄로 터진다")

        # 훅 — Headline.tsx는 top:% + translateY(-50%), lineHeight 1.2
        hook_px = pr["headlineFontSizePct"] * hook_scale / 100 * H
        hook_w = hook_em * hook_px
        block = len(hook_lines) * hook_px * 1.2
        top = pr["headlineYPct"] / 100 * H - block / 2
        cover = hook_w / fw if fw else 0.0
        if hook_lines:
            if hook_w > safe_w:
                fails.append(f"{r}: 훅 최장줄 {hook_w:.0f}px > 가용 {safe_w:.0f}px — 가로로 잘린다")
            if top < safe_t:
                fails.append(f"{r}: 훅 상단 {top:.0f}px < 안전선 {safe_t:.0f}px — 윗줄이 잘린다")
            if top + block > H - safe_t:
                fails.append(f"{r}: 훅 하단 {top + block:.0f}px > {H - safe_t:.0f}px — 아랫줄이 잘린다")
            if cover > hook_cover_max:
                warns.append(f"{r}: 훅이 원본 영상 폭의 {cover*100:.0f}% (기준 {hook_cover_max*100:.0f}%) — 훅 구간을 가린다")
            if pr["headlineFontSizePct"] * hook_scale <= pr["fontSizePct"]:
                warns.append(f"{r}: 헤드 {pr['headlineFontSizePct'] * hook_scale:.2f}% ≤ 자막 {pr['fontSizePct']}% — 위계가 뒤집힌다")

        # 라벨 — 박스 좌우 패딩 포함 (props.mjs 라벨여백가로)
        lab_px = pr["labelFontSizePct"] / 100 * H
        lab_w = lab_em * lab_px + 2 * round(33 * H / 1920) if lab_em else 0.0
        if lab_em:
            if lab_w > safe_w:
                fails.append(f"{r}: 라벨 {lab_w:.0f}px > 가용 {safe_w:.0f}px — 가로로 잘린다")
            lab_top = pr["labelYPct"] / 100 * H - lab_px * 1.2 / 2
            if lab_top < safe_t:
                fails.append(f"{r}: 라벨 상단 {lab_top:.0f}px < 안전선 {safe_t:.0f}px — 잘린다")

        if res["ratio"] is None:
            warns.append(f"{r}: {W}x{H}가 알려진 비율과 안 맞아 기본 프리셋으로 간다")
        elif not res["hasOverride"] and res["ratio"] != cfg.get("defaultRatio"):
            warns.append(f"{r}: ratioOverrides에 항목이 없어 9:16 크기 그대로 간다 (화면 폭 대비 작아진다)")

        rows.append((r, f"{W}x{H}", cap_px, budget, cap_em, hook_px, cover, top, safe_t,
                     pr["headlineFontSizePct"] * hook_scale / pr["fontSizePct"]))

    print(f"   최장 자막 {cap_em:.2f}em · 훅 최장줄 {hook_em:.2f}em · 라벨 {lab_em:.2f}em")
    print("   비율   캔버스      자막px  예산em  훅px  훅폭/영상  훅상단/안전선  헤드/자막")
    for (r, wh, cpx, bud, cem, hpx, cov, top, st, ratio_hc) in rows:
        print(f"   {r:6s} {wh:11s} {cpx:6.0f} {bud:7.2f} {hpx:5.0f} "
              f"{cov*100:8.0f}% {top:8.0f}/{st:<5.0f} {ratio_hc:9.2f}")
    for w in warns: print(f"   [경고] {w}")
    if fails:
        for f in fails: print(f"   [실패] {f}", file=sys.stderr)
        die("글자 기하가 깨진다 — 위 항목을 고치고 다시 실행하세요 "
            "(caption-preset.json의 ratioOverrides)")
    if warns and strict:
        die("--strict: 경고를 실패로 처리합니다")
    if hook_lines:
        if explicit_scale is not None:
            print(f"   훅 배율 {explicit_scale:.2f} (headline.json에 명시)")
        elif auto_scale is not None and auto_scale < 1.0:
            print(f"   훅 배율 {auto_scale:.2f} 자동 적용 — 문구가 길어 그만큼 줄였다")
    if not warns:
        print("   → 전부 통과")
    return hook_scale


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
    p.add_argument("--check-only", action="store_true",
                   help="글자 기하만 계산하고 끝낸다 (렌더 없음 — 크기 튜닝용)")
    p.add_argument("--strict", action="store_true", help="경고도 실패로 처리")
    p.add_argument("--hook-cover-max", type=float, default=1.10,
                   help="훅 가로폭 ÷ 원본 영상 폭 경고 기준 (기본 1.10, 9:16 실측 0.85)")
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

    # ⓪ 글자 기하 — 렌더보다 먼저, 가장 싸다
    hook_scale = 1.0
    if not a.no_captions:
        print("\n[1/5] 글자 기하 검증")
        hook_scale = preflight(run_dir, want, cfg, a.preset, src, a.hook_cover_max, a.strict)
        if a.check_only:
            print("\n[완료] --check-only: 렌더하지 않고 끝냅니다")
            return 0
    elif a.check_only:
        die("--check-only는 자막이 있을 때만 의미가 있습니다 (--no-captions와 함께 못 씁니다)")

    points = [float(x) for x in a.align_points.split(",") if x.strip()]
    points = [t for t in points if t < min(src["duration"], 1e9) - 0.5]

    # ① 정렬 검증
    if audio_src is not None and not a.skip_align_check:
        print("\n[2/5] 정렬 검증 — 영상 소스와 오디오 소스가 같은 타임라인인가")
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
        print("\n[2/5] 정렬 검증 생략 (--skip-align-check)")
    else:
        print("\n[2/5] 정렬 검증 불필요 (--audio 없음, 소스 자체 오디오 사용)")

    results = {}
    for i, ratio in enumerate(want, 1):
        spec = cfg["ratios"][ratio]
        cw, ch, slug = spec["width"], spec["height"], spec["slug"]
        pad = out_dir / f".pad_{slug}.mp4"
        final = out_dir / f"final_{slug}.mp4"

        print(f"\n[3/5] {ratio} ({cw}x{ch}) 패딩 — {i}/{len(want)}")
        fw, fh = pad_ratio(video, audio_src, pad, src, cw, ch, cfg["background"], fps, a.pad_crf)
        print(f"   원본 {fw}x{fh} 중앙 배치, 좌우 여백 {(cw-fw)//2}px · 상하 {(ch-fh)//2}px")

        if a.no_captions:
            shutil.move(str(pad), str(final))
        else:
            print(f"[4/5] {ratio} 자막·헤드카피 재렌더")
            render_captions(run_dir, f"{a.outdir}/.pad_{slug}.mp4",
                            f"{a.outdir}/final_{slug}.mp4", a.crf, a.codec, a.preset,
                            hook_scale)

        print(f"[5/5] {ratio} 검증")
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
