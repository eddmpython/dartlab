"""
실험 ID: 056-049
실험명: context-ready slices 생성
"""

from __future__ import annotations

import sys
from pathlib import Path

import polars as pl

from dartlab.engines.company.dart.docs.sections.views import contextSlices, saveView

DEFAULT_STOCK_CODE = "005930"
OUTPUT_DIR = Path("data/dart/docs/sectionsViews")


def main() -> None:
    stock_code = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_STOCK_CODE
    slices = contextSlices(stock_code)
    saveView(slices, OUTPUT_DIR / f"{stock_code}.contextSlices.parquet")
    print("=" * 72)
    print(f"056-049 context-ready slices · {stock_code}")
    print("=" * 72)
    print(f"shape: {slices.shape}")
    print(f"saved: {OUTPUT_DIR.resolve()}")
    print()
    print("[summary]")
    print(
        slices.group_by(["blockType", "isSemantic"])
        .agg(
            pl.len().alias("rows"),
            pl.col("chars").mean().alias("avgChars"),
            pl.col("chars").median().alias("medianChars"),
        )
        .sort(["isSemantic", "rows"], descending=[True, True])
    )
    print()
    print("[semantic slices]")
    print(
        slices.filter(pl.col("semanticTopic").is_not_null())
        .group_by("semanticTopic")
        .agg(pl.len().alias("rows"), pl.col("period").n_unique().alias("periods"))
        .sort("rows", descending=True)
        .head(20)
    )


if __name__ == "__main__":
    main()
