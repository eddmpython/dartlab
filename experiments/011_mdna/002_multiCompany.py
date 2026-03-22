"""
실험 ID: 002
실험명: MD&A 10종목 구조 비교

목적:
- 10종목에서 MD&A 섹션의 공통 구조 확인
- 서브섹션 번호 체계 및 내용 패턴 분석

가설:
1. 대부분 "1.예측정보 / 2.개요 / 3.재무상태 / 4~6.기타" 구조

방법:
1. 10종목 최신 사업보고서에서 MD&A 섹션 추출
2. ## 헤더 및 번호 섹션 패턴 비교

결과:

결론:

실험일: 2026-03-07
"""
import io
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import polars as pl

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "docsData"

STOCKS = [
    "005930", "000660", "035420", "005380", "055550",
    "003550", "034020", "006400", "001200", "000720",
]


def extractSections(content: str) -> list[tuple[str, int]]:
    lines = content.split("\n")
    sections = []
    for line in lines:
        s = line.strip()
        m = re.match(r"^(\d+)\.\s+(.+)", s)
        if m:
            num = m.group(1)
            title = m.group(2).strip()
            sections.append((f"{num}. {title}", len(s)))
    return sections


def main():
    print("=" * 100)
    print("MD&A 10종목 구조 비교")
    print("=" * 100)

    found = 0
    noData = 0

    for code in STOCKS:
        path = DATA_DIR / f"{code}.parquet"
        if not path.exists():
            continue

        df = pl.read_parquet(str(path))
        corpName = (
            df["corp_name"].unique().to_list()[0] if "corp_name" in df.columns else code
        )
        years = sorted(df["year"].unique().to_list(), reverse=True)

        ok = False
        for year in years[:2]:
            rows = df.filter(
                (pl.col("year") == year)
                & pl.col("section_title").str.contains("경영진단")
                & pl.col("report_type").str.contains("사업보고서")
                & ~pl.col("report_type").str.contains("기재정정|첨부")
            )
            if rows.height == 0:
                continue

            content = rows["section_content"][0]
            lines = content.split("\n")
            tableLines = [l for l in lines if l.strip().startswith("|")]
            textLines = [l for l in lines if l.strip() and not l.strip().startswith("|")]

            sections = extractSections(content)
            topSections = [s for s in sections if int(s[0].split(".")[0]) <= 10]

            print(f"\n[{code}] {corpName} ({year})")
            print(f"  길이: {len(content):,}자 / 텍스트 {len(textLines)}줄 / 테이블 {len(tableLines)}줄")
            print(f"  서브섹션:")
            for title, _ in topSections[:10]:
                print(f"    {title[:80]}")

            found += 1
            ok = True
            break

        if not ok:
            noData += 1
            print(f"\n[{code}] {corpName}: MD&A 섹션 없음")

    print(f"\n{'=' * 100}")
    print(f"성공: {found}/{len(STOCKS)}, 없음: {noData}/{len(STOCKS)}")


if __name__ == "__main__":
    main()
