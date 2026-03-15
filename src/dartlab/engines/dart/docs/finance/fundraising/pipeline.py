"""증권 발행(증자/감자) 파이프라인."""

import polars as pl

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.reportSelector import selectReport
from dartlab.engines.dart.docs.finance.fundraising.parser import parseEquityIssuance
from dartlab.engines.dart.docs.finance.fundraising.types import FundraisingResult


def fundraising(stockCode: str) -> FundraisingResult | None:
    """증권 발행(증자/감자) 분석."""
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
            if "증권" in title and "자금조달" in title:
                content = row.get("section_content", "") or ""
                if len(content) < 50:
                    continue

                issuances = parseEquityIssuance(content)

                if not issuances:
                    noDataSignals = (
                        "없습니다" in content[:500]
                        or "해당사항 없음" in content[:500]
                        or "해당없음" in content[:500]
                        or len(content) < 300
                    )
                    hasHeader = "발행" in content and ("일자" in content or "형태" in content)
                    if noDataSignals or hasHeader:
                        return FundraisingResult(
                            corpName=corpName,
                            nYears=1,
                            issuances=[],
                            noData=True,
                        )
                    continue

                issuanceDf = pl.DataFrame(
                    {
                        "date": [i.get("date", "") for i in issuances],
                        "issueType": [i.get("issueType", "") for i in issuances],
                        "stockType": [i.get("stockType", "") for i in issuances],
                        "quantity": [i.get("quantity") for i in issuances],
                        "parValue": [i.get("parValue") for i in issuances],
                        "issuePrice": [i.get("issuePrice") for i in issuances],
                        "note": [i.get("note", "") for i in issuances],
                    },
                    schema={
                        "date": pl.Utf8,
                        "issueType": pl.Utf8,
                        "stockType": pl.Utf8,
                        "quantity": pl.Int64,
                        "parValue": pl.Int64,
                        "issuePrice": pl.Int64,
                        "note": pl.Utf8,
                    },
                )

                return FundraisingResult(
                    corpName=corpName,
                    nYears=1,
                    issuances=issuances,
                    noData=False,
                    issuanceDf=issuanceDf,
                )

    return None
