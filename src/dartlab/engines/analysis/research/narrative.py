"""교차분석 서술 엔진 — 15개 차원에서 IS/BS/CF 3표를 교차분석하여 해석적 서술문으로 변환."""

from __future__ import annotations

from dataclasses import dataclass

from dartlab.engines.analysis.research.types import (
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
    """DuPont 3-factor 교차분해."""
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
    # ROE 분해 (DuPont values are ratios: 0.13 = 13%)
    roePct = roeLast * 100
    marginPct = marginLast * 100
    roeStr = f"ROE {roePct:.1f}%"
    decomp = []
    if marginLast is not None:
        decomp.append(f"순이익률 {marginPct:.1f}%")
    if turnoverLast is not None:
        decomp.append(f"자산회전율 {turnoverLast:.2f}배")
    if leverageLast is not None:
        decomp.append(f"레버리지 {leverageLast:.1f}배")
    parts.append(f"{roeStr}는 {' × '.join(decomp)}로 구성")

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
    return NarrativeParagraph(dimension="dupont", title="수익구조 분해 (DuPont)", body=body, severity=severity)


def _analyzeMarginTrend(inp: _Input) -> NarrativeParagraph | None:
    """마진 추세 분해 — 원가율/판관비 기여도 분석."""
    sales = _getVals(inp.aSeries, "IS", "sales")
    cogs = _getVals(inp.aSeries, "IS", "cost_of_sales")
    op = _getVals(inp.aSeries, "IS", "operating_profit")
    ni = _getVals(inp.aSeries, "IS", "net_profit")
    if not sales or len(sales) < 2:
        return None

    # 마진 계산
    omList = [_safeDiv(o, s) for o, s in zip(op, sales)] if op else []
    gmList = (
        [
            _safeDiv(
                _safeDiv(
                    s - c if s and c else None,
                    1,
                )
                if False
                else (s - c if s is not None and c is not None else None),
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
    ni = _getVals(inp.aSeries, "IS", "net_profit")
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
            parts.append(f"매출채권회전일 {cleanDso[-2]:.0f}일→{cleanDso[-1]:.0f}일 {label}")

    # CCC 추세
    cleanCcc = [v for v in cccList if v is not None]
    if len(cleanCcc) >= 2:
        cccDiff = cleanCcc[-1] - cleanCcc[-2]
        if abs(cccDiff) > 5:
            label = "연장" if cccDiff > 0 else "단축"
            parts.append(f"CCC {cleanCcc[-2]:.0f}일→{cleanCcc[-1]:.0f}일({cccDiff:+.0f}일 {label})")

    # 매출 증가 + CCC 악화 교차
    salesClean = [v for v in sales if v is not None]
    if len(salesClean) >= 2 and salesClean[-1] > salesClean[-2] and cleanCcc and len(cleanCcc) >= 2:
        if cleanCcc[-1] > cleanCcc[-2]:
            parts.append("매출 증가에도 운전자본 부담 확대")

    if not parts:
        return None
    body = ". ".join(parts) + "."
    severity = "warning" if any("악화" in p or "확대" in p for p in parts) else "neutral"
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
    if interest and op:
        pairs = [(o, i) for o, i in zip(op, interest) if o is not None and i is not None and i != 0]
        if pairs:
            latestOp, latestInt = pairs[-1]
            icr = latestOp / abs(latestInt)
            parts.append(f"이자보상배율 {icr:.1f}배")
            if icr < 1.5:
                parts.append("이자보상배율 위험 수준 — 이자비용 충당 불안")

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
    ni = _getVals(inp.aSeries, "IS", "net_profit")

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

    # 투자CF vs 재무CF 패턴
    if icf and fcf_cf:
        latestIcf = _lastN(icf, 1)
        latestFcf = _lastN(fcf_cf, 1)
        if latestIcf and latestFcf:
            if latestIcf[-1] is not None and latestIcf[-1] < 0 and latestFcf[-1] is not None and latestFcf[-1] > 0:
                parts.append("투자확대 + 외부조달 패턴 — 성장투자기")
            elif latestIcf[-1] is not None and latestIcf[-1] < 0 and latestFcf[-1] is not None and latestFcf[-1] < 0:
                parts.append("투자확대 + 부채상환/주주환원 — 현금흐름 여유")

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
        for s, l in zip(shortBorrow, longBorrow):
            if s is not None and l is not None:
                totalBorrowList.append(s + l)
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

    return refs[:7]


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

    return implications[:3]


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
) -> NarrativeAnalysis | None:
    """15차원 교차분석 서술 생성 (IS/BS/CF 3표 연결)."""
    # segments, costByNature 수집
    segDf = None
    costDf = None
    try:
        segDf = company.show("segments")  # type: ignore[union-attr]
    except (AttributeError, TypeError, KeyError, ValueError):
        pass
    try:
        costDf = company.show("costByNature")  # type: ignore[union-attr]
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
    )

    # 15개 분석 차원 실행 (v4)
    analyzers = [
        _analyzeDupont,
        _analyzeGrowthQuality,
        _analyzeCashflowDeep,
        _analyzeIsToCs,
        _analyzeCfToBs,
        _analyzeIsToBs,
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
