---
name: vox-video
description: Vox 스타일 애니메이션 저널리즘 영상을 완전 자동으로 생성한다. 사용자가 "vox 영상", "vox 스타일 영상", "뉴스 애니메이션 영상", "시사 해설 영상"을 만들어 달라고 하면 사용. 선택적 가이던스 프롬프트로 스토리와 챕터 수(기본 1, 최대 4)를 지정할 수 있다. 예— "미국 경제 현황에 대한 vox 스타일 영상, 3챕터로"
---

# Vox 스타일 자동 영상 생성

시사·정치 저널리즘용 Vox 스타일 애니메이션 영상을 리서치 → 대본 → 음성 →
클립 → 합본까지 완전 자동으로 만든다. 챕터당 약 30초(클립 4~8개, 각 4s/6s).

## 절대 원칙

1. **음성-화면 동기화가 항상 최우선이다.** 모든 결정(클립 분할, 프롬프트,
   합본)은 나레이션의 해당 구간과 화면 내용이 일치하도록 내린다.
2. 스토리는 **항상 리서치를 거친다.** 사용자가 소재를 줘도 웹 검색으로 최신
   사실관계를 확인하고, 소재가 없으면 현재 시사 이슈 중 가장 흥미로운 것을
   직접 고른다.
3. 공인(정치인 등 실존 유명 인물)이 나오는 클립은 별도 규칙(아래)을 따른다.
4. 실행 산출물은 전부 `output/<YYYYMMDD-주제슬러그>/`에 남긴다 (재실행 시 재사용).

## 0. 사전 점검 (실패 시 즉시 사용자에게 안내하고 중단)

- `.env`의 `GEMINI_API_KEY`(영상 Omni Flash용)가 채워져 있는가.
  `KIE_API_KEY`는 **공인 클립(Seedance)이 있을 때만** 필요
- 나레이션 TTS는 외장 SSD(Samsung_T5)의 clone-voice 백엔드를 자동 기동한다 —
  SSD 미연결이면 tts.py가 안내 메시지와 함께 실패하니 연결을 요청한다
- `codex login status`가 ChatGPT 로그인 상태인가 (이미지 생성은 구독 OAuth 사용)
- `.venv`가 존재하는가 — 없으면 `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`
- `assets/style_reference.png`가 존재하는가 (모든 이미지 생성의 스타일 기준.
  기본으로 Vox 마스터 스타일 시트가 들어 있으며 사용자가 교체 가능)
- `music/`에 음원이 있는가 — 없으면 "음악 없이 진행"을 알리고 계속한다
- 스크립트 실행은 항상 프로젝트 루트에서: `.venv/bin/python3 .claude/skills/vox-video/scripts/<이름>.py`

## 1. 가이던스 해석 & 리서치

- 가이던스 프롬프트에서 스토리 주제와 챕터 수를 파악한다. 챕터 수 기본 1,
  최대 4. 언어 기본 한국어(가이던스에서 지정 시 변경).
- 웹 검색으로 리서치한다: 최신 전개, 핵심 수치, 대립 구도, 왜 지금 중요한가.
- 스토리 각을 잡는다: Vox식 "흥미로운 질문 → 맥락 → 분석 → 시사점" 구조.
  멀티 챕터면 챕터들이 하나의 이해 가능한 이야기가 되도록 arc를 설계한다
  (예: 1장 현상 훅 / 2장 원인 / 3장 전망).

## 2. 챕터별 대본 작성

- 챕터당 소리내어 읽어 약 28~32초: 한국어 기준 **140~170음절** (문장 5~7개).
- Vox 톤: 첫 문장은 훅(의외의 사실·질문), 구체적 수치 1~2개, 짧고 명확한
  문장, 마지막 문장은 다음 챕터로 연결(또는 마지막 챕터면 시사점).
- **시각화를 염두에 두고 쓴다**: 각 문장이 그림으로 그려질 수 있어야 한다.
- 저장: `output/<run>/ch<N>/script.txt`

## 3. 음성 생성 + 타임스탬프

```bash
.venv/bin/python3 .claude/skills/vox-video/scripts/tts.py --text-file output/<run>/ch1/script.txt --out-dir output/<run>/ch1
```

- 내부 동작: 로컬 clone-voice 백엔드(Gemini 음색, SSD 자동 기동)로 음성 생성
  → 로컬 MLX Whisper(large-v3-turbo)로 단어 타이밍 추출 → 대본(정본)에 정렬.
  `narration.mp3`, `words.json`(단어별 start/end 초), `asr.json`(진단용),
  요약(총 길이·`alignment_ratio`)이 나온다.
- 음색 기본값은 Charon(남성 다큐 톤), 톤 프롬프트로 화자 성격을 지정한다
  (.env `VOX_TTS_VOICE`/`VOX_TTS_TONE`으로 변경). 감정 비트가 필요한 대본이면
  표현태그 삽입본을 `--tagged-file`로 따로 넘길 수 있다 (정렬은 항상 원본
  기준. 지원 태그 16종: [laughs] [giggles] [sighs] [gasp] [whispers] [excited]
  [amazed] [curious] [sarcastic] [serious] [shouting] [tired] [crying]
  [trembling] [mischievously] [panicked] — 다큐 톤에는 보통 불필요).
- 총 길이가 24초 미만/38초 초과면 대본을 조정해 재생성한다.
- `alignment_ratio`가 0.8 미만이면 asr.json을 확인한다 — 발음이 뭉개진
  구간이 있으면 대본 표현을 바꿔 재생성한다 (숫자·고유명사가 흔한 원인).

## 4. 클립 분할 (타임스탬프 기반 — 이 스킬의 핵심)

`words.json`을 읽고 나레이션을 클립 구간으로 나눈다.

- 클립 실효 길이: **4초 클립 = 3.75s, 6초 클립 = 5.75s** (합본 때 앞 0.25초가
  잘리기 때문). 구간 배분은 이 실효 길이 기준으로 한다.
- 분할 규칙:
  - 경계는 반드시 문장/구절 경계에 둔다 (의미 단위가 클립 중간에 끊기지 않게).
  - 각 구간 길이 ≤ 3.75s → 4초 클립, ≤ 5.75s → 6초 클립. 5.75s를 넘는 구절
    묶음은 더 쪼갠다.
  - 구간을 실효 길이에 가깝게 채운다 (여백이 크면 화면만 남고 말이 없는
    구간이 생긴다. 0.3~0.8s 여백이 이상적 — 자연스러운 호흡이 된다).
  - 챕터당 4~8클립이 되는지 확인한다.
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

- 이미지 프롬프트는 해당 클립의 나레이션 구간 텍스트를 근거로 작성하며,
  "Create ONE 16:9 scene frame, not a style board" 지시로 시작한다
  (pipeline-rules.md의 템플릿).
- **공인 클립**: 눈 검은 바 + 원거리 구도 필수 (pipeline-rules.md 참조).
- 병렬 실행은 **동시 2개까지만** (이미지 생성은 ChatGPT 구독 사용량을
  소모하므로 과도한 동시 실행을 피한다). 사용량 한도 초과로 실패하면
  사용자에게 알리고 대기 후 재개한다.
- 생성된 이미지를 Read로 열어 확인한다: 스타일 일치, 스타일 보드가 아닌 단일
  장면인지, 검은 바(공인), 텍스트 오염 여부. 문제 있으면 프롬프트 수정 후
  재생성 (클립당 최대 2회).

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

- 자동 처리: 클립당 앞 0.25s 컷 → 정규화·연결 → 나레이션 구간을 각 클립
  시작점에 정확히 배치 → 클립 자체 오디오 저볼륨(효과음 유지) → `music/`
  랜덤 1곡 저볼륨 루프.
- 멀티 챕터면 chapters 배열에 순서대로 넣는다 (챕터 연결도 자동).

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
- 나레이션: 로컬 clone-voice 백엔드(무료). Whisper 정렬도 로컬(무료).
- 3~4챕터 실행은 소모가 크므로, 멀티 챕터 요청이 아니면 기본 1챕터로
  진행한다.
