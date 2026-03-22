"""
실험 ID: 023
실험명: 자본금 변동사항 섹션 탐색

목적:
- "자본금 변동사항" 섹션의 구조와 테이블 패턴 파악
- 어떤 데이터가 추출 가능한지 확인 (유상/무상증자, 감자, 전환사채 등)
- 커버리지와 테이블 일관성 확인

가설:
1. 267개 기업 중 220개 이상이 자본금 변동 섹션 보유
2. 테이블은 "주식발행 총수", "유상증자", "무상증자", "감자" 등 표준 구조

방법:
1. 전체 기업의 section_title에서 "자본금" 관련 섹션 탐색
2. 대표 기업(삼성전자)의 섹션 내용 분석
3. 테이블 구조 패턴 분류

결과 (실험 후 작성):
-

결론:
-

실험일: 2026-03-08
"""

import os
import re
import sys
from collections import Counter

sys.path.insert(0, r"C:\Users\MSI\OneDrive\Desktop\sideProject\dartlab\src")

DATA_DIR = r"C:\Users\MSI\OneDrive\Desktop\sideProject\nicegui\eddmpython\data\dartData\docsData"

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.reportSelector import selectReport


def exploreSectionTitles():
    """전체 기업의 자본금 관련 섹션 타이틀 탐색."""
    codes = [f.replace(".parquet", "") for f in os.listdir(DATA_DIR) if f.endswith(".parquet")]

    titleCounter = Counter()
    hasCapital = 0
    total = 0

    for code in codes:
        try:
            df = loadData(code)
        except Exception:
            continue
        total += 1

        years = sorted(df["year"].unique().to_list(), reverse=True)
        if not years:
            continue

        report = selectReport(df, years[0], reportKind="annual")
        if report is None:
            continue

        found = False
        for row in report.iter_rows(named=True):
            title = row.get("section_title", "") or ""
            if re.search(r"자본금\s*변동", title):
                titleCounter[title.strip()] += 1
                found = True
            elif re.search(r"주식의\s*총수", title):
                titleCounter[title.strip()] += 1
                found = True

        if found:
            hasCapital += 1

    print(f"\n=== 자본금 관련 섹션 커버리지 ===")
    print(f"total: {total}, hasCapital: {hasCapital} ({hasCapital/total*100:.1f}%)")
    print(f"\n--- 섹션 타이틀 빈도 ---")
    for title, count in titleCounter.most_common(20):
        print(f"  [{count:3d}] {title}")


def exploreContent(stockCode: str = "005930"):
    """특정 기업의 자본금 변동 섹션 내용 상세 탐색."""
    df = loadData(stockCode)
    corpName = extractCorpName(df)
    years = sorted(df["year"].unique().to_list(), reverse=True)

    print(f"\n=== {corpName} ({stockCode}) 자본금 변동 섹션 ===")

    for year in years[:2]:
        report = selectReport(df, year, reportKind="annual")
        if report is None:
            continue

        print(f"\n--- {year}년 ---")
        for row in report.iter_rows(named=True):
            title = row.get("section_title", "") or ""
            if re.search(r"자본금\s*변동|주식의\s*총수", title):
                content = row.get("section_content", "") or ""
                print(f"  섹션: {title}")
                print(f"  길이: {len(content)}")
                # 테이블 블록 추출
                lines = content.split("\n")
                tableBlocks = []
                current = []
                for line in lines:
                    if "|" in line:
                        current.append(line.strip())
                    else:
                        if current:
                            tableBlocks.append(current)
                            current = []
                if current:
                    tableBlocks.append(current)

                print(f"  테이블 블록 수: {len(tableBlocks)}")
                for i, block in enumerate(tableBlocks):
                    print(f"\n  [블록 {i+1}] ({len(block)} rows)")
                    for line in block[:8]:
                        print(f"    {line[:120]}")
                    if len(block) > 8:
                        print(f"    ... (총 {len(block)} rows)")


def exploreKeywords():
    """자본금 변동 섹션에서 등장하는 키워드 빈도 분석."""
    codes = [f.replace(".parquet", "") for f in os.listdir(DATA_DIR) if f.endswith(".parquet")]

    keywords = Counter()
    sample = 0

    for code in codes:
        try:
            df = loadData(code)
        except Exception:
            continue

        years = sorted(df["year"].unique().to_list(), reverse=True)
        if not years:
            continue

        report = selectReport(df, years[0], reportKind="annual")
        if report is None:
            continue

        for row in report.iter_rows(named=True):
            title = row.get("section_title", "") or ""
            if re.search(r"자본금\s*변동|주식의\s*총수", title):
                content = row.get("section_content", "") or ""
                sample += 1
                for kw in ["유상증자", "무상증자", "감자", "전환사채", "전환", "신주인수권",
                           "스톡옵션", "주식배당", "발행주식", "보통주", "우선주",
                           "자본금", "액면가", "발행가", "발행한 주식", "주식의 총수"]:
                    if kw in content:
                        keywords[kw] += 1

    print(f"\n=== 키워드 빈도 (샘플: {sample}) ===")
    for kw, count in keywords.most_common():
        print(f"  [{count:3d}/{sample}] {kw}")


if __name__ == "__main__":
    exploreSectionTitles()
    exploreKeywords()
    exploreContent("005930")  # 삼성전자
    exploreContent("005380")  # 현대차
    exploreContent("035720")  # 카카오
