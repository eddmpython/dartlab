"""DART와 EDGAR가 공유하는 단일 시점 재무비율 계산기."""

from __future__ import annotations

from dartlab.core.ratios.common import (
    _applyArchetypePolicyResult,
    _averageLatest,
    _calcEbitdaValue,
    _calcNetDebt,
    _detectArchetype,
    _get,
    _pickFirst,
    _pickSeries,
    _resolveArchetype,
    _safeDiv,
    _safePct,
    _safePctPositive,
    _safeRound,
    _sumComplete,
    _yoy,
)
from dartlab.core.ratios.market import _calcPerShare, _calcValuation
from dartlab.core.ratios.models import RatioResult
from dartlab.core.utils.extract import getLatest, getRevenueGrowth3Y, getTTM


def calcRatios(
    series: dict[str, dict[str, list[float | None]]],
    *,
    annual: bool,
    marketCap: float | None = None,
    archetypeOverride: str | None = None,
    shares: int | None = None,
    currency: str = "KRW",
    yoyLag: int | None = None,
) -> RatioResult:
    """시계열 → 재무비율 단일 시점 계산 . DART/EDGAR 공통 백엔드.

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
        부적용 ratio 자동 None 처리 . ``_applyArchetypePolicyResult``.

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
        yoyLag: 성장률과 Piotroski 비교 간격. None이면 annual=True는 1,
            annual=False는 4를 사용한다.

    Returns:
        RatioResult . dataclass with 60+ float|None fields + ``currency`` / ``warnings``.
        Archetype 부적용 field 는 None.

    Raises:
        ValueError: archetypeOverride가 지원하지 않는 값인 경우.
        데이터 결측은 None으로 보존한다.

    Example:
        >>> series, _ = buildTimeseries("005930")
        >>> r = calcRatios(series, annual=False, marketCap=400e12, shares=5969782550)
        >>> r.roe, r.debtRatio
        (..., ...)

    SeeAlso:
        - ``RatioResult`` . dataclass 출력 schema.
        - ``calcRatioSeries`` . 시계열 전체 반환 (본 함수 N 회 호출).
        - ``_detectArchetype`` . archetype 자동 감지 룰.
        - ``_applyArchetypePolicyResult`` . archetype 별 N/A 처리.
        - ``_calcProfitability`` / ``_calcStability`` / ``_calcEfficiency`` / ``_calcCashflow``
          / ``_calcComposite`` / ``_calcPiotroski`` / ``_calcAltmanZ`` 등 helper.
        - ``getTTM`` / ``getLatest`` . flow vs stock 추출 헬퍼.

    Requires:
        - dataclasses (RatioResult)
        - dartlab.analysis.financial._constants (임계값 / archetype 룰)

    Capabilities:
        - DART KR + EDGAR US 공통 재무비율 60+ 계산 백엔드.
        - Archetype-aware . 업종별 부적용 ratio 자동 None.
        - TTM / Annual mode 양방향 . 분기 시계열 + 연간 시계열 모두.
        - Composite score (Piotroski/Altman/Springate/Zmijewski/Sloan) 5+ 종.

    Guide:
        - 사용자 API 는 ``c.panel("ratios")`` . 본 함수는 backend.
        - 다종목 batch 발굴 시 ``scanRatio("roe").sort(...).head(N)`` 가 빠름 (parquet vectorized).
        - 단일 종목 deep dive 시 ``c.panel("ratios")`` (본 함수 결과) 60+ field 전부 access.

    AIContext:
        Ask Workbench finance core . ``c.panel("ratios")`` 호출 시 backend. archetype 처리로
        은행/보험/지주 회사에서 부적절 ratio (제조업 기준 OPM 등) 자동 마스킹.

    LLM Specifications:
        AntiPatterns:
            - 본 함수 직접 호출 X . ``c.panel("ratios")`` 위임.
            - ``annual=False`` 인데 분기 시계열이 4 분기 미만 → TTM 계산 불가 → None.
            - ``archetypeOverride`` 강제 후 결과 신뢰 X . 자동 감지 우선, override 는 예외.
            - 다종목 발굴에 본 함수 N 회 X . ``scanRatio`` (vectorized parquet) 사용.
            - currency 누락 → "KRW" default, US 종목 호출 시 잘못된 grading 분기.
        OutputSchema:
            - RatioResult dataclass . 60+ ``float|None`` field
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
            - marketCap 은 일 단위 갱신 . caller 가 trade date 명시.
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
            - KR (DART) . 제조/금융/보험/지주/리츠 전체.
            - US (SEC EDGAR) . us-gaap 정규화 시 동일 함수 호출 가능 (currency="USD").
    """
    r = RatioResult()
    r.currency = currency
    archetype = _resolveArchetype(series, archetypeOverride)
    if yoyLag is None:
        yoyLag = 1 if annual else 4
    if isinstance(yoyLag, bool) or not isinstance(yoyLag, int) or yoyLag <= 0:
        raise ValueError("yoyLag must be a positive integer")

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
    r.totalEquity = _pickFirst(
        series,
        "BS",
        ["total_stockholders_equity", "owners_of_parent_equity"],
        annual=True,
    )
    r.ownersEquity = _pickFirst(
        series,
        "BS",
        ["owners_of_parent_equity", "total_stockholders_equity"],
        annual=True,
    )
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

    balanceLag = 1 if annual else 4
    r._averageTotalAssets = _averageLatest(series, "BS", ["total_assets"], balanceLag)
    r._averageTotalEquity = _averageLatest(
        series,
        "BS",
        ["total_stockholders_equity", "owners_of_parent_equity"],
        balanceLag,
    )
    r._averageOwnersEquity = _averageLatest(
        series,
        "BS",
        ["owners_of_parent_equity", "total_stockholders_equity"],
        balanceLag,
    )
    r._averageCurrentLiabilities = _averageLatest(series, "BS", ["current_liabilities"], balanceLag)
    r._averageTangibleAssets = _averageLatest(series, "BS", ["tangible_assets"], balanceLag)
    r._averageInventories = _averageLatest(series, "BS", ["inventories"], balanceLag)
    r._averageReceivables = _averageLatest(series, "BS", ["trade_and_other_receivables"], balanceLag)
    r._averagePayables = _averageLatest(series, "BS", ["trade_and_other_payables"], balanceLag)
    averageShortDebt = _averageLatest(series, "BS", ["shortterm_borrowings"], balanceLag)
    averageLongDebt = _averageLatest(series, "BS", ["longterm_borrowings"], balanceLag)
    averageBonds = _averageLatest(series, "BS", ["debentures"], balanceLag)
    averageCash = _averageLatest(series, "BS", ["cash_and_cash_equivalents"], balanceLag)
    r._averageNetDebt = _calcNetDebt(averageShortDebt, averageLongDebt, averageBonds, averageCash)

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
    _calcGrowth(r, series, yoyLag)
    _calcEfficiency(r)
    _calcCashflow(r, series, annual)
    _calcComposite(r, series, yoyLag)

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
    cfNetIncome = _pickFirst(
        series,
        "CF",
        ["net_income", "net_profit"],
        annual=annual,
        maxTrailingNones=ttmMaxTrailingNones,
    )
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
    ownersEquity = r._averageOwnersEquity if r._averageOwnersEquity is not None else r.ownersEquity
    totalAssets = r._averageTotalAssets if r._averageTotalAssets is not None else r.totalAssets
    currentLiabilities = (
        r._averageCurrentLiabilities if r._averageCurrentLiabilities is not None else r.currentLiabilities
    )
    r.roe = _safePctPositive(r.netIncomeTTM, ownersEquity)
    if r.roe is not None and not (-500 <= r.roe <= 500):
        r.warnings.append(f"ROE {r.roe:.0f}% 범위 초과")
        r.roe = None

    r.roa = _safePctPositive(r.netIncomeTTM, totalAssets)
    if r.roa is not None and not (-200 <= r.roa <= 200):
        r.warnings.append(f"ROA {r.roa:.0f}% 범위 초과")
        r.roa = None

    # ROCE: EBIT / Capital Employed (총자산 - 유동부채)
    if r.operatingIncomeTTM is not None and totalAssets and currentLiabilities is not None:
        capitalEmployed = totalAssets - currentLiabilities
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
    totalAssets = r._averageTotalAssets if r._averageTotalAssets is not None else r.totalAssets
    tangibleAssets = r._averageTangibleAssets if r._averageTangibleAssets is not None else r.tangibleAssets
    inventories = r._averageInventories if r._averageInventories is not None else r.inventories
    receivables = r._averageReceivables if r._averageReceivables is not None else r.receivables
    payables = r._averagePayables if r._averagePayables is not None else r.payables
    r.totalAssetTurnover = _safeRound(_safeDiv(r.revenueTTM, totalAssets), 2)
    r.fixedAssetTurnover = _safeRound(_safeDiv(r.revenueTTM, tangibleAssets), 2)
    r.inventoryTurnover = _safeRound(_safeDiv(r.revenueTTM, inventories), 2)
    r.receivablesTurnover = _safeRound(_safeDiv(r.revenueTTM, receivables), 2)

    if r.costOfSales is not None:
        r.payablesTurnover = _safeRound(_safeDiv(r.costOfSales, payables), 2)

    # 영업순환주기: DSO + DIO (CCC에서 DPO 빼기 전 . 매출+재고 회수에 걸리는 일수)
    # DSO/DIO는 _calcComposite에서 계산되므로 여기서는 placeholder만 설정


def _calcGrowth(
    r: RatioResult,
    series: dict[str, dict[str, list[float | None]]],
    yoyLag: int,
) -> None:
    """최신 기간 성장률을 입력 입도에 맞는 전년 기간과 비교한다."""
    fields = (
        ("revenueGrowth", _pickSeries(series, "IS", ["sales", "revenue"])),
        ("operatingProfitGrowth", _pickSeries(series, "IS", ["operating_profit", "operating_income"])),
        ("netProfitGrowth", _pickSeries(series, "IS", ["net_profit", "net_income"])),
        ("assetGrowth", _pickSeries(series, "BS", ["total_assets"])),
        (
            "equityGrowthRate",
            _pickSeries(series, "BS", ["total_stockholders_equity", "owners_of_parent_equity"]),
        ),
    )
    for fieldName, values in fields:
        value = _yoy(values, len(values) - 1, yoyLag) if values else None
        setattr(r, fieldName, value)


def _calcCashflow(
    r: RatioResult,
    series: dict[str, dict[str, list[float | None]]],
    annual: bool,
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

    r.revenueGrowth3Y = getRevenueGrowth3Y(series) if annual else None


def _calcComposite(
    r: RatioResult,
    series: dict[str, dict[str, list[float | None]]],
    yoyLag: int,
) -> None:
    """복합 지표 orchestrator . 각 블록은 별도 함수로 분리 (Q3.1).

    ROIC / DuPont / Debt/EBITDA / CCC / Piotroski / Altman Z / Sloan /
    Altman Z'' / Springate / Zmijewski.
    """
    _calcRoic(r)
    _calcDupont(r)
    _calcDebtToEbitda(r)
    _calcCCC(r)
    _calcPiotroski(r, series, yoyLag)
    _calcAltmanZ(r)
    _calcSloanAccrual(r)
    _calcAltmanZpp(r)
    _calcSpringate(r)
    _calcZmijewski(r)


def _calcRoic(r: RatioResult) -> None:
    """ROIC = NOPAT / Invested Capital. 유효세율은 동적, 불가능하면 22%."""
    effectiveTax = 0.22
    if r.effectiveTaxRate is not None and 0 <= r.effectiveTaxRate <= 50:
        effectiveTax = r.effectiveTaxRate / 100
    totalEquity = r._averageTotalEquity if r._averageTotalEquity is not None else r.totalEquity
    netDebt = r._averageNetDebt if r._averageNetDebt is not None else r.netDebt
    if r.operatingIncomeTTM is not None and totalEquity and netDebt is not None:
        nopat = r.operatingIncomeTTM * (1 - effectiveTax)
        invested = totalEquity + max(netDebt, 0)
        if invested > 0:
            r.roic = _safeRound((nopat / invested) * 100, 2)


def _calcDupont(r: RatioResult) -> None:
    """DuPont 3분해: ROE = Margin × Turnover × Leverage."""
    totalAssets = r._averageTotalAssets if r._averageTotalAssets is not None else r.totalAssets
    totalEquity = r._averageTotalEquity if r._averageTotalEquity is not None else r.totalEquity
    r.dupontMargin = _safePct(r.netIncomeTTM, r.revenueTTM)
    r.dupontTurnover = _safeRound(_safeDiv(r.revenueTTM, totalAssets), 2)
    if totalAssets and totalEquity and totalEquity > 0:
        r.dupontLeverage = _safeRound(totalAssets / totalEquity, 2)


def _calcDebtToEbitda(r: RatioResult) -> None:
    """Debt / EBITDA. 차입금 구성과 보고된 감가상각비가 모두 필요하다."""
    totalBorrowings = _sumComplete(r.shortTermBorrowings, r.longTermBorrowings, r.bonds)
    ebitda = _calcEbitdaValue(r.operatingIncomeTTM, r.depreciationExpense)
    if totalBorrowings is None or ebitda is None or ebitda <= 0:
        return
    r.debtToEbitda = _safeRound(totalBorrowings / ebitda, 2)


def _calcCCC(r: RatioResult) -> None:
    """Cash Conversion Cycle + 영업순환주기."""
    receivables = r._averageReceivables if r._averageReceivables is not None else r.receivables
    inventories = r._averageInventories if r._averageInventories is not None else r.inventories
    payables = r._averagePayables if r._averagePayables is not None else r.payables
    if r.revenueTTM and r.revenueTTM > 0:
        # 존재 여부로 본다. 매출채권이나 재고가 0 인 것은 값이 없는 것이 아니라
        # 0 일이라는 값이다. 진리값으로 보면 재고를 거의 두지 않는 회사가 전부
        # 미산출로 떨어지고, 그러면 CCC 자체가 사라진다.
        if receivables is not None:
            r.dso = _safeRound(receivables / r.revenueTTM * 365, 1)
        if inventories is not None and r.costOfSales is not None and r.costOfSales > 0:
            r.dio = _safeRound(inventories / r.costOfSales * 365, 1)
        if payables is not None and r.costOfSales is not None and r.costOfSales > 0:
            r.dpo = _safeRound(payables / r.costOfSales * 365, 1)
        if r.dso is not None and r.dio is not None and r.dpo is not None:
            r.ccc = _safeRound(r.dso + r.dio - r.dpo, 1)
    if r.dso is not None and r.dio is not None:
        r.operatingCycle = _safeRound(r.dso + r.dio, 1)


def _piotroskiTimeSeries(
    series: dict[str, dict[str, list[float | None]]],
) -> dict[str, list[float | None]]:
    """Piotroski 시계열 추출 . 전기 비교용."""
    npSeries = _pickSeries(series, "IS", ["net_profit", "net_income"])
    taSeries = _get(series, "BS", "total_assets")
    longTermBorrowings = _get(series, "BS", "longterm_borrowings")
    bonds = _get(series, "BS", "debentures")
    debtLength = max(len(longTermBorrowings), len(bonds))
    longTermDebt = [
        _sumComplete(
            longTermBorrowings[index] if index < len(longTermBorrowings) else None,
            bonds[index] if index < len(bonds) else None,
        )
        for index in range(debtLength)
    ]
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
        "ltd": longTermDebt,
        "ca": caSeries,
        "cl": clSeries,
        "cap": issuedCapital,
        "gp": gpSeries,
        "rev": revSeries,
    }


def _piotroskiImprovement(
    numerator: list[float | None],
    denominator: list[float | None],
    yoyLag: int,
    increasing: bool,
) -> int:
    """시계열 2기 ratio 개선 여부 판정. 1점 or 0점.

    increasing=True 면 현재 ratio가 전년 동기보다 클 때 1점.
    """
    if len(numerator) <= yoyLag or len(denominator) <= yoyLag:
        return -1
    current = _safeDiv(numerator[-1], denominator[-1])
    previous = _safeDiv(numerator[-1 - yoyLag], denominator[-1 - yoyLag])
    if current is None or previous is None:
        return -1
    return 1 if (current > previous if increasing else current < previous) else 0


def _calcPiotroski(
    r: RatioResult,
    series: dict[str, dict[str, list[float | None]]],
    yoyLag: int,
) -> None:
    """Piotroski F-Score (9점 만점).

    아홉 신호 중 하나라도 계산할 수 없으면 부분 점수를 완전한 F-Score처럼
    노출하지 않는다.
    """
    ts = _piotroskiTimeSeries(series)
    roaImp = _piotroskiImprovement(ts["np"], ts["ta"], yoyLag, increasing=True)
    drImp = _piotroskiImprovement(ts["ltd"], ts["ta"], yoyLag, increasing=False)
    crImp = _piotroskiImprovement(ts["ca"], ts["cl"], yoyLag, increasing=True)
    gmImp = _piotroskiImprovement(ts["gp"], ts["rev"], yoyLag, increasing=True)
    tatImp = _piotroskiImprovement(ts["rev"], ts["ta"], yoyLag, increasing=True)
    currentCapital = ts["cap"][-1] if ts["cap"] else None
    previousCapital = ts["cap"][-1 - yoyLag] if len(ts["cap"]) > yoyLag else None
    if (
        r.roa is None
        or r.operatingCashflowTTM is None
        or r.netIncomeTTM is None
        or -1 in (roaImp, drImp, crImp, gmImp, tatImp)
        or currentCapital is None
        or previousCapital is None
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
            currentCapital <= previousCapital,
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
        totalEquity = r.totalEquity
        if totalEquity is None:
            return
        dPrime = totalEquity / r.totalLiabilities
        zPrime = 0.717 * a + 0.847 * b + 3.107 * c + 0.420 * dPrime + 0.998 * e
        r.altmanZScore = _safeRound(zPrime, 2)


def _calcSloanAccrual(r: RatioResult) -> None:
    """Sloan Accrual Ratio . (순이익 - 영업CF) / 총자산.

    높으면 발생주의 이익 비중 과다 (조작 의심).
    """
    totalAssets = r._averageTotalAssets if r._averageTotalAssets is not None else r.totalAssets
    if r.netIncomeTTM is not None and r.operatingCashflowTTM is not None and totalAssets and totalAssets > 0:
        accrual = r.netIncomeTTM - r.operatingCashflowTTM
        r.sloanAccrualRatio = _safeRound((accrual / totalAssets) * 100, 2)


def _calcAltmanZpp(r: RatioResult) -> None:
    """Altman Z'' (1995 비제조업/신흥시장). Sales/TA 제거 . 금융/서비스업도 적용."""
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
    """Zmijewski X-Score (1984) . 3변수 프로빗. X > 0 → 부실 위험."""
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
