"""review 블록 빌더 — calc* 결과(dict) → Block 리스트 변환.

analysis.strategy 의 calc* 함수는 dict/숫자만 반환한다.
여기서 그 dict를 Block으로 조립한다.
"""

from __future__ import annotations

import polars as pl

from dartlab.review.blocks import (
    FlagBlock,
    HeadingBlock,
    MetricBlock,
    TableBlock,
    TextBlock,
)
from dartlab.review.utils import unifyTableScale

# ── 수익구조 (revenue) 빌더 ──


def profileBlock(data: dict) -> list:
    """calcCompanyProfile 결과 → TextBlock."""
    if not data:
        return []
    parts = []
    if "sector" in data:
        parts.append(data["sector"])
    if "products" in data:
        parts.append(data["products"])
    if not parts:
        return []
    return [TextBlock(" | ".join(parts), style="dim", indent="h2")]


def segmentCompositionBlock(data: dict) -> list:
    """calcSegmentComposition 결과 → HeadingBlock + TableBlock."""
    if not data:
        return []
    segments = data.get("segments", [])
    if not segments:
        return []

    totalRev = data["totalRevenue"]
    hasOp = data.get("hasOpIncome", False)

    rows = []
    for seg in segments:
        rev = seg["revenue"]
        pct = rev / totalRev * 100 if totalRev else 0
        row = {"부문": seg["name"], "매출": rev, "비중": f"{pct:.0f}%"}
        if hasOp and seg.get("opIncome") is not None:
            row["영업이익"] = seg["opIncome"]
            if rev > 0:
                row["이익률"] = f"{seg['opIncome'] / rev * 100:.1f}%"
            else:
                row["이익률"] = "-"
        rows.append(row)

    valueCols = ["매출"]
    if hasOp:
        valueCols.append("영업이익")

    unified = unifyTableScale(rows, "부문", valueCols, unit="millions")
    blocks: list = []
    blocks.append(
        HeadingBlock(
            "부문별 매출 구성",
            level=2,
            helper="매출 비중 + 이익률로 수익 구조 편중을 본다",
        )
    )
    blocks.append(TableBlock("", pl.DataFrame(unified)))

    # 다년간 비중 변화 테이블
    history = data.get("compositionHistory")
    if history and len(history) >= 2:
        # {year, shares: {seg: pct}} → 부문×연도 테이블
        allSegs = []
        for h in history:
            for s in h["shares"]:
                if s not in allSegs:
                    allSegs.append(s)
        histYears = [h["year"] for h in history]
        histRows = []
        for seg in allSegs:
            row: dict = {"부문": seg}
            for h in history:
                row[h["year"]] = f"{h['shares'].get(seg, 0):.1f}%"
            histRows.append(row)
        blocks.append(TableBlock("비중 변화", pl.DataFrame(histRows)))

    return blocks


def segmentTrendBlock(data: dict) -> list:
    """calcSegmentTrend 결과 → HeadingBlock + TableBlock."""
    if not data:
        return []
    yearCols = data.get("yearCols", [])
    trendRows = data.get("rows", [])
    if not yearCols or not trendRows:
        return []

    rows = []
    for tr in trendRows:
        row: dict = {"부문": tr["name"]}
        for yc in yearCols:
            row[yc] = tr["values"].get(yc)
        if tr.get("yoy") is not None:
            row["YoY"] = f"{tr['yoy']:+.0f}%"
        else:
            row["YoY"] = "-"
        rows.append(row)

    unified = unifyTableScale(rows, "부문", yearCols, unit="millions")
    blocks: list = []
    blocks.append(
        HeadingBlock(
            "부문별 매출 추이",
            level=2,
            helper="부문별 성장/정체를 연도 비교로 식별",
        )
    )
    blocks.append(TableBlock("", pl.DataFrame(unified)))
    return blocks


def breakdownBlock(data: dict, sub: str) -> list:
    """calcBreakdown 결과 → HeadingBlock + TableBlock."""
    if not data:
        return []
    items = data.get("items", [])
    if not items:
        return []

    titleMap = {"region": "지역별 매출", "product": "제품별 매출"}
    title = titleMap.get(sub, f"{sub}별 매출")

    rows = []
    for item in items:
        rows.append(
            {
                "구분": item["name"],
                "매출": item["value"],
                "비중": f"{item['pct']:.0f}%",
            }
        )

    unified = unifyTableScale(rows, "구분", ["매출"], unit="millions")
    blocks: list = []
    blocks.append(HeadingBlock(title, level=2))
    blocks.append(TableBlock("", pl.DataFrame(unified)))

    # 다년간 비중 변화
    history = data.get("breakdownHistory")
    if history and len(history) >= 2:
        allNames: list[str] = []
        for h in history:
            for n in h["shares"]:
                if n not in allNames:
                    allNames.append(n)
        histRows = []
        for name in allNames:
            row: dict = {"구분": name}
            for h in history:
                row[h["year"]] = f"{h['shares'].get(name, 0):.1f}%"
            histRows.append(row)
        blocks.append(TableBlock("비중 변화", pl.DataFrame(histRows)))

    return blocks


def revenueGrowthBlock(data: dict) -> list:
    """calcRevenueGrowth 결과 → MetricBlock + 분기 매출 TableBlock."""
    if not data:
        return []

    blocks: list = []
    metrics = []
    yoy = data.get("yoy")
    cagr = data.get("cagr3y")
    if yoy is not None:
        metrics.append(("매출 YoY", f"{yoy:+.1f}%"))
    if cagr is not None:
        metrics.append(("3Y CAGR", f"{cagr:+.1f}%"))

    # 분기 매출 테이블 (최근 8분기)
    quarterly = data.get("quarterlySelect")
    qTable = _quarterlyRevenueTable(quarterly)

    if not metrics and qTable is None:
        return []

    blocks.append(
        HeadingBlock(
            "매출 성장",
            level=2,
            helper="YoY vs 3Y CAGR 방향이 다르면 추세 전환 의심",
        )
    )
    if metrics:
        blocks.append(MetricBlock(metrics))
    if qTable is not None:
        blocks.append(qTable)

    return blocks


_MAX_QUARTERS = 5


def _quarterlyRevenueTable(selectResult) -> TableBlock | None:
    """SelectResult → 최근 N분기 매출 TableBlock."""
    if selectResult is None:
        return None

    df = selectResult.df
    if df is None or df.is_empty():
        return None

    # 기간 컬럼만 추출 (Q 포함)
    periodCols = [c for c in df.columns if "Q" in c]
    periodCols = sorted(periodCols, reverse=True)[:_MAX_QUARTERS]
    if not periodCols:
        return None

    labelCol = "계정명" if "계정명" in df.columns else df.columns[0]
    keepCols = [labelCol] + periodCols

    rows = []
    for row in df.select(keepCols).iter_rows(named=True):
        label = row[labelCol]
        rowDict = {"": label}
        for pc in periodCols:
            rowDict[pc] = row.get(pc)
        rows.append(rowDict)

    if not rows:
        return None

    unified = unifyTableScale(rows, "", periodCols, unit="won")
    return TableBlock("분기별 매출", pl.DataFrame(unified))


def concentrationBlock(data: dict) -> list:
    """calcConcentration 결과 → MetricBlock."""
    if not data:
        return []

    metrics = []
    metrics.append(("HHI", f"{data['hhi']:,.0f} ({data['hhiLabel']})"))
    metrics.append(("1위 부문 비중", f"{data['topPct']:.0f}%"))
    if data.get("domesticPct") is not None:
        metrics.append(("내수 비중", f"{data['domesticPct']:.0f}%"))

    blocks: list = []
    blocks.append(
        HeadingBlock(
            "매출 집중도",
            level=2,
            helper="HHI > 5000 고집중, > 2500 중간 집중",
        )
    )
    blocks.append(MetricBlock(metrics))

    # HHI 시계열
    hhiHistory = data.get("hhiHistory")
    hhiDir = data.get("hhiDirection")
    if hhiHistory and len(hhiHistory) >= 2:
        hhiRows = [{"연도": h["year"], "HHI": f"{h['hhi']:,.0f}"} for h in hhiHistory]
        blocks.append(TableBlock("HHI 추이", pl.DataFrame(hhiRows)))
        if hhiDir:
            blocks.append(TextBlock(f"방향: {hhiDir}", style="dim", indent="h2"))

    return blocks


def revenueQualityBlock(data: dict) -> list:
    """calcRevenueQuality 결과 → MetricBlock."""
    if not data:
        return []

    metrics = []
    cc = data.get("cashConversion")
    if cc is not None:
        metrics.append(("영업CF/순이익", f"{cc:.0f}% ({data['cashConversionLabel']})"))
    gm = data.get("grossMargin")
    if gm is not None:
        metrics.append(("매출총이익률", f"{gm:.1f}%"))

    gmTrend = data.get("grossMarginTrend", [])
    gmDir = data.get("grossMarginDirection", "안정")
    if gmTrend:
        trendStr = " → ".join(f"{v:.1f}%" for v in gmTrend)
        metrics.append(("총이익률 추세", f"{trendStr} ({gmDir})"))

    if not metrics:
        return []

    blocks: list = []
    blocks.append(
        HeadingBlock(
            "수익 품질",
            level=2,
            helper="영업CF/순이익 80%+ 양호, 총이익률 하락 추세 주의",
        )
    )
    blocks.append(MetricBlock(metrics))
    return blocks


def growthContributionBlock(data: dict) -> list:
    """calcGrowthContribution 결과 → MetricBlock + TextBlock."""
    if not data:
        return []

    totalPct = data.get("totalGrowthPct")
    contributions = data.get("contributions", [])
    driver = data.get("driver", "")

    if not contributions:
        return []

    period = data.get("period", "")

    blocks: list = []
    periodSuffix = f" ({period})" if period else ""
    blocks.append(
        HeadingBlock(
            f"성장 기여 분해{periodSuffix}",
            level=2,
            helper="어느 부문이 전체 성장을 이끌었는가",
        )
    )

    metrics = []
    if totalPct is not None:
        metrics.append(("전체 매출 변화", f"{totalPct:+.1f}%"))
    for c in contributions[:5]:
        sign = "+" if c["amount"] > 0 else ""
        metrics.append((c["name"], f"기여 {sign}{c['pct']:.0f}%"))
    blocks.append(MetricBlock(metrics))

    if driver:
        blocks.append(TextBlock(driver, style="dim", indent="h2"))

    return blocks


def revenueFlagsBlock(flags: list[tuple[str, str]]) -> list:
    """calcFlags 결과 → FlagBlock."""
    if not flags:
        return []
    warnings = [f for f, k in flags if k == "warning"]
    opportunities = [f for f, k in flags if k == "opportunity"]
    blocks: list = []
    if warnings:
        blocks.append(FlagBlock(warnings, kind="warning"))
    if opportunities:
        blocks.append(FlagBlock(opportunities, kind="opportunity"))
    return blocks


# ── 자금구조 (capital) 빌더 ──


def fundingSourcesBlock(data: dict) -> list:
    """calcFundingSources 결과 → 조달원 비중 테이블 + 시계열."""
    if not data:
        return []

    latest = data.get("latest")
    if not latest:
        return []

    blocks: list = []
    blocks.append(
        HeadingBlock(
            "자금 조달원",
            level=2,
            helper="내부유보 = 사업으로 번 돈, 금융차입 = 이자 붙는 빚, 영업조달 = 자연 발생 자금",
        )
    )

    # 최신 비중 메트릭
    fmtAmt = _fmtAmtShort(latest["totalAssets"])
    metrics = [("총자산", fmtAmt)]
    metrics.append(("내부유보 (이익잉여금)", f"{_fmtAmtShort(latest['retained'])} ({latest['retainedPct']:.0f}%)"))
    metrics.append(("외부-주주 (자본금+잉여금)", f"{_fmtAmtShort(latest['paidIn'])} ({latest['paidInPct']:.0f}%)"))
    metrics.append(("외부-금융차입", f"{_fmtAmtShort(latest['finDebt'])} ({latest['finDebtPct']:.0f}%)"))
    if latest["opFundingPct"] > 0.5:
        metrics.append(
            ("영업조달 (매입채무·선수금 등)", f"{_fmtAmtShort(latest['opFunding'])} ({latest['opFundingPct']:.0f}%)")
        )
    blocks.append(MetricBlock(metrics))

    # 시계열 테이블 (행=항목, 열=기간)
    history = data.get("history", [])
    if len(history) >= 2:
        cols = {"": ["내부유보", "주주자본", "금융차입", "영업조달"]}
        for h in history:
            cols[h["period"]] = [
                f"{h['retainedPct']:.0f}%",
                f"{h['paidInPct']:.0f}%",
                f"{h['finDebtPct']:.0f}%",
                f"{h['opFundingPct']:.0f}%",
            ]
        blocks.append(TableBlock("조달원 비중 추이", pl.DataFrame(cols)))

    # 보충 지표 (순차입금/EBITDA, 암묵적 차입금리)
    suppMetrics = []
    ndEbitda = data.get("netDebtEbitda")
    if ndEbitda is not None:
        if ndEbitda == 0:
            suppMetrics.append(("순차입금/EBITDA", "순현금 (차입 없음)"))
        else:
            suppMetrics.append(("순차입금/EBITDA", f"{ndEbitda:.1f}배"))
    impliedRate = data.get("impliedBorrowingRate")
    if impliedRate is not None:
        suppMetrics.append(("암묵적 차입금리", f"{impliedRate:.1f}%"))
    if suppMetrics:
        blocks.append(MetricBlock(suppMetrics))

    # 진단 + 비중 변화 방향
    diagnosis = data.get("diagnosis", "")
    leverageTrend = data.get("leverageTrend")
    diagParts = [p for p in [diagnosis, leverageTrend] if p]
    if diagParts:
        blocks.append(TextBlock(" | ".join(diagParts), style="dim", indent="h2"))

    return blocks


def _fmtAmtShort(value) -> str:
    """금액 간략 포맷."""
    if value is None or value == 0:
        return "-"
    absVal = abs(value)
    sign = "-" if value < 0 else ""
    if absVal >= 1_0000_0000_0000:
        return f"{sign}{absVal / 1_0000_0000_0000:.1f}조"
    if absVal >= 1_0000_0000:
        return f"{sign}{absVal / 1_0000_0000:.0f}억"
    return f"{sign}{absVal:,.0f}"


def capitalOverviewBlock(data: dict) -> list:
    """calcCapitalOverview 결과 → MetricBlock."""
    if not data:
        return []
    metrics = data.get("metrics", [])
    if not metrics:
        return []
    blocks: list = []
    blocks.append(
        HeadingBlock(
            "자본 개요",
            level=2,
            helper="부채비율 100% 이하 안정, 순현금이면 재무 여유",
        )
    )
    blocks.append(MetricBlock(metrics))
    return blocks


def capitalTimelineBlock(data: dict) -> list:
    """calcCapitalTimeline 결과 → TableBlock."""
    if not data:
        return []
    blocks: list = []
    blocks.append(
        HeadingBlock(
            "자본구조",
            level=2,
            helper="이익잉여금 = 사업으로 번 돈, 자본금+잉여금 = 외부 조달",
        )
    )
    for label, tableRows, cols in data.get("tables", []):
        if tableRows and cols:
            unified = unifyTableScale(tableRows, "", cols, unit="won")
            blocks.append(TableBlock(label, pl.DataFrame(unified)))
    if len(blocks) <= 1:
        return []
    return blocks


def debtTimelineBlock(data: dict) -> list:
    """calcDebtTimeline 결과 → TableBlock."""
    if not data:
        return []
    blocks: list = []
    blocks.append(
        HeadingBlock(
            "부채구조",
            level=2,
            helper="영업부채 = 자연 발생, 금융부채 = 이자 붙는 차입",
        )
    )
    for label, tableRows, cols in data.get("tables", []):
        if tableRows and cols:
            unified = unifyTableScale(tableRows, "", cols, unit="won")
            blocks.append(TableBlock(label, pl.DataFrame(unified)))
    if len(blocks) <= 1:
        return []
    return blocks


def interestBurdenBlock(data: dict) -> list:
    """calcInterestBurden 결과 → MetricBlock."""
    if not data:
        return []
    metrics = data.get("metrics", [])
    if not metrics:
        return []
    blocks: list = []
    blocks.append(
        HeadingBlock(
            "이자 부담",
            level=2,
            helper="이자보상배율 3배 이상 안정, 1.5배 이하 주의",
        )
    )
    blocks.append(MetricBlock(metrics))
    return blocks


def liquidityBlock(data: dict) -> list:
    """calcLiquidity 결과 → MetricBlock."""
    if not data:
        return []
    metrics = data.get("metrics", [])
    if not metrics:
        return []
    blocks: list = []
    blocks.append(
        HeadingBlock(
            "유동성",
            level=2,
            helper="유동비율 100% 이하 → 단기 지급 리스크",
        )
    )
    blocks.append(MetricBlock(metrics))
    return blocks


def cashFlowBlock(data: dict) -> list:
    """calcCashFlowStructure 결과 → TableBlock + TextBlock + MetricBlock."""
    if not data:
        return []
    blocks: list = []
    blocks.append(
        HeadingBlock(
            "현금 흐름 구조",
            level=2,
            helper="영업CF(+)/투자CF(-)/재무CF(-) → 건전한 패턴",
        )
    )
    tableRows = data.get("tableRows")
    cols = data.get("cols")
    if tableRows and cols:
        unified = unifyTableScale(tableRows, "", cols, unit="won")
        blocks.append(TableBlock("", pl.DataFrame(unified)))
    pattern = data.get("pattern")
    if pattern:
        blocks.append(TextBlock(f"CF 패턴: {pattern}", style="dim", indent="h2"))
    metrics = data.get("metrics")
    if metrics:
        blocks.append(MetricBlock(metrics))
    if len(blocks) <= 1:
        return []
    return blocks


def distressBlock(data: dict) -> list:
    """calcDistressIndicators 결과 → MetricBlock."""
    if not data:
        return []
    metrics = data.get("metrics", [])
    if not metrics:
        return []
    blocks: list = []
    blocks.append(
        HeadingBlock(
            "부실 예측 지표",
            level=2,
            helper="Altman Z > 2.99 안전, Piotroski F ≥ 7 건전",
        )
    )
    blocks.append(MetricBlock(metrics))
    return blocks


def capitalFlagsBlock(flags: list[tuple[str, str]]) -> list:
    """calcCapitalFlags 결과 → FlagBlock."""
    if not flags:
        return []
    warnings = [f for f, k in flags if k == "warning"]
    opportunities = [f for f, k in flags if k == "opportunity"]
    blocks: list = []
    if warnings:
        blocks.append(FlagBlock(warnings, kind="warning"))
    if opportunities:
        blocks.append(FlagBlock(opportunities, kind="opportunity"))
    return blocks


# ── 자산구조 (asset) 빌더 ──


def assetStructureBlock(data: dict) -> list:
    """calcAssetStructure 결과 → 영업/비영업 비중 + 구성 + 시계열."""
    if not data:
        return []

    latest = data.get("latest")
    if not latest:
        return []

    blocks: list = []
    blocks.append(
        HeadingBlock(
            "자산 재분류 — 영업 vs 비영업",
            level=2,
            helper="영업자산 = 사업에 투입된 자산, 비영업 = 현금/투자/금융자산",
        )
    )

    # 최신 비중
    metrics = [
        ("총자산", _fmtAmtShort(latest["totalAssets"])),
        ("영업자산", f"{_fmtAmtShort(latest['opAssets'])} ({latest['opAssetsPct']:.0f}%)"),
        ("비영업자산", f"{_fmtAmtShort(latest['nonOpAssets'])} ({latest['nonOpAssetsPct']:.0f}%)"),
        ("순영업자산(NOA)", _fmtAmtShort(latest["noa"])),
        ("순운전자본", _fmtAmtShort(latest["workingCapital"])),
        ("고정영업자산", _fmtAmtShort(latest["fixedOpAssets"])),
    ]
    blocks.append(MetricBlock(metrics))

    # 영업자산 구성 상세
    comp = data.get("composition")
    if comp:
        compMetrics = []
        for label, key in [
            ("매출채권", "receivables"),
            ("재고자산", "inventory"),
            ("유형자산", "ppe"),
            ("무형자산+영업권", None),
            ("사용권자산", "rou"),
            ("건설중인자산", "cip"),
            ("현금성자산", "cash"),
            ("투자자산", "investments"),
        ]:
            if key is None:
                val = comp.get("intangibles", 0) + comp.get("goodwill", 0)
            else:
                val = comp.get(key, 0)
            if val > 0:
                compMetrics.append((label, _fmtAmtShort(val)))
        if compMetrics:
            blocks.append(MetricBlock(compMetrics))

    # 시계열 테이블 (행=항목, 열=기간)
    history = data.get("history", [])
    if len(history) >= 2:
        cols = {"": ["영업자산", "비영업자산", "NOA"]}
        for h in history:
            cols[h["period"]] = [
                f"{h['opAssetsPct']:.0f}%",
                f"{h['nonOpAssetsPct']:.0f}%",
                _fmtAmtShort(h["noa"]),
            ]
        blocks.append(TableBlock("자산 구성 추이", pl.DataFrame(cols)))

    # 진단
    diagnosis = data.get("diagnosis")
    if diagnosis:
        blocks.append(TextBlock(diagnosis, style="dim", indent="h2"))

    return blocks


def workingCapitalBlock(data: dict) -> list:
    """calcWorkingCapital 결과 → 운전자본 + CCC."""
    if not data:
        return []

    latest = data.get("latest")
    if not latest:
        return []

    blocks: list = []
    blocks.append(
        HeadingBlock(
            "운전자본 순환 (CCC)",
            level=2,
            helper="CCC = 재고회전일 + 매출채권회전일 - 매입채무회전일",
        )
    )

    metrics = [
        ("순운전자본", _fmtAmtShort(latest["wc"])),
    ]
    for label, key, suffix in [
        ("매출채권 회전일", "receivableDays", "일"),
        ("재고 회전일", "inventoryDays", "일"),
        ("매입채무 회전일", "payableDays", "일"),
        ("CCC", "ccc", "일"),
    ]:
        val = latest.get(key)
        if val is not None:
            metrics.append((label, f"{val:.0f}{suffix}"))
    blocks.append(MetricBlock(metrics))

    # CCC 시계열 (행=항목, 열=기간)
    history = data.get("history", [])
    if len(history) >= 2:
        hasData = any(h.get("ccc") is not None for h in history)
        if hasData:
            cols = {"": ["매출채권일", "재고일", "매입채무일", "CCC"]}
            for h in history:
                cols[h["period"]] = [
                    f"{h['receivableDays']:.0f}" if h.get("receivableDays") is not None else "-",
                    f"{h['inventoryDays']:.0f}" if h.get("inventoryDays") is not None else "-",
                    f"{h['payableDays']:.0f}" if h.get("payableDays") is not None else "-",
                    f"{h['ccc']:.0f}" if h.get("ccc") is not None else "-",
                ]
            blocks.append(TableBlock("CCC 추이", pl.DataFrame(cols)))

    return blocks


def capexBlock(data: dict) -> list:
    """calcCapexPattern 결과 → CAPEX/감가상각 + 건설중인자산."""
    if not data:
        return []

    latest = data.get("latest")
    if not latest:
        return []

    blocks: list = []
    blocks.append(
        HeadingBlock(
            "CAPEX 패턴",
            level=2,
            helper="CAPEX/감가상각 > 1 → 성장 투자, < 1 → 유지/수확",
        )
    )

    metrics = [
        ("CAPEX", _fmtAmtShort(latest["capex"])),
        ("감가상각", _fmtAmtShort(latest["depreciation"])),
    ]
    ratio = latest.get("capexToDepRatio")
    if ratio is not None:
        metrics.append(("CAPEX/감가상각", f"{ratio:.1f}배"))
    cip = latest.get("cip", 0)
    if cip > 0:
        metrics.append(("건설중인자산", f"{_fmtAmtShort(cip)} ({latest['cipPct']:.0f}%)"))
    blocks.append(MetricBlock(metrics))

    investType = latest.get("investmentType")
    if investType:
        blocks.append(TextBlock(investType, style="dim", indent="h2"))

    # 시계열 (행=항목, 열=기간)
    history = data.get("history", [])
    if len(history) >= 2:
        cols = {"": ["CAPEX", "감가상각", "CAPEX/감가상각", "건설중인자산"]}
        for h in history:
            r = h.get("capexToDepRatio")
            cols[h["period"]] = [
                _fmtAmtShort(h["capex"]),
                _fmtAmtShort(h["depreciation"]),
                f"{r:.1f}배" if r is not None else "-",
                _fmtAmtShort(h["cip"]),
            ]
        blocks.append(TableBlock("CAPEX 추이", pl.DataFrame(cols)))

    return blocks


def assetEfficiencyBlock(data: dict) -> list:
    """calcAssetEfficiency 결과 → 회전율 시계열."""
    if not data:
        return []

    history = data.get("history", [])
    if len(history) < 2:
        return []

    blocks: list = []
    blocks.append(
        HeadingBlock(
            "자산 효율",
            level=2,
            helper="회전율이 높을수록 같은 자산으로 매출을 더 뽑는다",
        )
    )

    cols = {"": ["총자산회전율", "유형자산회전율"]}
    for h in history:
        ta = h.get("totalAssetTurnover")
        ppe = h.get("ppeTurnover")
        cols[h["period"]] = [
            f"{ta:.2f}회" if ta is not None else "-",
            f"{ppe:.2f}회" if ppe is not None else "-",
        ]
    blocks.append(TableBlock("회전율 추이", pl.DataFrame(cols)))

    return blocks


def assetFlagsBlock(flags: list[str]) -> list:
    """calcAssetFlags 결과 → FlagBlock."""
    if not flags:
        return []
    return [FlagBlock(flags, kind="warning")]
