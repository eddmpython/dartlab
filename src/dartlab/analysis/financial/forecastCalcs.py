"""매출전망 축 -- forecast 엔진을 analysis 패턴으로 래핑.

calc 함수 7개: 매출예측, 세그먼트전망, ProForma, 시나리오,
방법론, 과거비율, 플래그.

모든 함수는 (company) -> dict | None 시그니처를 따른다.
"""

from __future__ import annotations

import logging
from typing import Any

from dartlab.analysis.financial._memoize import memoized_calc
from dartlab.analysis.financial.valuation import _IG_TO_SECTOR_KEY
from dartlab.analysis.forecast.revenueForecast import CompanyDataBundle, forecastRevenue
from dartlab.analysis.forecast.simulation import simulateAllScenarios

log = logging.getLogger(__name__)


# ── 공통 헬퍼 ──


def _getSeriesAndMeta(company: Any) -> tuple[dict, str | None, str | None, str, str]:
    """company에서 series, stockCode, sectorKey, market, currency 추출."""
    ts = company.finance.timeseries
    series = ts[0] if isinstance(ts, tuple) else ts

    stockCode = getattr(company, "stockCode", None)
    currency = getattr(company, "currency", "KRW") or "KRW"
    market = getattr(company, "market", "KR") or "KR"

    # sectorKey: valuation.py _resolveSectorKey 동일 로직
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
    """segments, salesOrder → CompanyDataBundle 조립. 없으면 None."""
    segmentRevenue = None
    salesDf = None
    orderDf = None

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

    if segmentRevenue is None and salesDf is None and orderDf is None:
        return None

    return CompanyDataBundle(
        segmentRevenue=segmentRevenue,
        salesDf=salesDf,
        orderDf=orderDf,
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


# ── calc 함수 7개 ──


@memoized_calc
def calcRevenueForecast(company: Any, *, basePeriod: str | None = None) -> dict | None:
    """7-소스 앙상블 3-시나리오 매출 전망."""
    result = _runForecastRevenue(company)
    if not result or not result.projected:
        return None

    currency = getattr(company, "currency", "KRW") or "KRW"

    out: dict = {
        "isEstimate": True,
        "method": result.method,
        "confidence": result.confidence,
        "currency": currency,
        "historical": result.historical,
        "projected": result.projected,
        "growthRates": result.growthRates,
        "horizon": result.horizon,
    }

    # 시나리오
    if result.scenarios:
        out["scenarios"] = {}
        for label in ("base", "bull", "bear"):
            sc = result.scenarios.get(label, [])
            sg = result.scenarioGrowthRates.get(label, [])
            prob = result.scenarioProbabilities.get(label, 0)
            if sc:
                out["scenarios"][label] = {
                    "projected": sc,
                    "growthRates": sg,
                    "probability": prob,
                }

    # 라이프사이클
    lifecycle = result.aiContext.get("lifecycle", "")
    if lifecycle:
        out["lifecycle"] = lifecycle

    out["disclaimer"] = result.DISCLAIMER
    return out


@memoized_calc
def calcSegmentForecast(company: Any, *, basePeriod: str | None = None) -> dict | None:
    """세그먼트별 개별 매출 성장 전망."""
    result = _runForecastRevenue(company)
    if not result or not result.segmentForecasts:
        return None

    currency = getattr(company, "currency", "KRW") or "KRW"

    segments = []
    for seg in result.segmentForecasts:
        segments.append(
            {
                "name": seg.name,
                "projected": seg.projected,
                "growthRates": seg.growthRates,
                "method": seg.method,
                "shareOfRevenue": seg.shareOfRevenue,
                "lifecycle": seg.lifecycle,
            }
        )

    return {
        "isEstimate": True,
        "currency": currency,
        "segments": segments,
    }


@memoized_calc
def calcProFormaHighlights(company: Any, *, basePeriod: str | None = None) -> dict | None:
    """Pro-Forma IS 주요 항목 전망."""
    result = _runForecastRevenue(company)
    if not result or not result.projected:
        return None

    series, _, sectorKey, _, currency = _getSeriesAndMeta(company)
    shares = _getShares(company)
    sp = _getSectorParams(company)

    # 매출 성장률 경로 추출
    growthPath = result.growthRates
    if not growthPath:
        return None

    from dartlab.core.finance.proforma import build_proforma

    try:
        pf = build_proforma(
            series,
            revenue_growth_path=growthPath,
            sector_params=sp,
            shares=shares,
            scenario_name="base",
        )
    except (KeyError, ValueError, ZeroDivisionError, TypeError) as exc:
        log.debug("pro-forma 생성 실패: %s", exc)
        return None

    if not pf.projections:
        return None

    years = []
    for p in pf.projections:
        years.append(
            {
                "yearOffset": p.year_offset,
                "revenue": p.revenue,
                "operatingIncome": p.operating_income,
                "netIncome": p.net_income,
                "ebitda": p.ebitda,
                "fcf": p.fcf,
            }
        )

    return {
        "isEstimate": True,
        "currency": currency,
        "wacc": pf.wacc,
        "revenueGrowthPath": pf.revenue_growth_path,
        "years": years,
        "warnings": pf.warnings,
        "disclaimer": pf.DISCLAIMER,
    }


@memoized_calc
def calcScenarioImpact(company: Any, *, basePeriod: str | None = None) -> dict | None:
    """매크로 시나리오별 매출/마진 영향."""
    series, _, sectorKey, _, currency = _getSeriesAndMeta(company)
    shares = _getShares(company)
    sp = _getSectorParams(company)

    try:
        results = simulateAllScenarios(
            series,
            sectorKey=sectorKey,
            sectorParams=sp,
            shares=shares,
        )
    except (KeyError, ValueError, ZeroDivisionError, TypeError) as exc:
        log.debug("시나리오 시뮬레이션 실패: %s", exc)
        return None

    if not results:
        return None

    scenarios = {}
    for name, sim in results.items():
        scenarios[name] = {
            "label": sim.scenarioLabel,
            "revenueChangePct": sim.revenueChangePct,
            "marginChangeBps": sim.marginChangeBps,
            "revenuePath": sim.revenuePath,
            "marginPath": sim.marginPath,
            "warnings": sim.warnings,
        }

    return {
        "isEstimate": True,
        "currency": currency,
        "scenarios": scenarios,
    }


@memoized_calc
def calcForecastMethodology(company: Any, *, basePeriod: str | None = None) -> dict | None:
    """예측 방법론 투명성 공개."""
    result = _runForecastRevenue(company)
    if not result:
        return None

    return {
        "method": result.method,
        "confidence": result.confidence,
        "sources": result.sources,
        "sourceWeights": result.sourceWeights,
        "assumptions": result.assumptions,
        "warnings": result.warnings,
        "lifecycle": result.aiContext.get("lifecycle", ""),
    }


@memoized_calc
def calcHistoricalRatios(company: Any, *, basePeriod: str | None = None) -> dict | None:
    """Pro-Forma 기반 과거 구조 비율."""
    series, _, _, _, _ = _getSeriesAndMeta(company)

    from dartlab.core.finance.proforma import extract_historical_ratios

    try:
        ratios = extract_historical_ratios(series)
    except (KeyError, ValueError, ZeroDivisionError, TypeError) as exc:
        log.debug("과거 비율 추출 실패: %s", exc)
        return None

    return {
        "grossMargin": ratios.gross_margin,
        "sgaRatio": ratios.sga_ratio,
        "effectiveTaxRate": ratios.effective_tax_rate,
        "depreciationRatio": ratios.depreciation_ratio,
        "capexToRevenue": ratios.capex_to_revenue,
        "interestRateOnDebt": ratios.interest_rate_on_debt,
        "nwcToRevenue": ratios.nwc_to_revenue,
        "dividendPayout": ratios.dividend_payout,
        "yearsUsed": ratios.years_used,
        "confidence": ratios.confidence,
        "trends": ratios.trends,
        "warnings": ratios.warnings,
    }


@memoized_calc
def calcForecastFlags(company: Any, *, basePeriod: str | None = None) -> dict | None:
    """매출전망 플래그."""
    result = _runForecastRevenue(company)
    if not result:
        return None

    flags: list[tuple[str, str]] = []

    # 신뢰도 경고
    if result.confidence == "low":
        flags.append(("LOW_CONFIDENCE", "예측 신뢰도 낮음 -- 데이터 부족 또는 변동성 과다"))

    # 시계열 전용 (컨센서스/매크로 부재)
    if result.method == "timeseries_only":
        flags.append(("TIMESERIES_ONLY", "시계열만 사용 -- 컨센서스 데이터 없음"))

    # 구조변화 감지
    if "structural_break" in result.aiContext:
        flags.append(("STRUCTURAL_BREAK", "매출 시계열 구조변화 감지 -- 과거 추세가 미래에 유효하지 않을 수 있음"))

    # 시나리오 격차
    if result.scenarios:
        bull = result.scenarios.get("bull", [])
        bear = result.scenarios.get("bear", [])
        if bull and bear and bull[0] > 0 and bear[0] > 0:
            spread = (bull[0] - bear[0]) / bear[0] * 100
            if spread > 50:
                flags.append(("HIGH_UNCERTAINTY", f"Bull-Bear 격차 {spread:.0f}% -- 불확실성 높음"))

    # 엔진 warnings 전달
    for w in result.warnings:
        flags.append(("WARNING", w))

    if not flags:
        return None

    return {"flags": flags}
