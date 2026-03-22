"""주식의 총수 데이터 추출 파이프라인."""

import polars as pl

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.reportSelector import extractReportYear, selectReport
from dartlab.engines.company.dart.docs.finance.shareCapital.parser import parseShareCapitalTable
from dartlab.engines.company.dart.docs.finance.shareCapital.types import ShareCapitalResult


def shareCapital(stockCode: str) -> ShareCapitalResult | None:
    """사업보고서에서 주식의 총수 추출.

    Args:
        stockCode: 종목코드 (6자리)

    Returns:
        ShareCapitalResult 또는 데이터 부족 시 None
    """
    df = loadData(stockCode)
    corpName = extractCorpName(df)

    years = sorted(df["year"].unique().to_list(), reverse=True)

    yearData: dict[int, dict] = {}

    for year in years:
        report = selectReport(df, year, reportKind="annual")
        if report is None:
            continue

        shareRows = report.filter(pl.col("section_title").str.contains("주식의 총수"))
        if shareRows.height == 0:
            continue

        reportYear = extractReportYear(shareRows["report_type"][0])
        if reportYear is None:
            continue

        content = shareRows["section_content"][0]
        parsed = parseShareCapitalTable(content)

        if parsed is None:
            continue

        if reportYear not in yearData:
            yearData[reportYear] = parsed

    if not yearData:
        return None

    latestYear = max(yearData.keys())
    latest = yearData[latestYear]

    records = []
    for yr in sorted(yearData.keys()):
        d = yearData[yr]
        records.append(
            {
                "year": yr,
                "outstandingShares": d.get("outstandingShares"),
                "treasuryShares": d.get("treasuryShares"),
                "floatingShares": d.get("floatingShares"),
                "treasuryRatio": d.get("treasuryRatio"),
            }
        )

    ts = pl.DataFrame(records)

    return ShareCapitalResult(
        corpName=corpName,
        nYears=ts.height,
        authorizedShares=latest.get("authorizedShares"),
        issuedShares=latest.get("issuedShares"),
        retiredShares=latest.get("retiredShares"),
        outstandingShares=latest.get("outstandingShares"),
        treasuryShares=latest.get("treasuryShares"),
        floatingShares=latest.get("floatingShares"),
        treasuryRatio=latest.get("treasuryRatio"),
        timeSeries=ts,
    )
