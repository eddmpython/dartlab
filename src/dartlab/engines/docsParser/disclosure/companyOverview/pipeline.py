"""회사의 개요 추출 파이프라인."""

import polars as pl

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.reportSelector import extractReportYear, selectReport
from dartlab.engines.docsParser.disclosure.companyOverview.parser import parseOverview
from dartlab.engines.docsParser.disclosure.companyOverview.types import OverviewResult


def companyOverview(stockCode: str) -> OverviewResult | None:
    """사업보고서에서 회사의 개요 정량 데이터 추출.

    Args:
        stockCode: 종목코드 (6자리)

    Returns:
        OverviewResult 또는 데이터 부족 시 None
    """
    df = loadData(stockCode)
    corpName = extractCorpName(df)

    years = sorted(df["year"].unique().to_list(), reverse=True)

    for year in years:
        report = selectReport(df, year, reportKind="annual")
        if report is None:
            continue

        overviewRow = report.filter(
            pl.col("section_title") == "1. 회사의 개요"
        )
        if overviewRow.height == 0:
            overviewRow = report.filter(
                pl.col("section_title").str.contains("회사의 개요")
                & pl.col("section_title").str.starts_with("1.")
            )
        if overviewRow.height == 0:
            overviewRow = report.filter(
                pl.col("section_title").str.contains("회사의 개요")
                & ~pl.col("section_title").str.starts_with("I.")
            )
        if overviewRow.height == 0:
            continue

        text = overviewRow.row(0, named=True)["section_content"]
        reportYear = extractReportYear(overviewRow["report_type"][0])
        if reportYear is None:
            continue

        parsed = parseOverview(text)

        return OverviewResult(
            corpName=corpName,
            year=reportYear,
            founded=parsed.get("founded"),
            address=parsed.get("address"),
            homepage=parsed.get("homepage"),
            subsidiaryCount=parsed.get("subsidiaryCount"),
            isSME=parsed.get("isSME"),
            isVenture=parsed.get("isVenture"),
            creditRatings=parsed.get("creditRatings", []),
            listedDate=parsed.get("listedDate"),
            missing=parsed.get("missing", []),
            failed=parsed.get("failed", []),
        )

    return None
