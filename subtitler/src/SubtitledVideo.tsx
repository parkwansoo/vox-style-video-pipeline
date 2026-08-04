import React from "react";
import { AbsoluteFill, OffthreadVideo, staticFile } from "remotion";
import { Captions } from "./Captions";
import type { SubtitledVideoProps } from "./schema";

// 완성 영상(bg)을 전체 화면으로 깔고 자막만 얹는다 — 20번 render-video.mjs의
// --bg-video 경로와 같은 구성. 영상의 원본 오디오를 그대로 쓴다(volume 1).
export const SubtitledVideo: React.FC<SubtitledVideoProps> = (props) => {
  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {props.장면목록.map((scene, i) => (
        <OffthreadVideo
          key={i}
          src={staticFile(scene.asset)}
          volume={scene.volume}
          style={{ width: "100%", height: "100%", objectFit: "cover" }}
        />
      ))}
      <Captions
        captions={props.자막목록}
        fontKey={props.폰트}
        fontSizePct={props.글자크기}
        fontWeight={props.글자굵기}
        textColor={props.글자색}
        strokeColor={props.외곽선색}
        strokeWidthPx={props.외곽선두께}
        hlColor1={props.강조색1}
        hlColor2={props.강조색2}
        hlWords1={props.강조단어}
        hlWords2={props.강조단어2}
        entrance={props.등장효과}
        effectStrength={props.효과세기}
        captionYPct={props.자막높이}
        safeMarginPct={props.안전여백}
        captionMaxWidthPct={props.자막최대너비}
      />
    </AbsoluteFill>
  );
};
