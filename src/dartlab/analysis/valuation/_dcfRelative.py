"""상대가치 + 청산가치 + 민감도 분석 — dcf.py 에서 분리."""

from __future__ import annotations

from typing import Optional

from dartlab.analysis.valuation._dcfInputs import (
    _epsGrowth3Y,
    _estimateSectorPsr,
    _getNetDebt,
    _normalizedEarnings,
)
from dartlab.analysis.valuation._dcfTypes import RelativeValuationResult, SensitivityResult
from dartlab.core.utils.extract import getLatest, getTTM
from dartlab.frame.sector import SectorParams

_LIQUIDATION_RECOVERY = {
    "cash": 1.00,
    "receivables": 0.70,
    "inventory": 0.50,
    "tangible": 0.60,
    "intangible": 0.10,
    "other": 0.40,
}


def liquidationValuation(
    *,
    cash: float = 0.0,
    receivables: float = 0.0,
    inventory: float = 0.0,
    tangibleAssets: float = 0.0,
    intangibleAssets: float = 0.0,
    otherAssets: float = 0.0,
    totalLiabilities: float = 0.0,
    shares: int | None = None,
    recoveryOverrides: dict | None = None,
) -> dict:
    """Damodaran 청산가치 — 자산별 회수율 차등.

    Capabilities:
        - 자산별 차등 회수율 (cash 100%/AR 70%/inventory 50%/tangible 60%/intangible 10%)
        - gross recovery - 부채 = 주주 몫
        - recoveryOverrides 로 회수율 사용자 조정 가능

    Parameters
    ----------
    cash, receivables, inventory, tangibleAssets, intangibleAssets, otherAssets : float
        자산별 장부가 (원).
    totalLiabilities : float
        총 부채.
    shares : int, optional
        발행주식수.
    recoveryOverrides : dict, optional
        자산별 회수율 override.

    Returns
    -------
    dict
        recoveries : dict — 자산별 회수 금액
        grossRecovery : float — 총 자산 회수 합
        netToEquity : float — 부채 상환 후 잔여
        perShare : float | None
        weightedRecoveryRate : float — 가중 평균 회수율 (0.0~1.0)

    Example:
        >>> liquidationValuation(cash=1e9, tangibleAssets=5e9, totalLiabilities=4e9, shares=1e7)
        {"netToEquity": ..., "perShare": ..., ...}

    Guide:
        netToEquity ≤ 0 시 perShare=None — 청산 시 주주 몫 없음.

    When:
        decline phase 또는 distress 회사의 floor value 산출.

    How:
        liquidationValuation(cash=c, tangibleAssets=t, ..., totalLiabilities=L, shares=s).

    Requires:
        외부 의존 없음 — pure function.

    Raises:
        없음.

    See Also:
        - calcDFV : 본 함수를 floor 로 사용
        - Damodaran *Dark Side of Valuation* Ch.9

    AIContext:
        청산가치 답변 시 자산별 회수금액 + weightedRecoveryRate 인용.
    """
    recovery = dict(_LIQUIDATION_RECOVERY)
    if recoveryOverrides:
        recovery.update(recoveryOverrides)

    components = {
        "cash": cash * recovery["cash"],
        "receivables": receivables * recovery["receivables"],
        "inventory": inventory * recovery["inventory"],
        "tangible": tangibleAssets * recovery["tangible"],
        "intangible": intangibleAssets * recovery["intangible"],
        "other": otherAssets * recovery["other"],
    }
    gross = sum(components.values())
    net_to_equity = gross - totalLiabilities
    per_share = (net_to_equity / shares) if (shares and shares > 0 and net_to_equity > 0) else None

    gross_raw = cash + receivables + inventory + tangibleAssets + intangibleAssets + otherAssets
    weighted_rate = gross / gross_raw if gross_raw > 0 else 0.0

    return {
        "recoveries": components,
        "grossRecovery": gross,
        "netToEquity": net_to_equity,
        "perShare": per_share,
        "weightedRecoveryRate": weighted_rate,
        "recoveryRates": recovery,
    }


def relativeValuation(
    series: dict,
    sectorParams: Optional[SectorParams] = None,
    marketCap: Optional[float] = None,
    shares: Optional[int] = None,
    currentPrice: Optional[float] = None,
) -> RelativeValuationResult:
    """섹터 배수 기반 상대가치 추정 (Normalized Earnings 지원).

    Capabilities:
        - 5 멀티플 (PER/PBR/EV/EBITDA/PSR/PEG) 동시 산출 + 가중평균 consensusValue
        - Normalized Earnings (과거 평균 ROE × 현재 BPS) 자동 사용 옵션
        - 멀티플별 가중치 (EV/EBITDA 3.0 / PER 2.5 / PBR 1.5 / PSR 1.0 / PEG 1.0)

    Parameters
    ----------
    series : dict
        finance.timeseries dict.
    sectorParams : SectorParams, optional
        업종별 배수 (PER/PBR/EV/EBITDA 등).
    marketCap : float, optional
        시가총액.
    shares : int, optional
        발행주식수.
    currentPrice : float, optional
        현재 주가.

    Returns
    -------
    RelativeValuationResult
        sectorMultiples, currentMultiples, impliedValues, premiumDiscount,
        consensusValue, warnings.

    Example:
        >>> r = relativeValuation(series, sectorParams=sp, marketCap=4.5e14, shares=5e9)
        >>> r.consensusValue

    Guide:
        impliedValue 가 현재가의 5배 초과 시 outlier 제거. 양수 implied 만 가중평균.

    When:
        DCF 대안 / 신생기업 / 사이클 회사의 멀티플 기반 가치평가 시.

    How:
        relativeValuation(series, sectorParams=sp, marketCap=mc, shares=s, currentPrice=p).

    Requires:
        getTTM/getLatest (IS/BS/CF) + SectorParams.

    Raises:
        없음.

    See Also:
        - dcfValuation : 현금흐름 기반
        - calcDFV : 다중 모델 통합

    AIContext:
        멀티플 기반 가치 답변 시 currentMultiples 와 sectorMultiples 비교 노출.
    """
    warnings: list[str] = []
    sp = sectorParams or SectorParams(
        discountRate=10.0,
        growthRate=3.0,
        perMultiple=15,
        pbrMultiple=1.2,
        evEbitdaMultiple=8,
        label="기타",
    )

    sectorMults: dict[str, float] = {
        "PER": sp.perMultiple,
        "PBR": sp.pbrMultiple,
        "EV/EBITDA": sp.evEbitdaMultiple,
    }

    netIncome = getTTM(series, "IS", "net_profit") or getTTM(series, "IS", "net_income")
    equity = getLatest(series, "BS", "total_stockholders_equity") or getLatest(series, "BS", "owners_of_parent_equity")
    revenue = getTTM(series, "IS", "sales") or getTTM(series, "IS", "revenue")

    normNi, normEps, useNormalized = _normalizedEarnings(series, shares)
    if useNormalized and normNi is not None:
        netIncome = normNi
        warnings.append("정규화 수익 적용 (과거 평균 ROE x 현재 BPS)")

    multKeys = ["PER", "PBR", "EV/EBITDA", "PSR", "PEG"]
    currentMults: dict[str, Optional[float]] = {k: None for k in multKeys}
    if marketCap and marketCap > 0:
        if netIncome and netIncome > 0:
            currentMults["PER"] = round(marketCap / netIncome, 1)
        if equity and equity > 0:
            currentMults["PBR"] = round(marketCap / equity, 1)
        if revenue and revenue > 0:
            currentMults["PSR"] = round(marketCap / revenue, 2)

    implied: dict[str, Optional[float]] = {k: None for k in multKeys}
    premiumDisc: dict[str, Optional[float]] = {k: None for k in multKeys}

    if shares and shares > 0:
        if netIncome is not None and netIncome > 0:
            eps = netIncome / shares
            implied["PER"] = round(eps * sp.perMultiple, 0)

        if equity is not None and equity > 0:
            bps = equity / shares
            implied["PBR"] = round(bps * sp.pbrMultiple, 0)

        oi = getTTM(series, "IS", "operating_profit") or getTTM(series, "IS", "operating_income")
        dep = getTTM(series, "CF", "depreciation_and_amortization")
        if oi is not None and oi > 0:
            if dep is None:
                ta = getLatest(series, "BS", "tangible_assets") or 0
                ia = getLatest(series, "BS", "intangible_assets") or 0
                dep = ta * 0.05 + ia * 0.1
                warnings.append("감가상각 미확인 -> 추정치 적용")
            ebitda = oi + (dep or 0)
            if ebitda > 0:
                nd = _getNetDebt(series)
                impliedEv = ebitda * sp.evEbitdaMultiple
                impliedEq = impliedEv - nd
                if impliedEq > 0:
                    implied["EV/EBITDA"] = round(impliedEq / shares, 0)

        if revenue is not None and revenue > 0:
            sps = revenue / shares
            sectorPsr = _estimateSectorPsr(sp)
            sectorMults["PSR"] = sectorPsr
            implied["PSR"] = round(sps * sectorPsr, 0)

        epsGrowth = _epsGrowth3Y(series, shares)
        if epsGrowth is not None and epsGrowth > 0 and currentMults.get("PER"):
            peg = round(currentMults["PER"] / epsGrowth, 2)
            currentMults["PEG"] = peg
            eps = netIncome / shares if netIncome and netIncome > 0 else 0
            if eps > 0:
                implied["PEG"] = round(eps * epsGrowth, 0)
                sectorMults["PEG"] = 1.0

    if currentPrice and currentPrice > 0:
        for key in multKeys:
            iv = implied[key]
            if iv is not None and iv > 0:
                premiumDisc[key] = round((currentPrice - iv) / iv * 100, 1)

    multWeights = {"EV/EBITDA": 3.0, "PER": 2.5, "PBR": 1.5, "PSR": 1.0, "PEG": 1.0}
    _ivCap = currentPrice * 5 if currentPrice and currentPrice > 0 else float("inf")
    weightedSum = 0.0
    totalWeight = 0.0
    for key in multKeys:
        iv = implied[key]
        if iv is not None and 0 < iv < _ivCap:
            w = multWeights.get(key, 1.0)
            weightedSum += iv * w
            totalWeight += w
    consensus = round(weightedSum / totalWeight, 0) if totalWeight > 0 else None

    if totalWeight == 0:
        warnings.append("상대가치 추정 불가 (재무 데이터 부족)")

    return RelativeValuationResult(
        sectorMultiples=sectorMults,
        currentMultiples=currentMults,
        impliedValues=implied,
        premiumDiscount=premiumDisc,
        consensusValue=consensus,
        warnings=warnings,
    )


def sensitivityAnalysis(
    series: dict,
    shares: Optional[int] = None,
    sectorParams: Optional[SectorParams] = None,
    currentPrice: Optional[float] = None,
    currency: str = "KRW",
    waccRange: float = 2.0,
    growthRange: float = 2.0,
    steps: int = 5,
) -> SensitivityResult | None:
    """WACC x 영구성장률 민감도 그리드.

    DCF 결과를 WACC +-waccRange, 영구성장률 +-growthRange로 재계산.

    Capabilities:
        - WACC × terminalGrowth 2D 그리드 (steps × steps) DCF 재계산
        - WACC ≤ TG 또는 WACC ≤ 0 인 셀 자동 skip
        - base 결과 동시 반환 (베이스 vs 그리드 비교)

    Parameters
    ----------
    series : dict
        finance.timeseries dict.
    shares, sectorParams, currentPrice, currency : 일반 DCF 인자.
    waccRange : float
        WACC ±range (%, 기본 2.0).
    growthRange : float
        TG ±range (%, 기본 2.0).
    steps : int
        그리드 스텝 수 (기본 5).

    Returns
    -------
    SensitivityResult | None
        grid : list[{wacc, terminalGrowth, perShareValue, enterpriseValue}]
        baseWacc, baseTerminalGrowth, baseValue.

    Example:
        >>> r = sensitivityAnalysis(series, shares=5e9, waccRange=2.0, steps=5)
        >>> len(r.grid)

    Guide:
        steps=5 → 5×5=25 셀. 일부 셀은 wacc≤TG 로 skip 될 수 있음.

    When:
        밸류에이션 보고서의 sensitivity 표/heatmap 시각화 시.

    How:
        sensitivityAnalysis(series, shares=s, waccRange=2.0, growthRange=2.0, steps=5).

    Requires:
        dcfValuation — 각 셀 마다 재호출.

    Raises:
        없음.

    See Also:
        - dcfValuation : 본 함수가 반복 호출
        - calcDFV : 보다 정교한 시나리오 분석

    AIContext:
        가정 변화 영향 답변 시 grid 의 p10/p90 perShareValue 차이 인용.
    """
    from dartlab.analysis.valuation.dcf import dcfValuation

    baseDcf = dcfValuation(
        series,
        shares=shares,
        sectorParams=sectorParams,
        currentPrice=currentPrice,
        currency=currency,
    )
    baseWacc = baseDcf.discountRate
    baseTg = baseDcf.terminalGrowth

    grid: list[dict] = []
    waccStep = waccRange * 2 / (steps - 1) if steps > 1 else 0
    growthStep = growthRange * 2 / (steps - 1) if steps > 1 else 0

    for wi in range(steps):
        wacc = baseWacc - waccRange + wi * waccStep
        if wacc <= 0:
            continue
        for gi in range(steps):
            tg = baseTg - growthRange + gi * growthStep
            if tg >= wacc:
                continue
            result = dcfValuation(
                series,
                shares=shares,
                sectorParams=sectorParams,
                discountRate=wacc,
                terminalGrowth=tg,
                currentPrice=currentPrice,
                currency=currency,
            )
            grid.append(
                {
                    "wacc": round(wacc, 1),
                    "terminalGrowth": round(tg, 1),
                    "perShareValue": result.perShareValue,
                    "enterpriseValue": result.enterpriseValue,
                }
            )

    return SensitivityResult(
        grid=grid,
        baseWacc=baseWacc,
        baseTerminalGrowth=baseTg,
        baseValue=baseDcf.perShareValue,
    )
