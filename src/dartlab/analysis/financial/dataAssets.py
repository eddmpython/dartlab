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

        companyFactory = getattr(dartlab, "Company")
        company = companyFactory(subject)
    resolvedCompany: Any = company
    try:
        quarterly = resolvedCompany._buildFinanceSeries(freq="Q")
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


def edgarFinancialFeatures(
    *,
    subject: str | None = None,
    company: Any | None = None,
    knownAt: str,
) -> dict[str, Any]:
    """로컬 EDGAR evidence에서 operating-company PIT feature envelope를 만든다.

    Args:
        subject: US ticker 또는 Company가 해소할 수 있는 EDGAR identity.
        company: 테스트와 read-once 조합을 위한 기존 EDGAR Company.
        knownAt: SEC filing knowledge cutoff.

    Returns:
        Data Workbench가 검증하고 FactorProjection으로 변환할 plain mapping.

    Raises:
        ValueError: Subject가 없거나 EDGAR Company가 아니거나 coherent reduced state가 없을 때.
        FileNotFoundError: 현재 runtime에 local companyfacts shard가 없을 때.

    Example:
        ``payload = edgarFinancialFeatures(subject="AAPL", knownAt="20250201")``
    """

    if company is None:
        if not subject:
            raise ValueError("edgarFinancialFeatures는 subject 또는 company가 필요합니다")
        import dartlab

        companyFactory = getattr(dartlab, "Company")
        company = companyFactory(subject)
    resolvedCompany: Any = company
    cik = getattr(resolvedCompany, "cik", None)
    ticker = str(getattr(resolvedCompany, "ticker", subject or "")).strip().upper()
    if not cik or not ticker or ticker.isdigit():
        raise ValueError("edgarFinancialFeatures는 canonical ticker가 있는 EDGAR Company가 필요합니다")
    from dartlab.analysis.financial.filingFeatures import buildEdgarFinancialFeatureInput
    from dartlab.providers.edgar.finance.facts import readCompanyFactsLocal

    facts = readCompanyFactsLocal(str(cik))
    return buildEdgarFinancialFeatureInput(
        facts,
        entityId=f"US:{ticker}",
        knownAt=knownAt,
    )
