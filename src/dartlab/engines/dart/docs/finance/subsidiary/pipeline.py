"""타법인출자 현황 데이터 추출 파이프라인."""

import polars as pl

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.reportSelector import extractReportYear, selectReport
from dartlab.engines.dart.docs.finance.subsidiary.parser import parseSubsidiaryTable
from dartlab.engines.dart.docs.finance.subsidiary.types import SubsidiaryInvestment, SubsidiaryResult


def subsidiary(stockCode: str) -> SubsidiaryResult | None:
    """사업보고서에서 타법인출자 현황 추출.

    Args:
        stockCode: 종목코드 (6자리)

    Returns:
        SubsidiaryResult 또는 데이터 부족 시 None
    """
    df = loadData(stockCode)
    corpName = extractCorpName(df)

    years = sorted(df["year"].unique().to_list(), reverse=True)

    yearData: dict[int, list[dict]] = {}

    for year in years:
        report = selectReport(df, year, reportKind="annual")
        if report is None:
            continue

        subRows = report.filter(pl.col("section_title").str.contains("타법인"))
        if subRows.height == 0:
            subRows = report.filter(pl.col("section_title").str.contains("출자"))
        if subRows.height == 0:
            continue

        reportYear = extractReportYear(subRows["report_type"][0])
        if reportYear is None:
            continue

        for ri in range(subRows.height):
            content = subRows["section_content"][ri]
            parsed = parseSubsidiaryTable(content)
            if parsed:
                if reportYear not in yearData:
                    yearData[reportYear] = parsed
                break

    if not yearData:
        return None

    latestYear = max(yearData.keys())
    latestData = yearData[latestYear]

    investments = [
        SubsidiaryInvestment(
            name=d["name"],
            listed=d.get("listed"),
            firstAcquired=d.get("firstAcquired"),
            purpose=d.get("purpose"),
            firstAmount=d.get("firstAmount"),
            beginShares=d.get("beginShares"),
            beginRatio=d.get("beginRatio"),
            beginBook=d.get("beginBook"),
            acquiredShares=d.get("acquiredShares"),
            acquiredAmount=d.get("acquiredAmount"),
            valuationGain=d.get("valuationGain"),
            endShares=d.get("endShares"),
            endRatio=d.get("endRatio"),
            endBook=d.get("endBook"),
            totalAssets=d.get("totalAssets"),
            netIncome=d.get("netIncome"),
        )
        for d in latestData
    ]

    records = []
    for yr in sorted(yearData.keys()):
        data = yearData[yr]
        totalBook = sum(d.get("endBook") or 0 for d in data)
        listedCount = sum(1 for d in data if d.get("listed") == "상장")
        unlistedCount = len(data) - listedCount
        records.append(
            {
                "year": yr,
                "totalCount": len(data),
                "listedCount": listedCount,
                "unlistedCount": unlistedCount,
                "totalBook": totalBook,
            }
        )

    ts = pl.DataFrame(records)

    return SubsidiaryResult(
        corpName=corpName,
        nYears=ts.height,
        investments=investments,
        timeSeries=ts,
    )
