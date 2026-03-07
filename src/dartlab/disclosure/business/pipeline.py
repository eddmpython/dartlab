"""사업의 내용 데이터 추출 파이프라인."""

import polars as pl

from dartlab.core.dataLoader import loadData, extractCorpName
from dartlab.core.reportSelector import selectReport, extractReportYear
from dartlab.disclosure.business.parser import (
    extractFromSubSections,
    extractFromUnified,
    computeChanges,
)
from dartlab.disclosure.business.types import (
    BusinessSection,
    BusinessChange,
    BusinessResult,
)


def business(stockCode: str) -> BusinessResult | None:
    """사업보고서에서 사업의 내용 섹션 추출 + 연도별 변경 탐지.

    Args:
        stockCode: 종목코드 (6자리)

    Returns:
        BusinessResult 또는 데이터 부족 시 None
    """
    df = loadData(stockCode)
    corpName = extractCorpName(df)

    years = sorted(df["year"].unique().to_list(), reverse=True)

    latestSections: dict[str, dict] | None = None
    latestYear: int | None = None

    for year in years:
        report = selectReport(df, year, reportKind="annual")
        if report is None:
            continue

        reportYear = extractReportYear(report["report_type"][0])
        if reportYear is None:
            continue

        sections = extractFromSubSections(report)
        if not sections:
            sections = extractFromUnified(report)

        if sections and latestSections is None:
            latestSections = sections
            latestYear = reportYear
            break

    if not latestSections or latestYear is None:
        return None

    sectionList = [
        BusinessSection(
            key=key,
            title=info["title"],
            chars=info["chars"],
            text=info["text"],
        )
        for key, info in latestSections.items()
    ]

    allYears = sorted(df["year"].unique().to_list())
    rawChanges = computeChanges(df, allYears)
    changeList = [
        BusinessChange(
            year=c["year"],
            changedPct=c["changedPct"],
            added=c["added"],
            removed=c["removed"],
            totalChars=c["totalChars"],
        )
        for c in rawChanges
    ]

    return BusinessResult(
        corpName=corpName,
        year=latestYear,
        sections=sectionList,
        changes=changeList,
    )
