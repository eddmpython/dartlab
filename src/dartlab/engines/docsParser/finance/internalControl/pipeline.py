"""내부통제 데이터 추출 파이프라인."""

import re

import polars as pl

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.reportSelector import selectReport
from dartlab.engines.docsParser.finance.internalControl.parser import extractTableBlocks, parseInternalControlTable
from dartlab.engines.docsParser.finance.internalControl.types import InternalControlResult


def internalControl(stockCode: str) -> InternalControlResult | None:
    """사업보고서에서 내부회계관리제도 시계열 추출.

    Args:
        stockCode: 종목코드 (6자리)

    Returns:
        InternalControlResult 또는 데이터 부족 시 None
    """
    df = loadData(stockCode)
    corpName = extractCorpName(df)
    years = sorted(df["year"].unique().to_list(), reverse=True)

    allRows: list[dict] = []
    seenPeriods: set[str] = set()

    for year in years:
        report = selectReport(df, year, reportKind="annual")
        if report is None:
            continue

        content = _findSection(report)
        if content is None:
            continue

        blocks = extractTableBlocks(content)
        for block in blocks:
            entries = parseInternalControlTable(block)
            for entry in entries:
                period = entry.get("period", "")
                if period not in seenPeriods:
                    seenPeriods.add(period)
                    entry["year"] = year
                    allRows.append(entry)

    if not allRows:
        return None

    controlDf = _buildControlDf(allRows)

    return InternalControlResult(
        corpName=corpName,
        nYears=len(allRows),
        controlDf=controlDf,
    )


def _findSection(report: pl.DataFrame) -> str | None:
    """내부통제 섹션 content 반환."""
    for row in report.iter_rows(named=True):
        title = row.get("section_title", "") or ""
        if re.search(r"내부통제|내부회계", title):
            content = row.get("section_content", "") or ""
            if len(content) > 100:
                return content
    return None


def _buildControlDf(rows: list[dict]) -> pl.DataFrame:
    data = sorted(rows, key=lambda x: x.get("year", ""), reverse=True)
    schema = {
        "year": pl.Utf8,
        "period": pl.Utf8,
        "opinion": pl.Utf8,
        "auditor": pl.Utf8,
        "hasWeakness": pl.Boolean,
    }
    for r in data:
        for col in schema:
            if col not in r:
                r[col] = None
    return pl.DataFrame(data, schema=schema)
