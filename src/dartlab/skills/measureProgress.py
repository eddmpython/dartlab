#!/usr/bin/env python3
"""dartlab 진척 측정 — baseline 부채 · docstring backlog · pytest marker 분포 통합 시계열.

Sig::

    uv run python -X utf8 src/dartlab/skills/measureProgress.py
    uv run python -X utf8 src/dartlab/skills/measureProgress.py --record
    uv run python -X utf8 src/dartlab/skills/measureProgress.py --record --json

핵심 측정 (read-only — 코드/baseline 변경 0):

1. baseline 부채 — ``tests/audit/_baselines/*.json`` 의 ``violations`` list 또는
   ``known``/``protectedCompanyFacadeDebt`` dict 안 list 합산. ``dartlabGuard``
   ``docstring4Section`` ``docstringSpecifications`` 17 파일을 자동 walk.
2. docstring 격상 backlog — 9 섹션 baseline 7 종 (``4Section`` · ``Capabilities`` ·
   ``AIContext`` · ``Guide`` · ``SeeAlso`` · ``Requires`` · ``Specifications``)
   합산 — 격상 진행 시 자연 감소.
3. pytest marker 분포 — ``tests/test_*.py`` 안 ``@pytest.mark.<name>`` 출현
   회수 + 마커 0 으로 적힌 test 함수 수 (lock wrapper marker 분할 직렬화의
   가시화 결손 보강).

기존 측정 인프라와의 관계 — ``qualityGate.py`` 는 radon E/F · cdef · vulture
시계열을 ``qualityHistory.jsonl`` 에 기록한다. 본 스크립트는 *부채 원장*
시계열을 ``_progress/measureHistory.jsonl`` 로 분리해서 적재한다 (서로 다른 축).

룰 6 준수 — 본 스크립트는 *측정만* 한다. baseline/docstring/marker 어떤 파일도
변경하지 않는다. ``feedback_no_docstring_auto_sweep`` · ``feedback_no_skill_json_auto_build``
강행규칙 안에서 *진척 가시화* 만 보강.

Args::

    --record     측정값을 ``_progress/measureHistory.jsonl`` 에 한 줄 append
    --json       표 대신 single-line JSON 을 stdout 으로 출력 (CI artifact 용)

Example::

    >>> uv run python -X utf8 src/dartlab/skills/measureProgress.py
    dartlab progress — 2026-05-15 @ 1a3530bce
      baseline 부채 total   : 1217
      docstring backlog     : 894
      test 함수 총수        : 612
      test 마커 미적용      : 178

Returns::

    0   측정 정상
    1   baseline 파일 손상 (json.JSONDecodeError)

Raises::

    json.JSONDecodeError    ``_baselines/*.json`` 형식 손상 시 (조기 종료, exit 1).
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

_REPO = Path(__file__).resolve().parents[3]
_BASELINE_DIR = _REPO / "tests" / "audit" / "_baselines"
_PROGRESS_DIR = _REPO / "tests" / "audit" / "_progress"
_HISTORY_PATH = _PROGRESS_DIR / "measureHistory.jsonl"
_TESTS_DIR = _REPO / "tests"

_DOCSTRING_BASELINES = (
    "docstring4Section.json",
    "docstringCapabilities.json",
    "docstringAIContext.json",
    "docstringGuide.json",
    "docstringSeeAlso.json",
    "docstringRequires.json",
    "docstringSpecifications.json",
)

_PYTEST_MARKER_RE = re.compile(r"@pytest\.mark\.(\w+)")
_TEST_FN_RE = re.compile(r"^(?:async\s+)?def\s+(test\w*)\s*\(", re.MULTILINE)


def _countEntries(value: object) -> int:
    """항목 리스트를 구조에 상관없이 센다.

    예전에는 `violations`, `known`, `protectedCompanyFacadeDebt` 세 모양만 알아봤다.
    그런데 원장마다 키 이름이 달라서 `missing`, `over_split`, `under_split`,
    `twoCycles`, `asymmetry` 같은 이름을 쓰는 열네 개 원장이 전부 0 으로 집계됐다.
    가장 큰 `testCoverage` 1,106 건이 통째로 0 이었다. 이름을 하나씩 등록하는 방식은
    새 원장이 생길 때마다 같은 침묵을 반복하므로 모양으로 센다.
    """

    if isinstance(value, list):
        return len(value)
    if isinstance(value, dict):
        return sum(_countEntries(item) for key, item in value.items() if not key.startswith("_"))
    return 0


def _countViolations(baselinePath: Path) -> int:
    """단일 baseline json 의 위반 항목 수."""
    if not baselinePath.exists():
        return 0
    try:
        # utf-8-sig. 일부 baseline(예 testCoverage.json)이 BOM 으로 적혀 plain utf-8
        # 디코드가 깨진다. BOM 유무 모두 관용한다.
        data = json.loads(baselinePath.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"[measureProgress] baseline 손상: {baselinePath} ({exc})") from exc
    return _countEntries(data)


def _measureBaselineDebt() -> dict:
    """모든 baseline 파일의 위반 총수 + 파일별 카운트."""
    # 디렉터리 부재 시 빈 glob 가 silent 0 을 낳아 "부채 0" 거짓 시계열을 적재한다.
    # 경로 drift(scripts/ ↔ tests/audit) 즉시 fail — 가드 정직화.
    if not _BASELINE_DIR.exists():
        raise SystemExit(
            f"[measureProgress] baseline 디렉터리 부재: {_BASELINE_DIR}. 빈 glob silent 0 금지 — 경로 drift 즉시 fail."
        )
    counts: dict[str, int] = {}
    for path in sorted(_BASELINE_DIR.glob("*.json")):
        counts[path.stem] = _countViolations(path)
    return {"total": sum(counts.values()), "byFile": counts}


def _measureDocstringBacklog() -> dict:
    """9 섹션 docstring baseline 7 종 합산."""
    perCategory: dict[str, int] = {}
    for name in _DOCSTRING_BASELINES:
        key = name.replace("docstring", "").replace(".json", "") or "global"
        perCategory[key] = _countViolations(_BASELINE_DIR / name)
    return {"total": sum(perCategory.values()), "byCategory": perCategory}


def _measureMarkerCoverage() -> dict:
    """tests/ 안 pytest marker 분포 + 마커 미적용 test 함수 수."""
    markerCounts: dict[str, int] = {}
    totalTestFns = 0
    unmarkedFns = 0
    for path in _TESTS_DIR.rglob("test_*.py"):
        text = path.read_text(encoding="utf-8", errors="replace")
        markers = _PYTEST_MARKER_RE.findall(text)
        for marker in markers:
            markerCounts[marker] = markerCounts.get(marker, 0) + 1
        testFns = _TEST_FN_RE.findall(text)
        totalTestFns += len(testFns)
        if not markers:
            unmarkedFns += len(testFns)
    return {
        "totalTestFns": totalTestFns,
        "unmarkedFns": unmarkedFns,
        "byMarker": markerCounts,
    }


def _gitCommit() -> str:
    """현재 git commit short hash. git 없으면 'unknown'."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            cwd=str(_REPO),
            check=False,
        )
        return result.stdout.strip() or "unknown"
    except FileNotFoundError:
        return "unknown"


def _measure() -> dict:
    """3 축 측정값을 한 dict 으로 모은다."""
    baselineDebt = _measureBaselineDebt()
    docstringBacklog = _measureDocstringBacklog()
    markerCoverage = _measureMarkerCoverage()
    return {
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "commit": _gitCommit(),
        "baselineTotal": baselineDebt["total"],
        "baselineByFile": baselineDebt["byFile"],
        "docstringBacklog": docstringBacklog["total"],
        "docstringByCategory": docstringBacklog["byCategory"],
        "testFns": markerCoverage["totalTestFns"],
        "testFnsUnmarked": markerCoverage["unmarkedFns"],
        "testByMarker": markerCoverage["byMarker"],
    }


def _trend(curr: int, prevVal: int | None) -> str:
    """이전 측정 대비 화살표 — ▼ 감소 / ▲ 증가 / = 동일."""
    if prevVal is None:
        return ""
    delta = curr - prevVal
    if delta == 0:
        return " (=)"
    arrow = "▼" if delta < 0 else "▲"
    return f" ({arrow}{abs(delta)})"


def _formatTable(record: dict, prev: dict | None) -> str:
    """3 축 측정값 + 추세 + 상위 분포 콘솔 표 포맷."""
    lines: list[str] = []
    lines.append(f"dartlab progress — {record['date']} @ {record['commit']}")
    lines.append("")
    lines.append(
        f"  baseline 부채 total   : {record['baselineTotal']}"
        f"{_trend(record['baselineTotal'], (prev or {}).get('baselineTotal'))}"
    )
    lines.append(
        f"  docstring backlog     : {record['docstringBacklog']}"
        f"{_trend(record['docstringBacklog'], (prev or {}).get('docstringBacklog'))}"
    )
    lines.append(
        f"  test 함수 총수        : {record['testFns']}{_trend(record['testFns'], (prev or {}).get('testFns'))}"
    )
    lines.append(
        f"  test 마커 미적용      : {record['testFnsUnmarked']}"
        f"{_trend(record['testFnsUnmarked'], (prev or {}).get('testFnsUnmarked'))}"
    )
    lines.append("")
    lines.append("  baseline file 분포 top 8:")
    for name, count in sorted(record["baselineByFile"].items(), key=lambda item: -item[1])[:8]:
        lines.append(f"    {name:35s} {count}")
    lines.append("")
    lines.append("  marker 분포:")
    for marker, count in sorted(record["testByMarker"].items(), key=lambda item: -item[1]):
        lines.append(f"    {marker:20s} {count}")
    return "\n".join(lines)


def _loadLastHistory() -> dict | None:
    """history jsonl 의 마지막 행 — 추세 표시용."""
    if not _HISTORY_PATH.exists():
        return None
    try:
        text = _HISTORY_PATH.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    if not text:
        return None
    lastLine = text.splitlines()[-1]
    try:
        return json.loads(lastLine)
    except json.JSONDecodeError:
        return None


def _appendHistory(record: dict) -> None:
    """measureHistory.jsonl 에 한 줄 append (디렉토리 미존재 시 생성)."""
    _PROGRESS_DIR.mkdir(parents=True, exist_ok=True)
    with open(_HISTORY_PATH, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def buildParser() -> argparse.ArgumentParser:
    """measureProgress argparse 빌더."""
    parser = argparse.ArgumentParser(
        prog="measureProgress",
        description="dartlab 진척 측정 — baseline 부채 · docstring backlog · pytest marker 분포.",
    )
    parser.add_argument("--record", action="store_true", help="history jsonl 에 한 줄 append")
    parser.add_argument("--json", action="store_true", help="single-line JSON stdout 출력")
    return parser


def main() -> int:
    """CLI 진입점 — 측정 → 표 또는 JSON 출력 → (선택) jsonl append."""
    args = buildParser().parse_args()
    record = _measure()
    prev = _loadLastHistory()
    if args.record:
        _appendHistory(record)
    if args.json:
        print(json.dumps(record, ensure_ascii=False))
    else:
        print(_formatTable(record, prev))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
