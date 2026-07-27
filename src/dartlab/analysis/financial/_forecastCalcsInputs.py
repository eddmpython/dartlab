"""forecastCalcs.py 의 공통 헬퍼 — series/meta/shares/sectorParams/dataBundle/runForecast."""

from __future__ import annotations

from typing import Any

from dartlab.analysis.financial.valuation import _IG_TO_SECTOR_KEY
from dartlab.analysis.forecast.revenueForecast import CompanyDataBundle, forecastRevenue


def _getSeriesAndMeta(company: Any) -> tuple[dict, str | None, str | None, str, str]:
    """company에서 series, stockCode, sectorKey, market, currency 추출."""
    ts = company._buildFinanceSeries(freq="Q")
    series = ts[0] if isinstance(ts, tuple) else ts

    stockCode = getattr(company, "stockCode", None)
    currency = getattr(company, "currency", "KRW") or "KRW"
    market = getattr(company, "market", "KR") or "KR"

    sectorKey = None
    try:
        sectorInfo = company.sector
        if sectorInfo is not None:
            igName = sectorInfo.industryGroup.name
            sectorKey = _IG_TO_SECTOR_KEY.get(igName)
    except (AttributeError, ValueError):
        pass

    return series, stockCode, sectorKey, market, currency


def _getShares(company: Any) -> int | None:
    """발행주식수 추출."""
    profile = getattr(company, "profile", None)
    if profile:
        sharesVal = getattr(profile, "sharesOutstanding", None)
        if sharesVal:
            return int(sharesVal)
    return None


def _getSectorParams(company: Any):
    """SectorParams 추출."""
    try:
        return getattr(company, "sectorParams", None)
    except AttributeError:
        return None


def _buildCompanyDataBundle(company: Any):
    """segments, salesOrder, structuralBreak → CompanyDataBundle 조립. 없으면 None."""
    segmentRevenue = None
    salesDf = None
    orderDf = None
    structuralBreak = None

    try:
        segments = getattr(company, "segments", None)
        if segments is not None:
            segmentRevenue = getattr(segments, "revenue", None)
    except (AttributeError, TypeError):
        pass

    try:
        salesOrder = getattr(company, "salesOrder", None)
        if salesOrder is not None:
            salesDf = getattr(salesOrder, "salesDf", None)
            orderDf = getattr(salesOrder, "orderDf", None)
    except (AttributeError, TypeError):
        pass

    try:
        from dartlab.analysis.financial.predictionSignals import calcStructuralBreak

        structuralBreak = calcStructuralBreak(company)
    except (ImportError, AttributeError, TypeError, ValueError):
        pass

    if segmentRevenue is None and salesDf is None and orderDf is None and structuralBreak is None:
        return None

    return CompanyDataBundle(
        segmentRevenue=segmentRevenue,
        salesDf=salesDf,
        orderDf=orderDf,
        structuralBreak=structuralBreak,
    )


def _runForecastRevenue(company: Any):
    """forecastRevenue 실행 + 결과 캐시. 같은 company에서 중복 호출 방지."""
    cache = getattr(company, "_cache", None)
    _KEY = "_forecastRevenueResult"
    if cache is not None and _KEY in cache:
        return cache[_KEY]

    series, stockCode, sectorKey, market, currency = _getSeriesAndMeta(company)

    companyData = _buildCompanyDataBundle(company)

    result = forecastRevenue(
        series,
        stockCode=stockCode,
        sectorKey=sectorKey,
        market=market,
        horizon=3,
        companyData=companyData,
        currency=currency,
    )

    if cache is not None:
        cache[_KEY] = result
    return result
