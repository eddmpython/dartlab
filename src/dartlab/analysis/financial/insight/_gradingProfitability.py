"""analyzeProfitability — 마진율/ROE/ROIC 5등급 분석 (일반 + 금융)."""

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


def _operatingMarginSignal(om: float, details: list[str], risks: list[Flag], opps: list[Flag]) -> int:
    """영업이익률 구간 판정 (20/10/5/0%).

    Parameters
    ----------
    om : float
        영업이익률 (%).
    details, risks, opps : list
        누적 구조. 제자리 변경.

    Returns
    -------
    int
        점수 증분.
    """
    if om > 20:
        details.append(f"영업이익률 우수 ({om:.1f}%)")
        opps.append(Flag("strong", "finance", f"영업이익률 {om:.1f}%"))
        return 3
    if om > 10:
        details.append(f"영업이익률 양호 ({om:.1f}%)")
        return 2
    if om > 5:
        details.append(f"영업이익률 보통 ({om:.1f}%)")
        return 1
    if om < 0:
        details.append(f"영업적자 ({om:.1f}%)")
        risks.append(Flag("danger", "finance", f"영업이익률 {om:.1f}%. 적자"))
        return -2
    details.append(f"영업이익률 저조 ({om:.1f}%)")
    return -1


def _marginGapSignal(om: float, nm: float, details: list[str], risks: list[Flag], opps: list[Flag]) -> None:
    """영업이익률과 순이익률 괴리 해석. 점수에는 영향 없다.

    Parameters
    ----------
    om, nm : float
        영업이익률, 순이익률 (%).
    details, risks, opps : list
        누적 구조. 제자리 변경.
    """
    gap = nm - om
    gapRatio = (gap / abs(om)) * 100
    if abs(gapRatio) > 50:
        if gap > 0:
            details.append(f"영업외수익 발생 (순이익률 {nm:.1f}% > 영업이익률 {om:.1f}%)")
            risks.append(Flag("warning", "finance", "본업 외 수익에 의존"))
        else:
            details.append(f"영업외비용 발생 (순이익률 {nm:.1f}% < 영업이익률 {om:.1f}%)")
            risks.append(Flag("warning", "finance", "영업외비용 확인 필요"))
    elif abs(gap) < 2 and nm > 0:
        details.append("영업이익≈순이익. 본업 중심 수익구조")
        opps.append(Flag("positive", "finance", "건전한 수익구조"))


def _roeSignal(roe: float, details: list[str], opps: list[Flag]) -> int:
    """ROE 구간 판정 (20/10/5%).

    Parameters
    ----------
    roe : float
        자기자본이익률 (%).
    details, opps : list
        누적 구조. 제자리 변경.

    Returns
    -------
    int
        점수 증분.
    """
    if roe > 20:
        details.append(f"ROE 우수 ({roe:.1f}%)")
        opps.append(Flag("strong", "finance", f"ROE {roe:.1f}%"))
        return 2
    if roe > 10:
        details.append(f"ROE 양호 ({roe:.1f}%)")
        return 1
    if roe < 5:
        details.append(f"ROE 저조 ({roe:.1f}%)")
    return 0


def _leverageSignal(
    roe: float,
    roa: float,
    isFinancial: bool,
    details: list[str],
    risks: list[Flag],
    opps: list[Flag],
) -> None:
    """ROE/ROA 배수로 레버리지 해석. 점수에는 영향 없다.

    Parameters
    ----------
    roe, roa : float
        자기자본이익률, 총자산이익률 (%). roa 는 양수 보장.
    isFinancial : bool
        금융업 여부.
    details, risks, opps : list
        누적 구조. 제자리 변경.
    """
    leverage = roe / roa
    if isFinancial:
        # 금융업은 구조적으로 레버리지가 높음 (예수부채). 경고 대상이 아님
        details.append(f"금융업 레버리지 {leverage:.1f}x (구조적 특성)")
    elif leverage > 4:
        details.append(f"높은 레버리지로 ROE 달성 (ROE/ROA={leverage:.1f}x)")
        risks.append(Flag("warning", "finance", f"ROE/ROA {leverage:.1f}x. 부채 활용 높음"))
    elif leverage < 1.5 and roe > 15:
        details.append("낮은 레버리지로 고ROE. 진성 수익성")
        opps.append(Flag("strong", "finance", f"레버리지 {leverage:.1f}x로 ROE {roe:.1f}%"))


def _sectorAdjustmentSignal(
    om: float | None,
    roe: float | None,
    sector: Sector,
    market: str,
    details: list[str],
) -> int:
    """섹터 중앙값 대비 OM/ROE 보정.

    Parameters
    ----------
    om, roe : float | None
        영업이익률, ROE (%).
    sector : Sector
        업종.
    market : str
        시장 ('KR' | 'US').
    details : list
        누적 구조. 제자리 변경.

    Returns
    -------
    int
        점수 증분.
    """
    bm = getBenchmark(sector, market)
    omAdj = sectorAdjustment(om, bm.omMedian, bm.omQ1, bm.omQ3)
    roeAdj = sectorAdjustment(roe, bm.roeMedian, bm.roeQ1, bm.roeQ3)
    adj = omAdj + roeAdj
    if adj == 0:
        return 0
    direction = "상향" if adj > 0 else "하향"
    omArrow = "↑" if omAdj > 0 else "↓" if omAdj < 0 else "→"
    roeArrow = "↑" if roeAdj > 0 else "↓" if roeAdj < 0 else "→"
    details.append(f"[섹터 보정 {direction}: {sector.value} 대비 OM{omArrow} ROE{roeArrow}]")
    return adj


def analyzeProfitability(
    ratios: RatioResult,
    aSeries: dict,
    isFinancial: bool = False,
    sector: Sector = Sector.UNKNOWN,
    market: str = "KR",
) -> InsightResult:
    """수익성 분석 — 영업이익률 + ROE + ROA + 섹터 보정 + DuPont 분해.

    Capabilities:
        영업이익률 + 순이익률 (NM-OM 갭으로 영업외 영향 분석) + ROE + ROA
        + 섹터 벤치마크 보정 (sectorAdjustment) 결합. 금융업은 별도 함수
        (_analyzeProfitabilityFinancial). GICS 섹터별 다른 임계값 (IT 30%+,
        utility 5%+ 등).

    Args:
        ratios: RatioResult dataclass (operatingMargin, netMargin, roe, roa).
        aSeries: 연간 재무 시계열 dict.
        isFinancial: 금융업 여부. True 면 분기.
        sector: GICS 섹터 (Sector enum). 섹터 벤치마크 보정 입력.
        market: ``"KR"``/``"US"``. 벤치마크 선택 (KR/US 시장 ROE 평균 다름).

    Returns:
        InsightResult dataclass:
            - ``grade`` (str): A~F
            - ``summary`` (str)
            - ``details`` (list[str]): 영업이익률 + ROE + 레버리지 + 갭
            - ``risks``/``opportunities`` (list[Flag])

    Raises:
        없음.

    Example:
        >>> r = analyzeProfitability(ratios, aSeries, sector=Sector.IT, market="KR")
        >>> r.grade
        'A'  # IT 섹터 영업이익률 28%, ROE 22%

    Guide:
        영업이익률 임계 (비금융): > 20% = 우수 (+3), 10~20% = 양호 (+2),
        5~10% = 보통 (+1), 0~5% = 저조 (-1), < 0% = 적자 (-2). ROE > 15% =
        우수, > 10% = 양호. 섹터 보정으로 IT/utility 차이 반영.

    When:
        analyzeFinancial 의 'profitability' 키 산출 단계. ratios 산출 직후 호출.

    How:
        ratios.{operatingMargin/netMargin/roe/roa} 임계 분기 + sectorAdjustment 가산점.

    SeeAlso:
        - ``analyzePerformance``: 성장성 (수익성과 보완)
        - ``analyzeHealth``: 재무건전성 (ROE/레버리지 cross-check)
        - ``getBenchmark``: 섹터 벤치마크 룩업

    Requires:
        ratios = calcRatios 결과. sector enum (Sector.UNKNOWN 도 가능).

    AIContext:
        섹터별 임계값 차이 큼 — IT 영업이익률 20%+ 가 평균이지만 utility 는
        5%+ 가 우수. grade 만 인용 금지, 섹터 벤치마크 비교 함께.

    LLM Specifications:
        AntiPatterns:
            - 섹터 무시하고 절대 임계값 사용 — IT 의 5% 영업이익률을 "보통"
              평가하는 건 부정확 (IT 평균 25%+ 대비 매우 낮음).
            - 적자 회사를 자동 F — 신규 IPO 또는 turnaround 회사는 분기마다
              개선 추세 확인 필수.
        OutputSchema:
            InsightResult ``{grade, summary, details, risks, opportunities}``.
        Prerequisites:
            ratios (operatingMargin, netMargin, roe, roa) + sector enum.
        Freshness:
            최신 분기.
        Dataflow:
            ratios → 임계 + 섹터 보정 (getBenchmark) → score 누적 → grade.
        TargetMarkets: KR (DART), US (EDGAR). 섹터/market 별 분기.
    """
    details: list[str] = []
    risks: list[Flag] = []
    opps: list[Flag] = []
    score = 0

    if isFinancial:
        return _analyzeProfitabilityFinancial(aSeries, details, risks, opps)

    om = ratios.operatingMargin
    nm = ratios.netMargin
    roe = ratios.roe
    roa = ratios.roa

    if om is not None:
        score += _operatingMarginSignal(om, details, risks, opps)

    if om is not None and nm is not None and om != 0:
        _marginGapSignal(om, nm, details, risks, opps)

    if roe is not None:
        score += _roeSignal(roe, details, opps)

    if roe is not None and roa is not None and roa > 0:
        _leverageSignal(roe, roa, isFinancial, details, risks, opps)

    score += _sectorAdjustmentSignal(om, roe, sector, market, details)

    grade = _scoreToGrade(score, 5)
    summary = "수익성 " + ("우수" if score >= 4 else "양호" if score >= 2 else "보통" if score >= 0 else "개선 필요")
    return InsightResult(grade, summary, details, risks, opps)


def _analyzeProfitabilityFinancial(
    aSeries: dict,
    details: list[str],
    risks: list[Flag],
    opps: list[Flag],
) -> InsightResult:
    """금융업 전용 수익성 분석 (ROE/ROA/CIR).

    Parameters
    ----------
    aSeries : dict
        연간 재무 시계열.
    details : list[str]
        세부 항목 리스트 (in-place 추가).
    risks : list[Flag]
        리스크 플래그 리스트 (in-place 추가).
    opps : list[Flag]
        기회 플래그 리스트 (in-place 추가).

    Returns
    -------
    InsightResult
        grade : str — 'A'~'F' 등급
        summary : str — 금융업 수익성 요약
        details : list[str] — ROE, ROA, CIR 세부 항목
        risks : list[Flag] — 금융업 수익성 리스크
        opportunities : list[Flag] — 금융업 수익성 강점
    """
    details.append("[금융업 수익성 기준 적용]")
    score = 0
    netIncome = getLatest(aSeries, "IS", "net_profit")
    totalAssets = getLatest(aSeries, "BS", "total_assets")
    totalEquity = getLatest(aSeries, "BS", "owners_of_parent_equity") or getLatest(
        aSeries, "BS", "total_stockholders_equity"
    )
    opIncome = getLatest(aSeries, "IS", "operating_profit")
    opExpense = getLatest(aSeries, "IS", "operating_expense")

    roe = (netIncome / totalEquity) * 100 if netIncome and totalEquity and totalEquity > 0 else None
    roa = (netIncome / totalAssets) * 100 if netIncome and totalAssets and totalAssets > 0 else None
    cir = (
        (opExpense / (opExpense + opIncome)) * 100
        if opExpense is not None and opIncome is not None and (opExpense + opIncome) != 0
        else None
    )

    if roe is not None:
        if roe > 10:
            details.append(f"ROE 우수 ({roe:.1f}%)")
            opps.append(Flag("strong", "finance", f"금융업 ROE {roe:.1f}%"))
            score += 3
        elif roe > 8:
            details.append(f"ROE 양호 ({roe:.1f}%)")
            score += 2
        elif roe > 5:
            details.append(f"ROE 보통 ({roe:.1f}%)")
            score += 1
        else:
            details.append(f"ROE 저조 ({roe:.1f}%)")
            risks.append(Flag("warning", "finance", f"금융업 ROE {roe:.1f}%"))

    if roa is not None:
        if roa > 0.7:
            details.append(f"ROA 양호 ({roa:.2f}%)")
            score += 1
        elif roa > 0.4:
            details.append(f"ROA 보통 ({roa:.2f}%)")
        elif roa > 0:
            details.append(f"ROA 저조 ({roa:.2f}%)")
        else:
            details.append(f"ROA 적자 ({roa:.2f}%)")
            risks.append(Flag("danger", "finance", f"금융업 ROA {roa:.2f}%"))
            score -= 2

    if cir is not None:
        if cir < 50:
            details.append(f"CIR {cir:.1f}% — 효율적 운영")
            opps.append(Flag("positive", "finance", f"CIR {cir:.1f}%"))
            score += 1
        elif cir < 60:
            details.append(f"CIR {cir:.1f}% — 보통")
        else:
            details.append(f"CIR {cir:.1f}% — 비효율")
            risks.append(Flag("warning", "finance", f"CIR {cir:.1f}%"))

    grade = _scoreToGrade(score, 5)
    summary = "금융업 수익성 " + (
        "우수" if score >= 4 else "양호" if score >= 2 else "보통" if score >= 0 else "개선 필요"
    )
    return InsightResult(grade, summary, details, risks, opps)


__all__ = ["analyzeProfitability", "_analyzeProfitabilityFinancial"]
