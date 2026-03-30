"""1-1 수익 구조 분석 — 계산만 담당.

블록 조립은 review/sections/revenue.py가 한다.
여기는 company.select() → 계산 → dict/숫자 반환.

데이터 접근: select() 단일 경로.
- 부문별 매출: select("productService") → 항목×기간 수평화 DF
- 지역/제품별: select("salesOrder") → 항목×기간 수평화 DF
- 재무제표: select("IS", [...]) → 숫자 DF
"""

from __future__ import annotations

from dartlab.analysis.financial._helpers import (
    annualColsFromPeriods as _annualColsFromPeriods,
    parseNumStr as _parseNumStr,
)

_MAX_SEGMENTS = 8
_MAX_YEARS = 8

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

_SKIP_KEYWORDS = {"합계", "조정", "내부", "소계", "총계", "부문계", "기타", "국내외"}


def _getRatios(company):
    """ratios 객체를 안전하게 가져온다."""
    try:
        return company.finance.ratios
    except (ValueError, KeyError, AttributeError):
        return None


def _selectDocsRevenue(
    company, *, basePeriod: str | None = None
) -> tuple[dict[str, dict[str, float]], list[str]] | None:
    """productService/salesOrder에서 부문별 매출 시계열을 추출.

    fallback 체인: productService → salesOrder.
    반환: ({부문명: {period: 매출액}}, annualCols) 또는 None.
    """
    for topic in ("productService", "salesOrder"):
        result = company.select(topic, ["매출액"])
        if result is None:
            continue
        parsed = _parseDocsRevenueResult(result, basePeriod=basePeriod)
        if parsed is not None:
            return parsed
    return None


def _parseDocsRevenueResult(
    result, *, basePeriod: str | None = None
) -> tuple[dict[str, dict[str, float]], list[str]] | None:
    """docs select 결과에서 부문별 매출 시계열 파싱."""
    df = result.df
    if df.is_empty():
        return None

    itemCol = df.columns[0]
    pCols = [c for c in df.columns if c != itemCol]
    yCols = _annualColsFromPeriods(pCols, basePeriod, _MAX_YEARS)
    if not yCols:
        return None

    segData: dict[str, dict[str, float]] = {}
    for row in df.iter_rows(named=True):
        rawItem = str(row.get(itemCol, ""))
        if any(kw in rawItem for kw in _SKIP_KEYWORDS):
            continue
        # 부문명 추출: "DX_매출액" → "DX", "국내_매출액" → "국내"
        segName = rawItem.replace("_매출액", "").strip()
        if not segName:
            continue

        vals: dict[str, float] = {}
        for yc in yCols:
            v = _parseNumStr(row.get(yc))
            if v is not None and v > 0:
                vals[yc] = v
        if vals:
            segData[segName] = vals

    if not segData:
        return None
    return segData, yCols


def _selectDocsOpIncome(company, yCols: list[str]) -> dict[str, dict[str, float]] | None:
    """productService/salesOrder에서 부문별 영업이익 시계열을 추출 (있는 기업만)."""
    for topic in ("productService", "salesOrder"):
        result = company.select(topic, ["영업이익", "영업손익"])
        if result is None:
            continue
        df = result.df
        if df.is_empty():
            continue

        itemCol = df.columns[0]
        opData: dict[str, dict[str, float]] = {}
        for row in df.iter_rows(named=True):
            rawItem = str(row.get(itemCol, ""))
            if any(kw in rawItem for kw in _SKIP_KEYWORDS):
                continue
            segName = rawItem.replace("_영업이익", "").replace("_영업손익", "").strip()
            if not segName:
                continue
            vals: dict[str, float] = {}
            for yc in yCols:
                v = _parseNumStr(row.get(yc))
                if v is not None:
                    vals[yc] = v
            if vals:
                opData[segName] = vals

        if opData:
            return opData
    return None


def _selectDocsSalesOrder(company, keyword: str | None = None):
    """salesOrder에서 항목별 매출 시계열을 추출."""
    if keyword:
        result = company.select("salesOrder", [keyword])
    else:
        result = company.select("salesOrder", colList=None)
    if result is None:
        return None
    return result


# ── 계산 함수들 ──


def calcCompanyProfile(company, *, basePeriod: str | None = None) -> dict | None:
    """업종/주요제품 맥락. 반환: {"sector": str, "products": str} 또는 None."""
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


def calcSegmentComposition(company, *, basePeriod: str | None = None) -> dict | None:
    """부문별 매출 구성 (최신 기간).

    반환::

        {
            "segments": [{"name": str, "revenue": float, "opIncome": float|None}, ...],
            "totalRevenue": float,
            "totalOpIncome": float,
            "hasOpIncome": bool,
            "summary": str,
            "compositionHistory": [{"year": str, "shares": {seg: pct}}, ...] | None,
        }
    """
    docsResult = _selectDocsRevenue(company, basePeriod=basePeriod)
    if docsResult is None:
        return None

    segData, yCols = docsResult
    latestYear = yCols[0]

    # 영업이익 데이터도 시도 (있는 기업만)
    opData = _selectDocsOpIncome(company, yCols)

    segments = []
    for segName, vals in segData.items():
        rev = vals.get(latestYear)
        if rev is not None and rev > 0:
            opIncome = opData.get(segName, {}).get(latestYear) if opData else None
            opMargin = opIncome / rev * 100 if opIncome is not None and rev > 0 else None
            segments.append({"name": segName, "revenue": rev, "opIncome": opIncome, "opMargin": opMargin})

    if not segments:
        return None

    segments.sort(key=lambda x: x["revenue"], reverse=True)
    if len(segments) > _MAX_SEGMENTS:
        top = segments[: _MAX_SEGMENTS - 1]
        others = segments[_MAX_SEGMENTS - 1 :]
        othersRev = sum(s["revenue"] for s in others)
        top.append({"name": "기타", "revenue": othersRev, "opIncome": None})
        segments = top

    totalRev = sum(s["revenue"] for s in segments)
    if totalRev == 0:
        return None

    hasOp = any(s["opIncome"] is not None for s in segments)
    totalOp = sum(s["opIncome"] for s in segments if s["opIncome"] is not None)

    topSeg = segments[0]
    topPct = topSeg["revenue"] / totalRev * 100
    summary = f"{topSeg['name']} {topPct:.0f}%"
    if len(segments) >= 2:
        seg2 = segments[1]
        seg2Pct = seg2["revenue"] / totalRev * 100
        summary += f", {seg2['name']} {seg2Pct:.0f}%"

    compositionHistory = _calcCompositionHistory(segData, yCols)

    return {
        "segments": segments,
        "totalRevenue": totalRev,
        "totalOpIncome": totalOp,
        "hasOpIncome": hasOp,
        "summary": summary,
        "compositionHistory": compositionHistory,
    }


def calcSegmentTrend(company, *, basePeriod: str | None = None) -> dict | None:
    """다년간 부문별 매출 추이 + YoY.

    반환::

        {
            "yearCols": [str, ...],
            "rows": [{"name": str, "values": {year: float}, "yoy": float|None}, ...],
        }
    """
    docsResult = _selectDocsRevenue(company, basePeriod=basePeriod)
    if docsResult is None:
        return None

    segData, yCols = docsResult
    if not yCols:
        return None

    rows = []
    for segName, vals in segData.items():
        positiveVals = {yc: vals.get(yc, 0) for yc in yCols}
        if not any(v > 0 for v in positiveVals.values()):
            continue

        yoy = None
        if len(yCols) >= 2:
            cur = vals.get(yCols[0])
            prev = vals.get(yCols[1])
            if cur is not None and prev is not None and prev > 0:
                yoy = (cur - prev) / prev * 100

        rows.append({"name": segName, "values": positiveVals, "yoy": yoy})

    if not rows:
        return None

    rows.sort(key=lambda x: x["values"].get(yCols[0], 0), reverse=True)
    return {"yearCols": yCols, "rows": rows[:_MAX_SEGMENTS]}


def calcBreakdown(company, sub: str, *, basePeriod: str | None = None) -> dict | None:
    """지역별/제품별 매출 비중 + 다년간 비중 변화.

    반환::

        {
            "items": [{"name": str, "value": float, "pct": float}, ...],
            "total": float,
            "breakdownHistory": [{"year": str, "shares": {name: pct}}, ...] | None,
        }
    """
    result = _selectDocsSalesOrder(company)
    if result is None:
        return None

    df = result.df
    if df.is_empty():
        return None

    itemCol = df.columns[0]
    periodCols = [c for c in df.columns if c != itemCol]
    yCols = _annualColsFromPeriods(periodCols, basePeriod, 1)
    if not yCols:
        return None

    latestYear = yCols[0]

    items = []
    for row in df.iter_rows(named=True):
        name = str(row.get(itemCol, "")).strip()
        if any(kw in name for kw in _SKIP_KEYWORDS):
            continue
        v = _parseNumStr(row.get(latestYear))
        if v is not None and v > 0:
            items.append({"name": name, "value": v})

    if not items:
        return None

    items.sort(key=lambda x: x["value"], reverse=True)
    total = sum(i["value"] for i in items)
    if total == 0:
        return None

    for i in items:
        i["pct"] = i["value"] / total * 100

    result_dict: dict = {"items": items[:_MAX_SEGMENTS], "total": total}

    history = _calcBreakdownHistoryFromDocs(company, basePeriod=basePeriod)
    if history:
        result_dict["breakdownHistory"] = history

    return result_dict


def calcRevenueGrowth(company, *, basePeriod: str | None = None) -> dict | None:
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

    # annual 기반 CAGR 교차 검증 — ratioSeries 분기 기반이 왜곡될 수 있음
    try:
        ann = company.annual
        if ann:
            from dartlab.core.finance.extract import getRevenueGrowth3Y

            annualCagr = getRevenueGrowth3Y(ann[0])
            if annualCagr is not None:
                if cagr is None:
                    cagr = annualCagr
                elif abs((cagr or 0) - annualCagr) > 5:
                    # 분기 CAGR과 연간 CAGR이 5%p 이상 차이나면 연간 우선
                    cagr = annualCagr
    except (ValueError, KeyError, AttributeError):
        pass

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


def calcConcentration(company, *, basePeriod: str | None = None) -> dict | None:
    """매출 집중도.

    반환::

        {
            "hhi": float,
            "hhiLabel": str,
            "topPct": float,
            "domesticPct": float|None,
            "hhiHistory": list|None,
            "hhiDirection": str,
        }
    """
    revVals = _getDocsRevenueVals(company)
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

    hhiResult = _calcHhiHistory(company)
    hhiHistory = None
    hhiDirection = "안정"
    if hhiResult is not None:
        hhiHistory, hhiDirection = hhiResult

    return {
        "hhi": hhi,
        "hhiLabel": hhiLabel,
        "topPct": topPct,
        "domesticPct": domesticPct,
        "hhiHistory": hhiHistory,
        "hhiDirection": hhiDirection,
    }


def calcRevenueQuality(company, *, basePeriod: str | None = None) -> dict | None:
    """매출 품질 — 현금 뒷받침과 마진 추세.

    반환::

        {
            "cashConversion": float|None,
            "cashConversionLabel": str,
            "grossMargin": float|None,
            "grossMarginTrend": [float, ...],
            "grossMarginDirection": str,
        }
    """
    ratios = _getRatios(company)
    if ratios is None:
        return None

    cc = getattr(ratios, "operatingCfToNetIncome", None)
    gm = getattr(ratios, "grossMargin", None)

    if cc is None and gm is None:
        return None

    ccLabel = "양호"
    if cc is not None:
        if cc >= 80:
            ccLabel = "양호"
        elif cc >= 40:
            ccLabel = "주의"
        else:
            ccLabel = "위험"

    gmTrend: list[float] = []
    try:
        seriesResult = company.finance.ratioSeries
        if seriesResult is not None:
            data, _years = seriesResult
            gmSeries = data.get("RATIO", {}).get("grossMargin", [])
            if gmSeries:
                gmTrend = [v for v in gmSeries[-4:] if v is not None]
    except (ValueError, KeyError, AttributeError):
        pass

    gmDirection = "안정"
    if len(gmTrend) >= 2:
        first = gmTrend[0]
        last = gmTrend[-1]
        if first is not None and last is not None:
            diff = last - first
            if diff > 2:
                gmDirection = "개선"
            elif diff < -2:
                gmDirection = "악화"

    return {
        "cashConversion": cc,
        "cashConversionLabel": ccLabel,
        "grossMargin": gm,
        "grossMarginTrend": gmTrend,
        "grossMarginDirection": gmDirection,
    }


def calcGrowthContribution(company, *, basePeriod: str | None = None) -> dict | None:
    """부문별 성장 기여 분해 — 성장이 어디에서 왔는가.

    반환::

        {
            "totalGrowthPct": float,
            "contributions": [{"name": str, "amount": float, "pct": float}, ...],
            "driver": str,
            "period": str,
        }
    """
    docsResult = _selectDocsRevenue(company, basePeriod=basePeriod)
    if docsResult is None:
        return None

    segData, yCols = docsResult
    if len(yCols) < 2:
        return None

    curYear = yCols[0]
    baseIdx = min(3, len(yCols) - 1)
    baseYear = yCols[baseIdx]

    contributions = []
    totalCur = 0.0
    totalBase = 0.0

    for segName, vals in segData.items():
        cur = vals.get(curYear)
        base = vals.get(baseYear)
        if cur is None or base is None:
            continue

        totalCur += cur
        totalBase += base
        contributions.append({"name": segName, "amount": cur - base})

    if not contributions or totalBase == 0:
        return None

    totalChange = totalCur - totalBase
    totalGrowthPct = totalChange / totalBase * 100

    if totalChange == 0:
        for c in contributions:
            c["pct"] = 0.0
    else:
        for c in contributions:
            c["pct"] = c["amount"] / abs(totalChange) * 100

    contributions.sort(key=lambda x: abs(x["amount"]), reverse=True)
    contributions = contributions[:_MAX_SEGMENTS]

    top = contributions[0]
    topPct = abs(top["pct"])
    direction = "성장" if top["amount"] > 0 else "감소"
    driver = f"{top['name']}이(가) 전체 {direction}의 {topPct:.0f}% 기여"

    return {
        "totalGrowthPct": totalGrowthPct,
        "contributions": contributions,
        "driver": driver,
        "period": f"{baseYear} -> {curYear}",
    }


def calcFlags(company, *, basePeriod: str | None = None) -> list[tuple[str, str]]:
    """수익 관련 경고/기회 플래그. [(텍스트, "warning"|"opportunity"), ...]."""
    flags: list[tuple[str, str]] = []

    revVals = _getDocsRevenueVals(company)
    if revVals:
        total = sum(revVals)
        hhi = sum((v / total * 100) ** 2 for v in revVals)
        if hhi > 5000:
            flags.append((f"매출 고집중 (HHI {hhi:,.0f}) -- 단일 부문 의존", "warning"))
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
                flags.append(
                    (
                        f"YoY +{rg:.0f}%이나 3Y CAGR {cagr:.0f}%: 반짝 회복 가능성",
                        "warning",
                    )
                )
            elif rg < -5 and cagr > 5:
                flags.append(
                    (
                        f"YoY {rg:.0f}%이나 3Y CAGR +{cagr:.0f}%: 일시적 둔화 가능성",
                        "opportunity",
                    )
                )

    return flags


# ── 내부 헬퍼 ──


def _getDocsRevenueVals(company) -> list[float]:
    """productService에서 최신 기간 부문별 매출 양수 값 리스트."""
    docsResult = _selectDocsRevenue(company)
    if docsResult is None:
        return []

    segData, yCols = docsResult
    latestYear = yCols[0]

    vals = []
    for _segName, segVals in segData.items():
        v = segVals.get(latestYear)
        if v is not None and v > 0:
            vals.append(v)
    return vals


def _calcCompositionHistory(segData: dict[str, dict[str, float]], yCols: list[str]) -> list[dict] | None:
    """연도별 부문 비중 변화. [{year, shares: {seg: pct}}, ...]."""
    history = []
    for yc in yCols:
        yearVals = {s: segData[s].get(yc, 0) for s in segData}
        total = sum(yearVals.values())
        if total <= 0:
            continue
        shares = {s: v / total * 100 for s, v in yearVals.items() if v > 0}
        history.append({"year": yc, "shares": shares})
    return history if len(history) >= 2 else None


def _calcHhiHistory(company) -> tuple[list[dict], str] | None:
    """연도별 HHI 시계열 + 방향. ([{year, hhi}], direction)."""
    docsResult = _selectDocsRevenue(company)
    if docsResult is None:
        return None
    segData, yCols = docsResult
    hhiList = []
    for yc in yCols:
        yearVals = [segData[s].get(yc, 0) for s in segData]
        total = sum(yearVals)
        if total <= 0:
            continue
        hhi = sum((v / total * 100) ** 2 for v in yearVals if v > 0)
        hhiList.append({"year": yc, "hhi": hhi})
    if not hhiList:
        return None
    direction = "안정"
    if len(hhiList) >= 2:
        newest = hhiList[0]["hhi"]
        oldest = hhiList[-1]["hhi"]
        diff = newest - oldest
        if diff < -300:
            direction = "다각화 진행"
        elif diff > 300:
            direction = "집중 심화"
    return hhiList, direction


def _calcBreakdownHistoryFromDocs(company, *, basePeriod: str | None = None) -> list[dict] | None:
    """salesOrder���서 다년간 비중 변화."""
    result = _selectDocsSalesOrder(company)
    if result is None:
        return None

    df = result.df
    if df.is_empty():
        return None

    itemCol = df.columns[0]
    periodCols = [c for c in df.columns if c != itemCol]
    yCols = _annualColsFromPeriods(periodCols, basePeriod, _MAX_YEARS)
    if len(yCols) < 2:
        return None

    history = []
    for yc in yCols:
        shares: dict[str, float] = {}
        total = 0.0
        for row in df.iter_rows(named=True):
            name = str(row.get(itemCol, "")).strip()
            if any(kw in name for kw in _SKIP_KEYWORDS):
                continue
            v = _parseNumStr(row.get(yc))
            if v is not None and v > 0:
                shares[name] = v
                total += v
        if total > 0 and shares:
            history.append({"year": yc, "shares": {k: v / total * 100 for k, v in shares.items()}})

    return history if len(history) >= 2 else None


def _calcDomesticExportRatio(company) -> float | None:
    """내수 비중(%) — salesOrder��서 국내 키워드 매칭."""
    result = _selectDocsSalesOrder(company)
    if result is None:
        return None

    df = result.df
    if df.is_empty():
        return None

    itemCol = df.columns[0]
    periodCols = [c for c in df.columns if c != itemCol]
    yCols = _annualColsFromPeriods(periodCols, None, 1)
    if not yCols:
        return None

    latestYear = yCols[0]
    domesticKeywords = {"국내", "한국", "내수", "korea", "domestic"}

    domesticVal = 0.0
    totalVal = 0.0
    for row in df.iter_rows(named=True):
        name = str(row.get(itemCol, "")).strip()
        if any(kw in name for kw in _SKIP_KEYWORDS):
            continue
        v = _parseNumStr(row.get(latestYear))
        if v is not None and v > 0:
            totalVal += v
            if any(kw in name.lower() for kw in domesticKeywords):
                domesticVal += v

    return domesticVal / totalVal * 100 if totalVal > 0 else None
