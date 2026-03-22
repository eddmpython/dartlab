"""파싱 품질 검증 — 블록 구조 분석 + 값 정확성 체크."""

import os
import sys

sys.path.insert(0, "src")

from step03_parser import findMovementTables, getTotalValue

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.notesExtractor import extractNotesContent, findNumberedSection
from dartlab.core.reportSelector import selectReport

DATA_DIR = r"C:\Users\MSI\OneDrive\Desktop\sideProject\nicegui\eddmpython\data\dartData\docsData"


def getSection(code):
    df = loadData(code)
    corpName = extractCorpName(df)
    years = sorted(df["year"].unique().to_list(), reverse=True)
    for year in years[:2]:
        report = selectReport(df, year, reportKind="annual")
        if report is None:
            continue
        notes = extractNotesContent(report)
        if not notes:
            continue
        section = findNumberedSection(notes, "유형자산")
        if section:
            return corpName, year, section
    return corpName, None, None


if __name__ == "__main__":
    codes = sorted(
        f.replace(".parquet", "") for f in os.listdir(DATA_DIR) if f.endswith(".parquet")
    )

    multiBlock = []
    noEnd = []
    dupLabel = []
    negTotal = []
    okCount = 0

    for code in codes:
        corpName, year, section = getSection(code)
        if section is None:
            continue
        results = findMovementTables(section)
        if not results:
            continue

        dangki = [r for r in results if r["period"] == "당기"]
        if len(dangki) > 1:
            multiBlock.append((code, corpName, len(dangki)))

        if dangki:
            main = dangki[0]
            rowLabels = [r["label"] for r in main["rows"]]

            if "기말" not in rowLabels:
                noEnd.append((code, corpName, rowLabels))

            seen = set()
            dups = []
            for rl in rowLabels:
                if rl in seen:
                    dups.append(rl)
                seen.add(rl)
            if dups:
                dupLabel.append((code, corpName, dups))

            total = getTotalValue(
                next((r for r in main["rows"] if r["label"] == "기말"), {"values": {}}),
                main["categories"],
            )
            if total is not None and total < 0:
                negTotal.append((code, corpName, total))

            okCount += 1

    print(f"당기 블록 있는 기업: {okCount}")
    print(f"\n다중 당기 블록: {len(multiBlock)}")
    for code, name, cnt in multiBlock[:15]:
        print(f"  [{code}] {name}: {cnt}개")

    print(f"\n기말 행 없음: {len(noEnd)}")
    for code, name, labels in noEnd[:10]:
        print(f"  [{code}] {name}: {labels}")

    print(f"\n라벨 중복: {len(dupLabel)}")
    for code, name, dups in dupLabel[:10]:
        print(f"  [{code}] {name}: {dups}")

    print(f"\n기말 합계 음수: {len(negTotal)}")
    for code, name, val in negTotal[:10]:
        print(f"  [{code}] {name}: {val:,.0f}")
