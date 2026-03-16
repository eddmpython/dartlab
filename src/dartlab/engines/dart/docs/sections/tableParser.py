"""테이블 파서 — sections의 markdown 테이블을 구조화된 DataFrame으로 변환.

sections의 blockType="table" 셀에서:
1. 서브테이블 분리 (구분선 기준)
2. 헤더 기반 타입 분류 (tableMappings.json)
3. 같은 타입의 서브테이블끼리 기간별 수평화 (항목 × period)
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import polars as pl

_MAPPER_PATH = Path(__file__).parent / "mapperData" / "tableMappings.json"
_mappings: dict | None = None


def _loadMappings() -> dict:
    global _mappings
    if _mappings is None:
        with open(_MAPPER_PATH, encoding="utf-8") as f:
            _mappings = json.load(f)
    return _mappings


def _normalizeHeader(header: str) -> str:
    h = re.sub(r"\d{4}(Q\d)?", "", header)
    h = re.sub(r"제\s*\d+\s*기", "", h)
    h = re.sub(r"\(\s*단위\s*:\s*[^)]+\)", "", h)
    h = re.sub(r"\(\s*기준일\s*:?[^)]*\)", "", h)
    h = re.sub(r"\d+\.\d+\.\d+", "", h)
    h = re.sub(r"\s+", " ", h).strip()
    return h


def _isJunk(header: str) -> bool:
    h = header.strip()
    if not h:
        return True
    if set(h) <= {"|", " "}:
        return True
    m = _loadMappings()
    for prefix in m.get("junk_prefixes", []):
        if h.startswith(prefix):
            return True
    for phrase in m.get("junk_contains", []):
        if phrase in h:
            return True
    minLen = m.get("junk_min_length", 5)
    if len(h) < minLen:
        return True
    return False


def classifyHeader(header: str) -> str | None:
    """정규화 헤더 → 테이블 타입명."""
    m = _loadMappings()
    h = header.lower().replace(" ", "")
    for rule in m.get("rules", []):
        keywords = rule["keywords"]
        if all(kw.replace(" ", "").lower() in h for kw in keywords):
            return rule["type"]
    return None


def splitSubtables(md: str) -> list[list[str]]:
    """markdown 셀에서 구분선 기준으로 서브테이블 분리."""
    tables: list[list[str]] = []
    current: list[str] = []

    for line in md.strip().split("\n"):
        stripped = line.strip()
        if not stripped.startswith("|"):
            if current:
                tables.append(current)
                current = []
            continue

        cells = [c.strip() for c in stripped.strip("|").split("|")]
        isSep = all(set(c.strip()) <= {"-", ":"} for c in cells if c.strip())

        if isSep and current:
            if len(current) >= 2:
                prev = current[:-1]
                if prev:
                    tables.append(prev)
                current = [current[-1], stripped]
            else:
                current.append(stripped)
        else:
            current.append(stripped)

    if current:
        tables.append(current)

    return tables


def subtableHeader(lines: list[str]) -> str:
    """서브테이블의 헤더(첫 비구분선 줄)."""
    for line in lines:
        cells = [c.strip() for c in line.strip("|").split("|")]
        isSep = all(set(c.strip()) <= {"-", ":"} for c in cells if c.strip())
        if not isSep:
            return " | ".join(c.strip() for c in cells if c.strip())
    return ""


def parseSubtableRows(lines: list[str]) -> list[tuple[str, str]]:
    """서브테이블 → (항목, 값) 리스트. 헤더/구분선 이후 데이터만."""
    rows: list[tuple[str, str]] = []
    headerDone = False
    for line in lines:
        cells = [c.strip() for c in line.strip("|").split("|")]
        isSep = all(set(c.strip()) <= {"-", ":"} for c in cells if c.strip())
        if isSep:
            headerDone = True
            continue
        if not headerDone:
            continue
        label = cells[0].strip() if cells else ""
        value = " | ".join(cells[1:]).strip() if len(cells) > 1 else ""
        if label:
            rows.append((label, value))
    return rows


def parseTableCell(md: str) -> list[dict]:
    """하나의 markdown 셀 → 타입별 서브테이블 리스트.

    Returns:
        [{"type": "productDivision", "header": "...", "rows": [(항목,값),...]}]
    """
    results: list[dict] = []
    for sub in splitSubtables(md):
        header = subtableHeader(sub)
        normH = _normalizeHeader(header)
        if _isJunk(normH):
            continue
        tableType = classifyHeader(normH)
        if tableType is None:
            tableType = "_unclassified"
        dataRows = parseSubtableRows(sub)
        if dataRows:
            results.append({
                "type": tableType,
                "header": header,
                "rows": dataRows,
            })
    return results


def buildTableDataFrame(
    topicFrame: pl.DataFrame,
    periodCols: list[str],
) -> pl.DataFrame | None:
    """sections의 table 행 → 수평화된 DataFrame (항목 × period).

    같은 타입의 서브테이블끼리 항목을 기간별로 나란히 놓는다.

    Parameters
    ----------
    topicFrame : pl.DataFrame
        sections에서 특정 topic의 blockType="table" 행.
    periodCols : list[str]
        기간 컬럼 목록.

    Returns
    -------
    pl.DataFrame | None
        blockType | tableType | 항목 | period1 | period2 | ...
    """
    if topicFrame.is_empty():
        return None

    # 기간별 서브테이블 파싱
    # tableType → {period → {항목 → 값}}
    typeData: dict[str, dict[str, dict[str, str]]] = {}
    # tableType → 항목 순서 유지
    typeItemOrder: dict[str, list[str]] = {}
    typeItemSeen: dict[str, set[str]] = {}

    for p in periodCols:
        if p not in topicFrame.columns:
            continue
        md = topicFrame[p][0]
        if md is None:
            continue

        parsed = parseTableCell(str(md))
        for entry in parsed:
            tt = entry["type"]
            if tt not in typeData:
                typeData[tt] = {}
                typeItemOrder[tt] = []
                typeItemSeen[tt] = set()
            if p not in typeData[tt]:
                typeData[tt][p] = {}

            for label, value in entry["rows"]:
                typeData[tt][p][label] = value
                if label not in typeItemSeen[tt]:
                    typeItemOrder[tt].append(label)
                    typeItemSeen[tt].add(label)

    if not typeData:
        return None

    # DataFrame 생성
    outRows: list[dict[str, str | None]] = []
    for tt in typeData:
        items = typeItemOrder[tt]
        for item in items:
            row: dict[str, str | None] = {
                "blockType": "table",
                "tableType": tt,
                "항목": item,
            }
            for p in periodCols:
                row[p] = typeData[tt].get(p, {}).get(item)
            outRows.append(row)

    if not outRows:
        return None

    return pl.DataFrame(outRows)
