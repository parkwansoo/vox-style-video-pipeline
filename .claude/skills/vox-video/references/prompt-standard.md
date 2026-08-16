# 이미지·영상 프롬프트 표준 — mg-bodylab soft 3D

작성: 2026-08-14. 상태: v1, 관찰 중.

## 1. 이 문서가 있는 이유

검증된 페이스오일 편의 프롬프트 표준이 산출물에만 있고 스킬 문서에는 없어,
다음 편에서 STYLE·RENDER MODE 같은 핵심 블록이 통째로 유실됐다. 이 문서는
페이스오일 편 이미지 프롬프트 **40개 전부**와 영상 프롬프트 32개를 분석해 그
기준선을 보존한다. 새 형식을 창작하지 않고, 검증된 원문과 블록 순서를 먼저
복원한 뒤 개선점은 기존 블록 안의 지정 위치에만 얹는다.

**프롬프트를 다 쓴 다음에는 9절 셀프체크를 돌린다** — 버린 표본의 결함은
대부분 생성 전에 읽어서 잡을 수 있는 것이었다.

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

**확장형을 기본으로 쓰지 않는다 — 조건이 붙는다 (2026-08-16 실측 개정).**
확장형의 디테일 목록은 **렌더를 사진 쪽으로 끌어당긴다.** 바로 뒤에
`never by photographic wrinkle and pore detail`가 붙어 있어도 목록이 이긴다.

기미 편 앵커 실측(다른 조건 전부 동일, 연령 서술만 교체):

| | 연령 서술 | 나이 | 렌더 톤 |
|---|---|---|---|
| 후보6 | 확장형(목록 포함) | 50대 ✅ | **사진 질감·주름·모공** |
| 후보7 | 핵심형(숫자만) | 50대 ✅ | **매끈한 CG, 단순화된 면** |

**나이는 숫자 지정만으로 지켜진다.** 목록은 나이를 위해 필요한 것이 아니라
렌더 톤을 바꾸는 스위치다. 그러므로:

- **정체성 앵커·캐릭터 시트** → 핵심형. 톤이 편 전체로 복제되므로
- **건조·주름이 화면의 주제인 컷**(우리 편 씬 5 같은) → 확장형을 고려하되,
  그 컷만 사진 쪽으로 기우는 것을 감수할지 판단한다
- **캐릭터 시트를 만들 때는 사용자에게 방향을 묻는다** (character-sheet
  스킬 5단계 게이트. 사용자가 한쪽으로 확정할 때까지 매번 묻는다)

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

**글자 금지는 조건부다 (2026-08-15 정정).** 무조건형을 쓰면 화면에 있어야
할 라벨·숫자까지 금지된다. 지난 편은 컷 유형에 따라 아래 셋 중 하나를 썼고,
전부 원문이다. 이 자리에는 반드시 하나를 골라 넣는다.

```text
any text, letters, numbers, captions, logos or watermarks
any text anywhere except the five label lines on the bottle
any text, number, percentage, price, arrow, button or badge anywhere except the five label lines on the bottle
```

첫째는 글자가 전혀 없어야 하는 컷(31개 파일), 둘째·셋째는 제품 라벨이 보이는
컷(8+2개 파일)이다. 화면에 큰 숫자·배지가 들어가는 컷은 그 대상만 예외로
남기고 나머지를 금지한 원문이 따로 있다(`clip16`: `any text, word, letter,
currency symbol or extra digit beside the number - the giant number reads
exactly 41% and nothing more`). 우리 편의 «3만원대»·«14일 전액환불» 컷은
이 형태를 따른다.

`the man shown in the style sheet or any male face`도 컷에 남성이 등장하면
빼거나 좁힌다. 우리 편 씬 1a의 의사는 얼굴이 프레임 밖이라 그대로 둔다.

전체 조립 형식은 다음과 같다.

```text
AVOID: [슬롯: 이 컷의 반대 상태·반대 방향]; [슬롯: 유형별 추가 원문]; [슬롯: 위 글자 금지 3형 중 하나]; [슬롯: the man shown in the style sheet or any male face — 남성 등장 컷이면 제외]; a room corner, floor, wall, furniture or any interior; horizon lines, harsh shadows, lens flares, photographic film grain; [슬롯: photographic realism / photographic realism or photo-real skin texture]; [슬롯: 피사체에 sky-blue tint 금지]; flat 2D graphics, collage, paper texture or halftone; split screens or multi-panel layouts.
```

## 4. 컷 유형별 레시피

### 첨부 순번 규칙 (2026-08-15 추가 — 원문의 SECOND·THIRD를 그대로 쓰지 않는다)

아래 원문들에는 `The SECOND attached image`, `The THIRD attached image`처럼
**순번이 박혀 있다.** 지난 편은 첨부 조합이 고정(시트 + 인물 ref + first)이라
맞았지만, 우리는 컷마다 조합이 다르다 — 캐릭터 시트·직전 프레임·구도 앵커·
제품이 섞인다.

`gen_image.py`가 첨부 설명에 **실제 순번을 박아준다**(`Attachment 2 is...`).
프롬프트 본문의 순번도 그 실제 위치로 바꿔 쓴다. 첨부 순서는 스크립트가
고정한다: **시트(1) → 이전 렌더본 → 캐릭터 시트 → 세계 앵커 → 직전 프레임
→ 구도 앵커 → 제품(항상 마지막)**. 정체성 계열(캐릭터·세계) → 연속성(체인)
→ 구도(앵커) → 제품 순이다.

| 옵션 | 무엇을 승계하나 | 쓰는 곳 |
|---|---|---|
| `--style-ref` | 재질·시각 언어 (배경·팔레트·조명) | 항상 |
| `--ref-character` | 정체성만 (얼굴·머리·체형·나이) | 인물 컷 |
| `--ref-world` | **세계만** (재질·구조·물체 형태) — 구도·조명·색·상태는 명시적 제외 | 같은 세계의 떨어진 컷 (E→J) |
| `--ref-chain` | 같은 장소·재질 (**조명·상태는 승계하지 않는다** — 컷 프롬프트가 정한다) | 체인 end, 쌍의 end |
| `--ref-anchor` | **구도만** (각도·크롭·거리) — 조명·상태·표정은 명시적 제외 | 대구 컷 |
| `--ref` | 실물 정체성 (형태·비율·색·재질·라벨) | 제품 |

**`--ref-chain`이 조명·상태를 승계하지 않는 이유** (2026-08-15 개정).
이 래퍼는 **모든 체인 컷에 자동으로 붙는데** 조명·상태는 컷마다 다르다.
우리 편 6쌍 전수 대조:

| 쌍 | location | materials | lighting | state |
|---|---|---|---|---|
| A→B · x1a→C · x5→G | 같음 | 같음 | 같음 | 진행 |
| F1→F2 | 같음 | 같음 | 같음 | **다름**(기미 피어남) |
| I→N | 같음 | 같음 | **다름** | **다름**(스포이드 뽑힘) |
| L→M | 같음 | 같음 | **다름** | 같음 |
| **합계** | **6/6** | **6/6** | 4/6 | **1/6만 같음** |

체인은 "시간이 흐른 다음 프레임"이라 상태가 진행하는 것이 정상이고,
`same state`는 체인의 본질과 모순이었다. 반면 location·materials는 한 번도
어긋나지 않아 **그대로 남긴다** (갈리지 않은 것까지 지우면 오일 수위 때
CONTENTS 블록을 통째로 날린 것과 같은 실수다).

지난 편은 조명 승계를 **컷마다 손으로 판단했다** — clip17·clip9b의
`SCENE MATCH`가 "무엇이 같고 무엇이 바뀌었는지"를 컷별로 적었다. 래퍼는
그럴 수 없으므로 **항상 참인 것만** 말하고, 컷마다 다른 것은 본문
`SCENE MATCH`/`CONTINUITY` 블록이 말한다.

**지우기만 하면 부족하다.** ref는 침묵한 속성을 끌고 온다 (2026-08-12 실측:
바꿔야 할 표정을 ref가 끌고 와서 안 바뀌었다 — pipeline-rules 7절).
그래서 조명·상태를 **명시적 제외 목록**에 넣었다:
`this frame's camera, framing, subject placement, lighting and the state of
everything in it are set by the image prompt below`.

`--ref-chain`과 `--ref-anchor`는 여전히 섞지 않는다. **이제는 구도에서
싸운다** — chain은 "구도는 이 컷 프롬프트가 정한다"고 하고 anchor는
"구도는 나에게서 가져와라"고 한다. (2026-08-15 이전에는 조명에서도 싸웠다:
chain의 `same lighting`이 대구 컷 G→K의 "조명·상태는 반대"와 충돌했다.
그 문구는 사라졌지만 구도 충돌이 남아 금지는 유효하다.)

### 인물

- 조합: 첫 문장 → STYLE → RENDER MODE(인물형) → WOMAN → CAMERA(필요 시)
  → SCENE MATCH/CONTINUITY(체인·쌍일 때) → STILL → AVOID.
- 지난 편 WOMAN 기준 원문:

```text
WOMAN: [슬롯: 캐릭터 첨부 지칭] is the identity reference. The reflected face in this frame must be that very woman - the same Korean woman in her early fifties, the same facial structure, the same eyes, nose and mouth, the same shoulder-length dark-brown wavy hair, the same plain warm-cream crew-neck knit top, the same age. Take ONLY her facial identity, hair and age from the reference - NEVER its framing, camera distance, pose, EXPRESSION, gaze direction or head angle; this frame's expression is defined below and is different from the reference's. Match the reference's colour world: the same skin warmth, hair colour and flat sky-blue background - do not deepen or saturate the palette.
```

  `[슬롯: 캐릭터 첨부 지칭]`, `[슬롯: reflected face / this frame]`,
  `[슬롯: 인물의 확정 정체성·헤어·착의·나이]`, `[슬롯: 해당 표정]`만 바꾼다.
  **첨부 지칭**: 래퍼가 `Attachment N is a character sheet…`로 이미 선언하므로
  본문은 `That character reference`로 받는다. 지난 편 원문은
  `The SECOND attached image`였고, 당시엔 첨부 조합이 고정(시트+인물 ref+first)
  이라 맞았다 — 우리는 컷마다 조합이 달라 순번을 박으면 어긋난다. 캐릭터 시트가 있으면 얼굴·머리·나이는
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

**`CLOSE`는 빼지 않는다 — 분리 불가 부품이다 (2026-08-16 실측).**
광각 로우앵글의 왜곡은 **거리에 의존한다.** 렌즈가 멀면 `LOW`도
`tilted up`도 문장에 남아 있을 뿐 화면에 나타날 수가 없다. 기미 편 D
실측(다른 조건 전부 동일, 거리 서술만 교체):

| | 거리 서술 | 결과 |
|---|---|---|
| D v1 | `standing back far enough that ...` | **수평 정면·전신 — 로우앵글 소멸** |
| D v2·v3 | `held CLOSE and LOW` (원문 유지) | 로우앵글·대각 어깨·off-balance 전부 나옴 |

**미디엄·와이드가 필요해도 거리를 늘려 만들지 않는다.** `CLOSE`를 유지한
채 아래 손잡이로 조절한다.

**덧붙인 서술은 원문의 다른 부품을 움직인다 — 프레이밍 손잡이로 쓴다.**
D v3은 v2에 아래 한 줄을 더한 것뿐인데 카메라가 뒤로 물러나 미디엄이 됐다
(v2는 미디엄 클로즈). 그 서술을 만족시키려면 거리가 필요하기 때문이다.

```text
her raised elbow rises high against the sky-blue near the top of the picture
```

넓혀야 하는 컷에는 넣고, 좁혀야 하는 컷에는 넣지 않는다. `CLOSE` 삭제와는
성질이 다르다 — 그건 로우앵글을 **통째로** 잃고, 이쪽은 **거리만** 움직인다.
검증된 원문에 무엇을 더할 때는 그것이 거리·각도를 어느 쪽으로 미는지 먼저
예상한다.

**크롭은 씬 파일 원문을 그대로 옮긴다.** 기미 편 D에서 두 방향으로 어긋났다.

| 방향 | 실제 | 결과 |
|---|---|---|
| **뒤집기** | "무릎 아래는 잘림" → `the crop falls below her knees` | 정강이까지 나옴 — 모델은 문장대로 그렸다 |
| **좁히기** | 씬 파일은 무릎인데 AVOID에 `the picture ends at her waist`를 박음 | 씬 파일이 아니라 자기 기준으로 정상 결과를 감점 |

크롭은 "어디서 자르나"가 아니라 **"무엇이 프레임 안에 없나"**로 쓰고,
씬 파일보다 좁게도 넓게도 쓰지 않는다.

```text
the picture ends at her waist - nothing below it is in the frame
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
CONTINUITY: [슬롯: 체인 첨부 지칭] is the first frame of this exact shot. The lamp here is the SAME physical object shown there - same round dark metal head, same thin pole, same base, same position and same size in frame - and she stands at the same distance from the camera in the same knit. Reproduce that lamp exactly; only her skin and her expression differ from the first frame.
```

  `[슬롯: 체인 첨부 지칭]`, `[슬롯: 동일 물체의 실측 특징]`, `[슬롯: 허용 변화]`만
  바꾼다. **첨부 지칭**: 래퍼가 `Attachment N is the frame that comes
  immediately before…`로 선언하므로 본문은 `That previous frame`으로 받는다.
  지난 편 원문은 `The THIRD attached image`.
  쌍의 실루엣·거리·광원은 생성 후 나란히 비교한다.

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

## 7. 확정된 결정

### hex 코드 — 사용한다 (2026-08-15 사용자 확정)

지난 편 프롬프트 40개 중 **39개가 hex를 썼고**, 실제로 쓰인 값은 딱 셋이다:

| 값 | 사용 파일 수 | 스타일 DNA의 이름 |
|---|---:|---|
| `#4B8CC6` | 39 | Cyclorama Blue |
| `#E9D3BF` | 18 | Skin Light |
| `#C9A691` | 18 | Skin Mid |

셋 다 `styles/<스타일>/style_dna.json`의 팔레트 값이고, **DNA에 없는 색을
지어 쓴 사례는 0건**이다. 즉 "DNA 팔레트 값만 쓴다"는 새 규칙이 아니라 지난
편이 이미 하고 있던 것을 적어둔 것이다.

**왜 오일 수위와 다른가.** 오일 수위(`filling the lower two thirds`)는
레퍼런스를 보고 모델이 정할 양을 텍스트가 따로 지시한 **해석**이라 사진과
어긋나 컷마다 갈렸다. hex는 시트에서 뽑은 **바로 그 값**이라 경쟁할 여지가
없다. 오히려 "파란 배경"이라고 말로 쓰면 매번 다른 파랑이 나오지만, 값을
적으면 하나로 고정된다 — "시트가 결정한다"를 어기는 게 아니라 강화한다.

## 8. 관찰 중 (v1)

이 표준의 첫 실전은 20260813 기미 오일 편의 이미지 재작업이다. 아직 결과
표본이 없으므로 다음을 관찰한다: 캐릭터 시트와 스타일 시트의 역할 분리가
정체성과 렌더 재질을 동시에 지키는지, 디테일 과장 수위가 H v1~v2 사이에
드는지, STYLE+AVOID 배경 3층이 병원 인테리어를 막는지, 5행 라벨이 정면
고정·회전 금지·6초 후 트림에서 유지되는지. 실제 이미지 재생성은 사용자
검수 뒤 별도 작업으로 한다.

## 9. 생성 전 셀프체크 (프롬프트를 쓴 다음, 실행하기 전)

한 번에 통과하는 것을 기대하지 않는다 — 다만 **생성 전에 잡을 수 있는 것을
생성 후에 잡지 않는다.** 아래 다섯은 전부 기미 편에서 실제로 한 장을 버린
항목이고, 어느 것도 1분 이상 걸리지 않는다.

1. **크롭·프레이밍이 씬 파일과 같은 방향이고 같은 범위인가.** 영문을
   한국어로 되짚어 씬 파일 문장과 나란히 놓는다
   (D v1: "무릎 아래는 잘림"이 `crop falls below her knees`로 뒤집혔다)
2. **검증된 원문에서 뺀 단어가 있나.** 뺐다면 그게 왜 거기 있었는지 확인한다
   (D v1: `CLOSE`를 빼자 로우앵글이 통째로 사라졌다)
3. **검증된 원문에 더한 문장이 있나.** 더했다면 그것이 거리·각도를 어느
   쪽으로 미는지 예상하고 쓴다 (D v3: 팔꿈치 서술이 카메라를 물렸다)
4. **프롬프트가 침묵한 칸이 있나.** 하의·소품·배경을 안 쓰면 시트가 그 칸을
   메운다 (D v1: 크롭이 정강이까지 내려가자 시트 전신 패널의 크림 바지가
   따라왔다). 화면에 나오면 안 되는 것은 크롭이나 AVOID로 막는다
5. **AVOID에 이 컷의 반대 상태가 있나** (3절 조립 형식의 첫 슬롯)

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
