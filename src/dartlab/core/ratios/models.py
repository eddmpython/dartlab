"""재무비율 단일 시점과 시계열 결과 모델."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

from dartlab.core.htmlRenderer import getHtmlRenderer


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

    _averageTotalAssets: float | None = field(default=None, repr=False)
    _averageTotalEquity: float | None = field(default=None, repr=False)
    _averageOwnersEquity: float | None = field(default=None, repr=False)
    _averageCurrentLiabilities: float | None = field(default=None, repr=False)
    _averageTangibleAssets: float | None = field(default=None, repr=False)
    _averageInventories: float | None = field(default=None, repr=False)
    _averageReceivables: float | None = field(default=None, repr=False)
    _averagePayables: float | None = field(default=None, repr=False)
    _averageNetDebt: float | None = field(default=None, repr=False)

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
