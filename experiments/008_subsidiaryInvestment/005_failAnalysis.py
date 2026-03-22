"""
실험 ID: 005
실험명: 실패 케이스 상세 분석

목적:
- 47개 실패 종목의 섹션 내용 분석
- 실패 원인 분류 (구조 차이 / 빈 테이블 / 데이터 없음)

가설:
1. 대부분 SPAC/리츠/소형주 — 타법인출자 자체가 없음 (빈 테이블)

방법:
1. 실패 종목 섹션 내용 상위 5개 출력
2. 테이블 행 분석

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

FAIL_CODES = [
    "012210", "177900", "178920", "188040", "226590",
    "271940", "281820", "287840", "298690", "368030",
    "381970", "448730", "451800", "460860", "484130",
    "487360", "495810", "496320",
]


def main():
    for code in FAIL_CODES:
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

        for year in years[:2]:
            rows = df.filter(
                (pl.col("year") == year)
                & (
                    pl.col("section_title").str.contains("타법인")
                    | pl.col("section_title").str.contains("출자")
                )
                & pl.col("report_type").str.contains("사업보고서")
            )
            if rows.height == 0:
                continue

            for ri in range(min(rows.height, 2)):
                title = rows["section_title"][ri]
                content = rows["section_content"][ri]
                print(f"\n  [{year}] [{title}] ({len(content)}자)")

                lines = content.split("\n")
                tableLines = 0
                for line in lines:
                    s = line.strip()
                    if not s.startswith("|"):
                        if s and tableLines == 0:
                            print(f"    텍스트: {s[:150]}")
                        continue
                    cells = [c.strip() for c in s.split("|")]
                    cells = [c for c in cells if c != ""]
                    tableLines += 1
                    if tableLines <= 10:
                        print(f"    [{len(cells)}셀] {s[:200]}")

                if tableLines == 0:
                    print(f"    (테이블 없음)")
                else:
                    print(f"    총 테이블 행: {tableLines}")

            break


if __name__ == "__main__":
    main()
