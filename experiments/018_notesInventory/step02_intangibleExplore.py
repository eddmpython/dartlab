"""무형자산 주석 구조 탐색.

유형자산 파서(findMovementTables)를 그대로 적용할 수 있는지 확인.
- 변동표 구조 동일 여부
- 카테고리 차이 (영업권, 개발비, 산업재산권 등)
- 유형자산과의 차이점
"""

import os
import sys

sys.path.insert(0, "src")

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.notesExtractor import extractNotesContent, findNumberedSection
from dartlab.core.reportSelector import selectReport
from dartlab.finance.tangibleAsset.parser import findMovementTables, getTotalValue

DATA_DIR = r"C:\Users\MSI\OneDrive\Desktop\sideProject\nicegui\eddmpython\data\dartData\docsData"

TARGETS = [
    "005930",  # 삼성전자
    "000660",  # SK하이닉스
    "005380",  # 현대자동차
    "035420",  # NAVER
    "051910",  # LG화학
    "006400",  # 삼성SDI
    "003550",  # LG
    "034730",  # SK
    "028260",  # 삼성물산
    "105560",  # KB금융
]


if __name__ == "__main__":
    ok = 0
    fail = 0
    noSection = 0

    for code in TARGETS:
        df = loadData(code)
        corpName = extractCorpName(df)
        years = sorted(df["year"].unique().to_list(), reverse=True)

        report = selectReport(df, years[0], reportKind="annual")
        if report is None:
            print(f"[{code}] {corpName}: 보고서 없음")
            continue

        contents = extractNotesContent(report)
        if not contents:
            print(f"[{code}] {corpName}: 주석 없음")
            continue

        section = findNumberedSection(contents, "무형자산")
        if section is None:
            print(f"[{code}] {corpName}: 무형자산 섹션 없음")
            noSection += 1
            continue

        print(f"\n{'='*60}")
        print(f"[{code}] {corpName}")
        print(f"무형자산 섹션 길이: {len(section)} chars")
        print(f"첫 500자:")
        print(section[:500])
        print(f"...")

        results, warnings = findMovementTables(section)
        if results:
            ok += 1
            print(f"\n파싱 성공: {len(results)}개 블록")
            for r in results:
                period = r["period"]
                cats = r["categories"]
                rows = r["rows"]
                print(f"  {period}: {len(cats)}개 카테고리, {len(rows)}개 행")
                print(f"    카테고리: {cats[:5]}{'...' if len(cats) > 5 else ''}")
                print(f"    행 라벨: {[row['label'] for row in rows]}")

                total = getTotalValue(r, "기말")
                if total is not None:
                    print(f"    기말 합계: {total:,.0f}")
        else:
            fail += 1
            print(f"\n파싱 실패")
            if warnings:
                print(f"  경고: {warnings}")

    print(f"\n=== 요약 ===")
    print(f"성공: {ok}, 실패: {fail}, 섹션없음: {noSection}")
