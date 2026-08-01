# 백로그

## 대기

- [ ] 2026-08-01 클립 자체 오디오 볼륨(0.2) 청감 튜닝 — 첫 실전작에서 효과음이 잘 들리는지 확인 필요 — assemble.py
- [ ] 2026-08-01 SKILL.md 2단계에 "대본 32초/7문장 = 7클립" 가이드 반영 (37.8초→10클립 초과 사례) — SKILL.md
- [ ] 2026-08-01 music/ 에 배경음악 mp3 추가 (현재 0곡이라 음악 없이 합본됨)
- [ ] 2026-08-01 Gemini TTS 한국어 보이스 청감 비교 (Kore 기본, 후보 30종) 후 기본값 확정 — .env GEMINI_TTS_VOICE
- [ ] 2026-08-01 폴링 대신 callBackUrl 웹훅 방식 검토 (대량 생성 시 효율) — scripts/kie_common.py
- [ ] 2026-08-01 music/ 비어 있을 때 BGM 자동 생성 옵션 검토 (예: ElevenLabs Music API, Lyria 등) — assemble 단계
- [ ] 2026-08-01 대본에 아라비아 숫자 표기 시 ASR 정규화 불일치("이십 퍼센트"↔"20%")로 정렬률 하락 — 대본 작성 규칙에 숫자 한글 표기 지침 추가 검토 — SKILL.md 2단계

- [ ] 2026-08-02 SKILL.md 2단계 대본 분량표 실측 반영 — 1.3배속 실측 0.183초/음절이라 "185~220음절≈30초"는 과다. 30초=165음절 안팎, 완성길이=나레이션+클립여백(이번 6.7초) — SKILL.md
- [ ] 2026-08-02 mg-bodylab NOTES.md에 권장 배속 1.3 기록 (현재 미기재라 매번 명령에 써야 함) — styles/mg-bodylab/NOTES.md
- [ ] 2026-08-02 피부 색소질환 묘사 프롬프트 정답을 pipeline-rules.md에 정리 — 점(주근깨)도 단일 덩어리(마스크)도 아닌 "크기 제각각 불규칙 얼룩 여러 개 + 갈색 명시"가 정답 (PROGRESS.md 2026-08-02 표 참조) — references/pipeline-rules.md
- [ ] 2026-08-02 인물 지정 규칙 명문화 — "adult woman"은 서구 패션모델로 나옴. 국적·연령·헤어·"not a fashion model"까지 써야 함 — references/pipeline-rules.md
- [ ] 2026-08-02 이미지·영상 생성은 항상 백그라운드 실행 (gen_image.py 최대 14분, foreground 8분 타임아웃에 죽은 사례) — SKILL.md 5·6단계
- [ ] 2026-08-02 인물 이미지 착의 규칙을 pipeline-rules.md에 명문화 — 전신은 나체로 나오고, AVOID에 nudity류 단어를 넣으면 생성 거부됨. 흉상+긍정문 착의 지정이 정답 — references/pipeline-rules.md
- [ ] 2026-08-02 mg-bodylab 스타일 자막(캡션) 사용 여부 결정 — 스타일 시그니처지만 한국어 나레이션과 언어가 어긋나고 오탈자 위험
- [ ] 2026-08-01 style-sheet: 영상 레퍼런스(mp4) 입력 지원 검토 — 현재 모션 시그니처는 정지 이미지 추론이라 confidence low — .claude/skills/style-sheet/
- [ ] 2026-08-01 style-sheet: k-means가 종이 톤 그라데이션을 여러 색으로 쪼개는 문제 — 색상환 거리 기반 자동 병합 검토 — scripts/extract_palette.py

## 완료

- [x] 2026-08-02 gen_image.py 조용한 실패 수정 — 재생성 시 기존 파일이 남아 있으면 생성 거부돼도 성공 보고하던 문제 (mtime 검사 추가)
- [x] 2026-08-01 vox-video 스킬 v1 구축 (스크립트 6종 + 가이드라인 2종 + SKILL.md)
- [x] 2026-08-01 v0.2.0 마이그레이션: Gemini TTS + MLX Whisper 정렬, Codex 구독 OAuth 이미지 (c301957 이후)
- [x] 2026-08-01 v0.3.0 참고 프로젝트 이식: TTS→로컬 clone-voice 백엔드(20 프로젝트), 영상→Gemini API omni flash 직접(26 프로젝트). 세 경로 실생성 검증
- [x] 2026-08-01 9:16 세로 스타일 지원 (gen_image.py --aspect 추가, 영상·합본은 기존 옵션 사용)
- [x] 2026-08-01 style-sheet 스킬 구축: 레퍼런스 이미지 → 11슬롯 스타일 DNA → 마스터 시트 역설계 (템플릿 재현성 + E2E 검증 완료)
- [x] ~~ElevenLabs 기본 보이스 만료 대응~~ — ElevenLabs 제거로 불필요해짐
