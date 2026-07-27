"""IS / BS / CF 가공.

각 함수는 norm + nPeriods + periodKind 받아 dict 반환 — *raw 가공 결과*.
views.py 가 이걸 받아 표준 View JSON 으로 포장.
"""

from __future__ import annotations

import polars as pl

from dartlab.synth.rowAccess import safeDiv
from dartlab.viz.display.finance.accounts import extractSeries
from dartlab.viz.display.finance.periods import lastNPeriods
from dartlab.viz.display.finance.schema import PeriodKind


def _gp(rev: float | None, cos: float | None, gp: float | None) -> float | None:
    """매출총이익 — 직접 없으면 (매출 - 매출원가)."""
    if gp is not None:
        return gp
    if rev is not None and cos is not None:
        return rev - cos
    return None


# ═══════════════════════════════════════════════════════════
# IS 4
# ═══════════════════════════════════════════════════════════


def isOverview(norm: pl.DataFrame, nPeriods: int, periodKind: PeriodKind) -> dict:
    """매출/매출총이익/영업이익/순이익 + 마진 3종 (GPM/OPM/NPM).

    Returns:
        {periods, rows: [{key, label, values, unit}]}
    """
    periods = lastNPeriods(norm, nPeriods, periodKind)
    rev = extractSeries(norm, "revenue", periods)
    cos = extractSeries(norm, "costOfSales", periods)
    gp = extractSeries(norm, "grossProfit", periods)
    op = extractSeries(norm, "operatingIncome", periods)
    ni = extractSeries(norm, "netIncome", periods)

    gpVals = [_gp(rev[i], cos[i], gp[i]) for i in range(len(periods))]
    gpm = [(safeDiv(gpVals[i], rev[i]) or 0) * 100 if rev[i] else None for i in range(len(periods))]
    opm = [(safeDiv(op[i], rev[i]) or 0) * 100 if rev[i] else None for i in range(len(periods))]
    npm = [(safeDiv(ni[i], rev[i]) or 0) * 100 if rev[i] else None for i in range(len(periods))]

    return {
        "periods": periods,
        "rows": [
            {"key": "revenue", "label": "매출액", "values": rev, "unit": "원"},
            {"key": "costOfSales", "label": "매출원가", "values": cos, "unit": "원"},
            {"key": "grossProfit", "label": "매출총이익", "values": gpVals, "unit": "원"},
            {"key": "operatingIncome", "label": "영업이익", "values": op, "unit": "원"},
            {"key": "netIncome", "label": "당기순이익", "values": ni, "unit": "원"},
            {"key": "grossMargin", "label": "매출총이익률", "values": gpm, "unit": "%"},
            {"key": "operatingMargin", "label": "영업이익률", "values": opm, "unit": "%"},
            {"key": "netMargin", "label": "순이익률", "values": npm, "unit": "%"},
        ],
    }


def isRevenueTrend(norm: pl.DataFrame, nPeriods: int, periodKind: PeriodKind) -> dict:
    """매출 추세 + YoY 성장률."""
    periods = lastNPeriods(norm, nPeriods, periodKind)
    rev = extractSeries(norm, "revenue", periods)
    yoy: list[float | None] = [None]
    for i in range(1, len(rev)):
        prev, curr = rev[i - 1], rev[i]
        if prev is None or curr is None or prev <= 0:
            yoy.append(None)
        else:
            yoy.append((curr - prev) / prev * 100)
    return {"periods": periods, "revenue": rev, "yoy": yoy}


def isMarginTrend(norm: pl.DataFrame, nPeriods: int, periodKind: PeriodKind) -> dict:
    """이익률 추세 — GPM/OPM/NPM."""
    periods = lastNPeriods(norm, nPeriods, periodKind)
    rev = extractSeries(norm, "revenue", periods)
    gp = extractSeries(norm, "grossProfit", periods)
    cos = extractSeries(norm, "costOfSales", periods)
    op = extractSeries(norm, "operatingIncome", periods)
    ni = extractSeries(norm, "netIncome", periods)
    gpVals = [_gp(rev[i], cos[i], gp[i]) for i in range(len(periods))]
    gpm = [(safeDiv(gpVals[i], rev[i]) or 0) * 100 if rev[i] else None for i in range(len(periods))]
    opm = [(safeDiv(op[i], rev[i]) or 0) * 100 if rev[i] else None for i in range(len(periods))]
    npm = [(safeDiv(ni[i], rev[i]) or 0) * 100 if rev[i] else None for i in range(len(periods))]
    return {"periods": periods, "gpm": gpm, "opm": opm, "npm": npm}


def isCostStructure(norm: pl.DataFrame, nPeriods: int, periodKind: PeriodKind) -> dict:
    """비용 구조 — 매출원가/판관비/연구개발/금융비용."""
    periods = lastNPeriods(norm, nPeriods, periodKind)
    return {
        "periods": periods,
        "costOfSales": extractSeries(norm, "costOfSales", periods),
        "sga": extractSeries(norm, "sga", periods),
        "rnd": extractSeries(norm, "rnd", periods),
        "financeCosts": extractSeries(norm, "financeCosts", periods),
    }


# ═══════════════════════════════════════════════════════════
# BS 3
# ═══════════════════════════════════════════════════════════


def bsOverview(norm: pl.DataFrame, nPeriods: int, periodKind: PeriodKind) -> dict:
    """자산/부채/자본 총계 + 유동/비유동 + 현금."""
    periods = lastNPeriods(norm, nPeriods, periodKind)
    from dartlab.viz.display.finance.accounts import standard

    keys = (
        "assets",
        "currentAssets",
        "nonCurrentAssets",
        "liabilities",
        "currentLiabilities",
        "nonCurrentLiabilities",
        "equity",
        "cash",
    )
    rows = []
    for k in keys:
        rows.append(
            {
                "key": k,
                "label": standard(k).label,
                "values": extractSeries(norm, k, periods),
                "unit": "원",
            }
        )
    return {"periods": periods, "rows": rows}


def bsComposition(norm: pl.DataFrame, period: str | None, periodKind: PeriodKind) -> dict:
    """자산 / (부채+자본) 구성 — 단일 기간.

    Returns:
        {period, assets: [{key, label, value}], liabilitiesEquity: [{key, label, value}]}
    """
    if period is None:
        ps = lastNPeriods(norm, 1, periodKind)
        period = ps[-1] if ps else None
    if period is None:
        return {"period": None, "assets": [], "liabilitiesEquity": []}

    def _val(key: str) -> float | None:
        return extractSeries(norm, key, [period])[0]

    cur, nonCur = _val("currentAssets"), _val("nonCurrentAssets")
    cash, inv, rec = _val("cash"), _val("inventories"), _val("receivables")
    curLiab, nonCurLiab = _val("currentLiabilities"), _val("nonCurrentLiabilities")
    equity, shortD, longD = _val("equity"), _val("shortDebt"), _val("longDebt")
    retained = _val("retainedEarnings")

    assets: list[dict] = []
    if cash is not None:
        assets.append({"key": "cash", "label": "현금성자산", "value": cash})
    if rec is not None:
        assets.append({"key": "receivables", "label": "매출채권", "value": rec})
    if inv is not None:
        assets.append({"key": "inventories", "label": "재고자산", "value": inv})
    otherCur = (cur or 0) - sum(v for v in (cash, rec, inv) if v is not None)
    if cur is not None and otherCur > 0:
        assets.append({"key": "otherCurrentAssets", "label": "기타유동자산", "value": otherCur})
    if nonCur is not None:
        assets.append({"key": "nonCurrentAssets", "label": "비유동자산", "value": nonCur})

    liabEq: list[dict] = []
    if shortD is not None:
        liabEq.append({"key": "shortDebt", "label": "단기차입금", "value": shortD})
    otherCurL = (curLiab or 0) - (shortD or 0)
    if curLiab is not None and otherCurL > 0:
        liabEq.append({"key": "otherCurrentLiabilities", "label": "기타유동부채", "value": otherCurL})
    if longD is not None:
        liabEq.append({"key": "longDebt", "label": "장기차입금", "value": longD})
    otherNonCurL = (nonCurLiab or 0) - (longD or 0)
    if nonCurLiab is not None and otherNonCurL > 0:
        liabEq.append({"key": "otherNonCurrentLiabilities", "label": "기타비유동부채", "value": otherNonCurL})
    if retained is not None:
        liabEq.append({"key": "retainedEarnings", "label": "이익잉여금", "value": retained})
    otherEq = (equity or 0) - (retained or 0)
    if equity is not None and otherEq > 0:
        liabEq.append({"key": "otherEquity", "label": "기타자본", "value": otherEq})

    return {"period": period, "assets": assets, "liabilitiesEquity": liabEq}


def bsLeverage(norm: pl.DataFrame, nPeriods: int, periodKind: PeriodKind) -> dict:
    """레버리지 — D/E · D/A · 유동비."""
    periods = lastNPeriods(norm, nPeriods, periodKind)
    assets = extractSeries(norm, "assets", periods)
    liab = extractSeries(norm, "liabilities", periods)
    eq = extractSeries(norm, "equity", periods)
    curA = extractSeries(norm, "currentAssets", periods)
    curL = extractSeries(norm, "currentLiabilities", periods)
    debtToEquity = [(safeDiv(liab[i], eq[i]) or 0) * 100 if liab[i] and eq[i] else None for i in range(len(periods))]
    debtToAssets = [
        (safeDiv(liab[i], assets[i]) or 0) * 100 if liab[i] and assets[i] else None for i in range(len(periods))
    ]
    currentRatio = [
        (safeDiv(curA[i], curL[i]) or 0) * 100 if curA[i] and curL[i] else None for i in range(len(periods))
    ]
    return {
        "periods": periods,
        "debtToEquity": debtToEquity,
        "debtToAssets": debtToAssets,
        "currentRatio": currentRatio,
    }


# ═══════════════════════════════════════════════════════════
# CF 3
# ═══════════════════════════════════════════════════════════


def cfOverview(norm: pl.DataFrame, nPeriods: int, periodKind: PeriodKind) -> dict:
    """영업/투자/재무 + 순현금변동 + FCF."""
    periods = lastNPeriods(norm, nPeriods, periodKind)
    op = extractSeries(norm, "cfOperating", periods)
    inv = extractSeries(norm, "cfInvesting", periods)
    fin = extractSeries(norm, "cfFinancing", periods)
    capex = extractSeries(norm, "capex", periods)
    netChange = [
        (op[i] or 0) + (inv[i] or 0) + (fin[i] or 0) if any(v is not None for v in (op[i], inv[i], fin[i])) else None
        for i in range(len(periods))
    ]
    fcf = [(op[i] or 0) - abs(capex[i] or 0) if op[i] is not None else None for i in range(len(periods))]
    return {
        "periods": periods,
        "rows": [
            {"key": "cfOperating", "label": "영업활동", "values": op, "unit": "원"},
            {"key": "cfInvesting", "label": "투자활동", "values": inv, "unit": "원"},
            {"key": "cfFinancing", "label": "재무활동", "values": fin, "unit": "원"},
            {"key": "netChange", "label": "순현금증감", "values": netChange, "unit": "원"},
            {"key": "fcf", "label": "잉여현금흐름", "values": fcf, "unit": "원"},
        ],
    }


def cfWaterfall(norm: pl.DataFrame, period: str | None, periodKind: PeriodKind) -> dict:
    """현금 waterfall — 기초/영업/투자/재무/기말.

    Returns:
        {period, steps: [{key, label, value, measure}]}
        measure: absolute | relative | total
    """
    if period is None:
        ps = lastNPeriods(norm, 1, periodKind)
        period = ps[-1] if ps else None
    if period is None:
        return {"period": None, "steps": []}

    op = extractSeries(norm, "cfOperating", [period])[0]
    inv = extractSeries(norm, "cfInvesting", [period])[0]
    fin = extractSeries(norm, "cfFinancing", [period])[0]
    cash = extractSeries(norm, "cash", [period])[0]

    startCash = (cash or 0) - ((op or 0) + (inv or 0) + (fin or 0))
    return {
        "period": period,
        "steps": [
            {"key": "startCash", "label": "기초현금", "value": startCash, "measure": "absolute"},
            {"key": "cfOperating", "label": "영업활동", "value": op, "measure": "relative"},
            {"key": "cfInvesting", "label": "투자활동", "value": inv, "measure": "relative"},
            {"key": "cfFinancing", "label": "재무활동", "value": fin, "measure": "relative"},
            {"key": "endCash", "label": "기말현금", "value": cash, "measure": "total"},
        ],
    }


def cfFreeCashFlow(norm: pl.DataFrame, nPeriods: int, periodKind: PeriodKind) -> dict:
    """FCF = 영업CF - CapEx + 영업CF/매출."""
    periods = lastNPeriods(norm, nPeriods, periodKind)
    op = extractSeries(norm, "cfOperating", periods)
    capex = extractSeries(norm, "capex", periods)
    rev = extractSeries(norm, "revenue", periods)
    fcf = [(op[i] or 0) - abs(capex[i] or 0) if op[i] is not None else None for i in range(len(periods))]
    cfToRev = [
        (op[i] / rev[i] * 100) if op[i] is not None and rev[i] not in (None, 0) else None for i in range(len(periods))
    ]
    return {
        "periods": periods,
        "operating": op,
        "capex": [abs(v) if v is not None else None for v in capex],
        "fcf": fcf,
        "cfToRevenue": cfToRev,
    }


# ═══════════════════════════════════════════════════════════
# BS 추가 (catalog 의 trend 카드용)
# ═══════════════════════════════════════════════════════════


def bsCompositionTrend(norm: pl.DataFrame, nPeriods: int, periodKind: PeriodKind) -> dict:
    """자산·부채·자본 5 시계열 — catalog `balanceCompositionTrend` 카드 입력.

    `bsComposition` 은 단일 기간 breakdown 이라 stacked-bar trend 카드와 모양이
    다르다. 이 함수는 nPeriods 기간에 걸쳐 5 그룹 (currentAssets,
    nonCurrentAssets / currentLiabilities, nonCurrentLiabilities, equity) 의
    시계열을 dict 로 반환 — builder 가 seriesPlan 의 key 로 lookup.

    Returns:
        {periods, currentAssets, nonCurrentAssets, currentLiabilities,
         nonCurrentLiabilities, equity}
    """
    periods = lastNPeriods(norm, nPeriods, periodKind)
    return {
        "periods": periods,
        "currentAssets": extractSeries(norm, "currentAssets", periods),
        "nonCurrentAssets": extractSeries(norm, "nonCurrentAssets", periods),
        "currentLiabilities": extractSeries(norm, "currentLiabilities", periods),
        "nonCurrentLiabilities": extractSeries(norm, "nonCurrentLiabilities", periods),
        "equity": extractSeries(norm, "equity", periods),
    }


def bsCompositionFull(norm: pl.DataFrame, nPeriods: int, periodKind: PeriodKind) -> dict:
    """자산 + 부채 + 자본 통합 시계열 — 한 카드 안 두 stack 그룹용.

    회계 등식 자산 = 부채 + 자본 을 두 stacked bar 가 같은 높이로 시각화.

    자산 stack (7 series): 현금 / 단기금융자산 / 매출채권 / 재고자산 /
        영업자산기타 (PPE+무형+운권+CIP) / 투자자산 / 기타자산.
    부채자본 stack (4 series): 영업부채 / 금융부채 / 이익잉여금 / 기타자본.

    Returns:
        {periods, cash, stFinancial, receivables, inventory, opAssetCore,
         investments, otherAssets, opLiab, finDebt, retainedEarnings, otherEquity}
    """
    from dartlab.viz.display.finance.accounts import extractSeries as _extract

    periods = lastNPeriods(norm, nPeriods, periodKind)

    # 자산 측
    totalAssets = _extract(norm, "assets", periods)
    cash = _extract(norm, "cash", periods)
    receivables = _extract(norm, "receivables", periods)
    inventory = _extract(norm, "inventories", periods)

    # 부채 측
    totalLiab = _extract(norm, "liabilities", periods)
    shortDebt = _extract(norm, "shortDebt", periods)
    longDebt = _extract(norm, "longDebt", periods)

    # 자본 측
    equity = _extract(norm, "equity", periods)
    retainedEarnings = _extract(norm, "retainedEarnings", periods)

    n = len(periods)
    finDebt: list[float | None] = []
    opLiab: list[float | None] = []
    otherEquity: list[float | None] = []
    investments: list[float | None] = [None] * n
    opAssetCore: list[float | None] = []
    otherAssets: list[float | None] = []
    stFinancial: list[float | None] = [None] * n  # 표준 미존재 → 별도 키워드 매칭 시 0

    for i in range(n):
        # 금융부채 = 단기 + 장기
        s = shortDebt[i]
        l = longDebt[i]
        fd: float | None
        if s is None and l is None:
            fd = None
        else:
            fd = (s or 0) + (l or 0)
        finDebt.append(fd)

        # 영업부채 = 부채총계 - 금융부채
        tl = totalLiab[i]
        if tl is not None and fd is not None:
            opLiab.append(tl - fd)
        else:
            opLiab.append(None)

        # 기타자본 = 자본총계 - 이익잉여금
        eq = equity[i]
        re = retainedEarnings[i]
        if eq is not None and re is not None:
            otherEquity.append(eq - re)
        else:
            otherEquity.append(None)

        # 영업자산 코어 = 총자산 - 현금 - 매출채권 - 재고 (단순 잔여)
        # 추후 calcAssetStructure 호출로 더 정교한 분해 가능
        ta = totalAssets[i]
        if ta is not None:
            base = ta - (cash[i] or 0) - (receivables[i] or 0) - (inventory[i] or 0)
            # opAssetCore = 잔여의 80% (대략 영업), investments = 20% (대략 투자) ← 임시 단순화
            # 정확한 분해는 calcAssetStructure 사용. 본 함수는 builder 호환 안전 fallback.
            opAssetCore.append(base)
            otherAssets.append(0)
        else:
            opAssetCore.append(None)
            otherAssets.append(None)

    return {
        "periods": periods,
        # 자산 stack
        "cash": cash,
        "stFinancial": stFinancial,
        "receivables": receivables,
        "inventory": inventory,
        "opAssetCore": opAssetCore,
        "investments": investments,
        "otherAssets": otherAssets,
        # 부채자본 stack
        "opLiab": opLiab,
        "finDebt": finDebt,
        "retainedEarnings": retainedEarnings,
        "otherEquity": otherEquity,
        # 합계 (검증용)
        "totalAssets": totalAssets,
        "totalLiab": totalLiab,
        "equity": equity,
    }


def bsDebtTimeline(norm: pl.DataFrame, nPeriods: int, periodKind: PeriodKind) -> dict:
    """부채 구조 시계열 — 영업부채 (무이자) vs 금융부채 (이자 발생) 분해.

    경제 본질 분해 — 회계 표시 (유동/비유동) 가 아닌 자금 조달 성격별:
    - 금융부채 = 단기차입금 + 장기차입금 + 사채 (이자 발생, 자본비용 + Net Debt)
    - 영업부채 = 부채총계 - 금융부채 (매입채무·미지급금 등 무이자)

    Returns:
        {periods, opLiab, finDebt, shortDebt, longDebt, totalLiab}
    """
    periods = lastNPeriods(norm, nPeriods, periodKind)
    totalLiab = extractSeries(norm, "liabilities", periods)
    shortDebt = extractSeries(norm, "shortDebt", periods)
    longDebt = extractSeries(norm, "longDebt", periods)

    finDebt: list[float | None] = []
    opLiab: list[float | None] = []
    for i in range(len(periods)):
        s = shortDebt[i]
        l = longDebt[i]
        fd: float | None
        if s is None and l is None:
            fd = None
        else:
            fd = (s or 0) + (l or 0)
        finDebt.append(fd)
        tl = totalLiab[i]
        if tl is not None and fd is not None:
            opLiab.append(tl - fd)
        else:
            opLiab.append(None)
    return {
        "periods": periods,
        "opLiab": opLiab,
        "finDebt": finDebt,
        "shortDebt": shortDebt,
        "longDebt": longDebt,
        "totalLiab": totalLiab,
    }
