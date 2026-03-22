"""내재가치 추정 엔진 — DCF + DDM + 상대가치."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from dartlab.engines.analysis.sector.types import SectorParams
from dartlab.engines.common.finance.extract import (
    getAnnualValues,
    getLatest,
    getRevenueGrowth3Y,
    getTTM,
)

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
    assumptions: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    DISCLAIMER: str = "본 분석은 투자 참고용이며 투자 권유가 아닙니다."

    def __repr__(self) -> str:
        lines = [
            "[DCF 밸류에이션]",
            f"  할인율: {self.discountRate:.1f}%",
            f"  초기 성장률: {self.growthRateInitial:.1f}%",
            f"  영구 성장률: {self.terminalGrowth:.1f}%",
            f"  기업가치: {self.enterpriseValue / 1e8:,.0f}억",
            f"  주주가치: {self.equityValue / 1e8:,.0f}억",
        ]
        if self.perShareValue is not None:
            lines.append(f"  주당 내재가치: {self.perShareValue:,.0f}원")
        if self.marginOfSafety is not None:
            lines.append(f"  안전마진: {self.marginOfSafety:.1f}%")
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

    DISCLAIMER: str = "본 분석은 투자 참고용이며 투자 권유가 아닙니다."

    def __repr__(self) -> str:
        if self.modelUsed == "N/A":
            return "[DDM 밸류에이션]\n  적용 불가 (무배당 또는 데이터 부족)"
        lines = [
            f"[DDM 밸류에이션 — {self.modelUsed}]",
            f"  할인율: {self.discountRate:.1f}%",
        ]
        if self.dividendPerShare is not None:
            lines.append(f"  주당배당금: {self.dividendPerShare:,.0f}원")
        if self.dividendGrowth is not None:
            lines.append(f"  배당성장률: {self.dividendGrowth:.1f}%")
        if self.intrinsicValue is not None:
            lines.append(f"  주당 내재가치: {self.intrinsicValue:,.0f}원")
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

    DISCLAIMER: str = "본 분석은 투자 참고용이며 투자 권유가 아닙니다."

    def __repr__(self) -> str:
        lines = ["[상대가치 밸류에이션]"]
        lines.append("  지표       섹터배수   현재배수   적정가치      할증/할인")
        for key in ["PER", "PBR", "EV/EBITDA"]:
            sm = self.sectorMultiples.get(key)
            cm = self.currentMultiples.get(key)
            iv = self.impliedValues.get(key)
            pd = self.premiumDiscount.get(key)
            smS = f"{sm:.1f}" if sm is not None else "-"
            cmS = f"{cm:.1f}" if cm is not None else "-"
            ivS = f"{iv:,.0f}" if iv is not None else "-"
            pdS = f"{pd:+.1f}%" if pd is not None else "-"
            lines.append(f"  {key:<10s} {smS:>8s}  {cmS:>8s}  {ivS:>10s}  {pdS:>10s}")
        if self.consensusValue is not None:
            lines.append(f"  종합 적정가치: {self.consensusValue:,.0f}원")
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

    DISCLAIMER: str = "본 분석은 투자 참고용이며 투자 권유가 아닙니다."

    def __repr__(self) -> str:
        lines = ["[종합 밸류에이션]"]
        if self.fairValueRange:
            lo, hi = self.fairValueRange
            lines.append(f"  적정가치 범위: {lo:,.0f} ~ {hi:,.0f}원")
        if self.currentPrice is not None:
            lines.append(f"  현재가: {self.currentPrice:,.0f}원")
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

    assumptions = {
        "할인율": f"{wacc:.1f}%",
        "초기성장률": f"{initialGrowth:.1f}%",
        "영구성장률": f"{tg:.1f}%",
        "예측기간": f"{projectionYears}년",
        "순차입금": f"{netDebt / 1e8:,.0f}억",
        "기준FCF": f"{fcfCurrent / 1e8:,.0f}억",
    }

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
        assumptions=assumptions,
        warnings=warnings,
    )


# ── DDM ──────────────────────────────────────────────


def ddmValuation(
    series: dict,
    shares: Optional[int] = None,
    sectorParams: Optional[SectorParams] = None,
    currentPrice: Optional[float] = None,
    discountRate: Optional[float] = None,
) -> DDMResult:
    """Gordon Growth / 2-Stage DDM."""
    warnings: list[str] = []
    r = discountRate or (sectorParams.discountRate if sectorParams else 10.0)

    divPaidVals = getAnnualValues(series, "CF", "dividends_paid")
    validDivs = [abs(v) for v in divPaidVals if v is not None and v != 0]

    if len(validDivs) < 2 or shares is None or shares <= 0:
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

    latestDiv = validDivs[-1]
    dps = latestDiv / shares

    n = min(len(validDivs), 4)
    divGrowth = _cagr(validDivs[-n], validDivs[-1], n - 1)
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
    if len(validDivs) < 3:
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


def relativeValuation(
    series: dict,
    sectorParams: Optional[SectorParams] = None,
    marketCap: Optional[float] = None,
    shares: Optional[int] = None,
    currentPrice: Optional[float] = None,
) -> RelativeValuationResult:
    """섹터 배수 기반 상대가치 추정."""
    warnings: list[str] = []
    sp = sectorParams or SectorParams(
        discountRate=10.0,
        growthRate=3.0,
        perMultiple=15,
        pbrMultiple=1.2,
        evEbitdaMultiple=8,
        label="기타",
    )

    sectorMults = {
        "PER": sp.perMultiple,
        "PBR": sp.pbrMultiple,
        "EV/EBITDA": sp.evEbitdaMultiple,
    }

    netIncome = getTTM(series, "IS", "net_profit") or getTTM(series, "IS", "net_income")
    equity = getLatest(series, "BS", "total_stockholders_equity") or getLatest(series, "BS", "owners_of_parent_equity")

    currentMults: dict[str, Optional[float]] = {"PER": None, "PBR": None, "EV/EBITDA": None}
    if marketCap and marketCap > 0:
        if netIncome and netIncome > 0:
            currentMults["PER"] = round(marketCap / netIncome, 1)
        if equity and equity > 0:
            currentMults["PBR"] = round(marketCap / equity, 1)

    implied: dict[str, Optional[float]] = {"PER": None, "PBR": None, "EV/EBITDA": None}
    premiumDisc: dict[str, Optional[float]] = {"PER": None, "PBR": None, "EV/EBITDA": None}

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
                warnings.append("감가상각 미확인 → 추정치 적용")
            ebitda = oi + (dep or 0)
            if ebitda > 0:
                nd = _getNetDebt(series)
                impliedEv = ebitda * sp.evEbitdaMultiple
                impliedEq = impliedEv - nd
                if impliedEq > 0:
                    implied["EV/EBITDA"] = round(impliedEq / shares, 0)

    if currentPrice and currentPrice > 0:
        for key in ["PER", "PBR", "EV/EBITDA"]:
            iv = implied[key]
            if iv is not None:
                premiumDisc[key] = round((currentPrice - iv) / iv * 100, 1)

    validImplied = [v for v in implied.values() if v is not None and v > 0]
    consensus = round(sum(validImplied) / len(validImplied), 0) if validImplied else None

    if not validImplied:
        warnings.append("상대가치 추정 불가 (재무 데이터 부족)")

    return RelativeValuationResult(
        sectorMultiples=sectorMults,
        currentMultiples=currentMults,
        impliedValues=implied,
        premiumDiscount=premiumDisc,
        consensusValue=consensus,
        warnings=warnings,
    )


# ── 종합 밸류에이션 ──────────────────────────────────────────


def fullValuation(
    series: dict,
    shares: Optional[int] = None,
    sectorParams: Optional[SectorParams] = None,
    marketCap: Optional[float] = None,
    currentPrice: Optional[float] = None,
) -> ValuationSummary:
    """DCF + DDM + 상대가치 종합 밸류에이션."""
    dcf = dcfValuation(series, shares=shares, sectorParams=sectorParams, currentPrice=currentPrice)
    ddm = ddmValuation(series, shares=shares, sectorParams=sectorParams, currentPrice=currentPrice)
    rel = relativeValuation(series, sectorParams=sectorParams, marketCap=marketCap, shares=shares, currentPrice=currentPrice)

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
    )
