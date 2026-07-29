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
- 부실예측: Altman Z''-Score, Springate S-Score, Zmijewski X-Score
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

from dartlab.core.htmlRenderer import getHtmlRenderer
from dartlab.core.ratioCategories import RATIO_CATEGORIES as RATIO_CATEGORIES
from dartlab.core.utils.extract import getLatest, getRevenueGrowth3Y, getTTM


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

    # 이익 품질 지표. Beneish는 호환 슬롯이다. 공용 입력은 원식의 LTD,
    # current maturities, income tax payable, 순수 감가상각을 공급자 간
    # 같은 의미로 보장하지 못하므로 계산하지 않는다.
    beneishMScore: float | None = None
    sloanAccrualRatio: float | None = None

    # 부실 예측 모델. Ohlson 두 필드는 호환 슬롯이다. 공용 다통화 입력에는
    # 원식의 GNP price-level index로 보정한 SIZE가 없어 계산하지 않는다.
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
    ebitdaEstimated: bool | None = None

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
        renderer = getHtmlRenderer()
        if renderer is not None:
            text = renderer.renderRatio(self)
            if text is not None:
                return text
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


from dartlab.core.utils.calc import safeDiv as _safeDiv  # noqa: E402
from dartlab.core.utils.calc import safePct as _safePct  # noqa: E402
from dartlab.core.utils.calc import safePctPositive as _safePctPositive  # noqa: E402


def _safeRound(v: float | None, n: int = 2) -> float | None:
    if v is None:
        return None
    return round(v, n)


def _sumComplete(*values: float | None) -> float | None:
    """모든 구성값이 있을 때만 합계를 반환한다."""
    if any(value is None for value in values):
        return None
    return sum(value for value in values if value is not None)


def _calcNetDebt(
    shortTermBorrowings: float | None,
    longTermBorrowings: float | None,
    bonds: float | None,
    cash: float | None,
) -> float | None:
    """공시된 차입금 세 항목과 현금이 모두 있을 때만 순차입금을 계산한다."""
    totalBorrowings = _sumComplete(shortTermBorrowings, longTermBorrowings, bonds)
    if totalBorrowings is None or cash is None:
        return None
    return totalBorrowings - cash


def _calcEbitdaValue(
    operatingIncome: float | None,
    depreciationExpense: float | None,
) -> float | None:
    """보고된 영업이익과 감가상각비로만 EBITDA를 계산한다."""
    if operatingIncome is None or depreciationExpense is None:
        return None
    return operatingIncome + depreciationExpense


def yoyPct(cur: float | None, prev: float | None) -> float | None:
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
    return yoyPct(vals[i], vals[i - lag])


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

    # 일반 기업 시그니처 -- 매출/매출원가/판관비/영업비용이 있으면 general 우세
    # NAVER 같은 IT/플랫폼은 매출원가 없이 operating_expenses 단일 사용
    _GENERAL_IS = {
        "sales",
        "revenue",
        "cost_of_sales",
        "selling_and_administrative_expenses",
        "operating_expenses",
    }
    generalSignals = len(_GENERAL_IS.intersection(isKeys))

    # 일반 기업 BS 시그니처 (재고/매출채권/유형자산) -- IT/플랫폼은 재고 없을 수 있어 1개로 충분
    _GENERAL_BS = {"inventories", "trade_and_other_receivables", "tangible_assets", "intangible_assets"}
    generalSignalsBs = len(_GENERAL_BS.intersection(bsKeys))

    # 최고 점수 archetype 선택
    max_score = max(scores.values())
    if max_score == 0:
        return "general"

    # 일반 기업 시그니처가 충분하면 (IS 2+ 또는 IS 1 + BS 2+) 금융업 오분류 방지.
    # securities 처럼 financial_assets_* 만 점수에 잡히는 hybrid 도 제외.
    if max_score < 4 and (generalSignals >= 2 or (generalSignals >= 1 and generalSignalsBs >= 2)):
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


def _pickFirst(
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


def _pickSeries(
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
    """시계열 → 재무비율 단일 시점 계산 — DART/EDGAR 공통 백엔드.

    분기 시계열 (annual=False) 은 IS/CF 에 TTM (trailing 4Q 합) 적용, 연간 시계열
    (annual=True) 은 latest 단일 시점. BS 는 항상 latest 시점 잔액.

    계산 범주 (각 ``_calc*`` helper 위임):
      - **Profitability**: GPM / OPM / NPM / ROA / ROE / ROIC / DuPont.
      - **Stability**: 부채비율 / 자기자본비율 / 유동비율 / 당좌비율 / 이자보상.
      - **Efficiency**: 자산회전율 / 재고회전 / 매출채권회전 / CCC.
      - **Cashflow**: OCF / FCF / Capex 비율 / 배당성향.
      - **Composite**: Altman Z / Altman Z'' / Piotroski F / Springate / Zmijewski / Sloan Accrual.
      - **PerShare**: EPS / BPS / DPS (shares 제공 시).
      - **Valuation**: PER / PBR / PSR / EV/EBITDA (marketCap 제공 시).
      - **Archetype Policy**: detected archetype (industrial/bank/insurance/holding/etc.) 별
        부적용 ratio 자동 None 처리 — ``_applyArchetypePolicyResult``.

    Args:
        series: ``buildTimeseries()`` 또는 ``buildAnnual()`` 결과
            (``{"BS"|"IS"|"CF": {snakeId: list[float|None]}}``). dart provider 산출.
            edgar 도 동일 schema 로 정규화 (us-gaap concept → snakeId).
        marketCap: 시가총액 (원 단위, KR) 또는 USD (US). None 이면 밸류에이션 멀티플 skip.
        annual: True 면 IS/CF 에 ``getLatest`` (연간 시계열), False (default) 면 ``getTTM``
            (분기 시계열의 trailing 4Q 합, ``maxTrailingNones=0`` strict).
        archetypeOverride: archetype 자동 감지 (``_detectArchetype``) override. None 이면
            BS/IS 구성으로 industrial/bank/insurance/holding/reit/etc 추론.
        shares: 발행주식수. None 이면 EPS / BPS / DPS skip.
        currency: 통화 코드 ("KRW" / "USD" / "JPY"). grading 시장별 임계값 분기에 사용.

    Returns:
        RatioResult — dataclass with 60+ float|None fields + ``currency`` / ``warnings``.
        Archetype 부적용 field 는 None.

    Raises:
        없음. 데이터 결측은 None 반환 (예외 X). caller 가 None 체크 의무.

    Example:
        >>> series, _ = buildTimeseries("005930")
        >>> r = calcRatios(series, marketCap=400e12, shares=5969782550)
        >>> r.roe, r.debtRatio
        (..., ...)

    SeeAlso:
        - ``RatioResult`` — dataclass 출력 schema.
        - ``calcRatioSeries`` — 시계열 전체 반환 (본 함수 N 회 호출).
        - ``_detectArchetype`` — archetype 자동 감지 룰.
        - ``_applyArchetypePolicyResult`` — archetype 별 N/A 처리.
        - ``_calcProfitability`` / ``_calcStability`` / ``_calcEfficiency`` / ``_calcCashflow``
          / ``_calcComposite`` / ``_calcPiotroski`` / ``_calcAltmanZ`` 등 helper.
        - ``getTTM`` / ``getLatest`` — flow vs stock 추출 헬퍼.

    Requires:
        - dataclasses (RatioResult)
        - dartlab.analysis.financial._constants (임계값 / archetype 룰)

    Capabilities:
        - DART KR + EDGAR US 공통 재무비율 60+ 계산 백엔드.
        - Archetype-aware — 업종별 부적용 ratio 자동 None.
        - TTM / Annual mode 양방향 — 분기 시계열 + 연간 시계열 모두.
        - Composite score (Piotroski/Altman/Springate/Zmijewski/Sloan) 5+ 종.

    Guide:
        - 사용자 API 는 ``c.panel("ratios")`` — 본 함수는 backend.
        - 다종목 batch 발굴 시 ``scanRatio("roe").sort(...).head(N)`` 가 빠름 (parquet vectorized).
        - 단일 종목 deep dive 시 ``c.panel("ratios")`` (본 함수 결과) 60+ field 전부 access.

    AIContext:
        Ask Workbench finance core — ``c.panel("ratios")`` 호출 시 backend. archetype 처리로
        은행/보험/지주 회사에서 부적절 ratio (제조업 기준 OPM 등) 자동 마스킹.

    LLM Specifications:
        AntiPatterns:
            - 본 함수 직접 호출 X — ``c.panel("ratios")`` 위임.
            - ``annual=False`` 인데 분기 시계열이 4 분기 미만 → TTM 계산 불가 → None.
            - ``archetypeOverride`` 강제 후 결과 신뢰 X — 자동 감지 우선, override 는 예외.
            - 다종목 발굴에 본 함수 N 회 X — ``scanRatio`` (vectorized parquet) 사용.
            - currency 누락 → "KRW" default, US 종목 호출 시 잘못된 grading 분기.
        OutputSchema:
            - RatioResult dataclass — 60+ ``float|None`` field
              (``revenueTTM`` / ``operatingIncomeTTM`` / ``netIncomeTTM`` / ``roa`` / ``roe`` /
              ``roic`` / ``debtRatio`` / ``currentRatio`` / ``quickRatio`` /
              ``operatingMargin`` / ``netMargin`` / ``grossMargin`` / ``assetTurnover`` /
              ``inventoryTurnover`` / ``ccc`` / ``fcf`` / ``payoutRatio`` /
              ``altmanZ`` / ``piotroskiF`` / ``springate`` /
              ``zmijewski`` / ``sloanAccrual`` / ``eps`` / ``bps`` / ``per`` / ``pbr`` / ``psr`` /
              ``evEbitda`` 등) + ``currency`` (str) + ``warnings`` (list).
        Prerequisites:
            - series schema = ``{"BS"|"IS"|"CF": {snakeId(str): list[float|None]}}``.
            - 분기 시계열 = ``buildTimeseries()``, 연간 = ``buildAnnual()`` 출력.
            - marketCap / shares 는 gather 의 listing 모듈 또는 외부 origin.
        Freshness:
            - series 는 DART 분기 마감 후 ~45 일 (반기 60 일).
            - marketCap 은 일 단위 갱신 — caller 가 trade date 명시.
        Dataflow:
            - series (raw 시계열) → archetype 감지 → ``getTTM`` / ``getLatest`` 분기
            - → ``_calcProfitability`` / ``_calcStability`` / ``_calcEfficiency`` / ``_calcCashflow``
            - → ``_calcComposite`` / ``_calcRoic`` / ``_calcDupont`` / ``_calcDebtToEbitda`` / ``_calcCCC``
            - → ``_calcPiotroski`` / ``_calcAltmanZ`` / ``_calcSloanAccrual``
              / ``_calcSpringate`` / ``_calcZmijewski``
            - → ``_calcPerShare`` (shares 있을 때) / ``_calcValuation`` (marketCap 있을 때)
            - → ``_applyArchetypePolicyResult`` (부적용 field None 처리)
            - → RatioResult dataclass.
        TargetMarkets:
            - KR (DART) — 제조/금융/보험/지주/리츠 전체.
            - US (SEC EDGAR) — us-gaap 정규화 시 동일 함수 호출 가능 (currency="USD").
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

    r.revenueTTM = _pickFirst(series, "IS", ["sales", "revenue"], annual=annual, maxTrailingNones=ttmMaxTrailingNones)
    r.operatingIncomeTTM = _pickFirst(
        series,
        "IS",
        ["operating_profit", "operating_income"],
        annual=annual,
        maxTrailingNones=ttmMaxTrailingNones,
    )
    r.netIncomeTTM = _pickFirst(
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
    r.financeCosts = _pickFirst(
        series,
        "IS",
        ["finance_costs", "interest_expense"],
        annual=annual,
        maxTrailingNones=ttmMaxTrailingNones,
    )

    r.capex = _flow(series, "CF", "purchase_of_property_plant_and_equipment")
    r.dividendsPaid = _flow(series, "CF", "dividends_paid")
    r.depreciationExpense = _pickFirst(
        series,
        "CF",
        ["depreciation_and_amortization", "depreciation_cf", "depreciation"],
        annual=annual,
        maxTrailingNones=ttmMaxTrailingNones,
    )
    # CF에 없으면 IS의 D&A 시도 (EDGAR는 IS에 별도 기재하는 경우 있음)
    if r.depreciationExpense is None:
        r.depreciationExpense = _pickFirst(
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
    r.shortTermBorrowings = getLatest(series, "BS", "shortterm_borrowings")
    r.longTermBorrowings = getLatest(series, "BS", "longterm_borrowings")
    r.bonds = getLatest(series, "BS", "debentures")
    r.inventories = getLatest(series, "BS", "inventories")
    r.receivables = getLatest(series, "BS", "trade_and_other_receivables")
    r.payables = getLatest(series, "BS", "trade_and_other_payables")
    r.tangibleAssets = getLatest(series, "BS", "tangible_assets")
    r.intangibleAssets = getLatest(series, "BS", "intangible_assets")
    r.retainedEarnings = getLatest(series, "BS", "retained_earnings")
    r.noncurrentAssets = getLatest(series, "BS", "noncurrent_assets")
    r.noncurrentLiabilities = getLatest(series, "BS", "noncurrent_liabilities")

    r.profitBeforeTax = _pickFirst(
        series,
        "IS",
        ["profit_before_tax", "income_before_tax"],
        annual=annual,
        maxTrailingNones=ttmMaxTrailingNones,
    )
    r.incomeTaxExpense = _pickFirst(
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
    _calcComposite(r, series, maxTrailingNones=ttmMaxTrailingNones)

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
    # 자본이 음수면 ROE 는 부호가 뒤집힌다. 적자 기업이 +200% 로 읽혀 수익성
    # 랭킹 맨 위에 올라가고, -500~500 범위 검사도 그 값을 잡지 못한다. 같은
    # 저장소의 scan 빌더와 roce, noncurrentRatio 는 이미 분모 양수를 요구한다.
    r.roe = _safePctPositive(r.netIncomeTTM, r.ownersEquity)
    if r.roe is not None and not (-500 <= r.roe <= 500):
        r.warnings.append(f"ROE {r.roe:.0f}% 범위 초과")
        r.roe = None

    r.roa = _safePctPositive(r.netIncomeTTM, r.totalAssets)
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

    ebitda = _calcEbitdaValue(r.operatingIncomeTTM, r.depreciationExpense)
    if ebitda is not None and r.revenueTTM and r.revenueTTM > 0:
        r.ebitdaEstimated = False
        r.ebitdaMargin = _safeRound((ebitda / r.revenueTTM) * 100, 2)


def _calcStability(r: RatioResult) -> None:
    """안정성 비율 (9개)."""
    # 자본잠식 기업의 부채비율은 음수가 아니라 정의되지 않는다.
    r.debtRatio = _safePctPositive(r.totalLiabilities, r.totalEquity)
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

    r.equityRatio = _safePctPositive(r.totalEquity, r.totalAssets)

    if r.operatingIncomeTTM is not None and r.financeCosts and r.financeCosts > 0:
        r.interestCoverage = _safeRound(r.operatingIncomeTTM / r.financeCosts, 2)

    r.netDebt = _calcNetDebt(r.shortTermBorrowings, r.longTermBorrowings, r.bonds, r.cash)
    r.netDebtRatio = _safePctPositive(r.netDebt, r.totalEquity)

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
    if r.operatingCashflowTTM is not None and r.capex is not None:
        capexAmt = abs(r.capex)
        r.fcf = r.operatingCashflowTTM - capexAmt

    r.operatingCfMargin = _safePct(r.operatingCashflowTTM, r.revenueTTM)
    r.operatingCfToNetIncome = _safePctPositive(r.operatingCashflowTTM, r.netIncomeTTM)

    # 영업CF/유동부채: 단기 채무를 영업현금흐름으로 상환할 수 있는 능력
    r.operatingCfToCurrentLiab = _safePct(r.operatingCashflowTTM, r.currentLiabilities)

    if r.capex is not None and r.revenueTTM and r.revenueTTM > 0:
        r.capexRatio = _safeRound((abs(r.capex) / r.revenueTTM) * 100, 2)

    if r.dividendsPaid is not None and r.netIncomeTTM and r.netIncomeTTM > 0:
        r.dividendPayoutRatio = _safeRound((abs(r.dividendsPaid) / r.netIncomeTTM) * 100, 2)

    # FCF/OCF비율: FCF가 영업CF의 몇 %인지 (CAPEX 부담 측정)
    if r.fcf is not None and r.operatingCashflowTTM and r.operatingCashflowTTM > 0:
        r.fcfToOcfRatio = _safeRound((r.fcf / r.operatingCashflowTTM) * 100, 2)

    r.revenueGrowth3Y = getRevenueGrowth3Y(series)


def _calcComposite(
    r: RatioResult,
    series: dict[str, dict[str, list[float | None]]],
    maxTrailingNones: int | None = None,
) -> None:
    """복합 지표 orchestrator — 각 블록은 별도 함수로 분리 (Q3.1).

    ROIC / DuPont / Debt/EBITDA / CCC / Piotroski / Altman Z / Sloan /
    Altman Z'' / Springate / Zmijewski.
    """
    _calcRoic(r, series, maxTrailingNones)
    _calcDupont(r)
    _calcDebtToEbitda(r)
    _calcCCC(r)
    _calcPiotroski(r, series)
    _calcAltmanZ(r)
    _calcSloanAccrual(r)
    _calcAltmanZpp(r)
    _calcSpringate(r)
    _calcZmijewski(r)


def _calcRoic(
    r: RatioResult,
    series: dict[str, dict[str, list[float | None]]],
    maxTrailingNones: int | None,
) -> None:
    """ROIC = NOPAT / Invested Capital. 유효세율은 동적, 불가능하면 22%."""
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


def _calcDupont(r: RatioResult) -> None:
    """DuPont 3분해: ROE = Margin × Turnover × Leverage."""
    r.dupontMargin = _safePct(r.netIncomeTTM, r.revenueTTM)
    r.dupontTurnover = _safeRound(_safeDiv(r.revenueTTM, r.totalAssets), 2)
    if r.totalAssets and r.totalEquity and r.totalEquity > 0:
        r.dupontLeverage = _safeRound(r.totalAssets / r.totalEquity, 2)


def _calcDebtToEbitda(r: RatioResult) -> None:
    """Debt / EBITDA. 차입금 구성과 보고된 감가상각비가 모두 필요하다."""
    totalBorrowings = _sumComplete(r.shortTermBorrowings, r.longTermBorrowings, r.bonds)
    ebitda = _calcEbitdaValue(r.operatingIncomeTTM, r.depreciationExpense)
    if totalBorrowings is None or ebitda is None or ebitda <= 0:
        return
    r.debtToEbitda = _safeRound(totalBorrowings / ebitda, 2)


def _calcCCC(r: RatioResult) -> None:
    """Cash Conversion Cycle + 영업순환주기."""
    if r.revenueTTM and r.revenueTTM > 0:
        # 존재 여부로 본다. 매출채권이나 재고가 0 인 것은 값이 없는 것이 아니라
        # 0 일이라는 값이다. 진리값으로 보면 재고를 거의 두지 않는 회사가 전부
        # 미산출로 떨어지고, 그러면 CCC 자체가 사라진다.
        if r.receivables is not None:
            r.dso = _safeRound(r.receivables / r.revenueTTM * 365, 1)
        cos = r.costOfSales or r.revenueTTM
        if r.inventories is not None and cos > 0:
            r.dio = _safeRound(r.inventories / cos * 365, 1)
        if r.payables is not None and cos > 0:
            r.dpo = _safeRound(r.payables / cos * 365, 1)
        if r.dso is not None and r.dio is not None and r.dpo is not None:
            r.ccc = _safeRound(r.dso + r.dio - r.dpo, 1)
    if r.dso is not None and r.dio is not None:
        r.operatingCycle = _safeRound(r.dso + r.dio, 1)


def _piotroskiTimeSeries(
    series: dict[str, dict[str, list[float | None]]],
) -> dict[str, list[float | None]]:
    """Piotroski 시계열 추출 — 전기 비교용."""
    npSeries = _pickSeries(series, "IS", ["net_profit", "net_income"])
    taSeries = _get(series, "BS", "total_assets")
    tlSeries = _get(series, "BS", "total_liabilities")
    teSeries = _get(series, "BS", "total_stockholders_equity")
    if not any(v is not None for v in teSeries):
        teSeries = _get(series, "BS", "owners_of_parent_equity")
    caSeries = _get(series, "BS", "current_assets")
    clSeries = _get(series, "BS", "current_liabilities")
    issuedCapital = _get(series, "BS", "issued_capital")
    if not any(v is not None for v in issuedCapital):
        issuedCapital = _get(series, "BS", "capital_stock")
    gpSeries = _get(series, "IS", "gross_profit")
    revSeries = _pickSeries(series, "IS", ["sales", "revenue"])
    return {
        "np": npSeries,
        "ta": taSeries,
        "tl": tlSeries,
        "te": teSeries,
        "ca": caSeries,
        "cl": clSeries,
        "cap": issuedCapital,
        "gp": gpSeries,
        "rev": revSeries,
    }


def _piotroskiImprovement(cur: list, prev: list, metric: str, increasing: bool) -> int:
    """시계열 2기 ratio 개선 여부 판정. 1점 or 0점.

    metric: 명목상 용도 식별자 (디버그용). increasing=True 면 cur>prev 일 때 1점.
    """
    _ = metric
    if len(cur) < 2 or len(prev) < 2:
        return -1  # 계산 불가
    a = _safeDiv(cur[-1], prev[-1])
    b = _safeDiv(cur[-2], prev[-2])
    if a is None or b is None:
        return -1
    return 1 if (a > b if increasing else a < b) else 0


def _calcPiotroski(
    r: RatioResult,
    series: dict[str, dict[str, list[float | None]]],
) -> None:
    """Piotroski F-Score (9점 만점).

    아홉 신호 중 하나라도 계산할 수 없으면 부분 점수를 완전한 F-Score처럼
    노출하지 않는다.
    """
    ts = _piotroskiTimeSeries(series)
    roaImp = _piotroskiImprovement(ts["np"], ts["ta"], "ROA", increasing=True)
    drImp = _piotroskiImprovement(ts["tl"], ts["te"], "DR", increasing=False)
    crImp = _piotroskiImprovement(ts["ca"], ts["cl"], "CR", increasing=True)
    gmImp = _piotroskiImprovement(ts["gp"], ts["rev"], "GM", increasing=True)
    tatImp = _piotroskiImprovement(ts["rev"], ts["ta"], "TAT", increasing=True)
    if (
        r.roa is None
        or r.operatingCashflowTTM is None
        or r.netIncomeTTM is None
        or -1 in (roaImp, drImp, crImp, gmImp, tatImp)
        or len(ts["cap"]) < 2
        or ts["cap"][-1] is None
        or ts["cap"][-2] is None
    ):
        return

    r.piotroskiFScore = sum(
        (
            r.roa > 0,
            r.operatingCashflowTTM > 0,
            roaImp == 1,
            r.operatingCashflowTTM > r.netIncomeTTM,
            drImp == 1,
            crImp == 1,
            ts["cap"][-1] <= ts["cap"][-2],
            gmImp == 1,
            tatImp == 1,
        )
    )


def _calcAltmanZ(r: RatioResult) -> None:
    """Altman Z (1968 제조업 상장) or Z' (1983 비상장, 장부가).

    marketCap 유무로 분기. Z'': Z''-Score 함수 별도.
    """
    if not (
        r.totalAssets
        and r.totalAssets > 0
        and r.totalLiabilities
        and r.totalLiabilities > 0
        and r.currentAssets is not None
        and r.currentLiabilities is not None
        and r.retainedEarnings is not None
        and r.operatingIncomeTTM is not None
        and r.revenueTTM is not None
        and (r.marketCap is not None or r.totalEquity is not None)
    ):
        return
    wc = r.currentAssets - r.currentLiabilities
    a = wc / r.totalAssets
    b = r.retainedEarnings / r.totalAssets
    c = r.operatingIncomeTTM / r.totalAssets
    e = r.revenueTTM / r.totalAssets
    if r.marketCap is not None:
        d = r.marketCap / r.totalLiabilities
        z = 1.2 * a + 1.4 * b + 3.3 * c + 0.6 * d + 1.0 * e
        r.altmanZScore = _safeRound(z, 2)
    else:
        dPrime = r.totalEquity / r.totalLiabilities
        zPrime = 0.717 * a + 0.847 * b + 3.107 * c + 0.420 * dPrime + 0.998 * e
        r.altmanZScore = _safeRound(zPrime, 2)


def _calcSloanAccrual(r: RatioResult) -> None:
    """Sloan Accrual Ratio — (순이익 - 영업CF) / 총자산.

    높으면 발생주의 이익 비중 과다 (조작 의심).
    """
    if r.netIncomeTTM is not None and r.operatingCashflowTTM is not None and r.totalAssets and r.totalAssets > 0:
        accrual = r.netIncomeTTM - r.operatingCashflowTTM
        r.sloanAccrualRatio = _safeRound((accrual / r.totalAssets) * 100, 2)


def _calcAltmanZpp(r: RatioResult) -> None:
    """Altman Z'' (1995 비제조업/신흥시장). Sales/TA 제거 — 금융/서비스업도 적용."""
    if not (
        r.totalAssets
        and r.totalAssets > 0
        and r.totalLiabilities
        and r.totalLiabilities > 0
        and r.currentAssets is not None
        and r.currentLiabilities is not None
        and r.retainedEarnings is not None
        and r.operatingIncomeTTM is not None
        and r.totalEquity is not None
    ):
        return
    wc = r.currentAssets - r.currentLiabilities
    zpp = (
        6.56 * (wc / r.totalAssets)
        + 3.26 * (r.retainedEarnings / r.totalAssets)
        + 6.72 * (r.operatingIncomeTTM / r.totalAssets)
        + 1.05 * (r.totalEquity / r.totalLiabilities)
    )
    r.altmanZppScore = _safeRound(zpp, 2)


def _calcSpringate(r: RatioResult) -> None:
    """Springate S-Score (1978). S < 0.862 → 부실 위험."""
    if not (
        r.totalAssets
        and r.totalAssets > 0
        and r.currentLiabilities
        and r.currentLiabilities > 0
        and r.currentAssets is not None
        and r.operatingIncomeTTM is not None
        and r.profitBeforeTax is not None
        and r.revenueTTM is not None
    ):
        return
    wc = r.currentAssets - r.currentLiabilities
    s = (
        1.03 * (wc / r.totalAssets)
        + 3.07 * (r.operatingIncomeTTM / r.totalAssets)
        + 0.66 * (r.profitBeforeTax / r.currentLiabilities)
        + 0.40 * (r.revenueTTM / r.totalAssets)
    )
    r.springateSScore = _safeRound(s, 4)


def _calcZmijewski(r: RatioResult) -> None:
    """Zmijewski X-Score (1984) — 3변수 프로빗. X > 0 → 부실 위험."""
    if not (
        r.totalAssets
        and r.totalAssets > 0
        and r.totalLiabilities is not None
        and r.currentAssets is not None
        and r.currentLiabilities
        and r.currentLiabilities > 0
        and r.netIncomeTTM is not None
    ):
        return
    x = (
        -4.336
        - 4.513 * (r.netIncomeTTM / r.totalAssets)
        + 5.679 * (r.totalLiabilities / r.totalAssets)
        + 0.004 * (r.currentAssets / r.currentLiabilities)
    )
    r.zmijewskiXScore = _safeRound(x, 4)


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

    ebitda = _calcEbitdaValue(r.operatingIncomeTTM, r.depreciationExpense)
    if r.netDebt is not None and ebitda is not None and ebitda > 0:
        r.evEbitda = round((mc + r.netDebt) / ebitda, 2)


def _sv(lst: list, i: int) -> float | None:
    """시계열 리스트 i 번째 안전 조회 (범위 초과 시 None)."""
    return lst[i] if i < len(lst) else None


def _extractRatioSeriesInputs(
    annualSeries: dict[str, dict[str, list[float | None]]],
) -> dict[str, list]:
    """계산에 필요한 전체 시계열을 단일 dict 로 추출 — Q3.1c split 의 기준 입력."""
    totalEquity = _get(annualSeries, "BS", "total_stockholders_equity")
    if not any(v is not None for v in totalEquity):
        totalEquity = _get(annualSeries, "BS", "owners_of_parent_equity")
    ownersEquity = _get(annualSeries, "BS", "owners_of_parent_equity")
    if not any(v is not None for v in ownersEquity):
        ownersEquity = totalEquity
    depreciation = _get(annualSeries, "CF", "depreciation_and_amortization")
    if not any(v is not None for v in depreciation):
        depreciation = _get(annualSeries, "CF", "depreciation_cf")
    if not any(v is not None for v in depreciation):
        depreciation = _get(annualSeries, "CF", "depreciation")
    return {
        "revenue": _pickSeries(annualSeries, "IS", ["sales", "revenue"]),
        "costOfSales": _get(annualSeries, "IS", "cost_of_sales"),
        "grossProfit": _get(annualSeries, "IS", "gross_profit"),
        "opProfit": _pickSeries(annualSeries, "IS", ["operating_profit", "operating_income"]),
        "netProfit": _pickSeries(annualSeries, "IS", ["net_profit", "net_income"]),
        "sga": _get(annualSeries, "IS", "selling_and_administrative_expenses"),
        "finCosts": _pickSeries(annualSeries, "IS", ["finance_costs", "interest_expense"]),
        "totalAssets": _get(annualSeries, "BS", "total_assets"),
        "totalEquity": totalEquity,
        "ownersEquity": ownersEquity,
        "totalLiab": _get(annualSeries, "BS", "total_liabilities"),
        "curAssets": _get(annualSeries, "BS", "current_assets"),
        "curLiab": _get(annualSeries, "BS", "current_liabilities"),
        "cash": _get(annualSeries, "BS", "cash_and_cash_equivalents"),
        "inventories": _get(annualSeries, "BS", "inventories"),
        "receivables": _get(annualSeries, "BS", "trade_and_other_receivables"),
        "payables": _get(annualSeries, "BS", "trade_and_other_payables"),
        "tangible": _get(annualSeries, "BS", "tangible_assets"),
        "intangible": _get(annualSeries, "BS", "intangible_assets"),
        "stBorrow": _get(annualSeries, "BS", "shortterm_borrowings"),
        "ltBorrow": _get(annualSeries, "BS", "longterm_borrowings"),
        "bonds": _get(annualSeries, "BS", "debentures"),
        "ncAssets": _get(annualSeries, "BS", "noncurrent_assets"),
        "profitBeforeTax": _get(annualSeries, "IS", "profit_before_tax"),
        "incomeTaxExpense": (
            _get(annualSeries, "IS", "income_tax_expense") or _get(annualSeries, "IS", "income_taxes")
        ),
        "opCf": _get(annualSeries, "CF", "operating_cashflow"),
        "capex": _get(annualSeries, "CF", "purchase_of_property_plant_and_equipment"),
        "divPaid": _get(annualSeries, "CF", "dividends_paid"),
        "depreciation": depreciation,
    }


def _appendBasicAndProfitability(rs: RatioSeriesResult, i: int, S: dict[str, list]) -> None:
    """기본 6개 + 수익성 13개 (ROE/ROA/ROCE, margin, costRatio, 유효세율, 이익품질, EBITDA)."""
    rev_i = _sv(S["revenue"], i)
    cos_i = _sv(S["costOfSales"], i)
    gp_i = _sv(S["grossProfit"], i)
    op_i = _sv(S["opProfit"], i)
    np_i = _sv(S["netProfit"], i)
    sga_i = _sv(S["sga"], i)
    ta_i = _sv(S["totalAssets"], i)
    te_i = _sv(S["totalEquity"], i)
    oe_i = _sv(S["ownersEquity"], i)
    cl_i = _sv(S["curLiab"], i)
    opcf_i = _sv(S["opCf"], i)
    rs.revenue.append(rev_i)
    rs.operatingProfit.append(op_i)
    rs.netProfit.append(np_i)
    rs.totalAssets.append(ta_i)
    rs.totalEquity.append(te_i)
    rs.operatingCashflow.append(opcf_i)

    rs.roe.append(_safePctPositive(np_i, oe_i))
    rs.roa.append(_safePctPositive(np_i, ta_i))

    if op_i is not None and ta_i and cl_i is not None:
        ce_i = ta_i - cl_i
        rs.roce.append(_safeRound((op_i / ce_i) * 100, 2) if ce_i > 0 else None)
    else:
        rs.roce.append(None)

    rs.operatingMargin.append(_safePct(op_i, rev_i))
    rs.netMargin.append(_safePct(np_i, rev_i))

    pbt_i = _sv(S["profitBeforeTax"], i)
    rs.preTaxMargin.append(_safePct(pbt_i, rev_i))

    rs.grossMargin.append(_safePct(gp_i, rev_i))
    rs.costOfSalesRatio.append(_safePct(cos_i, rev_i))
    rs.sgaRatio.append(_safePct(sga_i, rev_i))

    tax_i = _sv(S["incomeTaxExpense"], i)
    if pbt_i and pbt_i > 0 and tax_i is not None:
        et_rate = tax_i / pbt_i
        rs.effectiveTaxRate.append(_safeRound(et_rate * 100, 2) if 0 <= et_rate <= 1 else None)
    else:
        rs.effectiveTaxRate.append(None)

    if opcf_i is not None and np_i and np_i > 0:
        rs.incomeQualityRatio.append(_safeRound((opcf_i / np_i) * 100, 2))
    else:
        rs.incomeQualityRatio.append(None)

    ebitda = _calcEbitdaValue(op_i, _sv(S["depreciation"], i))
    rs.ebitdaMargin.append(_safePct(ebitda, rev_i))


def _appendStability(rs: RatioSeriesResult, i: int, S: dict[str, list]) -> None:
    """안정성 9개 (debt, current, quick, cash, equity, interestCov, netDebt, noncurrent, workingCapital)."""
    tl_i = _sv(S["totalLiab"], i)
    te_i = _sv(S["totalEquity"], i)
    ta_i = _sv(S["totalAssets"], i)
    ca_i = _sv(S["curAssets"], i)
    cl_i = _sv(S["curLiab"], i)
    cash_i = _sv(S["cash"], i)
    inv_i = _sv(S["inventories"], i)
    nca_i = _sv(S["ncAssets"], i)
    op_i = _sv(S["opProfit"], i)
    fc_i = _sv(S["finCosts"], i)
    stb_i = _sv(S["stBorrow"], i)
    ltb_i = _sv(S["ltBorrow"], i)
    bnd_i = _sv(S["bonds"], i)

    rs.debtRatio.append(_safePctPositive(tl_i, te_i))
    rs.currentRatio.append(_safePct(ca_i, cl_i))

    if ca_i is not None and inv_i is not None and cl_i and cl_i > 0:
        rs.quickRatio.append(_safeRound(((ca_i - inv_i) / cl_i) * 100, 2))
    else:
        rs.quickRatio.append(None)

    rs.cashRatio.append(_safePct(cash_i, cl_i))
    rs.equityRatio.append(_safePctPositive(te_i, ta_i))

    if op_i is not None and fc_i and fc_i > 0:
        rs.interestCoverage.append(_safeRound(op_i / fc_i, 2))
    else:
        rs.interestCoverage.append(None)

    netDebt = _calcNetDebt(stb_i, ltb_i, bnd_i, cash_i)
    rs.netDebtRatio.append(_safePctPositive(netDebt, te_i))

    if nca_i is not None and te_i and te_i > 0:
        rs.noncurrentRatio.append(_safeRound((nca_i / te_i) * 100, 2))
    else:
        rs.noncurrentRatio.append(None)

    if ca_i is not None and cl_i is not None:
        rs.workingCapital.append(ca_i - cl_i)
    else:
        rs.workingCapital.append(None)


def _appendGrowth(rs: RatioSeriesResult, i: int, S: dict[str, list], yoyLag: int) -> None:
    """성장성 YoY 5개."""
    rs.revenueGrowth.append(_yoy(S["revenue"], i, yoyLag) if len(S["revenue"]) > i else None)
    rs.operatingProfitGrowth.append(_yoy(S["opProfit"], i, yoyLag) if len(S["opProfit"]) > i else None)
    rs.netProfitGrowth.append(_yoy(S["netProfit"], i, yoyLag) if len(S["netProfit"]) > i else None)
    rs.assetGrowth.append(_yoy(S["totalAssets"], i, yoyLag) if len(S["totalAssets"]) > i else None)
    rs.equityGrowthRate.append(_yoy(S["totalEquity"], i, yoyLag) if len(S["totalEquity"]) > i else None)


def _appendEfficiency(rs: RatioSeriesResult, i: int, S: dict[str, list]) -> None:
    """회전율 5개 (총자산/고정자산/재고/매출채권/매입채무)."""
    rev_i = _sv(S["revenue"], i)
    cos_i = _sv(S["costOfSales"], i)
    ta_i = _sv(S["totalAssets"], i)
    tan_i = _sv(S["tangible"], i)
    inv_i = _sv(S["inventories"], i)
    rec_i = _sv(S["receivables"], i)
    pay_i = _sv(S["payables"], i)

    rs.totalAssetTurnover.append(_safeRound(_safeDiv(rev_i, ta_i), 2))
    rs.fixedAssetTurnover.append(_safeRound(_safeDiv(rev_i, tan_i), 2))
    rs.inventoryTurnover.append(_safeRound(_safeDiv(rev_i, inv_i), 2))
    rs.receivablesTurnover.append(_safeRound(_safeDiv(rev_i, rec_i), 2))
    rs.payablesTurnover.append(_safeRound(_safeDiv(cos_i, pay_i), 2))


def _appendCashflow(rs: RatioSeriesResult, i: int, S: dict[str, list]) -> None:
    """현금흐름 7개 (FCF, 영업CF margin/to NI/to CL, capex/매출, 배당성향, FCF/OCF)."""
    rev_i = _sv(S["revenue"], i)
    np_i = _sv(S["netProfit"], i)
    cl_i = _sv(S["curLiab"], i)
    opcf_i = _sv(S["opCf"], i)
    cap_i = _sv(S["capex"], i)
    div_i = _sv(S["divPaid"], i)

    fcf_i: float | None
    if opcf_i is not None and cap_i is not None:
        fcf_i = opcf_i - abs(cap_i)
    else:
        fcf_i = None
    rs.fcf.append(fcf_i)

    rs.operatingCfMargin.append(_safePct(opcf_i, rev_i))
    rs.operatingCfToNetIncome.append(_safePctPositive(opcf_i, np_i))
    rs.operatingCfToCurrentLiab.append(_safePct(opcf_i, cl_i))

    if cap_i is not None and rev_i and rev_i > 0:
        rs.capexRatio.append(_safeRound((abs(cap_i) / rev_i) * 100, 2))
    else:
        rs.capexRatio.append(None)

    if div_i is not None and np_i and np_i > 0:
        rs.dividendPayoutRatio.append(_safeRound((abs(div_i) / np_i) * 100, 2))
    else:
        rs.dividendPayoutRatio.append(None)

    if fcf_i is not None and opcf_i and opcf_i > 0:
        rs.fcfToOcfRatio.append(_safeRound((fcf_i / opcf_i) * 100, 2))
    else:
        rs.fcfToOcfRatio.append(None)


def _piotroskiSeriesImproved(series: list, prevSeries: list, i: int, yoyLag: int, increasing: bool) -> int:
    """Piotroski 전기 대비 ratio 개선 여부 판정.

    리턴: 1=개선, 0=악화/동일, -1=계산불가 (fallback 판정에 활용).
    """
    if i < yoyLag:
        return -1
    a_now = _sv(series, i)
    b_now = _sv(prevSeries, i)
    a_prev = _sv(series, i - yoyLag)
    b_prev = _sv(prevSeries, i - yoyLag)
    cur = _safeDiv(a_now, b_now)
    prev = _safeDiv(a_prev, b_prev)
    if cur is None or prev is None:
        return -1
    return 1 if (cur > prev if increasing else cur < prev) else 0


def _piotroskiProfitPoints(i: int, S: dict[str, list], yoyLag: int) -> int | None:
    """Piotroski 1~4: ROA>0, OCF>0, ROA 개선, OCF>NI."""
    np_i = _sv(S["netProfit"], i)
    ta_i = _sv(S["totalAssets"], i)
    opcf_i = _sv(S["opCf"], i)
    roaImp = _piotroskiSeriesImproved(S["netProfit"], S["totalAssets"], i, yoyLag, increasing=True)
    if np_i is None or not ta_i or ta_i <= 0 or opcf_i is None or roaImp == -1:
        return None
    score = 0
    if np_i / ta_i > 0:
        score += 1
    if opcf_i > 0:
        score += 1
    if roaImp == 1:
        score += 1
    if opcf_i > np_i:
        score += 1
    return score


def _piotroskiLeveragePoints(i: int, S: dict[str, list], yoyLag: int) -> int | None:
    """Piotroski 5~6: 부채비율 감소, 유동비율 개선."""
    drImp = _piotroskiSeriesImproved(S["totalLiab"], S["totalEquity"], i, yoyLag, increasing=False)
    crImp = _piotroskiSeriesImproved(S["curAssets"], S["curLiab"], i, yoyLag, increasing=True)
    if drImp == -1 or crImp == -1:
        return None
    return (1 if drImp == 1 else 0) + (1 if crImp == 1 else 0)


def _piotroskiShareIssuePoint(i: int, yoyLag: int, annualSeries: dict) -> int | None:
    """Piotroski 7: 신주 미발행 (자본금 감소 or 동일)."""
    issuedCap = _get(annualSeries, "BS", "issued_capital")
    if not any(v is not None for v in issuedCap):
        issuedCap = _get(annualSeries, "BS", "capital_stock")
    if i < yoyLag or i >= len(issuedCap) or (i - yoyLag) >= len(issuedCap):
        return None
    cur_cap_i = issuedCap[i]
    prev_cap_i = issuedCap[i - yoyLag]
    if cur_cap_i is None or prev_cap_i is None:
        return None
    return 1 if cur_cap_i <= prev_cap_i else 0


def _piotroskiEfficiencyPoints(i: int, S: dict[str, list], yoyLag: int) -> int | None:
    """Piotroski 8~9: 매출총이익률 개선, 총자산회전율 개선."""
    gmImp = _piotroskiSeriesImproved(S["grossProfit"], S["revenue"], i, yoyLag, increasing=True)
    tatImp = _piotroskiSeriesImproved(S["revenue"], S["totalAssets"], i, yoyLag, increasing=True)
    if gmImp == -1 or tatImp == -1:
        return None
    return (1 if gmImp == 1 else 0) + (1 if tatImp == 1 else 0)


def _piotroskiScoreSeries(i: int, S: dict[str, list], yoyLag: int, annualSeries: dict) -> int | None:
    """calcRatioSeries 의 Piotroski F-Score (9점 만점) — 4 sub 합산."""
    parts = (
        _piotroskiProfitPoints(i, S, yoyLag),
        _piotroskiLeveragePoints(i, S, yoyLag),
        _piotroskiShareIssuePoint(i, yoyLag, annualSeries),
        _piotroskiEfficiencyPoints(i, S, yoyLag),
    )
    if any(part is None for part in parts):
        return None
    return sum(parts)


def _appendRoicDupontDebt(rs: RatioSeriesResult, i: int, S: dict[str, list]) -> None:
    """ROIC + DuPont 3분해 + Debt/EBITDA."""
    rev_i = _sv(S["revenue"], i)
    op_i = _sv(S["opProfit"], i)
    np_i = _sv(S["netProfit"], i)
    ta_i = _sv(S["totalAssets"], i)
    te_i = _sv(S["totalEquity"], i)
    cash_i = _sv(S["cash"], i)
    stb_i = _sv(S["stBorrow"], i)
    ltb_i = _sv(S["ltBorrow"], i)
    bnd_i = _sv(S["bonds"], i)

    # ROIC
    pbt_i = _sv(S["profitBeforeTax"], i)
    tax_i = _sv(S["incomeTaxExpense"], i)
    et_i = 0.22
    if pbt_i and pbt_i > 0 and tax_i is not None:
        _et_i = tax_i / pbt_i
        if 0 <= _et_i <= 0.5:
            et_i = _et_i
    nopat_i = op_i * (1 - et_i) if op_i is not None else None
    netDebt_i = _calcNetDebt(stb_i, ltb_i, bnd_i, cash_i)
    invested_i = te_i + max(netDebt_i, 0) if te_i is not None and netDebt_i is not None else None
    rs.roic.append(_safePctPositive(nopat_i, invested_i))

    # DuPont
    rs.dupontMargin.append(_safePct(np_i, rev_i))
    rs.dupontTurnover.append(_safeRound(_safeDiv(rev_i, ta_i), 2))
    rs.dupontLeverage.append(_safeRound(_safeDiv(ta_i, te_i), 2) if te_i and te_i > 0 else None)

    # Debt/EBITDA
    ebitda_i = _calcEbitdaValue(op_i, _sv(S["depreciation"], i))
    totalBorrowings_i = _sumComplete(stb_i, ltb_i, bnd_i)
    if ebitda_i is not None and ebitda_i > 0 and totalBorrowings_i is not None:
        rs.debtToEbitda.append(_safeRound(totalBorrowings_i / ebitda_i, 2))
    else:
        rs.debtToEbitda.append(None)


def _appendCCC(rs: RatioSeriesResult, i: int, S: dict[str, list]) -> None:
    """CCC + DSO/DIO/DPO + 영업순환주기."""
    rev_i = _sv(S["revenue"], i)
    cos_i = _sv(S["costOfSales"], i)
    inv_i = _sv(S["inventories"], i)
    rec_i = _sv(S["receivables"], i)
    pay_i = _sv(S["payables"], i)

    cos_for_days = cos_i if cos_i and cos_i > 0 else rev_i
    hasCos = cos_for_days is not None and cos_for_days > 0
    dso_i = _safeRound(rec_i / rev_i * 365, 1) if rec_i is not None and rev_i and rev_i > 0 else None
    dio_i = _safeRound(inv_i / cos_for_days * 365, 1) if inv_i is not None and hasCos else None
    dpo_i = _safeRound(pay_i / cos_for_days * 365, 1) if pay_i is not None and hasCos else None
    rs.dso.append(dso_i)
    rs.dio.append(dio_i)
    rs.dpo.append(dpo_i)
    # 진리값이 아니라 존재 여부로 본다. 재고가 거의 없는 회사는 dio 가 0.0 으로
    # 떨어지는데, 그것은 값이 없는 것이 아니라 0 일이라는 값이다. 바로 아래
    # operatingCycle 은 이미 `is not None` 이라 같은 회사에서 두 지표의 판정이
    # 엇갈렸고, 시점 경로의 CCC 와도 답이 달랐다.
    hasCycleParts = dso_i is not None and dio_i is not None and dpo_i is not None
    rs.ccc.append(_safeRound(dso_i + dio_i - dpo_i, 1) if hasCycleParts else None)
    rs.operatingCycle.append(_safeRound(dso_i + dio_i, 1) if dso_i is not None and dio_i is not None else None)


def _appendAltmanSloan(rs: RatioSeriesResult, i: int, S: dict[str, list], annualSeries: dict) -> None:
    """Altman Z' (비상장, 시계열에 marketCap 없음) + Sloan Accrual Ratio."""
    rev_i = _sv(S["revenue"], i)
    op_i = _sv(S["opProfit"], i)
    np_i = _sv(S["netProfit"], i)
    ta_i = _sv(S["totalAssets"], i)
    te_i = _sv(S["totalEquity"], i)
    tl_i = _sv(S["totalLiab"], i)
    ca_i = _sv(S["curAssets"], i)
    cl_i = _sv(S["curLiab"], i)
    opcf_i = _sv(S["opCf"], i)

    re_i = _sv(_get(annualSeries, "BS", "retained_earnings"), i)
    if (
        ta_i
        and ta_i > 0
        and tl_i
        and tl_i > 0
        and ca_i is not None
        and cl_i is not None
        and re_i is not None
        and op_i is not None
        and te_i is not None
        and rev_i is not None
    ):
        wc_i = ca_i - cl_i
        dPrime = te_i / tl_i
        zPrime = (
            0.717 * (wc_i / ta_i)
            + 0.847 * (re_i / ta_i)
            + 3.107 * (op_i / ta_i)
            + 0.420 * dPrime
            + 0.998 * (rev_i / ta_i)
        )
        rs.altmanZScore.append(_safeRound(zPrime, 2))
    else:
        rs.altmanZScore.append(None)

    if np_i is not None and opcf_i is not None and ta_i and ta_i > 0:
        rs.sloanAccrualRatio.append(_safeRound((np_i - opcf_i) / ta_i * 100, 2))
    else:
        rs.sloanAccrualRatio.append(None)


def _appendComposite(
    rs: RatioSeriesResult,
    i: int,
    S: dict[str, list],
    yoyLag: int,
    annualSeries: dict,
) -> None:
    """복합 지표 orchestrator — 5 sub 로 분할."""
    _appendRoicDupontDebt(rs, i, S)
    _appendCCC(rs, i, S)
    rs.piotroskiFScore.append(_piotroskiScoreSeries(i, S, yoyLag, annualSeries))
    _appendAltmanSloan(rs, i, S, annualSeries)
    # 공용 다공급자 입력으로는 원식의 Beneish 계정을 보장할 수 없다.
    rs.beneishMScore.append(None)


def calcRatioSeries(
    annualSeries: dict[str, dict[str, list[float | None]]],
    years: list[str],
    archetypeOverride: str | None = None,
    yoyLag: int = 1,
) -> RatioSeriesResult:
    """재무비율 시계열 계산 (연간 또는 분기).

    Q3.1c split: 6 category sub-function 으로 분해. 각 기간별로 6 호출.

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
    S = _extractRatioSeriesInputs(annualSeries)

    for i in range(n):
        _appendBasicAndProfitability(rs, i, S)
        _appendStability(rs, i, S)
        _appendGrowth(rs, i, S, yoyLag)
        _appendEfficiency(rs, i, S)
        _appendCashflow(rs, i, S)
        _appendComposite(rs, i, S, yoyLag, annualSeries)

    _applyArchetypePolicySeries(rs, archetype)
    return rs


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
