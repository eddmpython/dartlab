"""
실험 ID: 056-043
실험명: chapter II 정밀 projection 규칙

목적:
- chapter II coarse topic을 무조건 복사하지 않고, 내부 heading/키워드 기준으로 더 정확하게 fine topic에 투영한다.
- 연결 수보다 의미 정합성을 우선하는 projection rule을 만든다.

가설:
1. `주요제품및원재료등`은 heading 기준으로 `productService`와 `rawMaterial`로 분해 가능하다.
2. `매출에관한사항`은 `salesOrder`, `연구개발활동`은 `majorContractsAndRnd`로 직접 투영 가능하다.
3. `기타투자의사결정에필요한사항`은 chapter II fine topic으로 무리하게 넣지 않는 편이 더 정확하다.

방법:
1. `canonicalRows.parquet`에서 stock별 chapter II row를 읽는다.
2. coarse topic의 본문을 `가./나./다./라.` heading 단위로 나눈다.
3. heading/본문 키워드에 따라 fine topic을 배정한다.
4. observedPeriods와 recoveredPeriods를 다시 계산한다.

결과 (실험 후 작성):

결론:

실험일: 2026-03-12
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import polars as pl

FINE_TOPICS = [
    "businessOverview",
    "productService",
    "rawMaterial",
    "salesOrder",
    "majorContractsAndRnd",
]

RE_MAJOR = re.compile(r"^([가-힣])\.\s*(.+)$")


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


def split_by_major(text: str) -> list[tuple[str, str]]:
    lines = [line.rstrip() for line in text.splitlines()]
    segments: list[tuple[str, list[str]]] = []
    current_label = "(root)"
    current_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        major_match = RE_MAJOR.match(stripped)
        if major_match:
            if current_lines:
                segments.append((current_label, current_lines))
            current_label = stripped
            current_lines = []
            continue
        current_lines.append(stripped)

    if current_lines:
        segments.append((current_label, current_lines))

    return [(label, "\n".join(body).strip()) for label, body in segments if body]


def route_segment(source_topic: str, label: str, body: str) -> str | None:
    joined = f"{label}\n{body}"
    if source_topic == "주요제품및원재료등":
        if "원재료" in joined or "생산설비" in joined:
            return "rawMaterial"
        if "제품" in joined or "서비스" in joined:
            return "productService"
    if source_topic == "매출에관한사항":
        return "salesOrder"
    if source_topic == "연구개발활동":
        return "majorContractsAndRnd"
    return None


def projected_rows(df: pl.DataFrame) -> pl.DataFrame:
    out: list[dict[str, object]] = []
    for row in df.iter_rows(named=True):
        source_topic = row["topic"]
        if source_topic not in {"주요제품및원재료등", "매출에관한사항", "연구개발활동"}:
            continue
        segments = split_by_major(row["topicText"])
        if not segments:
            segments = [("(root)", row["topicText"])]
        for label, body in segments:
            target = route_segment(source_topic, label, body)
            if not target:
                continue
            out.append(
                {
                    "stockCode": row["stockCode"],
                    "period": row["period"],
                    "periodOrder": row["periodOrder"],
                    "chapter": row["chapter"],
                    "topic": target,
                    "topicText": body,
                    "projectionSource": source_topic,
                    "projectionLabel": label,
                    "projectionKind": "headingRule",
                }
            )
    return pl.DataFrame(out) if out else pl.DataFrame()


def recovered_cells(df: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    teacher = latest_teacher(df).select(["chapter", "topic"]).unique()
    periods = df.select(["period", "periodOrder"]).unique().sort("periodOrder").get_column("period").to_list()
    teacher_grid = teacher.join(pl.DataFrame({"period": periods}), how="cross")

    observed = df.select(["chapter", "topic", "period"]).with_columns(pl.lit(True).alias("hasObserved"))
    projected = projected_rows(df)
    projected_key = (
        projected.select(["chapter", "topic", "period"])
        .unique()
        .with_columns(pl.lit(True).alias("hasProjection"))
        if projected.height
        else pl.DataFrame(schema={"chapter": pl.Utf8, "topic": pl.Utf8, "period": pl.Utf8, "hasProjection": pl.Boolean})
    )

    result = (
        teacher_grid.join(observed, on=["chapter", "topic", "period"], how="left")
        .join(projected_key, on=["chapter", "topic", "period"], how="left")
        .with_columns(
            pl.col("hasObserved").fill_null(False),
            pl.col("hasProjection").fill_null(False),
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
    summary = (
        grid.group_by("topic")
        .agg(
            pl.col("hasObserved").sum().alias("observedPeriods"),
            pl.col("recovered").sum().alias("recoveredPeriods"),
        )
        .sort(["recoveredPeriods", "observedPeriods", "topic"], descending=[True, True, False])
    )

    print("=" * 72)
    print("056-043 chapter II precise projection")
    print("=" * 72)
    print(f"stockCode={stock_code}")
    print()
    print("[projection summary]")
    print(summary)
    print()
    print("[sample projected rows]")
    if projected.height == 0:
        print("NO_PROJECTION")
    else:
        print(projected.sort(["periodOrder", "topic"]).head(40))


if __name__ == "__main__":
    main()
