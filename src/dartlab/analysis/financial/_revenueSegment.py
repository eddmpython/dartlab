"""revenue.py 의 sector/segment/breakdown 계산 — calcCompanyProfile/SegmentComposition/SegmentTrend/Breakdown."""

from __future__ import annotations

from dartlab.analysis.financial._revenueHelpers import (
    _calcBreakdownHistoryFromDocs,
    _calcCompositionHistory,
)
from dartlab.analysis.financial._revenueSelect import (
    _MAX_SEGMENTS,
    _SKIP_KEYWORDS,
    _selectDocsOpIncome,
    _selectDocsRevenue,
    _selectDocsSalesOrder,
)
from dartlab.core.memory import memoizedCalc
from dartlab.core.utils.helpers import (
    annualColsFromPeriods as _annualColsFromPeriods,
)
from dartlab.core.utils.helpers import (
    parseNumStr as _parseNumStr,
)


@memoizedCalc
def calcCompanyProfile(company, *, basePeriod: str | None = None) -> dict | None:
    """업종/주요제품 맥락.

    Capabilities:
        - 섹터/산업그룹 + 기업명 + 주요제품 텍스트 컨텍스트 합성
        - KR: KRX 주요제품. US: EDGAR 10-K Item 1.

    Returns:
        dict | None — sector/company/products 키. 모두 없으면 None.

    Guide:
        story 첫 박스 (회사 소개) 입력. AI 답변에 회사 정체성 인용.

    When:
        Story intro + AI "이 회사 뭐 하는" 답변.

    How:
        sector dispatch → market 별 product 텍스트 추출.

    Requires:
        company.sector + (KR) listing 또는 (US) EDGAR sections view.

    Raises:
        없음.

    Example:
        >>> calcCompanyProfile(company)["sector"]
        '섹터: IT > 반도체'

    See Also:
        - companyContext.* : 추가 메타
        - calcSegmentComposition : 매출 구성

    AIContext:
        "이 회사 소개" 답변 시 sector + products 인용.
    """
    parts: dict[str, str] = {}

    market = getattr(company, "market", "KR")

    try:
        sectorInfo = company.sector
        if sectorInfo:
            sectorKr = sectorInfo.sector.value
            groupKr = sectorInfo.industryGroup.value
            parts["sector"] = f"섹터: {sectorKr} > {groupKr}"
    except (ValueError, KeyError, AttributeError):
        pass

    if market == "US":
        corpName = getattr(company, "corpName", None)
        if corpName:
            parts["company"] = corpName
        try:
            # EDGAR(US) 는 docs accessor 보유; DART 는 농장 은퇴로 _docs 없음 → getattr 방어.
            docsAccessor = getattr(company, "_docs", None)
            sections = docsAccessor.sections if docsAccessor is not None else None
            if sections is not None:
                import polars as pl

                item1 = sections.filter(pl.col("topic").str.contains("(?i)item1Business"))
                if not item1.is_empty():
                    pCols = [
                        c
                        for c in item1.columns
                        if c
                        not in (
                            "topic",
                            "blockType",
                            "blockOrder",
                            "textNodeType",
                            "textLevel",
                            "textPath",
                        )
                    ]
                    if pCols:
                        latestText = item1[pCols[-1]].drop_nulls().to_list()
                        if latestText:
                            firstPara = str(latestText[0])[:200]
                            parts["products"] = firstPara
        except (ValueError, KeyError, AttributeError):
            pass
    else:
        try:
            from dartlab._listingDispatch import listing as _listing

            listing = _listing()
            stockCode = getattr(company, "stockCode", "")
            # 목록이 비면(브라우저) 종목코드 dtype 이 Null 이라 str 비교가 TypeError 를 낸다.
            if stockCode and listing is not None and listing.height > 0 and "종목코드" in listing.columns:
                row = listing.filter(listing["종목코드"] == stockCode)
                if not row.is_empty() and "주요제품" in row.columns:
                    products = row["주요제품"][0]
                    if products:
                        parts["products"] = f"주요제품: {products}"
        except (ImportError, ValueError, KeyError):
            pass

    return parts if parts else None


@memoizedCalc
def calcSegmentComposition(company, *, basePeriod: str | None = None) -> dict | None:
    """부문별 매출 구성 (최신 기간).

    Parameters
    ----------
    company : Company
        분석 대상 기업.
    basePeriod : str, optional
        기준 기간.

    Returns
    -------
    dict | None
        segments : list[dict]
            name : str — 부문명
            revenue : float — 부문 매출 (원)
            opIncome : float | None — 부문 영업이익 (원)
            opMargin : float | None — 부문 영업이익률 (%)
        totalRevenue : float — 전체 매출 (원)
        totalOpIncome : float — 전체 영업이익 (원)
        hasOpIncome : bool — 영업이익 데이터 존재 여부
        summary : str — 상위 부문 요약
        compositionHistory : list[dict] | None — 연도별 비중 시계열

    Capabilities:
        - notes 부문별 매출/영업이익 추출 → segments list + summary
        - compositionHistory 시계열 비중

    Guide:
        story segment 박스 입력. 상위 부문 비중 ≥ 60% = 집중 (위험).

    When:
        Story segment + AI "사업부 매출 구성" 답변.

    How:
        ``_selectDocsRevenue`` + opIncome 매칭 → segments dict 변환.

    Requires:
        notes 부문 데이터.

    Raises:
        없음.

    Example:
        >>> calcSegmentComposition(company)["segments"][0]["name"]
        '반도체'

    See Also:
        - calcSegmentTrend : 시계열
        - calcConcentration : 집중도

    AIContext:
        "사업부 매출 구성" 답변 시 segments + summary 인용.
    """
    docsResult = _selectDocsRevenue(company, basePeriod=basePeriod)
    if docsResult is None:
        return None

    segData, yCols = docsResult
    latestYear = yCols[0]

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


@memoizedCalc
def calcSegmentTrend(company, *, basePeriod: str | None = None) -> dict | None:
    """다년간 부문별 매출 추이 + YoY + 영업이익률 추세.

    Parameters
    ----------
    company : Company
        분석 대상 기업.
    basePeriod : str, optional
        기준 기간.

    Returns
    -------
    dict | None
        yearCols : list[str] — 기간 컬럼
        rows : list[dict]
            name : str — 부문명
            values : dict[str, float] — 연도별 매출 (원)
            yoy : float | None — 최근 전기대비 (%)
            opMargins : dict[str, float] | None — 연도별 영업이익률 (%)
            opMarginDirection : str | None — 마진 방향 ("개선"|"악화"|"안정")

    Capabilities:
        - 부문별 multi-year 매출 시계열 + YoY + 영업이익률 변화 방향
        - rows list 로 부문별 trend 비교

    Guide:
        부문별 yoy ≥ 30% 와 마진 개선 동행 = 강세 부문.

    When:
        Story segment trend + AI 부문 추세 답변.

    How:
        notes 부문 시계열 + 연도별 op 매칭 → rows dict.

    Requires:
        notes 시계열 ≥ 2 년.

    Raises:
        없음.

    Example:
        >>> calcSegmentTrend(company)["rows"][0]["yoy"]
        24

    See Also:
        - calcSegmentComposition : 단일 시점
        - calcGrowthContribution : 부문 기여도

    AIContext:
        "이 사업부 성장세" 답변 시 yoy + opMarginDirection 인용.
    """
    docsResult = _selectDocsRevenue(company, basePeriod=basePeriod)
    if docsResult is None:
        return None

    segData, yCols = docsResult
    if not yCols:
        return None

    opData = _selectDocsOpIncome(company, yCols)

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

        opMargins = None
        opMarginDirection = None
        if opData and segName in opData:
            opMargins = {}
            for yc in yCols:
                rev = vals.get(yc)
                opInc = opData[segName].get(yc)
                if rev and rev > 0 and opInc is not None:
                    opMargins[yc] = opInc / rev * 100
            if not opMargins:
                opMargins = None
            elif len(opMargins) >= 2:
                marginVals = [opMargins[yc] for yc in yCols if yc in opMargins]
                diff = marginVals[0] - marginVals[-1]
                if diff > 3:
                    opMarginDirection = "개선"
                elif diff < -3:
                    opMarginDirection = "악화"
                else:
                    opMarginDirection = "안정"

        rows.append(
            {
                "name": segName,
                "values": positiveVals,
                "yoy": yoy,
                "opMargins": opMargins,
                "opMarginDirection": opMarginDirection,
            }
        )

    if not rows:
        return None

    rows.sort(key=lambda x: x["values"].get(yCols[0], 0), reverse=True)
    return {"yearCols": yCols, "rows": rows[:_MAX_SEGMENTS]}


@memoizedCalc
def calcBreakdown(company, sub: str, *, basePeriod: str | None = None) -> dict | None:
    """지역별/제품별 매출 비중 + 다년간 비중 변화.

    Parameters
    ----------
    company : Company
        분석 대상 기업.
    sub : str
        분해 기준 ("지역"|"제품").
    basePeriod : str, optional
        기준 기간.

    Returns
    -------
    dict | None
        items : list[dict]
            name : str — 항목명
            value : float — 금액 (원)
            pct : float — 비중 (%)
        total : float — 합계 (원)
        breakdownHistory : list[dict] | None — 연도별 비중 변화

    Capabilities:
        - 지역/제품 매출 비중 + 다년간 비중 변화 추세
        - 합계 + 비중 % 정규화

    Guide:
        지역 다변화 (top 비중 < 50%) = 글로벌 분산 안정. 제품 집중 = pricing power 가능.

    When:
        Story breakdown + AI 지역/제품 답변.

    How:
        ``_selectDocsSalesOrder`` → 항목별 매출 추출 → 정렬 + 비중 계산.

    Requires:
        notes 지역/제품 데이터.

    Raises:
        없음.

    Example:
        >>> calcBreakdown(company, "지역")["items"][0]["name"]
        '한국'

    See Also:
        - calcSegmentComposition : 사업부문
        - calcConcentration : 집중도

    AIContext:
        "이 회사 지역별/제품별 매출" 답변 시 items + pct 인용.
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

    resultDict: dict = {"items": items[:_MAX_SEGMENTS], "total": total}

    history = _calcBreakdownHistoryFromDocs(company, basePeriod=basePeriod)
    if history:
        resultDict["breakdownHistory"] = history

    return resultDict
