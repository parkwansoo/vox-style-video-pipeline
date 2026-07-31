# 백로그

## 대기

- [ ] 2026-08-01 클립 자체 오디오 볼륨(0.2) 청감 튜닝 — 첫 실전작에서 효과음이 잘 들리는지 확인 필요 — assemble.py
- [ ] 2026-08-01 SKILL.md 2단계에 "대본 32초/7문장 = 7클립" 가이드 반영 (37.8초→10클립 초과 사례) — SKILL.md
- [ ] 2026-08-01 music/ 에 배경음악 mp3 추가 (현재 0곡이라 음악 없이 합본됨)
- [ ] 2026-08-01 Gemini TTS 한국어 보이스 청감 비교 (Kore 기본, 후보 30종) 후 기본값 확정 — .env GEMINI_TTS_VOICE
- [ ] 2026-08-01 폴링 대신 callBackUrl 웹훅 방식 검토 (대량 생성 시 효율) — scripts/kie_common.py
- [ ] 2026-08-01 music/ 비어 있을 때 BGM 자동 생성 옵션 검토 (예: ElevenLabs Music API, Lyria 등) — assemble 단계
- [ ] 2026-08-01 대본에 아라비아 숫자 표기 시 ASR 정규화 불일치("이십 퍼센트"↔"20%")로 정렬률 하락 — 대본 작성 규칙에 숫자 한글 표기 지침 추가 검토 — SKILL.md 2단계

## 완료

- [x] 2026-08-01 vox-video 스킬 v1 구축 (스크립트 6종 + 가이드라인 2종 + SKILL.md)
- [x] 2026-08-01 v0.2.0 마이그레이션: Gemini TTS + MLX Whisper 정렬, Codex 구독 OAuth 이미지 (c301957 이후)
- [x] 2026-08-01 v0.3.0 참고 프로젝트 이식: TTS→로컬 clone-voice 백엔드(20 프로젝트), 영상→Gemini API omni flash 직접(26 프로젝트). 세 경로 실생성 검증
- [x] ~~ElevenLabs 기본 보이스 만료 대응~~ — ElevenLabs 제거로 불필요해짐
