"""
실험 ID: 001
실험명: 자본금 관련 섹션 구조 탐색

목적:
- 사업보고서에서 자본금/주식 관련 섹션 탐색
- "자본금 변동사항", "주식의 총수 등" 테이블 구조 파악

가설:
1. "자본금" 또는 "주식" 키워드로 섹션 검색 가능
2. 발행주식수, 자기주식, 유상증자 정보 추출 가능

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

CODE = "005930"


def main():
    path = DATA_DIR / f"{CODE}.parquet"
    df = pl.read_parquet(str(path))
    corpName = df["corp_name"].unique().to_list()[0]
    years = sorted(df["year"].unique().to_list(), reverse=True)

    print(f"[{CODE}] {corpName}")
    print("=" * 100)

    year = years[0]
    rows = df.filter(
        (pl.col("year") == year)
        & pl.col("report_type").str.contains("사업보고서")
        & ~pl.col("report_type").str.contains("기재정정|첨부")
    )

    titles = rows["section_title"].unique().to_list()
    print(f"\n{year} 사업보고서 섹션 ({len(titles)}개):")
    for t in sorted(titles):
        if "자본" in t or "주식" in t or "증자" in t or "증권" in t:
            print(f"  ★ {t}")

    print(f"\n{'=' * 100}")
    print("자본금/주식 관련 섹션 상세")
    print("=" * 100)

    for keyword in ["자본금", "주식의 총수"]:
        secRows = rows.filter(pl.col("section_title").str.contains(keyword))
        if secRows.height == 0:
            print(f"\n  '{keyword}' 섹션 없음")
            continue

        for i in range(secRows.height):
            title = secRows["section_title"][i]
            content = secRows["section_content"][i]
            print(f"\n  [{title}] ({len(content)}자)")

            lines = content.split("\n")
            for line in lines:
                s = line.strip()
                if not s.startswith("|"):
                    if s:
                        print(f"    텍스트: {s[:150]}")
                    continue
                cells = [c.strip() for c in s.split("|")]
                cells = [c for c in cells if c != ""]
                if len(cells) < 2:
                    continue
                print(f"    [{len(cells)}셀] {s[:200]}")


if __name__ == "__main__":
    main()
