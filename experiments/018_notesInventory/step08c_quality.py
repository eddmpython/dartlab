"""재고자산 파싱 결과 품질 검증.

다양한 패턴의 기업에서 파싱 결과가 정확한지 확인.
"""

import os
import sys

sys.path.insert(0, "src")

from step08_inventoryParser import parseInventory

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.notesExtractor import extractNotesContent, findNumberedSection
from dartlab.core.reportSelector import selectReport

DATA_DIR = r"C:\Users\MSI\OneDrive\Desktop\sideProject\nicegui\eddmpython\data\dartData\docsData"

SAMPLES = [
    ("005930", "삼성전자"),
    ("000020", "동화약품"),
    ("022100", "포스코DX"),
    ("465770", "STX그린로지스"),
    ("475150", "SK이터닉스"),
    ("010400", "우진아이엔에스"),
]


if __name__ == "__main__":
    for code, label in SAMPLES:
        df = loadData(code)
        corpName = extractCorpName(df)
        years = sorted(df["year"].unique().to_list(), reverse=True)
        report = selectReport(df, years[0], reportKind="annual")
        contents = extractNotesContent(report)
        section = findNumberedSection(contents, "재고자산")

        if section is None:
            print(f"\n=== [{code}] {corpName} — 섹션 없음 ===")
            continue

        result = parseInventory(section)

        print(f"\n=== [{code}] {corpName} ===")
        if result is None:
            print("  파싱 실패")
            continue

        for period in result:
            print(f"  [{period['period']}] headers={period['headers']}")
            for item in period["items"][:5]:
                print(f"    {item['name']}: {item['values']}")
            if len(period["items"]) > 5:
                print(f"    ... 총 {len(period['items'])}개 항목")
