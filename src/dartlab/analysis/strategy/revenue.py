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
    except (ValueError, KeyError, AttributeError, TypeError):
        return None
    except Exception:  # noqa: BLE001 — Polars ShapeError 등 예측 불가 에러
        return None


def _getSegmentsResult(company):
    """SegmentsResult 객체 안전 반환 (tables 딕셔너리 접근용)."""
    try:
        return company._call_module("segments")
    except (ValueError, KeyError, AttributeError, TypeError):
        return None
    except Exception:  # noqa: BLE001
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
        others = segments[_MAX_SEGMENTS - 1 :]
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

    # 다년간 구성 비중 변화 (segments wide DF 활용)
    compositionHistory = _calcCompositionHistory(company)

    return {
        "segments": segments,
        "totalRevenue": totalRev,
        "totalOpIncome": totalOp,
        "hasOpIncome": hasOp,
        "summary": summary,
        "compositionHistory": compositionHistory,
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
    yearCols = yearCols[:_MAX_YEARS]
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


def _extractRevRow(df, nameCol: str, segCols: list[str]) -> dict | None:
    """SegmentTable DataFrame에서 매출 행을 찾아 {col: value} 반환."""
    revRowName = None
    for row in df.iter_rows(named=True):
        name = str(row.get(nameCol, "")).strip()
        if ("매출" in name or "영업수익" in name) and "내부" not in name:
            revRowName = name
            break
    if revRowName is None:
        return None
    for row in df.iter_rows(named=True):
        if str(row.get(nameCol, "")) == revRowName:
            return row
    return None


def _calcBreakdownHistory(company, sub: str) -> list[dict] | None:
    """다년간 지역/제품 비중 변화. [{year, shares: {name: pct}}, ...]."""
    segResult = _getSegmentsResult(company)
    if segResult is None or segResult.tables is None:
        return None

    typeMap = {"region": "region", "product": "product"}
    tableType = typeMap.get(sub)
    if tableType is None:
        return None

    history = []
    for year in sorted(segResult.tables.keys(), reverse=True)[:_MAX_YEARS]:
        for t in segResult.tables[year]:
            if t.tableType != tableType or t.period != "당기" or not t.aligned:
                continue
            try:
                df = t.toDataFrame()
            except Exception:  # noqa: BLE001 — ShapeError 등
                continue
            if df.is_empty():
                continue
            nameCol = df.columns[0]
            segCols = [c for c in df.columns if c != nameCol]
            if not segCols:
                continue
            revRow = _extractRevRow(df, nameCol, segCols)
            if revRow is None:
                continue
            vals = {}
            for col in segCols:
                v = revRow.get(col)
                if v is not None and v > 0:
                    vals[col] = v
            total = sum(vals.values())
            if total <= 0:
                continue
            shares = {k: v / total * 100 for k, v in vals.items()}
            history.append({"year": year, "shares": shares})
            break  # 같은 연도 중복 방지

    return history if len(history) >= 2 else None


def calcBreakdown(company, sub: str) -> dict | None:
    """지역별/제품별 매출 비중 + 다년간 비중 변화.

    반환::

        {
            "items": [{"name": str, "value": float, "pct": float}, ...],
            "total": float,
            "breakdownHistory": [{"year": str, "shares": {name: pct}}, ...] | None,
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

    revRow = _extractRevRow(df, nameCol, segCols)
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

    result = {"items": items[:_MAX_SEGMENTS], "total": total}

    # 다년간 비중 변화
    history = _calcBreakdownHistory(company, sub)
    if history:
        result["breakdownHistory"] = history

    return result


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

    # HHI 시계열 (5년)
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


def calcRevenueQuality(company) -> dict | None:
    """매출 품질 — 현금 뒷받침과 마진 추세.

    반환::

        {
            "cashConversion": float|None,       # 영업CF/순이익 (%)
            "cashConversionLabel": str,          # "양호" / "주의" / "위험"
            "grossMargin": float|None,           # 최근 매출총이익률 (%)
            "grossMarginTrend": [float, ...],    # 최근 4분기 매출총이익률
            "grossMarginDirection": str,         # "개선" / "악화" / "안정"
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


def calcGrowthContribution(company) -> dict | None:
    """부문별 성장 기여 분해 — 성장이 어디에서 왔는가.

    반환::

        {
            "totalGrowthPct": float,
            "contributions": [{"name": str, "amount": float, "pct": float}, ...],
            "driver": str,
        }
    """
    segResult = _selectSegments(company)
    if segResult is None:
        return None

    df = segResult.df
    if df.is_empty():
        return None

    yearCols = [c for c in df.columns if c != "부문"]
    if len(yearCols) < 2:
        return None

    curYear = yearCols[0]
    # 3년 전 비교 (가용 범위 내에서 최대한)
    baseIdx = min(3, len(yearCols) - 1)
    baseYear = yearCols[baseIdx]

    contributions = []
    totalCur = 0.0
    totalBase = 0.0

    for row in df.iter_rows(named=True):
        name = row["부문"]
        if any(kw in name for kw in _SKIP_KEYWORDS):
            continue

        cur = row.get(curYear)
        base = row.get(baseYear)
        if cur is None or base is None:
            continue

        totalCur += cur
        totalBase += base
        contributions.append({"name": name, "amount": cur - base})

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
        "period": f"{baseYear}→{curYear}",
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

    mismatch = _checkRevenueIncomeRankMismatch(company)
    if mismatch:
        flags.append((mismatch, "warning"))

    return flags


# ── 내부 헬퍼 ──

_SKIP_KEYWORDS = {"합계", "조정", "내부", "소계"}


def _getSegmentWideData(company) -> tuple[list[str], list[str], dict[str, dict[str, float]]] | None:
    """segments wide DF에서 (yearCols, segNames, {seg: {year: revenue}}) 추출."""
    segResult = _selectSegments(company)
    if segResult is None:
        return None
    df = segResult.df
    if df.is_empty():
        return None
    yearCols = [c for c in df.columns if c != "부문"][:_MAX_YEARS]
    if not yearCols:
        return None
    segData: dict[str, dict[str, float]] = {}
    for row in df.iter_rows(named=True):
        name = row["부문"]
        if any(kw in name for kw in _SKIP_KEYWORDS):
            continue
        vals = {}
        for yc in yearCols:
            v = row.get(yc)
            if v is not None and v > 0:
                vals[yc] = v
        if vals:
            segData[name] = vals
    if not segData:
        return None
    segNames = sorted(segData, key=lambda s: segData[s].get(yearCols[0], 0), reverse=True)
    return yearCols, segNames, segData


def _calcCompositionHistory(company) -> list[dict] | None:
    """연도별 부문 비중 변화. [{year, shares: {seg: pct}}, ...]."""
    result = _getSegmentWideData(company)
    if result is None:
        return None
    yearCols, segNames, segData = result
    history = []
    for yc in yearCols:
        yearVals = {s: segData[s].get(yc, 0) for s in segNames}
        total = sum(yearVals.values())
        if total <= 0:
            continue
        shares = {s: v / total * 100 for s, v in yearVals.items() if v > 0}
        history.append({"year": yc, "shares": shares})
    return history if len(history) >= 2 else None


def _calcHhiHistory(company) -> tuple[list[dict], str] | None:
    """연도별 HHI 시계열 + 방향. ([{year, hhi}], direction)."""
    result = _getSegmentWideData(company)
    if result is None:
        return None
    yearCols, segNames, segData = result
    hhiList = []
    for yc in yearCols:
        yearVals = [segData[s].get(yc, 0) for s in segNames]
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
        return f"매출 1위 {revTop[0]}({revPct:.0f}%) ≠ 이익 1위 {opTop[0]}({opPct:.0f}%): 수익 구조 편중"

    return None
