"""Raw cross-company parquet scan 패턴 차단 — P-트랙 룰 9 게이트.

`pl.scan_parquet("data/{provider}/docs/*.parquet")` 처럼 다 회사 일괄 lazy scan 패턴은
STATUS_STACK_BUFFER_OVERRUN (Polars query plan 폭발) 사고 원인.

cross-company query 는 `data/{provider}/scan/docsIndex.parquet` 슬림 인덱스 (P3) 경유만.

baseline (`_baselines/rawCrossScan.json`) 외 위반만 fail.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

_REPO = Path(__file__).resolve().parent.parent.parent
_BASELINE = _REPO / "tests" / "audit" / "_baselines" / "rawCrossScan.json"

# 차단 패턴: data/{provider}/docs/*.parquet · data/{provider}/finance/*.parquet glob 일괄
_BANNED_PATTERNS = [
    re.compile(r'pl\.scan_parquet\([^)]*"data/[^"]*/(docs|finance)/\*\.parquet"'),
    re.compile(r'pl\.read_parquet\([^)]*"data/[^"]*/(docs|finance)/\*\.parquet"'),
    re.compile(r'glob\.glob\([^)]*"data/[^"]*/(docs|finance)/\*\.parquet"'),
]

_SCAN_ROOTS = ("src/dartlab",)


def _loadBaseline() -> dict:
    # 부재 시 silent fallback 금지 — 경로 drift(예: scripts/ ↔ tests/audit 이전) 를
    # 빈 baseline 으로 삼키면 ledger 가 끊긴 채 우연히 green 이 된다. 즉시 fail.
    if not _BASELINE.exists():
        raise FileNotFoundError(
            f"rawCrossScan baseline 부재: {_BASELINE}. 경로 drift 즉시 fail — 가드 정직화(silent {{}} fallback 금지)."
        )
    return json.loads(_BASELINE.read_text(encoding="utf-8"))


def _isLineViolation(line: str) -> bool:
    """line 에 차단 패턴 매칭 여부 — inline annotation 화이트리스트 적용 후 판정.

    M0: ``# polars-streaming-unsupported`` 주석이 같은 줄에 있으면 차단 예외
    (streaming engine 미지원 pivot/window/asof 22 건의 의도된 eager scan).
    """
    if "polars-streaming-unsupported" in line:
        return False
    for pat in _BANNED_PATTERNS:
        if pat.search(line):
            return True
    return False


def _scanFile(path: Path) -> list[str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (UnicodeDecodeError, OSError):
        return []
    violations: list[str] = []
    rel = str(path.relative_to(_REPO).as_posix())
    for i, line in enumerate(lines, start=1):
        if _isLineViolation(line):
            violations.append(f"{rel}:{i}")
    return violations


def _scanAll() -> list[str]:
    all_violations: list[str] = []
    for root in _SCAN_ROOTS:
        for p in (_REPO / root).rglob("*.py"):
            if "__pycache__" in p.parts:
                continue
            all_violations.extend(_scanFile(p))
    return sorted(all_violations)


def test_no_raw_cross_company_scan() -> None:
    """raw cross-company parquet glob 패턴이 dartlab 코드에 없어야 한다.

    P3 에서 docsIndex 빌더 + Scan.docsSections() API 도입 후 strict 전환.
    P0.5 baseline: 현 위반 (있다면) 기록 — 회귀만 차단.
    """
    violations = _scanAll()
    baseline = _loadBaseline()
    allowed = set(baseline.get("violations", []))
    new_violations = set(violations) - allowed
    assert not new_violations, (
        f"Raw cross-company scan 회귀 {len(new_violations)} 건: {sorted(new_violations)[:10]}. "
        f"cross-company 는 data/{{provider}}/scan/docsIndex.parquet 경유 (P3)."
    )


def test_streaming_unsupported_annotated() -> None:
    """M3: pivot/window/asof 27 호출부에 ``polars-streaming-unsupported`` 마커 부착 확인.

    M2 의 streaming engine 일괄 도입 시 이 호출부는 eager 유지 — 마커가
    auditor 에게 그 의도를 명시. 카테고리별 최소 횟수만 검증 (정확한 line 위치는
    refactor 로 이동 가능하므로 fragile 회피).
    """
    counts = {"pivot": 0, "over": 0, "asof": 0}
    for root in _SCAN_ROOTS:
        for p in (_REPO / root).rglob("*.py"):
            if "__pycache__" in p.parts:
                continue
            try:
                text = p.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for line in text.splitlines():
                if "polars-streaming-unsupported" not in line:
                    continue
                if ": pivot" in line:
                    counts["pivot"] += 1
                elif ": over" in line:
                    counts["over"] += 1
                elif ": asof" in line:
                    counts["asof"] += 1
    # docs 농장 은퇴와 EDGAR scanAccount pivot 제거로 호출부 3곳 삭제 — 임계 11→8 하향.
    assert counts["pivot"] >= 8, f"pivot 마커 부족: {counts['pivot']}/8"
    assert counts["over"] >= 6, f"over 마커 부족: {counts['over']}/6"
    assert counts["asof"] >= 4, f"asof 마커 부족: {counts['asof']}/4"


def test_gather_no_raw_cross_company_scan() -> None:
    """gather/ 내부에 raw cross-company glob 패턴 0 건 — P-G8 명시 가드.

    `src/dartlab` 전체 검사로 자동 포함되지만, gather 단독으로도 회귀 방지
    명시한다 (gather 가 cross-scan 진입점 위험 1차 위치).
    """
    repoSrc = _REPO / "src" / "dartlab" / "gather"
    if not repoSrc.exists():
        pytest.skip("gather/ 부재")
    gather_violations: list[str] = []
    for p in repoSrc.rglob("*.py"):
        if "__pycache__" in p.parts:
            continue
        gather_violations.extend(_scanFile(p))
    assert not gather_violations, (
        f"gather/ raw cross-scan 위반 {len(gather_violations)} 건: {gather_violations[:10]}. "
        "엔진 내부는 docsIndex / hfBulk.loadFiltered 같은 슬림 인덱스만 사용."
    )


def test_inline_annotation_excluded() -> None:
    """``# polars-streaming-unsupported`` 주석 있는 line 은 차단 제외 (M0 화이트리스트).

    streaming engine 미지원 22 건 (pivot/window/asof) 의 의도된 eager scan 을 위한
    명시 마킹. M3 가 22 호출부에 주석 부착.
    """
    # 차단 패턴 단독 → violation
    assert _isLineViolation('lf = pl.scan_parquet("data/dart/docs/*.parquet")')
    # 차단 패턴 + 주석 → 화이트리스트
    assert not _isLineViolation(
        'lf = pl.scan_parquet("data/dart/docs/*.parquet")  # polars-streaming-unsupported: pivot'
    )
    # 주석만 있고 패턴 없음 → violation 아님
    assert not _isLineViolation("# polars-streaming-unsupported: comment only")
    # 일반 line — 둘 다 없음
    assert not _isLineViolation("x = 1")
