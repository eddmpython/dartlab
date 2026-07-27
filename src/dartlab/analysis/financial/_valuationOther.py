"""valuation.py 비-DCF cluster — calcResidualIncome · calcNavValuation · calcReverseImplied."""

from __future__ import annotations

from typing import Any

from dartlab.analysis.financial._valuationInputs import (
    _fetchPriceContext,
    _getSectorParams,
    _getSeriesAndShares,
)
from dartlab.analysis.valuation.residualIncome import calcResidualIncome as _rimCalc
from dartlab.core.memory import memoizedCalc

_HOLDING_SUBS: dict[str, list[tuple[str, float]]] = {
    "034730": [
        ("096770", 64.25),
        ("017670", 26.80),
        ("402340", 42.30),
    ],
    "003550": [
        ("373220", 30.10),
        ("051910", 33.30),
        ("066570", 33.67),
    ],
    "028260": [
        ("005930", 4.99),
        ("207940", 43.37),
    ],
    "005490": [
        ("005380", 5.20),
    ],
}


@memoizedCalc
def calcResidualIncome(company: Any, *, basePeriod: str | None = None) -> dict | None:
    """RIM (잔여이익모델) 밸류에이션.

    Returns
    -------
    dict
        bps : float — 주당순자산 (원)
        coe : float — 자기자본비용 (%)
        riHistory : list — 잔여이익 시계열 (원)
        intrinsicValue : float — 주당 내재가치 (원)
        upside : float — 상승여력 (%)
        terminalValue : float — 터미널가치 (원)
        warnings : list[str] — 경고 메시지
        currentPrice : float | None — 현재 주가 (원)
        currency : str — 통화 (KRW | USD)

    Capabilities:
        - BPS + 잔여이익 (ROE-COE) × 자본 → 내재가치 + 상승여력
        - Ohlson 1995 RIM 표준

    Guide:
        ROE > COE 가 지속 = 가치 창출 (intrinsic > BPS). 반대는 가치 파괴.

    When:
        RIM valuation + AI 자기자본 기반 답변.

    How:
        ``_rimCalc`` 위임 → 시계열 + 터미널 합산.

    Requires:
        BS 자기자본 + ROE 시계열 + beta.

    Raises:
        없음.

    Example:
        >>> calcResidualIncome(company)["intrinsicValue"]
        78000

    See Also:
        - calcDcf / calcDdm : 대안
        - _rimCalc : core

    AIContext:
        "RIM 적정가" 답변 시 intrinsicValue + upside 인용.
    """
    series, shares, currency = _getSeriesAndShares(company)
    sp = _getSectorParams(company)
    price = _fetchPriceContext(company)
    currentPrice = price["currentPrice"] if price else None
    beta = sp.beta if sp else None

    result = _rimCalc(
        series,
        shares=shares,
        currentPrice=currentPrice,
        currency=currency,
        beta=beta,
    )
    if result is None:
        return None

    return {
        "bps": result.bps,
        "coe": result.coe,
        "riHistory": result.riHistory,
        "intrinsicValue": result.intrinsicValue,
        "upside": result.upside,
        "terminalValue": result.terminalValue,
        "warnings": result.warnings,
        "currentPrice": currentPrice,
        "currency": currency,
    }


@memoizedCalc
def calcNavValuation(company: Any) -> dict | None:
    """지주사 NAV = Sum(상장 자회사 시총 x 지분율) - 순차입금. 할인 30%.

    Returns
    -------
    dict
        navGross : float — 할인 전 NAV (원)
        navDiscounted : float — 할인 후 NAV (원)
        navPerShare : float | None — 주당 NAV (원)
        holdingDiscount : float — 지주사 할인율 (0.30)
        subsidiaries : list[dict] — 자회사별 상세 (code, ratio(%), marketCap(원), value(원))
        netDebt : float — 순차입금 (원)

    Capabilities:
        - 상장 자회사 시총 × 지분율 합산 - 순차입금 → NAV. 한국 평균 30% 할인 적용
        - SK/LG/삼성/POSCO 4 지주사 매핑 SSOT

    Guide:
        한국 지주사 valuation 표준. holdingDiscount 30% 는 실증 평균 (Damodaran KR study).

    When:
        지주사 valuation + AI 지주사 답변.

    How:
        _HOLDING_SUBS lookup → 자회사 시총 fetch → 합산 - netDebt → 할인.

    Requires:
        _HOLDING_SUBS 에 등록된 종목.

    Raises:
        없음 — 미등록 시 None.

    Example:
        >>> calcNavValuation(Company("034730"))["navPerShare"]
        180000

    See Also:
        - _HOLDING_SUBS : 매핑 SSOT

    AIContext:
        "지주사 NAV" 답변 시 navPerShare + holdingDiscount 인용.
    """
    stockCode = getattr(company, "stockCode", "")
    subs = _HOLDING_SUBS.get(stockCode)
    if not subs:
        return None

    series, shares, currency = _getSeriesAndShares(company)

    totalSubValue = 0.0
    subDetails = []
    for subCode, ratio in subs:
        try:
            from dartlab.gather.infra.http import runAsync
            from dartlab.gather.sources.price import fetch

            snapshot = runAsync(fetch(subCode, market="KR"))
            if snapshot and snapshot.marketCap and snapshot.marketCap > 0:
                subValue = snapshot.marketCap * ratio / 100
                totalSubValue += subValue
                subDetails.append({"code": subCode, "ratio": ratio, "marketCap": snapshot.marketCap, "value": subValue})
        except (ImportError, OSError, RuntimeError, AttributeError):
            pass

    if totalSubValue <= 0:
        return None

    from dartlab.core.utils.extract import getLatest

    if series:
        stb = getLatest(series, "BS", "shortterm_borrowings") or 0
        ltb = getLatest(series, "BS", "longterm_borrowings") or 0
        bonds = getLatest(series, "BS", "debentures") or 0
        cash = getLatest(series, "BS", "cash_and_cash_equivalents") or 0
        netDebt = stb + ltb + bonds - cash
    else:
        netDebt = 0

    navGross = totalSubValue - netDebt
    navDiscounted = navGross * 0.70

    navPerShare = navDiscounted / shares if shares and shares > 0 else None

    return {
        "navGross": navGross,
        "navDiscounted": navDiscounted,
        "navPerShare": navPerShare,
        "holdingDiscount": 0.30,
        "subsidiaries": subDetails,
        "netDebt": netDebt,
    }


@memoizedCalc
def calcReverseImplied(company: Any, *, basePeriod: str | None = None) -> dict | None:
    """역내재성장률 -- 시장이 내재하는 매출 성장률 역산.

    Returns
    -------
    dict
        impliedGrowthRate : float — 내재 매출 성장률 (%)
        impliedRevenue : float — 내재 매출 (원)
        marketCap : float — 시가총액 (원)
        latestRevenue : float — 최신 매출 (원)
        assumedMargin : float — 가정 영업이익률 (%)
        assumedWacc : float — 가정 WACC (%)
        signal : str — 신호 ("overpriced" | "underpriced" | "fair")
        warnings : list[str] — 경고 메시지
        currentPrice : float | None — 현재 주가 (원)
        currency : str — 통화 (KRW | USD)

    Capabilities:
        - 시장 가격에서 역산한 implied 매출 성장률 + 시장 신호 (overpriced/underpriced/fair)
        - 가정한 margin/WACC 명시

    Guide:
        Mauboussin 2006 reverse DCF. impliedGrowth > 역사 평균 + 5% = 시장 과도 낙관.

    When:
        시장 가격 해석 + AI "시장이 얼마를 기대" 답변.

    How:
        market cap → reverseImpliedGrowth → 가정 WACC/margin 으로 역산.

    Requires:
        시가총액 + 매출 시계열.

    Raises:
        없음.

    Example:
        >>> calcReverseImplied(company)["impliedGrowthRate"]
        12.5

    See Also:
        - calcDcf : 정방향
        - priceImplied.reverseImpliedGrowth

    AIContext:
        "시장이 내재하는 성장률" 답변 시 impliedGrowthRate + signal 인용.
    """
    from dartlab.analysis.valuation.priceImplied import reverseImpliedGrowth

    series, shares, currency = _getSeriesAndShares(company)
    price = _fetchPriceContext(company)
    if not price or not price.get("marketCap"):
        return None

    result = reverseImpliedGrowth(series, marketCap=price["marketCap"])
    if result is None:
        return None

    return {
        "impliedGrowthRate": result.impliedGrowthRate,
        "impliedRevenue": result.impliedRevenue,
        "marketCap": result.marketCap,
        "latestRevenue": result.latestRevenue,
        "assumedMargin": result.assumedMargin,
        "assumedWacc": result.assumedWacc,
        "signal": result.signal,
        "warnings": result.warnings,
        "currentPrice": price.get("currentPrice"),
        "currency": currency,
    }
