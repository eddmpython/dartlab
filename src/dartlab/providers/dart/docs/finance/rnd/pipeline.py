"""연구개발활동 데이터 추출 파이프라인."""

import re

import polars as pl

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.reportSelector import selectReport
from dartlab.providers.dart.docs.finance.rnd.parser import extractTableBlocks, parseRndTable
from dartlab.providers.dart.docs.finance.rnd.types import RndResult

RND_SECTION_PATTERNS = [
    r"연구개발활동",
    r"연구개발",
    r"주요계약\s*및\s*연구개발",
]


def rnd(stockCode: str) -> RndResult | None:
    """사업보고서에서 연구개발비 시계열 추출.

    Args:
        stockCode: 종목코드 (6자리)

    Returns:
        RndResult 또는 데이터 부족 시 None
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
            parsed = parseRndTable(block)
            if parsed and parsed["rndExpense"]:
                # 첫 번째 기간(당기) 값만 사용
                row: dict = {"year": int(year)}
                row["rndExpense"] = parsed["rndExpense"][0]
                if parsed["revenueRatio"]:
                    row["revenueRatio"] = parsed["revenueRatio"][0]
                allRows.append(row)
                break

    if not allRows:
        return None

    rndDf = _buildRndDf(allRows)

    return RndResult(
        corpName=corpName,
        nYears=len(allRows),
        rndDf=rndDf,
    )


def _findSection(report: pl.DataFrame) -> str | None:
    """연구개발 섹션 content 반환."""
    for row in report.iter_rows(named=True):
        title = row.get("section_title", "") or ""
        if any(re.search(p, title) for p in RND_SECTION_PATTERNS):
            content = row.get("section_content", "") or ""
            if len(content) > 100:
                return content
    return None


def _buildRndDf(rows: list[dict]) -> pl.DataFrame:
    data = sorted(rows, key=lambda x: x["year"])
    schema = {
        "year": pl.Int64,
        "rndExpense": pl.Int64,
        "revenueRatio": pl.Float64,
    }
    for r in data:
        for col in schema:
            if col not in r:
                r[col] = None
    return pl.DataFrame(data, schema=schema)
