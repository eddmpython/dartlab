"""analyzePerformance — 매출/영업이익/순이익 5등급 분석."""

from __future__ import annotations

from dartlab.analysis.financial.insight._gradingScales import (
    _getGrowthYoY,
    _getVolatility,
    _predictabilityGrade,
    _scoreToGrade,
    _uncertaintyGrade,
)
from dartlab.analysis.financial.insight.benchmark import getBenchmark, sectorAdjustment
from dartlab.analysis.financial.insight.detector import detectIncompleteYear
from dartlab.analysis.financial.insight.types import Flag, InsightResult
from dartlab.analysis.financial.ratios import RatioResult
from dartlab.core.utils.extract import getAnnualValues, getLatest
from dartlab.frame.sector import Sector


def _revenueGrowthSignal(
    revGrowth: float,
    revLabel: str,
    details: list[str],
    risks: list[Flag],
    opps: list[Flag],
) -> int:
    """매출 성장률 구간별 설명 + 플래그.

    Parameters
    ----------
    revGrowth : float
        YoY 성장률 (%).
    revLabel : str
        '매출' 또는 금융업의 '영업이익'.
    details, risks, opps : list
        누적 구조. 제자리 변경.

    Returns
    -------
    int
        점수 증분.
    """
    if revGrowth > 20:
        details.append(f"{revLabel} 고성장 (+{revGrowth:.1f}%)")
        opps.append(Flag("strong", "growth", f"{revLabel} {revGrowth:.1f}% 성장"))
        return 3
    if revGrowth > 10:
        details.append(f"{revLabel} 성장세 양호 (+{revGrowth:.1f}%)")
        return 2
    if revGrowth > 0:
        details.append(f"{revLabel} 소폭 성장 (+{revGrowth:.1f}%)")
        return 1
    if revGrowth > -10:
        details.append(f"{revLabel} 소폭 감소 ({revGrowth:.1f}%)")
        return 0
    details.append(f"{revLabel} 급감 ({revGrowth:.1f}%)")
    risks.append(Flag("danger", "finance", f"{revLabel} {revGrowth:.1f}% 급감"))
    return -2


def _operatingGrowthSignal(
    opGrowth: float,
    details: list[str],
    risks: list[Flag],
    opps: list[Flag],
) -> int:
    """영업이익 성장률 구간별 설명 + 플래그.

    Parameters
    ----------
    opGrowth : float
        YoY 성장률 (%).
    details, risks, opps : list
        누적 구조. 제자리 변경.

    Returns
    -------
    int
        점수 증분.
    """
    if opGrowth > 50:
        details.append(f"영업이익 급증 (+{opGrowth:.1f}%)")
        opps.append(Flag("strong", "growth", f"영업이익 {opGrowth:.1f}% 급증"))
        return 3
    if opGrowth > 15:
        details.append(f"영업이익 증가 (+{opGrowth:.1f}%)")
        return 2
    if opGrowth < -30:
        details.append(f"영업이익 급감 ({opGrowth:.1f}%)")
        risks.append(Flag("danger", "finance", f"영업이익 {opGrowth:.1f}% 급감"))
        return -2
    if opGrowth < -10:
        details.append(f"영업이익 감소 ({opGrowth:.1f}%)")
        risks.append(Flag("warning", "finance", f"영업이익 {opGrowth:.1f}% 감소"))
        return -1
    return 0


def _performanceSummary(revGrowth: float | None, opGrowth: float | None, revLabel: str) -> str:
    """성장률 조합을 한 줄 요약으로.

    Parameters
    ----------
    revGrowth, opGrowth : float | None
        매출 / 영업이익 YoY 성장률 (%).
    revLabel : str
        '매출' 또는 '영업이익'.

    Returns
    -------
    str
        요약 문장.
    """
    if revGrowth is None:
        return "실적 데이터 부족"
    if revGrowth > 20 and opGrowth and opGrowth > 30:
        return f"{revLabel}·이익 고성장"
    if revGrowth > 10 and opGrowth and opGrowth > 10:
        return f"{revLabel}·이익 동반 성장"
    if revGrowth > 0:
        return f"{revLabel} 성장세 유지"
    if revGrowth > -10:
        return f"{revLabel} 정체"
    return f"{revLabel} 감소 추세"


def analyzePerformance(
    aSeries: dict,
    aYears: list[str],
    qSeries: dict,
    qPeriods: list[str],
    isFinancial: bool = False,
) -> InsightResult:
    """실적 성장성 — 매출 + 영업이익 YoY + 변동성 (불완전 연도 자동 제외).

    Capabilities:
        연간 매출/영업이익 YoY 성장률 + 분기 시계열 변동성 (max quarterly
        change) 결합. 불완전 연도 (현재 진행 중 1Q/2Q/3Q) 자동 감지 + 제외
        (detectIncompleteYear). 금융업은 매출 대신 영업이익 사용.

    Args:
        aSeries: 연간 재무 시계열 dict (IS).
        aYears: 연간 기간 라벨 리스트.
        qSeries: 분기 재무 시계열 dict.
        qPeriods: 분기 기간 라벨 리스트.
        isFinancial: 금융업 여부. True 면 영업이익 기반.

    Returns:
        InsightResult dataclass:
            - ``grade`` (str): A~F
            - ``summary`` (str): 한국어
            - ``details`` (list[str])
            - ``risks``/``opportunities`` (list[Flag])

    Raises:
        없음. revGrowth=None 시 grade='N'.

    Example:
        >>> r = analyzePerformance(aSeries, ["2021","2022","2023"], qSeries, qPeriods)
        >>> r.grade, r.summary
        ('A', '매출 고성장 +25%, 영업이익 동반 성장')

    Guide:
        매출 성장률 임계: >20% = 고성장 (+3 score), 10~20% = 양호 (+2),
        0~10% = 안정 (+1), -10~0% = 감소, < -10% = 급감 (-2 + danger).
        영업이익 +50%+ = 급증, < -30% = 급감. 변동성 30%+ = warning.

    When:
        analyzeFinancial 의 'performance' 키 산출 단계. 가장 먼저 호출.

    How:
        detectIncompleteYear 로 4Q 미완 제외 → revGrowth/opGrowth/volatility → score.

    SeeAlso:
        - ``analyzeProfitability``: 수익성 (성장 + 마진)
        - ``calcStructuralBreak``: 매출/영업이익 구조변화점 감지
        - ``detectIncompleteYear``: 불완전 연도 식별

    Requires:
        aSeries 의 IS/sales + IS/operating_profit 시계열 ≥ 2 년.

    AIContext:
        성장률 단독 인용 금지 — 변동성 + 영업이익 동반 성장 여부 함께. 불완전
        연도 (예 2024 3Q) 가 자동 제외되므로 분기 정확도 영향 없음.

    LLM Specifications:
        AntiPatterns:
            - 단년도 YoY 만으로 grade 단정 — 본 함수는 3 년 추세 가능 시 활용.
            - 매출 급감 (-10%) → automatic F — 일회성 (M&A 분할 등) 가능
              하므로 영업이익 동반 확인.
        OutputSchema:
            InsightResult ``{grade, summary, details, risks, opportunities}``.
        Prerequisites:
            IS 시계열 ≥ 2 년 + 분기 시계열 (변동성용).
        Freshness:
            최신 분기. 불완전 연도 자동 제외.
        Dataflow:
            IS → revGrowth/opGrowth/volatility → score 누적 → grade →
            risks/opps Flag 생성.
        TargetMarkets: KR (DART), US (EDGAR).
    """
    lastYear, qCount = detectIncompleteYear(qPeriods)
    incomplete = qCount < 4

    revVals = getAnnualValues(aSeries, "IS", "sales")
    opVals = getAnnualValues(aSeries, "IS", "operating_profit")

    if incomplete and len(aYears) > 1:
        useRevVals = revVals[:-1]
        useOpVals = opVals[:-1]
        correctionNote = f"(불완전연도 {lastYear} {qCount}Q 제외)"
    else:
        useRevVals = revVals
        useOpVals = opVals
        correctionNote = ""

    if isFinancial and not any(v is not None for v in useRevVals):
        useRevVals = useOpVals
        revLabel = "영업이익"
    else:
        revLabel = "매출"

    revGrowth = _getGrowthYoY(useRevVals)
    opGrowth = _getGrowthYoY(useOpVals)

    qRevVals = qSeries.get("IS", {}).get("sales", [])
    if isFinancial and not any(v is not None for v in qRevVals):
        qRevVals = qSeries.get("IS", {}).get("operating_profit", [])
    revVolatility = _getVolatility(qRevVals)
    qOpVals = qSeries.get("IS", {}).get("operating_profit", [])
    opVolatility = _getVolatility(qOpVals)

    details: list[str] = []
    risks: list[Flag] = []
    opps: list[Flag] = []
    score = 0

    if correctionNote:
        details.append(correctionNote)

    if revGrowth is not None:
        score += _revenueGrowthSignal(revGrowth, revLabel, details, risks, opps)

    if opGrowth is not None and not isFinancial:
        score += _operatingGrowthSignal(opGrowth, details, risks, opps)

    if revVolatility is not None and revVolatility > 30:
        details.append(f"{revLabel} 변동성 높음 (분기 최대 {revVolatility:.1f}%)")
        risks.append(Flag("warning", "finance", f"{revLabel} 변동성 {revVolatility:.1f}%"))

    if not isFinancial and opVolatility is not None and opVolatility > 50:
        details.append(f"영업이익 변동성 높음 (분기 최대 {opVolatility:.1f}%)")
        risks.append(Flag("warning", "finance", f"영업이익 변동성 {opVolatility:.1f}%"))

    grade = _scoreToGrade(score, 6)
    summary = _performanceSummary(revGrowth, opGrowth, revLabel)

    return InsightResult(grade, summary, details, risks, opps)


__all__ = ["analyzePerformance"]
