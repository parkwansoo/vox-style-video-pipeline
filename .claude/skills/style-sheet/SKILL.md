---
name: style-sheet
description: 레퍼런스 이미지 2~8장에서 시각 스타일을 역설계해 styles/<이름>/ 폴더에 스타일 DNA·생성 프롬프트·마스터 스타일 시트를 만든다. 사용자가 "레퍼런스 이미지로 스타일 시트 만들어줘", "이 이미지들 스타일 뽑아줘", "스타일 레퍼런스 새로 만들자"라고 하면 사용. vox-video의 모든 이미지 생성이 이 시트를 기준으로 하므로, 새 비주얼 스타일로 갈아탈 때 먼저 실행한다.
---

# 스타일 시트 역설계

레퍼런스 이미지들을 관찰해 **11슬롯 스타일 DNA**를 뽑고, 그것으로 마스터
스타일 시트 한 장을 생성한다. 산출된 시트는 vox-video의 모든 클립 이미지
생성에 입력으로 쓰인다.

## 절대 원칙

1. **여러 장에서 반복되는 것만 스타일이다.** 한 장에만 있는 건 그 이미지의
   소재다. 이 구분이 결과 품질을 가장 크게 좌우한다.
2. **색은 눈대중 금지.** hex는 반드시 `extract_palette.py` 값을 쓴다.
3. **DNA JSON을 먼저 만들고 사용자에게 보여준다.** 바로 이미지를 생성하지
   않는다 — 사람이 검증·수정할 수 있어야 한다.
4. 산출물은 전부 `styles/<스타일명>/`에 모은다. `assets/`는 **현재 활성 스타일
   한 벌**만 두는 슬롯이므로 여기에 작업물을 흘리지 않는다.

## 폴더 구조

```
refs/                        새 레퍼런스를 넣는 인박스 (작업 끝나면 비운다)
styles/<스타일명>/
├── refs/                    이 스타일의 레퍼런스 원본 (git 제외)
├── style_dna.json           11슬롯 값
├── style_prompt.txt         조립된 생성 프롬프트
├── palette_raw.json         k-means 원시값
├── style_reference.png      생성된 시트
└── NOTES.md                 출처·판단·주의사항
assets/
├── style_reference.png      활성 스타일 복사본 (vox-video가 참조)
└── ACTIVE_STYLE             활성 스타일 폴더 이름
```

스타일명은 소문자 하이픈(`mg-bodylab`), DNA의 `system_name`은 대문자
(`MG-BODYLAB`)로 짝을 맞춘다.

## 0. 사전 점검

- 레퍼런스 이미지가 **2장 이상**인가 (1장이면 소재/스타일 구분 불가 — 경고 후
  진행하되 confidence를 전반적으로 낮게 잡는다). 권장 2~8장
- `codex login status`가 ChatGPT 로그인 상태인가 (시트 렌더에 필요)
- `.venv`에 pillow·numpy·scikit-learn이 있는가
  (없으면 `.venv/bin/pip install -r requirements.txt`)
- **`assets/`는 절대 덮어쓰지 않는다.** 새 스타일은 `styles/<이름>/`에만 만들고,
  활성 전환은 6단계에서 사용자 확인을 받은 뒤에 한다

## 1. 스타일 폴더 만들고 팔레트 추출

먼저 스타일명을 정해 폴더를 만들고 레퍼런스를 인박스에서 옮긴다.

```bash
mkdir -p styles/<스타일명>/refs && mv refs/*.png styles/<스타일명>/refs/
.venv/bin/python3 .claude/skills/style-sheet/scripts/extract_palette.py styles/<스타일명>/refs/*.png --k 6 --json styles/<스타일명>/palette_raw.json
```

출력에서 읽을 것:
- `hex` — 그대로 쓴다 (눈대중 금지)
- `coverage` — 20%↑ 주조색 / 10%↓ 강조색
- `edge_ratio` — 0.45↑면 선·윤곽 전용 색
- `shared: false` — 그 이미지만의 소재색이므로 **버린다**
- 명도만 다른 인접 색(종이 톤의 단계들)은 **한 색으로 병합**해 해석한다

색이 2~3개로 충분한 스타일이면 억지로 5개까지 채우지 않는다. `--k`를 낮춰
다시 돌려도 된다.

## 2. 이미지 관찰 → 스타일 DNA 작성

`references/extraction-rubric.md`를 **반드시 읽고** 그 순서대로 관찰한다.
레퍼런스 이미지를 Read로 모두 열어본다 — 파일명이나 추측이 아니라 실제
픽셀을 봐야 한다.

`references/slot-template.md`의 11슬롯과 정답지 3종(BLUEPRINT/Vox/SOFT3D)을
읽고 **같은 밀도와 어투로** 채운다.

DNA를 `styles/<스타일명>/style_dna.json`에 쓴다:

```json
{
  "system_name": "MG-NOIR",
  "series_type": "true-crime investigative",
  "surface": "high-contrast newsprint with heavy ink bleed and torn edges",
  "mood": ["tense", "nocturnal", "grainy"],
  "type_specimen": "H1 sample \"THE FILE\" in stencil caps; a case label sample \"EXHIBIT 04\"",
  "type_quality": ["stamped", "high-contrast"],
  "palette": [
    {"name": "Ink Black", "hex": "#0E0E10"},
    {"name": "Newsprint Gray", "hex": "#B9B4AC"},
    {"name": "Signal Amber", "hex": "#E8A33D"}
  ],
  "color_rules": "Amber is reserved for evidence markers and underlines; it never fills a shape",
  "components": ["...", "...", "...", "...", "..."],
  "construction_logic": "heavy ink bleed, 45-degree halftone screen, torn edges",
  "mini_scenes": ["...", "...", "..."],
  "motion_signature": ["...", "...", "...", "..."],
  "stage": null,
  "finish": ["coarse newsprint grain", "no glossy 3D", "no lens flares"],
  "confidence": {
    "palette": "high — extract_palette.py 실측",
    "construction_logic": "high — 4장 모두에서 관찰",
    "motion_signature": "low — 정지 이미지에서 추론",
    "type_specimen": "medium — 레퍼런스에 글자가 적어 일부 창작"
  },
  "rejected": ["배(한 장에만 등장) — 소재로 판단해 제외"]
}
```

**필수 규칙**
- **팔레트는 2~5색.** 명도만 다른 인접 색은 대표색으로 병합한다 (6색 이상이면
  make_sheet.py가 경고한다)
- **각 항목은 짧은 명사구.** `a torn-paper edge` 수준이지 설명문이 아니다.
  90자를 넘으면 경고가 뜬다. 기존 3종 프롬프트는 1782~2258자이며 **2400자를
  넘으면 시트가 아니라 설명서가 되고 있다는 뜻**이다
- `surface`에 Mood를 적지 않는다 (템플릿이 따로 붙여 중복 출력된다)
- `mini_scenes`는 정확히 3개, `motion_signature`는 정확히 4개
- `stage`는 레퍼런스들의 배경이 **같은 계열일 때만** 채운다. 아니면 `null`
  (억지로 넣으면 이후 모든 클립 배경이 똑같아진다)
- `color_rules`는 반드시 한 문장으로 — 이게 없으면 강조색이 화면을 덮는다
- `confidence`와 `rejected`를 채워 판단 근거를 남긴다

## 3. 사용자 확인 (생성 전 게이트)

DNA를 표로 요약해 보여주고 확인을 받는다. 최소한 이 항목들:

| 슬롯 | 값 |
|---|---|
| 시스템 이름 | MG-NOIR |
| 팔레트 | Ink Black #0E0E10 / Newsprint Gray #B9B4AC / Signal Amber #E8A33D |
| 색 규칙 | Amber는 강조 전용, 면을 채우지 않음 |
| 제작 논리 | heavy ink bleed, 45° halftone screen, torn edges |
| 제외한 것 | 배(한 장에만 등장) |
| 낮은 확신 | motion_signature (정지 이미지 추론) |

이름·팔레트·제외 항목은 사용자가 바꾸고 싶어 하는 경우가 많다. 확인 후
진행한다.

## 4. 프롬프트 조립 + 시트 생성

```bash
.venv/bin/python3 .claude/skills/style-sheet/scripts/make_sheet.py \
  --dna styles/<스타일명>/style_dna.json \
  --out-prompt styles/<스타일명>/style_prompt.txt \
  --render styles/<스타일명>/style_reference.png
```

- 프롬프트는 11슬롯 골격에 값만 끼워 넣어 조립된다 (문구는 항상 동일)
- **경고가 뜨면 렌더 전에 DNA를 고친다.** 팔레트 색 수, 항목 길이, 총 분량을
  검사하며 경고를 무시하고 렌더하면 구독 사용량만 낭비된다
- 렌더는 Codex 내장 이미지 생성(ChatGPT 구독 OAuth) — API 키 불필요
- 실패 시 1회 자동 재시도. 계속 실패하면 `codex login status` 확인 안내

사용자가 직접 다른 도구로 생성하겠다고 하면, 붙여넣기용 변형 두 개를 만들어
준다 (레퍼런스 첨부 여부에 따라 헤더만 다르고 본문은 동일하게):
`style_prompt_standalone.txt` / `style_prompt_with_refs.txt`

## 5. 자기 검증 (필수)

생성된 시트를 **Read로 열어** 원본 레퍼런스와 나란히 비교한다:

- [ ] 스타일 보드 형태인가 (장면 일러스트가 아니라 패널·라벨이 있는 시트)
- [ ] 팔레트 스와치의 색이 DNA의 hex와 맞는가
- [ ] 표면 질감이 레퍼런스와 같은 계열인가
- [ ] 타입 샘플 문자열이 지정한 그대로 인쇄됐는가 (오탈자·깨진 글자 없음)
- [ ] 컴포넌트들이 하나의 제작 논리로 보이는가

어긋나면 해당 슬롯만 고쳐 1회 재생성한다. 두 번 실패하면 무엇이 안 되는지
사용자에게 보고하고 멈춘다 (구독 사용량 낭비 방지).

## 6. 마무리 — NOTES 기록, 인박스 비우기, 활성 전환

**① NOTES.md를 쓴다** (`styles/<스타일명>/NOTES.md`). 나중에 이 스타일이
뭐였는지 알 수 있어야 한다:
- 출처 (사용자가 말해준 참조 대상 등). 브랜드명은 여기 기록하되 **생성
  프롬프트의 `system_name`에는 넣지 않는다** — 로고·워터마크가 그려지거나
  모델이 거부할 수 있고, 시각 정보는 이미 11슬롯에 다 있다
- 팔레트와 색 규칙, 제작 논리 요약
- **원본 콘텐츠의 비율** (세로 9:16 스타일이면 반드시 적는다 — 시트 자체는
  16:9지만 그 스타일로 만들 영상은 9:16이어야 한다)
- 제외한 것들과 그 이유

**② 인박스를 비운다**: `refs/`에 남은 파일이 없어야 다음 작업과 섞이지 않는다.

**③ 산출물을 알리고 시트 이미지를 보여준다.**

**④ 활성 전환은 사용자 확인 후에만**:
```bash
cp styles/<스타일명>/style_reference.png assets/style_reference.png
echo "<스타일명>" > assets/ACTIVE_STYLE
```
전환하면 이후 만드는 모든 영상이 이 스타일로 바뀐다는 점을 알린다. 전환하지
않으면 라이브러리에만 남고 현재 영상 제작에는 영향이 없다.

## 비용

- 팔레트 추출: 로컬 무료
- 시트 렌더: ChatGPT 구독 사용량 1회 (이미지 생성은 텍스트 대비 3~5배 차감)
- 재생성은 클립당 최대 2회로 제한 — DNA를 고쳐 정확도를 올리는 쪽이 싸다
