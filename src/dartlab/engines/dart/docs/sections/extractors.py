"""sections 기반 표 세분화 extractor."""

from __future__ import annotations

from dataclasses import dataclass

import polars as pl

from dartlab.engines.dart.docs.sections.views import sortPeriods


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
    if blocks is None or blocks.is_empty():
        return None

    resolved = _resolvedTopic(topic)
    selector = _TOPIC_SELECTORS.get(topic)
    subset = (
        blocks
        .filter(
            pl.col("topic") == resolved,
            pl.col("blockType") == "table",
            pl.col("blockText").is_not_null(),
        )
        .sort(
            ["periodOrder", "sectionOrder", "blockIdx"],
            descending=[True, False, False],
        )
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
        long_df
        .group_by(["topic", "sourceTopic", "subtopic", "subtopicOrder", "period"])
        .agg(
            pl.col("tableText").implode().list.join("\n\n").alias("tableText"),
        )
        .sort(["subtopicOrder", "period"], descending=[False, True])
    )
    wide_df = (
        merged
        .pivot(
            on="period",
            index=["topic", "sourceTopic", "subtopic", "subtopicOrder"],
            values="tableText",
        )
        .select(["topic", "sourceTopic", "subtopic", "subtopicOrder", *[p for p in periods if p in merged["period"].unique().to_list()]])
        .sort("subtopicOrder")
    )

    summary_df = (
        long_df
        .group_by(["topic", "sourceTopic", "subtopic", "subtopicOrder"])
        .agg(
            pl.len().alias("periodCount"),
            pl.col("chars").mean().round(0).alias("avgChars"),
            pl.col("semanticTopic").drop_nulls().n_unique().alias("semanticVariants"),
            pl.col("detailTopic").drop_nulls().n_unique().alias("detailVariants"),
        )
        .sort("subtopicOrder")
    )

    return TopicSubtables(topic=topic, long=long_df, wide=wide_df, summary=summary_df)
