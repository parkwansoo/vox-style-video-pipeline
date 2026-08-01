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
- ✅ **첫 실전 영상 완성** (2026-08-01): `output/20260801-melasma-causes/final.mp4`
  — 기미의 원인 다큐, 36.4초/7클립. 파이프라인 전 구간 무사고 관통.

## 스타일 라이브러리 구조 도입 (2026-08-01)

두 번째 스타일(mg-bodylab)을 만들자 `assets/`에 **서로 다른 스타일의 파일이
섞이는 문제**가 드러남 — `style_reference.png`는 Vox인데 `style_dna.json`은
MG-BODYLAB이라 한 세트처럼 보이지만 실제로는 무관했다. `refs/`도 다음 작업과
섞일 구조였다.

**결정: 스타일은 영상 폴더가 아니라 독립 라이브러리에 둔다** (사용자 확인).
스타일은 재사용 자산이고 영상은 일회성 산출물이라, 영상 폴더에 넣으면 같은
스타일로 영상 N개를 만들 때 레퍼런스와 DNA가 N번 복제된다.

```
styles/<이름>/     refs + DNA + 프롬프트 + 시트 + NOTES.md (스타일 원본)
assets/            활성 스타일 복사본 + ACTIVE_STYLE (현재 쓰는 것 한 벌)
output/<영상>/     style.txt 로 어떤 스타일을 썼는지 기록
refs/              새 작업 인박스 (스타일 폴더로 옮기고 비움)
```

`assets/style_reference.png`를 활성 슬롯으로 유지한 게 핵심 — vox-video가 이
경로를 참조하므로 **스킬 코드를 안 건드리고** 파일 복사만으로 전환된다.

레퍼런스 이미지는 제3자 콘텐츠라 `.gitignore`로 제외(로컬 보관만), DNA·프롬프트·
시트는 우리 산출물이라 커밋한다.

## style-sheet 스킬 추가 (2026-08-01)

레퍼런스 이미지 2~5장 → 스타일 DNA(JSON) → 마스터 스타일 시트 이미지를
역설계하는 `/style-sheet` 스킬. vox-video와 별도 스킬로 분리(시트 교체는
영상 제작과 빈도·성격이 다름).

**핵심 발견**: 사용자가 준 스타일 프롬프트 3종(MG-BLUEPRINT / Vox /
MG-SOFT3D)이 스타일은 전혀 다른데 **동일한 11슬롯 골격**을 공유. 역설계가
자유 서술이 아니라 **빈칸 채우기**가 되어 정확도가 크게 올라감.

**설계 결정**
- **DNA JSON 중간 단계를 둔다**: 이미지→프롬프트 직행이면 검증·수정 불가.
  JSON이면 hex 하나만 고치거나 같은 DNA로 시트를 여러 번 뽑을 수 있음
- **색은 코드, 나머지는 판단**: hex 눈대중은 반드시 틀림 → k-means로 실측.
  동시에 얻는 `coverage`(점유율)와 `edge_ratio`(윤곽 비율)가 "주조색 vs 선
  전용 강조색"을 자동 분류 (Vox 클립 3장 테스트에서 빨강을 6.2% hot accent로
  정확히 판정)
- **교집합 필터링이 품질의 핵심** (사용자 결정): 여러 장에서 반복되는 것만
  스타일로 채택. 한 장에만 있는 건 그 이미지의 소재 → `shared` 플래그로 판별
- **어두운 색은 채도 판정 제외**: RGB(31,26,19)가 saturation 0.39로 계산돼
  잉크 블랙이 accent로 오분류됨 → luminance ≤0.15면 먼저 ink로 분류
- **THE STAGE는 조건부**: 배경이 클립마다 다르면 통째로 빼야 함. 억지로 넣으면
  이후 모든 클립 배경이 똑같아짐

**검증**: ① 템플릿이 원본 Vox 프롬프트를 문자 단위로 완전 재현 ② Vox 클립
3장으로 E2E 실행 → 팔레트·타입 샘플·색 규칙이 모두 반영된 시트 생성 성공

## 첫 실전 실행에서 얻은 것 (2026-08-01, 기미 편)

- **대본 길이 → 클립 수 관계**: 대본이 34초를 넘으면 문장 경계를 지키는 한
  클립이 9개 이상 필요해져 규칙(4~8)을 벗어난다. **32초 내외 / 7문장이
  7클립에 정확히 맞는 지점.** 첫 대본 37.8초 → 10클립이라 두 번 축약함.
  TTS가 로컬 무료라 재생성 비용이 없다는 점이 이 조정을 가능하게 함.
- **Omni Flash는 참조 이미지를 잘 지킨다**: 7클립 전부 원본 이미지의 구도·
  텍스트·색을 유지한 채 모션만 추가. 다만 프롬프트에 없던 halftone 인물
  컷아웃을 몇 클립에 임의로 추가함(스타일 내라 무해). 텍스트 변조 방지에는
  "Keep the existing elements and text exactly as they are; do not add new
  text" 문구가 효과적이었다.
- **Codex 이미지 생성**: 7장 중 재시도 0회. 스타일 시트 반영도가 매우 높음.
  동시 2개 병렬이 안정적.
- **정렬률**: 한국어 다큐 대본에서 0.93. 숫자를 한글로 적으면(아흔다섯) ASR이
  "95"로 인식해도 문자 정렬이 흡수함 — 오히려 아라비아 숫자보다 안전했다.

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
