"""시계열 예측 + 시나리오 분석 + 민감도 분석 엔진.

외부 라이브러리 없이 순수 Python OLS 구현.
LLM이 아닌 엔진이 계산 (2-Tier 원칙).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from dartlab.engines.analysis.sector.types import SectorParams
from dartlab.engines.common.finance.extract import (
    getAnnualValues,
)
from dartlab.engines.common.finance.valuation import (
    DCFResult,
    dcf_valuation,
)

# ── 순수 Python OLS ──────────────────────────────────────


def _ols(x: list[float], y: list[float]) -> tuple[float, float, float]:
    """단순 선형 회귀 (OLS).

    Returns:
        (slope, intercept, r_squared)
    """
    n = len(x)
    if n < 2:
        return 0.0, 0.0, 0.0

    sum_x = sum(x)
    sum_y = sum(y)
    sum_xy = sum(xi * yi for xi, yi in zip(x, y))
    sum_x2 = sum(xi**2 for xi in x)

    denom = n * sum_x2 - sum_x**2
    if abs(denom) < 1e-12:
        return 0.0, sum_y / n, 0.0

    slope = (n * sum_xy - sum_x * sum_y) / denom
    intercept = (sum_y - slope * sum_x) / n

    # R²
    mean_y = sum_y / n
    ss_tot = sum((yi - mean_y) ** 2 for yi in y)
    ss_res = sum((yi - (slope * xi + intercept)) ** 2 for xi, yi in zip(x, y))

    r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return slope, intercept, max(0.0, r_squared)


def _detect_structural_break(
    vals: list[float],
    min_segment: int = 4,
) -> int | None:
    """Chow Test 기반 구조적 변화점 감지.

    전체 OLS SSR vs 분할 OLS SSR을 비교하여 F-statistic이
    임계치를 초과하면 구조적 break로 판정.

    Args:
        vals: 시계열 값 (None 제외된 순수 float).
        min_segment: 각 분할 구간의 최소 데이터 수.

    Returns:
        break 위치 인덱스 (없으면 None). break 이후 데이터만으로 예측 권장.
    """
    n = len(vals)
    if n < min_segment * 2:
        return None

    x_all = list(range(n))
    _, _, r2_full = _ols([float(x) for x in x_all], vals)
    # 전체 SSR
    mean_y = sum(vals) / n
    ss_tot = sum((v - mean_y) ** 2 for v in vals)
    ssr_full = ss_tot * (1 - r2_full) if ss_tot > 0 else 0

    best_break: int | None = None
    best_f = 0.0
    k = 2  # OLS 파라미터 수 (slope, intercept)

    for bp in range(min_segment, n - min_segment + 1):
        # 구간 1: [0, bp), 구간 2: [bp, n)
        x1 = [float(i) for i in range(bp)]
        y1 = vals[:bp]
        x2 = [float(i) for i in range(bp, n)]
        y2 = vals[bp:]

        _, _, r2_1 = _ols(x1, y1)
        _, _, r2_2 = _ols(x2, y2)

        ss_tot_1 = sum((v - sum(y1) / len(y1)) ** 2 for v in y1) if len(y1) > 0 else 0
        ss_tot_2 = sum((v - sum(y2) / len(y2)) ** 2 for v in y2) if len(y2) > 0 else 0

        ssr_1 = ss_tot_1 * (1 - r2_1) if ss_tot_1 > 0 else 0
        ssr_2 = ss_tot_2 * (1 - r2_2) if ss_tot_2 > 0 else 0

        ssr_split = ssr_1 + ssr_2
        denom = ssr_split / max(n - 2 * k, 1)
        if denom < 1e-12:
            continue

        f_stat = ((ssr_full - ssr_split) / k) / denom

        if f_stat > best_f:
            best_f = f_stat
            best_break = bp

    # F 임계치: k=2, df=n-2k, α=0.05 근사
    # n이 작을수록 임계치가 높아야 함 (보수적 판정)
    df = max(n - 2 * k, 1)
    # 간이 F 임계치: df>10이면 ~3.0, df<10이면 ~4.0+
    f_critical = 3.0 + max(0, 10 - df) * 0.3

    if best_f > f_critical and best_break is not None:
        return best_break
    return None


def _coefficient_of_variation(values: list[float]) -> float:
    """변동계수 (CV = stdev / |mean|)."""
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    if abs(mean) < 1e-12:
        return float("inf")
    variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    return math.sqrt(variance) / abs(mean)


# ── 결과 타입 ──────────────────────────────────────────────


@dataclass
class ForecastResult:
    """시계열 예측 결과."""

    metric: str
    metric_label: str
    historical: list[Optional[float]]
    projected: list[float]
    horizon: int
    method: str  # "linear" | "cagr_decay" | "mean_revert"
    confidence: str  # "high" | "medium" | "low"
    r_squared: float
    growth_rate: float  # 초기 추정 성장률 (%)
    assumptions: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    DISCLAIMER: str = "본 분석은 투자 참고용이며 투자 권유가 아닙니다."

    def __repr__(self) -> str:
        lines = [
            f"[{self.metric_label} 예측 — {self.method}]",
            f"  신뢰도: {self.confidence}  (R²={self.r_squared:.2f})",
            f"  성장률: {self.growth_rate:.1f}%",
        ]
        valid_hist = [v for v in self.historical if v is not None]
        if valid_hist:
            lines.append(f"  최근 실적: {valid_hist[-1] / 1e8:,.0f}억")
        if self.projected:
            for i, p in enumerate(self.projected, 1):
                lines.append(f"  +{i}년 예측: {p / 1e8:,.0f}억")
        if self.warnings:
            for w in self.warnings:
                lines.append(f"  ⚠ {w}")
        lines.append(f"  ※ {self.DISCLAIMER}")
        return "\n".join(lines)


@dataclass
class ScenarioResult:
    """시나리오 분석 결과."""

    base: dict[str, float]
    bull: dict[str, float]
    bear: dict[str, float]
    probability: dict[str, float]
    weighted_value: Optional[float]
    current_price: Optional[float]
    warnings: list[str] = field(default_factory=list)

    DISCLAIMER: str = "본 분석은 투자 참고용이며 투자 권유가 아닙니다."

    def __repr__(self) -> str:
        lines = ["[시나리오 분석]"]
        for label, scenario, prob in [
            ("Bull", self.bull, self.probability.get("bull", 25)),
            ("Base", self.base, self.probability.get("base", 50)),
            ("Bear", self.bear, self.probability.get("bear", 25)),
        ]:
            growth = scenario.get("growth", 0)
            value = scenario.get("per_share_value", 0)
            lines.append(f"  {label} ({prob:.0f}%): 성장 {growth:+.1f}%, 적정가 {value:,.0f}원")
        if self.weighted_value is not None:
            lines.append(f"  확률가중 적정가: {self.weighted_value:,.0f}원")
        if self.current_price:
            lines.append(f"  현재가: {self.current_price:,.0f}원")
        lines.append(f"  ※ {self.DISCLAIMER}")
        return "\n".join(lines)


@dataclass
class SensitivityResult:
    """민감도 분석 결과."""

    wacc_values: list[float]
    growth_values: list[float]
    matrix: list[list[float]]  # [wacc_idx][growth_idx] = per_share_value
    base_wacc: float
    base_growth: float
    base_value: float

    DISCLAIMER: str = "본 분석은 투자 참고용이며 투자 권유가 아닙니다."

    def __repr__(self) -> str:
        lines = ["[민감도 분석 — WACC × 영구성장률]"]
        header = "WACC \\ g  " + "  ".join(f"{g:.1f}%" for g in self.growth_values)
        lines.append(f"  {header}")
        for i, wacc in enumerate(self.wacc_values):
            row = f"  {wacc:.1f}%    " + "  ".join(
                f"{self.matrix[i][j] / 1e4:,.0f}만" if self.matrix[i][j] > 0 else "  N/A"
                for j in range(len(self.growth_values))
            )
            lines.append(row)
        lines.append(f"  ※ {self.DISCLAIMER}")
        return "\n".join(lines)


# ── 예측 메트릭 정의 ──────────────────────────────────────────

FORECAST_TARGETS: dict[str, tuple[str, str, str]] = {
    # key: (sj_div, snake_id, label)
    "revenue": ("IS", "sales", "매출"),
    "operating_income": ("IS", "operating_profit", "영업이익"),
    "net_income": ("IS", "net_profit", "순이익"),
    "operating_cashflow": ("CF", "operating_cashflow", "영업CF"),
}

# 대체 snake_id
_FALLBACKS: dict[str, list[str]] = {
    "sales": ["revenue"],
    "operating_profit": ["operating_income"],
    "net_profit": ["net_income"],
}


# ── 예측 엔진 ──────────────────────────────────────────────


def forecast_metric(
    series: dict,
    metric: str = "revenue",
    horizon: int = 3,
    sector_params: Optional[SectorParams] = None,
) -> ForecastResult:
    """단일 메트릭 시계열 예측.

    Args:
        series: finance timeseries dict.
        metric: 예측 대상 키 (FORECAST_TARGETS 참조).
        horizon: 예측 기간 (년, 기본 3년).
        sector_params: 섹터 파라미터.

    Returns:
        ForecastResult.
    """
    warnings: list[str] = []
    target = FORECAST_TARGETS.get(metric)
    if target is None:
        return ForecastResult(
            metric=metric,
            metric_label=metric,
            historical=[],
            projected=[],
            horizon=horizon,
            method="N/A",
            confidence="low",
            r_squared=0,
            growth_rate=0,
            warnings=[f"미지원 예측 대상: {metric}"],
        )

    sj_div, snake_id, label = target

    # 데이터 추출 (fallback 포함)
    vals = getAnnualValues(series, sj_div, snake_id)
    if not any(v is not None for v in vals):
        for fb in _FALLBACKS.get(snake_id, []):
            vals = getAnnualValues(series, sj_div, fb)
            if any(v is not None for v in vals):
                break

    valid_pairs = [(i, v) for i, v in enumerate(vals) if v is not None]
    if len(valid_pairs) < 3:
        return ForecastResult(
            metric=metric,
            metric_label=label,
            historical=vals,
            projected=[],
            horizon=horizon,
            method="N/A",
            confidence="low",
            r_squared=0,
            growth_rate=0,
            warnings=["예측 불가: 유효 데이터 3년 미만"],
        )

    x_vals = [float(p[0]) for p in valid_pairs]
    y_vals = [p[1] for p in valid_pairs]

    # 구조적 변화점 감지 — break 이후 데이터만 사용
    break_idx = _detect_structural_break(y_vals, min_segment=4)
    if break_idx is not None and break_idx < len(y_vals):
        n_before = break_idx
        n_after = len(y_vals) - break_idx
        if n_after >= 3:
            # break 이후 데이터로 교체
            warnings.append(f"구조적 전환 감지 (데이터 {n_before}→{n_after}개 분할) — 전환 이후 데이터 기반 예측")
            x_vals = x_vals[break_idx:]
            y_vals = y_vals[break_idx:]

    # 방법 자동 선택
    cv = _coefficient_of_variation(y_vals)
    slope, intercept, r2 = _ols(x_vals, y_vals)

    # 성장률 계산
    n = len(y_vals)
    if y_vals[0] > 0 and y_vals[-1] > 0:
        cagr = ((y_vals[-1] / y_vals[0]) ** (1 / max(n - 1, 1)) - 1) * 100
    else:
        cagr = 0.0

    sector_growth = sector_params.growthRate if sector_params else 3.0

    if cv > 0.4:
        # 변동성 높음 → 평균 회귀
        method = "mean_revert"
        mean_val = sum(y_vals) / n
        projected = []
        last = y_vals[-1]
        for yr in range(1, horizon + 1):
            blend = yr / (horizon + 1)
            proj = last * (1 - blend) + mean_val * blend
            projected.append(proj)
        growth_rate = 0.0
        warnings.append("높은 변동성 → 평균 회귀 모델 적용")
    elif r2 > 0.7 and abs(cagr) < 30:
        # 안정적 추세 → 선형 회귀
        method = "linear"
        last_x = x_vals[-1]
        projected = [slope * (last_x + yr) + intercept for yr in range(1, horizon + 1)]
        growth_rate = cagr
        # 음수 예측 방지
        for i, p in enumerate(projected):
            if p < 0 and y_vals[-1] > 0:
                projected[i] = y_vals[-1] * 0.5
                warnings.append(f"+{i + 1}년 예측이 음수 → 최근값의 50%로 대체")
    else:
        # CAGR 감속 모델
        method = "cagr_decay"
        growth = min(max(cagr, -10), 25)
        terminal = sector_growth
        projected = []
        last = y_vals[-1]
        for yr in range(1, horizon + 1):
            blend = (yr - 1) / max(horizon - 1, 1)
            g = growth * (1 - blend) + terminal * blend
            proj = last * (1 + g / 100)
            projected.append(proj)
            last = proj
        growth_rate = growth

    # 신뢰도 판정
    if r2 > 0.8 and n >= 5:
        confidence = "high"
    elif r2 > 0.5 and n >= 3:
        confidence = "medium"
    else:
        confidence = "low"

    assumptions = []
    if method == "linear":
        assumptions.append(f"선형 추세 연장 (R²={r2:.2f})")
    elif method == "cagr_decay":
        assumptions.append(f"CAGR {cagr:.1f}% → 섹터평균 {sector_growth:.1f}%로 감속")
    elif method == "mean_revert":
        mean_val = sum(y_vals) / n
        assumptions.append(f"평균 {mean_val / 1e8:,.0f}억으로 회귀")
    assumptions.append(f"과거 {n}개년 데이터 기반")

    return ForecastResult(
        metric=metric,
        metric_label=label,
        historical=vals,
        projected=projected,
        horizon=horizon,
        method=method,
        confidence=confidence,
        r_squared=round(r2, 3),
        growth_rate=round(growth_rate, 1),
        assumptions=assumptions,
        warnings=warnings,
    )


def forecast_all(
    series: dict,
    horizon: int = 3,
    sector_params: Optional[SectorParams] = None,
) -> dict[str, ForecastResult]:
    """모든 주요 메트릭 예측."""
    return {
        key: forecast_metric(series, metric=key, horizon=horizon, sector_params=sector_params)
        for key in FORECAST_TARGETS
    }


# ── 시나리오 분석 ──────────────────────────────────────────


def scenario_analysis(
    series: dict,
    shares: Optional[int] = None,
    sector_params: Optional[SectorParams] = None,
    current_price: Optional[float] = None,
) -> ScenarioResult:
    """3-Scenario DCF 분석.

    Base/Bull/Bear 시나리오별 DCF를 수행하고 확률 가중 가치를 산출.

    Args:
        series: finance timeseries dict.
        shares: 발행주식수.
        sector_params: 섹터 파라미터.
        current_price: 현재 주가.

    Returns:
        ScenarioResult.
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

    # Base case: 기본 파라미터
    base_dcf = dcf_valuation(
        series,
        shares=shares,
        sector_params=sp,
        current_price=current_price,
    )

    # Bull case: 성장률 +50%, 할인율 -1%p
    bull_dcf = dcf_valuation(
        series,
        shares=shares,
        sector_params=sp,
        current_price=current_price,
        discount_rate=max(sp.discountRate - 1.0, 5.0),
        terminal_growth=min(sp.growthRate, 3.0) + 0.5,
    )

    # Bear case: 성장률 -50%, 할인율 +1%p
    bear_dcf = dcf_valuation(
        series,
        shares=shares,
        sector_params=sp,
        current_price=current_price,
        discount_rate=sp.discountRate + 1.0,
        terminal_growth=max(min(sp.growthRate, 3.0) - 0.5, 0.5),
    )

    def _scenario_dict(dcf: DCFResult, growth_adj: str) -> dict[str, float]:
        return {
            "growth": dcf.growth_rate_initial,
            "discount_rate": dcf.discount_rate,
            "terminal_growth": dcf.terminal_growth,
            "enterprise_value": dcf.enterprise_value,
            "equity_value": dcf.equity_value,
            "per_share_value": dcf.per_share_value or 0,
        }

    base = _scenario_dict(base_dcf, "base")
    bull = _scenario_dict(bull_dcf, "bull")
    bear = _scenario_dict(bear_dcf, "bear")

    prob = {"base": 50, "bull": 25, "bear": 25}

    # 확률 가중 가치
    weighted = None
    base_v = base.get("per_share_value", 0)
    bull_v = bull.get("per_share_value", 0)
    bear_v = bear.get("per_share_value", 0)
    if base_v > 0 or bull_v > 0 or bear_v > 0:
        weighted = round(
            base_v * prob["base"] / 100 + bull_v * prob["bull"] / 100 + bear_v * prob["bear"] / 100,
            0,
        )

    if not base_dcf.fcf_projections:
        warnings.append("FCF 데이터 부족 → 시나리오 분석 신뢰도 낮음")

    return ScenarioResult(
        base=base,
        bull=bull,
        bear=bear,
        probability=prob,
        weighted_value=weighted,
        current_price=current_price,
        warnings=warnings,
    )


# ── 민감도 분석 ──────────────────────────────────────────


def sensitivity_analysis(
    series: dict,
    shares: Optional[int] = None,
    sector_params: Optional[SectorParams] = None,
    wacc_steps: int = 5,
    wacc_range: float = 2.0,
    growth_steps: int = 5,
    growth_range: float = 1.0,
) -> SensitivityResult:
    """WACC × Terminal Growth 민감도 테이블.

    Args:
        series: finance timeseries dict.
        shares: 발행주식수.
        sector_params: 섹터 파라미터.
        wacc_steps: WACC 단계 수 (기본 5).
        wacc_range: WACC ± 범위 (%, 기본 2).
        growth_steps: 영구성장률 단계 수 (기본 5).
        growth_range: 영구성장률 ± 범위 (%, 기본 1).

    Returns:
        SensitivityResult.
    """
    sp = sector_params or SectorParams(
        discountRate=10.0,
        growthRate=3.0,
        perMultiple=15,
        pbrMultiple=1.2,
        evEbitdaMultiple=8,
        label="기타",
    )

    base_wacc = sp.discountRate
    base_growth = min(sp.growthRate, 3.0)

    # WACC 범위
    wacc_lo = max(base_wacc - wacc_range, 4.0)
    wacc_hi = base_wacc + wacc_range
    wacc_step = (wacc_hi - wacc_lo) / max(wacc_steps - 1, 1)
    wacc_values = [round(wacc_lo + i * wacc_step, 1) for i in range(wacc_steps)]

    # Growth 범위
    growth_lo = max(base_growth - growth_range, 0.5)
    growth_hi = base_growth + growth_range
    growth_step = (growth_hi - growth_lo) / max(growth_steps - 1, 1)
    growth_values = [round(growth_lo + i * growth_step, 1) for i in range(growth_steps)]

    # 매트릭스 계산
    matrix: list[list[float]] = []
    base_value = 0.0

    for wacc in wacc_values:
        row: list[float] = []
        for tg in growth_values:
            if wacc <= tg:
                row.append(0)  # invalid
                continue
            dcf = dcf_valuation(
                series,
                shares=shares,
                sector_params=sp,
                discount_rate=wacc,
                terminal_growth=tg,
            )
            val = dcf.per_share_value or 0
            row.append(val)
            if abs(wacc - base_wacc) < 0.05 and abs(tg - base_growth) < 0.05:
                base_value = val
        matrix.append(row)

    return SensitivityResult(
        wacc_values=wacc_values,
        growth_values=growth_values,
        matrix=matrix,
        base_wacc=base_wacc,
        base_growth=base_growth,
        base_value=base_value,
    )
