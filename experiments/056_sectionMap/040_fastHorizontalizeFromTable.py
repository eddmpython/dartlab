"""
실험 ID: 056-040
실험명: 학습 테이블 기반 빠른 수평화

목적:
- 미리 생성한 canonical row 학습 테이블을 읽어 단일 종목을 즉시 수평화한다.
- 원본 docs parquet 전체를 다시 스캔하지 않고도 `topic x period`와 backfill 후보를 빠르게 확인한다.

가설:
1. canonicalRows.parquet만 있으면 단일 종목 수평화는 빠르게 수행된다.
2. 학습 테이블 참조 방식이 최종 운영 형태에 더 가깝다.

방법:
1. `output/canonicalRows.parquet`를 읽는다.
2. 입력 종목의 row만 필터한다.
3. `topic x period` pivot과 latest annual teacher topic, backfill 후보를 계산한다.

결과 (실험 후 작성):

결론:

실험일: 2026-03-12
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import polars as pl


def table_path() -> Path:
    return Path(__file__).resolve().parent / "output" / "canonicalRows.parquet"


def chapter_path() -> Path:
    return Path(__file__).resolve().parent / "output" / "chapterSources.parquet"


def chapter_two_rule_path() -> Path:
    return Path(__file__).resolve().parent / "output" / "projectionRules.chapterII.json"


def load_stock_rows(stock_code: str) -> pl.DataFrame:
    path = table_path()
    if not path.exists():
        return pl.DataFrame()
    return pl.read_parquet(path).filter(pl.col("stockCode") == stock_code).sort(["periodOrder", "chapter", "topic"])


def load_stock_chapters(stock_code: str) -> pl.DataFrame:
    path = chapter_path()
    if not path.exists():
        return pl.DataFrame()
    return pl.read_parquet(path).filter(pl.col("stockCode") == stock_code).sort(["periodOrder", "chapter"])


def load_projection_rules() -> dict[str, list[str]]:
    path = chapter_two_rule_path()
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def latest_annual_teacher(df: pl.DataFrame) -> pl.DataFrame:
    if df.height == 0:
        return pl.DataFrame()
    annual = df.filter(~pl.col("period").str.contains("Q"))
    if annual.height == 0:
        return pl.DataFrame()
    latest_period = annual.sort("periodOrder", descending=True).get_column("period").to_list()[0]
    return annual.filter(pl.col("period") == latest_period).sort(["chapter", "topic"])


def topic_pivot(df: pl.DataFrame) -> pl.DataFrame:
    if df.height == 0:
        return pl.DataFrame()
    return (
        df.pivot(
            values="topicText",
            index=["chapter", "topic"],
            on="period",
            aggregate_function="first",
        )
        .sort(["chapter", "topic"])
    )


def backfill_candidates(df: pl.DataFrame, chapter_df: pl.DataFrame) -> pl.DataFrame:
    teacher = latest_annual_teacher(df)
    if teacher.height == 0:
        return pl.DataFrame()
    if chapter_df.height == 0:
        return pl.DataFrame()

    periods = df.select(["period", "periodOrder"]).unique().sort("periodOrder").get_column("period").to_list()
    teacher_grid = teacher.select(["chapter", "topic"]).join(pl.DataFrame({"period": periods}), how="cross")
    observed = df.select(["chapter", "topic", "period"]).with_columns(pl.lit(True).alias("hasFine"))

    return (
        teacher_grid.join(observed, on=["chapter", "topic", "period"], how="left")
        .join(
            chapter_df.select(["chapter", "period", "chapterText"]).with_columns(
                (pl.col("chapterText").str.len_chars() > 0).alias("hasChapterText")
            ),
            on=["chapter", "period"],
            how="left",
        )
        .with_columns(
            pl.col("hasFine").fill_null(False),
            pl.col("hasChapterText").fill_null(False),
            ((pl.col("hasFine") == False) & (pl.col("hasChapterText") == True)).alias("backfillCandidate"),
        )
        .group_by(["chapter", "topic"])
        .agg(
            pl.col("hasFine").sum().alias("filledPeriods"),
            pl.col("backfillCandidate").sum().alias("backfillCandidatePeriods"),
            pl.col("period").filter(pl.col("backfillCandidate")).alias("candidatePeriods"),
        )
        .sort(["backfillCandidatePeriods", "filledPeriods", "chapter", "topic"], descending=[True, True, False, False])
    )


def projected_rows(df: pl.DataFrame) -> pl.DataFrame:
    rules = load_projection_rules()
    if not rules:
        return pl.DataFrame()
    out: list[dict[str, object]] = []
    for source_topic, targets in rules.items():
        source = df.filter((pl.col("chapter") == "II") & (pl.col("topic") == source_topic))
        if source.height == 0:
            continue
        for row in source.iter_rows(named=True):
            for target in targets:
                out.append(
                    {
                        "chapter": row["chapter"],
                        "topic": target,
                        "period": row["period"],
                        "periodOrder": row["periodOrder"],
                        "topicText": row["topicText"],
                        "projectionSource": source_topic,
                    }
                )
    return pl.DataFrame(out) if out else pl.DataFrame()


def projected_backfill_summary(df: pl.DataFrame) -> pl.DataFrame:
    teacher = latest_annual_teacher(df)
    projected = projected_rows(df)
    if teacher.height == 0 or projected.height == 0:
        return pl.DataFrame()

    periods = df.select(["period", "periodOrder"]).unique().sort("periodOrder").get_column("period").to_list()
    teacher_grid = teacher.select(["chapter", "topic"]).unique().join(pl.DataFrame({"period": periods}), how="cross")
    observed_key = df.select(["chapter", "topic", "period"]).unique()
    projected_key = projected.select(["chapter", "topic", "period"]).unique()

    observed_summary = (
        observed_key.group_by(["chapter", "topic"])
        .agg(pl.len().alias("observedPeriods"))
    )
    recovered_summary = (
        teacher_grid.join(observed_key, on=["chapter", "topic", "period"], how="anti")
        .join(projected_key, on=["chapter", "topic", "period"], how="inner")
        .group_by(["chapter", "topic"])
        .agg(pl.len().alias("recoveredPeriods"))
    )

    return (
        teacher.select(["chapter", "topic"]).unique()
        .join(observed_summary, on=["chapter", "topic"], how="left")
        .join(recovered_summary, on=["chapter", "topic"], how="left")
        .with_columns(
            pl.col("observedPeriods").fill_null(0),
            pl.col("recoveredPeriods").fill_null(0),
        )
        .sort(["recoveredPeriods", "observedPeriods", "chapter", "topic"], descending=[True, True, False, False])
    )


def main() -> None:
    stock_code = sys.argv[1] if len(sys.argv) > 1 else "005930"
    df = load_stock_rows(stock_code)
    chapter_df = load_stock_chapters(stock_code)

    print("=" * 72)
    print("056-040 학습 테이블 기반 빠른 수평화")
    print("=" * 72)
    print(f"stockCode={stock_code}")
    print(f"rows={df.height}")
    print()

    teacher = latest_annual_teacher(df)
    print("[latest annual teacher]")
    print(teacher.select(["chapter", "topic", "rawTitleVariants"]).head(40))
    print()

    pivot = topic_pivot(df)
    print("[topic x period pivot]")
    if pivot.height == 0:
        print("NO_DATA")
    else:
        preview_cols = pivot.columns[: min(len(pivot.columns), 12)]
        print(pivot.select(preview_cols).head(30))
    print()

    print("[backfill candidates]")
    print(backfill_candidates(df, chapter_df).head(40))
    print()

    print("[projected backfill summary]")
    projected_summary = projected_backfill_summary(df)
    if projected_summary.height == 0:
        print("NO_PROJECTION")
    else:
        print(projected_summary.head(40))
        print()
        print("[chapter II projected summary]")
        print(projected_summary.filter(pl.col("chapter") == "II"))


if __name__ == "__main__":
    main()
