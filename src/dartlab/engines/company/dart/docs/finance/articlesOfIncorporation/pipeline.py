"""정관에 관한 사항 파이프라인."""

import polars as pl

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.reportSelector import selectReport
from dartlab.engines.company.dart.docs.finance.articlesOfIncorporation.parser import (
    parseArticlesChanges,
    parseBusinessPurpose,
)
from dartlab.engines.company.dart.docs.finance.articlesOfIncorporation.types import ArticlesResult


def articlesOfIncorporation(stockCode: str) -> ArticlesResult | None:
    """정관에 관한 사항 분석."""
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
            if "정관" in title:
                content = row.get("section_content", "") or ""
                if len(content) < 50:
                    continue

                changes = parseArticlesChanges(content)
                purposes = parseBusinessPurpose(content)

                if not changes and not purposes:
                    if "없습니다" in content[:500] or "해당사항" in content[:500]:
                        return ArticlesResult(corpName=corpName, nYears=1, noData=True)
                    continue

                changesDf = None
                if changes:
                    changesDf = pl.DataFrame(changes)

                purposesDf = None
                if purposes:
                    purposesDf = pl.DataFrame(purposes)

                return ArticlesResult(
                    corpName=corpName,
                    nYears=1,
                    changes=changes,
                    purposes=purposes,
                    changesDf=changesDf,
                    purposesDf=purposesDf,
                )
    return None
