# 백로그

## 대기

- [ ] 2026-08-01 첫 실제 실행 후 볼륨 밸런스(클립 0.2/음악 0.15) 청감 튜닝 — assemble.py 기본값
- [ ] 2026-08-01 ElevenLabs 기본 보이스 만료 대응 (legacy default voices 2026-12-31 만료 예고) — .env의 ELEVENLABS_VOICE_ID, scripts/tts.py
- [ ] 2026-08-01 폴링 대신 callBackUrl 웹훅 방식 검토 (대량 생성 시 효율) — scripts/kie_common.py
- [ ] 2026-08-01 music/ 비어 있을 때 ElevenLabs Music API로 BGM 자동 생성 옵션 (POST /v1/music, 유료 플랜 필요) — assemble 단계

## 완료

- [x] 2026-08-01 vox-video 스킬 v1 구축 (스크립트 6종 + 가이드라인 2종 + SKILL.md)
