"""최대주주 데이터 추출 파이프라인."""

import polars as pl

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.reportSelector import extractReportYear, selectReport
from dartlab.providers.dart.docs.finance.majorHolder.parser import (
    parseBigHolders,
    parseMajorHolderTable,
    parseMinority,
    parseVoting,
)
from dartlab.providers.dart.docs.finance.majorHolder.types import (
    BigHolder,
    Holder,
    HolderOverview,
    MajorHolderResult,
    Minority,
    VotingRights,
)


def majorHolder(stockCode: str) -> MajorHolderResult | None:
    """사업보고서에서 최대주주 현황 추출.

    Args:
        stockCode: 종목코드 (6자리)

    Returns:
        MajorHolderResult 또는 데이터 부족 시 None
    """
    df = loadData(stockCode)
    corpName = extractCorpName(df)

    years = sorted(df["year"].unique().to_list(), reverse=True)

    yearData: dict[int, dict] = {}

    for year in years:
        report = selectReport(df, year, reportKind="annual")
        if report is None:
            continue

        holderRows = report.filter(pl.col("section_title").str.contains("주주"))
        if holderRows.height == 0:
            continue

        reportYear = extractReportYear(holderRows["report_type"][0])
        if reportYear is None:
            continue

        parsed = None
        for i in range(holderRows.height):
            content = holderRows["section_content"][i]
            if "최대주주" not in content and "주식소유" not in content:
                continue
            p = parseMajorHolderTable(content)
            if p["majorHolder"]:
                parsed = p
                break

        if parsed is None:
            continue

        if reportYear not in yearData:
            yearData[reportYear] = parsed

    if not yearData:
        return None

    latestYear = max(yearData.keys())
    latest = yearData[latestYear]

    holders = [
        Holder(
            name=h["name"],
            relation=h["relation"],
            stockType=h["stockType"],
            sharesStart=h.get("sharesStart"),
            ratioStart=h.get("ratioStart"),
            sharesEnd=h.get("sharesEnd"),
            ratioEnd=h.get("ratioEnd"),
        )
        for h in latest["holders"]
    ]

    records = []
    for yr in sorted(yearData.keys()):
        d = yearData[yr]
        records.append(
            {
                "year": yr,
                "majorHolder": d.get("majorHolder"),
                "majorRatio": d.get("majorRatio"),
                "totalRatio": d.get("totalRatio"),
                "holderCount": len(d.get("holders", [])),
            }
        )

    ts = pl.DataFrame(records)

    return MajorHolderResult(
        corpName=corpName,
        nYears=ts.height,
        majorHolder=latest["majorHolder"],
        majorRatio=latest["majorRatio"],
        totalRatio=latest["totalRatio"],
        holders=holders,
        timeSeries=ts,
    )


def holderOverview(stockCode: str) -> HolderOverview | None:
    """주주 종합 현황: 5% 이상 주주, 소액주주, 의결권 현황.

    Args:
        stockCode: 종목코드 (6자리)

    Returns:
        HolderOverview 또는 데이터 부족 시 None
    """
    df = loadData(stockCode)
    if df is None:
        return None
    corpName = extractCorpName(df)

    years = sorted(df["year"].unique().to_list(), reverse=True)
    if not years:
        return None
    report = selectReport(df, years[0], reportKind="annual")
    if report is None:
        return None

    reportYear = extractReportYear(report["report_type"][0])

    holderSections = report.filter(pl.col("section_title").str.contains("주주에 관한 사항"))
    totalSections = report.filter(pl.col("section_title").str.contains("주주총회"))

    fiveResult = None
    minResult = None
    for i in range(holderSections.height):
        content = holderSections["section_content"][i]
        if fiveResult is None:
            fiveResult = parseBigHolders(content)
        if minResult is None:
            minResult = parseMinority(content)

    votResult = None
    for i in range(totalSections.height):
        content = totalSections["section_content"][i]
        if votResult is None:
            votResult = parseVoting(content)

    if fiveResult is None and minResult is None and votResult is None:
        return None

    big = [BigHolder(name=h["name"], shares=h.get("shares"), ratio=h.get("ratio")) for h in (fiveResult or [])]

    min_ = None
    if minResult:
        min_ = Minority(**minResult)

    vot = None
    if votResult:
        vot = VotingRights(**{k: votResult.get(k) for k in VotingRights.__dataclass_fields__})

    return HolderOverview(
        corpName=corpName,
        year=reportYear,
        bigHolders=big,
        minority=min_,
        voting=vot,
    )
