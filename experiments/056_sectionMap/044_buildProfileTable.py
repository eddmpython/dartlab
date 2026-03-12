"""
실험 ID: 056-044
실험명: 전회사 section profiler table 생성

목적:
- 전회사 전기간 section row의 구조/텍스트 특징을 한 테이블에 모아 학습용 profiler table을 만든다.
- projection rule, semantic rule, appendix/detail 분리 기준의 공통 입력 레이어를 만든다.

가설:
1. row 단위 특징을 미리 뽑아두면 projection 규칙 탐색이 빨라진다.
2. profiler table은 canonical row, chapter source와 함께 운영용 학습 테이블 세트를 이룬다.

방법:
1. 전체 docs parquet를 scan한다.
2. `stockCode / period / chapter / normalizedTitle / canonicalTopic / textChars / tableLines / headingCount / keyword flags`를 계산한다.
3. parquet로 저장한다.

결과 (실험 후 작성):

결론:

실험일: 2026-03-12
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

from dartlab.engines.dart.docs.sections.mapper import loadSectionMappings


KEYWORDS = {
    "kwProduct": "제품|서비스",
    "kwRawMaterial": "원재료|생산설비",
    "kwSales": "매출|수주",
    "kwRnd": "연구개발|기술",
    "kwRisk": "위험|파생|신용|유동성|금리|환율",
    "kwFunding": "자금조달|회사채|차입|유상증자|신용등급",
}


def root_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def docs_glob() -> str:
    return str(root_dir() / "data" / "dart" / "docs" / "*.parquet")


def out_path() -> Path:
    return Path(__file__).resolve().parent / "output" / "sectionProfileTable.parquet"


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


def build_lazy() -> pl.LazyFrame:
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
        .join(mapping_df, on="normalizedTitle", how="left")
        .with_columns(
            pl.when(pl.col("section_title").str.contains(r"^\s*([IVX]{1,5})\.\s*"))
            .then(pl.lit("chapter"))
            .otherwise(pl.lit("leaf"))
            .alias("rowType"),
            pl.coalesce(["canonicalTopic", "normalizedTitle"]).alias("topic"),
        )
        .filter(pl.col("rowType") == "leaf")
    )

    exprs = [
        pl.col("text").str.len_chars().alias("textChars"),
        pl.col("text").str.count_matches(r"(?m)^\|").alias("tableLineCount"),
        pl.col("text").str.count_matches(r"(?m)^(?:[가-힣]\.|\(\d+\)|\([가-힣]\))").alias("headingCount"),
        pl.col("text").str.contains(r"(?m)^[가-힣]\.").alias("hasMajorHeading"),
        pl.col("text").str.contains(r"(?m)^\(\d+\)").alias("hasMinorHeading"),
    ]
    for col, pattern in KEYWORDS.items():
        exprs.append(pl.col("text").str.contains(pattern).alias(col))

    return base.with_columns(exprs).select(
        [
            "stockCode",
            "period",
            "periodOrder",
            "chapter",
            "section_order",
            "section_title",
            "normalizedTitle",
            "topic",
            "canonicalTopic",
            "textChars",
            "tableLineCount",
            "headingCount",
            "hasMajorHeading",
            "hasMinorHeading",
            *KEYWORDS.keys(),
        ]
    )


def main() -> None:
    out = out_path()
    out.parent.mkdir(parents=True, exist_ok=True)
    build_lazy().sink_parquet(str(out))

    df = pl.read_parquet(out)
    print("=" * 72)
    print("056-044 전회사 section profiler table 생성")
    print("=" * 72)
    print(f"path={out}")
    print(f"rows={df.height}")
    print(f"companies={df.get_column('stockCode').n_unique()}")
    print(f"periods={df.get_column('period').n_unique()}")
    print(f"topics={df.get_column('topic').n_unique()}")


if __name__ == "__main__":
    main()
