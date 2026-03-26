"""감사의견 파이프라인."""

from __future__ import annotations

import polars as pl

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.providers.dart.docs.finance.audit.parser import (
    classifyBlock,
    dedup,
    extractTableBlocks,
    findAuditSections,
    fiscalPeriodToYear,
    normalizeOpinion,
    parseFeeBlock,
    parseOpinionBlock,
)
from dartlab.providers.dart.docs.finance.audit.types import AuditResult


def audit(stockCode: str) -> AuditResult | None:
    """감사의견 + 감사보수 시계열 추출.

    Args:
        stockCode: 종목코드 (6자리).

    Returns:
        AuditResult 또는 데이터 부족 시 None.
    """
    df = loadData(stockCode)
    corpName = extractCorpName(df)
    years = sorted(df["year"].unique().to_list(), reverse=True)

    opinionRows: list[dict] = []
    feeRows: list[dict] = []

    for year in years:
        sections = findAuditSections(df, year)
        if not sections:
            continue

        allOpinions: list[dict] = []
        allFees: list[dict] = []

        for content in sections:
            blocks = extractTableBlocks(content)
            for block in blocks:
                kind = classifyBlock(block)
                if kind == "opinion":
                    parsed = parseOpinionBlock(block)
                    allOpinions.extend(parsed)
                elif kind == "fee":
                    parsed = parseFeeBlock(block)
                    allFees.extend(parsed)

        allPeriods = list({op["fiscalPeriod"] for op in allOpinions})
        allPeriods.extend(fee["fiscalPeriod"] for fee in allFees)
        allPeriods = list(set(allPeriods))

        for op in allOpinions:
            op["year"] = fiscalPeriodToYear(op["fiscalPeriod"], year, allPeriods)
        for fee in allFees:
            fee["year"] = fiscalPeriodToYear(fee["fiscalPeriod"], year, allPeriods)

        currentOpinion = _pickCurrentOpinion(allOpinions, year)
        if currentOpinion:
            opinionRows.append(currentOpinion)

        currentFee = _pickCurrentFee(allFees, year)
        if currentFee:
            feeRows.append(currentFee)

    if not opinionRows and not feeRows:
        return None

    opinionRows = dedup(opinionRows, ["year"])
    feeRows = dedup(feeRows, ["year"])

    opinionDf = _buildOpinionDf(opinionRows) if opinionRows else None
    feeDf = _buildFeeDf(feeRows) if feeRows else None

    return AuditResult(
        corpName=corpName,
        nYears=max(len(opinionRows), len(feeRows)),
        opinionDf=opinionDf,
        feeDf=feeDf,
    )


def _pickCurrentOpinion(opinions: list[dict], baseYear: str) -> dict | None:
    """당기 감사의견 선택. 연결감사보고서 > 감사보고서 > 단일."""
    currentOps = [op for op in opinions if op.get("year") == baseYear]
    if not currentOps:
        return None

    for reportType in ["연결감사보고서", "감사보고서", ""]:
        for op in currentOps:
            if op["reportType"] == reportType:
                if op["opinion"] and op["opinion"] not in ("-", "감사"):
                    return {
                        "year": baseYear,
                        "auditor": op["auditor"],
                        "opinion": op["opinion"],
                        "keyAuditMatters": op.get("keyAuditMatters", ""),
                        "goingConcern": op.get("goingConcern", ""),
                        "emphasis": op.get("emphasis", ""),
                    }

    first = currentOps[0]
    return {
        "year": baseYear,
        "auditor": first["auditor"],
        "opinion": first["opinion"],
        "keyAuditMatters": first.get("keyAuditMatters", ""),
        "goingConcern": first.get("goingConcern", ""),
        "emphasis": first.get("emphasis", ""),
    }


def _pickCurrentFee(fees: list[dict], baseYear: str) -> dict | None:
    """당기 감사보수 선택."""
    currentFees = [f for f in fees if f.get("year") == baseYear]
    if not currentFees:
        return None

    best = currentFees[0]
    for f in currentFees:
        if f["contractFee"] is not None:
            best = f
            break

    return {
        "year": baseYear,
        "auditor": best["auditor"],
        "contractFee": best["contractFee"],
        "contractHours": best["contractHours"],
        "actualFee": best["actualFee"],
        "actualHours": best["actualHours"],
    }


def _buildOpinionDf(rows: list[dict]) -> pl.DataFrame:
    """감사의견 시계열 DataFrame."""
    data = []
    for r in sorted(rows, key=lambda x: int(x["year"])):
        data.append(
            {
                "year": int(r["year"]),
                "auditor": r["auditor"],
                "opinion": normalizeOpinion(r["opinion"]),
                "keyAuditMatters": r.get("keyAuditMatters", ""),
            }
        )
    return pl.DataFrame(data)


def _buildFeeDf(rows: list[dict]) -> pl.DataFrame:
    """감사보수 시계열 DataFrame."""
    data = []
    for r in sorted(rows, key=lambda x: int(x["year"])):
        data.append(
            {
                "year": int(r["year"]),
                "auditor": r["auditor"],
                "contractFee": r["contractFee"],
                "contractHours": r["contractHours"],
                "actualFee": r["actualFee"],
                "actualHours": r["actualHours"],
            }
        )
    schema = {
        "year": pl.Int64,
        "auditor": pl.Utf8,
        "contractFee": pl.Float64,
        "contractHours": pl.Float64,
        "actualFee": pl.Float64,
        "actualHours": pl.Float64,
    }
    return pl.DataFrame(data, schema=schema)
