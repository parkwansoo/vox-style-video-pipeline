---
name: style-sheet
description: 레퍼런스 이미지 2~5장에서 시각 스타일을 역설계해 마스터 스타일 시트(assets/style_reference.png)와 그 생성 프롬프트를 만든다. 사용자가 "레퍼런스 이미지로 스타일 시트 만들어줘", "이 이미지들 스타일 뽑아줘", "스타일 레퍼런스 새로 만들자"라고 하면 사용. vox-video의 모든 이미지 생성이 이 시트를 기준으로 하므로, 새 비주얼 스타일로 갈아탈 때 먼저 실행한다.
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
4. 산출물은 전부 `assets/`에 남긴다 (DNA·프롬프트·시트 3종 세트).

## 0. 사전 점검

- 레퍼런스 이미지가 **2장 이상**인가 (1장이면 소재/스타일 구분 불가 — 경고 후
  진행하되 confidence를 전반적으로 낮게 잡는다). 권장 2~5장, 최대 8장
- `codex login status`가 ChatGPT 로그인 상태인가 (시트 렌더에 필요)
- `.venv`에 pillow·numpy·scikit-learn이 있는가
  (없으면 `.venv/bin/pip install -r requirements.txt`)
- **기존 `assets/style_reference.png`를 덮어쓰기 전에 반드시 사용자에게
  확인한다.** 기본은 새 이름(`assets/style_reference_<이름>.png`)으로 저장하고,
  교체 여부는 사용자가 정한다

## 1. 팔레트 추출 (스크립트)

```bash
.venv/bin/python3 .claude/skills/style-sheet/scripts/extract_palette.py refs/*.png --k 6 --json assets/palette_raw.json
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

DNA를 `assets/style_dna.json`에 쓴다:

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
  --dna assets/style_dna.json \
  --out-prompt assets/style_prompt.txt \
  --render assets/style_reference_<이름>.png
```

- 프롬프트는 11슬롯 골격에 값만 끼워 넣어 조립된다 (문구는 항상 동일)
- 렌더는 Codex 내장 이미지 생성(ChatGPT 구독 OAuth) — API 키 불필요
- 실패 시 1회 자동 재시도. 계속 실패하면 `codex login status` 확인 안내

## 5. 자기 검증 (필수)

생성된 시트를 **Read로 열어** 원본 레퍼런스와 나란히 비교한다:

- [ ] 스타일 보드 형태인가 (장면 일러스트가 아니라 패널·라벨이 있는 시트)
- [ ] 팔레트 스와치의 색이 DNA의 hex와 맞는가
- [ ] 표면 질감이 레퍼런스와 같은 계열인가
- [ ] 타입 샘플 문자열이 지정한 그대로 인쇄됐는가 (오탈자·깨진 글자 없음)
- [ ] 컴포넌트들이 하나의 제작 논리로 보이는가

어긋나면 해당 슬롯만 고쳐 1회 재생성한다. 두 번 실패하면 무엇이 안 되는지
사용자에게 보고하고 멈춘다 (구독 사용량 낭비 방지).

## 6. 전달 & 연결

- 산출물 3종을 알린다: `style_dna.json`(수정 가능) / `style_prompt.txt` /
  `style_reference_<이름>.png`
- 시트 이미지를 SendUserFile로 보낸다
- **vox-video에 적용하려면** `assets/style_reference.png`로 교체해야 함을
  안내하고, 교체 여부를 사용자에게 확인받는다 (기존 시트 백업 후 복사)

## 비용

- 팔레트 추출: 로컬 무료
- 시트 렌더: ChatGPT 구독 사용량 1회 (이미지 생성은 텍스트 대비 3~5배 차감)
- 재생성은 클립당 최대 2회로 제한 — DNA를 고쳐 정확도를 올리는 쪽이 싸다
