"""사업의 내용 데이터 추출 파이프라인."""

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.reportSelector import extractReportYear, selectReport
from dartlab.providers.dart.docs.disclosure.business.parser import (
    computeChanges,
    extractFromSubSections,
    extractFromUnified,
)
from dartlab.providers.dart.docs.disclosure.business.types import (
    BusinessChange,
    BusinessResult,
    BusinessSection,
)


def business(stockCode: str) -> BusinessResult | None:
    """사업보고서에서 사업의 내용 섹션 추출 + 연도별 변경 탐지.

    모든 연도의 섹션 텍스트를 수집하여 yearSections에 저장.
    LLM이 연도별 텍스트 변화를 비교 분석할 수 있도록 한다.

    Args:
        stockCode: 종목코드 (6자리)

    Returns:
        BusinessResult 또는 데이터 부족 시 None
    """
    df = loadData(stockCode)
    corpName = extractCorpName(df)

    years = sorted(df["year"].unique().to_list(), reverse=True)

    allSections: dict[int, list[BusinessSection]] = {}
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

        if sections and reportYear not in allSections:
            sectionList = [
                BusinessSection(
                    key=key,
                    title=info["title"],
                    chars=info["chars"],
                    text=info["text"],
                )
                for key, info in sections.items()
            ]
            allSections[reportYear] = sectionList
            if latestYear is None:
                latestYear = reportYear

    if not allSections or latestYear is None:
        return None

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
        sections=allSections[latestYear],
        changes=changeList,
        yearSections=allSections,
    )
