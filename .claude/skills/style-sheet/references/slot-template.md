# 마스터 스타일 시트 — 11슬롯 골격

모든 스타일 시트 프롬프트는 **아래 골격을 그대로** 따른다. 스타일이 아무리
달라도 구조는 바뀌지 않는다 — 바뀌는 것은 슬롯을 채우는 값뿐이다.

## 골격 (이 순서, 이 문장 그대로)

```
MASTER STYLE SHEET - ①{SYSTEM_NAME} visual system, one 16:9 reference board. A single
polished art-direction sheet defining the visual language for a ②{SERIES_TYPE} explainer
series. Editorial grid, consistent margins, section labels. Baked-in typography is
intentional here (this is a style guide).

SURFACE & MOOD: ③{표면 재질·바탕}. Mood: ④{분위기 형용사 3~4개}.

TYPE SPECIMEN PANEL: H1 sample "⑤a{H1 샘플어}" in ⑤b{서체 성격}; ⑤c{보조 샘플 1~2개,
각각 실제 문자열 포함}. Typography ⑤d{품질 서술}, no warped letters.

PALETTE STRIP: labeled swatches - ⑥{이름 #HEX} × 2~5개. ⑦{색 역할 분담 규칙}.

COMPONENT ZOO PANEL: ⑧{구성요소 5~6개, 세미콜론으로 구분}. All share one construction
logic: ⑨{공통 제작 논리}.

MINI-SCENE PANEL: 3 small example frames - (a) ⑩a, (b) ⑩b, (c) ⑩c. Same lighting and
finish throughout.

MOTION THUMBNAILS: 4 tiny storyboard frames with arrows only: ⑪a / ⑪b / ⑪c / ⑪d.

[선택] One panel shows THE STAGE: ⑫{모든 클립이 올라가는 고정 배경 세계}. No midground
elements present in this panel.

FINISH: ⑬{마감 특성}, ⑭{금지 목록}. No watermarks, no lorem ipsum, no unrelated logos,
no random gibberish text - every visible word is one of the samples above.
```

## 슬롯 작성 규칙

| 슬롯 | 필수 조건 |
|---|---|
| ① SYSTEM_NAME | 대문자 하이픈 표기 (`MG-BLUEPRINT`, `MG-SOFT3D`). Vox처럼 고유 이름도 가능 |
| ② SERIES_TYPE | "무엇을 설명하는 시리즈인가" — `how-it-works / engineering`, `documentary-collage`, `friendly-metaphor` |
| ③ 표면 | 재질 + 색조 + 질감을 한 문장에. hex 힌트를 괄호로 넣어도 좋다 |
| ④ Mood | 형용사 3~4개, 쉼표 구분. 모순되는 단어를 섞지 않는다 |
| ⑤ 타입 | **실제 샘플 문자열을 반드시 지정**한다. 시트에 그 단어가 그대로 인쇄된다 |
| ⑥ 팔레트 | 2~5색. 이름 + hex 둘 다. 색이 적을수록 시스템이 강해진다 |
| ⑦ 색 규칙 | 어떤 색이 면을 채우고 어떤 색이 선·강조 전용인지 **반드시 명시** |
| ⑧ 컴포넌트 | 5~6개. 그 스타일에서 반복 등장하는 부품들 |
| ⑨ 제작 논리 | 모든 부품을 관통하는 한 문장. **이 슬롯이 시트의 심장이다** |
| ⑩ 미니신 | 컴포넌트를 조합한 실사용 예 3개 |
| ⑪ 모션 | 동작 시그니처 4개. 정지 이미지에서 추론했다면 confidence를 낮게 표기 |
| ⑫ THE STAGE | 고정 배경이 있는 시스템에만. 없으면 이 문단을 통째로 뺀다 |
| ⑬⑭ 마감·금지 | 그 스타일이 **되지 말아야 할 것**을 구체적으로 |

## 정답지 — 실제로 작동한 예시 3종

밀도와 어투의 기준으로 삼는다. 슬롯을 채울 때 이 셋과 같은 수준의 구체성을
유지한다.

---

### 예시 1 — MG-BLUEPRINT (2색 극단적 절제)

MASTER STYLE SHEET - MG-BLUEPRINT visual system, one 16:9 reference board. A single polished art-direction sheet defining the visual language for a how-it-works / engineering explainer series. Editorial grid, consistent margins, section labels. Baked-in typography is intentional here (this is a style guide).

SURFACE & MOOD: deep blueprint blue (#1B3A6B-ish) with white ruled construction lines and faint grid paper texture. Mood: precise, technical, draftsman-calm.

TYPE SPECIMEN PANEL: H1 sample "ASSEMBLY VIEW" in technical lettering caps; a dimension label sample "142mm t0.5"; a revision stamp sample "REV. 03". Typography sharp, ruled, no warped letters.

PALETTE STRIP: Labeled swatches - Blueprint Blue #1B3A6B, White #FFFFFF (lines only). Strictly two-tone - no additional color fills anywhere on the sheet.

COMPONENT ZOO PANEL: an exploded-view diagram of three stacked parts with dashed construction lines connecting them; a dimension arrow with a measurement label; a circled detail callout with a leader line; a revision stamp in the corner. All share one construction logic: thin white ruled lines on blueprint blue, technical precision.

MINI-SCENE PANEL: 3 small example frames - (a) an exploded diagram assembling with dimension arrows, (b) a circled detail callout zoomed on one joint, (c) a revision stamp beside a dimension label. Same lighting and finish throughout.

MOTION THUMBNAILS: 4 tiny storyboard frames with arrows only: construction lines draft on stroke-by-stroke / exploded parts slide together and assemble / camera tracks slowly along the schematic / detail circle zooms in on a joint.

FINISH: crisp ruled linework, faint grid paper texture, no color fills beyond the two-tone scheme, no photorealism, no glow effects. No watermarks, no lorem ipsum, no unrelated logos, no random gibberish text - every visible word is one of the samples above.

---

### 예시 2 — Vox Style (5색 + 역할 분담 + THE STAGE)

MASTER STYLE SHEET - Vox Style visual system, one 16:9 reference board. A single polished art-direction sheet defining the visual language for a documentary-collage explainer series. Editorial grid, consistent margins, section labels. Baked-in typography is intentional here (this is a style guide).

SURFACE & MOOD: aged archival paper / muted map texture field, visible grain and print texture. Mood: newsroom-serious, layered, tactile, slightly retro.

TYPE SPECIMEN PANEL: H1 sample "THE DEAL" in condensed bold headline caps; a huge stat number sample "$123" treated as a hero character; small annotation label sample "Fig. 3 - Trade Route". Typography aligned, sharp, no warped letters.

PALETTE STRIP: labeled swatches - Archival Tan #C9BB9C, Ink Black #1A1A1A, Halftone Gray #8C8C8C, Hot Red #D62E1F, Mustard #D9A441. Red is reserved for strokes, underlines, and arrows; mustard is secondary accent only.

COMPONENT ZOO PANEL: a black-and-white halftone cutout of a generic figure with a rough white keyline and an offset red stroke behind it; a torn-paper edge; a big red stat counter card; a map pin marker; an underline swipe in red beneath a headline word; an archival photo card with a thin white border. All share one construction logic: halftone texture, offset stroke pop.

MINI-SCENE PANEL: 3 small example frames - (a) two halftone figures on the stage with a stat counter between them, (b) a map with a pin and a red underline swipe beneath a caption, (c) an archival photo card with a torn edge beside a mustard label. Same lighting and finish throughout.

MOTION THUMBNAILS: 4 tiny storyboard frames with arrows only: cutout springs up with slight overshoot / counter ticks upward / red underline swipes beneath a word / camera holds a slow 2% drift across the stage.

One panel shows THE STAGE: the persistent background world every clip lives on - a muted archival map/texture field, empty, pre-lit, evenly toned, ready for cutouts and stat cards to enter and exit. No midground elements present in this panel.

FINISH: print grain, halftone dot texture, torn-paper edges, matte finish, no glossy 3D, no lens flares. No watermarks, no lorem ipsum, no unrelated logos, no random gibberish text - every visible word is one of the samples above.

---

### 예시 3 — MG-SOFT3D (질감·조명 중심, 개수 제한 규칙)

MASTER STYLE SHEET - MG-SOFT3D visual system, one 16:9 reference board. A single polished art-direction sheet defining the visual language for a friendly-metaphor explainer series. Editorial grid, consistent margins, section labels. Baked-in typography is intentional here (this is a style guide).

SURFACE & MOOD: seamless pastel studio backdrop (soft peach-to-cream sweep), soft global illumination, no hard shadows. Mood: friendly, tactile, toy-like, calm.

TYPE SPECIMEN PANEL: H1 sample "BUILDING BLOCKS" in clean geometric sans, minimal and modest in size; a small label sample "STEP 1". Typography sharp, no warped letters, used sparingly.

PALETTE STRIP: Labeled swatches - Pastel Peach #F5D9C8, Clay Cream #EDE4D3, Soft Blue #ABCDE0, Soft Green #B7D9B0. Matte, low-saturation, no neon or metallic accents.

COMPONENT ZOO PANEL: a rounded clay sphere; a rounded clay cube; a simple character-less clay "hand" prop; a thin clay ring; a floating pastel geometric shape. All share one construction logic: matte clay finish, soft rounded edges, gentle ambient occlusion, no hard speculars.

MINI-SCENE PANEL: 3 small example frames - (a) a clay sphere and cube mid-assembly, (b) a clay ring resting beside a floating shape, (c) a simple clay prop with a soft shadow beneath it. Same lighting and finish throughout, max 3 hero objects per frame.

MOTION THUMBNAILS: 4 tiny storyboard frames with arrows only: object drops in with squash-and-stretch bounce / two parts snap together / object rotates on a turntable / shape settles with a gentle physics wobble.

FINISH: soft matte clay finish, gentle ambient occlusion, no hard speculars, no photorealism. No watermarks, no lorem ipsum, no unrelated logos, no random gibberish text - every visible word is one of the samples above.

---

## 세 예시의 대비 — 슬롯이 어떻게 달라지는가

| 슬롯 | BLUEPRINT | Vox | SOFT3D |
|---|---|---|---|
| 팔레트 수 | 2 (엄격) | 5 (역할 분담) | 4 (저채도) |
| 색 규칙 | "strictly two-tone" | "빨강=선 전용, 머스타드=보조" | "무광·저채도, 네온 금지" |
| 제작 논리 | 얇은 흰 괘선, 기술적 정밀 | 하프톤 + 오프셋 스트로크 팝 | 무광 클레이 + 부드러운 AO |
| 타입 비중 | 치수·리비전 라벨 중심 | 헤드라인 + 거대 숫자가 주인공 | 최소한으로 절제 |
| THE STAGE | 없음 | 있음 | 없음 |
| 금지 | 색 채움·글로우 | 광택 3D·렌즈 플레어 | 포토리얼·하드 스페큘러 |

**읽어낼 것**: 팔레트가 적으면 규칙이 강해지고(BLUEPRINT), 많으면 역할 분담이
필수가 된다(Vox). 타입이 주인공인 시스템과 절제하는 시스템이 갈린다.
