# 100% Automated Vox — 진행 기록

Vox 스타일 애니메이션 저널리즘 영상을 완전 자동 생성하는 프로젝트 로컬 스킬
(`/vox-video`).

## 현재 상태 (2026-08-01, v0.3.0 — 참고 프로젝트 이식 완료)

- ✅ v3 스택 확정, **세 경로 모두 실제 생성으로 검증 완료**:
  - 나레이션: clone-voice 백엔드(SSD Samsung_T5, 8930, 자동 기동) 경유 +
    **로컬 MLX Whisper** 정렬 — 20_숏츠 자동화 프로젝트 방식 이식.
    E2E 검증(정렬률 84%). ⚠️ 2026-08-02 정정: 이 백엔드는 여러 TTS 엔진을
    붙이는 로컬 허브이고 우리는 `model_id="gemini"`를 보내므로 실제 합성은
    **Google Gemini TTS 클라우드**(gemini-3.1-flash-tts-preview)에서 일어난다.
    무료가 아니라 약 $0.03/분 과금(clone-voice에 등록된 Google 계정 부담).
    우리 .env에 키가 필요 없을 뿐이다
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
  (당시엔 TTS를 무료로 알고 재생성했으나, 2026-08-02 확인 결과 Gemini
  클라우드 과금이었다 — 약 $0.03/분. 재생성 전에 분량을 계산하는 편이 낫다.)
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

## mg-bodylab 첫 실전 적용 — 기미 원인 편 리메이크 (2026-08-02)

같은 주제(기미 원인)를 vox-collage가 아닌 **mg-bodylab(Zack D. Films 계열)**
스타일로 다시 제작. 스타일 전환은 `assets/style_reference.png` 교체 +
`ACTIVE_STYLE` 갱신 두 줄로 끝났고, 라이브러리 구조가 의도대로 동작했다.

- **배속 1.3 확정**: 스타일 특성(빠른 숏폼)에 맞춰 지정. 대본 218음절이
  40.2초로 상한(38초)을 넘겨 184음절로 줄여 재생성 → 35.1초, 정렬률 0.978.
  **실측 환산율은 약 0.183초/음절**로, SKILL.md의 "1.3배속 185~220음절 ≈ 30초"
  표는 낙관적이었다. 30초를 노리면 **165음절 안팎**이 맞다.
- **클립 9개**(6초×4 + 4초×5). 완성 길이는 나레이션 35.1초 + 클립 여백 6.7초
  = **41.8초**. 여백은 클립 실효길이와 나레이션 구간의 차이가 누적된 값이다.
  즉 "완성 길이 ≈ 나레이션 + 여백 총합"이며, 30초 영상을 원하면 나레이션을
  26~28초로 잡아야 한다.
- **내용을 스타일에 맞췄다**: 원인 나열식(vox-collage 버전) 대신 몸속으로
  계속 파고드는 구조(표면→멜라노사이트→색소 생산→호르몬 과열→기저막 붕괴→
  색소 낙하→대식세포→크림이 못 닿음). 인체 매크로 스타일에는 이 구조가 맞다.
- **화면 자막 없음**: 스타일의 자막 문법은 영어인데 나레이션이 한국어라
  섞이고, 시트 생성 때 "SKIN MAYERS" 오탈자 전례가 있어 제외.

### 이미지 생성에서 배운 것

- **"soft-edged brown patches"만으로는 기미가 안 나온다** — 주근깨로 그려졌다.
  "one continuous soft-edged brown blotch ... a single unbroken stain, no
  defined outline"처럼 **연속된 하나의 얼룩**임을 명시하고 AVOID에
  freckles/speckles/dots를 넣어야 실제 기미 형태가 된다.
- **전신 인물은 나체로 나온다.** 인물 다수를 보여줄 땐 전신 대신
  **head-and-shoulders 흉상 + 착의 명시**가 안전하고, 얼굴 색소를 보여주는
  목적에도 훨씬 잘 맞는다.
- **AVOID에 nudity/bare chest 같은 단어를 넣으면 오히려 생성이 거부된다.**
  금지어를 나열하지 말고 "wearing a plain cream crew-neck top"처럼
  **긍정문으로 옷을 지정**해야 통과한다.
- 재생성 3회(clip1 기미형태, clip6 착의, clip9 심부 색소 가시성). 나머지
  6장은 1회 통과했고, 스타일 일치도는 전반적으로 매우 높았다.

### gen_image.py 조용한 실패 버그 수정

재생성 시 **기존 파일이 남아 있으면 생성이 거부돼도 성공으로 보고**했다
(`out_path.is_file()`만 검사). clip6이 낡은 이미지 그대로였는데 exit 0에
`{"out": ...}`이 찍혀 하마터면 그대로 영상화될 뻔했다. 호출 전 mtime을
기록해 **파일이 실제로 갱신됐는지**까지 검사하도록 수정. 갱신되지 않았으면
재시도하고, 끝내 실패하면 종료 코드로 알린다.

### 완성 (2026-08-02)

`output/20260802-melasma-causes/final.mp4` — 720×1280 세로, **41.9초**, 9클립,
배경음악 없음(music/ 비어 있음). 동기화는 9개 구간 전부 프레임 추출로 검증했다
("여성호르몬이"→호르몬 도킹, "뚫리면"→색소 낙하, "미백 성분이"→크림이 멈춤).
Omni 44초 생성, 약 $4.5. 재생성 없이 9개 모두 1회 통과.

**기미 묘사의 정답 구간을 찾았다.** 세 번의 시도로 좁혀진 결과:

| 지시 | 결과 |
|---|---|
| "soft-edged brown patches" | 주근깨 (점이 흩뿌려짐) |
| "one continuous soft-edged blotch, single unbroken stain" | 검은 마스크 (얼굴 절반이 균일하게 덮임) |
| **"several separate patches of clearly different sizes and irregular shapes, scattered around the outer corners of the eyes, temples and cheekbones, some broad and darker, some small and faint, a few merging, asymmetric"** | **실제 기미** |

즉 **점도 아니고 단일 덩어리도 아닌, 크기가 제각각인 불규칙한 얼룩 여러 개**가
정답이다. "붉거나 주황 톤 금지 - 갈색"도 함께 넣어야 일광화상처럼 안 나온다.

**훅 구도**: 강한 광각 + 눈높이 아래 로우앵글 + 3/4 측면 + 감정 있는 표정
(눈썹 찌푸리고 곁눈질하는 "아 또 이러네" 얼굴)이 정면 대칭 증명사진보다
훨씬 강했다. 어안 왜곡과 콧구멍 앙각은 AVOID로 막아야 한다.

**모델 지정은 구체적으로**: "adult woman"은 서구권 패션모델로 나온다.
"an ordinary Korean woman in her fifties, short dark permed hair, a warm
everyday face - not a fashion model"처럼 국적·연령·헤어·"모델 아님"까지
명시해야 의도한 인물이 나온다.

**bash 타임아웃 주의**: gen_image.py는 시도당 7분 + 재시도라 최대 14분이다.
foreground 8분 타임아웃으로 죽인 적이 있으니 이미지·영상 생성은 항상
백그라운드로 돌린다.

## 기미 지우기 시리즈 2편 — 브이지샷 광고 (2026-08-03 완성)

`output/20260802-melasma-vgshot/final.mp4` — 720×1280 세로, **59.2초**, 12클립
(ch1 6 + ch2 6), 배경음악 없음. **전 클립을 Google Flow 브라우저 경로로 생성**
(Omni API 대비 구독 크레딧 사용). 동기화는 12개 구간 전부 프레임 추출로 검증.

### Flow 브라우저 경로 실전 결과

12클립 + 재생성 2회 = **약 122크레딧** (4s=7, 6s=10). API였다면 약 $12.
제출→완료 **30~60초**로 Omni API보다 오히려 빨랐다. 프롬프트 입력은 12회 모두
SHA-256이 매니페스트와 완전 일치했다 — `computer.type` 경로는 신뢰할 수 있다.

**flow-browser.md에 없던 것들 (다음에 쓸 때 시간 절약)**

| 발견 | 내용 |
|---|---|
| 다운로드 | 카드 ⋮ 메뉴보다 **편집 화면 우상단 다운로드 아이콘 1회 클릭**이 빠르다. 720p 원본이 바로 받아진다 (메뉴 없이) |
| 애셋 선택 | 목록이 길어지면 **검색창에 `ch2-clip6` 입력**이 확실하다. 최신순 위치로 찾으면 틀린다 |
| 창 크기 | Flow는 창 크기를 임의로 바꾼다. 좌표 기반 배치 전에 매번 스크린샷으로 확인해야 한다 |
| 생성 실패 | ch1-clip3이 1회 실패했다. 카드에 재시도(↻) 버튼이 뜨고 **실패는 과금되지 않는다**. 재시도로 정상 생성 |
| JS 폴링 | 45초 넘는 루프는 CDP 타임아웃에 걸린다. `wait` 배치 + 단발 체크로 나눠야 한다 |
| 완료 판정 | 퍼센트 텍스트 소멸 + `video.currentSrc` 존재. `hasVideo`만으로는 placeholder와 구분 안 된다 |
| 업로드 경로 | `file_upload`는 세션 허용 경로만 받는다. 프로젝트 폴더는 거부되므로 **스크래치패드로 복사 후 업로드** |

### 영상 생성에서 제품이 변형된다 — 이미지가 정확해도 소용없다

ch2-clip6(CTA)의 제품이 영상화 과정에서 무너졌다. 이미지는 완벽했는데:

| 항목 | 원본 | 1차 생성 결과 |
|---|---|---|
| 내용물 | 금빛 노란 앰플 | 사라짐(투명) |
| 라벨 3행 | `VG SHOT AMPOULE` | `VO SHOT AMPOULE` |
| 라벨 4행 | `Vitanmine C + Glutathione` | `Vecoming & • Glutethence` |
| 용량 | `30 ml` | **`50 ml`** |

**원인은 push-in이다.** 같은 제품 고정 문구를 쓴 clip1·clip5는 멀쩡했는데,
clip6만 카메라가 라벨로 접근한다. 라벨이 화면에서 커질수록 모델이 글자를
새로 그린다. 광고에서 용량 오표기는 그냥 둘 수 없다.

**해결**: 영상 프롬프트에도 **라벨 5줄을 그대로 쓰고**(이미지 프롬프트에만
있으면 안 된다), "내용물이 비거나 투명해지지 않는다", "스티커 패널 금지",
"30 ml 외의 용량 금지"를 AVOID에 넣었다. 재생성 1회로 정확히 나왔다.

→ **제품이 클로즈업되는 컷은 영상 프롬프트에도 라벨 문구를 반복한다**는 규칙이
필요하다 (백로그 기록됨).

### Flow Pro는 워터마크를 끌 수 없다

생성 영상 우하단에 4각별 워터마크가 박힌다. Visible watermarking 토글이 Pro
구독에서는 비활성이다(사용자 확인). 이번 편은 사용자 판단으로 감수하고 진행했다.
광고 용도로 계속 쓰려면 후처리나 레이어 가림이 필요하다.
