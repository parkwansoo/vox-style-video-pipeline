# 이미지 프롬프트 선택 블록

기본 조립 절차(`references/image-prompts.md`)는 그대로 두고, **필요할 때만 골라
붙이는** 블록 모음이다. 여기 있는 문구는 스타일 시트를 이기기 위한 교정이므로
**항상 켜지 않는다.**

> 시트를 새로 잘 만들면 이 교정들은 필요 없어진다. 실제로 mg-bodylab 시트는
> 피부 단면을 *wet pinks*로 규정하고 있어 진피가 생살처럼 렌더된다(2026-08-05
> 실측). 아래 블록들은 그 시트를 쓰는 동안의 대응책이지 표준이 아니다.
> **기본 경로·`gen_image.py`·SKILL.md의 조립 순서를 바꾸지 말 것.**

사용법: 골라 쓴 블록을 프롬프트에 `STYLE:` 다음, `STILL:` 앞에 넣는다. AVOID
추가분은 기존 AVOID 줄 끝에 이어 붙인다.

---

## A. 세포를 구슬 격자로 (CELLS)

피부 단면·매크로에서 세포층이 화면을 차지할 때. 모델의 기본 습관은 둥근
사각형·타원 젤리 덩어리라, 그냥 두면 반드시 그쪽으로 간다.

```
CELLS: Rebuild the cell layer in one specific way. Every cell is a PERFECT SPHERE
of even size, made of clear glass-like translucent gel, and the spheres are packed
edge to edge in a tight brick-like lattice several rows deep, offset row to row.
Each sphere carries one small crisp white specular highlight near its upper left,
and light passes through the whole stack so the spheres glow from within. On a cut
face the front row of spheres bulges FORWARD out of the cut, whole and rounded,
like marbles set into the surface - never sliced flat, never a ring or doughnut
with a dip in the middle. Depth reads through colour: the spheres nearest the
surface are the most saturated and they fade to pale honey and cream the deeper
they sit. <색소 상태 — C의 눈금에서 가져온다>
```

AVOID 추가분:

```
cells drawn as flat discs, rings, doughnuts, tyres or anything with a dip or hole
at its centre; cells drawn as rounded rectangles, lozenges, ovals, soft blobs,
sacs, bubbles of uneven size or any irregular organic shape - they are perfect
spheres of even size; a loose scatter of spheres with gaps between them - the
lattice is packed edge to edge; matte or chalky spheres with no highlight;
```

**함정** — 단면 컷에서 구가 납작한 원반·도넛으로 나온다(2026-08-06 실측).
위 "bulges FORWARD" 문장과 AVOID 첫 항목이 그 대응이며, 둘 다 있어야 잡힌다.

---

## B. 표피·각질층 유지 (EPIDERMIS)

세포층만 지시하면 그 위를 덮는 각질·표피층이 통째로 사라진다(clip2·3·9 실측).
세포층이 나오는 컷에는 이 블록을 **같이** 넣는다.

```
EPIDERMIS: The cell lattice is never bare. A distinct epidermal cap sits on top of
it and reads as its own layer: a band of flattened, stacked cells hugging the
surface, and above them a smooth wavy coating layer with soft rolling undulations,
thicker and glossier than the cells below. The cap is clearly separated from the
lattice by its own boundary line. <표면 얼룩 — C의 눈금에서 가져온다>
```

AVOID 추가분:

```
a bare cell lattice reaching the open surface with no epidermal cap above it;
a cap so thin it reads as a line rather than a layer;
```

---

## C. 색소 진행 눈금 (PIGMENT STAGE)

**이 눈금이 A와 B를 묶는다.** 세포 안 색소와 표면 얼룩은 같은 사건의 두 얼굴
이므로 항상 같은 칸에서 가져온다. 한쪽만 진하면 화면이 앞뒤가 안 맞는다.

| 칸 | 세포 (A에 넣을 문구) | 표면 얼룩 (B에 넣을 문구) |
|---|---|---|
| **0 맑음** | The spheres are completely clear - no pigment anywhere. | The cap is clean and even, no discolouration. |
| **1 시작** | Only a faint dusting of tiny brown specks inside a few spheres, nothing gathered yet. | One very faint warm shadow spreading across part of the cap, barely there. |
| **2 형성** | Inside many spheres a small brown granular nucleus has gathered near the centre, the size of a pea against the sphere, with a few loose specks drifting around it. | A soft light-brown blotch on the cap, edges melting away with no defined outline. |
| **3 번짐** | The nucleus has grown large and its edge blurs outward as colour bleeds into the surrounding gel; a few spheres have stained through completely. | The blotch is clearly visible and denser at its centre, still soft-edged. |
| **4 착색** | Most spheres have stained through completely to deep warm brown, clustered in dark patches, while a few nearby stay pale cream - the contrast is the point. | A dark brown patch sits plainly on the cap, unmistakable against the clean skin around it. |

---

## D. 영상화를 고려한 단계 선택 (가장 중요)

Flow 프레임 모드와 seedance에서 **이미지는 곧 첫 프레임**이다. 그런데 이미지에
결말을 그려 넣으면 영상에서 변할 것이 남지 않아, 카메라만 움직이고 색소는
처음부터 끝까지 그대로다. 실제로 그렇게 만들었다가 되돌린 적이 있다
(2026-08-06, clip3·7·8).

**규칙: 이미지는 그 컷이 시작하는 칸을 그리고, 목표 칸은 영상 프롬프트가 만든다.**

- 이미지 프롬프트 → C의 **시작 칸**만 서술한다.
- 영상 프롬프트 SHOT → 무엇이 어떻게 변해 **끝 칸**에 닿는지 서술한다.
  예: `the nucleus inside each sphere swells and its colour bleeds outward until
  several spheres have stained through, and the blotch on the surface above
  darkens with them`
- 변화가 없는 컷(소개·상태 유지)은 시작 칸과 끝 칸이 같다. 그때는 카메라 이동만
  쓴다.
- 한 컷에서 두 칸 넘게 건너뛰지 않는다. 모델이 중간을 생략하고 튄다.

칸을 컷 순서대로 배치하면 편의 전체가 하나의 진행으로 읽힌다. 기미 원인 편
1챕터의 배치는 이랬다.

| 컷 | 대사 요지 | 시작 칸 → 끝 칸 |
|---|---|---|
| clip2 | 뿌리가 있다 (소개) | 0 → 0 |
| clip3 | 색소를 만들어 올려보낸다 | 0 → 2 |
| clip7 | 색소가 깊숙이 쏟아진다 | 1 → 3 |
| clip8 | 삼킨 채 눌러앉는다 | 2 → 4 |
| clip9 | 미백이 닿지 않는 깊이 | 4 → 4 (변하지 않는 것이 요점) |

**예외** — 대사의 요점이 "변하지 않음"이면 처음부터 끝 칸으로 둔다(clip9의
갈색 세포). 이때 변화는 다른 요소가 맡는다(크림이 퍼지다 멈춤).

---

## 조합 요령

- 세포층이 보이면 **A + B를 함께**, 색소는 **C의 같은 칸**에서 가져온다.
- 이미 통과한 컷의 재질만 고칠 때는 `gen_image.py --revise`로 구도를 붙잡는다.
- 레퍼런스 이미지가 있으면 `--ref`로 함께 붙인다. 구슬 격자는 말로만 설명하면
  잘 안 서고, 참조 한 장이 훨씬 정확하다.
