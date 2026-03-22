"""회사의 개요 파이프라인."""

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.reportSelector import selectReport
from dartlab.engines.company.dart.docs.finance.companyOverviewDetail.parser import parseCompanyInfo
from dartlab.engines.company.dart.docs.finance.companyOverviewDetail.types import CompanyOverviewDetailResult


def companyOverviewDetail(stockCode: str) -> CompanyOverviewDetailResult | None:
    """회사의 개요 분석."""
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
            if "회사의 개요" in title or "회사 의 개요" in title:
                content = row.get("section_content", "") or ""
                if len(content) < 50:
                    continue

                info = parseCompanyInfo(content)
                if info:
                    return CompanyOverviewDetailResult(
                        corpName=corpName,
                        nYears=1,
                        foundedDate=info.get("foundedDate"),
                        listedDate=info.get("listedDate"),
                        address=info.get("address"),
                        ceo=info.get("ceo"),
                        mainBusiness=info.get("mainBusiness"),
                        website=info.get("website"),
                    )

                if len(content) > 200:
                    return CompanyOverviewDetailResult(corpName=corpName, nYears=1)
    return None
