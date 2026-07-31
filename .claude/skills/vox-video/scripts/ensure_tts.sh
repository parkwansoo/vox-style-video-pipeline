#!/bin/bash
# clone-voice TTS 백엔드(8930) 자동 기동 — tts.py가 음성 생성 전에 자동 호출한다.
# 외장 SSD(Samsung_T5) 연결 전제. 이미 떠 있으면 즉시 종료.
# (20_숏츠 자동화 프로젝트의 ensure-tts.sh 이식)
set -u
export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/.local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

IMG="/Volumes/Samsung_T5/AI/TTS/clonevoice.sparseimage"
VOL="/Volumes/CloneVoiceTTS"
REPO="$VOL/clone-voice"
PORT="${BACKEND_PORT:-8930}"
READY="http://127.0.0.1:${PORT}/api/voices"

ready() { curl -s -o /dev/null --max-time 3 "$READY"; }

# 1) 이미 준비돼 있으면 끝
if ready; then echo "TTS 준비됨(${PORT}) — 이미 실행 중"; exit 0; fi

# 2) SSD/이미지 확인
if [ ! -f "$IMG" ]; then
  echo "SSD_NOT_CONNECTED: 외장 SSD(Samsung_T5)가 연결돼 있지 않습니다. 연결 후 다시 시도하세요."
  exit 2
fi

# 3) 이미지 마운트(안 돼 있으면)
if [ ! -d "$VOL" ]; then
  echo "디스크 이미지 마운트 중..."
  hdiutil attach "$IMG" >/dev/null || { echo "MOUNT_FAILED: 이미지 마운트 실패"; exit 3; }
fi
[ -d "$REPO" ] || { echo "REPO_MISSING: $REPO"; exit 3; }

# 4) 백엔드 기동(브라우저 없이, detached)
cd "$REPO" || exit 3
# shellcheck disable=SC1091
source .tts-env.sh >/dev/null 2>&1
LOG="$REPO/.tts-backend.log"
echo "백엔드 기동(uvicorn ${PORT})… 로그: $LOG"
nohup make dev-backend >"$LOG" 2>&1 &
disown 2>/dev/null || true

# 5) 준비 대기(첫 기동은 모델 로드로 느릴 수 있어 최대 ~120초)
for i in $(seq 1 60); do
  sleep 2
  if ready; then echo "TTS 준비 완료(${PORT}) — ${i}회 폴링(약 $((i*2))초)"; exit 0; fi
done
echo "TTS_TIMEOUT: ${PORT}이 시간 내 준비되지 않음. 로그 확인: $LOG"
exit 4
