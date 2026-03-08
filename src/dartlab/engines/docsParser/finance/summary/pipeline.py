import re

import polars as pl

from dartlab.core.dataLoader import PERIOD_KINDS, extractCorpName, loadData
from dartlab.core.reportSelector import parsePeriodKey, selectReport
from dartlab.core.tableParser import extractAccounts
from dartlab.engines.docsParser.finance.summary.bridgeMatcher import numberBridgeMatch, periodToIndex
from dartlab.engines.docsParser.finance.summary.contentExtractor import extractSummaryContent
from dartlab.engines.docsParser.finance.summary.segmentation import detectBreakpoints
from dartlab.engines.docsParser.finance.summary.types import AnalysisResult, YearAccounts


def loadYearData(
    df: pl.DataFrame,
    period: str = "y",
) -> dict[str, YearAccounts]:
    """parquet DataFrame → {periodKey: YearAccounts} 딕셔너리.

    Args:
        df: 전체 DataFrame
        period: "y" | "q" | "h"
    """
    kinds = PERIOD_KINDS.get(period, PERIOD_KINDS["y"])
    yearData: dict[str, YearAccounts] = {}
    years = sorted(df["year"].unique().to_list(), reverse=True)

    for year in years:
        for kind in kinds:
            report = selectReport(df, year, reportKind=kind)
            if report is None:
                continue

            content = extractSummaryContent(report)
            if content is None:
                continue

            accounts, order = extractAccounts(content)
            if not accounts:
                continue

            if period == "y":
                key = year
            else:
                # report_type에서 실제 결산기 파싱
                reportType = report["report_type"][0]
                key = parsePeriodKey(reportType)
                if key is None:
                    continue
            yearData[key] = YearAccounts(year=key, accounts=accounts, order=order)

    return yearData


def _sortPeriodKeys(keys: list[str]) -> list[str]:
    """period key 목록을 최신 → 과거 순으로 정렬."""
    return sorted(keys, key=periodToIndex, reverse=True)


def _extractYear(periodKey: str) -> int:
    """period key에서 연도 추출. "2024Q1" → 2024, "2024" → 2024."""
    return int(periodKey[:4])


def fsSummary(
    stockCode: str,
    ifrsOnly: bool = True,
    period: str = "y",
) -> AnalysisResult | None:
    """단일 기업 분석: 기간별 매칭률, 전환점 탐지, 구간 분리.

    Args:
        stockCode: 종목코드 (6자리)
        ifrsOnly: True면 K-IFRS 이후(2011~)만 분석
        period: "y" | "q" | "h"

    Returns:
        AnalysisResult 또는 데이터 부족 시 None
    """
    df = loadData(stockCode)
    corpName = extractCorpName(df)

    yearData = loadYearData(df, period=period)

    if len(yearData) < 2:
        return None

    sortedYears = _sortPeriodKeys(list(yearData.keys()))

    if ifrsOnly:
        sortedYears = [y for y in sortedYears if _extractYear(y) >= 2011]
        if len(sortedYears) < 2:
            return None

    pairResults = []
    for i in range(len(sortedYears) - 1):
        curYear = sortedYears[i]
        prevYear = sortedYears[i + 1]
        accCur = yearData[curYear].accounts
        accPrev = yearData[prevYear].accounts

        result = numberBridgeMatch(accCur, accPrev, curYear=curYear, prevYear=prevYear)
        pairResults.append(result)

    segments, breakpoints = detectBreakpoints(pairResults, sortedYears)

    contPairs = [p for p in pairResults if p.yearGap == 1]
    contMatched = sum(p.matched for p in contPairs)
    contTotal = sum(p.total for p in contPairs)
    contRate = contMatched / contTotal if contTotal > 0 else None

    allMatched = sum(p.matched for p in pairResults)
    allTotal = sum(p.total for p in pairResults)
    allRate = allMatched / allTotal if allTotal > 0 else None

    analysisResult = AnalysisResult(
        corpName=corpName,
        nYears=len(sortedYears),
        nPairs=len(pairResults),
        nBreakpoints=len(breakpoints),
        nSegments=len(segments),
        allRate=allRate,
        allMatched=allMatched,
        allTotal=allTotal,
        contRate=contRate,
        contMatched=contMatched,
        contTotal=contTotal,
        segments=segments,
        breakpoints=breakpoints,
        pairResults=pairResults,
        yearAccounts=yearData,
        period=period,
    )

    if period == "y":
        analysisResult.FS = _buildDataFrameBridge(sortedYears, yearData, pairResults, segments)
    else:
        analysisResult.FS = _buildDataFrameDirect(sortedYears, yearData)

    analysisResult.BS, analysisResult.IS = _splitBsIs(analysisResult.FS)
    return analysisResult


def _buildDataFrameBridge(
    sortedYears: list[str],
    yearData: dict[str, YearAccounts],
    pairResults: list,
    segments: list,
) -> pl.DataFrame:
    """bridge matching 기반 DataFrame. 연간 시계열용.

    최신 연도 계정명을 기준으로, pairs 체인을 따라가며 과거 연도의
    당기(idx=0) 금액을 수집한다. 구간(segment)별로 독립 처리.
    """
    nameChains: dict[str, dict[str, float | None]] = {}
    accountOrder: list[str] = []

    yearIndexMap = {y: periodToIndex(y) for y in sortedYears}

    for seg in segments:
        if seg.nYears < 1:
            continue

        startIdx = periodToIndex(seg.startYear)
        endIdx = periodToIndex(seg.endYear)

        segYears = []
        for y in sortedYears:
            idx = yearIndexMap[y]
            if seg.nYears == 1:
                if y == seg.startYear:
                    segYears.append(y)
            else:
                if startIdx >= idx >= endIdx:
                    segYears.append(y)

        if not segYears:
            continue

        latestYear = segYears[0]
        if latestYear not in yearData:
            continue

        latestAccounts = yearData[latestYear]
        for name in latestAccounts.order:
            if name not in nameChains:
                nameChains[name] = {}
                accountOrder.append(name)
            amt = latestAccounts.accounts[name][0] if latestAccounts.accounts[name] else None
            nameChains[name][latestYear] = amt

        curNames = {name: name for name in latestAccounts.order}

        for pr in pairResults:
            if pr.curYear not in segYears or pr.prevYear not in segYears:
                continue

            nextNames: dict[str, str] = {}
            for baseName, curName in curNames.items():
                if curName in pr.pairs:
                    prevName = pr.pairs[curName]
                    nextNames[baseName] = prevName

                    if prevName in yearData[pr.prevYear].accounts:
                        prevAmts = yearData[pr.prevYear].accounts[prevName]
                        amt = prevAmts[0] if prevAmts else None
                        nameChains[baseName][pr.prevYear] = amt

            curNames = nextNames

    return _toDataFrame(accountOrder, nameChains, sortedYears)


def _buildDataFrameDirect(
    sortedYears: list[str],
    yearData: dict[str, YearAccounts],
) -> pl.DataFrame:
    """계정명 직접 매칭 기반 DataFrame. 분기/반기 시계열용.

    최신 기간의 계정명을 기준으로, 동일 계정명의 당기(idx=0)를 수집.
    DART 분기보고서는 전기=전년연말이므로 bridge matching 대신 사용.
    """
    nameData: dict[str, dict[str, float | None]] = {}
    accountOrder: list[str] = []

    latestYear = sortedYears[0]
    if latestYear in yearData:
        for name in yearData[latestYear].order:
            if name not in nameData:
                nameData[name] = {}
                accountOrder.append(name)

    for periodKey in sortedYears:
        if periodKey not in yearData:
            continue
        ya = yearData[periodKey]
        for name, amts in ya.accounts.items():
            if name not in nameData:
                nameData[name] = {}
                accountOrder.append(name)
            nameData[name][periodKey] = amts[0] if amts else None

    return _toDataFrame(accountOrder, nameData, sortedYears)


def _splitBsIs(df: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    """전체 DataFrame을 재무상태표(BS)와 손익계산서(IS)로 분리.

    자본총계/자본합계 행을 경계로 그 행까지가 BS, 그 이후가 IS.
    """
    if df.is_empty() or "계정명" not in df.columns:
        return df, pl.DataFrame()

    names = df["계정명"].to_list()
    splitIdx = len(names)

    for i, name in enumerate(names):
        norm = re.sub(r"[\s·ㆍ\u3000]", "", name)
        if "자본총계" in norm or "자본합계" in norm:
            splitIdx = i + 1
            break

    bs = df.head(splitIdx)
    is_ = df.slice(splitIdx)
    return bs, is_


def _toDataFrame(
    accountOrder: list[str],
    nameData: dict[str, dict[str, float | None]],
    sortedYears: list[str],
) -> pl.DataFrame:
    """계정명 × 기간 딕셔너리 → polars DataFrame."""
    rows = []
    for name in accountOrder:
        row: dict[str, object] = {"계정명": name}
        for year in sortedYears:
            row[year] = nameData[name].get(year)
        rows.append(row)

    if not rows:
        return pl.DataFrame()

    schema = {"계정명": pl.Utf8}
    for year in sortedYears:
        schema[year] = pl.Float64
    return pl.DataFrame(rows, schema=schema)
