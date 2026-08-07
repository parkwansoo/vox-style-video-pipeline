# Flow 브라우저 제출 절차

Omni를 Gemini API 종량제 대신 **Google Flow 구독**으로 돌릴 때의 절차다.
80초 이상 영상처럼 API 비용이 부담될 때 쓴다.

출처: `26_vox_style_video`의 `flow-omni-browser` 스킬에서 조작 방법만 가져온
것이다. 저쪽의 scene-plan/cuts.json, Remotion 연동은 가져오지 않는다.

클립당 이미지는 **1장 또는 2장**이다. 앞 클립의 마지막 프레임에서 이어지는
연결 컷을 만들 때는 첫 프레임·끝 프레임 2장을 쓴다
(`prepare_flow_jobs.py`가 `clip<N>_first.png`+`clip<N>_end.png` 존재로 판별한다).

## 절대 금지 (실측으로 확인된 실패 원인)

- **`Enter`·`Shift+Enter`를 절대 보내지 않는다.** Enter는 즉시 제출되고
  Shift+Enter는 zero-width 문자를 남긴다.
- **클립보드 붙여넣기, DOM `fill`, 값 주입을 쓰지 않는다.** Slate 편집기는
  이런 입력을 무시하거나 안내 문구·BOM을 섞고 생성 버튼을 비활성으로 둔다.
- **프롬프트 전문을 도구 출력에 다시 찍지 않는다.** 길이와 SHA만 기록한다.
- **생성 중 새로고침하지 않는다.** 15초 간격으로 현재 카드만 다시 읽는다.
- **한 작업당 생성 버튼은 정확히 한 번**. 더블클릭 금지.
- 사용자 승인 없이 실패 카드를 삭제하거나 자동 재생성하지 않는다.

## 0. 준비

```bash
.venv/bin/python3 .claude/skills/vox-video/scripts/prepare_flow_jobs.py \
  --run output/<run> --chapter 1 \
  --clip 1:6 2:6 3:6 4:6 5:4 6:4 7:4 8:4 9:4 --run-name run-v01

.venv/bin/python3 .claude/skills/vox-video/scripts/flow_state.py init \
  --jobs output/<run>/flow-browser-runs/run-v01/jobs.json
```

`jobs.json`에는 한 줄로 정규화된 프롬프트, 이미지 SHA-256, 업로드용 고유
파일명, 설정이 같은 작업을 묶은 `submission_order`가 들어 있다. 각 job의
`flow_input_mode`("프레임"/"애셋")와 `asset_count`가 **화면에서 눌러야 할 입력
모드와 붙일 이미지 수**를 그대로 알려준다. stdout 요약에도 작업별로 찍힌다.

클립 번호에는 접미사를 쓸 수 있다(`--clip 1b:4`). 기존 클립 사이에 컷을 끼울 때
뒤 번호를 전부 밀지 않아도 된다.

## 1. 입력 경로 — claude-in-chrome (2026-08-02 실측 검증)

**MCP 도구를 쓰기 전에 `claude-in-chrome` 스킬을 먼저 호출한다.** 이걸 빼면
확장이 연결되지 않는다.

`tabs_context_mcp` → `navigate` 로 Flow 탭 하나를 잡고 끝까지 재사용한다.

**입력은 `computer` 의 `type` 을 그대로 쓴다.** 실측 결과 1,520자 프롬프트가
SHA-256까지 정확히 일치했고 줄바꿈·BOM 오염이 없었으며 생성 버튼도 활성화됐다.

> 26번 프로젝트는 "Chrome CUA 일괄 입력 실패"를 기록했지만 그건 **Codex 확장**
> 이야기다. claude-in-chrome은 깨끗하게 들어간다. 다만 Flow UI는 바뀌므로,
> 아래 회귀 시험은 매 작업 시작 때 한 번 돌린다.

### 회귀 시험 (크레딧 0원, 매번)

1. 입력창을 클릭해 포커스를 준 뒤 `abc123` 을 입력한다. 클릭 없이 `type` 하면
   아무 데도 들어가지 않는다(`document.activeElement` 가 null이면 실패다).
2. 실제 값을 읽어 대조한다. **`﻿`(BOM)·zero-width와 안내 문구를 걷어낸 뒤**
   비교해야 한다 — Slate는 빈 노드 표시에 저 문자들을 쓰고, 안내 문구
   "무엇을 만들고 싶으신가요?"는 **비어 있을 때 innerText에 그대로 섞여 나온다**.

```javascript
document.querySelector('[data-slate-editor="true"]')
  .innerText.replace(/[﻿​]/g, '').replace('무엇을 만들고 싶으신가요?', '').trim()
```

3. 정확히 `abc123` 이고 생성 버튼이 활성이면 통과다.
4. `cmd+a` → 이어서 실제 프롬프트를 입력하면 덮어써진다.

### 폴백 — Codex Chrome 플러그인

claude-in-chrome이 연결되지 않거나 회귀 시험이 깨질 때만 쓴다. 26번에서
2,416자를 38ms에 입력한 경로이며, 첫 글자 `press` + 나머지 `type` 혼합 방식이다.

```javascript
const slate = flowTab.playwright.locator('[data-slate-editor="true"]');
await slate.press(prompt[0]);
await slate.type(prompt.slice(1));
```

두 경로 모두 **같은 `jobs.json` / `state.json`** 을 쓰므로 중간에 바꿔도 진행이
이어진다.

## 2. 설정 확인 (제출 직전, 매번)

Flow UI는 바뀐다. 좌표나 버튼 순서를 고정하지 말고 **현재 화면을 읽어**
다음이 실제로 맞는지 본다.

설정 버튼(`동영상 · {duration}s crop_9_16 x1`)을 눌러 팝업을 연다. 실측 확인된
선택지는 다음과 같다.

| 항목 | 선택지 | 우리 값 |
|---|---|---|
| 미디어 | 이미지 / **동영상** | 동영상 |
| 입력 모드 | 프레임 / 애셋 | **job의 `flow_input_mode`** — 아래 표 참고 |
| 비율 | **9:16** / 16:9 | 스타일에 맞춰 |
| 모델 | 드롭다운 | **Omni Flash** (항상) |
| 길이 | **4s / 6s** / 8s / 10s | job의 `provider_duration_sec` |
| 출력 수 | **x1** / x2 / x3 / x4 | x1 |

### 입력 모드는 이미지 장수로 갈린다 (2026-08-06 실측)

| 이미지 | Flow 입력 모드 | 붙이는 곳 | job 필드 |
|---|---|---|---|
| **1장** (`clip<N>.png`) | **프레임** | 시작 슬롯에만 | `flow_input_mode: "프레임"` |
| **2장** (`clip<N>_first.png` + `clip<N>_end.png`) | **애셋** | 애셋으로 first → end 순서 | `flow_input_mode: "애셋"` |

`prepare_flow_jobs.py`가 파일 존재로 판별해 `flow_input_mode`에 **화면 라벨을
그대로** 넣어 둔다. 그 값을 보고 누르면 되고, 장수와 모드를 머리로 매칭하지
않는다. 모델은 두 경우 모두 **Omni Flash**다.

**왜 2장이 "프레임"이 아니라 "애셋"인가.** 이름만 보면 첫·끝 두 장은 프레임
모드처럼 보이지만 **그쪽 종료 슬롯은 Veo 전용**이다. 프레임 모드에서 종료
슬롯에 이미지를 넣으면 Omni Flash일 때 썸네일이 회색으로 바뀌며 "이 모델은
종료 프레임을 지원하지 않습니다" 경고가 뜬다. 모델을 Veo 3.1로 바꾸면 경고는
사라지지만 **길이 선택이 사라지고 크레딧이 7 → 20으로 오른다**(4s 기준) — 우리
기준으로는 오답이다. Omni Flash + 애셋 모드에 두 장을 순서대로 붙이면 경고 없이
첫·끝 프레임으로 동작하고 길이·크레딧도 그대로다.

**크레딧이 팝업 하단에 표시된다** ("생성 시 N크레딧이 사용됩니다"). 실측값:

| 길이 | 크레딧 |
|---|---|
| 4s | 7 |
| 6s | 10 |
| 10s | 15 |

9클립(6s×4 + 4s×5) 영상 한 편이면 **75크레딧**이다.

매니페스트 값과 화면이 다르면 **제출하지 않는다.** `submission_order`대로
처리하면 같은 길이끼리 묶여 설정 변경이 줄어든다.

## 3. 이미지 첨부

job의 `images` 배열에 있는 만큼 붙인다. 어디에 붙일지는 `flow_input_mode`가
정한다(2절 표).

1. 입력창이 비어 있는지 확인한다.
2. `find` 로 페이지의 file input(`ref`)을 찾아 `file_upload` 에 `upload_path`
   를 넘긴다. **파일 선택 버튼을 클릭하지 않는다** — OS 파일 선택창이 열리면
   제어할 수 없다. 업로드는 먼저 미디어 라이브러리로 들어간다. 2장이면
   `paths` 에 한 번에 넘겨도 되고, 업로드는 수십 초 걸리므로 퍼센트가 사라질
   때까지 기다린다.
3. 선택창을 연다.
   - **프레임 모드(1장)**: 입력창 위의 **`시작`** 슬롯을 누른다. 종료 슬롯은
     비워 둔다 — Omni는 종료 프레임을 받지 않는다.
   - **애셋 모드(2장)**: 입력창의 `add_2 만들기`(+) 버튼을 누른다.
4. 방금 올린 이미지를 고르고 **`프롬프트에 추가`** 를 누른다. 애셋 모드는 이
   과정을 **first → end 순서로** 두 번 반복한다. 선택창의 목록은 **최신 업로드가
   위**라 순서가 뒤집혀 보이므로, 파일명을 `find` 로 읽어 역할을 확인하고 고른다
   (목록 라벨은 잘려 나온다).
5. **첨부 수가 job의 `asset_count` 와 같은지 확인한다** (입력창 안 썸네일 개수).
   썸네일에 경고 아이콘이 뜨면 모드·모델 조합이 틀린 것이다. 2절로 돌아간다.

같은 SHA의 이미지가 Flow 라이브러리에 이미 있으면 재업로드하지 않고
`state.json`의 `asset_cache`에 기록해 재사용한다.

```bash
flow_state.py set --jobs <jobs.json> --job ch1-clip1 --stage assets-attached
```

## 4. 프롬프트 입력과 검증

경로 A/B 중 시험을 통과한 방식으로 `prompt_single_line`을 넣는다. 요약·번역·
재작성하지 않는다. 그리고 **세 가지를 모두** 확인한다.

- 입력창 실제 텍스트 == `prompt_single_line` (완전 일치)
- 첨부 수 == 1
- 생성 버튼 활성화

하나라도 어긋나면 `Meta+A` → `Backspace` 로 비우고 다시 넣는다. 두 번 실패하면
반대 경로로 바꾼다.

```bash
flow_state.py set --jobs <jobs.json> --job ch1-clip1 --stage prompt-ready
```

## 5. 제출 (사용자 승인 필요)

**화면에 표시된 크레딧을 사용자에게 그대로 보고하고 승인을 받은 뒤에만**
생성 버튼을 누른다. 크레딧 표시가 없거나 불명확하면 제출하지 않는다.

첫 작업은 **1개만** 제출한다. 정상 완료를 확인한 뒤에야 동시 2개를 허용한다.
`flow_state.py next` 가 이 규칙을 강제하므로 그 결과만 따른다.

```bash
flow_state.py set --jobs <jobs.json> --job ch1-clip1 --stage submitted
```

제출 직후 프롬프트와 첨부가 입력창에서 사라지는 것은 정상이다. 프로젝트
카드에서 새 edit ID를 찾아 기록한다.

```bash
flow_state.py set --jobs <jobs.json> --job ch1-clip1 --stage generating --edit-id <edit-id>
```

## 6. 진행 상태 판독

- **퍼센트가 오르면 생성 중이다.** 실패로 판정하지 않는다.
- 썸네일과 edit 링크가 보이면 완료다.
- **다른 카드의 실패 문구를 현재 작업 상태로 읽지 않는다.** 반드시 이번
  edit ID의 카드만 본다.
- 15초 간격으로 폴링한다. 새로고침하지 않는다.

```bash
flow_state.py set --jobs <jobs.json> --job ch1-clip1 --stage completed
```

## 7. 다운로드와 연결

완료 edit에서 원본 MP4를 한 번만 내려받는다. 파일명이 불명확하면 다운로드
전후의 디렉터리 목록 차이로 새 파일을 찾는다.

내려받은 파일을 우리 파이프라인의 표준 위치로 복사한다. **원본은 옮기거나
지우지 않는다.**

```bash
cp <다운로드 파일> output/<run>/ch1/clip1.mp4
flow_state.py set --jobs <jobs.json> --job ch1-clip1 --stage downloaded --download <경로>
```

이후 길이·해상도·비율을 기계 점검한다. Flow는 4/6/8초를 주므로 우리가 요청한
길이와 맞는지 반드시 확인한다. **길이가 다르면 합본의 실효 길이 계산
(4초→3.75s, 6초→5.75s)이 깨진다.**

```bash
ffprobe -v error -show_entries format=duration -show_entries stream=width,height \
  -of default=nw=1 output/<run>/ch1/clip1.mp4
```

이 지점부터는 기존 합본 절차(SKILL.md 7단계)가 그대로 이어진다. `assemble.py`는
mp4가 어디서 왔는지 신경 쓰지 않는다.

**단, 합본 뒤 워터마크를 지운다.** Flow는 Pro에서도 워터마크를 끌 수 없어
우하단 안쪽에 4각별이 박혀 나온다. 합본 뒤·자막 앞에 한 번만 돌린다
(SKILL.md 7.2 — `remove_flow_watermark.py`). 이 절차로 만든 클립이 한 편에
하나라도 섞여 있으면 필수다.

## 8. 재개

중단되면 같은 `jobs.json`과 `state.json`을 다시 읽고 현재 단계부터 잇는다.

- `downloaded` 이상이면 그 클립은 건너뛴다.
- `completed` 면 다운로드부터 재개한다.
- `generating` 이면 edit ID로 카드를 찾아 상태만 다시 읽는다. **다시 제출하지
  않는다.**
- `submitted` 이하면 화면을 새로 검증하고 이어간다.

프롬프트나 이미지가 바뀌면 fingerprint가 달라져 준비 스크립트가 덮어쓰기를
거부한다. 그때는 `--run-name run-v02` 로 새로 준비한다.
