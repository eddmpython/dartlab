"""
실험 ID: 056-038
실험명: scan_parquet 기반 전기간 section retable prototype

목적:
- docs parquet 전체를 Polars `scan_parquet()`로 한 번에 읽어 회사/기간/섹션을 수평화하는 prototype을 만든다.
- 최신 annual의 fine section을 teacher row로 삼고, 과거 coarse period에서 채울 수 있는 backfill 후보를 함께 본다.

가설:
1. 전기간 docs를 하나의 lazy frame으로 읽고 `topic x period` retable을 만들 수 있다.
2. 최신 annual fine topic을 teacher로 두면, 과거/분기 period에서 비는 row 상당수는 같은 chapter의 coarse text로 backfill 후보를 만들 수 있다.
3. 이 구조가 section map 다음 단계인 canonical report table의 직접적인 기반이 된다.

방법:
1. `data/dart/docs/*.parquet`를 `scan_parquet()`로 읽는다.
2. stockCode, period, chapter, normalizedTitle, canonicalTopic을 lazy expression으로 계산한다.
3. leaf row를 `stockCode / canonicalTopic / period` 기준으로 병합하고 pivot한다.
4. 선택 종목의 latest annual을 teacher row로 두고, chapter 기준 coarse backfill 후보를 계산한다.

결과 (실험 후 작성):
- 삼성전자(005930) 기준 period 수: `105`
- latest annual teacher topic 수: `100`
- chapter text가 존재하는 missing fine cell 수를 직접 계산 가능

결론:
- 056의 본체는 title 매핑만이 아니라, `scan_parquet()` 위에서 전체 기간 section을 retable하는 것이다.
- 이후 단계는 이 retable 위에 semantic unit 분해와 coarse-to-fine projection을 올리면 된다.

실험일: 2026-03-12
"""

from __future__ import annotations

import sys
from pathlib import Path

import polars as pl

from dartlab.engines.dart.docs.sections.mapper import loadSectionMappings


def root_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def docs_glob() -> str:
    return str(root_dir() / "data" / "dart" / "docs" / "*.parquet")


def stock_path(stock_code: str) -> str:
    return str(root_dir() / "data" / "dart" / "docs" / f"{stock_code}.parquet")


def period_expr() -> pl.Expr:
    year = pl.col("report_type").str.extract(r"\((\d{4})\.\d{2}\)", 1)
    return (
        pl.when(pl.col("report_type").str.contains(r"분기보고서.*\d{4}\.03"))
        .then(year + pl.lit("Q1"))
        .when(pl.col("report_type").str.contains("반기보고서"))
        .then(year + pl.lit("Q2"))
        .when(pl.col("report_type").str.contains(r"분기보고서.*\d{4}\.09"))
        .then(year + pl.lit("Q3"))
        .when(pl.col("report_type").str.contains("사업보고서"))
        .then(year)
        .otherwise(None)
    )


def period_order_expr() -> pl.Expr:
    year_part = pl.col("period").str.slice(0, 4).cast(pl.Int32)
    return (
        pl.when(pl.col("period").str.contains("Q1"))
        .then(year_part * 10 + 1)
        .when(pl.col("period").str.contains("Q2"))
        .then(year_part * 10 + 2)
        .when(pl.col("period").str.contains("Q3"))
        .then(year_part * 10 + 3)
        .otherwise(year_part * 10 + 4)
    )


def normalized_title_expr() -> pl.Expr:
    return (
        pl.col("section_title")
        .cast(pl.Utf8)
        .str.strip_chars()
        .str.replace(r"^\s*(?:(?:\d+|[가-힣])[.)]\s*|\(\d+\)\s*|[①-⑳]\s*)+", "")
        .str.replace(r"^\([^)]*업\)", "")
        .str.replace(r"^\s*(?:(?:\d+|[가-힣])[.)]\s*|\(\d+\)\s*|[①-⑳]\s*)+", "")
        .str.replace_all("ㆍ", ",")
        .str.replace_all(r"\s+", "")
    )


def scan_rows() -> pl.LazyFrame:
    scan = pl.scan_parquet(docs_glob(), include_file_paths="sourcePath").with_columns(
        pl.col("sourcePath").str.extract(r"([^/\\]+)\.parquet$", 1).alias("stockCode"),
        pl.col("section_title").cast(pl.Utf8),
        pl.col("section_content").cast(pl.Utf8).alias("text"),
        period_expr().alias("period"),
    )
    return _prepare_scan(scan)


def scan_stock_rows(stock_code: str) -> pl.LazyFrame:
    scan = pl.scan_parquet(stock_path(stock_code)).with_columns(
        pl.lit(stock_code).alias("stockCode"),
        pl.col("section_title").cast(pl.Utf8),
        pl.col("section_content").cast(pl.Utf8).alias("text"),
        period_expr().alias("period"),
    )
    return _prepare_scan(scan)


def _prepare_scan(scan: pl.LazyFrame) -> pl.LazyFrame:
    
    chapter_expr = (
        pl.when(pl.col("section_title").str.contains(r"^\s*([IVX]{1,5})\.\s*"))
        .then(pl.col("section_title").str.extract(r"^\s*([IVX]{1,5})\.\s*", 1))
        .otherwise(None)
        .forward_fill()
        .over(["stockCode", "period"])
    )

    return (
        scan.filter(pl.col("period").is_not_null())
        .sort(["stockCode", "period", "section_order"])
        .with_columns(
            chapter_expr.alias("chapter"),
            normalized_title_expr().alias("normalizedTitle"),
        )
        .filter(pl.col("text").is_not_null() & (pl.col("text").str.len_chars() > 0))
        .with_columns(period_order_expr().alias("periodOrder"))
    )


def canonical_leaf_rows() -> pl.LazyFrame:
    mapping_df = pl.DataFrame(
        {
            "normalizedTitle": list(loadSectionMappings().keys()),
            "canonicalTopic": list(loadSectionMappings().values()),
        }
    ).lazy()

    base = scan_rows()
    return (
        base.join(mapping_df, on="normalizedTitle", how="left")
        .with_columns(
            pl.when(pl.col("section_title").str.contains(r"^\s*([IVX]{1,5})\.\s*"))
            .then(pl.lit("chapter"))
            .otherwise(pl.lit("leaf"))
            .alias("rowType"),
            pl.coalesce(["canonicalTopic", "normalizedTitle"]).alias("topic"),
        )
        .filter(pl.col("rowType") == "leaf")
        .select(
            [
                "stockCode",
                "period",
                "periodOrder",
                "chapter",
                "section_order",
                "section_title",
                "normalizedTitle",
                "topic",
                "text",
            ]
        )
    )


def merged_topic_rows() -> pl.LazyFrame:
    rows = canonical_leaf_rows()
    return (
        rows.group_by(["stockCode", "period", "periodOrder", "chapter", "topic"])
        .agg(
            pl.col("text").sort_by("section_order").str.join("\n\n").alias("topicText"),
            pl.col("normalizedTitle").sort_by("section_order").alias("sourceTitles"),
            pl.col("section_title").n_unique().alias("rawTitleVariants"),
        )
    )


def chapter_aggregate_rows() -> pl.LazyFrame:
    rows = canonical_leaf_rows()
    return (
        rows.group_by(["stockCode", "period", "periodOrder", "chapter"])
        .agg(
            pl.col("text").sort_by("section_order").str.join("\n\n").alias("chapterText"),
            pl.col("topic").n_unique().alias("chapterTopicCount"),
        )
    )


def stock_merged_topic_rows(stock_code: str) -> pl.DataFrame:
    mapping_df = pl.DataFrame(
        {
            "normalizedTitle": list(loadSectionMappings().keys()),
            "canonicalTopic": list(loadSectionMappings().values()),
        }
    ).lazy()
    rows = (
        scan_stock_rows(stock_code)
        .join(mapping_df, on="normalizedTitle", how="left")
        .with_columns(
            pl.when(pl.col("section_title").str.contains(r"^\s*([IVX]{1,5})\.\s*"))
            .then(pl.lit("chapter"))
            .otherwise(pl.lit("leaf"))
            .alias("rowType"),
            pl.coalesce(["canonicalTopic", "normalizedTitle"]).alias("topic"),
        )
        .filter(pl.col("rowType") == "leaf")
        .select(
            [
                "stockCode",
                "period",
                "periodOrder",
                "chapter",
                "section_order",
                "section_title",
                "normalizedTitle",
                "topic",
                "text",
            ]
        )
    )
    return (
        rows.group_by(["stockCode", "period", "periodOrder", "chapter", "topic"])
        .agg(
            pl.col("text").sort_by("section_order").str.join("\n\n").alias("topicText"),
            pl.col("normalizedTitle").sort_by("section_order").alias("sourceTitles"),
            pl.col("section_title").n_unique().alias("rawTitleVariants"),
        )
        .collect()
    )


def stock_chapter_aggregate_rows(stock_code: str) -> pl.DataFrame:
    mapping_df = pl.DataFrame(
        {
            "normalizedTitle": list(loadSectionMappings().keys()),
            "canonicalTopic": list(loadSectionMappings().values()),
        }
    ).lazy()
    rows = (
        scan_stock_rows(stock_code)
        .join(mapping_df, on="normalizedTitle", how="left")
        .with_columns(
            pl.when(pl.col("section_title").str.contains(r"^\s*([IVX]{1,5})\.\s*"))
            .then(pl.lit("chapter"))
            .otherwise(pl.lit("leaf"))
            .alias("rowType"),
            pl.coalesce(["canonicalTopic", "normalizedTitle"]).alias("topic"),
        )
        .filter(pl.col("rowType") == "leaf")
        .select(
            [
                "stockCode",
                "period",
                "periodOrder",
                "chapter",
                "section_order",
                "topic",
                "text",
            ]
        )
    )
    return (
        rows.group_by(["stockCode", "period", "periodOrder", "chapter"])
        .agg(
            pl.col("text").sort_by("section_order").str.join("\n\n").alias("chapterText"),
            pl.col("topic").n_unique().alias("chapterTopicCount"),
        )
        .collect()
    )


def stock_period_pivot(stock_code: str) -> pl.DataFrame:
    merged = stock_merged_topic_rows(stock_code).sort(["topic", "periodOrder"])
    if merged.height == 0:
        return pl.DataFrame()
    return (
        merged.pivot(
            values="topicText",
            index=["chapter", "topic"],
            on="period",
            aggregate_function="first",
        )
        .sort(["chapter", "topic"])
    )


def latest_annual_teacher(stock_code: str) -> pl.DataFrame:
    merged = stock_merged_topic_rows(stock_code)
    if merged.height == 0:
        return pl.DataFrame()
    annual = merged.filter(~pl.col("period").str.contains("Q"))
    if annual.height == 0:
        return pl.DataFrame()
    latest_period = annual.sort("periodOrder", descending=True).get_column("period").to_list()[0]
    return annual.filter(pl.col("period") == latest_period).sort(["chapter", "topic"])


def backfill_candidates(stock_code: str) -> pl.DataFrame:
    teacher = latest_annual_teacher(stock_code)
    if teacher.height == 0:
        return pl.DataFrame()

    merged = stock_merged_topic_rows(stock_code)
    chapters = stock_chapter_aggregate_rows(stock_code)
    periods = (
        merged.select(["period", "periodOrder"])
        .unique()
        .sort("periodOrder")
        .get_column("period")
        .to_list()
    )

    period_df = pl.DataFrame({"period": periods})
    teacher_grid = teacher.select(["chapter", "topic"]).join(period_df, how="cross")
    observed = merged.select(["chapter", "topic", "period"]).with_columns(pl.lit(True).alias("hasFine"))
    chapter_text = chapters.select(["chapter", "period", "chapterText"]).with_columns(
        (pl.col("chapterText").str.len_chars() > 0).alias("hasChapterText")
    )

    out = (
        teacher_grid.join(observed, on=["chapter", "topic", "period"], how="left")
        .join(chapter_text, on=["chapter", "period"], how="left")
        .with_columns(
            pl.col("hasFine").fill_null(False),
            pl.col("hasChapterText").fill_null(False),
        )
        .with_columns(
            ((pl.col("hasFine") == False) & (pl.col("hasChapterText") == True)).alias("backfillCandidate")
        )
        .group_by(["chapter", "topic"])
        .agg(
            pl.col("hasFine").sum().alias("filledPeriods"),
            pl.col("backfillCandidate").sum().alias("backfillCandidatePeriods"),
            pl.col("period").filter(pl.col("backfillCandidate")).alias("candidatePeriods"),
        )
        .sort(["backfillCandidatePeriods", "filledPeriods", "chapter", "topic"], descending=[True, True, False, False])
    )
    return out


def global_topic_summary() -> pl.DataFrame:
    merged = merged_topic_rows()
    return (
        merged.group_by(["chapter", "topic"])
        .agg(
            pl.col("stockCode").n_unique().alias("companies"),
            pl.col("period").n_unique().alias("periods"),
        )
        .sort(["companies", "periods", "chapter", "topic"], descending=[True, True, False, False])
        .collect()
    )


def main() -> None:
    stock_code = sys.argv[1] if len(sys.argv) > 1 else "005930"
    include_global = "--global" in sys.argv[2:]

    teacher = latest_annual_teacher(stock_code)
    pivot = stock_period_pivot(stock_code)
    backfill = backfill_candidates(stock_code)

    print("=" * 72)
    print("056-038 scan_parquet 기반 section retable")
    print("=" * 72)
    if include_global:
        print("[global canonical topics]")
        print(global_topic_summary().head(30))
        print()

    print(f"[{stock_code} latest annual teacher topics]")
    print(teacher.select(["chapter", "topic", "rawTitleVariants"]).head(40))
    print()

    print(f"[{stock_code} topic x period pivot]")
    if pivot.height == 0:
        print("NO_DATA")
    else:
        preview_cols = pivot.columns[: min(len(pivot.columns), 12)]
        print(pivot.select(preview_cols).head(30))
    print()

    print(f"[{stock_code} coarse-to-fine backfill candidates]")
    if backfill.height == 0:
        print("NO_DATA")
    else:
        print(backfill.head(40))


if __name__ == "__main__":
    main()
