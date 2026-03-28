"""sections 기반 표 세분화 extractor."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import polars as pl

from dartlab.providers.dart.docs.sections._common import sortPeriods


@dataclass(frozen=True)
class _TopicSelector:
    sourceTopic: str
    detailTopics: tuple[str, ...] = ()


_TOPIC_SELECTORS: dict[str, _TopicSelector] = {
    "segments": _TopicSelector(sourceTopic="segmentFinancialSummary"),
    # 비용의 성격별 분류는 currently financialNotes detail layer에서 가장 안정적으로 회수된다.
    "costByNature": _TopicSelector(
        sourceTopic="financialNotes",
        detailTopics=("noteManufacturingCostDetail",),
    ),
}


@dataclass(frozen=True)
class TopicSubtables:
    """특정 topic의 테이블 블록을 long/wide/summary 세 가지 형태로 담는 컨테이너."""

    topic: str
    long: pl.DataFrame
    wide: pl.DataFrame
    summary: pl.DataFrame


def _resolvedTopic(topic: str) -> str:
    selector = _TOPIC_SELECTORS.get(topic)
    return selector.sourceTopic if selector is not None else topic


def _normalizeSubtopic(record: dict[str, object]) -> str:
    detail = record.get("detailTopic")
    if isinstance(detail, str) and detail:
        return detail

    semantic = record.get("semanticTopic")
    if isinstance(semantic, str) and semantic:
        return semantic

    label = str(record.get("blockLabel") or "").strip()
    if label and label != "(root)":
        return label

    return str(record.get("topic") or "unknown")


def topicSubtables(blocks: pl.DataFrame | None, topic: str) -> TopicSubtables | None:
    """retrievalBlocks에서 해당 topic의 테이블을 추출하여 TopicSubtables로 반환한다."""
    if blocks is None or blocks.is_empty():
        return None

    resolved = _resolvedTopic(topic)
    selector = _TOPIC_SELECTORS.get(topic)
    subset = blocks.filter(
        pl.col("topic") == resolved,
        pl.col("blockType") == "table",
        pl.col("blockText").is_not_null(),
    ).sort(
        ["periodOrder", "sectionOrder", "blockIdx"],
        descending=[True, False, False],
    )
    if selector is not None and selector.detailTopics:
        subset = subset.filter(pl.col("detailTopic").is_in(selector.detailTopics))
    if subset.is_empty():
        return None

    order_map: dict[str, int] = {}
    rows: list[dict[str, object]] = []
    for record in subset.to_dicts():
        subtopic = _normalizeSubtopic(record)
        if subtopic not in order_map:
            order_map[subtopic] = len(order_map) + 1
        rows.append(
            {
                "topic": topic,
                "sourceTopic": resolved,
                "subtopic": subtopic,
                "subtopicOrder": order_map[subtopic],
                "period": str(record["period"]),
                "periodOrder": int(record["periodOrder"]),
                "sectionOrder": int(record["sectionOrder"]),
                "blockIdx": int(record["blockIdx"]),
                "blockLabel": record.get("blockLabel"),
                "semanticTopic": record.get("semanticTopic"),
                "detailTopic": record.get("detailTopic"),
                "tableText": str(record.get("blockText") or ""),
                "chars": len(str(record.get("blockText") or "")),
            }
        )

    long_df = pl.DataFrame(
        rows,
        schema={
            "topic": pl.Utf8,
            "sourceTopic": pl.Utf8,
            "subtopic": pl.Utf8,
            "subtopicOrder": pl.Int64,
            "period": pl.Utf8,
            "periodOrder": pl.Int64,
            "sectionOrder": pl.Int64,
            "blockIdx": pl.Int64,
            "blockLabel": pl.Utf8,
            "semanticTopic": pl.Utf8,
            "detailTopic": pl.Utf8,
            "tableText": pl.Utf8,
            "chars": pl.Int64,
        },
        strict=False,
    ).sort(
        ["subtopicOrder", "periodOrder", "sectionOrder", "blockIdx"],
        descending=[False, True, False, False],
    )

    periods = sortPeriods(long_df.get_column("period").unique().to_list())
    merged = (
        long_df.group_by(["topic", "sourceTopic", "subtopic", "subtopicOrder", "period"])
        .agg(
            pl.col("tableText").implode().list.join("\n\n").alias("tableText"),
        )
        .sort(["subtopicOrder", "period"], descending=[False, True])
    )
    wide_df = (
        merged.pivot(
            on="period",
            index=["topic", "sourceTopic", "subtopic", "subtopicOrder"],
            values="tableText",
        )
        .select(
            [
                "topic",
                "sourceTopic",
                "subtopic",
                "subtopicOrder",
                *[p for p in periods if p in merged["period"].unique().to_list()],
            ]
        )
        .sort("subtopicOrder")
    )

    summary_df = (
        long_df.group_by(["topic", "sourceTopic", "subtopic", "subtopicOrder"])
        .agg(
            pl.len().alias("periodCount"),
            pl.col("chars").mean().round(0).alias("avgChars"),
            pl.col("semanticTopic").drop_nulls().n_unique().alias("semanticVariants"),
            pl.col("detailTopic").drop_nulls().n_unique().alias("detailVariants"),
        )
        .sort("subtopicOrder")
    )

    return TopicSubtables(topic=topic, long=long_df, wide=wide_df, summary=summary_df)


# ---------------------------------------------------------------------------
# ParsedSubtopicTable — subtopic wide 셀의 markdown table → 구조화 DataFrame
# ---------------------------------------------------------------------------

_RE_NORMALIZE_KO = re.compile(r"(?<=[\uAC00-\uD7A3])\s+(?=[\uAC00-\uD7A3])")
_RE_CURRENT_PERIOD = re.compile(r"(당기|당기말|당반기|당분기|현재|전체)")
_RE_PREV_PERIOD = re.compile(r"(전기|전반기|전분기)")


@dataclass(frozen=True)
class ParsedSubtopicTable:
    """subtopic wide 셀의 markdown table을 파싱한 결과."""

    subtopic: str
    df: pl.DataFrame
    unit: str | None = None
    pattern: str | None = None
    parsedPeriods: list[str] = field(default_factory=list)
    failedPeriods: list[str] = field(default_factory=list)


def _normalizeName(name: str) -> str:
    """항목명 정규화. 한글 사이 공백 제거."""
    return _RE_NORMALIZE_KO.sub("", name.strip())


def _pickValue(values: list[str]) -> str:
    """값 리스트에서 대표값 선택. 마지막 유효 숫자를 사용."""
    for v in reversed(values):
        if v and v.strip() and v.strip() not in ("-", ""):
            return v
    return values[0] if values else ""


def _isCurrentPeriod(period: str) -> bool:
    """당기 계열 period인지 판정. 전기/전기말은 제외."""
    if _RE_PREV_PERIOD.search(period):
        return False
    return bool(_RE_CURRENT_PERIOD.search(period))


def _parseOneCellTable(
    cellText: str,
    *,
    numeric: bool = False,
) -> tuple[list[dict[str, str | float | None]], str | None, str | None]:
    """단일 셀의 markdown table text → items 리스트.

    Returns:
        (items, unitLabel, pattern)
        items: [{"name": str, "value": str|float|None}, ...]
    """
    from dartlab.core.tableParser import (
        detectUnitLabel,
        extractRawTables,
        parseAmount,
        parseNotesTable,
    )

    if not cellText or not cellText.strip():
        return [], None, None

    unitLabel = detectUnitLabel(cellText)

    # parseNotesTable은 extractRawTables 내부 사용
    parsed = parseNotesTable(cellText)
    if parsed:
        # 당기 블록 선택
        currentBlock = None
        for p in parsed:
            if _isCurrentPeriod(p["period"]):
                currentBlock = p
                break
        if currentBlock is None:
            currentBlock = parsed[0]

        items: list[dict[str, str | float | None]] = []
        for item in currentBlock["items"]:
            name = _normalizeName(item["name"])
            if not name:
                continue
            rawVal = _pickValue(item["values"])
            if numeric:
                items.append({"name": name, "value": parseAmount(rawVal)})
            else:
                items.append({"name": name, "value": rawVal})
        return items, unitLabel, currentBlock["pattern"]

    # parseNotesTable 실패 시 extractRawTables fallback
    tables = extractRawTables(cellText)
    if not tables:
        return [], unitLabel, None

    items = []
    for row in tables[0]["rows"]:
        name = _normalizeName(row[0]) if row else ""
        if not name:
            continue
        values = row[1:] if len(row) > 1 else []
        rawVal = _pickValue(values) if values else ""
        if numeric:
            items.append({"name": name, "value": parseAmount(rawVal)})
        else:
            items.append({"name": name, "value": rawVal})
    return items, unitLabel, "raw"


def _mergeAcrossPeriods(
    periodItems: dict[str, list[dict[str, str | float | None]]],
    *,
    numeric: bool = False,
) -> pl.DataFrame | None:
    """기간별 items를 합산하여 항목 × 기간 DataFrame 구축."""
    if not periodItems:
        return None

    allNames: list[str] = []
    nameSet: set[str] = set()
    for items in periodItems.values():
        for item in items:
            name = str(item["name"])
            if name not in nameSet:
                allNames.append(name)
                nameSet.add(name)

    if not allNames:
        return None

    periods = sortPeriods(list(periodItems.keys()))

    rows: list[dict[str, object]] = []
    for name in allNames:
        row: dict[str, object] = {"항목": name}
        for period in periods:
            items = periodItems.get(period, [])
            value = None
            for item in items:
                if item["name"] == name:
                    value = item["value"]
                    break
            row[period] = value
        rows.append(row)

    schema: dict[str, type] = {"항목": pl.Utf8}
    valType = pl.Float64 if numeric else pl.Utf8
    for period in periods:
        schema[period] = valType

    return pl.DataFrame(rows, schema=schema, strict=False)


def parseSubtopicTable(
    subtables: TopicSubtables,
    subtopic: str | None = None,
    *,
    numeric: bool = False,
) -> ParsedSubtopicTable | None:
    """subtopic wide의 특정 subtopic 행에서 markdown table을 파싱.

    Args:
        subtables: topicSubtables()가 반환한 TopicSubtables
        subtopic: 파싱할 subtopic 이름 (None이면 첫 번째 subtopic)
        numeric: True이면 parseAmount()로 숫자 변환

    Returns:
        ParsedSubtopicTable 또는 파싱 실패 시 None
    """
    wide = subtables.wide
    if wide.is_empty():
        return None

    metaCols = {"topic", "sourceTopic", "subtopic", "subtopicOrder"}
    periodCols = [c for c in wide.columns if c not in metaCols]

    if not periodCols:
        return None

    # subtopic 선택
    if subtopic is None:
        targetRow = wide.row(0, named=True)
        subtopic = str(targetRow.get("subtopic", ""))
    else:
        matched = wide.filter(pl.col("subtopic") == subtopic)
        if matched.is_empty():
            return None
        targetRow = matched.row(0, named=True)

    # 각 기간별 파싱
    periodItems: dict[str, list[dict[str, str | float | None]]] = {}
    parsedPeriods: list[str] = []
    failedPeriods: list[str] = []
    firstUnit: str | None = None
    firstPattern: str | None = None

    for col in periodCols:
        cellText = targetRow.get(col)
        if cellText is None or (isinstance(cellText, str) and not cellText.strip()):
            continue

        items, unitLabel, pattern = _parseOneCellTable(
            str(cellText),
            numeric=numeric,
        )
        if items:
            periodItems[col] = items
            parsedPeriods.append(col)
            if firstUnit is None and unitLabel:
                firstUnit = unitLabel
            if firstPattern is None and pattern:
                firstPattern = pattern
        else:
            failedPeriods.append(col)

    df = _mergeAcrossPeriods(periodItems, numeric=numeric)
    if df is None:
        return None

    return ParsedSubtopicTable(
        subtopic=subtopic,
        df=df,
        unit=firstUnit,
        pattern=firstPattern,
        parsedPeriods=parsedPeriods,
        failedPeriods=failedPeriods,
    )
