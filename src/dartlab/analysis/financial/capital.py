"""1-2 자금 구조 분석 — 계산만 담당.

블록 조립은 review/builders.py가 한다.
여기는 company.select() → 계산 → dict/숫자 반환.
"""

from __future__ import annotations

_MAX_QUARTERS = 5
_MAX_YEARS = 5


# ── 유틸 ──


def _toDict(selectResult) -> tuple[dict[str, dict], list[str]] | None:
    """SelectResult → ({계정명: {period: val}}, 전체 periodCols)."""
    from dartlab.analysis.financial._helpers import toDict

    return toDict(selectResult)


def _annualCols(periods: list[str], maxYears: int = _MAX_YEARS) -> list[str]:
    """기간 목록에서 연도 컬럼만 추출."""
    cols = sorted([c for c in periods if "Q" not in c], reverse=True)
    if cols:
        return cols[:maxYears]
    return sorted([c for c in periods if c.endswith("Q4")], reverse=True)[:maxYears]


def _quarterlyCols(periods: list[str], maxQ: int = _MAX_QUARTERS) -> list[str]:
    """기간 목록에서 분기 컬럼만 추출."""
    return sorted([c for c in periods if "Q" in c], reverse=True)[:maxQ]


def _getRatios(company):
    """ratios 객체를 안전하게 가져온다."""
    try:
        return company.finance.ratios
    except (ValueError, KeyError, AttributeError):
        return None


def _fmtAmt(value) -> str:
    """금액을 조/억 단위로 포맷 (순수 문자열, review import 없이)."""
    if value is None:
        return "-"
    absVal = abs(value)
    sign = "-" if value < 0 else ""
    if absVal >= 1_0000_0000_0000:
        return f"{sign}{absVal / 1_0000_0000_0000:.1f}조"
    if absVal >= 1_0000_0000:
        return f"{sign}{absVal / 1_0000_0000:.0f}억"
    if absVal >= 1_0000:
        return f"{sign}{absVal / 1_0000:.0f}만"
    return f"{sign}{absVal:,.0f}"


# ── 계산 함수들 ──


def calcFundingSources(company) -> dict | None:
    """조달원 분해 — 돈을 어디서 가져왔는가.

    4가지 원천: 내부유보, 외부(주주), 금융차입, 영업조달.
    시계열로 비중 변화를 추적한다.

    반환::

        {
            "latest": {
                "totalAssets": float,
                "retained": float, "retainedPct": float,
                "paidIn": float, "paidInPct": float,
                "finDebt": float, "finDebtPct": float,
                "opFunding": float, "opFundingPct": float,
                "otherLiab": float, "otherLiabPct": float,
                "otherEquity": float, "otherEquityPct": float,
            },
            "history": [
                {"period": str, "retainedPct": float, "paidInPct": float,
                 "finDebtPct": float, "opFundingPct": float}, ...
            ],
            "diagnosis": str,
        }
    """
    accounts = [
        "자산총계",
        "자본총계",
        "이익잉여금",
        "자본금",
        "자본잉여금",
        "부채총계",
        "단기차입금",
        "장기차입금",
        "사채",
        "매입채무",
        "선수금",
        "계약부채",
        "선수수익",
    ]
    result = company.select("BS", accounts)
    parsed = _toDict(result)
    if parsed is None:
        return None

    data, allPeriods = parsed
    taRow = data.get("자산총계")
    if taRow is None:
        return None

    reRow = data.get("이익잉여금", {})
    pcRow = data.get("자본금", {})
    csRow = data.get("자본잉여금", {})
    eqRow = data.get("자본총계", {})
    liabRow = data.get("부채총계", {})
    stbRow = data.get("단기차입금", {})
    ltbRow = data.get("장기차입금", {})
    bondRow = data.get("사채", {})
    apRow = data.get("매입채무", {})
    advRow = data.get("선수금", {})
    clRow = data.get("계약부채", {})
    diRow = data.get("선수수익", {})

    yCols = _annualCols(allPeriods, _MAX_YEARS)
    if not yCols:
        yCols = _quarterlyCols(allPeriods, _MAX_YEARS)
    if not yCols:
        return None

    history = []
    latest = None

    for col in yCols:
        ta = taRow.get(col)
        if ta is None or ta <= 0:
            continue

        retained = reRow.get(col) or 0
        paidIn = (pcRow.get(col) or 0) + (csRow.get(col) or 0)
        finDebt = (stbRow.get(col) or 0) + (ltbRow.get(col) or 0) + (bondRow.get(col) or 0)
        opFunding = (apRow.get(col) or 0) + (advRow.get(col) or 0) + (clRow.get(col) or 0) + (diRow.get(col) or 0)

        equity = eqRow.get(col) or 0
        otherEquity = max(0, equity - retained - paidIn)
        liab = liabRow.get(col) or 0
        otherLiab = max(0, liab - finDebt - opFunding)

        entry = {
            "period": col,
            "retainedPct": retained / ta * 100,
            "paidInPct": paidIn / ta * 100,
            "finDebtPct": finDebt / ta * 100,
            "opFundingPct": opFunding / ta * 100,
            "otherLiabPct": otherLiab / ta * 100,
            "otherEquityPct": otherEquity / ta * 100,
        }
        history.append(entry)

        if latest is None:
            latest = {
                "totalAssets": ta,
                "retained": retained,
                "retainedPct": entry["retainedPct"],
                "paidIn": paidIn,
                "paidInPct": entry["paidInPct"],
                "finDebt": finDebt,
                "finDebtPct": entry["finDebtPct"],
                "opFunding": opFunding,
                "opFundingPct": entry["opFundingPct"],
                "otherLiab": otherLiab,
                "otherLiabPct": entry["otherLiabPct"],
                "otherEquity": otherEquity,
                "otherEquityPct": entry["otherEquityPct"],
            }

    if latest is None:
        return None

    # 진단: 내부유보 vs 금융차입 비중으로 자금조달 성격 판단
    rPct = latest["retainedPct"]
    fPct = latest["finDebtPct"]
    if rPct >= 50:
        diagnosis = "자기 힘으로 성장 — 이익잉여금이 자산의 절반 이상"
    elif rPct >= 30 and fPct < 30:
        diagnosis = "내부유보 중심 — 차입 의존도 낮음"
    elif fPct >= 40:
        diagnosis = "차입 의존 — 금융부채가 자산의 40% 이상"
    elif fPct >= rPct:
        diagnosis = "외부 조달 우위 — 금융차입이 내부유보를 초과"
    else:
        diagnosis = "균형 조달 — 내부유보와 외부 조달이 혼합"

    # 보충 지표: 순차입금/EBITDA, 암묵적 차입금리
    netDebtEbitda = _calcNetDebtEbitda(company, latest["finDebt"])
    impliedRate = _calcImpliedBorrowingRate(company, latest["finDebt"])

    result = {"latest": latest, "history": history, "diagnosis": diagnosis}
    if netDebtEbitda is not None:
        result["netDebtEbitda"] = netDebtEbitda
    if impliedRate is not None:
        result["impliedBorrowingRate"] = impliedRate

    # 비중 변화 방향 (금융차입 비중이 늘고 있는가)
    if len(history) >= 2:
        newest = history[0]["finDebtPct"]
        oldest = history[-1]["finDebtPct"]
        diff = newest - oldest
        if diff > 5:
            result["leverageTrend"] = (
                f"금융차입 비중 +{diff:.0f}pp 증가 ({history[-1]['period']}→{history[0]['period']})"
            )
        elif diff < -5:
            result["leverageTrend"] = (
                f"금융차입 비중 {diff:.0f}pp 감소 ({history[-1]['period']}→{history[0]['period']})"
            )

    return result


def _latestAnnualVal(company, stmt: str, accountName: str) -> float | None:
    """select(stmt, [accountName])에서 최신 연도 값을 꺼낸다."""
    result = company.select(stmt, [accountName])
    parsed = _toDict(result)
    if parsed is None:
        return None
    data, allPeriods = parsed
    row = data.get(accountName)
    if row is None:
        return None
    yCols = _annualCols(allPeriods, 1)
    if not yCols:
        return None
    return row.get(yCols[0])


def _calcNetDebtEbitda(company, finDebt: float) -> float | None:
    """순차입금/EBITDA — 차입 감당 능력."""
    cash = _latestAnnualVal(company, "BS", "현금및현금성자산") or 0
    netDebt = finDebt - cash
    if netDebt <= 0:
        return 0.0  # 순현금
    opIncome = _latestAnnualVal(company, "IS", "영업이익")
    if opIncome is not None and opIncome > 0:
        return netDebt / opIncome  # EBITDA 대신 영업이익 기반 (보수적)
    return None


def _calcImpliedBorrowingRate(company, finDebt: float) -> float | None:
    """암묵적 차입금리(%) — 금융비용/금융부채."""
    if finDebt <= 0:
        return None
    ie = _latestAnnualVal(company, "IS", "이자비용") or _latestAnnualVal(company, "IS", "금융비용")
    if ie is None or ie <= 0:
        return None
    return ie / finDebt * 100


def calcCapitalOverview(company) -> dict | None:
    """총자산/총부채/자기자본/순차입금 스냅샷.

    반환::

        {"metrics": [(label, value_str), ...]}
    """
    ratios = _getRatios(company)
    if ratios is None:
        return None

    metrics = []

    ta = getattr(ratios, "totalAssets", None)
    if ta is not None:
        metrics.append(("총자산", _fmtAmt(ta)))

    tl = getattr(ratios, "totalLiabilities", None)
    dr = getattr(ratios, "debtRatio", None)
    if tl is not None:
        label = _fmtAmt(tl)
        if dr is not None:
            label += f" (부채비율 {dr:.0f}%)"
        metrics.append(("총부채", label))

    te = getattr(ratios, "totalEquity", None)
    er = getattr(ratios, "equityRatio", None)
    if te is not None:
        label = _fmtAmt(te)
        if er is not None:
            label += f" (자기자본비율 {er:.0f}%)"
        metrics.append(("자기자본", label))

    nd = getattr(ratios, "netDebt", None)
    if nd is not None:
        if nd < 0:
            metrics.append(("순차입금", f"{_fmtAmt(abs(nd))} (순현금)"))
        else:
            ndr = getattr(ratios, "netDebtRatio", None)
            label = _fmtAmt(nd)
            if ndr is not None:
                label += f" (순차입금비율 {ndr:.0f}%)"
            metrics.append(("순차입금", label))

    if not metrics:
        return None

    return {"metrics": metrics}


def calcCapitalTimeline(company) -> dict | None:
    """자본총계·이익잉여금 시계열.

    반환::

        {"tables": [(label, rows, cols), ...]}
    """
    result = company.select("BS", ["자본총계", "이익잉여금"])
    parsed = _toDict(result)
    if parsed is None or "자본총계" not in parsed[0]:
        return None

    data, allPeriods = parsed
    equityRow = data["자본총계"]
    retainedRow = data.get("이익잉여금")

    tables = []
    yCols = _annualCols(allPeriods, _MAX_YEARS)
    if yCols:
        yearTable = _buildCapitalTable(equityRow, retainedRow, yCols)
        if yearTable:
            tables.append(("연도별", yearTable, yCols))

    qCols = _quarterlyCols(allPeriods, _MAX_QUARTERS)
    if qCols:
        qtrTable = _buildCapitalTable(equityRow, retainedRow, qCols)
        if qtrTable:
            tables.append(("분기별", qtrTable, qCols))

    if not tables:
        return None

    return {"tables": tables}


def _buildCapitalTable(equityRow: dict, retainedRow: dict | None, cols: list[str]) -> list[dict]:
    """자본구조 테이블 행 구성."""
    rows: list[dict] = []
    rows.append({"": "자본총계", **{c: equityRow.get(c) for c in cols}})

    if retainedRow:
        rows.append({"": "이익잉여금", **{c: retainedRow.get(c) for c in cols}})

        paidInRow: dict = {"": "자본금+잉여금"}
        for c in cols:
            eq = equityRow.get(c)
            re = retainedRow.get(c)
            if eq is not None and re is not None:
                paidInRow[c] = eq - re
            else:
                paidInRow[c] = None
        rows.append(paidInRow)

        pctRow: dict = {"": "→ 내부유보 비중"}
        for c in cols:
            eq = equityRow.get(c)
            re = retainedRow.get(c)
            if eq and re and eq != 0:
                pctRow[c] = f"{re / eq * 100:.0f}%"
            else:
                pctRow[c] = "-"
        rows.append(pctRow)

    return rows


def calcDebtTimeline(company) -> dict | None:
    """부채총계·금융부채·영업부채 시계열.

    반환::

        {"tables": [(label, rows, cols), ...]}
    """
    result = company.select("BS", ["부채총계", "단기차입금", "장기차입금", "사채"])
    parsed = _toDict(result)
    if parsed is None or "부채총계" not in parsed[0]:
        return None

    data, allPeriods = parsed
    liabRow = data["부채총계"]
    stbRow = data.get("단기차입금")
    ltbRow = data.get("장기차입금")
    bondRow = data.get("사채")

    tables = []
    yCols = _annualCols(allPeriods, _MAX_YEARS)
    if yCols:
        yearTable = _buildDebtTable(liabRow, stbRow, ltbRow, bondRow, yCols)
        if yearTable:
            tables.append(("연도별", yearTable, yCols))

    qCols = _quarterlyCols(allPeriods, _MAX_QUARTERS)
    if qCols:
        qtrTable = _buildDebtTable(liabRow, stbRow, ltbRow, bondRow, qCols)
        if qtrTable:
            tables.append(("분기별", qtrTable, qCols))

    if not tables:
        return None

    return {"tables": tables}


def _buildDebtTable(liabRow: dict, stbRow, ltbRow, bondRow, cols: list[str]) -> list[dict]:
    """부채구조 테이블 행 구성."""
    rows: list[dict] = []
    rows.append({"": "부채총계", **{c: liabRow.get(c) for c in cols}})

    finDebtRow: dict = {"": "금융부채"}
    hasFinDebt = False
    for c in cols:
        stb = (stbRow or {}).get(c)
        ltb = (ltbRow or {}).get(c)
        bond = (bondRow or {}).get(c)
        parts = [v for v in [stb, ltb, bond] if v is not None]
        if parts:
            finDebtRow[c] = sum(parts)
            hasFinDebt = True
        else:
            finDebtRow[c] = None

    if hasFinDebt:
        opDebtRow: dict = {"": "영업부채"}
        for c in cols:
            tl = liabRow.get(c)
            fd = finDebtRow.get(c)
            if tl is not None and fd is not None:
                opDebtRow[c] = tl - fd
            else:
                opDebtRow[c] = None
        rows.append(opDebtRow)
        rows.append(finDebtRow)

        pctRow: dict = {"": "→ 금융부채 비중"}
        for c in cols:
            tl = liabRow.get(c)
            fd = finDebtRow.get(c)
            if tl and fd and tl != 0:
                pctRow[c] = f"{fd / tl * 100:.0f}%"
            else:
                pctRow[c] = "-"
        rows.append(pctRow)

    return rows


def calcInterestBurden(company) -> dict | None:
    """이자보상배율·이자비용.

    반환::

        {"metrics": [(label, value_str), ...]}
    """
    ratios = _getRatios(company)
    if ratios is None:
        return None

    metrics = []

    ic = getattr(ratios, "interestCoverage", None)
    if ic is not None:
        if ic >= 10:
            quality = "우수"
        elif ic >= 3:
            quality = "안정"
        elif ic >= 1.5:
            quality = "주의"
        else:
            quality = "위험"
        metrics.append(("이자보상배율", f"{ic:.1f}배 — {quality}"))

    ie = getattr(ratios, "interestExpense", None)
    if ie is not None:
        metrics.append(("이자비용", _fmtAmt(ie)))

    if not metrics:
        return None

    return {"metrics": metrics}


def calcLiquidity(company) -> dict | None:
    """유동비율·당좌비율·현금비율·순운전자본.

    반환::

        {"metrics": [(label, value_str), ...]}
    """
    ratios = _getRatios(company)
    if ratios is None:
        return None

    metrics = []

    cr = getattr(ratios, "currentRatio", None)
    if cr is not None:
        quality = "안정" if cr >= 150 else "보통" if cr >= 100 else "주의"
        metrics.append(("유동비율", f"{cr:.0f}% — {quality}"))

    qr = getattr(ratios, "quickRatio", None)
    if qr is not None:
        metrics.append(("당좌비율", f"{qr:.0f}%"))

    car = getattr(ratios, "cashRatio", None)
    if car is not None:
        metrics.append(("현금비율", f"{car:.0f}%"))

    wc = getattr(ratios, "workingCapital", None)
    if wc is not None:
        metrics.append(("순운전자본", _fmtAmt(wc)))

    if not metrics:
        return None

    return {"metrics": metrics}


def calcCashFlowStructure(company) -> dict | None:
    """영업CF/투자CF/재무CF + FCF + CF 패턴.

    반환::

        {
            "tableRows": [dict, ...],
            "cols": [str, ...],
            "pattern": str | None,
            "metrics": [(label, value_str), ...] | None,
        }
    """
    result = company.select("CF", ["영업활동현금흐름", "투자활동현금흐름", "재무활동현금흐름", "유형자산의취득"])
    parsed = _toDict(result)
    if parsed is None or "영업활동현금흐름" not in parsed[0]:
        return None

    data, allPeriods = parsed
    ocfRow = data["영업활동현금흐름"]
    icfRow = data.get("투자활동현금흐름")
    fcfRow = data.get("재무활동현금흐름")
    capexRow = data.get("유형자산의취득")

    qCols = _quarterlyCols(allPeriods, _MAX_QUARTERS)
    if not qCols:
        return None

    rawRows: list[dict] = []
    rawRows.append({"": "영업CF", **{c: ocfRow.get(c) for c in qCols}})
    if icfRow:
        rawRows.append({"": "투자CF", **{c: icfRow.get(c) for c in qCols}})
    if fcfRow:
        rawRows.append({"": "재무CF", **{c: fcfRow.get(c) for c in qCols}})
    if capexRow:
        freeRow: dict = {"": "FCF"}
        for c in qCols:
            ocf = ocfRow.get(c)
            capex = capexRow.get(c)
            if ocf is not None and capex is not None:
                free = ocf + capex if capex < 0 else ocf - capex
                freeRow[c] = free
            else:
                freeRow[c] = None
        rawRows.append(freeRow)

    # CF 패턴 분류
    latestCol = qCols[0]
    ocfSign = _sign(ocfRow.get(latestCol))
    icfSign = _sign((icfRow or {}).get(latestCol))
    fcfSign = _sign((fcfRow or {}).get(latestCol))
    pattern = _classifyCfPattern(ocfSign, icfSign, fcfSign)

    # 추가 지표
    ratios = _getRatios(company)
    metrics = None
    if ratios is not None:
        extra = []
        ocfm = getattr(ratios, "operatingCfMargin", None)
        if ocfm is not None:
            extra.append(("영업CF 마진", f"{ocfm:.1f}%"))
        cxr = getattr(ratios, "capexRatio", None)
        if cxr is not None:
            extra.append(("CAPEX/매출", f"{cxr:.1f}%"))
        ftor = getattr(ratios, "fcfToOcfRatio", None)
        if ftor is not None:
            extra.append(("FCF/OCF", f"{ftor:.0f}%"))
        if extra:
            metrics = extra

    return {
        "tableRows": rawRows,
        "cols": qCols,
        "pattern": pattern,
        "metrics": metrics,
    }


def _sign(val) -> str:
    """양/음/0 부호."""
    if val is None:
        return "?"
    if val > 0:
        return "+"
    if val < 0:
        return "-"
    return "0"


def _classifyCfPattern(ocf: str, icf: str, fcf: str) -> str | None:
    """영업/투자/재무 CF 부호 조합으로 패턴 분류."""
    patterns = {
        ("+", "-", "-"): "성숙형 — 영업으로 벌어 투자하고 부채 상환",
        ("+", "-", "+"): "확장형 — 영업 + 외부 조달로 적극 투자",
        ("+", "+", "-"): "구조조정형 — 자산 매각하며 부채 상환",
        ("-", "-", "+"): "위기형 — 영업 적자를 외부 차입으로 메움",
        ("-", "+", "+"): "축소형 — 자산 매각 + 차입으로 영업 적자 보전",
        ("-", "+", "-"): "전환형 — 자산 매각으로 부채 상환, 영업 회복 필요",
    }
    return patterns.get((ocf, icf, fcf))


def calcDistressIndicators(company) -> dict | None:
    """Altman Z, Ohlson O, Piotroski F, Springate S.

    반환::

        {"metrics": [(label, value_str), ...]}
    """
    ratios = _getRatios(company)
    if ratios is None:
        return None

    metrics = []

    az = getattr(ratios, "altmanZScore", None)
    if az is None:
        az = getattr(ratios, "altmanZppScore", None)
    if az is not None:
        if az > 2.99:
            quality = "안전"
        elif az > 1.81:
            quality = "회색지대"
        else:
            quality = "부실 위험"
        metrics.append(("Altman Z", f"{az:.2f} — {quality}"))

    op = getattr(ratios, "ohlsonProbability", None)
    if op is not None:
        metrics.append(("Ohlson 부실확률", f"{op:.1f}%"))
    else:
        os_ = getattr(ratios, "ohlsonOScore", None)
        if os_ is not None:
            metrics.append(("Ohlson O-Score", f"{os_:.2f}"))

    pf = getattr(ratios, "piotroskiFScore", None)
    if pf is not None:
        maxF = getattr(ratios, "piotroskiMaxScore", 9)
        if pf >= 7:
            quality = "재무 건전"
        elif pf >= 4:
            quality = "보통"
        else:
            quality = "재무 약화"
        metrics.append(("Piotroski F", f"{pf}/{maxF} — {quality}"))

    ss = getattr(ratios, "springateSScore", None)
    if ss is not None:
        quality = "안전" if ss > 0.862 else "부실 위험"
        metrics.append(("Springate S", f"{ss:.2f} — {quality}"))

    if not metrics:
        return None

    return {"metrics": metrics}


def calcCapitalFlags(company) -> list[tuple[str, str]]:
    """자금조달 관련 경고/기회 플래그. [(텍스트, "warning"|"opportunity"), ...]."""
    flags: list[tuple[str, str]] = []

    ratios = _getRatios(company)
    if ratios is None:
        return flags

    dr = getattr(ratios, "debtRatio", None)
    if dr is not None and dr > 200:
        flags.append((f"고부채 (부채비율 {dr:.0f}%)", "warning"))

    ic = getattr(ratios, "interestCoverage", None)
    if ic is not None and ic < 3:
        severity = "심각" if ic < 1.5 else "주의"
        flags.append((f"이자보상 {severity} ({ic:.1f}배)", "warning"))

    cr = getattr(ratios, "currentRatio", None)
    if cr is not None and cr < 100:
        flags.append((f"유동성 위기 (유동비율 {cr:.0f}%)", "warning"))

    az = getattr(ratios, "altmanZScore", None) or getattr(ratios, "altmanZppScore", None)
    if az is not None and az < 1.81:
        flags.append((f"Altman Z 부실 경계 ({az:.2f})", "warning"))

    pf = getattr(ratios, "piotroskiFScore", None)
    if pf is not None and pf < 3:
        flags.append((f"Piotroski F 재무 약화 ({pf}/9)", "warning"))

    # 금융부채 비중 (BS에서 직접 계산)
    flagResult = company.select("BS", ["부채총계", "단기차입금", "장기차입금", "사채", "자본총계", "이익잉여금"])
    flagParsed = _toDict(flagResult)
    if flagParsed is not None and "부채총계" in flagParsed[0]:
        data = flagParsed[0]
        liabRow = data["부채총계"]
        stbRow = data.get("단기차입금")
        ltbRow = data.get("장기차입금")
        bondRow = data.get("사채")
        finDebtPct = _calcFinDebtPct(liabRow, stbRow, ltbRow, bondRow)
        if finDebtPct is not None and finDebtPct > 50:
            flags.append((f"금융부채 비중 {finDebtPct:.0f}% — 이자 부담 부채 높음", "warning"))

        equityRow = data.get("자본총계")
        retainedRow = data.get("이익잉여금")
        retainedPct = _calcRetainedPct(equityRow, retainedRow)
        if retainedPct is not None and retainedPct > 70:
            flags.append((f"내부유보 비중 {retainedPct:.0f}% — 자기 힘으로 성장", "opportunity"))

    nd = getattr(ratios, "netDebt", None)
    if nd is not None and nd < 0:
        flags.append(("순현금 상태", "opportunity"))

    if ic is not None and ic > 10:
        flags.append((f"이자보상 우수 ({ic:.0f}배)", "opportunity"))

    if pf is not None and pf >= 7:
        flags.append((f"Piotroski F 재무 건전 ({pf}/9)", "opportunity"))

    return flags


# ── 내부 헬퍼 ──


def _calcRetainedPct(equityRow, retainedRow) -> float | None:
    """이익잉여금 / 자본총계 비중 (%)."""
    if equityRow is None or retainedRow is None:
        return None
    for key in equityRow:
        eq = equityRow.get(key)
        re = retainedRow.get(key)
        if eq and re and eq != 0:
            return re / eq * 100
    return None


def _calcFinDebtPct(liabRow, stbRow, ltbRow, bondRow) -> float | None:
    """금융부채 / 부채총계 비중 (%) — 최신 기간."""
    if liabRow is None:
        return None
    for key in liabRow:
        tl = liabRow.get(key)
        if tl is None or tl == 0:
            continue
        stb = (stbRow or {}).get(key)
        ltb = (ltbRow or {}).get(key)
        bond = (bondRow or {}).get(key)
        parts = [v for v in [stb, ltb, bond] if v is not None]
        if parts:
            return sum(parts) / tl * 100
    return None
