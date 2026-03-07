"""
003b: 개요 섹션 누락 디버깅 - 삼성전자/SK하이닉스
"""
import re
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import polars as pl

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "docsData"


def main():
    for code in ["005930", "000660"]:
        path = DATA_DIR / f"{code}.parquet"
        df = pl.read_parquet(str(path))
        corpName = df["corp_name"].unique().to_list()[0]
        years = sorted(df["year"].unique().to_list(), reverse=True)

        for year in years[:1]:
            rows = df.filter(
                (pl.col("year") == year)
                & pl.col("section_title").str.contains("경영진단")
                & pl.col("report_type").str.contains("사업보고서")
                & ~pl.col("report_type").str.contains("기재정정|첨부")
            )
            content = rows["section_content"][0]
            lines = content.split("\n")

            print(f"\n{'='*80}")
            print(f"[{code}] {corpName} — 번호 섹션 라인 탐지")
            print(f"{'='*80}")

            for i, line in enumerate(lines[:80]):
                s = line.strip()
                m = re.match(r"^(\d+)\.\s+(.+)", s)
                if m:
                    print(f"  line {i:3d}: [{m.group(1)}] {m.group(2)[:80]}")


if __name__ == "__main__":
    main()
