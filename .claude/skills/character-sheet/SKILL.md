---
name: character-sheet
description: 편별 씬 설계에서 인물의 얼굴·머리·체형·의상·표정을 추출해 identity control asset인 캐릭터 시트를 만든다. 사용자가 "캐릭터 시트 만들어줘", "인물 정체성 고정해줘", "이 편 주인공 시트 만들자"라고 하거나, vox-video 씬에 인물 얼굴이 나오는 컷이 있으면 5단계 이미지 생성 전에 사용한다.
---

# 편별 인물 캐릭터 시트

씬 설계에서 인물의 정체성·편 의상·감정 비트를 뽑아 **identity control
asset** 한 장으로 고정한다. 아름다운 인물 초상화가 아니라 컷마다 같은 사람을
재현하기 위한 제작 자산이며, 프로젝트 공용이 아닌 **그 편 전용**이다.

## 절대 원칙

1. **시트는 반드시 인물 이미지에서 출발한다 — 예외 없다** (2026-08-14
   사용자 확정). 순서는 항상 **①스타일 시트로 인물이 들어간 이미지 1장을
   먼저 만든다 → ②그 이미지를 참조 얼굴로 캐릭터 시트를 만든다.**
   텍스트 서술만으로 시트를 생성하는 경로는 **없다.**
2. **캐릭터 시트는 편별 자산이다.** 프로젝트 공용 코어 시트를 만들지 않는다.
   같은 인물을 다음 편에 다시 쓰려면 지난 편 시트를 새 시트의 ref로 첨부한다.
3. **게이트 ③을 통과한 시트는 그 편에서 불변 정본이다.** 편 중간에
   수정하거나 재생성하지 않는다. 수정은 게이트 단계에서 끝낸다.
4. **피부는 중립 상태로 만든다.** 기미·건조 같은 씬 상태는 시트에 넣지 않고
   각 컷의 텍스트가 결정하게 한다.
5. **활성 스타일 시트와 같은 렌더 세계로 만든다.** 실사 렌더를 하드코딩하지
   않고, 활성 스타일의 렌더 톤을 따른다.

> **원칙 1이 왜 절대인가 (기미 오일 편 실측, 2026-08-14).** 텍스트만으로
> 시트를 만들었더니 실사에 가까운 인물이 나왔고, 그 톤이 인물 컷 3장에
> 그대로 전달돼 전부 폐기했다. `clean character sheet`·`studio backdrop`
> 같은 시트 형식 지시가 실사 캐릭터 시트 표본 쪽으로 강하게 끌어서,
> 스타일 시트를 ref로 붙여도 이기지 못했다. 반면 **인물 컷 프롬프트에는
> STYLE·RENDER MODE 블록이 통째로 들어가** 렌더 톤을 훨씬 강하게 잡는다.
> 그래서 톤이 확정된 인물 이미지를 먼저 얻고, 시트는 그것을 복제한다.

## 폴더 구조

```
output/<run>/ch<N>/character/
├── ANCHOR_후보N.png  앵커 생성본 (승인 전 — 정본 자리에 두지 않는다)
├── ANCHOR.png   앵커 인물 이미지 — 시트의 참조 얼굴 (게이트 ② 통과본)
├── SHEET_후보N.png   시트 생성본 (승인 전)
├── SHEET.png    캐릭터 시트 불변 정본 (게이트 ③ 통과본)
└── PLAN.md      계획·최종 프롬프트·게이트 기록
```

`output/` 아래의 편별 제작 자산이므로 git 추적 대상이 아니다.

## 0. 사전 점검

- 씬 설계와 `scenes/공통설정.md`가 완료됐는가. 감정 비트와 편 의상이
  확정되기 전에는 시트를 만들지 않는다
- `assets/style_reference.png`가 존재하는가. `assets/ACTIVE_STYLE`과
  `styles/<활성 스타일>/NOTES.md`에서 스타일명·렌더 톤을 확인한다
- 인물 얼굴이 나오는 컷이 있는가. 없으면 캐릭터 시트가 필요 없는 편이므로
  여기서 종료한다
- 생성 시점은 **씬 설계 완료 후부터 5단계 이미지 생산 전까지**다

## 1. 씬 파일에서 인물 정보 추출

`scenes/공통설정.md`와 모든 `sceneNN.md`를 읽고 다음을 뽑는다:

- **인물 정의** — 얼굴 생김새·머리·나이·체형·전체 인상
- **편 의상** — 이야기 시점에 실제로 입는 기본 의상과 핵심 액세서리
- **감정 비트 3~4개** — 씬별 감정 서술을 **원문 그대로 기록**하고, 시트
  프롬프트에는 그 원문을 번역해 쓴다. 중립 표정을 포함한다
- **방향** — 이야기에 필요한 카메라 접근 측. 정면 / 해당 방향 3/4 / 같은
  방향 프로필을 한 세트로 쓴다 (예: 기미 편의 오른쪽)
- **스토리 소품** — 손에 쥐거나 손의 동작이 이야기 정보라면 손 클로즈업
  패널을 추가한다

감정은 빠른 컷에서도 즉시 읽힐 만큼 과장하되 얼굴을 만화적으로 일그러뜨리지
않는다.

## 2. CHARACTER SHEET PLAN 작성 — 사용자 게이트 ①

`output/<run>/ch<N>/character/PLAN.md`에 아래 양식을 채운다. 감정마다 씬
번호를 붙이고, `Image prompt:` 아래에는 3단계에서 조립한 최종 프롬프트를
기록한다.

```
CHARACTER SHEET PLAN

Identity lock:
Story role:
Main outfit:
Required expressions:   ← 씬 번호와 함께 (예: disappointment — scene 2)
Required details:
Direction:              ← 추가 (이야기에 필요한 측. 예: right side)
Render tone:            ← 추가 (활성 스타일명 + soft-lit 3D 등 시트 문법)

Image prompt:
```

PLAN을 사용자에게 보여주고 **확인을 기다린다.** 확인 전에는 시트를 생성하지
않는다.

## 3. 앵커 인물 이미지 만들기 — 사용자 게이트 ② (시트보다 먼저)

**시트를 만들기 전에 인물이 들어간 이미지 1장을 반드시 먼저 만든다**
(절대 원칙 1). 이 이미지가 시트의 참조 얼굴이 되므로 **앵커 이미지**라
부른다.

1. **씬에 실제로 있는 인물 컷 하나를 고른다.** 새 장면을 지어내지 않는다 —
   그 편에서 어차피 만들 컷 중 얼굴이 가장 잘 보이는 것을 쓴다 (기미 편이면
   씬 2의 D, 실망 미디엄). 이러면 앵커가 버려지는 산출물이 아니라 편의 자산
   1장이 된다
2. **프롬프트는 이 편의 이미지 표준 그대로** 쓴다 —
   `../vox-video/references/prompt-standard.md`의 인물 컷 레시피
   (첫 문장 → STYLE → RENDER MODE 인물형 → WOMAN → CAMERA → STILL → AVOID).
   시트가 아니라 **한 장면**이므로 `clean character sheet` 같은 시트 형식
   문구를 절대 넣지 않는다
3. 첨부는 **스타일 시트 하나뿐**이다 (`--style-ref`). 아직 캐릭터 시트가
   없으므로 `--ref-character`는 쓸 수 없다
4. 생성 후 **사용자 확인** — 인물(얼굴·머리·나이·의상)과 **렌더 톤**이
   맞는가. 여기서 톤이 실사로 기울면 시트를 만들지 말고 이 단계에서 고친다.
   시트는 앵커를 복제하므로 **앵커의 결함은 편 전체로 번진다**
5. 생성본은 `character/ANCHOR_후보<N>.png`에 두고, **통과한 것만**
   `character/ANCHOR.png`로 복사한다 — 정본 자리에는 승인본만 있어야 하고,
   후보 파일명이 남으면 재생성해도 앞 버전을 잃지 않는다

## 4. 시트 프롬프트 조립

**참조 얼굴은 항상 있다** — 3단계의 `ANCHOR.png`다 (지난 편 인물을 이어
쓰는 경우에는 지난 편 시트). 아래 템플릿의 슬롯만 PLAN 값으로 바꾸고,
**첫 두 문장은 언제나 포함한다.**

```text
Use the attached face image as the face, hairstyle, and body proportion
reference. Preserve the same person throughout the sheet.

Create a clean character sheet of the same [character role],
rendered in the same visual style as the attached style reference sheet
([렌더 톤 — 예: soft-lit dimensional 3D, never photographic]).

Identity:
[face identity], [hair], [body proportion], [overall impression],
clean neutral skin without scene-specific conditions.

Outfit:
[main outfit], [key accessories], [story-critical prop if needed].

Sheet layout ([N] panels):
front face,
[direction] three-quarter face,
[direction] profile,
full body in the main outfit,
neutral expression,
[expression 1 — 씬 파일 원문 번역],
[expression 2],
[expression 3],
[optional: close-up of hands showing [detail]].

Background:
plain light neutral studio backdrop, soft even lighting,
clean reference sheet layout.

Do not change the face between panels.
Do not change the hairstyle or body type between panels.
Do not add extra people.
Do not add text, panel labels, logos, watermarks, or UI.
```

패널은 한 장에 **7~9개**만 둔다. 정면 / 이야기 방향의 3/4 / 같은 방향의
프로필 / 편 의상을 입은 전신 / 중립 표정 / 감정 3~4개가 기본이고, 스토리
소품이 있으면 손 클로즈업을 포함하되 총 패널 수 안에서 조정한다.

**Wardrobe Rules**

- 의상은 이야기 시점과 상황에 맞춘다
- 과잉 디자인을 피한다 — 단순한 의상이 영상 모델에서 더 잘 보존된다
- 스토리 소품은 의상·인물 정의에 직접 포함한다
- 소품이 중요하면 그 소품을 든 손의 클로즈업 패널을 요청한다

## 5. 캐릭터 시트 생성

기존 이미지 생성 경로와 같은 Codex 내장 이미지 생성(ChatGPT 구독 OAuth)을
사용한다. 첨부는 **항상 두 장**이다:

1. `assets/style_reference.png` — `--style-ref`
2. **앵커 인물 이미지** (`character/ANCHOR.png`) — `--ref-character`.
   같은 인물을 이어 쓰는 편이면 지난 편 시트가 이 자리에 온다

**앵커 없이 생성하지 않는다** (절대 원칙 1). 앵커가 없으면 3단계로 돌아간다.

한 장에 7~9개 패널이 모두 보이는 캐릭터 시트를 생성한다. 생성본과 실제 사용한
최종 프롬프트를 게이트 ③ 검수 대상으로 보존한다.

**저장은 `character/SHEET_후보<N>.png`로 한다** — `--out`에 `SHEET.png`를
직접 쓰지 않는다. 게이트 ③ 통과 후에만 통과본을 `SHEET.png`로 복사한다
(7단계). 정본 자리에 있는 파일은 반드시 승인된 것이어야 한다.

## 6. 자기 검증 (필수)

생성된 시트를 Read로 열고 다음을 전부 확인한다:

- [ ] 패널 수·방향·전신·감정·손 패널 구성이 PLAN과 일치한다
- [ ] 모든 패널이 같은 인물이다 — 얼굴·머리·체형이 바뀌지 않는다
- [ ] **앵커 이미지와 같은 사람인가** — 얼굴이 새로 지어지지 않았는지
- [ ] **렌더 톤이 앵커와 같은가** — 앵커는 스타일 세계인데 시트만 실사로
      기울지 않았는지 (첫 실패의 지점이다)
- [ ] 글자·패널 라벨·로고·워터마크·UI가 없다
- [ ] 기미·건조 같은 씬별 상태가 피부에 박혀 있지 않다

## 7. 사용자 게이트 ③ — 시트 확정

시트와 자기 검증 결과를 사용자에게 보여주고 **확인을 기다린다.** 통과하면
후보본을 `output/<run>/ch<N>/character/SHEET.png`로 **복사하고** `PLAN.md`에 게이트 통과
일자·최종 프롬프트를 기록한 뒤, 이 시트를 **그 편의 불변 정본**으로 선언한다.

실패하면 이 게이트 단계에서 PLAN 또는 프롬프트를 고쳐 재생성한다. 재생성은
최대 2회다. 두 번 실패하면 무엇이 맞지 않는지 사용자에게 보고하고 멈춘다.

## 게이트 요약

| 게이트 | 무엇을 확정하나 | 실패하면 |
|---|---|---|
| ① PLAN | 인물 정의·의상·감정 패널 구성 | 씬 파일로 돌아가 고친다 |
| ② 앵커 이미지 | **인물 외모와 렌더 톤** | 여기서 고친다 — 시트로 넘어가지 않는다 |
| ③ 시트 | 패널 구성과 앵커 복제 정확도 | PLAN·프롬프트 수정 후 최대 2회 재생성 |

## 다운스트림 사용 규칙

인물 얼굴이 나오는 클립 이미지에는 다음 ref를 함께 첨부한다:

1. 활성 스타일 시트 — `--style-ref`
2. 캐릭터 시트 — **`--ref-character`** (2026-08-15 신설)
3. 체인 프레임 — 해당 컷에 있을 때만, **`--ref-chain`**

**`--ref`로 캐릭터 시트를 넘기지 않는다.** `--ref`는 제품 등 실물용이고,
"이 이미지는 실물 사물이니 재질을 그대로 유지하라"는 문구가 붙는다. 시트에
이 문구가 걸리면 **시트의 렌더 톤이 컷으로 강제 승계된다** — 2026-08-14
A·D·F1이 실사로 나온 원인 중 하나다. `--ref-character`는 정체성만 가져오고
렌더·그리드·배경·비목표 패널 표정을 제외하도록 지시한다.

프롬프트에는 캐릭터 시트에서 **가져올 것과 제외할 것을 둘 다** 쓴다. 제외
목록에는 시트의 그리드 레이아웃·패널 배치·배경·목표가 아닌 패널의 표정을
반드시 넣는다.

표정은 해당 패널을 직접 가리킨다. 예:

> the worried expression as shown in the character sheet

ref가 표정을 끌고 오는 성질을 역이용하는 것이다. 세부 운용은
`../vox-video/references/pipeline-rules.md` 7절을 따른다.

AVOID에는 캐릭터 시트의 격자 구성이나 복수 패널이 단일 장면 컷에 나타나지
않도록 명시한다.

## 관찰 중 (v1)

현재 실전 표본은 0이다. 아래 항목은 규칙으로 승격하지 않고 관찰한다:

- 3D 렌더 톤에서 캐릭터 시트의 패널 간 정체성 품질
- 스타일 시트 + 캐릭터 시트 + 체인 프레임을 함께 붙였을 때 각 ref의 지배력
- 단일 장면 컷에 캐릭터 시트의 그리드·패널 배치가 유출되는지

표본이 쌓인 뒤에만 관찰 결과를 규칙으로 승격한다.

## 비용

- 캐릭터 시트 1장: ChatGPT 구독 이미지 생성 1회
- 재생성은 최대 2회 — 게이트에서 고쳐 편 중간의 정본 변경을 막는다
