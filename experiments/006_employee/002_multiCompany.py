"""
실험 ID: 002
실험명: 다종목 직원 현황 테이블 패턴 비교

목적:
- 10개 종목의 직원 현황 테이블 구조 비교
- 공통 추출 가능 항목 확인

가설:
1. "합 계" 행에서 총 직원수, 평균근속, 연간급여, 1인평균급여 추출 가능

방법:
1. 10개 종목 사업보고서에서 "직원 등" 관련 섹션 추출
2. 테이블 구조 비교

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


def findEmployeeSection(df: pl.DataFrame, year: str) -> str | None:
    rows = df.filter(
        (pl.col("year") == year)
        & (
            pl.col("section_title").str.contains("직원")
            | pl.col("section_title").str.contains("임원")
        )
        & pl.col("report_type").str.contains("사업보고서")
        & ~pl.col("report_type").str.contains("기재정정|첨부")
    )
    if rows.height == 0:
        rows = df.filter(
            (pl.col("year") == year)
            & (
                pl.col("section_title").str.contains("직원")
                | pl.col("section_title").str.contains("임원")
            )
            & pl.col("report_type").str.contains("사업보고서")
        )
    if rows.height == 0:
        return None
    return rows["section_content"][0]


def extractEmployeeTable(content: str) -> str | None:
    idx = content.find("직원 등")
    if idx < 0:
        idx = content.find("직원등")
    if idx < 0:
        return None

    end = len(content)
    for marker in ["육아지원", "미등기임원", "임원의 보수"]:
        eidx = content.find(marker, idx + 10)
        if eidx > 0 and eidx < end:
            end = eidx

    return content[idx:end]


def main():
    print("=" * 100)
    print("다종목 직원 현황 테이블 비교")
    print("=" * 100)

    for code in STOCKS:
        path = DATA_DIR / f"{code}.parquet"
        if not path.exists():
            print(f"\n[{code}] 파일 없음")
            continue

        df = pl.read_parquet(str(path))
        corpName = df["corp_name"].unique().to_list()[0] if "corp_name" in df.columns else code
        years = sorted(df["year"].unique().to_list(), reverse=True)

        print(f"\n{'=' * 100}")
        print(f"[{code}] {corpName}")
        print(f"{'=' * 100}")

        for year in years[:2]:
            content = findEmployeeSection(df, year)
            if content is None:
                print(f"  {year}: 섹션 없음")
                continue

            table = extractEmployeeTable(content)
            if table is None:
                print(f"  {year}: 직원 현황 테이블 없음")
                continue

            print(f"\n  --- {year} ---")
            lines = table.split("\n")
            for line in lines:
                s = line.strip()
                if s.startswith("|") and ("합" in s or "계" in s or "성별" in s or "합계" in s):
                    print(f"    {s}")
            break


if __name__ == "__main__":
    main()
