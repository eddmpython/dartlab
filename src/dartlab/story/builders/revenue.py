"""story 블록 빌더 — revenue 도메인 (debt-honesty P3-3 god-split). 공유 imports·상수·헬퍼는 _shared."""

from __future__ import annotations

from dartlab.story.builders._shared import (
    FlagBlock,
    HeadingBlock,
    MetricBlock,
    TableBlock,
    TextBlock,
    _fmtEstimate,
    _historyTable,
    _meta,
    _notesDetailBlocks,
    _quarterlyRevenueTable,
    _tupleFlags,
    narrateConcentration,
    narrateGrowth,
    pl,
    unifyTableScale,
)

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
            margin = seg.get("opMargin")
            row["이익률"] = f"{margin:.1f}%" if margin is not None else "-"
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
        [h["year"] for h in history]
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

    catalogKey = {"productBreakdown": "product", "regionBreakdown": "region"}.get(sub, sub)
    meta = _meta(catalogKey)
    title = meta.label

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

    narration = narrateGrowth(yoy, cagr)
    if narration:
        blocks.append(TextBlock(narration))

    if metrics:
        blocks.append(MetricBlock(metrics))
    if qTable is not None:
        blocks.append(qTable)

    return blocks


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

    narration = narrateConcentration(data)
    if narration:
        blocks.append(TextBlock(narration))

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

    gmDir = data.get("grossMarginDirection", "안정")
    if gmDir and gmDir != "안정":
        metrics.append(("총이익률 방향", gmDir))

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
    """calcFlags 결과 → FlagBlock.

    조립 규칙은 `_shared._tupleFlags` 가 갖는다. 예전에는 같은 일곱 줄이 이 파일과
    revenue 와 _shared 세 곳에 있었고, 공용 자리가 이미 있는데도 둘이 자기 사본을 썼다.
    """
    return _tupleFlags(flags)


# ── 3-2 비용구조 ──


def costBreakdownBlock(data: dict) -> list:
    """calcCostBreakdown 결과 → 비용 비중 시계열."""
    cols = _historyTable(
        data,
        [
            ("costOfSalesRatio", "매출원가율(%)", "{:.1f}%"),
            ("sgaRatio", "판관비율(%)", "{:.1f}%"),
            ("operatingCostRatio", "영업비용률(%)", "{:.1f}%"),
        ],
    )
    if cols is None:
        return []
    blocks: list = [
        HeadingBlock(
            _meta("costBreakdown").label,
            level=2,
            helper="원가율+판관비율 = 영업비용률, 100에서 빼면 영업이익률",
        ),
        TableBlock("비용 비중 추이", pl.DataFrame(cols)),
    ]
    blocks.extend(_notesDetailBlocks(data, {"costByNature": "비용 성격별 분류"}))
    return blocks


def revenueForecastBlock(data: dict) -> list:
    """calcRevenueForecast -> 시나리오 테이블 + 신뢰도."""
    if not data:
        return []

    # 예측 불가 판정 시 경고만 표시
    if not data.get("forecastable", True):
        reason = data.get("unforecastableReason", "")
        return [
            HeadingBlock(
                _meta("revenueForecast").label,
                level=2,
                helper="7-소스 앙상블 매출 예측 -- 모든 수치는 추정치",
            ),
            TextBlock(f"이 기업은 현재 정량 예측이 불가능합니다: {reason}"),
        ]

    cur = data.get("currency", "KRW")
    blocks: list = [
        HeadingBlock(
            _meta("revenueForecast").label,
            level=2,
            helper="7-소스 앙상블 매출 예측 -- 모든 수치는 추정치",
        ),
    ]

    # 신뢰도 + 방법론 요약
    metrics = [
        ("방법", data.get("method", "")),
        ("신뢰도", data.get("confidence", "")),
    ]
    lifecycle = data.get("lifecycle", "")
    if lifecycle:
        metrics.append(("라이프사이클", lifecycle))
    blocks.append(MetricBlock(metrics))

    # 시나리오 테이블
    scenarios = data.get("scenarios", {})
    if scenarios:
        rows = []
        for label in ("bull", "base", "bear"):
            sc = scenarios.get(label)
            if not sc:
                continue
            proj = sc.get("projected", [])
            gr = sc.get("growthRates", [])
            prob = sc.get("probability", 0)
            row = {"시나리오": f"{label.title()} ({prob:.0f}%)"}
            for i, (p, g) in enumerate(zip(proj, gr)):
                row[f"+{i + 1}년"] = f"{_fmtEstimate(p, cur)} ({g:+.1f}%)"
            rows.append(row)
        if rows:
            blocks.append(TableBlock("[추정] 시나리오별 매출 전망", pl.DataFrame(rows)))
    else:
        # 시나리오 없이 기본 전망만
        projected = data.get("projected", [])
        growthRates = data.get("growthRates", [])
        if projected:
            rows = []
            for i, (p, g) in enumerate(zip(projected, growthRates)):
                rows.append({"연차": f"+{i + 1}년", "매출": _fmtEstimate(p, cur), "성장률": f"{g:+.1f}%"})
            blocks.append(TableBlock("[추정] 매출 전망", pl.DataFrame(rows)))

    blocks.append(TextBlock(data.get("disclaimer", ""), style="dim"))

    # scenario band chart
    scenarios = data.get("scenarios", {})
    if scenarios:
        from dartlab.story.blocks import ChartBlock
        from dartlab.viz.generators import specRevenueScenarioBand

        # historical: calc가 반환하는 과거 매출 시계열 (list[float])
        hist_vals = data.get("historical", []) or []
        history_dicts = (
            [{"period": f"Y-{len(hist_vals) - i}", "revenue": v} for i, v in enumerate(hist_vals) if v is not None]
            if hist_vals
            else []
        )
        forecasts = {}
        for key in ("base", "bull", "bear"):
            sc = scenarios.get(key, {})
            if sc and sc.get("projected"):
                forecasts[key] = sc["projected"]
                if not forecasts.get("periods"):
                    forecasts["periods"] = [f"+{i + 1}Y" for i in range(len(sc["projected"]))]

        if history_dicts or forecasts:
            band_spec = specRevenueScenarioBand(history_dicts, forecasts if forecasts else None)
            if band_spec:
                blocks.append(ChartBlock(spec=band_spec))

    return blocks


def segmentForecastBlock(data: dict) -> list:
    """calcSegmentForecast -> 세그먼트별 성장 테이블."""
    if not data:
        return []
    segments = data.get("segments", [])
    if not segments:
        return []

    data.get("currency", "KRW")
    blocks: list = [
        HeadingBlock(
            _meta("segmentForecast").label,
            level=2,
            helper="부문별 개별 매출 성장 전망",
        ),
    ]

    rows = []
    for seg in segments:
        gr = seg.get("growthRates", [])
        row = {
            "부문": seg.get("name", ""),
            "매출비중": f"{seg.get('shareOfRevenue', 0):.1f}%",
            "방법": seg.get("method", ""),
        }
        for i, g in enumerate(gr):
            row[f"+{i + 1}년"] = f"{g:+.1f}%"
        rows.append(row)
    if rows:
        blocks.append(TableBlock("[추정] 세그먼트별 성장률", pl.DataFrame(rows)))

    return blocks


# ── 영업외손익 분해 빌더 ──


def nonOperatingBreakdownBlock(data: dict) -> list:
    """calcNonOperatingBreakdown → HeadingBlock + TableBlock."""
    if not data:
        return []
    history = data.get("history", [])
    if not history:
        return []

    rows = []
    for h in history:
        rows.append(
            {
                "기간": h["period"],
                "영업이익": h.get("opIncome"),
                "금융수익": h.get("finIncome"),
                "금융비용": h.get("finCost"),
                "지분법": h.get("associateIncome"),
                "기타수익": h.get("otherIncome"),
                "기타비용": h.get("otherExpense"),
                "영업외비율": f"{h['nonOpRatio']:.0f}%" if h.get("nonOpRatio") is not None else "-",
            }
        )

    valueCols = ["영업이익", "금융수익", "금융비용", "지분법", "기타수익", "기타비용"]
    unified = unifyTableScale(rows, "기간", valueCols, unit="millions")

    blocks: list = []
    blocks.append(
        HeadingBlock(
            _meta("nonOperatingBreakdown").label,
            level=2,
            helper="영업외 > 30%이면 영업만으로 기업 판단 불가",
        )
    )
    blocks.append(TableBlock("", pl.DataFrame(unified)))
    blocks.extend(_notesDetailBlocks(data, {"affiliates": "관계기업 투자"}))
    return blocks
