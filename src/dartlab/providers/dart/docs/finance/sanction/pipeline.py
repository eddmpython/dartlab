"""제재 현황 데이터 추출 파이프라인."""

import re

import polars as pl

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.reportSelector import selectReport
from dartlab.providers.dart.docs.finance.sanction.parser import extractTableBlocks, parseSanctionTable
from dartlab.providers.dart.docs.finance.sanction.types import SanctionResult


def sanction(stockCode: str) -> SanctionResult | None:
    """사업보고서에서 제재 현황 시계열 추출.

    Args:
        stockCode: 종목코드 (6자리)

    Returns:
        SanctionResult 또는 데이터 부족 시 None
    """
    df = loadData(stockCode)
    corpName = extractCorpName(df)
    years = sorted(df["year"].unique().to_list(), reverse=True)

    allRows: list[dict] = []

    for year in years:
        report = selectReport(df, year, reportKind="annual")
        if report is None:
            continue

        content = _findSection(report)
        if content is None:
            continue

        blocks = extractTableBlocks(content)
        for block in blocks:
            entries = parseSanctionTable(block)
            for entry in entries:
                entry["year"] = int(year)
                allRows.append(entry)

    if not allRows:
        return None

    sanctionDf = _buildSanctionDf(allRows)

    return SanctionResult(
        corpName=corpName,
        nYears=len({r["year"] for r in allRows}),
        sanctionDf=sanctionDf,
    )


def _findSection(report: pl.DataFrame) -> str | None:
    """제재 현황 섹션 content 반환."""
    for row in report.iter_rows(named=True):
        title = row.get("section_title", "") or ""
        if re.search(r"제재", title):
            content = row.get("section_content", "") or ""
            if len(content) > 100:
                return content
    return None


def _buildSanctionDf(rows: list[dict]) -> pl.DataFrame:
    data = sorted(rows, key=lambda x: x["year"])
    schema = {
        "year": pl.Int64,
        "date": pl.Utf8,
        "agency": pl.Utf8,
        "subject": pl.Utf8,
        "action": pl.Utf8,
        "amount": pl.Utf8,
        "amountValue": pl.Int64,
        "reason": pl.Utf8,
    }
    for r in data:
        for col in schema:
            if col not in r:
                r[col] = None
    return pl.DataFrame(data, schema=schema)
