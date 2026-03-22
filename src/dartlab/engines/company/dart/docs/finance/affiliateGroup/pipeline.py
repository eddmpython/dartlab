"""계열회사 현황 파이프라인."""

import re

import polars as pl

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.reportSelector import selectReport
from dartlab.engines.company.dart.docs.finance.affiliateGroup.parser import parseAffiliateList, parseGroupSummary
from dartlab.engines.company.dart.docs.finance.affiliateGroup.types import AffiliateGroupResult


def affiliateGroup(stockCode: str) -> AffiliateGroupResult | None:
    """계열회사 현황 분석."""
    try:
        df = loadData(stockCode)
    except FileNotFoundError:
        return None

    corpName = extractCorpName(df)
    years = sorted(df["year"].unique().to_list(), reverse=True)

    for year in years:
        report = selectReport(df, year, reportKind="annual")
        if report is None:
            continue

        # 1. 상세표에서 계열사 목록
        affiliates: list[dict] = []
        for row in report.iter_rows(named=True):
            title = row.get("section_title", "") or ""
            if "계열회사 현황" in title and "상세" in title:
                content = row.get("section_content", "") or ""
                if len(content) > 30:
                    affiliates = parseAffiliateList(content)
                break

        # 2. 본문에서 요약 (그룹명, 상장/비상장 수)
        summary = None
        for row in report.iter_rows(named=True):
            title = row.get("section_title", "") or ""
            if re.search(r"계열회사.*사항", title):
                content = row.get("section_content", "") or ""
                if len(content) > 30:
                    summary = parseGroupSummary(content)
                break

        if not affiliates and summary is None:
            continue

        listedCompanies = [a for a in affiliates if a["listed"]]
        unlistedCompanies = [a for a in affiliates if not a["listed"]]

        groupName = summary["groupName"] if summary else None
        listedCount = summary["listedCount"] if summary else len(listedCompanies)
        unlistedCount = summary["unlistedCount"] if summary else len(unlistedCompanies)
        totalCount = summary["totalCount"] if summary else len(affiliates)

        affiliateDf = None
        if affiliates:
            affiliateDf = pl.DataFrame(
                {
                    "name": [a["name"] for a in affiliates],
                    "listed": [a["listed"] for a in affiliates],
                },
                schema={"name": pl.Utf8, "listed": pl.Boolean},
            )

        return AffiliateGroupResult(
            corpName=corpName,
            nYears=1,
            groupName=groupName,
            listedCount=listedCount,
            unlistedCount=unlistedCount,
            totalCount=totalCount,
            affiliates=affiliates,
            affiliateDf=affiliateDf,
        )

    return None
