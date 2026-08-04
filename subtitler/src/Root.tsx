import "./index.css";
import React from "react";
import { Composition } from "remotion";
import { subtitledVideoSchema } from "./schema";
import { SubtitledVideo } from "./SubtitledVideo";
import activeInput from "./active-input.json";

// defaultProps는 JSON import 변수 참조로 둔다 — 리터럴로 바꾸면 Studio의 드래그
// 자동저장이 소스를 오염시킨다(20번 실사고). Studio의 "Can't save default props"
// 경고는 정상이며 "Resolve" 버튼은 절대 누르지 않는다. 렌더는 render.mjs가
// 모든 prop을 완전 명시로 전달하므로 이 값에 의존하지 않는다.
export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="CaptionVideo"
      component={SubtitledVideo}
      schema={subtitledVideoSchema}
      defaultProps={activeInput as never}
      durationInFrames={1}
      fps={30}
      width={1080}
      height={1920}
      calculateMetadata={async ({ props }) => ({
        width: props.가로,
        height: props.세로,
        fps: props.fps,
        durationInFrames: Math.max(
          1,
          Math.ceil((props.영상길이ms / 1000) * props.fps),
        ),
      })}
    />
  );
};
