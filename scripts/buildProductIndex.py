"""changes.parquet에서 제품 인덱스 추출 → productIndex.parquet.

2444종목의 최신 '주요 제품 및 서비스' preview를 0.3MB 파일로 저장.
exogenousAxes.py가 kindList 대신 이걸 참조하면 더 정확한 제품 매핑.

Usage:
    uv run python scripts/buildProductIndex.py
"""

from __future__ import annotations

from pathlib import Path

import polars as pl


def main():
    changesPath = Path("data/dart/scan/changes.parquet")
    outputPath = Path("data/dart/scan/productIndex.parquet")

    if not changesPath.exists():
        print(f"❌ {changesPath} 없음")
        return

    df = pl.read_parquet(changesPath)
    print(f"changes.parquet: {df.shape[0]:,}행")

    # 제품 섹션 필터
    prod = df.filter(df["sectionTitle"] == "2. 주요 제품 및 서비스")
    print(f"제품 섹션: {prod.shape[0]:,}행, {prod['stockCode'].n_unique()}종목")

    # 각 종목의 최신 기간만 추출
    latest = (
        prod.sort("toPeriod", descending=True)
        .group_by("stockCode")
        .first()
        .select(["stockCode", "toPeriod", "preview"])
        .rename({"preview": "product", "toPeriod": "latestPeriod"})
        .sort("stockCode")
    )

    # &cr; 등 치환
    latest = latest.with_columns(
        pl.col("product")
        .str.replace_all("&cr;", " ")
        .str.replace_all(r"\s+", " ")
        .str.strip_chars()
    )

    latest.write_parquet(outputPath)
    size = outputPath.stat().st_size
    print(f"✓ {outputPath} 저장: {latest.shape[0]}종목, {size / 1024:.0f}KB")

    # 샘플
    for code in ["005930", "000660", "035420", "004370"]:
        row = latest.filter(latest["stockCode"] == code)
        if not row.is_empty():
            print(f"  {code}: {str(row['product'][0])[:100]}")


if __name__ == "__main__":
    main()
