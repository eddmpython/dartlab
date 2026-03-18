"""테이블 파서 — sections의 markdown 테이블을 구조화된 DataFrame으로 변환.

구조 타입별 병합 전략:
- multi_year: 당기/전기/전전기 → 기수→연도 변환 → 체인 브릿지 수평화
- key_value: 2컬럼 키-값 → 기간별 단순 수평화
- matrix: 3컬럼+ → 첫 컬럼=항목, 나머지=값, 기간별 수평화
"""

from __future__ import annotations

import re
from collections import defaultdict

import polars as pl


# ── 서브테이블 분리 ──


def splitSubtables(md: str) -> list[list[str]]:
    """구분선 기준 서브테이블 분리."""
    tables: list[list[str]] = []
    current: list[str] = []

    for line in md.strip().split("\n"):
        s = line.strip()
        if not s.startswith("|"):
            if current:
                tables.append(current)
                current = []
            continue

        cells = [c.strip() for c in s.strip("|").split("|")]
        isSep = all(set(c.strip()) <= {"-", ":"} for c in cells if c.strip())

        if isSep and current:
            if len(current) >= 2:
                prev = current[:-1]
                if prev:
                    tables.append(prev)
                current = [current[-1], s]
            else:
                current.append(s)
        else:
            current.append(s)

    if current:
        tables.append(current)
    return tables


# ── 유틸 ──


def _headerCells(lines: list[str]) -> list[str]:
    for line in lines:
        cells = [c.strip() for c in line.strip("|").split("|")]
        if not all(set(c.strip()) <= {"-", ":"} for c in cells if c.strip()):
            return [c for c in cells if c.strip()]
    return []


def _dataRows(lines: list[str]) -> list[list[str]]:
    rows = []
    sepDone = False
    for line in lines:
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(set(c.strip()) <= {"-", ":"} for c in cells if c.strip()):
            sepDone = True
            continue
        if sepDone:
            rows.append(cells)
    return rows


def _normalizeHeader(headerCells: list[str]) -> str:
    h = " | ".join(headerCells)
    h = re.sub(r"\d{4}(Q\d)?", "", h)
    h = re.sub(r"제\s*\d+\s*기", "", h)
    h = re.sub(r"\(\s*단위\s*:\s*[^)]+\)", "", h)
    h = re.sub(r"\s+", " ", h).strip()
    return h


def _normalizeItemName(name: str) -> str:
    n = re.sub(r"\s+", "", name)
    n = n.replace("（", "(").replace("）", ")")
    n = n.replace("ㆍ", "·")
    return n


def _isJunk(headerCells: list[str]) -> bool:
    if not headerCells:
        return True
    h = " ".join(headerCells).strip()
    if not h or set(h) <= {"|", " "}:
        return True
    if h.startswith("※") or h.startswith("☞") or h.startswith("[△"):
        return True
    if "본문 위치로 이동" in h:
        return True
    if len(h) < 5:
        return True
    return False


def _extractUnit(lines: list[str]) -> str | None:
    full = "\n".join(lines)
    m = re.search(r"\(\s*단위\s*:\s*([^)]+)\)", full)
    return m.group(1).strip() if m else None


# ── 구조 분류 ──

_MULTI_YEAR_KW = {"당기", "전기", "전전기", "당반기", "전반기"}
_STOCK_TYPES = {"보통주", "우선주", "기타주식"}


def _classifyStructure(headerCells: list[str]) -> str:
    joined = " ".join(headerCells)
    if any(kw in joined for kw in _MULTI_YEAR_KW):
        return "multi_year"
    if len(headerCells) == 2:
        return "key_value"
    if len(headerCells) >= 3:
        return "matrix"
    return "skip"


# ── multi_year 파싱 ──


def _parseMultiYear(sub: list[str], periodYear: int) -> tuple[list[tuple[str, str, str]], str | None]:
    """multi_year → [(항목, 연도, 값), ...] + 단위."""
    sepIdx = -1
    for i, line in enumerate(sub):
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(set(c.strip()) <= {"-", ":"} for c in cells if c.strip()):
            sepIdx = i
            break

    if sepIdx < 0 or sepIdx + 1 >= len(sub):
        return [], None

    # 기수 행
    kisuCells = [c.strip() for c in sub[sepIdx + 1].strip("|").split("|")]
    kisuNums = []
    for cell in kisuCells:
        m = re.search(r"제\s*(\d+)\s*기", cell)
        if m:
            kisuNums.append(int(m.group(1)))

    if not kisuNums:
        return [], None

    maxKisu = max(kisuNums)
    sortedKisu = sorted(kisuNums, reverse=True)
    kisuToYear = {kn: str(periodYear - maxKisu + kn) for kn in kisuNums}

    unit = _extractUnit(sub)
    triples: list[tuple[str, str, str]] = []
    prevItem = ""

    for line in sub[sepIdx + 2:]:
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(set(c.strip()) <= {"-", ":"} for c in cells if c.strip()):
            continue
        if not cells or not cells[0].strip():
            continue

        first = cells[0].strip()
        if first.startswith("※"):
            continue

        # 보통주/우선주 연속행
        if first in _STOCK_TYPES and prevItem:
            itemName = _normalizeItemName(f"{prevItem}-{first}")
            valCells = cells[1:]
        elif len(cells) > 1 and cells[1].strip() in _STOCK_TYPES:
            stockType = cells[1].strip()
            itemName = _normalizeItemName(f"{first}-{stockType}")
            valCells = cells[2:]
            prevItem = first
        else:
            itemName = _normalizeItemName(first)
            valCells = cells[1:]
            prevItem = first

        for i, kn in enumerate(sortedKisu):
            if i < len(valCells):
                val = valCells[i].strip()
                if val and val != "-" and val not in _STOCK_TYPES:
                    triples.append((itemName, kisuToYear[kn], val))

    return triples, unit


# ── key_value / matrix 파싱 ──


def _parseKeyValueOrMatrix(sub: list[str]) -> tuple[list[tuple[str, list[str]]], list[str], str | None]:
    """key_value/matrix → [(항목, [값1, 값2, ...]), ...] + 헤더컬럼명 + 단위.

    다중행 헤더, 그룹 헤더, 주석 행 처리 포함.
    """
    headerCells = _headerCells(sub)
    headerNames = [_normalizeItemName(h) for h in headerCells[1:]] if len(headerCells) > 1 else []
    rows = _dataRows(sub)
    unit = _extractUnit(sub)
    result: list[tuple[str, list[str]]] = []

    if not rows:
        return result, headerNames, unit

    # 다중행 헤더 감지: 첫 데이터행이 순수 텍스트(숫자 없음)이고 컬럼 수가 헤더와 비슷하면 서브헤더
    firstRow = rows[0]
    isSubHeader = (
        len(firstRow) >= len(headerCells)
        and all(not any(ch.isdigit() for ch in cell) or not cell.strip() for cell in firstRow)
        and len(rows) > 1
    )
    dataStart = 1 if isSubHeader else 0

    prevGroupItem = ""
    for row in rows[dataStart:]:
        if not row or not row[0].strip():
            continue
        first = row[0].strip()
        if first.startswith("※") or first.startswith("☞"):
            continue

        item = _normalizeItemName(first)
        values = [c.strip() for c in row[1:]]

        # 그룹 헤더 감지: 값이 전부 비어있거나 1개만 있고 다음 행들이 세부 항목
        allEmpty = all(not v or v == "-" for v in values)
        if allEmpty and len(values) >= 2:
            prevGroupItem = item
            continue

        # 그룹 헤더 하위 항목이면 접두사 추가
        if prevGroupItem and not allEmpty:
            item = f"{prevGroupItem}_{item}"

        if item:
            result.append((item, values))

    return result, headerNames, unit


# ── 통합 빌더 ──


def buildTableDataFrame(
    topicFrame: pl.DataFrame,
    periodCols: list[str],
) -> pl.DataFrame | None:
    """sections의 table 행 → 수평화된 DataFrame.

    구조 타입별로 다른 병합 전략 적용.
    """
    if topicFrame.is_empty():
        return None

    # key: (blockOrder, normHeader) → {period → [(항목,값)]} / [(항목,연도,값)]
    kvData: dict[tuple[int, str], dict[str, list[tuple[str, str]]]] = defaultdict(lambda: defaultdict(list))
    myData: dict[tuple[int, str], list[tuple[str, str, str]]] = defaultdict(list)
    units: dict[tuple[int, str], str] = {}

    for record in topicFrame.iter_rows(named=True):
        blockOrder = int(record.get("blockOrder") or 0)
        for p in periodCols:
            if p not in topicFrame.columns:
                continue
            md = record.get(p)
            if md is None:
                continue

            pYear = int(re.match(r"\d{4}", p).group()) if re.match(r"\d{4}", p) else None

            for sub in splitSubtables(str(md)):
                hc = _headerCells(sub)
                if _isJunk(hc):
                    continue

                # 0행 서브테이블 스킵 (단위, 주석, 기준일 등)
                dr = _dataRows(sub)
                if not dr:
                    continue

                normH = _normalizeHeader(hc)
                groupKey = (blockOrder, normH)
                structType = _classifyStructure(hc)

                if structType == "multi_year" and pYear and "Q" not in p:
                    triples, unit = _parseMultiYear(sub, pYear)
                    myData[groupKey].extend(triples)
                    if unit:
                        units[groupKey] = unit

                elif structType in ("key_value", "matrix"):
                    rows, headerNames, unit = _parseKeyValueOrMatrix(sub)
                    if unit:
                        units[groupKey] = unit

                    # key_value/matrix: 첫 컬럼=항목, 나머지=값 (파이프로 합침)
                    for item, vals in rows:
                        val = " | ".join(v for v in vals if v).strip()
                        if val:
                            kvData[groupKey][p].append((item, val))

    if not kvData and not myData:
        return None

    outRows: list[dict[str, str | None]] = []

    # multi_year → 항목 × 연도
    for (blockOrder, normH), triples in myData.items():
        allItems: list[str] = []
        seenItems: set[str] = set()
        yearItemVal: dict[str, dict[str, str]] = defaultdict(dict)

        for item, year, val in triples:
            if item not in seenItems:
                allItems.append(item)
                seenItems.add(item)
            yearItemVal[item][year] = val

        allYears = sorted(set(y for iv in yearItemVal.values() for y in iv.keys()))
        unit = units.get((blockOrder, normH), "")

        subtableName = normH[:50] if normH else ""

        for item in allItems:
            row: dict[str, str | None] = {
                "blockType": "table",
                "blockOrder": blockOrder,
                "tableType": "multi_year",
                "subtable": subtableName,
                "단위": unit,
                "항목": item,
                "_rowOrder": len(outRows),
            }
            for y in allYears:
                row[y] = yearItemVal[item].get(y)
            outRows.append(row)

    # key_value / matrix → 항목 × period
    for (blockOrder, normH), periodData in kvData.items():
        allItems: list[str] = []
        seenItems: set[str] = set()
        periodItemVal: dict[str, dict[str, str]] = defaultdict(dict)

        for p, pairs in periodData.items():
            for item, val in pairs:
                if item not in seenItems:
                    allItems.append(item)
                    seenItems.add(item)
                periodItemVal[item][p] = val

        unit = units.get((blockOrder, normH), "")

        # normHeader에서 사람 읽기용 subtable명 생성
        subtableName = normH[:50] if normH else ""

        for item in allItems:
            row: dict[str, str | None] = {
                "blockType": "table",
                "blockOrder": blockOrder,
                "tableType": "key_value",
                "subtable": subtableName,
                "단위": unit,
                "항목": item,
                "_rowOrder": len(outRows),
            }
            for p in periodCols:
                row[p] = periodItemVal[item].get(p)
            outRows.append(row)

    if not outRows:
        return None

    # 각 normHeader 그룹별로 DataFrame 생성 후 concat
    # (다른 서브테이블은 다른 컬럼 세트를 가질 수 있으므로)
    groups: dict[str, list[dict]] = defaultdict(list)
    for row in outRows:
        # tableType + 항목 세트로 그룹핑
        key = row.get("tableType", "unknown")
        groups[key].append(row)

    frames: list[pl.DataFrame] = []
    for key, rows in groups.items():
        try:
            frames.append(pl.DataFrame(rows))
        except Exception:
            # 같은 tableType 내에서도 스키마 다를 수 있음 → 개별 처리
            for row in rows:
                try:
                    frames.append(pl.DataFrame([row]))
                except Exception:
                    pass

    if not frames:
        return None
    if len(frames) == 1:
        return frames[0]
    return pl.concat(frames, how="diagonal_relaxed")
