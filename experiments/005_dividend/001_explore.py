"""
실험 ID: 001
실험명: 삼성전자 배당 데이터 탐색

목적:
- DART 공시 "배당에 관한 사항" 섹션의 데이터 구조 파악
- 연도별 포맷 변화 확인
- 추출 가능한 항목 식별 (DPS, 배당수익률, 배당성향 등)

가설:
1. 배당 섹션에 마크다운 테이블이 있고 DPS/배당수익률/배당성향을 추출할 수 있다
2. 연도별 포맷이 크게 다르지 않아 단일 파서로 처리 가능하다

방법:
1. 삼성전자(005930) 데이터에서 배당 관련 섹션 필터
2. 연도별 섹션 제목 변화 확인
3. 최신 3개년 content 구조 비교
4. 테이블 헤더/행 패턴 분석

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


def main():
    df = pl.read_parquet(str(DATA_DIR / "005930.parquet"))

    dividend = df.filter(pl.col("section_title").str.contains("배당"))

    print("=" * 80)
    print("삼성전자 배당 관련 섹션")
    print("=" * 80)

    titles = dividend.select("year", "report_type", "section_title").unique().sort("year", descending=True)
    print(f"\n총 {titles.height}건\n")
    for row in titles.iter_rows():
        print(f"  {row[0]} | {row[1][:30]:30s} | {row[2]}")

    print("\n" + "=" * 80)
    print("연도별 배당 섹션 구조 (최신 3년)")
    print("=" * 80)

    for year in ["2025", "2024", "2023"]:
        yearData = dividend.filter(
            (pl.col("year") == year)
            & ~pl.col("report_type").str.contains("기재정정|첨부")
            & pl.col("report_type").str.contains("사업보고서")
        )
        if yearData.height == 0:
            yearData = dividend.filter(
                (pl.col("year") == year)
                & pl.col("report_type").str.contains("사업보고서")
            )
        if yearData.height == 0:
            print(f"\n--- {year}: 데이터 없음 ---")
            continue

        content = yearData["section_content"][0]
        lines = content.split("\n")

        print(f"\n--- {year} ({yearData['section_title'][0]}) ---")
        print(f"총 {len(lines)}줄")

        tableLines = [l for l in lines if l.strip().startswith("|")]
        print(f"테이블 행: {len(tableLines)}줄")

        if tableLines:
            print("\n처음 30줄:")
            for l in tableLines[:30]:
                print(f"  {l.strip()}")

        nonTableLines = [l for l in lines if l.strip() and not l.strip().startswith("|") and "---" not in l]
        if nonTableLines:
            print(f"\n비테이블 텍스트 ({len(nonTableLines)}줄, 처음 10줄):")
            for l in nonTableLines[:10]:
                print(f"  {l.strip()}")

    print("\n" + "=" * 80)
    print("2024 전체 content (형식 파악용)")
    print("=" * 80)

    yearData = dividend.filter(
        (pl.col("year") == "2024")
        & ~pl.col("report_type").str.contains("기재정정|첨부")
        & pl.col("report_type").str.contains("사업보고서")
    )
    if yearData.height > 0:
        content = yearData["section_content"][0]
        for i, line in enumerate(content.split("\n")):
            print(f"  {i:3d} | {line}")


if __name__ == "__main__":
    main()
