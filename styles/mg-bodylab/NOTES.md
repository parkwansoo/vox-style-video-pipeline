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
| `style_reference.png` | 생성된 시트 — **아직 없음**, 생성 후 여기 저장 |
