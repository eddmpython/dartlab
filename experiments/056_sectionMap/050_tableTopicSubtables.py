"""sections 기반 table-bearing topic 세분화 실험.

목표:
- docs sections/retrievalBlocks가 이미 수평화한 topic을 다시 읽는다.
- table block이 있는 topic을 semantic/detail/blockLabel 기준 subtopic으로 쪼갠다.
- show(topic) 대신 show(subtopic) 경로가 현실적인지 확인한다.

실행:
    ./.venv-wsl/bin/python experiments/056_sectionMap/050_tableTopicSubtables.py
    ./.venv-wsl/bin/python experiments/056_sectionMap/050_tableTopicSubtables.py 005930 riskDerivative,salesOrder
"""

from __future__ import annotations

import sys
from pathlib import Path

import polars as pl

from dartlab import Company
from dartlab.providers.dart.docs.sections.views import sortPeriods

DEFAULT_STOCK_CODE = "005930"
DEFAULT_TOPICS = [
    "riskDerivative",
    "salesOrder",
    "rawMaterial",
    "segmentFinancialSummary",
    "majorContractsAndRnd",
]
OUTPUT_DIR = Path("data/dart/docs/sectionsViews")


def normalize_subtopic(record: dict[str, object]) -> str:
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


def build_subtable_frames(stock_code: str, topics: list[str]) -> tuple[pl.DataFrame, pl.DataFrame]:
    c = Company(stock_code)
    blocks = c.docs.retrievalBlocks
    if blocks is None or blocks.is_empty():
        empty = pl.DataFrame()
        return empty, empty

    subset = (
        blocks
        .filter(
            pl.col("topic").is_in(topics),
            pl.col("blockType") == "table",
            pl.col("blockText").is_not_null(),
        )
        .sort(["topic", "periodOrder", "sectionOrder", "blockIdx"], descending=[False, True, False, False])
    )

    if subset.is_empty():
        empty = pl.DataFrame()
        return empty, empty

    rows: list[dict[str, object]] = []
    for record in subset.to_dicts():
        rows.append(
            {
                "stockCode": stock_code,
                "topic": record["topic"],
                "subtopic": normalize_subtopic(record),
                "period": record["period"],
                "periodOrder": record["periodOrder"],
                "sourceTopic": record.get("sourceTopic"),
                "blockLabel": record.get("blockLabel"),
                "semanticTopic": record.get("semanticTopic"),
                "detailTopic": record.get("detailTopic"),
                "chars": len(str(record.get("blockText") or "")),
                "tableText": record.get("blockText"),
            }
        )

    long_df = pl.DataFrame(
        rows,
        schema={
            "stockCode": pl.Utf8,
            "topic": pl.Utf8,
            "subtopic": pl.Utf8,
            "period": pl.Utf8,
            "periodOrder": pl.Int64,
            "sourceTopic": pl.Utf8,
            "blockLabel": pl.Utf8,
            "semanticTopic": pl.Utf8,
            "detailTopic": pl.Utf8,
            "chars": pl.Int64,
            "tableText": pl.Utf8,
        },
        strict=False,
    ).sort(
        ["topic", "subtopic", "periodOrder"],
        descending=[False, False, True],
    )

    periods = sortPeriods(long_df.get_column("period").unique().to_list())
    merged = (
        long_df
        .group_by(["topic", "subtopic", "period"])
        .agg(
            pl.col("tableText").implode().list.join("\n\n").alias("tableText"),
        )
        .sort(["topic", "subtopic", "period"])
    )
    wide = merged.pivot(on="period", index=["topic", "subtopic"], values="tableText")
    existing = [period for period in periods if period in wide.columns]
    wide = wide.select(["topic", "subtopic", *existing])
    return long_df, wide


def summarize(long_df: pl.DataFrame) -> pl.DataFrame:
    if long_df.is_empty():
        return pl.DataFrame()

    return (
        long_df
        .group_by(["topic", "subtopic"])
        .agg(
            pl.len().alias("periodCount"),
            pl.col("chars").mean().round(0).alias("avgChars"),
            pl.col("sourceTopic").drop_nulls().n_unique().alias("sourceVariants"),
        )
        .sort(["topic", "periodCount", "subtopic"], descending=[False, True, False])
    )


def save(df: pl.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(path)


def main() -> None:
    stock_code = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_STOCK_CODE
    topics = (
        [item.strip() for item in sys.argv[2].split(",") if item.strip()]
        if len(sys.argv) > 2
        else DEFAULT_TOPICS
    )

    long_df, wide_df = build_subtable_frames(stock_code, topics)
    summary_df = summarize(long_df)

    print("\n[subtable summary]")
    print(summary_df)
    print("\n[subtable wide preview]")
    print(wide_df.head(30))

    save(long_df, OUTPUT_DIR / f"{stock_code}.tableSubtopics.long.parquet")
    save(wide_df, OUTPUT_DIR / f"{stock_code}.tableSubtopics.wide.parquet")
    save(summary_df, OUTPUT_DIR / f"{stock_code}.tableSubtopics.summary.parquet")


if __name__ == "__main__":
    main()
