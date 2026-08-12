# Paper Diorama Prompt System

A repeatable system for writing AI video clip prompts in the aged-newsprint cutout-collage style. Every prompt is built from four blocks in fixed order: **STYLE BLOCK → SHOT → AUDIO → AVOID**.

---

## 1. Choose a Style Block

Pick whichever serves the shot. The style block is a fixed preamble — use it verbatim once chosen, but the choice is per clip, not per video. A restrained data beat wants Flat Parallax; a big reveal wants Deep Diorama. Choose for the moment.

### A. Flat Parallax (documentary, restrained)

> Use the attached style sheet as the strict visual system — match its aged-newsprint collage surface, desaturated archival palette with one hot accent, condensed headline caps with giant stat numbers, halftone black-and-white cutout people with rough white keylines and offset accent strokes, and its print-grain finish. Do NOT copy the sheet's layout; it defines the language, not the composition. Layers sit at distinct depths like a paper diorama — true parallax, never glossy 3D. Backgrounds are muted archival fields, varying per clip within this palette. ALERT WASH means the whole frame floods toward the hot accent tone. Motion: spring pop-ups with overshoot, staggered entrances, ticking counters, underline swipes; one slow camera move per clip. Audio: sound design only — paper pops, thwips, stamps, ticks, low newsroom hum. No music. No voice-over.

### B. Deep Diorama (cinematic, camera-as-actor)

> Use the attached style sheet for materials only — aged-print collage textures, halftone black-and-white cutout people with rough keylines and offset accent strokes, giant stat numbers, print grain. Do NOT copy the sheet's layout or its flatness: every clip is a deep 3D paper diorama — cutouts are physical layers separated in real space, strong shallow depth of field, foreground elements crossing close to the lens. The camera is an actor: it flies between layers, orbits, dives, whips, racks focus — one committed cinematic move per clip. Backgrounds change per clip, always within the sheet's palette. ALERT WASH means the entire frame floods to the hot accent tone in one beat. Motion: springs with overshoot, staggered entrances, ticking counters. Audio: sound design only — paper pops, whooshes, stamps, ticks. No music. No voice-over.

### C. Locked Stage (no style sheet attached — self-describing)

> Documentary cutout-collage stage: a locked, muted archival map/texture background that never changes. Midground: black-and-white halftone cutouts with a rough white keyline and an offset red marker stroke behind each. Foreground: structures, props, and big stat numbers in full color. Condensed bold headline caps; numbers rendered huge, as characters. Desaturated palette plus one hot red accent, secondary mustard. Spring pop-ups with slight overshoot, staggered entrances, counters ticking up, red underline swipes. Camera: subtle slow drift only, never cuts.

Swap the background clause when the shot needs it, e.g. *"a flat city-skyline silhouette cutout against a muted dusk-toned archival sky, print-grain texture, locked for this shot."*

---

## 2. Write the SHOT

One sentence-block. Always contains these five beats, in roughly this order:

| Beat | Function | Examples from the corpus |
|---|---|---|
| **Background** | Sets the depth field | "a faded world map tilted in perspective, far out of focus" · "stacked newspaper front pages receding in deep perspective" · "a collage field of ledger sheets and ticker strips at depth" |
| **MG** | The subject cutouts | "cutouts of Sam Altman, Elon Musk and Donald Trump work one large hand-pump" · "an iceberg cutout floats with only its tip above a paper waterline" |
| **FG** | The data element | "a counter ticks up to `$1.2T` (giant number)" · "a red stat number reads `POWER DEMAND ↑`" |
| **Camera** | ONE committed move | dive through · orbit quarter turn · whip ×3 · lateral track · climb alongside · push-in · ride the loop like a rail |
| **Settle** | Where the clip ends | "Settle deep, looking up at the tip far above." · "Settle on the sliver in macro." · "Settle mid-orbit." |

### Rules

- **One camera move per clip.** Never two. Never a cut.
- **Always end on "Settle on…"** — this is non-negotiable and tells the model where to park the final frame.
- **Tag every text element** with its type in parens: `(headline)`, `(label)`, `(counter)`, `(giant number)`.
- **Stagger everything.** Nothing enters simultaneously.
- **Logos must be "attached… flat, unmodified"** — never described, never invented.
- **Depth is the story.** State what crosses the lens, what blurs, what racks into focus.

### Camera move library

`push-in` · `slow drift lateral` · `dive through a layer` · `orbit quarter turn` · `whip ×2–3, each landing hard` · `fast lateral track then hard stop with overshoot` · `climb alongside a rising element` · `fly low between columns` · `ride a path like a rail` · `macro slide along an object, rack focus tip→subject`

### Escalation devices

- **ALERT WASH** — frame floods to hot accent. Save it for the single biggest beat.
- **Freeze before contact** — "everything freezes one millimeter before contact."
- **Counter slam** — number flies at the lens and snaps into razor focus while everything blurs.
- **Accelerating loop** — same geometry, each lap faster.

---

## 3. Write the AUDIO

Format: `AUDIO: [2–3 sounds, comma separated] — sound design only, no music, no narration.`

Sound must mirror the camera move:

| Move | Sound |
|---|---|
| Dive | submerge whoosh, deep pressure hum |
| Whips | three whip whooshes, pops landing each hit |
| Track + stall | track rumble, stall click, drain hiss |
| Contact / wash | rising air riser, deep sub thud on contact |
| Loop | accelerating ticks, whoosh per lap |
| Tension hold | rubber creak, room tone falling to near silence |

Bed options: `low newsroom hum` · `low hum` · `room tone`.

---

## 4. Write the AVOID

Use the block matching your style choice. Verbatim.

### For Flat Parallax (A) and Locked Stage (C)

> AVOID: no glossy CG 3D, no lens flares, no camera cuts within the clip, no full-color midground portraits (people stay halftone black-and-white), no warped or gibberish text, no invented logos, no watermarks, no simultaneous entrances, no music, no soundtrack, no voice-over, no narration, no lyrics

### For Deep Diorama (B)

> AVOID: no flat single-plane composition, no static locked-off camera, no glossy plastic CG (depth stays papercraft), no full-color midground portraits (people stay halftone black-and-white), no warped or gibberish text, no invented logos, no watermarks, no music, no soundtrack, no voice-over, no narration, no lyrics

Add `no UI or glass elements` when the shot involves screens, dashboards, or tech.

---

## 5. Fill-in Template

```
[STYLE BLOCK A / B / C — verbatim]
SHOT:
Background: [depth field, often out of focus].
MG: [subject cutouts, staggered entrance].
FG: [counter / stat number / label] reading "[TEXT]" ([type tag]).
[Camera: ONE committed move, describing what crosses the lens and what racks focus].
Settle [final frame].
AUDIO: [sound 1], [sound 2], [sound 3] — sound design only, no music, no narration.
AVOID: [matching AVOID block]
```

---

## 6. Sequencing a Video

- **Choose the style block per clip.** Match it to the beat: Flat Parallax for restrained data moments, Deep Diorama for reveals and escalation, Locked Stage when no sheet is attached. The materials stay constant across blocks, so the world holds even when the depth treatment shifts.
- **Use the shift as a tool.** Dropping from Deep Diorama into Flat Parallax reads as a breath; jumping the other way reads as a lift.
- **Vary the background per clip** — always inside the palette.
- **Vary the camera move per clip** — never two dives in a row.
- **Chain clips** by reusing geometry: build the loop, then ride the loop, then blow past it. Reference it explicitly: *"The triangle loop from the previous clip runs faster each lap."*
- **Reserve ALERT WASH** for one clip per video.
- **End the sequence on a held tension frame**, not a resolve — e.g. the frozen pin, the trembling summit, the wobbling slab.
```

---

## 7. 글자 AVOID 운용 (2026-08-12)

`no warped or gibberish text`는 **생성 오류**를 막는 문구지 글자의 **모션**을
막는 문구가 아니다. 두 가지를 갈라 쓴다.

| 대상 | 처리 | 문구 예 |
|---|---|---|
| 없던 글자 생성 | 금지 | `no text, letters, numbers or captions appearing anywhere` |
| 제품 라벨 | 잠금 (변형 전례 있음) | `no change to the printed label lines` |
| 큰 숫자·소품 글자 | **모션 허용** | `it stays 41% throughout and only moves as a whole solid object, no digits morphing, counting up or re-forming` |

허용할 때도 "**하나의 단단한 덩어리로만 움직인다**"를 함께 건다. 이걸 빼면
모델이 글자를 매 프레임 다시 그리며 값·형태가 흔들린다.

> 근거: 이미지 단계에서 `JUN`·`41%`·라벨 5줄이 전부 정확히 나왔지만
> (2026-08-12 크롭 검증), 영상은 매 프레임을 다시 그리므로 같은 보장이 없다.
> 기미 편 push-in에서 라벨이 `VG SHOT`→`VO SHOT`으로 변형된 것이 그 증거다.
> 그래서 라벨은 잠그되, 강조가 목적인 큰 숫자는 스프링·스탬프 모션을 준다.

### 7.1 제품 라벨은 문구가 아니라 **동작 설계**로 지킨다 (2026-08-12 실측)

`no change to the printed label lines`를 걸어도 라벨은 무너진다. 페이스오일
1차 12컷에서 라벨이 나오는 5컷 **전부** 가장 작은 4행이 열화했다. 문구는
브레이크일 뿐이고, 실제로 결과를 가르는 것은 **라벨 면이 렌즈에 대해
각도를 바꾸느냐**다.

| 컷 | 라벨 각도(입력) | 영상 동작 | 첫 프레임 4행 | 끝 4행 |
|---|---|---|---|---|
| clip17 | 정면 | 전진만 (`Nothing rotates` 명시) | **정확** | 오탈자 |
| clip16 | 정면 | 카메라 push-in | 살짝 어긋남 | 뭉개짐 |
| clip6b | 사선(기운 병) | 낙하 중 회전 | 거의 정확 | 뭉개짐 |
| clip3 | 사선(기운 병) | 손목 회전 | **완전 붕괴** | 완전 붕괴 |

읽는 법: **회전 컷 두 개가 정지 컷 두 개보다 심하게 무너졌다.** 각도가
바뀌는 동안 모델은 라벨을 베끼지 못하고 원근 왜곡된 글자를 새로 그린다.

**단, 입력 이미지의 기울기는 원인이 아니다.** clip3·clip6b가 똑같이 사선
라벨인데 첫 프레임이 갈렸다(붕괴 / 거의 정확). 사선 한 가지로는 설명되지
않으므로 이미지 단계에는 아무 제약도 걸지 않는다 — **병은 기울여 찍어도
된다.** (2026-08-12: 이 반례를 표에 적어놓고도 "사선이면 무너진다"로
일반화해 SPEC에 정면 강제를 넣었다가 사용자 지적으로 되돌렸다.)

**규칙 — 영상 단계에만 건다**

- **라벨이 화면에서 읽히는 크기면 회전을 쓰지 않는다.** 병 회전(`the wrist
  rotates`, `turns square to the lens`, `its label swings into full view`),
  카메라 궤도(`quarter orbit`)가 모두 여기 해당한다
- 대신 쓸 수 있는 것: 각도를 유지한 채 **전진·후퇴**, 상하 이동, 스펙큘러
  밴드가 유리 위를 지나감, 배경 소품의 등장. clip17·clip16이 이 계열이고
  큰 3행과 용량행은 5컷 모두 정확했다
- 라벨을 **각도 변화와 함께** 보여줘야 하는 연출이라면, 회전은 라벨이
  안 읽히는 크기(원경·부분 가림)에서만 하고, 크게 보여주는 구간은
  각도를 고정한 정지로 잡는다 (기울어진 각도 그대로 고정해도 된다)
- 그래도 **시간이 지나면 열화한다** (clip17: 첫 프레임 정확 → 끝 오탈자).
  라벨이 크게 읽히는 컷은 짧게 잡고, 회수 후 반드시 마지막 프레임을
  크롭 확대해 읽는다

> 큰 글자는 안 무너진다. 5컷 모두 `HEGI` / `JASMINE DROPS` /
> `BRIGHTENING FACE OIL` / `30 ml - 1.01 fl.oz`는 정확했고, 가장 작은
> `Jasmine oil CO₂ + 6 Botanical oils`만 깨졌다 — **글자 크기에 임계가 있다.**
> 라벨을 설계할 때 화면에서 읽혀야 하는 줄은 크게 잡고, 작은 줄은
> 읽히지 않아도 되는 정보만 담는다.
