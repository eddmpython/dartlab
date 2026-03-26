"""재무 시계열 변곡점 감지.

finance DataFrame(account × year)에서 전년 대비 급변 지점을 감지한다.
±20% = major, ±10% = minor, 부호전환 = major.

사용법::

    from dartlab.core.finance.inflection import detectInflections

    inflections = detectInflections(df)
    for inf in inflections:
        print(f"{inf.account} {inf.year}: {inf.changeRate:+.1%} ({inf.severity})")
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import polars as pl

_PERIOD_RE = re.compile(r"^\d{4}$")


@dataclass
class Inflection:
    """하나의 변곡점."""

    account: str
    year: str
    prevYear: str
    prev: float
    curr: float
    changeRate: float
    severity: str


def _accountCol(df: pl.DataFrame) -> str | None:
    for candidate in ("account", "계정명", "metric", "snakeId"):
        if candidate in df.columns:
            return candidate
    return None


def detectInflections(
    df: pl.DataFrame,
    *,
    majorThreshold: float = 0.20,
    minorThreshold: float = 0.10,
    minAbsValue: float = 1.0,
) -> list[Inflection]:
    """finance DataFrame에서 변곡점을 감지한다.

    Args:
        df: account(행) × year(열) DataFrame.
        majorThreshold: major 변곡점 기준 (기본 20%).
        minorThreshold: minor 변곡점 기준 (기본 10%).
        minAbsValue: 이 값 미만인 셀은 무시 (0 근처 노이즈 방지).

    Returns:
        Inflection 리스트 (severity 내림차순 → changeRate 내림차순).
    """
    acctCol = _accountCol(df)
    if acctCol is None:
        return []

    yearCols = sorted(
        [c for c in df.columns if _PERIOD_RE.fullmatch(c)],
    )
    if len(yearCols) < 2:
        return []

    results: list[Inflection] = []

    accounts = df[acctCol].to_list()
    # 연도 컬럼 값들을 한 번에 추출 (to_list 1회씩만)
    yearData: dict[str, list] = {c: df[c].to_list() for c in yearCols}

    for rowIdx, account in enumerate(accounts):
        if not account:
            continue
        account = str(account)

        for i in range(1, len(yearCols)):
            prevYear = yearCols[i - 1]
            currYear = yearCols[i]
            prevVal = yearData[prevYear][rowIdx]
            currVal = yearData[currYear][rowIdx]

            if prevVal is None or currVal is None:
                continue
            try:
                prev = float(prevVal)
                curr = float(currVal)
            except (ValueError, TypeError):
                continue

            if prev != 0 and curr != 0 and (prev > 0) != (curr > 0):
                results.append(
                    Inflection(
                        account=account,
                        year=currYear,
                        prevYear=prevYear,
                        prev=prev,
                        curr=curr,
                        changeRate=0.0,
                        severity="major",
                    )
                )
                continue

            if abs(prev) < minAbsValue:
                continue

            changeRate = (curr - prev) / abs(prev)

            if abs(changeRate) >= majorThreshold:
                severity = "major"
            elif abs(changeRate) >= minorThreshold:
                severity = "minor"
            else:
                continue

            results.append(
                Inflection(
                    account=account,
                    year=currYear,
                    prevYear=prevYear,
                    prev=prev,
                    curr=curr,
                    changeRate=changeRate,
                    severity=severity,
                )
            )

    severityOrder = {"major": 0, "minor": 1}
    results.sort(key=lambda x: (severityOrder.get(x.severity, 9), -abs(x.changeRate)))
    return results
