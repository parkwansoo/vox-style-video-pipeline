#!/usr/bin/env python3
"""파생 자산이 원천보다 낡지 않았는지 검사한다 — 재생성 후 갱신 누락 방어.

두 가지를 잡는다 (전부 2026-08-25 실측 사고 기반):

1) 패딩본 낡음: clip<N>[_first|_end].png 를 새로 만들고 clip<N>p*.png 를
   다시 만들지 않은 채 제출할 뻔했다 — 유리창·갈색번짐 구버전 패딩본 4건이
   제출 직전 mtime 대조로 잡혔다. 프롬프트만 새것이면 생성은 "성공"하고
   결과만 틀리는, 실패 신호가 없는 사고다.
2) 체인 first 낡음: clip<A> 를 재생성하고 clip<B> 의 first(=A의 끝 프레임)를
   재추출하지 않았다 — clip15 재생성 후 clip16_first 가 옛 프레임으로 남아
   51.7s 지점에서 격자 크기·갈색량이 불연속으로 끊겼다. CLAUDE.md의
   "하위 자산 목록을 먼저 적는다"는 문서 규칙만으로는 안 지켜졌다.

찾기만 한다 — 삭제·재추출은 사람이 한다. 체인 명세는 편의 진행상태 문서
"체인 의존 구조" 절에서 옮겨 적는다.

Usage:
  check_freshness.py --run output/<run> [--chapter 1] \
      [--chain 5:6 7:8 8:9 14:15 15:16 17:18]
  # --chain A:B = clip<B>의 first는 clip<A> 영상보다 새것이어야 한다
"""
import argparse
import json
import re
import sys
from pathlib import Path

# 같은 작업 배치에서 만든 쌍은 mtime이 수 분 이내에 붙어 있다(실측 최대 11분).
# 체인 컷은 패딩본을 먼저 만들고 4:5를 나중에 크롭하기도 해서 방향이 역전된다 —
# 그래서 방향이 아니라 "크게 벌어졌는가"를 본다. 진짜 사고는 시간 단위였다
# (패딩본 4건 9시간, 체인 12시간). 오차 이내의 역전은 같은 배치로 본다.
MARGIN_SEC = 30 * 60


def fmt(ts):
    import datetime
    return datetime.datetime.fromtimestamp(ts).strftime("%m-%d %H:%M")


def padded_name(name):
    """clip8_end.png -> clip8p_end.png / clip17.png -> clip17p.png"""
    m = re.fullmatch(r"clip(\d+[a-z]?)((?:_first|_end)?)\.png", name)
    if not m or m.group(1).endswith("p"):
        return None  # 보존본(_v1_… 등)·패딩본 자신은 검사 대상이 아니다
    return f"clip{m.group(1)}p{m.group(2)}.png"


def chain_targets(ch, number):
    """체인 컷 B의 first 후보: clipB_first.png(2프레임) 또는 clipB.png(1프레임)."""
    for base in (f"clip{number}_first.png", f"clip{number}.png"):
        p = ch / base
        if p.is_file():
            pad = ch / padded_name(base)
            return [p] + ([pad] if pad.is_file() else [])
    return []


def load_preflight(run: Path) -> dict:
    path = run / "preflight.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"preflight.json을 읽을 수 없습니다: {path} ({exc})") from exc
    if not isinstance(data, dict):
        raise ValueError(f"preflight.json 최상위 값은 객체여야 합니다: {path}")
    return data


def validate_exceptions(raw, key: str) -> list[dict[str, str]]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ValueError(f"preflight.json의 {key}는 배열이어야 합니다")
    result = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"{key}[{index}]는 객체여야 합니다")
        missing = [name for name in ("file", "reason", "date") if not item.get(name)]
        if missing:
            raise ValueError(f"{key}[{index}] 필수 필드 없음: {', '.join(missing)}")
        result.append({name: str(item[name]) for name in ("file", "reason", "date")})
    return result


def run_freshness(run: Path, chapter: int = 1, chains=None, exceptions=None,
                  clip_numbers=None) -> list[dict[str, object]]:
    """신선도 위반 중 예외가 아닌 항목을 반환한다.

    chains/exceptions가 None이면 preflight.json에서 읽는다. clip_numbers를 주면
    해당 클립의 업로드 이미지와 관련 체인만 검사한다(WP2 제출 게이트용).
    """
    run = Path(run)
    preflight = load_preflight(run)
    if chains is None:
        chains = preflight.get("chains", [])
    if exceptions is None:
        exceptions = preflight.get("freshness_exceptions", [])
    if not isinstance(chains, list):
        raise ValueError("preflight.json의 chains는 배열이어야 합니다")
    exceptions = validate_exceptions(exceptions, "freshness_exceptions")
    selected = {str(number) for number in clip_numbers} if clip_numbers is not None else None
    if selected is not None:
        # 부분 제출 게이트에서는 그 제출에 속하지 않는 예외를 "낡은 예외"로
        # 오인하지 않는다. 파일명에서 클립 번호를 읽을 수 없는 예외는 안전하게
        # 남겨 전체 검사 때 다루게 한다.
        exceptions = [
            exception for exception in exceptions
            if ((match := re.match(r"clip(\d+[a-z]?)p?", exception["file"])) is None
                or match.group(1) in selected)
        ]

    ch = run / f"ch{chapter}"
    if not ch.is_dir():
        raise ValueError(f"챕터 폴더 없음: {ch}")

    stale: list[dict[str, object]] = []

    # 1) 패딩본 — 원본보다 오래된 패딩본은 구버전 이미지다
    for png in sorted(ch.glob("clip*.png")):
        match = re.fullmatch(r"clip(\d+[a-z]?)(?:_first|_end)?\.png", png.name)
        if selected is not None and (not match or match.group(1) not in selected):
            continue
        pad = padded_name(png.name)
        if not pad:
            continue
        pad_path = ch / pad
        if pad_path.is_file() and pad_path.stat().st_mtime < png.stat().st_mtime - MARGIN_SEC:
            stale.append({
                "file": pad,
                "what": f"패딩본 낡음: {pad}",
                "derived_ts": pad_path.stat().st_mtime,
                "source": f"원본 {png.name}",
                "source_ts": png.stat().st_mtime,
                "fix": f"→ {png.name}에서 패딩본을 다시 만든다",
            })

    # 2) 체인 — 상류 영상보다 오래된 first는 옛 끝 프레임이다
    for spec in chains:
        spec = str(spec)
        match = re.fullmatch(r"(\d+[a-z]?):(\d+[a-z]?)", spec)
        if not match:
            raise ValueError(f"--chain 형식은 A:B 입니다: {spec}")
        a, b = match.group(1), match.group(2)
        if selected is not None and a not in selected and b not in selected:
            continue
        source = next((ch / name for name in (f"clip{a}p_raw.mp4", f"clip{a}.mp4")
                       if (ch / name).is_file()), None)
        if source is None:
            print(f"[알림] 체인 {spec}: 상류 영상이 아직 없다 (clip{a}) — 건너뜀")
            continue
        targets = chain_targets(ch, b)
        if not targets:
            print(f"[알림] 체인 {spec}: clip{b}의 first가 아직 없다 — 건너뜀")
            continue
        for target in targets:
            if target.stat().st_mtime < source.stat().st_mtime - MARGIN_SEC:
                stale.append({
                    "file": target.name,
                    "what": f"체인 first 낡음: {target.name}",
                    "derived_ts": target.stat().st_mtime,
                    "source": f"상류 {source.name}",
                    "source_ts": source.stat().st_mtime,
                    "fix": f"→ {source.name}의 끝 프레임을 재추출한다",
                })

    by_file: dict[str, dict[str, str]] = {}
    for exception in exceptions:
        file_name = exception["file"]
        if file_name in by_file:
            raise ValueError(f"freshness_exceptions에 파일이 중복됩니다: {file_name}")
        by_file[file_name] = exception

    matched = set()
    findings = []
    for finding in stale:
        exception = by_file.get(str(finding["file"]))
        if exception:
            matched.add(exception["file"])
            print(f"[예외] {exception['file']} — {exception['reason']} ({exception['date']})")
        else:
            findings.append(finding)
    for exception in exceptions:
        if exception["file"] not in matched:
            print(f"[알림] 낡은 예외 — 정리 후보: {exception['file']} — "
                  f"{exception['reason']} ({exception['date']})")
    return findings


def print_findings(findings: list[dict[str, object]]) -> None:
    print(f"[실패] 원천보다 낡은 파생 자산 {len(findings)}건:")
    for finding in findings:
        print(f"  {finding['what']} ({fmt(float(finding['derived_ts']))}) < "
              f"{finding['source']} ({fmt(float(finding['source_ts']))})")
        print(f"    {finding['fix']}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run", required=True, type=Path)
    p.add_argument("--chapter", type=int, default=1)
    p.add_argument("--chain", nargs="*", default=None, metavar="A:B",
                   help="clip<B>의 first가 clip<A> 영상보다 새것이어야 하는 쌍")
    args = p.parse_args()

    try:
        findings = run_freshness(args.run, args.chapter, args.chain)
    except ValueError as exc:
        sys.exit(str(exc))
    if findings:
        print_findings(findings)
        sys.exit(2)
    print("파생 자산 신선도 통과 (패딩본·체인 first 모두 원천 이후)")


if __name__ == "__main__":
    main()
