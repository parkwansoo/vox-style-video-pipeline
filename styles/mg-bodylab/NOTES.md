# mg-bodylab

3D 인체 매크로 + 하늘색 시클로라마 시각 시스템. 레퍼런스 13장에서
`/style-sheet` 스킬로 **역설계**한 첫 스타일이다 (2026-08-01).

- **출처**: Zack D. Films 영상 스타일 (사용자 확인). 브랜드명은 생성 프롬프트에
  넣지 않는다 — 로고·워터마크가 그려지거나 모델이 거부할 수 있고, 시각 정보는
  이미 11슬롯에 모두 담겨 있다
- **팔레트**: Cyclorama Blue #4B8CC6 / Skin Light #E9D3BF / Skin Mid #C9A691 /
  Hair Umber #6E5846 / Caption White #FFFFFF — 파랑은 배경 전용(피사체에 닿지 않음),
  흰색은 자막 전용
- **제작 논리**: soft-lit 3D renders, smooth subsurface skin, rounded simplified
  anatomy, shallow macro depth of field
- **비율 주의**: 원본 콘텐츠는 **세로 9:16**. 스타일 시트 자체는 16:9 보드다.
  이 스타일로 영상을 만들 때 클립 생성 비율을 9:16으로 바꿔야 한다
- **제외한 것**: 개미·유리병·나무 테이블 등 한 장짜리 소재, 도시·폭발 배경,
  티셔츠 브랜드 로고, 워터마크 있는 치과 이미지 1장(렌더 계열이 다른 아웃라이어)

## 파일

| 파일 | 뜻 |
|---|---|
| `refs/` | 레퍼런스 원본 13장 (git 제외 — 제3자 콘텐츠) |
| `style_dna.json` | 11슬롯 값. 여기를 고치고 재조립하면 시트가 바뀐다 |
| `style_prompt.txt` | 조립된 생성 프롬프트 (2,400자) |
| `style_prompt_standalone.txt` | 레퍼런스 미첨부용 (헤더 추가본) |
| `style_prompt_with_refs.txt` | 레퍼런스 첨부용 (소재·로고 복제 금지 문단 추가) |
| `palette_raw.json` | k-means 원시 추출값 |
| `style_reference.png` | **채택 시트** (사용자 생성, 2026-08-01) |
| `style_reference_alt.png` | 같은 프롬프트의 다른 생성본 (비교 보관용) |

## 시트 검증 (2026-08-01)

1672×941 (16:9). 11슬롯이 모두 패널로 렌더됐고 타입 샘플 문자열도 정확하다.

**팔레트 실측** — 생성된 시트의 스와치를 픽셀 샘플링해 DNA 값과 대조:

| 색 | DNA | 시트 실측 |
|---|---|---|
| Cyclorama Blue | `#4B8CC6` | `#568ABB` |
| Skin Light | `#E9D3BF` | `#E6CBB7` |
| Skin Mid | `#C9A691` | `#CDA690` |
| Hair Umber | `#6E5846` | `#654C38` |
| Caption White | `#FFFFFF` | `#F7F4F1` |

육안으로 구분되지 않는 수준의 오차. 이미지 생성 모델이 지정 hex를 이 정도로
맞추는 건 이례적으로 좋은 결과다.

**두 생성본의 차이** — `style_reference.png`를 채택한 이유:

| 항목 | 채택본 | alt |
|---|---|---|
| 인물 렌더 | 사실적, 레퍼런스에 근접 | 카툰/스타일라이즈드 |
| 소품 | 구체적 (드로퍼 병) | 추상적 (구슬·물컵) |
| 팔레트 스와치 | 5색 모두 식별됨 | 첫 색(파랑)이 배경에 묻힘 |
| 오탈자 | 없음 | "SKIN MAYERS" (LAYERS 오타) |
