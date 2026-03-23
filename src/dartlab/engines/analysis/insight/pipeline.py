"""통합 분석 파이프라인."""

from __future__ import annotations

from typing import TYPE_CHECKING

from dartlab.engines.analysis.insight.anomaly import detectAuditRedFlags, runAnomalyDetection
from dartlab.engines.analysis.insight.detector import detectFinancialSector
from dartlab.engines.analysis.insight.distress import calcDistress
from dartlab.engines.analysis.insight.grading import (
    analyzeCashflow,
    analyzeGovernance,
    analyzeHealth,
    analyzeOpportunitySummary,
    analyzePerformance,
    analyzeProfitability,
    analyzeRiskSummary,
)
from dartlab.engines.analysis.insight.summary import classifyProfile, generateSummary
from dartlab.engines.analysis.insight.types import AnalysisResult, Anomaly, AuditDataForAnomaly, MarketDataForDistress
from dartlab.engines.analysis.sector.types import Sector
from dartlab.engines.common.finance.ratios import calcRatios

if TYPE_CHECKING:
    from dartlab.engines.company.dart.company import Company

SeriesPair = tuple[dict, list[str]]


def _extractAuditData(company: Company | None) -> AuditDataForAnomaly | None:
    """Company에서 감사 데이터를 추출하여 AuditDataForAnomaly DTO 생성."""
    if company is None:
        return None

    rpt = getattr(company, "report", None)
    if rpt is None:
        return None

    auditors: list[str | None] = []
    opinions: list[str | None] = []
    fees: list[float | None] = []
    kamCounts: list[int | None] = []
    hasGoingConcern = False
    hasInternalControlWeakness = False

    # docs 파이프라인 감사 데이터 (opinionDf, feeDf)
    try:
        auditResult = getattr(rpt, "audit", None)
        if auditResult is not None:
            # Report API 기반: auditors, opinions 시계열
            rawAuditors = getattr(auditResult, "auditors", None)
            rawOpinions = getattr(auditResult, "opinions", None)
            if rawAuditors:
                auditors = list(rawAuditors)
            if rawOpinions:
                opinions = list(rawOpinions)

            # docs 기반: opinionDf (KAM, goingConcern 포함)
            opDf = getattr(auditResult, "opinionDf", None)
            if opDf is not None and len(opDf) > 0:
                # KAM 건수 추출
                if "keyAuditMatters" in opDf.columns:
                    for row in opDf.iter_rows(named=True):
                        kam = row.get("keyAuditMatters")
                        if kam and isinstance(kam, str) and len(kam.strip()) > 0:
                            kamCounts.append(kam.count(",") + 1)
                        else:
                            kamCounts.append(0)

                # goingConcern 확인 (최신기)
                if "goingConcern" in opDf.columns:
                    latestGc = opDf.row(-1, named=True).get("goingConcern")
                    if latestGc and isinstance(latestGc, str) and len(latestGc.strip()) > 0:
                        hasGoingConcern = True

                # opinionDf에서 auditors/opinions 보강 (Report API 없을 때)
                if not auditors and "auditor" in opDf.columns:
                    auditors = opDf["auditor"].to_list()
                if not opinions and "opinion" in opDf.columns:
                    opinions = opDf["opinion"].to_list()

            # feeDf에서 보수 추출
            feeDf = getattr(auditResult, "feeDf", None)
            if feeDf is not None and len(feeDf) > 0:
                feeCol = (
                    "actualFee"
                    if "actualFee" in feeDf.columns
                    else "contractFee"
                    if "contractFee" in feeDf.columns
                    else None
                )
                if feeCol:
                    fees = feeDf[feeCol].to_list()
    except (AttributeError, TypeError):
        pass

    # 내부통제 취약점
    try:
        ic = getattr(rpt, "internalControl", None)
        if ic is not None:
            controlDf = getattr(ic, "controlDf", None)
            if controlDf is not None and len(controlDf) > 0:
                latestRow = controlDf.row(-1, named=True)
                if latestRow.get("hasWeakness"):
                    hasInternalControlWeakness = True
    except (AttributeError, IndexError):
        pass

    # 데이터가 하나도 없으면 None
    if (
        not auditors
        and not opinions
        and not fees
        and not kamCounts
        and not hasGoingConcern
        and not hasInternalControlWeakness
    ):
        return None

    return AuditDataForAnomaly(
        auditors=auditors,
        opinions=opinions,
        fees=fees,
        kamCounts=kamCounts,
        hasGoingConcern=hasGoingConcern,
        hasInternalControlWeakness=hasInternalControlWeakness,
    )


def _ratio_archetype_override(company: Company | None) -> str | None:
    if company is None:
        return None

    try:
        from dartlab.engines.analysis.sector.types import IndustryGroup
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
    marketData: MarketDataForDistress | None = None,
    currency: str | None = None,
) -> AnalysisResult | None:
    """종목 종합 인사이트 분석.

    Args:
        stockCode: 종목코드 또는 CIK.
        company: Company 인스턴스. None이고 series도 없으면 DART pivot 시도.
        corpName: 회사명. company가 없을 때 사용.
        qSeriesPair: (qSeries, qPeriods). None이면 DART pivot에서 빌드.
        aSeriesPair: (aSeries, aYears). None이면 DART pivot에서 빌드.
        marketData: 시장 기반 부실 분석 입력. None이면 4축, 제공 시 Merton 5축.
        currency: 통화 코드. None이면 company에서 자동 추출 (기본 KRW).

    Returns:
        AnalysisResult 또는 데이터 부족 시 None.
    """
    if qSeriesPair is None or aSeriesPair is None:
        from dartlab.engines.company.dart.finance.pivot import buildAnnual, buildTimeseries

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

    # currency 자동 추출: company에서 가져오거나 기본 KRW
    if currency is None:
        currency = getattr(company, "currency", "KRW")
    market = "US" if currency == "USD" else "KR"

    ratios = calcRatios(aSeries, archetypeOverride=_ratio_archetype_override(company), currency=currency)

    if company is None and corpName is None:
        try:
            from dartlab.engines.company.dart.company import Company

            company = Company(stockCode)
        except ValueError:
            pass

    isFinancial, _ = detectFinancialSector(aSeries, ratios)

    sector = Sector.UNKNOWN
    if company is not None:
        sectorInfo = getattr(company, "sector", None)
        sector = sectorInfo.sector if sectorInfo else Sector.UNKNOWN

    insights = {}
    insights["performance"] = analyzePerformance(aSeries, aYears, qSeries, qPeriods, isFinancial)
    insights["profitability"] = analyzeProfitability(ratios, aSeries, isFinancial, sector=sector, market=market)
    insights["health"] = analyzeHealth(ratios, isFinancial, currency=currency)
    insights["cashflow"] = analyzeCashflow(ratios, aSeries, isFinancial)
    insights["governance"] = analyzeGovernance(company) if company else analyzeGovernance(None)
    insights["risk"] = analyzeRiskSummary(insights)
    insights["opportunity"] = analyzeOpportunitySummary(insights)

    # 감사 데이터 추출 (Company가 있을 때만)
    auditData = _extractAuditData(company) if company is not None else None
    anomalies = runAnomalyDetection(aSeries, isFinancial, auditData=auditData)

    # Merton 시장 기반 모델 (비금융 + marketData 제공 시)
    mertonResult = None
    if not isFinancial and marketData is not None:
        try:
            from dartlab.engines.common.finance.merton import calcEquityVolatility, solveMerton

            vol = calcEquityVolatility(marketData.dailyReturns)
            if vol > 0:
                mertonResult = solveMerton(
                    equityValue=marketData.marketCap,
                    debtFaceValue=ratios.totalLiabilities or 0,
                    equityVolatility=vol,
                    riskFreeRate=marketData.riskFreeRate,
                )
        except ImportError:
            pass  # scipy 미설치 → Merton 축 제외, 4축으로 동작

    distress = calcDistress(ratios, anomalies, isFinancial, mertonResult=mertonResult)

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
        distress=distress,
        summary=summaryText,
        profile=profile,
    )


def analyzeAudit(company) -> list[Anomaly]:
    """감사 Red Flag만 단독 분석."""
    auditData = _extractAuditData(company)
    return detectAuditRedFlags(auditData)
