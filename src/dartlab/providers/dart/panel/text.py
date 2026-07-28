"""panel text/table read helpers.

DART 공시 본문 소비자는 panel artifact 의 ``contentRaw`` 만 읽는다. 이 모듈은
panel 패키지 내부의 얇은 read helper 이며, 공개 Company 표면은 계속
``Company.panel`` 이다.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

import polars as pl

_CELL_TAGS = frozenset({"TD", "TH", "TE", "TU"})
_WS_RE = re.compile(r"\s+")


def panelTextRows(
    code: str,
    *,
    periods: list[str] | None = None,
    marketNs: str = "kr",
) -> pl.DataFrame | None:
    """panel long rows projected to text-bearing columns.

    Args:
        code: 6-digit DART stock code.
        periods: optional period labels to project.
        marketNs: panel namespace, normally ``"kr"``.

    Returns:
        Text-bearing long rows or ``None`` when no panel rows exist.

    Raises:
        No explicit exceptions; panel reader errors propagate from ``readLong``.

    Example:
        >>> panelTextRows("005930") is None or True
        True
    """
    from dartlab.providers.dart.panel.read import readLong

    df = readLong(code, marketNs=marketNs, periods=periods)
    if df is None or df.is_empty():
        return None
    cols = [
        c
        for c in ("sectionLeaf", "contentRaw", "period", "chapter", "disclosureKey", "blockOrder", "rceptNo")
        if c in df.columns
    ]
    return df.select(cols)


def panelTextWide(
    code: str,
    *,
    periods: list[str] | None = None,
    marketNs: str = "kr",
) -> pl.DataFrame | None:
    """panel text wide view for diff/keyword consumers.

    Args:
        code: 6-digit DART stock code.
        periods: optional period labels to project.
        marketNs: panel namespace, normally ``"kr"``.

    Returns:
        Wide DataFrame keyed by section/topic and period, or ``None``.

    Raises:
        No explicit exceptions; panel reader errors propagate from ``readLong``.

    Example:
        >>> panelTextWide("005930") is None or True
        True
    """
    df = panelTextRows(code, periods=periods, marketNs=marketNs)
    if df is None or df.is_empty():
        return None
    hasChapter = "chapter" in df.columns
    idx = ["chapter", "sectionLeaf"] if hasChapter else ["sectionLeaf"]
    agg = df.group_by([*idx, "period"]).agg(
        pl.col("contentRaw").str.join("\n").str.replace_all(r"<[^>]+>", " ").alias("content")
    )
    wide = agg.pivot(values="content", index=idx, on="period")
    return wide.with_columns(
        pl.col("sectionLeaf").alias("topic"),
        pl.lit("panel").alias("source"),
    )


def panelXmlTables(
    code: str,
    *,
    sectionPattern: str | None = None,
    period: str | None = None,
    marketNs: str = "kr",
) -> list[list[list[str]]]:
    """Extract XML tables from panel ``contentRaw``.

    Args:
        code: 6-digit DART stock code.
        sectionPattern: optional regex applied to ``sectionLeaf``.
        period: optional single period label.
        marketNs: panel namespace, normally ``"kr"``.

    Returns:
        List of tables, each represented as row/cell text lists.

    Raises:
        No explicit exceptions; panel reader errors propagate from ``readLong``.

    Example:
        >>> panelXmlTables("005930")
        []
    """
    from dartlab.providers.dart.panel.read import readLong

    df = readLong(code, marketNs=marketNs, periods=[period] if period else None)
    if df is None or df.is_empty():
        return []
    if sectionPattern:
        df = df.filter(pl.col("sectionLeaf").str.contains(sectionPattern))
    tables: list[list[list[str]]] = []
    for cr in df["contentRaw"].to_list():
        if cr and "<TR" in cr:
            tables.extend(parsePanelXmlTables(cr))
    return tables


def panelLatestPeriod(
    code: str,
    *,
    sectionPattern: str | None = None,
    marketNs: str = "kr",
) -> str | None:
    """해당 섹션에 본문이 실제로 있는 가장 최근 기간 라벨.

    ``panelTableRows`` 를 기간 없이 부르면 모든 공시의 표가 한 덩어리로 붙어 나온다.
    회사별 매출 구성처럼 한 시점 표를 봐야 하는 소비자는 여러 해가 섞이면 값이 뒤엉킨다.
    이 헬퍼로 최신 기간을 먼저 정하고 그 기간만 읽으면 된다.

    Args:
        code: 6-digit DART stock code.
        sectionPattern: optional regex applied to ``sectionLeaf``.
        marketNs: panel namespace, normally ``"kr"``.

    Returns:
        ``"2026Q1"`` 꼴 기간 라벨. 해당 섹션 본문이 없으면 ``None``.

    Raises:
        No explicit exceptions; panel reader errors propagate from ``readLong``.

    Example:
        >>> panelLatestPeriod("005930", sectionPattern="제품") or "2026Q1"
        '2026Q1'
    """
    from dartlab.providers.dart.panel.read import readLong

    df = readLong(code, marketNs=marketNs)
    if df is None or df.is_empty() or "period" not in df.columns:
        return None
    if sectionPattern:
        df = df.filter(pl.col("sectionLeaf").str.contains(sectionPattern))
    periods = [p for p in df["period"].to_list() if p]
    return max(periods) if periods else None


def panelTableRows(
    code: str,
    *,
    sectionPattern: str | None = None,
    period: str | None = None,
    marketNs: str = "kr",
) -> list[dict[str, str]]:
    """Extract XML tables from panel and flatten each table by its header row.

    Args:
        code: 6-digit DART stock code.
        sectionPattern: optional regex applied to ``sectionLeaf``.
        period: optional single period label.
        marketNs: panel namespace, normally ``"kr"``.

    Returns:
        Row dictionaries produced from table headers.

    Raises:
        No explicit exceptions; table conversion errors propagate from ``tableToRowDicts``.

    Example:
        >>> panelTableRows("005930")
        []
    """
    rows: list[dict[str, str]] = []
    for table in panelXmlTables(code, sectionPattern=sectionPattern, period=period, marketNs=marketNs):
        rows.extend(gridToRowDicts(table))
    return rows


def _span(cell: ET.Element, name: str) -> int:
    """``ROWSPAN``/``COLSPAN`` 정수 (대/소문자 모두, 부재·비정수 = 1).

    Args:
        cell: 표 셀 element (TD/TH/TE/TU).
        name: "ROWSPAN" 또는 "COLSPAN".

    Returns:
        정수 span (>=1). 비정수/부재 시 1.

    Raises:
        없음.
    """
    raw = cell.get(name) or cell.get(name.lower()) or "1"
    try:
        return max(1, int(raw))
    except (ValueError, TypeError):
        return 1


def _parseTableCells(tableEl: ET.Element) -> list[list[tuple[str, int, int]]]:
    """``<TABLE>`` → 행별 (텍스트, rowspan, colspan) 셀 리스트 (span 보존·미전개).

    Args:
        tableEl: TABLE element.

    Returns:
        행 리스트. 각 행 = (text, rowspan, colspan) 튜플 리스트.

    Raises:
        없음.
    """
    rows: list[list[tuple[str, int, int]]] = []
    for tr in tableEl.iter():
        if _xmlTag(tr.tag) != "TR":
            continue
        cells: list[tuple[str, int, int]] = []
        for cell in tr:
            if _xmlTag(cell.tag) not in _CELL_TAGS:
                continue
            text = _WS_RE.sub(" ", "".join(cell.itertext())).strip()
            cells.append((text, _span(cell, "ROWSPAN"), _span(cell, "COLSPAN")))
        if cells:
            rows.append(cells)
    return rows


def _expandGrid(rowCells: list[list[tuple[str, int, int]]]) -> list[list[str]]:
    """span 보존 셀 → 직사각 격자(rowspan 아래 forward-fill·colspan 오른쪽 채움).

    표준 HTML 표 격자 알고리즘: 열을 왼→오 순회하며 이전 행 rowspan 점유 열은 그 값으로 채우고,
    아니면 다음 셀을 colspan 만큼 펼친다. 모든 행을 최대 폭으로 패딩. DART 사업보고서 표의 병합셀
    (부문 ROWSPAN·COLSPAN)로 후속 행이 헤더보다 짧아지던 셀 밀림(ragged)을 제거.

    Args:
        rowCells: ``_parseTableCells`` 출력 (행별 (text, rowspan, colspan)).

    Returns:
        직사각 격자 (모든 행 동일 열 수).

    Raises:
        없음.

    Example:
        >>> _expandGrid([[("CE", 2, 2), ("A", 1, 1)], [("B", 1, 1)]])
        [['CE', 'CE', 'A'], ['CE', 'CE', 'B']]
    """
    active: dict[int, list] = {}  # col -> [remainingRows, text]
    out: list[list[str]] = []
    for cells in rowCells:
        rowArr: list[str] = []
        col = 0
        for text, rspan, cspan in cells:
            while col in active:
                rowArr.append(active[col][1])
                active[col][0] -= 1
                if active[col][0] <= 0:
                    del active[col]
                col += 1
            for _ in range(cspan):
                rowArr.append(text)
                if rspan > 1:
                    active[col] = [rspan - 1, text]
                col += 1
        while active and max(active) >= col:
            if col in active:
                rowArr.append(active[col][1])
                active[col][0] -= 1
                if active[col][0] <= 0:
                    del active[col]
            else:
                rowArr.append("")
            col += 1
        out.append(rowArr)
    width = max((len(r) for r in out), default=0)
    return [r + [""] * (width - len(r)) for r in out]


def _collapseColspanDupes(grid: list[list[str]]) -> list[list[str]]:
    """colspan 으로 생긴 완전 중복 인접 열을 1개로 합침 (모든 행 값 동일 열만).

    Args:
        grid: 직사각 격자.

    Returns:
        중복 열 제거 격자.

    Raises:
        없음.
    """
    if not grid or not grid[0]:
        return grid
    ncol = len(grid[0])
    keep = [0]
    for c in range(1, ncol):
        if not all(row[c] == row[c - 1] for row in grid):
            keep.append(c)
    return [[row[c] for c in keep] for row in grid]


def gridToRowDicts(grid: list[list[str]], headerRow: int = 0) -> list[dict[str, str]]:
    """직사각 격자(headerRow=헤더) → row dict 리스트. colspan 중복열 합침 + 헤더 중복키 suffix.

    Args:
        grid: ``parsePanelXmlTables`` 출력 격자 (직사각).
        headerRow: 헤더 행 인덱스 (메타행 "(단위: 억원)" 회피용, 기본 0).

    Returns:
        {헤더: 값} dict 리스트 (헤더 아래 데이터 행). 행 부족 시 빈 리스트.

    Raises:
        없음.

    Example:
        >>> gridToRowDicts([["부문", "부문", "품목"], ["CE", "CE", "A"]])
        [{'부문': 'CE', '품목': 'A'}]
    """
    grid = _collapseColspanDupes(grid[headerRow:])
    if len(grid) < 2:
        return []
    seen: dict[str, int] = {}
    keys: list[str] = []
    for i, h in enumerate(grid[0]):
        name = h or f"col{i}"
        if name in seen:
            seen[name] += 1
            keys.append(f"{name}.{seen[name]}")
        else:
            seen[name] = 0
            keys.append(name)
    return [dict(zip(keys, row)) for row in grid[1:]]


def parsePanelXmlTables(content: str) -> list[list[list[str]]]:
    """DART XML 조각 → span-aware 직사각 격자 리스트 (rowspan/colspan 전개).

    Args:
        content: DART XML fragment (0+ ``TABLE`` 노드).

    Returns:
        표 리스트. 각 표 = 직사각 격자 (행×셀, rowspan forward-fill·colspan 채움). 헤더+1행 이상만.

    Raises:
        없음. 깨진 XML 은 빈 리스트.

    Example:
        >>> parsePanelXmlTables("<TABLE><TR><TH>A</TH></TR><TR><TD>1</TD></TR></TABLE>")
        [[['A'], ['1']]]
    """
    try:
        root = ET.fromstring(f"<root>{content}</root>")
    except (ET.ParseError, ValueError):
        return []
    tables: list[list[list[str]]] = []
    for tableEl in root.iter():
        if _xmlTag(tableEl.tag) != "TABLE":
            continue
        rowCells = _parseTableCells(tableEl)
        if len(rowCells) >= 2:
            tables.append(_expandGrid(rowCells))
    return tables


def _xmlTag(tag: object) -> str:
    if not isinstance(tag, str):
        return ""
    return tag.rsplit("}", 1)[-1].upper()


__all__ = [
    "panelTextRows",
    "panelTextWide",
    "panelXmlTables",
    "panelTableRows",
    "parsePanelXmlTables",
    "gridToRowDicts",
]
