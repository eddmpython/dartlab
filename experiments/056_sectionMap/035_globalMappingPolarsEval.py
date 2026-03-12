"""
실험 ID: 056-035
실험명: 전종목 section mapping Polars 평가

목적:
- 전종목 docs parquet를 Polars lazy로 한 번에 스캔해 현재 sectionMappings의 전역 상태를 빠르게 점검한다.
- mapping 생성/보강 단계에서 매번 무거운 chunk 기반 검증을 돌리지 않고도 coverage와 남은 gap을 확인할 수 있게 한다.

가설:
1. latest annual leaf title coverage는 현재도 99% 안팎을 유지한다.
2. 남은 미매핑은 소수의 반복 title + 회사 특화 appendix/detail에 집중된다.

방법:
1. `data/dart/docs/*.parquet`를 `scan_parquet()`로 읽는다.
2. annual row만 남기고, stockCode별 latest year를 join한다.
3. chapter row를 제거한 leaf title을 mapper 규칙과 동일하게 정규화한다.
4. mapping hit, chapter별 coverage, top uncovered title을 집계한다.

결과 (실험 후 작성):
- latest annual leaf rows: `8,557`
- mapping keys: `59`
- coverage: `0.990`
- uncovered rows: `85`
- uncovered unique titles: `75`

결론:
- mapping 생성/운영 단계의 전역 상태 점검은 Polars lazy만으로 충분히 빠르게 수행 가능하다.
- 이후 mapping 업데이트 루프는 이 스크립트를 기본 대시보드처럼 사용하고,
  실제 sections 수평화 품질은 별도 stock-level 검증으로 분리하는 구조가 적절하다.

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


def latest_annual_leaf_rows() -> pl.LazyFrame:
    scan = pl.scan_parquet(docs_glob(), include_file_paths="sourcePath").with_columns(
        pl.col("sourcePath").str.extract(r"([^/\\]+)\.parquet$", 1).alias("stockCode"),
        pl.col("year").cast(pl.Int32),
        pl.col("section_title").cast(pl.Utf8),
    )

    annual = scan.filter(pl.col("report_type").str.contains("사업보고서"))
    latest_years = annual.group_by("stockCode").agg(pl.col("year").max().alias("latestYear"))

    latest = annual.join(latest_years, on="stockCode").filter(pl.col("year") == pl.col("latestYear"))

    chapter_col = (
        pl.when(pl.col("section_title").str.contains(r"^\s*([IVX]{1,5})\.\s*"))
        .then(pl.col("section_title").str.extract(r"^\s*([IVX]{1,5})\.\s*", 1))
        .otherwise(None)
        .forward_fill()
        .over(["stockCode", "year", "report_type"])
        .alias("chapter")
    )

    normalized = (
        pl.col("section_title")
        .str.strip_chars()
        .str.replace(r"^\s*(?:(?:\d+|[가-힣])[.)]\s*|\(\d+\)\s*|[①-⑳]\s*)+", "")
        .str.replace(r"^\([^)]*업\)", "")
        .str.replace_all("ㆍ", ",")
        .str.replace_all(r"\s+", "")
        .alias("normalizedTitle")
    )

    return (
        latest.sort(["stockCode", "year", "section_order"])
        .with_columns(chapter_col, normalized)
        .filter(pl.col("chapter").is_not_null())
        .filter(~pl.col("section_title").str.contains(r"^\s*([IVX]{1,5})\.\s*"))
        .select(["stockCode", "year", "chapter", "section_title", "normalizedTitle"])
    )


def main() -> None:
    mapping_keys = sorted(loadSectionMappings().keys())
    mapping_df = pl.DataFrame({"normalizedTitle": mapping_keys}).lazy()

    latest = latest_annual_leaf_rows().join(mapping_df, on="normalizedTitle", how="left", coalesce=True).with_columns(
        pl.col("normalizedTitle").is_in(mapping_keys).alias("isMapped")
    )

    summary = latest.select(
        pl.len().alias("latestAnnualLeafRows"),
        pl.lit(len(mapping_keys)).alias("mappingKeys"),
        pl.col("isMapped").mean().alias("coverage"),
        (pl.col("isMapped") == False).sum().alias("uncoveredRows"),
        pl.col("normalizedTitle").filter(pl.col("isMapped") == False).n_unique().alias("uncoveredUniqueTitles"),
    ).collect()

    chapter_summary = (
        latest.group_by("chapter")
        .agg(
            pl.len().alias("rows"),
            pl.col("stockCode").n_unique().alias("companies"),
            pl.col("isMapped").mean().alias("coverage"),
            (pl.col("isMapped") == False).sum().alias("uncoveredRows"),
        )
        .sort("chapter")
        .collect()
    )

    uncovered = (
        latest.filter(pl.col("isMapped") == False)
        .group_by(["chapter", "normalizedTitle"])
        .agg(
            pl.len().alias("rows"),
            pl.col("stockCode").n_unique().alias("companies"),
        )
        .sort(["rows", "companies", "chapter", "normalizedTitle"], descending=[True, True, False, False])
        .head(30)
        .collect()
    )

    print("=" * 72)
    print("056-035 전종목 section mapping Polars 평가")
    print("=" * 72)
    print(summary)
    print()
    print("[chapter coverage]")
    print(chapter_summary)
    print()
    print("[top uncovered normalized titles]")
    print(uncovered)


if __name__ == "__main__":
    main()
