"""매출 및 수주상황 파이프라인."""

import polars as pl

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.reportSelector import selectReport
from dartlab.engines.dart.docs.finance.salesOrder.parser import (
    detectUnit,
    parseOrderBacklog,
    parseSalesTable,
)
from dartlab.engines.dart.docs.finance.salesOrder.types import SalesOrderResult


def _buildDf(rows: list[dict], headers: list[str] | None = None) -> pl.DataFrame | None:
    """행 목록을 DataFrame으로 변환.

    headers가 제공되면 v1/v2/v3 대신 실제 헤더명을 컬럼명으로 사용한다.
    """
    if not rows:
        return None

    maxVals = max(len(r["values"]) for r in rows)
    data: dict[str, list] = {"label": [r["label"] for r in rows]}
    for i in range(maxVals):
        colName = headers[i] if headers and i < len(headers) else f"v{i + 1}"
        if colName in data:
            colName = f"{colName}_{i + 1}"
        data[colName] = [r["values"][i] if i < len(r["values"]) else None for r in rows]

    schema = {"label": pl.Utf8}
    for col in data:
        if col != "label":
            schema[col] = pl.Int64

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
                sales, salesHeaders = parseSalesTable(content)
                orders, orderHeaders = parseOrderBacklog(content)

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
                    salesDf=_buildDf(sales, salesHeaders),
                    orderDf=_buildDf(orders, orderHeaders),
                )

    return None
