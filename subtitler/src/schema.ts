import { z } from "zod";
import { zColor } from "@remotion/zod-types";
import { FONT_KEYS } from "./fonts";

// 20번(숏츠 자동화) remotion/schema.ts와 같은 캡션 스키마·같은 한글 키를 쓴다.
// 데이터 계약을 동일하게 유지해야 언제든 20번 렌더러로 갈아탈 수 있다
// (2026-08-04 테스트로 상호 호환 실증). 가로/세로/fps만 우리 확장이다 —
// 20번은 비율표(1080x1920 고정)를 쓰지만 우리는 입력 영상 규격을 그대로 따른다.
export const captionSchema = z.object({
  text: z.string(),
  startMs: z.number(),
  endMs: z.number(),
});

export const sceneSchema = z.object({
  startMs: z.number(),
  endMs: z.number(),
  type: z.literal("video"),
  asset: z.string(),
  volume: z.number().min(0).max(1),
});

// zod는 스키마에 없는 키를 조용히 제거한다(실증된 함정) — 새 prop은 반드시 여기에도 선언.
export const subtitledVideoSchema = z.object({
  가로: z.number().int().positive(),
  세로: z.number().int().positive(),
  fps: z.number().positive(),
  영상길이ms: z.number().positive(),
  폰트: z.enum(FONT_KEYS as [string, ...string[]]),
  글자굵기: z.number(),
  글자크기: z.number(),
  글자색: zColor(),
  외곽선색: zColor(),
  외곽선두께: z.number(),
  강조색1: zColor(),
  강조색2: zColor(),
  강조단어: z.array(z.string()),
  강조단어2: z.array(z.string()),
  등장효과: z.string(),
  효과세기: z.number(),
  자막높이: z.number(),
  안전여백: z.number(),
  자막최대너비: z.number().min(1).max(100),
  자막목록: z.array(captionSchema),
  장면목록: z.array(sceneSchema),
});

export type SubtitledVideoProps = z.infer<typeof subtitledVideoSchema>;
