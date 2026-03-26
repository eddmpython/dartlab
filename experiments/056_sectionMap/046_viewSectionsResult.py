"""
실험 ID: 056-046
실험명: production sections 결과 직접 보기

목적:
- `Company.sections`가 반환하는 `topic x period` DataFrame을 바로 확인한다.
- 핵심 canonical topic coverage와 남은 raw topic을 한 번에 점검한다.

사용 예시:
    uv run python experiments/056_sectionMap/046_viewSectionsResult.py
    uv run python experiments/056_sectionMap/046_viewSectionsResult.py 000660
    uv run python experiments/056_sectionMap/046_viewSectionsResult.py 005930 2025Q4,2025Q3,2024
    uv run python experiments/056_sectionMap/046_viewSectionsResult.py 005930 2025Q4,2025Q3,2024 salesOrder,riskDerivative
"""

from __future__ import annotations

import sys
from pathlib import Path

import polars as pl

from dartlab import Company
from dartlab.providers.dart.docs.sections.views import sortPeriods

DEFAULT_STOCK_CODE = "005930"
OUTPUT_DIR = Path("data/dart/docs/sectionsViews")
DEFAULT_TOPICS = [
    "companyOverview",
    "companyHistory",
    "businessOverview",
    "businessStatus",
    "salesOrder",
    "rawMaterial",
    "productService",
    "segmentOverview",
    "segmentFinancialSummary",
    "majorContractsAndRnd",
    "marketRisk",
    "creditRisk",
    "liquidityRisk",
    "capitalRisk",
    "riskDerivative",
    "audit",
    "auditSystem",
    "boardOfDirectors",
    "shareholderMeeting",
    "majorHolder",
]


def parse_csv_arg(index: int) -> list[str]:
    if len(sys.argv) <= index or not sys.argv[index].strip():
        return []
    return [part.strip() for part in sys.argv[index].split(",") if part.strip()]


def top_raw_topics(df: pl.DataFrame, limit: int = 30) -> pl.DataFrame:
    long = df.unpivot(index="topic", variable_name="period", value_name="text").filter(
        pl.col("text").is_not_null()
    )
    return (
        long.group_by("topic")
        .agg(pl.len().alias("periodCount"))
        .filter(~pl.col("topic").str.contains(r"^[A-Za-z]"))
        .sort("periodCount", descending=True)
        .head(limit)
    )


def topic_coverage(df: pl.DataFrame, topics: list[str]) -> pl.DataFrame:
    long = df.unpivot(index="topic", variable_name="period", value_name="text").filter(
        pl.col("text").is_not_null()
    )
    return (
        long.group_by("topic")
        .agg(pl.len().alias("periodCount"))
        .filter(pl.col("topic").is_in(topics))
        .sort("topic")
    )


def save_outputs(
    stock_code: str,
    df: pl.DataFrame,
    coverage: pl.DataFrame,
    raw_topics: pl.DataFrame,
) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df.write_parquet(OUTPUT_DIR / f"{stock_code}.sections.parquet")
    coverage.write_parquet(OUTPUT_DIR / f"{stock_code}.coverage.parquet")
    raw_topics.write_parquet(OUTPUT_DIR / f"{stock_code}.rawTopics.parquet")


def main() -> None:
    stock_code = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_STOCK_CODE
    periods = parse_csv_arg(2)
    topics = parse_csv_arg(3) or DEFAULT_TOPICS

    df = Company(stock_code).sections
    if df is None:
        print(f"[{stock_code}] sections 결과가 없습니다.")
        return

    ordered_periods = [period for period in sortPeriods([col for col in df.columns if col != "topic"]) if period in df.columns]
    df = df.select(["topic", *ordered_periods])

    selected_periods = [period for period in periods if period in df.columns]
    preview_cols = ["topic", *selected_periods] if selected_periods else df.columns[: min(16, len(df.columns))]
    coverage = topic_coverage(df, topics)
    raw_topics = top_raw_topics(df)
    save_outputs(stock_code, df, coverage, raw_topics)

    print("=" * 72)
    print(f"056-046 sections 결과 보기 · {stock_code}")
    print("=" * 72)
    print(f"shape: {df.shape}")
    print(f"saved: {OUTPUT_DIR.resolve()}")
    print()

    print("[topic coverage]")
    print(coverage)
    print()

    print("[wide preview]")
    print(df.select(preview_cols).head(40))
    print()

    print("[top raw topics]")
    print(raw_topics)


if __name__ == "__main__":
    main()
