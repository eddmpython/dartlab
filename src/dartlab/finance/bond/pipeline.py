"""채무증권 발행실적 데이터 추출 파이프라인."""

import polars as pl

from dartlab.core.dataLoader import loadData, extractCorpName
from dartlab.core.reportSelector import selectReport, extractReportYear
from dartlab.finance.bond.parser import parseBondTable
from dartlab.finance.bond.types import BondIssuance, BondResult


def bond(stockCode: str) -> BondResult | None:
    """사업보고서에서 채무증권 발행실적 추출.

    Args:
        stockCode: 종목코드 (6자리)

    Returns:
        BondResult 또는 데이터 부족 시 None
    """
    df = loadData(stockCode)
    corpName = extractCorpName(df)

    years = sorted(df["year"].unique().to_list(), reverse=True)

    yearData: dict[int, list[dict]] = {}

    for year in years:
        report = selectReport(df, year, reportKind="annual")
        if report is None:
            continue

        bondRows = report.filter(
            pl.col("section_title").str.contains("증권의 발행")
        )
        if bondRows.height == 0:
            continue

        reportYear = extractReportYear(bondRows["report_type"][0])
        if reportYear is None:
            continue

        content = bondRows["section_content"][0]
        parsed = parseBondTable(content)

        if parsed and reportYear not in yearData:
            yearData[reportYear] = parsed

    if not yearData:
        return None

    latestYear = max(yearData.keys())
    latestData = yearData[latestYear]

    issuances = [
        BondIssuance(
            issuer=d["issuer"],
            bondType=d.get("bondType"),
            method=d.get("method"),
            issueDate=d.get("issueDate"),
            amount=d.get("amount"),
            interestRate=d.get("interestRate"),
            rating=d.get("rating"),
            maturityDate=d.get("maturityDate"),
            redeemed=d.get("redeemed"),
            underwriter=d.get("underwriter"),
        )
        for d in latestData
    ]

    records = []
    for yr in sorted(yearData.keys()):
        data = yearData[yr]
        totalAmount = sum(d.get("amount") or 0 for d in data)
        unredeemed = sum(1 for d in data if "미상환" in (d.get("redeemed") or ""))
        records.append(
            {
                "year": yr,
                "totalIssuances": len(data),
                "totalAmount": totalAmount,
                "unredeemedCount": unredeemed,
            }
        )

    ts = pl.DataFrame(records)

    return BondResult(
        corpName=corpName,
        nYears=ts.height,
        issuances=issuances,
        timeSeries=ts,
    )


