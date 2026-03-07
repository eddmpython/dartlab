"""
실험 ID: 001
실험명: 최대주주 현황 데이터 탐색

목적:
- 사업보고서에서 최대주주 관련 섹션 탐색
- 어떤 데이터가 추출 가능한지 확인

가설:
1. 사업보고서에 최대주주명, 지분율, 특수관계인 정보 존재

방법:
1. 삼성전자 사업보고서에서 최대주주 관련 섹션 제목 확인
2. 해당 섹션의 테이블 구조 분석
3. 추출 가능 데이터 목록 작성

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
    path = DATA_DIR / "005930.parquet"
    df = pl.read_parquet(str(path))
    years = sorted(df["year"].unique().to_list(), reverse=True)

    print("=" * 100)
    print("삼성전자 최대주주 관련 데이터 탐색")
    print("=" * 100)

    for year in years[:2]:
        biz = df.filter(
            (pl.col("year") == year)
            & pl.col("report_type").str.contains("사업보고서")
            & ~pl.col("report_type").str.contains("기재정정|첨부")
        )
        if biz.height == 0:
            continue

        titles = biz["section_title"].unique().to_list()
        print(f"\n--- {year} (사업보고서 전체 섹션 {len(titles)}개) ---")

        holderTitles = [t for t in titles if "주주" in t or "지분" in t or "소유" in t or "대주주" in t]
        print(f"\n  최대주주 관련 섹션:")
        for t in sorted(holderTitles):
            print(f"    {t}")

        empTitles = [t for t in titles if "임원" in t]
        print(f"\n  임원 관련 섹션:")
        for t in sorted(empTitles):
            print(f"    {t}")

        for keyword in ["최대주주", "주주"]:
            rows = biz.filter(pl.col("section_title").str.contains(keyword))
            if rows.height == 0:
                continue

            print(f"\n  === '{keyword}' 포함 섹션 상세 ===")
            for i in range(min(rows.height, 3)):
                title = rows["section_title"][i]
                content = rows["section_content"][i]
                print(f"\n  [{title}] (길이: {len(content)}자)")
                preview = content[:2000]
                for line in preview.split("\n")[:30]:
                    s = line.strip()
                    if s:
                        print(f"    {s[:200]}")
            break
        break


if __name__ == "__main__":
    main()
