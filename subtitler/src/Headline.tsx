import React, { useEffect, useRef, useState } from 'react';
import {
  useCurrentFrame, useVideoConfig, AbsoluteFill,
  delayRender, continueRender, cancelRender, interpolate,
} from 'remotion';
import { loadFontByKey } from './fonts';

// 화면 상단의 헤드 카피. 자막(Captions)과 완전히 독립한 레이어다 —
// 자막 렌더 경로를 건드리지 않으려고 별도 컴포넌트로 뒀다.
//
// 2단 구성이다:
//   ① 훅 (0~3초)   큰 2줄 + 그라데이션 스크림. 스크롤을 세우는 역할
//   ② 라벨 (3초~끝) 작은 1줄 + 반투명 박스. 중간 유입자에게 맥락을 주는 역할
// 둘은 짧게 교차 페이드하고 y도 다르므로(18% → 13%) "축소되며 위로 자리잡는"
// 인상이 난다. 라벨은 종료 시각이 0이면 영상 끝까지 남는다.
//
// 배경 처리가 두 단계에서 다른 이유:
// - 훅은 3초뿐이라 스크림(상단 30%, 검정 45%→0%)이 싸다. 9:16 풀블리드에서
//   불투명 띠는 영상을 축소·절단해야 하지만 스크림은 화면을 잃지 않는다
// - 라벨은 41초 내내 떠 있어 스크림을 깔면 상단이 계속 어둡다. 대신 글자 뒤에만
//   반투명 박스를 둔다. 실측(기미 오일 편 세 배경): 검정 60% 박스에서 대비
//   4.95~8.55:1로 배경이 바뀌어도 무너지지 않고, 영상은 40% 비친다.
//   블러 박스도 만들어 비교했지만 배경 질감이 뭉개져 오히려 영상 정보가 죽었다

const HOOK_FADE_IN_SEC = 0.25;
const HOOK_FADE_OUT_SEC = 0.30;
const HOOK_SLIDE_PX = 18;
const LABEL_FADE_IN_SEC = 0.30;
const LABEL_LEAD_SEC = 0.15;  // 훅이 사라지기 전에 먼저 뜨기 시작하는 시간
const LABEL_RISE_PX = 8;

type Props = {
  // 훅
  hookLines: string[];
  hookStartMs: number;
  hookEndMs: number;
  hookFontSizePct: number;
  hookYPct: number;
  scrimPct: number;
  scrimOpacity: number;
  // 라벨
  labelText: string;
  labelStartMs: number;
  labelEndMs: number;   // 0이면 영상 끝까지
  labelFontSizePct: number;
  labelYPct: number;
  boxOpacity: number;
  boxRadiusPx: number;
  padXPx: number;
  padYPx: number;
  labelStrokeWidthPx: number;
  // 공통
  fontKey: string;
  fontWeight: number;
  color: string;
  highlightColor: string;
  highlightWords: string[];
  strokeColor: string;
  strokeWidthPx: number;
  safeMarginPct: number;
};

export const Headline: React.FC<Props> = ({
  hookLines, hookStartMs, hookEndMs, hookFontSizePct, hookYPct, scrimPct, scrimOpacity,
  labelText, labelStartMs, labelEndMs, labelFontSizePct, labelYPct,
  boxOpacity, boxRadiusPx, padXPx, padYPx, labelStrokeWidthPx,
  fontKey, fontWeight, color, highlightColor, highlightWords,
  strokeColor, strokeWidthPx, safeMarginPct,
}) => {
  const frame = useCurrentFrame();
  const { fps, height, width, durationInFrames } = useVideoConfig();
  // 자막과 같은 폰트를 쓰면 loadFontByKey 캐시를 공유한다(중복 로드 없음).
  const [family, setFamily] = useState<string>('sans-serif');
  const [handle] = useState(() => delayRender(`headline-font:${fontKey}`));
  const unblocked = useRef(false);
  useEffect(() => {
    let live = true;
    loadFontByKey(fontKey)
      .then((fam) => {
        if (!live) return;
        setFamily(fam);
        if (!unblocked.current) { continueRender(handle); unblocked.current = true; }
      })
      .catch((e) => cancelRender(e));
    return () => { live = false; };
  }, [fontKey, handle]);

  const clamp = { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' } as const;
  const nowMs = (frame / fps) * 1000;
  const marginX = (safeMarginPct / 100) * width;

  // 단어 단위 색칠 — 라벨 문구는 우리가 직접 쓰므로 구두점 제거 없이 단순 비교한다.
  const paint = (line: string) => line.split(' ').map((word, i, arr) => (
    <React.Fragment key={i}>
      <span style={{ color: highlightWords.some((w) => w && word.includes(w)) ? highlightColor : color }}>
        {word}
      </span>
      {i < arr.length - 1 ? ' ' : ''}
    </React.Fragment>
  ));

  const textBase: React.CSSProperties = {
    fontFamily: family,
    fontWeight: fontWeight ?? 800,
    lineHeight: 1.2,
    WebkitTextStroke: `${strokeWidthPx}px ${strokeColor}`,
    paintOrder: 'stroke fill',
    wordBreak: 'keep-all',
  };

  // ── ① 훅 ──
  const hookVisible = hookLines.length > 0 && nowMs >= hookStartMs && nowMs < hookEndMs;
  let hookNode: React.ReactNode = null;
  if (hookVisible) {
    const startFrame = (hookStartMs / 1000) * fps;
    const endFrame = (hookEndMs / 1000) * fps;
    const fadeIn = Math.max(1, Math.round(HOOK_FADE_IN_SEC * fps));
    const fadeOut = Math.max(1, Math.round(HOOK_FADE_OUT_SEC * fps));
    const opacity = Math.min(
      interpolate(frame, [startFrame, startFrame + fadeIn], [0, 1], clamp),
      interpolate(frame, [endFrame - fadeOut, endFrame], [1, 0], clamp),
    );
    const yShift = interpolate(frame, [startFrame, startFrame + fadeIn], [-HOOK_SLIDE_PX, 0], clamp);
    const fontSize = (hookFontSizePct / 100) * height;
    hookNode = (
      <AbsoluteFill style={{ opacity }}>
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: `${scrimPct}%`,
            background: `linear-gradient(180deg, rgba(0,0,0,${scrimOpacity}) 0%, rgba(0,0,0,0) 100%)`,
          }}
        />
        <div
          style={{
            ...textBase,
            position: 'absolute',
            top: `${hookYPct}%`,
            left: marginX,
            right: marginX,
            transform: `translateY(calc(-50% + ${yShift}px))`,
            textAlign: 'center',
            fontSize,
            textShadow: `0 ${Math.round(strokeWidthPx / 2)}px ${strokeWidthPx}px rgba(0,0,0,0.5)`,
          }}
        >
          {hookLines.map((line, i) => <div key={i}>{paint(line)}</div>)}
        </div>
      </AbsoluteFill>
    );
  }

  // ── ② 라벨 ──
  const labelEndFrame = labelEndMs > 0 ? (labelEndMs / 1000) * fps : durationInFrames;
  const labelStartFrame = (labelStartMs / 1000) * fps - LABEL_LEAD_SEC * fps;
  const labelVisible = labelText.length > 0 && frame >= labelStartFrame && frame < labelEndFrame;
  let labelNode: React.ReactNode = null;
  if (labelVisible) {
    const fadeIn = Math.max(1, Math.round(LABEL_FADE_IN_SEC * fps));
    // 끝까지 남는 라벨(종료 0)은 퇴장 페이드가 없다.
    const opacity = labelEndMs > 0
      ? Math.min(
          interpolate(frame, [labelStartFrame, labelStartFrame + fadeIn], [0, 1], clamp),
          interpolate(frame, [labelEndFrame - fadeIn, labelEndFrame], [1, 0], clamp),
        )
      : interpolate(frame, [labelStartFrame, labelStartFrame + fadeIn], [0, 1], clamp);
    const yShift = interpolate(frame, [labelStartFrame, labelStartFrame + fadeIn], [LABEL_RISE_PX, 0], clamp);
    const fontSize = (labelFontSizePct / 100) * height;
    labelNode = (
      <AbsoluteFill style={{ opacity }}>
        <div
          style={{
            position: 'absolute',
            top: `${labelYPct}%`,
            left: marginX,
            right: marginX,
            transform: `translateY(calc(-50% + ${yShift}px))`,
            textAlign: 'center',
          }}
        >
          {/* inline-block이라 박스 폭이 글자 폭을 그대로 따라간다 — 폭 계산이 필요 없다. */}
          <span
            style={{
              ...textBase,
              display: 'inline-block',
              fontSize,
              padding: `${padYPx}px ${padXPx}px`,
              borderRadius: boxRadiusPx,
              backgroundColor: `rgba(0,0,0,${boxOpacity})`,
              WebkitTextStroke: `${labelStrokeWidthPx}px ${strokeColor}`,
            }}
          >
            {paint(labelText)}
          </span>
        </div>
      </AbsoluteFill>
    );
  }

  if (!hookNode && !labelNode) return null;
  return <AbsoluteFill>{hookNode}{labelNode}</AbsoluteFill>;
};
