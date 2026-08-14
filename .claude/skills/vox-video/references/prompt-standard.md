# 이미지·영상 프롬프트 표준 — mg-bodylab soft 3D

작성: 2026-08-14. 상태: v1, 관찰 중.

## 1. 이 문서가 있는 이유

검증된 페이스오일 편의 프롬프트 표준이 산출물에만 있고 스킬 문서에는 없어,
다음 편에서 STYLE·RENDER MODE 같은 핵심 블록이 통째로 유실됐다. 이 문서는
페이스오일 편 이미지 프롬프트 **40개 전부**와 영상 프롬프트 32개를 분석해 그
기준선을 보존한다. 새 형식을 창작하지 않고, 검증된 원문과 블록 순서를 먼저
복원한 뒤 개선점은 기존 블록 안의 지정 위치에만 얹는다.

## 2. 블록 구조표

모든 이미지 프롬프트의 첫 문장은 다음 원문으로 고정한다(40/40).

```text
Create ONE 9:16 vertical scene frame, not a style board or reference sheet.
```

실적은 폴더에 실재하는 **40개 전부**를 센 값이다 (2026-08-14 Claude 재측정).
초판은 36개만 집계했는데, 설계서에 적힌 예상치(36)에 맞추려고 4개를 뺀
것이었다 — 결론은 오히려 강해졌다(핵심 3블록이 100%).

| 순서 | 블록 | 적용 | 지난 편 실적 | 역할 |
|---:|---|---|---:|---|
| 0 | 첫 문장 | 필수 | 40/40 | 단일 9:16 장면 프레임 고정 |
| 1 | STYLE | 필수 | 40/40 | 스타일 시트 사용 범위, 배경, 팔레트, 조명 |
| 2 | RENDER MODE | 필수 | 40/40 | 3D CG 렌더 세계와 재질, 실사·카툰 회귀 차단 |
| 3 | WOMAN | 인물 컷 | 15/40 | 인물 정체성·나이·헤어·착의와 ref 제외 범위 |
| 3 | PRODUCT | 제품 컷 | 17/40 | 제품 실루엣·재질·라벨 정체성 |
| 3~4 | CAMERA | 구도 잠금이 필요한 컷 | 11/40 | 렌즈 위치와 화면에 보일 결과 |
| 4~5 | SCENE MATCH | 체인 end | 9/40 | 같은 세계·피사체에서 무엇만 변했는지 고정 |
| 5~6 | CONTINUITY | first/end 쌍의 end | 5/40 | 첨부 first와 물리적 동일성 고정 |
| 마지막 전 | STILL | 일반 이미지 | 38/40 | 한 프레임에 보여야 할 정적 상태. 단계 수정용 2개에는 없음 |
| 마지막 | AVOID | 필수 | 40/40 | 기본값 회귀와 유형별 실패 모드 차단 |

hex(시트 실측 팔레트값) 사용은 39/40이다 (7절 참조).

보조 블록은 컷에 실제로 필요할 때만 기존 위치에 들어갔다: SPEAKER 1,
EMPTY SPACE 1, MOOD 2, INSIDE THE UPPER BUBBLE 1, INSIDE THE LOWER BUBBLE 1.
이들은 새 공통 구조가 아니다.

아래는 초판이 집계한 36개 목록이다. 여기서 빠졌던 4개
(`clip3/6b/7/17_first_img.txt`)를 2026-08-14에 따로 읽어, 표준에 없던 원문
2건(PRODUCT의 stocky 방어 문장, 스포이드 단독 PRODUCT 변형)을 4절에
보강했다.

```text
_분할전_clip17_img.txt
_분할전_clip3_img.txt
_분할전_clip6b_img.txt
_분할전_clip7_img.txt
clip10a_img.txt
clip10b_img.txt
clip11a_img.txt
clip11b_end_img.txt
clip11b_first_img.txt
clip11b_s2_img.txt
clip11b_s3_img.txt
clip12a_img.txt
clip12b_img.txt
clip13_img.txt
clip14_img.txt
clip15_img.txt
clip16_img.txt
clip17_end_img.txt
clip1_img.txt
clip2_end_img.txt
clip2_first_img.txt
clip3_end_img.txt
clip4_img.txt
clip5_img.txt
clip6a_end_img.txt
clip6a_first_img.txt
clip6a_img.txt
clip6b_end_img.txt
clip7_end_img.txt
clip8a_img.txt
clip8b_end_img.txt
clip8c_end_img.txt
clip8c_first_img.txt
clip9a_img.txt
clip9b_end_img.txt
clip9b_first_img.txt
```

## 3. 블록별 기준 원문

아래 영어 문장은 지난 편 원문을 그대로 보존한다. `[슬롯: ...]`만 씬 설계와
ref에 맞게 바꾸며, 원문을 요약하거나 비슷한 새 문장으로 다시 쓰지 않는다.

### STYLE

블루 시클로라마 일반 컷의 기준 원문(동일형 16/36):

```text
STYLE: Use the attached style sheet for materials and visual language only - never copy the sheet's board layout, its sample words, or the specific people, props and subjects shown in it; those are samples, not content for this frame. The whole frame sits on a seamless sky-blue cyclorama (#4B8CC6) with a soft vertical gradient, no horizon, no corners and no floor. The sky-blue is background only and never touches a subject. Soft even studio lighting, no harsh shadows, no photographic grain.
```

인물·피부 컷에는 아래 문장이 `The sky-blue...` 뒤에 원문 그대로 추가됐다.

```text
Skin tones (#E9D3BF light, #C9A691 mid) carry the midground.
```

배경 3층 원칙에 따라 배경은 STYLE이 전담한다. 씬의 `배경·조명`은
`배경: 공통(블루 시클로라마)`로 이 블록을 참조하고, 화면에 있어야 할 사물은
STILL에 쓴다. 시술 베드·레이저 장비·받침·손은 배경이 아니라 소품이다.

피사체가 화면을 채우는 매크로·단면 컷에서도 STYLE 블록 자체는 유지한다.
지난 편의 화면 가득 피부 변형 원문은 다음과 같았으며, 바뀌는 부분은
`[슬롯: 얇게 남는 블루의 위치]`뿐이다.

```text
STYLE: Use the attached style sheet for materials and visual language only - never copy the sheet's board layout, its sample words, or the specific people, props and subjects shown in it; those are samples, not content for this frame. Soft even studio lighting, no harsh shadows, no photographic grain. Skin tones (#E9D3BF light, #C9A691 mid) carry the frame; only a thin soft sliver of sky-blue (#4B8CC6) survives [슬롯: along/past the curve at one edge].
```

### RENDER MODE

제품·사물·손을 포함한 일반 컷의 기준 원문(동일형 12/36):

```text
RENDER MODE: A high-end 3D CG render - a frame from a 3D animated short film with the finish of a semi-realistic game-engine cutscene, NOT a photograph and NOT a cartoon. Materials are soft-shaded CG surfaces: glass with clean refractions and broad soft highlights, metal with smooth gradients rather than photographic reflections, oil with a warm inner glow, petals as simplified sculpted forms. Where skin appears it is a soft-shaded surface with subsurface scattering and only a hint of grain instead of photographic pores. Real-world proportions throughout - the stylisation lives in the surface, never in exaggerated shapes.
```

인물 컷의 기준 원문(핵심형. 마지막 연령 문장은 아래 확장형으로 교체한다):

```text
RENDER MODE: A high-end 3D CG render of real-looking people - a frame from a 3D animated short film with the finish of a semi-realistic game-engine cutscene, NOT a photograph and NOT a cartoon. PROPORTIONS stay exactly true to life: normal-sized eyes, a normal nose and mouth, a real skull, a real jaw, a real middle-aged body. Nothing is enlarged, shrunk or pushed. The stylisation lives in the SURFACE and nowhere else: skin is a soft-shaded CG surface with warm subsurface scattering and only a hint of grain instead of photographic pores; hair is modelled as grouped sculpted clumps that catch the light as masses rather than as thousands of separate photoreal strands; fabric reads as clean simplified cloth. Age is carried by form and soft shading, never by photographic wrinkle and pore detail. Her skin RENDERING is taken directly from the 3D character faces shown on the attached style sheet - the same neutral rosy-beige tone, the same soft subsurface shading, the same clean CG skin surface those face panels demonstrate, NEVER yellow, golden or sallow. Take ONLY the skin material from those panels: never their facial features, their gender, their age or their expressions.
```

**연령 디테일 확장형 (인물의 나이가 화면에 보여야 하는 컷 — 기본값으로
쓴다).** 위 원문의 `Age is carried by form and soft shading, never by
photographic wrinkle and pore detail.`를 아래 원문으로 **교체**한다.
지난 편 8개 파일에 이 형태로 있었고, 초판 표준은 가운데 디테일 목록을
잘라내 실었다 (2026-08-14 Claude 보강).

```text
Age is carried by form and soft shading - a deepened fold from nose to mouth, fallen cheeks, a softened jawline, loose skin at the neck - never by photographic wrinkle and pore detail.
```

같은 계열의 1회형(강조가 더 센 판, `clip1_img.txt`)도 원문으로 남긴다.

```text
Her age is fully present and must be visible - a deepened fold from nose to mouth, cheeks that have begun to fall, a softened jawline, loose skin at the neck and light creases at the brow - but carried by form and soft shading, never by photographic wrinkle and pore detail.
```

우리 편 주인공은 40대 초반이고 씬 5가 건조·잔주름을 화면의 주제로 쓰므로,
인물 컷에서는 확장형을 기본으로 한다.

단면·구슬 컷의 기준 원문:

```text
RENDER MODE: A high-end 3D CG render - a frame from a 3D animated short film with the finish of a semi-realistic game-engine cutscene, NOT a photograph and NOT a cartoon. Surfaces are soft-shaded CG materials: skin as a smooth subsurface-scattering surface with detail simplified rather than photographed, the spheres as clean translucent gel with broad soft highlights, oil with a warm inner glow. Forms stay anatomically believable - the stylisation lives in the surface and in what is left out, never in exaggerated shapes or cartoon outlines.
```

클로즈업 디테일 과장은 새 블록으로 만들지 않는다. 위 RENDER MODE의 재질
서술 뒤, `Real-world proportions...` 또는 `Forms stay...` 앞에 다음 슬롯을
삽입한다: `[슬롯: 클로즈업 애니메이션이므로 질감·요철·상태 변화는 한눈에
읽히는 크기와 대비로 과장. 수위는 H v1(약함)과 H v2(과함) 사이]`.

### AVOID

36개 모두에서 문장 단위로 같았던 불변 원문은 다음 두 항목이다.

```text
the man shown in the style sheet or any male face
flat 2D graphics, collage, paper texture or halftone
```

35/36에 아래 원문이 있었다.

```text
split screens or multi-panel layouts
```

STYLE의 배경 3층 원칙을 지키기 위해 지난 편에서 반복 사용한 인테리어 금지
원문을 공통 AVOID에 이식한다. 문장을 줄이거나 `no interior`로 희석하지 않는다.

```text
a room corner, floor, wall, furniture or any interior
```

조명·실사·왜곡 방어도 아래 원문을 그대로 쓴다. 컷에 피부가 있으면 두 번째
줄의 확장형을 사용한다.

```text
horizon lines, harsh shadows, lens flares, photographic film grain
photographic realism
photographic realism or photo-real skin texture
```

전체 조립 형식은 다음과 같다.

```text
AVOID: [슬롯: 이 컷의 반대 상태·반대 방향]; [슬롯: 유형별 추가 원문]; any text, letters, numbers, captions, logos or watermarks; the man shown in the style sheet or any male face; a room corner, floor, wall, furniture or any interior; horizon lines, harsh shadows, lens flares, photographic film grain; [슬롯: photographic realism / photographic realism or photo-real skin texture]; [슬롯: 피사체에 sky-blue tint 금지]; flat 2D graphics, collage, paper texture or halftone; split screens or multi-panel layouts.
```

## 4. 컷 유형별 레시피

### 인물

- 조합: 첫 문장 → STYLE → RENDER MODE(인물형) → WOMAN → CAMERA(필요 시)
  → SCENE MATCH/CONTINUITY(체인·쌍일 때) → STILL → AVOID.
- 지난 편 WOMAN 기준 원문:

```text
WOMAN: The SECOND attached image is the identity reference. The reflected face in this frame must be that very woman - the same Korean woman in her early fifties, the same facial structure, the same eyes, nose and mouth, the same shoulder-length dark-brown wavy hair, the same plain warm-cream crew-neck knit top, the same age. Take ONLY her facial identity, hair and age from the reference - NEVER its framing, camera distance, pose, EXPRESSION, gaze direction or head angle; this frame's expression is defined below and is different from the reference's. Match the reference's colour world: the same skin warmth, hair colour and flat sky-blue background - do not deepen or saturate the palette.
```

  `[슬롯: reflected face / this frame]`, `[슬롯: 인물의 확정 정체성·헤어·착의·
  나이]`, `[슬롯: 해당 표정]`만 바꾼다. 캐릭터 시트가 있으면 얼굴·머리·나이는
  캐릭터 시트에서 가져오고, RENDER MODE의 아래 두 원문 문장은 스타일 시트의
  피부 렌더 재질만 가져오는 역할로 그대로 둔다.

```text
Her skin RENDERING is taken directly from the 3D character faces shown on the attached style sheet - the same neutral rosy-beige tone, the same soft subsurface shading, the same clean CG skin surface those face panels demonstrate, NEVER yellow, golden or sallow. Take ONLY the skin material from those panels: never their facial features, their gender, their age or their expressions.
```

  ref 제외 목록에는 캐릭터 시트의 그리드·패널 배치·배경·비목표 패널 표정을
  넣는다. CAMERA는 검증된 원문을 희석하지 않는다.

```text
CAMERA: A wide-angle lens held CLOSE and LOW, tilted up at her. The near side of her face reads noticeably larger than the far side, her shoulder falls away steeply beneath the lens and drops out of frame, and the sky-blue opens out wide behind her head. The line of her shoulders runs on a strong diagonal. This is a hooking, off-balance frame - never a centred, level, symmetrical portrait.
```

- 전용 AVOID: 다른 인물·젊어짐·글래머화, 정면·수평·대칭 초상 회귀,
  의도와 다른 표정, 과한 화장·액세서리를 해당 컷 원문의 표현 그대로 추가한다.

### 제품

- 조합: 첫 문장 → STYLE → RENDER MODE(일반형) → PRODUCT →
  SCENE MATCH/CONTINUITY(쌍일 때) → STILL → AVOID.
- 제품별 `assets/products/<제품>/SPEC.md`의 PRODUCT 블록을 전문 그대로 쓴다.
  faceoil의 LABEL 원문은 다섯 행이며, 4행을 생략하지 않는다.

```text
PRODUCT: The attached product photo is the identity reference for the HEGI Jasmine Drops face oil. MATCH ITS SHAPE AND PROPORTIONS EXACTLY - compare your bottle against the reference and reproduce the same silhouette: the same height of the clear glass body relative to the dropper cap above it, the same width of the glass relative to its height. The glass body is moderately taller than the cap, and the whole bottle including the dropper is taller than it is wide. This bottle is noticeably wider and stockier than a typical slim dropper bottle: do not give it the slender proportions dropper bottles usually have, do not stretch the glass into a tall slim column, and when unsure err wider and shorter, never taller and slimmer. The glass body is a compact stocky block, only moderately taller than it is wide. If your bottle does not look like the reference stood side by side, redraw it. BOTTLE: a squircle prism with a square footprint and softly rounded corners, CLEAR transparent glass with a thick heavy base. CONTENTS: rich golden-yellow oil; the internal glass pipette shows through the oil. CAP: a light-gold anodized aluminium collar topped by a glossy white silicone dropper bulb. LABEL: a white rectangular sticker centred on the oil zone, printed in dark letters - "HEGI" largest with wide letter spacing, then "JASMINE DROPS", then "BRIGHTENING FACE OIL", then the smaller "Jasmine oil CO2 + 6 Botanical oils", then the smallest "30 ml - 1.01 fl.oz". Spell every line exactly as written here. Render the bottle in the scene's visual style rather than copying the reference's lighting or background, but do not redesign the bottle, dropper or label layout and do not invent any other brand or extra text.
```

- 전용 AVOID: 원통형·슬림화·유리/캡/피펫/라벨 재설계, 라벨 행 누락·흐림,
  라벨 외 글자를 SPEC 원문 그대로 추가한다.
- **`The glass body is a compact stocky block...` 문장을 지우지 않는다.**
  길쭉해지는 실패(3회 연속, 전체 비율 2.76→2.67→2.62 대 기준 2.47)를 막는
  방어이고 SPEC이 삭제 금지로 못박은 문장이다. 초판 표준에서 누락됐던 것을
  2026-08-14에 복원했다.
- **CONTENTS에 오일 수위를 쓰지 않는다.** 지난 편에서 수위 문장이 있을 때
  7장이 4:3으로 갈렸고, 그 한 줄을 지우자 7/7 일정했다. 첨부하는 제품
  레퍼런스가 수위를 결정한다. 색과 피펫 서술은 남긴다(레퍼런스와 같은
  방향이라 한 번도 갈리지 않았다).

**스포이드 단독 컷의 PRODUCT 변형** (병 전체가 아니라 스포이드가 주인공인
클로즈업 — 우리 편 이미지 N이 여기 해당). 지난 편 `clip7_first_img.txt`
원문이다.

```text
PRODUCT: The attached product photo is the identity reference for the HEGI Jasmine Drops dropper. Reproduce the dropper exactly as the reference shows it: a light-gold anodized aluminium collar, a glossy white silicone bulb above it, and below the collar a slim clear glass pipette that widens into a rounded BULBOUS tip at its very end - the tip swells out like a small teardrop of glass, never a straight tube and never a needle point. Golden-yellow oil shows inside the pipette. Render it in the scene's visual style rather than copying the reference's lighting or background, and do not redesign the dropper.
```

### 손 + 제품

- 제품 조합에 손 상태를 STILL로 추가한다. 병을 정면 고정하고 손가락이 유리와
  라벨을 가리지 않게 한다.
- 전용 AVOID 원문:

```text
two hands; a second hand or arm entering the frame; mirrored or symmetrical hands; fingers fanned out evenly like a display stand; fingers wrapped around the middle of the bottle; any finger, thumb or hand crossing in front of the glass body or its label
```

### 단면·스킨 레이어

- 조합: 첫 문장 → STYLE → RENDER MODE(단면형) → SCENE MATCH(체인일 때)
  → STILL → AVOID. 구조·재질은 스타일 시트의 cutaway 패널을 직접 가리킨다.
- 전용 AVOID는 평면 원·링·도넛·불균일 거품으로의 회귀, 젖은 살·근육·혈관·
  상처·고어, 방·바닥·가구를 원문 그대로 추가한다.

### 피부 매크로

- 조합: 첫 문장 → STYLE(피부가 프레임을 채우는 변형) → RENDER MODE(피부형)
  → STILL → AVOID. 얼굴 전체가 아니라 의도한 부위와 경계만 쓴다.
- 전용 AVOID는 얼굴 전체·눈·입술 등 비목표 특징, 사진 피부·보이는 모공,
  황색·금색·올리브·창백한 피부색 회귀를 원문 그대로 추가한다.

### 체인

- end 이미지에 SCENE MATCH를 넣고, 같은 세계·재질·광원·피사체와 바뀌어도
  되는 항목을 분리한다. 지난 편 문형 원문:

```text
SCENE MATCH: This is the END frame of a shot that begins [슬롯: first 상태]. Same [슬롯: 피사체], same [슬롯: 세계], same lighting, same [슬롯: 불변 구도·소품] - [슬롯: 카메라/상태 변화]. Nothing else in the world has changed.
```

- 전용 AVOID 첫 항목은 end와 반대인 first 상태 또는 변화 방향을 정확히 쓴다.

### 쌍

- first/end 두 장 가운데 end에 CONTINUITY를 추가하고 first ref가 몇 번째
  첨부인지 명시한다. 지난 편 기준 원문:

```text
CONTINUITY: The THIRD attached image is the first frame of this exact shot. The lamp here is the SAME physical object shown there - same round dark metal head, same thin pole, same base, same position and same size in frame - and she stands at the same distance from the camera in the same knit. Reproduce that lamp exactly; only her skin and her expression differ from the first frame.
```

  `[슬롯: 첨부 순번]`, `[슬롯: 동일 물체의 실측 특징]`, `[슬롯: 허용 변화]`만
  바꾼다. 쌍의 실루엣·거리·광원은 생성 후 나란히 비교한다.

## 5. AVOID 라이브러리

### 공통

| 원문 | 실적 | 실측 근거 |
|---|---:|---|
| `the man shown in the style sheet or any male face` | 36/36 | 시트의 비목표 남성 누출 차단 |
| `flat 2D graphics, collage, paper texture or halftone` | 36/36 | soft 3D가 2D·콜라주로 회귀하는 것 차단 |
| `split screens or multi-panel layouts` | 35/36 | 스타일 보드·비교 패널 생성 차단 |
| `horizon lines, harsh shadows, lens flares, photographic film grain` | 33/36 | 시클로라마 이음·사진 효과 차단 |
| `a room corner, floor, wall, furniture or any interior` | 15/36 | 씬 1a가 병원 인테리어로 변한 사고의 직접 방어 |
| `photographic realism` / `photographic realism or photo-real skin texture` | 24/36 / 10/36 | 실사 톤과 사진 피부 회귀 차단 |

### 유형별 추가

| 유형 | 그대로 가져올 원문 묶음 | 근거 |
|---|---|---|
| 인물 | `a different woman, a younger or slimmer face, changed features or hair`; `heavy make-up, lipstick or eye make-up`; `earrings, necklaces, rings or watches` | 정체성·연령·착의 drift |
| 인물 훅 | `a centred, level, symmetrical portrait`; `[슬롯: lens at/above eye level 같은 반대 앵글]` | HERO LOW 희석 뒤 정면 증명사진이 된 사고 |
| 피부 | `a yellow, golden, olive or sallow skin tone, a warm amber colour cast over the frame`; `visible pores or photographic skin texture` | 시트·identity ref 결합 때 피부색과 실사 질감 drift |
| 제품 | `a round cylindrical bottle`; `an elongated slim bottle stretched taller than the reference silhouette`; `a plastic-looking bottle`; `a pump or spray dispenser`; `a missing or opaque pipette` | 병 실루엣·재질·부품 변형 |
| 라벨 | `missing, blurred or unreadable label lines`; `any text anywhere except the five label lines on the bottle` | 작은 라벨 재렌더·오탈자 |
| 손+제품 | `two hands`; `a second hand or arm entering the frame`; `any finger, thumb or hand crossing in front of the glass body or its label` | 대칭 손·라벨 가림 |
| 단면 | `cells drawn as flat discs, rings, doughnuts`; `wet pink flesh, muscle, blood vessels, gore or anything medically graphic` | 구슬 격자의 평면화·의학적 고어화 |
| 매크로 | `a whole face or any facial feature`; `any text, letters, numbers, captions, logos or watermarks` | 비목표 얼굴·글자 유입 |
| 체인·쌍 | `[슬롯: first/end의 반대 상태]`; `[슬롯: 카메라·물체·광원의 허용되지 않은 변화]` | 보간 중 상태 역행·동일 물체 재설계 |

## 6. 개선점 삽입 지점

개선점은 새 최상위 블록으로 만들지 않는다.

| 개선점 | 기존 블록 안의 위치 | 적용 규칙 |
|---|---|---|
| 캐릭터 시트 | WOMAN | 정체성(얼굴·머리·나이)은 CS, 렌더 재질은 스타일 시트에서 분리해 가져온다. CS 그리드·패널 배치·배경·비목표 패널 표정 제외 목록을 유지한다. |
| 디테일 과장 | RENDER MODE | 재질 서술 뒤, 실제 비율 유지 문장 앞. 질감·요철·상태 변화가 한눈에 읽히게 하되 H v1(약함)~H v2(과함) 사이로 둔다. |
| 라벨 5행 | PRODUCT | LABEL 문장에 `Jasmine oil CO2 + 6 Botanical oils`를 `BRIGHTENING FACE OIL` 다음, 용량행 앞에 둔다. 다섯 행 모두 유지한다. |
| 9:16 | 첫 문장 | `Create ONE 9:16 vertical scene frame, not a style board or reference sheet.` 원문을 그대로 쓴다. |
| 배경 3층 | STYLE | STYLE이 블루 시클로라마를 전담하고, 씬은 소품만, AVOID는 인테리어를 금지한다. |

## 7. 미결 결정

### hex 코드 — 결정 대기

- **지난 편대로 사용**: 36개 중 35개가 스타일 시트 실측값인 `#4B8CC6`,
  `#E9D3BF`, `#C9A691` 등을 사용했고 결과 기준선을 만들었다. 시트 자신의
  팔레트를 숫자로 고정하는 이점이 있다.
- **프롬프트에는 미사용**: 이번 편 공통설정은 hex를 검증 전용으로 두고,
  프롬프트에는 색 이름·역할만 쓰도록 정했다. 시트와 어긋난 숫자가 경쟁하는
  위험을 피한다.

사용자 결정 전까지 양쪽을 병기한다. 어느 한쪽도 표준으로 확정하거나 다른
쪽을 삭제하지 않는다.

## 8. 관찰 중 (v1)

이 표준의 첫 실전은 20260813 기미 오일 편의 이미지 재작업이다. 아직 결과
표본이 없으므로 다음을 관찰한다: 캐릭터 시트와 스타일 시트의 역할 분리가
정체성과 렌더 재질을 동시에 지키는지, 디테일 과장 수위가 H v1~v2 사이에
드는지, STYLE+AVOID 배경 3층이 병원 인테리어를 막는지, 5행 라벨이 정면
고정·회전 금지·6초 후 트림에서 유지되는지. 실제 이미지 재생성은 사용자
검수 뒤 별도 작업으로 한다.

## 영상 프롬프트 구조

같은 폴더의 `clip*_vid*.txt` 32개(현재판·v1·single 변형 포함)를 전부 읽어
확인했다. 32/32가 아래 4층 구조이며, `clip8b_vid_single.txt`만 줄바꿈 없이
한 줄에 붙어 있지만 블록 내용은 같다.

| 순서 | 블록 | 실적 | 역할 |
|---:|---|---:|---|
| 1 | 불변 도입부 | 32/32 | 렌더·조명·카메라 원칙, 첨부 프레임 역할, 정체성 잠금 |
| 2 | SHOT | 32/32 | 하나의 연속 동작·카메라 경로·종점 |
| 3 | AUDIO | 32/32 | 효과음만 설계 |
| 4 | AVOID | 32/32 | 컷·장면·정체성·글자·음성 생성 등 실패 방향 차단 |

도입부의 첫 두 문장은 불변 원문이다.

```text
Use the attached image(s) as the strict visual system - a high-end 3D CG render with the finish of a semi-realistic game-engine cutscene, never photographic and never a cartoon. Soft even studio lighting, no harsh shadows, no photographic grain.
```

카메라는 둘 중 하나의 원문을 택한다(연속 이동 28/32, 고정 4/32).

```text
One committed camera move, slow and continuous, never a cut.
The camera does not move in this shot.
```

첨부가 한 장이면 첫 원문(20/32), first/end 쌍이면 두 번째 원문(12/32)을 쓴다.

```text
The attached image is the opening frame of the shot.
The FIRST attached image is the opening frame. The SECOND attached image is the EXACT final frame - the shot must land on it precisely. Generate only the continuous transition between the two.
```

인물 컷은 정체성 잠금 원문(9/32)을 도입부 끝에 붙인다.

```text
The same one woman throughout - keep her face, her age, her chin-length dark bob and her warm-cream knit top identical from first frame to last.
```

제품 컷은 물리적 동일성 잠금(12/32)을 붙인다. 기본 원문은 다음과 같고,
실루엣 취약 컷은 `shape`를 `silhouette, proportions`로 확장했으며 라벨 취약
컷은 `the size and layout ... never re-typeset`을 추가했다.

```text
The bottle is the same physical object throughout - its shape, its white label and every printed line on it stay exactly as in the attached image, never redrawn, never restyled.
```

유형별 차이는 SHOT 안에서만 만든다.

- 한 장 입력: opening 상태에서 `[슬롯: 하나의 연속 동작과 카메라 이동]`을
  수행하고 `[슬롯: extension anchor / edit point / resolve / hero hold]`에
  도착한다.
- first/end 쌍: 두 첨부 사이를 연속 보간하고 최종 프레임에 정확히 착지한다.
- 인물: 같은 얼굴·나이·헤어·착의를 잠그고 표정·손·피부 상태만 SHOT에서
  바꾼다.
- 제품: 같은 병·라벨을 잠그며 회전·측후면·재조판을 AVOID에 넣는다. 제품
  클로즈업이면 영상 프롬프트에도 라벨 다섯 행을 반복한다.
- 단면·상태 변화: 변화 전선이 역행하거나 건너뛰지 않게 하고, 카메라는
  한 경로만 사용한다.

모든 AUDIO는 효과음만 쓰며, 모든 AVOID에 아래 음성 금지 원문이 있었다
(각 32/32).

```text
no music; no soundtrack; no voice-over; no narration; no lyrics
```

완성 골격:

```text
[불변 도입부] [슬롯: 카메라 이동/고정 원문] [슬롯: 한 장/first-end 원문] [슬롯: 인물/제품 정체성 잠금]
SHOT: [슬롯: 시작 상태 → 하나의 연속 동작·카메라 경로 → 종점 상태]
AUDIO: [슬롯: 효과음] - sound design only, no music, no narration.
AVOID: [슬롯: 이 컷의 반대 상태·금지 방향], no camera cuts, no scene change, no identity change, [슬롯: 유형별 금지], no music, no soundtrack, no voice-over, no narration, no lyrics.
```
