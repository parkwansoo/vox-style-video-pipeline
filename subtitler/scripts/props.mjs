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
// 강조 단어는 편마다 다르므로 런 폴더의 highlights.json에서 읽는다.
// 파일이 없으면 빈 배열 — 강조색을 안 쓰던 기존 동작 그대로다.
// 형식: {"강조단어": ["41%", "미백"], "강조단어2": []}
// 색은 프리셋의 강조색1(노랑) / 강조색2(빨강)를 쓰고, 토큰이 단어를 포함하면
// 칠해지므로("기미"가 "기미가"에 걸린다) 자주 나오는 말은 넣지 않는다.
function loadHighlights(captionsPath) {
  const p = path.join(path.dirname(captionsPath), "highlights.json");
  if (!fs.existsSync(p)) return { 강조단어: [], 강조단어2: [] };
  const h = JSON.parse(fs.readFileSync(p, "utf8"));
  return {
    강조단어: Array.isArray(h.강조단어) ? h.강조단어 : [],
    강조단어2: Array.isArray(h.강조단어2) ? h.강조단어2 : [],
  };
}

// 헤드 카피는 편마다 문구·타이밍이 다르므로 런 폴더의 headline.json에서 읽는다
// (highlights.json과 같은 방식). 파일이 없으면 빈 배열 — 헤드 없이 기존 그대로 렌더된다.
// 형식: {"lines": ["기미의 핵심은", "레이저가 아닙니다"], "startMs": 0, "endMs": 3000}
// 줄바꿈은 lines 배열이 결정한다. 화면 폭을 넘기면 잘리므로 한 줄 길이는
// 폰트 메트릭으로 미리 확인한다 (720px 폭·안전여백 6%·6.0% 크기 기준 최대 8.25em).
function loadHeadline(captionsPath) {
  const p = path.join(path.dirname(captionsPath), "headline.json");
  if (!fs.existsSync(p)) return { lines: [], startMs: 0, endMs: 0 };
  const h = JSON.parse(fs.readFileSync(p, "utf8"));
  return {
    lines: Array.isArray(h.lines) ? h.lines : [],
    startMs: Number.isFinite(h.startMs) ? h.startMs : 0,
    endMs: Number.isFinite(h.endMs) ? h.endMs : 0,
  };
}

export function buildInputProps({ src, captionsPath, presetName, asset }) {
  const video = probeVideo(src);
  const captions = JSON.parse(fs.readFileSync(captionsPath, "utf8"));
  const p = loadPreset(presetName);
  const hl = loadHighlights(captionsPath);
  const hd = loadHeadline(captionsPath);
  const inputProps = {
    가로: video.width, 세로: video.height, fps: video.fps, 영상길이ms: video.durationMs,
    폰트: p.fontKey, 글자굵기: p.fontWeight, 글자크기: p.fontSizePct,
    글자색: p.textColor, 외곽선색: p.strokeColor,
    // 외곽선은 px 단위라 높이에 비례 보정 (프리셋 기준 1920px)
    외곽선두께: Math.max(1, Math.round(p.strokeWidthPx * video.height / 1920)),
    강조색1: p.highlightColor1, 강조색2: p.highlightColor2,
    강조단어: hl.강조단어, 강조단어2: hl.강조단어2,  // highlights.json이 없으면 빈 배열
    등장효과: p.entrance, 효과세기: p.effectStrength,
    자막높이: p.captionYPct, 안전여백: p.safeMarginPct,
    자막최대너비: p.captionMaxWidthPct,
    // 헤드 카피 — headline.json이 없으면 문구가 빈 배열이라 레이어 자체가 안 붙는다.
    헤드라인문구: hd.lines, 헤드라인시작ms: hd.startMs, 헤드라인종료ms: hd.endMs,
    헤드라인크기: p.headlineFontSizePct ?? 6.0,
    헤드라인색: p.headlineColor ?? p.highlightColor1,
    헤드라인외곽선색: p.headlineStrokeColor ?? p.strokeColor,
    // 자막 외곽선과 같은 규칙으로 높이 비례 보정 (프리셋 기준 1920px)
    헤드라인외곽선두께: Math.max(1, Math.round((p.headlineStrokeWidthPx ?? 6) * video.height / 1920)),
    헤드라인높이: p.headlineYPct ?? 18,
    스크림높이: p.headlineScrimPct ?? 30,
    스크림농도: p.headlineScrimOpacity ?? 0.45,
    자막목록: captions,
    장면목록: [{ startMs: 0, endMs: video.durationMs, type: "video", asset, volume: 1 }],
  };
  return { inputProps, video, captions };
}
