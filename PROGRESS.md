# 100% Automated Vox — 진행 기록

Vox 스타일 애니메이션 저널리즘 영상을 완전 자동 생성하는 프로젝트 로컬 스킬
(`/vox-video`).

## 현재 상태 (2026-08-01)

- ✅ 스킬 v1 구축 완료. 스모크 테스트(합성 클립으로 assemble.py 전체 실행) 통과.
- ✅ 사용자 제공 Paper Diorama 프롬프트 시스템(`drive-download-*` 폴더)을
  references/에 정본으로 채택, 예시 스타일 시트를 `assets/style_reference.png`
  기본값으로 배치.
- ⏳ 사용자 준비물 대기: `.env`에 API 키 2개 입력, `music/`에 mp3 (선택).
- 실제 API를 사용한 첫 end-to-end 실행은 아직 안 함.

## 구조

- `.claude/skills/vox-video/SKILL.md` — 워크플로 지침 (리서치→대본→TTS→분할→이미지→영상→합본)
- `scripts/` — tts.py(ElevenLabs with-timestamps), gen_image.py(GPT Image 2),
  gen_video.py(Gemini Omni Flash/Seedance 2.0 Fast), assemble.py(ffmpeg 합본),
  upload.py, kie_common.py
- `references/` — 사용자 제공 Paper Diorama 프롬프트 시스템(이미지/영상) +
  pipeline-rules.md(파이프라인 보충: 공인 규칙, 타임스탬프 큐 +0.25s 보정,
  이미지 프롬프트 템플릿)

## 주요 결정 (2026-08-01)

- **방식**: 지침형 SKILL.md + Python 헬퍼 스크립트. 창의적 판단(리서치, 대본,
  프롬프트, 클립 분할)은 Claude가, 결정적 작업(API·정렬·ffmpeg)은 스크립트가
  담당. 이유: 실행마다 재현성 확보 + 스토리 품질 유지.
- **실효 길이 기준 분할**: 합본 때 클립 앞 0.25s가 잘리므로 4s→3.75s,
  6s→5.75s를 기준으로 나레이션 구간을 배분. 영상 프롬프트의 타임스탬프 큐는
  +0.25s 보정.
- **동기화 방식**: 챕터 나레이션을 클립 구간별로 atrim해 각 클립 시작
  오프셋에 adelay로 배치 (구간 경계는 단어 사이 중간값 → 컷이 안 들림).
  이유: 클립 길이와 나레이션 길이의 오차 누적을 원천 차단.
- **설정 확정**: 16:9 / 720p 생성, 한국어 나레이션, 기본 보이스 Brian
  (`.env`에서 변경 가능), eleven_multilingual_v2, 스타일 참조·음악은 사용자 제공.
- **Kie.ai 세부**: 통합 Jobs API 사용. duration 타입이 모델별로 다름(Omni는
  문자열, Seedance는 정수). 로컬 이미지는 kieai.redpandaai.co 무료 임시
  호스팅(base64 업로드)으로 URL화.
