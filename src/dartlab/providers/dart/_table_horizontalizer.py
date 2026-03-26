"""sections 내 markdown 테이블 수평화.

company.py에서 분리된 _horizontalizeTableBlock / _stripUnitHeader.
docs table 블록의 기간별 markdown을 항목×기간 DataFrame으로 변환한다.
"""

from __future__ import annotations

import re

import polars as pl


def stripUnitHeader(sub: list[str]) -> list[str] | None:
    """단위행/기준일행이 헤더인 서브테이블 → 단위행 제거 + 나머지 반환.

    패턴: | (단위:천원) | | | → sep → 실제헤더 → 데이터
    다중컬럼: | (기준일 : | 2018년 03월 31일 | ) | (단위 : 주) |
    반환: 실제헤더 행부터의 서브테이블 (기존 파서가 그대로 동작).
    해당하지 않으면 None.
    """
    _UNIT_ONLY_RE = re.compile(
        r"^[\(\[\（<〈]?\s*"
        r"(?:<[^>]+>\s*)?"
        r"[\(\[\（]?\s*"
        r"(?:단위|원화\s*단위|외화\s*단위|금액\s*단위)"
        r".*$",
        re.IGNORECASE,
    )
    _DATE_ONLY_RE = re.compile(r"^\(?\s*기준일\s*:")

    firstRow = None
    for line in sub:
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(set(c.strip()) <= {"-", ":"} for c in cells if c.strip()):
            continue
        firstRow = [c for c in cells if c.strip()]
        break

    if firstRow is None:
        return None

    if len(firstRow) == 1:
        h = firstRow[0].strip()
        if not (_UNIT_ONLY_RE.match(h) or _DATE_ONLY_RE.match(h)):
            return None
    else:
        joined = " ".join(c.strip() for c in firstRow)
        hasUnit = bool(re.search(r"단위\s*[:/]", joined))
        hasDate = bool(re.search(r"기준일\s*[:/]", joined))
        if not (hasUnit or hasDate):
            return None

    sepIdx = -1
    for i, line in enumerate(sub):
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(set(c.strip()) <= {"-", ":"} for c in cells if c.strip()):
            sepIdx = i
            break

    if sepIdx < 0 or sepIdx + 1 >= len(sub):
        return None

    remainder = sub[sepIdx + 1 :]
    if not remainder:
        return None

    hasSep = any(
        all(set(c.strip()) <= {"-", ":"} for c in line.strip("|").split("|") if c.strip()) for line in remainder
    )
    if hasSep:
        return remainder

    if len(remainder) >= 2:
        headerLine = remainder[0]
        colCount = len(headerLine.strip("|").split("|"))
        sepLine = "| " + " | ".join(["---"] * colCount) + " |"
        return [headerLine, sepLine] + remainder[1:]

    return None


def horizontalizeTableBlock(
    topicFrame: pl.DataFrame,
    blockOrder: int,
    periodCols: list[str],
    period: str | None = None,
) -> pl.DataFrame | None:
    """table 블록을 기간 간 수평화 — 항목×기간 매트릭스.

    Args:
        topicFrame: sections에서 해당 topic의 행.
        blockOrder: 블록 인덱스.
        periodCols: 기간 컬럼 목록.
        period: 특정 기간 필터 (없으면 전체).

    Returns:
        항목(행) × 기간(열) DataFrame 또는 None.
    """
    from dartlab.providers.dart.docs.sections.tableParser import (
        _classifyStructure,
        _dataRows,
        _headerCells,
        _isJunk,
        splitSubtables,
    )

    boRow = topicFrame.filter((pl.col("blockOrder") == blockOrder) & (pl.col("blockType") == "table"))
    if boRow.is_empty():
        return None

    from dartlab.providers.dart.docs.sections.tableParser import (
        _parseKeyValueOrMatrix,
        _parseMultiYear,
    )

    _SUFFIX_RE = re.compile(r"(사업)?부문$")
    _KISU_RE = re.compile(r"제\d+기\s*(?:\d*분기|반기|말)?\s*" r"\(?(당기|전기|전전기|당반기|전반기|당분기|전분기)\)?")
    _NOTE_REF_RE = re.compile(r"\(\*\d*(?:,\d+)*\)")

    def _normalizeItem(name: str) -> str:
        name = _SUFFIX_RE.sub("", name).strip()
        name = _NOTE_REF_RE.sub("", name).strip()
        m = _KISU_RE.search(name)
        if m:
            return m.group(1)
        return name

    allItems: list[str] = []
    seenItems: set[str] = set()
    periodItemVal: dict[str, dict[str, str]] = {}

    def _collectMultiYear(sub: list[str], pYear: int, p: str) -> None:
        triples, _ = _parseMultiYear(sub, pYear)
        for rawItem, year, val in triples:
            item = _normalizeItem(rawItem)
            if year == str(pYear):
                if item not in seenItems:
                    allItems.append(item)
                    seenItems.add(item)
                if item not in periodItemVal:
                    periodItemVal[item] = {}
                periodItemVal[item][p] = val

    def _collectKvMatrix(sub: list[str], p: str) -> None:
        rows, headerNames, _ = _parseKeyValueOrMatrix(sub)
        for rawItem, vals in rows:
            item = _normalizeItem(rawItem)
            nonEmptyVals = [v for v in vals if v.strip()]
            if len(headerNames) >= 2 and len(nonEmptyVals) >= 2 and len(nonEmptyVals) <= len(headerNames):
                for hi, hname in enumerate(headerNames):
                    v = vals[hi].strip() if hi < len(vals) else ""
                    if not v or v == "-":
                        continue
                    compoundItem = f"{item}_{hname}"
                    if compoundItem not in seenItems:
                        allItems.append(compoundItem)
                        seenItems.add(compoundItem)
                    if compoundItem not in periodItemVal:
                        periodItemVal[compoundItem] = {}
                    periodItemVal[compoundItem][p] = v
            else:
                val = " | ".join(v for v in vals if v.strip()).strip()
                if val:
                    if item not in seenItems:
                        allItems.append(item)
                        seenItems.add(item)
                    if item not in periodItemVal:
                        periodItemVal[item] = {}
                    periodItemVal[item][p] = val

    from dartlab.providers.dart.docs.sections.tableParser import _normalizeHeader

    _PERIOD_KW_RE = re.compile(r"\d*분기|반기|당기|전기|전전기|당반기|전반기|당분기|전분기|당기말|전기말")

    def _groupHeader(hc: list[str]) -> str:
        h = _normalizeHeader(hc)
        h = _PERIOD_KW_RE.sub("", h)
        h = re.sub(r"\| *\|", "|", h)
        h = re.sub(r"\s+", " ", h).strip()
        return h

    # ── 1단계: 기간별 서브테이블의 헤더 시그니처 수집 ──
    _headerGroups: dict[str, list[str]] = {}
    for p in periodCols:
        md = boRow[p][0] if p in boRow.columns else None
        if md is None:
            continue
        for sub in splitSubtables(str(md)):
            hc = _headerCells(sub)
            if _isJunk(hc):
                continue
            dr = _dataRows(sub)
            if not dr:
                fixed = stripUnitHeader(sub)
                if fixed is not None:
                    fixedHc = _headerCells(fixed)
                    fixedDr = _dataRows(fixed)
                    if fixedHc and not _isJunk(fixedHc) and fixedDr:
                        sub = fixed
                        hc = fixedHc
                        dr = fixedDr
                    else:
                        continue
                else:
                    continue
            structType = _classifyStructure(hc)
            if structType == "skip":
                fixed = stripUnitHeader(sub)
                if fixed is not None:
                    fixedHc = _headerCells(fixed)
                    fixedDr = _dataRows(fixed)
                    if fixedHc and not _isJunk(fixedHc) and fixedDr:
                        hc = fixedHc
            gh = _groupHeader(hc)
            if gh not in _headerGroups:
                _headerGroups[gh] = []
            if p not in _headerGroups[gh]:
                _headerGroups[gh].append(p)

    if _headerGroups:
        bestHeader = max(_headerGroups, key=lambda k: len(_headerGroups[k]))
        bestPeriods = set(_headerGroups[bestHeader])
    else:
        bestPeriods = set(periodCols)

    # ── 2단계: 선택된 그룹의 기간에서만 수평화 ──
    for p in periodCols:
        if p not in bestPeriods:
            continue
        md = boRow[p][0] if p in boRow.columns else None
        if md is None:
            continue
        m = re.match(r"\d{4}", p)
        if m is None:
            continue
        pYear = int(m.group())

        for sub in splitSubtables(str(md)):
            hc = _headerCells(sub)
            if _isJunk(hc):
                continue
            dr = _dataRows(sub)
            if not dr:
                fixed = stripUnitHeader(sub)
                if fixed is not None:
                    fixedHc = _headerCells(fixed)
                    fixedDr = _dataRows(fixed)
                    if fixedHc and not _isJunk(fixedHc) and fixedDr:
                        sub = fixed
                        hc = fixedHc
                        dr = fixedDr
                    else:
                        continue
                else:
                    continue

            structType = _classifyStructure(hc)

            if structType == "skip":
                fixed = stripUnitHeader(sub)
                if fixed is not None:
                    fixedHc = _headerCells(fixed)
                    fixedDr = _dataRows(fixed)
                    if fixedHc and not _isJunk(fixedHc) and fixedDr:
                        structType = _classifyStructure(fixedHc)
                        hc = fixedHc
                        sub = fixed

            gh = _groupHeader(hc)
            if gh != bestHeader:
                continue

            if structType == "multi_year":
                beforeLen = len(allItems)
                _collectMultiYear(sub, pYear, p)
                if len(allItems) == beforeLen and len(hc) >= 2:
                    _collectKvMatrix(sub, p)

            elif structType in ("key_value", "matrix"):
                _collectKvMatrix(sub, p)

    if not allItems:
        return None

    # 품질 필터: 숫자만 항목명 제거
    def _isJunkItem(name: str) -> bool:
        stripped = re.sub(r"[,.\-\s]", "", name)
        return stripped.isdigit() or not stripped

    allItems = [item for item in allItems if not _isJunkItem(item)]
    if not allItems:
        return None

    # 이력형 감지
    periodItemSets: dict[str, set[str]] = {}
    for item in allItems:
        for p in periodItemVal.get(item, {}):
            if p not in periodItemSets:
                periodItemSets[p] = set()
            periodItemSets[p].add(item)
    if len(periodItemSets) >= 2:
        sets = list(periodItemSets.values())
        totalOverlap = 0
        totalPairs = 0
        for i in range(len(sets)):
            for j in range(i + 1, min(i + 4, len(sets))):
                union = len(sets[i] | sets[j])
                inter = len(sets[i] & sets[j])
                if union > 0:
                    totalOverlap += inter / union
                    totalPairs += 1
        avgOverlap = totalOverlap / totalPairs if totalPairs else 0
        if avgOverlap < 0.3 and len(allItems) > 5:
            return None

    # 목록형 감지
    if len(allItems) > 50:
        return None

    # DataFrame 구성
    usedPeriods = [p for p in periodCols if any(p in periodItemVal.get(item, {}) for item in allItems)]
    if not usedPeriods:
        return None

    # sparse 감지
    if len(usedPeriods) >= 3 and len(allItems) > 15:
        totalCells = len(allItems) * len(usedPeriods)
        filledCells = sum(1 for item in allItems for p in usedPeriods if periodItemVal.get(item, {}).get(p))
        fillRate = filledCells / totalCells if totalCells > 0 else 0
        if fillRate < 0.5:
            return None

    schema: dict[str, type] = {"항목": pl.Utf8}
    for p in usedPeriods:
        schema[p] = pl.Utf8

    rows = []
    for item in allItems:
        if not any(periodItemVal.get(item, {}).get(p) for p in usedPeriods):
            continue
        row: dict[str, str | None] = {"항목": item}
        for p in usedPeriods:
            row[p] = periodItemVal.get(item, {}).get(p)
        rows.append(row)

    if not rows:
        return None

    return pl.DataFrame(rows, schema=schema)
