"""재고자산 파싱 실패 케이스 분석.

step04에서 30개 실패 — 원인 분류 및 샘플 출력.
"""

import os
import sys

sys.path.insert(0, "src")

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.notesExtractor import extractNotesContent, findNumberedSection
from dartlab.core.reportSelector import selectReport
from dartlab.core.tableParser import detectUnit, extractTables

DATA_DIR = r"C:\Users\MSI\OneDrive\Desktop\sideProject\nicegui\eddmpython\data\dartData\docsData"


def classifyFailure(section: str) -> str:
    """실패 원인 분류."""
    tables = extractTables(section)

    if not tables:
        if len(section) < 50:
            return "too_short"
        return "no_table"

    for t in tables:
        headers = t["headers"]
        rows = t["rows"]
        headerText = " ".join(headers)

        if "단위" in headerText:
            continue

        if len(headers) < 2:
            continue

        if len(rows) < 2:
            return "few_rows"

        return "filter_issue"

    if all("단위" in " ".join(t["headers"]) for t in tables if t["headers"]):
        return "unit_only"

    return "other"


if __name__ == "__main__":
    codes = sorted(
        f.replace(".parquet", "")
        for f in os.listdir(DATA_DIR)
        if f.endswith(".parquet")
    )

    failures = {}
    total = 0

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

        section = findNumberedSection(contents, "재고자산")
        if section is None:
            continue

        total += 1
        tables = extractTables(section)

        hasData = False
        for t in tables:
            if len(t["headers"]) >= 2 and len(t["rows"]) >= 2:
                headerText = " ".join(t["headers"])
                if "단위" not in headerText:
                    hasData = True
                    break

        if not hasData:
            reason = classifyFailure(section)
            failures[code] = {
                "corpName": corpName,
                "reason": reason,
                "sectionLen": len(section),
                "tableCount": len(tables),
                "preview": section[:300],
            }

    print(f"=== 재고자산 실패 분석 ({len(failures)}/{total}) ===\n")

    from collections import Counter
    reasons = Counter(f["reason"] for f in failures.values())
    for reason, count in reasons.most_common():
        print(f"  {reason}: {count}")

    for reason in reasons:
        print(f"\n--- {reason} ---")
        samples = [
            (code, f) for code, f in failures.items()
            if f["reason"] == reason
        ]
        for code, f in samples[:3]:
            print(f"\n[{code}] {f['corpName']} (길이: {f['sectionLen']}, 테이블: {f['tableCount']})")
            print(f"미리보기:\n{f['preview']}\n")

            tables = extractTables(findNumberedSection(
                extractNotesContent(
                    selectReport(
                        loadData(code),
                        sorted(loadData(code)["year"].unique().to_list(), reverse=True)[0],
                        reportKind="annual",
                    )
                ),
                "재고자산",
            ))
            for i, t in enumerate(tables):
                print(f"  Table {i}: headers={t['headers']}")
                for row in t["rows"][:3]:
                    print(f"    {row}")
