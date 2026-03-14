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

from collections.abc import Iterator

import polars as pl

from dartlab.core.dataLoader import loadData
from dartlab.core.reportSelector import selectReport
from dartlab.engines.dart.docs.sections._common import (
    REPORT_KINDS,
    detectContentCol,
    sortPeriods,
)
from dartlab.engines.dart.docs.sections.chunker import parseMajorNum
from dartlab.engines.dart.docs.sections.mapper import mapSectionTitle, stripSectionPrefix
from dartlab.engines.dart.docs.sections.runtime import (
    applyProjections,
    chapterFromMajorNum,
    chapterTeacherTopics,
    detailTopicForTopic,
    projectionSuppressedTopics,
)


def iterPeriodSubsets(
    stockCode: str,
) -> Iterator[tuple[str, str, str, pl.DataFrame]]:
    """기간별 유효 섹션 subset을 순회한다.

    Yields:
        (periodKey, reportKind, contentCol, subset) 튜플.
        subset은 section_order 기준 정렬된 DataFrame.

    loadData를 1회만 호출하고, pipeline/views 양쪽이 공유한다.
    """
    df = loadData(stockCode)
    ccol = detectContentCol(df)
    years = sorted(df["year"].unique().to_list(), reverse=True)

    for year in years:
        for reportKind, suffix in REPORT_KINDS:
            periodKey = f"{year}{suffix}"
            report = selectReport(df, year, reportKind=reportKind)
            if report is None or ccol not in report.columns:
                continue
            subset = (
                report.select(["section_order", "section_title", ccol])
                .filter(
                    pl.col(ccol).is_not_null()
                    & (pl.col(ccol).str.len_chars() > 0)
                )
                .sort("section_order")
            )
            if subset.height == 0:
                continue
            yield periodKey, reportKind, ccol, subset


def _reportRowsToTopicRows(
    records: list[dict[str, object]], contentCol: str,
) -> list[dict[str, object]]:
    merged: dict[tuple[str, str], list[str]] = {}
    order: dict[tuple[str, str], tuple[int, int]] = {}
    source: dict[tuple[str, str], str] = {}
    currentMajorNum: int | None = None
    idx = 0
    # 장 제목 행은 보류했다가, 소항목이 없는 단독 장이면 등록한다.
    pendingChapter: dict[str, object] | None = None
    hasSubItems = False

    def _flushPending() -> None:
        nonlocal pendingChapter, hasSubItems, idx
        if pendingChapter is not None and not hasSubItems:
            # 소항목 없는 단독 장 — 장 제목 content를 topic으로 등록
            pTitle = str(pendingChapter.get("section_title") or "").strip()
            pContent = str(pendingChapter.get(contentCol) or "").strip()
            pMajor = parseMajorNum(pTitle)
            if pMajor is not None and pContent:
                ch = chapterFromMajorNum(pMajor)
                if ch is not None:
                    rawT = stripSectionPrefix(pTitle)
                    tp = mapSectionTitle(rawT)
                    key = (ch, tp)
                    if key not in merged:
                        merged[key] = []
                        order[key] = (pMajor, idx)
                        source[key] = rawT
                        idx += 1
                    merged[key].append(pContent)
        pendingChapter = None
        hasSubItems = False

    for record in records:
        title = str(record.get("section_title") or "").strip()
        content = str(record.get(contentCol) or "")
        if not title or not content.strip():
            continue

        majorNum = parseMajorNum(title)
        if majorNum is not None:
            # 이전 보류된 장 제목 처리
            _flushPending()
            currentMajorNum = majorNum
            pendingChapter = record
            hasSubItems = False
            continue
        if currentMajorNum is None:
            continue

        # 소항목 도달 — 장 제목 content는 중복이므로 버림
        hasSubItems = True

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

    # 마지막 장 처리
    _flushPending()

    result: list[dict[str, object]] = []
    for (chapter, topic), texts in merged.items():
        majorNum, seq = order[(chapter, topic)]
        result.append(
            {
                "chapter": chapter,
                "topic": topic,
                "text": "\n".join(texts),
                "majorNum": majorNum,
                "orderSeq": seq,
                "sourceTopic": source[(chapter, topic)],
            }
        )
    return result


def sections(stockCode: str) -> pl.DataFrame | None:
    """전 기간 보고서 섹션 텍스트 — topic × period DataFrame.

    Args:
        stockCode: 종목코드

    Returns:
        topic(행) × period(열) DataFrame. 값은 텍스트(str).
        데이터 없으면 None.
    """
    topicMap: dict[str, dict[str, str]] = {}
    topicOrder: dict[str, tuple[int, int]] = {}
    periodRows: dict[str, list[dict[str, object]]] = {}
    validPeriods: list[str] = []
    latestAnnualRows: list[dict[str, object]] | None = None
    suppressed = projectionSuppressedTopics()

    for periodKey, reportKind, ccol, subset in iterPeriodSubsets(stockCode):
        validPeriods.append(periodKey)
        topicRows = _reportRowsToTopicRows(subset.to_dicts(), ccol)
        periodRows[periodKey] = topicRows
        if reportKind == "annual" and latestAnnualRows is None:
            latestAnnualRows = topicRows

    teacherTopics = chapterTeacherTopics(latestAnnualRows or [])
    validPeriods = sortPeriods(validPeriods)

    topicChapter: dict[str, str] = {}

    for periodKey in validPeriods:
        projected = applyProjections(
            periodRows.get(periodKey, []), teacherTopics,
        )
        for row in projected:
            chapter = row["chapter"]
            topic = row["topic"]
            text = row["text"]
            if not isinstance(chapter, str) or not isinstance(topic, str) or not isinstance(text, str):
                continue
            if topic not in topicChapter:
                topicChapter[topic] = chapter
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

    dfRows: list[dict[str, str | None]] = []
    for topic in sortedTopics:
        row: dict[str, str | None] = {
            "chapter": topicChapter.get(topic),
            "topic": topic,
        }
        for period in validPeriods:
            row[period] = topicMap[topic].get(period)
        dfRows.append(row)

    remaining = set(topicMap.keys()) - set(topicOrder.keys())
    for topic in sorted(remaining):
        row: dict[str, str | None] = {
            "chapter": topicChapter.get(topic),
            "topic": topic,
        }
        for period in validPeriods:
            row[period] = topicMap[topic].get(period)
        dfRows.append(row)

    return pl.DataFrame(dfRows)
