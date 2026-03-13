"""
실험 ID: 057-007
실험명: EDGAR canonical row 기반 빠른 수평화

목적:
- 생성된 canonicalRows.parquet를 읽어 단일 ticker를 빠르게 horizontalize한다.
- 패키지 sections 파이프라인의 목표 형태를 실험 단계에서 미리 확인한다.

가설:
1. canonicalRows만 있으면 단일 ticker period x topic 뷰는 빠르게 생성된다.
2. source-native topic만으로도 10-K/20-F는 즉시 비교 가능한 수준이다.

방법:
1. output/canonicalRows.parquet를 읽는다.
2. 입력 ticker row만 필터한다.
3. topic x period pivot을 만든다.

결과 (실험 후 작성):
- 실행 후 갱신

결론:
- 실행 후 갱신

실험일: 2026-03-12
"""

from __future__ import annotations

import sys
from pathlib import Path

import polars as pl


def tablePath() -> Path:
    return Path(__file__).resolve().parent / "output" / "canonicalRows.parquet"


def main() -> None:
    stockCode = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    path = tablePath()
    if not path.exists():
        raise RuntimeError(f"canonicalRows 없음: {path}")

    df = pl.read_parquet(path).filter(pl.col("stockCode") == stockCode).sort(["periodOrder", "form_type", "topic"])
    if df.is_empty():
        raise RuntimeError(f"{stockCode} row 없음")

    pivot = (
        df.pivot(
            values="topicText",
            index=["form_type", "topic"],
            on="period",
            aggregate_function="first",
        )
        .sort(["form_type", "topic"])
    )

    print("=" * 72)
    print("057-007 EDGAR fast horizontalize")
    print("=" * 72)
    print(f"stockCode={stockCode}")
    print(f"rows={df.height}")
    print(f"periods={df['period'].n_unique()}")
    print(f"topics={df['topic'].n_unique()}")
    previewCols = pivot.columns[: min(len(pivot.columns), 12)]
    print(pivot.select(previewCols).head(30))


if __name__ == "__main__":
    main()
