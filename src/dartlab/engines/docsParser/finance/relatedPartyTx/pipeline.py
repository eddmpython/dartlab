"""대주주 거래 데이터 추출 파이프라인."""

import re

import polars as pl

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.reportSelector import selectReport
from dartlab.engines.docsParser.finance.relatedPartyTx.parser import (
    classifyBlock,
    extractTableBlocks,
    parseGuaranteeBlock,
    parseRevenueTxBlock,
)
from dartlab.engines.docsParser.finance.relatedPartyTx.types import RelatedPartyTxResult


def relatedPartyTx(stockCode: str) -> RelatedPartyTxResult | None:
    """사업보고서에서 대주주 거래 시계열 추출.

    Args:
        stockCode: 종목코드 (6자리)

    Returns:
        RelatedPartyTxResult 또는 데이터 부족 시 None
    """
    df = loadData(stockCode)
    corpName = extractCorpName(df)
    years = sorted(df["year"].unique().to_list(), reverse=True)

    guaranteeRows: list[dict] = []
    revenueTxRows: list[dict] = []

    for year in years:
        report = selectReport(df, year, reportKind="annual")
        if report is None:
            continue

        content = _findSection(report)
        if content is None:
            continue

        blocks = extractTableBlocks(content)
        yearHasGuarantee = False
        yearHasRevenue = False

        for block in blocks:
            kind = classifyBlock(block)

            if kind == "guarantee" and not yearHasGuarantee:
                entries = parseGuaranteeBlock(block)
                for e in entries:
                    e["year"] = year
                    guaranteeRows.append(e)
                if entries:
                    yearHasGuarantee = True

            elif kind == "revenueTx" and not yearHasRevenue:
                entries = parseRevenueTxBlock(block)
                for e in entries:
                    e["year"] = year
                    revenueTxRows.append(e)
                if entries:
                    yearHasRevenue = True

    if not guaranteeRows and not revenueTxRows:
        return None

    guaranteeDf = _buildGuaranteeDf(guaranteeRows) if guaranteeRows else None
    revenueTxDf = _buildRevenueTxDf(revenueTxRows) if revenueTxRows else None

    yearSet = {r["year"] for r in guaranteeRows} | {r["year"] for r in revenueTxRows}

    return RelatedPartyTxResult(
        corpName=corpName,
        nYears=len(yearSet),
        guaranteeDf=guaranteeDf,
        revenueTxDf=revenueTxDf,
    )


def _findSection(report: pl.DataFrame) -> str | None:
    """대주주 거래 섹션 content 반환."""
    for row in report.iter_rows(named=True):
        title = row.get("section_title", "") or ""
        if re.search(r"대주주.*거래|특수관계", title):
            content = row.get("section_content", "") or ""
            if len(content) > 100:
                return content
    return None


def _buildGuaranteeDf(rows: list[dict]) -> pl.DataFrame:
    data = sorted(rows, key=lambda x: x["year"], reverse=True)
    schema = {
        "year": pl.Utf8,
        "entity": pl.Utf8,
        "amount": pl.Int64,
    }
    for r in data:
        for col in schema:
            if col not in r:
                r[col] = None
    return pl.DataFrame(data, schema=schema)


def _buildRevenueTxDf(rows: list[dict]) -> pl.DataFrame:
    data = sorted(rows, key=lambda x: x["year"], reverse=True)
    schema = {
        "year": pl.Utf8,
        "entity": pl.Utf8,
        "sales": pl.Int64,
        "purchases": pl.Int64,
    }
    for r in data:
        for col in schema:
            if col not in r:
                r[col] = None
    return pl.DataFrame(data, schema=schema)
