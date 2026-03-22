"""
실험 038 · step01 — 감사제도에 관한 사항 탐색 + 파싱

목적: 감사위원회 구성, 활동 횟수, 위원 정보 파싱
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


def parseAuditCommittee(content: str) -> list[dict]:
    """감사위원회 위원 현황 파싱."""
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

        # 헤더 감지
        if any("성명" in c or "위원" in c for c in cells) and any(
            "직위" in c or "구분" in c or "경력" in c or "사외" in c or "재직" in c for c in cells
        ):
            headerFound = True
            continue

        if not headerFound:
            continue

        # 데이터 행
        name = cells[0].strip()
        if not name or len(name) < 2 or name in ("합계", "합 계", "소계"):
            continue

        entry: dict = {"name": name}
        if len(cells) >= 2:
            entry["role"] = cells[1].strip()
        if len(cells) >= 3:
            entry["detail"] = cells[2].strip()

        results.append(entry)

    return results


def parseAuditActivity(content: str) -> list[dict]:
    """감사 활동 내역 파싱."""
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

        if any("개최일자" in c or "일자" in c for c in cells) and any(
            "의안" in c or "안건" in c or "내용" in c or "보고" in c for c in cells
        ):
            headerFound = True
            continue

        if not headerFound:
            continue

        date = cells[0].strip()
        if not date or not re.search(r"\d{4}", date):
            continue

        agenda = cells[1].strip() if len(cells) >= 2 else ""
        entry: dict = {"date": date}
        if agenda:
            entry["agenda"] = agenda
        if len(cells) >= 3:
            entry["result"] = cells[2].strip()

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
            if "감사" in title and ("제도" in title or "기구" in title):
                content = row.get("section_content", "") or ""
                if len(content) < 50:
                    continue

                committee = parseAuditCommittee(content)
                activity = parseAuditActivity(content)

                if committee or activity:
                    return {
                        "corpName": corpName,
                        "year": year,
                        "committee": committee,
                        "activity": activity,
                    }

                if len(content) > 200:
                    return {
                        "corpName": corpName,
                        "year": year,
                        "committee": [],
                        "activity": [],
                        "textOnly": True,
                    }
    return None


if __name__ == "__main__":
    files = sorted([f.replace(".parquet", "") for f in os.listdir(DATA_DIR) if f.endswith(".parquet")])
    ok = fail = 0
    totalCommittee = 0
    totalActivity = 0
    errors = []

    for code in files:
        try:
            r = pipeline(code)
            if r is None:
                fail += 1
            else:
                ok += 1
                totalCommittee += len(r["committee"])
                totalActivity += len(r["activity"])
        except Exception as e:
            fail += 1
            errors.append((code, str(e)))

    total = len(files)
    print(f"\n=== 038 감사제도 배치 결과 ===")
    print(f"성공: {ok}/{total} ({ok/total*100:.1f}%)")
    print(f"실패: {fail}/{total}")
    print(f"감사위원: {totalCommittee}건")
    print(f"감사활동: {totalActivity}건")
    if errors:
        print(f"에러 ({len(errors)}건):")
        for code, err in errors[:5]:
            print(f"  {code}: {err}")
