"""
실험 ID: 056-045
실험명: profiler 기반 projection candidate 추출

목적:
- profiler table을 보고 coarse topic -> fine topic projection 후보를 자동으로 찾는다.
- 수동 규칙 추가 전에 어떤 coarse topic이 어떤 fine topic과 가장 강하게 연결되는지 빠르게 본다.

가설:
1. 같은 chapter 내에서 keyword/heading 패턴이 비슷한 coarse topic은 특정 fine topic으로 수렴한다.
2. 이 후보표를 보면 projection rule 설계 속도가 빨라진다.

방법:
1. `sectionProfileTable.parquet`를 읽는다.
2. stock별 latest annual fine topic을 teacher로 둔다.
3. 같은 chapter의 coarse topic에 대해 feature 유사성 기반 후보를 만든다.
4. chapter/topic별 상위 후보를 출력한다.

결과 (실험 후 작성):

결론:

실험일: 2026-03-12
"""

from __future__ import annotations

import sys
from pathlib import Path

import polars as pl

FEATURE_COLS = [
    "kwProduct",
    "kwRawMaterial",
    "kwSales",
    "kwRnd",
    "kwRisk",
    "kwFunding",
    "hasMajorHeading",
    "hasMinorHeading",
]


def profile_path() -> Path:
    return Path(__file__).resolve().parent / "output" / "sectionProfileTable.parquet"


def load_df(stock_code: str) -> pl.DataFrame:
    return pl.read_parquet(profile_path()).filter(pl.col("stockCode") == stock_code)


def latest_teacher(df: pl.DataFrame) -> pl.DataFrame:
    annual = df.filter(~pl.col("period").str.contains("Q"))
    latest_period = annual.sort("periodOrder", descending=True).get_column("period").to_list()[0]
    return annual.filter(pl.col("period") == latest_period)


def aggregate_features(df: pl.DataFrame) -> pl.DataFrame:
    agg_exprs = [pl.col("textChars").mean().alias("avgTextChars"), pl.col("headingCount").mean().alias("avgHeadingCount")]
    for col in FEATURE_COLS:
        agg_exprs.append(pl.col(col).mean().alias(col))
    return df.group_by(["chapter", "topic"]).agg(agg_exprs)


def candidate_table(df: pl.DataFrame) -> pl.DataFrame:
    teacher = aggregate_features(latest_teacher(df))
    full = aggregate_features(df)

    coarse = full.filter(~pl.col("topic").is_in(teacher.get_column("topic").to_list()))
    fine = teacher.rename({"topic": "fineTopic"})

    joined = coarse.join(fine, on="chapter", how="inner")

    score_expr = None
    for col in FEATURE_COLS:
        term = (1 - (pl.col(col) - pl.col(f"{col}_right")).abs()).clip(0, 1)
        score_expr = term if score_expr is None else score_expr + term

    return (
        joined.with_columns(
            score_expr.alias("featureScore"),
            (1 / (1 + (pl.col("avgHeadingCount") - pl.col("avgHeadingCount_right")).abs())).alias("headingScore"),
            (1 / (1 + (pl.col("avgTextChars") - pl.col("avgTextChars_right")).abs() / 1000)).alias("lengthScore"),
        )
        .with_columns(
            (pl.col("featureScore") + pl.col("headingScore") + pl.col("lengthScore")).alias("totalScore")
        )
        .select(["chapter", "topic", "fineTopic", "totalScore"])
        .sort(["chapter", "topic", "totalScore"], descending=[False, False, True])
    )


def main() -> None:
    stock_code = sys.argv[1] if len(sys.argv) > 1 else "005930"
    df = load_df(stock_code)
    candidates = candidate_table(df)
    best = candidates.group_by(["chapter", "topic"]).first().sort(["chapter", "totalScore"], descending=[False, True])

    print("=" * 72)
    print("056-045 profiler 기반 projection candidate")
    print("=" * 72)
    print(f"stockCode={stock_code}")
    print()
    print("[best candidates]")
    print(best.head(40))
    print()
    print("[chapter II candidates]")
    print(candidates.filter(pl.col("chapter") == "II").head(60))


if __name__ == "__main__":
    main()
