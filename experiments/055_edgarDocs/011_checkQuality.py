"""
실험 ID: 055-011
실험명: 배치 수집 결과 품질 점검

목적:
- MSFT 0.03MB 이상 → 텍스트가 비어있는지 확인
- NVO 1개 filing만 있는 이유 확인
- 전체 parquet 품질 요약

실험일: 2026-03-11
"""

import polars as pl
from pathlib import Path

if __name__ == "__main__":
    batchDir = Path(__file__).parent / "batch"

    print("=== 배치 parquet 품질 점검 ===\n")
    print(f"{'파일':20s} {'행수':>5} {'AvgChars':>10} {'크기MB':>8} {'연도범위':>15} {'연도수':>5}")
    print("=" * 70)

    for f in sorted(batchDir.glob("*.parquet")):
        df = pl.read_parquet(f)
        avgChars = df["section_content"].str.len_chars().mean()
        years = sorted(df["year"].unique().to_list())
        yearRange = f"{years[0]}~{years[-1]}" if years else "-"
        sizeMb = f.stat().st_size / (1024 * 1024)
        print(f"{f.name:20s} {df.height:5d} {avgChars:>10,.0f} {sizeMb:>8.2f} {yearRange:>15} {len(years):>5}")

    print("\n\n=== MSFT 상세 ===\n")
    msft = batchDir / "MSFT.parquet"
    if msft.exists():
        df = pl.read_parquet(msft)
        for row in df.select("year", "section_title", pl.col("section_content").str.len_chars().alias("chars")).iter_rows(named=True):
            if row["chars"] < 100:
                print(f"  {row['year']} {row['section_title']}: {row['chars']} chars <<<< EMPTY")
        print(f"\n  연도별 합계 chars:")
        stats = df.group_by("year").agg(
            pl.col("section_content").str.len_chars().sum().alias("total_chars"),
            pl.len().alias("sections"),
        ).sort("year")
        for row in stats.iter_rows(named=True):
            print(f"    {row['year']}: {row['total_chars']:>10,} chars  ({row['sections']} sections)")

    print("\n\n=== NVO 상세 ===\n")
    nvo = batchDir / "NVO.parquet"
    if nvo.exists():
        df = pl.read_parquet(nvo)
        print(f"  행수: {df.height}")
        print(f"  연도: {df['year'].unique().to_list()}")
        print(f"  filing_date: {df['filing_date'].unique().to_list()}")
    else:
        print("  파일 없음")
