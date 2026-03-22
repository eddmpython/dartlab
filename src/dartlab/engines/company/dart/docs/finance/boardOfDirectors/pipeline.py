"""이사회 데이터 추출 파이프라인."""

import re

import polars as pl

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.reportSelector import selectReport
from dartlab.engines.company.dart.docs.finance.boardOfDirectors.parser import (
    classifyBlock,
    extractTableBlocks,
    parseBoardMeeting,
    parseCommittee,
    parseDirectorCount,
    parseDirectorCountFromText,
)
from dartlab.engines.company.dart.docs.finance.boardOfDirectors.types import BoardResult

BOARD_SECTION_PATTERNS = [
    r"이사회에\s*관한\s*사항",
]

BOARD_PARENT_PATTERNS = [
    r"이사회\s*등\s*회사의\s*기관",
]


def boardOfDirectors(stockCode: str) -> BoardResult | None:
    """사업보고서에서 이사회 시계열 추출.

    이사 수, 사외이사 수, 이사회 개최횟수, 출석률, 위원회 구성.

    Args:
        stockCode: 종목코드 (6자리)

    Returns:
        BoardResult 또는 데이터 부족 시 None
    """
    df = loadData(stockCode)
    corpName = extractCorpName(df)
    years = sorted(df["year"].unique().to_list(), reverse=True)

    rows: list[dict] = []
    committeeRows: list[dict] = []

    for year in years:
        content = _findBoardSection(df, year)
        if content is None:
            continue

        blocks = extractTableBlocks(content)

        directorCount = None
        meeting = None
        committees = []

        for block in blocks:
            kind = classifyBlock(block)
            if kind == "directorCount" and directorCount is None:
                directorCount = parseDirectorCount(block)
            elif kind == "boardMeeting" and meeting is None:
                meeting = parseBoardMeeting(block)
            elif kind == "committee" and not committees:
                committees = parseCommittee(block)

        # fallback: 이사 수 직접 탐색
        if directorCount is None:
            directorCount = parseDirectorCountFromText(content)

        row = {"year": int(year)}

        if directorCount:
            row["totalDirectors"] = directorCount.get("totalDirectors")
            row["outsideDirectors"] = directorCount.get("outsideDirectors")

        if meeting:
            row["meetingCount"] = meeting.get("meetingCount")
            rates = meeting.get("attendanceRates", {})
            if rates:
                row["avgAttendanceRate"] = round(sum(rates.values()) / len(rates), 1)

        if row.keys() > {"year"}:
            rows.append(row)

        for comm in committees:
            committeeRows.append(
                {
                    "year": int(year),
                    "committeeName": comm["name"],
                    "composition": comm["composition"],
                    "members": comm["members"],
                }
            )

    if not rows and not committeeRows:
        return None

    boardDf = _buildBoardDf(rows) if rows else None
    committeeDf = _buildCommitteeDf(committeeRows) if committeeRows else None

    return BoardResult(
        corpName=corpName,
        nYears=len(rows),
        boardDf=boardDf,
        committeeDf=committeeDf,
    )


def _findBoardSection(df: pl.DataFrame, year: str) -> str | None:
    """이사회 섹션 content 반환."""
    report = selectReport(df, year, reportKind="annual")
    if report is None:
        return None

    for row in report.iter_rows(named=True):
        title = row.get("section_title", "") or ""
        if any(re.search(p, title) for p in BOARD_SECTION_PATTERNS):
            content = row.get("section_content", "") or ""
            if len(content) > 100:
                return content

    for row in report.iter_rows(named=True):
        title = row.get("section_title", "") or ""
        if any(re.search(p, title) for p in BOARD_PARENT_PATTERNS):
            content = row.get("section_content", "") or ""
            if len(content) > 100:
                return content

    return None


def _buildBoardDf(rows: list[dict]) -> pl.DataFrame:
    data = sorted(rows, key=lambda x: x["year"])
    schema = {
        "year": pl.Int64,
        "totalDirectors": pl.Int64,
        "outsideDirectors": pl.Int64,
        "meetingCount": pl.Int64,
        "avgAttendanceRate": pl.Float64,
    }
    for r in data:
        for col in schema:
            if col not in r:
                r[col] = None
    return pl.DataFrame(data, schema=schema)


def _buildCommitteeDf(rows: list[dict]) -> pl.DataFrame:
    data = sorted(rows, key=lambda x: (x["year"], x["committeeName"]))
    schema = {
        "year": pl.Int64,
        "committeeName": pl.Utf8,
        "composition": pl.Utf8,
        "members": pl.Utf8,
    }
    return pl.DataFrame(data, schema=schema)
