"""우발부채 데이터 추출 파이프라인."""

import re

import polars as pl

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.reportSelector import selectReport
from dartlab.engines.docsParser.finance.contingentLiability.parser import (
    classifyBlock,
    extractTableBlocks,
    parseGuaranteeDetail,
    parseGuaranteeSummary,
    parseLawsuit,
)
from dartlab.engines.docsParser.finance.contingentLiability.types import ContingentLiabilityResult


def contingentLiability(stockCode: str) -> ContingentLiabilityResult | None:
    """사업보고서에서 우발부채·채무보증·소송 시계열 추출.

    Args:
        stockCode: 종목코드 (6자리)

    Returns:
        ContingentLiabilityResult 또는 데이터 부족 시 None
    """
    df = loadData(stockCode)
    corpName = extractCorpName(df)
    years = sorted(df["year"].unique().to_list(), reverse=True)

    guaranteeRows: list[dict] = []
    lawsuitRows: list[dict] = []

    for year in years:
        report = selectReport(df, year, reportKind="annual")
        if report is None:
            continue

        content = _findSection(report)
        if content is None:
            continue

        blocks = extractTableBlocks(content)
        yearGuarantee = None
        yearLawsuits: list[dict] = []

        for block in blocks:
            kind = classifyBlock(block)

            if kind == "guaranteeDetail" and yearGuarantee is None:
                parsed = parseGuaranteeDetail(block)
                if parsed:
                    yearGuarantee = parsed
                    yearGuarantee["year"] = year

            elif kind == "guaranteeSummary" and yearGuarantee is None:
                parsed = parseGuaranteeSummary(block)
                if parsed:
                    yearGuarantee = parsed
                    yearGuarantee["year"] = year

            elif kind == "lawsuit":
                parsed = parseLawsuit(block)
                if parsed:
                    parsed["year"] = year
                    yearLawsuits.append(parsed)

        if yearGuarantee:
            guaranteeRows.append(yearGuarantee)
        lawsuitRows.extend(yearLawsuits)

    if not guaranteeRows and not lawsuitRows:
        return None

    guaranteeDf = _buildGuaranteeDf(guaranteeRows) if guaranteeRows else None
    lawsuitDf = _buildLawsuitDf(lawsuitRows) if lawsuitRows else None

    return ContingentLiabilityResult(
        corpName=corpName,
        nYears=max(len(guaranteeRows), len({r["year"] for r in lawsuitRows})) if lawsuitRows else len(guaranteeRows),
        guaranteeDf=guaranteeDf,
        lawsuitDf=lawsuitDf,
    )


def _findSection(report: pl.DataFrame) -> str | None:
    """우발부채 섹션 content 반환."""
    for row in report.iter_rows(named=True):
        title = row.get("section_title", "") or ""
        if re.search(r"우발부채", title):
            content = row.get("section_content", "") or ""
            if len(content) > 100:
                return content
    return None


def _buildGuaranteeDf(rows: list[dict]) -> pl.DataFrame:
    data = sorted(rows, key=lambda x: x["year"], reverse=True)
    schema = {
        "year": pl.Utf8,
        "totalGuaranteeAmount": pl.Int64,
        "lineCount": pl.Int64,
    }
    for r in data:
        for col in schema:
            if col not in r:
                r[col] = None
    return pl.DataFrame(data, schema=schema)


def _buildLawsuitDf(rows: list[dict]) -> pl.DataFrame:
    data = sorted(rows, key=lambda x: x["year"], reverse=True)
    schema = {
        "year": pl.Utf8,
        "filingDate": pl.Utf8,
        "parties": pl.Utf8,
        "description": pl.Utf8,
        "amount": pl.Utf8,
        "amountValue": pl.Int64,
        "status": pl.Utf8,
    }
    for r in data:
        for col in schema:
            if col not in r:
                r[col] = None
    return pl.DataFrame(data, schema=schema)
