"""
실험 ID: 057-004
실험명: EDGAR form별 item coverage 조사

목적:
- EDGAR docs가 form_type별로 얼마나 구조화되어 있는지 측정한다.
- 10-K item split 안정성과 10-Q Full Document 비중을 수치로 확인한다.

가설:
1. 10-K는 Item 기반 section split이 대체로 안정적이다.
2. 10-Q는 Full Document 비율이 높아 별도 item split 연구가 필요하다.

방법:
1. data/edgar/docs/*.parquet를 전수 스캔한다.
2. filing(accession_no) 단위로 section 개수와 title 패턴을 집계한다.
3. form_type별로 median section 수, Full Document filing 비율을 계산한다.

결과 (실험 후 작성):
- 실행 후 갱신

결론:
- 실행 후 갱신

실험일: 2026-03-12
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

from dartlab import config


def main() -> None:
    docsDir = Path(config.dataDir) / "edgar" / "docs"
    files = sorted(docsDir.glob("*.parquet"))
    if not files:
        raise RuntimeError("EDGAR docs parquet 없음")

    frames: list[pl.DataFrame] = []
    for filePath in files:
        frames.append(
            pl.read_parquet(
                filePath,
                columns=["accession_no", "form_type", "section_title", "ticker", "year"],
            )
        )

    df = pl.concat(frames, how="vertical")
    filingDf = (
        df.group_by(["accession_no", "form_type", "ticker", "year"])
        .agg(
            pl.len().alias("section_count"),
            (pl.col("section_title") == "Full Document").sum().alias("full_document_rows"),
        )
        .with_columns(
            (pl.col("full_document_rows") > 0).alias("has_full_document"),
        )
    )

    print("=" * 72)
    print("057-004 EDGAR item coverage")
    print("=" * 72)

    summary = (
        filingDf.group_by("form_type")
        .agg(
            pl.len().alias("filings"),
            pl.col("section_count").median().alias("median_sections"),
            pl.col("section_count").mean().alias("mean_sections"),
            pl.col("has_full_document").mean().mul(100).alias("full_document_filing_ratio"),
        )
        .sort("form_type")
    )
    print(summary)

    for formType in ["10-K", "10-Q", "20-F"]:
        formDf = filingDf.filter(pl.col("form_type") == formType).sort("section_count", descending=True)
        if formDf.is_empty():
            continue
        print()
        print(f"[{formType}] top filings by section count")
        print(formDf.head(10))


if __name__ == "__main__":
    main()
