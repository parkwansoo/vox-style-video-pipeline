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

### 실제 제품이 등장하는 이미지 (광고 편)

제품 컷은 스타일 시트에 더해 **제품 누끼 사진을 `--ref`로 함께 첨부**한다
(`gen_image.py --style-ref <시트> --ref <제품>`). 스타일 시트가 항상 첫 번째
첨부여야 프롬프트의 FIRST/REMAINING 구분이 맞는다.

**프롬프트에 치수를 숫자로 쓰지 않는다.** 대신 레퍼런스를 따르라고 한다.

> MATCH ITS SHAPE AND PROPORTIONS EXACTLY - compare your bottle against the
> reference and reproduce the same silhouette. If it does not look like the
> reference stood side by side, redraw it.

2026-08-02 실측으로 확인한 이유가 있다. 같은 프롬프트에 `유리병:펌프 1.7:1`을
넣었는데 한 컷은 1.57, 다른 컷은 1.41로 갈렸다. 숫자가 결과를 만들지 못했고
**레퍼런스 이미지가 만들었다.** 게다가 제품 스펙 문서의 수치(`1:2.85`)가 실제
레퍼런스 실측값(1.26)과 달라, 숫자를 주면 오히려 레퍼런스에서 멀어졌다.
숫자를 빼고 "레퍼런스와 같아 보이게"로 바꾸자 한 번에 맞았다.

**숫자는 검증용으로 쓴다.** 생성 후 레퍼런스와 실루엣 비율을 비교해 어긋나면
재생성한다. 프롬프트 입력이 아니라 사후 점검 기준이다.

숫자가 아닌 것은 프롬프트에 그대로 넣는다 — 재질(프로스트 유리·샴페인골드
펌프), 색, **라벨 문구 전부**(줄 순서와 상대 크기 포함), 그리고 AVOID
(투명 유리·원통형·스티커 라벨·은색 펌프 등).

**레퍼런스는 배경 없는 누끼를 쓴다.** 다른 스타일이 이미 입혀진 이미지
(예: 종이 질감 합성본)는 우리 스타일과 충돌한다.

**손이 나오면 한 손으로, 각도를 주어 넣는다.** 양손으로 받쳐 들면 좌우
대칭이 되어 인위적으로 보인다. 손은 제품의 **아랫부분만** 잡아 라벨과 몸체를
가리지 않게 한다 (실측: 양손 구도에서 하단 22%가 가려졌다).

### 프레이밍 선택 — 정면은 기본값이 아니라 선택이다

스타일 DNA에는 보통 "centred to camera" 같은 정면 서술이 박혀 있다(레퍼런스
원본이 그렇기 때문). 그래서 구도를 따로 정하지 않으면 **모든 클립이 자동으로
정면**이 된다. 클립마다 아래에서 하나를 골라 STILL에 명시한다.

| 프레이밍 | 프롬프트 문구 | 어울리는 장면 | 함께 넣을 AVOID |
|---|---|---|---|
| SPEC FRONT | centred to camera at eye level, symmetrical | 구조·층·비교를 정확히 읽혀야 할 때 | — |
| HERO LOW | wide-angle lens from below the eye line, camera close and tilted up, subject three-quarters to camera | 훅, 인물 등장, 감정 | fisheye or barrel distortion, stretched or bulging facial features, nostrils seen from underneath |
| WORM DEPTH | from far below looking steeply up, the subject towering out of frame | 깊이, 압도되는 규모 | HERO LOW와 동일 |
| OVERHEAD | looking straight down from directly above | 낙하·확산·퍼짐 | the subject flattening into a pattern, loss of depth cues |
| MACRO DRIFT | macro-close on the surface, shallow depth of field | 질감·세포 | — |
| TILTED | the frame rolled a few degrees off level | 이상 신호, 무너짐 | a strong dutch angle, a disorienting tilt |
| SCALE CONTRAST | a small subject near the lens against something far larger behind it | 크기 대비 | — |

**선택 규칙**

- **내용이 정한다.** 구조를 설명하는 컷은 SPEC FRONT가 옳다. 해부 단면을
  비틀면 뭘 보는지 안 읽혀 오히려 손해다.
- **같은 프레이밍을 3클립 연속 쓰지 않는다.**
- **첫 클립(훅)과 인물이 등장하는 클립은 SPEC FRONT를 기본값으로 쓰지
  않는다.** 쓰려면 이유가 있어야 한다.

마지막 클립에는 규칙을 두지 않는다 — 시리즈로 이어지는 영상이면 마지막 컷은
결말이 아니라 다음 편으로 넘기는 컷이라 정면이 오히려 맞을 수 있다.

프레이밍은 **강제가 아니라 메뉴**다. 이 파이프라인의 에너지는 앵글이 아니라
움직임과 내용에서 나오므로, 다이내믹한 구도는 인물·훅·전환에 집중시키고
설명 컷은 정면을 유지하되 영상 프롬프트에서 확실한 무브를 준다.

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
