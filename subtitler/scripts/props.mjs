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

// 비율별 override — 20번 숏츠자동화 scripts/lib/video-config.mjs의
// resolvePresetForRatio를 옮긴 것이다. 같은 %를 넓은 캔버스에 그대로 쓰면
// 화면 폭 대비 글자가 작아진다(16:9는 9:16의 0.32배). 9:16에는 override를
// 두지 않아 기존 경로(7.5단계 자막, 720x1280)가 한 값도 바뀌지 않는다.
const RATIO_OVERRIDE_FIELDS = new Set([
  "fontSizePct", "captionYPct", "safeMarginPct", "captionMaxWidthPct",
  "headlineFontSizePct", "headlineYPct", "labelFontSizePct", "labelYPct",
]);
const KNOWN_RATIOS = { "9:16": 1080 / 1920, "4:5": 1080 / 1350, "1:1": 1, "16:9": 1920 / 1080 };

// 해상도에서 비율을 판별한다 (720x1280도 9:16으로 잡힌다). 어느 것과도 2%
// 안에서 맞지 않으면 null — override 없이 기본 프리셋 그대로 간다.
export function detectRatio(width, height) {
  const a = width / height;
  let best = null;
  for (const [key, v] of Object.entries(KNOWN_RATIOS)) {
    const err = Math.abs(a - v) / v;
    if (err <= 0.02 && (best === null || err < best.err)) best = { key, err };
  }
  return best && best.key;
}

export function resolvePresetForRatio(preset, width, height) {
  const { ratioOverrides, ...base } = preset;
  if (ratioOverrides === undefined) return { preset: base, ratio: detectRatio(width, height) };
  if (!ratioOverrides || typeof ratioOverrides !== "object" || Array.isArray(ratioOverrides)) {
    throw new Error("ratioOverrides는 객체여야 합니다");
  }
  for (const [key, ov] of Object.entries(ratioOverrides)) {
    if (!(key in KNOWN_RATIOS)) throw new Error(`알 수 없는 ratioOverrides 키: ${key}`);
    if (!ov || typeof ov !== "object" || Array.isArray(ov)) {
      throw new Error(`ratioOverrides.${key}는 객체여야 합니다`);
    }
    for (const [f, v] of Object.entries(ov)) {
      if (!RATIO_OVERRIDE_FIELDS.has(f)) throw new Error(`알 수 없는 ratioOverrides 필드: ${f}`);
      if (!Number.isFinite(v)) throw new Error(`ratioOverrides.${key}.${f}는 숫자여야 합니다`);
      if (f.toLowerCase().includes("fontsizepct")) {
        if (v <= 0) throw new Error(`ratioOverrides.${key}.${f}는 0보다 커야 합니다`);
      } else if (v < 0 || v > 100) {
        throw new Error(`ratioOverrides.${key}.${f}는 0~100 범위여야 합니다`);
      }
    }
  }
  const ratio = detectRatio(width, height);
  return { preset: ratio ? { ...base, ...(ratioOverrides[ratio] || {}) } : base, ratio };
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
// (highlights.json과 같은 방식). 파일이 없으면 빈 값 — 헤드 없이 기존 그대로 렌더된다.
// 형식:
//   {"hook":  {"lines": ["기미의 핵심은", "레이저가 아닙니다"], "startMs": 0, "endMs": 3000},
//    "label": {"text": "기미의 핵심은 레이저가 아닙니다", "startMs": 3000, "endMs": 0},
//    "강조단어": ["레이저가"]}
// hook.fontScale(선택, 기본 1)로 이 편만 훅 크기를 줄인다 — 문구가 길어 한 줄이
// 넘칠 때. 절대값이 아니라 **배율**이라 비율별 보정(4:5는 6.6% 등)이 유지된다.
// 라벨 endMs 0 = 영상 끝까지. hook만 쓰거나 label만 써도 된다.
// 줄바꿈은 hook.lines 배열이 결정한다. 화면 폭을 넘기면 잘리므로 한 줄 길이는
// caption-font-metrics.json으로 미리 확인한다 (720폭·안전여백 6%에서 실효 634px:
// 훅 6.0%=76.8px이면 상한 8.25em, 라벨 3.13%=40px이면 박스 패딩 포함 14.8em).
function loadHeadline(captionsPath) {
  const empty = {
    lines: [], startMs: 0, endMs: 0, fontScale: 1,
    labelText: "", labelStartMs: 0, labelEndMs: 0, 강조단어: [],
  };
  const p = path.join(path.dirname(captionsPath), "headline.json");
  if (!fs.existsSync(p)) return empty;
  const h = JSON.parse(fs.readFileSync(p, "utf8"));
  const hook = h.hook ?? h;   // 최상위 lines만 있는 옛 형식도 훅으로 읽는다
  const label = h.label ?? {};
  return {
    lines: Array.isArray(hook.lines) ? hook.lines : [],
    startMs: Number.isFinite(hook.startMs) ? hook.startMs : 0,
    endMs: Number.isFinite(hook.endMs) ? hook.endMs : 0,
    // 편마다 문구 길이가 달라 프리셋 하나로는 안 맞는다. 배율로 받아 비율별
    // 보정 위에 곱한다 — 절대값으로 덮으면 16:9가 9:16과 같은 %가 돼 작아진다.
    fontScale: Number.isFinite(hook.fontScale) && hook.fontScale > 0 ? hook.fontScale : 1,
    labelText: typeof label.text === "string" ? label.text : "",
    labelStartMs: Number.isFinite(label.startMs) ? label.startMs : 0,
    labelEndMs: Number.isFinite(label.endMs) ? label.endMs : 0,
    강조단어: Array.isArray(h.강조단어) ? h.강조단어 : [],
  };
}

export function buildInputProps({ src, captionsPath, presetName, asset }) {
  const video = probeVideo(src);
  const captions = JSON.parse(fs.readFileSync(captionsPath, "utf8"));
  const { preset: p, ratio } = resolvePresetForRatio(loadPreset(presetName), video.width, video.height);
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
    // 헤드 카피 — headline.json이 없으면 훅·라벨 문구가 다 비어 레이어 자체가 안 붙는다.
    // px 단위 값들은 자막 외곽선과 같은 규칙으로 높이 비례 보정한다 (프리셋 기준 1920px).
    헤드라인문구: hd.lines, 헤드라인시작ms: hd.startMs, 헤드라인종료ms: hd.endMs,
    헤드라인크기: (p.headlineFontSizePct ?? 6.0) * hd.fontScale,
    헤드라인색: p.headlineColor ?? "#FFFFFF",
    헤드라인강조색: p.headlineHighlightColor ?? p.highlightColor1,
    헤드라인강조단어: hd.강조단어,
    헤드라인외곽선색: p.headlineStrokeColor ?? p.strokeColor,
    헤드라인외곽선두께: Math.max(1, Math.round((p.headlineStrokeWidthPx ?? 6) * video.height / 1920)),
    헤드라인높이: p.headlineYPct ?? 18,
    스크림높이: p.headlineScrimPct ?? 30,
    스크림농도: p.headlineScrimOpacity ?? 0.45,
    라벨문구: hd.labelText, 라벨시작ms: hd.labelStartMs, 라벨종료ms: hd.labelEndMs,
    라벨크기: p.labelFontSizePct ?? 3.13,
    라벨높이: p.labelYPct ?? 13,
    라벨외곽선두께: Math.max(1, Math.round((p.labelStrokeWidthPx ?? 3) * video.height / 1920)),
    라벨박스농도: p.labelBoxOpacity ?? 0.6,
    라벨박스라운드: Math.max(1, Math.round((p.labelBoxRadiusPx ?? 15) * video.height / 1920)),
    라벨여백가로: Math.max(1, Math.round((p.labelPadXPx ?? 33) * video.height / 1920)),
    라벨여백세로: Math.max(1, Math.round((p.labelPadYPx ?? 18) * video.height / 1920)),
    자막목록: captions,
    장면목록: [{ startMs: 0, endMs: video.durationMs, type: "video", asset, volume: 1 }],
  };
  return { inputProps, video, captions, ratio };
}
