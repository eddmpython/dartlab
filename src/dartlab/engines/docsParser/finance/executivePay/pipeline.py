"""임원 보수 데이터 추출 파이프라인."""

import re

import polars as pl

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.reportSelector import selectReport
from dartlab.engines.docsParser.finance.executivePay.parser import (
    classifyBlock,
    extractTableBlocks,
    parsePayByTypeBlock,
    parsePayIndividualBlock,
)
from dartlab.engines.docsParser.finance.executivePay.types import ExecutivePayResult

PAY_SECTION_PATTERNS = [
    r"임원의\s*보수",
    r"임원.*보수.*등",
]

EXEC_SECTION_PATTERNS = [
    r"임원.*직원.*에\s*관한",
]


def executivePay(stockCode: str) -> ExecutivePayResult | None:
    """사업보고서에서 임원 보수 시계열 추출.

    유형별(등기이사/사외이사/감사위원) 보수 + 5억 초과 개인별 보수.

    Args:
        stockCode: 종목코드 (6자리)

    Returns:
        ExecutivePayResult 또는 데이터 부족 시 None
    """
    df = loadData(stockCode)
    corpName = extractCorpName(df)
    years = sorted(df["year"].unique().to_list(), reverse=True)

    typeRows: list[dict] = []
    topPayRows: list[dict] = []

    for year in years:
        content = _findPaySection(df, year)
        if content is None:
            continue

        blocks = extractTableBlocks(content)

        # 유형별 보수
        for block in blocks:
            if classifyBlock(block) == "payByType":
                parsed = parsePayByTypeBlock(block)
                if parsed:
                    for item in parsed:
                        item["year"] = year
                        typeRows.append(item)
                break

        # 5억 초과 개인별
        for block in blocks:
            if classifyBlock(block) == "payIndividual":
                parsed = parsePayIndividualBlock(block)
                if parsed:
                    for item in parsed:
                        item["year"] = year
                        topPayRows.append(item)
                break

    if not typeRows and not topPayRows:
        return None

    payByTypeDf = _buildPayByTypeDf(typeRows) if typeRows else None
    topPayDf = _buildTopPayDf(topPayRows) if topPayRows else None

    nYears = len({r["year"] for r in typeRows}) if typeRows else len({r["year"] for r in topPayRows})

    return ExecutivePayResult(
        corpName=corpName,
        nYears=nYears,
        payByTypeDf=payByTypeDf,
        topPayDf=topPayDf,
    )


def _findPaySection(df: pl.DataFrame, year: str) -> str | None:
    """임원 보수 섹션 content 반환."""
    report = selectReport(df, year, reportKind="annual")
    if report is None:
        return None

    # 소분류 우선
    for row in report.iter_rows(named=True):
        title = row.get("section_title", "") or ""
        if any(re.search(p, title) for p in PAY_SECTION_PATTERNS):
            content = row.get("section_content", "") or ""
            if len(content) > 100:
                return content

    # 대분류 fallback
    for row in report.iter_rows(named=True):
        title = row.get("section_title", "") or ""
        if any(re.search(p, title) for p in EXEC_SECTION_PATTERNS):
            content = row.get("section_content", "") or ""
            if len(content) > 100:
                return content

    return None


def _buildPayByTypeDf(rows: list[dict]) -> pl.DataFrame:
    data = []
    for r in sorted(rows, key=lambda x: (x["year"], x["category"]), reverse=True):
        data.append({
            "year": r["year"],
            "category": r["category"],
            "headcount": r["headcount"],
            "totalPay": r["totalPay"],
            "avgPay": r["avgPay"],
        })
    schema = {
        "year": pl.Utf8,
        "category": pl.Utf8,
        "headcount": pl.Int64,
        "totalPay": pl.Float64,
        "avgPay": pl.Float64,
    }
    return pl.DataFrame(data, schema=schema)


def _buildTopPayDf(rows: list[dict]) -> pl.DataFrame:
    data = []
    for r in sorted(rows, key=lambda x: (x["year"], -(x["totalPay"] or 0)), reverse=True):
        data.append({
            "year": r["year"],
            "name": r["name"],
            "position": r["position"],
            "totalPay": r["totalPay"],
        })
    schema = {
        "year": pl.Utf8,
        "name": pl.Utf8,
        "position": pl.Utf8,
        "totalPay": pl.Float64,
    }
    return pl.DataFrame(data, schema=schema)
