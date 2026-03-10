"""자본금 변동 데이터 추출 파이프라인."""

import re

import polars as pl

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.reportSelector import selectReport
from dartlab.engines.dart.docs.finance.capitalChange.parser import (
    extractTableBlocks,
    parseCapitalChangeTable,
    parseShareTotalTable,
    parseTreasuryStockTable,
)
from dartlab.engines.dart.docs.finance.capitalChange.types import CapitalChangeResult

CAPITAL_SECTION_PATTERNS = [r"자본금\s*변동"]
SHARE_SECTION_PATTERNS = [r"주식의\s*총수"]


def capitalChange(stockCode: str) -> CapitalChangeResult | None:
    """사업보고서에서 자본금 변동·주식 총수·자기주식 시계열 추출.

    Args:
        stockCode: 종목코드 (6자리)

    Returns:
        CapitalChangeResult 또는 데이터 부족 시 None
    """
    df = loadData(stockCode)
    corpName = extractCorpName(df)
    years = sorted(df["year"].unique().to_list(), reverse=True)

    capitalRows: list[dict] = []
    shareTotalRows: list[dict] = []
    treasuryRows: list[dict] = []

    for year in years:
        report = selectReport(df, year, reportKind="annual")
        if report is None:
            continue

        # 자본금 변동사항
        capitalContent = _findSection(report, CAPITAL_SECTION_PATTERNS)
        if capitalContent:
            blocks = extractTableBlocks(capitalContent)
            for block in blocks:
                parsed = parseCapitalChangeTable(block)
                if parsed:
                    # 자본금 변동은 멀티기간 — 최신(첫 번째) 기간만 사용
                    row = {"year": int(year)}
                    for stype, prefix in [("common", "common"), ("preferred", "preferred")]:
                        data = parsed.get(stype, {})
                        if "발행주식총수" in data and data["발행주식총수"]:
                            row[f"{prefix}Shares"] = data["발행주식총수"][0]
                        if "액면금액" in data and data["액면금액"]:
                            row[f"{prefix}ParValue"] = data["액면금액"][0]
                        if "자본금" in data and data["자본금"]:
                            row[f"{prefix}Capital"] = data["자본금"][0]
                    if len(row) > 1:
                        capitalRows.append(row)
                    break

        # 주식의 총수
        shareContent = _findSection(report, SHARE_SECTION_PATTERNS)
        if shareContent:
            blocks = extractTableBlocks(shareContent)
            for block in blocks:
                blockText = " ".join(block)
                if "발행할" in blockText or "Ⅰ" in blockText:
                    parsed = parseShareTotalTable(block)
                    if parsed:
                        row = {"year": int(year), "referenceDate": parsed.get("referenceDate")}
                        for key, prefix in [
                            ("authorizedShares", "authorized"),
                            ("issuedShares", "issued"),
                            ("reducedShares", "reduced"),
                            ("outstandingShares", "outstanding"),
                        ]:
                            vals = parsed.get(key, {})
                            row[f"{prefix}Common"] = vals.get("common")
                            row[f"{prefix}Preferred"] = vals.get("preferred")
                            row[f"{prefix}Total"] = vals.get("total")
                        shareTotalRows.append(row)
                        break

            for block in blocks:
                blockText = " ".join(block)
                if "기초수량" in blockText and "기말수량" in blockText:
                    parsed = parseTreasuryStockTable(block)
                    if parsed:
                        treasuryRows.append({
                            "year": int(year),
                            "totalBegin": parsed["totalBegin"],
                            "totalEnd": parsed["totalEnd"],
                        })
                        break

    if not capitalRows and not shareTotalRows:
        return None

    capitalDf = _buildCapitalDf(capitalRows) if capitalRows else None
    shareTotalDf = _buildShareTotalDf(shareTotalRows) if shareTotalRows else None
    treasuryDf = _buildTreasuryDf(treasuryRows) if treasuryRows else None

    return CapitalChangeResult(
        corpName=corpName,
        nYears=max(len(capitalRows), len(shareTotalRows)),
        capitalDf=capitalDf,
        shareTotalDf=shareTotalDf,
        treasuryDf=treasuryDf,
    )


def _findSection(report: pl.DataFrame, patterns: list[str]) -> str | None:
    """report DataFrame에서 패턴 매칭 섹션 content 반환."""
    for row in report.iter_rows(named=True):
        title = row.get("section_title", "") or ""
        if any(re.search(p, title) for p in patterns):
            content = row.get("section_content", "") or ""
            if len(content) > 50:
                return content
    return None


def _buildCapitalDf(rows: list[dict]) -> pl.DataFrame:
    data = sorted(rows, key=lambda x: x["year"])
    schema = {
        "year": pl.Int64,
        "commonShares": pl.Int64,
        "preferredShares": pl.Int64,
        "commonParValue": pl.Int64,
        "preferredParValue": pl.Int64,
        "commonCapital": pl.Int64,
        "preferredCapital": pl.Int64,
    }
    for r in data:
        for col in schema:
            if col not in r:
                r[col] = None
    return pl.DataFrame(data, schema=schema)


def _buildShareTotalDf(rows: list[dict]) -> pl.DataFrame:
    data = sorted(rows, key=lambda x: x["year"])
    schema = {
        "year": pl.Int64,
        "referenceDate": pl.Utf8,
        "authorizedCommon": pl.Int64,
        "authorizedPreferred": pl.Int64,
        "authorizedTotal": pl.Int64,
        "issuedCommon": pl.Int64,
        "issuedPreferred": pl.Int64,
        "issuedTotal": pl.Int64,
        "reducedCommon": pl.Int64,
        "reducedPreferred": pl.Int64,
        "reducedTotal": pl.Int64,
        "outstandingCommon": pl.Int64,
        "outstandingPreferred": pl.Int64,
        "outstandingTotal": pl.Int64,
    }
    for r in data:
        for col in schema:
            if col not in r:
                r[col] = None
    return pl.DataFrame(data, schema=schema)


def _buildTreasuryDf(rows: list[dict]) -> pl.DataFrame:
    data = sorted(rows, key=lambda x: x["year"])
    schema = {
        "year": pl.Int64,
        "totalBegin": pl.Int64,
        "totalEnd": pl.Int64,
    }
    for r in data:
        for col in schema:
            if col not in r:
                r[col] = None
    return pl.DataFrame(data, schema=schema)
