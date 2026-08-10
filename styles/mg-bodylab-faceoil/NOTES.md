# mg-bodylab-faceoil

mg-bodylab의 **주제 반영 변형**. 헤기 페이스오일(자스민 드롭스) 편을 위해
샘플 소재와 문구만 갈아끼웠다 (2026-08-10). 스타일 관찰값(팔레트·재질·배경·
무드)은 mg-bodylab 실측값 그대로다.

- **출처**: Zack D. Films 영상 스타일. 레퍼런스 13장은 mg-bodylab/refs와 동일
  파일이고, 여기에 렌더 교정용 3장을 추가로 썼다 (`refs/`). 브랜드명은
  생성 프롬프트에 넣지 않는다
- **팔레트**: Cyclorama Blue #4B8CC6 / Skin Light #E9D3BF / Skin Mid #C9A691 /
  Hair Umber #6E5846 / Caption White #FFFFFF — mg-bodylab 실측값 재사용
  (동일 파일이므로 재추출 대신 palette_raw.json 복사)
- **주제**: 광대 기미 / 각질과 그 위로 갈라지는 파운데이션 / 스며드는 앰버
  오일 / 투명 유리 드로퍼 병 / 자스민
- **비율 주의**: 원본 콘텐츠는 **세로 9:16**. 시트는 16:9 보드다
- **권장 배속 1.3** — mg-bodylab과 동일

## mg-bodylab에서 바꾼 것

| 슬롯 | 변경 | 이유 |
|---|---|---|
| components 1 | `centred to camera` → `caught mid-reaction` | mg-bodylab NOTES의 경고대로 전 클립 정면 고착을 유발했다 |
| components 3 | 진피를 **투명 유리 구슬 격자**로 | TODO 2026-08-06 결정. 시트가 구슬을 보여주면 클립마다 넣던 CELLS 교정 블록이 불필요해진다 |
| components 5 | `frosted` → **투명 유리 병** | 실물이 투명이다 (PROGRESS 2026-08-04 제품 컷 실측). 근거 없이 창작했던 값을 교체 |
| construction_logic | `never photographic` 추가 | 1차 렌더가 포토리얼로 나왔다 |
| finish | 사진 계열·wet pink 금지 추가 | 위 둘을 AVOID 쪽에서도 잠갔다 |
| mini_scenes | 상태 서술 → **진행형 사건** | "something is happening, not someone explaining" (사용자 지시). 시트 샘플이 클립으로 유출되는 성질을 이용 |

## 렌더 이력

1차는 DNA만으로 렌더했더니 **인물과 피부 매크로가 포토리얼**로 나왔다 —
`soft-lit 3D renders`라고 썼는데도 Zack D. Films 특유의 조각된 머리카락·
매끈한 서브서피스가 안 나왔다. DNA는 레퍼런스를 텍스트로 번역한 것이라
말로 안 되는 렌더 질감이 유실된다.

2차에서 `make_sheet.py --ref`(이번에 추가한 옵션)로 시리즈 프레임 2장과
제품 실물 사진 1장을 붙여 재렌더해 해결했다. 보관본:
`style_reference_v1포토리얼.png`.

**부작용**: 컴포넌트 패널의 인물이 레퍼런스 속 인물과 꽤 닮게 나왔다.
"장면은 베끼지 말라"는 지시로 완전히 막히지 않는다. 클립 프롬프트에서
인물을 명시하지 않으면 이 얼굴이 새어나올 수 있다.

**미해결**: 프롬프트가 2,615자로 경고 임계값을 넘었다 (기존 3종 1,782~2,258).
construction_logic과 finish를 늘린 탓이며, 압축 여지가 있다.
