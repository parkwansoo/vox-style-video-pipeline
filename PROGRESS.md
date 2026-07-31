# 100% Automated Vox — 진행 기록

Vox 스타일 애니메이션 저널리즘 영상을 완전 자동 생성하는 프로젝트 로컬 스킬
(`/vox-video`).

## 현재 상태 (2026-08-01, v0.3.0 — 참고 프로젝트 이식 완료)

- ✅ v3 스택 확정, **세 경로 모두 실제 생성으로 검증 완료**:
  - 나레이션: **로컬 clone-voice TTS 백엔드**(SSD Samsung_T5, 8930, 자동
    기동, Gemini 음색 Charon 기본 + 톤 프롬프트) + **로컬 MLX Whisper** 정렬
    — 20_숏츠 자동화 프로젝트 방식 이식. API 키 불필요. E2E 검증(정렬률 84%)
  - 이미지: **Codex CLI 내장 생성 (ChatGPT 구독 OAuth, gpt-image-2)** —
    API 키 불필요, 스타일 시트 반영 검증 완료
  - 영상(일반): **Gemini API 직접 호출 `gemini-omni-flash-preview`**
    (google-genai Interactions API + Files API 참조 업로드) — 26_vox_style_video
    프로젝트 방식 이식. 4초 클립 실생성 검증 완료
  - 영상(공인): Kie.ai Seedance 2.0 Fast 유지 (첫 프레임 방식)
- `.env`: GEMINI_API_KEY는 26 프로젝트에서 복사해 채움. KIE_API_KEY는 공인
  클립 쓸 때만 필요 (현재 비어 있음). `music/` mp3는 선택.
- 다음: 첫 실전 영상 생성 (전체 파이프라인 관통)

## v1 상태 (2026-08-01 초기 구축)

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

## v0.2.0 마이그레이션 결정 (2026-08-01)

- **Gemini TTS는 타임스탬프 미지원** → 로컬 MLX Whisper(word_timestamps) +
  대본 정본 정렬로 해결. 정렬은 문자 단위 SequenceMatcher 방식(한국어
  띄어쓰기 차이에 강함), 미매칭 단어는 이웃 사이 보간. 참고 프로젝트
  26_vox_style_video의 정렬 설계를 단순화해 채택.
- **이미지 구독 OAuth 경로**: `~/.codex/skills/imagegen`(OPENAI_API_KEY 요구
  스킬)이 아니라 Codex CLI **내장** `image_generation` 기능(stable)을 사용.
  `codex exec -i <스타일시트> -- "<프롬프트>"` 형태. `--` 없이는 -i가
  프롬프트를 삼키는 버그 있음 (수정 반영).
- **영상은 Veo가 아닌 Omni Flash 유지** (사용자 결정) → Omni Flash는 Gemini
  API에 없어 Kie.ai 경유가 계속 필요, KIE_API_KEY 유지.
- 의존성은 프로젝트 `.venv`(requirements.txt: requests, python-dotenv,
  mlx-whisper). Whisper 모델은 ~/.cache/huggingface의 기존 스냅샷 재사용.

## v0.3.0 참고 프로젝트 이식 결정 (2026-08-01)

- **TTS는 Gemini API가 아니라 로컬 clone-voice 백엔드** (사용자 지시,
  20_숏츠 자동화 이식): ensure_tts.sh가 SSD 이미지 마운트 + uvicorn(8930)
  자동 기동. 음색 이름→프로필 id는 `/api/voices`의 `gemini-voice:<이름>`
  태그로 해석. 톤 프롬프트에 "감정이 풍부함" + 비언어 가드 포함(20 프로젝트
  실측 확정 규칙). 표현태그 삽입본은 --tagged-file, 정렬은 항상 원본 대본.
- **Omni Flash는 Gemini API에 존재** (`gemini-omni-flash-preview`) — v0.2.0
  조사 때 놓쳤던 것. google-genai SDK `client.interactions.create(model,
  input=[image/text parts], response_format={type:video, duration:"4s"~,
  aspect_ratio, delivery:"uri"})`, 이미지는 Files API 업로드 후 uri 참조,
  duration 3~10초. 26_vox_style_video의 generate_video.py 이식.
- Kie.ai는 공인 클립(Seedance 첫 프레임)에만 남김 — KIE_API_KEY 없이도
  일반 영상은 전부 생성 가능.
