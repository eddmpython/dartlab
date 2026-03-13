"""
실험 ID: 057-005
실험명: 기존 sectionMappings.json 커버리지 검증

목적:
- 현재 138+ ticker 데이터에 대해 기존 mapper의 매핑률을 측정한다.
- unmapped title을 식별하고, 매퍼에 추가할 후보를 뽑는다.

가설:
1. 10-K/10-Q/20-F 핵심 title은 이미 매핑되어 있을 것이다.
2. long-tail wording 변형 중 일부가 unmapped일 수 있다.

방법:
1. 전체 docs parquet의 section_title을 normalizeSectionTitle 통과
2. sectionMappings.json에 매핑 존재 여부 확인
3. form별 매핑률, unmapped title 목록 출력

결과 (실험 후 작성):

결론:

실험일: 2026-03-13
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

from dartlab import config
from dartlab.engines.edgar.docs.sections.mapper import (
    loadSectionMappings,
    normalizeSectionTitle,
)


def main() -> None:
    docsDir = Path(config.dataDir) / "edgar" / "docs"
    files = sorted(docsDir.glob("*.parquet"))
    if not files:
        print("docs 없음")
        return

    frames: list[pl.DataFrame] = []
    for f in files:
        df = pl.read_parquet(f, columns=["form_type", "section_title", "accession_no"])
        frames.append(df.with_columns(pl.lit(f.stem).alias("ticker")))
    allDf = pl.concat(frames, how="vertical_relaxed")

    mappings = loadSectionMappings()
    mappingKeys = set(mappings.keys())

    normalized = [normalizeSectionTitle(str(t)) for t in allDf["section_title"].to_list()]
    allDf = allDf.with_columns(
        pl.Series("normalized", normalized),
        pl.Series("mapped", [n in mappingKeys for n in normalized]),
    )

    print("=" * 72)
    print(f"057-005 sectionMappings 커버리지 검증")
    print(f"docs files: {len(files)}")
    print(f"total rows: {allDf.height:,}")
    print(f"mappings in json: {len(mappings)}")
    print("=" * 72)

    for formType in ["10-K", "10-Q", "20-F", "40-F"]:
        formDf = allDf.filter(pl.col("form_type") == formType)
        if formDf.is_empty():
            continue

        totalRows = formDf.height
        mappedRows = formDf.filter(pl.col("mapped")).height
        coverage = mappedRows / totalRows * 100

        titleStats = (
            formDf.group_by(["normalized", "mapped"])
            .agg(
                pl.len().alias("rows"),
                pl.col("ticker").n_unique().alias("tickers"),
                pl.col("accession_no").n_unique().alias("filings"),
            )
            .sort("rows", descending=True)
        )
        uniqueTitles = titleStats.height
        mappedTitles = titleStats.filter(pl.col("mapped")).height

        print()
        print(f"--- {formType} ---")
        print(f"rows: {totalRows:,} / mapped: {mappedRows:,} ({coverage:.1f}%)")
        print(f"unique titles: {uniqueTitles} / mapped: {mappedTitles}")

        unmapped = titleStats.filter(~pl.col("mapped")).sort("rows", descending=True)
        if not unmapped.is_empty():
            print(f"\nunmapped ({unmapped.height}):")
            for row in unmapped.iter_rows(named=True):
                print(f"  [{row['rows']:4d} rows, {row['tickers']:3d} tickers] {row['normalized']}")

    totalMapped = allDf.filter(pl.col("mapped")).height
    totalAll = allDf.height
    print()
    print(f"=== TOTAL: {totalMapped:,}/{totalAll:,} ({totalMapped/totalAll*100:.1f}%) ===")


if __name__ == "__main__":
    main()
