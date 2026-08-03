# mg-bodylab-vgshot

mg-bodylab의 **주제 반영 변형**. 동일한 레퍼런스 13장(SHA 대조로 확인)을
시리즈 주제를 알고 다시 역설계했다 (2026-08-03). 스타일 관찰값(서체 스타일·
팔레트·재질·배경)은 mg-bodylab 그대로, **샘플 문자열과 샘플 소재만** 주제에
맞춰 새로 썼다.

- **출처**: Zack D. Films 영상 스타일 스크린샷 13장 (mg-bodylab/refs와 동일
  파일). 브랜드명은 생성 프롬프트에 넣지 않는다
- **주제** (사용자 지정, SUBJECT THEMES 줄로 조립됨): 기미와 비타민C 앰플
  제형 / 비타민C 묻은 노란 타원형 바늘 스피큘 / 기미의 원인 / 징그럽지 않은
  스킨레이어 — 영어로는 "melasma and vitamin C ampoule fluid textures,
  golden-yellow oval needle-like spicules coated in vitamin C, the causes of
  melasma, and soft clean simplified skin layers"
- **팔레트**: Cyclorama Blue #4B8CC6 / Skin Light #E9D3BF / Skin Mid #C9A691 /
  Hair Umber #6E5846 / Caption White #FFFFFF — mg-bodylab 실측값 재사용
  (동일 파일이므로 재추출 대신 palette_raw.json 복사)
- **제작 논리**: soft-lit 3D renders, smooth subsurface skin, rounded
  simplified anatomy, shallow macro depth of field (유지)
- **비율 주의**: 원본 콘텐츠는 **세로 9:16**. 시트는 16:9 보드다. 클립 생성
  비율은 9:16
- **권장 배속 1.3** — mg-bodylab과 동일

## mg-bodylab에서 바뀐 슬롯

| 슬롯 | 기존 | 여기 |
|---|---|---|
| H1 견본 | IF YOU SWALLOW THIS | WHY MELASMA APPEARS |
| 캡션 견본 | natural oils | vitamin C |
| 피부 단면 | 모낭 있는 단면, wet pinks | 매끈하고 단순한 단면 (모낭·습윤 제거) |
| 소품 | 평범한 일상 소품 | 골든 액체 유리 앰플 |
| 미니씬 | 리액션 / 피부 위 곤충 / 모낭 단면 | 기미 얼굴 / 모공 사이 노란 타원 바늘 스피큘 / 골든 방울 스며드는 단면 |
| 모션 4번 | 소품 낙하 | 앰플 낙하 |

**wet pinks·follicles를 뺀 이유**: 광고 용도에 피부 단면이 의학 도해처럼
생생해 징그럽다는 사용자 피드백 (2026-08-03). 시트의 샘플이 클립 소재로
유출되는 성질 때문에, 클립마다 제약을 거는 대신 시트 단계에서 순화했다.

## 파일

| 파일 | 뜻 |
|---|---|
| `refs/` | 레퍼런스 원본 13장 (git 제외, mg-bodylab/refs와 동일) |
| `style_dna.json` | 11슬롯 값 (주제 반영판) |
| `프롬프트_자동생성용.txt` | 조립된 프롬프트 — SUBJECT THEMES 줄 포함 (2,623자), Codex 렌더에 사용 |
| `프롬프트_직접생성용_텍스트만.txt` | 외부 도구 직접 생성용 (텍스트만 붙여넣기) |
| `프롬프트_직접생성용_레퍼런스첨부.txt` | 외부 도구 직접 생성용 (레퍼런스 13장 첨부 시) |
| `palette_raw.json` | mg-bodylab에서 복사한 k-means 실측값 |
| `style_reference.png` | 생성된 시트 |
