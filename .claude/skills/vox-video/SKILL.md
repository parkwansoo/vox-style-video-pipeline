---
name: vox-video
description: Vox 스타일 애니메이션 저널리즘 영상을 완전 자동으로 생성한다. 사용자가 "vox 영상", "vox 스타일 영상", "뉴스 애니메이션 영상", "시사 해설 영상"을 만들어 달라고 하면 사용. 선택적 가이던스 프롬프트로 스토리와 챕터 수(기본 1, 최대 4)를 지정할 수 있다. 예— "미국 경제 현황에 대한 vox 스타일 영상, 3챕터로"
---

# Vox 스타일 자동 영상 생성

시사·정치 저널리즘용 Vox 스타일 애니메이션 영상을 리서치 → 대본 → 음성 →
클립 → 합본까지 완전 자동으로 만든다. 챕터당 약 30초, 클립은 각 4s/6s이며
개수는 대본 분량이 정한다(1.0배속 4~8개, 1.3배속이면 그보다 늘어난다).

## 절대 원칙

1. **음성-화면 동기화가 항상 최우선이다.** 모든 결정(클립 분할, 프롬프트,
   합본)은 나레이션의 해당 구간과 화면 내용이 일치하도록 내린다.
2. 스토리는 **항상 리서치를 거친다.** 사용자가 소재를 줘도 웹 검색으로 최신
   사실관계를 확인하고, 소재가 없으면 현재 시사 이슈 중 가장 흥미로운 것을
   직접 고른다.
3. 공인(정치인 등 실존 유명 인물)이 나오는 클립은 별도 규칙(아래)을 따른다.
4. 실행 산출물은 전부 `output/<YYYYMMDD-주제슬러그>/`에 남긴다 (재실행 시 재사용).
   실행을 시작할 때 그 폴더에 `style.txt`를 만들어 사용한 스타일 이름을 적는다
   (`cat assets/ACTIVE_STYLE > output/<run>/style.txt`) — 나중에 이 영상이 어떤
   스타일이었는지 추적할 수 있어야 한다.
5. **검토 정지점 2곳에서 반드시 멈춘다** (아래 "검토 정지점" 참조).

## 검토 정지점 (2026-08-02 도입, 한시적)

대본과 이미지 품질이 아직 안정되지 않아, 다음 **두 지점에서 멈추고 사용자
검토를 받는다.** 멈춘다는 것은 결과를 보여주고 **응답을 기다린다**는 뜻이다 —
확인 없이 다음 단계로 넘어가지 않는다.

| 정지점 | 시점 | 보여줄 것 |
|---|---|---|
| ① 대본 | 2단계 대본 작성 직후, **TTS 실행 전** | 대본 전문, 예상 길이, 클립 수 전망 |
| ② 이미지 | 5단계 이미지 **전체** 생성 직후, 영상 생성 전 | 클립별 이미지 + 인덱스 시트, 나레이션 구간과의 대응표 |

**예외 — 사용자가 끝까지 진행을 명시하면 멈추지 않는다.** "끝까지 진행해",
"영상까지 다 만들어줘", "자동으로 완성해줘" 같은 요청이면 정지점을 건너뛰고
합본까지 한 번에 간다. 애매하면 멈추는 쪽을 택한다.

정지점 ②는 **전체 이미지가 다 나온 뒤** 한 번만이다. 클립마다 멈추지 않는다.
다만 첫 배치(2장)를 받은 시점에 스타일이 명백히 어긋났다면 남은 생성을
낭비하지 않도록 그때 알린다.

> 이 절은 품질이 안정되면 제거하고 완전 자동으로 되돌린다 (TODO.md 참조).

## 0. 사전 점검 (실패 시 즉시 사용자에게 안내하고 중단)

- `.env`의 `GEMINI_API_KEY`(영상 Omni Flash용)가 채워져 있는가.
  `KIE_API_KEY`는 **공인 클립(Seedance)이 있을 때만** 필요
- 나레이션 TTS는 외장 SSD(Samsung_T5)의 clone-voice 백엔드를 자동 기동한다 —
  SSD 미연결이면 tts.py가 안내 메시지와 함께 실패하니 연결을 요청한다
- `codex login status`가 ChatGPT 로그인 상태인가 (이미지 생성은 구독 OAuth 사용)
- `.venv`가 존재하는가 — 없으면 `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`
- `assets/style_reference.png`가 존재하는가 (모든 이미지 생성의 스타일 기준).
  이 파일은 **현재 활성 스타일**의 복사본이며, 어떤 스타일인지는
  `assets/ACTIVE_STYLE`에 적혀 있다. 스타일 원본과 주의사항은
  `styles/<그 이름>/NOTES.md`에 있으니 **작업 전에 읽는다** — 특히 그 스타일이
  세로 9:16용이면 클립 생성 비율을 바꿔야 한다 (`--aspect 9:16`)
- 다른 스타일로 만들고 싶다는 요청이 있으면 `styles/`의 목록을 보여주고
  전환 여부를 확인한다. 새 스타일을 만들어야 하면 `/style-sheet` 스킬을 쓴다
- `music/`에 음원이 있는가 — 없으면 "음악 없이 진행"을 알리고 계속한다
- 스크립트 실행은 항상 프로젝트 루트에서: `.venv/bin/python3 .claude/skills/vox-video/scripts/<이름>.py`

## 1. 제작 사양 확정 & 리서치

**대본을 쓰기 전에 세 가지를 확정한다. 가이던스에서 추론해 단정하지 말고,
AskUserQuestion 한 번으로 묶어 사용자에게 확인받는다** (2026-08-03 도입 —
제품·스타일이 여럿이 되면서 암묵 추론이 사고 지점이 됐다):

1. **주제·챕터 수** — 가이던스에서 읽은 해석을 요약해 보여주고 확인받는다.
   챕터 수 기본 1, 최대 4. 언어 기본 한국어.
2. **스타일** — `styles/`의 폴더들을 선택지로 나열한다. 현재
   `assets/ACTIVE_STYLE`을 첫 번째(추천)로 표시한다. 다른 스타일이 선택되면
   그 시트를 `assets/style_reference.png`로 복사하고 ACTIVE_STYLE을 갱신한다.
3. **제품 (광고 편만)** — `assets/products/`의 제품들을 선택지로 나열한다.
   가이던스에 제품명이 있으면 그 제품을 첫 번째(추천)로 표시하되, 묻지 않고
   진행하지 않는다. 교양 편이면 "제품 없음"으로 확정한다. 확정된 제품의
   `SPEC.md`가 5단계 제품 컷의 PRODUCT 블록·AVOID 출처이고, `SOURCE.md`가
   가리키는 제품 프로필 문서(소구 포인트·필수 키워드·금지 표현)가 2단계
   대본의 근거다.

이후 리서치와 스토리 설계:

- 웹 검색으로 리서치한다: 최신 전개, 핵심 수치, 대립 구도, 왜 지금 중요한가.
  광고 편이면 제품 프로필 문서가 리서치의 출발점이다.
- 스토리 각을 잡는다: Vox식 "흥미로운 질문 → 맥락 → 분석 → 시사점" 구조.
  멀티 챕터면 챕터들이 하나의 이해 가능한 이야기가 되도록 arc를 설계한다
  (예: 1장 현상 훅 / 2장 원인 / 3장 전망).

## 2. 챕터별 대본 작성

- 챕터당 **완성 영상 기준 약 30초**가 되도록 쓴다. 아래는 3단계에서 자동
  적용되는 무음 압축을 반영한 실측 기준이다:

  | 배속 | 대본 분량 (한국어 음절) | 문장 수 | 압축 후 나레이션 |
  |---|---|---|---|
  | 1.0 (다큐) | 125~140음절 | 5~7문장 | 약 25초 |
  | 1.3 (숏폼) | 145~165음절 | 7~9문장 | 약 25초 |

  **완성 길이 = 나레이션 + 클립 여백(보통 12~17%)**이라 30초를 노리면
  나레이션을 25초 안팎으로 잡는다. 실측 환산율은 압축 후 1.0배속
  **0.194초/음절**, 1.3배속 **0.167초/음절** (2026-08-03, 4챕터 443+134음절).
  1.0배속은 표본이 1챕터뿐이라 참고치다.

  배속은 스타일에 맞춘다 — 차분한 다큐는 1.0, 빠른 숏폼은 1.3.
  활성 스타일의 `styles/<이름>/NOTES.md`에 권장 배속이 있으면 그것을 따른다.
- Vox 톤: 첫 문장은 훅(의외의 사실·질문), 구체적 수치 1~2개, 짧고 명확한
  문장, 마지막 문장은 다음 챕터로 연결(또는 마지막 챕터면 시사점).
- **시각화를 염두에 두고 쓴다**: 각 문장이 그림으로 그려질 수 있어야 한다.

- **광고 편이면 숏츠 자동화의 완성 대본을 표현·후킹 레퍼런스로 참고해
  작성한다** (브이지샷·페이스오일 공통, 2026-08-03 결정). 경로:
  `20_숏츠 자동화/outputs/YYYY-MM-DD-<제품>.md` — 검증된 레퍼런스 광고에서
  만들어진 재료라 품질이 높고, 제품 팩트·금지표현 검사를 이미 통과한
  대본들이다.
- 저장: `output/<run>/ch<N>/script.txt`

⏸ **정지점 ①** — 여기서 멈추고 대본을 보여준다. TTS는 과금되므로 대본 확정
전에 돌리지 않는다. 사용자가 끝까지 진행을 명시한 경우만 그대로 계속한다.

## 3. 음성 생성 + 타임스탬프

```bash
# 기본 (1.0배속)
.venv/bin/python3 .claude/skills/vox-video/scripts/tts.py --text-file output/<run>/ch1/script.txt --out-dir output/<run>/ch1
# 숏폼 스타일이면 배속 지정
.venv/bin/python3 .claude/skills/vox-video/scripts/tts.py --text-file output/<run>/ch1/script.txt --out-dir output/<run>/ch1 --speed 1.3
# 사용자가 "타이트하게/더 빠르게"를 요청했을 때만 (임의 판단 금지)
.venv/bin/python3 .claude/skills/vox-video/scripts/tts.py --text-file output/<run>/ch1/script.txt --out-dir output/<run>/ch1 --speed 1.3 --silence-preset tight
```

**배속은 이 단계에서만 지정하면 되고 뒤 단계는 손대지 않는다.** 배속이 Whisper
분석 **전에** 적용되므로 `words.json`이 처음부터 배속된 시간축으로 나오고,
클립 분할·합본은 그 값을 그대로 쓴다. (실측: 1.0배속과 1.3배속의 정렬률이
0.933으로 동일 — 배속이 인식 정확도를 떨어뜨리지 않는다)

**무음은 자동으로 압축된다.** Gemini TTS는 나레이션의 27~32%를 침묵으로
만드는데(3개 영상 공통, 실발화는 55~57%뿐), 이대로 두면 클립 길이가 말이 아니라
침묵에 맞춰 잡힌다.

| 프리셋 | 문장 경계 | 문장 내부 | 무보정 기준 | 쓰는 곳 |
|---|---|---|---|---|
| `sentence` (기본) | 0.45s | 0.25s | 0.20s | 일반 다큐·해설 |
| `tight` | 0.35s | 0.20s | 0.15s | 훅이 중요한 빠른 전개 |

**항상 `sentence`로 실행한다.** `tight`은 **사용자가 명시적으로 요청할 때만**
쓴다("타이트하게", "더 빠르게", "훅 강하게", "tight으로" 등). 대본이 짧다거나
광고편이라는 이유로 임의 판단하지 않는다 — 스타일 NOTES.md에 권장 배속이 있는
것과 달리, 압축 강도는 사용자 결정 사항이다 (2026-08-03 사용자 지시).

개별 값은 `--silence-sentence`/`--silence-inner`/`--silence-mincut`으로
덮어쓴다. 아예 끄려면 `--no-compress-silence`.

**문장 경계와 내부를 구분하는 게 핵심이다.** 무음 길이만으로는 둘을 가를 수
없어서(실측에서 문장 경계와 내부 호흡이 똑같이 0.59초였다) **대본으로
판정**하며, 그래서 정렬을 두 번 돈다 — 1차로 문장 위치를 잡고, 압축하고,
압축본으로 다시 정렬한다. 정렬률은 압축 전후가 동일하다(실측 1.0000 / 0.9044,
프리셋·임계값 조합 8종 전부 유지).

⚠ **표현태그(`--tagged-file`)를 쓸 때는 주의한다.** 태그로 만든 한숨·추임새는
대본에 없는 소리라 정렬로 위치를 알 수 없고, 소리가 작으면 무음으로 잡혀
잘려나간다. 태그본을 넘기면 무음 임계값이 자동으로 `-45dB`로 내려가 약한 발성이
소리 쪽에 남지만(실측 제거량 4.63s→3.35s), **완전한 보장은 아니다.** 추임새가
연출의 핵심이면 `--no-compress-silence`로 끄는 편이 안전하다.

- 내부 동작: 로컬 clone-voice 백엔드(Gemini 음색, SSD 자동 기동)로 음성 생성
  → **무음 압축** → 로컬 MLX Whisper(large-v3-turbo)로 단어 타이밍 추출 →
  대본(정본)에 정렬. `narration.mp3`(압축본), `narration_raw.mp3`(압축 전,
  진단용), `words.json`(단어별 start/end 초), `asr.json`(진단용), 요약(총 길이·
  `alignment_ratio`·`silence_compression`)이 나온다.
**음색은 `Charon` 고정이 기본이다** (남성 다큐 톤, 랜덤 선택 아님). 사용자가
다른 목소리를 원하면 `--voice <이름>`으로 바꾼다. Gemini TTS가 지원하는 30종:

괄호는 성별 (남/여).

| 결 | 음색 |
|---|---|
| 정보 전달 | **Charon**(남·기본) · Rasalgethi(남) · Sadaltager(남) · Iapetus(남) · Erinome(여) |
| 단단함 | Alnilam(남) · Schedar(남) · Kore(여) · Orus(여) · Gacrux(여) |
| 밝음·경쾌 | Sadachbia(남) · Zephyr(여) · Autonoe(여) · Puck(여) · Laomedeia(여) · Fenrir(여) |
| 부드러움 | Algieba(남) · Achernar(여) · Vindemiatrix(여) · Despina(여) · Sulafat(여) |
| 편안함 | Umbriel(남) · Zubenelgenubi(남) · Callirrhoe(여) · Aoede(여) · Achird(여) |
| 개성 | Enceladus(남·숨결) · Algenib(남·거칢) · Leda(여·젊음) · Pulcherrima(여·직진) |

남성 12종 / 여성 18종. **2026-08-03 기준 30종 전부 clone-voice 백엔드에 프리셋이
등록되어 있어 바로 쓸 수 있다.** 다만 백엔드 상태는 바뀔 수 있으므로, 바꾸기 전에
`tts.py --list-voices`로 확인하는 편이 안전하다. 없는 이름을 지정하면 합성이
실패하며 에러 메시지가 사용 가능한 목록을 알려준다.

- 톤 프롬프트로 화자 성격을 따로 지정한다
  (.env `VOX_TTS_VOICE`/`VOX_TTS_TONE`으로 기본값 변경). 감정 비트가 필요한 대본이면
  표현태그 삽입본을 `--tagged-file`로 따로 넘길 수 있다 (정렬은 항상 원본
  기준. 지원 태그 16종: [laughs] [giggles] [sighs] [gasp] [whispers] [excited]
  [amazed] [curious] [sarcastic] [serious] [shouting] [tired] [crying]
  [trembling] [mischievously] [panicked] — 다큐 톤에는 보통 불필요).
- 압축 후 총 길이가 20초 미만/32초 초과면 대본을 조정해 재생성한다 (압축 전
  기준이던 24~38초를 실측 압축률 15.5%로 환산한 값).
- `alignment_ratio`가 0.8 미만이면 asr.json을 확인한다 — 발음이 뭉개진
  구간이 있으면 대본 표현을 바꿔 재생성한다 (숫자·고유명사가 흔한 원인).

## 4. 클립 분할 (타임스탬프 기반 — 이 스킬의 핵심)

`words.json`을 읽고 나레이션을 클립 구간으로 나눈다.

- 클립 실효 길이 = **생성 길이 − 0.25s** (합본 때 앞 0.25초가 잘린다).
  4초→3.75s, 5초→4.75s, 6초→5.75s, 7초→6.75s. 플랫폼이 지원하는 단위를 쓰면
  되고, 합본은 실제 길이를 재서 처리하므로 4/6초로 한정되지 않는다.
- 분할 규칙:
  - 경계는 반드시 문장/구절 경계에 둔다 (의미 단위가 클립 중간에 끊기지 않게).
  - 구간 길이보다 **크되 가장 가까운** 생성 단위를 고른다 (구간 3.2s → 4초 클립,
    4.9s → 5초 또는 6초). 구간이 가장 긴 단위를 넘으면 더 쪼갠다.
  - **구간보다 짧은 클립은 안 된다.** 합본은 클립을 빠르게만 만들 수 있고 느리게
    늘리지는 못한다.
  - 여백은 합본이 배속으로 흡수하므로 화면이 늘어지지 않는다. 다만 여백이 클수록
    배속이 세지니 **실효 길이의 20% 이내**로 두면 배율이 1.25x 안쪽에 머문다
    (실측: 여백 12%였던 편이 1.05~1.36x).
  - **클립 수는 대본이 결정한다.** 1.0배속이면 보통 4~8개지만, 배속을 쓰면
    같은 30초에 내용이 더 들어가므로 그만큼 늘어난다(1.3배속이면 10개 안팎도
    정상). 문장 경계를 깨면서까지 개수를 맞추지 않는다.
- 구간 경계값: `seg_start`/`seg_end`는 **앞 단어의 end와 뒤 단어의 start의
  중간값**으로 잡는다 (단어가 잘리지 않게). 첫 구간은 0.0에서, 마지막 구간은
  마지막 단어 end + 0.3에서 끝낸다.
- 각 클립에 대해 기록한다: 구간 텍스트, seg_start/seg_end, 클립 길이(4/6),
  공인 등장 여부. → `output/<run>/ch<N>/plan.md`에 표로 저장.

## 5. 클립 이미지 생성

`references/image-prompt-guidelines.md`(Paper Diorama 프롬프트 시스템)와
`references/pipeline-rules.md`(이미지 프롬프트 구성·공인 규칙)를 **반드시
읽고** 프롬프트를 작성한다.

이미지는 **Codex CLI의 내장 이미지 생성(ChatGPT 구독 OAuth, gpt-image-2)**으로
만든다. API 키·업로드 불필요 — 스타일 시트는 로컬 파일로 첨부된다.

```bash
# 클립마다 (프롬프트는 파일로 저장해두면 재현 가능)
.venv/bin/python3 .claude/skills/vox-video/scripts/gen_image.py --prompt-file output/<run>/ch1/clip1_img.txt --style-ref assets/style_reference.png --out output/<run>/ch1/clip1.png
```

**제품 컷이면** (1단계에서 확정한 제품이 화면에 나오는 클립) 제품 누끼를
`--ref`로 함께 첨부하고, 그 제품 `assets/products/<제품>/SPEC.md`의 PRODUCT
블록·AVOID 문구를 프롬프트에 넣는다. 스타일 시트가 항상 첫 번째 첨부다
(상세: pipeline-rules.md "실제 제품이 등장하는 이미지").

```bash
.venv/bin/python3 .claude/skills/vox-video/scripts/gen_image.py --prompt-file ... --style-ref assets/style_reference.png --ref assets/products/<제품>/reference.png --out ...
```

**세로(9:16) 스타일이면** 세 스크립트 모두에 비율을 넘긴다. 기본값은 16:9라
가로 스타일에서는 아무것도 붙이지 않는다.

| 단계 | 세로일 때 추가 |
|---|---|
| 이미지 | `--aspect 9:16` |
| 영상 | `--aspect 9:16` |
| 합본 | `--size 720x1280` |

이미지 프롬프트의 첫 문장도 `Create ONE 9:16 scene frame...`으로 바꿔 쓴다
(pipeline-rules.md 템플릿의 16:9 부분).

- 이미지 프롬프트는 해당 클립의 나레이션 구간 텍스트를 근거로 작성하며,
  "Create ONE 16:9 scene frame, not a style board" 지시로 시작한다
  (pipeline-rules.md의 템플릿).
- **공인 클립**: 눈 검은 바 + 원거리 구도 필수 (pipeline-rules.md 참조).
- 병렬 실행은 **동시 2개까지만** (이미지 생성은 ChatGPT 구독 사용량을
  소모하므로 과도한 동시 실행을 피한다). 사용량 한도 초과로 실패하면
  사용자에게 알리고 대기 후 재개한다.
- 생성된 이미지를 Read로 열어 확인한다: 스타일 일치, 스타일 보드가 아닌 단일
  장면인지, 검은 바(공인), 텍스트 오염 여부. 문제 있으면 프롬프트 수정 후
  재생성 (클립당 최대 3회).
- 이미지·영상 생성은 **항상 백그라운드로 돌린다.** gen_image.py는 시도당 7분
  + 재시도라 최대 14분이고, foreground 타임아웃에 죽으면 그대로 날린다.
- 검토용 인덱스 시트를 만들어두면 사용자가 9장을 한 번에 본다 (PIL로 격자
  합성 → `output/<run>/ch<N>/_contact_sheet.png`).

⏸ **정지점 ②** — 전체 이미지가 나오면 여기서 멈추고 인덱스 시트와 클립별
나레이션 대응표를 보여준다. 영상 생성은 클립당 과금되므로 이미지 확정 전에
돌리지 않는다. 사용자가 끝까지 진행을 명시한 경우만 그대로 계속한다.

## 6. 클립 영상 생성

`references/video-prompt-guidelines.md`(STYLE BLOCK → SHOT → AUDIO → AVOID
4블록 시스템)와 `references/pipeline-rules.md`를 **반드시 읽고** 프롬프트를
작성한다.

```bash
# 일반 클립 — Gemini API 직접 호출(gemini-omni-flash-preview), 이미지 = 참조
.venv/bin/python3 .claude/skills/vox-video/scripts/gen_video.py --model omni --prompt-file output/<run>/ch1/clip1_vid.txt --image output/<run>/ch1/clip1.png --duration 4 --out output/<run>/ch1/clip1.mp4
# 공인 클립 — Kie.ai Seedance 2.0 Fast, 이미지 = 첫 프레임, 프롬프트에 실명 절대 금지
.venv/bin/python3 .claude/skills/vox-video/scripts/gen_video.py --model seedance --prompt-file output/<run>/ch1/clip2_vid.txt --image output/<run>/ch1/clip2.png --duration 6 --out output/<run>/ch1/clip2.mp4
```

- SHOT은 그 구간 나레이션이 말하는 내용을 시각화하고, 꼭 필요할 때만
  타임스탬프 큐를 넣는다 (계산법: pipeline-rules.md의 `+0.25s` 보정 참조).
- 클립마다 배경과 카메라 무브를 바꾸고, ALERT WASH는 영상 전체 1회만
  (video-prompt-guidelines.md의 Sequencing 규칙).
- 영상 생성은 수 분 걸린다. 여러 클립을 병렬(백그라운드)로 돌리고 폴링한다.

### 생성 경로 선택 — API vs Flow 구독

| 경로 | 언제 | 비용 |
|---|---|---|
| **Gemini API** (기본) | 30~40초 영상, 안정성 우선 | 초당 약 $0.10 (44초 ≈ $4.5) |
| **Google Flow 브라우저** | 80초 이상 등 API 비용이 부담될 때 | 구독 할당량 |

Flow 경로는 사용자가 **명시적으로 요청할 때만** 쓴다. 브라우저 자동화라
API보다 취약하고 사람 개입이 필요하다. 절차는
`references/flow-browser.md`를 **전부 읽고** 따른다 — Slate 편집기 입력,
설정 검증, 진행 상태 판독에 실측으로 확인된 함정이 많다.

```bash
.venv/bin/python3 .claude/skills/vox-video/scripts/prepare_flow_jobs.py \
  --run output/<run> --chapter 1 --clip 1:6 2:6 5:4 --run-name run-v01
.venv/bin/python3 .claude/skills/vox-video/scripts/flow_state.py init \
  --jobs output/<run>/flow-browser-runs/run-v01/jobs.json
```

어느 경로로 만들었든 산출물은 같은 `output/<run>/ch<N>/clipN.mp4`이므로
7단계 합본은 동일하다.

## 7. 합본

매니페스트를 작성하고 assemble.py를 실행한다.

```json
{
  "chapters": [
    {
      "narration": "output/<run>/ch1/narration.mp3",
      "clips": [
        {"file": "output/<run>/ch1/clip1.mp4", "seg_start": 0.0, "seg_end": 3.6},
        {"file": "output/<run>/ch1/clip2.mp4", "seg_start": 3.6, "seg_end": 9.2}
      ]
    }
  ]
}
```

```bash
.venv/bin/python3 .claude/skills/vox-video/scripts/assemble.py --manifest output/<run>/manifest.json --out output/<run>/final.mp4
```

- 자동 처리: 클립당 앞 0.25s 컷 → **클립을 나레이션 구간 길이에 맞춰 배속** →
  정규화·연결 → 나레이션 구간을 각 클립 시작점에 정확히 배치 → 클립 자체 오디오
  저볼륨(효과음 유지) → `music/` 랜덤 1곡 저볼륨 루프.
- 멀티 챕터면 chapters 배열에 순서대로 넣는다 (챕터 연결도 자동).

**클립 맞춤 배속(기본 켜짐).** 생성 클립은 정수 초(4·5·6·7s)로만 나오는데
나레이션 구간은 3.7s·5.7s처럼 임의 길이로 떨어진다. 이 어긋남은 구조적이라
아무리 잘 쪼개도 남고, 그대로 두면 컷 끝마다 말 없는 화면이 붙는다. 각 클립을
자기 구간 길이에 맞춰 빠르게 하면 그 시간이 사라지고, 이 정도 배율에서는
빨리감기가 아니라 생동감으로 읽힌다 (사용자 확인, 2026-08-03).

- 배율은 **컷마다 따로** 계산된다 — 그 컷이 담은 말에 맞추지 전체 평균에
  맞추지 않는다. 결과는 `clip_rates`로 출력된다
- 상한은 `--max-rate`(기본 2.0). 걸리면 경고와 함께 남는 여백을 알려준다
- 여백을 그대로 두려면 `--no-fit-clips`
- 클립이 구간보다 **짧으면** 손쓸 수 없다(느리게 만들지 않는다). 4단계에서
  구간보다 긴 클립을 고르는 이유다

## 8. 검증 & 전달

- 출력된 duration이 기대치(챕터 수 × 약 30s)와 맞는지 확인한다.
- 경고 로그("나레이션 구간이 클립 실효 길이보다 깁니다")가 있으면 해당 클립
  분할을 고쳐 재합본한다.
- 최종 영상을 SendUserFile로 사용자에게 전달하고, 스토리 요약·클립 구성
  (몇 초에 무엇이 나오는지)을 함께 보고한다.

## 공인(public figure) 규칙 요약

| 단계 | 규칙 |
|---|---|
| 이미지 | 눈에 검은 바(이미지에 그려 넣음), 인물은 원거리·작게, 클로즈업 금지 |
| 영상 모델 | 반드시 Seedance 2.0 Fast (`--model seedance`), 이미지는 첫 프레임 |
| 영상 프롬프트 | **실명·직함·별칭 절대 금지** — 외형으로만 지칭 |
| 카메라 | 인물에게 다가가지 않음, 검은 바 유지 명시 |

## 비용 주의

- 영상(일반): Gemini API 종량제 (Omni Flash). 오류/쿼터 초과 시 중단하고
  사용자에게 안내한다.
- 영상(공인): Kie.ai 크레딧 소모. 402(크레딧 부족) 발생 시 즉시 중단하고
  사용자에게 충전을 안내한다.
- 이미지: ChatGPT 구독 사용량(5시간 윈도우)을 소모 — 텍스트 대비 3~5배
  빠르게 차감되므로 불필요한 재생성을 피한다.
- 나레이션: clone-voice 경유 **Gemini TTS 클라우드** — 약 $0.03/분 과금
  (우리 .env에는 키 불필요, 비용은 clone-voice의 Google 계정에서 발생).
  Whisper 정렬은 로컬 무료. 대본 재생성도 과금되므로 분량을 미리 맞춘다.
- 3~4챕터 실행은 소모가 크므로, 멀티 챕터 요청이 아니면 기본 1챕터로
  진행한다.
