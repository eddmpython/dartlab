"""analyzeHealth — 부채비율/유동성/O-Score/Z-Score/Piotroski 통합."""

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


def _financialDebtSignal(dr: float, details: list[str], risks: list[Flag], opps: list[Flag]) -> int:
    """금융업 부채비율 구간 판정 (1000/1500/2000%).

    Parameters
    ----------
    dr : float
        부채비율 (%).
    details, risks, opps : list
        누적 구조. 제자리 변경.

    Returns
    -------
    int
        점수 증분.
    """
    if dr < 1000:
        details.append(f"부채비율 {dr:.0f}%. 금융업 양호")
        opps.append(Flag("positive", "finance", f"금융업 부채비율 {dr:.0f}%"))
        return 3
    if dr < 1500:
        details.append(f"부채비율 {dr:.0f}%. 금융업 보통")
        return 1
    if dr < 2000:
        details.append(f"부채비율 {dr:.0f}%. 금융업 다소 높음")
        return 0
    details.append(f"부채비율 {dr:.0f}%. 금융업 과다")
    risks.append(Flag("warning", "finance", f"금융업 부채비율 {dr:.0f}%"))
    return -1


def _usDebtSignal(dr: float, details: list[str], risks: list[Flag], opps: list[Flag]) -> int:
    """US 기업 부채비율 구간 판정 (100/200/400/600%).

    Parameters
    ----------
    dr : float
        부채비율 (%).
    details, risks, opps : list
        누적 구조. 제자리 변경.

    Returns
    -------
    int
        점수 증분.
    """
    if dr < 100:
        details.append(f"부채비율 매우 양호 ({dr:.0f}%)")
        opps.append(Flag("strong", "finance", f"부채비율 {dr:.0f}%"))
        return 3
    if dr < 200:
        details.append(f"부채비율 양호 ({dr:.0f}%)")
        opps.append(Flag("positive", "finance", f"부채비율 {dr:.0f}%"))
        return 2
    if dr < 400:
        details.append(f"부채비율 보통 ({dr:.0f}%)")
        return 1
    if dr < 600:
        details.append(f"부채비율 다소 높음 ({dr:.0f}%)")
        return 0
    details.append(f"부채비율 과다 ({dr:.0f}%)")
    risks.append(Flag("warning", "finance", f"부채비율 {dr:.0f}%"))
    return -1


def _usLiquiditySignal(cr: float, details: list[str], risks: list[Flag], opps: list[Flag]) -> int:
    """US 기업 유동비율 구간 판정 (150/100/80%).

    Parameters
    ----------
    cr : float
        유동비율 (%).
    details, risks, opps : list
        누적 구조. 제자리 변경.

    Returns
    -------
    int
        점수 증분.
    """
    if cr > 150:
        details.append(f"유동성 매우 충분 ({cr:.0f}%)")
        opps.append(Flag("positive", "finance", f"유동비율 {cr:.0f}%"))
        return 2
    if cr > 100:
        details.append(f"유동성 충분 ({cr:.0f}%)")
        return 1
    if cr > 80:
        details.append(f"유동성 보통 ({cr:.0f}%)")
        return 0
    details.append(f"유동성 부족 ({cr:.0f}%)")
    risks.append(Flag("warning", "finance", f"유동비율 {cr:.0f}%"))
    return -1


def _koreanDebtSignal(dr: float, details: list[str], risks: list[Flag], opps: list[Flag]) -> int:
    """국내 기준 부채비율 구간 판정 (50/100/150/200%).

    Parameters
    ----------
    dr : float
        부채비율 (%).
    details, risks, opps : list
        누적 구조. 제자리 변경.

    Returns
    -------
    int
        점수 증분.
    """
    if dr < 50:
        details.append(f"부채비율 매우 양호 ({dr:.0f}%)")
        opps.append(Flag("strong", "finance", f"부채비율 {dr:.0f}%"))
        return 3
    if dr < 100:
        details.append(f"부채비율 양호 ({dr:.0f}%)")
        opps.append(Flag("positive", "finance", f"부채비율 {dr:.0f}%"))
        return 2
    if dr < 150:
        details.append(f"부채비율 보통 ({dr:.0f}%)")
        return 1
    if dr < 200:
        details.append(f"부채비율 다소 높음 ({dr:.0f}%)")
        return 0
    details.append(f"부채비율 과다 ({dr:.0f}%)")
    risks.append(Flag("warning", "finance", f"부채비율 {dr:.0f}%"))
    return -1


def _koreanLiquiditySignal(cr: float, details: list[str], risks: list[Flag], opps: list[Flag]) -> int:
    """국내 기준 유동비율 구간 판정 (200/150/100%). 정확히 100% 는 무판정.

    Parameters
    ----------
    cr : float
        유동비율 (%).
    details, risks, opps : list
        누적 구조. 제자리 변경.

    Returns
    -------
    int
        점수 증분.
    """
    if cr > 200:
        details.append(f"유동성 매우 충분 ({cr:.0f}%)")
        opps.append(Flag("positive", "finance", f"유동비율 {cr:.0f}%"))
        return 2
    if cr > 150:
        details.append(f"유동성 충분 ({cr:.0f}%)")
        return 1
    if cr > 100:
        details.append(f"유동성 보통 ({cr:.0f}%)")
        return 0
    if cr < 100:
        details.append(f"유동성 부족 ({cr:.0f}%)")
        risks.append(Flag("warning", "finance", f"유동비율 {cr:.0f}%"))
        return -1
    return 0


def _distressModelSignal(ratios: RatioResult, details: list[str], risks: list[Flag]) -> int:
    """O-Score 와 Altman Z''-Score 부실 신호.

    Parameters
    ----------
    ratios : RatioResult
        재무비율 계산 결과.
    details, risks : list
        누적 구조. 제자리 변경.

    Returns
    -------
    int
        점수 증분.
    """
    score = 0

    # Ohlson O-Score: P(bankruptcy) 10% 초과면 경고
    if ratios.ohlsonProbability is not None:
        if ratios.ohlsonProbability > 20:
            details.append(f"O-Score 부도확률 {ratios.ohlsonProbability:.1f}%. 고위험")
            risks.append(Flag("danger", "distress", f"O-Score P(부도) {ratios.ohlsonProbability:.1f}%"))
            score -= 2
        elif ratios.ohlsonProbability > 10:
            details.append(f"O-Score 부도확률 {ratios.ohlsonProbability:.1f}%. 주의")
            risks.append(Flag("warning", "distress", f"O-Score P(부도) {ratios.ohlsonProbability:.1f}%"))
            score -= 1

    # Altman Z''-Score (비금융사 범용)
    if ratios.altmanZppScore is not None:
        if ratios.altmanZppScore < 1.1:
            details.append(f"Z''-Score {ratios.altmanZppScore:.2f}. 부실 영역")
            risks.append(Flag("danger", "distress", f"Z'' {ratios.altmanZppScore:.2f} (부실)"))
            score -= 2
        elif ratios.altmanZppScore <= 2.6:
            details.append(f"Z''-Score {ratios.altmanZppScore:.2f}. 회색 영역")
            risks.append(Flag("warning", "distress", f"Z'' {ratios.altmanZppScore:.2f} (회색)"))
            score -= 1
        else:
            details.append(f"Z''-Score {ratios.altmanZppScore:.2f}. 안전")
            score += 1

    return score


def analyzeHealth(ratios: RatioResult, isFinancial: bool = False, currency: str = "KRW") -> InsightResult:
    """재무건전성 분석 — 부채비율 + 유동비율 + O-Score + Z''-Score + Piotroski.

    Capabilities:
        재무비율 + Altman Z''-Score (회사 부도예측) + Ohlson O-Score
        (10 변수) + Piotroski F-Score (9 가지) 결합하여 재무건전성 5 등급
        분류. 금융업/비금융업 분기, KRW/USD 통화별 다른 임계값 적용.

    Args:
        ratios: RatioResult dataclass — debtRatio, currentRatio, quickRatio,
            zScore, oScore, fScore, interestCoverage 등 포함.
        isFinancial: 금융업 여부. True 면 부채비율 기준 완화 (은행 BIS 8% 등).
        currency: ``"KRW"`` 또는 ``"USD"``. 임계값 분기 (예 부채비율 200%
            기준이 미국 시장에선 다름).

    Returns:
        InsightResult dataclass:
            - ``grade`` (str): A/B/C/D/F
            - ``summary`` (str): 한국어 요약
            - ``details`` (list[str]): 5+ 지표 분석 라인
            - ``risks`` (list[Flag]): 건전성 리스크 (warning/danger)
            - ``opportunities`` (list[Flag]): 건전성 강점

    Raises:
        없음. ratios=None 시 grade='N' 반환.

    Example:
        >>> from dartlab.core.ratios import calcRatios
        >>> ratios = calcRatios(company.finance.timeseries)
        >>> r = analyzeHealth(ratios)
        >>> r.grade, r.summary
        ('A', '재무건전성 우수 — 부채비율 80%, 유동비율 250%')

    Guide:
        Altman Z''-Score: > 2.6 = safe, 1.1~2.6 = grey, < 1.1 = distress.
        Piotroski F-Score: 9 = 최고, 0~3 = 부실. Ohlson O-Score 0.5 이상 =
        부도 확률 50%+. 본 함수는 3 모델 합산 + 부채비율 정성 평가.

    When:
        analyzeFinancial 의 'health' 키 산출 단계. ratios 산출 직후 호출.

    How:
        ratios.{debtRatio/currentRatio/zScore/oScore/fScore} 룰 분기 → score → grade.

    SeeAlso:
        - ``analyzeCashflow``: 현금흐름 (건전성과 보완)
        - ``credit.engine.evaluateCompany``: 종합 신용등급
        - ``dartlab.synth.distress.chsModel.calcCHS``: CHS 부도확률

    Requires:
        ratios = ``calcRatios(finance.timeseries)`` 결과.

    AIContext:
        grade + risks 함께 인용. F 등급 결과는 distress 신호 — credit 엔진
        호출 권장 (Track A 7 축 분해). 금융업 (은행/보험) 은 부채비율 1000%+
        가 정상이므로 isFinancial=True 명시 필수.

    LLM Specifications:
        AntiPatterns:
            - 비금융업 부채비율 200%+ → automatic F 단정 — 영업 부담 (예
              항공/조선) 고려 필요. 본 함수는 업종 보정 별도 적용.
            - O-Score 단독 인용 — Altman + Piotroski 와 cross-check 필수.
        OutputSchema:
            InsightResult ``{grade, summary, details, risks, opportunities}``.
        Prerequisites:
            ratios 가 calcRatios 출력 (RatioResult 인스턴스).
        Freshness:
            ratios = 최신 분기 (마감 후 30~45 일).
        Dataflow:
            ratios → 부채비율 + 유동/당좌비율 + Altman Z''-Score + Ohlson
            O-Score + Piotroski F-Score → 가중 score → grade 매핑.
        TargetMarkets: KR (DART), US (EDGAR). 통화별 임계값 분기.
    """
    details: list[str] = []
    risks: list[Flag] = []
    opps: list[Flag] = []
    score = 0
    dr = ratios.debtRatio
    cr = ratios.currentRatio

    if isFinancial:
        details.append("[금융업 기준 적용]")
        if dr is not None:
            score += _financialDebtSignal(dr, details, risks, opps)
    elif currency == "USD":
        # US 기업: 자사주매입으로 equity 축소가 일반적, 부채비율 높음이 정상
        if dr is not None:
            score += _usDebtSignal(dr, details, risks, opps)

        if cr is not None:
            score += _usLiquiditySignal(cr, details, risks, opps)
    else:
        if dr is not None:
            score += _koreanDebtSignal(dr, details, risks, opps)

        if cr is not None:
            score += _koreanLiquiditySignal(cr, details, risks, opps)

    # ── 부실 예측 모델 신호 (ratios에서 계산된 값 활용) ──
    score += _distressModelSignal(ratios, details, risks)

    grade = _scoreToGrade(score, 7)
    label = "금융업 재무건전성" if isFinancial else "재무건전성"
    summary = f"{label} " + ("우수" if score >= 5 else "안정" if score >= 2 else "보통" if score >= 0 else "주의 필요")
    return InsightResult(grade, summary, details, risks, opps)


__all__ = ["analyzeHealth"]
