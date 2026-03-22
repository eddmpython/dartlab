"""3-Statement Pro-Forma 재무제표 엔진.

과거 재무제표에서 구조적 비율을 추출하고,
매출 성장 경로에 따라 IS → BS → CF 연결 모델을 생성한다.

외부 의존성 제로 (math 모듈만 사용).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from dartlab.engines.common.finance.extract import (
    getLatest,
    getTTM,
)

if TYPE_CHECKING:
    from dartlab.engines.analysis.analyst.simulation import SectorElasticity

# ══════════════════════════════════════
# 데이터 구조
# ══════════════════════════════════════


@dataclass
class HistoricalRatios:
    """과거 재무제표에서 추출한 구조적 비율 — pro-forma의 입력."""

    gross_margin: float  # 매출총이익률 (%)
    sga_ratio: float  # 판관비/매출 (%)
    effective_tax_rate: float  # 유효세율 (%)
    depreciation_ratio: float  # 감가상각/매출 (%)
    interest_rate_on_debt: float  # 이자비용/평균차입금 (%)
    nwc_to_revenue: float  # 순운전자본/매출 (%)
    capex_to_revenue: float  # CAPEX/매출 (%) — 양수 저장
    dividend_payout: float  # 배당성향 (%)
    receivables_to_revenue: float  # 매출채권/매출 (%)
    inventory_to_revenue: float  # 재고/매출 (%)
    payables_to_revenue: float  # 매입채무/매출 (%)
    years_used: int
    confidence: str  # "high" | "medium" | "low"
    dep_in_sga: bool = False  # v3: D&A가 SGA에 포함된 IS 구조 (이중 차감 방지)
    warnings: list[str] = field(default_factory=list)
    trends: dict[str, float] = field(default_factory=dict)  # 비율별 연간 트렌드 (v2)

    def __repr__(self) -> str:
        lines = [f"[과거 비율 분석 ({self.years_used}년, 신뢰도: {self.confidence})]"]
        lines.append(f"  매출총이익률: {self.gross_margin:.1f}%")
        lines.append(f"  판관비율: {self.sga_ratio:.1f}%{'  (D&A 포함)' if self.dep_in_sga else ''}")
        lines.append(f"  유효세율: {self.effective_tax_rate:.1f}%")
        lines.append(f"  감가상각/매출: {self.depreciation_ratio:.1f}%{'  (EBITDA 전용)' if self.dep_in_sga else ''}")
        lines.append(f"  CAPEX/매출: {self.capex_to_revenue:.1f}%")
        lines.append(f"  차입 이자율: {self.interest_rate_on_debt:.1f}%")
        lines.append(f"  NWC/매출: {self.nwc_to_revenue:.1f}%")
        lines.append(f"  배당성향: {self.dividend_payout:.1f}%")
        if self.trends:
            lines.append(
                f"  트렌드: {', '.join(f'{k}={v:+.2f}%p/yr' for k, v in self.trends.items() if abs(v) > 0.01)}"
            )
        if self.warnings:
            for w in self.warnings:
                lines.append(f"  ⚠ {w}")
        return "\n".join(lines)


@dataclass
class ProFormaYear:
    """단일 연도 pro-forma — IS + BS + CF 전체."""

    year_offset: int  # +1, +2, ... +5

    # IS
    revenue: float = 0
    cogs: float = 0
    gross_profit: float = 0
    sga: float = 0
    depreciation: float = 0
    operating_income: float = 0
    interest_expense: float = 0
    ebt: float = 0
    tax: float = 0
    net_income: float = 0
    ebitda: float = 0

    # BS
    cash: float = 0
    receivables: float = 0
    inventories: float = 0
    other_current_assets: float = 0
    current_assets: float = 0
    ppe_net: float = 0
    other_noncurrent_assets: float = 0
    total_assets: float = 0
    payables: float = 0
    short_term_debt: float = 0
    other_current_liabilities: float = 0
    current_liabilities: float = 0
    long_term_debt: float = 0
    other_noncurrent_liabilities: float = 0
    total_liabilities: float = 0
    retained_earnings: float = 0
    total_equity: float = 0

    # CF
    ocf: float = 0
    capex: float = 0
    fcf: float = 0
    dividends: float = 0
    financing_cf: float = 0
    net_cash_change: float = 0

    # 검증
    bs_balanced: bool = True


@dataclass
class ProFormaResult:
    """3-statement pro-forma 전체 결과."""

    historical_ratios: HistoricalRatios
    base_year: dict[str, float]
    projections: list[ProFormaYear]
    scenario_name: str
    revenue_growth_path: list[float]
    wacc: float
    wacc_details: dict[str, float] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    DISCLAIMER: str = "본 분석은 투자 참고용이며 투자 권유가 아닙니다."

    def __repr__(self) -> str:
        lines = [f"[Pro-Forma 재무제표 — {self.scenario_name}]"]
        lines.append(f"  WACC: {self.wacc:.1f}%")
        lines.append(f"  성장률: {' → '.join(f'{g:+.1f}%' for g in self.revenue_growth_path)}")
        lines.append("")

        # IS 요약
        lines.append("  === 손익계산서 (IS) ===")
        lines.append("  연도   |    매출    |  영업이익  |  순이익   | EBITDA")
        lines.append("  -------|-----------|-----------|----------|----------")
        for p in self.projections:
            lines.append(
                f"  +{p.year_offset}년  | {p.revenue / 1e8:>9,.0f}억 | {p.operating_income / 1e8:>9,.0f}억 "
                f"| {p.net_income / 1e8:>8,.0f}억 | {p.ebitda / 1e8:>8,.0f}억"
            )

        # BS 요약
        lines.append("")
        lines.append("  === 대차대조표 (BS) ===")
        lines.append("  연도   |   총자산   |  총부채   |  총자본   |  현금")
        lines.append("  -------|-----------|----------|----------|----------")
        for p in self.projections:
            bal = "✓" if p.bs_balanced else "✗"
            lines.append(
                f"  +{p.year_offset}년  | {p.total_assets / 1e8:>9,.0f}억 | {p.total_liabilities / 1e8:>8,.0f}억 "
                f"| {p.total_equity / 1e8:>8,.0f}억 | {p.cash / 1e8:>8,.0f}억 {bal}"
            )

        # CF 요약
        lines.append("")
        lines.append("  === 현금흐름표 (CF) ===")
        lines.append("  연도   |    OCF    |   CAPEX   |   FCF    |  배당")
        lines.append("  -------|-----------|-----------|----------|----------")
        for p in self.projections:
            lines.append(
                f"  +{p.year_offset}년  | {p.ocf / 1e8:>9,.0f}억 | {p.capex / 1e8:>9,.0f}억 "
                f"| {p.fcf / 1e8:>8,.0f}억 | {p.dividends / 1e8:>8,.0f}억"
            )

        if self.warnings:
            lines.append("")
            for w in self.warnings:
                lines.append(f"  ⚠ {w}")
        lines.append(f"\n  ※ {self.DISCLAIMER}")
        return "\n".join(lines)


# ══════════════════════════════════════
# 유틸
# ══════════════════════════════════════


def _median(values: list[float]) -> float:
    """순수 Python 중위값."""
    if not values:
        return 0.0
    s = sorted(values)
    n = len(s)
    if n % 2 == 1:
        return s[n // 2]
    return (s[n // 2 - 1] + s[n // 2]) / 2


def _remove_outliers_iqr(values: list[float]) -> list[float]:
    """IQR 기반 이상치 제거 (Q1 - 1.5×IQR ~ Q3 + 1.5×IQR)."""
    if len(values) < 4:
        return values
    s = sorted(values)
    n = len(s)
    q1 = s[n // 4]
    q3 = s[3 * n // 4]
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    return [v for v in values if lower <= v <= upper]


def _weighted_ratio(values: list[float]) -> tuple[float, float]:
    """최근 가중 비율 + 연간 트렌드 기울기.

    v2 Adaptive Ratio: 정적 중위값 대신 최근 데이터에 높은 가중치를 두고,
    방향성(트렌드)도 함께 추출한다.

    Returns:
        (weighted_value, trend_per_year)
    """
    if not values:
        return 0.0, 0.0
    if len(values) == 1:
        return values[0], 0.0

    # IQR 이상치 제거 — 원본 순서 유지를 위해 인덱스 기반
    cleaned = _remove_outliers_iqr(values)
    if not cleaned:
        cleaned = values

    # 최근 가중 평균 (최근일수록 높은 가중치)
    # 2개: [0.35, 0.65], 3개: [0.15, 0.30, 0.55], 4개: [0.10, 0.15, 0.30, 0.45], 5+개: [0.05, 0.10, 0.15, 0.25, 0.45]
    n = len(cleaned)
    if n == 2:
        weights = [0.35, 0.65]
    elif n == 3:
        weights = [0.15, 0.30, 0.55]
    elif n == 4:
        weights = [0.10, 0.15, 0.30, 0.45]
    else:
        # 5+ 데이터: 마지막 5개만 사용
        cleaned = cleaned[-5:]
        weights = [0.05, 0.10, 0.15, 0.25, 0.45]
        n = len(cleaned)
        weights = weights[-n:]

    # 가중치 정규화
    w_sum = sum(weights)
    weights = [w / w_sum for w in weights]

    weighted_val = sum(v * w for v, w in zip(cleaned, weights))

    # 트렌드: 마지막 3년 평균 - 처음 3년 평균 → 연간 기울기
    trend = 0.0
    if n >= 3:
        first_half = cleaned[: max(1, n // 2)]
        second_half = cleaned[max(1, n // 2) :]
        avg_first = sum(first_half) / len(first_half)
        avg_second = sum(second_half) / len(second_half)
        span = max(1, n - 1)
        trend = (avg_second - avg_first) / span

    return weighted_val, trend


def _annual_ttm_values(series: dict, sj: str, key: str, n: int) -> list[float]:
    """최근 N년간 연간 합산값(TTM 방식) 리스트.

    분기별 시계열에서 4분기 단위 rolling TTM을 역순으로 N개 추출.
    """
    vals = series.get(sj, {}).get(key, [])
    if not vals:
        return []
    results = []
    for end in range(len(vals), 3, -4):
        chunk = [v for v in vals[end - 4 : end] if v is not None]
        if len(chunk) == 4:
            results.append(sum(chunk))
        if len(results) >= n:
            break
    results.reverse()
    return results


def _annual_latest_values(series: dict, sj: str, key: str, n: int) -> list[float]:
    """최근 N년간 BS 최신값 리스트 (분기 말 잔액)."""
    vals = series.get(sj, {}).get(key, [])
    if not vals:
        return []
    results = []
    for end in range(len(vals), 0, -4):
        chunk = [v for v in vals[max(0, end - 4) : end] if v is not None]
        if chunk:
            results.append(chunk[-1])
        if len(results) >= n:
            break
    results.reverse()
    return results


def _safe_ratio_list(num_vals: list[float], den_vals: list[float], *, pct: bool = True) -> list[float]:
    """두 값 리스트의 비율 리스트 (% 변환 옵션)."""
    ratios = []
    for n, d in zip(num_vals, den_vals):
        if d and abs(d) > 1e-12:
            r = n / d
            if pct:
                r *= 100
            ratios.append(r)
    return ratios


# ══════════════════════════════════════
# 과거 비율 추출
# ══════════════════════════════════════


def extract_historical_ratios(
    series: dict,
    years: int = 5,
) -> HistoricalRatios:
    """과거 시계열에서 구조적 비율을 중위값으로 추출한다."""
    warnings: list[str] = []
    n = years

    # IS 계정들
    rev_vals = _annual_ttm_values(series, "IS", "sales", n)
    gp_vals = _annual_ttm_values(series, "IS", "gross_profit", n)
    sga_vals = _annual_ttm_values(series, "IS", "selling_and_administrative_expenses", n)
    pbt_vals = _annual_ttm_values(series, "IS", "profit_before_tax", n)
    tax_vals = _annual_ttm_values(series, "IS", "income_tax_expense", n)
    fc_vals = _annual_ttm_values(series, "IS", "finance_costs", n)
    if not fc_vals:
        fc_vals = _annual_ttm_values(series, "IS", "interest_expense", n)
    ni_vals = _annual_ttm_values(series, "IS", "net_profit", n)
    if not ni_vals:
        ni_vals = _annual_ttm_values(series, "IS", "net_income", n)
    op_vals = _annual_ttm_values(series, "IS", "operating_profit", n)
    if not op_vals:
        op_vals = _annual_ttm_values(series, "IS", "operating_income", n)

    # CF 계정
    dep_vals = _annual_ttm_values(series, "CF", "depreciation_and_amortization", n)
    if not dep_vals:
        dep_vals = _annual_ttm_values(series, "CF", "depreciation_cf", n)
    if not dep_vals:
        # IS에서 감가상각비 조회 시도
        dep_vals = _annual_ttm_values(series, "IS", "depreciation_and_amortization", n)
    if not dep_vals:
        dep_vals = _annual_ttm_values(series, "IS", "depreciation", n)
    capex_vals = _annual_ttm_values(series, "CF", "purchase_of_property_plant_and_equipment", n)
    div_vals = _annual_ttm_values(series, "CF", "dividends_paid", n)

    # BS 계정 (연말 잔액)
    ca_vals = _annual_latest_values(series, "BS", "current_assets", n)
    cl_vals = _annual_latest_values(series, "BS", "current_liabilities", n)
    cash_vals = _annual_latest_values(series, "BS", "cash_and_cash_equivalents", n)
    stb_vals = _annual_latest_values(series, "BS", "shortterm_borrowings", n)
    ltb_vals = _annual_latest_values(series, "BS", "longterm_borrowings", n)
    bond_vals = _annual_latest_values(series, "BS", "debentures", n)
    ar_vals = _annual_latest_values(series, "BS", "trade_receivables", n)
    if not ar_vals:
        ar_vals = _annual_latest_values(series, "BS", "trade_and_other_receivables", n)
    inv_vals = _annual_latest_values(series, "BS", "inventories", n)
    ap_vals = _annual_latest_values(series, "BS", "trade_payables", n)
    if not ap_vals:
        ap_vals = _annual_latest_values(series, "BS", "trade_and_other_payables", n)

    actual_years = len(rev_vals)
    if actual_years < 2:
        warnings.append("과거 데이터 2년 미만 — 비율 신뢰도 낮음")

    # 비율 계산 (v2: 최근 가중 + 트렌드)
    trends: dict[str, float] = {}

    gm_list = _safe_ratio_list(gp_vals, rev_vals) if gp_vals else []
    if gm_list:
        gross_margin, trends["gross_margin"] = _weighted_ratio(gm_list)
    else:
        gross_margin = 30.0

    sga_list = _safe_ratio_list(sga_vals, rev_vals) if sga_vals else []
    if sga_list:
        sga_ratio, trends["sga_ratio"] = _weighted_ratio(sga_list)
    else:
        sga_ratio = 15.0

    capex_list = [abs(c) / r * 100 for c, r in zip(capex_vals, rev_vals) if r > 0] if capex_vals else []
    if capex_list:
        capex_ratio, trends["capex_to_revenue"] = _weighted_ratio(capex_list)
    else:
        capex_ratio = 5.0

    dep_list = _safe_ratio_list(dep_vals, rev_vals) if dep_vals else []
    if dep_list:
        dep_ratio, trends["depreciation_ratio"] = _weighted_ratio(dep_list)
    elif capex_ratio > 0:
        # D&A 데이터 없으면 CAPEX의 80% 추정 (성숙 기업 순투자 < 총투자)
        dep_ratio = capex_ratio * 0.8
        warnings.append(f"감가상각 데이터 없음 — CAPEX×80% 추정 ({dep_ratio:.1f}%)")
    else:
        dep_ratio = 3.0

    # v3: K-IFRS IS 구조 감지 — D&A가 SGA에 포함되었는지 자동 판별
    # GP - SGA ≈ OP → D&A가 SGA에 이미 포함 (삼성전자, SK하이닉스 등)
    # GP - SGA - D&A ≈ OP → D&A 별도 (LG화학 등)
    dep_in_sga = False
    if gp_vals and sga_vals and op_vals:
        # 최근 3년 기준으로 판별 (안정적 판단)
        check_n = min(3, len(gp_vals), len(sga_vals), len(op_vals), len(rev_vals))
        if check_n >= 1:
            matches = 0
            for j in range(check_n):
                idx = -(j + 1)
                gp_j = gp_vals[idx]
                sga_j = sga_vals[idx]
                op_j = op_vals[idx]
                rev_j = rev_vals[idx]
                if rev_j and rev_j > 0:
                    # GP - SGA vs OP: 매출 대비 차이가 2%p 이내면 SGA에 D&A 포함
                    gap_pct = abs((gp_j - sga_j - op_j) / rev_j) * 100
                    if gap_pct < 2.0:
                        matches += 1
            if matches >= max(1, check_n - 1):
                dep_in_sga = True
                warnings.append("IS 구조 감지: D&A가 SGA에 포함 — 별도 차감 생략 (EBITDA 계산에만 사용)")

    # 유효세율
    tax_ratios = _safe_ratio_list(tax_vals, pbt_vals) if tax_vals and pbt_vals else []
    tax_ratios = [t for t in tax_ratios if 0 < t < 50]  # 비정상 제거
    if tax_ratios:
        effective_tax, trends["effective_tax_rate"] = _weighted_ratio(tax_ratios)
    else:
        effective_tax = 22.0

    # 이자율
    debt_totals = []
    for i in range(min(len(stb_vals), len(ltb_vals))):
        d = (
            (stb_vals[i] if i < len(stb_vals) else 0)
            + (ltb_vals[i] if i < len(ltb_vals) else 0)
            + (bond_vals[i] if i < len(bond_vals) else 0)
        )
        debt_totals.append(d)
    int_ratios = []
    for fc_v, d_v in zip(fc_vals, debt_totals):
        if d_v and d_v > 0 and fc_v:
            r = abs(fc_v) / d_v * 100
            if 0 < r < 30:  # 비정상 제거
                int_ratios.append(r)
    if int_ratios:
        interest_rate, _ = _weighted_ratio(int_ratios)
    else:
        interest_rate = 4.0

    # NWC/매출
    nwc_ratios = []
    for i in range(min(len(ca_vals), len(cl_vals), len(cash_vals), len(rev_vals))):
        nwc = ca_vals[i] - cl_vals[i] - cash_vals[i]
        if rev_vals[i] and abs(rev_vals[i]) > 0:
            nwc_ratios.append(nwc / rev_vals[i] * 100)
    if nwc_ratios:
        nwc_ratio, trends["nwc_to_revenue"] = _weighted_ratio(nwc_ratios)
    else:
        nwc_ratio = 10.0

    # 매출채권/매출, 재고/매출, 매입채무/매출
    ar_list = _safe_ratio_list(ar_vals, rev_vals[: len(ar_vals)]) if ar_vals else []
    inv_list = _safe_ratio_list(inv_vals, rev_vals[: len(inv_vals)]) if inv_vals else []
    ap_list = _safe_ratio_list(ap_vals, rev_vals[: len(ap_vals)]) if ap_vals else []
    ar_ratio = _weighted_ratio(ar_list)[0] if ar_list else 15.0
    inv_ratio = _weighted_ratio(inv_list)[0] if inv_list else 10.0
    ap_ratio = _weighted_ratio(ap_list)[0] if ap_list else 8.0

    # 배당성향
    payout_ratios = []
    for dv, ni in zip(div_vals, ni_vals):
        if ni and ni > 0 and dv:
            p = abs(dv) / ni * 100
            if 0 < p < 200:
                payout_ratios.append(p)
    if payout_ratios:
        payout, _ = _weighted_ratio(payout_ratios)
    else:
        payout = 0.0

    # 신뢰도
    if actual_years >= 4:
        confidence = "high"
    elif actual_years >= 2:
        confidence = "medium"
    else:
        confidence = "low"

    # 기본값 사용 경고
    if not gp_vals:
        warnings.append("매출총이익 데이터 없음 — 기본값 30% 사용")
    if not sga_vals:
        warnings.append("판관비 데이터 없음 — 기본값 15% 사용")
    if not dep_vals and capex_ratio <= 0:
        warnings.append("감가상각 데이터 없음 — 기본값 3% 사용")
    if not capex_vals:
        warnings.append("CAPEX 데이터 없음 — 기본값 5% 사용")

    return HistoricalRatios(
        gross_margin=gross_margin,
        sga_ratio=sga_ratio,
        effective_tax_rate=effective_tax,
        depreciation_ratio=dep_ratio,
        interest_rate_on_debt=interest_rate,
        nwc_to_revenue=nwc_ratio,
        capex_to_revenue=capex_ratio,
        dividend_payout=payout,
        receivables_to_revenue=ar_ratio,
        inventory_to_revenue=inv_ratio,
        payables_to_revenue=ap_ratio,
        years_used=actual_years,
        confidence=confidence,
        dep_in_sga=dep_in_sga,
        warnings=warnings,
        trends=trends,
    )


# ══════════════════════════════════════
# 회사 고유 WACC
# ══════════════════════════════════════


def compute_company_wacc(
    series: dict,
    sector_params=None,
    sector_elasticity: SectorElasticity | None = None,
    risk_free_rate: float = 3.5,
    market_premium: float = 6.0,
    market_cap: float | None = None,
) -> tuple[float, dict[str, float]]:
    """회사 고유 WACC 계산.

    WACC = E/(D+E) × Ke + D/(D+E) × Kd × (1-t)
    """
    # 차입금
    stb = getLatest(series, "BS", "shortterm_borrowings") or 0
    ltb = getLatest(series, "BS", "longterm_borrowings") or 0
    bonds = getLatest(series, "BS", "debentures") or 0
    total_debt = stb + ltb + bonds

    # 자기자본 = 시가총액 or 장부가
    equity_book = getLatest(series, "BS", "total_stockholders_equity") or getLatest(
        series, "BS", "owners_of_parent_equity"
    )
    equity_value = market_cap if market_cap else (equity_book or 1)

    # Kd (타인자본비용) — 실제 이자비용 역산
    fc = getTTM(series, "IS", "finance_costs") or getTTM(series, "IS", "interest_expense")
    if fc and total_debt > 0:
        kd = abs(fc) / total_debt * 100
        kd = max(2.0, min(kd, 15.0))  # 클램프
    else:
        kd = 4.0  # 기본값

    # Ke (자기자본비용) — v2: 업종 β 활용
    if sector_params and hasattr(sector_params, "discountRate"):
        ke = sector_params.discountRate
    elif sector_elasticity and hasattr(sector_elasticity, "revenueToGdp"):
        # GDP 감응도를 equity β proxy로 사용
        beta = max(0.5, min(sector_elasticity.revenueToGdp, 2.5))
        ke = risk_free_rate + beta * market_premium
    else:
        beta = 1.0  # 시장 평균
        ke = risk_free_rate + beta * market_premium

    # 유효세율
    pbt = getTTM(series, "IS", "profit_before_tax")
    tax_exp = getTTM(series, "IS", "income_tax_expense")
    if pbt and tax_exp and pbt > 0:
        tax_rate = min(abs(tax_exp) / pbt, 0.5)
    else:
        tax_rate = 0.22

    # WACC
    total_capital = equity_value + total_debt
    if total_capital > 0:
        e_weight = equity_value / total_capital
        d_weight = total_debt / total_capital
    else:
        e_weight, d_weight = 1.0, 0.0

    wacc = e_weight * ke + d_weight * kd * (1 - tax_rate)
    wacc = max(5.0, min(wacc, 20.0))  # 현실적 범위로 클램프

    details = {
        "ke": ke,
        "kd": kd,
        "tax_rate": tax_rate * 100,
        "equity_weight": e_weight * 100,
        "debt_weight": d_weight * 100,
        "total_debt": total_debt,
        "equity_value": equity_value,
    }
    return wacc, details


# ══════════════════════════════════════
# 3-Statement Pro-Forma 생성
# ══════════════════════════════════════


def _extract_base_year(series: dict) -> dict[str, float]:
    """현재(기준) 연도 실적 스냅샷 추출."""
    rev = getTTM(series, "IS", "sales") or 0
    gp = getTTM(series, "IS", "gross_profit")
    oi = getTTM(series, "IS", "operating_profit") or getTTM(series, "IS", "operating_income") or 0
    ni = getTTM(series, "IS", "net_profit") or getTTM(series, "IS", "net_income") or 0

    ca = getLatest(series, "BS", "current_assets") or 0
    cl = getLatest(series, "BS", "current_liabilities") or 0
    cash = getLatest(series, "BS", "cash_and_cash_equivalents") or 0
    ta = getLatest(series, "BS", "total_assets") or 0
    tl = getLatest(series, "BS", "total_liabilities") or 0
    te = getLatest(series, "BS", "total_stockholders_equity") or getLatest(series, "BS", "owners_of_parent_equity") or 0
    ppe = getLatest(series, "BS", "tangible_assets") or 0
    ar = getLatest(series, "BS", "trade_receivables") or getLatest(series, "BS", "trade_and_other_receivables") or 0
    inv = getLatest(series, "BS", "inventories") or 0
    ap = getLatest(series, "BS", "trade_payables") or getLatest(series, "BS", "trade_and_other_payables") or 0
    stb = getLatest(series, "BS", "shortterm_borrowings") or 0
    ltb = getLatest(series, "BS", "longterm_borrowings") or 0
    bonds = getLatest(series, "BS", "debentures") or 0

    return {
        "revenue": rev,
        "gross_profit": gp,
        "operating_income": oi,
        "net_income": ni,
        "current_assets": ca,
        "current_liabilities": cl,
        "cash": cash,
        "total_assets": ta,
        "total_liabilities": tl,
        "total_equity": te,
        "ppe_net": ppe,
        "receivables": ar,
        "inventories": inv,
        "payables": ap,
        "short_term_debt": stb,
        "long_term_debt": ltb + bonds,
        "total_debt": stb + ltb + bonds,
    }


def build_proforma(
    series: dict,
    revenue_growth_path: list[float],
    sector_params=None,
    sector_elasticity: SectorElasticity | None = None,
    shares: int | None = None,
    market_cap: float | None = None,
    scenario_name: str = "base",
    overrides: dict[str, float] | None = None,
) -> ProFormaResult:
    """3-statement pro-forma 생성.

    Args:
        series: 시계열 dict.
        revenue_growth_path: 연도별 매출 성장률 (%), 예: [5.0, 4.0, 3.5]
        sector_params: SectorParams (WACC 계산용).
        shares: 발행주식수.
        market_cap: 시가총액.
        scenario_name: 시나리오 이름.
        overrides: 비율 오버라이드 (예: {"gross_margin": 35.0}).
    """
    warnings: list[str] = []

    # 1. 과거 비율 추출
    ratios = extract_historical_ratios(series)
    warnings.extend(ratios.warnings)

    # 오버라이드 적용
    if overrides:
        for k, v in overrides.items():
            if hasattr(ratios, k):
                setattr(ratios, k, v)

    # 2. WACC 계산
    wacc, wacc_details = compute_company_wacc(
        series,
        sector_params=sector_params,
        sector_elasticity=sector_elasticity,
        market_cap=market_cap,
    )

    # 3. 기준연도 추출
    base = _extract_base_year(series)
    if base["revenue"] <= 0:
        warnings.append("기준 매출이 0 — pro-forma 불가")
        return ProFormaResult(
            historical_ratios=ratios,
            base_year=base,
            projections=[],
            scenario_name=scenario_name,
            revenue_growth_path=revenue_growth_path,
            wacc=wacc,
            wacc_details=wacc_details,
            warnings=warnings,
        )

    # 4. 연도별 pro-forma 생성
    projections: list[ProFormaYear] = []
    prev_revenue = base["revenue"]
    prev_ppe = base["ppe_net"]
    prev_cash = base["cash"]
    prev_equity = base["total_equity"]
    prev_stb = base["short_term_debt"]
    prev_ltb = base["long_term_debt"]
    prev_nwc = base["receivables"] + base["inventories"] - base["payables"]
    prev_other_ca = base["current_assets"] - base["cash"] - base["receivables"] - base["inventories"]
    prev_other_nca = base["total_assets"] - base["current_assets"] - base["ppe_net"]
    prev_other_cl = base["current_liabilities"] - base["payables"] - base["short_term_debt"]
    prev_other_ncl = base["total_liabilities"] - base["current_liabilities"] - base["long_term_debt"]

    # 음수 보정
    prev_other_ca = max(prev_other_ca, 0)
    prev_other_nca = max(prev_other_nca, 0)
    prev_other_cl = max(prev_other_cl, 0)
    prev_other_ncl = max(prev_other_ncl, 0)

    # v2: 비율 트렌드 경로 — 연도별 비율이 트렌드 방향으로 점진 변화
    def _ratio_for_year(
        base_val: float, trend_key: str, yr_idx: int, floor: float = 0.0, ceiling: float = 100.0
    ) -> float:
        trend = ratios.trends.get(trend_key, 0.0)
        val = base_val + trend * yr_idx
        return max(floor, min(val, ceiling))

    for i, growth_pct in enumerate(revenue_growth_path):
        yr = ProFormaYear(year_offset=i + 1)

        # v2: 연도별 비율 (트렌드 반영)
        yr_gm = _ratio_for_year(ratios.gross_margin, "gross_margin", i, floor=5.0, ceiling=90.0)
        yr_sga = _ratio_for_year(ratios.sga_ratio, "sga_ratio", i, floor=1.0, ceiling=50.0)
        yr_dep = _ratio_for_year(ratios.depreciation_ratio, "depreciation_ratio", i, floor=0.5, ceiling=30.0)
        yr_capex = _ratio_for_year(ratios.capex_to_revenue, "capex_to_revenue", i, floor=0.5, ceiling=40.0)

        # === IS ===
        yr.revenue = prev_revenue * (1 + growth_pct / 100)
        yr.cogs = yr.revenue * (1 - yr_gm / 100)
        yr.gross_profit = yr.revenue - yr.cogs
        yr.sga = yr.revenue * yr_sga / 100
        yr.depreciation = yr.revenue * yr_dep / 100

        # v3: IS 구조 분기 — D&A가 SGA에 포함된 경우 별도 차감하지 않음
        if ratios.dep_in_sga:
            # SGA에 이미 D&A 포함 → OP = GP - SGA (depreciation은 EBITDA 역산에만 사용)
            yr.operating_income = yr.gross_profit - yr.sga
        else:
            # D&A 별도 보고 → OP = GP - SGA - D&A
            yr.operating_income = yr.gross_profit - yr.sga - yr.depreciation
        yr.ebitda = yr.operating_income + yr.depreciation

        # 이자비용 = 전기 차입금 × 이자율
        total_prev_debt = prev_stb + prev_ltb
        yr.interest_expense = total_prev_debt * ratios.interest_rate_on_debt / 100

        yr.ebt = yr.operating_income - yr.interest_expense
        if yr.ebt > 0:
            yr.tax = yr.ebt * ratios.effective_tax_rate / 100
        else:
            yr.tax = 0  # 적자 시 세금 없음
        yr.net_income = yr.ebt - yr.tax

        # === BS ===
        # 운전자본 항목 (매출 비례)
        yr.receivables = yr.revenue * ratios.receivables_to_revenue / 100
        yr.inventories = yr.revenue * ratios.inventory_to_revenue / 100
        yr.payables = yr.revenue * ratios.payables_to_revenue / 100

        # CAPEX & PPE
        yr.capex = -(yr.revenue * yr_capex / 100)  # 음수
        yr.ppe_net = prev_ppe + abs(yr.capex) - yr.depreciation

        # 부채 초기값 (시나리오 기본: 변동 없음)
        yr.short_term_debt = prev_stb
        yr.long_term_debt = prev_ltb

        # 기타 항목 (비례 or 유지)
        yr.other_current_assets = prev_other_ca * (1 + growth_pct / 100 * 0.3)  # 매출 연동 30%
        yr.other_noncurrent_assets = prev_other_nca

        yr.other_current_liabilities = prev_other_cl * (1 + growth_pct / 100 * 0.3)
        yr.other_noncurrent_liabilities = prev_other_ncl

        # 배당
        if yr.net_income > 0:
            yr.dividends = yr.net_income * ratios.dividend_payout / 100
        else:
            yr.dividends = 0

        # 자본 = 전기 자본 + 순이익 - 배당
        yr.retained_earnings = prev_equity + yr.net_income - yr.dividends
        yr.total_equity = yr.retained_earnings

        # 부채 합계
        yr.current_liabilities = yr.payables + yr.short_term_debt + yr.other_current_liabilities
        yr.total_liabilities = yr.current_liabilities + yr.long_term_debt + yr.other_noncurrent_liabilities

        # Cash = plug (총자산 = 총부채 + 총자본 이므로, 나머지 자산의 차이)
        non_cash_assets = (
            yr.receivables + yr.inventories + yr.other_current_assets + yr.ppe_net + yr.other_noncurrent_assets
        )
        required_total_assets = yr.total_liabilities + yr.total_equity
        yr.cash = required_total_assets - non_cash_assets

        # v2: 현금 음수 → 자동 차입 (50:50 단기/장기 분배)
        if yr.cash < 0:
            shortfall = abs(yr.cash)
            # 반복 균형 (이자→순이익→자본 감소→현금 재하락 사이클 수렴)
            for _ in range(3):
                yr.short_term_debt += shortfall * 0.5
                yr.long_term_debt += shortfall * 0.5
                extra_interest = shortfall * ratios.interest_rate_on_debt / 100
                yr.interest_expense += extra_interest
                yr.ebt = yr.operating_income - yr.interest_expense
                yr.tax = yr.ebt * ratios.effective_tax_rate / 100 if yr.ebt > 0 else 0
                yr.net_income = yr.ebt - yr.tax
                yr.dividends = yr.net_income * ratios.dividend_payout / 100 if yr.net_income > 0 else 0
                yr.retained_earnings = prev_equity + yr.net_income - yr.dividends
                yr.total_equity = yr.retained_earnings
                yr.current_liabilities = yr.payables + yr.short_term_debt + yr.other_current_liabilities
                yr.total_liabilities = yr.current_liabilities + yr.long_term_debt + yr.other_noncurrent_liabilities
                required_total_assets = yr.total_liabilities + yr.total_equity
                yr.cash = required_total_assets - non_cash_assets
                if yr.cash >= 0:
                    break
                shortfall = abs(yr.cash)
            if yr.cash < 0:
                yr.cash = 0
            warnings.append(f"+{yr.year_offset}년: 현금 부족 → 자동 차입 {shortfall / 1e8:.0f}억")

        yr.current_assets = yr.cash + yr.receivables + yr.inventories + yr.other_current_assets
        yr.total_assets = yr.current_assets + yr.ppe_net + yr.other_noncurrent_assets

        # BS 균형 검증
        imbalance = abs(yr.total_assets - yr.total_liabilities - yr.total_equity)
        yr.bs_balanced = imbalance < max(1, yr.total_assets * 1e-10)

        # === CF ===
        nwc = yr.receivables + yr.inventories - yr.payables
        delta_nwc = nwc - prev_nwc

        yr.ocf = yr.net_income + yr.depreciation - delta_nwc
        yr.fcf = yr.ocf + yr.capex  # capex는 음수
        delta_debt = (yr.short_term_debt + yr.long_term_debt) - (prev_stb + prev_ltb)
        yr.financing_cf = delta_debt - yr.dividends
        yr.net_cash_change = yr.ocf + yr.capex + yr.financing_cf

        projections.append(yr)

        # 다음 연도용 이전값 갱신
        prev_revenue = yr.revenue
        prev_ppe = yr.ppe_net
        prev_cash = yr.cash
        prev_equity = yr.total_equity
        prev_stb = yr.short_term_debt
        prev_ltb = yr.long_term_debt
        prev_nwc = nwc
        prev_other_ca = yr.other_current_assets
        prev_other_nca = yr.other_noncurrent_assets
        prev_other_cl = yr.other_current_liabilities
        prev_other_ncl = yr.other_noncurrent_liabilities

    # v3: 영업이익률 크로스체크 — 기준연도와 예측 1년차 괴리 감지
    if projections and base["revenue"] > 0 and base["operating_income"] > 0:
        base_opm = base["operating_income"] / base["revenue"] * 100
        proj_opm = projections[0].operating_income / projections[0].revenue * 100 if projections[0].revenue > 0 else 0
        gap = abs(proj_opm - base_opm)
        if gap > 5.0:
            warnings.append(f"영업이익률 괴리 경고: 기준 {base_opm:.1f}% → 예측 {proj_opm:.1f}% (차이 {gap:.1f}%p)")

    return ProFormaResult(
        historical_ratios=ratios,
        base_year=base,
        projections=projections,
        scenario_name=scenario_name,
        revenue_growth_path=revenue_growth_path,
        wacc=wacc,
        wacc_details=wacc_details,
        warnings=warnings,
    )
