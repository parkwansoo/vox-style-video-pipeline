// 리모션 스튜디오 검수 준비 — 20번 prepare-studio.mjs와 같은 역할.
// run의 영상·자막·프리셋을 스튜디오가 보는 곳(public/bg.mp4, src/active-input.json)에
// 동기화한다. 이후 `cd subtitler && npm run studio`로 브라우저에서 미리보며
// 오른쪽 Props 패널에서 폰트·글자크기·색·위치를 실시간으로 바꿔볼 수 있다.
//
// 사용법:
//   node subtitler/scripts/prepare-studio.mjs --run output/<run> \
//     [--video final.mp4] [--captions captions.json] [--preset vox-기본]
//
// 주의:
// - 스튜디오는 검수·튜닝 전용이다. 마음에 든 값은 config/caption-preset.json에
//   옮겨 적어야 렌더에 반영된다. 폰트나 글자크기를 바꿨다면 자막 조각 폭이
//   달라지므로 make_captions.mjs를 다시 돌린 뒤 렌더한다.
// - Inspector의 "Can't save default props" 경고는 정상이며 "Resolve" 버튼은
//   절대 누르지 않는다 (소스 오염 — 20번 실사고).
import fs from "node:fs";
import path from "node:path";
import { buildInputProps, SUBTITLER } from "./props.mjs";

function arg(name, fallback = null) {
  const i = process.argv.indexOf(name);
  return i >= 0 && i + 1 < process.argv.length ? process.argv[i + 1] : fallback;
}

const runDir = arg("--run");
if (!runDir) {
  console.error("사용법: node prepare-studio.mjs --run output/<run> [--video final.mp4] [--preset vox-기본]");
  process.exit(1);
}
const src = path.resolve(runDir, arg("--video", "final.mp4"));
const captionsPath = path.resolve(runDir, arg("--captions", "captions.json"));
const presetName = arg("--preset", "vox-기본");

const { inputProps, video, captions } = buildInputProps({
  src, captionsPath, presetName, asset: "bg.mp4",
});
fs.copyFileSync(src, path.join(SUBTITLER, "public", "bg.mp4"));
fs.writeFileSync(
  path.join(SUBTITLER, "src", "active-input.json"),
  JSON.stringify(inputProps, null, 1),
);
console.log(JSON.stringify({
  video: `${video.width}x${video.height} ${video.fps}fps ${(video.durationMs / 1000).toFixed(1)}s`,
  captions: captions.length,
  preset: presetName,
}, null, 1));
console.log("\n준비 완료. 실행: cd subtitler && npm run studio  (http://localhost:4330)");
console.log("- 오른쪽 Props 패널에서 폰트(29종)·글자크기·색·자막높이 실시간 조정");
console.log('- "Can\'t save default props" 경고는 정상 — Resolve 버튼 금지');
console.log("- 확정한 값은 config/caption-preset.json에 반영 → make_captions 재실행 → 렌더");
