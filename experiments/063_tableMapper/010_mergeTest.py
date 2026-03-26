"""실험 ID: 063-010
실험명: 구조 타입별 수평화 실제 검증

목적:
- 각 구조 타입의 수평화가 실제로 동작하는지 실데이터로 검증
- multi_year 체인 브릿지 검증 (겹치는 기간 값 일치 + 항목명 보간)
- key_value, matrix, yearly 수평화 검증
- 다종목에서 깨지는 케이스 확인

방법:
1. 삼성전자에서 각 타입별 대표 서브테이블 수평화
2. 결과 DataFrame을 직접 출력해서 사람이 쓸 수 있는지 확인
3. 다종목(5개)에서 동일 검증

실험일: 2026-03-16
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import polars as pl

from dartlab.providers.dart.docs.sections.pipeline import sections


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


def getHeaderCells(lines):
    for line in lines:
        cells = [c.strip() for c in line.strip("|").split("|")]
        isSep = all(set(c.strip()) <= {"-",":"} for c in cells if c.strip())
        if not isSep:
            return [c for c in cells if c.strip()]
    return []


def getDataRows(lines):
    rows = []
    headerDone = False
    for line in lines:
        cells = [c.strip() for c in line.strip("|").split("|") if c is not None]
        isSep = all(set(c.strip()) <= {"-",":"} for c in cells if c.strip())
        if isSep: headerDone = True; continue
        if headerDone: rows.append(cells)
    return rows


def extractUnit(lines):
    full = "\n".join(lines)
    m = re.search(r"\(\s*단위\s*:\s*([^)]+)\)", full)
    return m.group(1).strip() if m else None


def normalizeHeader(header_cells):
    h = " | ".join(header_cells)
    h = re.sub(r"\d{4}(Q\d)?", "", h)
    h = re.sub(r"제\s*\d+\s*기", "", h)
    h = re.sub(r"\(\s*단위\s*:\s*[^)]+\)", "", h)
    h = re.sub(r"\s+", " ", h).strip()
    return h


_MULTI_YEAR_KW = {"당기", "전기", "전전기", "당반기", "전반기"}


def isMultiYear(header_cells):
    joined = " ".join(header_cells)
    return any(kw in joined for kw in _MULTI_YEAR_KW)


def mergeMultiYear(topicTablesBySub, periods):
    """multi_year 서브테이블의 체인 브릿지 수평화.

    topicTablesBySub: {normHeader: {period: (headerCells, dataRows, unit)}}
    """
    results = {}

    for normH, periodData in topicTablesBySub.items():
        # 각 기간에서 데이터 추출 — 실제 연도 해석
        # 첫 데이터행이 "제56기 | 제55기 | 제54기" 같은 패턴인지 확인
        yearItemValues = defaultdict(dict)  # {항목: {연도: 값}}
        allItems = []
        seenItems = set()
        unit = None

        for period in sorted(periodData.keys()):
            headerCells, dataRows, u = periodData[period]
            if u:
                unit = u

            if not dataRows:
                continue

            # 실제 연도 해석 시도 — 첫 데이터행에서 "제XX기" 또는 연도 추출
            firstRow = dataRows[0]
            yearLabels = []
            for cell in firstRow:
                m = re.search(r"제\s*(\d+)\s*기", cell)
                if m:
                    yearLabels.append(cell.strip())
                    continue
                m = re.search(r"(20\d{2})", cell)
                if m:
                    yearLabels.append(m.group(1))

            # 연도 해석 실패하면 period 자체를 키로
            useYearLabels = len(yearLabels) >= 2

            for dataRow in dataRows[1:] if useYearLabels else dataRows:
                if not dataRow:
                    continue
                item = dataRow[0].strip()
                if not item:
                    continue
                if item not in seenItems:
                    allItems.append(item)
                    seenItems.add(item)

                if useYearLabels:
                    for i, yearLabel in enumerate(yearLabels):
                        valIdx = i + 1  # 첫 셀은 항목명
                        if valIdx < len(dataRow):
                            val = dataRow[valIdx].strip()
                            if val and val != "-":
                                yearItemValues[item][yearLabel] = val
                else:
                    # 연도 해석 못하면 헤더 컬럼명 사용
                    for i, hcell in enumerate(headerCells[1:], 1):
                        if i < len(dataRow):
                            val = dataRow[i].strip()
                            if val and val != "-":
                                yearItemValues[item][f"{period}:{hcell}"] = val

        results[normH] = {
            "items": allItems,
            "yearValues": dict(yearItemValues),
            "unit": unit,
        }

    return results


if __name__ == "__main__":
    sec = sections("005930")
    tables = sec.filter(pl.col("blockType") == "table")
    periods = [c for c in tables.columns if c not in {"chapter", "topic", "blockType"}]

    # dividend topic의 multi_year 서브테이블 수평화 테스트
    print("=== dividend multi_year 수평화 ===\n")

    divRow = tables.filter(pl.col("topic") == "dividend")
    if not divRow.is_empty():
        # 기간별 서브테이블 수집
        topicSubs = defaultdict(dict)

        for p in periods:
            md = divRow[p][0]
            if md is None:
                continue
            for sub in splitSubtables(str(md)):
                hc = getHeaderCells(sub)
                if not hc:
                    continue
                if isMultiYear(hc):
                    normH = normalizeHeader(hc)
                    dr = getDataRows(sub)
                    unit = extractUnit(sub)
                    topicSubs[normH][p] = (hc, dr, unit)

        merged = mergeMultiYear(topicSubs, periods)

        for normH, data in merged.items():
            print(f"헤더: {normH[:60]}")
            print(f"단위: {data['unit']}")
            print(f"항목: {len(data['items'])}개")
            yearValues = data["yearValues"]

            # 모든 연도 수집
            allYears = set()
            for item, yv in yearValues.items():
                allYears.update(yv.keys())
            allYears = sorted(allYears)

            print(f"연도: {allYears}")
            print()

            # DataFrame으로 출력
            rows = []
            for item in data["items"][:15]:
                row = {"항목": item}
                for y in allYears[-5:]:  # 최근 5개만
                    row[y] = yearValues.get(item, {}).get(y)
                rows.append(row)

            if rows:
                df = pl.DataFrame(rows)
                print(df)
            print()

    # key_value 수평화 테스트
    print("\n=== companyOverview key_value 수평화 ===\n")

    coRow = tables.filter(pl.col("topic") == "companyOverview")
    if not coRow.is_empty():
        kvSubs = defaultdict(dict)

        for p in periods[-5:]:  # 최근 5기간
            md = coRow[p][0]
            if md is None:
                continue
            for sub in splitSubtables(str(md)):
                hc = getHeaderCells(sub)
                if len(hc) == 2 and not isMultiYear(hc):
                    normH = normalizeHeader(hc)
                    dr = getDataRows(sub)
                    if dr:
                        kvSubs[normH][p] = dr

        for normH, periodData in kvSubs.items():
            print(f"헤더: {normH}")
            allItems = []
            seen = set()
            periodItemValues = {}
            for p, rows in periodData.items():
                pMap = {}
                for row in rows:
                    if len(row) >= 2:
                        item = row[0].strip()
                        value = row[1].strip()
                        if item and item not in seen:
                            allItems.append(item)
                            seen.add(item)
                        pMap[item] = value
                periodItemValues[p] = pMap

            dfRows = []
            for item in allItems[:8]:
                r = {"항목": item}
                for p in sorted(periodItemValues.keys()):
                    r[p] = periodItemValues[p].get(item)
                dfRows.append(r)

            if dfRows:
                print(pl.DataFrame(dfRows))
            print()

    # matrix 수평화 테스트 — businessOverview의 부문|제품
    print("\n=== businessOverview matrix 수평화 ===\n")

    boRow = tables.filter(pl.col("topic") == "businessOverview")
    if not boRow.is_empty():
        matrixSubs = defaultdict(dict)

        for p in periods[-5:]:
            md = boRow[p][0]
            if md is None:
                continue
            for sub in splitSubtables(str(md)):
                hc = getHeaderCells(sub)
                if len(hc) >= 2 and not isMultiYear(hc):
                    normH = normalizeHeader(hc)
                    dr = getDataRows(sub)
                    if dr:
                        matrixSubs[normH][p] = dr

        for normH, periodData in list(matrixSubs.items())[:3]:
            print(f"헤더: {normH[:60]}")
            allItems = []
            seen = set()
            periodItemValues = {}

            for p, rows in periodData.items():
                pMap = {}
                for row in rows:
                    if row:
                        item = row[0].strip()
                        value = " | ".join(row[1:]).strip() if len(row) > 1 else ""
                        if item and item not in seen:
                            allItems.append(item)
                            seen.add(item)
                        pMap[item] = value
                periodItemValues[p] = pMap

            dfRows = []
            for item in allItems[:8]:
                r = {"항목": item}
                for p in sorted(periodItemValues.keys()):
                    r[p] = periodItemValues[p].get(item, "")[:40]
                dfRows.append(r)

            if dfRows:
                print(pl.DataFrame(dfRows))
            print()
