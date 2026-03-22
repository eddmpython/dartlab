"""임원 현황 데이터 추출 파이프라인."""

import re

import polars as pl

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.reportSelector import selectReport
from dartlab.engines.company.dart.docs.finance.executive.parser import (
    aggregateExecutives,
    classifyBlock,
    extractTableBlocks,
    parseExecutiveBlock,
    parseUnregisteredPayBlock,
)
from dartlab.engines.company.dart.docs.finance.executive.types import ExecutiveResult

EXECUTIVE_SECTION_PATTERNS = [
    r"임원.*직원.*현황",
    r"임원.*현황",
]


def executive(stockCode: str) -> ExecutiveResult | None:
    """사업보고서에서 임원 현황 시계열 추출.

    등기임원 집계(사내/사외/기타, 상근/비상근, 성별) + 미등기임원 보수 시계열.

    Args:
        stockCode: 종목코드 (6자리)

    Returns:
        ExecutiveResult 또는 데이터 부족 시 None
    """
    df = loadData(stockCode)
    corpName = extractCorpName(df)
    years = sorted(df["year"].unique().to_list(), reverse=True)

    execRows: list[dict] = []
    payRows: list[dict] = []

    for year in years:
        content = _findExecutiveSection(df, year)
        if content is None:
            continue

        blocks = extractTableBlocks(content)

        # 등기임원
        for block in blocks:
            if classifyBlock(block) == "executive":
                executives = parseExecutiveBlock(block)
                if executives:
                    stats = aggregateExecutives(executives)
                    stats["year"] = int(year)
                    execRows.append(stats)
                break

        # 미등기임원 보수
        for block in blocks:
            if classifyBlock(block) == "unregisteredPay":
                pay = parseUnregisteredPayBlock(block)
                if pay:
                    pay["year"] = int(year)
                    payRows.append(pay)
                break

    if not execRows and not payRows:
        return None

    execRows = _dedup(execRows)
    payRows = _dedup(payRows)

    executiveDf = _buildExecutiveDf(execRows) if execRows else None
    unregPayDf = _buildUnregPayDf(payRows) if payRows else None

    nYears = max(len(execRows), len(payRows))

    return ExecutiveResult(
        corpName=corpName,
        nYears=nYears,
        executiveDf=executiveDf,
        unregPayDf=unregPayDf,
    )


def _findExecutiveSection(df: pl.DataFrame, year: str) -> str | None:
    """임원 현황 섹션의 content 반환. 소분류 우선."""
    report = selectReport(df, year, reportKind="annual")
    if report is None:
        return None

    candidates = []
    for row in report.iter_rows(named=True):
        title = row.get("section_title", "") or ""
        if any(re.search(p, title) for p in EXECUTIVE_SECTION_PATTERNS):
            isSub = not title.startswith(("V", "VI", "VII", "VIII", "IX"))
            candidates.append(
                {
                    "content": row.get("section_content", "") or "",
                    "isSub": isSub,
                }
            )

    if not candidates:
        return None

    sub = [c for c in candidates if c["isSub"]]
    if sub:
        return sub[0]["content"]
    return candidates[0]["content"]


def _dedup(rows: list[dict]) -> list[dict]:
    """연도별 중복 제거 (최신 우선)."""
    seen: set[int] = set()
    result = []
    for r in rows:
        if r["year"] not in seen:
            seen.add(r["year"])
            result.append(r)
    return result


def _buildExecutiveDf(rows: list[dict]) -> pl.DataFrame:
    data = []
    for r in sorted(rows, key=lambda x: x["year"]):
        data.append(
            {
                "year": r["year"],
                "totalRegistered": r["totalRegistered"],
                "insideDirectors": r["insideDirectors"],
                "outsideDirectors": r["outsideDirectors"],
                "otherNonexec": r["otherNonexec"],
                "fullTimeCount": r["fullTimeCount"],
                "partTimeCount": r["partTimeCount"],
                "maleCount": r["maleCount"],
                "femaleCount": r["femaleCount"],
            }
        )
    return pl.DataFrame(data)


def _buildUnregPayDf(rows: list[dict]) -> pl.DataFrame:
    data = []
    for r in sorted(rows, key=lambda x: x["year"]):
        data.append(
            {
                "year": r["year"],
                "headcount": r["headcount"],
                "totalSalary": r["totalSalary"],
                "avgSalary": r["avgSalary"],
            }
        )
    schema = {
        "year": pl.Int64,
        "headcount": pl.Int64,
        "totalSalary": pl.Float64,
        "avgSalary": pl.Float64,
    }
    return pl.DataFrame(data, schema=schema)
