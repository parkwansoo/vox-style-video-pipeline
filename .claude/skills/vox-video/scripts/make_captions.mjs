// 나레이션 어절 타임스탬프(words.json)를 최종 영상 시간축의 자막 조각으로 변환한다.
//
// 사용법:
//   node make_captions.mjs --run output/<run> [--max-chars 16] [--min-dur-ms 700]
//
// 입력: <run>/timeline.json (assemble.py 산출), <run>/ch<N>/words.json
// 출력: <run>/captions.json  [{text, startMs, endMs}]
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {segmentCaptions, setCaptionMetrics} from './segment.mjs';

function arg(name, fallback = null) {
  const i = process.argv.indexOf(name);
  return i >= 0 && i + 1 < process.argv.length ? process.argv[i + 1] : fallback;
}

const runDir = arg('--run');
if (!runDir) {
  console.error('사용법: node make_captions.mjs --run output/<run> [--font-px 91] [--avail-px 930] [--min-dur-ms 700]');
  process.exit(1);
}
// 자막은 한 줄로 나와야 한다. 조각 길이를 글자 수가 아니라 렌더 폭으로 정하고,
// 폭은 실제 폰트 메트릭(caption-font-metrics.json)으로 잰다. 예산은 timeline의
// 해상도와 렌더 프리셋(subtitler/config/caption-preset.json)에서 자동 계산하므로
// 720x1280이든 1080x1920이든 같은 비율로 잘린다. --font-px/--avail-px로 덮어쓰기 가능.
const here = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(here, '../../../..');
const minDurMs = Number(arg('--min-dur-ms', 700));
const outPath = arg('--out', path.join(runDir, 'captions.json'));

const timeline = JSON.parse(fs.readFileSync(path.join(runDir, 'timeline.json'), 'utf8'));

// 폭 예산: 글자 크기 = 높이 × fontSizePct, 가용 폭 = 너비 × min(최대너비, 100-여백×2)
// − 여유분(1080 기준 20px 상당). 렌더(render.mjs)와 같은 프리셋을 읽어 일치를 보장한다.
const presetName = arg('--preset', 'vox-기본');
const presets = JSON.parse(fs.readFileSync(
  path.join(repoRoot, 'subtitler', 'config', 'caption-preset.json'), 'utf8'));
const preset = presets[presetName];
if (!preset) { console.error(`프리셋 없음: ${presetName}`); process.exit(1); }

// 메트릭은 폰트별로 실측돼 있다 (한글 폭이 폰트마다 0.83~0.96em으로 다르다).
// 프리셋의 폰트가 측정에 없으면 measure_font_metrics.py를 먼저 돌린다.
const allMetrics = JSON.parse(fs.readFileSync(path.join(here, 'caption-font-metrics.json'), 'utf8'));
const metrics = allMetrics[preset.fontKey];
if (!metrics) {
  console.error(`폰트 메트릭 없음: ${preset.fontKey} — measure_font_metrics.py를 실행하세요`);
  process.exit(1);
}
setCaptionMetrics(metrics);
const fontPx = Number(arg('--font-px',
  (preset.fontSizePct / 100) * timeline.height));
const widthPct = Math.min(preset.captionMaxWidthPct ?? 100, 100 - 2 * preset.safeMarginPct);
const availPx = Number(arg('--avail-px',
  (widthPct / 100) * timeline.width - timeline.width * 0.0185));
// 한글 한 글자 = 1 로 환산한 예산. 예: 620px / (60.7px × 0.962) = 10.6글자분
const maxChars = availPx / (fontPx * (metrics.hangul / metrics.unitsPerEm));

// 나레이션은 배속 없이 각 클립 시작점에 재배치된다(assemble.py 3단계). 따라서 챕터
// 타임라인의 시각 t는 t를 담은 클립의 offset 기준으로 옮기면 된다. offset을 seg_start로
// 대신 계산하면 안 된다 — 프레임 반올림 오차가 누적된다(이 런 실측 +0.115s).
const wordsCache = new Map();
function loadWords(narrationPath) {
  const p = path.join(path.dirname(narrationPath), 'words.json');
  if (!wordsCache.has(p)) wordsCache.set(p, JSON.parse(fs.readFileSync(p, 'utf8')));
  return wordsCache.get(p);
}

const captions = [];
for (const clip of timeline.clips) {
  const words = loadWords(clip.narration);
  const isLast = clip.clip === Math.max(
    ...timeline.clips.filter((c) => c.chapter === clip.chapter).map((c) => c.clip),
  );
  // 어절 배정: 시작 시각이 이 클립 구간 안에 드는 것. 챕터 마지막 클립은 구간을 넘어
  // 시작하는 꼬리 어절까지 흡수한다(나레이션 끝이 seg_end보다 길 수 있다).
  const picked = words.filter((w) => w.start >= clip.seg_start
    && (w.start < clip.seg_end || (isLast && w.start >= clip.seg_end)));
  if (picked.length === 0) continue;

  const limit = clip.offset + clip.duration;
  const texts = picked.map((w) => w.word);
  const timings = picked.map((w) => {
    const start = clip.offset + (w.start - clip.seg_start);
    const end = clip.offset + (Math.min(w.end, clip.seg_end) - clip.seg_start);
    return {
      start: Math.max(clip.offset, Math.min(start, limit)),
      end: Math.max(start, Math.min(end, limit)),
      matched: true,
    };
  });
  // 클립별로 나눠 부르므로 자막 조각이 컷 경계를 넘지 않는다.
  for (const cap of segmentCaptions(texts, timings, {maxChars, minDurMs})) {
    captions.push({text: cap.text, startMs: cap.startMs, endMs: cap.endMs});
  }
}

// 전역 후처리: segmentCaptions의 최소 표시시간 연장은 클립 안에서만 다음 조각을 알기에,
// 클립 경계를 넘어 다음 조각을 침범할 수 있다. 여기서 다시 조인다.
const totalMs = Math.round(timeline.total_duration * 1000);
for (let i = 0; i < captions.length; i++) {
  const limit = i + 1 < captions.length ? captions[i + 1].startMs : totalMs;
  captions[i].endMs = Math.min(captions[i].endMs, limit);
  if (captions[i].endMs <= captions[i].startMs) captions[i].endMs = captions[i].startMs + 1;
}

fs.writeFileSync(outPath, JSON.stringify(captions, null, 1), 'utf8');

// 렌더 폭 자체 검증 — 한 조각이라도 예산을 넘으면 화면에서 두 줄이 된다.
const pxOf = (t) => {
  let u = 0;
  for (const ch of t) u += ch === ' ' ? metrics.space : (metrics.chars[ch] ?? metrics.hangul);
  return (u / metrics.unitsPerEm) * fontPx;
};
const widest = captions.reduce((m, c) => Math.max(m, pxOf(c.text)), 0);
const overflow = captions.filter((c) => pxOf(c.text) > availPx).map((c) => c.text);

const shortest = captions.filter((c) => c.endMs - c.startMs < minDurMs).length;
console.log(JSON.stringify({
  out: outPath,
  count: captions.length,
  first_ms: captions[0]?.startMs ?? null,
  last_ms: captions.at(-1)?.endMs ?? null,
  total_ms: totalMs,
  widest_px: Math.round(widest),
  avail_px: availPx,
  overflow,
  under_min_dur: shortest,
}, null, 1));
if (overflow.length) process.exitCode = 1;
