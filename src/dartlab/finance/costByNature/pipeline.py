"""비용의 성격별 분류 데이터 추출 파이프라인."""

import re

import polars as pl

from dartlab.core.dataLoader import loadData, extractCorpName
from dartlab.core.reportSelector import selectReport
from dartlab.core.notesExtractor import extractNotesContent
from dartlab.finance.costByNature.parser import (
    findCostByNatureSection,
    parseCostByNature,
    normalizeAccountName,
    isTotalRow,
)
from dartlab.finance.costByNature.types import CostByNatureResult

PERIOD_KINDS = {
    "y": ["annual"],
    "q": ["Q1", "semi", "Q3", "annual"],
    "h": ["semi", "annual"],
}


def costByNature(stockCode: str, period: str = "y") -> CostByNatureResult | None:
    """연결재무제표 주석에서 비용의 성격별 분류 시계열 추출.

    Args:
        stockCode: 종목코드 (6자리)
        period: "y" (연간) | "q" (분기) | "h" (반기)

    Returns:
        CostByNatureResult 또는 데이터 부족 시 None
    """
    df = loadData(stockCode)
    corpName = extractCorpName(df)

    years = sorted(df["year"].unique().to_list(), reverse=True)
    reportKinds = PERIOD_KINDS.get(period, ["annual"])

    yearData: dict[str, dict[str, float | None]] = {}
    prevData: dict[str, dict[str, float | None]] = {}
    allAccounts: list[str] = []

    for year in years:
      for reportKind in reportKinds:
        report = selectReport(df, year, reportKind=reportKind)
        if report is None:
            continue

        notes = extractNotesContent(report)
        if not notes:
            continue

        section = findCostByNatureSection(notes)
        if section is None:
            continue

        result = parseCostByNature(section)
        if result is None:
            continue

        periodKey = _extractPeriodKey(report["report_type"][0], reportKind)
        if periodKey is None:
            continue

        if periodKey in yearData:
            continue

        danggi: dict[str, float | None] = {}
        jeongi: dict[str, float | None] = {}
        order: list[str] = []

        for rawName in result["order"]:
            if isTotalRow(rawName):
                continue
            stdName = normalizeAccountName(rawName)

            if stdName in danggi:
                continue

            dVal = result["당기"].get(rawName)
            jVal = result["전기"].get(rawName)

            danggi[stdName] = dVal
            jeongi[stdName] = jVal

            if stdName not in order:
                order.append(stdName)

        if danggi:
            yearData[periodKey] = danggi
            for n in order:
                if n not in allAccounts:
                    allAccounts.append(n)
        if jeongi:
            prevData[periodKey] = jeongi

    if not yearData:
        return None

    sortedYears = sorted(yearData.keys(), reverse=True)

    crossCheck: dict[str, dict[str, int]] = {}
    for yr in sortedYears:
        if yr not in prevData:
            continue
        if not re.match(r"^\d{4}$", yr):
            continue
        prevYear = str(int(yr) - 1)
        if prevYear not in yearData:
            continue
        matches = mismatches = 0
        for name, pv in prevData[yr].items():
            av = yearData[prevYear].get(name)
            if pv is not None and av is not None:
                if abs(pv - av) < 1:
                    matches += 1
                else:
                    mismatches += 1
        crossCheck[yr] = {"matches": matches, "mismatches": mismatches}

    rows = []
    for name in allAccounts:
        row: dict = {"account": name}
        for yr in sortedYears:
            row[yr] = yearData[yr].get(name)
        rows.append(row)

    if not rows:
        return None

    schema: dict = {"account": pl.Utf8}
    for yr in sortedYears:
        schema[yr] = pl.Float64

    ts = pl.DataFrame(rows, schema=schema)

    ratios = _buildRatios(ts, sortedYears)

    return CostByNatureResult(
        corpName=corpName,
        nYears=len(sortedYears),
        timeSeries=ts,
        crossCheck=crossCheck,
        ratios=ratios,
    )


def _buildRatios(ts: pl.DataFrame, years: list[str]) -> pl.DataFrame | None:
    """각 비용 항목의 합계 대비 비율(%) 계산."""
    if ts is None or ts.height == 0:
        return None

    rows = []
    for yr in years:
        col = ts[yr].to_list()
        total = sum(v for v in col if v is not None and v > 0)
        if total <= 0:
            continue

        accounts = ts["account"].to_list()
        for i, name in enumerate(accounts):
            val = col[i]
            ratio = (val / total * 100) if val is not None else None
            rows.append({"year": yr, "account": name, "amount": val, "ratio": ratio})

    if not rows:
        return None

    return pl.DataFrame(rows)


def _extractPeriodKey(reportType: str, reportKind: str) -> str | None:
    """보고서 유형에서 기간 키 추출.

    annual → "2024", Q1 → "2024Q1", semi → "2024H1", Q3 → "2024Q3"
    """
    m = re.search(r"\((\d{4})\.\d{2}\)", reportType)
    if not m:
        return None
    year = m.group(1)
    if reportKind == "annual":
        return year
    if reportKind == "Q1":
        return f"{year}Q1"
    if reportKind == "semi":
        return f"{year}H1"
    if reportKind == "Q3":
        return f"{year}Q3"
    return year
