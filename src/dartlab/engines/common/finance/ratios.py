"""재무비율 계산.

시계열 dict에서 핵심 비율을 계산한다.

두 가지 모드:
1. calcRatios(series) → RatioResult (최신 단일 시점, 하위호환)
2. calcRatioSeries(annualSeries, years) → RatioSeriesResult (연도별 시계열)

비율 분류 (6개 카테고리, 30+ 비율):
- 수익성: ROE, ROA, 영업이익률, 순이익률, 매출총이익률, EBITDA마진, 매출원가율, 판관비율
- 안정성: 부채비율, 유동비율, 당좌비율, 자기자본비율, 이자보상배율, 순차입금비율, 비유동비율
- 성장성: 매출성장률, 영업이익성장률, 순이익성장률, 자산성장률, 자본성장률
- 효율성: 총자산회전율, 재고자산회전율, 매출채권회전율, 매입채무회전율
- 현금흐름: FCF, 영업CF마진, 영업CF/순이익, CAPEX비율, 배당성향
- 주당지표: EPS, BPS (시가총액 필요: PER, PBR, PSR, EV/EBITDA)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar, Optional

from dartlab.engines.common.finance.extract import getLatest, getRevenueGrowth3Y, getTTM


@dataclass
class RatioResult:
    """비율 계산 결과 (최신 단일 시점)."""

    revenueTTM: Optional[float] = None
    operatingIncomeTTM: Optional[float] = None
    netIncomeTTM: Optional[float] = None
    operatingCashflowTTM: Optional[float] = None
    investingCashflowTTM: Optional[float] = None

    totalAssets: Optional[float] = None
    totalEquity: Optional[float] = None
    ownersEquity: Optional[float] = None
    totalLiabilities: Optional[float] = None
    currentAssets: Optional[float] = None
    currentLiabilities: Optional[float] = None
    cash: Optional[float] = None
    shortTermBorrowings: Optional[float] = None
    longTermBorrowings: Optional[float] = None
    bonds: Optional[float] = None

    grossProfit: Optional[float] = None
    costOfSales: Optional[float] = None
    sga: Optional[float] = None
    inventories: Optional[float] = None
    receivables: Optional[float] = None
    payables: Optional[float] = None
    tangibleAssets: Optional[float] = None
    intangibleAssets: Optional[float] = None
    retainedEarnings: Optional[float] = None
    financeIncome: Optional[float] = None
    financeCosts: Optional[float] = None
    capex: Optional[float] = None
    dividendsPaid: Optional[float] = None
    depreciationExpense: Optional[float] = None
    noncurrentAssets: Optional[float] = None
    noncurrentLiabilities: Optional[float] = None

    roe: Optional[float] = None
    roa: Optional[float] = None
    operatingMargin: Optional[float] = None
    netMargin: Optional[float] = None
    grossMargin: Optional[float] = None
    ebitdaMargin: Optional[float] = None
    costOfSalesRatio: Optional[float] = None
    sgaRatio: Optional[float] = None

    debtRatio: Optional[float] = None
    currentRatio: Optional[float] = None
    quickRatio: Optional[float] = None
    equityRatio: Optional[float] = None
    interestCoverage: Optional[float] = None
    netDebt: Optional[float] = None
    netDebtRatio: Optional[float] = None
    noncurrentRatio: Optional[float] = None

    revenueGrowth: Optional[float] = None
    operatingProfitGrowth: Optional[float] = None
    netProfitGrowth: Optional[float] = None
    assetGrowth: Optional[float] = None
    equityGrowthRate: Optional[float] = None
    revenueGrowth3Y: Optional[float] = None

    totalAssetTurnover: Optional[float] = None
    inventoryTurnover: Optional[float] = None
    receivablesTurnover: Optional[float] = None
    payablesTurnover: Optional[float] = None

    fcf: Optional[float] = None
    operatingCfMargin: Optional[float] = None
    operatingCfToNetIncome: Optional[float] = None
    capexRatio: Optional[float] = None
    dividendPayoutRatio: Optional[float] = None

    # 복합 지표
    roic: Optional[float] = None
    dupontMargin: Optional[float] = None
    dupontTurnover: Optional[float] = None
    dupontLeverage: Optional[float] = None
    debtToEbitda: Optional[float] = None
    ccc: Optional[float] = None
    dso: Optional[float] = None
    dio: Optional[float] = None
    dpo: Optional[float] = None
    piotroskiFScore: Optional[int] = None
    piotroskiMaxScore: int = 7  # 현재 구현 가능 항목 기준 (9점 중 2항목 데이터 미접근)
    altmanZScore: Optional[float] = None

    per: Optional[float] = None
    pbr: Optional[float] = None
    psr: Optional[float] = None
    evEbitda: Optional[float] = None
    marketCap: Optional[float] = None
    ebitdaEstimated: bool = True

    warnings: list[str] = field(default_factory=list)

    # ── 카테고리별 필드 그룹 (표시용) ──────────────────────────
    _DISPLAY_GROUPS: ClassVar[list[tuple[str, list[str]]]] = [
        (
            "수익성",
            [
                "roe",
                "roa",
                "operatingMargin",
                "netMargin",
                "grossMargin",
                "ebitdaMargin",
                "costOfSalesRatio",
                "sgaRatio",
            ],
        ),
        (
            "안정성",
            [
                "debtRatio",
                "currentRatio",
                "quickRatio",
                "equityRatio",
                "interestCoverage",
                "netDebtRatio",
                "noncurrentRatio",
            ],
        ),
        (
            "성장성",
            [
                "revenueGrowth",
                "operatingProfitGrowth",
                "netProfitGrowth",
                "assetGrowth",
                "equityGrowthRate",
                "revenueGrowth3Y",
            ],
        ),
        (
            "효율성",
            [
                "totalAssetTurnover",
                "inventoryTurnover",
                "receivablesTurnover",
                "payablesTurnover",
            ],
        ),
        (
            "현금흐름",
            [
                "fcf",
                "operatingCfMargin",
                "operatingCfToNetIncome",
                "capexRatio",
                "dividendPayoutRatio",
            ],
        ),
        ("밸류에이션", ["per", "pbr", "psr", "evEbitda", "marketCap"]),
        (
            "복합지표",
            [
                "roic",
                "dupontMargin",
                "dupontTurnover",
                "dupontLeverage",
                "debtToEbitda",
                "ccc",
                "dso",
                "dio",
                "dpo",
                "piotroskiFScore",
                "altmanZScore",
            ],
        ),
    ]

    _LABELS: ClassVar[dict[str, str]] = {
        "roe": "ROE (%)",
        "roa": "ROA (%)",
        "operatingMargin": "영업이익률 (%)",
        "netMargin": "순이익률 (%)",
        "grossMargin": "매출총이익률 (%)",
        "ebitdaMargin": "EBITDA 마진 (%)",
        "costOfSalesRatio": "매출원가율 (%)",
        "sgaRatio": "판관비율 (%)",
        "debtRatio": "부채비율 (%)",
        "currentRatio": "유동비율 (%)",
        "quickRatio": "당좌비율 (%)",
        "equityRatio": "자기자본비율 (%)",
        "interestCoverage": "이자보상배율 (x)",
        "netDebtRatio": "순차입금비율 (%)",
        "noncurrentRatio": "비유동비율 (%)",
        "revenueGrowth": "매출성장률 (%)",
        "operatingProfitGrowth": "영업이익성장률 (%)",
        "netProfitGrowth": "순이익성장률 (%)",
        "assetGrowth": "자산성장률 (%)",
        "equityGrowthRate": "자본성장률 (%)",
        "revenueGrowth3Y": "매출 3Y CAGR (%)",
        "totalAssetTurnover": "총자산회전율 (x)",
        "inventoryTurnover": "재고자산회전율 (x)",
        "receivablesTurnover": "매출채권회전율 (x)",
        "payablesTurnover": "매입채무회전율 (x)",
        "fcf": "FCF",
        "operatingCfMargin": "영업CF마진 (%)",
        "operatingCfToNetIncome": "영업CF/순이익 (%)",
        "capexRatio": "CAPEX비율 (%)",
        "dividendPayoutRatio": "배당성향 (%)",
        "per": "PER (x)",
        "pbr": "PBR (x)",
        "psr": "PSR (x)",
        "evEbitda": "EV/EBITDA (x)",
        "marketCap": "시가총액",
        "roic": "ROIC (%)",
        "dupontMargin": "DuPont 순이익률 (%)",
        "dupontTurnover": "DuPont 자산회전율 (x)",
        "dupontLeverage": "DuPont 레버리지 (x)",
        "debtToEbitda": "Debt/EBITDA (x)",
        "ccc": "현금전환주기 (일)",
        "dso": "매출채권회수기간 (일)",
        "dio": "재고자산보유기간 (일)",
        "dpo": "매입채무지급기간 (일)",
        "piotroskiFScore": "Piotroski F-Score (0~7, 현재 구현 기준)",
        "piotroskiMaxScore": "Piotroski 현재 최대 점수 (구현 항목 기준)",
        "altmanZScore": "Altman Z-Score",
    }

    def __repr__(self) -> str:
        lines: list[str] = []
        for group, fields in self._DISPLAY_GROUPS:
            rows = []
            for f in fields:
                v = getattr(self, f, None)
                if v is None:
                    continue
                label = self._LABELS.get(f, f)
                if isinstance(v, float) and abs(v) >= 1e8:
                    formatted = f"{v / 1e8:>14,.0f}억"
                elif isinstance(v, float):
                    formatted = f"{v:>14,.2f}"
                else:
                    formatted = f"{v!s:>14}"
                rows.append(f"  {label:<24s}{formatted}")
            if rows:
                lines.append(f"[{group}]")
                lines.extend(rows)
                lines.append("")
        if self.warnings:
            lines.append(f"⚠ {', '.join(self.warnings)}")
        return "\n".join(lines) if lines else "RatioResult(empty)"

    def _repr_html_(self) -> str:
        """Jupyter/marimo용 HTML 테이블."""
        rows: list[str] = []
        for group, fields in self._DISPLAY_GROUPS:
            has_data = False
            group_rows: list[str] = []
            for f in fields:
                v = getattr(self, f, None)
                if v is None:
                    continue
                has_data = True
                label = self._LABELS.get(f, f)
                if isinstance(v, float) and abs(v) >= 1e8:
                    formatted = f"{v / 1e8:,.0f}억"
                elif isinstance(v, float):
                    formatted = f"{v:,.2f}"
                else:
                    formatted = str(v)
                group_rows.append(
                    f"<tr><td style='padding:2px 8px'>{label}</td>"
                    f"<td style='padding:2px 8px;text-align:right'>{formatted}</td></tr>"
                )
            if has_data:
                rows.append(
                    f"<tr><td colspan='2' style='padding:6px 8px 2px;"
                    f"font-weight:bold;border-bottom:1px solid #ccc'>{group}</td></tr>"
                )
                rows.extend(group_rows)
        if self.warnings:
            rows.append(
                f"<tr><td colspan='2' style='padding:4px 8px;color:#c00'>⚠ {', '.join(self.warnings)}</td></tr>"
            )
        return "<table style='font-size:13px;border-collapse:collapse'>" + "".join(rows) + "</table>"


@dataclass
class RatioSeriesResult:
    """연도별 비율 시계열."""

    years: list[str] = field(default_factory=list)

    roe: list[Optional[float]] = field(default_factory=list)
    roa: list[Optional[float]] = field(default_factory=list)
    operatingMargin: list[Optional[float]] = field(default_factory=list)
    netMargin: list[Optional[float]] = field(default_factory=list)
    grossMargin: list[Optional[float]] = field(default_factory=list)
    ebitdaMargin: list[Optional[float]] = field(default_factory=list)
    costOfSalesRatio: list[Optional[float]] = field(default_factory=list)
    sgaRatio: list[Optional[float]] = field(default_factory=list)

    debtRatio: list[Optional[float]] = field(default_factory=list)
    currentRatio: list[Optional[float]] = field(default_factory=list)
    quickRatio: list[Optional[float]] = field(default_factory=list)
    equityRatio: list[Optional[float]] = field(default_factory=list)
    interestCoverage: list[Optional[float]] = field(default_factory=list)
    netDebtRatio: list[Optional[float]] = field(default_factory=list)
    noncurrentRatio: list[Optional[float]] = field(default_factory=list)

    revenueGrowth: list[Optional[float]] = field(default_factory=list)
    operatingProfitGrowth: list[Optional[float]] = field(default_factory=list)
    netProfitGrowth: list[Optional[float]] = field(default_factory=list)
    assetGrowth: list[Optional[float]] = field(default_factory=list)
    equityGrowthRate: list[Optional[float]] = field(default_factory=list)

    totalAssetTurnover: list[Optional[float]] = field(default_factory=list)
    inventoryTurnover: list[Optional[float]] = field(default_factory=list)
    receivablesTurnover: list[Optional[float]] = field(default_factory=list)
    payablesTurnover: list[Optional[float]] = field(default_factory=list)

    fcf: list[Optional[float]] = field(default_factory=list)
    operatingCfMargin: list[Optional[float]] = field(default_factory=list)
    operatingCfToNetIncome: list[Optional[float]] = field(default_factory=list)
    capexRatio: list[Optional[float]] = field(default_factory=list)
    dividendPayoutRatio: list[Optional[float]] = field(default_factory=list)

    # 복합 지표
    roic: list[Optional[float]] = field(default_factory=list)
    dupontMargin: list[Optional[float]] = field(default_factory=list)
    dupontTurnover: list[Optional[float]] = field(default_factory=list)
    dupontLeverage: list[Optional[float]] = field(default_factory=list)
    debtToEbitda: list[Optional[float]] = field(default_factory=list)
    ccc: list[Optional[float]] = field(default_factory=list)
    dso: list[Optional[float]] = field(default_factory=list)
    dio: list[Optional[float]] = field(default_factory=list)
    dpo: list[Optional[float]] = field(default_factory=list)
    piotroskiFScore: list[Optional[int]] = field(default_factory=list)
    altmanZScore: list[Optional[float]] = field(default_factory=list)

    revenue: list[Optional[float]] = field(default_factory=list)
    operatingProfit: list[Optional[float]] = field(default_factory=list)
    netProfit: list[Optional[float]] = field(default_factory=list)
    totalAssets: list[Optional[float]] = field(default_factory=list)
    totalEquity: list[Optional[float]] = field(default_factory=list)
    operatingCashflow: list[Optional[float]] = field(default_factory=list)


def _safeDiv(a: Optional[float], b: Optional[float]) -> Optional[float]:
    if a is None or b is None or b == 0:
        return None
    return a / b


def _safePct(a: Optional[float], b: Optional[float]) -> Optional[float]:
    r = _safeDiv(a, b)
    if r is None:
        return None
    return round(r * 100, 2)


def _safeRound(v: Optional[float], n: int = 2) -> Optional[float]:
    if v is None:
        return None
    return round(v, n)


def yoy_pct(cur: Optional[float], prev: Optional[float]) -> Optional[float]:
    """전년 대비 증감률(%). 부호 전환 시 None 반환.

    - 양수→양수 또는 음수→음수: 정상 계산
    - 부호 전환(흑자↔적자): None (단순 비교 불가)
    - 분모 0 또는 None: None
    """
    if cur is None or prev is None or prev == 0:
        return None
    if prev > 0 and cur >= 0:
        return round(((cur - prev) / prev) * 100, 2)
    if prev < 0 and cur < 0:
        return round(((cur - prev) / abs(prev)) * 100, 2)
    return None


def _yoy(vals: list[Optional[float]], i: int, lag: int = 1) -> Optional[float]:
    if i < lag:
        return None
    return yoy_pct(vals[i], vals[i - lag])


def _get(series: dict, sjDiv: str, snakeId: str) -> list[Optional[float]]:
    return series.get(sjDiv, {}).get(snakeId, [])


def _detectArchetype(series: dict[str, dict[str, list[Optional[float]]]]) -> str:
    isKeys = set(series.get("IS", {}))
    bsKeys = set(series.get("BS", {}))

    if {
        "insurance_revenue",
        "assumed_reinsurance_premiums",
        "benefit_payments",
    }.intersection(isKeys):
        return "insurance"

    if "interest_income" in isKeys and {
        "loans",
        "cash_and_deposits",
        "debt_securities_at_amortized_cost",
    }.intersection(bsKeys):
        return "bank"

    if "commission_income" in isKeys and {
        "financial_assets_at_fv_through_profit",
        "financial_assets_at_fv_through_oci",
        "financial_assets_at_amortized_cost",
    }.intersection(bsKeys):
        return "securities"

    if any(token in isKeys for token in ("interest_income", "insurance_revenue", "commission_income")):
        return "financial"

    return "general"


def _setNone(result: RatioResult, *fieldNames: str) -> None:
    for fieldName in fieldNames:
        setattr(result, fieldName, None)


def _setSeriesNone(result: RatioSeriesResult, *fieldNames: str) -> None:
    empty = [None] * len(result.years)
    for fieldName in fieldNames:
        setattr(result, fieldName, list(empty))


def _applyArchetypePolicyResult(result: RatioResult, archetype: str) -> None:
    if archetype == "general":
        return

    _setNone(
        result,
        "debtRatio",
        "currentRatio",
        "quickRatio",
        "interestCoverage",
        "netDebt",
        "netDebtRatio",
        "noncurrentRatio",
        "inventoryTurnover",
        "receivablesTurnover",
        "payablesTurnover",
        "operatingCfMargin",
        "operatingCfToNetIncome",
        "capexRatio",
        "fcf",
    )

    # composite — CCC/DIO는 금융업 무의미, Altman Z-Score도 제조업 전용
    _setNone(result, "ccc", "dso", "dio", "dpo", "altmanZScore", "debtToEbitda")

    if archetype in {"bank", "financial"}:
        _setNone(
            result,
            "operatingMargin",
            "netMargin",
            "grossMargin",
            "ebitdaMargin",
            "costOfSalesRatio",
            "sgaRatio",
        )


def _applyArchetypePolicySeries(result: RatioSeriesResult, archetype: str) -> None:
    if archetype == "general":
        return

    _setSeriesNone(
        result,
        "debtRatio",
        "currentRatio",
        "quickRatio",
        "interestCoverage",
        "netDebtRatio",
        "noncurrentRatio",
        "inventoryTurnover",
        "receivablesTurnover",
        "payablesTurnover",
        "operatingCfMargin",
        "operatingCfToNetIncome",
        "capexRatio",
        "fcf",
    )

    _setSeriesNone(result, "ccc", "dso", "dio", "dpo", "altmanZScore", "debtToEbitda")

    if archetype in {"bank", "financial"}:
        _setSeriesNone(
            result,
            "operatingMargin",
            "netMargin",
            "grossMargin",
            "ebitdaMargin",
            "costOfSalesRatio",
            "sgaRatio",
        )


def _pick_first(
    series: dict[str, dict[str, list[Optional[float]]]], sjDiv: str, snakeIds: list[str], annual: bool = False
) -> Optional[float]:
    getter = getLatest if annual else getTTM
    for snakeId in snakeIds:
        val = getter(series, sjDiv, snakeId)
        if val is not None:
            return val
    return None


def _pick_series(
    series: dict[str, dict[str, list[Optional[float]]]],
    sjDiv: str,
    snakeIds: list[str],
) -> list[Optional[float]]:
    for snakeId in snakeIds:
        values = _get(series, sjDiv, snakeId)
        if any(v is not None for v in values):
            return values
    return []


def calcRatios(
    series: dict[str, dict[str, list[Optional[float]]]],
    marketCap: Optional[float] = None,
    annual: bool = False,
    archetypeOverride: str | None = None,
) -> RatioResult:
    """시계열에서 재무비율 계산 (최신 단일 시점).

    Args:
            series: buildTimeseries() 또는 buildAnnual() 결과.
            marketCap: 시가총액 (원 단위). None이면 밸류에이션 멀티플 건너뜀.
            annual: True면 IS/CF에 getLatest 사용 (연간 시계열).
                    False면 getTTM 사용 (분기 시계열, 기본값).

    Returns:
            RatioResult.
    """
    r = RatioResult()
    archetype = archetypeOverride or _detectArchetype(series)

    _flow = getLatest if annual else getTTM

    r.revenueTTM = _pick_first(series, "IS", ["sales", "revenue"], annual=annual)
    r.operatingIncomeTTM = _pick_first(series, "IS", ["operating_profit", "operating_income"], annual=annual)
    r.netIncomeTTM = _pick_first(series, "IS", ["net_profit", "net_income"], annual=annual)
    r.operatingCashflowTTM = _flow(series, "CF", "operating_cashflow")
    r.investingCashflowTTM = _flow(series, "CF", "investing_cashflow")

    r.grossProfit = _flow(series, "IS", "gross_profit")
    r.costOfSales = _flow(series, "IS", "cost_of_sales")
    r.sga = _flow(series, "IS", "selling_and_administrative_expenses")
    r.financeIncome = _flow(series, "IS", "finance_income")
    r.financeCosts = _pick_first(series, "IS", ["finance_costs", "interest_expense"], annual=annual)

    r.capex = _flow(series, "CF", "purchase_of_property_plant_and_equipment")
    r.dividendsPaid = _flow(series, "CF", "dividends_paid")
    r.depreciationExpense = _pick_first(
        series,
        "CF",
        ["depreciation_and_amortization", "depreciation_cf", "depreciation"],
        annual=annual,
    )

    r.totalAssets = getLatest(series, "BS", "total_assets")
    r.totalEquity = getLatest(series, "BS", "total_stockholders_equity") or getLatest(
        series, "BS", "owners_of_parent_equity"
    )
    r.ownersEquity = getLatest(series, "BS", "owners_of_parent_equity") or r.totalEquity
    r.totalLiabilities = getLatest(series, "BS", "total_liabilities")
    r.currentAssets = getLatest(series, "BS", "current_assets")
    r.currentLiabilities = getLatest(series, "BS", "current_liabilities")
    r.cash = getLatest(series, "BS", "cash_and_cash_equivalents")
    r.shortTermBorrowings = getLatest(series, "BS", "shortterm_borrowings") or 0
    r.longTermBorrowings = getLatest(series, "BS", "longterm_borrowings") or 0
    r.bonds = getLatest(series, "BS", "debentures") or 0
    r.inventories = getLatest(series, "BS", "inventories")
    r.receivables = getLatest(series, "BS", "trade_and_other_receivables")
    r.payables = getLatest(series, "BS", "trade_and_other_payables")
    r.tangibleAssets = getLatest(series, "BS", "tangible_assets")
    r.intangibleAssets = getLatest(series, "BS", "intangible_assets")
    r.retainedEarnings = getLatest(series, "BS", "retained_earnings")
    r.noncurrentAssets = getLatest(series, "BS", "noncurrent_assets")
    r.noncurrentLiabilities = getLatest(series, "BS", "noncurrent_liabilities")

    _calcProfitability(r)
    _calcStability(r)
    _calcEfficiency(r)
    _calcCashflow(r, series)
    _calcComposite(r, series, annual=annual)

    if marketCap and marketCap > 0:
        r.marketCap = marketCap
        _calcValuation(r)

    # BS 항등식 검증: 자산 ≈ 부채 + 자본
    if r.totalAssets and r.totalLiabilities is not None and r.totalEquity is not None:
        lhs = r.totalAssets
        rhs = r.totalLiabilities + r.totalEquity
        if lhs > 0:
            diff = abs(lhs - rhs) / lhs
            if diff > 0.01:
                r.warnings.append(f"BS 항등식 불일치: 자산 {lhs:,.0f} ≠ 부채+자본 {rhs:,.0f} (차이 {diff:.1%})")

    _applyArchetypePolicyResult(r, archetype)
    return r


def _calcProfitability(r: RatioResult) -> None:
    """수익성 비율 (8개)."""
    r.roe = _safePct(r.netIncomeTTM, r.ownersEquity)
    if r.roe is not None and not (-500 <= r.roe <= 500):
        r.warnings.append(f"ROE {r.roe:.0f}% 범위 초과")
        r.roe = None

    r.roa = _safePct(r.netIncomeTTM, r.totalAssets)
    if r.roa is not None and not (-200 <= r.roa <= 200):
        r.warnings.append(f"ROA {r.roa:.0f}% 범위 초과")
        r.roa = None

    r.operatingMargin = _safePct(r.operatingIncomeTTM, r.revenueTTM)
    r.netMargin = _safePct(r.netIncomeTTM, r.revenueTTM)
    r.grossMargin = _safePct(r.grossProfit, r.revenueTTM)
    r.costOfSalesRatio = _safePct(r.costOfSales, r.revenueTTM)
    r.sgaRatio = _safePct(r.sga, r.revenueTTM)

    if r.operatingIncomeTTM is not None and r.revenueTTM and r.revenueTTM > 0:
        depreciation = r.depreciationExpense
        if depreciation is None:
            depreciation = (r.tangibleAssets or 0) * 0.05 + (r.intangibleAssets or 0) * 0.1
            r.ebitdaEstimated = True
        else:
            r.ebitdaEstimated = False
        ebitda = r.operatingIncomeTTM + depreciation
        r.ebitdaMargin = _safeRound((ebitda / r.revenueTTM) * 100, 2)


def _calcStability(r: RatioResult) -> None:
    """안정성 비율 (7개)."""
    r.debtRatio = _safePct(r.totalLiabilities, r.totalEquity)
    if r.debtRatio is not None and r.debtRatio > 5000:
        r.debtRatio = None

    r.currentRatio = _safePct(r.currentAssets, r.currentLiabilities)
    if r.currentRatio is not None and r.currentRatio > 10000:
        r.currentRatio = None

    if r.currentAssets is not None and r.inventories is not None and r.currentLiabilities and r.currentLiabilities > 0:
        quickAssets = r.currentAssets - r.inventories
        r.quickRatio = _safeRound((quickAssets / r.currentLiabilities) * 100, 2)

    r.equityRatio = _safePct(r.totalEquity, r.totalAssets)

    if r.operatingIncomeTTM is not None and r.financeCosts and r.financeCosts > 0:
        r.interestCoverage = _safeRound(r.operatingIncomeTTM / r.financeCosts, 2)

    totalBorrowings = r.shortTermBorrowings + r.longTermBorrowings + r.bonds
    r.netDebt = totalBorrowings - (r.cash or 0)

    r.netDebtRatio = _safePct(r.netDebt, r.totalEquity)

    if r.noncurrentAssets is not None and r.totalEquity and r.totalEquity > 0:
        r.noncurrentRatio = _safeRound((r.noncurrentAssets / r.totalEquity) * 100, 2)


def _calcEfficiency(r: RatioResult) -> None:
    """효율성 비율 (4개)."""
    r.totalAssetTurnover = _safeRound(_safeDiv(r.revenueTTM, r.totalAssets), 2)
    r.inventoryTurnover = _safeRound(_safeDiv(r.revenueTTM, r.inventories), 2)
    r.receivablesTurnover = _safeRound(_safeDiv(r.revenueTTM, r.receivables), 2)

    if r.costOfSales is not None:
        r.payablesTurnover = _safeRound(_safeDiv(r.costOfSales, r.payables), 2)


def _calcCashflow(
    r: RatioResult,
    series: dict[str, dict[str, list[Optional[float]]]],
) -> None:
    """현금흐름 비율 (5개)."""
    capexAmt = abs(r.capex) if r.capex else 0
    if r.operatingCashflowTTM is not None:
        r.fcf = r.operatingCashflowTTM - capexAmt

    r.operatingCfMargin = _safePct(r.operatingCashflowTTM, r.revenueTTM)
    r.operatingCfToNetIncome = _safePct(r.operatingCashflowTTM, r.netIncomeTTM)

    if r.capex and r.revenueTTM and r.revenueTTM > 0:
        r.capexRatio = _safeRound((abs(r.capex) / r.revenueTTM) * 100, 2)

    if r.dividendsPaid and r.netIncomeTTM and r.netIncomeTTM > 0:
        r.dividendPayoutRatio = _safeRound((abs(r.dividendsPaid) / r.netIncomeTTM) * 100, 2)

    r.revenueGrowth3Y = getRevenueGrowth3Y(series)


def _calcComposite(
    r: RatioResult,
    series: dict[str, dict[str, list[Optional[float]]]],
    annual: bool = False,
) -> None:
    """복합 지표 (11개): ROIC, DuPont, Debt/EBITDA, CCC, Piotroski, Altman."""
    # ── ROIC: NOPAT / Invested Capital ──
    # 유효세율 동적 계산. 불가능하면 22% 기본값.
    effective_tax = 0.22
    pbt = getTTM(series, "IS", "profit_before_tax")
    tax_exp = getTTM(series, "IS", "income_tax_expense")
    if pbt and pbt > 0 and tax_exp is not None:
        _et = tax_exp / pbt
        if 0 <= _et <= 0.5:
            effective_tax = _et
    if r.operatingIncomeTTM is not None and r.totalEquity and r.netDebt is not None:
        nopat = r.operatingIncomeTTM * (1 - effective_tax)
        invested = r.totalEquity + max(r.netDebt, 0)
        if invested > 0:
            r.roic = _safeRound((nopat / invested) * 100, 2)

    # ── DuPont 3분해: ROE = Margin × Turnover × Leverage ──
    r.dupontMargin = _safePct(r.netIncomeTTM, r.revenueTTM)
    r.dupontTurnover = _safeRound(_safeDiv(r.revenueTTM, r.totalAssets), 2)
    if r.totalAssets and r.totalEquity and r.totalEquity > 0:
        r.dupontLeverage = _safeRound(r.totalAssets / r.totalEquity, 2)

    # ── Debt/EBITDA ──
    if r.operatingIncomeTTM is not None:
        dep = r.depreciationExpense
        if dep is None:
            dep = (r.tangibleAssets or 0) * 0.05 + (r.intangibleAssets or 0) * 0.1
        ebitda = r.operatingIncomeTTM + dep
        totalBorr = r.shortTermBorrowings + r.longTermBorrowings + r.bonds
        if ebitda > 0:
            r.debtToEbitda = _safeRound(totalBorr / ebitda, 2)

    # ── CCC: Cash Conversion Cycle ──
    if r.revenueTTM and r.revenueTTM > 0:
        if r.receivables:
            r.dso = _safeRound(r.receivables / r.revenueTTM * 365, 1)
        cos = r.costOfSales or r.revenueTTM
        if r.inventories and cos > 0:
            r.dio = _safeRound(r.inventories / cos * 365, 1)
        if r.payables and cos > 0:
            r.dpo = _safeRound(r.payables / cos * 365, 1)
        if r.dso is not None and r.dio is not None and r.dpo is not None:
            r.ccc = _safeRound(r.dso + r.dio - r.dpo, 1)

    # ── Piotroski F-Score (9점) ──
    _flow = getLatest if annual else getTTM
    score = 0

    # 1. ROA > 0
    if r.roa is not None and r.roa > 0:
        score += 1
    # 2. Operating CF > 0
    if r.operatingCashflowTTM is not None and r.operatingCashflowTTM > 0:
        score += 1
    # 3. ROA 개선 (전년 대비)
    prev_np = _pick_first(series, "IS", ["net_profit", "net_income"], annual=True)
    prev_ta = getLatest(series, "BS", "total_assets")
    # ROA는 이미 계산됨 — 전기 데이터 접근이 제한적이므로 현재 값 기준으로 가용 시 체크
    if r.roa is not None and r.roa > 0:
        score += 0  # 전기 비교 불가 시 skip (보수적)
    # 4. Operating CF > Net Income (발생주의 품질)
    if r.operatingCashflowTTM is not None and r.netIncomeTTM is not None:
        if r.operatingCashflowTTM > r.netIncomeTTM:
            score += 1
    # 5. 부채비율 감소 → 전기 비교 불가 시 현재가 낮으면 가산
    if r.debtRatio is not None and r.debtRatio < 100:
        score += 1
    # 6. 유동비율 > 100%
    if r.currentRatio is not None and r.currentRatio > 100:
        score += 1
    # 7. 신주 미발행 → 데이터 제한으로 skip
    # 8. 매출총이익률 개선 → 현재 양수면 가산 (보수적)
    if r.grossMargin is not None and r.grossMargin > 0:
        score += 1
    # 9. 총자산회전율 양수
    if r.totalAssetTurnover is not None and r.totalAssetTurnover > 0:
        score += 1

    r.piotroskiFScore = score

    # ── Altman Z-Score (제조업) ──
    # Z = 1.2×A + 1.4×B + 3.3×C + 0.6×D + 1.0×E
    # A=WC/TA, B=RE/TA, C=EBIT/TA, D=MarketCap/TL(or Equity/TL), E=Sales/TA
    if r.totalAssets and r.totalAssets > 0 and r.totalLiabilities and r.totalLiabilities > 0:
        wc = (r.currentAssets or 0) - (r.currentLiabilities or 0)
        a = wc / r.totalAssets
        b = (r.retainedEarnings or 0) / r.totalAssets
        c = (r.operatingIncomeTTM or 0) / r.totalAssets
        d = (r.totalEquity or 0) / r.totalLiabilities  # equity proxy for market cap
        e = (r.revenueTTM or 0) / r.totalAssets
        z = 1.2 * a + 1.4 * b + 3.3 * c + 0.6 * d + 1.0 * e
        r.altmanZScore = _safeRound(z, 2)


def _calcValuation(r: RatioResult) -> None:
    """밸류에이션 멀티플 (시가총액 필요)."""
    mc = r.marketCap

    if r.netIncomeTTM and r.netIncomeTTM > 0:
        r.per = round(mc / r.netIncomeTTM, 2)

    if r.totalEquity and r.totalEquity > 0:
        r.pbr = round(mc / r.totalEquity, 2)

    if r.revenueTTM and r.revenueTTM > 0:
        r.psr = round(mc / r.revenueTTM, 2)

    totalDebt = r.shortTermBorrowings + r.longTermBorrowings + r.bonds
    netDebt = totalDebt - (r.cash or 0)
    ev = mc + netDebt

    if r.operatingIncomeTTM and r.operatingIncomeTTM > 0:
        depreciation = r.depreciationExpense
        if depreciation is None:
            depreciation = (r.tangibleAssets or 0) * 0.05 + (r.intangibleAssets or 0) * 0.1
        ebitda = r.operatingIncomeTTM + depreciation
        if ebitda > 0:
            r.evEbitda = round(ev / ebitda, 2)


def calcRatioSeries(
    annualSeries: dict[str, dict[str, list[Optional[float]]]],
    years: list[str],
    archetypeOverride: str | None = None,
    yoyLag: int = 1,
) -> RatioSeriesResult:
    """재무비율 시계열 계산 (연간 또는 분기).

    Args:
            annualSeries: buildAnnual() 또는 timeseries 결과의 series.
            years: 기간 리스트 (연간 또는 분기).
            yoyLag: 성장률 비교 기간 간격 (연간=1, 분기=4).

    Returns:
            RatioSeriesResult — 모든 비율이 기간별 리스트.
    """
    n = len(years)
    rs = RatioSeriesResult(years=list(years))
    archetype = archetypeOverride or _detectArchetype(annualSeries)

    revenue = _pick_series(annualSeries, "IS", ["sales", "revenue"])
    costOfSales = _get(annualSeries, "IS", "cost_of_sales")
    grossProfit = _get(annualSeries, "IS", "gross_profit")
    opProfit = _pick_series(annualSeries, "IS", ["operating_profit", "operating_income"])
    netProfit = _pick_series(annualSeries, "IS", ["net_profit", "net_income"])
    sga = _get(annualSeries, "IS", "selling_and_administrative_expenses")
    finCosts = _pick_series(annualSeries, "IS", ["finance_costs", "interest_expense"])

    totalAssets = _get(annualSeries, "BS", "total_assets")
    totalEquity = _get(annualSeries, "BS", "total_stockholders_equity")
    if not any(v is not None for v in totalEquity):
        totalEquity = _get(annualSeries, "BS", "owners_of_parent_equity")
    ownersEquity = _get(annualSeries, "BS", "owners_of_parent_equity")
    if not any(v is not None for v in ownersEquity):
        ownersEquity = totalEquity
    totalLiab = _get(annualSeries, "BS", "total_liabilities")
    curAssets = _get(annualSeries, "BS", "current_assets")
    curLiab = _get(annualSeries, "BS", "current_liabilities")
    cash = _get(annualSeries, "BS", "cash_and_cash_equivalents")
    inventories = _get(annualSeries, "BS", "inventories")
    receivables = _get(annualSeries, "BS", "trade_and_other_receivables")
    payables = _get(annualSeries, "BS", "trade_and_other_payables")
    tangible = _get(annualSeries, "BS", "tangible_assets")
    intangible = _get(annualSeries, "BS", "intangible_assets")
    stBorrow = _get(annualSeries, "BS", "shortterm_borrowings")
    ltBorrow = _get(annualSeries, "BS", "longterm_borrowings")
    bonds = _get(annualSeries, "BS", "debentures")
    ncAssets = _get(annualSeries, "BS", "noncurrent_assets")

    profitBeforeTax = _get(annualSeries, "IS", "profit_before_tax")
    incomeTaxExpense = _get(annualSeries, "IS", "income_tax_expense")

    opCf = _get(annualSeries, "CF", "operating_cashflow")
    capex = _get(annualSeries, "CF", "purchase_of_property_plant_and_equipment")
    divPaid = _get(annualSeries, "CF", "dividends_paid")
    depreciation = _get(annualSeries, "CF", "depreciation_and_amortization")
    if not any(v is not None for v in depreciation):
        depreciation = _get(annualSeries, "CF", "depreciation_cf")
    if not any(v is not None for v in depreciation):
        depreciation = _get(annualSeries, "CF", "depreciation")

    def _v(lst: list, i: int) -> Optional[float]:
        if i < len(lst):
            return lst[i]
        return None

    for i in range(n):
        rev_i = _v(revenue, i)
        cos_i = _v(costOfSales, i)
        gp_i = _v(grossProfit, i)
        op_i = _v(opProfit, i)
        np_i = _v(netProfit, i)
        sga_i = _v(sga, i)
        fc_i = _v(finCosts, i)

        ta_i = _v(totalAssets, i)
        te_i = _v(totalEquity, i)
        oe_i = _v(ownersEquity, i)
        tl_i = _v(totalLiab, i)
        ca_i = _v(curAssets, i)
        cl_i = _v(curLiab, i)
        cash_i = _v(cash, i)
        inv_i = _v(inventories, i)
        rec_i = _v(receivables, i)
        pay_i = _v(payables, i)
        tan_i = _v(tangible, i)
        int_i = _v(intangible, i)
        stb_i = _v(stBorrow, i) or 0
        ltb_i = _v(ltBorrow, i) or 0
        bnd_i = _v(bonds, i) or 0
        nca_i = _v(ncAssets, i)

        opcf_i = _v(opCf, i)
        cap_i = _v(capex, i)
        div_i = _v(divPaid, i)

        rs.revenue.append(rev_i)
        rs.operatingProfit.append(op_i)
        rs.netProfit.append(np_i)
        rs.totalAssets.append(ta_i)
        rs.totalEquity.append(te_i)
        rs.operatingCashflow.append(opcf_i)

        rs.roe.append(_safePct(np_i, oe_i))
        rs.roa.append(_safePct(np_i, ta_i))
        rs.operatingMargin.append(_safePct(op_i, rev_i))
        rs.netMargin.append(_safePct(np_i, rev_i))
        rs.grossMargin.append(_safePct(gp_i, rev_i))
        rs.costOfSalesRatio.append(_safePct(cos_i, rev_i))
        rs.sgaRatio.append(_safePct(sga_i, rev_i))

        dep = _v(depreciation, i)
        if dep is None:
            dep = (tan_i or 0) * 0.05 + (int_i or 0) * 0.1
        ebitda = (op_i + dep) if op_i is not None else None
        rs.ebitdaMargin.append(_safePct(ebitda, rev_i))

        rs.debtRatio.append(_safePct(tl_i, te_i))
        rs.currentRatio.append(_safePct(ca_i, cl_i))

        if ca_i is not None and inv_i is not None and cl_i and cl_i > 0:
            rs.quickRatio.append(_safeRound(((ca_i - inv_i) / cl_i) * 100, 2))
        else:
            rs.quickRatio.append(None)

        rs.equityRatio.append(_safePct(te_i, ta_i))

        if op_i is not None and fc_i and fc_i > 0:
            rs.interestCoverage.append(_safeRound(op_i / fc_i, 2))
        else:
            rs.interestCoverage.append(None)

        nd = stb_i + ltb_i + bnd_i - (cash_i or 0)
        rs.netDebtRatio.append(_safePct(nd, te_i))

        if nca_i is not None and te_i and te_i > 0:
            rs.noncurrentRatio.append(_safeRound((nca_i / te_i) * 100, 2))
        else:
            rs.noncurrentRatio.append(None)

        rs.revenueGrowth.append(_yoy(revenue, i, yoyLag) if len(revenue) > i else None)
        rs.operatingProfitGrowth.append(_yoy(opProfit, i, yoyLag) if len(opProfit) > i else None)
        rs.netProfitGrowth.append(_yoy(netProfit, i, yoyLag) if len(netProfit) > i else None)
        rs.assetGrowth.append(_yoy(totalAssets, i, yoyLag) if len(totalAssets) > i else None)
        rs.equityGrowthRate.append(_yoy(totalEquity, i, yoyLag) if len(totalEquity) > i else None)

        rs.totalAssetTurnover.append(_safeRound(_safeDiv(rev_i, ta_i), 2))
        rs.inventoryTurnover.append(_safeRound(_safeDiv(rev_i, inv_i), 2))
        rs.receivablesTurnover.append(_safeRound(_safeDiv(rev_i, rec_i), 2))
        rs.payablesTurnover.append(_safeRound(_safeDiv(cos_i, pay_i), 2))

        capAmt = abs(cap_i) if cap_i and cap_i > 0 else 0
        if opcf_i is not None:
            rs.fcf.append(opcf_i - capAmt)
        else:
            rs.fcf.append(None)

        rs.operatingCfMargin.append(_safePct(opcf_i, rev_i))
        rs.operatingCfToNetIncome.append(_safePct(opcf_i, np_i))

        if cap_i and rev_i and rev_i > 0:
            rs.capexRatio.append(_safeRound((abs(cap_i) / rev_i) * 100, 2))
        else:
            rs.capexRatio.append(None)

        if div_i and np_i and np_i > 0:
            rs.dividendPayoutRatio.append(_safeRound((abs(div_i) / np_i) * 100, 2))
        else:
            rs.dividendPayoutRatio.append(None)

        # ── 복합 지표 (시계열) ──

        # ROIC — 유효세율 동적 계산
        pbt_i = _v(profitBeforeTax, i)
        tax_i = _v(incomeTaxExpense, i)
        et_i = 0.22
        if pbt_i and pbt_i > 0 and tax_i is not None:
            _et_i = tax_i / pbt_i
            if 0 <= _et_i <= 0.5:
                et_i = _et_i
        nopat_i = op_i * (1 - et_i) if op_i is not None else None
        nd_i = stb_i + ltb_i + bnd_i - (cash_i or 0)
        invested_i = (te_i or 0) + max(nd_i, 0) if te_i is not None else None
        rs.roic.append(_safePct(nopat_i, invested_i))

        # DuPont
        rs.dupontMargin.append(_safePct(np_i, rev_i))
        rs.dupontTurnover.append(_safeRound(_safeDiv(rev_i, ta_i), 2))
        rs.dupontLeverage.append(_safeRound(_safeDiv(ta_i, te_i), 2) if te_i and te_i > 0 else None)

        # Debt/EBITDA
        dep_i = _v(depreciation, i)
        if dep_i is None:
            dep_i = (tan_i or 0) * 0.05 + (int_i or 0) * 0.1
        ebitda_i = (op_i + dep_i) if op_i is not None else None
        totalBorr_i = stb_i + ltb_i + bnd_i
        if ebitda_i and ebitda_i > 0:
            rs.debtToEbitda.append(_safeRound(totalBorr_i / ebitda_i, 2))
        else:
            rs.debtToEbitda.append(None)

        # CCC (DSO + DIO - DPO)
        cos_for_days = cos_i if cos_i and cos_i > 0 else rev_i
        dso_i = _safeRound(rec_i / rev_i * 365, 1) if rec_i and rev_i and rev_i > 0 else None
        dio_i = _safeRound(inv_i / cos_for_days * 365, 1) if inv_i and cos_for_days and cos_for_days > 0 else None
        dpo_i = _safeRound(pay_i / cos_for_days * 365, 1) if pay_i and cos_for_days and cos_for_days > 0 else None
        rs.dso.append(dso_i)
        rs.dio.append(dio_i)
        rs.dpo.append(dpo_i)
        rs.ccc.append(_safeRound(dso_i + dio_i - dpo_i, 1) if dso_i and dio_i and dpo_i else None)

        # Piotroski F-Score (시계열 — 사용 가능한 지표만)
        fscore = 0
        if np_i is not None and ta_i and ta_i > 0 and np_i / ta_i > 0:
            fscore += 1
        if opcf_i is not None and opcf_i > 0:
            fscore += 1
        if opcf_i is not None and np_i is not None and opcf_i > np_i:
            fscore += 1
        if tl_i is not None and te_i and te_i > 0 and (tl_i / te_i * 100) < 100:
            fscore += 1
        if ca_i and cl_i and cl_i > 0 and (ca_i / cl_i * 100) > 100:
            fscore += 1
        gm = _safePct(gp_i, rev_i)
        if gm is not None and gm > 0:
            fscore += 1
        tat = _safeDiv(rev_i, ta_i)
        if tat is not None and tat > 0:
            fscore += 1
        rs.piotroskiFScore.append(fscore)

        # Altman Z-Score
        if ta_i and ta_i > 0 and tl_i and tl_i > 0:
            wc_i = (ca_i or 0) - (cl_i or 0)
            re_i = _v(_get(annualSeries, "BS", "retained_earnings"), i)
            z = (
                1.2 * (wc_i / ta_i)
                + 1.4 * ((re_i or 0) / ta_i)
                + 3.3 * ((op_i or 0) / ta_i)
                + 0.6 * ((te_i or 0) / tl_i)
                + 1.0 * ((rev_i or 0) / ta_i)
            )
            rs.altmanZScore.append(_safeRound(z, 2))
        else:
            rs.altmanZScore.append(None)

    _applyArchetypePolicySeries(rs, archetype)
    return rs


RATIO_CATEGORIES: list[tuple[str, list[str]]] = [
    (
        "profitability",
        [
            "roe",
            "roa",
            "operatingMargin",
            "netMargin",
            "grossMargin",
            "ebitdaMargin",
            "costOfSalesRatio",
            "sgaRatio",
        ],
    ),
    (
        "stability",
        [
            "debtRatio",
            "currentRatio",
            "quickRatio",
            "equityRatio",
            "interestCoverage",
            "netDebtRatio",
            "noncurrentRatio",
        ],
    ),
    (
        "growth",
        [
            "revenueGrowth",
            "operatingProfitGrowth",
            "netProfitGrowth",
            "assetGrowth",
            "equityGrowthRate",
        ],
    ),
    (
        "efficiency",
        [
            "totalAssetTurnover",
            "inventoryTurnover",
            "receivablesTurnover",
            "payablesTurnover",
        ],
    ),
    (
        "cashflow",
        [
            "fcf",
            "operatingCfMargin",
            "operatingCfToNetIncome",
            "capexRatio",
            "dividendPayoutRatio",
        ],
    ),
    (
        "composite",
        [
            "roic",
            "dupontMargin",
            "dupontTurnover",
            "dupontLeverage",
            "debtToEbitda",
            "ccc",
            "dso",
            "dio",
            "dpo",
            "piotroskiFScore",
            "altmanZScore",
        ],
    ),
    (
        "absolute",
        [
            "revenue",
            "operatingProfit",
            "netProfit",
            "totalAssets",
            "totalEquity",
            "operatingCashflow",
        ],
    ),
]


def toSeriesDict(
    rs: RatioSeriesResult,
) -> tuple[dict[str, dict[str, list[Optional[float]]]], list[str]]:
    """RatioSeriesResult → IS/BS/CF와 동일한 시계열 dict 변환.

    Returns:
            ({"RATIO": {snakeId: [v1, v2, ...], ...}}, years)
    """
    ratioDict: dict[str, list[Optional[float]]] = {}
    for _, fields in RATIO_CATEGORIES:
        for fieldName in fields:
            vals = getattr(rs, fieldName, [])
            if any(v is not None for v in vals):
                ratioDict[fieldName] = vals
    return {"RATIO": ratioDict}, rs.years
