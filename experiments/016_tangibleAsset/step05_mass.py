"""전체 267개 기업 유형자산 변동표 파싱 대규모 실험."""

import os
import sys

sys.path.insert(0, "src")

from step03_parser import findMovementTables, getTotalValue

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.notesExtractor import extractNotesContent, findNumberedSection
from dartlab.core.reportSelector import selectReport

DATA_DIR = r"C:\Users\MSI\OneDrive\Desktop\sideProject\nicegui\eddmpython\data\dartData\docsData"


def getAllStockCodes():
    codes = []
    for fname in sorted(os.listdir(DATA_DIR)):
        if fname.endswith(".parquet"):
            codes.append(fname.replace(".parquet", ""))
    return codes


def testOne(stockCode):
    df = loadData(stockCode)
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
        if section is None:
            continue

        movements = findMovementTables(section)
        if movements:
            danggi = [m for m in movements if m["period"] == "당기"]
            jeongi = [m for m in movements if m["period"] == "전기"]

            danggiMain = None
            for d in danggi:
                rows = d["rows"]
                hasStart = any(r["label"] == "기초" for r in rows)
                hasEnd = any(r["label"] == "기말" for r in rows)
                if hasStart and hasEnd and len(rows) >= 3:
                    if danggiMain is None or len(d["categories"]) > len(danggiMain["categories"]):
                        danggiMain = d

            return {
                "code": stockCode,
                "name": corpName,
                "year": year,
                "status": "OK",
                "danggiCount": len(danggi),
                "jeongiCount": len(jeongi),
                "categories": danggiMain["categories"] if danggiMain else [],
                "rowCount": len(danggiMain["rows"]) if danggiMain else 0,
                "unit": danggiMain["unit"] if danggiMain else None,
            }

        return {
            "code": stockCode,
            "name": corpName,
            "year": year,
            "status": "NO_MOVEMENT",
            "section_length": len(section),
        }

    return {
        "code": stockCode,
        "name": corpName,
        "year": None,
        "status": "NO_SECTION",
    }


if __name__ == "__main__":
    codes = getAllStockCodes()
    print(f"전체 {len(codes)}개 기업 테스트")
    print("=" * 80)

    okList = []
    noMovList = []
    noSecList = []
    errorList = []

    for i, code in enumerate(codes):
        try:
            result = testOne(code)
        except Exception as e:
            result = {"code": code, "status": "ERROR", "error": str(e)}

        status = result["status"]
        if status == "OK":
            okList.append(result)
        elif status == "NO_MOVEMENT":
            noMovList.append(result)
        elif status == "NO_SECTION":
            noSecList.append(result)
        else:
            errorList.append(result)

        if (i + 1) % 50 == 0:
            print(f"  ... {i + 1}/{len(codes)} 완료 (OK: {len(okList)})")

    print(f"\n{'=' * 80}")
    print(f"결과 요약")
    print(f"{'=' * 80}")
    print(f"  전체: {len(codes)}개")
    print(f"  성공 (변동표 추출): {len(okList)}개 ({len(okList)/len(codes)*100:.1f}%)")
    print(f"  주석 있으나 변동표 실패: {len(noMovList)}개")
    print(f"  유형자산 주석 없음: {len(noSecList)}개")
    print(f"  에러: {len(errorList)}개")

    if noMovList:
        print(f"\n변동표 실패 목록:")
        for r in noMovList:
            print(f"  {r['code']} {r.get('name', '')} (섹션 {r.get('section_length', 0):,}자)")

    if noSecList:
        print(f"\n주석 없음 목록:")
        for r in noSecList[:20]:
            print(f"  {r['code']} {r.get('name', '')}")
        if len(noSecList) > 20:
            print(f"  ... 외 {len(noSecList) - 20}개")

    if errorList:
        print(f"\n에러 목록:")
        for r in errorList:
            print(f"  {r['code']}: {r.get('error', '')[:80]}")

    if okList:
        print(f"\n{'─' * 60}")
        print(f"성공 기업 카테고리 수 분포:")
        catCounts = {}
        for r in okList:
            n = len(r["categories"])
            catCounts[n] = catCounts.get(n, 0) + 1
        for n in sorted(catCounts.keys()):
            print(f"  {n}개 카테고리: {catCounts[n]}개 기업")

        print(f"\n변동행 수 분포:")
        rowCounts = {}
        for r in okList:
            n = r["rowCount"]
            rowCounts[n] = rowCounts.get(n, 0) + 1
        for n in sorted(rowCounts.keys()):
            print(f"  {n}행: {rowCounts[n]}개 기업")

        print(f"\n단위 분포:")
        unitCounts = {}
        for r in okList:
            u = r["unit"]
            unitCounts[u] = unitCounts.get(u, 0) + 1
        for u, cnt in sorted(unitCounts.items(), key=lambda x: -x[1]):
            print(f"  {u}: {cnt}개 기업")
