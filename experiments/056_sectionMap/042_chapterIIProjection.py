"""
실험 ID: 056-042
실험명: chapter II coarse-to-fine projection 초안

목적:
- chapter II의 구연도 coarse topic을 최신 fine topic 축으로 투영해 빈 row를 채울 수 있는지 검증한다.
- `businessOverview / productService / rawMaterial / salesOrder / majorContractsAndRnd / riskDerivative / otherReference`
  축을 과거 period까지 최대한 연결한다.

가설:
1. chapter II는 구연도에 coarse topic이 반복되므로 규칙 기반 topic-to-topic projection이 가능하다.
2. 이 projection만으로도 fine topic 빈 칸을 상당수 채울 수 있다.

방법:
1. `canonicalRows.parquet`에서 chapter II row만 읽는다.
2. 구연도 coarse topic -> 최신 fine topic 규칙을 정의한다.
3. stock별 latest annual teacher topic 축 위에서 projection row를 추가한다.
4. 실제 recovered cell 수를 계산한다.

결과 (실험 후 작성):

결론:

실험일: 2026-03-12
"""

from __future__ import annotations

import sys
from pathlib import Path

import polars as pl

FINE_TOPICS = [
    "businessOverview",
    "productService",
    "rawMaterial",
    "salesOrder",
    "majorContractsAndRnd",
    "riskDerivative",
    "otherReference",
]

COARSE_TO_FINE = {
    "주요제품및원재료등": ["productService", "rawMaterial"],
    "매출에관한사항": ["salesOrder"],
    "연구개발활동": ["majorContractsAndRnd"],
    "기타투자의사결정에필요한사항": ["riskDerivative", "otherReference"],
}


def row_table_path() -> Path:
    return Path(__file__).resolve().parent / "output" / "canonicalRows.parquet"


def load_chapter_two(stock_code: str) -> pl.DataFrame:
    return (
        pl.read_parquet(row_table_path())
        .filter((pl.col("stockCode") == stock_code) & (pl.col("chapter") == "II"))
        .sort(["periodOrder", "topic"])
    )


def latest_teacher(df: pl.DataFrame) -> pl.DataFrame:
    annual = df.filter(~pl.col("period").str.contains("Q"))
    latest_period = annual.sort("periodOrder", descending=True).get_column("period").to_list()[0]
    return annual.filter((pl.col("period") == latest_period) & pl.col("topic").is_in(FINE_TOPICS))


def projected_rows(df: pl.DataFrame) -> pl.DataFrame:
    coarse_rows = []
    for coarse_topic, fine_topics in COARSE_TO_FINE.items():
        source = df.filter(pl.col("topic") == coarse_topic)
        if source.height == 0:
            continue
        for row in source.iter_rows(named=True):
            for fine_topic in fine_topics:
                coarse_rows.append(
                    {
                        "stockCode": row["stockCode"],
                        "period": row["period"],
                        "periodOrder": row["periodOrder"],
                        "chapter": row["chapter"],
                        "topic": fine_topic,
                        "topicText": row["topicText"],
                        "projectionSource": coarse_topic,
                        "projectionKind": "coarseTopicRule",
                    }
                )
    return pl.DataFrame(coarse_rows) if coarse_rows else pl.DataFrame()


def recovered_cells(df: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    teacher = latest_teacher(df).select(["chapter", "topic"]).unique()
    periods = df.select(["period", "periodOrder"]).unique().sort("periodOrder").get_column("period").to_list()
    teacher_grid = teacher.join(pl.DataFrame({"period": periods}), how="cross")

    observed = df.select(["chapter", "topic", "period"]).with_columns(pl.lit(True).alias("hasObserved"))
    projected = projected_rows(df)
    projected_key = (
        projected.select(["chapter", "topic", "period", "projectionSource"])
        if projected.height
        else pl.DataFrame(schema={"chapter": pl.Utf8, "topic": pl.Utf8, "period": pl.Utf8, "projectionSource": pl.Utf8})
    )

    result = (
        teacher_grid.join(observed, on=["chapter", "topic", "period"], how="left")
        .join(projected_key, on=["chapter", "topic", "period"], how="left")
        .with_columns(
            pl.col("hasObserved").fill_null(False),
            pl.col("projectionSource").is_not_null().alias("hasProjection"),
        )
        .with_columns(
            ((pl.col("hasObserved") == False) & (pl.col("hasProjection") == True)).alias("recovered")
        )
    )
    return result, projected


def main() -> None:
    stock_code = sys.argv[1] if len(sys.argv) > 1 else "005930"
    df = load_chapter_two(stock_code)
    if df.height == 0:
        print("NO_DATA")
        return

    grid, projected = recovered_cells(df)
    summary = grid.group_by("topic").agg(
        pl.col("hasObserved").sum().alias("observedPeriods"),
        pl.col("recovered").sum().alias("recoveredPeriods"),
    ).sort(["recoveredPeriods", "observedPeriods", "topic"], descending=[True, True, False])

    print("=" * 72)
    print("056-042 chapter II coarse-to-fine projection")
    print("=" * 72)
    print(f"stockCode={stock_code}")
    print(f"chapterIIRows={df.height}")
    print()
    print("[teacher fine topics]")
    print(latest_teacher(df).select(["topic"]).unique().sort("topic"))
    print()
    print("[projection summary]")
    print(summary)
    print()
    print("[sample projected rows]")
    if projected.height == 0:
        print("NO_PROJECTION")
    else:
        print(projected.sort(["periodOrder", "topic"]).head(30))


if __name__ == "__main__":
    main()
