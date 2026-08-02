# Flow 브라우저 제출 절차

Omni를 Gemini API 종량제 대신 **Google Flow 구독**으로 돌릴 때의 절차다.
80초 이상 영상처럼 API 비용이 부담될 때 쓴다.

출처: `26_vox_style_video`의 `flow-omni-browser` 스킬에서 조작 방법만 가져와
우리 파이프라인(클립당 이미지 **1장**)에 맞춘 것이다. 저쪽의 first/end 2장
방식, scene-plan/cuts.json, Remotion 연동은 가져오지 않는다.

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
파일명, 설정이 같은 작업을 묶은 `submission_order`가 들어 있다.

## 1. 입력 경로 결정 — 먼저 시험한다

Slate 편집기에 정확히 입력할 수 있는지가 이 절차의 성패를 가른다. **추측하지
말고 버리는 문자열로 먼저 시험한다.** 크레딧은 들지 않는다.

1. Flow 프롬프트 입력창에 `abc123` 을 입력해 본다.
2. 실제 값을 읽어 대조한다.

```javascript
document.querySelector('[data-slate-editor="true"]').innerText
```

3. `abc123` 과 **정확히** 같고 생성 버튼이 활성화되면 그 경로를 쓴다.
   다르거나 안내 문구가 섞이면 그 경로를 버린다.
4. 시험 후 `Meta+A` → `Backspace` 로 비운다.

### 경로 A — claude-in-chrome (기본)

사용자의 실제 로그인 Chrome을 그대로 쓴다. 확장 연결이 필요하다
(<https://claude.ai/chrome> 설치 후 Chrome 재시작, flow.google 사이트 권한 허용).

- `tabs_context_mcp` → `navigate` 로 Flow 탭 하나를 잡고 끝까지 재사용한다.
- 입력은 `computer` 의 `type` 을 쓰되 **반드시 위 시험을 통과한 뒤에만** 쓴다.
  26번 프로젝트는 Chrome CUA 일괄 입력이 실패했다고 기록했다. 우리 확장은
  구현이 다르므로 될 수도 있지만, 확인 전에는 실제 프롬프트를 넣지 않는다.
- 이미지 첨부는 `find` 로 file input을 찾아 `file_upload` 에 `upload_path` 를
  넘긴다. **파일 선택 버튼을 클릭하지 않는다** — OS 파일 선택창이 열리면
  제어할 수 없다.
- 상태 확인은 `read_page` 또는 `javascript_tool` 로 현재 카드만 읽는다.

### 경로 B — Codex Chrome 플러그인 (폴백)

경로 A의 시험이 실패하면 이쪽을 쓴다. 26번에서 **2,416자를 38ms에 정확히
입력**한 실측 경로다.

- Codex의 Chrome 확장이 탭 단위 Playwright 핸들(`flowTab.playwright`)을 준다.
- 입력은 **첫 글자 `press` + 나머지 `type`** 혼합 방식이 기본이다.

```javascript
const slate = flowTab.playwright.locator('[data-slate-editor="true"]');
if (await slate.count() !== 1) throw new Error("Slate 카운트 불일치");
await slate.click();
await slate.press(prompt[0]);
await slate.type(prompt.slice(1));
```

- 혼합 입력이 전문 일치나 버튼 활성화를 통과하지 못할 때만 문자별 `press`로
  **한 번** 폴백한다.
- 로컬 파일 업로드 전에 Codex Chrome 확장의 `Allow access to file URLs`를
  확인한다. 파일 선택기가 멈췄다는 사실만으로 권한이 꺼졌다고 단정하지 않는다.

두 경로 모두 **같은 `jobs.json` / `state.json`** 을 쓰므로, 중간에 경로를
바꿔도 진행 상태가 이어진다.

## 2. 설정 확인 (제출 직전, 매번)

Flow UI는 바뀐다. 좌표나 버튼 순서를 고정하지 말고 **현재 화면을 읽어**
다음이 실제로 맞는지 본다.

| 항목 | 값 |
|---|---|
| 미디어 | 동영상 |
| 입력 모드 | 애셋 |
| 비율 | 9:16 (가로 스타일이면 16:9) |
| 모델 | Omni Flash |
| 길이 | job의 `provider_duration_sec` (4 또는 6) |
| 출력 수 | x1 |

설정 버튼 이름은 `동영상 · {duration}s crop_9_16 x1` 형태다. 매니페스트 값과
화면이 다르면 **제출하지 않는다.**

`submission_order`대로 처리하면 같은 길이끼리 묶여 설정 변경이 줄어든다.

## 3. 애셋 첨부

우리 파이프라인은 클립당 이미지 **한 장**이다.

1. 입력창이 비어 있는지 확인한다.
2. `add_2 만들기` 버튼을 연다.
3. `jobs.json`의 `image.upload_path` 파일 하나를 올린다.
4. `프롬프트에 추가` 후 첨부가 실제로 화면에 뜰 때까지 기다린다.
5. **첨부 수가 정확히 1인지 확인한다.**

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

## 8. 재개

중단되면 같은 `jobs.json`과 `state.json`을 다시 읽고 현재 단계부터 잇는다.

- `downloaded` 이상이면 그 클립은 건너뛴다.
- `completed` 면 다운로드부터 재개한다.
- `generating` 이면 edit ID로 카드를 찾아 상태만 다시 읽는다. **다시 제출하지
  않는다.**
- `submitted` 이하면 화면을 새로 검증하고 이어간다.

프롬프트나 이미지가 바뀌면 fingerprint가 달라져 준비 스크립트가 덮어쓰기를
거부한다. 그때는 `--run-name run-v02` 로 새로 준비한다.
