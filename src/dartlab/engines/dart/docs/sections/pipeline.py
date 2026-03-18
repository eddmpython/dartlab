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
from dartlab.engines.dart.docs.sections.textStructure import parseTextStructureWithState


def _periodSortKey(period: str) -> tuple[int, int]:
    year = int(period[:4])
    if period.endswith("Q1"):
        return (year, 1)
    if period.endswith("Q2"):
        return (year, 2)
    if period.endswith("Q3"):
        return (year, 3)
    return (year, 4)


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
                    "sourceBlockOrder": nextBlockOrder,
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


def _expandStructuredRows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    expanded: list[dict[str, object]] = []
    headingStateByTopic: dict[str, list[dict[str, object]]] = {}

    orderedRows = sorted(
        rows,
        key=lambda r: (
            int(r.get("majorNum") or 99),
            int(r.get("orderSeq") or 999999),
            int(r.get("sourceBlockOrder") or r.get("blockOrder") or 0),
        ),
    )

    for row in orderedRows:
        blockType = str(row.get("blockType") or "text")
        topic = str(row.get("topic") or "")
        sourceBlockOrder = int(row.get("sourceBlockOrder") or row.get("blockOrder") or 0)
        orderSeq = int(row.get("orderSeq") or 0)
        baseRow = dict(row)
        baseRow["sourceBlockOrder"] = sourceBlockOrder

        if blockType != "text":
            baseRow["textNodeType"] = None
            baseRow["textStructural"] = None
            baseRow["textLevel"] = None
            baseRow["textPath"] = None
            baseRow["textPathKey"] = None
            baseRow["textParentPathKey"] = None
            baseRow["textSemanticPathKey"] = None
            baseRow["textSemanticParentPathKey"] = None
            baseRow["segmentOrder"] = 0
            baseRow["segmentKeyBase"] = f"table|sb:{sourceBlockOrder}"
            baseRow["segmentOccurrence"] = 1
            baseRow["sortOrder"] = orderSeq * 1000
            expanded.append(baseRow)
            continue

        text = str(row.get("text") or "").strip()
        initialHeadings = headingStateByTopic.get(topic, [])
        nodes, finalHeadings = parseTextStructureWithState(
            text,
            sourceBlockOrder=sourceBlockOrder,
            topic=topic,
            initialHeadings=initialHeadings,
        )
        headingStateByTopic[topic] = finalHeadings
        if not nodes:
            baseRow["textNodeType"] = "body"
            baseRow["textStructural"] = True
            if finalHeadings:
                pathLabels = [str(item["label"]) for item in finalHeadings]
                pathKeys = [str(item["key"]) for item in finalHeadings if str(item["key"])]
                semanticPathKeys = [str(item["semanticKey"]) for item in finalHeadings if str(item["semanticKey"])]
                textLevel = int(finalHeadings[-1]["level"])
                textPath = " > ".join(pathLabels) if pathLabels else None
                textPathKey = " > ".join(pathKeys) if pathKeys else None
                textParentPathKey = " > ".join(pathKeys[:-1]) if len(pathKeys) > 1 else None
                textSemanticPathKey = " > ".join(semanticPathKeys) if semanticPathKeys else None
                textSemanticParentPathKey = " > ".join(semanticPathKeys[:-1]) if len(semanticPathKeys) > 1 else None
                segmentKeyBase = (
                    f"body|p:{textSemanticPathKey}" if textSemanticPathKey else f"body|lv:{textLevel}|a:empty"
                )
            else:
                textLevel = 0
                textPath = None
                textPathKey = None
                textParentPathKey = None
                textSemanticPathKey = None
                textSemanticParentPathKey = None
                segmentKeyBase = "body|lv:0|a:empty"
            baseRow["textLevel"] = textLevel
            baseRow["textPath"] = textPath
            baseRow["textPathKey"] = textPathKey
            baseRow["textParentPathKey"] = textParentPathKey
            baseRow["textSemanticPathKey"] = textSemanticPathKey
            baseRow["textSemanticParentPathKey"] = textSemanticParentPathKey
            baseRow["segmentOrder"] = 0
            baseRow["segmentKeyBase"] = segmentKeyBase
            baseRow["segmentOccurrence"] = 1
            baseRow["sortOrder"] = orderSeq * 1000
            expanded.append(baseRow)
            continue

        for node in nodes:
            nodeRow = dict(baseRow)
            nodeRow["text"] = str(node["text"])
            nodeRow["textNodeType"] = node["textNodeType"]
            nodeRow["textStructural"] = bool(node.get("textStructural", True))
            nodeRow["textLevel"] = node["textLevel"]
            nodeRow["textPath"] = node["textPath"]
            nodeRow["textPathKey"] = node["textPathKey"]
            nodeRow["textParentPathKey"] = node["textParentPathKey"]
            nodeRow["textSemanticPathKey"] = node.get("textSemanticPathKey")
            nodeRow["textSemanticParentPathKey"] = node.get("textSemanticParentPathKey")
            nodeRow["segmentOrder"] = node["segmentOrder"]
            nodeRow["segmentKeyBase"] = node["segmentKeyBase"]
            nodeRow["segmentOccurrence"] = 1
            nodeRow["sortOrder"] = (orderSeq * 1000) + int(node["segmentOrder"])
            expanded.append(nodeRow)

    occurrenceCount: dict[tuple[str, str], int] = {}
    for row in sorted(expanded, key=lambda r: (str(r.get("topic") or ""), int(r.get("sortOrder") or 0))):
        topic = str(row.get("topic") or "")
        baseKey = str(row.get("segmentKeyBase") or "")
        occKey = (topic, baseKey)
        occurrenceCount[occKey] = occurrenceCount.get(occKey, 0) + 1
        occ = occurrenceCount[occKey]
        row["segmentOccurrence"] = occ
        row["segmentKey"] = f"{baseKey}|occ:{occ}"

    return expanded


def _periodCadence(period: str) -> str:
    if period.endswith("Q1"):
        return "q1"
    if period.endswith("Q2"):
        return "q2"
    if period.endswith("Q3"):
        return "q3"
    return "annual"


def _cadenceSortKey(cadence: str) -> int:
    return {"annual": 0, "q1": 1, "q2": 2, "q3": 3}.get(cadence, 9)


def _rowCadenceMeta(periodMap: dict[str, str]) -> dict[str, object]:
    presentPeriods = [period for period, value in periodMap.items() if isinstance(value, str) and value.strip()]
    if not presentPeriods:
        return {
            "cadenceKey": "none",
            "cadenceScope": "none",
            "annualPeriodCount": 0,
            "quarterlyPeriodCount": 0,
            "latestAnnualPeriod": None,
            "latestQuarterlyPeriod": None,
        }

    cadenceKeys = sorted({_periodCadence(period) for period in presentPeriods}, key=_cadenceSortKey)
    annualPeriods = [period for period in presentPeriods if _periodCadence(period) == "annual"]
    quarterlyPeriods = [period for period in presentPeriods if _periodCadence(period) != "annual"]
    hasAnnual = bool(annualPeriods)
    hasQuarterly = bool(quarterlyPeriods)
    if hasAnnual and hasQuarterly:
        cadenceScope = "mixed"
    elif hasAnnual:
        cadenceScope = "annual"
    else:
        cadenceScope = "quarterly"

    latestAnnual = max(annualPeriods, key=_periodSortKey) if annualPeriods else None
    latestQuarterly = max(quarterlyPeriods, key=_periodSortKey) if quarterlyPeriods else None

    return {
        "cadenceKey": ",".join(cadenceKeys),
        "cadenceScope": cadenceScope,
        "annualPeriodCount": len(annualPeriods),
        "quarterlyPeriodCount": len(quarterlyPeriods),
        "latestAnnualPeriod": latestAnnual,
        "latestQuarterlyPeriod": latestQuarterly,
    }


def projectCadenceRows(
    df: pl.DataFrame,
    *,
    cadenceScope: str,
    includeMixed: bool = True,
) -> pl.DataFrame:
    """sections DataFrame를 cadence 기준으로 투영한다."""
    if df.is_empty() or "cadenceScope" not in df.columns:
        return df

    scope = str(cadenceScope).strip().lower()
    if scope == "all":
        return df
    if scope not in {"annual", "quarterly", "mixed"}:
        raise ValueError(f"unsupported cadenceScope: {cadenceScope}")

    allowed = {scope}
    if includeMixed and scope in {"annual", "quarterly"}:
        allowed.add("mixed")

    return df.filter(pl.col("cadenceScope").is_in(sorted(allowed)))


def _emptySemanticRegistryFrame() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "topic": pl.Utf8,
            "textNodeType": pl.Utf8,
            "textLevel": pl.Int64,
            "cadenceScope": pl.Utf8,
            "textSemanticPathKey": pl.Utf8,
            "textSemanticParentPathKey": pl.Utf8,
            "rowCount": pl.Int64,
            "rawPathCount": pl.Int64,
            "rawPaths": pl.List(pl.Utf8),
            "rawParentPaths": pl.List(pl.Utf8),
            "semanticPathCount": pl.Int64,
            "semanticPaths": pl.List(pl.Utf8),
            "sourceBlockOrders": pl.List(pl.Int64),
            "segmentKeys": pl.List(pl.Utf8),
            "latestAnnualPeriod": pl.Utf8,
            "latestQuarterlyPeriod": pl.Utf8,
            "hasCollision": pl.Boolean,
        }
    )


def semanticRegistry(
    df: pl.DataFrame | None,
    *,
    topic: str | None = None,
    cadenceScope: str = "all",
    includeMixed: bool = True,
) -> pl.DataFrame:
    """textSemanticPathKey 기준 semantic registry를 만든다."""
    if df is None or df.is_empty():
        return _emptySemanticRegistryFrame()

    required = {"topic", "textSemanticPathKey", "textPathKey", "segmentKey"}
    if not required.issubset(set(df.columns)):
        return _emptySemanticRegistryFrame()

    scoped = df
    if cadenceScope != "all":
        scoped = projectCadenceRows(scoped, cadenceScope=cadenceScope, includeMixed=includeMixed)
    if topic is not None:
        scoped = scoped.filter(pl.col("topic") == topic)
    if scoped.is_empty():
        return _emptySemanticRegistryFrame()

    textScoped = scoped
    if "blockType" in textScoped.columns:
        textScoped = textScoped.filter(pl.col("blockType") == "text")
    if "textStructural" in textScoped.columns:
        textScoped = textScoped.filter(pl.col("textStructural") != False)  # noqa: E712
    textScoped = textScoped.filter(pl.col("textSemanticPathKey").is_not_null() & pl.col("textPathKey").is_not_null())
    if textScoped.is_empty():
        return _emptySemanticRegistryFrame()

    rawPathExpr = (
        pl.col("textPathVariants").list.explode().drop_nulls().unique().sort()
        if "textPathVariants" in textScoped.columns
        else pl.col("textPathKey").drop_nulls().unique().sort()
    )
    rawParentExpr = (
        pl.col("textParentPathVariants").list.explode().drop_nulls().unique().sort()
        if "textParentPathVariants" in textScoped.columns
        else pl.col("textParentPathKey").drop_nulls().unique().sort()
    )
    semanticPathExpr = (
        pl.col("textSemanticPathVariants").list.explode().drop_nulls().unique().sort()
        if "textSemanticPathVariants" in textScoped.columns
        else pl.col("textSemanticPathKey").drop_nulls().unique().sort()
    )

    registry = (
        textScoped.group_by(
            [
                "topic",
                "textNodeType",
                "textLevel",
                "cadenceScope",
                "textSemanticPathKey",
                "textSemanticParentPathKey",
            ],
            maintain_order=True,
        )
        .agg(
            [
                pl.len().alias("rowCount"),
                rawPathExpr.alias("rawPaths"),
                rawParentExpr.alias("rawParentPaths"),
                semanticPathExpr.alias("semanticPaths"),
                pl.col("sourceBlockOrder").drop_nulls().unique().sort().alias("sourceBlockOrders"),
                pl.col("segmentKey").drop_nulls().unique().sort().alias("segmentKeys"),
                pl.col("latestAnnualPeriod").drop_nulls().max().alias("latestAnnualPeriod"),
                pl.col("latestQuarterlyPeriod").drop_nulls().max().alias("latestQuarterlyPeriod"),
            ]
        )
        .with_columns(
            [
                pl.col("rawPaths").list.len().alias("rawPathCount"),
                pl.col("semanticPaths").list.len().alias("semanticPathCount"),
            ]
        )
        .with_columns((pl.col("rawPathCount") > 1).alias("hasCollision"))
        .sort(["topic", "textSemanticPathKey", "textNodeType", "textLevel", "cadenceScope"])
    )
    return registry


def semanticCollisions(
    df: pl.DataFrame | None,
    *,
    topic: str | None = None,
    cadenceScope: str = "all",
    includeMixed: bool = True,
) -> pl.DataFrame:
    """semantic registry에서 raw path 충돌 그룹만 반환한다."""
    registry = semanticRegistry(df, topic=topic, cadenceScope=cadenceScope, includeMixed=includeMixed)
    if registry.is_empty():
        return registry
    return registry.filter(pl.col("hasCollision"))


def sections(stockCode: str) -> pl.DataFrame | None:
    """전 기간 보고서 섹션 — (topic, blockType, blockOrder) × period DataFrame.

    텍스트와 테이블을 분리하여 같은 topic이라도 text 행과 table 행으로 나뉜다.

    Args:
        stockCode: 종목코드

    Returns:
        (topic, blockType, blockOrder)(행) × period(열) DataFrame. 값은 텍스트(str).
        데이터 없으면 None.
    """
    topicMap: dict[tuple[str, str], dict[str, str]] = {}
    rowMeta: dict[tuple[str, str], dict[str, object]] = {}
    rowOrder: dict[tuple[str, str], dict[str, int]] = {}
    pathVariantsByKey: dict[tuple[str, str], set[str]] = {}
    parentPathVariantsByKey: dict[tuple[str, str], set[str]] = {}
    semanticPathVariantsByKey: dict[tuple[str, str], set[str]] = {}
    semanticParentPathVariantsByKey: dict[tuple[str, str], set[str]] = {}
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
    latestPeriod = validPeriods[-1]

    def _representativePeriodRank(period: str | None) -> int:
        if not isinstance(period, str):
            return -1
        year = int(period[:4])
        quarter = {"Q1": 1, "Q2": 2, "Q3": 3}.get(period[4:], 4)
        return (year * 10) + quarter

    topicChapter: dict[str, str] = {}
    topicFirstSeq: dict[str, tuple[int, int]] = {}

    for periodKey in validPeriods:
        projected = applyProjections(
            periodRows.get(periodKey, []),
            teacherTopics,
        )
        for row in _expandStructuredRows(projected):
            chapter = row["chapter"]
            topic = row["topic"]
            text = row["text"]
            blockType = row.get("blockType", "text")
            segmentKey = row.get("segmentKey")
            if not isinstance(chapter, str) or not isinstance(topic, str) or not isinstance(text, str):
                continue
            if not isinstance(blockType, str):
                blockType = "text"
            if not isinstance(segmentKey, str) or not segmentKey:
                continue
            if topic not in topicChapter:
                topicChapter[topic] = chapter
            if topic in suppressed.get(chapter, set()):
                continue
            if detailTopicForTopic(topic) is not None:
                continue

            key = (topic, segmentKey)
            if key not in topicMap:
                topicMap[key] = {}
            topicMap[key][periodKey] = text
            if isinstance(row.get("textPathKey"), str) and row.get("textPathKey"):
                pathVariantsByKey.setdefault(key, set()).add(str(row["textPathKey"]))
            if isinstance(row.get("textParentPathKey"), str) and row.get("textParentPathKey"):
                parentPathVariantsByKey.setdefault(key, set()).add(str(row["textParentPathKey"]))
            if isinstance(row.get("textSemanticPathKey"), str) and row.get("textSemanticPathKey"):
                semanticPathVariantsByKey.setdefault(key, set()).add(str(row["textSemanticPathKey"]))
            if isinstance(row.get("textSemanticParentPathKey"), str) and row.get("textSemanticParentPathKey"):
                semanticParentPathVariantsByKey.setdefault(key, set()).add(str(row["textSemanticParentPathKey"]))
            majorNum = int(row.get("majorNum", 99))
            sortOrder = int(row.get("sortOrder", 999999))
            if topic not in topicFirstSeq or (majorNum, sortOrder) < topicFirstSeq[topic]:
                topicFirstSeq[topic] = (majorNum, sortOrder)

            orderInfo = rowOrder.setdefault(
                key,
                {
                    "latestRank": 999999999,
                    "latestMissing": 1,
                    "firstRank": 999999999,
                    "sourceBlockOrder": int(row.get("sourceBlockOrder") or 0),
                    "segmentOrder": int(row.get("segmentOrder") or 0),
                    "segmentOccurrence": int(row.get("segmentOccurrence") or 1),
                },
            )
            orderInfo["firstRank"] = min(orderInfo["firstRank"], sortOrder)
            orderInfo["sourceBlockOrder"] = min(orderInfo["sourceBlockOrder"], int(row.get("sourceBlockOrder") or 0))
            orderInfo["segmentOrder"] = min(orderInfo["segmentOrder"], int(row.get("segmentOrder") or 0))
            orderInfo["segmentOccurrence"] = min(orderInfo["segmentOccurrence"], int(row.get("segmentOccurrence") or 1))
            if periodKey == latestPeriod:
                orderInfo["latestMissing"] = 0
                orderInfo["latestRank"] = min(orderInfo["latestRank"], sortOrder)

            prevMeta = rowMeta.get(key)
            prevRank = _representativePeriodRank(prevMeta.get("_repPeriod")) if isinstance(prevMeta, dict) else -1
            currRank = _representativePeriodRank(periodKey)
            if prevMeta is None or currRank >= prevRank:
                rowMeta[key] = {
                    "chapter": chapter,
                    "topic": topic,
                    "blockType": blockType,
                    "sourceBlockOrder": int(row.get("sourceBlockOrder") or 0),
                    "textNodeType": row.get("textNodeType"),
                    "textStructural": row.get("textStructural"),
                    "textLevel": int(row["textLevel"]) if isinstance(row.get("textLevel"), int) else None,
                    "textPath": row.get("textPath"),
                    "textPathKey": row.get("textPathKey"),
                    "textParentPathKey": row.get("textParentPathKey"),
                    "textSemanticPathKey": row.get("textSemanticPathKey"),
                    "textSemanticParentPathKey": row.get("textSemanticParentPathKey"),
                    "segmentKey": segmentKey,
                    "segmentOrder": int(row.get("segmentOrder") or 0),
                    "segmentOccurrence": int(row.get("segmentOccurrence") or 1),
                    "sourceTopic": row.get("sourceTopic"),
                    "_repPeriod": periodKey,
                }

    if not validPeriods or not topicMap:
        return None

    cadenceMetaByKey = {key: _rowCadenceMeta(periodMap) for key, periodMap in topicMap.items()}
    topicKeysByTopic: dict[str, list[tuple[str, str]]] = {}
    for key in topicMap.keys():
        topicKeysByTopic.setdefault(key[0], []).append(key)

    topicIndex: dict[str, int] = {}
    for topic_seq in sorted(topicFirstSeq.items(), key=lambda x: x[1]):
        topicIndex[topic_seq[0]] = len(topicIndex)

    def _cadenceScopePriority(scope: str | None) -> int:
        return {"mixed": 0, "annual": 1, "quarterly": 2, "none": 3}.get(str(scope or "none"), 9)

    def _topicRowSortKey(k: tuple[str, str]) -> tuple[int, int, int, int, int, int, int, int, str]:
        topic, _segmentKey = k
        majorNum, firstSeq = topicFirstSeq.get(topic, (99, 999999))
        tIdx = topicIndex.get(topic, 999999)
        info = rowOrder.get(k, {})
        cadenceMeta = cadenceMetaByKey.get(k, {})
        return (
            majorNum,
            firstSeq,
            tIdx,
            _cadenceScopePriority(str(cadenceMeta.get("cadenceScope") or "none")),
            int(info.get("latestMissing", 1)),
            int(info.get("latestRank", 999999999)),
            int(info.get("firstRank", 999999999)),
            int(info.get("segmentOccurrence", 1)),
            str(k[1]),
        )

    sortedTopics = [topic for topic, _ in sorted(topicFirstSeq.items(), key=lambda x: x[1])]

    dfRows: list[dict[str, str | None]] = []
    for topic in sortedTopics:
        topicKeys = sorted(topicKeysByTopic.get(topic, []), key=_topicRowSortKey)
        for blockOrder, key in enumerate(topicKeys):
            meta = rowMeta.get(key, {})
            orderInfo = rowOrder.get(key, {})
            cadenceMeta = cadenceMetaByKey.get(key, {})
            pathVariants = sorted(pathVariantsByKey.get(key, set()))
            parentPathVariants = sorted(parentPathVariantsByKey.get(key, set()))
            semanticPathVariants = sorted(semanticPathVariantsByKey.get(key, set()))
            semanticParentPathVariants = sorted(semanticParentPathVariantsByKey.get(key, set()))
            row: dict[str, str | int | None] = {
                "chapter": topicChapter.get(topic),
                "topic": topic,
                "blockType": str(meta.get("blockType") or "text"),
                "blockOrder": blockOrder,
                "sourceBlockOrder": int(orderInfo.get("sourceBlockOrder") or meta.get("sourceBlockOrder") or 0),
                "textNodeType": str(meta["textNodeType"]) if isinstance(meta.get("textNodeType"), str) else None,
                "textStructural": bool(meta["textStructural"])
                if isinstance(meta.get("textStructural"), bool)
                else None,
                "textLevel": int(meta["textLevel"]) if isinstance(meta.get("textLevel"), int) else None,
                "textPath": str(meta["textPath"]) if isinstance(meta.get("textPath"), str) else None,
                "textPathKey": str(meta["textPathKey"]) if isinstance(meta.get("textPathKey"), str) else None,
                "textParentPathKey": (
                    str(meta["textParentPathKey"]) if isinstance(meta.get("textParentPathKey"), str) else None
                ),
                "textPathVariantCount": len(pathVariants),
                "textPathVariants": pathVariants or None,
                "textParentPathVariants": parentPathVariants or None,
                "textSemanticPathKey": (
                    str(meta["textSemanticPathKey"]) if isinstance(meta.get("textSemanticPathKey"), str) else None
                ),
                "textSemanticParentPathKey": (
                    str(meta["textSemanticParentPathKey"])
                    if isinstance(meta.get("textSemanticParentPathKey"), str)
                    else None
                ),
                "textSemanticPathVariants": semanticPathVariants or None,
                "textSemanticParentPathVariants": semanticParentPathVariants or None,
                "segmentKey": str(meta.get("segmentKey") or ""),
                "segmentOrder": int(meta.get("segmentOrder") or 0),
                "segmentOccurrence": int(orderInfo.get("segmentOccurrence") or meta.get("segmentOccurrence") or 1),
                "cadenceKey": str(cadenceMeta.get("cadenceKey") or "none"),
                "cadenceScope": str(cadenceMeta.get("cadenceScope") or "none"),
                "annualPeriodCount": int(cadenceMeta.get("annualPeriodCount") or 0),
                "quarterlyPeriodCount": int(cadenceMeta.get("quarterlyPeriodCount") or 0),
                "latestAnnualPeriod": (
                    str(cadenceMeta["latestAnnualPeriod"])
                    if isinstance(cadenceMeta.get("latestAnnualPeriod"), str)
                    else None
                ),
                "latestQuarterlyPeriod": (
                    str(cadenceMeta["latestQuarterlyPeriod"])
                    if isinstance(cadenceMeta.get("latestQuarterlyPeriod"), str)
                    else None
                ),
                "sourceTopic": str(meta["sourceTopic"]) if isinstance(meta.get("sourceTopic"), str) else None,
            }
            for period in validPeriods:
                row[period] = topicMap[key].get(period)
            dfRows.append(row)

    schema = {
        "chapter": pl.Utf8,
        "topic": pl.Utf8,
        "blockType": pl.Utf8,
        "blockOrder": pl.Int64,
        "sourceBlockOrder": pl.Int64,
        "textNodeType": pl.Utf8,
        "textStructural": pl.Boolean,
        "textLevel": pl.Int64,
        "textPath": pl.Utf8,
        "textPathKey": pl.Utf8,
        "textParentPathKey": pl.Utf8,
        "textPathVariantCount": pl.Int64,
        "textPathVariants": pl.List(pl.Utf8),
        "textParentPathVariants": pl.List(pl.Utf8),
        "textSemanticPathKey": pl.Utf8,
        "textSemanticParentPathKey": pl.Utf8,
        "textSemanticPathVariants": pl.List(pl.Utf8),
        "textSemanticParentPathVariants": pl.List(pl.Utf8),
        "segmentKey": pl.Utf8,
        "segmentOrder": pl.Int64,
        "segmentOccurrence": pl.Int64,
        "cadenceKey": pl.Utf8,
        "cadenceScope": pl.Utf8,
        "annualPeriodCount": pl.Int64,
        "quarterlyPeriodCount": pl.Int64,
        "latestAnnualPeriod": pl.Utf8,
        "latestQuarterlyPeriod": pl.Utf8,
        "sourceTopic": pl.Utf8,
    }
    for p in validPeriods:
        schema[p] = pl.Utf8
    return pl.DataFrame(dfRows, schema=schema)
