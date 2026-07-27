"""computeCompanyWacc 의 구성요소 (Rf/ERP · 베타 · Kd · 세율 · 자본구조 가중).

WACC 한 줄을 만들려면 다섯 갈래의 우선순위 사슬을 각각 풀어야 한다.
_proformaCore 본문에서 그 다섯을 함수로 떼어내 800 줄 상한도 함께 지킨다.
"""

from __future__ import annotations

from dartlab.core.utils.extract import getLatest, getTTM


def _resolveCountryFromCurrency(currency: str) -> str:
    """currency → ISO2 fallback. riskPremiums.resolveCountryCode 재사용."""
    try:
        from dartlab.synth.riskPremiums import resolveCountryCode

        return resolveCountryCode(currency=currency)
    except ImportError:
        return "KR"


def _resolveRfAndErp(
    riskFreeRate: float | None,
    marketPremium: float | None,
    damodaran: dict | None,
    market,
    countryRiskPremium: float | None,
) -> tuple[float, float]:
    """무위험수익률과 ERP 결정. 명시 인자 > Damodaran > 시장 기본값.

    Parameters
    ----------
    riskFreeRate, marketPremium : float | None
        호출자가 못 박은 값 (%).
    damodaran : dict | None
        loadDamodaranERP 또는 calcImpliedERP 결과.
    market : Any
        getMarketParams 결과.
    countryRiskPremium : float | None
        국가위험 프리미엄 override (%).

    Returns
    -------
    tuple[float, float]
        (rf, erp).
    """
    if riskFreeRate is not None:
        rf = riskFreeRate
    elif damodaran is not None:
        rf = damodaran["riskFreeRate"]
    else:
        rf = market.riskFreeRate

    if marketPremium is not None:
        erp = marketPremium
    elif damodaran is not None:
        baseErp = damodaran["matureMarketERP"]
        crp = countryRiskPremium if countryRiskPremium is not None else damodaran["countryRiskPremium"]
        erp = baseErp + crp
    else:
        erp = market.totalErp
    return rf, erp


def _bottomUpBeta(series: dict, sectorParams, country: str | None, currency: str) -> tuple[float | None, str | None]:
    """peer Hamada 기반 bottom-up 베타. 실패하면 (None, method 또는 None).

    Parameters
    ----------
    series : dict
        finance.timeseries dict.
    sectorParams : Any
        섹터 파라미터 (label 사용).
    country : str | None
        ISO2 국가코드.
    currency : str
        통화.

    Returns
    -------
    tuple[float | None, str | None]
        (beta, betaSource). bottom_up 이 아니면 beta 는 None.
    """
    beta = None
    betaSource = None
    try:
        from dartlab.synth.bottomUpBeta import calcBottomUpBeta

        stbBu = getLatest(series, "BS", "shortterm_borrowings") or 0
        ltbBu = getLatest(series, "BS", "longterm_borrowings") or 0
        bondsBu = getLatest(series, "BS", "debentures") or 0
        debtBu = stbBu + ltbBu + bondsBu
        equityBu = getLatest(series, "BS", "total_stockholders_equity") or getLatest(
            series, "BS", "owners_of_parent_equity"
        )
        deBu = (debtBu / equityBu) if (equityBu and equityBu > 0) else 0.3
        # 섹터 이름은 `label` 이다. `name` 은 존재하지 않는 속성이라 언제나
        # "Unknown" 으로 떨어졌고, 그러면 베타 조회가 반드시 실패해 1.0 이 나온다.
        sectorName = getattr(sectorParams, "label", "") or "Unknown"
        buResult = calcBottomUpBeta(
            sector=sectorName,
            debtToEquity=deBu,
            taxRate=0.22,
            country=country or _resolveCountryFromCurrency(currency),
        )
        # method 를 확인한다. `bottom_up` 만 실제 peer 계산 결과이고 나머지는 대체값이다.
        # 예전에는 값만 보고 받아서, 더 정교한 방법을 켰는데 섹터 베타 1.2 대신
        # 대체값 1.0 이 들어가 할인율이 오히려 낮아지고 가치평가가 부풀었다.
        betaSource = buResult.get("method")
        if betaSource == "bottom_up" and buResult.get("leveredBeta"):
            beta = buResult["leveredBeta"]
    except (ImportError, AttributeError, ValueError, TypeError):
        # 원본과 같은 자리에서 삼킨다. 이미 잡아 둔 betaSource 는 그대로 유지한다.
        pass
    return beta, betaSource


def _resolveBeta(
    series: dict,
    *,
    sectorParams,
    sectorElasticity,
    betaOverride: float | None,
    bottomUpBeta: bool,
    country: str | None,
    currency: str,
    marketCap: float | None,
) -> tuple[float, str | None]:
    """베타와 그 출처. 1순위 외부 주입, 2순위 bottom-up, 3순위 섹터, 4순위 1.0.

    Parameters
    ----------
    series : dict
        finance.timeseries dict.
    sectorParams, sectorElasticity : Any
        섹터 파라미터 / 탄력성.
    betaOverride : float | None
        외부 주입 베타.
    bottomUpBeta : bool
        bottom-up 시도 여부.
    country : str | None
        ISO2 국가코드.
    currency : str
        통화.
    marketCap : float | None
        시가총액 (대형주 감쇠용).

    Returns
    -------
    tuple[float, str | None]
        (beta, betaSource).
    """
    beta = betaOverride
    betaSource = "override" if betaOverride is not None else None
    if beta is None and bottomUpBeta:
        buBeta, buSource = _bottomUpBeta(series, sectorParams, country, currency)
        if buSource is not None:
            betaSource = buSource
        if buBeta is not None:
            beta = buBeta
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

    # 시가총액 기반 beta 감쇠. 대형주는 시장 대비 변동성이 낮다.
    if marketCap and marketCap > 0:
        mcTrillion = marketCap / 1e12
        if mcTrillion > 50:
            beta *= 0.8
        elif mcTrillion > 10:
            beta *= 0.9
    return beta, betaSource


def _costOfDebt(series: dict, totalDebt: float, rf: float) -> float:
    """Kd (타인자본비용). 실제 이자비용 역산, 없으면 Rf + 1%p.

    Parameters
    ----------
    series : dict
        finance.timeseries dict.
    totalDebt : float
        총 차입금.
    rf : float
        무위험수익률 (%).

    Returns
    -------
    float
        Kd (%). 역산 시 2~15% 로 clip.
    """
    fc = getTTM(series, "IS", "finance_costs") or getTTM(series, "IS", "interest_expense")
    if fc and totalDebt > 0:
        kd = abs(fc) / totalDebt * 100
        return max(2.0, min(kd, 15.0))
    return rf + 1.0  # Rf + 1%p 스프레드 (기존 4.0% 하드코딩 제거)


def _effectiveTaxRate(series: dict, market) -> float:
    """유효세율. 세전이익 대비 법인세, 없으면 시장 기본값.

    Parameters
    ----------
    series : dict
        finance.timeseries dict.
    market : Any
        getMarketParams 결과.

    Returns
    -------
    float
        세율 (0.0~0.5).
    """
    pbt = getTTM(series, "IS", "profit_before_tax")
    taxExp = getTTM(series, "IS", "income_tax_expense")
    if pbt and taxExp and pbt > 0:
        return min(abs(taxExp) / pbt, 0.5)
    return market.defaultTaxRate / 100


def _capitalWeights(equityValue: float | None, totalDebt: float) -> tuple[float, float, bool, float]:
    """자본구조 가중. 자기자본 가치를 세울 수 없으면 자기자본 100% 로 둔다.

    Parameters
    ----------
    equityValue : float | None
        자기자본 가치 (시총 또는 장부가). 양수 아니면 None.
    totalDebt : float
        총 차입금.

    Returns
    -------
    tuple[float, float, bool, float]
        (eWeight, dWeight, equityUnknown, equityValue).
    """
    if equityValue is None:
        return 1.0, 0.0, True, 0.0
    totalCapital = equityValue + totalDebt
    if totalCapital > 0:
        return equityValue / totalCapital, totalDebt / totalCapital, False, equityValue
    return 1.0, 0.0, False, equityValue
