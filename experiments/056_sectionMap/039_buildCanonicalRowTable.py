"""
실험 ID: 056-039
실험명: 전회사 canonical row 학습 테이블 생성

목적:
- 전체 docs parquet를 한 번 스캔해 canonical row 테이블을 생성하고 parquet로 저장한다.
- 이후 단일 종목 수평화는 원본 docs 전체를 다시 읽지 않고 이 학습 테이블만 참조하게 한다.

가설:
1. sectionMappings와 정규화 규칙만으로 전회사 전기간 canonical row 테이블을 만들 수 있다.
2. 이 테이블을 저장해두면 단일 종목 수평화 속도가 크게 빨라진다.

방법:
1. `scan_parquet()`로 `data/dart/docs/*.parquet` 전체를 읽는다.
2. `stockCode / period / chapter / topic / topicText` canonical row를 생성한다.
3. parquet로 저장한다.
4. 전체 row 수와 회사 수, period 수를 출력한다.

결과 (실험 후 작성):

결론:

실험일: 2026-03-12
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

from dartlab.engines.dart.docs.sections.mapper import loadSectionMappings


def root_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def docs_glob() -> str:
    return str(root_dir() / "data" / "dart" / "docs" / "*.parquet")


def out_path() -> Path:
    return Path(__file__).resolve().parent / "output" / "canonicalRows.parquet"


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


def canonical_rows_lazy() -> pl.LazyFrame:
    mapping_df = pl.DataFrame(
        {
            "normalizedTitle": list(loadSectionMappings().keys()),
            "canonicalTopic": list(loadSectionMappings().values()),
        }
    ).lazy()

    scan = pl.scan_parquet(docs_glob(), include_file_paths="sourcePath").with_columns(
        pl.col("sourcePath").str.extract(r"([^/\\]+)\.parquet$", 1).alias("stockCode"),
        pl.col("section_title").cast(pl.Utf8),
        pl.col("section_content").cast(pl.Utf8).alias("text"),
        period_expr().alias("period"),
    )

    chapter_expr = (
        pl.when(pl.col("section_title").str.contains(r"^\s*([IVX]{1,5})\.\s*"))
        .then(pl.col("section_title").str.extract(r"^\s*([IVX]{1,5})\.\s*", 1))
        .otherwise(None)
        .forward_fill()
        .over(["stockCode", "period"])
    )

    base = (
        scan.filter(pl.col("period").is_not_null())
        .sort(["stockCode", "period", "section_order"])
        .with_columns(
            chapter_expr.alias("chapter"),
            normalized_title_expr().alias("normalizedTitle"),
            period_order_expr().alias("periodOrder"),
        )
        .filter(pl.col("text").is_not_null() & (pl.col("text").str.len_chars() > 0))
    )

    leaf = (
        base.join(mapping_df, on="normalizedTitle", how="left")
        .with_columns(
            pl.when(pl.col("section_title").str.contains(r"^\s*([IVX]{1,5})\.\s*"))
            .then(pl.lit("chapter"))
            .otherwise(pl.lit("leaf"))
            .alias("rowType"),
            pl.coalesce(["canonicalTopic", "normalizedTitle"]).alias("topic"),
        )
        .filter(pl.col("rowType") == "leaf")
    )

    return (
        leaf.group_by(["stockCode", "period", "periodOrder", "chapter", "topic"])
        .agg(
            pl.col("text").sort_by("section_order").str.join("\n\n").alias("topicText"),
            pl.col("normalizedTitle").sort_by("section_order").alias("sourceTitles"),
            pl.col("section_title").n_unique().alias("rawTitleVariants"),
        )
    )


def main() -> None:
    out = out_path()
    out.parent.mkdir(parents=True, exist_ok=True)
    canonical_rows_lazy().sink_parquet(str(out))

    df = pl.read_parquet(out)
    print("=" * 72)
    print("056-039 전회사 canonical row 학습 테이블 생성")
    print("=" * 72)
    print(f"path={out}")
    print(f"rows={df.height}")
    print(f"companies={df.get_column('stockCode').n_unique()}")
    print(f"periods={df.get_column('period').n_unique()}")
    print(f"topics={df.get_column('topic').n_unique()}")


if __name__ == "__main__":
    main()
