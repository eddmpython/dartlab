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

import re
from collections.abc import Iterator

import polars as pl

from dartlab.core.dataLoader import loadData
from dartlab.core.reportSelector import selectReport
from dartlab.engines.dart.docs.sections._common import (
    REPORT_KINDS,
    detectContentCol,
    periodOrderValue,
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

_RE_BUSINESS_UNIT_SEGMENT = re.compile(r".+(?:부문|총괄)$")
_RE_BUSINESS_UNIT_SHORT = re.compile(r"^[A-Z][A-Z0-9&/-]{1,7}$")

_BUSINESS_OVERVIEW_COMPARABLE_ROOTS: dict[str, str] = {
    "주요제품서비스등": "주요제품및서비스",
    "매출및수주상황": "매출",
    "주요계약및연구개발활동": "연구개발활동",
    "주요원재료": "원재료및생산설비",
    "주요사업장현황": "생산및설비",
    "위험관리및파생거래": "시장위험과위험관리",
}

_STRUCTURE_SLOT_ALIASES: dict[str, dict[str, str]] = {
    "businessOverview": {
        "판매경로": "판매경로및판매방법",
        "판매방법및조건": "판매경로및판매방법",
        "판매전략": "판매경로및판매방법",
        "판매조직": "판매경로및판매방법",
        "판매경로및판매방법등": "판매경로및판매방법",
        "생산능력": "생산능력생산실적가동률",
        "생산실적": "생산능력생산실적가동률",
        "가동률": "생산능력생산실적가동률",
        "생산능력및산출근거": "생산능력생산실적가동률",
        "생산능력생산실적가동률": "생산능력생산실적가동률",
        "생산능력산출근거및생산실적": "생산능력생산실적가동률",
        "사업부문별요약재무현황": "사업부문별요약재무현황",
        "산업의특성": "산업의특성",
        "시장여건": "시장여건",
        "영업현황": "영업현황",
    },
    "auditSystem": {
        "감사위원회교육실시계획및현황": "감사위원회교육",
        "감사위원회의교육실시계획": "감사위원회교육",
        "감사위원회교육실시현황": "감사위원회교육",
    },
}

_BUSINESS_UNIT_SEGMENT_LITERALS = {"Harman", "SDC"}


def _splitPathSegments(path: str | None) -> list[str]:
    if not isinstance(path, str) or not path:
        return []
    return [segment.strip() for segment in path.split(" > ") if segment.strip()]


def _joinPathSegments(segments: list[str]) -> str | None:
    cleaned = [segment for segment in segments if isinstance(segment, str) and segment]
    if not cleaned:
        return None
    return " > ".join(cleaned)


def _isBusinessUnitSegment(segment: str) -> bool:
    return (
        segment in _BUSINESS_UNIT_SEGMENT_LITERALS
        or bool(_RE_BUSINESS_UNIT_SEGMENT.fullmatch(segment))
        or bool(_RE_BUSINESS_UNIT_SHORT.fullmatch(segment))
    )


def _normalizeComparableSegment(topic: str, segment: str) -> str:
    if topic == "businessOverview":
        segment = _BUSINESS_OVERVIEW_COMPARABLE_ROOTS.get(segment, segment)
    return _STRUCTURE_SLOT_ALIASES.get(topic, {}).get(segment, segment)


def _comparablePathInfo(topic: str, semanticPathKey: str | None) -> tuple[str | None, str | None]:
    segments = _splitPathSegments(semanticPathKey)
    if not segments:
        return None, None

    normalized: list[str] = []
    unitAnchorInserted = False

    for segment in segments:
        if segment.startswith("@topic:"):
            normalized.append(segment)
            continue

        if topic == "businessOverview" and _isBusinessUnitSegment(segment):
            if not unitAnchorInserted:
                anchor = "사업부문현황"
                if not normalized or normalized[-1] != anchor:
                    normalized.append(anchor)
                unitAnchorInserted = True
            continue

        normalizedSegment = _normalizeComparableSegment(topic, segment)
        if normalized and normalized[-1] == normalizedSegment:
            continue
        normalized.append(normalizedSegment)

    pathKey = _joinPathSegments(normalized)
    parentPathKey = _joinPathSegments(normalized[:-1])
    return pathKey, parentPathKey


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
    strippedContent = content.strip()
    if not strippedContent:
        return []
    if "|" not in strippedContent:
        return [("text", strippedContent)]

    rows: list[tuple[str, str]] = []
    rowsAppend = rows.append
    buffer: list[str] = []
    currentKind: str | None = None

    def _flush(kind: str | None) -> None:
        nonlocal buffer
        if kind is None or not buffer:
            buffer = []
            return
        text = "\n".join(buffer).strip()
        if text:
            rowsAppend((kind, text))
        buffer = []

    for raw in content.splitlines():
        stripped = raw.strip()
        if not stripped:
            if currentKind == "table":
                _flush(currentKind)
                currentKind = None
            elif currentKind == "text" and buffer:
                buffer.append("")
            continue

        nextKind = "table" if stripped.startswith("|") else "text"
        if currentKind is None:
            currentKind = nextKind
            buffer.append(stripped)
            continue

        if nextKind != currentKind:
            _flush(currentKind)
            currentKind = nextKind
        buffer.append(stripped)

    _flush(currentKind)
    return rows


def _reportRowsToTopicRows(
    subset: pl.DataFrame,
    contentCol: str,
) -> list[dict[str, object]]:
    emitted: list[dict[str, object]] = []
    topicBlockCounts: dict[tuple[str, str], int] = {}
    currentMajorNum: int | None = None
    idx = 0
    # 장 제목 행은 보류했다가, 소항목이 없는 단독 장이면 등록한다.
    pendingChapter: dict[str, object] | None = None
    if subset.is_empty():
        return emitted

    cols = subset.columns
    titleIdx = cols.index("section_title")
    contentIdx = cols.index(contentCol)

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

    def _registerPendingChapter() -> None:
        nonlocal pendingChapter
        if pendingChapter is None:
            return
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

    def _flushPending() -> None:
        _registerPendingChapter()

    for values in subset.iter_rows():
        title = str(values[titleIdx] or "").strip()
        content = str(values[contentIdx] or "")
        if not title or not content.strip():
            continue

        record = {
            "section_title": title,
            contentCol: content,
        }

        majorNum = parseMajorNum(title)
        if majorNum is not None:
            # 이전 보류된 장 제목 처리
            _flushPending()
            currentMajorNum = majorNum
            pendingChapter = record
            continue
        if currentMajorNum is None:
            continue

        # 장 제목 행의 content도 raw source-of-truth로 보존한다.
        # 이후 소항목이 같은 semantic row를 채우면 그 셀만 overwrite되고,
        # 장 제목에만 있던 segment는 그대로 남는다.
        _registerPendingChapter()

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

    if any(row.get("projectionKind") is not None for row in rows):
        orderedRows = sorted(
            rows,
            key=lambda r: (
                int(r.get("majorNum") or 99),
                int(r.get("orderSeq") or 999999),
                int(r.get("sourceBlockOrder") or r.get("blockOrder") or 0),
            ),
        )
    else:
        orderedRows = rows

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


def _emptyStructureRegistryFrame() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "topic": pl.Utf8,
            "textNodeType": pl.Utf8,
            "textLevel": pl.Int64,
            "cadenceScope": pl.Utf8,
            "textComparablePathKey": pl.Utf8,
            "textComparableParentPathKey": pl.Utf8,
            "rowCount": pl.Int64,
            "rawSemanticPathCount": pl.Int64,
            "rawSemanticPaths": pl.List(pl.Utf8),
            "rawSemanticParentPaths": pl.List(pl.Utf8),
            "rawSemanticLeafCount": pl.Int64,
            "rawSemanticLeafs": pl.List(pl.Utf8),
            "sourceBlockOrders": pl.List(pl.Int64),
            "segmentKeys": pl.List(pl.Utf8),
            "latestAnnualPeriod": pl.Utf8,
            "latestQuarterlyPeriod": pl.Utf8,
            "activePeriodCount": pl.Int64,
            "activePeriods": pl.List(pl.Utf8),
            "activePathCounts": pl.List(pl.Int64),
            "minActivePathCount": pl.Int64,
            "maxActivePathCount": pl.Int64,
            "earliestPathCount": pl.Int64,
            "latestPathCount": pl.Int64,
            "multiPathPeriods": pl.List(pl.Utf8),
            "structurePattern": pl.Utf8,
            "hasCollision": pl.Boolean,
        }
    )


def _emptyStructureEventsFrame() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "topic": pl.Utf8,
            "textNodeType": pl.Utf8,
            "textLevel": pl.Int64,
            "cadenceScope": pl.Utf8,
            "textComparablePathKey": pl.Utf8,
            "textComparableParentPathKey": pl.Utf8,
            "periodLane": pl.Utf8,
            "fromPeriod": pl.Utf8,
            "toPeriod": pl.Utf8,
            "fromPathCount": pl.Int64,
            "toPathCount": pl.Int64,
            "fromPaths": pl.List(pl.Utf8),
            "toPaths": pl.List(pl.Utf8),
            "addedPaths": pl.List(pl.Utf8),
            "removedPaths": pl.List(pl.Utf8),
            "eventType": pl.Utf8,
        }
    )


def _emptyStructureSummaryFrame() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "topic": pl.Utf8,
            "textNodeType": pl.Utf8,
            "textLevel": pl.Int64,
            "cadenceScope": pl.Utf8,
            "textComparablePathKey": pl.Utf8,
            "textComparableParentPathKey": pl.Utf8,
            "structurePattern": pl.Utf8,
            "hasCollision": pl.Boolean,
            "activePeriodCount": pl.Int64,
            "activePeriods": pl.List(pl.Utf8),
            "latestPeriod": pl.Utf8,
            "latestPeriodLane": pl.Utf8,
            "latestPathCount": pl.Int64,
            "multiPathPeriods": pl.List(pl.Utf8),
            "eventCount": pl.Int64,
            "latestEventType": pl.Utf8,
            "latestEventFromPeriod": pl.Utf8,
            "latestEventToPeriod": pl.Utf8,
            "latestEventLane": pl.Utf8,
        }
    )


def _emptyStructureChangesFrame() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "topic": pl.Utf8,
            "textNodeType": pl.Utf8,
            "textLevel": pl.Int64,
            "cadenceScope": pl.Utf8,
            "textComparablePathKey": pl.Utf8,
            "textComparableParentPathKey": pl.Utf8,
            "structurePattern": pl.Utf8,
            "hasCollision": pl.Boolean,
            "activePeriodCount": pl.Int64,
            "activePeriods": pl.List(pl.Utf8),
            "latestPeriod": pl.Utf8,
            "latestPeriodLane": pl.Utf8,
            "latestPathCount": pl.Int64,
            "multiPathPeriods": pl.List(pl.Utf8),
            "eventCount": pl.Int64,
            "latestEventType": pl.Utf8,
            "latestEventFromPeriod": pl.Utf8,
            "latestEventToPeriod": pl.Utf8,
            "latestEventLane": pl.Utf8,
            "anchorPeriod": pl.Utf8,
            "anchorPeriodLane": pl.Utf8,
            "isLatest": pl.Boolean,
            "isStale": pl.Boolean,
        }
    )


def _structureGroupColumns() -> list[str]:
    return [
        "topic",
        "textNodeType",
        "textLevel",
        "cadenceScope",
        "textComparablePathKey",
        "textComparableParentPathKey",
    ]


def _normalizeStructureGroupDtypes(frame: pl.DataFrame) -> pl.DataFrame:
    casts: list[pl.Expr] = []
    stringCols = ["topic", "textNodeType", "cadenceScope", "textComparablePathKey", "textComparableParentPathKey"]
    for colName in stringCols:
        if colName in frame.columns:
            casts.append(pl.col(colName).cast(pl.Utf8).alias(colName))
    if "textLevel" in frame.columns:
        casts.append(pl.col("textLevel").cast(pl.Int64).alias("textLevel"))
    return frame.with_columns(casts) if casts else frame


def _periodLane(period: str | None) -> str | None:
    if not isinstance(period, str) or not period:
        return None
    if period.endswith("Q1"):
        return "q1"
    if period.endswith("Q2"):
        return "q2"
    if period.endswith("Q3"):
        return "q3"
    return "annual"


def _allowedStructurePeriodLanes(cadenceScope: str | None) -> set[str] | None:
    scope = str(cadenceScope).strip().lower() if isinstance(cadenceScope, str) else "all"
    if scope == "annual":
        return {"annual"}
    if scope == "quarterly":
        return {"q1", "q2", "q3"}
    return None


def _structurePatternRank(pattern: str | None) -> int:
    order = {
        "parallel": 7,
        "split_merge": 6,
        "split": 5,
        "merge": 4,
        "reassigned": 3,
        "moved": 2,
        "variant": 1,
        "same": 0,
    }
    return order.get(str(pattern), 0)


def _pathCollection(paths: object) -> list[str]:
    if isinstance(paths, pl.Series):
        values = paths.to_list()
    elif isinstance(paths, list):
        values = paths
    else:
        return []
    return [str(path) for path in values if isinstance(path, str) and path]


def _intCollection(values: object) -> list[int]:
    if isinstance(values, pl.Series):
        rawValues = values.to_list()
    elif isinstance(values, list):
        rawValues = values
    else:
        return []

    result: list[int] = []
    for value in rawValues:
        if isinstance(value, bool):
            continue
        if isinstance(value, int):
            result.append(value)
            continue
        if isinstance(value, float) and value.is_integer():
            result.append(int(value))
    return result


def _path_leafs(paths: object) -> list[str]:
    values = _pathCollection(paths)
    leafs = sorted({segments[-1] for path in values if (segments := _splitPathSegments(path))})
    return leafs


def _isBusinessUnitComparablePath(path: str | None) -> bool:
    return isinstance(path, str) and any(segment == "사업부문현황" for segment in _splitPathSegments(path))


def _periodsWithMultiplePaths(payload: object) -> list[str]:
    if not isinstance(payload, dict):
        return []
    periods = payload.get("activePeriods")
    counts = payload.get("activePathCounts")
    if not isinstance(periods, list) or not isinstance(counts, list):
        return []

    result: list[str] = []
    for period, count in zip(periods, counts, strict=False):
        if isinstance(period, str) and isinstance(count, (int, float)) and int(count) > 1:
            result.append(period)
    return result


def _changedPaths(fromPaths: list[str], toPaths: list[str]) -> tuple[list[str], list[str]]:
    added = [path for path in toPaths if path not in fromPaths]
    removed = [path for path in fromPaths if path not in toPaths]
    return added, removed


def _structureTransitionType(comparablePathKey: str | None, fromPaths: list[str], toPaths: list[str]) -> str:
    if fromPaths == toPaths:
        return "stable"

    fromCount = len(fromPaths)
    toCount = len(toPaths)
    fromLeafs = _path_leafs(fromPaths)
    toLeafs = _path_leafs(toPaths)
    fromParents = {_joinPathSegments(_splitPathSegments(path)[:-1]) for path in fromPaths if _splitPathSegments(path)}
    toParents = {_joinPathSegments(_splitPathSegments(path)[:-1]) for path in toPaths if _splitPathSegments(path)}
    fromParents.discard(None)
    toParents.discard(None)

    if fromCount == 1 and toCount == 1:
        if set(fromLeafs) == set(toLeafs) and fromParents != toParents:
            return "moved"
        if _isBusinessUnitComparablePath(comparablePathKey) and set(fromLeafs) != set(toLeafs):
            return "reassigned"
        return "variant"
    if fromCount == 1 and toCount > 1:
        return "split"
    if fromCount > 1 and toCount == 1:
        return "merge"
    return "parallel_change"


def _structurePattern(payload: object) -> str:
    if isinstance(payload, dict):
        values = _pathCollection(payload.get("rawSemanticPaths"))
        comparablePathKey = payload.get("textComparablePathKey")
        activeCounts = _intCollection(payload.get("activePathCounts"))
    else:
        values = _pathCollection(payload)
        comparablePathKey = None
        activeCounts = []

    if len(values) <= 1:
        return "same"

    parents = {_joinPathSegments(_splitPathSegments(path)[:-1]) for path in values if _splitPathSegments(path)}
    parents.discard(None)
    leafs = _path_leafs(values)

    if activeCounts and max(activeCounts) <= 1:
        if len(leafs) == 1 and len(parents) > 1:
            return "moved"
        if _isBusinessUnitComparablePath(str(comparablePathKey)) and len(leafs) > 1:
            return "reassigned"
        return "variant"

    if len(leafs) == 1 and len(parents) > 1:
        if activeCounts and max(activeCounts) > 1:
            return "parallel"
        return "moved"

    if activeCounts:
        earliestCount = activeCounts[0]
        latestCount = activeCounts[-1]
        minCount = min(activeCounts)
        maxCount = max(activeCounts)
        if earliestCount <= 1 and latestCount > 1:
            return "split"
        if earliestCount > 1 and latestCount <= 1:
            return "merge"
        if minCount <= 1 and maxCount > 1:
            return "split_merge"
        return "parallel"

    return "variant"


def _structurePeriodActivity(textScoped: pl.DataFrame, *, cadenceScope: str = "all") -> pl.DataFrame | None:
    groupCols = _structureGroupColumns()
    periodCols = sortPeriods([str(col) for col in textScoped.columns if re.fullmatch(r"^\d{4}(Q[1-4])?$", str(col))])
    allowedLanes = _allowedStructurePeriodLanes(cadenceScope)
    if allowedLanes is not None:
        periodCols = [period for period in periodCols if _periodLane(period) in allowedLanes]
    if not periodCols:
        return None

    periodActivity = (
        textScoped.select(groupCols + ["textSemanticPathKey"] + periodCols)
        .unpivot(
            index=groupCols + ["textSemanticPathKey"],
            on=periodCols,
            variable_name="period",
            value_name="payload",
        )
        .filter(pl.col("payload").is_not_null() & (pl.col("payload").cast(pl.Utf8).str.len_chars() > 0))
        .with_columns(pl.col("period").map_elements(periodOrderValue, return_dtype=pl.Int64).alias("periodOrder"))
        .group_by(groupCols + ["period", "periodOrder"], maintain_order=True)
        .agg(pl.col("textSemanticPathKey").drop_nulls().unique().sort().alias("activeRawSemanticPaths"))
        .with_columns(pl.col("activeRawSemanticPaths").list.len().alias("activePathCount"))
        .sort(groupCols + ["periodOrder"])
    )
    return None if periodActivity.is_empty() else periodActivity


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


def structureRegistry(
    df: pl.DataFrame | None,
    *,
    topic: str | None = None,
    cadenceScope: str = "all",
    includeMixed: bool = True,
    nodeType: str | None = None,
) -> pl.DataFrame:
    """Comparable slot spine 기준 structure registry를 만든다."""
    if df is None or df.is_empty():
        return _emptyStructureRegistryFrame()

    required = {"topic", "textComparablePathKey", "textSemanticPathKey", "segmentKey"}
    if not required.issubset(set(df.columns)):
        return _emptyStructureRegistryFrame()

    scoped = df
    if cadenceScope != "all":
        scoped = projectCadenceRows(scoped, cadenceScope=cadenceScope, includeMixed=includeMixed)
    if topic is not None:
        scoped = scoped.filter(pl.col("topic") == topic)
    if scoped.is_empty():
        return _emptyStructureRegistryFrame()

    textScoped = scoped
    if "blockType" in textScoped.columns:
        textScoped = textScoped.filter(pl.col("blockType") == "text")
    if "textStructural" in textScoped.columns:
        textScoped = textScoped.filter(pl.col("textStructural") != False)  # noqa: E712
    normalizedNodeType = str(nodeType).strip().lower() if isinstance(nodeType, str) and nodeType.strip() else None
    if normalizedNodeType is not None and "textNodeType" in textScoped.columns:
        textScoped = textScoped.filter(pl.col("textNodeType") == normalizedNodeType)
    textScoped = textScoped.filter(
        pl.col("textComparablePathKey").is_not_null() & pl.col("textSemanticPathKey").is_not_null()
    )
    if textScoped.is_empty():
        return _emptyStructureRegistryFrame()

    groupCols = _structureGroupColumns()
    periodActivity = _structurePeriodActivity(textScoped, cadenceScope=cadenceScope)
    periodActivitySummary: pl.DataFrame | None = None
    if periodActivity is not None:
        periodActivitySummary = periodActivity.group_by(groupCols, maintain_order=True).agg(
            [
                pl.len().alias("activePeriodCount"),
                pl.col("period").alias("activePeriods"),
                pl.col("activePathCount").alias("activePathCounts"),
                pl.col("activePathCount").min().alias("minActivePathCount"),
                pl.col("activePathCount").max().alias("maxActivePathCount"),
                pl.col("activePathCount").first().alias("earliestPathCount"),
                pl.col("activePathCount").last().alias("latestPathCount"),
            ]
        )

    registry = textScoped.group_by(groupCols, maintain_order=True).agg(
        [
            pl.len().alias("rowCount"),
            pl.col("textSemanticPathKey").drop_nulls().unique().sort().alias("rawSemanticPaths"),
            pl.col("textSemanticParentPathKey").drop_nulls().unique().sort().alias("rawSemanticParentPaths"),
            pl.col("sourceBlockOrder").drop_nulls().unique().sort().alias("sourceBlockOrders"),
            pl.col("segmentKey").drop_nulls().unique().sort().alias("segmentKeys"),
            pl.col("latestAnnualPeriod").drop_nulls().max().alias("latestAnnualPeriod"),
            pl.col("latestQuarterlyPeriod").drop_nulls().max().alias("latestQuarterlyPeriod"),
        ]
    )
    if periodActivitySummary is not None:
        registry = registry.join(periodActivitySummary, on=groupCols, how="left", nulls_equal=True)
    else:
        registry = registry.with_columns(
            [
                pl.lit(0).cast(pl.Int64).alias("activePeriodCount"),
                pl.lit([], dtype=pl.List(pl.Utf8)).alias("activePeriods"),
                pl.lit([], dtype=pl.List(pl.Int64)).alias("activePathCounts"),
                pl.lit(0).cast(pl.Int64).alias("minActivePathCount"),
                pl.lit(0).cast(pl.Int64).alias("maxActivePathCount"),
                pl.lit(0).cast(pl.Int64).alias("earliestPathCount"),
                pl.lit(0).cast(pl.Int64).alias("latestPathCount"),
            ]
        )

    registry = (
        registry.with_columns(
            [
                pl.col("rawSemanticPaths").list.len().alias("rawSemanticPathCount"),
                pl.col("rawSemanticPaths")
                .map_elements(_path_leafs, return_dtype=pl.List(pl.Utf8))
                .alias("rawSemanticLeafs"),
            ]
        )
        .with_columns(
            [
                pl.col("rawSemanticLeafs").list.len().alias("rawSemanticLeafCount"),
                pl.struct(["activePeriods", "activePathCounts"])
                .map_elements(_periodsWithMultiplePaths, return_dtype=pl.List(pl.Utf8))
                .alias("multiPathPeriods"),
                pl.struct(["rawSemanticPaths", "textComparablePathKey", "activePathCounts"])
                .map_elements(_structurePattern, return_dtype=pl.Utf8)
                .alias("structurePattern"),
            ]
        )
        .with_columns((pl.col("rawSemanticPathCount") > 1).alias("hasCollision"))
        .sort(["topic", "textComparablePathKey", "textNodeType", "textLevel", "cadenceScope"])
    )
    return _normalizeStructureGroupDtypes(registry)


def structureCollisions(
    df: pl.DataFrame | None,
    *,
    topic: str | None = None,
    cadenceScope: str = "all",
    includeMixed: bool = True,
    nodeType: str | None = None,
) -> pl.DataFrame:
    registry = structureRegistry(
        df,
        topic=topic,
        cadenceScope=cadenceScope,
        includeMixed=includeMixed,
        nodeType=nodeType,
    )
    if registry.is_empty():
        return registry
    return registry.filter(pl.col("hasCollision"))


def structureEvents(
    df: pl.DataFrame | None,
    *,
    topic: str | None = None,
    cadenceScope: str = "all",
    includeMixed: bool = True,
    changedOnly: bool = True,
    nodeType: str | None = None,
) -> pl.DataFrame:
    if df is None or df.is_empty():
        return _emptyStructureEventsFrame()

    required = {"topic", "textComparablePathKey", "textSemanticPathKey", "segmentKey"}
    if not required.issubset(set(df.columns)):
        return _emptyStructureEventsFrame()

    scoped = df
    if cadenceScope != "all":
        scoped = projectCadenceRows(scoped, cadenceScope=cadenceScope, includeMixed=includeMixed)
    if topic is not None:
        scoped = scoped.filter(pl.col("topic") == topic)
    if scoped.is_empty():
        return _emptyStructureEventsFrame()

    textScoped = scoped
    if "blockType" in textScoped.columns:
        textScoped = textScoped.filter(pl.col("blockType") == "text")
    if "textStructural" in textScoped.columns:
        textScoped = textScoped.filter(pl.col("textStructural") != False)  # noqa: E712
    normalizedNodeType = str(nodeType).strip().lower() if isinstance(nodeType, str) and nodeType.strip() else None
    if normalizedNodeType is not None and "textNodeType" in textScoped.columns:
        textScoped = textScoped.filter(pl.col("textNodeType") == normalizedNodeType)
    textScoped = textScoped.filter(
        pl.col("textComparablePathKey").is_not_null() & pl.col("textSemanticPathKey").is_not_null()
    )
    if textScoped.is_empty():
        return _emptyStructureEventsFrame()

    periodActivity = _structurePeriodActivity(textScoped, cadenceScope=cadenceScope)
    if periodActivity is None:
        return _emptyStructureEventsFrame()

    groupCols = _structureGroupColumns()
    rows: list[dict[str, object]] = []
    groupFrame = periodActivity.group_by(groupCols, maintain_order=True).agg(
        [
            pl.col("period").alias("periods"),
            pl.col("activeRawSemanticPaths").alias("pathsByPeriod"),
            pl.col("activePathCount").alias("pathCounts"),
        ]
    )
    for entry in groupFrame.iter_rows(named=True):
        periods = entry.get("periods")
        pathsByPeriod = entry.get("pathsByPeriod")
        pathCounts = entry.get("pathCounts")
        if not isinstance(periods, list) or not isinstance(pathsByPeriod, list) or not isinstance(pathCounts, list):
            continue
        lanes: dict[str, list[int]] = {}
        for idx, period in enumerate(periods):
            lane = _periodLane(period)
            if lane is None:
                continue
            lanes.setdefault(lane, []).append(idx)

        for lane, indices in lanes.items():
            if len(indices) < 2:
                continue
            for pos in range(1, len(indices)):
                fromIdx = indices[pos - 1]
                toIdx = indices[pos]
                fromPeriod = periods[fromIdx]
                toPeriod = periods[toIdx]
                fromPaths = _pathCollection(pathsByPeriod[fromIdx])
                toPaths = _pathCollection(pathsByPeriod[toIdx])
                if not isinstance(fromPeriod, str) or not isinstance(toPeriod, str) or not fromPaths or not toPaths:
                    continue
                eventType = _structureTransitionType(entry.get("textComparablePathKey"), fromPaths, toPaths)
                if changedOnly and eventType == "stable":
                    continue
                addedPaths, removedPaths = _changedPaths(fromPaths, toPaths)
                rows.append(
                    {
                        "topic": entry.get("topic"),
                        "textNodeType": entry.get("textNodeType"),
                        "textLevel": entry.get("textLevel"),
                        "cadenceScope": entry.get("cadenceScope"),
                        "textComparablePathKey": entry.get("textComparablePathKey"),
                        "textComparableParentPathKey": entry.get("textComparableParentPathKey"),
                        "periodLane": lane,
                        "fromPeriod": fromPeriod,
                        "toPeriod": toPeriod,
                        "fromPathCount": int(pathCounts[fromIdx]),
                        "toPathCount": int(pathCounts[toIdx]),
                        "fromPaths": fromPaths,
                        "toPaths": toPaths,
                        "addedPaths": addedPaths,
                        "removedPaths": removedPaths,
                        "eventType": eventType,
                    }
                )

    if not rows:
        return _emptyStructureEventsFrame()
    return pl.DataFrame(rows, schema=_emptyStructureEventsFrame().schema).sort(
        ["topic", "textComparablePathKey", "fromPeriod", "toPeriod", "textNodeType", "textLevel"]
    )


def structureSummary(
    df: pl.DataFrame | None,
    *,
    topic: str | None = None,
    cadenceScope: str = "all",
    includeMixed: bool = True,
    nodeType: str | None = None,
) -> pl.DataFrame:
    registry = structureRegistry(
        df,
        topic=topic,
        cadenceScope=cadenceScope,
        includeMixed=includeMixed,
        nodeType=nodeType,
    )
    if registry.is_empty():
        return _emptyStructureSummaryFrame()

    groupCols = _structureGroupColumns()
    summary = registry.select(
        groupCols
        + [
            "structurePattern",
            "hasCollision",
            "activePeriodCount",
            "activePeriods",
            "latestPathCount",
            "multiPathPeriods",
        ]
    ).with_columns(
        [
            pl.col("activePeriods").list.last().alias("latestPeriod"),
            pl.col("activePeriods")
            .list.last()
            .map_elements(_periodLane, return_dtype=pl.Utf8)
            .alias("latestPeriodLane"),
        ]
    )
    summary = _normalizeStructureGroupDtypes(summary)

    events = structureEvents(
        df,
        topic=topic,
        cadenceScope=cadenceScope,
        includeMixed=includeMixed,
        changedOnly=True,
        nodeType=nodeType,
    )
    if not events.is_empty():
        eventSummary = (
            events.with_columns(
                pl.col("toPeriod").map_elements(periodOrderValue, return_dtype=pl.Int64).alias("toOrder")
            )
            .sort(groupCols + ["toOrder"])
            .group_by(groupCols, maintain_order=True)
            .agg(
                [
                    pl.len().alias("eventCount"),
                    pl.col("eventType").last().alias("latestEventType"),
                    pl.col("fromPeriod").last().alias("latestEventFromPeriod"),
                    pl.col("toPeriod").last().alias("latestEventToPeriod"),
                    pl.col("periodLane").last().alias("latestEventLane"),
                ]
            )
        )
        eventSummary = _normalizeStructureGroupDtypes(eventSummary)
        summary = summary.join(eventSummary, on=groupCols, how="left", nulls_equal=True)
    else:
        summary = summary.with_columns(
            [
                pl.lit(0).cast(pl.Int64).alias("eventCount"),
                pl.lit(None, dtype=pl.Utf8).alias("latestEventType"),
                pl.lit(None, dtype=pl.Utf8).alias("latestEventFromPeriod"),
                pl.lit(None, dtype=pl.Utf8).alias("latestEventToPeriod"),
                pl.lit(None, dtype=pl.Utf8).alias("latestEventLane"),
            ]
        )

    if "eventCount" in summary.columns:
        summary = summary.with_columns(pl.col("eventCount").fill_null(0))

    for colName in ["latestEventType", "latestEventFromPeriod", "latestEventToPeriod", "latestEventLane"]:
        if colName not in summary.columns:
            summary = summary.with_columns(pl.lit(None, dtype=pl.Utf8).alias(colName))

    return summary.sort(["topic", "textComparablePathKey", "textNodeType", "textLevel", "cadenceScope"])


def structureChanges(
    df: pl.DataFrame | None,
    *,
    topic: str | None = None,
    cadenceScope: str = "all",
    includeMixed: bool = True,
    nodeType: str | None = None,
    latestOnly: bool = True,
    changedOnly: bool = True,
) -> pl.DataFrame:
    summary = structureSummary(
        df,
        topic=topic,
        cadenceScope=cadenceScope,
        includeMixed=includeMixed,
        nodeType=nodeType,
    )
    if summary.is_empty():
        return _emptyStructureChangesFrame()

    allowedAnchorLanes = _allowedStructurePeriodLanes(cadenceScope)
    latestPeriods = [
        period
        for period in summary["latestPeriod"].to_list()
        if isinstance(period, str)
        and period
        and (allowedAnchorLanes is None or _periodLane(period) in allowedAnchorLanes)
    ]
    anchorPeriod = max(latestPeriods, key=periodOrderValue) if latestPeriods else None
    anchorLane = _periodLane(anchorPeriod)

    changes = summary.with_columns(
        [
            pl.lit(anchorPeriod, dtype=pl.Utf8).alias("anchorPeriod"),
            pl.lit(anchorLane, dtype=pl.Utf8).alias("anchorPeriodLane"),
            (pl.col("latestPeriod") == anchorPeriod).alias("isLatest"),
            (pl.col("latestPeriod") != anchorPeriod).alias("isStale"),
            pl.col("structurePattern").map_elements(_structurePatternRank, return_dtype=pl.Int64).alias("_patternRank"),
        ]
    )

    if changedOnly:
        changes = changes.filter(pl.col("eventCount") > 0)
    if latestOnly:
        changes = changes.filter(pl.col("isLatest"))
    if changes.is_empty():
        return _emptyStructureChangesFrame()

    return (
        changes.sort(
            ["isLatest", "eventCount", "_patternRank", "latestPathCount", "textComparablePathKey"],
            descending=[True, True, True, True, False],
        )
        .drop("_patternRank")
        .select(_emptyStructureChangesFrame().columns)
    )


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
        topicRows = _reportRowsToTopicRows(subset, ccol)
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
            comparablePathKey, comparableParentPathKey = _comparablePathInfo(
                topic,
                str(row.get("textSemanticPathKey") or row.get("textPathKey") or "") or None,
            )
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
                    "textComparablePathKey": comparablePathKey,
                    "textComparableParentPathKey": comparableParentPathKey,
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
        "textComparablePathKey": pl.Utf8,
        "textComparableParentPathKey": pl.Utf8,
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

    dataColumns: dict[str, list[object]] = {col: [] for col in schema}
    sortedTopics = [topic for topic, _ in sorted(topicFirstSeq.items(), key=lambda x: x[1])]

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

            dataColumns["chapter"].append(topicChapter.get(topic))
            dataColumns["topic"].append(topic)
            dataColumns["blockType"].append(str(meta.get("blockType") or "text"))
            dataColumns["blockOrder"].append(blockOrder)
            dataColumns["sourceBlockOrder"].append(
                int(orderInfo.get("sourceBlockOrder") or meta.get("sourceBlockOrder") or 0)
            )
            dataColumns["textNodeType"].append(
                str(meta["textNodeType"]) if isinstance(meta.get("textNodeType"), str) else None
            )
            dataColumns["textStructural"].append(
                bool(meta["textStructural"]) if isinstance(meta.get("textStructural"), bool) else None
            )
            dataColumns["textLevel"].append(int(meta["textLevel"]) if isinstance(meta.get("textLevel"), int) else None)
            dataColumns["textPath"].append(str(meta["textPath"]) if isinstance(meta.get("textPath"), str) else None)
            dataColumns["textPathKey"].append(
                str(meta["textPathKey"]) if isinstance(meta.get("textPathKey"), str) else None
            )
            dataColumns["textParentPathKey"].append(
                str(meta["textParentPathKey"]) if isinstance(meta.get("textParentPathKey"), str) else None
            )
            dataColumns["textPathVariantCount"].append(len(pathVariants))
            dataColumns["textPathVariants"].append(pathVariants or None)
            dataColumns["textParentPathVariants"].append(parentPathVariants or None)
            dataColumns["textSemanticPathKey"].append(
                str(meta["textSemanticPathKey"]) if isinstance(meta.get("textSemanticPathKey"), str) else None
            )
            dataColumns["textSemanticParentPathKey"].append(
                str(meta["textSemanticParentPathKey"])
                if isinstance(meta.get("textSemanticParentPathKey"), str)
                else None
            )
            dataColumns["textComparablePathKey"].append(
                str(meta["textComparablePathKey"]) if isinstance(meta.get("textComparablePathKey"), str) else None
            )
            dataColumns["textComparableParentPathKey"].append(
                str(meta["textComparableParentPathKey"])
                if isinstance(meta.get("textComparableParentPathKey"), str)
                else None
            )
            dataColumns["textSemanticPathVariants"].append(semanticPathVariants or None)
            dataColumns["textSemanticParentPathVariants"].append(semanticParentPathVariants or None)
            dataColumns["segmentKey"].append(str(meta.get("segmentKey") or ""))
            dataColumns["segmentOrder"].append(int(meta.get("segmentOrder") or 0))
            dataColumns["segmentOccurrence"].append(
                int(orderInfo.get("segmentOccurrence") or meta.get("segmentOccurrence") or 1)
            )
            dataColumns["cadenceKey"].append(str(cadenceMeta.get("cadenceKey") or "none"))
            dataColumns["cadenceScope"].append(str(cadenceMeta.get("cadenceScope") or "none"))
            dataColumns["annualPeriodCount"].append(int(cadenceMeta.get("annualPeriodCount") or 0))
            dataColumns["quarterlyPeriodCount"].append(int(cadenceMeta.get("quarterlyPeriodCount") or 0))
            dataColumns["latestAnnualPeriod"].append(
                str(cadenceMeta["latestAnnualPeriod"])
                if isinstance(cadenceMeta.get("latestAnnualPeriod"), str)
                else None
            )
            dataColumns["latestQuarterlyPeriod"].append(
                str(cadenceMeta["latestQuarterlyPeriod"])
                if isinstance(cadenceMeta.get("latestQuarterlyPeriod"), str)
                else None
            )
            dataColumns["sourceTopic"].append(
                str(meta["sourceTopic"]) if isinstance(meta.get("sourceTopic"), str) else None
            )
            periodMap = topicMap.get(key, {})
            for period in validPeriods:
                dataColumns[period].append(periodMap.get(period))

    return pl.DataFrame(dataColumns, schema=schema)
