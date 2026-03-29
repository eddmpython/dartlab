"""재무비율 계산.

시계열 dict에서 핵심 비율을 계산한다.

두 가지 모드:
1. calcRatios(series) → RatioResult (최신 단일 시점, 하위호환)
2. calcRatioSeries(annualSeries, years) → RatioSeriesResult (연도별 시계열)

비율 분류 (6개 카테고리, 60+ 비율):
- 수익성: ROE, ROA, ROCE, 영업이익률, 순이익률, 세전이익률, 매출총이익률, EBITDA마진, 매출원가율, 판관비율, 유효세율, 이익품질비율
- 안정성: 부채비율, 유동비율, 당좌비율, 현금비율, 자기자본비율, 이자보상배율, 순차입금비율, 비유동비율, 운전자본
- 성장성: 매출성장률, 영업이익성장률, 순이익성장률, 자산성장률, 자본성장률
- 효율성: 총자산회전율, 유형자산회전율, 재고자산회전율, 매출채권회전율, 매입채무회전율, 영업순환주기
- 현금흐름: FCF, 영업CF마진, 영업CF/순이익, 영업CF/유동부채, CAPEX비율, 배당성향, FCF/OCF비율
- 주당지표: EPS, BPS (시가총액 필요: PER, PBR, PSR, EV/EBITDA)
- 부실예측: Ohlson O-Score, Altman Z''-Score, Springate S-Score, Zmijewski X-Score
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import ClassVar

from dartlab.core.finance.extract import getLatest, getRevenueGrowth3Y, getTTM


@dataclass
class RatioResult:
    """비율 계산 결과 (최신 단일 시점)."""

    revenueTTM: float | None = None
    operatingIncomeTTM: float | None = None
    netIncomeTTM: float | None = None
    operatingCashflowTTM: float | None = None
    investingCashflowTTM: float | None = None

    totalAssets: float | None = None
    totalEquity: float | None = None
    ownersEquity: float | None = None
    totalLiabilities: float | None = None
    currentAssets: float | None = None
    currentLiabilities: float | None = None
    cash: float | None = None
    shortTermBorrowings: float | None = None
    longTermBorrowings: float | None = None
    bonds: float | None = None

    grossProfit: float | None = None
    costOfSales: float | None = None
    sga: float | None = None
    inventories: float | None = None
    receivables: float | None = None
    payables: float | None = None
    tangibleAssets: float | None = None
    intangibleAssets: float | None = None
    retainedEarnings: float | None = None
    profitBeforeTax: float | None = None
    incomeTaxExpense: float | None = None
    financeIncome: float | None = None
    financeCosts: float | None = None
    capex: float | None = None
    dividendsPaid: float | None = None
    depreciationExpense: float | None = None
    noncurrentAssets: float | None = None
    noncurrentLiabilities: float | None = None

    roe: float | None = None
    roa: float | None = None
    roce: float | None = None
    operatingMargin: float | None = None
    netMargin: float | None = None
    preTaxMargin: float | None = None
    grossMargin: float | None = None
    ebitdaMargin: float | None = None
    costOfSalesRatio: float | None = None
    sgaRatio: float | None = None
    effectiveTaxRate: float | None = None
    incomeQualityRatio: float | None = None

    debtRatio: float | None = None
    currentRatio: float | None = None
    quickRatio: float | None = None
    cashRatio: float | None = None
    equityRatio: float | None = None
    interestCoverage: float | None = None
    netDebt: float | None = None
    netDebtRatio: float | None = None
    noncurrentRatio: float | None = None
    workingCapital: float | None = None

    revenueGrowth: float | None = None
    operatingProfitGrowth: float | None = None
    netProfitGrowth: float | None = None
    assetGrowth: float | None = None
    equityGrowthRate: float | None = None
    revenueGrowth3Y: float | None = None

    totalAssetTurnover: float | None = None
    fixedAssetTurnover: float | None = None
    inventoryTurnover: float | None = None
    receivablesTurnover: float | None = None
    payablesTurnover: float | None = None
    operatingCycle: float | None = None

    fcf: float | None = None
    operatingCfMargin: float | None = None
    operatingCfToNetIncome: float | None = None
    operatingCfToCurrentLiab: float | None = None
    capexRatio: float | None = None
    dividendPayoutRatio: float | None = None
    fcfToOcfRatio: float | None = None

    # 복합 지표
    roic: float | None = None
    dupontMargin: float | None = None
    dupontTurnover: float | None = None
    dupontLeverage: float | None = None
    debtToEbitda: float | None = None
    ccc: float | None = None
    dso: float | None = None
    dio: float | None = None
    dpo: float | None = None
    piotroskiFScore: int | None = None
    piotroskiMaxScore: int = 9
    altmanZScore: float | None = None

    # 이익 품질 지표
    beneishMScore: float | None = None
    sloanAccrualRatio: float | None = None

    # 부실 예측 모델
    ohlsonOScore: float | None = None
    ohlsonProbability: float | None = None
    altmanZppScore: float | None = None
    springateSScore: float | None = None
    zmijewskiXScore: float | None = None

    # 주당지표
    eps: float | None = None
    bps: float | None = None
    dps: float | None = None

    per: float | None = None
    pbr: float | None = None
    psr: float | None = None
    evEbitda: float | None = None
    marketCap: float | None = None
    sharesOutstanding: int | None = None
    ebitdaEstimated: bool = True

    currency: str = "KRW"
    warnings: list[str] = field(default_factory=list)

    # ── 카테고리별 필드 그룹 (표시용) ──────────────────────────
    _DISPLAY_GROUPS: ClassVar[list[tuple[str, list[str]]]] = [
        (
            "수익성",
            [
                "roe",
                "roa",
                "roce",
                "operatingMargin",
                "netMargin",
                "preTaxMargin",
                "grossMargin",
                "ebitdaMargin",
                "costOfSalesRatio",
                "sgaRatio",
                "effectiveTaxRate",
                "incomeQualityRatio",
            ],
        ),
        (
            "안정성",
            [
                "debtRatio",
                "currentRatio",
                "quickRatio",
                "cashRatio",
                "equityRatio",
                "interestCoverage",
                "netDebtRatio",
                "noncurrentRatio",
                "workingCapital",
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
                "fixedAssetTurnover",
                "inventoryTurnover",
                "receivablesTurnover",
                "payablesTurnover",
                "operatingCycle",
            ],
        ),
        (
            "현금흐름",
            [
                "fcf",
                "operatingCfMargin",
                "operatingCfToNetIncome",
                "operatingCfToCurrentLiab",
                "capexRatio",
                "dividendPayoutRatio",
                "fcfToOcfRatio",
            ],
        ),
        ("주당지표", ["eps", "bps", "dps"]),
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
                "altmanZppScore",
                "ohlsonOScore",
                "ohlsonProbability",
                "springateSScore",
                "zmijewskiXScore",
                "beneishMScore",
                "sloanAccrualRatio",
            ],
        ),
    ]

    _LABELS: ClassVar[dict[str, str]] = {
        "roe": "ROE (%)",
        "roa": "ROA (%)",
        "roce": "ROCE (%)",
        "operatingMargin": "영업이익률 (%)",
        "netMargin": "순이익률 (%)",
        "preTaxMargin": "세전이익률 (%)",
        "grossMargin": "매출총이익률 (%)",
        "ebitdaMargin": "EBITDA 마진 (%)",
        "costOfSalesRatio": "매출원가율 (%)",
        "sgaRatio": "판관비율 (%)",
        "effectiveTaxRate": "유효세율 (%)",
        "incomeQualityRatio": "이익품질비율 (%)",
        "debtRatio": "부채비율 (%)",
        "currentRatio": "유동비율 (%)",
        "quickRatio": "당좌비율 (%)",
        "cashRatio": "현금비율 (%)",
        "equityRatio": "자기자본비율 (%)",
        "interestCoverage": "이자보상배율 (x)",
        "netDebtRatio": "순차입금비율 (%)",
        "noncurrentRatio": "비유동비율 (%)",
        "workingCapital": "운전자본",
        "revenueGrowth": "매출성장률 (%)",
        "operatingProfitGrowth": "영업이익성장률 (%)",
        "netProfitGrowth": "순이익성장률 (%)",
        "assetGrowth": "자산성장률 (%)",
        "equityGrowthRate": "자본성장률 (%)",
        "revenueGrowth3Y": "매출 3Y CAGR (%)",
        "totalAssetTurnover": "총자산회전율 (x)",
        "fixedAssetTurnover": "유형자산회전율 (x)",
        "inventoryTurnover": "재고자산회전율 (x)",
        "receivablesTurnover": "매출채권회전율 (x)",
        "payablesTurnover": "매입채무회전율 (x)",
        "operatingCycle": "영업순환주기 (일)",
        "fcf": "FCF",
        "operatingCfMargin": "영업CF마진 (%)",
        "operatingCfToNetIncome": "영업CF/순이익 (%)",
        "operatingCfToCurrentLiab": "영업CF/유동부채 (%)",
        "capexRatio": "CAPEX비율 (%)",
        "dividendPayoutRatio": "배당성향 (%)",
        "fcfToOcfRatio": "FCF/OCF비율 (%)",
        "eps": "EPS (원)",
        "bps": "BPS (원)",
        "dps": "DPS (원)",
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
        "piotroskiFScore": "Piotroski F-Score (0~9)",
        "piotroskiMaxScore": "Piotroski 최대 점수",
        "altmanZScore": "Altman Z-Score",
        "altmanZppScore": "Altman Z''-Score (신흥시장)",
        "ohlsonOScore": "Ohlson O-Score",
        "ohlsonProbability": "부도확률 (%)",
        "springateSScore": "Springate S-Score",
        "zmijewskiXScore": "Zmijewski X-Score",
        "beneishMScore": "Beneish M-Score",
        "sloanAccrualRatio": "Sloan Accrual Ratio (%)",
    }

    def __repr__(self) -> str:
        try:
            from rich.console import Console

            from dartlab.display.richRatio import renderRatio

            console = Console(record=True, width=70)
            console.print(renderRatio(self))
            return console.export_text()
        except ImportError:
            pass
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

    roe: list[float | None] = field(default_factory=list)
    roa: list[float | None] = field(default_factory=list)
    roce: list[float | None] = field(default_factory=list)
    operatingMargin: list[float | None] = field(default_factory=list)
    netMargin: list[float | None] = field(default_factory=list)
    preTaxMargin: list[float | None] = field(default_factory=list)
    grossMargin: list[float | None] = field(default_factory=list)
    ebitdaMargin: list[float | None] = field(default_factory=list)
    costOfSalesRatio: list[float | None] = field(default_factory=list)
    sgaRatio: list[float | None] = field(default_factory=list)
    effectiveTaxRate: list[float | None] = field(default_factory=list)
    incomeQualityRatio: list[float | None] = field(default_factory=list)

    debtRatio: list[float | None] = field(default_factory=list)
    currentRatio: list[float | None] = field(default_factory=list)
    quickRatio: list[float | None] = field(default_factory=list)
    cashRatio: list[float | None] = field(default_factory=list)
    equityRatio: list[float | None] = field(default_factory=list)
    interestCoverage: list[float | None] = field(default_factory=list)
    netDebtRatio: list[float | None] = field(default_factory=list)
    noncurrentRatio: list[float | None] = field(default_factory=list)
    workingCapital: list[float | None] = field(default_factory=list)

    revenueGrowth: list[float | None] = field(default_factory=list)
    operatingProfitGrowth: list[float | None] = field(default_factory=list)
    netProfitGrowth: list[float | None] = field(default_factory=list)
    assetGrowth: list[float | None] = field(default_factory=list)
    equityGrowthRate: list[float | None] = field(default_factory=list)

    totalAssetTurnover: list[float | None] = field(default_factory=list)
    fixedAssetTurnover: list[float | None] = field(default_factory=list)
    inventoryTurnover: list[float | None] = field(default_factory=list)
    receivablesTurnover: list[float | None] = field(default_factory=list)
    payablesTurnover: list[float | None] = field(default_factory=list)
    operatingCycle: list[float | None] = field(default_factory=list)

    fcf: list[float | None] = field(default_factory=list)
    operatingCfMargin: list[float | None] = field(default_factory=list)
    operatingCfToNetIncome: list[float | None] = field(default_factory=list)
    operatingCfToCurrentLiab: list[float | None] = field(default_factory=list)
    capexRatio: list[float | None] = field(default_factory=list)
    dividendPayoutRatio: list[float | None] = field(default_factory=list)
    fcfToOcfRatio: list[float | None] = field(default_factory=list)

    # 복합 지표
    roic: list[float | None] = field(default_factory=list)
    dupontMargin: list[float | None] = field(default_factory=list)
    dupontTurnover: list[float | None] = field(default_factory=list)
    dupontLeverage: list[float | None] = field(default_factory=list)
    debtToEbitda: list[float | None] = field(default_factory=list)
    ccc: list[float | None] = field(default_factory=list)
    dso: list[float | None] = field(default_factory=list)
    dio: list[float | None] = field(default_factory=list)
    dpo: list[float | None] = field(default_factory=list)
    piotroskiFScore: list[int | None] = field(default_factory=list)
    altmanZScore: list[float | None] = field(default_factory=list)
    beneishMScore: list[float | None] = field(default_factory=list)
    sloanAccrualRatio: list[float | None] = field(default_factory=list)

    revenue: list[float | None] = field(default_factory=list)
    operatingProfit: list[float | None] = field(default_factory=list)
    netProfit: list[float | None] = field(default_factory=list)
    totalAssets: list[float | None] = field(default_factory=list)
    totalEquity: list[float | None] = field(default_factory=list)
    operatingCashflow: list[float | None] = field(default_factory=list)


def _safeDiv(a: float | None, b: float | None) -> float | None:
    if a is None or b is None or b == 0:
        return None
    return a / b


def _safePct(a: float | None, b: float | None) -> float | None:
    r = _safeDiv(a, b)
    if r is None:
        return None
    return round(r * 100, 2)


def _safeRound(v: float | None, n: int = 2) -> float | None:
    if v is None:
        return None
    return round(v, n)


def yoy_pct(cur: float | None, prev: float | None) -> float | None:
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


def _yoy(vals: list[float | None], i: int, lag: int = 1) -> float | None:
    if i < lag:
        return None
    return yoy_pct(vals[i], vals[i - lag])


def _get(series: dict, sjDiv: str, snakeId: str) -> list[float | None]:
    return series.get(sjDiv, {}).get(snakeId, [])


def _detectArchetype(series: dict[str, dict[str, list[float | None]]]) -> str:
    """점수 기반 업종 분류. 하이브리드 기업도 정확히 분류.

    각 archetype의 시그니처 계정 존재 여부로 점수를 매기고,
    가장 높은 점수의 archetype을 반환. 복수 archetype이 비슷하면 "financial" 반환.
    """
    isKeys = set(series.get("IS", {}))
    bsKeys = set(series.get("BS", {}))

    scores: dict[str, int] = {
        "insurance": 0,
        "bank": 0,
        "securities": 0,
    }

    # 보험 시그니처
    _INSURANCE_IS = {
        "insurance_revenue",
        "assumed_reinsurance_premiums",
        "benefit_payments",
        "insurance_service_expense",
        "net_insurance_finance_expense",
    }
    scores["insurance"] = len(_INSURANCE_IS.intersection(isKeys))

    # 은행 시그니처
    _BANK_IS = {"interest_income", "net_interest_income"}
    _BANK_BS = {"loans", "cash_and_deposits", "debt_securities_at_amortized_cost", "deposits_from_customers"}
    scores["bank"] = len(_BANK_IS.intersection(isKeys)) + len(_BANK_BS.intersection(bsKeys))

    # 증권 시그니처
    _SEC_IS = {"commission_income", "fee_and_commission_income"}
    _SEC_BS = {
        "financial_assets_at_fv_through_profit",
        "financial_assets_at_fv_through_oci",
        "financial_assets_at_amortized_cost",
    }
    scores["securities"] = len(_SEC_IS.intersection(isKeys)) + len(_SEC_BS.intersection(bsKeys))

    # 일반 기업 시그니처 -- 매출/매출원가가 있으면 general 우세
    _GENERAL_IS = {"sales", "revenue", "cost_of_sales", "selling_and_administrative_expenses"}
    generalSignals = len(_GENERAL_IS.intersection(isKeys))

    # 최고 점수 archetype 선택
    max_score = max(scores.values())
    if max_score == 0:
        return "general"

    # 일반 기업 시그니처가 있으면 (매출 존재) 금융업 오분류 방지
    # 최소 3점 이상이어야 금융업 확정. BS 금융자산만으로는 부족.
    if max_score < 3 and generalSignals >= 1:
        return "general"

    top = [k for k, v in scores.items() if v == max_score]

    # 복수 archetype이 동점이면 "financial" (하이브리드)
    if len(top) > 1:
        return "financial"

    return top[0]


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
        "cashRatio",
        "interestCoverage",
        "netDebt",
        "netDebtRatio",
        "noncurrentRatio",
        "workingCapital",
        "inventoryTurnover",
        "fixedAssetTurnover",
        "receivablesTurnover",
        "payablesTurnover",
        "operatingCycle",
        "operatingCfMargin",
        "operatingCfToNetIncome",
        "operatingCfToCurrentLiab",
        "capexRatio",
        "fcf",
        "fcfToOcfRatio",
    )

    _setNone(result, "ccc", "dso", "dio", "dpo", "altmanZScore", "debtToEbitda")

    if archetype in {"bank", "financial"}:
        _setNone(
            result,
            "operatingMargin",
            "netMargin",
            "preTaxMargin",
            "grossMargin",
            "ebitdaMargin",
            "costOfSalesRatio",
            "sgaRatio",
            "roce",
        )


def _applyArchetypePolicySeries(result: RatioSeriesResult, archetype: str) -> None:
    if archetype == "general":
        return

    _setSeriesNone(
        result,
        "debtRatio",
        "currentRatio",
        "quickRatio",
        "cashRatio",
        "interestCoverage",
        "netDebtRatio",
        "noncurrentRatio",
        "workingCapital",
        "inventoryTurnover",
        "fixedAssetTurnover",
        "receivablesTurnover",
        "payablesTurnover",
        "operatingCycle",
        "operatingCfMargin",
        "operatingCfToNetIncome",
        "operatingCfToCurrentLiab",
        "capexRatio",
        "fcf",
        "fcfToOcfRatio",
    )

    _setSeriesNone(result, "ccc", "dso", "dio", "dpo", "altmanZScore", "debtToEbitda")

    if archetype in {"bank", "financial"}:
        _setSeriesNone(
            result,
            "operatingMargin",
            "netMargin",
            "preTaxMargin",
            "grossMargin",
            "ebitdaMargin",
            "costOfSalesRatio",
            "sgaRatio",
            "roce",
        )


def _pick_first(
    series: dict[str, dict[str, list[float | None]]],
    sjDiv: str,
    snakeIds: list[str],
    annual: bool = False,
    maxTrailingNones: int | None = None,
) -> float | None:
    def _getTtmValue(
        targetSeries: dict[str, dict[str, list[float | None]]],
        targetSjDiv: str,
        targetSnakeId: str,
    ) -> float | None:
        return getTTM(targetSeries, targetSjDiv, targetSnakeId, maxTrailingNones=maxTrailingNones)

    if annual:
        getter = getLatest
    else:
        getter = _getTtmValue
    for snakeId in snakeIds:
        val = getter(series, sjDiv, snakeId)
        if val is not None:
            return val
    return None


def _pick_series(
    series: dict[str, dict[str, list[float | None]]],
    sjDiv: str,
    snakeIds: list[str],
) -> list[float | None]:
    for snakeId in snakeIds:
        values = _get(series, sjDiv, snakeId)
        if any(v is not None for v in values):
            return values
    return []


def calcRatios(
    series: dict[str, dict[str, list[float | None]]],
    marketCap: float | None = None,
    annual: bool = False,
    archetypeOverride: str | None = None,
    shares: int | None = None,
    currency: str = "KRW",
) -> RatioResult:
    """시계열에서 재무비율 계산 (최신 단일 시점).

    Args:
            series: buildTimeseries() 또는 buildAnnual() 결과.
            marketCap: 시가총액 (원 단위). None이면 밸류에이션 멀티플 건너뜀.
            annual: True면 IS/CF에 getLatest 사용 (연간 시계열).
                    False면 getTTM 사용 (분기 시계열, 기본값).
            shares: 발행주식수. None이면 주당지표(EPS/BPS/DPS) 건너뜀.
            currency: 통화 코드. grading에서 시장별 임계값 분기에 사용.

    Returns:
            RatioResult.
    """
    r = RatioResult()
    r.currency = currency
    archetype = archetypeOverride or _detectArchetype(series)

    if annual:
        _flow = getLatest
        ttmMaxTrailingNones = None
    else:

        def _flowTtm(
            targetSeries: dict[str, dict[str, list[float | None]]],
            targetSjDiv: str,
            targetSnakeId: str,
        ) -> float | None:
            return getTTM(targetSeries, targetSjDiv, targetSnakeId, maxTrailingNones=0)

        _flow = _flowTtm
        ttmMaxTrailingNones = 0

    r.revenueTTM = _pick_first(series, "IS", ["sales", "revenue"], annual=annual, maxTrailingNones=ttmMaxTrailingNones)
    r.operatingIncomeTTM = _pick_first(
        series,
        "IS",
        ["operating_profit", "operating_income"],
        annual=annual,
        maxTrailingNones=ttmMaxTrailingNones,
    )
    r.netIncomeTTM = _pick_first(
        series,
        "IS",
        ["net_profit", "net_income"],
        annual=annual,
        maxTrailingNones=ttmMaxTrailingNones,
    )
    r.operatingCashflowTTM = _flow(series, "CF", "operating_cashflow")
    r.investingCashflowTTM = _flow(series, "CF", "investing_cashflow")

    r.grossProfit = _flow(series, "IS", "gross_profit")
    r.costOfSales = _flow(series, "IS", "cost_of_sales")
    r.sga = _flow(series, "IS", "selling_and_administrative_expenses")
    r.financeIncome = _flow(series, "IS", "finance_income")
    r.financeCosts = _pick_first(
        series,
        "IS",
        ["finance_costs", "interest_expense"],
        annual=annual,
        maxTrailingNones=ttmMaxTrailingNones,
    )

    r.capex = _flow(series, "CF", "purchase_of_property_plant_and_equipment")
    r.dividendsPaid = _flow(series, "CF", "dividends_paid")
    r.depreciationExpense = _pick_first(
        series,
        "CF",
        ["depreciation_and_amortization", "depreciation_cf", "depreciation"],
        annual=annual,
        maxTrailingNones=ttmMaxTrailingNones,
    )
    # CF에 없으면 IS의 D&A 시도 (EDGAR는 IS에 별도 기재하는 경우 있음)
    if r.depreciationExpense is None:
        r.depreciationExpense = _pick_first(
            series,
            "IS",
            ["depreciation_amortization", "depreciation_and_amortization"],
            annual=annual,
            maxTrailingNones=ttmMaxTrailingNones,
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

    r.profitBeforeTax = _pick_first(
        series,
        "IS",
        ["profit_before_tax", "income_before_tax"],
        annual=annual,
        maxTrailingNones=ttmMaxTrailingNones,
    )
    r.incomeTaxExpense = _pick_first(
        series,
        "IS",
        ["income_tax_expense", "income_taxes"],
        annual=annual,
        maxTrailingNones=ttmMaxTrailingNones,
    )

    if marketCap and marketCap > 0:
        r.marketCap = marketCap

    _calcProfitability(r)
    _calcStability(r)
    _calcEfficiency(r)
    _calcCashflow(r, series)
    _calcComposite(r, series, annual=annual, maxTrailingNones=ttmMaxTrailingNones)

    if shares and shares > 0:
        r.sharesOutstanding = shares
        _calcPerShare(r)

    if r.marketCap and r.marketCap > 0:
        _calcValuation(r)

    # BS 항등식 검증: 자산 ≈ 부채 + 자본
    if r.totalAssets and r.totalLiabilities is not None and r.totalEquity is not None:
        lhs = r.totalAssets
        rhs = r.totalLiabilities + r.totalEquity
        if lhs > 0:
            diff = abs(lhs - rhs) / lhs
            if diff > 0.01:
                r.warnings.append(f"BS 항등식 불일치: 자산 {lhs:,.0f} ≠ 부채+자본 {rhs:,.0f} (차이 {diff:.1%})")

    # IS-CF 교차 검증: 순이익 일치 여부
    cfNetIncome = _flow(series, "CF", "net_income") or _flow(series, "CF", "net_profit")
    if r.netIncomeTTM is not None and cfNetIncome is not None:
        if r.netIncomeTTM != 0:
            niDiff = abs(r.netIncomeTTM - cfNetIncome) / abs(r.netIncomeTTM)
            if niDiff > 0.05:
                r.warnings.append(
                    f"IS-CF 순이익 불일치: IS {r.netIncomeTTM:,.0f} vs CF {cfNetIncome:,.0f} (차이 {niDiff:.1%})"
                )

    _applyArchetypePolicyResult(r, archetype)
    return r


def _calcProfitability(r: RatioResult) -> None:
    """수익성 비율 (12개)."""
    r.roe = _safePct(r.netIncomeTTM, r.ownersEquity)
    if r.roe is not None and not (-500 <= r.roe <= 500):
        r.warnings.append(f"ROE {r.roe:.0f}% 범위 초과")
        r.roe = None

    r.roa = _safePct(r.netIncomeTTM, r.totalAssets)
    if r.roa is not None and not (-200 <= r.roa <= 200):
        r.warnings.append(f"ROA {r.roa:.0f}% 범위 초과")
        r.roa = None

    # ROCE: EBIT / Capital Employed (총자산 - 유동부채)
    if r.operatingIncomeTTM is not None and r.totalAssets and r.currentLiabilities is not None:
        capitalEmployed = r.totalAssets - r.currentLiabilities
        if capitalEmployed > 0:
            r.roce = _safeRound((r.operatingIncomeTTM / capitalEmployed) * 100, 2)

    r.operatingMargin = _safePct(r.operatingIncomeTTM, r.revenueTTM)
    r.netMargin = _safePct(r.netIncomeTTM, r.revenueTTM)
    r.preTaxMargin = _safePct(r.profitBeforeTax, r.revenueTTM)
    r.grossMargin = _safePct(r.grossProfit, r.revenueTTM)
    r.costOfSalesRatio = _safePct(r.costOfSales, r.revenueTTM)
    r.sgaRatio = _safePct(r.sga, r.revenueTTM)

    # 유효세율
    if r.profitBeforeTax and r.profitBeforeTax > 0 and r.incomeTaxExpense is not None:
        etRate = r.incomeTaxExpense / r.profitBeforeTax
        if 0 <= etRate <= 1:
            r.effectiveTaxRate = _safeRound(etRate * 100, 2)

    # 이익품질비율: 영업CF / 순이익 (100% 이상이면 이익의 현금 뒷받침 양호)
    if r.operatingCashflowTTM is not None and r.netIncomeTTM and r.netIncomeTTM > 0:
        r.incomeQualityRatio = _safeRound((r.operatingCashflowTTM / r.netIncomeTTM) * 100, 2)

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
    """안정성 비율 (9개)."""
    r.debtRatio = _safePct(r.totalLiabilities, r.totalEquity)
    if r.debtRatio is not None and r.debtRatio > 5000:
        r.debtRatio = None

    r.currentRatio = _safePct(r.currentAssets, r.currentLiabilities)
    if r.currentRatio is not None and r.currentRatio > 10000:
        r.currentRatio = None

    if r.currentAssets is not None and r.inventories is not None and r.currentLiabilities and r.currentLiabilities > 0:
        quickAssets = r.currentAssets - r.inventories
        r.quickRatio = _safeRound((quickAssets / r.currentLiabilities) * 100, 2)

    # 현금비율: (현금 + 현금성자산) / 유동부채
    r.cashRatio = _safePct(r.cash, r.currentLiabilities)

    r.equityRatio = _safePct(r.totalEquity, r.totalAssets)

    if r.operatingIncomeTTM is not None and r.financeCosts and r.financeCosts > 0:
        r.interestCoverage = _safeRound(r.operatingIncomeTTM / r.financeCosts, 2)

    totalBorrowings = r.shortTermBorrowings + r.longTermBorrowings + r.bonds
    r.netDebt = totalBorrowings - (r.cash or 0)

    r.netDebtRatio = _safePct(r.netDebt, r.totalEquity)

    if r.noncurrentAssets is not None and r.totalEquity and r.totalEquity > 0:
        r.noncurrentRatio = _safeRound((r.noncurrentAssets / r.totalEquity) * 100, 2)

    # 운전자본: 유동자산 - 유동부채
    if r.currentAssets is not None and r.currentLiabilities is not None:
        r.workingCapital = r.currentAssets - r.currentLiabilities


def _calcEfficiency(r: RatioResult) -> None:
    """효율성 비율 (6개)."""
    r.totalAssetTurnover = _safeRound(_safeDiv(r.revenueTTM, r.totalAssets), 2)
    r.fixedAssetTurnover = _safeRound(_safeDiv(r.revenueTTM, r.tangibleAssets), 2)
    r.inventoryTurnover = _safeRound(_safeDiv(r.revenueTTM, r.inventories), 2)
    r.receivablesTurnover = _safeRound(_safeDiv(r.revenueTTM, r.receivables), 2)

    if r.costOfSales is not None:
        r.payablesTurnover = _safeRound(_safeDiv(r.costOfSales, r.payables), 2)

    # 영업순환주기: DSO + DIO (CCC에서 DPO 빼기 전 — 매출+재고 회수에 걸리는 일수)
    # DSO/DIO는 _calcComposite에서 계산되므로 여기서는 placeholder만 설정


def _calcCashflow(
    r: RatioResult,
    series: dict[str, dict[str, list[float | None]]],
) -> None:
    """현금흐름 비율 (7개)."""
    capexAmt = abs(r.capex) if r.capex else 0
    if r.operatingCashflowTTM is not None:
        r.fcf = r.operatingCashflowTTM - capexAmt

    r.operatingCfMargin = _safePct(r.operatingCashflowTTM, r.revenueTTM)
    r.operatingCfToNetIncome = _safePct(r.operatingCashflowTTM, r.netIncomeTTM)

    # 영업CF/유동부채: 단기 채무를 영업현금흐름으로 상환할 수 있는 능력
    r.operatingCfToCurrentLiab = _safePct(r.operatingCashflowTTM, r.currentLiabilities)

    if r.capex and r.revenueTTM and r.revenueTTM > 0:
        r.capexRatio = _safeRound((abs(r.capex) / r.revenueTTM) * 100, 2)

    if r.dividendsPaid and r.netIncomeTTM and r.netIncomeTTM > 0:
        r.dividendPayoutRatio = _safeRound((abs(r.dividendsPaid) / r.netIncomeTTM) * 100, 2)

    # FCF/OCF비율: FCF가 영업CF의 몇 %인지 (CAPEX 부담 측정)
    if r.fcf is not None and r.operatingCashflowTTM and r.operatingCashflowTTM > 0:
        r.fcfToOcfRatio = _safeRound((r.fcf / r.operatingCashflowTTM) * 100, 2)

    r.revenueGrowth3Y = getRevenueGrowth3Y(series)


def _calcComposite(
    r: RatioResult,
    series: dict[str, dict[str, list[float | None]]],
    annual: bool = False,
    maxTrailingNones: int | None = None,
) -> None:
    """복합 지표 (11개): ROIC, DuPont, Debt/EBITDA, CCC, Piotroski, Altman."""
    # ── ROIC: NOPAT / Invested Capital ──
    # 유효세율 동적 계산. 불가능하면 22% 기본값.
    effective_tax = 0.22
    pbt = getTTM(series, "IS", "profit_before_tax", maxTrailingNones=maxTrailingNones)
    tax_exp = getTTM(series, "IS", "income_tax_expense", maxTrailingNones=maxTrailingNones) or getTTM(
        series,
        "IS",
        "income_taxes",
        maxTrailingNones=maxTrailingNones,
    )
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

    # 영업순환주기: DSO + DIO (CCC와 달리 DPO를 빼지 않음)
    if r.dso is not None and r.dio is not None:
        r.operatingCycle = _safeRound(r.dso + r.dio, 1)

    # ── Piotroski F-Score (9점 만점) ──
    score = 0

    # 1. ROA > 0
    if r.roa is not None and r.roa > 0:
        score += 1
    # 2. Operating CF > 0
    if r.operatingCashflowTTM is not None and r.operatingCashflowTTM > 0:
        score += 1
    # 3. ROA 개선 (전년 대비) — 시계열에서 전기 ROA 계산
    npSeries = _pick_series(series, "IS", ["net_profit", "net_income"])
    taSeries = _get(series, "BS", "total_assets")
    if len(npSeries) >= 2 and len(taSeries) >= 2:
        curROA = _safeDiv(npSeries[-1], taSeries[-1]) if npSeries[-1] is not None and taSeries[-1] else None
        prevROA = _safeDiv(npSeries[-2], taSeries[-2]) if npSeries[-2] is not None and taSeries[-2] else None
        if curROA is not None and prevROA is not None and curROA > prevROA:
            score += 1
    # 4. Operating CF > Net Income (발생주의 품질)
    if r.operatingCashflowTTM is not None and r.netIncomeTTM is not None:
        if r.operatingCashflowTTM > r.netIncomeTTM:
            score += 1
    # 5. 부채비율 감소 — 시계열에서 전기 비교
    tlSeries = _get(series, "BS", "total_liabilities")
    teSeries = _get(series, "BS", "total_stockholders_equity")
    if not any(v is not None for v in teSeries):
        teSeries = _get(series, "BS", "owners_of_parent_equity")
    if len(tlSeries) >= 2 and len(teSeries) >= 2:
        curDR = _safeDiv(tlSeries[-1], teSeries[-1])
        prevDR = _safeDiv(tlSeries[-2], teSeries[-2])
        if curDR is not None and prevDR is not None and curDR < prevDR:
            score += 1
    elif r.debtRatio is not None and r.debtRatio < 100:
        score += 1  # 전기 비교 불가 시 fallback
    # 6. 유동비율 개선 — 시계열 비교 or 현재 > 100%
    caSeries = _get(series, "BS", "current_assets")
    clSeries = _get(series, "BS", "current_liabilities")
    if len(caSeries) >= 2 and len(clSeries) >= 2:
        curCR = _safeDiv(caSeries[-1], clSeries[-1])
        prevCR = _safeDiv(caSeries[-2], clSeries[-2])
        if curCR is not None and prevCR is not None and curCR > prevCR:
            score += 1
    elif r.currentRatio is not None and r.currentRatio > 100:
        score += 1
    # 7. 신주 미발행 — 자본금 시계열 비교
    issuedCapital = _get(series, "BS", "issued_capital")
    if not any(v is not None for v in issuedCapital):
        issuedCapital = _get(series, "BS", "capital_stock")
    if len(issuedCapital) >= 2:
        cur_cap = issuedCapital[-1]
        prev_cap = issuedCapital[-2]
        if cur_cap is not None and prev_cap is not None and cur_cap <= prev_cap:
            score += 1
    else:
        score += 1  # 데이터 없으면 신주 미발행으로 간주 (보수적)
    # 8. 매출총이익률 개선 — 시계열 비교
    gpSeries = _get(series, "IS", "gross_profit")
    revSeries = _pick_series(series, "IS", ["sales", "revenue"])
    if len(gpSeries) >= 2 and len(revSeries) >= 2:
        curGM = _safeDiv(gpSeries[-1], revSeries[-1])
        prevGM = _safeDiv(gpSeries[-2], revSeries[-2])
        if curGM is not None and prevGM is not None and curGM > prevGM:
            score += 1
    elif r.grossMargin is not None and r.grossMargin > 0:
        score += 1
    # 9. 총자산회전율 개선 — 시계열 비교
    if len(revSeries) >= 2 and len(taSeries) >= 2:
        curTAT = _safeDiv(revSeries[-1], taSeries[-1])
        prevTAT = _safeDiv(revSeries[-2], taSeries[-2])
        if curTAT is not None and prevTAT is not None and curTAT > prevTAT:
            score += 1
    elif r.totalAssetTurnover is not None and r.totalAssetTurnover > 0:
        score += 1

    r.piotroskiFScore = score

    # ── Altman Z-Score (제조업, 1968) ──
    # Z = 1.2×A + 1.4×B + 3.3×C + 0.6×D + 1.0×E
    # A=WC/TA, B=RE/TA, C=EBIT/TA, D=MarketCap/TL, E=Sales/TA
    # marketCap 없으면 원본 Z 계산 불가 → Z' (비상장 모델, 1983) 사용
    # Z' = 0.717×A + 0.847×B + 3.107×C + 0.420×D' + 0.998×E (D'=BookEquity/TL)
    if r.totalAssets and r.totalAssets > 0 and r.totalLiabilities and r.totalLiabilities > 0:
        wc = (r.currentAssets or 0) - (r.currentLiabilities or 0)
        a = wc / r.totalAssets
        b = (r.retainedEarnings or 0) / r.totalAssets
        c = (r.operatingIncomeTTM or 0) / r.totalAssets
        e = (r.revenueTTM or 0) / r.totalAssets
        if r.marketCap is not None:
            # 원본 Altman Z (상장 기업용)
            d = r.marketCap / r.totalLiabilities
            z = 1.2 * a + 1.4 * b + 3.3 * c + 0.6 * d + 1.0 * e
            r.altmanZScore = _safeRound(z, 2)
        else:
            # Z' (비상장 기업용, 장부가)
            dPrime = (r.totalEquity or 0) / r.totalLiabilities
            zPrime = 0.717 * a + 0.847 * b + 3.107 * c + 0.420 * dPrime + 0.998 * e
            r.altmanZScore = _safeRound(zPrime, 2)

    # ── Sloan Accrual Ratio ──
    # (순이익 - 영업CF) / 총자산. 높으면 발생주의 이익 비중 과다 (조작 의심)
    if r.netIncomeTTM is not None and r.operatingCashflowTTM is not None and r.totalAssets and r.totalAssets > 0:
        accrual = r.netIncomeTTM - r.operatingCashflowTTM
        r.sloanAccrualRatio = _safeRound((accrual / r.totalAssets) * 100, 2)

    # ── Beneish M-Score (8변수 모델) ──
    # M = -4.84 + 0.920×DSRI + 0.528×GMI + 0.404×AQI + 0.892×SGI
    #     + 0.115×DEPI - 0.172×SGAI + 4.679×TATA - 0.327×LVGI
    # M > -2.22이면 이익 조작 가능성
    _calcBeneish(r, series, annual)

    # ── Altman Z''-Score (비제조업/신흥시장, 1995) ──
    # Z'' = 6.56×(WC/TA) + 3.26×(RE/TA) + 6.72×(EBIT/TA) + 1.05×(BV_Equity/TL)
    # Sales/TA 제거 → 금융업/서비스업도 적용 가능
    if r.totalAssets and r.totalAssets > 0 and r.totalLiabilities and r.totalLiabilities > 0:
        wc = (r.currentAssets or 0) - (r.currentLiabilities or 0)
        zpp = (
            6.56 * (wc / r.totalAssets)
            + 3.26 * ((r.retainedEarnings or 0) / r.totalAssets)
            + 6.72 * ((r.operatingIncomeTTM or 0) / r.totalAssets)
            + 1.05 * ((r.totalEquity or 0) / r.totalLiabilities)
        )
        r.altmanZppScore = _safeRound(zpp, 2)

    # ── Ohlson O-Score (1980) — 9변수 로지스틱 ──
    # 금융업 포함 범용. P(bankruptcy) = 1 / (1 + exp(-O))
    if r.totalAssets and r.totalAssets > 0:
        ni = r.netIncomeTTM or 0
        tl = r.totalLiabilities or 0
        ca = r.currentAssets or 0
        cl = r.currentLiabilities or 0

        size = math.log(max(r.totalAssets / 1e6, 1))  # 백만원 단위
        tlta = tl / r.totalAssets
        wcta = (ca - cl) / r.totalAssets
        clca = cl / ca if ca > 0 else 0
        oeneg = 1 if tl > r.totalAssets else 0
        nita = ni / r.totalAssets
        futl = 0  # FFO 간이 대체 (보수적)

        # INTWO: 최근 2기 연속 적자
        npSeries = _pick_series(series, "IS", ["net_profit", "net_income"])
        intwo = 0
        if len(npSeries) >= 2:
            n1 = npSeries[-1]
            n2 = npSeries[-2]
            if n1 is not None and n2 is not None and n1 < 0 and n2 < 0:
                intwo = 1

        # CHIN: 순이익 변화율
        chin = 0
        if len(npSeries) >= 2 and npSeries[-1] is not None and npSeries[-2] is not None:
            denom = abs(npSeries[-1]) + abs(npSeries[-2])
            if denom > 0:
                chin = (npSeries[-1] - npSeries[-2]) / denom

        o = (
            -1.32
            - 0.407 * size
            + 6.03 * tlta
            - 1.43 * wcta
            + 0.0757 * clca
            - 1.72 * oeneg
            - 2.37 * nita
            - 1.83 * futl
            + 0.285 * intwo
            - 0.521 * chin
        )
        r.ohlsonOScore = _safeRound(o, 4)
        r.ohlsonProbability = _safeRound(1 / (1 + math.exp(-o)) * 100, 2)

    # ── Springate S-Score (1978) ──
    # S = 1.03×(WC/TA) + 3.07×(EBIT/TA) + 0.66×(EBT/CL) + 0.40×(Sales/TA)
    # S < 0.862 → 부실 위험
    if r.totalAssets and r.totalAssets > 0 and r.currentLiabilities and r.currentLiabilities > 0:
        wc = (r.currentAssets or 0) - (r.currentLiabilities or 0)
        ebit = r.operatingIncomeTTM or 0
        ebt = r.profitBeforeTax if r.profitBeforeTax is not None else (r.netIncomeTTM or 0)
        rev = r.revenueTTM or 0
        s = (
            1.03 * (wc / r.totalAssets)
            + 3.07 * (ebit / r.totalAssets)
            + 0.66 * (ebt / r.currentLiabilities)
            + 0.40 * (rev / r.totalAssets)
        )
        r.springateSScore = _safeRound(s, 4)

    # ── Zmijewski X-Score (1984) — 3변수 프로빗 ──
    # X = -4.336 - 4.513×(NI/TA) + 5.679×(TL/TA) + 0.004×(CA/CL)
    # X > 0 → 부실 위험. 금융업 부채비율 왜곡 주의.
    if (
        r.totalAssets
        and r.totalAssets > 0
        and r.totalLiabilities is not None
        and r.currentAssets is not None
        and r.currentLiabilities
        and r.currentLiabilities > 0
    ):
        x = (
            -4.336
            - 4.513 * ((r.netIncomeTTM or 0) / r.totalAssets)
            + 5.679 * (r.totalLiabilities / r.totalAssets)
            + 0.004 * (r.currentAssets / r.currentLiabilities)
        )
        r.zmijewskiXScore = _safeRound(x, 4)


def _calcBeneishForPeriod(
    *,
    rev_t: float | None,
    rev_p: float | None,
    rec_t: float | None,
    rec_p: float | None,
    cogs_t: float | None,
    cogs_p: float | None,
    ta_t: float | None,
    ta_p: float | None,
    ca_t: float | None,
    ca_p: float | None,
    sga_t: float | None,
    sga_p: float | None,
    dep_t: float | None,
    dep_p: float | None,
    tan_t: float | None,
    tan_p: float | None,
    np_t: float | None,
    ocf_t: float | None,
    tl_t: float | None,
    tl_p: float | None,
) -> float | None:
    """Beneish M-Score 단일 기간 계산 (현재 t vs 전기 p)."""
    if rev_t is None or rev_p is None or rev_p == 0:
        return None
    if ta_t is None or ta_p is None or ta_p == 0:
        return None

    # DSRI
    dsri = None
    if rec_t is not None and rec_p is not None and rev_t > 0:
        dsr_t = rec_t / rev_t
        dsr_p = rec_p / rev_p
        if dsr_p > 0:
            dsri = dsr_t / dsr_p

    # GMI
    gmi = None
    if cogs_t is not None and cogs_p is not None and rev_t > 0:
        gm_t = (rev_t - cogs_t) / rev_t
        gm_p = (rev_p - cogs_p) / rev_p
        if gm_t > 0 and gm_p > 0:
            gmi = gm_p / gm_t

    # AQI
    aqi = None
    if ca_t is not None and ca_p is not None:
        ppe_t = tan_t or 0
        ppe_p = tan_p or 0
        aq_t = 1 - (ca_t + ppe_t) / ta_t if ta_t > 0 else None
        aq_p = 1 - (ca_p + ppe_p) / ta_p if ta_p > 0 else None
        if aq_t is not None and aq_p is not None and aq_p != 0:
            aqi = aq_t / aq_p

    # SGI
    sgi = rev_t / rev_p

    # DEPI
    depi = None
    if dep_t is not None and dep_p is not None:
        ppe_t = tan_t or 0
        ppe_p = tan_p or 0
        if ppe_t + dep_t > 0 and ppe_p + dep_p > 0:
            dr_t = dep_t / (ppe_t + dep_t)
            dr_p = dep_p / (ppe_p + dep_p)
            if dr_t > 0:
                depi = dr_p / dr_t

    # SGAI
    sgai = None
    if sga_t is not None and sga_p is not None and rev_t > 0 and rev_p > 0:
        sga_r_t = sga_t / rev_t
        sga_r_p = sga_p / rev_p
        if sga_r_p > 0:
            sgai = sga_r_t / sga_r_p

    # TATA
    tata = None
    if np_t is not None and ocf_t is not None and ta_t > 0:
        tata = (np_t - ocf_t) / ta_t

    # LVGI
    lvgi = None
    if tl_t is not None and tl_p is not None and ta_t > 0 and ta_p > 0:
        lev_t = tl_t / ta_t
        lev_p = tl_p / ta_p
        if lev_p > 0:
            lvgi = lev_t / lev_p

    vs = [dsri, gmi, aqi, sgi, depi, sgai, tata, lvgi]
    if all(v is not None for v in vs):
        m = (
            -4.84
            + 0.920 * dsri
            + 0.528 * gmi
            + 0.404 * aqi
            + 0.892 * sgi
            + 0.115 * depi
            - 0.172 * sgai
            + 4.679 * tata
            - 0.327 * lvgi
        )
        return _safeRound(m, 2)
    return None


def _calcBeneish(
    r: RatioResult,
    series: dict[str, dict[str, list[float | None]]],
    annual: bool = False,
) -> None:
    """Beneish M-Score 8변수 모델 — _calcBeneishForPeriod에 위임."""
    revSeries = _pick_series(series, "IS", ["sales", "revenue"])
    taSeries = _get(series, "BS", "total_assets")

    if len(revSeries) < 2 or len(taSeries) < 2:
        return

    t, p = len(revSeries) - 1, len(revSeries) - 2

    def _val(s: list, i: int) -> float | None:
        return s[i] if i < len(s) and s[i] is not None else None

    depSeries = _pick_series(series, "CF", ["depreciation_and_amortization", "depreciation_cf", "depreciation"])
    npSeries = _pick_series(series, "IS", ["net_profit", "net_income"])
    tlSeries = _get(series, "BS", "total_liabilities")
    tanSeries = _get(series, "BS", "tangible_assets")

    r.beneishMScore = _calcBeneishForPeriod(
        rev_t=_val(revSeries, t),
        rev_p=_val(revSeries, p),
        rec_t=_val(_get(series, "BS", "trade_and_other_receivables"), t),
        rec_p=_val(_get(series, "BS", "trade_and_other_receivables"), p),
        cogs_t=_val(_get(series, "IS", "cost_of_sales"), t),
        cogs_p=_val(_get(series, "IS", "cost_of_sales"), p),
        ta_t=_val(taSeries, t),
        ta_p=_val(taSeries, p),
        ca_t=_val(_get(series, "BS", "current_assets"), t),
        ca_p=_val(_get(series, "BS", "current_assets"), p),
        sga_t=_val(_get(series, "IS", "selling_and_administrative_expenses"), t),
        sga_p=_val(_get(series, "IS", "selling_and_administrative_expenses"), p),
        dep_t=_val(depSeries, t),
        dep_p=_val(depSeries, p),
        tan_t=_val(tanSeries, t),
        tan_p=_val(tanSeries, p),
        np_t=_val(npSeries, t),
        ocf_t=_val(_get(series, "CF", "operating_cashflow"), t),
        tl_t=_val(tlSeries, t),
        tl_p=_val(tlSeries, p),
    )


def _calcPerShare(r: RatioResult) -> None:
    """주당지표 (발행주식수 필요)."""
    s = r.sharesOutstanding
    if not s or s <= 0:
        return

    if r.netIncomeTTM is not None:
        r.eps = round(r.netIncomeTTM / s, 0)

    equity = r.ownersEquity or r.totalEquity
    if equity is not None:
        r.bps = round(equity / s, 0)

    if r.dividendsPaid is not None and r.dividendsPaid != 0:
        r.dps = round(abs(r.dividendsPaid) / s, 0)


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
    annualSeries: dict[str, dict[str, list[float | None]]],
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
    incomeTaxExpense = _get(annualSeries, "IS", "income_tax_expense") or _get(annualSeries, "IS", "income_taxes")

    opCf = _get(annualSeries, "CF", "operating_cashflow")
    capex = _get(annualSeries, "CF", "purchase_of_property_plant_and_equipment")
    divPaid = _get(annualSeries, "CF", "dividends_paid")
    depreciation = _get(annualSeries, "CF", "depreciation_and_amortization")
    if not any(v is not None for v in depreciation):
        depreciation = _get(annualSeries, "CF", "depreciation_cf")
    if not any(v is not None for v in depreciation):
        depreciation = _get(annualSeries, "CF", "depreciation")

    def _v(lst: list, i: int) -> float | None:
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

        # ROCE
        if op_i is not None and ta_i and cl_i is not None:
            ce_i = ta_i - cl_i
            rs.roce.append(_safeRound((op_i / ce_i) * 100, 2) if ce_i > 0 else None)
        else:
            rs.roce.append(None)

        rs.operatingMargin.append(_safePct(op_i, rev_i))
        rs.netMargin.append(_safePct(np_i, rev_i))

        pbt_i = _v(profitBeforeTax, i)
        rs.preTaxMargin.append(_safePct(pbt_i, rev_i))

        rs.grossMargin.append(_safePct(gp_i, rev_i))
        rs.costOfSalesRatio.append(_safePct(cos_i, rev_i))
        rs.sgaRatio.append(_safePct(sga_i, rev_i))

        # 유효세율
        tax_i = _v(incomeTaxExpense, i)
        if pbt_i and pbt_i > 0 and tax_i is not None:
            et_rate = tax_i / pbt_i
            rs.effectiveTaxRate.append(_safeRound(et_rate * 100, 2) if 0 <= et_rate <= 1 else None)
        else:
            rs.effectiveTaxRate.append(None)

        # 이익품질비율
        if opcf_i is not None and np_i and np_i > 0:
            rs.incomeQualityRatio.append(_safeRound((opcf_i / np_i) * 100, 2))
        else:
            rs.incomeQualityRatio.append(None)

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

        # 현금비율
        rs.cashRatio.append(_safePct(cash_i, cl_i))

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

        # 운전자본
        if ca_i is not None and cl_i is not None:
            rs.workingCapital.append(ca_i - cl_i)
        else:
            rs.workingCapital.append(None)

        rs.revenueGrowth.append(_yoy(revenue, i, yoyLag) if len(revenue) > i else None)
        rs.operatingProfitGrowth.append(_yoy(opProfit, i, yoyLag) if len(opProfit) > i else None)
        rs.netProfitGrowth.append(_yoy(netProfit, i, yoyLag) if len(netProfit) > i else None)
        rs.assetGrowth.append(_yoy(totalAssets, i, yoyLag) if len(totalAssets) > i else None)
        rs.equityGrowthRate.append(_yoy(totalEquity, i, yoyLag) if len(totalEquity) > i else None)

        rs.totalAssetTurnover.append(_safeRound(_safeDiv(rev_i, ta_i), 2))
        rs.fixedAssetTurnover.append(_safeRound(_safeDiv(rev_i, tan_i), 2))
        rs.inventoryTurnover.append(_safeRound(_safeDiv(rev_i, inv_i), 2))
        rs.receivablesTurnover.append(_safeRound(_safeDiv(rev_i, rec_i), 2))
        rs.payablesTurnover.append(_safeRound(_safeDiv(cos_i, pay_i), 2))

        capAmt = abs(cap_i) if cap_i and cap_i > 0 else 0
        if opcf_i is not None:
            fcf_i = opcf_i - capAmt
            rs.fcf.append(fcf_i)
        else:
            fcf_i = None
            rs.fcf.append(None)

        rs.operatingCfMargin.append(_safePct(opcf_i, rev_i))
        rs.operatingCfToNetIncome.append(_safePct(opcf_i, np_i))

        # 영업CF/유동부채
        rs.operatingCfToCurrentLiab.append(_safePct(opcf_i, cl_i))

        if cap_i and rev_i and rev_i > 0:
            rs.capexRatio.append(_safeRound((abs(cap_i) / rev_i) * 100, 2))
        else:
            rs.capexRatio.append(None)

        if div_i and np_i and np_i > 0:
            rs.dividendPayoutRatio.append(_safeRound((abs(div_i) / np_i) * 100, 2))
        else:
            rs.dividendPayoutRatio.append(None)

        # FCF/OCF비율
        if fcf_i is not None and opcf_i and opcf_i > 0:
            rs.fcfToOcfRatio.append(_safeRound((fcf_i / opcf_i) * 100, 2))
        else:
            rs.fcfToOcfRatio.append(None)

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

        # 영업순환주기
        rs.operatingCycle.append(_safeRound(dso_i + dio_i, 1) if dso_i is not None and dio_i is not None else None)

        # Piotroski F-Score (9/9 시계열)
        fscore = 0
        # 1. ROA > 0
        if np_i is not None and ta_i and ta_i > 0 and np_i / ta_i > 0:
            fscore += 1
        # 2. Operating CF > 0
        if opcf_i is not None and opcf_i > 0:
            fscore += 1
        # 3. ROA 개선 (전기 대비)
        if i >= yoyLag:
            prev_np_i = _v(netProfit, i - yoyLag)
            prev_ta_i = _v(totalAssets, i - yoyLag)
            curROA_i = _safeDiv(np_i, ta_i)
            prevROA_i = _safeDiv(prev_np_i, prev_ta_i)
            if curROA_i is not None and prevROA_i is not None and curROA_i > prevROA_i:
                fscore += 1
        # 4. Operating CF > Net Income (발생주의 품질)
        if opcf_i is not None and np_i is not None and opcf_i > np_i:
            fscore += 1
        # 5. 부채비율 감소
        if i >= yoyLag:
            prev_tl_i = _v(totalLiab, i - yoyLag)
            prev_te_i = _v(totalEquity, i - yoyLag)
            curDR_i = _safeDiv(tl_i, te_i)
            prevDR_i = _safeDiv(prev_tl_i, prev_te_i)
            if curDR_i is not None and prevDR_i is not None and curDR_i < prevDR_i:
                fscore += 1
        elif tl_i is not None and te_i and te_i > 0 and (tl_i / te_i * 100) < 100:
            fscore += 1
        # 6. 유동비율 개선
        if i >= yoyLag:
            prev_ca_i = _v(curAssets, i - yoyLag)
            prev_cl_i = _v(curLiab, i - yoyLag)
            curCR_i = _safeDiv(ca_i, cl_i)
            prevCR_i = _safeDiv(prev_ca_i, prev_cl_i)
            if curCR_i is not None and prevCR_i is not None and curCR_i > prevCR_i:
                fscore += 1
        elif ca_i and cl_i and cl_i > 0 and (ca_i / cl_i * 100) > 100:
            fscore += 1
        # 7. 신주 미발행
        issuedCap = _get(annualSeries, "BS", "issued_capital")
        if not any(v is not None for v in issuedCap):
            issuedCap = _get(annualSeries, "BS", "capital_stock")
        if i >= yoyLag and i < len(issuedCap) and (i - yoyLag) < len(issuedCap):
            cur_cap_i = issuedCap[i]
            prev_cap_i = issuedCap[i - yoyLag]
            if cur_cap_i is not None and prev_cap_i is not None and cur_cap_i <= prev_cap_i:
                fscore += 1
            elif cur_cap_i is None and prev_cap_i is None:
                fscore += 1  # 데이터 없으면 미발행 간주
        else:
            fscore += 1  # 데이터 없으면 미발행 간주
        # 8. 매출총이익률 개선
        if i >= yoyLag:
            prev_gp_i = _v(grossProfit, i - yoyLag)
            prev_rev_i = _v(revenue, i - yoyLag)
            curGM_i = _safeDiv(gp_i, rev_i)
            prevGM_i = _safeDiv(prev_gp_i, prev_rev_i)
            if curGM_i is not None and prevGM_i is not None and curGM_i > prevGM_i:
                fscore += 1
        else:
            gm = _safePct(gp_i, rev_i)
            if gm is not None and gm > 0:
                fscore += 1
        # 9. 총자산회전율 개선
        if i >= yoyLag:
            prev_rev_i2 = _v(revenue, i - yoyLag)
            prev_ta_i2 = _v(totalAssets, i - yoyLag)
            curTAT_i = _safeDiv(rev_i, ta_i)
            prevTAT_i = _safeDiv(prev_rev_i2, prev_ta_i2)
            if curTAT_i is not None and prevTAT_i is not None and curTAT_i > prevTAT_i:
                fscore += 1
        else:
            tat = _safeDiv(rev_i, ta_i)
            if tat is not None and tat > 0:
                fscore += 1
        rs.piotroskiFScore.append(fscore)

        # Altman Z'-Score (비상장 모델 — 시계열에 marketCap 없으므로 항상 Z')
        if ta_i and ta_i > 0 and tl_i and tl_i > 0:
            wc_i = (ca_i or 0) - (cl_i or 0)
            re_i = _v(_get(annualSeries, "BS", "retained_earnings"), i)
            dPrime = (te_i or 0) / tl_i
            zPrime = (
                0.717 * (wc_i / ta_i)
                + 0.847 * ((re_i or 0) / ta_i)
                + 3.107 * ((op_i or 0) / ta_i)
                + 0.420 * dPrime
                + 0.998 * ((rev_i or 0) / ta_i)
            )
            rs.altmanZScore.append(_safeRound(zPrime, 2))
        else:
            rs.altmanZScore.append(None)

        # Sloan Accrual Ratio
        if np_i is not None and opcf_i is not None and ta_i and ta_i > 0:
            rs.sloanAccrualRatio.append(_safeRound((np_i - opcf_i) / ta_i * 100, 2))
        else:
            rs.sloanAccrualRatio.append(None)

        # Beneish M-Score (2년 이상 데이터 필요)
        if i >= 1:
            rev_p = _v(revenue, i - 1)
            rec_p = _v(receivables, i - 1)
            cos_p = _v(costOfSales, i - 1)
            ta_p = _v(totalAssets, i - 1)
            ca_p = _v(curAssets, i - 1)
            sga_p = _v(sga, i - 1)
            dep_p = _v(depreciation, i - 1)
            dep_i_val = _v(depreciation, i)
            tan_p = _v(tangible, i - 1)
            tl_p = _v(totalLiab, i - 1)

            m = _calcBeneishForPeriod(
                rev_t=rev_i,
                rev_p=rev_p,
                rec_t=rec_i,
                rec_p=rec_p,
                cogs_t=cos_i,
                cogs_p=cos_p,
                ta_t=ta_i,
                ta_p=ta_p,
                ca_t=ca_i,
                ca_p=ca_p,
                sga_t=sga_i,
                sga_p=sga_p,
                dep_t=dep_i_val,
                dep_p=dep_p,
                tan_t=tan_i,
                tan_p=tan_p,
                np_t=np_i,
                ocf_t=opcf_i,
                tl_t=tl_i,
                tl_p=tl_p,
            )
            rs.beneishMScore.append(m)
        else:
            rs.beneishMScore.append(None)

    _applyArchetypePolicySeries(rs, archetype)
    return rs


RATIO_CATEGORIES: list[tuple[str, list[str]]] = [
    (
        "profitability",
        [
            "roe",
            "roa",
            "roce",
            "operatingMargin",
            "netMargin",
            "preTaxMargin",
            "grossMargin",
            "ebitdaMargin",
            "costOfSalesRatio",
            "sgaRatio",
            "effectiveTaxRate",
            "incomeQualityRatio",
        ],
    ),
    (
        "stability",
        [
            "debtRatio",
            "currentRatio",
            "quickRatio",
            "cashRatio",
            "equityRatio",
            "interestCoverage",
            "netDebtRatio",
            "noncurrentRatio",
            "workingCapital",
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
            "fixedAssetTurnover",
            "inventoryTurnover",
            "receivablesTurnover",
            "payablesTurnover",
            "operatingCycle",
        ],
    ),
    (
        "cashflow",
        [
            "fcf",
            "operatingCfMargin",
            "operatingCfToNetIncome",
            "operatingCfToCurrentLiab",
            "capexRatio",
            "dividendPayoutRatio",
            "fcfToOcfRatio",
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
) -> tuple[dict[str, dict[str, list[float | None]]], list[str]]:
    """RatioSeriesResult → IS/BS/CF와 동일한 시계열 dict 변환.

    Returns:
            ({"RATIO": {snakeId: [v1, v2, ...], ...}}, years)
    """
    ratioDict: dict[str, list[float | None]] = {}
    for _, fields in RATIO_CATEGORIES:
        for fieldName in fields:
            vals = getattr(rs, fieldName, [])
            if any(v is not None for v in vals):
                ratioDict[fieldName] = vals
    return {"RATIO": ratioDict}, rs.years
