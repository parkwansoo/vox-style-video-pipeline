# 백로그

## 대기

- [ ] 2026-08-01 클립 자체 오디오 볼륨(0.2) 청감 튜닝 — 첫 실전작에서 효과음이 잘 들리는지 확인 필요 — assemble.py
- [ ] 2026-08-01 SKILL.md 2단계에 "대본 32초/7문장 = 7클립" 가이드 반영 (37.8초→10클립 초과 사례) — SKILL.md
- [ ] 2026-08-01 music/ 에 배경음악 mp3 추가 (현재 0곡이라 음악 없이 합본됨)
- [ ] 2026-08-01 Gemini TTS 한국어 보이스 청감 비교 (**기본은 Charon**, 후보 30종) 후 기본값 확정 — .env `VOX_TTS_VOICE` 또는 `tts.py --voice`. 목록은 `tts.py --list-voices`로 확인 (백엔드에 프리셋 등록된 것만 사용 가능). ※2026-08-03 정정: 기존 기록의 "Kore 기본 / GEMINI_TTS_VOICE"는 v0.3.0에서 clone-voice 백엔드로 갈아타기 전 정보라 실제와 달랐다
- [ ] 2026-08-01 폴링 대신 callBackUrl 웹훅 방식 검토 (대량 생성 시 효율) — scripts/kie_common.py
- [ ] 2026-08-01 music/ 비어 있을 때 BGM 자동 생성 옵션 검토 (예: ElevenLabs Music API, Lyria 등) — assemble 단계
- [ ] 2026-08-01 대본에 아라비아 숫자 표기 시 ASR 정규화 불일치("이십 퍼센트"↔"20%")로 정렬률 하락 — 대본 작성 규칙에 숫자 한글 표기 지침 추가 검토 — SKILL.md 2단계

- [x] 2026-08-02 mg-bodylab NOTES.md에 권장 배속 1.3 기록 (완료 섹션으로 이동)
- [ ] 2026-08-02 피부 색소질환 묘사 프롬프트 정답을 pipeline-rules.md에 정리 — 점(주근깨)도 단일 덩어리(마스크)도 아닌 "크기 제각각 불규칙 얼룩 여러 개 + 갈색 명시"가 정답 (PROGRESS.md 2026-08-02 표 참조) — references/pipeline-rules.md
- [ ] 2026-08-02 인물 지정 규칙 명문화 — "adult woman"은 서구 패션모델로 나옴. 국적·연령·헤어·"not a fashion model"까지 써야 함 — references/pipeline-rules.md
- [ ] 2026-08-02 **검토 정지점 2곳(대본·이미지) 제거하고 완전 자동으로 되돌리기** — 대본·이미지 품질이 안정되면. 도입 이유는 아직 한 번에 통과하지 못하기 때문 — SKILL.md "검토 정지점" 절
- [x] 2026-08-02 이미지·영상 생성은 항상 백그라운드 실행 — SKILL.md 5단계에 반영
- [ ] 2026-08-02 인물 이미지 착의 규칙을 pipeline-rules.md에 명문화 — 전신은 나체로 나오고, AVOID에 nudity류 단어를 넣으면 생성 거부됨. 흉상+긍정문 착의 지정이 정답 — references/pipeline-rules.md
- [ ] 2026-08-02 자막·타이틀 등 정보 레이어를 HyperFrames(HeyGen 오픈소스, HTML→MP4) 또는 Remotion으로 얹는 방안 검토 — 생성 모델은 텍스트 오탈자에 취약하지만 HTML은 오탈자가 원천적으로 없다. 생성 클립 위에 덧씌우는 용도이지 장면 생성 대체는 아님 — assemble 단계
- [ ] 2026-08-02 광고 영상의 표현 제약 정리 — 브이지샷 제품 프로필은 "진피층 도달/흡수"를 의약품 오인 표현으로 금지하고 "각질층을 열어 속기미 뿌리까지 전달"을 안전 표현으로 지정한다. 그런데 시리즈1은 색소가 진피로 떨어진다는 서사라 광고 편에서 충돌한다. 이번(20260802-melasma-vgshot)은 사용자 지시로 그대로 진행했고, 추후 개선 논의 때 다시 꺼낸다
- [ ] 2026-08-02 mg-bodylab 스타일 자막(캡션) 사용 여부 결정 — 스타일 시그니처지만 한국어 나레이션과 언어가 어긋나고 오탈자 위험
- [ ] 2026-08-03 **제품 클로즈업 컷은 영상 프롬프트에도 라벨 문구를 반복한다** — ch2-clip6(CTA)에서 push-in 중 라벨이 `VO SHOT`/`50 ml`로 변형됐다. 같은 제품 고정 문구를 쓴 clip1·5는 멀쩡했고 차이는 카메라가 라벨로 접근하는지 여부였다. 이미지 프롬프트에만 라벨을 쓰면 영상화에서 무너진다 — references/pipeline-rules.md
- [ ] 2026-08-03 flow-browser.md에 실전 발견 7가지 반영 — 편집화면 다운로드 아이콘 1클릭, 애셋 검색으로 선택, 창 크기 변동, 실패 재시도(무과금), JS 45초 CDP 타임아웃, 완료 판정 기준, 업로드 경로 제약. 상세는 PROGRESS.md 2026-08-03 표 — references/flow-browser.md
- [ ] 2026-08-03 Flow 워터마크 대응 검토 — Pro 구독은 Visible watermarking을 못 끈다. 광고 용도면 후처리 제거나 자막·타이틀 레이어로 가리는 방안이 필요 — assemble 단계
- [ ] 2026-08-03 prepare_flow_jobs.py 챕터별 경로 분리를 flow-browser.md 예시에 반영 — 출력이 `run-v01/ch<N>/jobs.json`으로 바뀌었다 (커밋 참조) — references/flow-browser.md
- [ ] 2026-08-03 이미지 생성 시간이 프롬프트 길이에 비례하는지 검증 — 실측: 첨부1장·1.4k자 약 1분 / 첨부2장·3.0k자 4~7분 / 첨부2장·4.1k자 3분29초(재시도 3회는 7분 타임아웃). AVOID에 금지구를 덧붙일수록 길어지므로 중복 정리 기준이 필요 — scripts/gen_image.py, references/pipeline-rules.md
- [ ] 2026-08-03 **무음 압축 기본값(sentence 0.45/0.25/0.20) 청감 확인** — 수치는 실측 근거가 있지만 귀로는 아직 검증 안 됨. `output/20260802-melasma-vgshot/test-audio/`의 sentence/tight/uniform 3종 비교. 어색하면 `--silence-sentence` 등으로 조정 — scripts/compress_silence.py PRESETS
- [ ] 2026-08-03 무음 압축을 실제 TTS 합성 경로로 E2E 검증 — 지금까지는 기존 나레이션으로 2패스 흐름만 재현했다(합성 단계 제외, 과금 회피). 다음 영상 제작 때 자연히 검증되며 `silence_compression` 요약을 확인하면 된다 — scripts/tts.py
- [ ] 2026-08-03 컷별 배속 지원을 assemble.py에 추가할지 결정 — 순서 변경만으로 대부분 해결되므로 후순위. 필요하면 manifest clip에 선택적 `rate` 필드(없으면 1.0). `setpts`는 프레임을 버리므로(1.886x에서 48% 드롭) 1.4x 이상 쓸 거면 `minterpolate` 동반 필요 — scripts/assemble.py
- [ ] 2026-08-03 보이스·TTS배속 변경 시 무음 패턴 재검증 — 측정은 전부 Kore/1.3배속 기준. 정렬률 안전 마진은 크다(1.0/0.91) — TODO 8번과 함께 처리
- [ ] 2026-08-03 seg 경계 규칙 재검토 (우선순위 하락) — `SKILL.md`의 "앞뒤 단어의 중간값"이 뒤 패딩을 만들었으나(압축 전 7.50s), 무음 압축이 들어가 무음 자체가 짧아졌으므로 영향이 작아졌다. 더 조이려면 `seg_end = 마지막 단어 end + 0.15` — SKILL.md 4단계
- [ ] 2026-08-01 style-sheet: 영상 레퍼런스(mp4) 입력 지원 검토 — 현재 모션 시그니처는 정지 이미지 추론이라 confidence low — .claude/skills/style-sheet/
- [ ] 2026-08-01 style-sheet: k-means가 종이 톤 그라데이션을 여러 색으로 쪼개는 문제 — 색상환 거리 기반 자동 병합 검토 — scripts/extract_palette.py

## 완료

- [x] 2026-08-03 **나레이션 무음 압축을 tts.py의 ASR 직전에 도입** (132cab4) — 3영상 모두 실발화 55~57%/무음 27~32%인 TTS 구조 문제. `compress_silence.py` 신설, 프리셋 sentence(기본)/tight. `words.json`이 압축 기준이 되어 뒤 단계 무변경, 배속이 불필요해졌다
- [x] 2026-08-03 무음 압축은 대본 기반 문장 경계 판정으로 구현 (균일 클램프 금지) — 길이로는 못 가른다(경계·내부가 똑같이 0.59s). 그래서 정렬을 두 번 돈다. auto-editor도 볼륨 임계값이라 문장 경계를 모르는 게 도구를 안 쓴 결정적 이유
- [x] 2026-08-03 SKILL.md 대본 분량표 실측 반영 — 압축 후 1.0배속 0.194초/음절, 1.3배속 0.167초/음절. 완성 30초 = 대본 125~140(1.0) / 145~165음절(1.3). NOTES.md도 갱신
- [x] 2026-08-03 회수한 시간의 용처 결정 — "영상을 짧게" 채택 (52.02s→43.96s, 15.5%). 대사 추가 안은 보류
- [x] 2026-08-03 words.json은 무음 탐지에 못 쓴다는 점 명문화 — `compress_silence.py` 모듈 docstring에 기록 (보간이 무음을 앞 단어 end에 흡수시켜 gap이 2.82s로만 잡힌다. 파형을 `silencedetect`로 재야 한다)
- [x] 2026-08-03 Remotion 도입 검토 → 보류 — `playbackRate`가 프레임 매핑일 뿐 보간을 안 해 `setpts`와 결과 동일. 자막·워터마크 레이어(20·25번)에는 여전히 후보
- [x] 2026-08-02 gen_image.py 조용한 실패 수정 — 재생성 시 기존 파일이 남아 있으면 생성 거부돼도 성공 보고하던 문제 (mtime 검사 추가)
- [x] 2026-08-01 vox-video 스킬 v1 구축 (스크립트 6종 + 가이드라인 2종 + SKILL.md)
- [x] 2026-08-01 v0.2.0 마이그레이션: Gemini TTS + MLX Whisper 정렬, Codex 구독 OAuth 이미지 (c301957 이후)
- [x] 2026-08-01 v0.3.0 참고 프로젝트 이식: TTS→로컬 clone-voice 백엔드(20 프로젝트), 영상→Gemini API omni flash 직접(26 프로젝트). 세 경로 실생성 검증
- [x] 2026-08-01 9:16 세로 스타일 지원 (gen_image.py --aspect 추가, 영상·합본은 기존 옵션 사용)
- [x] 2026-08-01 style-sheet 스킬 구축: 레퍼런스 이미지 → 11슬롯 스타일 DNA → 마스터 시트 역설계 (템플릿 재현성 + E2E 검증 완료)
- [x] ~~ElevenLabs 기본 보이스 만료 대응~~ — ElevenLabs 제거로 불필요해짐
