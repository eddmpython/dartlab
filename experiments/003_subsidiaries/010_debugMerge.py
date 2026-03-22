"""서브헤더 병합 디버깅."""
import re
from pathlib import Path

import polars as pl

# 007_v2Parse.py의 함수들 직접 로드
exec(open("experiments/003_subsidiaries/007_v2Parse.py", encoding="utf-8").read().split("def main")[0])

df = pl.read_parquet("data/docsData/035420.parquet")
contents = extractNotes(df, "2025")
section = findSection(contents, "관계기업") or findSection(contents, "공동기업")
rows = parseTableRows(section)

# 변동내역 추출 디버깅
headers = None
colMap = None
headerIdx = None

for i, cells in enumerate(rows[148:165], start=148):
    cellStr = " ".join(cells)
    hasOpening = any(kw in cellStr for kw in MOVEMENT_HEADER_KEYWORDS)
    if hasOpening and 3 <= len(cells) <= 30:
        movKws = sum(1 for kw in MOVEMENT_COL_MAP if kw in cellStr)
        if movKws >= 2:
            headers = cells
            colMap = _mapMovementColumns(headers)
            headerIdx = i
            print(f"[{i}] HEADER ({len(cells)}셀): {' | '.join(cells[:12])}")
            print(f"  colMap: {colMap}")
            continue

    # 서브헤더 체크
    if headers and headerIdx is not None and i == headerIdx + 1:
        subKws = sum(1 for kw in MOVEMENT_COL_MAP if kw in cellStr)
        print(f"[{i}] SUB? ({len(cells)}셀): {' | '.join(cells)} (subKws={subKws}, headerLen={len(headers)})")
        if subKws >= 2 and len(cells) < len(headers):
            headers = _mergeSubHeader(headers, cells)
            colMap = _mapMovementColumns(headers)
            print(f"  MERGED: {' | '.join(headers[:12])}")
            print(f"  mergedColMap: {colMap}")
            continue

    if headers is None:
        continue

    # 데이터행 테스트
    if len(cells) >= 2:
        firstCell = cells[0].strip()
        if _isNameCell(firstCell) or firstCell in ("관계기업", "공동기업"):
            offset = len(headers) - len(cells) if len(cells) < len(headers) else 0
            name = firstCell
            if firstCell in ("관계기업", "공동기업") and len(cells) > 2:
                name = cells[1].strip()

            vals = {}
            for j, fieldName in colMap.items():
                dataIdx = j - offset
                if 0 <= dataIdx < len(cells):
                    val = parseAmount(cells[dataIdx])
                    vals[fieldName] = val

            print(f"[{i}] DATA ({len(cells)}셀, offset={offset}): {name}")
            print(f"  vals: {vals}")
            if i >= 155:
                break
