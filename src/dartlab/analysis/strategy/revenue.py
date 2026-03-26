"""1-1 수익 구조 분석 — 계산만 담당.

블록 조립은 review/sections/revenue.py가 한다.
여기는 company.select() → 계산 → dict/숫자 반환.
"""

from __future__ import annotations

_MAX_SEGMENTS = 8
_MAX_YEARS = 5

_SECTOR_KR = {
    "ENERGY": "에너지",
    "MATERIALS": "소재",
    "INDUSTRIALS": "산업재",
    "CONSUMER_DISC": "경기관련소비재",
    "CONSUMER_STAPLES": "필수소비재",
    "HEALTHCARE": "건강관리",
    "FINANCIALS": "금융",
    "IT": "IT",
    "COMMUNICATION": "커뮤니케이션서비스",
    "UTILITIES": "유틸리티",
    "REAL_ESTATE": "부동산",
}


# ── 유틸 ──


def _getRatios(company):
    """ratios 객체를 안전하게 가져온다."""
    try:
        return company.finance.ratios
    except (ValueError, KeyError, AttributeError):
        return None


def _selectSegments(company, sub: str | None = None):
    """select("segments") 또는 select("segments:sub") 안전 호출."""
    topic = f"segments:{sub}" if sub else "segments"
    try:
        return company.select(topic)
    except (ValueError, KeyError, AttributeError):
        return None


# ── 계산 함수들 ──


def calcCompanyProfile(company) -> dict | None:
    """업종·주요제품 맥락. 반환: {"sector": str, "products": str} 또는 None."""
    parts: dict[str, str] = {}

    try:
        sectorInfo = company.sector
        if sectorInfo:
            sectorKr = _SECTOR_KR.get(sectorInfo.sector.name, sectorInfo.sector.name)
            groupKr = sectorInfo.industryGroup.value
            parts["sector"] = f"섹터: {sectorKr} > {groupKr}"
    except (ValueError, KeyError, AttributeError):
        pass

    try:
        import dartlab

        listing = dartlab.listing()
        stockCode = getattr(company, "stockCode", "")
        if stockCode:
            row = listing.filter(listing["종목코드"] == stockCode)
            if not row.is_empty() and "주요제품" in row.columns:
                products = row["주요제품"][0]
                if products:
                    parts["products"] = f"주요제품: {products}"
    except (ImportError, ValueError, KeyError):
        pass

    return parts if parts else None


def calcSegmentComposition(company) -> dict | None:
    """부문별 매출·이익 구성.

    반환::

        {
            "segments": [{"name": str, "revenue": float, "opIncome": float|None}, ...],
            "totalRevenue": float,
            "totalOpIncome": float,
            "hasOpIncome": bool,
            "summary": str,  # "반도체 60%, DS 25%"
        }
    """
    compDf = _selectSegments(company, "composition")
    if compDf is None:
        return None

    df = compDf.df
    if df.is_empty():
        return None

    labelCol = df.columns[0]
    segCols = [c for c in df.columns if c != labelCol]
    if not segCols:
        return None

    revRowName = None
    opRowName = None
    for row in df.iter_rows(named=True):
        name = str(row.get(labelCol, "")).strip()
        if ("매출" in name or "영업수익" in name) and "내부" not in name:
            if revRowName is None:
                revRowName = name
        if "영업이익" in name or "영업손익" in name:
            if opRowName is None:
                opRowName = name

    if revRowName is None:
        return None

    rowMap: dict[str, dict[str, float | None]] = {}
    for row in df.iter_rows(named=True):
        name = str(row.get(labelCol, ""))
        rowMap[name] = {c: row.get(c) for c in segCols}

    revData = rowMap.get(revRowName, {})
    opData = rowMap.get(opRowName, {}) if opRowName else {}

    segments = []
    for col in segCols:
        rev = revData.get(col)
        opIncome = opData.get(col)
        if rev is not None and rev > 0 and "합계" not in col and "조정" not in col:
            segments.append({"name": col, "revenue": rev, "opIncome": opIncome})

    if not segments:
        return None

    segments.sort(key=lambda x: x["revenue"], reverse=True)
    if len(segments) > _MAX_SEGMENTS:
        top = segments[: _MAX_SEGMENTS - 1]
        others = segments[_MAX_SEGMENTS - 1:]
        othersRev = sum(s["revenue"] for s in others)
        opVals = [s["opIncome"] for s in others if s["opIncome"] is not None]
        othersOp = sum(opVals) if opVals else None
        top.append({"name": "기타", "revenue": othersRev, "opIncome": othersOp})
        segments = top

    totalRev = sum(s["revenue"] for s in segments)
    if totalRev == 0:
        return None

    totalOp = sum(s["opIncome"] for s in segments if s["opIncome"] is not None)
    hasOp = any(s["opIncome"] is not None for s in segments)

    topSeg = segments[0]
    topPct = topSeg["revenue"] / totalRev * 100
    summary = f"{topSeg['name']} {topPct:.0f}%"
    if len(segments) >= 2:
        seg2 = segments[1]
        seg2Pct = seg2["revenue"] / totalRev * 100
        summary += f", {seg2['name']} {seg2Pct:.0f}%"

    return {
        "segments": segments,
        "totalRevenue": totalRev,
        "totalOpIncome": totalOp,
        "hasOpIncome": hasOp,
        "summary": summary,
    }


def calcSegmentTrend(company) -> dict | None:
    """다년간 부문별 매출 추이 + YoY.

    반환::

        {
            "yearCols": [str, ...],
            "rows": [{"name": str, "values": {year: float}, "yoy": float|None}, ...],
        }
    """
    segResult = _selectSegments(company)
    if segResult is None:
        return None

    df = segResult.df
    if df.is_empty():
        return None

    yearCols = [c for c in df.columns if c != "부문"]
    maxYears = min(_MAX_YEARS, 4) if len(yearCols) >= 2 else _MAX_YEARS
    yearCols = yearCols[:maxYears]
    if not yearCols:
        return None

    skipKeywords = {"합계", "조정", "내부", "소계"}
    rows = []
    for row in df.iter_rows(named=True):
        name = row["부문"]
        if any(kw in name for kw in skipKeywords):
            continue

        vals = {yc: row.get(yc) for yc in yearCols}
        positiveVals = [v for v in vals.values() if v is not None and v > 0]
        if not positiveVals:
            continue

        yoy = None
        if len(yearCols) >= 2:
            cur = vals.get(yearCols[0])
            prev = vals.get(yearCols[1])
            if cur is not None and prev is not None and prev > 0:
                yoy = (cur - prev) / prev * 100

        rows.append({"name": name, "values": vals, "yoy": yoy})

    if not rows:
        return None

    return {"yearCols": yearCols, "rows": rows[:_MAX_SEGMENTS]}


def calcBreakdown(company, sub: str) -> dict | None:
    """지역별/제품별 매출 비중.

    반환::

        {
            "items": [{"name": str, "value": float, "pct": float}, ...],
            "total": float,
        }
    """
    selectResult = _selectSegments(company, sub)
    if selectResult is None:
        return None

    df = selectResult.df
    if df.is_empty():
        return None

    nameCol = df.columns[0]
    segCols = [c for c in df.columns if c != nameCol]
    if not segCols:
        return None

    revRowName = None
    for row in df.iter_rows(named=True):
        name = str(row.get(nameCol, "")).strip()
        if ("매출" in name or "영업수익" in name) and "내부" not in name:
            revRowName = name
            break

    if revRowName is None:
        return None

    revRow = None
    for row in df.iter_rows(named=True):
        if str(row.get(nameCol, "")) == revRowName:
            revRow = row
            break

    if revRow is None:
        return None

    items = []
    for col in segCols:
        v = revRow.get(col)
        if v is not None and v > 0:
            items.append({"name": col, "value": v})

    if not items:
        return None

    items.sort(key=lambda x: x["value"], reverse=True)
    total = sum(i["value"] for i in items)
    if total == 0:
        return None

    for i in items:
        i["pct"] = i["value"] / total * 100

    return {"items": items[:_MAX_SEGMENTS], "total": total}


def calcRevenueGrowth(company) -> dict | None:
    """매출 성장 지표.

    반환::

        {
            "yoy": float|None,
            "cagr3y": float|None,
            "quarterlySelect": SelectResult|None,
        }
    """
    ratios = _getRatios(company)
    yoy = getattr(ratios, "revenueGrowth", None) if ratios else None
    cagr = getattr(ratios, "revenueGrowth3Y", None) if ratios else None

    quarterly = None
    try:
        result = company.select("IS", ["매출액"])
        if result is not None:
            quarterly = result
    except (ValueError, KeyError, AttributeError):
        pass

    if yoy is None and cagr is None and quarterly is None:
        return None

    return {"yoy": yoy, "cagr3y": cagr, "quarterlySelect": quarterly}


def calcConcentration(company) -> dict | None:
    """매출 집중도.

    반환::

        {
            "hhi": float,
            "hhiLabel": str,
            "topPct": float,
            "domesticPct": float|None,
        }
    """
    revVals = _getSegmentRevenueVals(company)
    if not revVals:
        return None

    total = sum(revVals)
    hhi = sum((v / total * 100) ** 2 for v in revVals)
    if hhi > 5000:
        hhiLabel = "고집중"
    elif hhi > 2500:
        hhiLabel = "중간 집중"
    else:
        hhiLabel = "분산"

    topPct = max(revVals) / total * 100
    domesticPct = _calcDomesticExportRatio(company)

    return {
        "hhi": hhi,
        "hhiLabel": hhiLabel,
        "topPct": topPct,
        "domesticPct": domesticPct,
    }


def calcFlags(company) -> list[tuple[str, str]]:
    """수익 관련 경고/기회 플래그. [(텍스트, "warning"|"opportunity"), ...]."""
    flags: list[tuple[str, str]] = []

    revVals = _getSegmentRevenueVals(company)
    if revVals:
        total = sum(revVals)
        hhi = sum((v / total * 100) ** 2 for v in revVals)
        if hhi > 5000:
            flags.append((f"매출 고집중 (HHI {hhi:,.0f}) — 단일 부문 의존", "warning"))
        elif hhi > 2500:
            flags.append((f"매출 중간 집중 (HHI {hhi:,.0f})", "warning"))

    ratios = _getRatios(company)
    if ratios is not None:
        rg = getattr(ratios, "revenueGrowth", None)
        cagr = getattr(ratios, "revenueGrowth3Y", None)
        if rg is not None:
            if rg > 20:
                flags.append((f"매출 고성장 YoY +{rg:.0f}%", "opportunity"))
            elif rg < -10:
                flags.append((f"매출 역성장 YoY {rg:.0f}%", "warning"))
        if rg is not None and cagr is not None:
            if rg > 10 and cagr < 0:
                flags.append((
                    f"YoY +{rg:.0f}%이나 3Y CAGR {cagr:.0f}%: 반짝 회복 가능성",
                    "warning",
                ))
            elif rg < -5 and cagr > 5:
                flags.append((
                    f"YoY {rg:.0f}%이나 3Y CAGR +{cagr:.0f}%: 일시적 둔화 가능성",
                    "opportunity",
                ))

    mismatch = _checkRevenueIncomeRankMismatch(company)
    if mismatch:
        flags.append((mismatch, "warning"))

    return flags


# ── 내부 헬퍼 ──


def _getSegmentRevenueVals(company) -> list[float]:
    """composition에서 매출 행의 부문별 양수 값 리스트."""
    selectResult = _selectSegments(company, "composition")
    if selectResult is None:
        return []

    df = selectResult.df
    if df.is_empty():
        return []

    nameCol = df.columns[0]
    segCols = [c for c in df.columns if c != nameCol]

    for row in df.iter_rows(named=True):
        name = str(row.get(nameCol, "")).strip()
        if ("매출" in name or "영업수익" in name) and "내부" not in name:
            return [row[c] for c in segCols if row.get(c) is not None and row[c] > 0]
    return []


def _calcDomesticExportRatio(company) -> float | None:
    """내수 비중(%)."""
    selectResult = _selectSegments(company, "region")
    if selectResult is None:
        return None

    df = selectResult.df
    if df.is_empty():
        return None

    nameCol = df.columns[0]
    segCols = [c for c in df.columns if c != nameCol]

    for row in df.iter_rows(named=True):
        name = str(row.get(nameCol, "")).strip()
        if ("매출" in name or "영업수익" in name) and "내부" not in name:
            domesticKeywords = {"국내", "한국", "내수", "Korea", "Domestic"}
            domesticVal = 0.0
            totalVal = 0.0
            for col in segCols:
                v = row.get(col)
                if v is not None and v > 0:
                    totalVal += v
                    if any(kw in col for kw in domesticKeywords):
                        domesticVal += v
            return domesticVal / totalVal * 100 if totalVal > 0 else None
    return None


def _checkRevenueIncomeRankMismatch(company) -> str | None:
    """매출 1위 ≠ 이익 1위이면 텍스트 반환."""
    selectResult = _selectSegments(company, "composition")
    if selectResult is None:
        return None

    df = selectResult.df
    if df.is_empty():
        return None

    nameCol = df.columns[0]
    segCols = [c for c in df.columns if c != nameCol]

    revRowName = None
    opRowName = None
    for row in df.iter_rows(named=True):
        name = str(row.get(nameCol, "")).strip()
        if ("매출" in name or "영업수익" in name) and "내부" not in name:
            if revRowName is None:
                revRowName = name
        if "영업이익" in name or "영업손익" in name:
            if opRowName is None:
                opRowName = name

    if revRowName is None or opRowName is None:
        return None

    rowMap: dict[str, dict] = {}
    for row in df.iter_rows(named=True):
        rowMap[str(row.get(nameCol, ""))] = {c: row.get(c) for c in segCols}

    revData = rowMap.get(revRowName, {})
    opData = rowMap.get(opRowName, {})

    skipKw = {"합계", "조정", "소계"}
    segments = []
    for col in segCols:
        if any(kw in col for kw in skipKw):
            continue
        rev = revData.get(col)
        op = opData.get(col)
        if rev is not None and rev > 0:
            segments.append((col, rev, op if op is not None else 0))

    if len(segments) < 2:
        return None

    revTop = max(segments, key=lambda x: x[1])
    opTop = max(segments, key=lambda x: x[2])

    if revTop[0] != opTop[0]:
        totalRev = sum(r for _, r, _ in segments)
        totalOp = sum(o for _, _, o in segments)
        revPct = revTop[1] / totalRev * 100 if totalRev else 0
        opPct = opTop[2] / totalOp * 100 if totalOp else 0
        return (
            f"매출 1위 {revTop[0]}({revPct:.0f}%) ≠ "
            f"이익 1위 {opTop[0]}({opPct:.0f}%): 수익 구조 편중"
        )

    return None
