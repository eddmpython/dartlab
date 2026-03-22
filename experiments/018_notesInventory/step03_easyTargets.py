"""주석 후보 — 구조 난이도 빠른 조사.

각 후보의 대표 기업 3개에서 섹션 내용을 뽑아 구조 파악.
테이블 형태인지, 변동표인지, 단순 목록인지 분류.
"""

import os
import sys

sys.path.insert(0, "src")

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.notesExtractor import extractNotesContent, findNumberedSection
from dartlab.core.reportSelector import selectReport

DATA_DIR = r"C:\Users\MSI\OneDrive\Desktop\sideProject\nicegui\eddmpython\data\dartData\docsData"

CANDIDATES = [
    ("차입금", ["005930", "000660", "051910"]),
    ("리스", ["005930", "035420", "051910"]),
    ("재고자산", ["005930", "005380", "051910"]),
    ("매출채권", ["005930", "035420", "006400"]),
    ("충당부채", ["005930", "005380", "051910"]),
    ("투자부동산", ["005930", "034730", "028260"]),
    ("주당이익", ["005930", "005380", "035420"]),
]


if __name__ == "__main__":
    for keyword, targetCodes in CANDIDATES:
        print(f"\n{'='*60}")
        print(f"=== {keyword} ===")

        for code in targetCodes:
            df = loadData(code)
            corpName = extractCorpName(df)
            years = sorted(df["year"].unique().to_list(), reverse=True)

            report = selectReport(df, years[0], reportKind="annual")
            if report is None:
                continue

            contents = extractNotesContent(report)
            if not contents:
                continue

            section = findNumberedSection(contents, keyword)
            if section is None:
                print(f"\n  [{code}] {corpName}: 섹션 없음")
                continue

            lines = section.split("\n")
            tableLines = [l for l in lines if l.strip().startswith("|")]
            textLines = [l for l in lines if l.strip() and not l.strip().startswith("|")]

            print(f"\n  [{code}] {corpName}")
            print(f"    총 {len(lines)}줄, 테이블 {len(tableLines)}줄, 텍스트 {len(textLines)}줄")
            print(f"    미리보기 (첫 300자):")
            preview = section[:300].replace("\n", "\n    ")
            print(f"    {preview}")
