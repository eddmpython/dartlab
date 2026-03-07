"""
실험 ID: 001
실험명: 사채 관련 섹션 구조 탐색

목적:
- 사업보고서에서 사채/채무증권 관련 섹션 탐색
- 테이블 구조 파악

가설:
1. "사채" 또는 "채무" 키워드로 섹션 검색 가능
2. 회사채 발행/상환/잔액 정보 추출 가능

방법:
1. 삼성전자 사업보고서에서 관련 섹션 추출
2. 테이블 구조 분석

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

STOCKS = ["005930", "000660", "035420", "005380", "055550", "003550", "034020"]


def main():
    print("=" * 100)
    print("사채 관련 섹션 구조 탐색")
    print("=" * 100)

    for code in STOCKS:
        path = DATA_DIR / f"{code}.parquet"
        if not path.exists():
            continue

        df = pl.read_parquet(str(path))
        corpName = (
            df["corp_name"].unique().to_list()[0] if "corp_name" in df.columns else code
        )
        years = sorted(df["year"].unique().to_list(), reverse=True)

        print(f"\n{'=' * 100}")
        print(f"[{code}] {corpName}")
        print(f"{'=' * 100}")

        year = years[0]
        rows = df.filter(
            (pl.col("year") == year)
            & pl.col("report_type").str.contains("사업보고서")
            & ~pl.col("report_type").str.contains("기재정정|첨부")
        )

        titles = rows["section_title"].unique().to_list()
        for t in sorted(titles):
            if "사채" in t or "채무" in t or "차입" in t or "증권" in t:
                print(f"  ★ {t}")

        for keyword in ["사채", "채무증권"]:
            secRows = rows.filter(pl.col("section_title").str.contains(keyword))
            if secRows.height == 0:
                continue

            for i in range(min(secRows.height, 2)):
                title = secRows["section_title"][i]
                content = secRows["section_content"][i]
                print(f"\n  [{title}] ({len(content)}자)")

                lines = content.split("\n")
                printCount = 0
                for line in lines:
                    s = line.strip()
                    if not s.startswith("|"):
                        if s and printCount < 3:
                            print(f"    텍스트: {s[:150]}")
                        continue
                    cells = [c.strip() for c in s.split("|")]
                    cells = [c for c in cells if c != ""]
                    if len(cells) < 2:
                        continue
                    printCount += 1
                    if printCount <= 20:
                        print(f"    [{len(cells)}셀] {s[:200]}")


if __name__ == "__main__":
    main()
