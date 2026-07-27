"""proforma.py 깊이 — buildProforma + WACC + _fetchBeta 분리.

본체 proforma.py 에서 분리, BC re-export.
"""

from __future__ import annotations

import functools
from typing import TYPE_CHECKING

from dartlab.core.utils.extract import getLatest, getTTM

if TYPE_CHECKING:
    from dartlab.analysis.financial.proforma import (
        HistoricalRatios,
        ProformaFinancials,
        ProformaInput,
        ProFormaResult,
        ProformaResult,
        ProformaScenario,
        ProFormaYear,
    )
    from dartlab.synth.scenario import SectorElasticity


def __getattr__(name: str):
    if name in {
        "HistoricalRatios",
        "ProformaFinancials",
        "ProformaInput",
        "ProformaResult",
        "ProFormaResult",
        "ProFormaYear",
        "ProformaScenario",
    }:
        from dartlab.analysis.financial import proforma as _pf

        return getattr(_pf, name)
    raise AttributeError(f"module 'dartlab.analysis.financial._proformaCore' has no attribute {name!r}")


def extractHistoricalRatios(*args, **kwargs):
    """과거 비율 추출 — proforma.py 본체 위임 (cycle 회피 lazy proxy).

    Requires:
        dartlab.analysis.financial.proforma 본체 import 가능.

    Raises:
        proforma 본체가 던지는 예외 그대로 전파.

    Example:
        >>> extractHistoricalRatios(company)
        {...}
    """
    from dartlab.analysis.financial.proforma import extractHistoricalRatios as _f

    return _f(*args, **kwargs)


@functools.lru_cache(maxsize=128)
def _fetchBeta(stockCode: str, currency: str = "KRW") -> float | None:
    """1년 일별 수익률 vs 시장 지수 회귀로 Beta 산출.

    [성능] @lru_cache 적용 — review에서 6번 호출되는데 매번 외부 API.
    같은 stockCode 입력은 첫 호출 후 즉시 반환.
    """
    try:
        import httpx

        from dartlab.gather.infra.http import runAsync

        async def _calc():
            async with httpx.AsyncClient(timeout=15) as client:
                if currency == "KRW":
                    from dartlab.gather.domains.naver import fetchHistory

                    stockHist = await fetchHistory(stockCode, client, market="KR")
                    marketHist = await fetchHistory("KOSPI", client, market="KR")
                else:
                    return None

                if len(stockHist) < 250 or len(marketHist) < 250:
                    return None

                # 최근 1년(약 250 거래일)만 사용
                stockHist = stockHist[-260:]
                marketHist = marketHist[-260:]

                import polars as pl

                sdf = pl.DataFrame(stockHist).select(
                    pl.col("date").cast(pl.Date).alias("date"),
                    pl.col("close").cast(pl.Float64).alias("sc"),
                )
                mdf = pl.DataFrame(marketHist).select(
                    pl.col("date").cast(pl.Date).alias("date"),
                    pl.col("close").cast(pl.Float64).alias("mc"),
                )
                joined = sdf.join(mdf, on="date", how="inner").sort("date")
                if joined.height < 60:
                    return None

                joined = joined.with_columns(
                    (pl.col("sc") / pl.col("sc").shift(1) - 1).alias("sr"),
                    (pl.col("mc") / pl.col("mc").shift(1) - 1).alias("mr"),
                ).drop_nulls()

                if joined.height < 30:
                    return None

                sr = joined["sr"].to_numpy()
                mr = joined["mr"].to_numpy()
                cov = (sr * mr).mean() - sr.mean() * mr.mean()
                var = mr.var()
                if var is None or var == 0:
                    return None
                beta = float(cov / var)
                return round(max(0.3, min(beta, 3.0)), 2)

        return runAsync(_calc())
    except (ImportError, OSError, RuntimeError, AttributeError):
        return None
    except Exception as exc:
        try:
            import httpx

            from dartlab.gather.types import SourceUnavailableError
        except ImportError:
            raise
        if isinstance(exc, (httpx.HTTPError, SourceUnavailableError)):
            return None
        raise


def _resolveCountryFromCurrency(currency: str) -> str:
    """currency → ISO2 fallback. riskPremiums.resolveCountryCode 재사용."""
    try:
        from dartlab.synth.riskPremiums import resolveCountryCode

        return resolveCountryCode(currency=currency)
    except ImportError:
        return "KR"


def computeCompanyWacc(
    series: dict,
    sectorParams=None,
    sectorElasticity: SectorElasticity | None = None,
    riskFreeRate: float | None = None,
    marketPremium: float | None = None,
    marketCap: float | None = None,
    currency: str = "KRW",
    betaOverride: float | None = None,
    country: str | None = None,
    countryRiskPremium: float | None = None,
    impliedErp: bool = False,
    bottomUpBeta: bool = False,
) -> tuple[float, dict[str, float]]:
    """회사 고유 WACC 계산 (Damodaran CAPM 기반).

    Ke = Rf + beta * (matureMarketERP + countryRiskPremium)
    WACC = E/(D+E) * Ke + D/(D+E) * Kd * (1-t)

    Capabilities:
        - 회사 시계열 + 시장 파라미터 + Damodaran 표 결합 WACC 산출.

    Parameters
    ----------
    country : ISO2 국가코드 (KR/US/JP/...). 지정 시 Damodaran 테이블로 rf/erp 자동.
              None 이면 기존 `getMarketParams(currency)` 경로 (backward compat).
    country_risk_premium : 국가 리스크 프리미엄 (%) 명시 override. None 이면 자동.
    implied_erp : True 면 Damodaran Gordon 역산 (시장 내재). 실패 시 historical fallback.
    bottom_up_beta : True 면 섹터 peer unlever/relever (Hamada). 실패 시 기본 beta.

    Guide:
        impliedErp 실패 시 historical fallback 자동.

    When:
        DCF·proforma 빌드 직전 회사별 WACC 산출.

    How:
        Rf + beta × ERP 로 Ke, Kd × (1-t) 가중 합산.

    Requires:
        BS 차입금/자기자본, 섹터 파라미터 또는 베타 source.

    Raises:
        Damodaran/sector 파라미터 결측 시 ImportError 전파 가능.

    Example:
        >>> computeCompanyWacc(series, currency="KRW")
        (0.085, {...})

    See Also:
        - buildProforma : WACC 소비.

    AIContext:
        결과 dict 의 component 노출 (Ke/Kd/weights) 로 재현 가능성 보장.
    """
    from dartlab.frame.sector import getMarketParams

    damodaran = None
    if country or countryRiskPremium is not None or impliedErp:
        if impliedErp:
            from dartlab.synth.impliedERP import calcImpliedERP

            damodaran = calcImpliedERP(country=country or _resolveCountryFromCurrency(currency))
        else:
            from dartlab.synth.riskPremiums import loadDamodaranERP

            damodaran = loadDamodaranERP(countryCode=country, currency=currency)

    mkt = getMarketParams(currency)
    if riskFreeRate is not None:
        rf = riskFreeRate
    elif damodaran is not None:
        rf = damodaran["riskFreeRate"]
    else:
        rf = mkt.riskFreeRate

    if marketPremium is not None:
        erp = marketPremium
    elif damodaran is not None:
        base_erp = damodaran["matureMarketERP"]
        crp = countryRiskPremium if countryRiskPremium is not None else damodaran["countryRiskPremium"]
        erp = base_erp + crp
    else:
        erp = mkt.totalErp

    # beta: 1순위 외부 주입, 2순위 bottom-up peer Hamada, 3순위 섹터 파라미터, 4순위 1.0
    beta = betaOverride
    betaSource = "override" if betaOverride is not None else None
    if beta is None and bottomUpBeta:
        try:
            from dartlab.synth.bottomUpBeta import calcBottomUpBeta

            stb_bu = getLatest(series, "BS", "shortterm_borrowings") or 0
            ltb_bu = getLatest(series, "BS", "longterm_borrowings") or 0
            bonds_bu = getLatest(series, "BS", "debentures") or 0
            debt_bu = stb_bu + ltb_bu + bonds_bu
            equity_bu = getLatest(series, "BS", "total_stockholders_equity") or getLatest(
                series, "BS", "owners_of_parent_equity"
            )
            de_bu = (debt_bu / equity_bu) if (equity_bu and equity_bu > 0) else 0.3
            # 섹터 이름은 `label` 이다. `name` 은 존재하지 않는 속성이라 언제나
            # "Unknown" 으로 떨어졌고, 그러면 베타 조회가 반드시 실패해 1.0 이 나온다.
            sector_name = getattr(sectorParams, "label", "") or "Unknown"
            bu_result = calcBottomUpBeta(
                sector=sector_name,
                debtToEquity=de_bu,
                taxRate=0.22,
                country=country or _resolveCountryFromCurrency(currency),
            )
            # method 를 확인한다. `bottom_up` 만 실제 peer 계산 결과이고 나머지는 대체값이다.
            # 예전에는 값만 보고 받아서, 더 정교한 방법을 켰는데 섹터 베타 1.2 대신
            # 대체값 1.0 이 들어가 할인율이 오히려 낮아지고 가치평가가 부풀었다.
            betaSource = bu_result.get("method")
            if betaSource == "bottom_up" and bu_result.get("leveredBeta"):
                beta = bu_result["leveredBeta"]
        except (ImportError, AttributeError, ValueError, TypeError):
            pass
    if beta is None:
        if sectorParams and hasattr(sectorParams, "beta") and sectorParams.beta:
            beta = sectorParams.beta
            betaSource = "sectorParams"
        elif sectorElasticity and hasattr(sectorElasticity, "revenueToGdp"):
            beta = max(0.5, min(sectorElasticity.revenueToGdp, 2.5))
            betaSource = "sectorElasticity"
        else:
            beta = 1.0
            betaSource = "fallbackOne"

    # 시가총액 기반 beta 감쇠 — 대형주는 시장 대비 변동성이 낮음
    if marketCap and marketCap > 0:
        mcTrillion = marketCap / 1e12
        if mcTrillion > 50:
            beta *= 0.8
        elif mcTrillion > 10:
            beta *= 0.9

    # 차입금
    stb = getLatest(series, "BS", "shortterm_borrowings") or 0
    ltb = getLatest(series, "BS", "longterm_borrowings") or 0
    bonds = getLatest(series, "BS", "debentures") or 0
    total_debt = stb + ltb + bonds

    # 자기자본 = 시가총액 or 장부가
    equity_book = getLatest(series, "BS", "total_stockholders_equity") or getLatest(
        series, "BS", "owners_of_parent_equity"
    )
    # `or 1` 은 None 과 0 만 걸러내고 음수 장부가는 그대로 통과시켰다. 자본잠식 기업이
    # 음수 자기자본으로 들어가면 가중치가 -200% 와 300% 처럼 뒤집히고, 그 조합이 하필
    # WACC 하한 4% 에 걸려 가장 위험한 회사가 가장 싼 할인율을 받았다. 자본이 -200 억일
    # 때 4%, -400 억일 때 11% 로 값이 튀기까지 한다.
    equity_value = marketCap if marketCap else equity_book
    if not equity_value or equity_value <= 0:
        equity_value = None

    # Kd (타인자본비용) -- 실제 이자비용 역산
    fc = getTTM(series, "IS", "finance_costs") or getTTM(series, "IS", "interest_expense")
    if fc and total_debt > 0:
        kd = abs(fc) / total_debt * 100
        kd = max(2.0, min(kd, 15.0))
    else:
        kd = rf + 1.0  # Rf + 1%p 스프레드 (기존 4.0% 하드코딩 제거)

    # Ke (자기자본비용) -- CAPM: Rf + beta * (ERP + CRP)
    ke = rf + beta * erp

    # 유효세율
    pbt = getTTM(series, "IS", "profit_before_tax")
    tax_exp = getTTM(series, "IS", "income_tax_expense")
    if pbt and tax_exp and pbt > 0:
        tax_rate = min(abs(tax_exp) / pbt, 0.5)
    else:
        tax_rate = mkt.defaultTaxRate / 100

    # WACC. 자기자본 가치를 세울 수 없으면 자본구조 가중을 만들 수 없다. 억지로 만들면
    # 가중치가 구간을 벗어나고 결과가 자본 크기에 대해 단조롭지도 않게 된다.
    if equity_value is None:
        equityUnknown = True
        e_weight, d_weight = 1.0, 0.0
        equity_value = 0.0
    else:
        equityUnknown = False
        total_capital = equity_value + total_debt
        if total_capital > 0:
            e_weight = equity_value / total_capital
            d_weight = total_debt / total_capital
        else:
            e_weight, d_weight = 1.0, 0.0

    wacc = e_weight * ke + d_weight * kd * (1 - tax_rate)
    # Phase 4 G12.1: 대기업 AA급 현실 (Rf 2.4% + 1.5%p ≈ 4%) 반영 — 하한 5→4
    wacc = max(4.0, min(wacc, 20.0))

    details = {
        "ke": ke,
        "kd": kd,
        "beta": beta,
        # 베타가 계산 결과인지 대체값인지 소비자가 알아야 한다. 예전에는 구분이 없어
        # 대체값 1.0 과 실제 섹터 베타가 같은 모양으로 나갔다.
        "betaSource": betaSource,
        # 자기자본 가치를 세우지 못해 자본구조 가중을 자기자본 100% 로 둔 경우를 알린다.
        "equityValueUnknown": equityUnknown,
        "rf": rf,
        "erp": erp,
        "tax_rate": tax_rate * 100,
        "equity_weight": e_weight * 100,
        "debt_weight": d_weight * 100,
        "total_debt": total_debt,
        "equity_value": equity_value,
    }
    if damodaran is not None:
        details["countryCode"] = damodaran["countryCode"]
        details["countryRiskPremium"] = damodaran["countryRiskPremium"]
        details["matureMarketERP"] = damodaran["matureMarketERP"]
        details["erpSource"] = damodaran["source"]
    return wacc, details


def _extractBaseYear(series: dict) -> dict[str, float]:
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


def buildProforma(
    series: dict,
    revenueGrowthPath: list[float],
    sectorParams=None,
    sectorElasticity: SectorElasticity | None = None,
    shares: int | None = None,
    marketCap: float | None = None,
    scenarioName: str = "base",
    overrides: dict[str, float] | None = None,
    revenueLevelPath: list[float] | None = None,
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
        revenueLevelPath: 절대 매출레벨 경로 (원). 주어지면 base 상대성장 대신 이 레벨을
            매출로 직접 사용 (봉인 매출기대 앵커링, 06 D2 해소). BS 기초잔액은 base(TTM)
            유지, IS 첫 줄만 절대 앵커. 길이 = revenueGrowthPath 와 동일해야 함.

    Capabilities:
        - 과거 비율 + 성장 경로 + WACC 로 IS/BS/CF 3-statement 추정.

    Guide:
        overrides 는 마진·회전율 등 핵심 비율만. 전 비율 override 비권장.

    When:
        DCF·시나리오 산출 직전 회계 일관성 유지된 추정치 생성.

    How:
        ratios → margin·turnover 적용 → BS/CF 회계 잠금 → WACC 결합.

    Requires:
        series 시계열 ≥ 3 년, sectorParams 또는 elasticity.

    Raises:
        WACC 계산 의존성 부재 시 ImportError 전파.

    SeeAlso:
        - computeCompanyWacc : 할인율 산출.
        - extractHistoricalRatios : 입력 비율 추출.

    AIContext:
        결과 ProFormaResult 의 warnings 가 비어있는지 함께 검토 후 인용.
    """
    from dartlab.analysis.financial.proforma import ProFormaResult, ProFormaYear  # noqa: F401

    warnings: list[str] = []

    # 1. 과거 비율 추출
    ratios = extractHistoricalRatios(series)
    warnings.extend(ratios.warnings)

    # 영업레버리지 분해 사용 여부: 신뢰가능 + margin override 없음(명시 마진 존중)
    useOplev = ratios.oplev_reliable and not (overrides and "gross_margin" in overrides)

    # 오버라이드 적용
    if overrides:
        for k, v in overrides.items():
            if hasattr(ratios, k):
                setattr(ratios, k, v)

    # 2. WACC 계산
    wacc, wacc_details = computeCompanyWacc(
        series,
        sectorParams=sectorParams,
        sectorElasticity=sectorElasticity,
        marketCap=marketCap,
    )

    # 3. 기준연도 추출
    base = _extractBaseYear(series)
    if base["revenue"] <= 0:
        warnings.append("기준 매출이 0 — pro-forma 불가")
        return ProFormaResult(
            historical_ratios=ratios,
            base_year=base,
            projections=[],
            scenarioName=scenarioName,
            revenueGrowthPath=revenueGrowthPath,
            wacc=wacc,
            wacc_details=wacc_details,
            warnings=warnings,
        )

    # 4. 연도별 pro-forma 생성
    projections: list[ProFormaYear] = []
    prev_revenue = base["revenue"]
    prev_ppe = base["ppe_net"]
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
    def _ratioForYear(baseVal: float, trendKey: str, yrIdx: int, floor: float = 0.0, ceiling: float = 100.0) -> float:
        trend = ratios.trends.get(trendKey, 0.0)
        val = baseVal + trend * yrIdx
        return max(floor, min(val, ceiling))

    for i, growth_pct_in in enumerate(revenueGrowthPath):
        yr = ProFormaYear(year_offset=i + 1)

        # v2: 연도별 비율 (트렌드 반영)
        yr_gm = _ratioForYear(ratios.gross_margin, "gross_margin", i, floor=5.0, ceiling=90.0)
        yr_sga = _ratioForYear(ratios.sga_ratio, "sga_ratio", i, floor=1.0, ceiling=50.0)
        yr_dep = _ratioForYear(ratios.depreciation_ratio, "depreciation_ratio", i, floor=0.5, ceiling=30.0)
        yr_capex = _ratioForYear(ratios.capex_to_revenue, "capex_to_revenue", i, floor=0.5, ceiling=40.0)

        # === IS ===
        # 매출 앵커: 절대레벨 경로가 있으면 봉인 레벨 직접 사용(D2), 없으면 base 상대성장.
        # 기타(other_*) 비례에 쓰는 growth_pct 는 어느 경우든 실효 성장률로 통일.
        if revenueLevelPath is not None and i < len(revenueLevelPath):
            yr.revenue = revenueLevelPath[i]
            growth_pct = (yr.revenue / prev_revenue - 1) * 100 if prev_revenue > 0 else 0.0
        else:
            growth_pct = growth_pct_in
            yr.revenue = prev_revenue * (1 + growth_pct / 100)
        # 원가·판관비: 영업레버리지(고정+변동)면 매출 급변 시 마진 비대칭 반응(D5), 아니면 순변동비.
        if useOplev:
            yr.cogs = min(ratios.cogs_fixed + ratios.cogs_var_ratio * yr.revenue, yr.revenue * 0.98)
            yr.sga = max(ratios.sga_fixed + ratios.sga_var_ratio * yr.revenue, 0.0)
        else:
            yr.cogs = yr.revenue * (1 - yr_gm / 100)
            yr.sga = yr.revenue * yr_sga / 100
        yr.gross_profit = yr.revenue - yr.cogs
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
        scenarioName=scenarioName,
        revenueGrowthPath=revenueGrowthPath,
        wacc=wacc,
        wacc_details=wacc_details,
        warnings=warnings,
    )
