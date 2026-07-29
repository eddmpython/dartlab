"""HTML 표를 bounded markdown grid로 변환하는 L0 primitive."""

from __future__ import annotations

import re
from dataclasses import dataclass

from bs4 import Tag
from lxml.html import HtmlElement

_MAX_TABLE_COLUMNS = 256
_MAX_TABLE_CELLS = 1_000_000


class HtmlTableShapeError(ValueError):
    """HTML 표 span이 안전한 grid 범위를 벗어난 경우."""


@dataclass(frozen=True, slots=True)
class _TableCell:
    text: str
    rowspan: object
    colspan: object


def _parseSpan(raw: object, *, attribute: str, rowCount: int | None = None) -> int:
    if raw is None or raw == "":
        return 1
    try:
        value = int(str(raw))
    except (TypeError, ValueError) as exc:
        raise HtmlTableShapeError(f"{attribute}은 정수여야 합니다: {raw!r}") from exc
    if attribute == "rowspan" and value == 0 and rowCount is not None:
        return rowCount
    if value <= 0:
        raise HtmlTableShapeError(f"{attribute}은 양수여야 합니다: {value}")
    return value


def _isOccupied(grid: list[list[str | None]], row: int, column: int) -> bool:
    return column < len(grid[row]) and grid[row][column] is not None


def _rectangleOccupied(
    grid: list[list[str | None]],
    *,
    row: int,
    column: int,
    rowspan: int,
    colspan: int,
) -> bool:
    return any(
        _isOccupied(grid, row + rowOffset, column + columnOffset)
        for rowOffset in range(rowspan)
        for columnOffset in range(colspan)
    )


def _writeCell(
    grid: list[list[str | None]],
    *,
    row: int,
    column: int,
    rowspan: int,
    colspan: int,
    text: str,
) -> None:
    for rowOffset in range(rowspan):
        targetRow = grid[row + rowOffset]
        required = column + colspan - len(targetRow)
        if required > 0:
            targetRow.extend([None] * required)
        for columnOffset in range(colspan):
            targetRow[column + columnOffset] = text if rowOffset == columnOffset == 0 else ""


def _rowsToMarkdown(rows: list[list[_TableCell]]) -> str:
    if not rows:
        return ""
    if len(rows) > _MAX_TABLE_CELLS:
        raise HtmlTableShapeError(f"표 행 수가 최대 {_MAX_TABLE_CELLS}개를 초과했습니다: {len(rows)}")

    grid: list[list[str | None]] = [[] for _ in rows]
    hasCell = False

    for rowIndex, row in enumerate(rows):
        columnIndex = 0
        for cell in row:
            hasCell = True
            colspan = _parseSpan(cell.colspan, attribute="colspan")
            if colspan > _MAX_TABLE_COLUMNS:
                raise HtmlTableShapeError(f"colspan이 최대 {_MAX_TABLE_COLUMNS}열을 초과했습니다: {colspan}")
            remainingRows = len(rows) - rowIndex
            rowspan = min(
                _parseSpan(cell.rowspan, attribute="rowspan", rowCount=remainingRows),
                remainingRows,
            )

            while _rectangleOccupied(
                grid,
                row=rowIndex,
                column=columnIndex,
                rowspan=rowspan,
                colspan=colspan,
            ):
                columnIndex += 1
            if columnIndex + colspan > _MAX_TABLE_COLUMNS:
                raise HtmlTableShapeError(f"표 너비가 최대 {_MAX_TABLE_COLUMNS}열을 초과했습니다")

            _writeCell(
                grid,
                row=rowIndex,
                column=columnIndex,
                rowspan=rowspan,
                colspan=colspan,
                text=cell.text,
            )
            columnIndex += colspan

    if not hasCell:
        return ""

    grid = [row for row in grid if any(cell is not None for cell in row)]
    maxColumns = max(len(row) for row in grid)
    if len(grid) * maxColumns > _MAX_TABLE_CELLS:
        raise HtmlTableShapeError(f"표 grid가 최대 {_MAX_TABLE_CELLS} cell을 초과했습니다: {len(grid)}x{maxColumns}")

    normalizedRows = [[cell or "" for cell in row] + [""] * (maxColumns - len(row)) for row in grid]
    lines = [
        "| " + " | ".join(normalizedRows[0]) + " |",
        "| " + " | ".join(["---"] * maxColumns) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in normalizedRows[1:])
    return "\n".join(lines)


def tableToMarkdown(table: Tag) -> str:
    """BeautifulSoup table을 span-aware markdown grid로 변환한다.

    Capabilities:
        최상위 행만 읽어 중첩 표의 중복 행을 막고, rowspan과 colspan을 bounded grid로
        확장하며 cell pipe를 fullwidth 문자로 바꾼다.
    AIContext:
        DART와 EDGAR 원문 표를 동일한 textual evidence 형식으로 만드는 SSOT다.
    Guide:
        BeautifulSoup에서 얻은 ``table`` Tag만 전달한다. 빈 표는 빈 문자열을 반환한다.
    When:
        BeautifulSoup 기반 EDGAR 또는 기타 HTML parser가 markdown evidence 표를 만들 때.
    How:
        직속 행과 cell을 추출한 뒤 공용 bounded grid renderer에 전달한다.
    Requires:
        표 너비는 256열, 최종 grid는 100만 cell 이하이어야 한다.
    SeeAlso:
        ``lxmlTableToMarkdown``은 같은 grid renderer의 lxml adapter다.

    Args:
        table: BeautifulSoup ``<table>`` Tag.

    Returns:
        첫 행을 header로 사용하는 markdown table. cell이 없으면 빈 문자열.

    Example:
        >>> from bs4 import BeautifulSoup
        >>> tag = BeautifulSoup("<table><tr><td>A</td></tr></table>", "lxml").find("table")
        >>> tableToMarkdown(tag)  # doctest: +ELLIPSIS
        '| A |...'

    Raises:
        TypeError: 입력이 ``table`` Tag가 아닌 경우.
        HtmlTableShapeError: span 또는 최종 grid가 안전 한계를 벗어난 경우.
    """
    if not isinstance(table, Tag) or table.name != "table":
        raise TypeError("table은 BeautifulSoup의 <table> Tag여야 합니다")

    rowTags = [row for row in table.find_all("tr") if row.find_parent("table") is table]
    rows = [
        [
            _TableCell(
                text=re.sub(r"\s+", " ", cell.get_text(" ", strip=True)).replace("|", "｜"),
                rowspan=cell.get("rowspan"),
                colspan=cell.get("colspan"),
            )
            for cell in row.find_all(["td", "th"], recursive=False)
        ]
        for row in rowTags
    ]
    return _rowsToMarkdown(rows)


def lxmlTableToMarkdown(table: HtmlElement) -> str:
    """lxml table을 공용 markdown grid로 변환한다.

    Capabilities:
        lxml의 빠른 tree 순회를 사용하되 span 확장, 중첩 행 제외, 안전 한계, markdown
        형식은 ``tableToMarkdown``과 같은 SSOT를 사용한다.
    AIContext:
        대형 DART viewer section을 BeautifulSoup 재구축 없이 evidence text로 바꾼다.
    Guide:
        ``lxml.html``에서 얻은 ``table`` element만 전달한다.
    When:
        lxml로 파싱한 대형 HTML에서 표를 markdown evidence로 보존할 때.
    How:
        직속 행과 cell text만 읽어 공용 bounded grid renderer에 전달한다.
    Requires:
        lxml HTML element와 최대 256열, 100만 cell 제한.
    SeeAlso:
        ``tableToMarkdown``은 같은 grid renderer의 BeautifulSoup adapter다.

    Args:
        table: lxml ``<table>`` element.

    Returns:
        ``tableToMarkdown``과 같은 markdown table.

    Example:
        >>> from lxml.html import fromstring
        >>> tag = fromstring("<table><tr><td>A</td></tr></table>")
        >>> lxmlTableToMarkdown(tag)  # doctest: +ELLIPSIS
        '| A |...'

    Raises:
        TypeError: 입력이 lxml ``table`` element가 아닌 경우.
        HtmlTableShapeError: span 또는 최종 grid가 안전 한계를 벗어난 경우.
    """
    if not isinstance(table, HtmlElement) or table.tag != "table":
        raise TypeError("table은 lxml의 <table> element여야 합니다")

    rowElements = [row for row in table.iter("tr") if next(row.iterancestors("table"), None) is table]
    rows = [
        [
            _TableCell(
                text=re.sub(r"\s+", " ", " ".join(cell.itertext()).strip()).replace("|", "｜"),
                rowspan=cell.get("rowspan"),
                colspan=cell.get("colspan"),
            )
            for cell in row
            if cell.tag in {"td", "th"}
        ]
        for row in rowElements
    ]
    return _rowsToMarkdown(rows)
