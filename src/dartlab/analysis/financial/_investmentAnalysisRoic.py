"""investmentAnalysis 의 ROIC + Intensity cluster: calcRoicTimeline · calcInvestmentIntensity + 헬퍼."""

from __future__ import annotations

from dartlab.analysis.financial._seriesMath import _yoy
from dartlab.analysis.financial.accountSums import sumBorrowings
from dartlab.core.memory import memoizedCalc
from dartlab.core.utils.calc import safePct as _pct
from dartlab.core.utils.helpers import annualColsFromPeriods, toDictBySnakeId
from dartlab.core.utils.safe import get as _get

_getF = _getF2 = _getF3 = _getF4 = _get
_MAX_YEARS = 8


def _estimateWacc(company) -> float | None:
    """company에서 WACC 추정 (compute_company_wacc 래퍼).

    [성능] 자체 캐시 (None 결과도 캐싱). review에서 5개 calc가 각자 호출하는데
    매번 fetch_price + fetchBeta 외부 API 호출 발생 (각 ~2.6s = 13s).
    None 결과도 캐시해야 외부 API 재호출 방지.
    memoized_calc은 None 결과를 캐시 안 함 → 자체 sentinel 캐시 사용.
    """

    def _isOptionalMarketDataError(exc: BaseException) -> bool:
        if isinstance(exc, BaseExceptionGroup):
            return bool(exc.exceptions) and all(_isOptionalMarketDataError(child) for child in exc.exceptions)
        if isinstance(exc, (OSError, RuntimeError)):
            return True
        try:
            import httpx

            from dartlab.gather.types import SourceUnavailableError
        except ImportError:
            return False
        return isinstance(exc, (httpx.HTTPError, SourceUnavailableError))

    cache = getattr(company, "_cache", None)
    _KEY = "_estimateWacc_v3"  # v3: bottom-up β + Damodaran 국가테이블 de-gate (P1a)
    _SENTINEL = "__NONE__"
    if cache is not None and _KEY in cache:
        cached = cache[_KEY]
        return None if cached == _SENTINEL else cached

    result: float | None = None
    try:
        from dartlab.analysis.financial.proforma import computeCompanyWacc

        annual = company._buildFinanceSeries(freq="Y")
        if annual is not None:
            series, _ = annual
            sectorParams = getattr(company, "sectorParams", None)
            # 시총: gather.price 경유 (beta 감쇠에 필요)
            marketCap = None
            try:
                from dartlab.gather.infra.http import runAsync
                from dartlab.gather.sources.price import fetch

                stockCode = getattr(company, "stockCode", "")
                snapshot = runAsync(fetch(stockCode, market="KR")) if stockCode else None
                if snapshot:
                    marketCap = snapshot.marketCap
            except (ImportError, OSError, RuntimeError):
                pass
            except Exception as exc:
                if not _isOptionalMarketDataError(exc):
                    raise
            # 개별 beta
            betaCalc = None
            try:
                from dartlab.analysis.financial.proforma import _fetchBeta

                betaCalc = _fetchBeta(getattr(company, "stockCode", ""), getattr(company, "currency", "KRW"))
            except (ImportError, OSError, RuntimeError):
                pass
            except Exception as exc:
                if not _isOptionalMarketDataError(exc):
                    raise
            _currency = getattr(company, "currency", "KRW")
            # de-gate (P1a): Damodaran 국가테이블(정밀 Rf/ERP) + bottom-up β fallback 활성.
            # betaOverride(회귀 β) 우선 유지 → 평시 무변, 콜드/403 시 sector-const/1.0 대신 bottom-up.
            try:
                from dartlab.synth.riskPremiums import resolveCountryCode

                _country = resolveCountryCode(currency=_currency)
            except (ImportError, ValueError, TypeError):
                _country = None
            wacc, _ = computeCompanyWacc(
                series,
                sectorParams=sectorParams,
                marketCap=marketCap,
                currency=_currency,
                betaOverride=betaCalc,
                country=_country,
                bottomUpBeta=True,
            )
            result = round(wacc, 2)
    except (ImportError, AttributeError, TypeError, ValueError):
        result = None

    if cache is not None:
        cache[_KEY] = result if result is not None else _SENTINEL
    return result


# ── ROIC (NOPAT / 투하자본) ──


def _roicHistoryEntry(col: str, yCols: list[str], rows: dict[str, dict], bsData: dict) -> dict:
    """한 연도의 NOPAT / 투하자본 / ROIC.

    Parameters
    ----------
    col : str
        연도 컬럼.
    yCols : list[str]
        연도 컬럼 목록 (자본 fallback 탐색용).
    rows : dict[str, dict]
        op/tax/pt/rev/eq/cash 행 dict.
    bsData : dict
        BS 전체 dict (차입금 합산용).

    Returns
    -------
    dict
        history 항목 한 장.
    """
    opIncome = _getF(rows["op"], col)
    taxExpense = _getF(rows["tax"], col)
    ptIncome = _getF(rows["pt"], col)
    revenue = _getF(rows["rev"], col)

    # 유효세율
    effectiveTaxRate = abs(taxExpense) / abs(ptIncome) if ptIncome != 0 else 0.25
    effectiveTaxRate = min(effectiveTaxRate, 0.5)

    nopat = round(opIncome * (1 - effectiveTaxRate)) if opIncome != 0 else None

    equity = _get(rows["eq"], col)
    # equity 누락(0) 시 인접 기간 값으로 fallback (매핑 공백 대응)
    if equity == 0:
        for adjCol in yCols:
            adjEq = _get(rows["eq"], adjCol)
            if adjEq > 0:
                equity = adjEq
                break
    # 차입금: 회사 키 패턴 무관 헬퍼
    totalBorrowing = sumBorrowings(bsData, col)
    cash = _get(rows["cash"], col)
    investedCapital = equity + totalBorrowing - cash

    roic = round(nopat / investedCapital * 100, 2) if nopat is not None and investedCapital > 0 else None

    return {
        "period": col,
        "operatingIncome": opIncome if opIncome != 0 else None,
        "effectiveTaxRate": round(effectiveTaxRate * 100, 2),
        "nopat": nopat,
        "revenue": revenue if revenue != 0 else None,
        "equity": equity if equity != 0 else None,
        "totalBorrowing": totalBorrowing if totalBorrowing > 0 else None,
        "cash": cash if cash != 0 else None,
        "investedCapital": investedCapital if investedCapital > 0 else None,
        "roic": roic,
        "roicYoy": _yoy(roic, None),  # 이전 기간 ROIC는 아래서 계산
    }


def _injectRoicDecomposition(history: list[dict]) -> None:
    """Damodaran Excess Return 분해를 history 에 제자리 주입.

    Parameters
    ----------
    history : list[dict]
        _roicHistoryEntry 결과 목록.
    """
    from dartlab.core.utils.calc import decomposeRoic

    for h in history:
        op = h.get("operatingIncome")
        rev = h.get("revenue")
        ic = h.get("investedCapital")
        etr = h.get("effectiveTaxRate")
        if op is None or rev is None or ic is None:
            h["decomposition"] = None
            continue
        h["decomposition"] = decomposeRoic(
            operatingIncome=op,
            revenue=rev,
            investedCapital=ic,
            effectiveTaxRate=etr / 100.0 if etr is not None else None,
            wacc=h.get("waccEstimate"),
        )


def _injectRoicDrivers(history: list[dict]) -> None:
    """ROIC 변화 driver 분해 (Margin x Turnover x Tax) 를 제자리 주입.

    Parameters
    ----------
    history : list[dict]
        decomposition 이 주입된 history.
    """
    try:
        from dartlab.analysis.financial.attribution import decomposeRoicChange

        for i in range(len(history) - 1):
            cur = history[i]
            prev = history[i + 1]
            curD = cur.get("decomposition") or {}
            prevD = prev.get("decomposition") or {}
            roicT = cur.get("roic")
            roicT1 = prev.get("roic")
            marginT = curD.get("operatingMargin")
            marginT1 = prevD.get("operatingMargin")
            turnoverT = curD.get("assetTurnover")
            turnoverT1 = prevD.get("assetTurnover")
            if all(isinstance(v, (int, float)) for v in (roicT, roicT1, marginT, marginT1, turnoverT, turnoverT1)):
                attribution = decomposeRoicChange(
                    roicT=roicT,
                    roicT1=roicT1,
                    marginT=marginT,
                    marginT1=marginT1,
                    turnoverT=turnoverT,
                    turnoverT1=turnoverT1,
                    taxT=cur.get("effectiveTaxRate"),
                    taxT1=prev.get("effectiveTaxRate"),
                )
                cur["drivers"] = attribution.get("drivers") or []
                cur["driversExplained"] = attribution.get("explainedPct")
    except (ImportError, AttributeError, TypeError, ValueError):
        # 원본과 같은 자리에서 삼킨다. 이미 주입된 driver 는 그대로 둔다.
        pass


@memoizedCalc
def calcRoicTimeline(company, *, basePeriod: str | None = None) -> dict | None:
    """ROIC 시계열 -- 투하자본 대비 실제 수익률.

    Capabilities:
        - ROIC = NOPAT / Invested Capital 시계열 + WACC 스프레드 + Damodaran
          Excess Return 분해 + 변화 driver attribution.

    Args:
        company: 분석 대상 기업.
        basePeriod: 기준 기간.

    Returns:
        dict | None: history 키에 기간별 13+ 키 (operatingIncome/NOPAT/
        investedCapital/roic/spread/decomposition) 행 리스트. 데이터 부재
        시 None.

    Guide:
        IS 영업이익·법인세 + BS 자본·차입금으로 직접 계산. 유효세율 0~50%
        클립. equity=0 인 기간은 인접 기간 fallback.

    When:
        가치 창출 진단 (ROIC vs WACC), 마진/회전율 driver 분해, 투자 효율
        시계열 분석.

    How:
        IS/BS rawNormalized → NOPAT/Invested Capital 계산 → ROIC →
        ``decomposeRoic`` 로 분해 → ``decomposeRoicChange`` 로 attribution.

    Requires:
        IS (영업이익/법인세/매출) + BS (자본/차입금/현금) ≥ 2 년.

    Raises:
        없음.

    Example:
        >>> calcRoicTimeline(Company("005930"))
        {"history": [{"period": "2024-12", "roic": 14.2, ...}]}

    SeeAlso:
        - ``calcEvaTimeline``: EVA 절대값
        - ``attribution.decomposeRoicChange``: ROIC 변화 분해

    AIContext:
        AI 답변에서 ROIC 시계열·WACC 스프레드 인용 시.
    """
    isResult = company.select("IS", ["영업이익", "법인세비용", "법인세차감전순이익", "매출액"])
    bsResult = company.select(
        "BS",
        [
            "자본총계",
            "단기차입금",
            "장기차입금",
            "차입금단기",
            "long_term_borrowings",
            "short_term_borrowings",
            "차입부채",
            "장기차입부채",
            "유동성장기차입금",
            "사채",
            "현금및현금성자산",
        ],
    )

    isParsed = toDictBySnakeId(isResult)
    bsParsed = toDictBySnakeId(bsResult)
    if isParsed is None or bsParsed is None:
        return None

    isData, isPeriods = isParsed
    bsData, _ = bsParsed

    opRow = isData.get("operating_profit", {})
    taxRow = isData.get("income_tax_expense") or isData.get("income_taxes", {})
    ptRow = isData.get("profit_before_tax", {})
    revRow = isData.get("sales", {})
    eqRow = bsData.get("total_stockholders_equity", {})
    bsData.get("shortterm_borrowings", {})
    bsData.get("longterm_borrowings", {})
    bsData.get("borrowings", {})
    bsData.get("debentures", {})
    cashRow = bsData.get("cash_and_cash_equivalents", {})

    yCols = annualColsFromPeriods(isPeriods, maxYears=_MAX_YEARS + 1, basePeriod=basePeriod)
    if len(yCols) < 2:
        return None

    rows = {"op": opRow, "tax": taxRow, "pt": ptRow, "rev": revRow, "eq": eqRow, "cash": cashRow}
    history = [_roicHistoryEntry(col, yCols, rows, bsData) for col in yCols[:-1]]

    # ROIC YoY 후처리 (history가 최신→과거 순)
    for i in range(len(history) - 1):
        cur = history[i].get("roic")
        prev = history[i + 1].get("roic")
        history[i]["roicYoy"] = _yoy(cur, prev)

    # WACC 추정 (최신 시점 1회만, 전 기간 동일 적용)
    waccEstimate = _estimateWacc(company)
    if waccEstimate is not None:
        for h in history:
            h["waccEstimate"] = waccEstimate
            roic = h.get("roic")
            h["spread"] = round(roic - waccEstimate, 2) if roic is not None else None

    # Damodaran Excess Return 분해 주입
    _injectRoicDecomposition(history)

    # Phase 7 G24: ROIC 변화 driver 분해 (Margin × Turnover × Tax)
    _injectRoicDrivers(history)

    # Phase 8 A5
    from dartlab.synth.turningPoint import injectTurningPoints

    return (
        {"history": history, "turningPoints": injectTurningPoints(history, seriesKey="roic", minDeltaPct=30.0)}
        if history
        else None
    )


# ── 투자 강도 ──


@memoizedCalc
def calcInvestmentIntensity(company, *, basePeriod: str | None = None) -> dict | None:
    """투자 강도 시계열 -- CAPEX/매출, 유무형 비율.

    Capabilities:
        - CAPEX(유형+무형 취득)/매출 비율 + 유형/무형자산 구성 시계열.

    Args:
        company: 분석 대상 기업.
        basePeriod: 기준 기간.

    Returns:
        dict | None: history 키에 기간별 CAPEX·매출·자산·비율 8 키 행 리스트.
        데이터 부재 시 None.

    Guide:
        capexToRevenue > 10% = 자본집약, < 3% = 자산경량. 무형자산 비율
        급등은 M&A·영업권 신호.

    When:
        설비투자 강도·자산 경량화 시계열 진단, 산업 평균 대비 투자 정책 비교.

    How:
        CF 의 PP&E·무형 취득 + IS 매출 + BS 유무형/자산총계 매핑 후 비율 계산.

    Requires:
        CF/IS/BS rawNormalized parquet.

    Raises:
        없음.

    Example:
        >>> calcInvestmentIntensity(Company("005930"))
        {"history": [{"period": "...", "capexToRevenue": 8.2, ...}]}

    SeeAlso:
        - ``calcRoicTimeline``: 투자 수익률 평가
        - ``calcEvaTimeline``: EVA 시계열

    AIContext:
        AI 답변에서 CAPEX 강도·자산 구성 인용 시.
    """
    cfResult = company.select(
        "CF",
        ["purchase_of_property_plant_and_equipment", "purchase_of_intangible_assets"],
    )
    isResult = company.select("IS", ["매출액"])
    bsResult = company.select("BS", ["유형자산", "무형자산", "자산총계"])

    isParsed = toDictBySnakeId(isResult)
    bsParsed = toDictBySnakeId(bsResult)
    if isParsed is None or bsParsed is None:
        return None

    cfParsed = toDictBySnakeId(cfResult)
    cfData = cfParsed[0] if cfParsed else {}
    isData, isPeriods = isParsed
    bsData, _ = bsParsed

    capexRow = cfData.get("purchase_of_property_plant_and_equipment", {})
    intCapexRow = cfData.get("purchase_of_intangible_assets", {})
    revRow = isData.get("sales", {})
    ppeRow = bsData.get("tangible_assets", {})
    intRow = bsData.get("intangible_assets", {})
    taRow = bsData.get("자산총계", {})

    yCols = annualColsFromPeriods(isPeriods, maxYears=_MAX_YEARS, basePeriod=basePeriod)
    if not yCols:
        return None

    history = []
    for col in yCols:
        capex = abs(_getF2(capexRow, col)) + abs(_getF2(intCapexRow, col))
        rev = _getF2(revRow, col)
        ppe = _get(ppeRow, col)
        intangible = _get(intRow, col)
        ta = _get(taRow, col)

        history.append(
            {
                "period": col,
                "capex": capex if capex > 0 else None,
                "revenue": rev if rev != 0 else None,
                "tangibleAssets": ppe if ppe != 0 else None,
                "intangibleAssets": intangible if intangible != 0 else None,
                "totalAssets": ta if ta != 0 else None,
                "capexToRevenue": _pct(capex, rev),
                "tangibleRatio": _pct(ppe, ta),
                "intangibleRatio": _pct(intangible, ta),
            }
        )

    return {"history": history} if history else None


# ── NOPAT + 투하자본 ──
