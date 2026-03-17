"""사업보고서/분기보고서/반기보고서 섹션 청킹 파이프라인.

Company에서 호출되는 진입점.
기간별 섹션 청크를 생성하여 수평 비교 가능하게 한다.

period key 형식:
- "2024"   → 사업보고서 (연간)
- "2024Q1" → 1분기보고서
- "2024Q2" → 반기보고서
- "2024Q3" → 3분기보고서

반환 형식:
    (topic, blockType, blockOrder)(행) × period(열) DataFrame
    ┌──────────────┬───────────┬────────────┬────────┬──────────┬────────┐
    │ topic        │ blockType │ blockOrder │ 2025   │ 2025Q3   │ 2024   │
    ├──────────────┼───────────┼────────────┼────────┼──────────┼────────┤
    │ 사업의 개요  │ text      │ 0          │ 텍스트 │ 텍스트   │ 텍스트 │
    │ 사업의 개요  │ table     │ 1          │ 테이블 │ null     │ 테이블 │
    │ 사업의 개요  │ text      │ 2          │ 텍스트 │ null     │ 텍스트 │
    └──────────────┴───────────┴────────────┴────────┴──────────┴────────┘
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
    *,
    sinceYear: int = 2016,
) -> Iterator[tuple[str, str, str, pl.DataFrame]]:
    """기간별 유효 섹션 subset을 순회한다.

    Yields:
        (periodKey, reportKind, contentCol, subset) 튜플.
        subset은 section_order 기준 정렬된 DataFrame.

    loadData를 1회만 호출하고, pipeline/views 양쪽이 공유한다.
    sinceYear 이전 기간은 건너뛴다 (finance 없는 기간 제외).
    """
    df = loadData(stockCode)
    ccol = detectContentCol(df)
    years = sorted(df["year"].unique().to_list(), reverse=True)

    for year in years:
        if isinstance(year, str) and year.isdigit() and int(year) < sinceYear:
            continue
        if isinstance(year, (int, float)) and int(year) < sinceYear:
            continue
        for reportKind, suffix in REPORT_KINDS:
            periodKey = f"{year}{suffix}"
            report = selectReport(df, year, reportKind=reportKind)
            if report is None or ccol not in report.columns:
                continue
            subset = (
                report.select(["section_order", "section_title", ccol])
                .filter(pl.col(ccol).is_not_null() & (pl.col(ccol).str.len_chars() > 0))
                .sort("section_order")
            )
            if subset.height == 0:
                continue
            yield periodKey, reportKind, ccol, subset


def _splitContentBlocks(content: str) -> list[tuple[str, str]]:
    """content를 원문 순서대로 text/table block으로 분해."""
    rows: list[tuple[str, str]] = []
    textBuffer: list[str] = []
    tableBuffer: list[str] = []

    def _flushText() -> None:
        nonlocal textBuffer
        text = "\n".join(textBuffer).strip()
        if text:
            rows.append(("text", text))
        textBuffer = []

    def _flushTable() -> None:
        nonlocal tableBuffer
        text = "\n".join(tableBuffer).strip()
        if text:
            rows.append(("table", text))
        tableBuffer = []

    for raw in content.splitlines():
        stripped = raw.strip()
        if not stripped:
            _flushTable()
            if textBuffer:
                textBuffer.append("")
            continue
        if stripped.startswith("|"):
            _flushText()
            tableBuffer.append(stripped)
            continue
        _flushTable()
        textBuffer.append(stripped)

    _flushText()
    _flushTable()
    return rows


def _reportRowsToTopicRows(
    records: list[dict[str, object]],
    contentCol: str,
) -> list[dict[str, object]]:
    emitted: list[dict[str, object]] = []
    topicBlockCounts: dict[tuple[str, str], int] = {}
    currentMajorNum: int | None = None
    idx = 0
    # 장 제목 행은 보류했다가, 소항목이 없는 단독 장이면 등록한다.
    pendingChapter: dict[str, object] | None = None
    hasSubItems = False

    def _registerContent(ch: str, tp: str, rawT: str, content: str, majorNum: int) -> None:
        nonlocal idx
        topicKey = (ch, tp)
        nextBlockOrder = topicBlockCounts.get(topicKey, 0)
        for blockType, blockText in _splitContentBlocks(content):
            emitted.append(
                {
                    "chapter": ch,
                    "topic": tp,
                    "blockType": blockType,
                    "blockOrder": nextBlockOrder,
                    "text": blockText,
                    "majorNum": majorNum,
                    "orderSeq": idx,
                    "sourceTopic": rawT,
                }
            )
            nextBlockOrder += 1
            idx += 1
        topicBlockCounts[topicKey] = nextBlockOrder

    def _flushPending() -> None:
        nonlocal pendingChapter, hasSubItems
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
                    _registerContent(ch, tp, rawT, pContent, pMajor)
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
        _registerContent(chapter, topic, rawTitle, content.strip(), currentMajorNum)

    # 마지막 장 처리
    _flushPending()

    return emitted


def sections(stockCode: str) -> pl.DataFrame | None:
    """전 기간 보고서 섹션 — (topic, blockType, blockOrder) × period DataFrame.

    텍스트와 테이블을 분리하여 같은 topic이라도 text 행과 table 행으로 나뉜다.

    Args:
        stockCode: 종목코드

    Returns:
        (topic, blockType, blockOrder)(행) × period(열) DataFrame. 값은 텍스트(str).
        데이터 없으면 None.
    """
    # key: (topic, blockType, blockOrder)
    topicMap: dict[tuple[str, str, int], dict[str, str]] = {}
    topicOrder: dict[tuple[str, str, int], tuple[int, int]] = {}
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
            periodRows.get(periodKey, []),
            teacherTopics,
        )
        for row in projected:
            chapter = row["chapter"]
            topic = row["topic"]
            text = row["text"]
            blockType = row.get("blockType", "text")
            blockOrder = row.get("blockOrder", 0)
            if not isinstance(chapter, str) or not isinstance(topic, str) or not isinstance(text, str):
                continue
            if not isinstance(blockType, str):
                blockType = "text"
            if not isinstance(blockOrder, int):
                blockOrder = int(blockOrder)
            if topic not in topicChapter:
                topicChapter[topic] = chapter
            if topic in suppressed.get(chapter, set()):
                continue
            if detailTopicForTopic(topic) is not None:
                continue
            key = (topic, blockType, blockOrder)
            if key not in topicMap:
                topicMap[key] = {}
            topicMap[key][periodKey] = text
            if key not in topicOrder:
                majorNum = int(row.get("majorNum", 99))
                seq = int(row.get("orderSeq", 999999))
                topicOrder[key] = (majorNum, seq)

    if not validPeriods or not topicMap:
        return None

    # topic 그룹핑: 같은 topic의 블록이 반드시 연속하도록 정렬
    # (majorNum, topic_first_seq) → topic 순서, 그 안에서 blockOrder
    topicFirstSeq: dict[str, tuple[int, int]] = {}
    for key, (majorNum, seq) in topicOrder.items():
        topic = key[0]
        if topic not in topicFirstSeq or (majorNum, seq) < topicFirstSeq[topic]:
            topicFirstSeq[topic] = (majorNum, seq)

    # topic 내 안정 순서를 위해 topic별 고유 인덱스 부여
    topicIndex: dict[str, int] = {}
    for topic_seq in sorted(topicFirstSeq.items(), key=lambda x: x[1]):
        topicIndex[topic_seq[0]] = len(topicIndex)

    def _sortKey(k: tuple[str, str, int]) -> tuple[int, int, int, int]:
        topic, _blockType, blockOrder = k
        majorNum, firstSeq = topicFirstSeq.get(topic, (99, 999999))
        tIdx = topicIndex.get(topic, 999999)
        return (majorNum, firstSeq, tIdx, blockOrder)

    sortedKeys = sorted(topicOrder.keys(), key=_sortKey)

    dfRows: list[dict[str, str | None]] = []
    for key in sortedKeys:
        topic, blockType, blockOrder = key
        row: dict[str, str | None] = {
            "chapter": topicChapter.get(topic),
            "topic": topic,
            "blockType": blockType,
            "blockOrder": blockOrder,
        }
        for period in validPeriods:
            row[period] = topicMap[key].get(period)
        dfRows.append(row)

    remaining = set(topicMap.keys()) - set(topicOrder.keys())
    for key in sorted(remaining):
        topic, blockType, blockOrder = key
        row: dict[str, str | None] = {
            "chapter": topicChapter.get(topic),
            "topic": topic,
            "blockType": blockType,
            "blockOrder": blockOrder,
        }
        for period in validPeriods:
            row[period] = topicMap[key].get(period)
        dfRows.append(row)

    schema = {"chapter": pl.Utf8, "topic": pl.Utf8, "blockType": pl.Utf8, "blockOrder": pl.Int64}
    for p in validPeriods:
        schema[p] = pl.Utf8
    return pl.DataFrame(dfRows, schema=schema)
