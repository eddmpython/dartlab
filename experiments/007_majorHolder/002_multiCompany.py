"""
실험 ID: 002
실험명: 다종목 최대주주 데이터 패턴 비교

목적:
- 10개 종목의 최대주주 테이블 구조 비교
- 공통 추출 가능 항목 확인

가설:
1. "최대주주 및 특수관계인" 테이블에서 이름, 관계, 지분율 추출 가능

방법:
1. 10개 종목 사업보고서에서 "주주" 섹션 추출
2. 테이블 구조 비교 (헤더행, 데이터행)

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


def main():
    print("=" * 100)
    print("다종목 최대주주 테이블 패턴 비교")
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
                & pl.col("section_title").str.contains("주주")
                & pl.col("report_type").str.contains("사업보고서")
                & ~pl.col("report_type").str.contains("기재정정|첨부")
            )
            if rows.height == 0:
                rows = df.filter(
                    (pl.col("year") == year)
                    & pl.col("section_title").str.contains("주주")
                    & pl.col("report_type").str.contains("사업보고서")
                )
            if rows.height == 0:
                print(f"  {year}: 주주 섹션 없음")
                continue

            for i in range(rows.height):
                title = rows["section_title"][i]
                content = rows["section_content"][i]
                print(f"\n  [{title}] ({len(content)}자)")

                if "최대주주" not in content and "주주명" not in content:
                    print(f"    (최대주주 관련 테이블 없음)")
                    continue

                lines = content.split("\n")
                printCount = 0
                for line in lines:
                    s = line.strip()
                    if not s.startswith("|"):
                        continue
                    cells = [c.strip() for c in s.split("|")]
                    cells = [c for c in cells if c]
                    if len(cells) < 3:
                        continue
                    txt = " ".join(cells)
                    if (
                        "최대주주" in txt
                        or "특수관계" in txt
                        or "성 명" in txt
                        or "성명" in txt
                        or "본인" in txt
                        or "합 계" in txt
                        or "합계" in txt
                        or "계열" in txt
                    ):
                        print(f"    {s[:200]}")
                        printCount += 1
                        if printCount >= 15:
                            break


if __name__ == "__main__":
    main()
