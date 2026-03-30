"""이익의 질 분석 — 발생액, 이익 지속성, M-Score 시계열.

이익이 현금으로 뒷받침되는지, 일회성인지, 조작 가능성이 있는지를 시계열로 추적한다.
"""

from __future__ import annotations

import math

_MAX_YEARS = 8


# ── 유틸 ──


def _toDict(selectResult) -> tuple[dict[str, dict], list[str]] | None:
    from dartlab.analysis.financial._helpers import toDict

    return toDict(selectResult)


def _annualColsFromPeriods(
    periods: list[str], maxYears: int = _MAX_YEARS, *, basePeriod: str | None = None
) -> list[str]:
    from dartlab.analysis.financial._helpers import annualColsFromPeriods

    return annualColsFromPeriods(periods, basePeriod=basePeriod, maxYears=maxYears)


def _get(row: dict, col: str) -> float:
    v = row.get(col) if row else None
    return v if v is not None else 0


def _safe(numerator: float, denominator: float) -> float | None:
    if denominator is None or denominator == 0:
        return None
    return numerator / denominator


# ── 발생액 분석 ──


def calcAccrualAnalysis(company, *, basePeriod: str | None = None) -> dict | None:
    """발생액(Accrual) 시계열 — 이익 중 현금이 아닌 비중.

    반환::

        {
            "history": [
                {
                    "period": str,
                    "netIncome": float,
                    "ocf": float,
                    "totalAssets": float,
                    "sloanAccrualRatio": float | None,
                    "accrualToRevenue": float | None,
                    "ocfToNi": float | None,
                },
                ...
            ],
        }
    """
    isResult = company.select("IS", ["당기순이익", "매출액"])
    cfResult = company.select("CF", ["영업활동현금흐름"])
    bsResult = company.select("BS", ["자산총계"])

    isParsed = _toDict(isResult)
    cfParsed = _toDict(cfResult)
    bsParsed = _toDict(bsResult)
    if isParsed is None or cfParsed is None or bsParsed is None:
        return None

    isData, _ = isParsed
    cfData, cfPeriods = cfParsed
    bsData, _ = bsParsed

    niRow = isData.get("당기순이익", {})
    revRow = isData.get("매출액", {})
    ocfRow = cfData.get("영업활동현금흐름", {})
    taRow = bsData.get("자산총계", {})

    yCols = _annualColsFromPeriods(cfPeriods, _MAX_YEARS, basePeriod=basePeriod)
    if not yCols:
        return None

    history = []
    for col in yCols:
        ni = _get(niRow, col)
        ocf = _get(ocfRow, col)
        ta = _get(taRow, col)
        rev = _get(revRow, col)
        accrual = ni - ocf

        history.append(
            {
                "period": col,
                "netIncome": ni,
                "ocf": ocf,
                "totalAssets": ta,
                "sloanAccrualRatio": _safe(accrual, ta) if ta > 0 else None,
                "accrualToRevenue": _safe(accrual, rev) * 100 if rev > 0 and _safe(accrual, rev) is not None else None,
                "ocfToNi": (lambda r: r if abs(r) <= 1000 else None)(_safe(ocf, ni) * 100)
                if ni != 0 and _safe(ocf, ni) is not None
                else None,
            }
        )

    return {"history": history} if history else None


# ── 이익 지속성 ──


def calcEarningsPersistence(company, *, basePeriod: str | None = None) -> dict | None:
    """이익 지속성 — 영업이익 vs 영업외손익, 변동성.

    반환::

        {
            "history": [
                {
                    "period": str,
                    "operatingIncome": float,
                    "preTaxIncome": float,
                    "nonOperatingIncome": float,
                    "nonOpRatio": float | None,
                },
                ...
            ],
            "earningsVolatility": float | None,
        }
    """
    accounts = ["영업이익", "법인세차감전순이익", "세전이익"]
    isResult = company.select("IS", accounts)
    isParsed = _toDict(isResult)
    if isParsed is None:
        return None

    isData, isPeriods = isParsed
    opRow = isData.get("영업이익", {})
    # 세전이익 fallback
    ptRow = isData.get("법인세차감전순이익", isData.get("세전이익", {}))

    yCols = _annualColsFromPeriods(isPeriods, _MAX_YEARS, basePeriod=basePeriod)
    if not yCols:
        return None

    history = []
    opValues = []
    for col in yCols:
        opIncome = _get(opRow, col)
        ptIncome = _get(ptRow, col)
        nonOp = ptIncome - opIncome

        nonOpRatio = None
        if ptIncome != 0:
            nonOpRatio = abs(nonOp) / abs(ptIncome) * 100

        history.append(
            {
                "period": col,
                "operatingIncome": opIncome,
                "preTaxIncome": ptIncome,
                "nonOperatingIncome": nonOp,
                "nonOpRatio": nonOpRatio,
            }
        )
        if opIncome != 0:
            opValues.append(opIncome)

    # 변동계수 (CV = std / |mean|)
    earningsVolatility = None
    if len(opValues) >= 3:
        mean = sum(opValues) / len(opValues)
        if mean != 0:
            variance = sum((v - mean) ** 2 for v in opValues) / len(opValues)
            earningsVolatility = math.sqrt(variance) / abs(mean)

    return {"history": history, "earningsVolatility": earningsVolatility} if history else None


# ── Beneish M-Score 시계열 ──


def calcBeneishTimeline(company, *, basePeriod: str | None = None) -> dict | None:
    """Beneish M-Score 시계열 — annual 데이터에서 직접 8변수 계산.

    8-Variable Model:
      DSRI(매출채권/매출 변화), GMI(매출총이익률 역전), AQI(자산품질 변화),
      SGI(매출성장), DEPI(감가상각률 변화, 기본1.0), SGAI(판관비율 변화),
      LVGI(레버리지 변화), TATA(발생액/총자산)

    M = -4.84 + 0.920*DSRI + 0.528*GMI + 0.404*AQI + 0.892*SGI
        + 0.115*DEPI - 0.172*SGAI + 4.679*TATA - 0.327*LVGI

    반환::

        {
            "history": [{"period": str, "mScore": float | None}, ...],
            "threshold": float,
        }
    """
    from dartlab.analysis.financial._helpers import toDictBySnakeId

    isResult = company.select(
        "IS",
        ["매출액", "매출원가", "판매비와관리비", "당기순이익"],
    )
    bsResult = company.select(
        "BS",
        ["매출채권및기타채권", "유동자산", "유형자산", "자산총계", "유동부채", "부채총계"],
    )
    cfResult = company.select("CF", ["operating_cashflow"])

    isParsed = _toDict(isResult)
    bsParsed = _toDict(bsResult)
    cfParsed = toDictBySnakeId(cfResult)
    if isParsed is None or bsParsed is None:
        return None

    isData, isPeriods = isParsed
    bsData, _ = bsParsed
    cfData = cfParsed[0] if cfParsed else {}

    revRow = isData.get("매출액", {})
    cogsRow = isData.get("매출원가", {})
    sgaRow = isData.get("판매비와관리비", {})
    niRow = isData.get("당기순이익", {})
    recRow = bsData.get("매출채권및기타채권", {})
    caRow = bsData.get("유동자산", {})
    ppeRow = bsData.get("유형자산", {})
    taRow = bsData.get("자산총계", {})
    clRow = bsData.get("유동부채", {})
    tlRow = bsData.get("부채총계", {})
    ocfRow = cfData.get("operating_cashflow", {})

    yCols = _annualColsFromPeriods(isPeriods, _MAX_YEARS + 1, basePeriod=basePeriod)  # 전년 대비 필요 → 1년 더
    if len(yCols) < 2:
        return None

    history = []
    for i in range(len(yCols) - 1):
        col = yCols[i]  # 당기
        prevCol = yCols[i + 1]  # 전기

        rev = _get(revRow, col)
        prevRev = _get(revRow, prevCol)
        cogs = _get(cogsRow, col)
        prevCogs = _get(cogsRow, prevCol)
        sga = _get(sgaRow, col)
        prevSga = _get(sgaRow, prevCol)
        ni = _get(niRow, col)
        rec = _get(recRow, col)
        prevRec = _get(recRow, prevCol)
        ca = _get(caRow, col)
        prevCa = _get(caRow, prevCol)
        ppe = _get(ppeRow, col)
        prevPpe = _get(ppeRow, prevCol)
        ta = _get(taRow, col)
        prevTa = _get(taRow, prevCol)
        cl = _get(clRow, col)
        prevCl = _get(clRow, prevCol)
        tl = _get(tlRow, col)
        prevTl = _get(tlRow, prevCol)
        ocf = _get(ocfRow, col)

        # 분모가 0이면 계산 불가
        if prevRev <= 0 or rev <= 0 or prevTa <= 0 or ta <= 0:
            history.append({"period": col, "mScore": None})
            continue

        # DSRI: (매출채권t/매출t) / (매출채권t-1/매출t-1)
        dsri = (rec / rev) / (prevRec / prevRev) if prevRec > 0 else 1.0

        # GMI: 매출총이익률t-1 / 매출총이익률t
        gm = (rev - cogs) / rev
        prevGm = (prevRev - prevCogs) / prevRev if prevRev > 0 else 0
        gmi = prevGm / gm if gm > 0 else 1.0

        # AQI: (1 - 유동자산t/총자산t - 유형자산t/총자산t) / (1 - 유동자산t-1/총자산t-1 - 유형자산t-1/총자산t-1)
        aqi_t = 1 - ca / ta - ppe / ta
        aqi_prev = 1 - prevCa / prevTa - prevPpe / prevTa
        aqi = aqi_t / aqi_prev if abs(aqi_prev) > 0.001 else 1.0

        # SGI: 매출t / 매출t-1
        sgi = rev / prevRev

        # DEPI: 감가상각 데이터 없음 → 기본 1.0 (중립)
        depi = 1.0

        # SGAI: (판관비t/매출t) / (판관비t-1/매출t-1)
        sgai = (sga / rev) / (prevSga / prevRev) if prevSga > 0 else 1.0

        # LVGI: (부채총계t/총자산t) / (부채총계t-1/총자산t-1)
        lev_t = tl / ta
        lev_prev = prevTl / prevTa if prevTa > 0 else 0
        lvgi = lev_t / lev_prev if lev_prev > 0 else 1.0

        # TATA: (순이익 - 영업CF) / 총자산
        tata = (ni - ocf) / ta if ta > 0 else 0

        mScore = (
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

        history.append({"period": col, "mScore": round(mScore, 4)})

    return {"history": history, "threshold": -1.78} if history else None


# ── 플래그 ──


def calcEarningsQualityFlags(company, *, basePeriod: str | None = None) -> list[str]:
    """이익 품질 경고 신호."""
    flags = []

    accrual = calcAccrualAnalysis(company, basePeriod=basePeriod)
    if accrual and accrual["history"]:
        h0 = accrual["history"][0]
        sar = h0.get("sloanAccrualRatio")
        if sar is not None and sar > 0.10:
            flags.append(f"Sloan 발생액비율 {sar:.1%} — 이익 현금화 부족")
        ocfNi = h0.get("ocfToNi")
        if ocfNi is not None and 0 < ocfNi < 40:
            flags.append(f"영업CF/순이익 {ocfNi:.0f}% — 이익 대비 현금 부족")

    persistence = calcEarningsPersistence(company, basePeriod=basePeriod)
    if persistence:
        if persistence["history"]:
            h0 = persistence["history"][0]
            nonOpRatio = h0.get("nonOpRatio")
            nonOpIncome = h0.get("nonOperatingIncome")
            if nonOpRatio is not None and nonOpRatio > 30:
                if nonOpIncome is not None and nonOpIncome < 0:
                    suffix = " (일회성 항목 가능성)" if nonOpRatio > 100 else ""
                    flags.append(f"영업외손실 비중 {nonOpRatio:.0f}% — 영업이익을 상쇄{suffix}")
                else:
                    suffix = " (일회성 항목 가능성)" if nonOpRatio > 100 else ""
                    flags.append(f"영업외이익 비중 {nonOpRatio:.0f}% — 일회성 이익 의존{suffix}")

        cv = persistence.get("earningsVolatility")
        if cv is not None and cv > 0.5:
            flags.append(f"이익 변동계수 {cv:.2f} — 이익 변동성 높음")

    beneish = calcBeneishTimeline(company, basePeriod=basePeriod)
    if beneish and beneish["history"]:
        h0 = beneish["history"][0]
        ms = h0.get("mScore")
        if ms is not None and ms > -1.78:
            flags.append(f"Beneish M-Score {ms:.2f} — 임계값 초과, 이익 조작 가능성")

    return flags
