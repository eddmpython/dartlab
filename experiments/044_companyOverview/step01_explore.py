"""
실험 044 · step01 — 회사의 개요 탐색 + 파싱

목적: 설립일, 상장일, 주요사업, 본점소재지 등 파싱
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


def parseCompanyInfo(content: str) -> dict:
    """회사 기본정보 테이블 파싱."""
    lines = content.split("\n")
    info: dict = {}

    for line in lines:
        stripped = line.strip()
        if "|" not in stripped or isSeparatorRow(stripped):
            continue

        cells = splitCells(stripped)
        if len(cells) < 2:
            continue

        for i, c in enumerate(cells):
            c_clean = c.strip()
            if "설립일" in c_clean and i + 1 < len(cells):
                info["foundedDate"] = cells[i + 1].strip()
            elif "상장일" in c_clean and i + 1 < len(cells):
                info["listedDate"] = cells[i + 1].strip()
            elif "본점소재지" in c_clean and i + 1 < len(cells):
                info["address"] = cells[i + 1].strip()
            elif "대표이사" in c_clean and i + 1 < len(cells):
                info["ceo"] = cells[i + 1].strip()
            elif "주요사업" in c_clean and i + 1 < len(cells):
                info["mainBusiness"] = cells[i + 1].strip()
            elif "홈페이지" in c_clean and i + 1 < len(cells):
                info["website"] = cells[i + 1].strip()

    return info


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
            if "회사의 개요" in title or "회사 의 개요" in title:
                content = row.get("section_content", "") or ""
                if len(content) < 50:
                    continue

                info = parseCompanyInfo(content)
                if info:
                    return {"corpName": corpName, "year": year, "info": info}

                if len(content) > 200:
                    return {"corpName": corpName, "year": year, "info": {}, "textOnly": True}
    return None


if __name__ == "__main__":
    files = sorted([f.replace(".parquet", "") for f in os.listdir(DATA_DIR) if f.endswith(".parquet")])
    ok = fail = withInfo = 0
    fields = set()

    for code in files:
        try:
            r = pipeline(code)
            if r is None:
                fail += 1
            else:
                ok += 1
                if r["info"]:
                    withInfo += 1
                    fields.update(r["info"].keys())
        except Exception:
            fail += 1

    total = len(files)
    print(f"\n=== 044 회사의 개요 배치 결과 ===")
    print(f"성공: {ok}/{total} ({ok/total*100:.1f}%)")
    print(f"실패: {fail}/{total}")
    print(f"기본정보 파싱: {withInfo}건")
    print(f"추출된 필드: {sorted(fields)}")
