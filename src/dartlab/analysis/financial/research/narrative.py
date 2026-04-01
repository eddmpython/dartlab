"""교차분석 서술 엔진 — 15개 차원에서 IS/BS/CF 3표를 교차분석하여 해석적 서술문으로 변환."""

from __future__ import annotations

from dataclasses import dataclass

from dartlab.analysis.financial.research.types import (
    DuPontResult,
    EarningsQuality,
    MarketData,
    NarrativeAnalysis,
    NarrativeParagraph,
)

# ══════════════════════════════════════
# 내부 입력 구조체
# ══════════════════════════════════════


@dataclass
class _Input:
    """narrative 분석 공통 입력."""

    aSeries: dict
    aYears: list[str]
    dupont: DuPontResult | None = None
    earningsQuality: EarningsQuality | None = None
    marketData: MarketData | None = None
    segmentsDf: object | None = None  # pl.DataFrame | None
    costByNatureDf: object | None = None  # pl.DataFrame | None
    sectorBenchmark: object | None = None  # SectorBenchmark | None
    sectorParams: object | None = None  # SectorParams | None
    isFinancial: bool = False
    # Phase 1: ratios 연결
    ratios: object | None = None  # finance.ratios
    # Phase 4: 실전 사업분석
    salesOrderDf: object | None = None  # pl.DataFrame | None
    productServiceDf: object | None = None  # pl.DataFrame | None
    quarterlyIsDf: object | None = None  # pl.DataFrame | None
    # Phase 5: 인적자본
    employeeDf: object | None = None  # pl.DataFrame | None
    rndDf: object | None = None  # pl.DataFrame | None


# ══════════════════════════════════════
# 유틸
# ══════════════════════════════════════


def _safeDiv(a: float | None, b: float | None) -> float | None:
    """안전한 나누기."""
    if a is None or b is None or b == 0:
        return None
    return a / b


def _pct(v: float | None) -> str:
    """% 포맷."""
    if v is None:
        return "-"
    return f"{v:.1f}%"


def _pctChange(v: float | None) -> str:
    """+/- % 포맷."""
    if v is None:
        return "-"
    return f"{v:+.1f}%"


def _pp(v: float | None) -> str:
    """%p 포맷."""
    if v is None:
        return "-"
    return f"{v:+.1f}%p"


def _getVals(series: dict, sjDiv: str, key: str) -> list[float | None]:
    """aSeries에서 특정 계정 시계열 추출."""
    return series.get(sjDiv, {}).get(key, [])


def _lastN(vals: list[float | None], n: int = 2) -> list[float | None]:
    """마지막 n개 non-None 값."""
    filtered = [(i, v) for i, v in enumerate(vals) if v is not None]
    return [v for _, v in filtered[-n:]]


def _trend(vals: list[float | None]) -> str:
    """3개 이상 값의 추세 판별."""
    clean = [v for v in vals if v is not None]
    if len(clean) < 3:
        return "unknown"
    diffs = [clean[i] - clean[i - 1] for i in range(1, len(clean))]
    if all(d > 0 for d in diffs):
        return "improving"
    if all(d < 0 for d in diffs):
        return "deteriorating"
    return "mixed"


def _consecutiveDirection(vals: list[float | None]) -> tuple[str, int]:
    """연속 개선/악화 횟수."""
    clean = [v for v in vals if v is not None]
    if len(clean) < 2:
        return "unknown", 0
    direction = "up" if clean[-1] > clean[-2] else "down"
    count = 1
    for i in range(len(clean) - 2, 0, -1):
        if direction == "up" and clean[i] > clean[i - 1]:
            count += 1
        elif direction == "down" and clean[i] < clean[i - 1]:
            count += 1
        else:
            break
    return direction, count


# ══════════════════════════════════════
# 7개 분석 차원
# ══════════════════════════════════════


def _analyzeDupont(inp: _Input) -> NarrativeParagraph | None:
    """DuPont 5-factor 교차분해 + ROIC."""
    dp = inp.dupont
    if dp is None or not dp.roe:
        return None
    roeLast = next((v for v in reversed(dp.roe) if v is not None), None)
    marginLast = next((v for v in reversed(dp.netMargin) if v is not None), None)
    turnoverLast = next((v for v in reversed(dp.assetTurnover) if v is not None), None)
    leverageLast = next((v for v in reversed(dp.equityMultiplier) if v is not None), None)
    if roeLast is None or marginLast is None:
        return None

    parts: list[str] = []
    roePct = roeLast * 100
    marginPct = marginLast * 100
    roeStr = f"ROE {roePct:.1f}%"

    # 5-factor 분해
    tbLast = next((v for v in reversed(dp.taxBurden) if v is not None), None) if dp.taxBurden else None
    ibLast = next((v for v in reversed(dp.interestBurden) if v is not None), None) if dp.interestBurden else None
    opmLast = next((v for v in reversed(dp.operatingMargin) if v is not None), None) if dp.operatingMargin else None

    if tbLast is not None and ibLast is not None and opmLast is not None:
        decomp5 = [
            f"세금부담 {tbLast:.2f}",
            f"이자부담 {ibLast:.2f}",
            f"OPM {opmLast * 100:.1f}%",
            f"회전율 {turnoverLast:.2f}배" if turnoverLast else "",
            f"레버리지 {leverageLast:.1f}배" if leverageLast else "",
        ]
        parts.append(f"{roeStr} = {' × '.join(d for d in decomp5 if d)}")
        if tbLast < 0.7:
            parts.append(f"세금부담률 높음(유효세율 {(1 - tbLast) * 100:.0f}%)")
        if ibLast < 0.7:
            parts.append("이자비용이 세전이익을 크게 잠식")
    else:
        decomp = []
        if marginLast is not None:
            decomp.append(f"순이익률 {marginPct:.1f}%")
        if turnoverLast is not None:
            decomp.append(f"자산회전율 {turnoverLast:.2f}배")
        if leverageLast is not None:
            decomp.append(f"레버리지 {leverageLast:.1f}배")
        parts.append(f"{roeStr}는 {' × '.join(decomp)}로 구성")

    # ROIC
    roicLast = next((v for v in reversed(dp.roic) if v is not None), None) if dp.roic else None
    if roicLast is not None:
        roicPct = roicLast * 100
        parts.append(f"ROIC {roicPct:.1f}%")
        if roicPct > 10:
            parts.append("투자자본 대비 양호한 가치창출")
        elif roicPct < 5:
            parts.append("ROIC 낮음 — 자본비용 대비 가치파괴 가능성")

    # 업종 비교
    bench = inp.sectorBenchmark
    if bench is not None:
        roeMedian = getattr(bench, "roeMedian", None)
        if roeMedian is not None:
            if roePct > roeMedian:
                parts.append(f"업종 중앙값({roeMedian:.1f}%) 대비 우수")
            else:
                parts.append(f"업종 중앙값({roeMedian:.1f}%) 하회")

    # 추세 (assetTurnover)
    if len(dp.assetTurnover) >= 2:
        cleanTurnover = [v for v in dp.assetTurnover if v is not None]
        if len(cleanTurnover) >= 2:
            diff = cleanTurnover[-1] - cleanTurnover[-2]
            if abs(diff) > 0.05:
                direction = "상승" if diff > 0 else "하락"
                parts.append(f"자산회전율 {direction} 추세(전년 대비 {diff:+.2f})")

    # driver
    driverMap = {
        "margin": "마진 주도형",
        "turnover": "회전율 주도형",
        "leverage": "레버리지 주도형",
        "balanced": "균형형",
    }
    driverLabel = driverMap.get(dp.driver, dp.driver)
    parts.append(driverLabel)

    body = ". ".join(parts) + "."
    severity = "positive" if roeLast > 0.10 else "neutral" if roeLast > 0.05 else "negative"
    return NarrativeParagraph(dimension="dupont", title="수익구조 분해 (DuPont 5-Factor)", body=body, severity=severity)


def _analyzeMarginTrend(inp: _Input) -> NarrativeParagraph | None:
    """마진 추세 분해 — 원가율/판관비 기여도 분석."""
    sales = _getVals(inp.aSeries, "IS", "sales")
    cogs = _getVals(inp.aSeries, "IS", "cost_of_sales")
    op = _getVals(inp.aSeries, "IS", "operating_profit")
    if not sales or len(sales) < 2:
        return None

    # 마진 계산
    gmList = (
        [
            _safeDiv(
                s - c if s is not None and c is not None else None,
                s,
            )
            for s, c in zip(sales, cogs)
        ]
        if cogs
        else []
    )
    # 더 간단하게 다시
    gmList = []
    if cogs:
        for s, c in zip(sales, cogs):
            if s is not None and c is not None and s != 0:
                gmList.append((s - c) / s * 100)
            else:
                gmList.append(None)

    omPctList = []
    for o, s in zip(op, sales):
        if o is not None and s is not None and s != 0:
            omPctList.append(o / s * 100)
        else:
            omPctList.append(None)

    if not omPctList or all(v is None for v in omPctList):
        return None

    parts: list[str] = []
    clean = [v for v in omPctList if v is not None]
    if len(clean) >= 2:
        latest = clean[-1]
        prev = clean[-2]
        diff = latest - prev
        direction, count = _consecutiveDirection(omPctList)

        if count >= 3:
            dirLabel = "개선" if direction == "up" else "악화"
            vals = [f"{v:.1f}%" for v in clean[-count - 1 :] if v is not None]
            parts.append(f"영업이익률 {count}년 연속 {dirLabel} ({'→'.join(vals)})")
        else:
            parts.append(f"영업이익률 {latest:.1f}%(전년 {prev:.1f}%, {_pp(diff)})")

    # 원가율 변동 기여
    if gmList and len(gmList) >= 2:
        cleanGm = [(i, v) for i, v in enumerate(gmList) if v is not None]
        if len(cleanGm) >= 2:
            gmDiff = cleanGm[-1][1] - cleanGm[-2][1]
            if abs(gmDiff) > 0.3:
                label = "원가율 개선" if gmDiff > 0 else "원가율 악화"
                parts.append(f"매출총이익률 {_pp(gmDiff)} ({label} 기여)")

    # SGA 비율 (sales - cogs - op = SGA)
    if cogs and op:
        sgaList = []
        for s, c, o in zip(sales, cogs, op):
            if all(v is not None for v in (s, c, o)) and s != 0:
                sga = s - c - o
                sgaList.append(sga / s * 100)
            else:
                sgaList.append(None)
        cleanSga = [(i, v) for i, v in enumerate(sgaList) if v is not None]
        if len(cleanSga) >= 2:
            sgaDiff = cleanSga[-1][1] - cleanSga[-2][1]
            if abs(sgaDiff) > 0.3:
                label = "판관비 효율화" if sgaDiff < 0 else "판관비 증가"
                parts.append(f"판관비율 {_pp(sgaDiff)} ({label})")

    # EBITDA 마진 (Lens 1 강화)
    depreciation = _getVals(inp.aSeries, "CF", "depreciation_and_amortization")
    if not depreciation:
        depreciation = _getVals(inp.aSeries, "IS", "depreciation")
    if op and depreciation:
        ebitdaMarginList = []
        for o, d, s in zip(op, depreciation, sales):
            if all(v is not None for v in (o, d, s)) and s != 0:
                ebitdaMarginList.append((o + abs(d)) / s * 100)
            else:
                ebitdaMarginList.append(None)
        emClean = [v for v in ebitdaMarginList if v is not None]
        if len(emClean) >= 2:
            emDiff = emClean[-1] - emClean[-2]
            parts.append(f"EBITDA마진 {emClean[-1]:.1f}%({_pp(emDiff)})")

    # 유효세율 추이 (Lens 1 강화)
    ebt = _getVals(inp.aSeries, "IS", "income_before_tax")
    if not ebt:
        ebt = _getVals(inp.aSeries, "IS", "profit_before_tax")
    taxExpense = _getVals(inp.aSeries, "IS", "income_tax_expense")
    if ebt and taxExpense:
        taxRateList = []
        for e, t in zip(ebt, taxExpense):
            if e is not None and t is not None and e != 0 and e > 0:
                taxRateList.append(abs(t) / e * 100)
            else:
                taxRateList.append(None)
        trClean = [v for v in taxRateList if v is not None]
        if len(trClean) >= 2:
            trDiff = trClean[-1] - trClean[-2]
            if abs(trDiff) > 3:
                label = "세부담 증가" if trDiff > 0 else "세부담 경감"
                parts.append(f"유효세율 {trClean[-1]:.1f}%({_pp(trDiff)}, {label})")

    # costByNature 원가 구조 분해 (Lens 1 강화)
    costDf = inp.costByNatureDf
    if costDf is not None:
        try:
            import polars as pl

            if isinstance(costDf, pl.DataFrame) and len(costDf) > 0:
                # 원재료비/인건비 비중 추이 (가용 컬럼 기반)
                cols = costDf.columns
                for keyword, label in [("원재료", "원재료비율"), ("인건비", "인건비율"), ("감가상각", "감가상각비율")]:
                    matchCols = [c for c in cols if keyword in c]
                    if matchCols:
                        vals = costDf[matchCols[0]].to_list()
                        cleanVals = [v for v in vals if v is not None]
                        if len(cleanVals) >= 2:
                            diff = cleanVals[-1] - cleanVals[-2]
                            if abs(diff) > 1:
                                parts.append(f"{label} {cleanVals[-1]:.1f}%({_pp(diff)})")
        except (ImportError, AttributeError, ValueError, KeyError):
            pass

    if not parts:
        return None
    body = ". ".join(parts) + "."
    latestOm = clean[-1] if clean else 0
    severity = "positive" if latestOm > 10 else "neutral" if latestOm > 5 else "negative"
    return NarrativeParagraph(dimension="margin", title="마진 추세 분석", body=body, severity=severity)


def _analyzeGrowthQuality(inp: _Input) -> NarrativeParagraph | None:
    """성장의 질 — 매출 vs 이익 성장률 + 부문별 기여."""
    sales = _getVals(inp.aSeries, "IS", "sales")
    op = _getVals(inp.aSeries, "IS", "operating_profit")
    ni = _getVals(inp.aSeries, "IS", "net_profit")
    if not sales or len(sales) < 2:
        return None

    # 직전 YoY 성장률
    def _yoyGrowth(vals: list[float | None]) -> float | None:
        clean = [(i, v) for i, v in enumerate(vals) if v is not None and v != 0]
        if len(clean) < 2:
            return None
        prev, curr = clean[-2][1], clean[-1][1]
        return (curr - prev) / abs(prev) * 100

    salesGr = _yoyGrowth(sales)
    opGr = _yoyGrowth(op)
    niGr = _yoyGrowth(ni)

    parts: list[str] = []
    if salesGr is not None:
        parts.append(f"매출 {_pctChange(salesGr)}")
    if opGr is not None:
        parts.append(f"영업이익 {_pctChange(opGr)}")
    if niGr is not None:
        parts.append(f"순이익 {_pctChange(niGr)}")

    if not parts:
        return None

    # 질적 판단
    qualityNote = ""
    if salesGr is not None and opGr is not None:
        if opGr > salesGr + 5:
            qualityNote = "이익 성장이 매출 성장을 상회하는 질적 성장"
        elif salesGr > opGr + 5 and salesGr > 0:
            qualityNote = "외형 성장 대비 수익성 미흡 — 마진 압박 가능성"
        elif salesGr > 0 and opGr > 0:
            qualityNote = "매출과 이익 동반 성장"
    if qualityNote:
        parts.append(qualityNote)

    # SGR (지속가능성장률 = ROE × (1 - 배당성향))
    totalEquity = _getVals(inp.aSeries, "BS", "total_equity")
    niVals = [v for v in ni if v is not None]
    teVals = [v for v in totalEquity if v is not None] if totalEquity else []
    if len(niVals) >= 1 and len(teVals) >= 1 and teVals[-1] and teVals[-1] > 0:
        roe = niVals[-1] / teVals[-1]
        # 배당성향 추정: 이익잉여금 변동 / 순이익
        retainedEarnings = _getVals(inp.aSeries, "BS", "retained_earnings")
        reVals = [v for v in retainedEarnings if v is not None] if retainedEarnings else []
        retentionRate = 0.7  # 기본 70%
        if len(reVals) >= 2 and niVals[-1] != 0:
            reChange = reVals[-1] - reVals[-2]
            rr = reChange / niVals[-1]
            if 0 < rr <= 1:
                retentionRate = rr
        sgr = roe * retentionRate * 100
        if salesGr is not None and sgr > 0:
            gap = (salesGr or 0) - sgr
            parts.append(f"SGR(지속가능성장률) {sgr:.1f}%")
            if gap > 10:
                parts.append("실제 매출 성장률이 SGR을 크게 상회 — 외부 자금 조달 필요 구간")
            elif gap < -10:
                parts.append("SGR 대비 저성장 — 잉여 자본 활용 여력 존재")

    # 매출 vs 이익 3년+ 성장률 괴리 패턴
    salesAll = [v for v in sales if v is not None]
    opAll = [v for v in op if v is not None]
    if len(salesAll) >= 3 and len(opAll) >= 3:
        salesCagr = ((salesAll[-1] / salesAll[0]) ** (1 / (len(salesAll) - 1)) - 1) * 100 if salesAll[0] > 0 else None
        opCagr = ((opAll[-1] / opAll[0]) ** (1 / (len(opAll) - 1)) - 1) * 100 if opAll[0] > 0 else None
        if salesCagr is not None and opCagr is not None:
            parts.append(f"매출 CAGR {salesCagr:.1f}% / 영업이익 CAGR {opCagr:.1f}%")

    # 부문별 기여 (segments)
    segDf = inp.segmentsDf
    if segDf is not None:
        try:
            segParts = _analyzeSegmentGrowth(segDf)
            if segParts:
                parts.extend(segParts)
        except (AttributeError, ValueError, KeyError):
            pass

    body = ". ".join(parts) + "."
    severity = "positive" if (salesGr or 0) > 5 else "neutral" if (salesGr or 0) > -5 else "negative"
    return NarrativeParagraph(dimension="growth", title="성장의 질", body=body, severity=severity)


def _analyzeSegmentGrowth(segDf: object) -> list[str]:
    """segments DataFrame에서 부문별 성장 기여 분석."""
    import polars as pl

    if not isinstance(segDf, pl.DataFrame) or segDf.is_empty():
        return []

    cols = segDf.columns
    # 숫자 컬럼 = 기간 (연도)
    numCols = [c for c in cols if c not in ("부문", "segment", "항목", "구분") and not c.startswith("__")]
    if len(numCols) < 2:
        return []

    # 마지막 2개 기간
    latestCol = numCols[-1]
    prevCol = numCols[-2]
    nameCol = cols[0]  # 첫 컬럼 = 부문명

    parts: list[str] = []
    rows = segDf.to_dicts()
    segments: list[dict] = []
    totalLatest = 0.0

    for row in rows:
        name = row.get(nameCol, "")
        if not name or "합계" in str(name) or "소계" in str(name):
            continue
        latestVal = row.get(latestCol)
        prevVal = row.get(prevCol)
        if latestVal is not None and isinstance(latestVal, (int, float)):
            totalLatest += abs(latestVal)
            segments.append({"name": name, "latest": latestVal, "prev": prevVal})

    if not segments or totalLatest == 0:
        return []

    # 비중 계산 + 성장률
    topSegments: list[str] = []
    for seg in sorted(segments, key=lambda s: abs(s["latest"]), reverse=True)[:3]:
        share = abs(seg["latest"]) / totalLatest * 100
        gr = None
        if seg["prev"] is not None and isinstance(seg["prev"], (int, float)) and seg["prev"] != 0:
            gr = (seg["latest"] - seg["prev"]) / abs(seg["prev"]) * 100
        grStr = f" {_pctChange(gr)}" if gr is not None else ""
        topSegments.append(f"{seg['name']} {share:.0f}%{grStr}")

    if topSegments:
        parts.append(f"부문별: {', '.join(topSegments)}")

    # 집중도 경고
    if segments:
        maxShare = max(abs(s["latest"]) / totalLatest * 100 for s in segments)
        if maxShare > 70:
            topName = max(segments, key=lambda s: abs(s["latest"]))["name"]
            parts.append(f"{topName} 비중 {maxShare:.0f}% — 단일 부문 의존도 높음")

    return parts


def _analyzeCashflowQuality(inp: _Input) -> NarrativeParagraph | None:
    """현금흐름의 질 — OCF/NI + CAPEX + FCF."""
    eq = inp.earningsQuality
    ocf = _getVals(inp.aSeries, "CF", "operating_cashflow")
    sales = _getVals(inp.aSeries, "IS", "sales")

    # capex: 여러 가능한 키
    capex = _getVals(inp.aSeries, "CF", "capital_expenditure")
    if not capex:
        capex = _getVals(inp.aSeries, "CF", "acquisition_of_property_plant_and_equipment")

    parts: list[str] = []

    # OCF/NI
    if eq and eq.cfToNi is not None:
        ratio = eq.cfToNi
        if ratio > 1.2:
            parts.append(f"OCF/순이익 {ratio:.1f}배로 이익의 질 양호 — 현금 뒷받침 충분")
        elif ratio > 0.8:
            parts.append(f"OCF/순이익 {ratio:.1f}배로 보통 수준")
        elif ratio > 0:
            parts.append(f"OCF/순이익 {ratio:.1f}배로 현금 뒷받침 미흡")
        else:
            parts.append(f"OCF/순이익 {ratio:.1f}배 — 영업현금흐름 적자")

    # CAPEX 비율
    if capex and sales:
        cleanOcf = [(o, s) for o, s in zip(capex, sales) if o is not None and s is not None and s != 0]
        if cleanOcf:
            latestCapex, latestSales = cleanOcf[-1]
            capexRatio = abs(latestCapex) / latestSales * 100
            parts.append(f"CAPEX/매출 {capexRatio:.1f}%")

    # FCF
    if ocf and capex:
        cleanPairs = [(o, c) for o, c in zip(ocf, capex) if o is not None and c is not None]
        if cleanPairs:
            latestOcf, latestCapex = cleanPairs[-1]
            fcf = latestOcf - abs(latestCapex)
            if fcf > 0:
                parts.append(f"FCF 양호({fcf / 1e8:,.0f}억)")
            else:
                parts.append(f"FCF 적자({fcf / 1e8:,.0f}억) — 투자 부담")

    if not parts:
        return None
    body = ". ".join(parts) + "."
    cfSev = "positive"
    if eq and eq.cfToNi is not None:
        if eq.cfToNi < 0.5:
            cfSev = "negative"
        elif eq.cfToNi < 0.8:
            cfSev = "warning"
        elif eq.cfToNi < 1.2:
            cfSev = "neutral"
    return NarrativeParagraph(dimension="cashflow", title="현금흐름의 질", body=body, severity=cfSev)


def _analyzeEfficiency(inp: _Input) -> NarrativeParagraph | None:
    """운전자본 효율성 — DSO/DIO/DPO/CCC 추세."""
    sales = _getVals(inp.aSeries, "IS", "sales")
    cogs = _getVals(inp.aSeries, "IS", "cost_of_sales")
    receivables = _getVals(inp.aSeries, "BS", "trade_receivable")
    if not receivables:
        receivables = _getVals(inp.aSeries, "BS", "trade_and_other_receivables")
    inventories = _getVals(inp.aSeries, "BS", "inventories")
    payables = _getVals(inp.aSeries, "BS", "trade_payable")
    if not payables:
        payables = _getVals(inp.aSeries, "BS", "trade_and_other_payables")

    if not sales or len(sales) < 2:
        return None

    # DSO 계산
    dsoList: list[float | None] = []
    for r, s in zip(receivables, sales):
        dsoList.append(r / (s / 365) if r is not None and s is not None and s != 0 else None)

    # DIO 계산
    dioList: list[float | None] = []
    for inv, c in zip(inventories, cogs):
        dioList.append(inv / (c / 365) if inv is not None and c is not None and c != 0 else None)

    # DPO 계산
    dpoList: list[float | None] = []
    for p, c in zip(payables, cogs):
        dpoList.append(p / (c / 365) if p is not None and c is not None and c != 0 else None)

    # CCC
    cccList: list[float | None] = []
    for dso, dio, dpo in zip(dsoList, dioList, dpoList):
        if all(v is not None for v in (dso, dio, dpo)):
            cccList.append(dso + dio - dpo)
        else:
            cccList.append(None)

    parts: list[str] = []

    # DSO 추세
    cleanDso = [v for v in dsoList if v is not None]
    if len(cleanDso) >= 2:
        dsoDiff = cleanDso[-1] - cleanDso[-2]
        if abs(dsoDiff) > 3:
            label = "악화" if dsoDiff > 0 else "개선"
            parts.append(f"DSO {cleanDso[-2]:.0f}일→{cleanDso[-1]:.0f}일({label})")
        else:
            parts.append(f"DSO {cleanDso[-1]:.0f}일(안정)")

    # DIO 추세 (개별 표시)
    cleanDio = [v for v in dioList if v is not None]
    if len(cleanDio) >= 2:
        dioDiff = cleanDio[-1] - cleanDio[-2]
        if abs(dioDiff) > 3:
            label = "재고부담 증가" if dioDiff > 0 else "재고 효율화"
            parts.append(f"DIO {cleanDio[-2]:.0f}일→{cleanDio[-1]:.0f}일({label})")
        else:
            parts.append(f"DIO {cleanDio[-1]:.0f}일(안정)")

    # DPO 추세 (개별 표시)
    cleanDpo = [v for v in dpoList if v is not None]
    if len(cleanDpo) >= 2:
        dpoDiff = cleanDpo[-1] - cleanDpo[-2]
        if abs(dpoDiff) > 3:
            label = "지급 지연" if dpoDiff > 0 else "조기 지급"
            parts.append(f"DPO {cleanDpo[-2]:.0f}일→{cleanDpo[-1]:.0f}일({label})")

    # CCC 추세
    cleanCcc = [v for v in cccList if v is not None]
    if len(cleanCcc) >= 2:
        cccDiff = cleanCcc[-1] - cleanCcc[-2]
        if abs(cccDiff) > 5:
            label = "연장" if cccDiff > 0 else "단축"
            parts.append(f"CCC {cleanCcc[-2]:.0f}일→{cleanCcc[-1]:.0f}일({cccDiff:+.0f}일 {label})")
        # CCC 마이너스 해석 (선수금·선결제 비즈니스)
        if cleanCcc[-1] < 0:
            parts.append(f"CCC 음수({cleanCcc[-1]:.0f}일) — 매입채무 지급 전 현금 회수, 운전자본 우위 구조")
    elif len(cleanCcc) == 1 and cleanCcc[0] < 0:
        parts.append(f"CCC 음수({cleanCcc[0]:.0f}일) — 운전자본 우위 구조")

    # 운전자본 절대치 추이
    salesClean = [v for v in sales if v is not None]
    arClean = [v for v in receivables if v is not None] if receivables else []
    invClean = [v for v in inventories if v is not None] if inventories else []
    apClean = [v for v in payables if v is not None] if payables else []
    if arClean and invClean and apClean:
        nwc = (arClean[-1] + invClean[-1]) - apClean[-1]
        nwcRatio = nwc / salesClean[-1] * 100 if salesClean and salesClean[-1] > 0 else None
        if nwcRatio is not None:
            parts.append(f"순운전자본/매출 {nwcRatio:.1f}%")

    # 매출 증가 + CCC 악화 교차
    if len(salesClean) >= 2 and salesClean[-1] > salesClean[-2] and cleanCcc and len(cleanCcc) >= 2:
        if cleanCcc[-1] > cleanCcc[-2]:
            parts.append("매출 증가에도 운전자본 부담 확대")

    if not parts:
        return None
    body = ". ".join(parts) + "."
    severity = "warning" if any("악화" in p or "확대" in p or "부담 증가" in p for p in parts) else "neutral"
    return NarrativeParagraph(dimension="efficiency", title="운전자본 효율성", body=body, severity=severity)


def _analyzeSegments(inp: _Input) -> NarrativeParagraph | None:
    """사업부문 분석 — 비중 + 집중도."""
    import polars as pl

    segDf = inp.segmentsDf
    if segDf is None or not isinstance(segDf, pl.DataFrame) or segDf.is_empty():
        return None

    cols = segDf.columns
    numCols = [c for c in cols if c not in ("부문", "segment", "항목", "구분") and not c.startswith("__")]
    if not numCols:
        return None

    latestCol = numCols[-1]
    nameCol = cols[0]
    rows = segDf.to_dicts()

    segments: list[dict] = []
    total = 0.0
    for row in rows:
        name = row.get(nameCol, "")
        if not name or "합계" in str(name) or "소계" in str(name):
            continue
        val = row.get(latestCol)
        if val is not None and isinstance(val, (int, float)):
            total += abs(val)
            segments.append({"name": name, "value": val})

    if not segments or total == 0:
        return None

    parts: list[str] = []
    # 비중 상위 3개
    sorted_segs = sorted(segments, key=lambda s: abs(s["value"]), reverse=True)
    topParts = []
    for seg in sorted_segs[:4]:
        share = abs(seg["value"]) / total * 100
        topParts.append(f"{seg['name']} {share:.0f}%")
    parts.append(f"사업구성: {', '.join(topParts)}")

    # 집중도
    maxShare = max(abs(s["value"]) / total * 100 for s in segments)
    if maxShare > 70:
        topName = sorted_segs[0]["name"]
        parts.append(f"{topName} 비중 {maxShare:.0f}% — 단일 부문 의존 구조")
    elif maxShare < 30 and len(segments) >= 3:
        parts.append("사업 다각화 구조")

    # 기간별 비중 변화 (2개 이상 기간)
    if len(numCols) >= 2:
        prevCol = numCols[-2]
        prevTotal = 0.0
        prevMap: dict[str, float] = {}
        for row in rows:
            name = row.get(nameCol, "")
            if not name or "합계" in str(name):
                continue
            val = row.get(prevCol)
            if val is not None and isinstance(val, (int, float)):
                prevTotal += abs(val)
                prevMap[name] = val

        if prevTotal > 0:
            bigShift = []
            for seg in sorted_segs[:3]:
                currShare = abs(seg["value"]) / total * 100
                prevVal = prevMap.get(seg["name"])
                if prevVal is not None:
                    prevShare = abs(prevVal) / prevTotal * 100
                    shiftPp = currShare - prevShare
                    if abs(shiftPp) > 3:
                        bigShift.append(f"{seg['name']} {_pp(shiftPp)}")
            if bigShift:
                parts.append(f"비중 변화: {', '.join(bigShift)}")

    body = ". ".join(parts) + "."
    severity = "warning" if maxShare > 70 else "neutral"
    return NarrativeParagraph(dimension="segment", title="사업부문 분석", body=body, severity=severity)


def _analyzeSectorRelative(inp: _Input) -> NarrativeParagraph | None:
    """섹터 상대 포지셔닝 — PER/PBR vs 섹터 + ROE 대비."""
    md = inp.marketData
    sp = inp.sectorParams
    bench = inp.sectorBenchmark
    if md is None or sp is None:
        return None

    parts: list[str] = []

    # PER 비교
    perMultiple = getattr(sp, "perMultiple", None)
    if md.per is not None and perMultiple is not None and perMultiple > 0:
        discount = (md.per - perMultiple) / perMultiple * 100
        label = "할인" if discount < 0 else "할증"
        sectorLabel = getattr(sp, "label", "업종")
        parts.append(f"PER {md.per:.1f}배 vs {sectorLabel} 평균 {perMultiple:.1f}배 = {abs(discount):.0f}% {label}")

    # PBR 비교
    pbrMultiple = getattr(sp, "pbrMultiple", None)
    if md.pbr is not None and pbrMultiple is not None and pbrMultiple > 0:
        discount = (md.pbr - pbrMultiple) / pbrMultiple * 100
        label = "할인" if discount < 0 else "할증"
        parts.append(f"PBR {md.pbr:.2f}배 vs 업종 {pbrMultiple:.1f}배({abs(discount):.0f}% {label})")

    # ROE vs 업종 대비 밸류에이션 정당성
    if bench is not None and md.per is not None and perMultiple is not None:
        roeMedian = getattr(bench, "roeMedian", None)
        dp = inp.dupont
        roeLast = None
        if dp and dp.roe:
            roeLast = next((v for v in reversed(dp.roe) if v is not None), None)
            if roeLast is not None:
                roeLast = roeLast * 100

        if roeLast is not None and roeMedian is not None:
            perDiscount = md.per < perMultiple
            roeAbove = roeLast > roeMedian
            if perDiscount and roeAbove:
                parts.append(f"ROE({roeLast:.1f}%)가 업종 중앙값({roeMedian:.1f}%) 상회하나 PER 할인 — 저평가 가능성")
            elif not perDiscount and not roeAbove:
                parts.append(f"ROE({roeLast:.1f}%)가 업종 중앙값({roeMedian:.1f}%) 하회하나 PER 할증 — 프리미엄 과도")

    if not parts:
        return None
    body = ". ".join(parts) + "."
    # PER 할인 + ROE 우수 → positive
    severity = "neutral"
    if md.per is not None and perMultiple is not None:
        if md.per < perMultiple * 0.8:
            severity = "positive"
        elif md.per > perMultiple * 1.2:
            severity = "negative"
    return NarrativeParagraph(dimension="sectorRelative", title="섹터 상대 포지셔닝", body=body, severity=severity)


# ══════════════════════════════════════
# BS/CF 심층 + 3표 연결 (Stage 1 v4)
# ══════════════════════════════════════


def _analyzeBalanceSheetStructure(inp: _Input) -> NarrativeParagraph | None:
    """자산구성 분석 — 유동/비유동 비중, 유형 vs 무형, 추세."""
    totalAssets = _getVals(inp.aSeries, "BS", "total_assets")
    currentAssets = _getVals(inp.aSeries, "BS", "total_current_assets")
    nonCurrentAssets = _getVals(inp.aSeries, "BS", "total_non_current_assets")
    tangible = _getVals(inp.aSeries, "BS", "property_plant_and_equipment")
    intangible = _getVals(inp.aSeries, "BS", "intangible_assets")
    if not totalAssets or len(totalAssets) < 2:
        return None

    ta = [v for v in totalAssets if v is not None]
    if len(ta) < 2 or ta[-1] == 0:
        return None

    parts: list[str] = []

    # 자산 규모 변동
    taGr = (ta[-1] - ta[-2]) / abs(ta[-2]) * 100
    parts.append(f"총자산 {ta[-1] / 1e8:,.0f}억(전년 대비 {taGr:+.1f}%)")

    # 유동/비유동 비중
    ca = _lastN(currentAssets, 1)
    nca = _lastN(nonCurrentAssets, 1)
    if ca and nca and ta[-1] > 0:
        caRatio = ca[-1] / ta[-1] * 100
        ncaRatio = nca[-1] / ta[-1] * 100
        parts.append(f"유동 {caRatio:.0f}% / 비유동 {ncaRatio:.0f}%")

    # 유형 vs 무형
    tanClean = _lastN(tangible, 1)
    intClean = _lastN(intangible, 1)
    if tanClean and ta[-1] > 0:
        tanRatio = tanClean[-1] / ta[-1] * 100
        intRatio = intClean[-1] / ta[-1] * 100 if intClean else 0
        if tanRatio > 30:
            parts.append(f"유형자산 비중 {tanRatio:.0f}% — 자본집약적 구조")
        if intRatio > 15:
            parts.append(f"무형자산 비중 {intRatio:.0f}% — 지식자산 기반")

    # 자산 성장 vs 매출 성장 교차
    sales = _getVals(inp.aSeries, "IS", "sales")
    salesClean = [v for v in sales if v is not None] if sales else []
    if len(salesClean) >= 2 and salesClean[-2] != 0:
        salesGr = (salesClean[-1] - salesClean[-2]) / abs(salesClean[-2]) * 100
        if taGr > salesGr + 10:
            parts.append("자산증가율이 매출증가율 상회 — 자산효율 하락 주의")

    # 감가상각률 변동 (Lens 4 — 이익의 질)
    depreciation = _getVals(inp.aSeries, "CF", "depreciation_and_amortization")
    if not depreciation:
        depreciation = _getVals(inp.aSeries, "IS", "depreciation")
    tanVals = [v for v in tangible if v is not None] if tangible else []
    depVals = [v for v in depreciation if v is not None] if depreciation else []
    if len(tanVals) >= 2 and len(depVals) >= 2:
        depRatePrev = abs(depVals[-2]) / tanVals[-2] * 100 if tanVals[-2] > 0 else None
        depRateCurr = abs(depVals[-1]) / tanVals[-1] * 100 if tanVals[-1] > 0 else None
        if depRatePrev is not None and depRateCurr is not None:
            depDiff = depRateCurr - depRatePrev
            if abs(depDiff) > 2:
                label = "감가상각 강화" if depDiff > 0 else "감가상각 완화(이익 부풀리기 가능성)"
                parts.append(f"감가상각률 {depRateCurr:.1f}%({_pp(depDiff)}, {label})")

    # 이연법인세 추세 (BS)
    deferredTax = _getVals(inp.aSeries, "BS", "deferred_tax_liabilities")
    if not deferredTax:
        deferredTax = _getVals(inp.aSeries, "BS", "deferred_tax_assets")
    dtVals = [v for v in deferredTax if v is not None] if deferredTax else []
    if len(dtVals) >= 2 and ta[-1] > 0:
        dtRatioCurr = dtVals[-1] / ta[-1] * 100
        dtRatioPrev = dtVals[-2] / ta[-2] * 100 if len(ta) >= 2 and ta[-2] > 0 else None
        if dtRatioPrev is not None and abs(dtRatioCurr - dtRatioPrev) > 0.5:
            dtDiff = dtRatioCurr - dtRatioPrev
            parts.append(f"이연법인세 비중 {dtRatioCurr:.1f}%({_pp(dtDiff)}) — 세무·회계 차이 변동 주시")

    if not parts:
        return None
    body = ". ".join(parts) + "."
    severity = "neutral"
    if taGr > 20:
        severity = "warning"
    elif taGr < -10:
        severity = "negative"
    return NarrativeParagraph(
        dimension="bsStructure",
        title="자산구성 분석",
        body=body,
        severity=severity,
    )


def _analyzeDebtStructure(inp: _Input) -> NarrativeParagraph | None:
    """부채구조 분석 — 부채비율, 차입금 의존도, 이자보상배율."""
    totalLiab = _getVals(inp.aSeries, "BS", "total_liabilities")
    totalEquity = _getVals(inp.aSeries, "BS", "total_equity")
    shortBorrow = _getVals(inp.aSeries, "BS", "short_term_borrowings")
    longBorrow = _getVals(inp.aSeries, "BS", "long_term_borrowings")
    totalAssets = _getVals(inp.aSeries, "BS", "total_assets")
    op = _getVals(inp.aSeries, "IS", "operating_profit")
    interest = _getVals(inp.aSeries, "IS", "interest_expense")
    if not interest:
        interest = _getVals(inp.aSeries, "IS", "finance_costs")

    if not totalLiab or len(totalLiab) < 2:
        return None

    parts: list[str] = []

    # 부채비율 추세
    debtRatioList = []
    for tl, te in zip(totalLiab, totalEquity):
        debtRatioList.append(tl / te * 100 if tl is not None and te is not None and te != 0 else None)
    cleanDr = [v for v in debtRatioList if v is not None]
    if len(cleanDr) >= 2:
        drDiff = cleanDr[-1] - cleanDr[-2]
        direction, count = _consecutiveDirection(debtRatioList)
        if count >= 3:
            label = "상승" if direction == "up" else "하락"
            parts.append(f"부채비율 {count}년 연속 {label}({cleanDr[-1]:.0f}%)")
        else:
            parts.append(f"부채비율 {cleanDr[-1]:.0f}%(전년 {cleanDr[-2]:.0f}%, {_pp(drDiff)})")

    # 차입금 의존도
    if shortBorrow and longBorrow and totalAssets:
        latestShort = _lastN(shortBorrow, 1)
        latestLong = _lastN(longBorrow, 1)
        latestTa = _lastN(totalAssets, 1)
        if latestShort and latestLong and latestTa and latestTa[-1] > 0:
            borrowTotal = (latestShort[-1] or 0) + (latestLong[-1] or 0)
            borrowDep = borrowTotal / latestTa[-1] * 100
            parts.append(f"차입금 의존도 {borrowDep:.1f}%")
            if borrowDep > 30:
                parts.append("차입금 의존도 과다 — 금리 변동 리스크")

    # 이자보상배율
    latestIcr = None
    if interest and op:
        pairs = [(o, i) for o, i in zip(op, interest) if o is not None and i is not None and i != 0]
        if pairs:
            latestOp, latestInt = pairs[-1]
            latestIcr = latestOp / abs(latestInt)
            parts.append(f"이자보상배율 {latestIcr:.1f}배")
            if latestIcr < 1.5:
                parts.append("이자보상배율 위험 수준 — 이자비용 충당 불안")

    # Net Debt/EBITDA (Lens 10 — 부채상환능력 핵심)
    cash = _getVals(inp.aSeries, "BS", "cash_and_cash_equivalents")
    depreciation = _getVals(inp.aSeries, "CF", "depreciation_and_amortization")
    if not depreciation:
        depreciation = _getVals(inp.aSeries, "IS", "depreciation")
    cashLast = next((v for v in reversed(cash) if v is not None), None) if cash else None
    opLast = next((v for v in reversed(op) if v is not None), None) if op else None
    depLast = next((v for v in reversed(depreciation) if v is not None), None) if depreciation else None
    borrowLast = None
    if shortBorrow and longBorrow:
        sb = next((v for v in reversed(shortBorrow) if v is not None), 0)
        lb = next((v for v in reversed(longBorrow) if v is not None), 0)
        borrowLast = (sb or 0) + (lb or 0)
    if borrowLast is not None and cashLast is not None and opLast is not None and depLast is not None:
        netDebt = borrowLast - cashLast
        ebitda = opLast + abs(depLast)
        if ebitda > 0:
            ndEbitda = netDebt / ebitda
            parts.append(f"Net Debt/EBITDA {ndEbitda:.1f}배")
            if ndEbitda > 4:
                parts.append("Net Debt/EBITDA 4배 초과 — 부채 부담 과중")
            elif ndEbitda < 0:
                parts.append("순현금 상태 — 실질 무차입 경영")

    # CF/Debt (OCF/총부채)
    ocf = _getVals(inp.aSeries, "CF", "operating_cashflow")
    ocfLast = next((v for v in reversed(ocf) if v is not None), None) if ocf else None
    liabLast = next((v for v in reversed(totalLiab) if v is not None), None)
    if ocfLast is not None and liabLast is not None and liabLast > 0:
        cfDebt = ocfLast / liabLast * 100
        parts.append(f"OCF/총부채 {cfDebt:.1f}%")
        if cfDebt < 10:
            parts.append("현금흐름 대비 부채 과중 — 상환여력 미흡")

    # Fixed Charge Coverage (영업이익 / (이자비용 + 리스비용))
    # 리스비용 별도 계정 없으면 이자보상배율로 대체 (이미 계산)

    if not parts:
        return None
    body = ". ".join(parts) + "."
    severity = "neutral"
    if cleanDr and cleanDr[-1] > 200:
        severity = "negative"
    elif cleanDr and cleanDr[-1] < 50:
        severity = "positive"
    return NarrativeParagraph(
        dimension="debtStructure",
        title="부채구조 분석",
        body=body,
        severity=severity,
    )


def _analyzeLiquidity(inp: _Input) -> NarrativeParagraph | None:
    """유동성 분석 — 유동비율, 당좌비율, 현금 대비 단기차입금."""
    currentAssets = _getVals(inp.aSeries, "BS", "total_current_assets")
    currentLiab = _getVals(inp.aSeries, "BS", "total_current_liabilities")
    inventories = _getVals(inp.aSeries, "BS", "inventories")
    cash = _getVals(inp.aSeries, "BS", "cash_and_cash_equivalents")
    shortBorrow = _getVals(inp.aSeries, "BS", "short_term_borrowings")

    if not currentAssets or not currentLiab or len(currentAssets) < 2:
        return None

    parts: list[str] = []

    # 유동비율 추세
    crList = []
    for ca, cl in zip(currentAssets, currentLiab):
        crList.append(ca / cl * 100 if ca is not None and cl is not None and cl != 0 else None)
    cleanCr = [v for v in crList if v is not None]
    if len(cleanCr) >= 2:
        crDiff = cleanCr[-1] - cleanCr[-2]
        parts.append(f"유동비율 {cleanCr[-1]:.0f}%(전년 {cleanCr[-2]:.0f}%, {_pp(crDiff)})")

    # 당좌비율
    if inventories:
        qrList = []
        for ca, cl, inv in zip(currentAssets, currentLiab, inventories):
            if all(v is not None for v in (ca, cl, inv)) and cl != 0:
                qrList.append((ca - inv) / cl * 100)
            else:
                qrList.append(None)
        cleanQr = [v for v in qrList if v is not None]
        if cleanQr:
            parts.append(f"당좌비율 {cleanQr[-1]:.0f}%")

    # 현금 대비 단기차입금
    if cash and shortBorrow:
        cashClean = _lastN(cash, 1)
        sbClean = _lastN(shortBorrow, 1)
        if cashClean and sbClean and sbClean[-1] > 0:
            cashCover = cashClean[-1] / sbClean[-1]
            parts.append(f"현금/단기차입금 {cashCover:.1f}배")
            if cashCover < 0.5:
                parts.append("단기차입금 대비 현금 부족 — 유동성 리스크")

    if not parts:
        return None
    body = ". ".join(parts) + "."
    severity = "neutral"
    if cleanCr and cleanCr[-1] < 100:
        severity = "negative"
    elif cleanCr and cleanCr[-1] > 200:
        severity = "positive"
    return NarrativeParagraph(
        dimension="liquidity",
        title="유동성 분석",
        body=body,
        severity=severity,
    )


def _analyzeCapitalChange(inp: _Input) -> NarrativeParagraph | None:
    """자본변동 분석 — 이익잉여금 축적, 자사주/배당, 유상증자."""
    totalEquity = _getVals(inp.aSeries, "BS", "total_equity")
    retainedEarnings = _getVals(inp.aSeries, "BS", "retained_earnings")
    shareCapital = _getVals(inp.aSeries, "BS", "share_capital")
    if not shareCapital:
        shareCapital = _getVals(inp.aSeries, "BS", "capital_stock")
    treasuryStock = _getVals(inp.aSeries, "BS", "treasury_stock")
    if not treasuryStock:
        treasuryStock = _getVals(inp.aSeries, "BS", "treasury_shares")

    if not totalEquity or len(totalEquity) < 2:
        return None

    teClean = [v for v in totalEquity if v is not None]
    if len(teClean) < 2:
        return None

    parts: list[str] = []

    # 자본 증감
    teGr = (teClean[-1] - teClean[-2]) / abs(teClean[-2]) * 100
    parts.append(f"자기자본 {teClean[-1] / 1e8:,.0f}억(전년 대비 {teGr:+.1f}%)")

    # 이익잉여금 추세
    reClean = [v for v in retainedEarnings if v is not None] if retainedEarnings else []
    if len(reClean) >= 2:
        reGr = (reClean[-1] - reClean[-2]) / abs(reClean[-2]) * 100 if reClean[-2] != 0 else 0
        parts.append(f"이익잉여금 {reGr:+.1f}% 변동")
        if reGr < -5:
            parts.append("이익잉여금 감소 — 배당/자사주 또는 결손 영향")

    # 유상증자 감지
    scClean = [v for v in shareCapital if v is not None] if shareCapital else []
    if len(scClean) >= 2 and scClean[-2] != 0:
        scGr = (scClean[-1] - scClean[-2]) / abs(scClean[-2]) * 100
        if scGr > 5:
            parts.append(f"자본금 {scGr:+.1f}% 증가 — 유상증자 가능성")

    # 자사주 변동
    tsClean = [v for v in treasuryStock if v is not None] if treasuryStock else []
    if len(tsClean) >= 2:
        tsDiff = tsClean[-1] - tsClean[-2]
        if tsDiff < -1e9:  # 10억 이상 증가 (자사주는 음수이므로 감소 = 매입)
            parts.append("자사주 매입 확대 — 주주환원 강화 시그널")
        elif tsDiff > 1e9:
            parts.append("자사주 처분 — 희석 가능성")

    # Shareholder Yield (배당 + 자사주 매입) / 시가총액 (Lens 6)
    ni = _getVals(inp.aSeries, "IS", "net_profit")
    niClean = [v for v in ni if v is not None] if ni else []
    dividendPaid = _getVals(inp.aSeries, "CF", "dividends_paid")
    if not dividendPaid:
        dividendPaid = _getVals(inp.aSeries, "CF", "dividend_paid")
    divClean = [v for v in dividendPaid if v is not None] if dividendPaid else []
    if divClean and niClean:
        payoutRatio = abs(divClean[-1]) / niClean[-1] * 100 if niClean[-1] and niClean[-1] > 0 else None
        if payoutRatio is not None:
            parts.append(f"배당성향 {payoutRatio:.0f}%")
            if payoutRatio > 80:
                parts.append("배당성향 과다 — 재투자 여력 부족 가능")
            elif payoutRatio < 10 and niClean[-1] > 0:
                parts.append("배당성향 매우 낮음 — 내부유보 위주 경영")

    # Owner Earnings 추정 (= NI + D&A - maintenance CAPEX)
    depreciation = _getVals(inp.aSeries, "CF", "depreciation_and_amortization")
    if not depreciation:
        depreciation = _getVals(inp.aSeries, "IS", "depreciation")
    capex = _getVals(inp.aSeries, "CF", "capital_expenditure")
    if not capex:
        capex = _getVals(inp.aSeries, "CF", "acquisition_of_property_plant_and_equipment")
    depAll = [v for v in depreciation if v is not None] if depreciation else []
    capexAll = [v for v in capex if v is not None] if capex else []
    if niClean and depAll and capexAll:
        # maintenance capex ≈ 감가상각 수준으로 추정
        ownerEarnings = niClean[-1] + abs(depAll[-1]) - abs(capexAll[-1])
        if niClean[-1] != 0:
            oeRatio = ownerEarnings / niClean[-1]
            if abs(oeRatio) > 0.1:
                parts.append(f"Owner Earnings/NI {oeRatio:.2f}")
                if oeRatio > 1.3:
                    parts.append("유지보수 CAPEX 이하 투자 — 현금 창출 우수")
                elif oeRatio < 0.3:
                    parts.append("성장투자로 현금 대부분 소진 — 주주 환원 여력 제한적")

    if not parts:
        return None
    body = ". ".join(parts) + "."
    severity = "positive" if teGr > 10 else "neutral" if teGr > 0 else "negative"
    return NarrativeParagraph(
        dimension="capitalChange",
        title="자본변동 분석",
        body=body,
        severity=severity,
    )


def _analyzeCashflowDeep(inp: _Input) -> NarrativeParagraph | None:
    """현금흐름 심층 — 투자CF/재무CF 분해, FCF 추세, 배당 여력."""
    ocf = _getVals(inp.aSeries, "CF", "operating_cashflow")
    icf = _getVals(inp.aSeries, "CF", "investing_cashflow")
    if not icf:
        icf = _getVals(inp.aSeries, "CF", "investing_activities")
    fcf_cf = _getVals(inp.aSeries, "CF", "financing_cashflow")
    if not fcf_cf:
        fcf_cf = _getVals(inp.aSeries, "CF", "financing_activities")
    capex = _getVals(inp.aSeries, "CF", "capital_expenditure")
    if not capex:
        capex = _getVals(inp.aSeries, "CF", "acquisition_of_property_plant_and_equipment")
    dividend = _getVals(inp.aSeries, "CF", "dividends_paid")

    if not ocf or len(ocf) < 2:
        return None

    parts: list[str] = []

    # OCF/NI 비율 (기존 cashflowQuality 기능 포함)
    eq = inp.earningsQuality
    if eq and eq.cfToNi is not None:
        ratio = eq.cfToNi
        if ratio > 1.2:
            parts.append(f"OCF/순이익 {ratio:.1f}배 — 현금 뒷받침 우수")
        elif ratio > 0.8:
            parts.append(f"OCF/순이익 {ratio:.1f}배 — 보통 수준")
        elif ratio > 0:
            parts.append(f"OCF/순이익 {ratio:.1f}배 — 현금 뒷받침 미흡")
        else:
            parts.append(f"OCF/순이익 {ratio:.1f}배 — 영업현금흐름 적자")

    # OCF 추세
    ocfClean = [v for v in ocf if v is not None]
    if len(ocfClean) >= 2:
        trendDir = _trend(ocf)
        if trendDir == "improving":
            parts.append("영업CF 지속 개선 추세")
        elif trendDir == "deteriorating":
            parts.append("영업CF 지속 악화 추세 — 현금창출 능력 점검 필요")

    # FCF 추세 (OCF - CAPEX)
    if capex:
        fcfList = []
        for o, c in zip(ocf, capex):
            if o is not None and c is not None:
                fcfList.append(o - abs(c))
            else:
                fcfList.append(None)
        fcfClean = [v for v in fcfList if v is not None]
        if len(fcfClean) >= 2:
            parts.append(f"FCF {fcfClean[-1] / 1e8:,.0f}억(전년 {fcfClean[-2] / 1e8:,.0f}억)")
            if fcfClean[-1] < 0:
                parts.append("FCF 적자 — 투자 부담 과다")
            fcfTrend = _trend(fcfList)
            if fcfTrend == "deteriorating" and fcfClean[-1] > 0:
                parts.append("FCF 감소 추세 주의")

    # 배당 여력 (FCF / 배당)
    if capex and dividend:
        pairs = [(o, c, d) for o, c, d in zip(ocf, capex, dividend) if all(v is not None for v in (o, c, d))]
        if pairs:
            latestOcf, latestCapex, latestDiv = pairs[-1]
            fcf = latestOcf - abs(latestCapex)
            if latestDiv != 0:
                divCover = fcf / abs(latestDiv)
                parts.append(f"배당 커버리지(FCF/배당) {divCover:.1f}배")
                if divCover < 1:
                    parts.append("FCF로 배당 충당 불가 — 배당 지속성 의문")

    # CF 라이프사이클 스테이지 판별 (Lens 5)
    latestOcfVal = _lastN(ocf, 1)
    latestIcfVal = _lastN(icf, 1) if icf else []
    latestFcfVal = _lastN(fcf_cf, 1) if fcf_cf else []
    if latestOcfVal and latestIcfVal and latestFcfVal:
        oSign = latestOcfVal[-1] is not None and latestOcfVal[-1] > 0
        iSign = latestIcfVal[-1] is not None and latestIcfVal[-1] > 0
        fSign = latestFcfVal[-1] is not None and latestFcfVal[-1] > 0
        if oSign and not iSign and fSign:
            parts.append("CF패턴 [+,-,+] 성장기 — 영업흑자, 투자확대, 외부조달")
        elif oSign and not iSign and not fSign:
            parts.append("CF패턴 [+,-,-] 성숙기 — 자체 현금으로 투자와 주주환원 병행")
        elif not oSign and iSign and not fSign:
            parts.append("CF패턴 [-,+,-] 쇠퇴기 — 영업적자, 자산매각, 부채상환")
        elif not oSign and not iSign and fSign:
            parts.append("CF패턴 [-,-,+] 도입기 — 적자, 투자중, 외부조달 의존")
        elif not oSign and iSign and fSign:
            parts.append("CF패턴 [-,+,+] 구조조정 — 자산매각 + 외부조달로 적자 보전")

    if not parts:
        return None
    body = ". ".join(parts) + "."
    cfSev = "positive"
    if eq and eq.cfToNi is not None:
        if eq.cfToNi < 0.5:
            cfSev = "negative"
        elif eq.cfToNi < 0.8:
            cfSev = "warning"
        elif eq.cfToNi < 1.2:
            cfSev = "neutral"
    return NarrativeParagraph(
        dimension="cashflowDeep",
        title="현금흐름 심층분석",
        body=body,
        severity=cfSev,
    )


def _analyzeIsToCs(inp: _Input) -> NarrativeParagraph | None:
    """3표 연결 — IS 순이익 vs CF OCF 괴리 분석."""
    ni = _getVals(inp.aSeries, "IS", "net_profit")
    ocf = _getVals(inp.aSeries, "CF", "operating_cashflow")
    depreciation = _getVals(inp.aSeries, "CF", "depreciation_and_amortization")
    if not depreciation:
        depreciation = _getVals(inp.aSeries, "IS", "depreciation")

    if not ni or not ocf or len(ni) < 2:
        return None

    parts: list[str] = []

    # OCF - NI 갭 추세
    gapList = []
    for n, o in zip(ni, ocf):
        if n is not None and o is not None:
            gapList.append(o - n)
        else:
            gapList.append(None)

    gapClean = [v for v in gapList if v is not None]
    if len(gapClean) >= 2:
        latestGap = gapClean[-1]
        if abs(latestGap) > 1e9:  # 10억 이상 차이
            direction = "초과" if latestGap > 0 else "부족"
            parts.append(f"영업CF가 순이익 대비 {abs(latestGap) / 1e8:,.0f}억 {direction}")

    # OCF/NI 비율 추세 (시계열)
    ratioList = []
    for n, o in zip(ni, ocf):
        ratioList.append(o / n if n is not None and o is not None and n != 0 else None)
    ratioClean = [v for v in ratioList if v is not None]
    if len(ratioClean) >= 3:
        rTrend = _trend(ratioList)
        if rTrend == "deteriorating":
            parts.append("OCF/순이익 비율 추세적 하락 — 이익의 질 저하 경고")
        elif rTrend == "improving":
            parts.append("OCF/순이익 비율 추세적 개선 — 이익의 질 향상")

    # 감가상각 기여
    if depreciation:
        depClean = _lastN(depreciation, 2)
        niClean = _lastN(ni, 2)
        if len(depClean) >= 1 and len(niClean) >= 1 and niClean[-1] is not None and niClean[-1] != 0:
            depToNi = abs(depClean[-1]) / abs(niClean[-1])
            if depToNi > 0.5:
                parts.append(f"감가상각이 순이익의 {depToNi:.0%} — 비현금비용 기여 큼(OCF 양호 원인)")

    # Earnings Persistence (현금이익 비중, Lens 4)
    # 현금이익 = OCF, 발생이익 = NI - OCF
    niAll = [v for v in ni if v is not None]
    ocfAll = [v for v in ocf if v is not None]
    if len(niAll) >= 3 and len(ocfAll) >= 3:
        cashEarningsRatios = []
        for n, o in zip(niAll, ocfAll):
            if n != 0:
                cashEarningsRatios.append(o / n)
        if len(cashEarningsRatios) >= 3:
            avgCer = sum(cashEarningsRatios) / len(cashEarningsRatios)
            if avgCer > 1.2:
                parts.append(f"평균 OCF/NI {avgCer:.2f} — 높은 이익의 질(Earnings Persistence 양호)")
            elif avgCer < 0.5:
                parts.append(f"평균 OCF/NI {avgCer:.2f} — 발생이익 의존도 높음(이익 지속성 취약)")

    # incomeQualityRatio (직전 기간)
    if ratioClean:
        latest = ratioClean[-1]
        parts.append(f"이익품질비율(OCF/NI) {latest:.2f}")
        if latest < 0:
            parts.append("OCF 적자 — 이익의 현금 전환 실패")
        elif latest > 2.0:
            parts.append("OCF가 순이익의 2배 이상 — 비현금비용 또는 운전자본 환입 효과 큼")

    if not parts:
        return None
    body = ". ".join(parts) + "."
    severity = "neutral"
    if ratioClean and ratioClean[-1] < 0.5:
        severity = "warning"
    elif ratioClean and ratioClean[-1] > 1.5:
        severity = "positive"
    return NarrativeParagraph(
        dimension="isToCs",
        title="손익↔현금흐름 연결분석",
        body=body,
        severity=severity,
    )


def _analyzeCfToBs(inp: _Input) -> NarrativeParagraph | None:
    """3표 연결 — CF 투자활동 → BS 유형자산, CF 재무활동 → BS 차입금."""
    capex = _getVals(inp.aSeries, "CF", "capital_expenditure")
    if not capex:
        capex = _getVals(inp.aSeries, "CF", "acquisition_of_property_plant_and_equipment")
    depreciation = _getVals(inp.aSeries, "CF", "depreciation_and_amortization")
    if not depreciation:
        depreciation = _getVals(inp.aSeries, "IS", "depreciation")
    tangible = _getVals(inp.aSeries, "BS", "property_plant_and_equipment")
    shortBorrow = _getVals(inp.aSeries, "BS", "short_term_borrowings")
    longBorrow = _getVals(inp.aSeries, "BS", "long_term_borrowings")

    parts: list[str] = []

    # CAPEX vs 감가상각 (유지보수 투자 수준)
    if capex and depreciation:
        pairs = [(c, d) for c, d in zip(capex, depreciation) if c is not None and d is not None and d != 0]
        if pairs:
            latestCapex, latestDep = pairs[-1]
            capexToDep = abs(latestCapex) / abs(latestDep)
            parts.append(f"CAPEX/감가상각 {capexToDep:.1f}배")
            if capexToDep > 2.0:
                parts.append("감가상각의 2배 이상 투자 — 적극적 확장투자")
            elif capexToDep < 0.8:
                parts.append("감가상각 미만 투자 — 설비 노후화 리스크")

    # BS 유형자산 변동 vs CAPEX 규모
    if tangible and capex:
        tanClean = [v for v in tangible if v is not None]
        capexClean = [v for v in capex if v is not None]
        if len(tanClean) >= 2 and capexClean:
            tanChange = tanClean[-1] - tanClean[-2]
            latestCapex = abs(capexClean[-1])
            if latestCapex > 0:
                retentionRate = tanChange / latestCapex
                if retentionRate < 0:
                    parts.append("CAPEX 투입에도 유형자산 순감소 — 처분 또는 감가상각 과대")

    # BS 차입금 변동
    if shortBorrow and longBorrow:
        totalBorrowList = []
        for sb, lb in zip(shortBorrow, longBorrow):
            if sb is not None and lb is not None:
                totalBorrowList.append(sb + lb)
            else:
                totalBorrowList.append(None)
        bClean = [v for v in totalBorrowList if v is not None]
        if len(bClean) >= 2:
            bGr = (bClean[-1] - bClean[-2]) / abs(bClean[-2]) * 100 if bClean[-2] != 0 else 0
            if abs(bGr) > 15:
                direction = "증가" if bGr > 0 else "감소"
                parts.append(f"총차입금 {bGr:+.1f}% {direction}")

    if not parts:
        return None
    body = ". ".join(parts) + "."
    severity = "neutral"
    return NarrativeParagraph(
        dimension="cfToBs",
        title="현금흐름↔재무상태 연결분석",
        body=body,
        severity=severity,
    )


def _analyzeIsToBs(inp: _Input) -> NarrativeParagraph | None:
    """3표 연결 — IS 순이익 → BS 이익잉여금, 매출 → 매출채권/재고 비례."""
    ni = _getVals(inp.aSeries, "IS", "net_profit")
    retainedEarnings = _getVals(inp.aSeries, "BS", "retained_earnings")
    sales = _getVals(inp.aSeries, "IS", "sales")
    receivables = _getVals(inp.aSeries, "BS", "trade_receivable")
    if not receivables:
        receivables = _getVals(inp.aSeries, "BS", "trade_and_other_receivables")
    inventories = _getVals(inp.aSeries, "BS", "inventories")

    if not ni or not sales or len(ni) < 2:
        return None

    parts: list[str] = []

    # 순이익 → 이익잉여금 축적률
    if retainedEarnings:
        reClean = [v for v in retainedEarnings if v is not None]
        niClean = [v for v in ni if v is not None]
        if len(reClean) >= 2 and len(niClean) >= 1 and niClean[-1] != 0:
            reChange = reClean[-1] - reClean[-2]
            retentionRate = reChange / niClean[-1] * 100 if niClean[-1] != 0 else 0
            if retentionRate > 0:
                parts.append(f"순이익 중 {retentionRate:.0f}%가 잉여금으로 축적(배당성향 {100 - retentionRate:.0f}%)")
            elif retentionRate < -20:
                parts.append("이익잉여금 감소 — 순이익 대비 과도한 유출")

    # 매출 증가 vs 매출채권 증가 비례 여부
    salesClean = [v for v in sales if v is not None]
    arClean = [v for v in receivables if v is not None] if receivables else []
    if len(salesClean) >= 2 and len(arClean) >= 2:
        salesGr = (salesClean[-1] - salesClean[-2]) / abs(salesClean[-2]) * 100 if salesClean[-2] != 0 else 0
        arGr = (arClean[-1] - arClean[-2]) / abs(arClean[-2]) * 100 if arClean[-2] != 0 else 0
        gap = arGr - salesGr
        if gap > 20:
            parts.append(
                f"매출채권 증가율({arGr:+.1f}%)이 매출 증가율({salesGr:+.1f}%)을 크게 상회 — 수금 악화 또는 채널 스터핑 주의"
            )
        elif gap < -20 and arGr < 0:
            parts.append("매출채권 감소율이 매출 대비 과도 — 공격적 회수 또는 매출 구조 변화")

    # 매출 증가 vs 재고 증가 비례 여부
    invClean = [v for v in inventories if v is not None] if inventories else []
    if len(salesClean) >= 2 and len(invClean) >= 2:
        salesGr = (salesClean[-1] - salesClean[-2]) / abs(salesClean[-2]) * 100 if salesClean[-2] != 0 else 0
        invGr = (invClean[-1] - invClean[-2]) / abs(invClean[-2]) * 100 if invClean[-2] != 0 else 0
        gap = invGr - salesGr
        if gap > 15:
            parts.append(f"재고 증가율({invGr:+.1f}%)이 매출 증가율({salesGr:+.1f}%)을 상회 — 재고 리스크 주의")

    # Revenue Recognition Quality — 지수 분석 (Lens 4 강화)
    # 매출채권지수(DSRI) = (AR/Sales)t / (AR/Sales)t-1
    if len(salesClean) >= 2 and len(arClean) >= 2 and salesClean[-2] > 0 and salesClean[-1] > 0:
        arRatioPrev = arClean[-2] / salesClean[-2]
        arRatioCurr = arClean[-1] / salesClean[-1]
        if arRatioPrev > 0:
            dsri = arRatioCurr / arRatioPrev
            if dsri > 1.2:
                parts.append(f"매출채권지수(DSRI) {dsri:.2f} — 매출 대비 매출채권 비정상 팽창, 매출 인식 공격성 주의")
            elif dsri < 0.8:
                parts.append(f"매출채권지수(DSRI) {dsri:.2f} — 매출 대비 회수 효율 개선")

    # 재고자산지수 = (Inv/Sales)t / (Inv/Sales)t-1
    if len(salesClean) >= 2 and len(invClean) >= 2 and salesClean[-2] > 0 and salesClean[-1] > 0:
        invRatioPrev = invClean[-2] / salesClean[-2]
        invRatioCurr = invClean[-1] / salesClean[-1]
        if invRatioPrev > 0:
            invIdx = invRatioCurr / invRatioPrev
            if invIdx > 1.2:
                parts.append(f"재고자산지수 {invIdx:.2f} — 매출 대비 재고 과잉 축적, 수요 둔화 또는 과잉 생산 신호")

    if not parts:
        return None
    body = ". ".join(parts) + "."
    # severity 판단
    severity = "neutral"
    for p in parts:
        if "주의" in p or "과도" in p or "악화" in p:
            severity = "warning"
            break
    return NarrativeParagraph(
        dimension="isToBs",
        title="손익↔재무상태 연결분석",
        body=body,
        severity=severity,
    )


def _analyzeEarningsManipulation(inp: _Input) -> NarrativeParagraph | None:
    """Beneish M-Score 8변수 개별 분석 (Lens 4 — 이익의 질)."""
    eq = inp.earningsQuality
    if eq is None:
        return None
    mScore = getattr(eq, "beneishMScore", None)
    if mScore is None:
        return None

    parts: list[str] = []
    flagged = mScore < -1.78  # 조작 가능성 임계값

    if mScore < -2.22:
        parts.append(f"Beneish M-Score {mScore:.2f} — 이익 조작 가능성 낮음(양호)")
    elif mScore < -1.78:
        parts.append(f"Beneish M-Score {mScore:.2f} — 경계 구간(주의 관찰)")
    else:
        parts.append(f"Beneish M-Score {mScore:.2f} — 이익 조작 가능성 높음(경고)")

    # ratios에서 Beneish 세부 변수 추출 시도 (BeneishDetail이 있으면)
    ratios = inp.ratios
    if ratios is not None:
        # ratios 객체에서 개별 Beneish 지표 확인
        bd = getattr(ratios, "beneishDetail", None)
        if bd is not None and hasattr(bd, "dsri"):
            warnings = []
            if bd.dsri is not None and bd.dsri > 1.465:
                warnings.append(f"DSRI {bd.dsri:.2f}(매출채권지수 경고)")
            if bd.gmi is not None and bd.gmi > 1.193:
                warnings.append(f"GMI {bd.gmi:.2f}(매출총이익지수 경고)")
            if bd.aqi is not None and bd.aqi > 1.254:
                warnings.append(f"AQI {bd.aqi:.2f}(자산품질지수 경고)")
            if bd.sgi is not None and bd.sgi > 1.607:
                warnings.append(f"SGI {bd.sgi:.2f}(매출성장지수 경고)")
            if bd.depi is not None and bd.depi > 1.077:
                warnings.append(f"DEPI {bd.depi:.2f}(감가상각지수 경고)")
            if bd.tata is not None and bd.tata > 0.018:
                warnings.append(f"TATA {bd.tata:.3f}(발생이익비율 경고)")
            if warnings:
                parts.append("개별 경고: " + ", ".join(warnings))

    # aSeries 기반 직접 계산 (ratios에 BeneishDetail 없을 때)
    if len(parts) == 1:  # mScore만 있고 세부 없으면 직접 계산
        sales = _getVals(inp.aSeries, "IS", "sales")
        cogs = _getVals(inp.aSeries, "IS", "cost_of_sales")
        receivables = _getVals(inp.aSeries, "BS", "trade_receivable")
        if not receivables:
            receivables = _getVals(inp.aSeries, "BS", "trade_and_other_receivables")
        sClean = [v for v in sales if v is not None] if sales else []
        cClean = [v for v in cogs if v is not None] if cogs else []
        arClean = [v for v in receivables if v is not None] if receivables else []
        if len(sClean) >= 2 and len(arClean) >= 2:
            arSalesRatioPrev = arClean[-2] / sClean[-2] if sClean[-2] > 0 else 0
            arSalesRatioCurr = arClean[-1] / sClean[-1] if sClean[-1] > 0 else 0
            if arSalesRatioPrev > 0:
                dsri = arSalesRatioCurr / arSalesRatioPrev
                if dsri > 1.465:
                    parts.append(f"DSRI {dsri:.2f} — 매출 대비 매출채권 비정상 팽창")
        if len(sClean) >= 2 and len(cClean) >= 2:
            gmPrev = (sClean[-2] - cClean[-2]) / sClean[-2] if sClean[-2] > 0 else 0
            gmCurr = (sClean[-1] - cClean[-1]) / sClean[-1] if sClean[-1] > 0 else 0
            if gmCurr > 0:
                gmi = gmPrev / gmCurr
                if gmi > 1.193:
                    parts.append(f"GMI {gmi:.2f} — 매출총이익률 악화(이익 품질 저하)")

    if not parts:
        return None
    body = ". ".join(parts) + "."
    severity = "warning" if flagged else "positive" if mScore < -2.22 else "neutral"
    return NarrativeParagraph(
        dimension="earningsManipulation", title="이익조작 감지(Beneish)", body=body, severity=severity
    )


def _analyzeDistressModels(inp: _Input) -> NarrativeParagraph | None:
    """부실예측 다중모델 교차판정 (Lens 10+15)."""
    ratios = inp.ratios
    if ratios is None:
        return None

    parts: list[str] = []
    models: dict[str, str] = {}  # 모델명 → safe/warning/danger

    # Piotroski F-Score
    piotroski = getattr(ratios, "piotroskiFScore", None)
    if piotroski is not None:
        if piotroski >= 7:
            models["Piotroski"] = "safe"
            parts.append(f"Piotroski F-Score {piotroski}/9(건전)")
        elif piotroski <= 3:
            models["Piotroski"] = "danger"
            parts.append(f"Piotroski F-Score {piotroski}/9(위험)")
        else:
            models["Piotroski"] = "neutral"
            parts.append(f"Piotroski F-Score {piotroski}/9(보통)")

    # Altman Z-Score
    altmanZ = getattr(ratios, "altmanZScore", None)
    if altmanZ is not None:
        if altmanZ > 2.99:
            models["Altman"] = "safe"
            parts.append(f"Altman Z-Score {altmanZ:.2f}(안전)")
        elif altmanZ < 1.81:
            models["Altman"] = "danger"
            parts.append(f"Altman Z-Score {altmanZ:.2f}(부실 위험)")
        else:
            models["Altman"] = "neutral"
            parts.append(f"Altman Z-Score {altmanZ:.2f}(회색지대)")

    # Altman Z''-Score (신흥시장)
    altmanZpp = getattr(ratios, "altmanZppScore", None)
    if altmanZpp is not None:
        if altmanZpp > 2.6:
            models["Altman-Z''"] = "safe"
        elif altmanZpp < 1.1:
            models["Altman-Z''"] = "danger"
        else:
            models["Altman-Z''"] = "neutral"
        parts.append(f"Z''-Score {altmanZpp:.2f}")

    # Beneish M-Score (이미 earningsManipulation에서 분석하지만, 부실 관점 교차)
    eq = inp.earningsQuality
    beneish = getattr(eq, "beneishMScore", None) if eq else None
    if beneish is not None:
        if beneish < -2.22:
            models["Beneish"] = "safe"
        elif beneish > -1.78:
            models["Beneish"] = "danger"
        else:
            models["Beneish"] = "neutral"

    if not models:
        return None

    # 교차판정 — 모델 간 consensus / disagreement
    safeCount = sum(1 for v in models.values() if v == "safe")
    dangerCount = sum(1 for v in models.values() if v == "danger")
    total = len(models)

    if total >= 2:
        if safeCount == total:
            parts.append(f"부실모델 {total}개 전원 안전 판정 — 재무건전성 높음")
        elif dangerCount == total:
            parts.append(f"부실모델 {total}개 전원 위험 판정 — 심각한 부실 신호")
        elif dangerCount > 0 and safeCount > 0:
            parts.append(
                f"모델 간 disagreement(안전 {safeCount} vs 위험 {dangerCount}/{total}) — 불확실성 구간, 심층 분석 필요"
            )
        elif dangerCount > 0:
            parts.append(f"부실 위험 모델 {dangerCount}개 경고 — 재무 안정성 점검 필요")

    if not parts:
        return None
    body = ". ".join(parts) + "."
    severity = (
        "negative"
        if dangerCount >= 2
        else "warning"
        if dangerCount >= 1
        else "positive"
        if safeCount == total
        else "neutral"
    )
    return NarrativeParagraph(dimension="distressModels", title="부실예측 다중모델", body=body, severity=severity)


def _analyzeCostStructure(inp: _Input) -> NarrativeParagraph | None:
    """비용 구조 분해 — costByNature 기반 원재료/인건비/감가상각 비중 (Lens 13)."""
    costDf = inp.costByNatureDf
    if costDf is None:
        return None

    try:
        import polars as pl

        if not isinstance(costDf, pl.DataFrame) or len(costDf) == 0:
            return None
    except ImportError:
        return None

    parts: list[str] = []
    cols = costDf.columns

    sales = _getVals(inp.aSeries, "IS", "sales")
    salesClean = [v for v in sales if v is not None] if sales else []

    # 주요 비용 항목 비중 추출
    for keyword, label in [
        ("원재료", "원재료비"),
        ("인건비", "인건비"),
        ("감가상각", "감가상각비"),
        ("외주", "외주가공비"),
        ("연료", "연료비"),
    ]:
        matchCols = [c for c in cols if keyword in c]
        if not matchCols:
            continue
        try:
            vals = costDf[matchCols[0]].to_list()
            cleanVals = [v for v in vals if v is not None]
            if len(cleanVals) >= 2:
                # 매출 대비 비중 계산
                if salesClean and len(salesClean) >= len(cleanVals):
                    latestRatio = cleanVals[-1] / salesClean[-1] * 100 if salesClean[-1] > 0 else None
                    prevRatio = (
                        cleanVals[-2] / salesClean[-(len(cleanVals))] * 100
                        if len(salesClean) >= 2 and salesClean[-2] > 0
                        else None
                    )
                    if latestRatio is not None:
                        if prevRatio is not None:
                            diff = latestRatio - prevRatio
                            parts.append(f"{label}/매출 {latestRatio:.1f}%({_pp(diff)})")
                        else:
                            parts.append(f"{label}/매출 {latestRatio:.1f}%")
                elif len(cleanVals) >= 2:
                    diff = cleanVals[-1] - cleanVals[-2]
                    pctDiff = diff / abs(cleanVals[-2]) * 100 if cleanVals[-2] != 0 else 0
                    parts.append(f"{label} {pctDiff:+.1f}% 변동")
        except (AttributeError, ValueError, IndexError):
            continue

    # 고정비/변동비 추이 추정 (원재료=변동, 감가상각+인건비=고정)
    fixedCols = [c for c in cols if any(k in c for k in ("인건비", "감가상각", "임차"))]
    variableCols = [c for c in cols if any(k in c for k in ("원재료", "외주", "연료"))]
    if fixedCols and variableCols and salesClean:
        try:
            fixedTotal = sum(costDf[c].to_list()[-1] or 0 for c in fixedCols)
            variableTotal = sum(costDf[c].to_list()[-1] or 0 for c in variableCols)
            total = fixedTotal + variableTotal
            if total > 0:
                fixedRatio = fixedTotal / total * 100
                parts.append(f"고정비 비중 추정 {fixedRatio:.0f}% / 변동비 {100 - fixedRatio:.0f}%")
        except (AttributeError, ValueError, IndexError):
            pass

    if not parts:
        return None
    body = ". ".join(parts) + "."
    return NarrativeParagraph(dimension="costStructure", title="비용 구조 분석", body=body, severity="neutral")


def _analyzeSalesOrder(inp: _Input) -> NarrativeParagraph | None:
    """수주잔고 분석 — Book-to-Bill, 수주 추이 (Lens 13)."""
    soDf = inp.salesOrderDf
    if soDf is None:
        return None

    try:
        import polars as pl

        if not isinstance(soDf, pl.DataFrame) or len(soDf) == 0:
            return None
    except ImportError:
        return None

    parts: list[str] = []
    cols = soDf.columns

    # 수주잔고 컬럼 탐색
    backlogCol = None
    orderCol = None
    salesCol = None
    for c in cols:
        cl = c.lower()
        if "잔고" in c or "backlog" in cl:
            backlogCol = c
        elif "수주" in c and "잔고" not in c or "order" in cl:
            orderCol = c
        elif "매출" in c or "sales" in cl or "납품" in c:
            salesCol = c

    if backlogCol:
        try:
            vals = soDf[backlogCol].to_list()
            cleanVals = [v for v in vals if v is not None]
            if len(cleanVals) >= 2:
                diff = (cleanVals[-1] - cleanVals[-2]) / abs(cleanVals[-2]) * 100 if cleanVals[-2] != 0 else 0
                parts.append(f"수주잔고 {cleanVals[-1] / 1e8:,.0f}억(전년 대비 {diff:+.1f}%)")

            # Book-to-Bill 비율 (수주잔고/매출)
            sales = _getVals(inp.aSeries, "IS", "sales")
            salesClean = [v for v in sales if v is not None] if sales else []
            if salesClean and len(cleanVals) >= 1 and salesClean[-1] > 0:
                btb = cleanVals[-1] / salesClean[-1]
                parts.append(f"수주잔고/매출 비율 {btb:.2f}")
                if btb > 1.5:
                    parts.append("수주잔고 풍부 — 1.5년 이상 매출 보장")
                elif btb < 0.3:
                    parts.append("수주잔고 부족 — 매출 가시성 낮음")
        except (AttributeError, ValueError, IndexError):
            pass

    if not parts:
        return None
    body = ". ".join(parts) + "."
    severity = (
        "positive" if any("풍부" in p for p in parts) else "warning" if any("부족" in p for p in parts) else "neutral"
    )
    return NarrativeParagraph(dimension="salesOrder", title="수주잔고 분석", body=body, severity=severity)


def _analyzeProductMix(inp: _Input) -> NarrativeParagraph | None:
    """제품별 매출 구성 + 비중 변화 (Lens 13)."""
    psDf = inp.productServiceDf
    if psDf is None:
        return None

    try:
        import polars as pl

        if not isinstance(psDf, pl.DataFrame) or len(psDf) == 0:
            return None
    except ImportError:
        return None

    parts: list[str] = []
    cols = psDf.columns

    # 제품명 + 매출 컬럼 탐색
    nameCol = None
    valCols = []
    for c in cols:
        cl = c.lower()
        if "품목" in c or "제품" in c or "부문" in c or "product" in cl or "name" in cl:
            nameCol = c
        elif any(ch.isdigit() for ch in c) or "매출" in c or "금액" in c or "sales" in cl:
            valCols.append(c)

    if nameCol and valCols:
        try:
            names = psDf[nameCol].to_list()
            latestCol = valCols[-1]
            vals = psDf[latestCol].to_list()
            total = sum(v for v in vals if v is not None and v > 0)
            if total > 0:
                items = [(n, v) for n, v in zip(names, vals) if v is not None and v > 0]
                items.sort(key=lambda x: x[1], reverse=True)
                topItems = items[:3]
                topParts = [f"{n} {v / total * 100:.0f}%" for n, v in topItems]
                parts.append(f"제품 구성: {', '.join(topParts)}")

                # 집중도
                if items:
                    topShare = items[0][1] / total * 100
                    if topShare > 60:
                        parts.append(f"최대 제품 비중 {topShare:.0f}% — 높은 제품 집중 리스크")

                # 비중 변화 (이전 기간 데이터 있으면)
                if len(valCols) >= 2:
                    prevCol = valCols[-2]
                    prevVals = psDf[prevCol].to_list()
                    prevTotal = sum(v for v in prevVals if v is not None and v > 0)
                    if prevTotal > 0 and items:
                        topName = items[0][0]
                        topIdx = names.index(topName) if topName in names else -1
                        if topIdx >= 0 and topIdx < len(prevVals) and prevVals[topIdx] is not None:
                            prevShare = prevVals[topIdx] / prevTotal * 100
                            currShare = items[0][1] / total * 100
                            shareDiff = currShare - prevShare
                            if abs(shareDiff) > 3:
                                parts.append(f"주력제품 비중 {_pp(shareDiff)}")
        except (AttributeError, ValueError, IndexError, KeyError):
            pass

    if not parts:
        return None
    body = ". ".join(parts) + "."
    severity = "warning" if any("리스크" in p for p in parts) else "neutral"
    return NarrativeParagraph(dimension="productMix", title="제품별 매출 구성", body=body, severity=severity)


def _analyzeQuarterlyMomentum(inp: _Input) -> NarrativeParagraph | None:
    """분기별 손익 QoQ/YoY + 계절성 패턴 (Lens 13)."""
    qDf = inp.quarterlyIsDf
    if qDf is None:
        return None

    try:
        import polars as pl

        if not isinstance(qDf, pl.DataFrame) or len(qDf) == 0:
            return None
    except ImportError:
        return None

    parts: list[str] = []
    cols = qDf.columns

    # 분기별 매출/영업이익 시계열 추출
    salesCol = None
    opCol = None
    periodCol = None
    for c in cols:
        cl = c.lower()
        if "매출" in c and "원가" not in c or "sales" in cl or "revenue" in cl:
            salesCol = c
        elif "영업이익" in c or "operating" in cl:
            opCol = c
        elif "기간" in c or "period" in cl or "quarter" in cl or "분기" in c:
            periodCol = c

    if salesCol:
        try:
            qSales = qDf[salesCol].to_list()
            cleanQ = [v for v in qSales if v is not None]
            if len(cleanQ) >= 4:
                # 최근 4분기 QoQ 추세
                latest = cleanQ[-1]
                prev = cleanQ[-2]
                qoq = (latest - prev) / abs(prev) * 100 if prev != 0 else 0
                parts.append(f"직전분기 매출 QoQ {qoq:+.1f}%")

                # YoY (4분기 전 대비)
                if len(cleanQ) >= 5:
                    yoyBase = cleanQ[-5]
                    if yoyBase != 0:
                        yoy = (latest - yoyBase) / abs(yoyBase) * 100
                        parts.append(f"YoY {yoy:+.1f}%")

                # 계절성 패턴 (Q4 > Q1 패턴 등)
                if len(cleanQ) >= 8:
                    # 최근 2년 분기별 평균으로 계절성 탐지
                    q4s = [cleanQ[i] for i in range(3, len(cleanQ), 4)]
                    q1s = [cleanQ[i] for i in range(0, len(cleanQ), 4)]
                    if q4s and q1s:
                        avgQ4 = sum(q4s) / len(q4s)
                        avgQ1 = sum(q1s) / len(q1s)
                        if avgQ4 > avgQ1 * 1.3:
                            parts.append("Q4 매출 집중 패턴 — 연말 계절성")
                        elif avgQ1 > avgQ4 * 1.3:
                            parts.append("Q1 매출 집중 패턴 — 연초 계절성")
        except (AttributeError, ValueError, IndexError):
            pass

    if not parts:
        return None
    body = ". ".join(parts) + "."
    severity = "neutral"
    return NarrativeParagraph(dimension="quarterlyMomentum", title="분기별 모멘텀", body=body, severity=severity)


def _analyzeBusinessStrategy(inp: _Input) -> NarrativeParagraph | None:
    """정량→정성 브릿지 — 수치 패턴에서 사업 전략 자동 분류 (Lens 13 종합)."""
    sales = _getVals(inp.aSeries, "IS", "sales")
    op = _getVals(inp.aSeries, "IS", "operating_profit")
    cogs = _getVals(inp.aSeries, "IS", "cost_of_sales")
    if not sales or len(sales) < 3:
        return None

    sClean = [v for v in sales if v is not None]
    opClean = [v for v in op if v is not None] if op else []
    cClean = [v for v in cogs if v is not None] if cogs else []
    if len(sClean) < 3:
        return None

    parts: list[str] = []

    # 매출 CAGR
    salesCagr = ((sClean[-1] / sClean[0]) ** (1 / (len(sClean) - 1)) - 1) * 100 if sClean[0] > 0 else 0

    # OPM 수준
    latestOpm = opClean[-1] / sClean[-1] * 100 if opClean and sClean[-1] > 0 else 0

    # 원가율 추이
    cogsRatio = cClean[-1] / sClean[-1] * 100 if cClean and sClean[-1] > 0 else 0
    prevCogsRatio = cClean[-2] / sClean[-2] * 100 if len(cClean) >= 2 and len(sClean) >= 2 and sClean[-2] > 0 else 0

    # 전략 분류
    strategy = ""
    if salesCagr > 15 and latestOpm > 15:
        strategy = "고성장·고마진(프리미엄/기술주도형)"
    elif salesCagr > 15 and latestOpm <= 5:
        strategy = "고성장·저마진(시장점유율 확대전략)"
    elif salesCagr < 3 and latestOpm > 15:
        strategy = "안정형·고마진(캐시카우/니치마켓)"
    elif salesCagr < 3 and latestOpm <= 5:
        strategy = "저성장·저마진(원가경쟁/구조조정 필요)"
    elif salesCagr > 5 and cogsRatio < prevCogsRatio - 2:
        strategy = "수익구조 개선형(원가 절감 성과)"
    elif salesCagr > 5 and cogsRatio > prevCogsRatio + 2:
        strategy = "외형 확대형(원가 전가 미흡)"
    elif abs(salesCagr) <= 5 and latestOpm > 5:
        strategy = "안정 성숙형(매출 보합, 수익성 유지)"
    else:
        strategy = "전환기(명확한 패턴 미형성)"

    parts.append(f"사업전략 유형: {strategy}")
    parts.append(f"매출 CAGR {salesCagr:.1f}%, 영업이익률 {latestOpm:.1f}%")

    # segments 정보가 있으면 포트폴리오 판단
    segDf = inp.segmentsDf
    if segDf is not None:
        try:
            import polars as pl

            if isinstance(segDf, pl.DataFrame) and len(segDf) >= 2:
                # 부문수
                parts.append(f"사업부문 {len(segDf)}개 운영")
        except (ImportError, AttributeError):
            pass

    body = ". ".join(parts) + "."
    severity = (
        "positive"
        if "고성장·고마진" in strategy or "개선형" in strategy
        else "warning"
        if "저성장·저마진" in strategy
        else "neutral"
    )
    return NarrativeParagraph(dimension="businessStrategy", title="사업전략 분류", body=body, severity=severity)


def _analyzeHumanCapital(inp: _Input) -> NarrativeParagraph | None:
    """인적자본 분석 — 1인당 매출/영업이익, 직원수 추이 (Lens 14)."""
    empDf = inp.employeeDf
    if empDf is None:
        return None

    try:
        import polars as pl

        if not isinstance(empDf, pl.DataFrame) or len(empDf) == 0:
            return None
    except ImportError:
        return None

    parts: list[str] = []
    cols = empDf.columns

    # 직원수 컬럼 탐색
    headcountCol = None
    for c in cols:
        if "직원" in c or "인원" in c or "총원" in c or "headcount" in c.lower():
            headcountCol = c
            break

    if headcountCol:
        try:
            headcounts = empDf[headcountCol].to_list()
            hClean = [v for v in headcounts if v is not None and v > 0]
            if hClean:
                sales = _getVals(inp.aSeries, "IS", "sales")
                op = _getVals(inp.aSeries, "IS", "operating_profit")
                sClean = [v for v in sales if v is not None] if sales else []
                opClean = [v for v in op if v is not None] if op else []

                # 1인당 매출
                if sClean:
                    perCapSales = sClean[-1] / hClean[-1] / 1e8  # 억 단위
                    parts.append(f"직원수 {hClean[-1]:,.0f}명, 1인당 매출 {perCapSales:.1f}억")

                # 1인당 영업이익
                if opClean and hClean:
                    perCapOp = opClean[-1] / hClean[-1] / 1e8
                    parts.append(f"1인당 영업이익 {perCapOp:.2f}억")

                # 추이
                if len(hClean) >= 2:
                    hGr = (hClean[-1] - hClean[-2]) / abs(hClean[-2]) * 100
                    parts.append(f"직원수 {hGr:+.1f}% 변동")
                    if sClean and len(sClean) >= 2 and sClean[-2] > 0:
                        sGr = (sClean[-1] - sClean[-2]) / abs(sClean[-2]) * 100
                        if hGr > sGr + 5:
                            parts.append("직원 증가율 > 매출 증가율 — 생산성 하락 추세")
                        elif sGr > hGr + 5:
                            parts.append("매출 증가율 > 직원 증가율 — 생산성 향상")
        except (AttributeError, ValueError, IndexError):
            pass

    if not parts:
        return None
    body = ". ".join(parts) + "."
    severity = "warning" if any("하락" in p for p in parts) else "neutral"
    return NarrativeParagraph(dimension="humanCapital", title="인적자본 분석", body=body, severity=severity)


def _analyzeRndEfficiency(inp: _Input) -> NarrativeParagraph | None:
    """R&D 투자 효율성 — R&D/매출 비율, 추이 (Lens 14)."""
    rndDf = inp.rndDf
    if rndDf is None:
        return None

    try:
        import polars as pl

        if not isinstance(rndDf, pl.DataFrame) or len(rndDf) == 0:
            return None
    except ImportError:
        return None

    parts: list[str] = []
    cols = rndDf.columns

    # R&D 금액 컬럼 탐색
    rndCol = None
    for c in cols:
        cl = c.lower()
        if "연구" in c or "개발" in c or "r&d" in cl or "rnd" in cl or "금액" in c:
            rndCol = c
            break

    if rndCol:
        try:
            rndVals = rndDf[rndCol].to_list()
            rClean = [v for v in rndVals if v is not None and v > 0]
            if rClean:
                sales = _getVals(inp.aSeries, "IS", "sales")
                sClean = [v for v in sales if v is not None] if sales else []

                if sClean and sClean[-1] > 0:
                    rndIntensity = rClean[-1] / sClean[-1] * 100
                    parts.append(f"R&D/매출 {rndIntensity:.1f}%")
                    if rndIntensity > 10:
                        parts.append("R&D 집약적 — 기술주도형 기업")
                    elif rndIntensity < 1:
                        parts.append("R&D 투자 미미")

                # R&D 지출 추이
                if len(rClean) >= 2:
                    rGr = (rClean[-1] - rClean[-2]) / abs(rClean[-2]) * 100
                    parts.append(f"R&D 지출 {rGr:+.1f}% 변동")

                    # R&D 투자 대비 매출 증가 효율
                    if sClean and len(sClean) >= 2 and sClean[-2] > 0:
                        sGr = (sClean[-1] - sClean[-2]) / abs(sClean[-2]) * 100
                        if rGr > 20 and sGr < 5:
                            parts.append("R&D 대폭 확대에도 매출 정체 — 투자 회수 시차 또는 효율성 점검 필요")
                        elif sGr > 10 and rGr > 10:
                            parts.append("R&D 확대 + 매출 성장 동반 — 투자 효율 양호")
        except (AttributeError, ValueError, IndexError):
            pass

    if not parts:
        return None
    body = ". ".join(parts) + "."
    severity = "neutral"
    return NarrativeParagraph(dimension="rndEfficiency", title="R&D 투자 효율", body=body, severity=severity)


def _analyzeValueCreation(inp: _Input) -> NarrativeParagraph | None:
    """EVA + 가치창출 판정 — ROIC vs WACC (Lens 6)."""
    op = _getVals(inp.aSeries, "IS", "operating_profit")
    totalAssets = _getVals(inp.aSeries, "BS", "total_assets")
    currentLiab = _getVals(inp.aSeries, "BS", "current_liabilities")
    if not currentLiab:
        currentLiab = _getVals(inp.aSeries, "BS", "total_current_liabilities")
    cash = _getVals(inp.aSeries, "BS", "cash_and_cash_equivalents")
    totalEquity = _getVals(inp.aSeries, "BS", "total_equity")
    totalLiab = _getVals(inp.aSeries, "BS", "total_liabilities")

    opClean = [v for v in op if v is not None] if op else []
    taClean = [v for v in totalAssets if v is not None] if totalAssets else []
    clClean = [v for v in currentLiab if v is not None] if currentLiab else []
    cashClean = [v for v in cash if v is not None] if cash else []
    teClean = [v for v in totalEquity if v is not None] if totalEquity else []
    tlClean = [v for v in totalLiab if v is not None] if totalLiab else []

    if not opClean or not taClean or len(opClean) < 2:
        return None

    parts: list[str] = []
    taxRate = 0.22  # 법인세율 22% 근사

    # Invested Capital = 총자산 - 유동부채 - 현금
    cl = clClean[-1] if clClean else 0
    ca = cashClean[-1] if cashClean else 0
    ic = taClean[-1] - cl - ca
    if ic <= 0:
        return None

    nopat = opClean[-1] * (1 - taxRate)
    roic = nopat / ic * 100

    # WACC 추정 (간이: 자기자본비용 10% + 부채비용 3% × (1-세율))
    equity = teClean[-1] if teClean else 0
    debt = tlClean[-1] if tlClean else 0
    totalCap = equity + debt
    if totalCap > 0 and equity > 0:
        equityWeight = equity / totalCap
        debtWeight = debt / totalCap
        costOfEquity = 0.10  # 주주 기대수익률 10% 근사
        costOfDebt = 0.03  # 세후 부채비용 3% 근사
        wacc = (equityWeight * costOfEquity + debtWeight * costOfDebt * (1 - taxRate)) * 100
    else:
        wacc = 8.0  # 기본값

    # EVA = NOPAT - IC × WACC
    eva = nopat - ic * (wacc / 100)
    evaBillions = eva / 1e8  # 억 단위

    parts.append(f"ROIC {roic:.1f}% vs WACC {wacc:.1f}%")
    spread = roic - wacc
    if spread > 3:
        parts.append(f"경제적 부가가치(EVA) {evaBillions:+,.0f}억 — 가치 창출 기업")
    elif spread > 0:
        parts.append(f"EVA {evaBillions:+,.0f}억 — 소폭 가치 창출")
    elif spread > -3:
        parts.append(f"EVA {evaBillions:+,.0f}억 — 가치 중립(WACC 근접)")
    else:
        parts.append(f"EVA {evaBillions:+,.0f}억 — 가치 파괴(자본비용 미달)")

    # ROIC 추이 (2년 이상)
    if len(opClean) >= 2 and len(taClean) >= 2:
        prevCl = clClean[-2] if len(clClean) >= 2 else 0
        prevCash = cashClean[-2] if len(cashClean) >= 2 else 0
        prevIc = taClean[-2] - prevCl - prevCash
        if prevIc > 0:
            prevNopat = opClean[-2] * (1 - taxRate)
            prevRoic = prevNopat / prevIc * 100
            roicDiff = roic - prevRoic
            if abs(roicDiff) > 1:
                label = "자본효율 개선" if roicDiff > 0 else "자본효율 악화"
                parts.append(f"ROIC {_pp(roicDiff)}({label})")

    body = ". ".join(parts) + "."
    severity = "positive" if spread > 3 else "neutral" if spread > 0 else "warning" if spread > -3 else "negative"
    return NarrativeParagraph(dimension="valueCreation", title="가치창출 분석(EVA)", body=body, severity=severity)


def _analyzeIndexTrend(inp: _Input) -> NarrativeParagraph | None:
    """지수형 분석 — 기준년=100, 주요 계정 추이, 비정상 팽창 감지 (Lens 3)."""
    sales = _getVals(inp.aSeries, "IS", "sales")
    op = _getVals(inp.aSeries, "IS", "operating_profit")
    ni = _getVals(inp.aSeries, "IS", "net_profit")
    receivables = _getVals(inp.aSeries, "BS", "trade_receivable")
    if not receivables:
        receivables = _getVals(inp.aSeries, "BS", "trade_and_other_receivables")
    inventories = _getVals(inp.aSeries, "BS", "inventories")
    totalAssets = _getVals(inp.aSeries, "BS", "total_assets")
    totalEquity = _getVals(inp.aSeries, "BS", "total_equity")

    if not sales or len(sales) < 3:
        return None

    def _toIndex(vals: list[float | None]) -> list[float | None]:
        """첫 non-None 값 = 100 기준 지수 변환."""
        base = next((v for v in vals if v is not None and v != 0), None)
        if base is None:
            return [None] * len(vals)
        return [round(v / base * 100, 1) if v is not None else None for v in vals]

    salesIdx = _toIndex(sales)
    opIdx = _toIndex(op) if op else []
    niIdx = _toIndex(ni) if ni else []
    arIdx = _toIndex(receivables) if receivables else []
    invIdx = _toIndex(inventories) if inventories else []
    taIdx = _toIndex(totalAssets) if totalAssets else []
    teIdx = _toIndex(totalEquity) if totalEquity else []

    parts: list[str] = []

    # 매출 지수 추이
    salesIdxClean = [v for v in salesIdx if v is not None]
    if len(salesIdxClean) >= 3:
        parts.append(f"매출지수 {salesIdxClean[0]:.0f}→{salesIdxClean[-1]:.0f}(기준년=100)")

    # 매출채권지수 vs 매출지수 괴리
    arIdxClean = [v for v in arIdx if v is not None]
    if len(arIdxClean) >= 3 and len(salesIdxClean) >= 3:
        arGap = arIdxClean[-1] - salesIdxClean[-1]
        if arGap > 30:
            parts.append(
                f"매출채권지수({arIdxClean[-1]:.0f})가 매출지수({salesIdxClean[-1]:.0f}) 대비 {arGap:.0f}p 초과 팽창 — 수금 악화 또는 매출 인식 공격성"
            )
        elif arGap < -30:
            parts.append(f"매출채권지수가 매출 대비 {abs(arGap):.0f}p 축소 — 회수 효율 개선")

    # 재고지수 vs 매출지수 괴리
    invIdxClean = [v for v in invIdx if v is not None]
    if len(invIdxClean) >= 3 and len(salesIdxClean) >= 3:
        invGap = invIdxClean[-1] - salesIdxClean[-1]
        if invGap > 30:
            parts.append(
                f"재고지수({invIdxClean[-1]:.0f})가 매출지수 대비 {invGap:.0f}p 초과 팽창 — 재고 과잉 축적 경고"
            )

    # 영업이익지수 vs 매출지수 (마진 변화 시각화)
    opIdxClean = [v for v in opIdx if v is not None]
    if len(opIdxClean) >= 3 and len(salesIdxClean) >= 3:
        opGap = opIdxClean[-1] - salesIdxClean[-1]
        if opGap > 20:
            parts.append(f"영업이익지수({opIdxClean[-1]:.0f})가 매출지수 상회 — 수익성 레버리지 확대")
        elif opGap < -20:
            parts.append(f"영업이익지수({opIdxClean[-1]:.0f})가 매출지수 하회 — 마진 압축")

    # 자산지수 vs 자본지수 (레버리지 변화)
    taIdxClean = [v for v in taIdx if v is not None]
    teIdxClean = [v for v in teIdx if v is not None]
    if len(taIdxClean) >= 3 and len(teIdxClean) >= 3:
        leverageGap = taIdxClean[-1] - teIdxClean[-1]
        if leverageGap > 30:
            parts.append(f"자산지수({taIdxClean[-1]:.0f}) vs 자본지수({teIdxClean[-1]:.0f}) 괴리 확대 — 레버리지 증가")

    if not parts:
        return None
    body = ". ".join(parts) + "."
    severity = "neutral"
    for p in parts:
        if "경고" in p or "공격성" in p or "과잉" in p:
            severity = "warning"
            break
    return NarrativeParagraph(dimension="indexTrend", title="지수형 추세 분석", body=body, severity=severity)


# ══════════════════════════════════════
# 교차참조 + 전망
# ══════════════════════════════════════


def _detectCrossReferences(paragraphs: list[NarrativeParagraph]) -> list[str]:
    """차원 간 교차 패턴 탐지."""
    dimMap = {p.dimension: p for p in paragraphs}
    refs: list[str] = []

    margin = dimMap.get("margin")
    eff = dimMap.get("efficiency")
    growth = dimMap.get("growth")
    cf = dimMap.get("cashflowDeep") or dimMap.get("cashflow")
    dp = dimMap.get("dupont")
    sector = dimMap.get("sectorRelative")
    segment = dimMap.get("segment")
    bs = dimMap.get("bsStructure")
    debt = dimMap.get("debtStructure")
    liq = dimMap.get("liquidity")
    isToCs = dimMap.get("isToCs")
    isToBs = dimMap.get("isToBs")

    # ── 기존 교차 패턴 ──
    if margin and eff and margin.severity == "positive" and eff.severity == "warning":
        refs.append("마진 개선에도 운전자본 효율 악화 — 실질 현금 수익성 점검 필요")

    if growth and cf and growth.severity == "positive" and cf.severity in ("negative", "warning"):
        refs.append("매출 성장 대비 현금창출 부족 — 성장의 지속가능성 의문")

    if dp and sector and "레버리지 주도" in dp.body and sector.severity == "positive":
        refs.append("레버리지 의존 수익구조가 밸류에이션 할인의 원인일 수 있음")

    if segment and growth and segment.severity == "warning" and growth.severity == "positive":
        refs.append("성장이 단일 부문에 집중 — 해당 부문 둔화 시 전체 실적 급락 리스크")

    if eff and cf and eff.severity == "warning" and cf.severity in ("negative", "warning"):
        refs.append("운전자본 비효율과 현금흐름 부진 동반 — 유동성 관리 강화 필요")

    if margin and growth and margin.severity == "negative" and growth.severity == "negative":
        refs.append("마진과 성장 동시 악화 — 구조적 수익성 하락 우려")

    # ── v4 3표 연결 교차 패턴 ──
    if bs and growth and bs.severity == "warning" and growth.severity in ("negative", "neutral"):
        refs.append("자산 증가에도 매출 정체 — 투자 효율성 점검 필요")

    if cf and debt and cf.severity in ("negative", "warning") and debt.body and "증가" in debt.body:
        refs.append("영업현금 부진 + 차입금 증가 — 적자 보전 차입 가능성")

    if isToCs and isToCs.severity == "warning" and growth and growth.severity == "positive":
        refs.append("이익 증가에도 현금흐름 악화 — 이익의 질 의문")

    if liq and liq.severity == "negative" and cf and cf.severity in ("negative", "warning"):
        refs.append("유동성 악화 + 현금흐름 부진 — 단기 자금 경색 리스크")

    if margin and isToBs and margin.severity == "positive" and isToBs.severity == "warning":
        refs.append("마진 개선에도 매출채권/재고 과잉 — 채널 스터핑 의심")

    # ── v5 신규 교차 패턴 (Phase 7) ──
    costStr = dimMap.get("costStructure")
    salesOrder = dimMap.get("salesOrder")
    quarterly = dimMap.get("quarterlyMomentum")
    employee = dimMap.get("humanCapital")
    rnd = dimMap.get("rndEfficiency")
    distress = dimMap.get("distressModels")
    beneish = dimMap.get("earningsManipulation")
    valueCreation = dimMap.get("valueCreation")
    indexTrend = dimMap.get("indexTrend")
    strategy = dimMap.get("businessStrategy")

    # segment + margin: 고마진 부문 비중 하락
    if (
        segment
        and margin
        and segment.body
        and "비중 하락" in segment.body
        and margin.severity in ("negative", "warning")
    ):
        refs.append("고마진 부문 비중 하락 → 전체 이익률 압박")

    # costStructure + margin: 원재료비 비중 상승 + 마진 축소
    if costStr and margin and costStr.body and "원재료" in costStr.body and margin.severity in ("negative", "warning"):
        refs.append("원재료비 비중 상승 + 마진 축소 → 원가 전가 실패")

    # salesOrder + growth: 수주잔고 증가 + 매출 정체
    if salesOrder and growth and salesOrder.severity == "positive" and growth.severity in ("negative", "neutral"):
        refs.append("수주잔고 증가 + 매출 정체 → 생산능력 병목 또는 인식 시차")

    # quarterly + cashflow: Q4 매출 집중 + OCF 우수
    if quarterly and cf and quarterly.body and "Q4" in quarterly.body and cf.severity == "positive":
        refs.append("Q4 매출 집중 + OCF 우수 → 건전한 계절성")

    # employee + growth: 직원 증가율 > 매출 증가율
    if employee and growth and employee.body and "생산성 하락" in employee.body:
        refs.append("직원 증가율 > 매출 증가율 → 생산성 하락 추세, 인력 효율화 필요")

    # rnd + margin: R&D 투자 확대 + 마진 유지
    if rnd and margin and rnd.body and "확대" in rnd.body and margin.severity in ("positive", "neutral"):
        refs.append("R&D 투자 확대 + 마진 유지 → 기술 투자 효율적")

    # distress + debt: 부실 모델 disagreement + 부채 비율 높음
    if distress and debt and "disagreement" in (distress.body or "") and debt.severity in ("negative", "warning"):
        refs.append("부실 모델 disagreement + 부채 비율 높음 → 불확실성 구간")

    # beneish + isToCs: Beneish 경고 + OCF/NI 괴리
    if beneish and isToCs and beneish.severity == "warning" and isToCs.severity == "warning":
        refs.append("Beneish 경고 + OCF/NI 괴리 → 이익 품질 심층 검토 필요")

    # costStructure + segment: 비용 구조 변화 + 부문 비중 변화
    if costStr and segment and costStr.body and segment.body:
        refs.append("비용 구조 변화 + 부문 비중 변화 → 포트폴리오 전환 진행 가능성")

    # valueCreation + growth: 가치 파괴 + 성장
    if valueCreation and growth and valueCreation.severity in ("warning", "negative") and growth.severity == "positive":
        refs.append("매출 성장에도 EVA 부진 → 자본비용 초과 투자, 성장의 질 의문")

    # indexTrend + isToBs: 매출채권 비정상 팽창 교차 확인
    if indexTrend and isToBs and indexTrend.severity == "warning" and isToBs.severity == "warning":
        refs.append("지수분석·3표 연결 모두 매출채권/재고 비정상 팽창 감지 → 매출 인식 공격성 심각")

    return refs[:10]


def _buildForwardImplications(paragraphs: list[NarrativeParagraph], inp: _Input) -> list[str]:
    """전망 시사점 — 가장 강한 신호에서 조건부 시사점 생성."""
    implications: list[str] = []

    positive = [p for p in paragraphs if p.severity == "positive"]
    negative = [p for p in paragraphs if p.severity in ("negative", "warning")]

    if positive:
        best = positive[0]
        if best.dimension == "growth":
            implications.append("현 성장 추세 유지 시 실적 개선 지속 전망")
        elif best.dimension == "dupont":
            implications.append("수익구조 건전성 기반 안정적 주주가치 창출 기대")
        elif best.dimension == "sectorRelative":
            implications.append("업종 대비 저평가 구간 — 촉매 발생 시 재평가 여지")
        elif best.dimension == "margin":
            implications.append("마진 개선 추세 지속 시 이익 레버리지 확대 기대")
        elif best.dimension in ("cashflow", "cashflowDeep"):
            implications.append("양호한 현금창출력 기반 주주환원 또는 재투자 여력 충분")
        elif best.dimension == "bsStructure":
            implications.append("자산 구성 효율성 유지 시 자본수익률 개선 기대")
        elif best.dimension == "liquidity":
            implications.append("풍부한 유동성 — 경기 둔화에도 안정적 운영 가능")
        elif best.dimension == "capitalChange":
            implications.append("자본 축적 추세 지속 시 재무 안전판 강화")
        elif best.dimension == "isToCs":
            implications.append("현금주의 이익 양호 — 높은 이익의 질 유지 전망")
        elif best.dimension == "valueCreation":
            implications.append("ROIC > WACC — 자본비용 초과 수익 창출, 기업가치 증대 지속 기대")
        elif best.dimension == "distressModels":
            implications.append("부실 모델 전원 안전 판정 — 재무건전성 우수")
        elif best.dimension == "salesOrder":
            implications.append("수주잔고 풍부 — 향후 매출 가시성 높음")
        elif best.dimension == "businessStrategy":
            implications.append("고성장·고마진 전략 유효 — 프리미엄 밸류에이션 정당화")

    if negative:
        worst = negative[0]
        if worst.dimension == "efficiency":
            implications.append("운전자본 효율 악화 방치 시 유동성 리스크 확대 가능")
        elif worst.dimension in ("cashflow", "cashflowDeep"):
            implications.append("현금흐름 부진 지속 시 재무 안정성 악화 우려")
        elif worst.dimension == "growth":
            implications.append("성장 둔화 추세 반전 없으면 밸류에이션 디레이팅 가능")
        elif worst.dimension == "margin":
            implications.append("마진 하락 추세 지속 시 구조적 수익성 문제 대두 가능")
        elif worst.dimension == "sectorRelative":
            implications.append("업종 대비 프리미엄 지속 시 하방 리스크 존재")
        elif worst.dimension == "debtStructure":
            implications.append("부채구조 악화 추세 지속 시 신용 리스크 상승 가능")
        elif worst.dimension == "liquidity":
            implications.append("유동성 부족 심화 시 차입 의존도 확대 불가피")
        elif worst.dimension == "isToCs":
            implications.append("이익-현금흐름 괴리 지속 시 이익의 질 의문 심화")
        elif worst.dimension == "isToBs":
            implications.append("매출채권/재고 과잉 축적 시 대손·평가손실 리스크")
        elif worst.dimension == "cfToBs":
            implications.append("투자-자산 불일치 지속 시 자산 효율성 저하 우려")
        elif worst.dimension == "valueCreation":
            implications.append("EVA 부진 지속 시 기업가치 훼손 — 자본 배분 재검토 필요")
        elif worst.dimension == "distressModels":
            implications.append("다수 부실 모델 경고 — 재무 안정성 심층 점검 시급")
        elif worst.dimension == "earningsManipulation":
            implications.append("Beneish 경고 지속 시 이익의 신뢰성 의문 — 감사보고서 주의")

    return implications[:4]


# ══════════════════════════════════════
# 진입점
# ══════════════════════════════════════


def buildNarrative(
    aSeries: dict,
    aYears: list[str],
    dupont: DuPontResult | None,
    earningsQuality: EarningsQuality | None,
    marketData: MarketData | None,
    company: object,
    sectorBenchmark: object | None = None,
    sectorParams: object | None = None,
    ratios: object | None = None,
) -> NarrativeAnalysis | None:
    """15차원 교차분석 서술 생성 (IS/BS/CF 3표 연결)."""
    # segments, costByNature 수집 (show → notes fallback)
    segDf = None
    costDf = None
    try:
        segDf = company.show("segments")  # type: ignore[union-attr]
    except (AttributeError, TypeError, KeyError, ValueError):
        pass
    if segDf is None:
        try:
            notes = getattr(company, "notes", None)
            if notes is not None:
                segDf = notes.segments
        except (AttributeError, TypeError, KeyError, ValueError):
            pass
    try:
        costDf = company.show("costByNature")  # type: ignore[union-attr]
    except (AttributeError, TypeError, KeyError, ValueError):
        pass
    if costDf is None:
        try:
            notes = getattr(company, "notes", None)
            if notes is not None:
                costDf = notes.costByNature
        except (AttributeError, TypeError, KeyError, ValueError):
            pass

    # Phase 4: 실전 사업분석 데이터 수집
    salesOrderDf = None
    productServiceDf = None
    quarterlyIsDf = None
    try:
        salesOrderDf = company.show("salesOrder")  # type: ignore[union-attr]
    except (AttributeError, TypeError, KeyError, ValueError):
        pass
    try:
        productServiceDf = company.show("productService")  # type: ignore[union-attr]
    except (AttributeError, TypeError, KeyError, ValueError):
        pass
    try:
        finance = getattr(company, "finance", None)
        if finance is not None:
            ts = getattr(finance, "timeseries", None)
            if ts is not None:
                quarterlyIsDf = getattr(ts, "IS", None)
    except (AttributeError, TypeError):
        pass

    # Phase 5: 인적자본 데이터 수집
    employeeDf = None
    rndDf = None
    try:
        employeeDf = company.show("employee")  # type: ignore[union-attr]
    except (AttributeError, TypeError, KeyError, ValueError):
        pass
    try:
        rndDf = company.show("rnd")  # type: ignore[union-attr]
    except (AttributeError, TypeError, KeyError, ValueError):
        pass

    # 금융업 판별
    isFinancial = False
    sectorEnum = None
    try:
        sectorInfo = getattr(company, "sector", None)
        if sectorInfo is not None:
            sectorEnum = getattr(sectorInfo, "sector", sectorInfo)
            if hasattr(sectorEnum, "value"):
                isFinancial = sectorEnum.value == "금융"
            elif isinstance(sectorEnum, str):
                isFinancial = "금융" in sectorEnum or "FINANCIAL" in sectorEnum.upper()
    except (AttributeError, TypeError):
        pass

    inp = _Input(
        aSeries=aSeries,
        aYears=aYears,
        dupont=dupont,
        earningsQuality=earningsQuality,
        marketData=marketData,
        segmentsDf=segDf,
        costByNatureDf=costDf,
        sectorBenchmark=sectorBenchmark,
        sectorParams=sectorParams,
        isFinancial=isFinancial,
        ratios=ratios,
        salesOrderDf=salesOrderDf,
        productServiceDf=productServiceDf,
        quarterlyIsDf=quarterlyIsDf,
        employeeDf=employeeDf,
        rndDf=rndDf,
    )

    # 26개 분석 차원 실행 (v5)
    analyzers = [
        _analyzeDupont,
        _analyzeGrowthQuality,
        _analyzeCashflowDeep,
        _analyzeIsToCs,
        _analyzeCfToBs,
        _analyzeIsToBs,
        _analyzeIndexTrend,
        _analyzeEarningsManipulation,
        _analyzeDistressModels,
        _analyzeCostStructure,
        _analyzeSalesOrder,
        _analyzeProductMix,
        _analyzeQuarterlyMomentum,
        _analyzeBusinessStrategy,
        _analyzeHumanCapital,
        _analyzeRndEfficiency,
        _analyzeValueCreation,
        _analyzeSectorRelative,
        _analyzeSegments,
    ]
    # 금융업은 margin/efficiency/liquidity skip (BS/CF 구조 다름)
    if not isFinancial:
        analyzers.insert(1, _analyzeMarginTrend)
        analyzers.insert(2, _analyzeBalanceSheetStructure)
        analyzers.insert(3, _analyzeDebtStructure)
        analyzers.insert(4, _analyzeLiquidity)
        analyzers.insert(5, _analyzeCapitalChange)
        analyzers.insert(8, _analyzeEfficiency)

    paragraphs: list[NarrativeParagraph] = []
    for fn in analyzers:
        try:
            result = fn(inp)
            if result is not None:
                paragraphs.append(result)
        except (TypeError, ValueError, KeyError, ZeroDivisionError, AttributeError):
            continue

    if len(paragraphs) < 2:
        return None

    crossRefs = _detectCrossReferences(paragraphs)
    implications = _buildForwardImplications(paragraphs, inp)

    return NarrativeAnalysis(
        paragraphs=paragraphs,
        forwardImplications=implications,
        crossReferences=crossRefs,
    )
