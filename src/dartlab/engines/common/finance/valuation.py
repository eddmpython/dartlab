"""내재가치 추정 엔진.

3가지 밸류에이션 모델:
1. DCF (Discounted Cash Flow) — 2-Stage FCF 할인
2. DDM (Dividend Discount Model) — Gordon/2-Stage 배당 할인
3. Relative Valuation — 섹터 배수 기반 상대가치

모든 계산은 엔진이 수행, LLM은 해석만 (2-Tier 원칙).
"""

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

    fcf_historical: list[Optional[float]]
    fcf_projections: list[float]
    terminal_value: float
    enterprise_value: float
    equity_value: float
    per_share_value: Optional[float]
    discount_rate: float
    growth_rate_initial: float
    terminal_growth: float
    margin_of_safety: Optional[float]
    assumptions: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    DISCLAIMER: str = "본 분석은 투자 참고용이며 투자 권유가 아닙니다."

    def __repr__(self) -> str:
        lines = [
            "[DCF 밸류에이션]",
            f"  할인율: {self.discount_rate:.1f}%",
            f"  초기 성장률: {self.growth_rate_initial:.1f}%",
            f"  영구 성장률: {self.terminal_growth:.1f}%",
            f"  기업가치: {self.enterprise_value / 1e8:,.0f}억",
            f"  주주가치: {self.equity_value / 1e8:,.0f}억",
        ]
        if self.per_share_value is not None:
            lines.append(f"  주당 내재가치: {self.per_share_value:,.0f}원")
        if self.margin_of_safety is not None:
            lines.append(f"  안전마진: {self.margin_of_safety:.1f}%")
        if self.warnings:
            for w in self.warnings:
                lines.append(f"  ⚠ {w}")
        lines.append(f"  ※ {self.DISCLAIMER}")
        return "\n".join(lines)


@dataclass
class DDMResult:
    """DDM 밸류에이션 결과."""

    intrinsic_value: Optional[float]
    dividend_per_share: Optional[float]
    dividend_yield: Optional[float]
    payout_ratio: Optional[float]
    dividend_growth: Optional[float]
    model_used: str  # "gordon" | "2stage" | "N/A"
    discount_rate: float
    warnings: list[str] = field(default_factory=list)

    DISCLAIMER: str = "본 분석은 투자 참고용이며 투자 권유가 아닙니다."

    def __repr__(self) -> str:
        if self.model_used == "N/A":
            return "[DDM 밸류에이션]\n  적용 불가 (무배당 또는 데이터 부족)"
        lines = [
            f"[DDM 밸류에이션 — {self.model_used}]",
            f"  할인율: {self.discount_rate:.1f}%",
        ]
        if self.dividend_per_share is not None:
            lines.append(f"  주당배당금: {self.dividend_per_share:,.0f}원")
        if self.dividend_growth is not None:
            lines.append(f"  배당성장률: {self.dividend_growth:.1f}%")
        if self.intrinsic_value is not None:
            lines.append(f"  주당 내재가치: {self.intrinsic_value:,.0f}원")
        if self.payout_ratio is not None:
            lines.append(f"  배당성향: {self.payout_ratio:.1f}%")
        if self.warnings:
            for w in self.warnings:
                lines.append(f"  ⚠ {w}")
        lines.append(f"  ※ {self.DISCLAIMER}")
        return "\n".join(lines)


@dataclass
class RelativeValuationResult:
    """상대가치 밸류에이션 결과."""

    sector_multiples: dict[str, float]
    current_multiples: dict[str, Optional[float]]
    implied_values: dict[str, Optional[float]]
    premium_discount: dict[str, Optional[float]]
    consensus_value: Optional[float]
    warnings: list[str] = field(default_factory=list)

    DISCLAIMER: str = "본 분석은 투자 참고용이며 투자 권유가 아닙니다."

    def __repr__(self) -> str:
        lines = ["[상대가치 밸류에이션]"]
        lines.append("  지표       섹터배수   현재배수   적정가치      할증/할인")
        for key in ["PER", "PBR", "EV/EBITDA"]:
            sm = self.sector_multiples.get(key)
            cm = self.current_multiples.get(key)
            iv = self.implied_values.get(key)
            pd = self.premium_discount.get(key)
            sm_s = f"{sm:.1f}" if sm is not None else "-"
            cm_s = f"{cm:.1f}" if cm is not None else "-"
            iv_s = f"{iv:,.0f}" if iv is not None else "-"
            pd_s = f"{pd:+.1f}%" if pd is not None else "-"
            lines.append(f"  {key:<10s} {sm_s:>8s}  {cm_s:>8s}  {iv_s:>10s}  {pd_s:>10s}")
        if self.consensus_value is not None:
            lines.append(f"  종합 적정가치: {self.consensus_value:,.0f}원")
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
    fair_value_range: Optional[tuple[float, float]]
    current_price: Optional[float]
    verdict: str  # "저평가" | "적정" | "고평가" | "판단불가"

    DISCLAIMER: str = "본 분석은 투자 참고용이며 투자 권유가 아닙니다."

    def __repr__(self) -> str:
        lines = ["[종합 밸류에이션]"]
        if self.fair_value_range:
            lo, hi = self.fair_value_range
            lines.append(f"  적정가치 범위: {lo:,.0f} ~ {hi:,.0f}원")
        if self.current_price is not None:
            lines.append(f"  현재가: {self.current_price:,.0f}원")
        lines.append(f"  판단: {self.verdict}")
        lines.append(f"  ※ {self.DISCLAIMER}")
        return "\n".join(lines)


# ── 내부 유틸 ──────────────────────────────────────────────


def _safe_div(a: Optional[float], b: Optional[float]) -> Optional[float]:
    if a is None or b is None or b == 0:
        return None
    return a / b


def _cagr(start: float, end: float, years: int) -> Optional[float]:
    """CAGR (%) 계산."""
    if start <= 0 or end <= 0 or years <= 0:
        return None
    return ((end / start) ** (1 / years) - 1) * 100


def _get_fcf_from_series(
    series: dict,
    annual: bool = False,
) -> Optional[float]:
    """FCF = 영업CF - CAPEX."""
    flow = getLatest if annual else getTTM
    ocf = flow(series, "CF", "operating_cashflow")
    capex = flow(series, "CF", "purchase_of_property_plant_and_equipment")
    if ocf is None:
        return None
    return ocf - abs(capex or 0)


def _get_net_debt(series: dict) -> float:
    """순차입금 = 총차입금 - 현금."""
    stb = getLatest(series, "BS", "shortterm_borrowings") or 0
    ltb = getLatest(series, "BS", "longterm_borrowings") or 0
    bonds = getLatest(series, "BS", "debentures") or 0
    cash = getLatest(series, "BS", "cash_and_cash_equivalents") or 0
    return stb + ltb + bonds - cash


def _fcf_history(series: dict) -> list[Optional[float]]:
    """연간 FCF 시계열 (영업CF - CAPEX)."""
    ocf_vals = getAnnualValues(series, "CF", "operating_cashflow")
    capex_vals = getAnnualValues(series, "CF", "purchase_of_property_plant_and_equipment")
    if not ocf_vals:
        return []
    result: list[Optional[float]] = []
    for i in range(len(ocf_vals)):
        o = ocf_vals[i]
        c = capex_vals[i] if i < len(capex_vals) else None
        if o is None:
            result.append(None)
        else:
            result.append(o - abs(c or 0))
    return result


# ── DCF ──────────────────────────────────────────────


def dcf_valuation(
    series: dict,
    shares: Optional[int] = None,
    sector_params: Optional[SectorParams] = None,
    current_price: Optional[float] = None,
    discount_rate: Optional[float] = None,
    terminal_growth: Optional[float] = None,
    projection_years: int = 5,
) -> DCFResult:
    """2-Stage DCF 밸류에이션.

    Args:
        series: finance timeseries dict.
        shares: 발행주식수. None이면 주당가치 계산 안 함.
        sector_params: 섹터 파라미터 (할인율/성장률). None이면 기본값 사용.
        current_price: 현재 주가. None이면 안전마진 계산 안 함.
        discount_rate: 할인율 (%) 직접 지정. None이면 sector_params 사용.
        terminal_growth: 영구성장률 (%) 직접 지정. None이면 자동 계산.
        projection_years: 예측 기간 (기본 5년).

    Returns:
        DCFResult.
    """
    warnings: list[str] = []

    # 할인율/성장률 결정
    wacc = discount_rate or (sector_params.discountRate if sector_params else 10.0)
    sector_growth = sector_params.growthRate if sector_params else 3.0
    tg = terminal_growth if terminal_growth is not None else min(sector_growth, 3.0)

    if wacc <= tg:
        tg = max(wacc - 2.0, 1.0)
        warnings.append(f"영구성장률이 할인율 이상이어서 {tg:.1f}%로 조정")

    # FCF 추출
    fcf_current = _get_fcf_from_series(series)
    fcf_hist = _fcf_history(series)

    if fcf_current is None or fcf_current <= 0:
        # FCF가 음수/없음 → 영업CF 기반 추정
        ocf = getTTM(series, "CF", "operating_cashflow")
        if ocf is not None and ocf > 0:
            fcf_current = ocf * 0.7  # 보수적: 영업CF의 70%
            warnings.append("FCF 음수/미확인 → 영업CF × 70%로 대체 추정")
        else:
            return DCFResult(
                fcf_historical=fcf_hist,
                fcf_projections=[],
                terminal_value=0,
                enterprise_value=0,
                equity_value=0,
                per_share_value=None,
                discount_rate=wacc,
                growth_rate_initial=0,
                terminal_growth=tg,
                margin_of_safety=None,
                warnings=["FCF 및 영업CF 데이터 부족으로 DCF 적용 불가"],
            )

    # 성장률 추정: 3년 매출 CAGR 기반, 섹터 성장률로 수렴
    rev_cagr = getRevenueGrowth3Y(series)
    if rev_cagr is not None:
        initial_growth = min(max(rev_cagr, -5.0), 30.0)  # -5% ~ 30% 클램프
    else:
        initial_growth = sector_growth
        warnings.append("매출 3Y CAGR 미확인 → 섹터 평균 성장률 적용")

    # FCF 예측: 점진 감속 (초기 성장률 → 영구성장률)
    projections: list[float] = []
    prev_fcf = fcf_current
    for yr in range(1, projection_years + 1):
        # 선형 감속: year 1 = initial_growth, year N = terminal_growth
        blend = (yr - 1) / max(projection_years - 1, 1)
        growth = initial_growth * (1 - blend) + tg * blend
        proj = prev_fcf * (1 + growth / 100)
        projections.append(proj)
        prev_fcf = proj

    # Terminal Value
    final_fcf = projections[-1]
    tv = final_fcf * (1 + tg / 100) / (wacc / 100 - tg / 100)

    # Enterprise Value = PV(FCFs) + PV(TV)
    pv_fcfs = sum(fcf / (1 + wacc / 100) ** yr for yr, fcf in enumerate(projections, 1))
    pv_tv = tv / (1 + wacc / 100) ** projection_years
    ev = pv_fcfs + pv_tv

    # Equity Value = EV - 순차입금
    net_debt = _get_net_debt(series)
    equity_value = ev - net_debt

    # 주당 가치
    per_share = None
    if shares and shares > 0:
        per_share = equity_value / shares

    # 안전마진
    mos = None
    if per_share is not None and current_price is not None and current_price > 0:
        mos = (per_share - current_price) / per_share * 100

    assumptions = {
        "할인율": f"{wacc:.1f}%",
        "초기성장률": f"{initial_growth:.1f}%",
        "영구성장률": f"{tg:.1f}%",
        "예측기간": f"{projection_years}년",
        "순차입금": f"{net_debt / 1e8:,.0f}억",
        "기준FCF": f"{fcf_current / 1e8:,.0f}억",
    }

    return DCFResult(
        fcf_historical=fcf_hist,
        fcf_projections=projections,
        terminal_value=tv,
        enterprise_value=ev,
        equity_value=equity_value,
        per_share_value=per_share,
        discount_rate=wacc,
        growth_rate_initial=initial_growth,
        terminal_growth=tg,
        margin_of_safety=mos,
        assumptions=assumptions,
        warnings=warnings,
    )


# ── DDM ──────────────────────────────────────────────


def ddm_valuation(
    series: dict,
    shares: Optional[int] = None,
    sector_params: Optional[SectorParams] = None,
    current_price: Optional[float] = None,
    discount_rate: Optional[float] = None,
) -> DDMResult:
    """Gordon Growth / 2-Stage DDM.

    Args:
        series: finance timeseries dict.
        shares: 발행주식수.
        sector_params: 섹터 파라미터.
        current_price: 현재 주가.
        discount_rate: 할인율 (%) 직접 지정.

    Returns:
        DDMResult.
    """
    warnings: list[str] = []
    r = discount_rate or (sector_params.discountRate if sector_params else 10.0)

    # 배당금 시계열 추출
    div_paid_vals = getAnnualValues(series, "CF", "dividends_paid")
    valid_divs = [abs(v) for v in div_paid_vals if v is not None and v != 0]

    if len(valid_divs) < 2 or shares is None or shares <= 0:
        return DDMResult(
            intrinsic_value=None,
            dividend_per_share=None,
            dividend_yield=None,
            payout_ratio=None,
            dividend_growth=None,
            model_used="N/A",
            discount_rate=r,
            warnings=["무배당 또는 배당 데이터 부족"],
        )

    latest_div = valid_divs[-1]
    dps = latest_div / shares

    # 배당 성장률 (최근 3년 CAGR 또는 2년)
    n = min(len(valid_divs), 4)
    div_growth = _cagr(valid_divs[-n], valid_divs[-1], n - 1)
    if div_growth is None or div_growth > 25:
        div_growth = min(r - 2, 5.0)  # 보수적 기본값
        warnings.append("배당 성장률 비정상 → 보수적 추정 적용")

    if div_growth < 0:
        div_growth = 0.0
        warnings.append("배당 감소 추세 → 성장률 0%로 설정")

    # 배당성향
    net_income = getTTM(series, "IS", "net_profit") or getTTM(series, "IS", "net_income")
    payout = None
    if net_income and net_income > 0:
        payout = latest_div / net_income * 100

    # 배당수익률
    div_yield = None
    if current_price and current_price > 0:
        div_yield = dps / current_price * 100

    # Gordon GGM
    if r / 100 <= div_growth / 100:
        warnings.append("배당성장률 ≥ 할인율 → DDM 적용 불가")
        return DDMResult(
            intrinsic_value=None,
            dividend_per_share=dps,
            dividend_yield=div_yield,
            payout_ratio=payout,
            dividend_growth=div_growth,
            model_used="N/A",
            discount_rate=r,
            warnings=warnings,
        )

    d1 = dps * (1 + div_growth / 100)
    intrinsic = d1 / (r / 100 - div_growth / 100)

    model = "gordon"
    if len(valid_divs) < 3:
        warnings.append("배당 데이터 3년 미만 → 결과 신뢰도 낮음")

    return DDMResult(
        intrinsic_value=round(intrinsic, 0),
        dividend_per_share=round(dps, 0),
        dividend_yield=round(div_yield, 2) if div_yield is not None else None,
        payout_ratio=round(payout, 1) if payout is not None else None,
        dividend_growth=round(div_growth, 1),
        model_used=model,
        discount_rate=r,
        warnings=warnings,
    )


# ── 상대가치 ──────────────────────────────────────────────


def relative_valuation(
    series: dict,
    sector_params: Optional[SectorParams] = None,
    market_cap: Optional[float] = None,
    shares: Optional[int] = None,
    current_price: Optional[float] = None,
) -> RelativeValuationResult:
    """섹터 배수 기반 상대가치 추정.

    Args:
        series: finance timeseries dict.
        sector_params: 섹터 파라미터 (PER/PBR/EV 배수).
        market_cap: 시가총액.
        shares: 발행주식수.
        current_price: 현재 주가.

    Returns:
        RelativeValuationResult.
    """
    warnings: list[str] = []
    sp = sector_params or SectorParams(
        discountRate=10.0,
        growthRate=3.0,
        perMultiple=15,
        pbrMultiple=1.2,
        evEbitdaMultiple=8,
        label="기타",
    )

    sector_mults = {
        "PER": sp.perMultiple,
        "PBR": sp.pbrMultiple,
        "EV/EBITDA": sp.evEbitdaMultiple,
    }

    # 현재 배수 계산
    net_income = getTTM(series, "IS", "net_profit") or getTTM(series, "IS", "net_income")
    equity = getLatest(series, "BS", "total_stockholders_equity") or getLatest(series, "BS", "owners_of_parent_equity")
    revenue = getTTM(series, "IS", "sales") or getTTM(series, "IS", "revenue")

    current_mults: dict[str, Optional[float]] = {
        "PER": None,
        "PBR": None,
        "EV/EBITDA": None,
    }
    if market_cap and market_cap > 0:
        if net_income and net_income > 0:
            current_mults["PER"] = round(market_cap / net_income, 1)
        if equity and equity > 0:
            current_mults["PBR"] = round(market_cap / equity, 1)

    # Implied values (주당)
    implied: dict[str, Optional[float]] = {
        "PER": None,
        "PBR": None,
        "EV/EBITDA": None,
    }
    premium_disc: dict[str, Optional[float]] = {
        "PER": None,
        "PBR": None,
        "EV/EBITDA": None,
    }

    if shares and shares > 0:
        # PER 기준: EPS × 섹터 PER
        if net_income is not None and net_income > 0:
            eps = net_income / shares
            implied["PER"] = round(eps * sp.perMultiple, 0)

        # PBR 기준: BPS × 섹터 PBR
        if equity is not None and equity > 0:
            bps = equity / shares
            implied["PBR"] = round(bps * sp.pbrMultiple, 0)

        # EV/EBITDA 기준
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
                net_debt = _get_net_debt(series)
                implied_ev = ebitda * sp.evEbitdaMultiple
                implied_eq = implied_ev - net_debt
                if implied_eq > 0:
                    implied["EV/EBITDA"] = round(implied_eq / shares, 0)

    # 할증/할인율 계산
    if current_price and current_price > 0:
        for key in ["PER", "PBR", "EV/EBITDA"]:
            iv = implied[key]
            if iv is not None:
                premium_disc[key] = round((current_price - iv) / iv * 100, 1)

    # 종합 적정가치 (유효 implied values의 평균)
    valid_implied = [v for v in implied.values() if v is not None and v > 0]
    consensus = round(sum(valid_implied) / len(valid_implied), 0) if valid_implied else None

    if not valid_implied:
        warnings.append("상대가치 추정 불가 (재무 데이터 부족)")

    return RelativeValuationResult(
        sector_multiples=sector_mults,
        current_multiples=current_mults,
        implied_values=implied,
        premium_discount=premium_disc,
        consensus_value=consensus,
        warnings=warnings,
    )


# ── 종합 밸류에이션 ──────────────────────────────────────────


def full_valuation(
    series: dict,
    shares: Optional[int] = None,
    sector_params: Optional[SectorParams] = None,
    market_cap: Optional[float] = None,
    current_price: Optional[float] = None,
) -> ValuationSummary:
    """DCF + DDM + 상대가치 종합 밸류에이션.

    Args:
        series: finance timeseries dict.
        shares: 발행주식수.
        sector_params: 섹터 파라미터.
        market_cap: 시가총액.
        current_price: 현재 주가.

    Returns:
        ValuationSummary.
    """
    dcf = dcf_valuation(
        series,
        shares=shares,
        sector_params=sector_params,
        current_price=current_price,
    )
    ddm = ddm_valuation(
        series,
        shares=shares,
        sector_params=sector_params,
        current_price=current_price,
    )
    rel = relative_valuation(
        series,
        sector_params=sector_params,
        market_cap=market_cap,
        shares=shares,
        current_price=current_price,
    )

    # 적정가치 범위 산출
    estimates: list[float] = []
    if dcf.per_share_value is not None and dcf.per_share_value > 0:
        estimates.append(dcf.per_share_value)
    if ddm.intrinsic_value is not None and ddm.intrinsic_value > 0:
        estimates.append(ddm.intrinsic_value)
    if rel.consensus_value is not None and rel.consensus_value > 0:
        estimates.append(rel.consensus_value)

    fair_range = None
    verdict = "판단불가"

    if estimates:
        lo = min(estimates)
        hi = max(estimates)
        # 보수적 범위: 최소의 0.9 ~ 최대의 1.1
        fair_range = (round(lo * 0.9, 0), round(hi * 1.1, 0))

        if current_price and current_price > 0:
            mid = sum(estimates) / len(estimates)
            ratio = current_price / mid
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
        fair_value_range=fair_range,
        current_price=current_price,
        verdict=verdict,
    )
