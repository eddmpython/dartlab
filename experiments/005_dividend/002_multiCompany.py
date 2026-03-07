"""
실험 ID: 002
실험명: 다종목 배당 데이터 패턴 비교

목적:
- 여러 종목의 배당 섹션 포맷 차이 파악
- 고배당주, 무배당주, 우선주 없는 기업 등 다양한 케이스 확인
- 과거 연도(2015 이전) 포맷 변화 확인

가설:
1. "주요 배당지표" 테이블 포맷이 대부분 기업에서 동일하다
2. 핵심 계정명(DPS, 배당성향, 배당수익률)이 표준화되어 있다

방법:
1. 10개 종목 선정 (대형주, 고배당, 무배당, 금융, 우선주 없음)
2. 각 종목 최신 사업보고서의 배당 섹션 비교
3. 테이블 헤더/행 패턴 수집
4. 과거 연도(2010~2015) 포맷 변화 확인

결과:

결론:

실험일: 2026-03-06
"""
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import polars as pl

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "docsData"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"

STOCKS = [
    "005930",
    "000660",
    "035420",
    "005380",
    "055550",
    "051910",
    "006400",
    "032830",
    "003550",
    "034020",
]


def getDividendSection(df: pl.DataFrame, year: str) -> str | None:
    rows = df.filter(
        (pl.col("year") == year)
        & pl.col("section_title").str.contains("배당")
        & pl.col("report_type").str.contains("사업보고서")
        & ~pl.col("report_type").str.contains("기재정정|첨부")
    )
    if rows.height == 0:
        rows = df.filter(
            (pl.col("year") == year)
            & pl.col("section_title").str.contains("배당")
            & pl.col("report_type").str.contains("사업보고서")
        )
    if rows.height == 0:
        return None
    return rows["section_content"][0]


def extractTableRows(content: str) -> list[list[str]]:
    rows = []
    for line in content.split("\n"):
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.split("|")]
        if cells and cells[0] == "":
            cells = cells[1:]
        if cells and cells[-1] == "":
            cells = cells[:-1]
        if not cells:
            continue
        if all(c.replace("-", "") == "" for c in cells):
            continue
        rows.append(cells)
    return rows


def main():
    print("=" * 100)
    print("다종목 배당 데이터 패턴 비교")
    print("=" * 100)

    allAccounts = set()

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

        for year in years[:3]:
            content = getDividendSection(df, year)
            if content is None:
                print(f"\n  {year}: 배당 섹션 없음")
                continue

            rows = extractTableRows(content)
            print(f"\n  {year}: {len(rows)}행")

            for row in rows:
                if len(row) >= 2:
                    label = row[0].strip()
                    if label and not label.startswith("[") and not label.startswith("※") and "단위" not in label:
                        allAccounts.add(label)

                lineStr = " | ".join(row)
                if len(lineStr) > 120:
                    lineStr = lineStr[:120] + "..."
                print(f"    {lineStr}")

    print(f"\n{'=' * 100}")
    print(f"발견된 계정명 ({len(allAccounts)}개)")
    print(f"{'=' * 100}")
    for acc in sorted(allAccounts):
        print(f"  {acc}")

    print(f"\n{'=' * 100}")
    print("과거 연도 포맷 비교 (삼성전자)")
    print(f"{'=' * 100}")

    df = pl.read_parquet(str(DATA_DIR / "005930.parquet"))
    for year in ["2020", "2017", "2014", "2010"]:
        content = getDividendSection(df, year)
        if content is None:
            print(f"\n  {year}: 데이터 없음")
            continue

        rows = extractTableRows(content)
        print(f"\n  {year}: {len(rows)}행")
        for row in rows[:20]:
            lineStr = " | ".join(row)
            if len(lineStr) > 120:
                lineStr = lineStr[:120] + "..."
            print(f"    {lineStr}")
        if len(rows) > 20:
            print(f"    ... (+{len(rows) - 20}행)")


if __name__ == "__main__":
    main()
