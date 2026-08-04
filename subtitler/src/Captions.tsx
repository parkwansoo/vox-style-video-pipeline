import React, { useEffect, useRef, useState } from 'react';
import {
  useCurrentFrame, useVideoConfig, AbsoluteFill,
  delayRender, continueRender, cancelRender, spring, interpolate,
} from 'remotion';
import { loadFontByKey } from './fonts';
import {captionHighlightBoxStyle, captionHighlightColorAt, constrainedCaptionWidthPct} from './caption-layout.mjs';

type Caption = { text: string; startMs: number; endMs: number };
type CaptionScene = { startMs: number; endMs: number; captionEffect?: string };

export const Captions: React.FC<{
  captions: Caption[];
  fontKey: string;
  fontSizePct: number;
  fontWeight: number;
  textColor: string;
  strokeColor: string;
  strokeWidthPx: number;
  hlColor1: string;
  hlColor2: string;
  hlWords1: string[];
  hlWords2: string[];
  entrance: string;
  effectStrength: number;
  captionYPct: number;
  safeMarginPct: number;
  captionMaxWidthPct?: number;
  scenes?: CaptionScene[];
  highlightBox?: boolean;
}> = ({ captions, fontKey, fontSizePct, fontWeight, textColor, strokeColor, strokeWidthPx, hlColor1, hlColor2, hlWords1, hlWords2, entrance, effectStrength, captionYPct, safeMarginPct, captionMaxWidthPct, scenes = [], highlightBox = false }) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
  // 선택된 폰트 1개만 lazy 로드. 첫 렌더는 로드 완료까지 대기(delayRender)해 폰트 확실 적용.
  const [family, setFamily] = useState<string>('sans-serif');
  const [handle] = useState(() => delayRender(`font:${fontKey}`));
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

  const nowMs = (frame / fps) * 1000;
  const active = captions.find((c) => nowMs >= c.startMs && nowMs < c.endMs);
  if (!active) return null;
  const fontSize = (fontSizePct / 100) * height;
  const marginX = (safeMarginPct / 100) * width;
  const constrainedWidthPct = constrainedCaptionWidthPct(captionMaxWidthPct, safeMarginPct);

  // ── 등장 효과(조각 바뀔 때마다 재생) — scene.captionEffect가 있으면 해당 컷만 전역 효과를 덮어쓴다. ──
  const localFrame = frame - (active.startMs / 1000) * fps;
  const activeScene = scenes.find((s) => nowMs >= s.startMs && nowMs < s.endMs);
  const effectiveEntrance = activeScene?.captionEffect || entrance;
  const useFade = effectiveEntrance.includes('fade') || effectiveEntrance === 'slide-up' || effectiveEntrance === 'blur-in' || effectiveEntrance === 'scale-down';
  const usePop = effectiveEntrance.includes('pop');
  const strength = Number.isFinite(effectStrength) ? Math.max(0, effectStrength) : 1;
  const opacity = useFade && effectiveEntrance !== 'word-stagger'
    ? interpolate(localFrame, [0, 4], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })
    : 1;
  let scale = 1;
  if (usePop) {
    const pop = spring({ frame: localFrame, fps, config: { damping: 16, stiffness: 140, mass: 0.5 } });
    const depth = Math.min(0.6, 0.18 * strength); // 세기 1 → 0.82에서 시작, 클수록 더 크게 팝
    scale = interpolate(pop, [0, 1], [1 - depth, 1]);
  }
  if (effectiveEntrance === 'scale-down') {
    scale *= interpolate(localFrame, [0, 8], [1.12, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  }
  const yShiftPx = effectiveEntrance === 'slide-up'
    ? interpolate(localFrame, [0, 8], [18, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })
    : 0;
  const blurPx = effectiveEntrance === 'blur-in'
    ? interpolate(localFrame, [0, 8], [8, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })
    : 0;
  const wordStagger = effectiveEntrance === 'word-stagger';
  const wordStyle = (i: number): React.CSSProperties => {
    if (!wordStagger) return {};
    const delayedFrame = localFrame - i * 2;
    const wordOpacity = interpolate(delayedFrame, [0, 6], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
    const wordY = interpolate(delayedFrame, [0, 6], [10, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
    return {
      display: 'inline-block',
      opacity: wordOpacity,
      transform: `translateY(${wordY}px)`,
    };
  };

  // ── 핵심 단어 색 강조(색2=우선) — 단어에만, 나머지는 기본 글자색 ──
  const hlColorOf = (tokens: string[], index: number): string | null => {
    return captionHighlightColorAt(tokens, index, {
      highlightWords1: hlWords1,
      highlightWords2: hlWords2,
      highlightColor1: hlColor1,
      highlightColor2: hlColor2,
    });
  };
  const highlightStyle = (hl: string | null): React.CSSProperties => {
    if (!hl) return {};
    if (!highlightBox) return { color: hl };
    // 렌더와 안전 편집 미리보기에서 같은 형광펜 상자 규칙을 쓴다.
    return captionHighlightBoxStyle(hl);
  };
  const tokens = active.text.split(' ');

  return (
    <AbsoluteFill>
      <div
        style={{
          position: 'absolute',
          top: `${captionYPct}%`,
          ...(constrainedWidthPct === null
            ? {
                left: marginX,
                right: marginX,
                transform: `translateY(calc(-50% + ${yShiftPx}px)) scale(${scale})`,
              }
            : {
                left: '50%',
                width: `${constrainedWidthPct}%`,
                transform: `translate(-50%, calc(-50% + ${yShiftPx}px)) scale(${scale})`,
              }),
          opacity,
          filter: blurPx > 0 ? `blur(${blurPx}px)` : undefined,
          textAlign: 'center',
          fontFamily: family,
          fontWeight: fontWeight ?? 700,
          fontSize,
          lineHeight: 1.2,
          color: textColor,
          WebkitTextStroke: `${strokeWidthPx}px ${strokeColor}`,
          paintOrder: 'stroke fill',
          textShadow: `0 ${Math.round(strokeWidthPx / 2)}px ${strokeWidthPx}px rgba(0,0,0,0.5)`,
          wordBreak: 'keep-all',
        }}
      >
        {tokens.map((t, i) => (
          // 공백은 span 밖에 둔다 — inline-block(word-stagger) 내부의 후행 공백은 CSS가 접어서 단어가 붙어 보인다.
          <React.Fragment key={i}>
            <span style={{ color: textColor, ...highlightStyle(hlColorOf(tokens, i)), ...wordStyle(i) }}>{t}</span>
            {i < tokens.length - 1 ? ' ' : ''}
          </React.Fragment>
        ))}
      </div>
    </AbsoluteFill>
  );
};
