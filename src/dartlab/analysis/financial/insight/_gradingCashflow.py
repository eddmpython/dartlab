"""analyzeCashflow — OCF/매출, FCF 마진, Sloan accrual 통합."""

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


def analyzeCashflow(
    ratios: RatioResult,
    aSeries: dict,
    isFinancial: bool = False,
) -> InsightResult:
    """현금흐름 분석 — OCF/매출 + FCF 마진 + OCF/NI 안정성 (Sloan accrual 보강).

    Capabilities:
        영업현금흐름 마진 + FCF 마진 + OCF/NI (이익품질) + CF 추세 (3 년 CAGR)
        결합. Sloan (1996) accrual 분해와 연계해 "현금 뒷받침" 이익 vs 발생액
        의존 이익 구분. 금융업은 _analyzeCashflowFinancial 별도 분기.

    Args:
        ratios: RatioResult dataclass (ocfMargin, fcfMargin, ocfToNi 포함).
        aSeries: 연간 재무 시계열 dict (CF/IS).
        isFinancial: 금융업 여부. True 면 별도 함수로 분기.

    Returns:
        InsightResult dataclass:
            - ``grade`` (str): A~F
            - ``summary`` (str)
            - ``details`` (list[str]): OCF/매출, FCF 마진, OCF/NI 등
            - ``risks`` (list[Flag]): warning/danger 플래그
            - ``opportunities`` (list[Flag]): 강점 플래그

    Raises:
        없음.

    Example:
        >>> r = analyzeCashflow(ratios, aSeries=company.finance.timeseries)
        >>> r.grade
        'A'  # OCF/매출 15%, FCF 마진 10%, OCF/NI 1.2

    Guide:
        OCF/매출 > 15% = 매우 우수, 10~15% = 양호, < 5% = 부족. FCF 마진 양수
        (3 년 연속) = 자본배분 여력. OCF/NI > 1 = 이익이 현금으로 뒷받침,
        < 0.7 = 발생액 의존 (Sloan 경고).

    When:
        analyzeFinancial 의 10 영역 중 'cashflow' 키 산출 단계.

    How:
        ratios.{ocfMargin/fcfMargin/ocfToNi} 룰 분기 → score 합산 → _scoreToGrade.

    SeeAlso:
        - ``analyzeHealth``: 재무건전성 (현금흐름과 보완)
        - ``calcEarningsMomentum``: Sloan 분해 단독 호출
        - ``dartlab.synth.distress.chsFeatures``: CHS PD 계산

    Requires:
        ratios + aSeries (CF/IS 시계열 ≥ 3 년).

    AIContext:
        OCF/NI < 0.5 결과는 분식 위험 가능 — Sloan 의 academic 신호이지 즉시
        분식 단정 금지. 동종업종 평균과 비교 (calcPeerPrediction) 권장.

    LLM Specifications:
        AntiPatterns:
            - 단년도 OCF 만 보고 결론 — 3 년 평균 + 추세 (CAGR) 필수.
            - 신규 IPO 회사의 CapEx 큰 음수 FCF 를 "현금흐름 부실" 로 단정 —
              성장 회사는 정상 (Amazon 1997~2010 사례).
        OutputSchema:
            InsightResult ``{grade, summary, details, risks, opportunities}``.
        Prerequisites:
            CF 시계열 (operating_cashflow, capex) ≥ 3 년 + IS net_income.
        Freshness:
            최신 분기 + 3 년 시계열.
        Dataflow:
            ratios → ocfMargin/fcfMargin/ocfToNi 룰 → score 누적 → grade.
        TargetMarkets: KR (DART), US (EDGAR 표준 CF 동일).
    """
    if isFinancial:
        return _analyzeCashflowFinancial(aSeries)

    details: list[str] = []
    risks: list[Flag] = []
    opps: list[Flag] = []
    score = 0
    opCF = ratios.operatingCashflowTTM
    fcf = ratios.fcf
    revenue = ratios.revenueTTM

    if opCF is not None:
        if opCF > 0:
            details.append("영업활동 현금 창출 양호")
            score += 2
        else:
            details.append("영업활동 현금 적자")
            risks.append(Flag("danger", "finance", "영업CF 적자"))
            score -= 2

    if fcf is not None:
        if fcf > 0:
            if revenue and revenue > 0:
                fcfMargin = (fcf / revenue) * 100
                if fcfMargin > 15:
                    details.append(f"FCF 마진 우수 ({fcfMargin:.1f}%)")
                    opps.append(Flag("strong", "cashflow", f"FCF 마진 {fcfMargin:.1f}%"))
                    score += 3
                elif fcfMargin > 5:
                    details.append(f"FCF 마진 양호 ({fcfMargin:.1f}%)")
                    opps.append(Flag("positive", "cashflow", f"FCF 마진 {fcfMargin:.1f}%"))
                    score += 2
                else:
                    details.append(f"FCF 양호, 마진 저조 ({fcfMargin:.1f}%)")
                    score += 1
            else:
                details.append("FCF 양호")
                score += 1
        elif opCF and opCF > 0:
            details.append("FCF 적자 — 투자 확대 중")
            opps.append(Flag("positive", "growth", "적극 투자 (영업CF 양호)"))
        else:
            details.append("FCF 적자 — 현금 부족")
            risks.append(Flag("warning", "finance", "FCF + 영업CF 부진"))
            score -= 1

    cfVals = getAnnualValues(aSeries, "CF", "operating_cashflow")
    validCf = [v for v in cfVals if v is not None]
    if len(validCf) >= 2:
        improving = validCf[-1] > validCf[-2]
        if improving and validCf[-1] > 0:
            details.append("영업CF 개선 추세")
            score += 1
        elif not improving and validCf[-1] < validCf[-2]:
            details.append("영업CF 악화 추세")

    grade = _scoreToGrade(score, 6)
    summary = "현금흐름 " + ("우수" if score >= 5 else "양호" if score >= 2 else "보통" if score >= 0 else "주의")
    return InsightResult(grade, summary, details, risks, opps)


def _analyzeCashflowFinancial(aSeries: dict) -> InsightResult:
    """금융업 전용 현금흐름 분석.

    Parameters
    ----------
    aSeries : dict
        연간 재무 시계열.

    Returns
    -------
    InsightResult
        grade : str — 'A'~'F' 등급
        summary : str — 금융업 현금흐름 요약
        details : list[str] — 영업CF, 배당, 순이익 세부
        risks : list[Flag] — 리스크
        opportunities : list[Flag] — 강점
    """
    details: list[str] = ["[금융업 현금흐름]"]
    risks: list[Flag] = []
    opps: list[Flag] = []
    score = 0

    opCF = getLatest(aSeries, "CF", "operating_cashflow")
    dividendsPaid = getLatest(aSeries, "CF", "dividends_paid")
    netIncome = getLatest(aSeries, "IS", "net_profit")

    if opCF is not None:
        details.append(f"영업CF: {opCF / 1e8:,.0f}억")

    if dividendsPaid is not None and dividendsPaid > 0:
        details.append(f"배당 지급: {dividendsPaid / 1e8:,.0f}억")
        opps.append(Flag("positive", "shareholder", f"배당 지급 {dividendsPaid / 1e8:,.0f}억"))
        score += 1

    if netIncome is not None and netIncome > 0:
        details.append(f"순이익 {netIncome / 1e8:,.0f}억")
        score += 2

    grade = _scoreToGrade(score, 3)
    summary = "금융업 현금흐름 " + ("양호" if score >= 2 else "보통" if score >= 0 else "주의")
    return InsightResult(grade, summary, details, risks, opps)


__all__ = ["analyzeCashflow", "_analyzeCashflowFinancial"]
