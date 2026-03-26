"""
실험 ID: 057-006
실험명: EDGAR canonical row 학습 테이블 생성

목적:
- source-native EDGAR section을 period별 canonical row 테이블로 저장한다.
- 이후 빠른 horizontalization과 mapping 실험의 기반 테이블로 사용한다.

가설:
1. form_type namespace를 유지한 topic 체계를 쓰면 10-K/20-F는 안정적으로 수평화할 수 있다.
2. 10-Q는 현재 Full Document만 담아도 period slot 자체는 유지할 수 있다.

방법:
1. data/edgar/docs/*.parquet를 스캔한다.
2. period_key가 있는 row만 사용한다.
3. form_type + mapped topic 기준으로 text를 병합한다.
4. output/canonicalRows.parquet에 저장한다.

결과 (실험 후 작성):
- 실행 후 갱신

결론:
- 실행 후 갱신

실험일: 2026-03-12
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

from dartlab import config
from dartlab.providers.edgar.docs.sections.mapper import mapSectionTitle


def docsGlob() -> str:
    return str(Path(config.dataDir) / "edgar" / "docs" / "*.parquet")


def outPath() -> Path:
    return Path(__file__).resolve().parent / "output" / "canonicalRows.parquet"


def periodOrderExpr() -> pl.Expr:
    yearPart = pl.col("period").str.slice(0, 4).cast(pl.Int32)
    return (
        pl.when(pl.col("period").str.contains("Q1"))
        .then(yearPart * 10 + 1)
        .when(pl.col("period").str.contains("Q2"))
        .then(yearPart * 10 + 2)
        .when(pl.col("period").str.contains("Q3"))
        .then(yearPart * 10 + 3)
        .otherwise(yearPart * 10 + 4)
    )


def canonicalRowsLazy() -> pl.LazyFrame:
    scan = pl.scan_parquet(docsGlob(), include_file_paths="sourcePath").with_columns(
        pl.col("sourcePath").str.extract(r"([^/\\]+)\.parquet$", 1).alias("stockCode"),
        pl.col("period_key").cast(pl.Utf8).alias("period"),
        pl.col("form_type").cast(pl.Utf8),
        pl.col("section_title").cast(pl.Utf8),
        pl.col("section_content").cast(pl.Utf8).alias("text"),
    )

    return (
        scan.filter(pl.col("period").is_not_null())
        .filter(pl.col("text").is_not_null() & (pl.col("text").str.len_chars() > 0))
        .with_columns(
            pl.struct(["form_type", "section_title"])
            .map_elements(
                lambda row: mapSectionTitle(str(row["form_type"]), str(row["section_title"])),
                return_dtype=pl.Utf8,
            )
            .alias("topic"),
            periodOrderExpr().alias("periodOrder"),
        )
        .group_by(["stockCode", "period", "periodOrder", "form_type", "topic"])
        .agg(
            pl.col("text").sort_by("section_order").str.join("\n\n").alias("topicText"),
            pl.col("section_title").unique().alias("rawTitleVariants"),
        )
        .sort(["stockCode", "periodOrder", "form_type", "topic"])
    )


def main() -> None:
    out = outPath()
    out.parent.mkdir(parents=True, exist_ok=True)
    canonicalRowsLazy().sink_parquet(str(out))

    df = pl.read_parquet(out)
    print("=" * 72)
    print("057-006 EDGAR canonical row table")
    print("=" * 72)
    print(f"path={out}")
    print(f"rows={df.height}")
    print(f"companies={df.get_column('stockCode').n_unique()}")
    print(f"periods={df.get_column('period').n_unique()}")
    print(f"topics={df.get_column('topic').n_unique()}")


if __name__ == "__main__":
    main()
