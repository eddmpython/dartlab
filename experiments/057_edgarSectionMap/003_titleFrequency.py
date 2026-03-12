"""
실험 ID: 057-003
실험명: EDGAR section_title 전수 빈도 분석

목적:
- 현재까지 수집된 EDGAR docs에서 form_type별 section_title 분포를 확인한다.
- 10-K, 10-Q, 20-F별 canonical topic 설계 우선순위를 정한다.

가설:
1. 10-K는 item title이 상위 소수 패턴으로 수렴한다.
2. 10-Q는 현재 Full Document 비중이 높아 별도 구조화 연구가 필요하다.
3. 20-F는 표본이 적을 수 있어 초기에는 coverage 조사 단계가 적절하다.

방법:
1. data/edgar/docs/*.parquet를 전수 스캔한다.
2. form_type, section_title, ticker, year를 읽는다.
3. form_type별 section_title 빈도표를 계산한다.
4. Full Document 비율과 상위 title 커버리지를 출력한다.

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


def docsDir() -> Path:
    return Path(config.dataDir) / "edgar" / "docs"


def loadTitles(files: list[Path]) -> pl.DataFrame:
    frames: list[pl.DataFrame] = []
    for filePath in files:
        df = pl.read_parquet(filePath, columns=["form_type", "section_title", "year"])
        frames.append(
            df.with_columns(
                pl.lit(filePath.stem).alias("ticker"),
                pl.col("form_type").cast(pl.Utf8).fill_null(""),
                pl.col("section_title").cast(pl.Utf8).fill_null(""),
                pl.col("year").cast(pl.Utf8).fill_null(""),
            )
        )

    if not frames:
        return pl.DataFrame(
            schema={
                "form_type": pl.Utf8,
                "section_title": pl.Utf8,
                "year": pl.Utf8,
                "ticker": pl.Utf8,
            }
        )
    return pl.concat(frames, how="vertical")


def printFormSummary(df: pl.DataFrame, formType: str) -> None:
    formDf = df.filter(pl.col("form_type") == formType)
    if formDf.is_empty():
        print(f"[{formType}] 없음")
        return

    titleFreq = (
        formDf.group_by("section_title")
        .agg(pl.len().alias("count"))
        .sort("count", descending=True)
    )
    totalRows = formDf.height
    top10 = titleFreq.head(10)
    top10Sum = int(top10["count"].sum()) if top10.height else 0
    fullDocumentRows = formDf.filter(pl.col("section_title") == "Full Document").height
    fullDocumentRatio = (fullDocumentRows / totalRows * 100) if totalRows else 0.0

    print("=" * 72)
    print(f"{formType} summary")
    print(f"rows: {totalRows}")
    print(f"unique titles: {titleFreq.height}")
    print(f"tickers: {formDf['ticker'].n_unique()}")
    print(f"years: {formDf['year'].min()} ~ {formDf['year'].max()}")
    print(f"full document ratio: {fullDocumentRatio:.2f}% ({fullDocumentRows}/{totalRows})")
    print(f"top10 coverage: {(top10Sum / totalRows * 100):.2f}% ({top10Sum}/{totalRows})")
    print()
    print(top10)
    print()


def main() -> None:
    files = sorted(docsDir().glob("*.parquet"))
    if not files:
        raise RuntimeError("EDGAR docs parquet 없음")

    df = loadTitles(files)
    print("=" * 72)
    print("057-003 EDGAR section_title 빈도 분석")
    print("=" * 72)
    print(f"docs files: {len(files)}")
    print(f"rows: {df.height}")
    print(f"tickers: {df['ticker'].n_unique()}")
    print(f"forms: {sorted(df['form_type'].unique().to_list())}")
    print()

    for formType in ["10-K", "10-Q", "20-F"]:
        printFormSummary(df, formType)


if __name__ == "__main__":
    main()
