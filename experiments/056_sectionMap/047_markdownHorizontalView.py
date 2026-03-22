"""
실험 ID: 056-047
실험명: markdown 보존 수평화 뷰
"""

from __future__ import annotations

from pathlib import Path
import sys

import polars as pl

from dartlab.engines.company.dart.docs.sections.views import (
    buildMarkdownBlocks,
    buildMarkdownWide,
    saveView,
)


DEFAULT_STOCK_CODE = "005930"
OUTPUT_DIR = Path("data/dart/docs/sectionsViews")


def main() -> None:
    stock_code = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_STOCK_CODE
    blocks = buildMarkdownBlocks(stock_code)
    if blocks.height == 0:
        print(f"[{stock_code}] markdown horizontalization 결과가 없습니다.")
        return

    wide = buildMarkdownWide(blocks)
    saveView(wide, OUTPUT_DIR / f"{stock_code}.markdownWide.parquet")
    saveView(blocks, OUTPUT_DIR / f"{stock_code}.markdownBlocks.parquet")

    print("=" * 72)
    print(f"056-047 markdown 보존 수평화 · {stock_code}")
    print("=" * 72)
    print(f"wide shape: {wide.shape}")
    print(f"blocks shape: {blocks.shape}")
    print(f"saved: {OUTPUT_DIR.resolve()}")
    print()
    print("[wide preview]")
    print(wide.select(wide.columns[: min(10, len(wide.columns))]).head(20))
    print()
    print("[table-heavy blocks]")
    print(
        blocks.select(["period", "topic", "rawTitle", "tableLines", "textLines"])
        .filter(pl.col("tableLines") > 0)
        .sort(["tableLines", "period"], descending=[True, True])
        .head(20)
    )


if __name__ == "__main__":
    main()
