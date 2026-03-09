"""통합 분석 파이프라인."""

from __future__ import annotations

from typing import TYPE_CHECKING

from dartlab.engines.financeEngine.pivot import buildTimeseries, buildAnnual
from dartlab.engines.financeEngine.ratios import calcRatios
from dartlab.engines.insightEngine.anomaly import runAnomalyDetection
from dartlab.engines.insightEngine.detector import detectFinancialSector
from dartlab.engines.insightEngine.grading import (
    analyzeCashflow,
    analyzeGovernance,
    analyzeHealth,
    analyzeOpportunitySummary,
    analyzePerformance,
    analyzeProfitability,
    analyzeRiskSummary,
)
from dartlab.engines.insightEngine.summary import classifyProfile, generateSummary
from dartlab.engines.insightEngine.types import AnalysisResult

if TYPE_CHECKING:
    from dartlab.company import Company


def analyze(stockCode: str, company: Company | None = None) -> AnalysisResult | None:
    """종목 종합 인사이트 분석.

    Args:
        stockCode: 종목코드 (6자리).
        company: Company 인스턴스. None이면 내부에서 생성.

    Returns:
        AnalysisResult 또는 데이터 부족 시 None.
    """
    qResult = buildTimeseries(stockCode)
    aResult = buildAnnual(stockCode)
    if qResult is None or aResult is None:
        return None

    qSeries, qPeriods = qResult
    aSeries, aYears = aResult
    ratios = calcRatios(aSeries)

    if company is None:
        import dartlab
        company = dartlab.Company(stockCode)

    isFinancial, _ = detectFinancialSector(aSeries, ratios)

    insights = {}
    insights["performance"] = analyzePerformance(aSeries, aYears, qSeries, qPeriods, isFinancial)
    insights["profitability"] = analyzeProfitability(ratios, aSeries, isFinancial)
    insights["health"] = analyzeHealth(ratios, isFinancial)
    insights["cashflow"] = analyzeCashflow(ratios, aSeries, isFinancial)
    insights["governance"] = analyzeGovernance(company)
    insights["risk"] = analyzeRiskSummary(insights)
    insights["opportunity"] = analyzeOpportunitySummary(insights)

    anomalies = runAnomalyDetection(aSeries, isFinancial)

    grades = {k: v.grade for k, v in insights.items()}
    profile = classifyProfile(grades)
    summaryText = generateSummary(company.corpName, insights, anomalies, profile)

    return AnalysisResult(
        corpName=company.corpName,
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
