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
from dartlab.review.catalog import getBlockMeta as _meta
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
            _meta("segmentComposition").label,
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
            _meta("segmentTrend").label,
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

    meta = _meta(sub)
    title = meta.label if meta else f"{sub}별 매출"

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
            _meta("growth").label,
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
            _meta("concentration").label,
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
            _meta("revenueQuality").label,
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
            f"{_meta('growthContribution').label}{periodSuffix}",
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
            _meta("fundingSources").label,
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
            _meta("capitalOverview").label,
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
            _meta("capitalTimeline").label,
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
            _meta("debtTimeline").label,
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
            _meta("interestBurden").label,
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
            _meta("liquidity").label,
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
            _meta("cashFlowStructure").label,
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
            _meta("distressIndicators").label,
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
    """calcAssetStructure 결과 → 영업/비영업 재분류 시계열."""
    if not data:
        return []

    history = data.get("history", [])
    if not history:
        return []

    blocks: list = []
    blocks.append(
        HeadingBlock(
            _meta("assetStructure").label,
            level=2,
            helper="영업자산 = 사업에 투입된 자산, 비영업 = 현금/투자/금융자산",
        )
    )

    # 비중 시계열 테이블
    rows = ["총자산", "영업자산", "비영업자산", "순영업자산(NOA)", "순운전자본", "고정영업자산"]
    cols = {"": rows}
    for h in history:
        ta = h.get("totalAssets", 0)
        cols[h["period"]] = [
            _fmtAmtShort(ta),
            f"{_fmtAmtShort(h['opAssets'])} ({h['opAssetsPct']:.0f}%)",
            f"{_fmtAmtShort(h['nonOpAssets'])} ({h['nonOpAssetsPct']:.0f}%)",
            _fmtAmtShort(h["noa"]),
            _fmtAmtShort(h["wc"]),
            _fmtAmtShort(h["fixedOp"]),
        ]
    blocks.append(TableBlock("자산 재분류 추이", pl.DataFrame(cols)))

    # 세부 구성 시계열 (영업+비영업 주요 항목)
    detailRows = ["매출채권", "재고자산", "유형자산", "무형자산+영업권", "건설중인자산", "현금성자산", "투자자산"]
    detailCols = {"": detailRows}
    for h in history:
        intGw = h.get("intangibles", 0) + h.get("goodwill", 0)
        detailCols[h["period"]] = [
            _fmtAmtShort(h.get("receivables", 0)),
            _fmtAmtShort(h.get("inventory", 0)),
            _fmtAmtShort(h.get("ppe", 0)),
            _fmtAmtShort(intGw),
            _fmtAmtShort(h.get("cip", 0)),
            _fmtAmtShort(h.get("cash", 0)),
            _fmtAmtShort(h.get("investments", 0)),
        ]
    blocks.append(TableBlock("자산 구성 상세 추이", pl.DataFrame(detailCols)))

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
            _meta("workingCapital").label,
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
            _meta("capexPattern").label,
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
            _meta("assetEfficiency").label,
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


# ── 1-4 현금흐름 빌더 ──


def cashFlowOverviewBlock(data: dict) -> list:
    """calcCashFlowOverview 결과 → CF 3구간 + FCF 시계열 테이블."""
    if not data:
        return []
    history = data.get("history", [])
    if not history:
        return []

    blocks: list = []
    blocks.append(
        HeadingBlock(
            _meta("cashFlowOverview").label,
            level=2,
            helper="영업CF(+)/투자CF(-)/재무CF(-) = 건전한 패턴",
        )
    )

    rows = ["영업CF", "투자CF", "재무CF", "CAPEX", "FCF"]
    cols = {"": rows}
    for h in history:
        cols[h["period"]] = [
            _fmtAmtShort(h["ocf"]),
            _fmtAmtShort(h["icf"]),
            _fmtAmtShort(h["fcfFinancing"]),
            _fmtAmtShort(h["capex"]),
            _fmtAmtShort(h["fcf"]),
        ]
    blocks.append(TableBlock("현금흐름 추이", pl.DataFrame(cols)))

    # CF 패턴 시계열
    patternRows = ["CF 패턴"]
    patternCols = {"": patternRows}
    for h in history:
        pat = h.get("pattern")
        label = pat.split(" — ")[0] if pat else "-"
        patternCols[h["period"]] = [label]
    blocks.append(TableBlock("CF 패턴 추이", pl.DataFrame(patternCols)))

    return blocks


def cashQualityBlock(data: dict) -> list:
    """calcCashQuality 결과 → 영업CF/순이익, 영업CF 마진 시계열."""
    if not data:
        return []
    history = data.get("history", [])
    if not history:
        return []

    blocks: list = []
    blocks.append(
        HeadingBlock(
            _meta("cashQuality").label,
            level=2,
            helper="영업CF/순이익 > 100%이면 이익이 현금으로 회수됨",
        )
    )

    rows = ["영업CF", "당기순이익", "영업CF/순이익", "영업CF 마진"]
    cols = {"": rows}
    for h in history:
        ratio = h.get("ocfToNi")
        margin = h.get("ocfMargin")
        cols[h["period"]] = [
            _fmtAmtShort(h["ocf"]),
            _fmtAmtShort(h["netIncome"]),
            f"{ratio:.0f}%" if ratio is not None else "-",
            f"{margin:.1f}%" if margin is not None else "-",
        ]
    blocks.append(TableBlock("현금 품질 추이", pl.DataFrame(cols)))

    return blocks


def cashFlowFlagsBlock(flags: list[str]) -> list:
    """calcCashFlowFlags 결과 → FlagBlock."""
    if not flags:
        return []
    return [FlagBlock(flags, kind="warning")]


# ── 2부: 재무비율 분석 빌더 ──


def _timelineTable(
    specs: list[tuple[list[dict], str]],
    rowLabels: list[str],
) -> dict[str, list[str]] | None:
    """[{period, value}, ...] 시계열 → 행=지표, 열=기간 dict.

    specs: [(series, fmt), ...] -- series는 buildTimeline 결과, fmt는 f-string 포맷.
    rowLabels: 각 행 라벨 (specs와 동일 순서).
    반환: polars DataFrame으로 변환 가능한 dict. 기간 데이터 없으면 None.
    """
    cols: dict[str, list[str]] = {"": rowLabels}
    for idx, (series, fmt) in enumerate(specs):
        for item in series:
            period = item["period"]
            if period not in cols:
                cols[period] = ["-"] * len(rowLabels)
            v = item["value"]
            cols[period][idx] = fmt.format(v) if v is not None else "-"
    if len(cols) <= 1:
        return None
    return cols


def _flagsBlock(flags: list[str]) -> list:
    """플래그 리스트 → FlagBlock. 공통 래퍼."""
    if not flags:
        return []
    return [FlagBlock(flags, kind="warning")]


# ── 2-1 수익성 ──


def marginTrendBlock(data: dict) -> list:
    """calcMarginTrend 결과 → 마진 시계열 테이블."""
    if not data:
        return []

    cols = _timelineTable(
        [
            (data.get("grossMargin", []), "{:.1f}%"),
            (data.get("operatingMargin", []), "{:.1f}%"),
            (data.get("netMargin", []), "{:.1f}%"),
        ],
        ["매출총이익률", "영업이익률", "순이익률"],
    )
    if cols is None:
        return []

    return [
        HeadingBlock(
            _meta("marginTrend").label,
            level=2,
            helper="매출총이익률 안정 + 영업이익률 상승 = 원가 통제 + 판관비 효율",
        ),
        TableBlock("마진 추이", pl.DataFrame(cols)),
    ]


def returnTrendBlock(data: dict) -> list:
    """calcReturnTrend 결과 → ROE/ROA 시계열."""
    if not data:
        return []

    cols = _timelineTable(
        [
            (data.get("roe", []), "{:.1f}%"),
            (data.get("roa", []), "{:.1f}%"),
            (data.get("leverage", []), "{:.2f}배"),
        ],
        ["ROE", "ROA", "레버리지(ROE/ROA)"],
    )
    if cols is None:
        return []

    return [
        HeadingBlock(
            _meta("returnTrend").label,
            level=2,
            helper="ROE/ROA > 2 → 레버리지로 수익률 확대",
        ),
        TableBlock("수익률 추이", pl.DataFrame(cols)),
    ]


def dupontBlock(data: dict) -> list:
    """calcDupont 결과 → 듀퐁 분해 시계열."""
    if not data:
        return []

    cols = _timelineTable(
        [
            (data.get("margin", []), "{:.1f}%"),
            (data.get("turnover", []), "{:.2f}"),
            (data.get("leverage", []), "{:.2f}"),
        ],
        ["순이익률(%)", "자산회전율(회)", "재무레버리지(배)"],
    )
    if cols is None:
        return []

    return [
        HeadingBlock(
            _meta("dupont").label,
            level=2,
            helper="ROE = 순이익률 x 자산회전율 x 재무레버리지",
        ),
        TableBlock("듀퐁 분해", pl.DataFrame(cols)),
    ]


def profitabilityFlagsBlock(flags: list[str]) -> list:
    """calcProfitabilityFlags 결과 → FlagBlock."""
    return _flagsBlock(flags)


# ── 2-2 성장성 ──


def growthTrendBlock(data: dict) -> list:
    """calcGrowthTrend 결과 → 성장률 시계열."""
    if not data:
        return []

    cols = _timelineTable(
        [
            (data.get("revenueGrowth", []), "{:+.1f}%"),
            (data.get("operatingProfitGrowth", []), "{:+.1f}%"),
            (data.get("netProfitGrowth", []), "{:+.1f}%"),
            (data.get("assetGrowth", []), "{:+.1f}%"),
        ],
        ["매출 성장률", "영업이익 성장률", "순이익 성장률", "자산 성장률"],
    )
    if cols is None:
        return []

    return [
        HeadingBlock(
            _meta("growthTrend").label,
            level=2,
            helper="매출 성장 > 이익 성장이면 수익성 희석 가능",
        ),
        TableBlock("성장률 추이", pl.DataFrame(cols)),
    ]


def growthQualityBlock(data: dict) -> list:
    """calcGrowthQuality 결과 → CAGR + 성장 품질."""
    if not data:
        return []

    blocks: list = []
    blocks.append(
        HeadingBlock(
            _meta("growthQuality").label,
            level=2,
            helper="CAGR로 단기 변동 너머의 중기 추세를 본다",
        )
    )

    periods = data.get("periods", 0)
    metrics = []
    revCagr = data.get("revenueCagr")
    opCagr = data.get("operatingProfitCagr")
    npCagr = data.get("netProfitCagr")
    quality = data.get("quality", "")

    if revCagr is not None:
        metrics.append((f"매출 CAGR ({periods}Y)", f"{revCagr:+.1f}%"))
    if opCagr is not None:
        metrics.append((f"영업이익 CAGR ({periods}Y)", f"{opCagr:+.1f}%"))
    if npCagr is not None:
        metrics.append((f"순이익 CAGR ({periods}Y)", f"{npCagr:+.1f}%"))
    if quality:
        metrics.append(("성장 품질", quality))

    if not metrics:
        return []
    blocks.append(MetricBlock(metrics))
    return blocks


def growthFlagsBlock(flags: list[str]) -> list:
    """calcGrowthFlags 결과 → FlagBlock."""
    return _flagsBlock(flags)


# ── 2-3 안정성 ──


def leverageTrendBlock(data: dict) -> list:
    """calcLeverageTrend 결과 → 레버리지 시계열."""
    if not data:
        return []

    cols = _timelineTable(
        [
            (data.get("debtRatio", []), "{:.0f}%"),
            (data.get("netDebtRatio", []), "{:.0f}%"),
            (data.get("equityRatio", []), "{:.0f}%"),
        ],
        ["부채비율", "순부채비율", "자기자본비율"],
    )
    if cols is None:
        return []

    return [
        HeadingBlock(
            _meta("leverageTrend").label,
            level=2,
            helper="부채비율 200% 이상 위험, 50% 이하 매우 안정",
        ),
        TableBlock("레버리지 추이", pl.DataFrame(cols)),
    ]


def coverageTrendBlock(data: dict) -> list:
    """calcCoverageTrend 결과 → 이자보상배율 시계열."""
    if not data:
        return []

    cols = _timelineTable(
        [(data.get("interestCoverage", []), "{:.1f}배")],
        ["이자보상배율"],
    )
    if cols is None:
        return []

    return [
        HeadingBlock(
            _meta("coverageTrend").label,
            level=2,
            helper="이자보상배율 3배 이상 안정, 1배 미만 이자 지급 불능",
        ),
        TableBlock("이자보상 추이", pl.DataFrame(cols)),
    ]


def distressScoreBlock(data: dict) -> list:
    """calcDistressScore 결과 → Z-Score 시계열 + 등급."""
    if not data:
        return []

    blocks: list = []
    blocks.append(
        HeadingBlock(
            _meta("distressScore").label,
            level=2,
            helper="Z > 2.99 안전, 1.81~2.99 회색, < 1.81 위험",
        )
    )

    metrics = []
    latest = data.get("latestScore")
    zone = data.get("zone", "")
    if latest is not None:
        metrics.append(("최신 Z-Score", f"{latest:.2f}"))
    if zone:
        metrics.append(("판정", zone))
    if metrics:
        blocks.append(MetricBlock(metrics))

    cols = _timelineTable(
        [(data.get("altmanZScore", []), "{:.2f}")],
        ["Altman Z-Score"],
    )
    if cols is not None:
        blocks.append(TableBlock("Z-Score 추이", pl.DataFrame(cols)))

    return blocks


def stabilityFlagsBlock(flags: list[str]) -> list:
    """calcStabilityFlags 결과 → FlagBlock."""
    return _flagsBlock(flags)


# ── 2-4 효율성 ──


def turnoverTrendBlock(data: dict) -> list:
    """calcTurnoverTrend 결과 → 회전율 시계열."""
    if not data:
        return []

    cols = _timelineTable(
        [
            (data.get("totalAssetTurnover", []), "{:.2f}회"),
            (data.get("receivablesTurnover", []), "{:.2f}회"),
            (data.get("inventoryTurnover", []), "{:.2f}회"),
        ],
        ["총자산회전율", "매출채권회전율", "재고회전율"],
    )
    if cols is None:
        return []

    return [
        HeadingBlock(
            _meta("turnoverTrend").label,
            level=2,
            helper="회전율 상승 = 같은 자산으로 매출을 더 뽑는다",
        ),
        TableBlock("회전율 추이", pl.DataFrame(cols)),
    ]


def cccTrendBlock(data: dict) -> list:
    """calcCccTrend 결과 → CCC 구성요소 시계열."""
    if not data:
        return []

    cols = _timelineTable(
        [
            (data.get("dso", []), "{:.0f}일"),
            (data.get("dio", []), "{:.0f}일"),
            (data.get("dpo", []), "{:.0f}일"),
            (data.get("ccc", []), "{:.0f}일"),
        ],
        ["DSO(매출채권일)", "DIO(재고일)", "DPO(매입채무일)", "CCC"],
    )
    if cols is None:
        return []

    return [
        HeadingBlock(
            _meta("cccTrend").label,
            level=2,
            helper="CCC = DSO + DIO - DPO, 마이너스면 운전자본 유리",
        ),
        TableBlock("CCC 추이", pl.DataFrame(cols)),
    ]


def efficiencyFlagsBlock(flags: list[str]) -> list:
    """calcEfficiencyFlags 결과 → FlagBlock."""
    return _flagsBlock(flags)


# ── 2-5 종합 평가 ──


def scorecardBlock(data: dict) -> list:
    """calcScorecard 결과 → 5영역 등급 테이블."""
    if not data:
        return []

    items = data.get("items", [])
    if not items:
        return []

    blocks: list = []
    blocks.append(
        HeadingBlock(
            _meta("scorecard").label,
            level=2,
            helper="F 등급 영역을 최우선으로 개선 검토",
        )
    )

    rows = []
    for item in items:
        rows.append({"영역": item["area"], "등급": item["grade"]})
    blocks.append(TableBlock("", pl.DataFrame(rows)))

    profile = data.get("profile", "")
    if profile:
        blocks.append(TextBlock(f"재무 프로필: {profile}", style="dim", indent="h2"))

    return blocks


def piotroskiBlock(data: dict) -> list:
    """calcPiotroskiDetail 결과 → 9개 항목 상세."""
    if not data:
        return []

    blocks: list = []
    blocks.append(
        HeadingBlock(
            _meta("piotroski").label,
            level=2,
            helper="9점 만점, 7+ 건전, 3- 심각",
        )
    )

    total = data.get("total", 0)
    interp = data.get("interpretation", "")
    interpKor = {"strong": "건전", "moderate": "보통", "weak": "취약"}.get(interp, interp)
    blocks.append(MetricBlock([("F-Score", f"{total}/9 ({interpKor})")]))

    items = data.get("items", [])
    if items:
        rows = []
        for item in items:
            rows.append(
                {
                    "항목": item["signal"],
                    "충족": "O" if item["pass"] else "X",
                }
            )
        blocks.append(TableBlock("", pl.DataFrame(rows)))

    return blocks


def summaryFlagsBlock(flags: list[str]) -> list:
    """calcSummaryFlags 결과 → FlagBlock."""
    if not flags:
        return []
    return [FlagBlock(flags, kind="warning")]
