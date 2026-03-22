"""실험 ID: 063-011
실험명: multi_year 수평화 강건성 — 보통주/우선주 + 항목명 정규화 + 다종목

목적:
- 보통주/우선주 연속행 처리
- 항목명 정규화 (공백/괄호 통일)
- 5종목에서 dividend multi_year 수평화 검증
- 사용자가 실제로 쓸 수 있는 품질인지 확인

실험일: 2026-03-16
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import polars as pl
from dartlab.engines.company.dart.docs.sections.pipeline import sections


def splitSubtables(md):
    tables, current = [], []
    for line in md.strip().split("\n"):
        s = line.strip()
        if not s.startswith("|"):
            if current: tables.append(current); current = []
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        isSep = all(set(c.strip()) <= {"-",":"} for c in cells if c.strip())
        if isSep and current:
            if len(current) >= 2:
                prev = current[:-1]
                if prev: tables.append(prev)
                current = [current[-1], s]
            else: current.append(s)
        else: current.append(s)
    if current: tables.append(current)
    return tables


def normalizeItemName(name: str) -> str:
    """항목명 정규화 — 공백/괄호 통일."""
    n = re.sub(r"\s+", "", name)  # 공백 전부 제거
    n = n.replace("（", "(").replace("）", ")")
    n = n.replace("ㆍ", "·")
    return n


_STOCK_TYPES = {"보통주", "우선주", "기타주식"}


def parseMultiYearTable(sub: list[str], periodYear: int) -> dict:
    """multi_year 서브테이블 파싱 → {항목: {연도: 값}}.

    보통주/우선주 연속행 처리 포함.
    """
    # 구분선 찾기
    sepIdx = -1
    for i, line in enumerate(sub):
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(set(c.strip()) <= {"-",":"} for c in cells if c.strip()):
            sepIdx = i
            break

    if sepIdx < 0 or sepIdx + 1 >= len(sub):
        return {}

    # 기수 행 (구분선 바로 다음)
    kisuLine = sub[sepIdx + 1]
    kisuCells = [c.strip() for c in kisuLine.strip("|").split("|")]
    kisuNums = []
    for cell in kisuCells:
        m = re.search(r"제\s*(\d+)\s*기", cell)
        if m:
            kisuNums.append(int(m.group(1)))

    if not kisuNums:
        return {}

    maxKisu = max(kisuNums)
    kisuToYear = {kn: periodYear - maxKisu + kn for kn in kisuNums}
    sortedKisu = sorted(kisuToYear.keys(), reverse=True)

    # 단위 추출
    unit = None
    full = "\n".join(sub)
    m = re.search(r"\(\s*단위\s*:\s*([^)]+)\)", full)
    if m:
        unit = m.group(1).strip()

    # 데이터 행 파싱
    result = {}
    prevItem = None

    for line in sub[sepIdx + 2:]:
        cells = [c.strip() for c in line.strip("|").split("|")]
        isSep = all(set(c.strip()) <= {"-",":"} for c in cells if c.strip())
        if isSep:
            continue

        if not cells or not cells[0].strip():
            continue

        firstCell = cells[0].strip()
        if firstCell.startswith("※"):
            continue

        # 보통주/우선주 연속행 감지
        if firstCell in _STOCK_TYPES and prevItem is not None:
            itemName = normalizeItemName(f"{prevItem}-{firstCell}")
            valCells = cells[1:]
        else:
            # 주식종류 컬럼이 두 번째에 있는지 확인
            if len(cells) > 1 and cells[1].strip() in _STOCK_TYPES:
                stockType = cells[1].strip()
                itemName = normalizeItemName(f"{firstCell}-{stockType}")
                valCells = cells[2:]
                prevItem = firstCell
            else:
                itemName = normalizeItemName(firstCell)
                valCells = cells[1:]
                prevItem = firstCell

        # 값 매핑
        for i, kn in enumerate(sortedKisu):
            if i < len(valCells):
                val = valCells[i].strip()
                if val and val != "-" and val not in _STOCK_TYPES:
                    year = str(kisuToYear[kn])
                    result.setdefault(itemName, {})[year] = val

    return result


def dividendMultiYear(stockCode: str) -> pl.DataFrame | None:
    """dividend topic의 multi_year 수평화."""
    sec = sections(stockCode)
    if sec is None:
        return None

    tables = sec.filter(pl.col("blockType") == "table")
    periods = [c for c in tables.columns if c not in {"chapter", "topic", "blockType"}]
    div = tables.filter(pl.col("topic") == "dividend")
    if div.is_empty():
        return None

    yearItemValues = defaultdict(dict)
    allItems = []
    seenItems = set()

    for p in periods:
        if "Q" in p:
            continue  # 연간만
        md = div[p][0]
        if md is None:
            continue

        pYear = int(p[:4])

        for sub in splitSubtables(str(md)):
            joined = " ".join(sub)
            if "당기" not in joined or "전기" not in joined:
                continue

            parsed = parseMultiYearTable(sub, pYear)
            for item, yearVals in parsed.items():
                if item not in seenItems:
                    allItems.append(item)
                    seenItems.add(item)
                for year, val in yearVals.items():
                    yearItemValues[item][year] = val

    if not allItems:
        return None

    allYears = sorted(set(y for iv in yearItemValues.values() for y in iv.keys()))

    rows = []
    for item in allItems:
        row = {"항목": item}
        for y in allYears:
            row[y] = yearItemValues[item].get(y)
        rows.append(row)

    return pl.DataFrame(rows)


if __name__ == "__main__":
    testCodes = [
        ("005930", "삼성전자"),
        ("000660", "SK하이닉스"),
        ("035420", "NAVER"),
        ("005380", "현대차"),
        ("068270", "셀트리온"),
    ]

    for code, name in testCodes:
        print(f"\n{'='*60}")
        print(f"  {name} ({code}) — dividend multi_year 수평화")
        print(f"{'='*60}\n")

        df = dividendMultiYear(code)
        if df is None:
            print("  데이터 없음")
            continue

        print(f"  {df.height}행 x {df.width}열")
        # 연도 컬럼만
        yearCols = [c for c in df.columns if c != "항목"]
        print(f"  연도: {yearCols}")
        print()

        # 최근 5년만 미리보기
        previewCols = ["항목"] + yearCols[-5:]
        print(df.select(previewCols).head(15))
