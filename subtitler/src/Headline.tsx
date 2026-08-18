import React, { useEffect, useRef, useState } from 'react';
import {
  useCurrentFrame, useVideoConfig, AbsoluteFill,
  delayRender, continueRender, cancelRender, interpolate,
} from 'remotion';
import { loadFontByKey } from './fonts';

// 화면 상단의 헤드 카피(훅) + 스크림. 자막(Captions)과 완전히 독립한 레이어다 —
// 자막 렌더 경로를 건드리지 않으려고 별도 컴포넌트로 뒀다.
//
// 스크림은 불투명 띠가 아니라 위→아래로 사라지는 그라데이션이다. 9:16 풀블리드에서
// 띠를 넣으려면 영상을 축소하거나 잘라야 하는데, 그라데이션은 화면을 잃지 않으면서
// 밝고 복잡한 배경 위의 글자 대비를 확보한다. 실측(기미 오일 편 0~3.2초, 16프레임
// 평균 배경 RGB 160,150,147): 노랑 #fdfb25 대비 2.62:1 → 스크림 45%에서 6.90:1.
// 같은 배경에서 빨강 #fa0011은 스크림 75%에서도 3.66:1에 그쳐 채택하지 않았다.

const FADE_IN_SEC = 0.25;
const FADE_OUT_SEC = 0.30;
const SLIDE_PX = 18;

export const Headline: React.FC<{
  lines: string[];
  startMs: number;
  endMs: number;
  fontKey: string;
  fontSizePct: number;
  fontWeight: number;
  color: string;
  strokeColor: string;
  strokeWidthPx: number;
  yPct: number;
  safeMarginPct: number;
  scrimPct: number;
  scrimOpacity: number;
}> = ({
  lines, startMs, endMs, fontKey, fontSizePct, fontWeight, color,
  strokeColor, strokeWidthPx, yPct, safeMarginPct, scrimPct, scrimOpacity,
}) => {
  const frame = useCurrentFrame();
  const { fps, height, width } = useVideoConfig();
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

  const nowMs = (frame / fps) * 1000;
  if (!lines.length || nowMs < startMs || nowMs >= endMs) return null;

  // 진입 페이드+슬라이드다운, 퇴장 페이드. 스크림도 카피와 같이 나타나고 사라진다.
  const startFrame = (startMs / 1000) * fps;
  const endFrame = (endMs / 1000) * fps;
  const fadeIn = Math.max(1, Math.round(FADE_IN_SEC * fps));
  const fadeOut = Math.max(1, Math.round(FADE_OUT_SEC * fps));
  const clamp = { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' } as const;
  const opacity = Math.min(
    interpolate(frame, [startFrame, startFrame + fadeIn], [0, 1], clamp),
    interpolate(frame, [endFrame - fadeOut, endFrame], [1, 0], clamp),
  );
  const yShift = interpolate(frame, [startFrame, startFrame + fadeIn], [-SLIDE_PX, 0], clamp);

  const fontSize = (fontSizePct / 100) * height;
  const marginX = (safeMarginPct / 100) * width;

  return (
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
          position: 'absolute',
          top: `${yPct}%`,
          left: marginX,
          right: marginX,
          transform: `translateY(calc(-50% + ${yShift}px))`,
          textAlign: 'center',
          fontFamily: family,
          fontWeight: fontWeight ?? 800,
          fontSize,
          lineHeight: 1.2,
          color,
          WebkitTextStroke: `${strokeWidthPx}px ${strokeColor}`,
          paintOrder: 'stroke fill',
          textShadow: `0 ${Math.round(strokeWidthPx / 2)}px ${strokeWidthPx}px rgba(0,0,0,0.5)`,
          wordBreak: 'keep-all',
        }}
      >
        {lines.map((line, i) => (
          <div key={i}>{line}</div>
        ))}
      </div>
    </AbsoluteFill>
  );
};
