"""내재가치 추정 엔진 — DCF + DDM + 상대가치."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from dartlab.core.finance.fmt import fmtBig, fmtPrice
from dartlab.core.finance.extract import (
    getAnnualValues,
    getLatest,
    getRevenueGrowth3Y,
    getTTM,
)
from dartlab.core.sector.types import SectorParams

# ── 결과 타입 ──────────────────────────────────────────────


@dataclass
class DCFResult:
    """DCF 밸류에이션 결과."""

    fcfHistorical: list[Optional[float]]
    fcfProjections: list[float]
    terminalValue: float
    enterpriseValue: float
    equityValue: float
    perShareValue: Optional[float]
    discountRate: float
    growthRateInitial: float
    terminalGrowth: float
    marginOfSafety: Optional[float]
    exitMultipleTv: Optional[float] = None  # Exit Multiple 기반 TV (교차검증)
    exitMultipleEv: Optional[float] = None  # Exit Multiple 기반 EV
    exitMultiplePerShare: Optional[float] = None  # Exit Multiple 기반 주당가치
    assumptions: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    currency: str = "KRW"

    DISCLAIMER: str = "본 분석은 투자 참고용이며 투자 권유가 아닙니다."

    def __repr__(self) -> str:
        c = self.currency
        lines = [
            "[DCF 밸류에이션]",
            f"  할인율: {self.discountRate:.1f}%",
            f"  초기 성장률: {self.growthRateInitial:.1f}%",
            f"  영구 성장률: {self.terminalGrowth:.1f}%",
            f"  기업가치: {fmtBig(self.enterpriseValue, c)}",
            f"  주주가치: {fmtBig(self.equityValue, c)}",
        ]
        if self.perShareValue is not None:
            lines.append(f"  주당 내재가치: {fmtPrice(self.perShareValue, c)}")
        if self.marginOfSafety is not None:
            lines.append(f"  안전마진: {self.marginOfSafety:.1f}%")
        if self.exitMultiplePerShare is not None:
            lines.append(f"  [교차검증] Exit Multiple 주당가치: {fmtPrice(self.exitMultiplePerShare, c)}")
        if self.warnings:
            for w in self.warnings:
                lines.append(f"  ⚠ {w}")
        lines.append(f"  ※ {self.DISCLAIMER}")
        return "\n".join(lines)


@dataclass
class DDMResult:
    """DDM 밸류에이션 결과."""

    intrinsicValue: Optional[float]
    dividendPerShare: Optional[float]
    dividendYield: Optional[float]
    payoutRatio: Optional[float]
    dividendGrowth: Optional[float]
    modelUsed: str
    discountRate: float
    warnings: list[str] = field(default_factory=list)
    currency: str = "KRW"

    DISCLAIMER: str = "본 분석은 투자 참고용이며 투자 권유가 아닙니다."

    def __repr__(self) -> str:
        if self.modelUsed == "N/A":
            return "[DDM 밸류에이션]\n  적용 불가 (무배당 또는 데이터 부족)"
        c = self.currency
        lines = [
            f"[DDM 밸류에이션 — {self.modelUsed}]",
            f"  할인율: {self.discountRate:.1f}%",
        ]
        if self.dividendPerShare is not None:
            lines.append(f"  주당배당금: {fmtPrice(self.dividendPerShare, c)}")
        if self.dividendGrowth is not None:
            lines.append(f"  배당성장률: {self.dividendGrowth:.1f}%")
        if self.intrinsicValue is not None:
            lines.append(f"  주당 내재가치: {fmtPrice(self.intrinsicValue, c)}")
        if self.payoutRatio is not None:
            lines.append(f"  배당성향: {self.payoutRatio:.1f}%")
        if self.warnings:
            for w in self.warnings:
                lines.append(f"  ⚠ {w}")
        lines.append(f"  ※ {self.DISCLAIMER}")
        return "\n".join(lines)


@dataclass
class RelativeValuationResult:
    """상대가치 밸류에이션 결과."""

    sectorMultiples: dict[str, float]
    currentMultiples: dict[str, Optional[float]]
    impliedValues: dict[str, Optional[float]]
    premiumDiscount: dict[str, Optional[float]]
    consensusValue: Optional[float]
    warnings: list[str] = field(default_factory=list)
    currency: str = "KRW"

    DISCLAIMER: str = "본 분석은 투자 참고용이며 투자 권유가 아닙니다."

    def __repr__(self) -> str:
        lines = ["[상대가치 밸류에이션]"]
        lines.append("  지표       섹터배수   현재배수   적정가치      할증/할인")
        for key in ["PER", "PBR", "EV/EBITDA", "PSR", "PEG"]:
            sm = self.sectorMultiples.get(key)
            cm = self.currentMultiples.get(key)
            iv = self.impliedValues.get(key)
            pd = self.premiumDiscount.get(key)
            if sm is None and cm is None and iv is None:
                continue
            smS = f"{sm:.1f}" if sm is not None else "-"
            cmS = f"{cm:.1f}" if cm is not None else "-"
            ivS = fmtPrice(iv, self.currency) if iv is not None else "-"
            pdS = f"{pd:+.1f}%" if pd is not None else "-"
            lines.append(f"  {key:<10s} {smS:>8s}  {cmS:>8s}  {ivS:>10s}  {pdS:>10s}")
        if self.consensusValue is not None:
            lines.append(f"  종합 적정가치: {fmtPrice(self.consensusValue, self.currency)}")
        if self.warnings:
            for w in self.warnings:
                lines.append(f"  ⚠ {w}")
        lines.append(f"  ※ {self.DISCLAIMER}")
        return "\n".join(lines)


@dataclass
class ValuationSummary:
    """종합 밸류에이션 결과."""

    dcf: Optional[DCFResult]
    ddm: Optional[DDMResult]
    relative: Optional[RelativeValuationResult]
    fairValueRange: Optional[tuple[float, float]]
    currentPrice: Optional[float]
    verdict: str
    currency: str = "KRW"

    DISCLAIMER: str = "본 분석은 투자 참고용이며 투자 권유가 아닙니다."

    def __repr__(self) -> str:
        c = self.currency
        lines = ["[종합 밸류에이션]"]
        if self.fairValueRange:
            lo, hi = self.fairValueRange
            lines.append(f"  적정가치 범위: {fmtPrice(lo, c)} ~ {fmtPrice(hi, c)}")
        if self.currentPrice is not None:
            lines.append(f"  현재가: {fmtPrice(self.currentPrice, c)}")
        lines.append(f"  판단: {self.verdict}")
        lines.append(f"  ※ {self.DISCLAIMER}")
        return "\n".join(lines)


# ── 내부 유틸 ──────────────────────────────────────────────


def _safeDiv(a: Optional[float], b: Optional[float]) -> Optional[float]:
    if a is None or b is None or b == 0:
        return None
    return a / b


def _cagr(start: float, end: float, years: int) -> Optional[float]:
    """CAGR (%) 계산."""
    if start <= 0 or end <= 0 or years <= 0:
        return None
    return ((end / start) ** (1 / years) - 1) * 100


def _getFcfFromSeries(series: dict, annual: bool = False) -> Optional[float]:
    """FCF = 영업CF - CAPEX."""
    flow = getLatest if annual else getTTM
    ocf = flow(series, "CF", "operating_cashflow")
    capex = flow(series, "CF", "purchase_of_property_plant_and_equipment")
    if ocf is None:
        return None
    return ocf - abs(capex or 0)


def _getNetDebt(series: dict) -> float:
    """순차입금 = 총차입금 - 현금."""
    stb = getLatest(series, "BS", "shortterm_borrowings") or 0
    ltb = getLatest(series, "BS", "longterm_borrowings") or 0
    bonds = getLatest(series, "BS", "debentures") or 0
    cash = getLatest(series, "BS", "cash_and_cash_equivalents") or 0
    return stb + ltb + bonds - cash


def _fcfHistory(series: dict) -> list[Optional[float]]:
    """연간 FCF 시계열 (영업CF - CAPEX)."""
    ocfVals = getAnnualValues(series, "CF", "operating_cashflow")
    capexVals = getAnnualValues(series, "CF", "purchase_of_property_plant_and_equipment")
    if not ocfVals:
        return []
    result: list[Optional[float]] = []
    for i in range(len(ocfVals)):
        o = ocfVals[i]
        c = capexVals[i] if i < len(capexVals) else None
        if o is None:
            result.append(None)
        else:
            result.append(o - abs(c or 0))
    return result


# ── DCF ──────────────────────────────────────────────


def dcfValuation(
    series: dict,
    shares: Optional[int] = None,
    sectorParams: Optional[SectorParams] = None,
    currentPrice: Optional[float] = None,
    discountRate: Optional[float] = None,
    terminalGrowth: Optional[float] = None,
    projectionYears: int = 5,
    currency: str = "KRW",
) -> DCFResult:
    """2-Stage DCF 밸류에이션."""
    warnings: list[str] = []

    wacc = discountRate or (sectorParams.discountRate if sectorParams else 10.0)
    sectorGrowth = sectorParams.growthRate if sectorParams else 3.0
    tg = terminalGrowth if terminalGrowth is not None else min(sectorGrowth, 3.0)

    if wacc <= tg:
        tg = max(wacc - 2.0, 1.0)
        warnings.append(f"영구성장률이 할인율 이상이어서 {tg:.1f}%로 조정")

    fcfCurrent = _getFcfFromSeries(series)
    fcfHist = _fcfHistory(series)

    if fcfCurrent is None or fcfCurrent <= 0:
        ocf = getTTM(series, "CF", "operating_cashflow")
        if ocf is not None and ocf > 0:
            fcfCurrent = ocf * 0.7
            warnings.append("FCF 음수/미확인 → 영업CF × 70%로 대체 추정")
        else:
            return DCFResult(
                fcfHistorical=fcfHist,
                fcfProjections=[],
                terminalValue=0,
                enterpriseValue=0,
                equityValue=0,
                perShareValue=None,
                discountRate=wacc,
                growthRateInitial=0,
                terminalGrowth=tg,
                marginOfSafety=None,
                warnings=["FCF 및 영업CF 데이터 부족으로 DCF 적용 불가"],
                currency=currency,
            )

    revCagr = getRevenueGrowth3Y(series)
    if revCagr is not None:
        initialGrowth = min(max(revCagr, -5.0), 30.0)
    else:
        initialGrowth = sectorGrowth
        warnings.append("매출 3Y CAGR 미확인 → 섹터 평균 성장률 적용")

    projections: list[float] = []
    prevFcf = fcfCurrent
    for yr in range(1, projectionYears + 1):
        blend = (yr - 1) / max(projectionYears - 1, 1)
        growth = initialGrowth * (1 - blend) + tg * blend
        proj = prevFcf * (1 + growth / 100)
        projections.append(proj)
        prevFcf = proj

    finalFcf = projections[-1]
    # Gordon Growth TV
    tv = finalFcf * (1 + tg / 100) / (wacc / 100 - tg / 100)

    pvFcfs = sum(fcf / (1 + wacc / 100) ** yr for yr, fcf in enumerate(projections, 1))
    pvTv = tv / (1 + wacc / 100) ** projectionYears
    ev = pvFcfs + pvTv

    netDebt = _getNetDebt(series)
    eqValue = ev - netDebt

    perShare = None
    if shares and shares > 0:
        perShare = eqValue / shares

    mos = None
    if perShare is not None and currentPrice is not None and currentPrice > 0:
        mos = (perShare - currentPrice) / perShare * 100

    # Exit Multiple TV 교차검증 -- EBITDA × 섹터 exit multiple
    exitTv = None
    exitEv = None
    exitPerShare = None
    exitMult = sectorParams.exitMultiple if sectorParams and sectorParams.exitMultiple else None
    if exitMult and exitMult > 0:
        oi = getTTM(series, "IS", "operating_profit") or getTTM(series, "IS", "operating_income")
        dep = getTTM(series, "CF", "depreciation_and_amortization")
        if oi is not None and oi > 0:
            if dep is None:
                ta = getLatest(series, "BS", "tangible_assets") or 0
                ia = getLatest(series, "BS", "intangible_assets") or 0
                dep = ta * 0.05 + ia * 0.1
            ebitda = oi + (dep or 0)
            if ebitda > 0:
                # 5년차 EBITDA 추정 (현재 EBITDA에 초기성장률 적용)
                projEbitda = ebitda
                for yr in range(1, projectionYears + 1):
                    blend = (yr - 1) / max(projectionYears - 1, 1)
                    g = initialGrowth * (1 - blend) + tg * blend
                    projEbitda *= (1 + g / 100)
                exitTv = projEbitda * exitMult
                pvExitTv = exitTv / (1 + wacc / 100) ** projectionYears
                exitEv = pvFcfs + pvExitTv
                exitEqValue = exitEv - netDebt
                if shares and shares > 0:
                    exitPerShare = exitEqValue / shares

    assumptions = {
        "할인율": f"{wacc:.1f}%",
        "초기성장률": f"{initialGrowth:.1f}%",
        "영구성장률": f"{tg:.1f}%",
        "예측기간": f"{projectionYears}년",
        "순차입금": fmtBig(netDebt, currency),
        "기준FCF": fmtBig(fcfCurrent, currency),
    }
    if exitMult:
        assumptions["Exit Multiple"] = f"EV/EBITDA {exitMult:.1f}x"

    return DCFResult(
        fcfHistorical=fcfHist,
        fcfProjections=projections,
        terminalValue=tv,
        enterpriseValue=ev,
        equityValue=eqValue,
        perShareValue=perShare,
        discountRate=wacc,
        growthRateInitial=initialGrowth,
        terminalGrowth=tg,
        marginOfSafety=mos,
        exitMultipleTv=exitTv,
        exitMultipleEv=exitEv,
        exitMultiplePerShare=exitPerShare,
        assumptions=assumptions,
        warnings=warnings,
        currency=currency,
    )


# ── DDM ──────────────────────────────────────────────


def _annualDividends(series: dict) -> list[float]:
    """분기 dividends_paid → 4분기 합산 연간 배당 리스트.

    CF/dividends_paid는 분기별 데이터가 섞여 있으므로
    4개씩 묶어 합산하여 연간 값으로 변환한다.
    부호가 혼재하므로 abs 적용 후 합산.
    이상값(전체 중앙값의 100배 초과) 제거.
    """
    raw = getAnnualValues(series, "CF", "dividends_paid")
    if not raw:
        return []

    # None 제거하고 abs 적용한 인접 데이터 추출
    absVals = [abs(v) for v in raw if v is not None]
    if not absVals:
        return []

    # 이상값 필터: 중앙값의 100배 초과 제거
    sortedVals = sorted(absVals)
    median = sortedVals[len(sortedVals) // 2] if sortedVals else 0
    if median > 0:
        absVals = [v for v in absVals if v < median * 100]

    # 4분기 합산
    annuals: list[float] = []
    for i in range(0, len(absVals) - 3, 4):
        chunk = absVals[i : i + 4]
        total = sum(chunk)
        if total > 0:
            annuals.append(total)

    # 4분기 합산이 2개 미만이면 TTM fallback
    if len(annuals) < 2:
        ttm = getTTM(series, "CF", "dividends_paid")
        if ttm is not None and abs(ttm) > 0:
            annuals = [abs(ttm)]

    return annuals


def ddmValuation(
    series: dict,
    shares: Optional[int] = None,
    sectorParams: Optional[SectorParams] = None,
    currentPrice: Optional[float] = None,
    discountRate: Optional[float] = None,
    annualDividends: Optional[list[float]] = None,
) -> DDMResult:
    """Gordon Growth / 2-Stage DDM.

    Args:
        annualDividends: 연간 배당 총액 리스트 (과거→최신 순).
            calcDividendPolicy에서 추출한 정확한 연간 합산 값 우선.
            None이면 CF/dividends_paid에서 자체 추출.
    """
    warnings: list[str] = []
    r = discountRate or (sectorParams.discountRate if sectorParams else 10.0)

    # 1순위: 외부에서 전달받은 연간 배당 (calcDividendPolicy 기반)
    # 2순위: CF/dividends_paid에서 자체 추출
    if annualDividends and len(annualDividends) >= 1:
        annualDivs = annualDividends
        latestDiv = annualDivs[-1]
    else:
        annualDivs = _annualDividends(series)
        ttmDiv = getTTM(series, "CF", "dividends_paid")
        latestDivFromTtm = abs(ttmDiv) if ttmDiv is not None and ttmDiv != 0 else None

        if annualDivs:
            latestDiv = annualDivs[-1]
        elif latestDivFromTtm and latestDivFromTtm > 0:
            latestDiv = latestDivFromTtm
            annualDivs = [latestDiv]
        else:
            latestDiv = None

    if latestDiv is None or latestDiv <= 0 or shares is None or shares <= 0:
        return DDMResult(
            intrinsicValue=None,
            dividendPerShare=None,
            dividendYield=None,
            payoutRatio=None,
            dividendGrowth=None,
            modelUsed="N/A",
            discountRate=r,
            warnings=["무배당 또는 배당 데이터 부족"],
        )

    dps = latestDiv / shares

    # 배당 성장률: 연간 합산 기준 CAGR
    divGrowth: float | None = None
    if len(annualDivs) >= 2:
        n = min(len(annualDivs), 4)
        divGrowth = _cagr(annualDivs[-n], annualDivs[-1], n - 1)

    if divGrowth is None or divGrowth > 25:
        divGrowth = min(r - 2, 5.0)
        warnings.append("배당 성장률 비정상 → 보수적 추정 적용")

    if divGrowth < 0:
        divGrowth = 0.0
        warnings.append("배당 감소 추세 → 성장률 0%로 설정")

    netIncome = getTTM(series, "IS", "net_profit") or getTTM(series, "IS", "net_income")
    payout = None
    if netIncome and netIncome > 0:
        payout = latestDiv / netIncome * 100

    divYield = None
    if currentPrice and currentPrice > 0:
        divYield = dps / currentPrice * 100

    if r / 100 <= divGrowth / 100:
        warnings.append("배당성장률 ≥ 할인율 → DDM 적용 불가")
        return DDMResult(
            intrinsicValue=None,
            dividendPerShare=dps,
            dividendYield=divYield,
            payoutRatio=payout,
            dividendGrowth=divGrowth,
            modelUsed="N/A",
            discountRate=r,
            warnings=warnings,
        )

    d1 = dps * (1 + divGrowth / 100)
    intrinsic = d1 / (r / 100 - divGrowth / 100)

    model = "gordon"
    if len(annualDivs) < 3:
        warnings.append("배당 데이터 3년 미만 → 결과 신뢰도 낮음")

    return DDMResult(
        intrinsicValue=round(intrinsic, 0),
        dividendPerShare=round(dps, 0),
        dividendYield=round(divYield, 2) if divYield is not None else None,
        payoutRatio=round(payout, 1) if payout is not None else None,
        dividendGrowth=round(divGrowth, 1),
        modelUsed=model,
        discountRate=r,
        warnings=warnings,
    )


# ── 상대가치 ──────────────────────────────────────────────


def _normalizedEarnings(series: dict, shares: int | None) -> tuple[float | None, float | None, bool]:
    """경기순환 조정 정규화 수익 -- Damodaran/CFA 표준.

    방법: 과거 3-5년 평균 ROE x 현재 BPS (mid-cycle earnings)
    Returns: (normalizedNI, normalizedEps, wasNormalized)
    """
    niVals = getAnnualValues(series, "IS", "net_profit")
    if not niVals:
        niVals = getAnnualValues(series, "IS", "net_income")
    eqVals = getAnnualValues(series, "BS", "total_stockholders_equity")
    if not eqVals:
        eqVals = getAnnualValues(series, "BS", "owners_of_parent_equity")

    if not niVals or not eqVals or len(niVals) < 3 or len(eqVals) < 3:
        return None, None, False

    # 최근 3-5년 ROE 평균
    n = min(len(niVals), len(eqVals), 5)
    roes: list[float] = []
    for i in range(-n, 0):
        ni = niVals[i] if abs(i) <= len(niVals) else None
        eq = eqVals[i] if abs(i) <= len(eqVals) else None
        if ni is not None and eq is not None and eq > 0:
            roes.append(ni / eq)

    if len(roes) < 2:
        return None, None, False

    avgRoe = sum(roes) / len(roes)
    currentEquity = eqVals[-1]
    if currentEquity is None or currentEquity <= 0:
        return None, None, False

    normalizedNi = currentEquity * avgRoe
    normalizedEps = normalizedNi / shares if shares and shares > 0 else None

    # TTM 대비 30% 이상 차이나면 정규화 적용
    ttmNi = getTTM(series, "IS", "net_profit") or getTTM(series, "IS", "net_income")
    if ttmNi and ttmNi > 0 and normalizedNi > 0:
        divergence = abs(ttmNi - normalizedNi) / max(ttmNi, normalizedNi)
        return normalizedNi, normalizedEps, divergence > 0.3

    return normalizedNi, normalizedEps, True


def relativeValuation(
    series: dict,
    sectorParams: Optional[SectorParams] = None,
    marketCap: Optional[float] = None,
    shares: Optional[int] = None,
    currentPrice: Optional[float] = None,
) -> RelativeValuationResult:
    """섹터 배수 기반 상대가치 추정 (Normalized Earnings 지원)."""
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

    # Normalized Earnings -- 경기순환 조정
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

        # PSR -- 매출 기반 가치
        if revenue is not None and revenue > 0:
            sps = revenue / shares  # Sales Per Share
            sectorPsr = _estimateSectorPsr(sp)
            sectorMults["PSR"] = sectorPsr
            implied["PSR"] = round(sps * sectorPsr, 0)

        # PEG -- PER / EPS 성장률
        epsGrowth = _epsGrowth3Y(series, shares)
        if epsGrowth is not None and epsGrowth > 0 and currentMults.get("PER"):
            peg = round(currentMults["PER"] / epsGrowth, 2)
            currentMults["PEG"] = peg
            # PEG 1.0 = 적정, 적정가 = EPS × 성장률 × 1.0 (PEG fair = 1)
            eps = netIncome / shares if netIncome and netIncome > 0 else 0
            if eps > 0:
                implied["PEG"] = round(eps * epsGrowth, 0)
                sectorMults["PEG"] = 1.0  # fair PEG

    if currentPrice and currentPrice > 0:
        for key in multKeys:
            iv = implied[key]
            if iv is not None and iv > 0:
                premiumDisc[key] = round((currentPrice - iv) / iv * 100, 1)

    # 가중 합의값 -- EV/EBITDA(자본구조 중립) > PER > PBR > PSR > PEG
    multWeights = {"EV/EBITDA": 3.0, "PER": 2.5, "PBR": 1.5, "PSR": 1.0, "PEG": 1.0}
    weightedSum = 0.0
    totalWeight = 0.0
    for key in multKeys:
        iv = implied[key]
        if iv is not None and iv > 0:
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


def _estimateSectorPsr(sp: SectorParams) -> float:
    """섹터 PSR 추정 -- PER × 순이익률 가정으로 역산."""
    # 일반적으로 PSR = PER × 순이익률
    # 순이익률 모르면 섹터 평균 5% 가정
    estimatedMargin = 0.05
    psr = sp.perMultiple * estimatedMargin
    return round(max(psr, 0.3), 2)


def _epsGrowth3Y(series: dict, shares: int) -> Optional[float]:
    """EPS 3년 CAGR (%)."""
    niVals = getAnnualValues(series, "IS", "net_profit")
    if not niVals:
        niVals = getAnnualValues(series, "IS", "net_income")
    if not niVals or len(niVals) < 4 or shares <= 0:
        return None

    recent = niVals[-4:]
    validNi = [v for v in recent if v is not None and v > 0]
    if len(validNi) < 2:
        return None

    epsStart = validNi[0] / shares
    epsEnd = validNi[-1] / shares
    if epsStart <= 0 or epsEnd <= 0:
        return None

    years = len(validNi) - 1
    return _cagr(epsStart, epsEnd, years)


# ── 민감도 분석 ──────────────────────────────────────────────


@dataclass
class SensitivityResult:
    """DCF 민감도 분석 결과."""

    grid: list[dict]  # [{wacc, terminalGrowth, perShareValue}, ...]
    baseWacc: float
    baseTerminalGrowth: float
    baseValue: Optional[float]


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
    """
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


# ── 종합 밸류에이션 ──────────────────────────────────────────


def fullValuation(
    series: dict,
    shares: Optional[int] = None,
    sectorParams: Optional[SectorParams] = None,
    marketCap: Optional[float] = None,
    currentPrice: Optional[float] = None,
    currency: str = "KRW",
) -> ValuationSummary:
    """DCF + DDM + 상대가치 종합 밸류에이션."""
    dcf = dcfValuation(series, shares=shares, sectorParams=sectorParams, currentPrice=currentPrice, currency=currency)
    ddm = ddmValuation(series, shares=shares, sectorParams=sectorParams, currentPrice=currentPrice)
    ddm.currency = currency
    rel = relativeValuation(
        series, sectorParams=sectorParams, marketCap=marketCap, shares=shares, currentPrice=currentPrice
    )
    rel.currency = currency

    estimates: list[float] = []
    if dcf.perShareValue is not None and dcf.perShareValue > 0:
        estimates.append(dcf.perShareValue)
    if ddm.intrinsicValue is not None and ddm.intrinsicValue > 0:
        estimates.append(ddm.intrinsicValue)
    if rel.consensusValue is not None and rel.consensusValue > 0:
        estimates.append(rel.consensusValue)

    fairRange = None
    verdict = "판단불가"

    if estimates:
        lo = min(estimates)
        hi = max(estimates)
        fairRange = (round(lo * 0.9, 0), round(hi * 1.1, 0))

        if currentPrice and currentPrice > 0:
            mid = sum(estimates) / len(estimates)
            ratio = currentPrice / mid
            if ratio < 0.8:
                verdict = "저평가"
            elif ratio > 1.2:
                verdict = "고평가"
            else:
                verdict = "적정"

    return ValuationSummary(
        dcf=dcf,
        ddm=ddm,
        relative=rel,
        fairValueRange=fairRange,
        currentPrice=currentPrice,
        verdict=verdict,
        currency=currency,
    )
