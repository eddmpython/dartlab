"""
실험 ID: 056-048
실험명: retrieval-ready markdown horizontal view
"""

from __future__ import annotations

import sys
from pathlib import Path

import polars as pl

from dartlab.engines.company.dart.docs.sections.views import retrievalBlocks, saveView

DEFAULT_STOCK_CODE = "005930"
OUTPUT_DIR = Path("data/dart/docs/sectionsViews")


def main() -> None:
    stock_code = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_STOCK_CODE
    blocks = retrievalBlocks(stock_code)
    if blocks.height == 0:
        print(f"[{stock_code}] retrieval block 결과가 없습니다.")
        return

    saveView(blocks, OUTPUT_DIR / f"{stock_code}.retrievalBlocks.parquet")
    summary = (
        blocks.group_by("blockType")
        .agg(
            pl.len().alias("rows"),
            pl.col("chars").mean().alias("avgChars"),
            pl.col("chars").median().alias("medianChars"),
            pl.col("tableLines").sum().alias("sumTableLines"),
        )
        .sort("rows", descending=True)
    )

    print("=" * 72)
    print(f"056-048 retrieval-ready horizontal view · {stock_code}")
    print("=" * 72)
    print(f"shape: {blocks.shape}")
    print(f"saved: {OUTPUT_DIR.resolve()}")
    print()
    print("[block summary]")
    print(summary)
    print()
    print("[semantic topic summary]")
    print(
        blocks.filter(pl.col("semanticTopic").is_not_null())
        .group_by("semanticTopic")
        .agg(pl.len().alias("rows"), pl.col("period").n_unique().alias("periods"))
        .sort("rows", descending=True)
        .head(20)
    )
    print()
    print("[largest table blocks]")
    print(
        blocks.filter(pl.col("blockType") == "table")
        .sort(["tableLines", "chars"], descending=[True, True])
        .select(["period", "topic", "rawTitle", "blockLabel", "tableLines", "chars"])
        .head(20)
    )


if __name__ == "__main__":
    main()
