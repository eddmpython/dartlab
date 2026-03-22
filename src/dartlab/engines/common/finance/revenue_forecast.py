"""매출액 예측 엔진 v3 — 7-소스 앙상블 + 세그먼트 Bottom-Up + 시나리오.

7-소스 앙상블:
1. 자체 시계열 (과거 매출 OLS/CAGR/평균회귀)
2. 시장 컨센서스 (네이버/Yahoo 금융 애널리스트 매출 추정치)
3. 매크로 조건부 (GDP β × 섹터 감응도, β>0.5 섹터)
4. ROIC 기반 내재 성장 (Damodaran Value Driver: g = ROIC × Reinvestment Rate)
5. 세그먼트 Bottom-Up (부문별 개별 예측 → 합산)
6. 수주잔고 선행지표 (B/R ratio → 내재 성장률)
7. 환율 민감도 (수출비율 × FX β)

설계 원칙 (Engine-First, AI-Augmented):
- 엔진이 재현 가능하고 투명한 기본 예측을 생성
- ai_context 필드로 AI가 세계 지식으로 보정할 수 있는 브릿지 제공
- 결과 스키마는 도메인(DART/EDGAR/EDINET) 불문 동일
- 3-시나리오 출력 (Base/Bull/Bear)으로 불확실성 정량화
- CompanyDataBundle로 L1 데이터를 L0에 전달 (L0→L1 import 금지)

외부 의존성: gather 엔진 (optional — 없으면 시계열 only).
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    import polars as pl

from dartlab.engines.common.finance.extract import (
    getAnnualValues,
    getLatest,
    getTTM,
)
from dartlab.engines.common.finance.forecast import (
    ForecastResult,
    forecast_metric,
)

log = logging.getLogger(__name__)

# β > 0.5이고 R² 극저가 아닌 섹터만 매크로 조정 적용
# simulation.py SECTOR_ELASTICITY에서 β ≥ 0.8인 섹터
_MACRO_VALID_SECTORS = {
    "반도체", "자동차", "화학", "철강", "건설",
    "금융/증권", "IT/소프트웨어", "유통", "섬유/의류",
    "금융/은행", "금융/보험", "산업재",
}
# R² 극저 — β가 있어도 신호 대비 노이즈가 큼
_MACRO_SKIP_SECTORS: set[str] = set()

# β 크기별 매크로 가중치 (시계열에서 할당)
_MACRO_WEIGHT_HIGH = 0.10   # β ≥ 1.2
_MACRO_WEIGHT_MED = 0.05    # 0.8 ≤ β < 1.2

# ROIC 기반 성장 소스 가중치 (시계열에서 할당)
_ROIC_WEIGHT = 0.15


# ══════════════════════════════════════
# L1 → L0 데이터 브릿지
# ══════════════════════════════════════


@dataclass
class MacroData:
    """라이브 매크로 경제 데이터.

    None이면 하드코딩 기본값 fallback. 부분 제공 가능 — None인 필드만 기본값 사용.
    """

    gdp_forecast: list[float] | None = None  # 연도별 GDP 성장률 (%)
    cpi_forecast: list[float] | None = None  # 연도별 CPI (%)
    commodity_index_change: float | None = None  # CRB 등 원자재 지수 YoY 변화(%)
    oil_price_change: float | None = None  # 유가 YoY 변화(%)
    source: str = "default"  # "ecos" | "fred" | "default"


# 원자재 민감 섹터 → commodity 조정 적용
_COMMODITY_SECTORS = {"화학", "철강", "에너지", "정유", "석유화학", "비철금속"}
_COMMODITY_BETA = 0.3  # commodity 지수 10% 변동 → 매출 3% 조정


@dataclass
class CompanyDataBundle:
    """L1(Company) → L0(forecast) 데이터 브릿지.

    Company 객체를 직접 전달하지 않고, 예측에 필요한 데이터만 추출해서 전달.
    L0(common)은 L1(company)을 import하지 않는다.
    """

    segment_revenue: pl.DataFrame | None = None  # c.segments.revenue
    sales_df: pl.DataFrame | None = None  # c.salesOrder.salesDf
    order_df: pl.DataFrame | None = None  # c.salesOrder.orderDf
    export_ratio: float | None = None  # 수출비율 (0~1)
    fx_rate: float | None = None  # 현재 KRW/USD 환율
    macro_data: MacroData | None = None  # 라이브 매크로 데이터


@dataclass
class SegmentForecast:
    """개별 세그먼트 예측 결과."""

    name: str
    historical: list[Optional[float]]
    projected: list[float]
    growth_rates: list[float]
    method: str
    share_of_revenue: float  # 최근 매출 비중 (%, 0~100)
    lifecycle: str


@dataclass
class BacklogSignal:
    """수주잔고 기반 선행 시그널."""

    backlog_revenue_ratio: float  # 현재 B/R ratio
    br_ratio_trend: str  # "increasing" | "stable" | "declining"
    implied_revenue_growth: float  # 수주잔고 기반 내재 매출 성장률 (%)
    conversion_rate: float  # 과거 평균 수주→매출 전환율
    sectors_applicable: bool  # 건설/조선/방산만 강신호


@dataclass
class RevenueForecastAIOverlay:
    """AI 보정 결과 — 구조화된 스키마.

    가드레일:
    - 연간 보정 ±10%p 캡
    - 총 보정 ±20%p 캡
    - reasoning 없으면 거부
    """

    growth_adjustment: list[float]  # 연도별 %p 보정
    direction: str  # "up" | "down" | "neutral"
    magnitude: str  # "minor" (<2%p) | "moderate" (2-5%p) | "major" (>5%p)
    scenario_shift: dict[str, float] | None = None  # 시나리오 확률 이동
    reasoning: list[str] = field(default_factory=list)  # 보정 근거
    applied: bool = False


# ══════════════════════════════════════
# 결과 타입
# ══════════════════════════════════════


@dataclass
class RevenueForecastResult:
    """매출 예측 결과 — 소스별 기여도 투명 공개.

    스키마 불변 보장: 어떤 도메인/시장에서든 모든 필드가 채워짐.
    소스가 적으면 confidence가 낮아지고 warnings에 이유가 기록될 뿐.
    """

    historical: list[Optional[float]]
    projected: list[float]
    horizon: int
    method: str  # "ensemble" | "timeseries_only" | "consensus_only" | "N/A"
    confidence: str  # "high" | "medium" | "low"
    growth_rates: list[float]  # 연도별 YoY 성장률 (%)
    sources: list[str]  # ["timeseries", "consensus", "macro", "roic"]
    source_weights: dict[str, float]  # {"timeseries": 0.4, "consensus": 0.45, ...}
    consensus_revenue: list[float] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    ai_context: dict = field(default_factory=dict)

    # v3 확장 필드 (전부 default — 하위호환)
    scenarios: dict[str, list[float]] = field(default_factory=dict)  # base/bull/bear
    scenario_growth_rates: dict[str, list[float]] = field(default_factory=dict)
    scenario_probabilities: dict[str, float] = field(default_factory=dict)
    segment_forecasts: list[SegmentForecast] = field(default_factory=list)
    backlog_signal: BacklogSignal | None = None
    ai_overlay: RevenueForecastAIOverlay | None = None
    forward_test_key: str | None = None

    DISCLAIMER: str = "본 분석은 투자 참고용이며 투자 권유가 아닙니다."

    def __repr__(self) -> str:
        lines = [f"[매출 예측 — {self.method}]"]
        lines.append(f"  신뢰도: {self.confidence}")
        lc = self.ai_context.get("lifecycle", "")
        if lc:
            lines.append(f"  라이프사이클: {lc}")
        lines.append(f"  소스: {', '.join(f'{k}({v:.0%})' for k, v in self.source_weights.items())}")

        valid_hist = [v for v in self.historical if v is not None]
        if self.projected and valid_hist:
            base = self.projected[0] / (1 + self.growth_rates[0] / 100) if self.growth_rates and self.growth_rates[0] != -100 else valid_hist[-1]
            lines.append(f"  기준 매출: {base / 1e8:,.0f}억")
        elif valid_hist:
            lines.append(f"  최근 실적: {valid_hist[-1] / 1e8:,.0f}억")

        for i, (proj, gr) in enumerate(zip(self.projected, self.growth_rates), 1):
            lines.append(f"  +{i}년: {proj / 1e8:,.0f}억 ({gr:+.1f}%)")

        # v3: 시나리오
        if self.scenarios:
            probs = self.scenario_probabilities
            for label in ("bull", "bear"):
                sc = self.scenarios.get(label, [])
                sg = self.scenario_growth_rates.get(label, [])
                prob = probs.get(label, 0)
                if sc:
                    lines.append(f"  {label.title()}({prob:.0f}%): {sc[0] / 1e8:,.0f}억 ({sg[0]:+.1f}%)" if sg else f"  {label.title()}: {sc[0] / 1e8:,.0f}억")

        # v3: 세그먼트
        if self.segment_forecasts:
            lines.append(f"  세그먼트: {len(self.segment_forecasts)}개 부문")
            for sf in self.segment_forecasts[:3]:  # 상위 3개만 표시
                if sf.projected:
                    lines.append(f"    {sf.name}({sf.share_of_revenue:.0f}%): {sf.projected[0] / 1e8:,.0f}억 ({sf.growth_rates[0]:+.1f}%)" if sf.growth_rates else f"    {sf.name}: {sf.projected[0] / 1e8:,.0f}억")

        # v3: 수주잔고
        if self.backlog_signal:
            bs = self.backlog_signal
            lines.append(f"  수주잔고: B/R={bs.backlog_revenue_ratio:.1f}x ({bs.br_ratio_trend}), 내재 성장 {bs.implied_revenue_growth:+.1f}%")

        if self.assumptions:
            for a in self.assumptions:
                lines.append(f"  · {a}")
        if self.warnings:
            for w in self.warnings:
                lines.append(f"  ⚠ {w}")
        lines.append(f"  ※ {self.DISCLAIMER}")
        return "\n".join(lines)


# ══════════════════════════════════════
# 컨센서스 매출 추출
# ══════════════════════════════════════


def _fetch_consensus_revenue(
    stock_code: str, market: str = "KR",
) -> list[tuple[int, float, str]]:
    """gather에서 매출 컨센서스를 가져온다.

    KR: 네이버, US: Yahoo quoteSummary.

    Returns:
        [(fiscal_year, revenue, source), ...] — 실적+컨센서스 모두 포함.
    """
    try:
        from dartlab.engines.gather import Gather

        g = Gather()
        items = g.revenue_consensus(stock_code, market=market)
        try:
            g.close()
        except RuntimeError:
            pass  # event loop already closed
        return [
            (item.fiscal_year, item.revenue_est, item.source)
            for item in items
            if item.revenue_est > 0
        ]
    except (ImportError, OSError) as exc:
        log.debug("컨센서스 수집 실패: %s", exc)
        return []


# ══════════════════════════════════════
# ROIC 기반 내재 성장률 (Damodaran Value Driver)
# ══════════════════════════════════════


def _fundamental_growth(series: dict) -> tuple[float | None, dict]:
    """ROIC × Reinvestment Rate → 내재 성장률.

    Damodaran/McKinsey Value Driver Formula:
    g = ROIC × Reinvestment Rate
    RR = (CAPEX - Depreciation + ΔNWC) / NOPAT

    Returns:
        (growth_rate_pct, detail_dict) — 성장률(%) 또는 (None, {}).
    """
    detail: dict = {}

    # NOPAT = 영업이익 × (1 - 유효세율)
    op_income = getTTM(series, "IS", "operating_income") or getTTM(series, "IS", "operating_profit")
    if op_income is None or op_income <= 0:
        return None, detail

    pbt = getTTM(series, "IS", "profit_before_tax")
    tax_exp = getTTM(series, "IS", "income_tax_expense")
    effective_tax = 0.22  # 기본값: 한국 법인세 실효세율
    if pbt and pbt > 0 and tax_exp is not None:
        _et = tax_exp / pbt
        if 0 <= _et <= 0.5:
            effective_tax = _et

    nopat = op_income * (1 - effective_tax)

    # Invested Capital = 자기자본 + max(순차입금, 0)
    total_equity = getLatest(series, "BS", "total_stockholders_equity") or getLatest(
        series, "BS", "owners_of_parent_equity"
    )
    cash = getLatest(series, "BS", "cash_and_cash_equivalents") or 0
    short_borr = getLatest(series, "BS", "shortterm_borrowings") or 0
    long_borr = getLatest(series, "BS", "longterm_borrowings") or 0
    bonds = getLatest(series, "BS", "bonds_payable") or 0
    net_debt = short_borr + long_borr + bonds - cash

    if total_equity is None or total_equity <= 0:
        return None, detail

    invested = total_equity + max(net_debt, 0)
    if invested <= 0:
        return None, detail

    roic = (nopat / invested) * 100  # %

    # CAPEX (CF에서 음수로 기록됨)
    capex_raw = getTTM(series, "CF", "purchase_of_property_plant_and_equipment")
    capex = abs(capex_raw) if capex_raw else 0

    # Depreciation
    dep = getTTM(series, "CF", "depreciation_and_amortization")
    if dep is None:
        dep = getTTM(series, "CF", "depreciation_cf")
    if dep is None:
        dep = getTTM(series, "CF", "depreciation")
    if dep is None:
        # fallback: 유형자산 × 5% + 무형자산 × 10%
        tangible = getLatest(series, "BS", "tangible_assets") or 0
        intangible = getLatest(series, "BS", "intangible_assets") or 0
        dep = tangible * 0.05 + intangible * 0.1

    # ΔNWC (순운전자본 변동)
    # NWC = 유동자산 - 유동부채 (현금 제외)
    ca_vals = getAnnualValues(series, "BS", "current_assets")
    cl_vals = getAnnualValues(series, "BS", "current_liabilities")
    cash_vals = getAnnualValues(series, "BS", "cash_and_cash_equivalents")
    delta_nwc = 0.0
    if len(ca_vals) >= 2 and len(cl_vals) >= 2:
        # 최근 2기간 NWC 차분
        def _nwc_at(idx: int) -> float | None:
            ca = ca_vals[idx] if idx < len(ca_vals) else None
            cl = cl_vals[idx] if idx < len(cl_vals) else None
            c = cash_vals[idx] if idx < len(cash_vals) and cash_vals[idx] else 0
            if ca is not None and cl is not None:
                return (ca - (c or 0)) - cl
            return None

        nwc_curr = _nwc_at(-1)
        nwc_prev = _nwc_at(-2)
        if nwc_curr is not None and nwc_prev is not None:
            delta_nwc = nwc_curr - nwc_prev

    # Reinvestment = CAPEX - Depreciation + ΔNWC
    reinvestment = capex - dep + delta_nwc

    if nopat <= 0:
        return None, detail

    reinvestment_rate = reinvestment / nopat
    # 재투자율 범위 제한 (음수 = 자본 회수, >1.0 = 공격 투자)
    reinvestment_rate = max(min(reinvestment_rate, 1.5), -0.5)

    fundamental_g = roic * reinvestment_rate  # % 단위

    detail = {
        "roic": round(roic, 2),
        "reinvestment_rate": round(reinvestment_rate * 100, 1),
        "nopat": nopat,
        "invested_capital": invested,
        "capex": capex,
        "depreciation": dep,
        "delta_nwc": delta_nwc,
        "fundamental_growth": round(fundamental_g, 2),
    }

    return fundamental_g, detail


# ══════════════════════════════════════
# 기업 라이프사이클 판별
# ══════════════════════════════════════


def _classify_lifecycle(series: dict) -> tuple[str, dict]:
    """기업 라이프사이클 단계 판별.

    판별 기준:
    - 매출 3Y CAGR > 15% + CV < 0.3 → high_growth
    - CAGR 0~15% + CV < 0.3 → mature
    - CV > 0.4 또는 CAGR 부호 급변 → transition
    - CAGR < -5% 지속 → decline

    Returns:
        (lifecycle, detail_dict)
    """
    rev_vals = getAnnualValues(series, "IS", "revenue") or getAnnualValues(series, "IS", "sales")
    valid = [v for v in rev_vals if v is not None and v > 0]

    if len(valid) < 4:
        return "unknown", {"reason": "매출 데이터 4기간 미만"}

    # 3Y CAGR
    recent = valid[-4:]  # 최근 4개 = 3년 성장
    cagr = ((recent[-1] / recent[0]) ** (1 / 3) - 1) * 100 if recent[0] > 0 else 0

    # CV (Coefficient of Variation)
    mean_rev = sum(recent) / len(recent)
    if mean_rev > 0:
        variance = sum((v - mean_rev) ** 2 for v in recent) / len(recent)
        cv = math.sqrt(variance) / mean_rev
    else:
        cv = 0

    # 부호 변화 횟수 (성장률 방향 전환)
    growth_signs = []
    for i in range(1, len(recent)):
        if recent[i - 1] > 0:
            growth_signs.append(1 if recent[i] > recent[i - 1] else -1)
    sign_changes = sum(1 for i in range(1, len(growth_signs)) if growth_signs[i] != growth_signs[i - 1])

    detail = {
        "cagr_3y": round(cagr, 1),
        "cv": round(cv, 3),
        "sign_changes": sign_changes,
        "data_points": len(valid),
    }

    # sign_changes 임계: 분기 데이터(>8개)는 3회, 연간은 2회
    sign_threshold = 3 if len(recent) > 8 else 2
    if cv > 0.4 or sign_changes >= sign_threshold:
        return "transition", detail
    if cagr > 15 and cv < 0.3:
        return "high_growth", detail
    if cagr < -5:
        return "decline", detail
    return "mature", detail


def _lifecycle_weight_adjustments(
    lifecycle: str,
    base_weights: dict[str, float],
) -> dict[str, float]:
    """라이프사이클에 따른 가중치 조정.

    high_growth: 컨센서스↑, ROIC↑ (성장 기업은 컨센서스가 잘 추적)
    mature: 시계열↑, ROIC↑ (안정적 기업은 과거 추세가 신뢰도↑)
    transition: 컨센서스↑ (전환기는 과거가 미래를 반영 못함)
    decline: mean_revert 강제, 시계열↑
    """
    w = dict(base_weights)

    if lifecycle == "high_growth":
        # 컨센서스 의존도 높임
        if "consensus" in w and "timeseries" in w:
            shift = min(0.1, w["timeseries"])
            w["consensus"] += shift
            w["timeseries"] -= shift
    elif lifecycle == "mature":
        # ROIC, 시계열에 더 의존
        if "roic" in w and "consensus" in w:
            shift = min(0.05, w["consensus"])
            w["roic"] += shift
            w["consensus"] -= shift
    elif lifecycle == "transition":
        # 넓은 신뢰구간 (여기서는 가중치보다 confidence에 반영)
        if "consensus" in w and "timeseries" in w:
            shift = min(0.1, w["timeseries"])
            w["consensus"] += shift
            w["timeseries"] -= shift
    # decline: 기본 가중치 유지 (시계열 mean_revert가 이미 보수적)

    return w


# ══════════════════════════════════════
# 앙상블 가중치 계산
# ══════════════════════════════════════


def _compute_weights(
    ts_available: bool,
    consensus_items: list[tuple[int, float, str]],
    sector_key: str | None,
    roic_growth: float | None,
) -> dict[str, float]:
    """소스별 가중치 계산.

    규칙:
    - 컨센서스 가용 → 컨센 45%, 시계열 40%, ROIC 15% (있으면)
    - 컨센서스 없음 → 시계열 85%, ROIC 15% (있으면)
    - 매크로: β ≥ 1.2 → 10%, 0.8~1.2 → 5% (시계열에서 할당)
    """
    weights: dict[str, float] = {}

    has_consensus_est = any(src.endswith("_consensus") for _, _, src in consensus_items)

    if ts_available and has_consensus_est:
        weights["timeseries"] = 0.40
        weights["consensus"] = 0.45
    elif has_consensus_est:
        weights["consensus"] = 1.0
    else:
        weights["timeseries"] = 1.0

    # ROIC 소스: 시계열에서 할당
    if roic_growth is not None and "timeseries" in weights:
        roic_share = min(_ROIC_WEIGHT, weights["timeseries"])
        weights["roic"] = roic_share
        weights["timeseries"] -= roic_share

    # 매크로 β: 유효 섹터에서 시계열 할당
    if sector_key and sector_key not in _MACRO_SKIP_SECTORS and "timeseries" in weights:
        try:
            from dartlab.engines.common.finance.simulation import get_elasticity
            beta = get_elasticity(sector_key).revenue_to_gdp
        except (ImportError, AttributeError):
            beta = 0

        if beta >= 1.2 and sector_key in _MACRO_VALID_SECTORS:
            macro_share = min(_MACRO_WEIGHT_HIGH, weights["timeseries"])
            weights["macro"] = macro_share
            weights["timeseries"] -= macro_share
        elif beta >= 0.8 and sector_key in _MACRO_VALID_SECTORS:
            macro_share = min(_MACRO_WEIGHT_MED, weights["timeseries"])
            weights["macro"] = macro_share
            weights["timeseries"] -= macro_share

    return weights


# ══════════════════════════════════════
# 매크로 조정
# ══════════════════════════════════════


def _macro_adjustment(
    sector_key: str,
    horizon: int,
    macro_data: MacroData | None = None,
) -> list[float]:
    """GDP β + 원자재 감응도 기반 매출 성장률 조정치 (% 단위).

    macro_data가 있으면 라이브 GDP/원자재 데이터 사용, 없으면 하드코딩 fallback.
    """
    if sector_key in _MACRO_SKIP_SECTORS:
        return [0.0] * horizon

    try:
        from dartlab.engines.common.finance.simulation import get_elasticity

        elasticity = get_elasticity(sector_key)
        beta = elasticity.revenue_to_gdp
    except (ImportError, AttributeError, KeyError):
        return [0.0] * horizon

    if beta < 0.5:
        return [0.0] * horizon

    # GDP 전망: 라이브 → 하드코딩 fallback
    _DEFAULT_GDP = [1.5, 2.0, 2.2]
    if macro_data and macro_data.gdp_forecast:
        gdp_forecast = macro_data.gdp_forecast
    else:
        gdp_forecast = _DEFAULT_GDP

    adjustments = []
    for i in range(horizon):
        gdp = gdp_forecast[i] if i < len(gdp_forecast) else gdp_forecast[-1]
        adj = beta * gdp / 100  # β × ΔGDP → 매출 성장률 조정
        adjustments.append(adj * 100)  # % 단위로 변환

    # 원자재 민감 섹터: commodity 지수 변동 반영
    if sector_key in _COMMODITY_SECTORS and macro_data:
        commodity_change = macro_data.commodity_index_change
        oil_change = macro_data.oil_price_change
        # 더 강한 시그널 사용 (commodity 지수 우선, 없으면 유가)
        raw_change = commodity_change if commodity_change is not None else oil_change
        if raw_change is not None:
            # commodity 10% 변동 → 매출 _COMMODITY_BETA% 조정, 감쇠 적용
            for i in range(len(adjustments)):
                decay = 1.0 / (1 + i * 0.3)  # 시간 감쇠: 1년차 100%, 2년차 77%, 3년차 63%
                commodity_adj = _COMMODITY_BETA * (raw_change / 10) * decay
                adjustments[i] += commodity_adj

    return adjustments


# ══════════════════════════════════════
# 세그먼트 Bottom-Up 예측 (Source 5)
# ══════════════════════════════════════

# 세그먼트 가중치: 시계열에서 할당
_SEGMENT_WEIGHT = 0.25

# 건설/조선/방산: 수주잔고 선행 시그널 가중치
_BACKLOG_WEIGHT = 0.15
_BACKLOG_SECTORS = {"건설", "조선", "방산", "건설/토목", "조선/기계"}


def _extract_segment_forecasts(
    segment_revenue: object,  # pl.DataFrame | None (TYPE_CHECKING 회피)
    horizon: int = 3,
) -> list[SegmentForecast]:
    """세그먼트별 개별 시계열 예측.

    segment_revenue: Polars DataFrame — columns: ["부문", "2024", "2023", ...].
    """
    if segment_revenue is None:
        return []

    try:
        import polars as pl_rt
    except ImportError:
        return []

    df = segment_revenue
    if not hasattr(df, "columns") or "부문" not in df.columns:
        return []

    # 연도 컬럼 추출 (숫자만)
    year_cols = sorted(
        [c for c in df.columns if c != "부문" and c.isdigit()],
        key=int,
    )
    if len(year_cols) < 3:
        return []

    total_latest = 0.0
    segment_latest: dict[str, float] = {}

    results: list[SegmentForecast] = []
    for row in df.iter_rows(named=True):
        name = row.get("부문", "")
        if not name:
            continue

        # 시계열 추출 (오래된 순서로)
        vals = [row.get(y) for y in year_cols]
        valid = [(i, v) for i, v in enumerate(vals) if v is not None and v > 0]
        if len(valid) < 3:
            continue

        # 최근 매출 (비중 계산용)
        latest = valid[-1][1]
        segment_latest[name] = latest
        total_latest += latest

        # forecast_metric에 넣기 위한 가짜 series dict 구성
        fake_series = {
            "IS": {"sales": [v for _, v in valid]},
        }
        fr = forecast_metric(fake_series, "revenue", horizon)
        if not fr.projected:
            continue

        # 라이프사이클 판정
        lc, _ = _classify_lifecycle(fake_series)

        # 성장률 계산
        growth_rates: list[float] = []
        prev_val = latest
        for p in fr.projected:
            if prev_val > 0:
                growth_rates.append(round((p / prev_val - 1) * 100, 1))
            else:
                growth_rates.append(0.0)
            prev_val = p

        results.append(
            SegmentForecast(
                name=name,
                historical=[v for _, v in valid],
                projected=fr.projected,
                growth_rates=growth_rates,
                method=fr.method,
                share_of_revenue=0.0,  # 후처리에서 계산
                lifecycle=lc,
            )
        )

    # 비중 계산
    if total_latest > 0:
        for sf in results:
            latest_rev = segment_latest.get(sf.name, 0)
            sf.share_of_revenue = round(latest_rev / total_latest * 100, 1)

    # 비중 내림차순 정렬
    results.sort(key=lambda x: x.share_of_revenue, reverse=True)
    return results


def _segment_bottom_up_growth(
    segment_forecasts: list[SegmentForecast],
    horizon: int,
    last_revenue: float | None,
) -> list[float]:
    """세그먼트별 예측을 합산하여 Bottom-Up 성장률 시계열 생성.

    Returns:
        연도별 Bottom-Up 성장률 (%), 불가능하면 빈 리스트.
    """
    if not segment_forecasts or not last_revenue or last_revenue <= 0:
        return []

    growth_rates: list[float] = []
    # 세그먼트 합산: 각 연도별 세그먼트 projected 합
    prev_total = sum(sf.historical[-1] for sf in segment_forecasts if sf.historical)
    if prev_total <= 0:
        return []

    for yr in range(horizon):
        yr_total = 0.0
        for sf in segment_forecasts:
            if yr < len(sf.projected):
                yr_total += sf.projected[yr]
            elif sf.projected:
                yr_total += sf.projected[-1]
        if prev_total > 0:
            growth_rates.append((yr_total / prev_total - 1) * 100)
        else:
            growth_rates.append(0.0)
        prev_total = yr_total

    return growth_rates


# ══════════════════════════════════════
# 수주잔고 선행지표 (Source 6)
# ══════════════════════════════════════


def _compute_backlog_signal(
    order_df: object,  # pl.DataFrame | None
    sales_df: object,  # pl.DataFrame | None
    sector_key: str | None = None,
) -> BacklogSignal | None:
    """수주잔고 기반 선행 시그널 계산.

    order_df: Polars DataFrame — columns: ["label", "v1", "v2", ...] or 실제 헤더.
    sales_df: Polars DataFrame — 동일 구조.
    """
    if order_df is None or sales_df is None:
        return None

    if not hasattr(order_df, "columns") or not hasattr(sales_df, "columns"):
        return None

    try:
        # 수주잔고 합산 (모든 행의 마지막 value 컬럼 합)
        order_val_cols = [c for c in order_df.columns if c != "label"]
        sales_val_cols = [c for c in sales_df.columns if c != "label"]

        if not order_val_cols or not sales_val_cols:
            return None

        # 최신 기간 수주잔고 합산
        latest_order_col = order_val_cols[0]  # 첫 컬럼이 최근
        latest_sales_col = sales_val_cols[0]

        order_total = 0.0
        for row in order_df.iter_rows(named=True):
            v = row.get(latest_order_col)
            if v is not None and isinstance(v, (int, float)):
                order_total += abs(v)

        sales_total = 0.0
        for row in sales_df.iter_rows(named=True):
            v = row.get(latest_sales_col)
            if v is not None and isinstance(v, (int, float)):
                sales_total += abs(v)

        if sales_total <= 0 or order_total <= 0:
            return None

        br_ratio = order_total / sales_total

        # B/R ratio 추세 (2기간 이상 필요)
        br_ratios: list[float] = []
        n_periods = min(len(order_val_cols), len(sales_val_cols))
        for i in range(min(n_periods, 3)):
            o_col = order_val_cols[i]
            s_col = sales_val_cols[i]
            o_sum = sum(
                abs(row.get(o_col, 0) or 0)
                for row in order_df.iter_rows(named=True)
                if isinstance(row.get(o_col), (int, float))
            )
            s_sum = sum(
                abs(row.get(s_col, 0) or 0)
                for row in sales_df.iter_rows(named=True)
                if isinstance(row.get(s_col), (int, float))
            )
            if s_sum > 0:
                br_ratios.append(o_sum / s_sum)

        # 추세 판단
        if len(br_ratios) >= 2:
            if br_ratios[0] > br_ratios[-1] * 1.05:
                trend = "increasing"
            elif br_ratios[0] < br_ratios[-1] * 0.95:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "stable"

        # 내재 매출 성장률: B/R ratio 변화 → 매출 성장 추정
        if len(br_ratios) >= 2 and br_ratios[-1] > 0:
            implied_growth = (br_ratios[0] / br_ratios[-1] - 1) * 100
        else:
            implied_growth = 0.0

        # 전환율: 역사적 평균 (매출/수주잔고)
        conversion_rate = 1.0 / br_ratio if br_ratio > 0 else 0.0

        is_applicable = bool(
            sector_key and any(s in sector_key for s in _BACKLOG_SECTORS)
        )

        return BacklogSignal(
            backlog_revenue_ratio=round(br_ratio, 2),
            br_ratio_trend=trend,
            implied_revenue_growth=round(implied_growth, 1),
            conversion_rate=round(conversion_rate, 3),
            sectors_applicable=is_applicable,
        )
    except (TypeError, ValueError, KeyError):
        return None


# ══════════════════════════════════════
# 3-시나리오 빌더 (Base/Bull/Bear)
# ══════════════════════════════════════

# 라이프사이클별 spread 배수 (1σ 대비)
_LIFECYCLE_SPREAD = {
    "high_growth": 1.5,
    "mature": 0.7,
    "transition": 2.0,
    "decline": 1.2,
    "unknown": 1.0,
}


def _build_scenarios(
    projected: list[float],
    growth_rates: list[float],
    historical: list[Optional[float]],
    lifecycle: str,
    last_revenue: float | None,
) -> tuple[dict[str, list[float]], dict[str, list[float]], dict[str, float]]:
    """Base/Bull/Bear 3-시나리오 생성.

    Returns:
        (scenarios, scenario_growth_rates, scenario_probabilities)
    """
    if not projected or not last_revenue or last_revenue <= 0:
        return {}, {}, {}

    # 과거 성장률 변동성 (σ) 계산
    valid_hist = [v for v in historical if v is not None and v > 0]
    hist_growth: list[float] = []
    for i in range(1, len(valid_hist)):
        if valid_hist[i - 1] > 0:
            hist_growth.append((valid_hist[i] / valid_hist[i - 1] - 1) * 100)

    if hist_growth:
        mean_g = sum(hist_growth) / len(hist_growth)
        variance = sum((g - mean_g) ** 2 for g in hist_growth) / max(len(hist_growth) - 1, 1)
        sigma = math.sqrt(variance)
    else:
        sigma = 5.0  # 기본 5%p

    # 최소 sigma 보장 (너무 좁은 밴드 방지)
    sigma = max(sigma, 3.0)

    spread = _LIFECYCLE_SPREAD.get(lifecycle, 1.0)

    scenarios: dict[str, list[float]] = {"base": list(projected)}
    scenario_grs: dict[str, list[float]] = {"base": list(growth_rates)}

    # Bull / Bear
    for label, direction in [("bull", 1.0), ("bear", -1.0)]:
        sc_projected: list[float] = []
        sc_grs: list[float] = []
        prev = last_revenue
        for i, gr in enumerate(growth_rates):
            # 시간 감쇠: 멀수록 불확실성 증가
            time_factor = 1.0 + i * 0.15
            adj_gr = gr + direction * sigma * spread * time_factor
            # Bull cap: 2× base growth, Bear floor: -base growth (mature 이상)
            if direction > 0:
                adj_gr = min(adj_gr, max(gr * 2, gr + 20))
            else:
                if lifecycle != "decline":
                    adj_gr = max(adj_gr, min(gr * 0.5, gr - 20))
            val = prev * (1 + adj_gr / 100)
            sc_projected.append(val)
            sc_grs.append(round(adj_gr, 1))
            prev = val
        scenarios[label] = sc_projected
        scenario_grs[label] = sc_grs

    probabilities = {"base": 50.0, "bull": 25.0, "bear": 25.0}

    return scenarios, scenario_grs, probabilities


# ══════════════════════════════════════
# FX 민감도 (Source 7)
# ══════════════════════════════════════

# 기준 환율 (5년 평균 근사)
_FX_BASELINE = 1300.0  # KRW/USD 5년 평균 근사


def _compute_fx_adjustment(
    export_ratio: float | None,
    fx_rate: float | None,
    sector_key: str | None,
) -> float:
    """수출비율 × 환율 편차 → 매출 성장률 조정 (%p).

    Returns:
        매출 성장률 조정치 (%p). 적용 불가 시 0.0.
    """
    if not export_ratio or export_ratio < 0.3 or not fx_rate or fx_rate <= 0:
        return 0.0

    # 환율 편차 (%)
    fx_deviation = (fx_rate - _FX_BASELINE) / _FX_BASELINE * 100

    # 섹터별 환율 감응도 (기본 0.5)
    fx_beta = 0.5
    try:
        from dartlab.engines.common.finance.simulation import get_elasticity
        elasticity = get_elasticity(sector_key or "")
        if hasattr(elasticity, "revenue_to_fx") and elasticity.revenue_to_fx > 0:
            fx_beta = elasticity.revenue_to_fx
    except (ImportError, AttributeError, KeyError):
        pass

    # 조정: 수출비율 × β × (환율편차 / 10)
    # 10으로 나누어 10% 환율 변동 → β만큼 매출 성장률 조정
    adj = export_ratio * fx_beta * (fx_deviation / 10)
    return round(adj, 2)


# ══════════════════════════════════════
# 메인 예측 함수
# ══════════════════════════════════════


def forecast_revenue(
    series: dict,
    stock_code: str | None = None,
    sector_key: str | None = None,
    market: str = "KR",
    horizon: int = 3,
    company_data: CompanyDataBundle | None = None,
) -> RevenueForecastResult:
    """매출액 앙상블 예측.

    Args:
        series: finance timeseries dict (buildTimeseries 결과).
        stock_code: 종목코드 (없으면 시계열 only).
        sector_key: 섹터명 (매크로 β 적용 판단).
        market: 시장 ("KR" | "US" | "JP"). 컨센서스 소스 라우팅.
        horizon: 예측 기간 (년).
        company_data: L1 데이터 번들 (세그먼트, 수주, 환율 등). None이면 v2 동작.

    Returns:
        RevenueForecastResult — 스키마 불변 (도메인 불문).
    """
    warnings: list[str] = []
    assumptions: list[str] = []

    # ── 라이프사이클 판별 ──
    lifecycle, lifecycle_detail = _classify_lifecycle(series)

    # ── Source 1: 시계열 예측 (기존 forecast.py) ──
    ts_result = forecast_metric(series, "revenue", horizon)
    ts_available = len(ts_result.projected) > 0

    # 과거 매출 시계열 (revenue 키 조회)
    historical = ts_result.historical

    # 최근 매출 (앙상블 기준점)
    valid_hist = [v for v in historical if v is not None]
    last_revenue = valid_hist[-1] if valid_hist else None

    # ── Source 2: 컨센서스 (KR: 네이버, US+: Yahoo) ──
    consensus_items: list[tuple[int, float, str]] = []
    if stock_code:
        consensus_items = _fetch_consensus_revenue(stock_code, market)
        if not consensus_items and market != "KR":
            warnings.append(f"컨센서스 수집 실패({market}) — 시계열 기반 예측")

    # ── Source 4: ROIC 기반 내재 성장 ──
    roic_growth, roic_detail = _fundamental_growth(series)
    roic_growth_rate: float | None = roic_growth  # % 단위

    # ── Source 5: 세그먼트 Bottom-Up ──
    segment_forecasts: list[SegmentForecast] = []
    seg_growth_rates: list[float] = []
    if company_data and company_data.segment_revenue is not None:
        segment_forecasts = _extract_segment_forecasts(
            company_data.segment_revenue, horizon,
        )
        if segment_forecasts:
            seg_growth_rates = _segment_bottom_up_growth(
                segment_forecasts, horizon, last_revenue,
            )

    # ── Source 6: 수주잔고 선행지표 ──
    backlog_signal: BacklogSignal | None = None
    if company_data and company_data.order_df is not None:
        backlog_signal = _compute_backlog_signal(
            company_data.order_df,
            company_data.sales_df,
            sector_key,
        )

    # ── 가중치 계산 ──
    weights = _compute_weights(ts_available, consensus_items, sector_key, roic_growth)

    # v3 소스 가중치 할당 (시계열에서 할당)
    if seg_growth_rates and "timeseries" in weights:
        seg_share = min(_SEGMENT_WEIGHT, weights["timeseries"])
        weights["segments"] = seg_share
        weights["timeseries"] -= seg_share

    if backlog_signal and backlog_signal.sectors_applicable and "timeseries" in weights:
        bl_share = min(_BACKLOG_WEIGHT, weights["timeseries"])
        weights["backlog"] = bl_share
        weights["timeseries"] -= bl_share

    # 라이프사이클 기반 가중치 조정
    weights = _lifecycle_weight_adjustments(lifecycle, weights)

    # ── Source 3: 매크로 조정 ──
    macro_adj = [0.0] * horizon
    if "macro" in weights and sector_key:
        macro_data = company_data.macro_data if company_data else None
        macro_adj = _macro_adjustment(sector_key, horizon, macro_data)
        if any(abs(a) > 0.01 for a in macro_adj):
            src_label = macro_data.source if macro_data else "default"
            assumptions.append(f"매크로 β 조정: {sector_key} GDP 감응도 적용 (source={src_label})")

    # ── Source 7: FX 조정 (매크로에 합산) ──
    fx_adj = 0.0
    if company_data:
        fx_adj = _compute_fx_adjustment(
            company_data.export_ratio, company_data.fx_rate, sector_key,
        )
        if abs(fx_adj) > 0.01:
            macro_adj = [m + fx_adj for m in macro_adj]
            assumptions.append(f"환율 조정: 수출비율 {(company_data.export_ratio or 0) * 100:.0f}%, FX {fx_adj:+.1f}%p")

    # ── 앙상블 ──
    projected: list[float] = []
    consensus_revenue: list[float] = []

    # 컨센서스에서 전체 매출 시계열 (actual + estimate) 구축
    consensus_by_year: dict[int, tuple[float, str]] = {}  # year → (revenue_원, source)
    if consensus_items:
        for fy, rev, src in consensus_items:
            if rev > 0:
                consensus_by_year[fy] = (rev * 1e8, src)  # 억원 → 원

    # 컨센서스 estimate만 추출
    consensus_proj: dict[int, float] = {}
    for fy, (rev_won, src) in consensus_by_year.items():
        if src.endswith("_consensus"):
            consensus_proj[fy] = rev_won
            consensus_revenue.append(rev_won)

    # 기준 연도: 컨센서스 actual 중 가장 최근
    base_year = 0
    last_actual_revenue: float | None = None
    actuals_sorted = sorted(
        [(fy, rev) for fy, (rev, src) in consensus_by_year.items() if src.endswith("_actual")],
        key=lambda x: x[0],
    )
    if actuals_sorted:
        base_year = actuals_sorted[-1][0]
        last_actual_revenue = actuals_sorted[-1][1]
    if base_year == 0:
        base_year = 2025

    # last_revenue를 컨센서스 actual과 동기화 (더 신뢰할 수 있으므로)
    if last_actual_revenue:
        last_revenue = last_actual_revenue

    # 시계열 성장률: projected 간 YoY 성장률 (분기 데이터이므로 자체 기준 비교)
    ts_growth_rates: list[float] = []
    if ts_available and ts_result.projected:
        prev = ts_result.historical[-1] if ts_result.historical and ts_result.historical[-1] else None
        for p in ts_result.projected:
            if prev and prev > 0 and p > 0:
                ts_growth_rates.append((p / prev - 1) * 100)
            else:
                ts_growth_rates.append(ts_result.growth_rate)
            prev = p

    # 컨센서스 성장률 계산
    con_growth_rates: list[float] = []
    sorted_con_years = sorted(consensus_proj.keys())
    for i, fy in enumerate(sorted_con_years):
        if i == 0:
            # 첫 컨센서스 연도: actual 대비 성장률
            if last_revenue and last_revenue > 0:
                con_growth_rates.append((consensus_proj[fy] / last_revenue - 1) * 100)
            else:
                con_growth_rates.append(0.0)
        else:
            prev_fy = sorted_con_years[i - 1]
            prev_rev = consensus_proj[prev_fy]
            if prev_rev > 0:
                con_growth_rates.append((consensus_proj[fy] / prev_rev - 1) * 100)
            else:
                con_growth_rates.append(0.0)

    # ROIC 성장률: horizon 동안 일정 (내재 성장은 구조적)
    roic_g = roic_growth_rate if roic_growth_rate is not None else 0.0

    # ROIC vs 시계열 괴리 감지
    roic_ts_gap: float | None = None
    if roic_growth_rate is not None and ts_growth_rates:
        avg_ts_g = sum(ts_growth_rates) / len(ts_growth_rates)
        roic_ts_gap = roic_growth_rate - avg_ts_g
        if abs(roic_ts_gap) > 10:
            warnings.append(
                f"ROIC 내재 성장률({roic_growth_rate:.1f}%)과 "
                f"시계열 성장률({avg_ts_g:.1f}%) 괴리 {roic_ts_gap:+.1f}%p"
            )

    # 앙상블: 성장률 기반 블렌딩 (스케일 불일치 방지)
    prev_revenue = last_revenue or 0
    for yr_offset in range(1, horizon + 1):
        if prev_revenue <= 0:
            break

        # 시계열 성장률
        ts_g = ts_growth_rates[yr_offset - 1] if yr_offset <= len(ts_growth_rates) else (ts_growth_rates[-1] if ts_growth_rates else 0.0)

        # 컨센서스 성장률
        con_g = con_growth_rates[yr_offset - 1] if yr_offset <= len(con_growth_rates) else None

        # 매크로 조정
        macro_g = macro_adj[yr_offset - 1] if yr_offset <= len(macro_adj) else 0.0

        # 가중 성장률 계산
        blended_growth = 0.0
        if con_g is not None and "consensus" in weights:
            blended_growth += con_g * weights.get("consensus", 0)
            blended_growth += ts_g * weights.get("timeseries", 0)
        else:
            # 컨센서스 없는 연도 → 시계열이 컨센서스 몫도 흡수
            blended_growth += ts_g * (weights.get("timeseries", 0) + weights.get("consensus", 0))

        blended_growth += macro_g * weights.get("macro", 0)
        blended_growth += roic_g * weights.get("roic", 0)

        # v3: 세그먼트 Bottom-Up 성장률
        if seg_growth_rates and "segments" in weights:
            seg_g = seg_growth_rates[yr_offset - 1] if yr_offset <= len(seg_growth_rates) else (seg_growth_rates[-1] if seg_growth_rates else 0.0)
            blended_growth += seg_g * weights.get("segments", 0)

        # v3: 수주잔고 내재 성장률
        if backlog_signal and "backlog" in weights:
            # 수주잔고 신호는 horizon 동안 감쇠
            decay = max(0.5, 1.0 - (yr_offset - 1) * 0.2)
            blended_growth += backlog_signal.implied_revenue_growth * decay * weights.get("backlog", 0)

        proj_val = prev_revenue * (1 + blended_growth / 100)
        projected.append(proj_val)
        prev_revenue = proj_val

    # ── 스키마 보장: projected가 horizon보다 적으면 패딩 ──
    while len(projected) < horizon:
        if projected:
            projected.append(projected[-1])
        elif last_revenue and last_revenue > 0:
            projected.append(last_revenue)
        else:
            projected.append(0.0)

    # ── 성장률 계산 ──
    growth_rates: list[float] = []
    for i, proj in enumerate(projected):
        if i == 0 and last_revenue and last_revenue > 0:
            growth_rates.append((proj / last_revenue - 1) * 100)
        elif i > 0 and projected[i - 1] > 0:
            growth_rates.append((proj / projected[i - 1] - 1) * 100)
        else:
            growth_rates.append(0.0)

    while len(growth_rates) < horizon:
        growth_rates.append(0.0)

    # ── 메서드 & 신뢰도 결정 ──
    active_sources = [s for s in weights if weights[s] > 0]
    if not active_sources:
        active_sources = ["timeseries"]
    method = "ensemble" if len(active_sources) > 1 else f"{active_sources[0]}_only"

    # 신뢰도: 소스 수 + 시계열 R² + 컨센서스 유무 + 라이프사이클
    if len(active_sources) >= 3 and ts_result.r_squared > 0.5:
        confidence = "high"
    elif len(active_sources) >= 2 and (ts_available or consensus_proj):
        confidence = "medium" if lifecycle != "transition" else "low"
    elif ts_available or consensus_proj:
        confidence = "medium"
    else:
        confidence = "low"

    # transition → 최대 medium
    if lifecycle == "transition" and confidence == "high":
        confidence = "medium"

    # 비-KR 시장에서 컨센서스 없으면 → 최대 medium
    if market != "KR" and not consensus_proj:
        if confidence == "high":
            confidence = "medium"

    # ── 스키마 보장: source_weights 합이 1.0 ──
    # 라이프사이클 조정 등으로 합이 1.0이 아닐 수 있으므로 정규화
    w_sum = sum(v for v in weights.values() if v > 0)
    if w_sum > 0 and abs(w_sum - 1.0) > 0.01:
        for k in weights:
            if weights[k] > 0:
                weights[k] = weights[k] / w_sum

    final_weights = {k: round(v, 2) for k, v in weights.items() if v > 0}
    if not final_weights:
        final_weights = {"timeseries": 1.0}
    # 반올림 오차 보정: 가장 큰 가중치에 잔여분 할당
    w_total = sum(final_weights.values())
    if abs(w_total - 1.0) > 0.001 and final_weights:
        max_key = max(final_weights, key=final_weights.get)  # type: ignore[arg-type]
        final_weights[max_key] = round(final_weights[max_key] + (1.0 - w_total), 2)

    # ── 가정 설명 (정규화된 가중치 기준) ──
    for src, w in final_weights.items():
        if w > 0:
            if src == "timeseries":
                assumptions.append(f"시계열({w:.0%}): {ts_result.method}, R²={ts_result.r_squared:.2f}")
            elif src == "consensus":
                n_est = len(consensus_proj)
                assumptions.append(f"컨센서스({w:.0%}): 네이버 금융 {n_est}개년 추정치")
            elif src == "macro":
                assumptions.append(f"매크로({w:.0%}): {sector_key} GDP β 감응도")
            elif src == "roic":
                assumptions.append(f"ROIC({w:.0%}): g=ROIC×재투자율={roic_growth_rate:.1f}%")

    if lifecycle != "unknown":
        assumptions.append(f"라이프사이클: {lifecycle} (CAGR {lifecycle_detail.get('cagr_3y', 'N/A')}%, CV {lifecycle_detail.get('cv', 'N/A')})")

    # ── AI 컨텍스트 (Tier 2 브릿지) ──
    # 컨센서스 vs 시계열 괴리
    con_ts_gap: float | None = None
    if con_growth_rates and ts_growth_rates:
        avg_con = sum(con_growth_rates) / len(con_growth_rates)
        avg_ts = sum(ts_growth_rates) / len(ts_growth_rates)
        con_ts_gap = avg_con - avg_ts

    avg_growth = sum(growth_rates) / len(growth_rates) if growth_rates else 0.0
    ai_context: dict = {
        "base_growth": round(avg_growth, 2),
        "lifecycle": lifecycle,
        "lifecycle_detail": lifecycle_detail,
        "market": market,
        "sources_used": list(final_weights.keys()),
        "ts_method": ts_result.method,
        "ts_r_squared": ts_result.r_squared,
        "roic_growth": round(roic_growth_rate, 2) if roic_growth_rate is not None else None,
        "roic_detail": roic_detail if roic_detail else None,
        "roic_ts_gap": round(roic_ts_gap, 2) if roic_ts_gap is not None else None,
        "consensus_vs_ts_gap": round(con_ts_gap, 2) if con_ts_gap is not None else None,
        "sector_key": sector_key,
        "key_assumptions": assumptions.copy(),
        "uncertainty_flags": [],
    }

    # 불확실성 플래그
    if lifecycle == "transition":
        ai_context["uncertainty_flags"].append("전환기 기업 — 과거 추세 신뢰도 낮음")
    if roic_ts_gap is not None and abs(roic_ts_gap) > 10:
        ai_context["uncertainty_flags"].append(f"ROIC-시계열 괴리 {roic_ts_gap:+.1f}%p")
    if con_ts_gap is not None and abs(con_ts_gap) > 15:
        ai_context["uncertainty_flags"].append(f"컨센서스-시계열 괴리 {con_ts_gap:+.1f}%p")
    if not consensus_proj:
        ai_context["uncertainty_flags"].append("컨센서스 데이터 없음")

    # ── v3: 3-시나리오 ──
    scenarios, scenario_grs, scenario_probs = _build_scenarios(
        projected, [round(g, 1) for g in growth_rates],
        historical, lifecycle, last_revenue,
    )

    # v3: 세그먼트/수주잔고 AI 컨텍스트
    if segment_forecasts:
        ai_context["segment_count"] = len(segment_forecasts)
        ai_context["segments_top3"] = [
            {"name": sf.name, "share": sf.share_of_revenue, "growth": sf.growth_rates[0] if sf.growth_rates else 0}
            for sf in segment_forecasts[:3]
        ]
    if backlog_signal:
        ai_context["backlog"] = {
            "br_ratio": backlog_signal.backlog_revenue_ratio,
            "trend": backlog_signal.br_ratio_trend,
            "implied_growth": backlog_signal.implied_revenue_growth,
            "applicable": backlog_signal.sectors_applicable,
        }

    # Forward test 키 생성 (저장은 opt-in)
    ft_key = None
    if stock_code:
        from dartlab.engines.common.finance.forward_test import generate_key
        ft_key = generate_key(stock_code, horizon)

    return RevenueForecastResult(
        historical=historical,
        projected=projected,
        horizon=horizon,
        method=method,
        confidence=confidence,
        growth_rates=[round(g, 1) for g in growth_rates],
        sources=list(final_weights.keys()),
        source_weights=final_weights,
        consensus_revenue=consensus_revenue,
        assumptions=assumptions,
        warnings=warnings + ts_result.warnings,
        ai_context=ai_context,
        scenarios=scenarios,
        scenario_growth_rates=scenario_grs,
        scenario_probabilities=scenario_probs,
        segment_forecasts=segment_forecasts,
        backlog_signal=backlog_signal,
        forward_test_key=ft_key,
    )


# ══════════════════════════════════════
# AI 오버레이 적용
# ══════════════════════════════════════


_MAX_ANNUAL_ADJ = 10.0  # 연간 보정 ±%p 캡
_MAX_TOTAL_ADJ = 20.0  # 총 보정 ±%p 캡


def apply_ai_overlay(
    result: RevenueForecastResult,
    overlay: RevenueForecastAIOverlay,
) -> RevenueForecastResult:
    """AI 보정을 예측 결과에 적용.

    가드레일:
    - 연간 보정 ±10%p 캡
    - 총 보정 ±20%p 캡
    - reasoning 없으면 거부 (원본 반환)
    """
    if not overlay.reasoning:
        log.warning("AI overlay rejected: reasoning 비어있음")
        return result

    adj = overlay.growth_adjustment
    if not adj or len(adj) < result.horizon:
        adj = (adj or []) + [0.0] * result.horizon
        adj = adj[: result.horizon]

    # 가드레일: 연간 캡
    adj = [max(min(a, _MAX_ANNUAL_ADJ), -_MAX_ANNUAL_ADJ) for a in adj]

    # 가드레일: 총 캡
    total = sum(abs(a) for a in adj)
    if total > _MAX_TOTAL_ADJ:
        scale = _MAX_TOTAL_ADJ / total
        adj = [a * scale for a in adj]

    # 보정 적용
    new_projected: list[float] = []
    prev = result.projected[0] / (1 + result.growth_rates[0] / 100) if result.projected and result.growth_rates and result.growth_rates[0] != -100 else 0

    for i, (proj, gr) in enumerate(zip(result.projected, result.growth_rates)):
        new_gr = gr + adj[i]
        if prev > 0:
            new_val = prev * (1 + new_gr / 100)
        else:
            new_val = proj * (1 + adj[i] / 100)
        new_projected.append(new_val)
        prev = new_val

    new_growth_rates = []
    for i, p in enumerate(new_projected):
        if i == 0:
            base = result.projected[0] / (1 + result.growth_rates[0] / 100) if result.projected and result.growth_rates and result.growth_rates[0] != -100 else 0
            if base > 0:
                new_growth_rates.append(round((p / base - 1) * 100, 1))
            else:
                new_growth_rates.append(0.0)
        elif new_projected[i - 1] > 0:
            new_growth_rates.append(round((p / new_projected[i - 1] - 1) * 100, 1))
        else:
            new_growth_rates.append(0.0)

    # 시나리오 확률 이동
    new_probs = dict(result.scenario_probabilities)
    if overlay.scenario_shift and new_probs:
        for k, shift in overlay.scenario_shift.items():
            if k in new_probs:
                new_probs[k] = max(5, min(70, new_probs[k] + shift))
        # 정규화
        p_sum = sum(new_probs.values())
        if p_sum > 0:
            new_probs = {k: round(v / p_sum * 100, 1) for k, v in new_probs.items()}

    applied_overlay = RevenueForecastAIOverlay(
        growth_adjustment=adj,
        direction=overlay.direction,
        magnitude=overlay.magnitude,
        scenario_shift=overlay.scenario_shift,
        reasoning=overlay.reasoning,
        applied=True,
    )

    return RevenueForecastResult(
        historical=result.historical,
        projected=new_projected,
        horizon=result.horizon,
        method=result.method,
        confidence=overlay.confidence_override if hasattr(overlay, "confidence_override") and overlay.confidence_override else result.confidence,  # type: ignore[attr-defined]
        growth_rates=new_growth_rates,
        sources=result.sources,
        source_weights=result.source_weights,
        consensus_revenue=result.consensus_revenue,
        assumptions=result.assumptions + [f"AI 보정: {overlay.direction} ({overlay.magnitude})"],
        warnings=result.warnings,
        ai_context=result.ai_context,
        scenarios=result.scenarios,
        scenario_growth_rates=result.scenario_growth_rates,
        scenario_probabilities=new_probs,
        segment_forecasts=result.segment_forecasts,
        backlog_signal=result.backlog_signal,
        ai_overlay=applied_overlay,
        forward_test_key=result.forward_test_key,
    )
