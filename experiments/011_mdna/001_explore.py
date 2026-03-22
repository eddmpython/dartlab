"""
실험 ID: 001
실험명: 이사의 경영진단 및 분석의견 섹션 탐색

목적:
- 사업보고서에서 "이사의 경영진단 및 분석의견" (MD&A) 섹션 구조 파악
- 어떤 내용이 포함되는지, 텍스트/테이블 비율 확인

가설:
1. 대부분의 상장기업이 MD&A 섹션을 보유
2. 주로 텍스트 위주이며 일부 테이블 포함

방법:
1. 삼성전자/현대차/NAVER 3종목 탐색
2. section_title 필터링 → 내용 구조 분석

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
    ("005930", "삼성전자"),
    ("005380", "현대자동차"),
    ("035420", "NAVER"),
]


def main():
    print("=" * 100)
    print("이사의 경영진단 및 분석의견 (MD&A) 섹션 탐색")
    print("=" * 100)

    for code, name in STOCKS:
        path = DATA_DIR / f"{code}.parquet"
        if not path.exists():
            print(f"\n[{code}] {name}: 파일 없음")
            continue

        df = pl.read_parquet(str(path))
        years = sorted(df["year"].unique().to_list(), reverse=True)

        print(f"\n{'=' * 80}")
        print(f"[{code}] {name}")
        print(f"{'=' * 80}")

        titles = df["section_title"].unique().to_list()
        mdnaTitles = [t for t in titles if "경영진단" in t or "분석의견" in t]
        print(f"\n관련 section_title: {mdnaTitles}")

        for year in years[:2]:
            rows = df.filter(
                (pl.col("year") == year)
                & pl.col("section_title").str.contains("경영진단")
                & pl.col("report_type").str.contains("사업보고서")
                & ~pl.col("report_type").str.contains("기재정정|첨부")
            )
            if rows.height == 0:
                print(f"\n  {year}: 해당 섹션 없음")
                continue

            content = rows["section_content"][0]
            lines = content.split("\n")
            tableLines = [l for l in lines if l.strip().startswith("|")]
            textLines = [l for l in lines if l.strip() and not l.strip().startswith("|")]

            print(f"\n  {year}: 총 {len(lines)}줄 (텍스트 {len(textLines)}줄, 테이블 {len(tableLines)}줄)")
            print(f"  콘텐츠 길이: {len(content):,}자")

            print(f"\n  === 첫 30줄 ===")
            for line in lines[:30]:
                print(f"  {line[:120]}")

            headers = [l for l in lines if l.strip().startswith("#")]
            if headers:
                print(f"\n  === 헤더 목록 ===")
                for h in headers[:20]:
                    print(f"  {h.strip()}")

            subSections = []
            for line in lines:
                s = line.strip()
                if s.startswith("##") and not s.startswith("###"):
                    subSections.append(s)
            if subSections:
                print(f"\n  === ## 서브섹션 ({len(subSections)}개) ===")
                for ss in subSections:
                    print(f"  {ss}")

            print(f"\n  === 마지막 10줄 ===")
            for line in lines[-10:]:
                print(f"  {line[:120]}")

            break


if __name__ == "__main__":
    main()
