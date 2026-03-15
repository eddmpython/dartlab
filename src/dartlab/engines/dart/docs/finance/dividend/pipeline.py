"""배당 데이터 추출 파이프라인."""

import polars as pl

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.reportSelector import extractReportYear, selectReport
from dartlab.engines.dart.docs.finance.dividend.parser import parseDividendTable
from dartlab.engines.dart.docs.finance.dividend.types import DividendResult


def dividend(stockCode: str) -> DividendResult | None:
    """사업보고서에서 배당지표 시계열 추출.

    Args:
        stockCode: 종목코드 (6자리)

    Returns:
        DividendResult 또는 데이터 부족 시 None
    """
    df = loadData(stockCode)
    corpName = extractCorpName(df)

    years = sorted(df["year"].unique().to_list(), reverse=True)

    yearData: dict[int, dict[str, float]] = {}

    for year in years:
        report = selectReport(df, year, reportKind="annual")
        if report is None:
            continue

        divRows = report.filter(pl.col("section_title").str.contains("배당"))
        if divRows.height == 0:
            continue

        content = divRows["section_content"][0]
        reportYear = extractReportYear(divRows["report_type"][0])
        if reportYear is None:
            continue

        parsed = parseDividendTable(content)
        offsets = [0, -1, -2]

        for field in [
            "netIncome",
            "eps",
            "totalDividend",
            "payoutRatio",
            "dividendYieldCommon",
            "dpsCommon",
            "dpsPreferred",
        ]:
            vals = parsed.get(field, [])
            for j, offset in enumerate(offsets):
                if j < len(vals) and vals[j] is not None:
                    yr = reportYear + offset
                    if yr not in yearData:
                        yearData[yr] = {}
                    if field not in yearData[yr]:
                        yearData[yr][field] = vals[j]

    if not yearData:
        return None

    records = []
    for yr in sorted(yearData.keys()):
        d = yearData[yr]
        records.append(
            {
                "year": yr,
                "netIncome": d.get("netIncome"),
                "eps": d.get("eps"),
                "totalDividend": d.get("totalDividend"),
                "payoutRatio": d.get("payoutRatio"),
                "dividendYield": d.get("dividendYieldCommon"),
                "dps": d.get("dpsCommon"),
                "dpsPreferred": d.get("dpsPreferred"),
            }
        )

    ts = pl.DataFrame(records)

    return DividendResult(
        corpName=corpName,
        nYears=ts.height,
        timeSeries=ts,
    )
