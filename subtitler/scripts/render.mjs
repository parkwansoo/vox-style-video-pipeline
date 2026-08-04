// 완성 영상 위에 자막을 렌더한다 (Node API — 20번 render-video.mjs:110-161 미러).
//
// 사용법:
//   node subtitler/scripts/render.mjs --run output/<run> \
//     [--video final.mp4] [--out final_sub.mp4] [--captions captions.json] \
//     [--preset vox-기본] [--crf 14] [--codec h264|h265]
//
// 입력 영상의 해상도·fps를 그대로 따른다 (24fps 원본이면 24fps 유지).
// 모든 prop을 완전 명시로 전달한다 — inputProps에 없는 키는 defaultProps로
// 채워지는데, 그 잔여값이 자막 폭을 조인 실사고가 있었다(2026-08-04).
import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SUBTITLER = path.dirname(HERE);

function arg(name, fallback = null) {
  const i = process.argv.indexOf(name);
  return i >= 0 && i + 1 < process.argv.length ? process.argv[i + 1] : fallback;
}

const runDir = arg("--run");
if (!runDir) {
  console.error("사용법: node render.mjs --run output/<run> [--video final.mp4] [--out final_sub.mp4] [--crf 14]");
  process.exit(1);
}
const src = path.resolve(runDir, arg("--video", "final.mp4"));
const outPath = path.resolve(runDir, arg("--out", "final_sub.mp4"));
const captionsPath = path.resolve(runDir, arg("--captions", "captions.json"));
const presetName = arg("--preset", "vox-기본");
const crf = Number(arg("--crf", 14));
const codec = arg("--codec", "h264");

// ① 입력 영상 규격 실측
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
const durationMs = Math.round(parseFloat(probe.format.duration) * 1000);
const { width, height } = stream;

// ② props 구성 (프리셋 + 자막)
const captions = JSON.parse(fs.readFileSync(captionsPath, "utf8"));
const presets = JSON.parse(fs.readFileSync(path.join(SUBTITLER, "config", "caption-preset.json"), "utf8"));
const p = presets[presetName];
if (!p) { console.error(`프리셋 없음: ${presetName}`); process.exit(1); }

const inputProps = {
  가로: width, 세로: height, fps, 영상길이ms: durationMs,
  폰트: p.fontKey, 글자굵기: p.fontWeight, 글자크기: p.fontSizePct,
  글자색: p.textColor, 외곽선색: p.strokeColor,
  // 외곽선은 px 단위라 높이에 비례 보정 (프리셋 기준 1920px)
  외곽선두께: Math.max(1, Math.round(p.strokeWidthPx * height / 1920)),
  강조색1: p.highlightColor1, 강조색2: p.highlightColor2,
  강조단어: [], 강조단어2: [],  // vox 기본: 강조색 미사용 (사용자 확정)
  등장효과: p.entrance, 효과세기: p.effectStrength,
  자막높이: p.captionYPct, 안전여백: p.safeMarginPct,
  자막최대너비: p.captionMaxWidthPct,
  자막목록: captions,
  장면목록: [{ startMs: 0, endMs: durationMs, type: "video", asset: "bg.mp4", volume: 1 }],
};

// ③ 스테이징 publicDir — bundle()이 publicDir 전체를 복사하므로 필요한 것만 담는다
const staging = path.join(path.resolve(runDir), ".subtitle-public");
fs.rmSync(staging, { recursive: true, force: true });
fs.mkdirSync(path.join(staging, "_fonts"), { recursive: true });
fs.copyFileSync(src, path.join(staging, "bg.mp4"));
for (const f of fs.readdirSync(path.join(SUBTITLER, "public", "_fonts"))) {
  fs.copyFileSync(path.join(SUBTITLER, "public", "_fonts", f), path.join(staging, "_fonts", f));
}

try {
  // ④ 번들 → 컴포지션 → 렌더
  console.log(`번들 준비… (${width}x${height} ${fps}fps, ${captions.length}자막, crf ${crf})`);
  const serveUrl = await bundle({
    entryPoint: path.join(SUBTITLER, "src", "index.ts"),
    publicDir: staging,
  });
  const composition = await selectComposition({ serveUrl, id: "CaptionVideo", inputProps });
  const tmpOut = `${outPath}.render-${process.pid}.mp4`;
  let last = -1;
  await renderMedia({
    composition, serveUrl, codec, crf,
    outputLocation: tmpOut, inputProps,
    onProgress: ({ progress }) => {
      const pct = Math.floor(progress * 100);
      if (pct !== last) { last = pct; console.log(`PROGRESS ${pct}`); }
    },
  });

  // ⑤ 원자적 발행 (기존본은 .prev 백업)
  if (fs.existsSync(outPath)) {
    fs.renameSync(outPath, outPath.replace(/\.mp4$/, ".prev.mp4"));
  }
  fs.renameSync(tmpOut, outPath);

  // ⑥ 자체 검증 — 오디오 존재·길이·해상도. 길이는 **영상 스트림** 기준으로
  // 비교한다: Remotion이 AAC 패딩으로 오디오 꼬리를 ~0.4s 덧붙이는데(무음,
  // 20번 산출물도 동일) 컨테이너 duration은 그걸 포함해 길게 나온다.
  const chk = JSON.parse(execFileSync("ffprobe", [
    "-v", "error", "-show_entries", "stream=codec_type,width,height,duration",
    "-of", "json", outPath,
  ], { encoding: "utf8" }));
  const audio = chk.streams.find((s) => s.codec_type === "audio");
  const v = chk.streams.find((s) => s.codec_type === "video");
  const vDur = parseFloat(v.duration) * 1000;
  const problems = [];
  if (!audio) problems.push("오디오 스트림 없음");
  if (Math.abs(vDur - durationMs) > 150 + 1000 / fps) problems.push(`영상 길이 차이 ${(vDur - durationMs).toFixed(0)}ms`);
  if (v.width !== width || v.height !== height) problems.push(`해상도 ${v.width}x${v.height} ≠ ${width}x${height}`);
  console.log(JSON.stringify({
    out: outPath, width, height, fps, crf, codec,
    video_ms: Math.round(vDur),
    audio_tail_ms: audio ? Math.round(parseFloat(audio.duration) * 1000 - vDur) : null,
    captions: captions.length,
    problems,
  }, null, 1));
  if (problems.length) process.exitCode = 1;
} finally {
  fs.rmSync(staging, { recursive: true, force: true });
}
