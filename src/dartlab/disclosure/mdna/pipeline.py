"""이사의 경영진단 및 분석의견(MD&A) 데이터 추출 파이프라인."""

import polars as pl

from dartlab.core.dataLoader import loadData, extractCorpName
from dartlab.core.reportSelector import selectReport, extractReportYear
from dartlab.disclosure.mdna.parser import parseMdna, extractOverview, classifySection
from dartlab.disclosure.mdna.types import MdnaSection, MdnaResult


def mdna(stockCode: str) -> MdnaResult | None:
    """사업보고서에서 이사의 경영진단 및 분석의견(MD&A) 추출.

    Args:
        stockCode: 종목코드 (6자리)

    Returns:
        MdnaResult 또는 데이터 부족 시 None
    """
    df = loadData(stockCode)
    corpName = extractCorpName(df)

    years = sorted(df["year"].unique().to_list(), reverse=True)

    yearSections: dict[int, dict[str, str]] = {}

    for year in years:
        report = selectReport(df, year, reportKind="annual")
        if report is None:
            continue

        mdnaRows = report.filter(
            pl.col("section_title").str.contains("경영진단")
        )
        if mdnaRows.height == 0:
            continue

        reportYear = extractReportYear(mdnaRows["report_type"][0])
        if reportYear is None:
            continue

        content = mdnaRows["section_content"][0]
        sections = parseMdna(content)

        if sections and reportYear not in yearSections:
            yearSections[reportYear] = sections

    if not yearSections:
        return None

    latestYear = max(yearSections.keys())
    latestSections = yearSections[latestYear]

    sectionList = []
    for title, content in latestSections.items():
        category = classifySection(title)
        textLines = [l for l in content.split("\n") if l.strip() and not l.strip().startswith("|")]
        tableLines = [l for l in content.split("\n") if l.strip().startswith("|")]
        sectionList.append(
            MdnaSection(
                title=title,
                category=category,
                text=content,
                textLines=len(textLines),
                tableLines=len(tableLines),
            )
        )

    overview = extractOverview(latestSections)

    return MdnaResult(
        corpName=corpName,
        nYears=len(yearSections),
        sections=sectionList,
        overview=overview,
    )
