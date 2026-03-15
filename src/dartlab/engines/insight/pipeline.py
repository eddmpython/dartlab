"""통합 분석 파이프라인."""

from __future__ import annotations

from typing import TYPE_CHECKING

from dartlab.engines.common.finance.ratios import calcRatios
from dartlab.engines.insight.anomaly import runAnomalyDetection
from dartlab.engines.insight.detector import detectFinancialSector
from dartlab.engines.insight.grading import (
    analyzeCashflow,
    analyzeGovernance,
    analyzeHealth,
    analyzeOpportunitySummary,
    analyzePerformance,
    analyzeProfitability,
    analyzeRiskSummary,
)
from dartlab.engines.insight.summary import classifyProfile, generateSummary
from dartlab.engines.insight.types import AnalysisResult
from dartlab.engines.sector.types import Sector

if TYPE_CHECKING:
    from dartlab.engines.dart.company import Company

SeriesPair = tuple[dict, list[str]]


def _ratio_archetype_override(company: Company | None) -> str | None:
    if company is None:
        return None

    try:
        from dartlab.engines.sector.types import IndustryGroup
    except ImportError:
        return None

    sectorInfo = getattr(company, "sector", None)
    industryGroup = getattr(sectorInfo, "industryGroup", None)
    mapping = {
        IndustryGroup.BANK: "bank",
        IndustryGroup.INSURANCE: "insurance",
        IndustryGroup.DIVERSIFIED_FINANCIALS: "securities",
    }
    return mapping.get(industryGroup)


def analyze(
    stockCode: str,
    company: Company | None = None,
    *,
    corpName: str | None = None,
    qSeriesPair: SeriesPair | None = None,
    aSeriesPair: SeriesPair | None = None,
) -> AnalysisResult | None:
    """종목 종합 인사이트 분석.

    Args:
        stockCode: 종목코드 또는 CIK.
        company: Company 인스턴스. None이고 series도 없으면 DART pivot 시도.
        corpName: 회사명. company가 없을 때 사용.
        qSeriesPair: (qSeries, qPeriods). None이면 DART pivot에서 빌드.
        aSeriesPair: (aSeries, aYears). None이면 DART pivot에서 빌드.

    Returns:
        AnalysisResult 또는 데이터 부족 시 None.
    """
    if qSeriesPair is None or aSeriesPair is None:
        from dartlab.engines.dart.finance.pivot import buildAnnual, buildTimeseries

        if qSeriesPair is None:
            qResult = buildTimeseries(stockCode)
            if qResult is None:
                return None
            qSeriesPair = qResult
        if aSeriesPair is None:
            aResult = buildAnnual(stockCode)
            if aResult is None:
                return None
            aSeriesPair = aResult

    qSeries, qPeriods = qSeriesPair
    aSeries, aYears = aSeriesPair
    ratios = calcRatios(aSeries, archetypeOverride=_ratio_archetype_override(company))

    if company is None and corpName is None:
        try:
            from dartlab.engines.dart.company import Company

            company = Company(stockCode)
        except ValueError:
            pass

    isFinancial, _ = detectFinancialSector(aSeries, ratios)

    sector = Sector.UNKNOWN
    if company is not None:
        sectorInfo = company.sector
        sector = sectorInfo.sector if sectorInfo else Sector.UNKNOWN

    insights = {}
    insights["performance"] = analyzePerformance(aSeries, aYears, qSeries, qPeriods, isFinancial)
    insights["profitability"] = analyzeProfitability(ratios, aSeries, isFinancial, sector=sector)
    insights["health"] = analyzeHealth(ratios, isFinancial)
    insights["cashflow"] = analyzeCashflow(ratios, aSeries, isFinancial)
    insights["governance"] = analyzeGovernance(company) if company else analyzeGovernance(None)
    insights["risk"] = analyzeRiskSummary(insights)
    insights["opportunity"] = analyzeOpportunitySummary(insights)

    anomalies = runAnomalyDetection(aSeries, isFinancial)

    resolvedName = corpName or (company.corpName if company else stockCode)
    grades = {k: v.grade for k, v in insights.items()}
    profile = classifyProfile(grades)
    summaryText = generateSummary(resolvedName, insights, anomalies, profile)

    return AnalysisResult(
        corpName=resolvedName,
        stockCode=stockCode,
        isFinancial=isFinancial,
        performance=insights["performance"],
        profitability=insights["profitability"],
        health=insights["health"],
        cashflow=insights["cashflow"],
        governance=insights["governance"],
        risk=insights["risk"],
        opportunity=insights["opportunity"],
        anomalies=anomalies,
        summary=summaryText,
        profile=profile,
    )
