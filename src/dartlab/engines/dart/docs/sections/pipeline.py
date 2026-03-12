"""사업보고서/분기보고서/반기보고서 섹션 청킹 파이프라인.

Company에서 호출되는 진입점.
기간별 섹션 청크를 생성하여 수평 비교 가능하게 한다.

period key 형식:
- "2024"   → 사업보고서 (연간)
- "2024Q1" → 1분기보고서
- "2024Q2" → 반기보고서
- "2024Q3" → 3분기보고서

반환 형식:
    topic(행) × period(열) DataFrame
    ┌──────────────┬────────┬──────────┬────────┐
    │ topic        │ 2025   │ 2025Q3   │ 2024   │
    ├──────────────┼────────┼──────────┼────────┤
    │ 사업의 개요  │ 텍스트 │ 텍스트   │ 텍스트 │
    │ 영업실적     │ 텍스트 │ null     │ 텍스트 │
    └──────────────┴────────┴──────────┴────────┘
"""

from __future__ import annotations

import polars as pl

from dartlab.core.dataLoader import loadData
from dartlab.core.reportSelector import selectReport
from dartlab.engines.dart.docs.sections.chunker import parseMajorNum
from dartlab.engines.dart.docs.sections.mapper import mapSectionTitle, stripSectionPrefix
from dartlab.engines.dart.docs.sections.runtime import (
    applyProjections,
    chapterFromMajorNum,
    chapterTeacherTopics,
    detailTopicForTopic,
    projectionSuppressedTopics,
)
from dartlab.engines.dart.docs.sections.views import sortPeriods

_REPORT_KINDS = [
    ("annual", ""),
    ("Q1", "Q1"),
    ("semi", "Q2"),
    ("Q3", "Q3"),
]

def _getContentCol(df: pl.DataFrame) -> str:
    if "section_content" in df.columns:
        return "section_content"
    return "content"


def _reportRowsToTopicRows(rows: list[dict[str, object]], contentCol: str) -> list[dict[str, object]]:
    merged: dict[tuple[str, str], list[str]] = {}
    order: dict[tuple[str, str], tuple[int, int]] = {}
    source: dict[tuple[str, str], str] = {}
    currentMajorNum: int | None = None
    idx = 0

    for record in rows:
        title = str(record.get("section_title") or "").strip()
        content = str(record.get(contentCol) or "")
        if not title or not content.strip():
            continue

        majorNum = parseMajorNum(title)
        if majorNum is not None:
            currentMajorNum = majorNum
        if currentMajorNum is None:
            continue

        chapter = chapterFromMajorNum(currentMajorNum)
        if chapter is None:
            continue

        rawTitle = stripSectionPrefix(title)
        topic = mapSectionTitle(rawTitle)
        key = (chapter, topic)
        if key not in merged:
            merged[key] = []
            order[key] = (currentMajorNum, idx)
            source[key] = rawTitle
            idx += 1
        merged[key].append(content.strip())

    rows: list[dict[str, object]] = []
    for (chapter, topic), texts in merged.items():
        majorNum, seq = order[(chapter, topic)]
        rows.append(
            {
                "chapter": chapter,
                "topic": topic,
                "text": "\n".join(texts),
                "majorNum": majorNum,
                "orderSeq": seq,
                "sourceTopic": source[(chapter, topic)],
            }
        )
    return rows


def sections(stockCode: str) -> pl.DataFrame | None:
    """전 기간 보고서 섹션 텍스트 — topic × period DataFrame.

    Args:
        stockCode: 종목코드

    Returns:
        topic(행) × period(열) DataFrame. 값은 텍스트(str).
        데이터 없으면 None.
    """
    df = loadData(stockCode)
    contentCol = _getContentCol(df)

    years = sorted(df["year"].unique().to_list(), reverse=True)

    topicMap: dict[str, dict[str, str]] = {}
    topicOrder: dict[str, tuple[int, int]] = {}
    periodRows: dict[str, list[dict[str, object]]] = {}
    validPeriods: list[str] = []
    latestAnnualRows: list[dict[str, object]] | None = None
    suppressed = projectionSuppressedTopics()

    for year in years:
        for reportKind, suffix in _REPORT_KINDS:
            periodKey = f"{year}{suffix}"
            report = selectReport(df, year, reportKind=reportKind)
            if report is None or contentCol not in report.columns:
                continue
            subset = (
                report.select(["section_order", "section_title", contentCol])
                .filter(pl.col(contentCol).is_not_null() & (pl.col(contentCol).str.len_chars() > 0))
                .sort("section_order")
            )
            if subset.height == 0:
                continue
            validPeriods.append(periodKey)
            rows = _reportRowsToTopicRows(subset.to_dicts(), contentCol)
            periodRows[periodKey] = rows
            if reportKind == "annual" and latestAnnualRows is None:
                latestAnnualRows = rows

    teacherTopics = chapterTeacherTopics(latestAnnualRows or [])
    validPeriods = sortPeriods(validPeriods)

    for periodKey in validPeriods:
        rows = applyProjections(periodRows.get(periodKey, []), teacherTopics)
        for row in rows:
            chapter = row["chapter"]
            topic = row["topic"]
            text = row["text"]
            if not isinstance(chapter, str) or not isinstance(topic, str) or not isinstance(text, str):
                continue
            if topic in suppressed.get(chapter, set()):
                continue
            if detailTopicForTopic(topic) is not None:
                continue
            if topic not in topicMap:
                topicMap[topic] = {}
            topicMap[topic][periodKey] = text
            if topic not in topicOrder:
                majorNum = int(row.get("majorNum", 99))
                seq = int(row.get("orderSeq", 999999))
                topicOrder[topic] = (majorNum, seq)

    if not validPeriods or not topicMap:
        return None

    sortedTopics = sorted(topicOrder.keys(), key=lambda t: topicOrder[t])

    rows: list[dict] = []
    for topic in sortedTopics:
        row: dict[str, str | None] = {"topic": topic}
        for period in validPeriods:
            row[period] = topicMap[topic].get(period)
        rows.append(row)

    remaining = set(topicMap.keys()) - set(topicOrder.keys())
    for topic in sorted(remaining):
        row = {"topic": topic}
        for period in validPeriods:
            row[period] = topicMap[topic].get(period)
        rows.append(row)

    return pl.DataFrame(rows)
