"""매출 및 수주상황 파이프라인."""

import polars as pl

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.reportSelector import selectReport
from dartlab.engines.docsParser.finance.salesOrder.parser import (
    detectUnit,
    parseOrderBacklog,
    parseSalesTable,
)
from dartlab.engines.docsParser.finance.salesOrder.types import SalesOrderResult


def _buildDf(rows: list[dict]) -> pl.DataFrame | None:
    """행 목록을 DataFrame으로 변환."""
    if not rows:
        return None

    maxVals = max(len(r["values"]) for r in rows)
    data: dict[str, list] = {"label": [r["label"] for r in rows]}
    for i in range(maxVals):
        data[f"v{i+1}"] = [
            r["values"][i] if i < len(r["values"]) else None for r in rows
        ]

    schema = {"label": pl.Utf8}
    for i in range(maxVals):
        schema[f"v{i+1}"] = pl.Int64

    return pl.DataFrame(data, schema=schema)


def salesOrder(stockCode: str) -> SalesOrderResult | None:
    """매출 및 수주상황 분석."""
    try:
        df = loadData(stockCode)
    except FileNotFoundError:
        return None

    corpName = extractCorpName(df)
    years = sorted(df["year"].unique().to_list(), reverse=True)

    for year in years[:2]:
        report = selectReport(df, year, reportKind="annual")
        if report is None:
            continue

        for row in report.iter_rows(named=True):
            title = row.get("section_title", "") or ""
            if "매출" in title and ("수주" in title or "사항" in title):
                content = row.get("section_content", "") or ""
                if len(content) < 50:
                    continue

                unit = detectUnit(content)
                sales = parseSalesTable(content)
                orders = parseOrderBacklog(content)

                if not sales and not orders:
                    if "없습니다" in content[:500] or len(content) < 300:
                        return SalesOrderResult(
                            corpName=corpName,
                            nYears=1,
                            unit=unit,
                            noData=True,
                        )
                    continue

                return SalesOrderResult(
                    corpName=corpName,
                    nYears=1,
                    unit=unit,
                    sales=sales,
                    orders=orders,
                    noData=False,
                    salesDf=_buildDf(sales),
                    orderDf=_buildDf(orders),
                )

    return None
