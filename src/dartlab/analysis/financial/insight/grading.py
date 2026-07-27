"""10영역 인사이트 등급 분석.

영역: performance, profitability, health, cashflow, governance, risk, opportunity,
      predictability, uncertainty, coreEarnings
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dartlab.analysis.financial.insight.benchmark import getBenchmark, sectorAdjustment
from dartlab.analysis.financial.insight.detector import detectIncompleteYear
from dartlab.analysis.financial.insight.types import Flag, InsightResult
from dartlab.analysis.financial.ratios import RatioResult
from dartlab.core.utils.extract import getAnnualValues, getLatest
from dartlab.frame.sector import Sector

if TYPE_CHECKING:
    from dartlab.core.protocols import CompanyProtocol as Company


from dartlab.analysis.financial.insight._gradingCashflow import _analyzeCashflowFinancial, analyzeCashflow
from dartlab.analysis.financial.insight._gradingForecast import (
    analyzeCoreEarnings,
    analyzePredictability,
    analyzeUncertainty,
    disclosureGapFlags,
)
from dartlab.analysis.financial.insight._gradingGovernance import (
    _analyzeGovernanceFromSections,
    analyzeGovernance,
)
from dartlab.analysis.financial.insight._gradingHealth import analyzeHealth
from dartlab.analysis.financial.insight._gradingPerformance import analyzePerformance
from dartlab.analysis.financial.insight._gradingProfitability import (
    _analyzeProfitabilityFinancial,
    analyzeProfitability,
)
from dartlab.analysis.financial.insight._gradingScales import (
    _getGrowthYoY,
    _getVolatility,
    _predictabilityGrade,
    _scoreToGrade,
    _uncertaintyGrade,
)


def analyzeRiskSummary(insights: dict[str, InsightResult]) -> InsightResult:
    """8 인사이트 영역 리스크 통합 — 가장 위험한 영역 강조 + 종합 등급.

    Capabilities:
        8 인사이트 영역 (performance/profitability/health/cashflow/governance/
        predictability/uncertainty/coreEarnings) 의 risks Flag 를 모두 합쳐
        통합. severity 가중 (danger 3 / warning 2 / info 1) 합산하여 종합
        리스크 등급 산출.

    Args:
        insights: 영역별 InsightResult dict. analyzePerformance/Profitability/
            Health/Cashflow/Governance/Predictability/Uncertainty/CoreEarnings
            결과를 키-값으로 보유.

    Returns:
        InsightResult:
            - ``grade`` (str): A (낮은 리스크) ~ F (높은 리스크)
            - ``summary`` (str): 한국어 요약
            - ``details`` (list[str]): danger/warning 플래그 텍스트
            - ``risks`` (list[Flag]): 8 영역 전체 합집합

    Raises:
        없음. 빈 insights dict 시 grade='N'.

    Example:
        >>> insights = {"health": analyzeHealth(ratios),
        ...             "cashflow": analyzeCashflow(...)}
        >>> r = analyzeRiskSummary(insights)
        >>> r.grade, len(r.risks)
        ('B', 3)

    Guide:
        리스크 가중치: danger=3, warning=2, info=1. 합산 0~3 = A, 4~6 = B,
        7~9 = C, 10~14 = D, 15+ = F. 가장 많은 danger 가 어디서 왔는지
        details 첫 라인에 명시.

    When:
        analyzeFinancial 마지막 단계. 8 영역 InsightResult 산출 직후 호출.

    How:
        영역 키 8 종 순회 → risks Flag 합집합 → severity 가중 합산 → grade 매핑.

    SeeAlso:
        - ``analyzeOpportunitySummary``: 반대 (강점 통합)
        - ``credit.engine.evaluateCompany``: 본 함수와 별도 신용 등급
        - 본 함수 호출자: ``Company.insights``

    Requires:
        insights dict 가 영역별 InsightResult.risks 보유.

    AIContext:
        risks 리스트는 사용자 향 직접 텍스트 — 모두 노출 권장 (truncate
        금지). grade 만 인용 시 위험 종류 (governance vs health) 정보 손실.

    LLM Specifications:
        AntiPatterns:
            - 단일 영역 (예 health) 만 보고 종합 리스크 판단 — 8 영역 합집합 권장.
            - 빈 risks 리스트 → A 등급 — 실제 데이터 부족일 수도 있으므로
              insights 키 개수 확인 함께.
        OutputSchema:
            InsightResult ``{grade, summary, details, risks}``.
        Prerequisites:
            insights dict 의 영역별 InsightResult (risks 필드 보유).
        Freshness:
            영역별 InsightResult freshness (최신 분기).
        Dataflow:
            8 영역 risks → severity 가중 합산 → grade 매핑 → details
            (danger 우선) 합성.
        TargetMarkets: KR + US. 영역별 분석에 따라 분기.
    """
    allRisks: list[Flag] = []
    for key in [
        "performance",
        "profitability",
        "health",
        "cashflow",
        "governance",
        "predictability",
        "uncertainty",
        "coreEarnings",
    ]:
        if key in insights and insights[key] is not None:
            allRisks.extend(insights[key].risks)

    if not allRisks:
        return InsightResult("A", "특별한 리스크 없음", ["주요 재무지표 양호"])

    dangerCount = sum(1 for r in allRisks if r.level == "danger")
    warningCount = sum(1 for r in allRisks if r.level == "warning")

    if dangerCount >= 2:
        grade = "F"
        summary = f"중대 리스크 {dangerCount}건"
    elif dangerCount == 1:
        grade = "D"
        summary = f"리스크 경고 (위험 {dangerCount}, 주의 {warningCount})"
    elif warningCount > 3:
        grade = "D"
        summary = f"다수 주의 ({warningCount}건)"
    elif warningCount > 1:
        grade = "C"
        summary = f"일부 주의 ({warningCount}건)"
    else:
        grade = "B"
        summary = "경미한 주의 사항"

    return InsightResult(grade, summary, [r.text for r in allRisks], allRisks)


def analyzeOpportunitySummary(insights: dict[str, InsightResult]) -> InsightResult:
    """기회 종합 분석.

    Capabilities:
        - 8 영역 InsightResult.opportunities Flag 합집합 → 강점/긍정 카운트
          → 종합 투자매력 등급 A~F 산출.

    Parameters
    ----------
    insights : dict[str, InsightResult]
        영역별 인사이트 결과.

    Returns
    -------
    InsightResult
        grade : str — 'A'~'F' 등급
        summary : str — 기회 종합 요약
        details : list[str] — 개별 기회 텍스트 목록
        opportunities : list[Flag] — 전체 기회 플래그 취합

    Guide:
        analyzeRiskSummary 와 대칭. 강점 (strong) + 긍정 (positive) 카운트 기반 등급.

    When:
        analyzeFinancial 후반. 8 영역 InsightResult 산출 직후 risk 와 함께 호출.

    How:
        영역 키 8 종 순회 → opportunities Flag 합 → strong/positive 카운트 → 등급 매핑.

    Requires:
        영역별 InsightResult.opportunities 보유.

    Raises:
        없음.

    Example:
        >>> analyzeOpportunitySummary({"health": ..., "cashflow": ...})
        InsightResult(grade='B', summary='투자 매력 있음 ...')

    See Also:
        - analyzeRiskSummary: 대칭 (위험 통합)
        - analyzeFinancial: 상위 호출자

    AIContext:
        ‘투자 강점’ 답변 시 opportunities 텍스트 직접 인용. truncate 금지.
    """
    allOpps: list[Flag] = []
    for key in [
        "performance",
        "profitability",
        "health",
        "cashflow",
        "governance",
        "predictability",
        "uncertainty",
        "coreEarnings",
    ]:
        if key in insights and insights[key] is not None:
            allOpps.extend(insights[key].opportunities)

    if not allOpps:
        return InsightResult("D", "특별한 투자 기회 없음")

    strongCount = sum(1 for o in allOpps if o.level == "strong")
    positiveCount = sum(1 for o in allOpps if o.level == "positive")
    total = strongCount + positiveCount

    if strongCount >= 3 and total >= 5:
        grade = "A"
        summary = f"투자 매력 높음 ({strongCount}강점, {positiveCount}긍정)"
    elif strongCount >= 2:
        grade = "B"
        summary = f"투자 매력 있음 ({strongCount}강점)"
    elif strongCount >= 1 or positiveCount >= 3:
        grade = "C"
        summary = f"일부 긍정 ({strongCount}강점, {positiveCount}긍정)"
    elif positiveCount >= 1:
        grade = "D"
        summary = f"긍정 요소 미약 ({positiveCount}건)"
    else:
        grade = "F"
        summary = "투자 매력 없음"

    return InsightResult(grade, summary, [o.text for o in allOpps], opportunities=allOpps)
