"""회사의 연혁 파이프라인."""

import polars as pl

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.reportSelector import selectReport
from dartlab.engines.docsParser.finance.companyHistory.parser import parseHistory
from dartlab.engines.docsParser.finance.companyHistory.types import CompanyHistoryResult


def companyHistory(stockCode: str) -> CompanyHistoryResult | None:
    """회사의 연혁 분석."""
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
            if "연혁" in title and ("회사" in title or title.strip().endswith("연혁")):
                content = row.get("section_content", "") or ""
                if len(content) < 50:
                    continue

                events = parseHistory(content)
                if events:
                    eventsDf = pl.DataFrame(events)
                    return CompanyHistoryResult(
                        corpName=corpName,
                        nYears=1,
                        events=events,
                        eventsDf=eventsDf,
                    )
    return None
