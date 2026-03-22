"""
실험 037 · step01 — 주주총회 등에 관한 사항 탐색 + 파싱

목적: 주주총회 결의사항, 투표 참여율 등 파싱
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
    text = re.sub(r"[^\d]", "", text)
    if not text:
        return None
    try:
        return int(text)
    except (ValueError, OverflowError):
        return None


def parseMeetingAgenda(content: str) -> list[dict]:
    """주주총회 안건 파싱."""
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
        if any("안건" in c or "의안" in c or "부의안건" in c for c in cells) and any(
            "결과" in c or "가결" in c or "찬성" in c or "내용" in c for c in cells
        ):
            headerFound = True
            continue

        if any("구분" in c or "구 분" in c for c in cells) and any(
            "안건" in c or "내용" in c for c in cells
        ):
            headerFound = True
            continue

        if not headerFound:
            continue

        # 데이터 행
        label = ""
        for c in cells:
            if len(c.strip()) >= 3 and parseAmount(c) is None:
                label = c.strip()
                break

        if not label:
            continue

        entry: dict = {"agenda": label}
        # 결과 찾기
        for c in cells:
            if "가결" in c or "승인" in c or "원안" in c:
                entry["result"] = c.strip()
                break
            elif "부결" in c:
                entry["result"] = c.strip()
                break

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
            if "주주총회" in title:
                content = row.get("section_content", "") or ""
                if len(content) < 50:
                    continue

                agendas = parseMeetingAgenda(content)
                if agendas:
                    return {"corpName": corpName, "year": year, "agendas": agendas}

                # 텍스트만 있는 경우
                if len(content) > 200:
                    return {"corpName": corpName, "year": year, "agendas": [], "textOnly": True}
    return None


if __name__ == "__main__":
    files = sorted([f.replace(".parquet", "") for f in os.listdir(DATA_DIR) if f.endswith(".parquet")])
    ok = fail = 0
    totalAgendas = 0
    errors = []

    for code in files:
        try:
            r = pipeline(code)
            if r is None:
                fail += 1
            else:
                ok += 1
                totalAgendas += len(r["agendas"])
        except Exception as e:
            fail += 1
            errors.append((code, str(e)))

    total = len(files)
    print(f"\n=== 037 주주총회 배치 결과 ===")
    print(f"성공: {ok}/{total} ({ok/total*100:.1f}%)")
    print(f"실패: {fail}/{total}")
    print(f"안건: {totalAgendas}건")
    if errors:
        print(f"에러 ({len(errors)}건):")
        for code, err in errors[:5]:
            print(f"  {code}: {err}")
