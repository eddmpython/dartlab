"""무형자산 — 유형자산 파서 대량 적용 테스트.

전체 기업에 findMovementTables를 적용하고 성공률 측정.
실패 패턴을 분류해서 별도 파서 개발 범위 판단.
"""

import os
import sys

sys.path.insert(0, "src")

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.notesExtractor import extractNotesContent, findNumberedSection
from dartlab.core.reportSelector import selectReport
from dartlab.finance.tangibleAsset.parser import findMovementTables

DATA_DIR = r"C:\Users\MSI\OneDrive\Desktop\sideProject\nicegui\eddmpython\data\dartData\docsData"


if __name__ == "__main__":
    codes = sorted(
        f.replace(".parquet", "")
        for f in os.listdir(DATA_DIR)
        if f.endswith(".parquet")
    )

    hasSection = 0
    ok = 0
    fail = 0
    noSection = 0

    failTypes = {
        "no_blocks": 0,
        "bad_cats": 0,
    }

    for code in codes:
        df = loadData(code)
        corpName = extractCorpName(df)
        years = sorted(df["year"].unique().to_list(), reverse=True)

        report = selectReport(df, years[0], reportKind="annual")
        if report is None:
            continue

        contents = extractNotesContent(report)
        if not contents:
            continue

        section = findNumberedSection(contents, "무형자산")
        if section is None:
            noSection += 1
            continue

        hasSection += 1
        results, warnings = findMovementTables(section)

        if results:
            hasDangki = any(r["period"] == "당기" for r in results)
            hasEnd = any(
                any(row["label"] == "기말" for row in r["rows"])
                for r in results
            )
            if hasDangki and hasEnd:
                ok += 1
            else:
                fail += 1
                failTypes["bad_cats"] += 1
        else:
            fail += 1
            failTypes["no_blocks"] += 1

    total = hasSection
    print(f"=== 무형자산 — 유형자산 파서 적용 결과 ===")
    print(f"무형자산 섹션 있음: {hasSection}")
    print(f"섹션 없음: {noSection}")
    print(f"파싱 성공: {ok}/{total} ({ok/total*100:.1f}%)")
    print(f"파싱 실패: {fail}/{total}")
    print(f"  블록 못 찾음: {failTypes['no_blocks']}")
    print(f"  불완전 결과: {failTypes['bad_cats']}")
