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
