"""15개 신규 후보 — 파싱 실패 케이스 분석.

각 키워드별 실패 기업의 섹션 내용을 분석하여
parseNotesTable 개선 방향 도출.
"""

import os
import sys

sys.path.insert(0, "src")

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.notesExtractor import extractNotesContent, findNumberedSection
from dartlab.core.reportSelector import selectReport
from dartlab.core.tableParser import extractRawTables, extractTables, parseNotesTable

DATA_DIR = r"C:\Users\MSI\OneDrive\Desktop\sideProject\nicegui\eddmpython\data\dartData\docsData"

CANDIDATES = [
    "법인세", "특수관계자", "약정사항", "금융자산", "공정가치",
    "이익잉여금", "금융부채", "기타포괄손익", "사채",
    "종업원급여", "퇴직급여", "확정급여", "재무위험", "우발부채", "담보",
]


def classifyFailure(section: str) -> str:
    lines = section.split("\n")
    tableLines = [l for l in lines if l.strip().startswith("|")]
    textLines = [l for l in lines if l.strip() and not l.strip().startswith("|")]

    if not tableLines:
        return "no_table"

    rawTables = extractRawTables(section)
    if not rawTables:
        return "extract_fail"

    totalRows = sum(len(t["rows"]) for t in rawTables)
    if totalRows <= 1:
        return "few_rows"

    return "parse_logic"


if __name__ == "__main__":
    codes = sorted(
        f.replace(".parquet", "")
        for f in os.listdir(DATA_DIR)
        if f.endswith(".parquet")
    )

    for kw in CANDIDATES:
        failures = []
        found = 0

        for code in codes:
            df = loadData(code)
            years = sorted(df["year"].unique().to_list(), reverse=True)
            report = selectReport(df, years[0], reportKind="annual")
            if report is None:
                continue
            contents = extractNotesContent(report)
            if not contents:
                continue
            section = findNumberedSection(contents, kw)
            if section is None:
                continue
            found += 1
            result = parseNotesTable(section)
            if not result:
                corpName = extractCorpName(df)
                category = classifyFailure(section)
                failures.append((code, corpName, category, section))

        if not failures:
            continue

        print(f"\n{'='*60}")
        print(f"=== {kw} — {len(failures)}/{found} 실패 ({len(failures)/found*100:.1f}%) ===")

        categories = {}
        for code, name, cat, sec in failures:
            categories.setdefault(cat, []).append((code, name, sec))

        for cat, items in sorted(categories.items(), key=lambda x: -len(x[1])):
            print(f"\n  [{cat}] {len(items)}건")
            for code, name, sec in items[:3]:
                lines = sec.split("\n")
                tableLines = [l for l in lines if l.strip().startswith("|")]
                print(f"    {code} {name} — {len(lines)}줄, 테이블 {len(tableLines)}줄")
                preview = sec[:200].replace("\n", "\n      ")
                print(f"      {preview}")
