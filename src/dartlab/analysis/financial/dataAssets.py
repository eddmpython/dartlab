"""Analysis owner가 Data Workbench에 제공하는 stable composite assets."""

from __future__ import annotations

import re
from typing import Any

_PERIOD_RE = re.compile(r"^(?P<year>\d{4})(?:-?Q(?P<quarter>[1-4]))?$")


def _periodKey(period: str) -> tuple[int, int]:
    match = _PERIOD_RE.fullmatch(str(period).strip().upper())
    if not match:
        raise ValueError(f"asOf/period 형식 오류: {period!r} (YYYY 또는 YYYY-Qn)")
    return int(match.group("year")), int(match.group("quarter") or 4)


def _periodLabel(key: tuple[int, int]) -> str:
    return f"{key[0]:04d}-Q{key[1]}"


def sliceFinanceSeries(
    series: dict,
    periods: list[str],
    asOf: str | None,
) -> tuple[dict, str, str, str]:
    """분기 재무 시리즈를 요청 fiscal period까지 절단한다."""
    if not periods:
        requested = str(asOf) if asOf is not None else "latest"
        return series, requested, "latest", requested

    keyed = [(_periodKey(period), index) for index, period in enumerate(periods)]
    latestKey = max(key for key, _ in keyed)
    requestedKey = latestKey if asOf is None else _periodKey(asOf)
    earliestKey = min(key for key, _ in keyed)
    if requestedKey < earliestKey or requestedKey > latestKey:
        raise ValueError(f"asOf={asOf!r} 는 가용 기간 {_periodLabel(earliestKey)}~{_periodLabel(latestKey)} 밖입니다.")

    kept = [index for key, index in keyed if key <= requestedKey]
    effectiveKey = max(key for key, _ in keyed if key <= requestedKey)
    sliced: dict[str, dict[str, list]] = {}
    for statement, accounts in series.items():
        sliced[statement] = {}
        for account, values in accounts.items():
            sliced[statement][account] = [values[index] if index < len(values) else None for index in kept]
    return sliced, _periodLabel(effectiveKey), _periodLabel(latestKey), _periodLabel(requestedKey)


def simulationInputs(
    *,
    subject: str | None = None,
    company: Any | None = None,
    asOf: str | None = None,
) -> dict[str, Any]:
    """Company 분기 재무를 한 번 읽고 valid-time 절단한 data asset을 반환한다."""
    if company is None:
        if not subject:
            raise ValueError("simulationInputs는 subject 또는 company가 필요합니다")
        import dartlab

        company = dartlab.Company(subject)
    try:
        quarterly = company._buildFinanceSeries(freq="Q")
    except (ValueError, KeyError, AttributeError):
        quarterly = None
    rawSeries = quarterly[0] if isinstance(quarterly, tuple) and len(quarterly) >= 2 else None
    periods = list(quarterly[1]) if isinstance(quarterly, tuple) and len(quarterly) >= 2 else []
    if rawSeries:
        series, effectiveAsOf, latestAsOf, requestedAsOf = sliceFinanceSeries(rawSeries, periods, asOf)
    else:
        requestedAsOf = str(asOf) if asOf is not None else "latest"
        effectiveAsOf = requestedAsOf
        latestAsOf = "latest"
        series = None
    return {
        "series": series,
        "asOf": effectiveAsOf,
        "latestAsOf": latestAsOf,
        "requestedAsOf": requestedAsOf,
    }
