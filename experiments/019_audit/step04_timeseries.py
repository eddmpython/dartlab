"""
실험 ID: 019-04
실험명: 감사 시계열 DataFrame 생성

목적:
- step03 파서 결과를 연도별 시계열 DataFrame으로 변환
- 각 연도 사업보고서에서 당기 데이터만 추출하여 연도 인덱스로 정렬

가설:
1. 감사의견: year | auditor | opinion | keyAuditMatters (연결감사보고서 우선)
2. 감사보수: year | auditor | contractFee | contractHours | actualFee | actualHours (백만원)

방법:
1. 연도별 parseAuditData 호출
2. 당기 데이터만 선택
3. 연결감사보고서 우선 (없으면 감사보고서)
4. DataFrame 생성

결과 (실험 후 작성):

결론:

실험일: 2026-03-07
"""
import os
import re
import sys

import polars as pl

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.reportSelector import selectReport

DATA_DIR = r"C:\Users\MSI\OneDrive\Desktop\sideProject\nicegui\eddmpython\data\dartData\docsData"

sys.path.insert(0, os.path.dirname(__file__))
from step03_parser import (
    _dedup,
    classifyBlock,
    extractTableBlocks,
    findAuditSections,
    fiscalPeriodToYear,
    parseFeeBlock,
    parseOpinionBlock,
)


def buildAuditTimeSeries(stockCode: str) -> dict | None:
    """감사 시계열 생성.

    Returns:
        {
            "corpName": str,
            "nYears": int,
            "opinionDf": pl.DataFrame,  # year | auditor | opinion | keyAuditMatters
            "feeDf": pl.DataFrame,      # year | auditor | contractFee | contractHours | actualFee | actualHours
        }
    """
    df = loadData(stockCode)
    corpName = extractCorpName(df)
    years = sorted(df["year"].unique().to_list(), reverse=True)

    opinionRows = []
    feeRows = []

    for year in years:
        sections = findAuditSections(df, year)
        if not sections:
            continue

        allOpinions = []
        allFees = []

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

    opinionRows = _dedup(opinionRows, ["year"])
    feeRows = _dedup(feeRows, ["year"])

    opinionDf = _buildOpinionDf(opinionRows) if opinionRows else None
    feeDf = _buildFeeDf(feeRows) if feeRows else None

    return {
        "corpName": corpName,
        "nYears": max(len(opinionRows), len(feeRows)),
        "opinionDf": opinionDf,
        "feeDf": feeDf,
    }


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


def _normalizeOpinion(raw: str) -> str:
    """감사의견 정규화."""
    if not raw:
        return ""
    raw = raw.strip()
    if raw in ("적정의견", "적정"):
        return "적정"
    if "한정" in raw:
        return "한정"
    if "부적정" in raw:
        return "부적정"
    if "의견거절" in raw:
        return "의견거절"
    return raw


def _buildOpinionDf(rows: list[dict]) -> pl.DataFrame:
    """감사의견 시계열 DataFrame."""
    data = []
    for r in sorted(rows, key=lambda x: x["year"], reverse=True):
        data.append({
            "year": r["year"],
            "auditor": r["auditor"],
            "opinion": _normalizeOpinion(r["opinion"]),
            "keyAuditMatters": r.get("keyAuditMatters", ""),
        })
    return pl.DataFrame(data)


def _buildFeeDf(rows: list[dict]) -> pl.DataFrame:
    """감사보수 시계열 DataFrame."""
    data = []
    for r in sorted(rows, key=lambda x: x["year"], reverse=True):
        data.append({
            "year": r["year"],
            "auditor": r["auditor"],
            "contractFee": r["contractFee"],
            "contractHours": r["contractHours"],
            "actualFee": r["actualFee"],
            "actualHours": r["actualHours"],
        })
    schema = {
        "year": pl.Utf8,
        "auditor": pl.Utf8,
        "contractFee": pl.Float64,
        "contractHours": pl.Float64,
        "actualFee": pl.Float64,
        "actualHours": pl.Float64,
    }
    return pl.DataFrame(data, schema=schema)


if __name__ == "__main__":
    targets = [
        ("005930", "삼성전자"),
        ("005380", "현대자동차"),
        ("000660", "SK하이닉스"),
        ("035720", "카카오"),
    ]

    for code, name in targets:
        print(f"\n{'='*60}")
        print(f"{name} ({code})")
        print(f"{'='*60}")

        result = buildAuditTimeSeries(code)
        if result is None:
            print("  결과 없음")
            continue

        print(f"  {result['corpName']} — {result['nYears']}년")

        if result["opinionDf"] is not None:
            print("\n  [감사의견 시계열]")
            print(result["opinionDf"])

        if result["feeDf"] is not None:
            print("\n  [감사보수 시계열]")
            print(result["feeDf"])
