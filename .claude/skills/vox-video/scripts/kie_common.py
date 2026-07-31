"""Shared Kie.ai client: task creation, polling, file upload, download.

All three models (gemini-omni-video, bytedance/seedance-2-fast,
gpt-image-2-image-to-image) use the unified Jobs API:
  POST https://api.kie.ai/api/v1/jobs/createTask
  GET  https://api.kie.ai/api/v1/jobs/recordInfo?taskId=...
Input images must be publicly reachable URLs; local files are hosted
temporarily via the free upload API at kieai.redpandaai.co.
"""
import base64
import json
import mimetypes
import os
import sys
import time

import requests

API_BASE = "https://api.kie.ai/api/v1"
UPLOAD_BASE = "https://kieai.redpandaai.co"


class KieError(RuntimeError):
    pass


def _key():
    key = os.environ.get("KIE_API_KEY", "").strip()
    if not key:
        raise KieError("KIE_API_KEY가 비어 있습니다. 프로젝트 루트의 .env에 키를 입력하세요.")
    return key


def _headers():
    return {"Authorization": f"Bearer {_key()}", "Content-Type": "application/json"}


def _check_http(r):
    if r.status_code == 402:
        raise KieError("Kie.ai 크레딧 부족(402). https://kie.ai 에서 충전 후 다시 시도하세요.")
    if r.status_code == 401:
        raise KieError("Kie.ai API 키가 유효하지 않습니다(401). .env의 KIE_API_KEY를 확인하세요.")
    if r.status_code != 200:
        raise KieError(f"HTTP {r.status_code}: {r.text[:500]}")


def upload_file(path):
    """Upload a local file, return a public downloadUrl (temp hosting, ~3 days)."""
    mime = mimetypes.guess_type(path)[0] or "application/octet-stream"
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    r = requests.post(
        f"{UPLOAD_BASE}/api/file-base64-upload",
        headers=_headers(),
        json={
            "base64Data": f"data:{mime};base64,{b64}",
            "uploadPath": "vox-video",
            "fileName": os.path.basename(path),
        },
        timeout=180,
    )
    _check_http(r)
    data = r.json()
    if data.get("code") != 200:
        raise KieError(f"파일 업로드 실패: {data}")
    return data["data"]["downloadUrl"]


def create_task(model, input_payload):
    r = requests.post(
        f"{API_BASE}/jobs/createTask",
        headers=_headers(),
        json={"model": model, "input": input_payload},
        timeout=60,
    )
    _check_http(r)
    data = r.json()
    if data.get("code") != 200:
        raise KieError(f"createTask 실패: {data}")
    return data["data"]["taskId"]


def poll_task(task_id, timeout=900, interval=10):
    """Poll until success/fail. Returns resultUrls list."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        r = requests.get(
            f"{API_BASE}/jobs/recordInfo",
            headers=_headers(),
            params={"taskId": task_id},
            timeout=60,
        )
        _check_http(r)
        data = r.json().get("data") or {}
        state = data.get("state")
        if state == "success":
            # resultJson is a JSON *string* — parse it once more
            return json.loads(data["resultJson"])["resultUrls"]
        if state == "fail":
            raise KieError(
                f"생성 실패 (taskId={task_id}): {data.get('failCode')} {data.get('failMsg')}"
            )
        time.sleep(interval)
    raise KieError(f"폴링 타임아웃 (taskId={task_id}, {timeout}s)")


def download(url, dest):
    r = requests.get(url, stream=True, timeout=600)
    r.raise_for_status()
    parent = os.path.dirname(os.path.abspath(dest))
    os.makedirs(parent, exist_ok=True)
    with open(dest, "wb") as f:
        for chunk in r.iter_content(1 << 16):
            f.write(chunk)
    return dest


def generate(model, input_payload, out_path, retries=1, timeout=900):
    """createTask → poll → download, retrying once on generation failure."""
    last = None
    for attempt in range(retries + 1):
        try:
            task_id = create_task(model, input_payload)
            print(f"[kie] {model} taskId={task_id} (시도 {attempt + 1})", file=sys.stderr)
            urls = poll_task(task_id, timeout=timeout)
            return download(urls[0], out_path)
        except KieError as e:
            last = e
            msg = str(e)
            # 크레딧/키 문제는 재시도해도 소용없음
            if "402" in msg or "401" in msg or "크레딧" in msg or "유효하지" in msg:
                raise
            print(f"[kie] 실패: {e}", file=sys.stderr)
    raise last
