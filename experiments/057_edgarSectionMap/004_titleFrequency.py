"""
실험 ID: 057-004
실험명: EDGAR section_title 전수 빈도 분석

목적:
- 현재 수집된 137+ docs에서 form_type별 section_title 분포를 확인한다.
- canonical topic 설계의 기초 데이터를 만든다.

가설:
1. 10-K는 Item 1~16이 대부분이고 wording 변형은 소수다.
2. 10-Q는 Part I/II + Item 구조다.
3. 20-F는 Item 수가 더 많고, wording 변형도 클 수 있다.

방법:
1. data/edgar/docs/*.parquet 전수 스캔
2. form_type별 section_title 빈도표 계산
3. Full Document 비율과 상위 title 커버리지 출력

결과 (실험 후 작성):

결론:

실험일: 2026-03-13
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

from dartlab import config


def main() -> None:
    docsDir = Path(config.dataDir) / "edgar" / "docs"
    files = sorted(docsDir.glob("*.parquet"))
    if not files:
        print("docs 없음")
        return

    frames: list[pl.DataFrame] = []
    for f in files:
        df = pl.read_parquet(f, columns=["form_type", "section_title", "year"])
        frames.append(df.with_columns(pl.lit(f.stem).alias("ticker")))
    allDf = pl.concat(frames, how="vertical_relaxed")

    print("=" * 72)
    print(f"057-004 EDGAR section_title 빈도 분석")
    print(f"docs files: {len(files)}")
    print(f"total rows: {allDf.height:,}")
    print(f"tickers: {allDf['ticker'].n_unique()}")
    print(f"forms: {sorted(allDf['form_type'].drop_nulls().unique().to_list())}")
    print("=" * 72)

    for formType in ["10-K", "10-Q", "20-F", "40-F"]:
        formDf = allDf.filter(pl.col("form_type") == formType)
        if formDf.is_empty():
            continue

        titleFreq = (
            formDf.group_by("section_title")
            .agg(
                pl.len().alias("count"),
                pl.col("ticker").n_unique().alias("tickers"),
            )
            .sort("count", descending=True)
        )
        totalRows = formDf.height
        fullDocRows = formDf.filter(pl.col("section_title") == "Full Document").height

        print()
        print(f"--- {formType} ---")
        print(f"rows: {totalRows:,}")
        print(f"unique titles: {titleFreq.height}")
        print(f"tickers: {formDf['ticker'].n_unique()}")
        print(f"Full Document: {fullDocRows} ({fullDocRows / totalRows * 100:.1f}%)")
        print()
        print(titleFreq)


if __name__ == "__main__":
    main()
