"""strategy 빌더 공통 유틸."""

from __future__ import annotations

import polars as pl


def periodCols(df: pl.DataFrame) -> list[str]:
    """DataFrame에서 기간 컬럼만 추출 (최신 먼저)."""
    from dartlab.core.show import isPeriodColumn

    return [c for c in df.columns if isPeriodColumn(c)]


def annualCols(df: pl.DataFrame, maxYears: int = 5) -> list[str]:
    """연도 컬럼만 추출 (Q4 또는 연도)."""
    cols = periodCols(df)
    annual = [c for c in cols if "Q" not in c]
    if annual:
        return annual[:maxYears]
    return [c for c in cols if c.endswith("Q4")][:maxYears]


def quarterlyCols(df: pl.DataFrame, maxQuarters: int = 5) -> list[str]:
    """분기 컬럼만 추출 (최신 먼저)."""
    cols = periodCols(df)
    return [c for c in cols if "Q" in c][:maxQuarters]


MAX_RATIO_YEARS = 5


def getRatioSeries(company) -> tuple[dict, list[str]] | None:
    """ratioSeries를 안전하게 가져온다."""
    try:
        result = company.finance.ratioSeries
        if result is None:
            return None
        return result
    except (ValueError, KeyError, AttributeError):
        return None


def buildTimeline(data: dict, field: str, years: list[str]) -> list[dict]:
    """시계열 데이터를 [{period, value}, ...] 형태로 변환."""
    vals = data.get("RATIO", {}).get(field, [])
    n = min(len(vals), len(years), MAX_RATIO_YEARS)
    if n == 0:
        return []
    return [{"period": years[i], "value": vals[i]} for i in range(len(years) - n, len(years))]


def getRatios(company):
    """ratios 객체를 안전하게 가져온다."""
    try:
        return company.finance.ratios
    except (ValueError, KeyError, AttributeError):
        return None


def toDict(selectResult, maxPeriods: int = 0) -> tuple[dict[str, dict], list[str]] | None:
    """SelectResult → ({계정명: {period: val}}, periodCols).

    maxPeriods=0이면 전체 기간, >0이면 최신 N개만.
    """
    if selectResult is None:
        return None

    df = selectResult.df
    periods = sorted(periodCols(df), reverse=True)
    if maxPeriods > 0:
        periods = periods[:maxPeriods]
    if not periods:
        return None

    labelCol = "계정명" if "계정명" in df.columns else (df.columns[0] if df.columns else None)
    if labelCol is None:
        return None

    data: dict[str, dict] = {}
    for row in df.iter_rows(named=True):
        label = str(row.get(labelCol, ""))
        data[label] = {c: row.get(c) for c in periods}
    return (data, periods) if data else None
