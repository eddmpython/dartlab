"""
실험 ID: 056-041
실험명: 전회사 chapter source 학습 테이블 생성

목적:
- coarse-to-fine backfill을 위해 period별 chapter 원문 source 테이블을 별도로 저장한다.
- canonical row 테이블과 함께 읽어서, 특정 fine topic이 비어 있어도 같은 chapter 본문으로 projection 후보를 만들 수 있게 한다.

가설:
1. chapter 단위 원문 source를 따로 저장해야 backfill 후보 계산이 정확해진다.
2. canonical row 테이블 + chapter source 테이블 조합이 빠른 운영 구조에 적합하다.

방법:
1. 전체 docs parquet를 scan한다.
2. `stockCode / period / chapter` 기준으로 leaf text를 병합한다.
3. parquet로 저장한다.

결과 (실험 후 작성):

결론:

실험일: 2026-03-12
"""

from __future__ import annotations

from pathlib import Path

import polars as pl


def root_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def docs_glob() -> str:
    return str(root_dir() / "data" / "dart" / "docs" / "*.parquet")


def out_path() -> Path:
    return Path(__file__).resolve().parent / "output" / "chapterSources.parquet"


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


def chapter_sources_lazy() -> pl.LazyFrame:
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

    return (
        scan.filter(pl.col("period").is_not_null())
        .sort(["stockCode", "period", "section_order"])
        .with_columns(
            chapter_expr.alias("chapter"),
            period_order_expr().alias("periodOrder"),
        )
        .filter(pl.col("text").is_not_null() & (pl.col("text").str.len_chars() > 0))
        .filter(~pl.col("section_title").str.contains(r"^\s*([IVX]{1,5})\.\s*"))
        .group_by(["stockCode", "period", "periodOrder", "chapter"])
        .agg(
            pl.col("text").sort_by("section_order").str.join("\n\n").alias("chapterText"),
            pl.col("section_title").n_unique().alias("leafCount"),
        )
    )


def main() -> None:
    out = out_path()
    out.parent.mkdir(parents=True, exist_ok=True)
    chapter_sources_lazy().sink_parquet(str(out))

    df = pl.read_parquet(out)
    print("=" * 72)
    print("056-041 전회사 chapter source 학습 테이블 생성")
    print("=" * 72)
    print(f"path={out}")
    print(f"rows={df.height}")
    print(f"companies={df.get_column('stockCode').n_unique()}")
    print(f"periods={df.get_column('period').n_unique()}")
    print(f"chapters={df.get_column('chapter').n_unique()}")


if __name__ == "__main__":
    main()
