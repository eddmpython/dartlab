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

import gc
import re
from collections.abc import Iterator

import polars as pl

from dartlab.core.dataLoader import loadData
from dartlab.core.reportSelector import selectReport
from dartlab.providers.dart.docs.sections._common import (
    REPORT_KINDS,
    detectContentCol,
    sortPeriods,
)
from dartlab.providers.dart.docs.sections.chunker import parseMajorNum
from dartlab.providers.dart.docs.sections.mapper import mapSectionTitle, stripSectionPrefix
from dartlab.providers.dart.docs.sections.runtime import (
    applyProjections,
    chapterFromMajorNum,
    chapterTeacherTopics,
    detailTopicForTopic,
    projectionSuppressedTopics,
)
from dartlab.providers.dart.docs.sections.textStructure import parseTextStructureWithState

# ── Phase 1 캐시: parquet 로드 + topic 매핑 결과 재사용 ──

_preparedCache: dict[str, "_PreparedRows"] = {}
_PREPARED_CACHE_MAX = 2  # OOM 방지: 최대 2종목


class _PreparedRows:
    """Phase 1 결과 — parquet 로드 + _reportRowsToTopicRows + teacherTopics."""

    __slots__ = ("periodRows", "validPeriods", "teacherTopics")

    def __init__(
        self,
        periodRows: dict[str, list[dict[str, object]]],
        validPeriods: list[str],
        teacherTopics: dict[str, str],
    ):
        self.periodRows = periodRows
        self.validPeriods = validPeriods
        self.teacherTopics = teacherTopics


def _getPrepared(stockCode: str) -> _PreparedRows:
    """Phase 1 결과를 캐싱하여 반환. 같은 종목 반복 호출 시 parquet 재로드 방지."""
    if stockCode in _preparedCache:
        return _preparedCache[stockCode]

    periodRows: dict[str, list[dict[str, object]]] = {}
    validPeriods: list[str] = []
    latestAnnualRows: list[dict[str, object]] | None = None

    for periodKey, reportKind, ccol, subset in iterPeriodSubsets(stockCode):
        validPeriods.append(periodKey)
        topicRows = _reportRowsToTopicRows(subset, ccol)
        periodRows[periodKey] = topicRows
        if reportKind == "annual" and latestAnnualRows is None:
            latestAnnualRows = topicRows

    teacherTopics = chapterTeacherTopics(latestAnnualRows or [])
    validPeriods = sortPeriods(validPeriods)

    prepared = _PreparedRows(periodRows, validPeriods, teacherTopics)

    # LRU 방식: 최대치 초과 시 가장 오래된 항목 제거
    if len(_preparedCache) >= _PREPARED_CACHE_MAX:
        oldest = next(iter(_preparedCache))
        del _preparedCache[oldest]
    _preparedCache[stockCode] = prepared
    return prepared


def clearPreparedCache(stockCode: str | None = None) -> None:
    """Phase 1 캐시 해제. stockCode=None이면 전체 해제."""
    if stockCode is None:
        _preparedCache.clear()
    else:
        _preparedCache.pop(stockCode, None)


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


_SECTIONS_REQUIRED_COLS = [
    "year",
    "report_type",
    "rcept_date",
    "section_order",
    "section_title",
    "section_content",
    "content",
]


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
    df = loadData(stockCode, sinceYear=sinceYear, columns=_SECTIONS_REQUIRED_COLS)
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
                .with_columns(pl.col("section_title").cast(pl.Utf8))
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


_NOTES_TOPICS = frozenset({"financialNotes", "consolidatedNotes"})


def _expandStructuredRows(rows: list[dict[str, object]]) -> Iterator[dict[str, object]]:
    """rows를 text structure로 확장하여 yield한다. occurrence는 인라인 카운트."""
    headingStateByTopic: dict[str, list[dict[str, object]]] = {}
    occurrenceCount: dict[tuple[str, str], int] = {}
    # 주석 topic의 table 블록에 직전 heading 시맨틱 키를 전파하기 위한 상태
    lastHeadingKeyByTopic: dict[str, str] = {}

    hasProjection = False
    for row in rows:
        if row.get("projectionKind") is not None:
            hasProjection = True
            break

    if hasProjection:
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
            # 주석 topic: 직전 heading의 시맨틱 키로 table 블록을 식별 (기간간 정렬)
            lastKey = lastHeadingKeyByTopic.get(topic)
            if topic in _NOTES_TOPICS and lastKey:
                segmentKeyBase = f"table|sem:{lastKey}"
            else:
                segmentKeyBase = f"table|sb:{sourceBlockOrder}"
            baseRow["segmentKeyBase"] = segmentKeyBase
            baseRow["sortOrder"] = orderSeq * 1000
            occKey = (topic, segmentKeyBase)
            occurrenceCount[occKey] = occurrenceCount.get(occKey, 0) + 1
            baseRow["segmentOccurrence"] = occurrenceCount[occKey]
            baseRow["segmentKey"] = f"{segmentKeyBase}|occ:{occurrenceCount[occKey]}"
            yield baseRow
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
        # 주석 topic: heading 시맨틱 키를 기억 (다음 table 블록에 전파)
        if topic in _NOTES_TOPICS and finalHeadings:
            lastLabel = str(finalHeadings[-1].get("label") or "")
            lastSemKey = str(finalHeadings[-1].get("semanticKey") or finalHeadings[-1].get("key") or lastLabel)
            if lastSemKey:
                lastHeadingKeyByTopic[topic] = lastSemKey
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
            baseRow["sortOrder"] = orderSeq * 1000
            occKey = (topic, segmentKeyBase)
            occurrenceCount[occKey] = occurrenceCount.get(occKey, 0) + 1
            baseRow["segmentOccurrence"] = occurrenceCount[occKey]
            baseRow["segmentKey"] = f"{segmentKeyBase}|occ:{occurrenceCount[occKey]}"
            yield baseRow
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
            segmentKeyBase = node["segmentKeyBase"]
            nodeRow["segmentKeyBase"] = segmentKeyBase
            nodeRow["sortOrder"] = (orderSeq * 1000) + int(node["segmentOrder"])
            occKey = (topic, str(segmentKeyBase))
            occurrenceCount[occKey] = occurrenceCount.get(occKey, 0) + 1
            nodeRow["segmentOccurrence"] = occurrenceCount[occKey]
            nodeRow["segmentKey"] = f"{segmentKeyBase}|occ:{occurrenceCount[occKey]}"
            yield nodeRow


def _periodFreq(period: str) -> str:
    if period.endswith("Q1"):
        return "q1"
    if period.endswith("Q2"):
        return "q2"
    if period.endswith("Q3"):
        return "q3"
    if period.endswith("Q4"):
        return "q4"
    return "annual"


def _freqSortKey(freq: str) -> int:
    return {"annual": 0, "q1": 1, "q2": 2, "q3": 3, "q4": 4}.get(freq, 9)


def _rowFreqMeta(periodMap: dict[str, str]) -> dict[str, object]:
    annualPeriods: list[str] = []
    quarterlyPeriods: list[str] = []
    for period, value in periodMap.items():
        if not isinstance(value, str) or not value.strip():
            continue
        suffix = period[-2:]
        if suffix in ("Q1", "Q2", "Q3", "Q4"):
            quarterlyPeriods.append(period)
        else:
            annualPeriods.append(period)

    annualCount = len(annualPeriods)
    quarterlyCount = len(quarterlyPeriods)

    if annualCount == 0 and quarterlyCount == 0:
        return {
            "freqKey": "none",
            "freqScope": "none",
            "annualPeriodCount": 0,
            "quarterlyPeriodCount": 0,
            "latestAnnualPeriod": None,
            "latestQuarterlyPeriod": None,
        }

    if annualCount > 0 and quarterlyCount > 0:
        freqScope = "mixed"
    elif annualCount > 0:
        freqScope = "annual"
    else:
        freqScope = "quarterly"

    freqKeys: list[str] = []
    if annualCount > 0:
        freqKeys.append("annual")
    freqSet = set()
    for p in quarterlyPeriods:
        c = _periodFreq(p)
        if c not in freqSet:
            freqSet.add(c)
            freqKeys.append(c)
    freqKeys.sort(key=_freqSortKey)

    latestAnnual = max(annualPeriods) if annualPeriods else None
    latestQuarterly = max(quarterlyPeriods) if quarterlyPeriods else None

    return {
        "freqKey": ",".join(freqKeys),
        "freqScope": freqScope,
        "annualPeriodCount": annualCount,
        "quarterlyPeriodCount": quarterlyCount,
        "latestAnnualPeriod": latestAnnual,
        "latestQuarterlyPeriod": latestQuarterly,
    }


# ── 분석 함수들은 analysis.py로 이동 ──
# projectFreqRows, semanticRegistry, semanticCollisions,
# structureRegistry, structureCollisions, structureEvents,
# structureSummary, structureChanges


def sections(stockCode: str, topics: set[str] | None = None) -> pl.DataFrame | None:
    """전 기간 보고서 섹션 — (topic, blockType, blockOrder) × period DataFrame.

    텍스트와 테이블을 분리하여 같은 topic이라도 text 행과 table 행으로 나뉜다.

    Args:
        stockCode: 종목코드
        topics: 필요한 topic 집합. None이면 전체.

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
    suppressed = projectionSuppressedTopics()

    prepared = _getPrepared(stockCode)
    validPeriods = prepared.validPeriods
    teacherTopics = prepared.teacherTopics
    # periodRows는 pop으로 소비되므로 shallow copy (list 참조만 복사, row dict는 공유)
    periodRows = dict(prepared.periodRows)
    latestPeriod = validPeriods[-1]

    def _representativePeriodRank(period: str | None) -> int:
        if not isinstance(period, str):
            return -1
        year = int(period[:4])
        quarter = {"Q1": 1, "Q2": 2, "Q3": 3}.get(period[4:], 4)
        return (year * 10) + quarter

    topicChapter: dict[str, str] = {}
    topicFirstSeq: dict[str, tuple[int, int]] = {}

    for _pIdx, periodKey in enumerate(validPeriods):
        projected = applyProjections(
            periodRows.pop(periodKey, []),
            teacherTopics,
        )
        if topics is not None:
            projected = [r for r in projected if r.get("topic") in topics]
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

        # 전체 빌드만 주기적 GC — 부분 빌드는 데이터가 적어 불필요
        if topics is None and _pIdx % 10 == 9:
            gc.collect()

    # 메모리 해제: periodRows는 pop으로 이미 소진, 빈 dict 정리
    del periodRows

    if not validPeriods or not topicMap:
        return None

    freqMetaByKey = {key: _rowFreqMeta(periodMap) for key, periodMap in topicMap.items()}
    topicKeysByTopic: dict[str, list[tuple[str, str]]] = {}
    for key in topicMap.keys():
        topicKeysByTopic.setdefault(key[0], []).append(key)

    topicIndex: dict[str, int] = {}
    for topic_seq in sorted(topicFirstSeq.items(), key=lambda x: x[1]):
        topicIndex[topic_seq[0]] = len(topicIndex)

    _FREQ_SCOPE_PRIORITY = {"mixed": 0, "annual": 1, "quarterly": 2, "none": 3}

    def _topicRowSortKey(k: tuple[str, str]) -> tuple[int, int, int, int, int, int, int, int, str]:
        topic, _segmentKey = k
        majorNum, firstSeq = topicFirstSeq.get(topic, (99, 999999))
        tIdx = topicIndex.get(topic, 999999)
        info = rowOrder.get(k, {})  # noqa: F821 — closure variable
        freqMeta = freqMetaByKey.get(k, {})  # noqa: F821 — closure variable
        return (
            majorNum,
            firstSeq,
            tIdx,
            _FREQ_SCOPE_PRIORITY.get(str(freqMeta.get("freqScope") or "none"), 9),
            int(info.get("latestMissing", 1)),
            int(info.get("latestRank", 999999999)),
            int(info.get("firstRank", 999999999)),
            int(info.get("segmentOccurrence", 1)),
            str(k[1]),
        )

    schema = {
        "chapter": pl.Categorical,
        "topic": pl.Categorical,
        "blockType": pl.Categorical,
        "blockOrder": pl.Int64,
        "sourceBlockOrder": pl.Int64,
        "textNodeType": pl.Categorical,
        "textStructural": pl.Boolean,
        "textLevel": pl.Int64,
        "textPath": pl.Categorical,
        "textPathKey": pl.Categorical,
        "textParentPathKey": pl.Categorical,
        "textPathVariantCount": pl.Int64,
        "textPathVariants": pl.List(pl.Utf8),
        "textParentPathVariants": pl.List(pl.Utf8),
        "textSemanticPathKey": pl.Categorical,
        "textSemanticParentPathKey": pl.Categorical,
        "textComparablePathKey": pl.Categorical,
        "textComparableParentPathKey": pl.Categorical,
        "textSemanticPathVariants": pl.List(pl.Utf8),
        "textSemanticParentPathVariants": pl.List(pl.Utf8),
        "segmentKey": pl.Categorical,
        "segmentOrder": pl.Int64,
        "segmentOccurrence": pl.Int64,
        "freqKey": pl.Categorical,
        "freqScope": pl.Categorical,
        "annualPeriodCount": pl.Int64,
        "quarterlyPeriodCount": pl.Int64,
        "latestAnnualPeriod": pl.Categorical,
        "latestQuarterlyPeriod": pl.Categorical,
        "sourceTopic": pl.Categorical,
    }
    for p in validPeriods:
        schema[p] = pl.Categorical

    dataColumns: dict[str, list[object]] = {col: [] for col in schema}
    sortedTopics = [topic for topic, _ in sorted(topicFirstSeq.items(), key=lambda x: x[1])]

    for topic in sortedTopics:
        topicKeys = sorted(topicKeysByTopic.get(topic, []), key=_topicRowSortKey)
        for blockOrder, key in enumerate(topicKeys):
            meta = rowMeta.get(key, {})
            orderInfo = rowOrder.get(key, {})
            freqMeta = freqMetaByKey.get(key, {})
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
            dataColumns["freqKey"].append(str(freqMeta.get("freqKey") or "none"))
            dataColumns["freqScope"].append(str(freqMeta.get("freqScope") or "none"))
            dataColumns["annualPeriodCount"].append(int(freqMeta.get("annualPeriodCount") or 0))
            dataColumns["quarterlyPeriodCount"].append(int(freqMeta.get("quarterlyPeriodCount") or 0))
            dataColumns["latestAnnualPeriod"].append(
                str(freqMeta["latestAnnualPeriod"]) if isinstance(freqMeta.get("latestAnnualPeriod"), str) else None
            )
            dataColumns["latestQuarterlyPeriod"].append(
                str(freqMeta["latestQuarterlyPeriod"])
                if isinstance(freqMeta.get("latestQuarterlyPeriod"), str)
                else None
            )
            dataColumns["sourceTopic"].append(
                str(meta["sourceTopic"]) if isinstance(meta.get("sourceTopic"), str) else None
            )
            periodMap = topicMap.pop(key, None)
            if periodMap:
                for period in validPeriods:
                    dataColumns[period].append(periodMap.get(period))
            else:
                for period in validPeriods:
                    dataColumns[period].append(None)
            # 소비한 중간 dict 항목 즉시 해제
            rowMeta.pop(key, None)
            rowOrder.pop(key, None)
            pathVariantsByKey.pop(key, None)
            parentPathVariantsByKey.pop(key, None)
            semanticPathVariantsByKey.pop(key, None)
            semanticParentPathVariantsByKey.pop(key, None)
            freqMetaByKey.pop(key, None)

    # 메모리 해제: DataFrame 생성 전 잔여 dict 퇴출
    del topicMap, rowMeta, rowOrder
    del pathVariantsByKey, parentPathVariantsByKey
    del semanticPathVariantsByKey, semanticParentPathVariantsByKey
    del freqMetaByKey

    if topics is None:
        gc.collect()

    return pl.DataFrame(dataColumns, schema=schema)
