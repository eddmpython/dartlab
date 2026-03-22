"""
실험 ID: 002
실험명: 다종목 주식의 총수 테이블 구조 비교

목적:
- 10개 종목의 "주식의 총수" 테이블 구조 비교
- 공통 추출 항목 확인

가설:
1. "주식의 총수" 테이블에서 발행주식수, 자기주식수, 유통주식수 추출 가능
2. 보통주/우선주 구분이 표준 구조

방법:
1. 10개 종목 사업보고서에서 "주식" 섹션 추출
2. 상단 요약 테이블 구조 비교

결과:

결론:

실험일: 2026-03-07
"""
import io
import sys
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


def main():
    print("=" * 100)
    print("다종목 주식의 총수 테이블 비교")
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
            rows = df.filter(
                (pl.col("year") == year)
                & pl.col("section_title").str.contains("주식의 총수")
                & pl.col("report_type").str.contains("사업보고서")
                & ~pl.col("report_type").str.contains("기재정정|첨부")
            )
            if rows.height == 0:
                rows = df.filter(
                    (pl.col("year") == year)
                    & pl.col("section_title").str.contains("주식")
                    & pl.col("report_type").str.contains("사업보고서")
                    & ~pl.col("report_type").str.contains("기재정정|첨부")
                )
            if rows.height == 0:
                print(f"  {year}: 주식 섹션 없음")
                continue

            title = rows["section_title"][0]
            content = rows["section_content"][0]
            print(f"  [{title}] ({len(content)}자)")

            lines = content.split("\n")
            printCount = 0
            for line in lines:
                s = line.strip()
                if not s.startswith("|"):
                    continue
                cells = [c.strip() for c in s.split("|")]
                cells = [c for c in cells if c != ""]
                if len(cells) < 2:
                    continue
                txt = " ".join(cells)

                if any(kw in txt for kw in [
                    "발행할 주식", "발행한 주식", "감소한 주식",
                    "발행주식", "자기주식", "유통주식",
                    "보통주", "우선주", "합계",
                    "보유비율",
                ]):
                    print(f"    [{len(cells)}셀] {s[:200]}")
                    printCount += 1
                    if printCount >= 15:
                        break


if __name__ == "__main__":
    main()
