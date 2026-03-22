"""연결/별도 재무제표 내용 비교.

"2. 연결재무제표" vs "4. 재무제표" 섹션의 실제 내용 비교.
- 둘 다 있는 기업: 연결 vs 별도 차이
- "4. 재무제표"만 있는 기업: 연결인지 별도인지
"""

import sys

sys.path.insert(0, "src")

import polars as pl

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.reportSelector import selectReport


def compareStatements(code):
    df = loadData(code)
    corpName = extractCorpName(df)
    years = sorted(df["year"].unique().to_list(), reverse=True)

    for year in years[:1]:
        report = selectReport(df, year, reportKind="annual")
        if report is None:
            continue

        # 연결재무제표
        cons = report.filter(
            pl.col("section_title").str.contains("연결재무제표")
            & ~pl.col("section_title").str.contains("주석")
        )
        # 별도/개별 재무제표 (= "4. 재무제표")
        sep = report.filter(
            (pl.col("section_title") == "4. 재무제표")
            | (pl.col("section_title").str.strip_chars() == "4. 재무제표")
        )

        print(f"\n{'=' * 70}")
        print(f"[{code}] {corpName} — {year}")

        if cons.height > 0:
            content = cons["section_content"][0]
            lines = content.split("\n")
            print(f"\n[연결재무제표] {len(content)}자, {len(lines)}줄")
            # 재무상태표 자산총계 찾기
            for line in lines:
                if "자산총계" in line or "자산 총계" in line:
                    print(f"  → {line.strip()[:120]}")
                    break

        if sep.height > 0:
            content = sep["section_content"][0]
            lines = content.split("\n")
            print(f"\n[재무제표(별도)] {len(content)}자, {len(lines)}줄")
            for line in lines:
                if "자산총계" in line or "자산 총계" in line:
                    print(f"  → {line.strip()[:120]}")
                    break

        if cons.height == 0 and sep.height == 0:
            print("  둘 다 없음")

        return corpName, cons.height > 0, sep.height > 0

    return corpName, False, False


if __name__ == "__main__":
    # 연결 있는 대표 기업
    consTargets = [
        "005930",  # 삼성전자
        "000660",  # SK하이닉스
        "005380",  # 현대자동차
        "035420",  # NAVER
        "105560",  # KB금융
    ]

    # 연결 없는 기업 (NEITHER)
    neitherTargets = [
        "012210",  # 삼미금속
        "062040",  # 산일전기
        "177900",  # 쓰리에이로직스
        "272450",  # 진에어
        "281820",  # 케이씨텍
    ]

    print("=== 연결 있는 기업 ===")
    for code in consTargets:
        compareStatements(code)

    print("\n\n=== 연결 없는 기업 ===")
    for code in neitherTargets:
        compareStatements(code)
