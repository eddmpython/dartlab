"""3-Statement Pro-Forma 재무제표 엔진.

과거 재무제표에서 구조적 비율을 추출하고,
매출 성장 경로에 따라 IS → BS → CF 연결 모델을 생성한다.

외부 의존성 제로 (math 모듈만 사용).
"""

from __future__ import annotations

import functools
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from dartlab.core.utils.extract import (
    getLatest,
    getTTM,
)

if TYPE_CHECKING:
    from dartlab.synth.scenario import SectorElasticity

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
    # v4: 영업레버리지 (고정+변동비 분해, 06 D5). 원가·판관비를 매출에 회귀:
    # cost = fixed(원) + var_ratio*revenue. reliable=False 면 순변동비(현행)로 폴백.
    cogs_fixed: float = 0.0
    cogs_var_ratio: float = 0.0
    sga_fixed: float = 0.0
    sga_var_ratio: float = 0.0
    oplev_reliable: bool = False

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
    scenarioName: str
    revenueGrowthPath: list[float]
    wacc: float
    wacc_details: dict[str, float] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    DISCLAIMER: str = "본 분석은 투자 참고용이며 투자 권유가 아닙니다."

    def __repr__(self) -> str:
        lines = [f"[Pro-Forma 재무제표 — {self.scenarioName}]"]
        lines.append(f"  WACC: {self.wacc:.1f}%")
        lines.append(f"  성장률: {' → '.join(f'{g:+.1f}%' for g in self.revenueGrowthPath)}")
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
        lines.append("  === 재무상태표 (BS) ===")
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


def _removeOutliersIqr(values: list[float]) -> list[float]:
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


def _weightedRatio(values: list[float]) -> tuple[float, float]:
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
    cleaned = _removeOutliersIqr(values)
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


def _annualTtmValues(series: dict, sj: str, key: str, n: int) -> list[float]:
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


def _annualLatestValues(series: dict, sj: str, key: str, n: int) -> list[float]:
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


def _safeRatioList(numVals: list[float], denVals: list[float], *, pct: bool = True) -> list[float]:
    """두 값 리스트의 비율 리스트 (% 변환 옵션)."""
    ratios = []
    for n, d in zip(numVals, denVals):
        if d and abs(d) > 1e-12:
            r = n / d
            if pct:
                r *= 100
            ratios.append(r)
    return ratios


# ══════════════════════════════════════
# 과거 비율 추출
# ══════════════════════════════════════


def _ehrCollectSeries(series: dict, n: int) -> dict[str, list]:
    """IS/CF/BS 10+ 계정 시계열 일괄 수집. 반환: {key: list[float]}."""

    def ttm(sj: str, acc: str) -> list:
        """주제 sj·계정 acc 의 TTM 시계열 n 개.

        Requires:
            상위 series dict 와 n 이 클로저로 캡쳐.

        Raises:
            없음.

        Example:
            >>> ttm("IS", "sales")
            [..., ...]
        """
        return _annualTtmValues(series, sj, acc, n)

    def bs(acc: str) -> list:
        """BS 계정 acc 의 연말 잔액 시계열 n 개.

        Requires:
            series dict 안에 BS 슬롯 존재.

        Raises:
            없음.

        Example:
            >>> bs("current_assets")
            [..., ...]
        """
        return _annualLatestValues(series, "BS", acc, n)

    return {
        "rev": ttm("IS", "sales"),
        "gp": ttm("IS", "gross_profit"),
        "sga": ttm("IS", "selling_and_administrative_expenses"),
        "pbt": ttm("IS", "profit_before_tax"),
        "tax": ttm("IS", "income_tax_expense"),
        "fc": ttm("IS", "finance_costs") or ttm("IS", "interest_expense"),
        "ni": ttm("IS", "net_profit") or ttm("IS", "net_income"),
        "op": ttm("IS", "operating_profit") or ttm("IS", "operating_income"),
        "dep": (
            ttm("CF", "depreciation_and_amortization")
            or ttm("CF", "depreciation_cf")
            or ttm("IS", "depreciation_and_amortization")
            or ttm("IS", "depreciation")
        ),
        "capex": ttm("CF", "purchase_of_property_plant_and_equipment"),
        "div": ttm("CF", "dividends_paid"),
        "ca": bs("current_assets"),
        "cl": bs("current_liabilities"),
        "cash": bs("cash_and_cash_equivalents"),
        "stb": bs("shortterm_borrowings"),
        "ltb": bs("longterm_borrowings"),
        "bond": bs("debentures"),
        "ar": bs("trade_receivables") or bs("trade_and_other_receivables"),
        "inv": bs("inventories"),
        "ap": bs("trade_payables") or bs("trade_and_other_payables"),
    }


def _ehrDepInSga(s: dict) -> bool:
    """K-IFRS IS 구조 감지 — D&A 가 SGA 에 포함되었는지 (최근 3년 gap<2%p)."""
    gp, sga, op, rev = s["gp"], s["sga"], s["op"], s["rev"]
    if not (gp and sga and op):
        return False
    check_n = min(3, len(gp), len(sga), len(op), len(rev))
    if check_n < 1:
        return False
    matches = 0
    for j in range(check_n):
        idx = -(j + 1)
        if rev[idx] and rev[idx] > 0:
            gap_pct = abs((gp[idx] - sga[idx] - op[idx]) / rev[idx]) * 100
            if gap_pct < 2.0:
                matches += 1
    return matches >= max(1, check_n - 1)


def _ehrInterestRate(s: dict) -> float:
    """FC / 총차입금 가중 비율. 기본 4%."""
    debt_totals: list[float] = []
    for i in range(min(len(s["stb"]), len(s["ltb"]))):
        d = (
            (s["stb"][i] if i < len(s["stb"]) else 0)
            + (s["ltb"][i] if i < len(s["ltb"]) else 0)
            + (s["bond"][i] if i < len(s["bond"]) else 0)
        )
        debt_totals.append(d)
    int_ratios: list[float] = []
    for fc_v, d_v in zip(s["fc"], debt_totals):
        if d_v and d_v > 0 and fc_v:
            r = abs(fc_v) / d_v * 100
            if 0 < r < 30:
                int_ratios.append(r)
    return _weightedRatio(int_ratios)[0] if int_ratios else 4.0


def _ehrNwcRatio(s: dict, trends: dict) -> float:
    """순운전자본 / 매출 가중 비율. 기본 10%."""
    nwc_ratios: list[float] = []
    for i in range(min(len(s["ca"]), len(s["cl"]), len(s["cash"]), len(s["rev"]))):
        nwc = s["ca"][i] - s["cl"][i] - s["cash"][i]
        if s["rev"][i] and abs(s["rev"][i]) > 0:
            nwc_ratios.append(nwc / s["rev"][i] * 100)
    if nwc_ratios:
        ratio, trends["nwc_to_revenue"] = _weightedRatio(nwc_ratios)
        return ratio
    return 10.0


def _ehrPayoutRatio(s: dict) -> float:
    """배당성향 가중 비율 (0 < p < 200). 기본 0%."""
    payout_ratios: list[float] = []
    for dv, ni in zip(s["div"], s["ni"]):
        if ni and ni > 0 and dv:
            p = abs(dv) / ni * 100
            if 0 < p < 200:
                payout_ratios.append(p)
    return _weightedRatio(payout_ratios)[0] if payout_ratios else 0.0


def _ehrWeightedOrDefault(ratios: list[float], default: float, trends: dict, trendKey: str) -> float:
    """_weighted_ratio(ratios) 계산. 비어있으면 default. trend 는 trends[trend_key] 에 저장."""
    if not ratios:
        return default
    val, trend = _weightedRatio(ratios)
    trends[trendKey] = trend
    return val


def _ehrDepreciationRatio(s: dict, capexRatio: float, trends: dict) -> tuple[float, list[str]]:
    """감가상각/매출 비율 계산 — D&A 시계열 없으면 CAPEX×80% 추정. 반환: (비율, warnings)."""
    dep_list = _safeRatioList(s["dep"], s["rev"]) if s["dep"] else []
    warnings: list[str] = []
    if dep_list:
        ratio, trends["depreciation_ratio"] = _weightedRatio(dep_list)
        return ratio, warnings
    if capexRatio > 0:
        ratio = capexRatio * 0.8
        warnings.append(f"감가상각 데이터 없음 — CAPEX×80% 추정 ({ratio:.1f}%)")
        return ratio, warnings
    return 3.0, warnings


def _olsFixedVar(y: list[float], x: list[float]) -> tuple[float, float, float] | None:
    """비용 y 를 매출 x 에 회귀: y = fixed + varRatio*x. 반환 (fixed, varRatio, r2) 또는 None.

    영업레버리지 분해(06 D5)의 코어. 표본<4·기울기 밖([0,1])·저적합(R2<0.7)·고정비 음수는
    None 반환(호출자가 순변동비로 폴백). 순수 최소자승(numpy 불요, stdlib 만).
    """
    pairs = [(xi, yi) for xi, yi in zip(x, y) if xi is not None and yi is not None and xi > 0]
    n = len(pairs)
    if n < 4:
        return None
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((xi - mx) ** 2 for xi in xs)
    sxy = sum((xi - mx) * (yi - my) for xi, yi in zip(xs, ys))
    if sxx <= 0:
        return None
    slope = sxy / sxx
    intercept = my - slope * mx
    syy = sum((yi - my) ** 2 for yi in ys)
    r2 = (sxy * sxy / (sxx * syy)) if syy > 0 else 0.0
    # 변동비율은 (0,1], 고정비 음수 불가, 적합도 게이트
    if not (0.0 < slope <= 1.0) or intercept < 0 or r2 < 0.7:
        return None
    return intercept, slope, r2


def _ehrOperatingLeverage(s: dict) -> dict:
    """원가·판관비 고정+변동 분해 (06 D5). 둘 다 신뢰가능해야 oplev_reliable=True.

    cogs = rev - gp 를 매출에 회귀, sga 를 매출에 회귀. 하나라도 실패하면 비활성(폴백).
    """
    rev = s.get("rev") or []
    gp = s.get("gp") or []
    sga = s.get("sga") or []
    if not rev or not gp or not sga:
        return {"oplev_reliable": False}
    m = min(len(rev), len(gp), len(sga))
    cogs = [(rev[i] - gp[i]) if (rev[i] is not None and gp[i] is not None) else None for i in range(m)]
    cogsFit = _olsFixedVar(cogs, rev[:m])
    sgaFit = _olsFixedVar(sga[:m], rev[:m])
    if cogsFit is None or sgaFit is None:
        return {"oplev_reliable": False}
    return {
        "cogs_fixed": cogsFit[0],
        "cogs_var_ratio": cogsFit[1],
        "sga_fixed": sgaFit[0],
        "sga_var_ratio": sgaFit[1],
        "oplev_reliable": True,
    }


def _ehrBuildWarnings(s: dict, actualYears: int, capexRatio: float) -> list[str]:
    """기본값 사용 / 저신뢰 경고 문자열 리스트."""
    warnings: list[str] = []
    if actualYears < 2:
        warnings.append("과거 데이터 2년 미만 — 비율 신뢰도 낮음")
    if not s["gp"]:
        warnings.append("매출총이익 데이터 없음 — 기본값 30% 사용")
    if not s["sga"]:
        warnings.append("판관비 데이터 없음 — 기본값 15% 사용")
    if not s["dep"] and capexRatio <= 0:
        warnings.append("감가상각 데이터 없음 — 기본값 3% 사용")
    if not s["capex"]:
        warnings.append("CAPEX 데이터 없음 — 기본값 5% 사용")
    return warnings


def extractHistoricalRatios(
    series: dict,
    years: int = 5,
) -> HistoricalRatios:
    """과거 시계열에서 구조적 비율을 중위값으로 추출 orchestrator (Q3.1f split).

    Capabilities:
        - 11 개 구조 비율 (gm/sga/tax/dep/int/nwc/capex/div/ar/inv/ap) 추출.

    Guide:
        proforma forecast 입력으로 쓰는 안정 비율 셋트.

    When:
        forecast 빌드 직전, 과거 비율 골격이 필요할 때.

    How:
        series 시계열 → _ehrCollectSeries → 각 ehr 헬퍼 가중평균.

    Requires:
        series dict 에 IS/CF/BS 슬롯 ≥ 2 년.

    Raises:
        없음 (부재 시 default + warnings).

    Example:
        >>> extractHistoricalRatios(series, years=5).gross_margin
        35.0

    See Also:
        - buildBaselineForecast : 본 비율 소비
        - calcScenarioSensitivity : 비율 변형 민감도

    AIContext:
        AI proforma 답변에서 "최근 5 년 평균 마진" 인용에 사용.

    Parameters
    ----------
    series : dict
        {sjDiv: {accountNm: list[float]}} 형태의 시계열.
    years : int
        과거 몇 년치를 사용할지 (기본 5).

    Returns
    -------
    HistoricalRatios
        gross_margin/sga_ratio/effective_tax_rate/depreciation_ratio/
        interest_rate_on_debt/nwc_to_revenue/capex_to_revenue/dividend_payout/
        receivables_to_revenue/inventory_to_revenue/payables_to_revenue (모두 %)
        years_used : int, confidence : str, dep_in_sga : bool,
        warnings : list[str], trends : dict[str, float]
    """
    s = _ehrCollectSeries(series, years)
    trends: dict[str, float] = {}
    actualYears = len(s["rev"])

    gross_margin = _ehrWeightedOrDefault(
        _safeRatioList(s["gp"], s["rev"]) if s["gp"] else [], 30.0, trends, "gross_margin"
    )
    sga_ratio = _ehrWeightedOrDefault(_safeRatioList(s["sga"], s["rev"]) if s["sga"] else [], 15.0, trends, "sga_ratio")
    capex_list = [abs(c) / r * 100 for c, r in zip(s["capex"], s["rev"]) if r > 0] if s["capex"] else []
    capexRatio = _ehrWeightedOrDefault(capex_list, 5.0, trends, "capex_to_revenue")

    dep_ratio, warnings_extra = _ehrDepreciationRatio(s, capexRatio, trends)
    dep_in_sga = _ehrDepInSga(s)
    if dep_in_sga:
        warnings_extra.append("IS 구조 감지: D&A가 SGA에 포함 — 별도 차감 생략 (EBITDA 계산에만 사용)")

    tax_ratios_raw = _safeRatioList(s["tax"], s["pbt"]) if s["tax"] and s["pbt"] else []
    effective_tax = _ehrWeightedOrDefault([t for t in tax_ratios_raw if 0 < t < 50], 22.0, trends, "effective_tax_rate")

    interest_rate = _ehrInterestRate(s)
    nwc_ratio = _ehrNwcRatio(s, trends)

    ar_list = _safeRatioList(s["ar"], s["rev"][: len(s["ar"])]) if s["ar"] else []
    inv_list = _safeRatioList(s["inv"], s["rev"][: len(s["inv"])]) if s["inv"] else []
    ap_list = _safeRatioList(s["ap"], s["rev"][: len(s["ap"])]) if s["ap"] else []
    ar_ratio = _weightedRatio(ar_list)[0] if ar_list else 15.0
    inv_ratio = _weightedRatio(inv_list)[0] if inv_list else 10.0
    ap_ratio = _weightedRatio(ap_list)[0] if ap_list else 8.0

    payout = _ehrPayoutRatio(s)
    confidence = "high" if actualYears >= 4 else "medium" if actualYears >= 2 else "low"
    warnings = _ehrBuildWarnings(s, actualYears, capexRatio) + warnings_extra
    # v4: 영업레버리지 분해 (D&A가 SGA에 포함되면 고정비 이중반영 우려로 비활성)
    oplev = {"oplev_reliable": False} if dep_in_sga else _ehrOperatingLeverage(s)
    if oplev.get("oplev_reliable"):
        warnings.append("영업레버리지 분해 적용 (원가·판관비 고정+변동)")

    return HistoricalRatios(
        gross_margin=gross_margin,
        sga_ratio=sga_ratio,
        effective_tax_rate=effective_tax,
        depreciation_ratio=dep_ratio,
        interest_rate_on_debt=interest_rate,
        nwc_to_revenue=nwc_ratio,
        capex_to_revenue=capexRatio,
        dividend_payout=payout,
        receivables_to_revenue=ar_ratio,
        inventory_to_revenue=inv_ratio,
        payables_to_revenue=ap_ratio,
        years_used=actualYears,
        confidence=confidence,
        dep_in_sga=dep_in_sga,
        warnings=warnings,
        trends=trends,
        cogs_fixed=oplev.get("cogs_fixed", 0.0),
        cogs_var_ratio=oplev.get("cogs_var_ratio", 0.0),
        sga_fixed=oplev.get("sga_fixed", 0.0),
        sga_var_ratio=oplev.get("sga_var_ratio", 0.0),
        oplev_reliable=oplev.get("oplev_reliable", False),
    )


# ══════════════════════════════════════
# 개별 Beta (주가 수익률 회귀)
# ══════════════════════════════════════


# 회사 고유 WACC
# ══════════════════════════════════════


# ══════════════════════════════════════
# 3-Statement Pro-Forma 생성
# ══════════════════════════════════════


# 분리된 깊이 (BC re-export)
from dartlab.analysis.financial._proformaCore import (  # noqa: E402, F401
    _extractBaseYear,
    _fetchBeta,
    _resolveCountryFromCurrency,
    buildProforma,
    computeCompanyWacc,
)
