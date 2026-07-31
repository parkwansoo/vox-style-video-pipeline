# 파이프라인 적용 규칙 (프롬프트 시스템 보충)

`image-prompt-guidelines.md`와 `video-prompt-guidelines.md`(Paper Diorama
프롬프트 시스템)가 프롬프트 작성의 **정본**이다. 이 문서는 그 시스템을 이
파이프라인(스타일 시트 입력 → 이미지 → 영상 → 나레이션 합본)에 적용할 때의
보충 규칙만 담는다.

## 1. 이미지 프롬프트 (GPT Image 2, 스타일 시트가 입력 이미지)

클립 이미지는 SHOT의 **정지 상태**를 그린다. 구성:

```
Create ONE 16:9 scene frame, not a style board or reference sheet.
[STYLE BLOCK — video 가이드의 A/B 중 해당 클립에 쓸 블록 그대로]
STILL: [SHOT의 Background / MG / FG를 정지 화면으로 서술]
AVOID: [해당 스타일의 AVOID 블록 그대로]
```

- 맨 앞의 "ONE scene frame, not a style board" 문장은 필수 — 입력이 스타일
  시트라서 이 지시가 없으면 보드 형태로 나온다.
- **Omni용(참조 이미지)**: 장면의 완성 상태를 그려도 된다 (모델이 참조로만 사용).
- **Seedance용(첫 프레임)**: 영상의 **시작 시점** 상태로 그린다 — 배경과 MG는
  자리에 있고, 클립 중 등장·변화할 요소(카운터 수치, 화살표, 스탬프)는 초기
  상태로. 영상 프롬프트가 그 변화를 서술한다.

## 2. 나레이션 동기화 (최우선)

- SHOT은 해당 클립 구간의 나레이션이 말하는 내용을 시각화한다. 프롬프트를
  쓸 때 구간 텍스트를 앞에 두고, 나레이션의 핵심 명사/수치가 화면의 MG/FG로
  나타나는지 확인한다.
- 화면 속 텍스트·숫자(giant number, headline, label)는 나레이션의 수치·표현과
  일치해야 한다. 나레이션이 한국어여도 화면 텍스트는 **영어·숫자**로 쓴다
  (생성 오탈자 위험 최소화). 짧게: 숫자 또는 1~3단어.

## 3. 타임스탬프 큐 — "no timecodes" 규칙의 유일한 예외

프롬프트 시스템은 타임코드를 금지하지만, 이 파이프라인에서는 **꼭 필요할
때만** 한 클립에 최대 1개의 시각 큐를 허용한다:

- 사용 조건: 6초 클립처럼 길어서 화면 사건과 나레이션 단어가 어긋날 수 있고,
  그 사건이 결과물을 실제로 개선하는 주요 beat일 때만.
- 계산: 큐 시각 = (해당 단어의 words.json start − 클립 seg_start) + **0.25**
  (합본 때 클립 앞 0.25초가 잘리는 것 보정)
- 형식: SHOT의 연결 동작 자리에 자연스럽게: "At 3.4s the stamp slams down."
- 그 외에는 시스템 규칙대로 타임코드 없이 쓴다.

## 4. 공인(public figure) 규칙 — 필수

시스템의 halftone 흑백 컷아웃 인물 문법을 그대로 쓰되:

| 항목 | 규칙 |
|---|---|
| 이미지 | 컷아웃 인물의 눈 위에 **검은 검열 바**를 그려 넣는다: "a solid black censor bar covering the eyes". 인물은 **원거리·작게**(small in frame, seen from a distance), 클로즈업 금지, 얼굴 디테일 최소화 |
| 이미지 프롬프트의 이름 | 허용. 단 생성 거부 시 인상착의 묘사("a tall politician in a dark suit")로 교체 후 재시도 |
| 영상 모델 | 반드시 Seedance 2.0 Fast (`--model seedance`). 이미지는 첫 프레임 |
| 영상 프롬프트의 이름 | **실명·직함·별칭 절대 금지** — "the cutout figure in the dark suit"처럼 외형으로만 지칭 (실명이 들어가면 생성 거부됨) |
| 영상 프롬프트 필수 문구 | "the solid black censor bar stays fixed over the eyes throughout" + 카메라가 인물에게 접근 금지 (인물 쪽 push-in 불가, 배경·오브제로의 무브는 가능) |

## 5. 스타일 블록 선택

- 스타일 시트가 항상 입력으로 첨부되므로 **A(Flat Parallax) 또는 B(Deep
  Diorama)**를 쓴다. C(Locked Stage)는 시트 없이 돌릴 때만.
- 절제된 데이터 beat = A, 리빌·에스컬레이션 = B. ALERT WASH는 영상 전체에서
  1회만.
- 공인 클립은 A를 우선한다 (카메라가 배우처럼 움직이는 B는 인물 접근 금지
  규칙과 충돌하기 쉽다).
