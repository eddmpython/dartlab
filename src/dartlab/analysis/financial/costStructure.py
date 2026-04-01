"""비용 구조 분석 — 원가/판관비 비중, 영업레버리지, 손익분기점 시계열.

비용이 어떻게 움직이는지, 매출 변동에 이익이 얼마나 민감한지를 시계열로 추적한다.
"""

from __future__ import annotations

from typing import Any

from dartlab.analysis.financial._helpers import annualColsFromPeriods as _annualColsFromPeriods
from dartlab.analysis.financial._memoize import memoized_calc

_MAX_YEARS = 8


# ── 유틸 ──


def _toDict(selectResult) -> tuple[dict[str, dict], list[str]] | None:
    from dartlab.analysis.financial._helpers import toDict

    return toDict(selectResult)


def _get(row: dict, col: str) -> float:
    v = row.get(col) if row else None
    return v if v is not None else 0


def _pct(part: float, total: float) -> float | None:
    if total is None or total == 0:
        return None
    return part / total * 100


# ── 비용 비중 분해 ──


@memoized_calc
def calcCostBreakdown(company, *, basePeriod: str | None = None) -> dict | None:
    """매출원가율, 판관비율, 영업비용률 시계열.

    반환::

        {
            "history": [
                {
                    "period": str,
                    "revenue": float,
                    "costOfSales": float,
                    "sga": float,
                    "costOfSalesRatio": float | None,
                    "sgaRatio": float | None,
                    "operatingCostRatio": float | None,
                },
                ...
            ],
        }
    """
    accounts = ["매출액", "매출원가", "판매비와관리비"]
    isResult = company.select("IS", accounts)
    isParsed = _toDict(isResult)
    if isParsed is None:
        return None

    isData, isPeriods = isParsed
    revRow = isData.get("매출액", {})
    cogsRow = isData.get("매출원가", {})
    sgaRow = isData.get("판매비와관리비", {})

    yCols = _annualColsFromPeriods(isPeriods, basePeriod, _MAX_YEARS)
    if not yCols:
        return None

    history = []
    for col in yCols:
        rev = _get(revRow, col)
        cogs = _get(cogsRow, col)
        sga = _get(sgaRow, col)

        history.append(
            {
                "period": col,
                "revenue": rev,
                "costOfSales": cogs,
                "sga": sga,
                "costOfSalesRatio": _pct(cogs, rev),
                "sgaRatio": _pct(sga, rev),
                "operatingCostRatio": _pct(cogs + sga, rev),
            }
        )

    if not history:
        return None

    # notes enrichment — 비용의 성격별 분류 (있으면)
    from dartlab.analysis.financial._helpers import fetchNotesDetail

    result: dict[str, Any] = {"history": history}
    notesDetail = fetchNotesDetail(company, ["costByNature"])
    if notesDetail:
        result["notesDetail"] = notesDetail

    return result


# ── 영업레버리지 ──


@memoized_calc
def calcOperatingLeverage(company, *, basePeriod: str | None = None) -> dict | None:
    """영업레버리지(DOL) 시계열 — 매출 변동 대비 영업이익 민감도.

    반환::

        {
            "history": [
                {
                    "period": str,
                    "revenue": float,
                    "operatingIncome": float,
                    "grossProfit": float,
                    "dol": float | None,
                    "contributionProxy": float | None,
                },
                ...
            ],
        }
    """
    accounts = ["매출액", "영업이익", "매출총이익"]
    isResult = company.select("IS", accounts)
    isParsed = _toDict(isResult)
    if isParsed is None:
        return None

    isData, isPeriods = isParsed
    revRow = isData.get("매출액", {})
    opRow = isData.get("영업이익", {})
    gpRow = isData.get("매출총이익", {})

    yCols = _annualColsFromPeriods(isPeriods, basePeriod, _MAX_YEARS)
    if not yCols:
        return None

    history = []
    for i, col in enumerate(yCols):
        rev = _get(revRow, col)
        opIncome = _get(opRow, col)
        gp = _get(gpRow, col)

        # DOL = 영업이익 변화율 / 매출 변화율 (전년 대비)
        # 양쪽 다 양수일 때만 의미 있음 (부호 전환 시 DOL 해석 불가)
        dol = None
        if i + 1 < len(yCols):
            prevCol = yCols[i + 1]
            prevRev = _get(revRow, prevCol)
            prevOp = _get(opRow, prevCol)
            if prevRev > 0 and prevOp > 0 and opIncome > 0:
                revChange = (rev - prevRev) / prevRev
                opChange = (opIncome - prevOp) / prevOp
                if abs(revChange) > 0.001:
                    rawDol = opChange / revChange
                    # DOL > 20이면 해석 무의미 (극단적 레버리지), cap 처리
                    dol = max(-20, min(20, rawDol))

        # contribution proxy = 매출총이익 / 영업이익 (고정비 구조 프록시)
        contributionProxy = None
        if opIncome > 0 and gp > 0:
            contributionProxy = gp / opIncome

        history.append(
            {
                "period": col,
                "revenue": rev,
                "operatingIncome": opIncome,
                "grossProfit": gp,
                "dol": dol,
                "contributionProxy": contributionProxy,
            }
        )

    return {"history": history} if history else None


# ── 손익분기점 추정 ──


@memoized_calc
def calcBreakevenEstimate(company, *, basePeriod: str | None = None) -> dict | None:
    """BEP 추정 — 고정비/(1-변동비율) 기반 손익분기 매출.

    반환::

        {
            "history": [
                {
                    "period": str,
                    "revenue": float,
                    "fixedCostEstimate": float,
                    "variableCostRatio": float | None,
                    "bepRevenue": float | None,
                    "marginOfSafety": float | None,
                },
                ...
            ],
        }
    """
    accounts = ["매출액", "매출원가", "판매비와관리비"]
    isResult = company.select("IS", accounts)
    isParsed = _toDict(isResult)
    if isParsed is None:
        return None

    isData, isPeriods = isParsed
    revRow = isData.get("매출액", {})
    cogsRow = isData.get("매출원가", {})
    sgaRow = isData.get("판매비와관리비", {})

    yCols = _annualColsFromPeriods(isPeriods, basePeriod, _MAX_YEARS)
    if not yCols:
        return None

    history = []
    for col in yCols:
        rev = _get(revRow, col)
        cogs = _get(cogsRow, col)
        sga = _get(sgaRow, col)

        # 단순화: 변동비 = 매출원가, 고정비 = 판관비
        variableCostRatio = cogs / rev if rev > 0 else None
        fixedCost = sga
        bepRevenue = None
        marginOfSafety = None

        # 변동비율 95% 이상이면 한계이익률이 너무 작아 BEP 무의미
        if variableCostRatio is not None and 0 < variableCostRatio < 0.95:
            bepRevenue = fixedCost / (1 - variableCostRatio)
            if rev > 0:
                marginOfSafety = (rev - bepRevenue) / rev * 100

        history.append(
            {
                "period": col,
                "revenue": rev,
                "fixedCostEstimate": fixedCost,
                "variableCostRatio": variableCostRatio,
                "bepRevenue": bepRevenue,
                "marginOfSafety": marginOfSafety,
            }
        )

    return {"history": history} if history else None


# ── 비용의 성격별 분류 분석 ──


@memoized_calc
def calcCostByNatureAnalysis(company, *, basePeriod: str | None = None) -> dict | None:
    """비용의 성격별 분류(notes) — 인건비/원재료/감가상각 비중 추세.

    K-IFRS 주석에서 비용의 성격별 분류를 추출하여,
    원재료비·인건비·감가상각비 등 성격별 비중의 시계열 변화를 추적한다.
    173개사 이상 데이터 보유 (금융/REIT/지주회사 미공시).

    반환::

        {
            "categories": [
                {
                    "name": str,
                    "history": [{"period": str, "amount": float, "ratio": float}, ...],
                    "latestRatio": float,
                    "direction": str,
                },
                ...
            ],
            "periods": [str, ...],
            "insight": str | None,
        }
    """
    from dartlab.analysis.financial._helpers import fetchNotesDetail, parseNumStr

    notesData = fetchNotesDetail(company, ["costByNature"])
    rawRows = notesData.get("costByNature")
    if not rawRows:
        return None

    # costByNature: [{항목, 2024, 2023, ...}] (항목×연도 테이블)
    # 기간 컬럼 추출
    sampleRow = rawRows[0]
    periodCols = sorted(
        [k for k in sampleRow if k != "항목" and str(k).replace("-", "").isdigit()],
        reverse=True,
    )
    if not periodCols:
        return None

    periodCols = periodCols[:_MAX_YEARS]

    # 총비용 행 찾기 (합계/총계)
    totalRow = None
    detailRows = []
    for row in rawRows:
        item = str(row.get("항목", "")).strip()
        if any(kw in item for kw in ("합계", "총계", "계")):
            if totalRow is None:
                totalRow = row
        else:
            detailRows.append(row)

    if not detailRows:
        return None

    # 성격별 분류: 주요 비용 카테고리 매핑
    _CATEGORY_KEYWORDS = {
        "원재료": ["원재료", "재료비", "원자재"],
        "상품매입": ["상품", "상품매입"],
        "인건비": ["종업원급여", "급여", "인건비", "퇴직급여", "복리후생"],
        "감가상각": ["감가상각", "상각비", "무형자산상각"],
        "외주비": ["외주", "용역"],
        "기타": [],
    }

    categories: dict[str, dict[str, float]] = {}  # {catName: {period: amount}}
    for row in detailRows:
        item = str(row.get("항목", "")).strip()
        if not item:
            continue

        # 카테고리 매칭
        matched = "기타"
        for catName, keywords in _CATEGORY_KEYWORDS.items():
            if any(kw in item for kw in keywords):
                matched = catName
                break

        if matched not in categories:
            categories[matched] = {}
        for col in periodCols:
            v = parseNumStr(row.get(col))
            if v is not None:
                categories[matched][col] = categories[matched].get(col, 0) + v

    if not categories:
        return None

    # 총비용 계산 (totalRow 없으면 합산)
    totals: dict[str, float] = {}
    if totalRow:
        for col in periodCols:
            v = parseNumStr(totalRow.get(col))
            if v is not None and v > 0:
                totals[col] = v
    if not totals:
        for col in periodCols:
            s = sum(cats.get(col, 0) for cats in categories.values())
            if s > 0:
                totals[col] = s

    # 카테고리별 결과 생성
    result_categories = []
    for catName, vals in categories.items():
        if not vals:
            continue
        history = []
        for col in periodCols:
            amt = vals.get(col, 0)
            total = totals.get(col, 0)
            ratio = round(amt / total * 100, 1) if total > 0 else 0
            history.append({"period": col, "amount": amt, "ratio": ratio})

        latestRatio = history[0]["ratio"] if history else 0
        direction = None
        ratios = [h["ratio"] for h in history if h["ratio"] > 0]
        if len(ratios) >= 2:
            diff = ratios[0] - ratios[-1]
            if diff > 3:
                direction = "비중 증가"
            elif diff < -3:
                direction = "비중 감소"
            else:
                direction = "안정"

        result_categories.append({
            "name": catName,
            "history": history,
            "latestRatio": latestRatio,
            "direction": direction,
        })

    # 비중 기준 정렬 (기타 제외하고 큰 순)
    result_categories.sort(key=lambda x: (x["name"] == "기타", -x["latestRatio"]))

    # 인사이트 생성
    insight = None
    laborCat = next((c for c in result_categories if c["name"] == "인건비"), None)
    materialCat = next((c for c in result_categories if c["name"] == "원재료"), None)
    if laborCat and laborCat["direction"] == "비중 증가":
        insight = f"인건비 비중 {laborCat['latestRatio']:.0f}%로 증가 추세 — 노동집약도 심화"
    elif materialCat and materialCat["direction"] == "비중 증가":
        insight = f"원재료비 비중 {materialCat['latestRatio']:.0f}%로 증가 — 원가 부담 확대"

    return {
        "categories": result_categories,
        "periods": periodCols,
        "insight": insight,
    }


# ── 원재료 비중 (docs 보강) ──


@memoized_calc
def calcRawMaterialBreakdown(company, *, basePeriod: str | None = None) -> dict | None:
    """주요 원재료 품목별 매입액 비중 — rawMaterial docs 토픽 기반.

    부문/품목별 매입액 금액 행만 추출 (비중% 행 제외).
    계층적 테이블의 경우 부문별 첫 품목 금액이 대표값으로 나타남.
    """
    from dartlab.analysis.financial._helpers import parseNumStr

    result = company.select("rawMaterial", ["매입액"])
    if result is None:
        return None

    import polars as pl

    df = result if isinstance(result, pl.DataFrame) else getattr(result, "df", None)
    if df is None or "항목" not in df.columns:
        return None

    from dartlab.analysis.financial._helpers import periodCols

    pCols = periodCols(df)
    if not pCols:
        return None

    # 최신 연도 컬럼 사용 (basePeriod 이하, Q 없는 연도 우선)
    annuals = _annualColsFromPeriods(pCols, basePeriod, 1)
    latestCol = annuals[0] if annuals else pCols[0]

    items = df["항목"].to_list()
    vals = df[latestCol].to_list()

    # 총계 행 찾기
    totalAmount = None
    for it, v in zip(items, vals):
        if any(k in str(it) for k in ["총계", "합계"]):
            totalAmount = parseNumStr(str(v))
            break

    if totalAmount is None or totalAmount <= 0:
        return None

    # 금액 행만 추출 (소계/총계 제외, % 비중 행 제외)
    segments = []
    for it, v in zip(items, vals):
        it = str(it)
        vStr = str(v).strip()
        if any(k in it for k in ["총계", "합계", "소계"]):
            continue
        if "%" in vStr:
            continue
        parsed = parseNumStr(vStr)
        if parsed is None or parsed <= 0:
            continue
        name = it.replace("_매입액", "").strip()
        if not name:
            continue
        pct = parsed / totalAmount * 100
        if pct < 1:
            continue
        segments.append({"name": name, "amount": parsed, "pct": round(pct, 1)})

    if not segments:
        return None

    segments.sort(key=lambda x: x["amount"], reverse=True)
    return {
        "segments": segments[:8],
        "totalAmount": totalAmount,
        "period": latestCol,
    }


# ── 플래그 ──


@memoized_calc
def calcCostStructureFlags(company, *, basePeriod: str | None = None) -> list[str]:
    """비용 구조 경고 신호."""
    flags = []

    breakdown = calcCostBreakdown(company, basePeriod=basePeriod)
    if breakdown and len(breakdown["history"]) >= 3:
        hist = breakdown["history"]
        # 매출원가율 3년 연속 상승
        cogsRatios = [h.get("costOfSalesRatio") for h in hist[:3]]
        if all(r is not None for r in cogsRatios):
            if cogsRatios[0] > cogsRatios[1] > cogsRatios[2]:
                flags.append(f"매출원가율 3년 연속 상승 ({cogsRatios[2]:.1f}% -> {cogsRatios[0]:.1f}%)")

        # 판관비율 3년 연속 상승
        sgaRatios = [h.get("sgaRatio") for h in hist[:3]]
        if all(r is not None for r in sgaRatios):
            if sgaRatios[0] > sgaRatios[1] > sgaRatios[2]:
                flags.append(f"판관비율 3년 연속 상승 ({sgaRatios[2]:.1f}% -> {sgaRatios[0]:.1f}%)")

    leverage = calcOperatingLeverage(company, basePeriod=basePeriod)
    if leverage and leverage["history"]:
        h0 = leverage["history"][0]
        dol = h0.get("dol")
        if dol is not None and dol > 3:
            flags.append(f"영업레버리지(DOL) {dol:.1f} — 매출 변동에 이익 민감")

    bep = calcBreakevenEstimate(company, basePeriod=basePeriod)
    if bep and bep["history"]:
        h0 = bep["history"][0]
        mos = h0.get("marginOfSafety")
        if mos is not None and mos < 10:
            flags.append(f"안전마진 {mos:.1f}% — 손익분기점 근접")

    return flags
