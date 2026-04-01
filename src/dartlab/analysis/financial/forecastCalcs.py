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

    # 구조변화 감지 결과 전달 (Chow Test 기반)
    try:
        from dartlab.analysis.financial.research.predictionSignals import calcStructuralBreak

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

    # v4: 예측 불가능성 상태 전달
    out["forecastable"] = result.forecastable
    if not result.forecastable:
        out["unforecastableReason"] = result.unforecastableReason

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

    # 예측 불가 판정
    if not result.forecastable:
        flags.insert(0, ("UNFORECASTABLE", f"예측 불가 -- {result.unforecastableReason}"))

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


@memoized_calc
def calcCalibrationReport(company: Any, *, basePeriod: str | None = None) -> dict | None:
    """예측 캘리브레이션 리포트 — 이 종목의 과거 예측 정확도.

    forward test 레코드가 5건 미만이면 None 반환.
    데이터가 축적되면서 점진적으로 활성화된다.
    """
    from dataclasses import asdict

    from dartlab.analysis.forecast.calibrationMetrics import (
        buildCalibrationBins,
        computeBrierScore,
    )
    from dartlab.analysis.forecast.forwardTest import loadRecords

    stockCode = getattr(company, "stockCode", None)
    if not stockCode:
        return None

    records = loadRecords(stockCode)
    evaluated = [r for r in records if r.directionProbability is not None and r.directionActual is not None]
    if len(evaluated) < 5:
        return None

    predictions = [r.directionProbability for r in evaluated]  # type: ignore[misc]
    outcomes = [1 if r.directionActual == "up" else 0 for r in evaluated]

    brier = computeBrierScore(predictions, outcomes)
    bins = buildCalibrationBins(predictions, outcomes)

    return {
        "brierScore": round(brier, 4),
        "nRecords": len(evaluated),
        "bins": [asdict(b) for b in bins],
    }


# ── calc 8: 시나리오 시뮬레이션 ──


@memoized_calc
def calcScenarioSimulation(company: Any, *, basePeriod: str | None = None) -> dict | None:
    """시나리오 시뮬레이션 — 과거 CAGR 기반 자동 3시나리오 ProForma + 분기 목표.

    과거 3년 매출 CAGR을 자동 계산하여 base 성장률로 사용하고,
    bull/base/bear 3개 시나리오의 ProForma IS/BS/CF + 분기 목표 + DCF를 생성한다.

    사용자 지정 성장률이 필요하면 scenarioSim.createSimulation()을 직접 호출.
    """
    from dartlab.analysis.forecast.scenarioSim import createSimulation

    series, _, _, _, currency = _getSeriesAndMeta(company)
    shares = _getShares(company)

    # 과거 CAGR 자동 계산 (3년)
    revVals = []
    for sj_key in ("sales", "revenue"):
        vals = series.get("IS", {}).get(sj_key, [])
        if vals:
            # 연간 TTM: 4분기씩 역순으로 4개 연도
            annuals = []
            for end in range(len(vals), 3, -4):
                chunk = [v for v in vals[end - 4 : end] if v is not None]
                if len(chunk) == 4:
                    annuals.append(sum(chunk))
                if len(annuals) >= 4:
                    break
            annuals.reverse()
            if len(annuals) >= 2:
                revVals = annuals
                break

    if len(revVals) < 2:
        return None

    # CAGR 계산
    first, last = revVals[0], revVals[-1]
    nYears = len(revVals) - 1
    if first <= 0 or last <= 0:
        cagr = 0.0
    else:
        cagr = ((last / first) ** (1 / nYears) - 1) * 100

    # CAGR 범위 제한 (-20% ~ +50%)
    cagr = max(-20.0, min(50.0, cagr))

    try:
        sim = createSimulation(
            company,
            "자동(CAGR기반)",
            revenueGrowth=round(cagr, 1),
            shares=shares,
        )
    except (KeyError, ValueError, ZeroDivisionError, TypeError) as exc:
        log.debug("시나리오 시뮬레이션 실패: %s", exc)
        return None

    # 결과 직렬화 (dict 반환)
    scenarios = {}
    for scName, pf in sim.proformaResults.items():
        if pf.projections:
            p = pf.projections[0]
            scenarios[scName] = {
                "revenue": p.revenue,
                "operatingIncome": p.operating_income,
                "netIncome": p.net_income,
                "fcf": p.fcf,
                "wacc": pf.wacc,
            }

    return {
        "isEstimate": True,
        "currency": currency,
        "baseYear": sim.baseYear,
        "targetYear": sim.targetYear,
        "revenueGrowthCAGR": round(cagr, 1),
        "scenarios": scenarios,
        "quarterlyRevTargets": {sc: [round(v) for v in vals] for sc, vals in sim.quarterlyRevTargets.items()},
        "quarterlyOITargets": {sc: [round(v) for v in vals] for sc, vals in sim.quarterlyOITargets.items()},
        "dcfPerShare": sim.dcfPerShare,
        "seasonality": {
            "revenue": [round(w, 3) for w in sim.revSeasonality],
            "operatingIncome": [round(w, 3) for w in sim.oiSeasonality],
        },
    }
