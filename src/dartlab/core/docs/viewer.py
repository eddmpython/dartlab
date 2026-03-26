"""sections DataFrame → 뷰어용 dict 변환.

sections 수평화 DataFrame을 GUI가 바로 렌더링할 수 있는 dict/list 구조로 변환한다.
신구대조표 패턴 — 기간간 추가/삭제/변경을 블록 단위로 표현.

사용법::

    from dartlab.core.docs.viewer import viewer
    doc = viewer(sections, "businessOverview", "2025", "2024")
"""

from __future__ import annotations

import re
from typing import Any

import polars as pl

_PERIOD_RE = re.compile(r"^\d{4}(Q[1-4])?$")


def _isPeriodCol(name: str) -> bool:
    return bool(_PERIOD_RE.fullmatch(name))


def _periodCols(df: pl.DataFrame) -> list[str]:
    return sorted([c for c in df.columns if _isPeriodCol(c)], reverse=True)


def _autoComparePeriod(availablePeriods: list[str], basePeriod: str) -> str | None:
    """같은 cadence 직전 기간 자동 선택."""
    if not availablePeriods or not basePeriod:
        return None

    m = _PERIOD_RE.fullmatch(basePeriod)
    if not m:
        return None

    quarter = m.group(1)
    if quarter:
        year = int(basePeriod[:4])
        candidate = f"{year - 1}{quarter}"
    else:
        candidate = str(int(basePeriod) - 1)

    if candidate in availablePeriods:
        return candidate

    return None


def _charDiffOps(fromText: str, toText: str) -> list[dict[str, str]]:
    """diff-match-patch 기반 글자 단위 diff → list[{type, text}]."""
    import diff_match_patch as dmpModule

    dmp = dmpModule.diff_match_patch()
    dmp.Diff_Timeout = 0.05
    diffs = dmp.diff_main(fromText, toText)
    dmp.diff_cleanupSemantic(diffs)

    opMap = {0: "equal", 1: "insert", -1: "delete"}
    return [{"type": opMap[op], "text": text} for op, text in diffs if text]


def _parseTable(md: str) -> dict[str, Any] | None:
    """마크다운 테이블 → {headers, rows}. 파싱 실패 시 None."""
    lines = md.strip().split("\n")
    if len(lines) < 3:
        return None

    headerLine = None
    sepFound = False
    dataLines: list[list[str]] = []

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]

        if all(set(c.strip()) <= {"-", ":", " "} for c in cells if c.strip()):
            sepFound = True
            for j in range(i - 1, -1, -1):
                prev = lines[j].strip()
                if prev.startswith("|"):
                    prevCells = [c.strip() for c in prev.strip("|").split("|")]
                    if not all(set(c.strip()) <= {"-", ":", " "} for c in prevCells if c.strip()):
                        headerLine = prevCells
                        break
            continue

        if sepFound and headerLine is not None:
            dataLines.append(cells)

    if headerLine is None or not dataLines:
        return None

    headers = [h for h in headerLine if h]
    rows = []
    for cells in dataLines:
        while len(cells) < len(headers):
            cells.append("")
        rows.append(cells[: len(headers)])

    return {"headers": headers, "rows": rows}


def _tableCellDiffs(
    baseTable: dict[str, Any] | None,
    compareTable: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """두 테이블의 셀 단위 diff. 변경된 셀만 반환."""
    if baseTable is None or compareTable is None:
        return []

    diffs: list[dict[str, Any]] = []
    baseRows = baseTable.get("rows", [])
    compareRows = compareTable.get("rows", [])
    maxRows = max(len(baseRows), len(compareRows))

    for r in range(maxRows):
        bRow = baseRows[r] if r < len(baseRows) else []
        cRow = compareRows[r] if r < len(compareRows) else []
        maxCols = max(len(bRow), len(cRow))
        for c in range(maxCols):
            bVal = bRow[c] if c < len(bRow) else ""
            cVal = cRow[c] if c < len(cRow) else ""
            if bVal != cVal:
                diffs.append({"row": r, "col": c, "from": cVal, "to": bVal})

    return diffs


def _assignTreeMeta(blocks: list[dict[str, Any]]) -> None:
    """heading level 스택 기반으로 depth, parentId를 in-place 할당."""
    stack: list[dict[str, Any]] = []

    for block in blocks:
        if block["kind"] == "heading" and block.get("level") is not None:
            level = block["level"]
            while stack and stack[-1].get("level", 0) >= level:
                stack.pop()
            block["depth"] = len(stack)
            block["parentId"] = stack[-1]["id"] if stack else None
            stack.append(block)
        else:
            block["depth"] = len(stack)
            block["parentId"] = stack[-1]["id"] if stack else None


def _assignFoldGroups(blocks: list[dict[str, Any]]) -> int:
    """연속 unchanged 블록 3개 이상에 foldable/foldGroupId 할당. 그룹 수 반환."""
    groupId = 0
    i = 0
    while i < len(blocks):
        if blocks[i].get("status") == "unchanged" and blocks[i]["kind"] != "heading":
            runStart = i
            while i < len(blocks) and blocks[i].get("status") == "unchanged" and blocks[i]["kind"] != "heading":
                i += 1
            runLen = i - runStart
            if runLen >= 3:
                groupId += 1
                for j in range(runStart, i):
                    blocks[j]["foldable"] = True
                    blocks[j]["foldGroupId"] = groupId
        else:
            i += 1
    return groupId


def viewer(
    sections: pl.DataFrame,
    topic: str,
    basePeriod: str,
    comparePeriod: str | None = None,
) -> dict[str, Any]:
    """sections DataFrame → 뷰어용 비교 문서 dict.

    Args:
        sections: topic × period 수평화 DataFrame.
        topic: 표시할 topic (예: "businessOverview").
        basePeriod: 기준 기간 — 최신 (예: "2025").
        comparePeriod: 비교 기간 (예: "2024"). None이면 자동 선택, ""이면 단독 뷰.

    Returns:
        JSON 직렬화 가능한 dict.
    """
    if "topic" not in sections.columns:
        return _emptyDoc(topic, basePeriod, comparePeriod)

    filtered = sections.filter(pl.col("topic") == topic)
    if filtered.height == 0:
        return _emptyDoc(topic, basePeriod, comparePeriod)

    periods = _periodCols(filtered)
    availablePeriods = [p for p in periods if filtered.select(pl.col(p).is_not_null().any()).item()]

    # comparePeriod 자동 선택: None → 같은 cadence 직전 기간, "" → 단독 뷰
    if comparePeriod is None:
        comparePeriod = _autoComparePeriod(availablePeriods, basePeriod)
    elif comparePeriod == "":
        comparePeriod = None

    hasBlockType = "blockType" in filtered.columns
    hasTextNodeType = "textNodeType" in filtered.columns
    hasTextLevel = "textLevel" in filtered.columns
    hasTextPath = "textPath" in filtered.columns
    hasBlockOrder = "blockOrder" in filtered.columns

    if hasBlockOrder:
        filtered = filtered.sort("blockOrder")

    blocks: list[dict[str, Any]] = []
    counts = {"added": 0, "removed": 0, "modified": 0, "unchanged": 0}
    lastHeadingPath: str | None = None

    for rowIdx in range(filtered.height):
        blockType = filtered.item(rowIdx, "blockType") if hasBlockType else "text"
        textNodeType = filtered.item(rowIdx, "textNodeType") if hasTextNodeType else None
        textLevel = filtered.item(rowIdx, "textLevel") if hasTextLevel else None
        textPath = filtered.item(rowIdx, "textPath") if hasTextPath else None
        blockOrder = filtered.item(rowIdx, "blockOrder") if hasBlockOrder else rowIdx

        # kind 판정: heading | text | table
        if blockType == "table":
            kind = "table"
        elif textNodeType == "heading" or blockType == "heading":
            kind = "heading"
        else:
            kind = "text"

        # path 상속: heading이면 갱신, 나머지는 fallback
        if kind == "heading" and textPath:
            lastHeadingPath = textPath
        elif textPath is None and lastHeadingPath:
            textPath = lastHeadingPath

        # base/compare 텍스트 추출
        baseText = None
        compareText = None
        if basePeriod in filtered.columns:
            val = filtered.item(rowIdx, basePeriod)
            baseText = str(val) if val is not None else None
        if comparePeriod and comparePeriod in filtered.columns:
            val = filtered.item(rowIdx, comparePeriod)
            compareText = str(val) if val is not None else None

        # status 판정
        if comparePeriod is None:
            status = None
        elif baseText is not None and compareText is None:
            status = "added"
        elif baseText is None and compareText is not None:
            status = "removed"
        elif baseText is None and compareText is None:
            continue
        elif baseText == compareText:
            status = "unchanged"
        else:
            status = "modified"

        if basePeriod and baseText is None and comparePeriod is None:
            continue

        block: dict[str, Any] = {
            "id": f"seg-{blockOrder:03d}",
            "order": blockOrder,
            "kind": kind,
            "level": int(textLevel) if textLevel is not None else None,
            "path": textPath,
            "status": status,
        }

        if kind == "table":
            baseTable = _parseTable(baseText) if baseText else None
            compareTable = _parseTable(compareText) if compareText else None
            block["base"] = baseTable or ({"raw": baseText} if baseText else None)
            block["compare"] = compareTable or ({"raw": compareText} if compareText else None)
            if status == "modified" and baseTable and compareTable:
                block["cellDiffs"] = _tableCellDiffs(baseTable, compareTable)
        else:
            block["base"] = baseText
            block["compare"] = compareText
            if status == "modified" and baseText and compareText:
                block["diff"] = _charDiffOps(compareText, baseText)

        if status:
            counts[status] = counts.get(status, 0) + 1

        blocks.append(block)

    # 트리 구조 메타데이터 (depth, parentId)
    _assignTreeMeta(blocks)

    # unchanged 블록 접기 힌트
    foldableGroups = _assignFoldGroups(blocks)

    return {
        "topic": topic,
        "basePeriod": basePeriod,
        "comparePeriod": comparePeriod,
        "availablePeriods": availablePeriods,
        "summary": {
            "totalBlocks": len(blocks),
            "addedBlocks": counts["added"],
            "removedBlocks": counts["removed"],
            "modifiedBlocks": counts["modified"],
            "unchangedBlocks": counts["unchanged"],
            "foldableGroups": foldableGroups,
        },
        "blocks": blocks,
    }


def _emptyDoc(topic: str, basePeriod: str, comparePeriod: str | None) -> dict[str, Any]:
    return {
        "topic": topic,
        "basePeriod": basePeriod,
        "comparePeriod": comparePeriod,
        "availablePeriods": [],
        "summary": {
            "totalBlocks": 0,
            "addedBlocks": 0,
            "removedBlocks": 0,
            "modifiedBlocks": 0,
            "unchangedBlocks": 0,
            "foldableGroups": 0,
        },
        "blocks": [],
    }
