"""
실험 ID: 001
실험명: 임직원 데이터 구조 탐색

목적:
- 사업보고서 "임원 및 직원 등의 현황" 섹션 구조 파악
- 어떤 테이블이 있는지, 계정명, 단위, 포맷 확인
- 시계열 구성 가능성 탐색

가설:
1. 직원 현황 테이블에서 총 직원수, 평균 연봉, 남녀 비율 추출 가능

방법:
1. 삼성전자 최신 사업보고서에서 임직원 관련 섹션 추출
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


def main():
    df = pl.read_parquet(str(DATA_DIR / "005930.parquet"))
    corpName = df["corp_name"].unique().to_list()[0]

    print(f"종목: {corpName}")
    print("=" * 100)

    years = sorted(df["year"].unique().to_list(), reverse=True)

    for year in years[:3]:
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
            print(f"\n{year}: 섹션 없음")
            continue

        print(f"\n{'=' * 100}")
        print(f"{year}: {rows.height}개 섹션")
        print(f"{'=' * 100}")

        for i in range(rows.height):
            title = rows["section_title"][i]
            content = rows["section_content"][i]
            print(f"\n--- {title} ---")
            print(f"길이: {len(content)}자")
            print(content[:3000])
            if len(content) > 3000:
                print("...(truncated)")


if __name__ == "__main__":
    main()
