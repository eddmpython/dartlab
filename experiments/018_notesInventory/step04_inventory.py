"""재고자산 주석 파싱 실험.

구조: 당기/전기 단순 테이블 (항목별 취득원가/평가충당금/장부금액)
extractAccounts로 바로 가능한지 확인.
"""

import os
import sys

sys.path.insert(0, "src")

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.notesExtractor import extractNotesContent, findNumberedSection
from dartlab.core.reportSelector import selectReport
from dartlab.core.tableParser import detectUnit, extractAccounts, extractTables

DATA_DIR = r"C:\Users\MSI\OneDrive\Desktop\sideProject\nicegui\eddmpython\data\dartData\docsData"


def parseInventory(section: str) -> dict | None:
    """재고자산 주석에서 당기/전기 내역 추출.

    일반 구조:
    당기 (단위: 백만원)
    | 구분 | 취득원가 | 평가충당금 | 장부금액 |
    | 제품 | 100 | -10 | 90 |
    ...
    전기 (단위: 백만원)
    | 구분 | 취득원가 | 평가충당금 | 장부금액 |
    ...
    """
    unit = detectUnit(section)
    tables = extractTables(section)

    if not tables:
        return None

    result = {"unit": unit, "periods": []}

    for table in tables:
        headers = table["headers"]
        rows = table["rows"]

        if len(headers) < 2 or len(rows) < 1:
            continue

        headerText = " ".join(headers)
        if "단위" in headerText:
            continue

        items = []
        for row in rows:
            if len(row) < 2:
                continue
            name = row[0].strip()
            if not name:
                continue
            items.append({
                "name": name,
                "cells": row[1:],
            })

        if items:
            result["periods"].append({
                "headers": headers,
                "items": items,
            })

    return result if result["periods"] else None


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
            noSection += 1
            continue

        hasSection += 1
        result = parseInventory(section)

        if result and result["periods"]:
            ok += 1
        else:
            fail += 1
            if fail <= 5:
                print(f"FAIL [{code}] {corpName}")
                print(f"  섹션 길이: {len(section)}")
                print(f"  미리보기: {section[:200]}")

    total = hasSection
    print(f"\n=== 재고자산 파싱 결과 ===")
    print(f"섹션 있음: {hasSection}, 없음: {noSection}")
    print(f"파싱 성공: {ok}/{total} ({ok/total*100:.1f}%)")
    print(f"실패: {fail}")

    # 샘플 결과 출력
    code = "005930"
    df = loadData(code)
    corpName = extractCorpName(df)
    years = sorted(df["year"].unique().to_list(), reverse=True)
    report = selectReport(df, years[0], reportKind="annual")
    contents = extractNotesContent(report)
    section = findNumberedSection(contents, "재고자산")
    result = parseInventory(section)
    print(f"\n=== 샘플: {corpName} ===")
    for i, period in enumerate(result["periods"]):
        print(f"  Period {i}: headers={period['headers']}")
        for item in period["items"][:5]:
            print(f"    {item['name']}: {item['cells']}")
