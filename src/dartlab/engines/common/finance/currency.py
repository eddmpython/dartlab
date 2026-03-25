"""환율 정규화 — 다국가 재무 비교용 통화 변환."""

from __future__ import annotations

from functools import lru_cache

import polars as pl

# FRED 시리즈 ID → USD 기준 환율
_FRED_SERIES: dict[str, str] = {
    "KRW": "DEXKOUS",
    "JPY": "DEXJPUS",
    "EUR": "DEXUSEU",
    "GBP": "DEXUSUK",
    "CNY": "DEXCHUS",
}


@lru_cache(maxsize=8)
def _fetchRate(fromCurrency: str) -> pl.DataFrame | None:
    """FRED에서 환율 시계열 가져오기 (캐시)."""
    seriesId = _FRED_SERIES.get(fromCurrency.upper())
    if seriesId is None:
        return None
    try:
        from dartlab.engines.gather.fred import Fred
        f = Fred()
        return f.series(seriesId)
    except (ImportError, ValueError, RuntimeError):
        return None


def getExchangeRate(fromCurrency: str, toCurrency: str = "USD") -> float | None:
    """최신 환율 조회. 현재 USD 기준만 지원."""
    fc = fromCurrency.upper()
    tc = toCurrency.upper()
    if fc == tc:
        return 1.0
    if tc != "USD":
        # A→USD→B 경유
        aToUsd = getExchangeRate(fc, "USD")
        bToUsd = getExchangeRate(tc, "USD")
        if aToUsd is None or bToUsd is None or bToUsd == 0:
            return None
        return aToUsd / bToUsd

    df = _fetchRate(fc)
    if df is None or df.is_empty():
        return None

    # 최신 non-null 값
    vals = df.drop_nulls()
    if vals.is_empty():
        return None

    valCol = [c for c in vals.columns if c != "date"]
    if not valCol:
        return None

    lastVal = vals[valCol[0]][-1]
    if lastVal is None or lastVal == 0:
        return None

    # FRED 환율 방향 보정: DEXKOUS = KRW per USD → 1/rate = USD per KRW
    if fc in ("KRW", "JPY", "CNY"):
        return 1.0 / float(lastVal)
    return float(lastVal)


def convertValue(
    value: float,
    fromCurrency: str,
    toCurrency: str = "USD",
) -> float | None:
    """금액을 통화 변환."""
    rate = getExchangeRate(fromCurrency, toCurrency)
    if rate is None:
        return None
    return value * rate
