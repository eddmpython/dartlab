"""
실험 039 · step01 — 타법인출자 현황(상세) 탐색 + 파싱

목적: 타법인 투자 목록 (법인명, 지분율, 취득가, 장부가) 파싱
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
    text = text.strip()
    if text in ("-", "−", "–", ""):
        return None
    negative = False
    if text.startswith("△") or text.startswith("(") or text.startswith("−"):
        negative = True
        text = text.lstrip("△(−").rstrip(")")
    text = text.replace(",", "").replace(" ", "")
    text = re.sub(r"[^\d.]", "", text)
    if not text:
        return None
    try:
        val = int(float(text))
        return -val if negative else val
    except (ValueError, OverflowError):
        return None


def parseInvestments(content: str) -> list[dict]:
    """타법인출자 현황 파싱."""
    lines = content.split("\n")
    results: list[dict] = []
    headerFound = False

    for line in lines:
        stripped = line.strip()
        if "|" not in stripped or isSeparatorRow(stripped):
            continue

        cells = splitCells(stripped)
        if len(cells) < 3:
            continue

        # 단위 행 스킵
        if any("단위" in c for c in cells) and len(cells) <= 2:
            continue

        # 헤더 감지
        if any("법인명" in c or "회사명" in c or "종목명" in c for c in cells) and any(
            "지분" in c or "장부" in c or "취득" in c or "기초" in c or "기말" in c for c in cells
        ):
            headerFound = True
            continue

        if not headerFound:
            continue

        # 합계 행 스킵
        if any(c.strip() in ("합계", "합 계", "소계", "소 계", "총계") for c in cells):
            continue

        # 데이터 행: 법인명 + 숫자
        name = ""
        nums = []
        for c in cells:
            val = parseAmount(c)
            if val is not None:
                nums.append(val)
            elif c.strip() and len(c.strip()) >= 2 and c.strip() not in ("-", "−", "–"):
                if not name:
                    name = c.strip()

        if not name or not nums:
            continue

        results.append({"name": name, "values": nums})

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
            if "타법인" in title and ("출자" in title or "투자" in title):
                content = row.get("section_content", "") or ""
                if len(content) < 50:
                    continue

                investments = parseInvestments(content)
                if investments:
                    return {"corpName": corpName, "year": year, "investments": investments}

                if "해당사항" in content[:500] or "없습니다" in content[:500]:
                    return {"corpName": corpName, "year": year, "investments": [], "noData": True}
    return None


if __name__ == "__main__":
    files = sorted([f.replace(".parquet", "") for f in os.listdir(DATA_DIR) if f.endswith(".parquet")])
    ok = fail = 0
    totalInvestments = 0
    errors = []

    for code in files:
        try:
            r = pipeline(code)
            if r is None:
                fail += 1
            else:
                ok += 1
                totalInvestments += len(r["investments"])
        except Exception as e:
            fail += 1
            errors.append((code, str(e)))

    total = len(files)
    print(f"\n=== 039 타법인출자 현황 배치 결과 ===")
    print(f"성공: {ok}/{total} ({ok/total*100:.1f}%)")
    print(f"실패: {fail}/{total}")
    print(f"투자법인: {totalInvestments}건")
    if errors:
        print(f"에러 ({len(errors)}건):")
        for code, err in errors[:5]:
            print(f"  {code}: {err}")
