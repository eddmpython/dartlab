"""valuation.py DCF cluster — calcDcf · calcDdm · calcRelativeValuation · calcSensitivity."""

from __future__ import annotations

from typing import Any

from dartlab.analysis.financial._valuationInputs import (
    _fetchPriceContext,
    _getSectorParams,
    _getSeriesAndShares,
)
from dartlab.core.memory import memoizedCalc


@memoizedCalc
def calcDcf(
    company: Any,
    *,
    basePeriod: str | None = None,
    overrides: dict | None = None,
) -> dict | None:
    """DCF (현금흐름 할인) 밸류에이션.

    Parameters
    ----------
    overrides : dict | None
        AI/사용자 가정 override. wacc, terminalGrowth 키 지원.

    Returns
    -------
    dict
        perShareValue : float — 주당 적정가 (원)
        enterpriseValue : float — 기업가치 (원)
        equityValue : float — 자기자본가치 (원)
        discountRate : float — 할인율 (%)
        growthRateInitial : float — 초기 성장률 (%)
        terminalGrowth : float — 영구성장률 (%)
        marginOfSafety : float — 안전마진 (%)
        fcfProjections : list — FCF 예측 시계열 (원)
        fcfHistorical : list — FCF 과거 시계열 (원)
        exitMultipleTv : float — 출구배수 기반 터미널가치 (원)
        exitMultipleEv : float — 출구배수 기반 기업가치 (원)
        exitMultiplePerShare : float — 출구배수 기반 주당가치 (원)
        assumptions : dict — 가정 파라미터
        warnings : list[str] — 경고 메시지
        currentPrice : float | None — 현재 주가 (원)
        currency : str — 통화 (KRW | USD)
        overrideApplied : dict | None — 적용된 override (있으면)

    Capabilities:
        - 5 년 FCF projection + 영구가치 (terminal) → DCF intrinsic value
        - overrides 로 WACC/terminalGrowth 가정 변경 가능

    Guide:
        Damodaran DCF 표준. marginOfSafety ≥ 30% = 저평가.

    When:
        Valuation + AI DCF 답변.

    How:
        ``dcfValuation`` 위임 → overrides 적용 → 결과 dict.

    Requires:
        IS/CF 시계열 + WACC 추정.

    Raises:
        없음.

    Example:
        >>> calcDcf(company)["perShareValue"]
        82000

    See Also:
        - calcDdm : 배당 기반
        - calcRelativeValuation : 상대

    AIContext:
        "DCF 적정가" 답변 시 perShareValue + marginOfSafety 인용.
    """
    from dartlab.analysis.valuation.dcf import dcfValuation
    from dartlab.synth.overrides import applyOverride

    ov = overrides or {}

    series, shares, currency = _getSeriesAndShares(company)
    sp = _getSectorParams(company)
    price = _fetchPriceContext(company)
    currentPrice = price["currentPrice"] if price else None
    marketCap = price["marketCap"] if price else None

    from dartlab.analysis.financial.proforma import computeCompanyWacc

    wacc, _ = computeCompanyWacc(
        series,
        sectorParams=sp,
        marketCap=marketCap,
        currency=currency,
    )
    wacc = applyOverride(wacc, "wacc", ov)

    pfFCF = None
    try:
        from dartlab.analysis.financial.forecastCalcs import calcProFormaHighlights

        pf = calcProFormaHighlights(company, basePeriod=basePeriod)
        if pf and pf.get("years"):
            pfFCF = [yr["fcf"] for yr in pf["years"] if yr.get("fcf") is not None]
            if not pfFCF:
                pfFCF = None
    except (ImportError, AttributeError, ValueError, TypeError, KeyError):
        pfFCF = None

    tg_override = ov.get("terminalGrowth")
    dcf_kwargs: dict[str, Any] = {
        "shares": shares,
        "sectorParams": sp,
        "currentPrice": currentPrice,
        "currency": currency,
        "discountRate": wacc,
        "proformaFCF": pfFCF,
    }
    if tg_override is not None:
        dcf_kwargs["terminalGrowth"] = tg_override * 100 if tg_override <= 1 else tg_override

    result = dcfValuation(series, **dcf_kwargs)
    out: dict[str, Any] = {
        "perShareValue": result.perShareValue,
        "enterpriseValue": result.enterpriseValue,
        "equityValue": result.equityValue,
        "discountRate": result.discountRate,
        "growthRateInitial": result.growthRateInitial,
        "terminalGrowth": result.terminalGrowth,
        "marginOfSafety": result.marginOfSafety,
        "fcfProjections": result.fcfProjections,
        "fcfHistorical": result.fcfHistorical,
        "exitMultipleTv": result.exitMultipleTv,
        "exitMultipleEv": result.exitMultipleEv,
        "exitMultiplePerShare": result.exitMultiplePerShare,
        "assumptions": result.assumptions,
        "warnings": result.warnings,
        "currentPrice": currentPrice,
        "currency": currency,
    }
    if ov:
        out["overrideApplied"] = {k: v for k, v in ov.items() if k in ("wacc", "terminalGrowth")}
    return out


@memoizedCalc
def calcDdm(company: Any, *, basePeriod: str | None = None) -> dict | None:
    """DDM (배당 할인) 밸류에이션.

    calcDividendPolicy의 연간 배당 데이터를 우선 사용하여
    분기 CF 합산 오류를 방지한다.

    Returns
    -------
    dict
        intrinsicValue : float — 주당 내재가치 (원)
        dividendPerShare : float — 주당배당금 (원)
        dividendYield : float — 배당수익률 (%)
        payoutRatio : float — 배당성향 (%)
        dividendGrowth : float — 배당 성장률 (%)
        modelUsed : str — 사용 모델 ("Gordon" | "H-Model" | "N/A")
        discountRate : float — 할인율 (%)
        warnings : list[str] — 경고 메시지
        currentPrice : float | None — 현재 주가 (원)
        currency : str — 통화 (KRW | USD)

    Capabilities:
        - Gordon / H-Model 자동 선택 + dividend growth + discount rate → 주당 내재가치
        - calcDividendPolicy 연간 배당 사용 (분기 합산 오류 회피)

    Guide:
        배당주 (payout > 30% 안정) 한정 적용. 무배당/저배당은 calcDcf 사용.

    When:
        DDM valuation + AI 배당주 평가 답변.

    How:
        capitalAllocation.calcDividendPolicy → annual DPS → ddmValuation 모델 호출.

    Requires:
        배당 시계열 + WACC.

    Raises:
        없음.

    Example:
        >>> calcDdm(company)["intrinsicValue"]
        76000

    See Also:
        - calcDcf : FCF 기반
        - capitalAllocation.calcDividendPolicy : 입력

    AIContext:
        "DDM 적정가" 답변 시 intrinsicValue + modelUsed 인용.
    """
    from dartlab.analysis.financial.capitalAllocation import calcDividendPolicy
    from dartlab.analysis.valuation.dcf import ddmValuation

    series, shares, currency = _getSeriesAndShares(company)
    sp = _getSectorParams(company)
    price = _fetchPriceContext(company)
    currentPrice = price["currentPrice"] if price else None

    annualDivs: list[float] | None = None
    try:
        stockCode = getattr(company, "stockCode", None)
        divResult = None
        if divResult and divResult.dps:
            validDps = [d for d in divResult.dps if d is not None and d > 0]
            if validDps and shares and shares > 0:
                annualDivs = [dps * shares for dps in validDps]
    except (ImportError, ValueError, KeyError, AttributeError, RuntimeError, OSError):
        pass

    if not annualDivs:
        divPolicy = calcDividendPolicy(company, basePeriod=basePeriod)
        if divPolicy and divPolicy.get("history"):
            hist = divPolicy["history"]
            minDiv = shares * 100 if shares and shares > 0 else 1e9
            annualDivs = [
                h["dividendsPaid"] for h in reversed(hist) if h.get("dividendsPaid") and h["dividendsPaid"] > minDiv
            ]

    result = ddmValuation(
        series,
        shares=shares,
        sectorParams=sp,
        currentPrice=currentPrice,
        annualDividends=annualDivs,
    )
    if result.modelUsed == "N/A" and not result.warnings:
        return None

    return {
        "intrinsicValue": result.intrinsicValue,
        "dividendPerShare": result.dividendPerShare,
        "dividendYield": result.dividendYield,
        "payoutRatio": result.payoutRatio,
        "dividendGrowth": result.dividendGrowth,
        "modelUsed": result.modelUsed,
        "discountRate": result.discountRate,
        "warnings": result.warnings,
        "currentPrice": currentPrice,
        "currency": currency,
    }


@memoizedCalc
def calcRelativeValuation(company: Any, *, basePeriod: str | None = None) -> dict | None:
    """상대가치 (PER/PBR/EV-EBITDA/PSR/PEG) 밸류에이션.

    Returns
    -------
    dict
        sectorMultiples : dict — 업종 평균 멀티플 (PER, PBR 등) (배수)
        currentMultiples : dict — 현재 멀티플 (배수)
        impliedValues : dict — 멀티플별 내재가치 (원)
        premiumDiscount : dict — 업종 대비 할인/프리미엄 (%)
        consensusValue : float — 합의 적정가 (원)
        warnings : list[str] — 경고 메시지
        currentPrice : float | None — 현재 주가 (원)
        currency : str — 통화 (KRW | USD)

    Capabilities:
        - PER/PBR/EV-EBITDA/PSR/PEG 5 멀티플 동시 → 업종 대비 premium/discount + consensus
        - 멀티플별 implied value 산출

    Guide:
        업종 대비 -30% 이상 discount = 저평가. consensusValue = 5 멀티플 평균.

    When:
        상대 valuation + AI 업종 대비 답변.

    How:
        sector multiples + 현재 멀티플 → implied per/pbr/etc. → consensus.

    Requires:
        sector params + 현재 가격.

    Raises:
        없음.

    Example:
        >>> calcRelativeValuation(company)["consensusValue"]
        72000

    See Also:
        - calcDcf : DCF
        - sector params

    AIContext:
        "업종 대비 valuation" 답변 시 premiumDiscount + consensusValue 인용.
    """
    from dartlab.analysis.valuation.dcf import relativeValuation

    series, shares, currency = _getSeriesAndShares(company)
    sp = _getSectorParams(company)
    price = _fetchPriceContext(company)
    marketCap = price["marketCap"] if price else None
    currentPrice = price["currentPrice"] if price else None

    result = relativeValuation(
        series,
        sectorParams=sp,
        marketCap=marketCap,
        shares=shares,
        currentPrice=currentPrice,
    )
    return {
        "sectorMultiples": result.sectorMultiples,
        "currentMultiples": result.currentMultiples,
        "impliedValues": result.impliedValues,
        "premiumDiscount": result.premiumDiscount,
        "consensusValue": result.consensusValue,
        "warnings": result.warnings,
        "currentPrice": currentPrice,
        "currency": currency,
    }


@memoizedCalc
def calcSensitivity(company: Any, *, basePeriod: str | None = None) -> dict | None:
    """WACC x 영구성장률 민감도 그리드.

    Returns
    -------
    dict
        grid : list[list[float]] — WACC x 영구성장률 주가 그리드 (원)
        baseWacc : float — 기준 WACC (%)
        baseTerminalGrowth : float — 기준 영구성장률 (%)
        baseValue : float — 기준 주가 (원)
        currentPrice : float | None — 현재 주가 (원)
        currency : str — 통화 (KRW | USD)

    Capabilities:
        - WACC × terminalGrowth 2D 그리드로 DCF 결과 sensitivity
        - 가정 변동 시 주가 범위 표시

    Guide:
        ±1%p 변동 grid → 가정 민감도 시각화. 셀 간격 큼 = high sensitivity.

    When:
        Valuation 가정 검증 + AI "가정 변하면" 답변.

    How:
        ``sensitivityAnalysis`` 위임 → grid 산출.

    Requires:
        DCF 기본 가정.

    Raises:
        없음.

    Example:
        >>> calcSensitivity(company)["baseValue"]
        82000

    See Also:
        - calcDcf : base case
        - sensitivityAnalysis

    AIContext:
        "가정 민감도" 답변 시 grid range 인용.
    """
    from dartlab.analysis.valuation.dcf import sensitivityAnalysis

    series, shares, currency = _getSeriesAndShares(company)
    sp = _getSectorParams(company)
    price = _fetchPriceContext(company)
    currentPrice = price["currentPrice"] if price else None

    result = sensitivityAnalysis(
        series,
        shares=shares,
        sectorParams=sp,
        currentPrice=currentPrice,
        currency=currency,
    )
    if result is None:
        return None

    return {
        "grid": result.grid,
        "baseWacc": result.baseWacc,
        "baseTerminalGrowth": result.baseTerminalGrowth,
        "baseValue": result.baseValue,
        "currentPrice": currentPrice,
        "currency": currency,
    }
