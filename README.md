# Vox Style Video Pipeline

주제 한 줄을 넣으면 **리서치 → 대본 → 나레이션 → 클립 생성 → 합본**까지
자동으로 도는 Claude Code 스킬 모음입니다. Vox 스타일 애니메이션 해설 영상을
만드는 것이 목표이며, 나레이션과 화면이 초 단위로 맞물리는 것을 최우선으로
설계했습니다.

> 개인 작업 환경에 맞춘 파이프라인입니다. 그대로 실행하려면 아래 "환경 의존성"에
> 적힌 로컬 구성이 필요합니다. 설계와 프롬프트 체계는 그대로 참고하실 수 있습니다.

## 스킬 두 개

| 스킬 | 하는 일 |
|---|---|
| **`/vox-video`** | 주제 → 완성 영상 (리서치·대본·TTS·클립 분할·이미지/영상 생성·합본) |
| **`/style-sheet`** | 레퍼런스 이미지 2~8장 → 시각 스타일 역설계 → 마스터 스타일 시트 |

## 파이프라인

```
주제
 ├─ 웹 리서치 → 대본 (챕터당 약 30초)
 ├─ TTS → narration.mp3
 ├─ MLX Whisper(로컬) → 단어 타임스탬프 → 대본에 정렬 → words.json
 ├─ words.json 기반 클립 분할 (4초 / 6초)
 │    실효 길이 3.75s / 5.75s 로 배분 — 합본 때 앞 0.25초를 잘라내기 때문
 ├─ 클립별 이미지 생성 (스타일 시트를 재료로 참조)
 ├─ 이미지 → 영상 클립 생성
 └─ ffmpeg 합본: 나레이션 구간을 각 클립 시작점에 정확히 배치
      + 클립 자체 오디오는 낮은 볼륨으로 유지(효과음) + 배경음악 랜덤 1곡
```

**동기화 방식이 핵심입니다.** 클립 길이와 나레이션 길이의 오차가 누적되지
않도록, 챕터 나레이션을 구간별로 잘라 각 클립의 시작 오프셋에 배치합니다.
구간 경계는 단어 사이 중간값으로 잡아 컷이 들리지 않게 합니다.

## 사용하는 모델

| 단계 | 사용 |
|---|---|
| 나레이션 | Gemini TTS (clone-voice 로컬 허브 경유) — 약 $0.03/분 |
| 타임스탬프 | MLX Whisper large-v3-turbo — 로컬, 무료 |
| 이미지 | GPT Image 2 (Codex CLI 내장 생성, ChatGPT 구독) |
| 영상 | Gemini Omni Flash (`gemini-omni-flash-preview`) |
| 영상(공인 등장 시) | Seedance 2.0 Fast (Kie.ai) — 첫 프레임 방식 |

## 스타일 시스템

모든 이미지는 **마스터 스타일 시트 한 장**을 재료로 삼아 생성됩니다. 시트는
팔레트·질감·타이포·컴포넌트·모션을 한 판에 정의한 아트디렉션 보드입니다.

```
styles/<이름>/     스타일 원본 (DNA·프롬프트·시트·NOTES)
assets/            현재 활성 스타일 한 벌 + ACTIVE_STYLE
output/<영상>/     영상별 산출물 + 사용한 스타일 기록
```

스타일 전환은 파일 복사 두 줄입니다:

```bash
cp styles/<스타일명>/style_reference.png assets/style_reference.png
echo "<스타일명>" > assets/ACTIVE_STYLE
```

### 스타일 역설계 (`/style-sheet`)

레퍼런스 이미지를 넣으면 **11슬롯 스타일 DNA**를 뽑아 시트를 생성합니다.

- 팔레트 hex는 눈대중이 아니라 **k-means로 실측**하고, 화면 점유율과 윤곽
  비율로 "주조색 vs 선 전용 강조색"을 자동 분류합니다
- **여러 장에서 반복되는 것만** 스타일로 채택합니다. 한 장에만 있는 건 그
  이미지의 소재이지 시각 시스템이 아닙니다
- 중간 산출물인 `style_dna.json`을 사람이 검토·수정한 뒤 시트를 렌더합니다

## 환경 의존성

이 저장소를 그대로 돌리려면 다음이 필요합니다.

- **macOS + Apple Silicon** (MLX Whisper)
- **ffmpeg**
- **Python 3.13** + `requirements.txt`
- **Codex CLI** + ChatGPT 구독 로그인 (이미지 생성)
- **clone-voice TTS 백엔드** — 외장 SSD에 설치된 로컬 웹앱을 자동 기동합니다.
  경로가 `scripts/ensure_tts.sh`에 하드코딩되어 있으니 환경에 맞게 고쳐야 합니다
- **API 키**: `.env.example`을 `.env`로 복사해 채웁니다

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env    # 키 입력
```

## 저장소에 포함하지 않는 것

- `.env` (API 키)
- `output/` (생성된 영상·이미지·음성)
- `refs/`, `styles/*/refs/` — **스타일 분석에 쓴 레퍼런스 이미지는 제3자
  콘텐츠라 커밋하지 않습니다.** 저장소에는 그로부터 도출한 DNA와 프롬프트,
  그리고 직접 생성한 시트만 있습니다
- `music/` (배경음악 파일)

## 문서

- [`PROGRESS.md`](PROGRESS.md) — 진행 기록과 설계 결정의 이유
- [`TODO.md`](TODO.md) — 백로그
- `styles/*/NOTES.md` — 스타일별 출처·팔레트·주의사항
