"""부문별 보고 추출 파이프라인."""

import polars as pl

from dartlab.core.dataLoader import PERIOD_KINDS, loadData, extractCorpName
from dartlab.core.notesExtractor import extractNotesContent, findNumberedSection
from dartlab.core.reportSelector import selectReport
from dartlab.finance.segment.parser import parseSegmentTables
from dartlab.finance.segment.types import SegmentsResult, SegmentTable


def segments(
    stockCode: str,
    period: str = "y",
) -> SegmentsResult | None:
    """연결재무제표 주석에서 부문별 보고 데이터 추출.

    Args:
        stockCode: 종목코드 (6자리)
        period: "y" (연간) | "q" (분기) | "h" (반기)

    Returns:
        SegmentsResult 또는 데이터 부족 시 None
    """
    df = loadData(stockCode)
    corpName = extractCorpName(df)

    kinds = PERIOD_KINDS.get(period, PERIOD_KINDS["y"])
    years = sorted(df["year"].unique().to_list(), reverse=True)

    allTables: dict[str, list[SegmentTable]] = {}

    for year in years:
        for kind in kinds:
            report = selectReport(df, year, reportKind=kind)
            if report is None:
                continue

            contents = extractNotesContent(report)
            if not contents:
                continue

            section = findNumberedSection(contents, "부문")
            if section is None:
                continue

            tables = parseSegmentTables(section)
            if tables:
                allTables[year] = tables
            break  # 해당 연도는 첫 번째 매칭된 보고서 사용

    if not allTables:
        return None

    revenue = _buildRevenueDf(allTables, years)

    return SegmentsResult(
        corpName=corpName,
        nYears=len(allTables),
        period=period,
        tables=allTables,
        revenue=revenue,
    )


def _buildRevenueDf(
    allTables: dict[str, list[SegmentTable]],
    sortedYears: list[str],
) -> pl.DataFrame | None:
    """부문별 매출 시계열 DataFrame 생성.

    당기 segment 테이블에서 매출/영업수익 행을 추출하여
    부문명 = 행, 연도 = 열 형태로 구성.
    """
    segmentRevenue: dict[str, dict[str, float | None]] = {}

    for year in sortedYears:
        tables = allTables.get(year, [])
        for t in tables:
            if t.tableType == "segment" and t.period == "당기" and t.aligned:
                for name in t.order:
                    if ("매출" in name or "영업수익" in name) and "내부" not in name:
                        for i, col in enumerate(t.columns):
                            val = t.rows[name][i] if i < len(t.rows[name]) else None
                            if col not in segmentRevenue:
                                segmentRevenue[col] = {}
                            segmentRevenue[col][year] = val
                        break
                break

    if not segmentRevenue:
        return None

    # 연도 목록 (데이터가 있는 연도만, 역순)
    allYears = sorted(
        {y for vals in segmentRevenue.values() for y in vals},
        reverse=True,
    )

    rows = []
    for segName, yearVals in segmentRevenue.items():
        row: dict[str, object] = {"부문": segName}
        for y in allYears:
            row[y] = yearVals.get(y)
        rows.append(row)

    if not rows:
        return None

    schema: dict[str, type] = {"부문": pl.Utf8}
    for y in allYears:
        schema[y] = pl.Float64
    return pl.DataFrame(rows, schema=schema)
