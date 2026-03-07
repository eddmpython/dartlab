"""
실험 ID: 002
실험명: 다종목 타법인출자 테이블 구조 비교

목적:
- 10개 종목의 타법인출자 테이블 구조 비교
- 공통 셀 수, 헤더 패턴 확인

가설:
1. 대부분 종목이 16셀 구조를 따름
2. 헤더 키워드 "법인명" + "지분율" + "장부가액" 공통

방법:
1. 10개 종목 사업보고서에서 타법인출자 섹션 추출
2. 셀 수 분포, 헤더 행 패턴 비교

결과:

결론:

실험일: 2026-03-07
"""
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import polars as pl

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "docsData"

STOCKS = [
    "005930",
    "000660",
    "035420",
    "005380",
    "055550",
    "051910",
    "006400",
    "003550",
    "034020",
    "000270",
]


def findSubsidiarySection(df, year):
    rows = df.filter(
        (pl.col("year") == year)
        & pl.col("section_title").str.contains("타법인")
        & pl.col("report_type").str.contains("사업보고서")
        & ~pl.col("report_type").str.contains("기재정정|첨부")
    )
    if rows.height == 0:
        rows = df.filter(
            (pl.col("year") == year)
            & pl.col("section_title").str.contains("출자")
            & pl.col("report_type").str.contains("사업보고서")
            & ~pl.col("report_type").str.contains("기재정정|첨부")
        )
    if rows.height == 0:
        rows = df.filter(
            (pl.col("year") == year)
            & pl.col("section_title").str.contains("타법인")
            & pl.col("report_type").str.contains("사업보고서")
        )
    return rows


def main():
    print("=" * 100)
    print("다종목 타법인출자 테이블 구조 비교")
    print("=" * 100)

    for code in STOCKS:
        path = DATA_DIR / f"{code}.parquet"
        if not path.exists():
            print(f"\n[{code}] 파일 없음")
            continue

        df = pl.read_parquet(str(path))
        corpName = (
            df["corp_name"].unique().to_list()[0] if "corp_name" in df.columns else code
        )
        years = sorted(df["year"].unique().to_list(), reverse=True)

        print(f"\n{'=' * 100}")
        print(f"[{code}] {corpName}")
        print(f"{'=' * 100}")

        for year in years[:1]:
            rows = findSubsidiarySection(df, year)
            if rows.height == 0:
                print(f"  {year}: 타법인출자 섹션 없음")
                continue

            for ri in range(rows.height):
                title = rows["section_title"][ri]
                content = rows["section_content"][ri]
                print(f"\n  [{title}] ({len(content)}자)")

                lines = content.split("\n")
                cellCounts = {}
                headerLine = None
                dataCount = 0

                for line in lines:
                    s = line.strip()
                    if not s.startswith("|"):
                        continue
                    cells = [c.strip() for c in s.split("|")]
                    if cells and cells[0] == "":
                        cells = cells[1:]
                    if cells and cells[-1] == "":
                        cells = cells[:-1]
                    if len(cells) < 3:
                        continue

                    nCells = len(cells)
                    cellCounts[nCells] = cellCounts.get(nCells, 0) + 1

                    txt = " ".join(cells)
                    if all(c.replace("-", "") == "" for c in cells):
                        continue

                    if "법인명" in txt or "법 인 명" in txt:
                        headerLine = s[:200]
                    elif "합 계" in txt or "합계" in txt:
                        print(f"    합계행 [{nCells}셀]: {s[:200]}")
                    else:
                        dataCount += 1
                        if dataCount <= 3:
                            print(f"    데이터 [{nCells}셀]: {s[:200]}")

                print(f"    셀 수 분포: {cellCounts}")
                if headerLine:
                    print(f"    헤더: {headerLine}")
                print(f"    데이터 행: {dataCount}개")


if __name__ == "__main__":
    main()
