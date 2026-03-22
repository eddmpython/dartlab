"""
실험 036 · step01 — 회사의 연혁 탐색 + 파싱

목적: 회사의 연혁 섹션에서 연혁 이벤트 테이블 파싱
실험일: 2026-03-08
"""

import os
import re
import sys

DATA_DIR = r"C:\Users\MSI\OneDrive\Desktop\sideProject\nicegui\eddmpython\data\dartData\docsData"
sys.path.insert(0, r"C:\Users\MSI\OneDrive\Desktop\sideProject\dartlab\src")

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.reportSelector import selectReport


def splitCells(line: str) -> list[str]:
    cells = [c.strip() for c in line.split("|")]
    while cells and cells[0] == "":
        cells.pop(0)
    while cells and cells[-1] == "":
        cells.pop()
    return cells


def isSeparatorRow(line: str) -> bool:
    cells = splitCells(line)
    return all(re.match(r"^-+$", c.strip()) for c in cells if c.strip())


def parseHistory(content: str) -> list[dict]:
    """연혁 테이블 파싱."""
    lines = content.split("\n")
    results: list[dict] = []
    headerFound = False

    for line in lines:
        stripped = line.strip()
        if "|" not in stripped or isSeparatorRow(stripped):
            continue

        cells = splitCells(stripped)
        if len(cells) < 2:
            continue

        # 헤더 감지
        if any("일자" in c or "연월" in c or "날짜" in c or "년월" in c for c in cells) and any(
            "내용" in c or "연혁" in c or "사항" in c or "내역" in c for c in cells
        ):
            headerFound = True
            continue

        if not headerFound:
            # 날짜 패턴이 있으면 헤더 없이도 파싱
            if re.search(r"\d{4}[년.]\s*\d{1,2}", cells[0]):
                headerFound = True
            else:
                continue

        date = cells[0].strip()
        if not date or not re.search(r"\d{4}", date):
            continue

        event = cells[1].strip() if len(cells) >= 2 else ""
        if not event or len(event) < 2:
            continue

        results.append({"date": date, "event": event})

    return results


def pipeline(stockCode: str):
    try:
        df = loadData(stockCode)
    except FileNotFoundError:
        return None

    corpName = extractCorpName(df)
    years = sorted(df["year"].unique().to_list(), reverse=True)

    for year in years[:2]:
        report = selectReport(df, year, reportKind="annual")
        if report is None:
            continue

        for row in report.iter_rows(named=True):
            title = row.get("section_title", "") or ""
            if "연혁" in title and ("회사" in title or title.strip().endswith("연혁")):
                content = row.get("section_content", "") or ""
                if len(content) < 50:
                    continue

                events = parseHistory(content)
                if events:
                    return {"corpName": corpName, "year": year, "events": events}
    return None


if __name__ == "__main__":
    files = sorted([f.replace(".parquet", "") for f in os.listdir(DATA_DIR) if f.endswith(".parquet")])
    ok = fail = 0
    totalEvents = 0
    errors = []

    for code in files:
        try:
            r = pipeline(code)
            if r is None:
                fail += 1
            else:
                ok += 1
                totalEvents += len(r["events"])
        except Exception as e:
            fail += 1
            errors.append((code, str(e)))

    total = len(files)
    print(f"\n=== 036 회사의 연혁 배치 결과 ===")
    print(f"성공: {ok}/{total} ({ok/total*100:.1f}%)")
    print(f"실패: {fail}/{total}")
    print(f"연혁 이벤트: {totalEvents}건")
    if errors:
        print(f"에러 ({len(errors)}건):")
        for code, err in errors[:5]:
            print(f"  {code}: {err}")
