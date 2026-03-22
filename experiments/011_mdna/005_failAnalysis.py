"""
실험 ID: 005
실험명: MD&A 파싱 실패 케이스 분석

목적:
- 16개 실패 종목의 MD&A 섹션 구조 파악
- 파서 개선 가능 여부 판단

가설:
1. 번호 체계 없이 텍스트만 나열된 경우
2. 리츠/SPAC 등 간소화된 MD&A

방법:
1. 실패 종목 콘텐츠 첫 30줄 확인
2. 공통 패턴 분석

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
    "100090", "101970", "139990", "271940", "326030",
    "334890", "368030", "377190", "387570", "395400",
    "404990", "463480", "474650", "479960", "480370",
    "489210",
]


def main():
    print("=" * 100)
    print("MD&A 실패 케이스 분석")
    print("=" * 100)

    for code in FAIL_CODES:
        path = DATA_DIR / f"{code}.parquet"
        if not path.exists():
            continue

        df = pl.read_parquet(str(path))
        corpName = (
            df["corp_name"].unique().to_list()[0] if "corp_name" in df.columns else code
        )
        years = sorted(df["year"].unique().to_list(), reverse=True)

        for year in years[:3]:
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

            print(f"\n{'=' * 80}")
            print(f"[{code}] {corpName} ({year}) - {len(content):,}자, {len(lines)}줄")
            print(f"{'=' * 80}")

            for line in lines[:20]:
                print(f"  {line[:120]}")
            if len(lines) > 20:
                print(f"  ... (총 {len(lines)}줄)")
            break


if __name__ == "__main__":
    main()
