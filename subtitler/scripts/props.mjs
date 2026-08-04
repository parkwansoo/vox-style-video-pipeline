// 렌더(render.mjs)와 스튜디오 준비(prepare-studio.mjs)가 공유하는 props 구성.
// 두 경로가 같은 값을 보게 해 "스튜디오에서 본 것 ≠ 렌더 결과" 어긋남을 막는다.
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
export const SUBTITLER = path.dirname(HERE);

export function probeVideo(src) {
  const probe = JSON.parse(execFileSync("ffprobe", [
    "-v", "error", "-select_streams", "v:0",
    "-show_entries", "stream=width,height,avg_frame_rate",
    "-show_entries", "format=duration", "-of", "json", src,
  ], { encoding: "utf8" }));
  const stream = probe.streams[0];
  const [num, den] = stream.avg_frame_rate.split("/").map(Number);
  let fps = den ? num / den : Number(num);
  // concat 산물은 avg가 23.897처럼 흔들린다 — 정수에 가까우면 스냅
  if (Math.abs(fps - Math.round(fps)) < 0.2) fps = Math.round(fps);
  return {
    width: stream.width,
    height: stream.height,
    fps,
    durationMs: Math.round(parseFloat(probe.format.duration) * 1000),
  };
}

export function loadPreset(presetName) {
  const presets = JSON.parse(fs.readFileSync(
    path.join(SUBTITLER, "config", "caption-preset.json"), "utf8"));
  const p = presets[presetName];
  if (!p) throw new Error(`프리셋 없음: ${presetName}`);
  return p;
}

// 모든 prop을 완전 명시로 만든다 — inputProps에 없는 키는 defaultProps로
// 채워지는데, 그 잔여값이 자막 폭을 조인 실사고가 있었다(2026-08-04).
export function buildInputProps({ src, captionsPath, presetName, asset }) {
  const video = probeVideo(src);
  const captions = JSON.parse(fs.readFileSync(captionsPath, "utf8"));
  const p = loadPreset(presetName);
  const inputProps = {
    가로: video.width, 세로: video.height, fps: video.fps, 영상길이ms: video.durationMs,
    폰트: p.fontKey, 글자굵기: p.fontWeight, 글자크기: p.fontSizePct,
    글자색: p.textColor, 외곽선색: p.strokeColor,
    // 외곽선은 px 단위라 높이에 비례 보정 (프리셋 기준 1920px)
    외곽선두께: Math.max(1, Math.round(p.strokeWidthPx * video.height / 1920)),
    강조색1: p.highlightColor1, 강조색2: p.highlightColor2,
    강조단어: [], 강조단어2: [],  // vox 기본: 강조색 미사용 (사용자 확정)
    등장효과: p.entrance, 효과세기: p.effectStrength,
    자막높이: p.captionYPct, 안전여백: p.safeMarginPct,
    자막최대너비: p.captionMaxWidthPct,
    자막목록: captions,
    장면목록: [{ startMs: 0, endMs: video.durationMs, type: "video", asset, volume: 1 }],
  };
  return { inputProps, video, captions };
}
