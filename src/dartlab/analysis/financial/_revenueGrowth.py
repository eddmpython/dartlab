"""revenue.py 의 growth/concentration/contribution/flags 계산.

calcRevenueGrowth · calcConcentration · calcGrowthContribution · calcFlags.
"""

from __future__ import annotations

from dartlab.analysis.financial._revenueComposition import (
    _calcDomesticExportRatio,
    _calcHhiHistory,
    _getDocsRevenueVals,
)
from dartlab.analysis.financial._revenueSelect import (
    _MAX_SEGMENTS,
    _getRatios,
    _selectDocsRevenue,
)
from dartlab.core.memory import memoizedCalc


@memoizedCalc
def calcRevenueGrowth(company, *, basePeriod: str | None = None) -> dict | None:
    """매출 성장 지표.

    Parameters
    ----------
    company : Company
        분석 대상 기업.
    basePeriod : str, optional
        기준 기간.

    Returns
    -------
    dict | None
        yoy : float | None — 매출 전기대비 성장률 (%)
        cagr3y : float | None — 매출 3년 CAGR (%)
        quarterlySelect : SelectResult | None — 분기별 매출 원본

    Capabilities:
        - ratios.revenueGrowth + cagr3y + 분기 시계열 원본 통합
        - 분기 vs 연간 CAGR 교차 검증 (5%p 이상 차이 시 연간 우선)

    Guide:
        성장률 표준 진입. yoy ≥ 20% + cagr 매년 안정 = 강한 성장.

    When:
        Growth 평가 + AI 매출 성장률 답변.

    How:
        ratios → CAGR + annual 교차 검증 + 분기 select.

    Requires:
        IS 시계열 ≥ 4 분기.

    Raises:
        없음.

    Example:
        >>> calcRevenueGrowth(company)["yoy"]
        18.2

    See Also:
        - calcGrowthContribution : 부문 기여
        - growthAnalysis.* : 정밀 성장 분석

    AIContext:
        "성장률" 답변 시 yoy + cagr3y 인용.
    """
    ratios = _getRatios(company)
    yoy = getattr(ratios, "revenueGrowth", None) if ratios else None
    cagr = getattr(ratios, "revenueGrowth3Y", None) if ratios else None

    try:
        ann = company._buildFinanceSeries(freq="Y")
        if ann:
            from dartlab.core.utils.extract import getRevenueGrowth3Y

            annualCagr = getRevenueGrowth3Y(ann[0])
            if annualCagr is not None:
                if cagr is None:
                    cagr = annualCagr
                elif abs((cagr or 0) - annualCagr) > 5:
                    cagr = annualCagr
    except (ValueError, KeyError, AttributeError):
        pass

    quarterly = None
    try:
        result = company.select("IS", ["매출액"])
        if result is not None:
            quarterly = result
    except (ValueError, KeyError, AttributeError):
        pass

    if yoy is None and cagr is None and quarterly is None:
        return None

    return {"yoy": yoy, "cagr3y": cagr, "quarterlySelect": quarterly}


@memoizedCalc
def calcConcentration(company, *, basePeriod: str | None = None) -> dict | None:
    """매출 집중도.

    Parameters
    ----------
    company : Company
        분석 대상 기업.
    basePeriod : str, optional
        기준 기간.

    Returns
    -------
    dict | None
        hhi : float — 허핀달-허쉬만 지수
        hhiLabel : str — 집중도 판단 ("고집중"|"중간 집중"|"분산")
        topPct : float — 최대 부문 매출 비중 (%)
        domesticPct : float | None — 내수 비중 (%)
        hhiHistory : list | None — HHI 시계열
        hhiDirection : str — HHI 추세 방향

    Capabilities:
        - HHI (Herfindahl-Hirschman) 집중도 + 3 단계 라벨 + 최대 부문 비중 + 내수 비중
        - HHI 시계열 추세 (분산화/집중화)

    Guide:
        HHI > 5000 = 고집중 (단일 사업 위험), < 2500 = 분산. 추세 ↑ = 사업 집중화.

    When:
        Risk concentration + AI 사업 집중도 답변.

    How:
        부문별 매출 비중² 합 → HHI → 라벨링 + history.

    Requires:
        부문별 매출 데이터.

    Raises:
        없음.

    Example:
        >>> calcConcentration(company)["hhiLabel"]
        '중간 집중'

    See Also:
        - calcBreakdown : 지역/제품
        - calcSegmentComposition : 사업부문

    AIContext:
        "사업 집중도 위험" 답변 시 hhi + hhiLabel 인용.
    """
    revVals = _getDocsRevenueVals(company)
    if not revVals:
        return None

    total = sum(revVals)
    hhi = sum((v / total * 100) ** 2 for v in revVals)
    if hhi > 5000:
        hhiLabel = "고집중"
    elif hhi > 2500:
        hhiLabel = "중간 집중"
    else:
        hhiLabel = "분산"

    topPct = max(revVals) / total * 100
    domesticPct = _calcDomesticExportRatio(company)

    hhiResult = _calcHhiHistory(company)
    hhiHistory = None
    hhiDirection = "안정"
    if hhiResult is not None:
        hhiHistory, hhiDirection = hhiResult

    return {
        "hhi": hhi,
        "hhiLabel": hhiLabel,
        "topPct": topPct,
        "domesticPct": domesticPct,
        "hhiHistory": hhiHistory,
        "hhiDirection": hhiDirection,
    }


@memoizedCalc
def calcGrowthContribution(company, *, basePeriod: str | None = None) -> dict | None:
    """부문별 성장 기여 분해 — 성장이 어디에서 왔는가.

    Parameters
    ----------
    company : Company
        분석 대상 기업.
    basePeriod : str, optional
        기준 기간.

    Returns
    -------
    dict | None
        totalGrowthPct : float — 전체 매출 성장률 (%)
        contributions : list[dict]
            name : str — 부문명
            amount : float — 성장 기여 금액 (원)
            pct : float — 성장 기여 비중 (%)
        driver : str — 핵심 성장 동인 요약
        period : str — 비교 기간 ("2021 -> 2024")

    Capabilities:
        - 부문별 매출 변동 분해 → 성장 기여 % + 핵심 동인 식별
        - "이 회사 성장은 X 부문에서" 답변 출처

    Guide:
        contributions[0].pct ≥ 70% = 단일 부문 의존 성장 (다각화 부재).

    When:
        Story growth attribution + AI "어디서 성장" 답변.

    How:
        부문별 (end - start) → 합산 → 비중 정렬.

    Requires:
        부문별 다년 매출 데이터.

    Raises:
        없음.

    Example:
        >>> calcGrowthContribution(company)["driver"]
        '반도체 부문이 성장 65% 기여'

    See Also:
        - calcSegmentTrend : 부문 시계열
        - calcRevenueGrowth : 단일 yoy

    AIContext:
        "성장 동인" 답변 시 driver + contributions 인용.
    """
    docsResult = _selectDocsRevenue(company, basePeriod=basePeriod)
    if docsResult is None:
        return None

    segData, yCols = docsResult
    if len(yCols) < 2:
        return None

    curYear = yCols[0]
    baseIdx = min(3, len(yCols) - 1)
    baseYear = yCols[baseIdx]

    contributions = []
    totalCur = 0.0
    totalBase = 0.0

    for segName, vals in segData.items():
        cur = vals.get(curYear)
        base = vals.get(baseYear)
        if cur is None or base is None:
            continue

        totalCur += cur
        totalBase += base
        contributions.append({"name": segName, "amount": cur - base})

    if not contributions or totalBase == 0:
        return None

    totalChange = totalCur - totalBase
    totalGrowthPct = totalChange / totalBase * 100

    if totalChange == 0:
        for c in contributions:
            c["pct"] = 0.0
    else:
        for c in contributions:
            c["pct"] = c["amount"] / abs(totalChange) * 100

    contributions.sort(key=lambda x: abs(x["amount"]), reverse=True)
    contributions = contributions[:_MAX_SEGMENTS]

    top = contributions[0]
    topPct = abs(top["pct"])
    direction = "성장" if top["amount"] > 0 else "감소"
    driver = f"{top['name']}이(가) 전체 {direction}의 {topPct:.0f}% 기여"

    return {
        "totalGrowthPct": totalGrowthPct,
        "contributions": contributions,
        "driver": driver,
        "period": f"{baseYear} -> {curYear}",
    }


@memoizedCalc
def calcFlags(company, *, basePeriod: str | None = None) -> list[tuple[str, str]]:
    """수익 관련 경고/기회 플래그.

    Returns
    -------
    list[tuple[str, str]]
        각 원소는 (플래그 텍스트, "warning" | "opportunity").

    Capabilities:
        - HHI 집중도 + 성장률 + cagr 기반 자동 flag 누적
        - opportunity / warning 2 종 분류

    Guide:
        revenue 종합 위험/기회 플래그. flag ≥ 2 = 강한 시그널.

    When:
        Story revenue flag + AI 위험/기회 답변.

    How:
        HHI + revenueGrowth + cagr 임계 비교 → flags 누적.

    Requires:
        ratios + 매출 데이터.

    Raises:
        없음.

    Example:
        >>> calcFlags(company)
        [('매출 고성장 YoY +24%', 'opportunity')]

    See Also:
        - calcConcentration : HHI
        - calcRevenueGrowth : 성장률

    AIContext:
        "revenue 시그널" 답변 시 flag 인용.
    """
    flags: list[tuple[str, str]] = []

    revVals = _getDocsRevenueVals(company)
    if revVals:
        total = sum(revVals)
        hhi = sum((v / total * 100) ** 2 for v in revVals)
        if hhi > 5000:
            flags.append((f"매출 고집중 (HHI {hhi:,.0f}) -- 단일 부문 의존", "warning"))
        elif hhi > 2500:
            flags.append((f"매출 중간 집중 (HHI {hhi:,.0f})", "warning"))

    ratios = _getRatios(company)
    if ratios is not None:
        rg = getattr(ratios, "revenueGrowth", None)
        cagr = getattr(ratios, "revenueGrowth3Y", None)
        if rg is not None:
            if rg > 20:
                flags.append((f"매출 고성장 YoY +{rg:.0f}%", "opportunity"))
            elif rg < -10:
                flags.append((f"매출 역성장 YoY {rg:.0f}%", "warning"))
        if rg is not None and cagr is not None:
            if rg > 10 and cagr < 0:
                flags.append(
                    (
                        f"YoY +{rg:.0f}%이나 3Y CAGR {cagr:.0f}%: 반짝 회복 가능성",
                        "warning",
                    )
                )
            elif rg < -5 and cagr > 5:
                flags.append(
                    (
                        f"YoY {rg:.0f}%이나 3Y CAGR +{cagr:.0f}%: 일시적 둔화 가능성",
                        "opportunity",
                    )
                )

    return flags
