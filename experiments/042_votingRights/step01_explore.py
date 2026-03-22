"""
실험 042 · step01 — 의결권 현황 탐색 + 파싱

목적: 의결권 주식수, 행사 현황 파싱
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


def parseAmount(text: str) -> int | None:
    if not text or not isinstance(text, str):
        return None
    text = text.strip().replace(",", "").replace(" ", "")
    if text in ("-", "−", "–", ""):
        return None
    text = re.sub(r"[^\d]", "", text)
    if not text:
        return None
    try:
        return int(text)
    except (ValueError, OverflowError):
        return None


def parseVotingRights(content: str) -> list[dict]:
    """의결권 현황 테이블 파싱."""
    lines = content.split("\n")
    results: list[dict] = []
    headerFound = False

    for line in lines:
        stripped = line.strip()
        if "|" not in stripped or isSeparatorRow(stripped):
            if headerFound and results:
                break
            continue

        cells = splitCells(stripped)
        if len(cells) < 2:
            continue

        if any("단위" in c for c in cells) and len(cells) <= 2:
            continue

        # 헤더 감지
        if any("구 분" in c or "구분" in c for c in cells) and any(
            "주식수" in c or "주식 수" in c or "수량" in c for c in cells
        ):
            headerFound = True
            continue

        if not headerFound:
            continue

        # 데이터
        label = ""
        for c in cells:
            if parseAmount(c) is None and c.strip() and len(c.strip()) >= 2:
                label = c.strip()
                break

        if not label:
            continue

        nums = [parseAmount(c) for c in cells]
        validNums = [n for n in nums if n is not None]

        entry: dict = {"label": label}
        if validNums:
            entry["shares"] = validNums[0]
        results.append(entry)

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
            if "의결권" in title and ("현황" in title or "행사" in title):
                content = row.get("section_content", "") or ""
                if len(content) < 50:
                    continue

                rights = parseVotingRights(content)
                if rights:
                    return {"corpName": corpName, "year": year, "rights": rights}

                if len(content) > 100:
                    return {"corpName": corpName, "year": year, "rights": [], "textOnly": True}
    return None


if __name__ == "__main__":
    files = sorted([f.replace(".parquet", "") for f in os.listdir(DATA_DIR) if f.endswith(".parquet")])
    ok = fail = 0
    totalRights = 0

    for code in files:
        try:
            r = pipeline(code)
            if r is None:
                fail += 1
            else:
                ok += 1
                totalRights += len(r["rights"])
        except Exception:
            fail += 1

    total = len(files)
    print(f"\n=== 042 의결권 현황 배치 결과 ===")
    print(f"성공: {ok}/{total} ({ok/total*100:.1f}%)")
    print(f"실패: {fail}/{total}")
    print(f"의결권 항목: {totalRights}건")
