"""HTML ``<table>`` native parser — ALIGN/COLSPAN/ROWSPAN 인식.

plan snazzy-wibbling-origami PR-5c. ``content_table_struct`` 컬럼 (PR-5b) 의 HTML
``<table>`` block 을 항목 × 기간 dict 또는 cell grid 로 변환. 옛 markdown 평탄화
경로 (``tableHorizontalizer`` 의 ``splitSubtables`` 등) 가 잃은 정보 복원:

- ``<td align="right">`` → 숫자 cell 자동 분류
- ``<td colspan="3">`` → multi-period header 그룹 인식
- ``<td rowspan="2">`` → cell 병합 cascade

finance pipeline (analysis/financial/* 60 모듈) 의 BS/IS/CF 변환 정확도 향상 입력.
horizontalizeTableBlock 의 부분 path 또는 별도 entry 로 통합 (후속).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator

from lxml import etree


@dataclass
class HtmlTableCell:
    """HTML 표 cell 의 정규화된 표현 — ALIGN/colspan/rowspan 포함."""

    text: str
    colspan: int = 1
    rowspan: int = 1
    align: str = ""  # "right" / "center" / "left" / ""
    valign: str = ""
    isHeader: bool = False  # th 인지 td 인지


@dataclass
class HtmlTableRow:
    """HTML 표 한 row 의 cell list."""

    cells: list[HtmlTableCell] = field(default_factory=list)


@dataclass
class HtmlTable:
    """HTML 표 전체 — rows + 메타 (column count, header rows count)."""

    rows: list[HtmlTableRow] = field(default_factory=list)
    maxCols: int = 0
    headerRowCount: int = 0  # 첫 th row 들의 개수 (multi-row header)


def parseHtmlTable(html: str) -> HtmlTable | None:
    """HTML ``<table>...</table>`` string → ``HtmlTable`` 구조체.

    옛 ``_tableToHtml`` (xmlAdapter) 가 emit 한 양식 입력. multi-row header (연속 th
    row) 자동 카운트. ALIGN/VALIGN/colspan/rowspan 모두 보존. 잘못된 HTML 은 None.

    Args:
        html: ``<table>...</table>`` HTML string.

    Returns:
        HtmlTable 또는 None (parse 실패 / 비어있음).

    Example:
        >>> t = parseHtmlTable("<table><tr><th>구분</th></tr><tr><td>매출</td></tr></table>")
        >>> (t.headerRowCount, len(t.rows))
        (1, 2)

    Raises:
        없음 — XMLSyntaxError silent + None.
    """
    if not html or "<table" not in html:
        return None
    try:
        # XHTML 호환 — recover=True 로 attribute 따옴표 누락 등 복구.
        parser = etree.HTMLParser(recover=True)
        root = etree.fromstring(html, parser)
    except (etree.XMLSyntaxError, ValueError):
        return None
    if root is None:
        return None
    # lxml.html parser 는 <html><body><table>...</table></body></html> 으로 wrap. table 만 찾기.
    tables = list(root.iter("table"))
    if not tables:
        return None
    return _tableFromElement(tables[0])


def parseHtmlTables(html: str) -> list[HtmlTable]:
    """본문 내 *모든* ``<table>`` 를 ``HtmlTable`` list 로 (행/ALIGN/span 보존).

    ``parseHtmlTable`` 이 첫 표 1 개만 보는 것과 달리, KRX 수시공시처럼 여러 ``<table>``
    block 으로 구성된 본문(예 잠정실적: 안내표 + 실적표)에서 실적 행렬표를 골라 쓰려면
    표별 행 구조를 유지한 채 전부 열거해야 한다. ``flattenTableCells`` 는 행 경계를 잃어
    행렬표(계정 × 기간)에 부적합하다.

    Args:
        html: 공시 본문 HTML (다중 ``<table>`` 허용).

    Returns:
        list[HtmlTable]. 문서 순서. parse 실패/비표는 빈 list.

    Example:
        >>> ts = parseHtmlTables("<table><tr><td>a</td></tr></table><table><tr><td>b</td></tr></table>")
        >>> len(ts)
        2

    Raises:
        없음. XMLSyntaxError silent 처리 후 빈 list.
    """
    if not html or "<table" not in html:
        return []
    try:
        parser = etree.HTMLParser(recover=True)
        root = etree.fromstring(html, parser)
    except (etree.XMLSyntaxError, ValueError):
        return []
    if root is None:
        return []
    out: list[HtmlTable] = []
    for table in root.iter("table"):
        parsed = _tableFromElement(table)
        if parsed is not None:
            out.append(parsed)
    return out


def _tableFromElement(table) -> HtmlTable | None:
    """단일 ``<table>`` lxml element 를 ``HtmlTable`` 로 (rows + header 카운트)."""
    out = HtmlTable()
    inHeaderSection = True
    for tr in _findTrs(table):
        row = HtmlTableRow()
        hasNonHeader = False
        for td in tr:
            if not isinstance(td.tag, str) or td.tag not in ("td", "th"):
                continue
            isHeader = td.tag == "th"
            if not isHeader:
                hasNonHeader = True
            cell = HtmlTableCell(
                text="".join(td.itertext()).strip(),
                colspan=_intAttr(td, "colspan", 1),
                rowspan=_intAttr(td, "rowspan", 1),
                align=(td.get("align", "") or "").strip().lower(),
                valign=(td.get("valign", "") or "").strip().lower(),
                isHeader=isHeader,
            )
            row.cells.append(cell)
        if row.cells:
            out.rows.append(row)
            cols = sum(c.colspan for c in row.cells)
            if cols > out.maxCols:
                out.maxCols = cols
            # 연속 header row 카운트 (td 1 개 이상 등장 시 header section 종료).
            if inHeaderSection:
                if hasNonHeader:
                    inHeaderSection = False
                else:
                    out.headerRowCount += 1
    return out if out.rows else None


def _findTrs(table) -> Iterator:
    """``<table>`` 직속 + ``<tbody>``/``<thead>``/``<tfoot>`` 안 ``<tr>`` 만 iter."""
    for child in table:
        if not isinstance(child.tag, str):
            continue
        if child.tag == "tr":
            yield child
        elif child.tag in ("tbody", "thead", "tfoot"):
            for sub in child:
                if isinstance(sub.tag, str) and sub.tag == "tr":
                    yield sub


def _intAttr(elem, name: str, default: int) -> int:
    raw = elem.get(name, "")
    if not raw:
        return default
    try:
        return int(str(raw).strip())
    except (ValueError, TypeError):
        return default


def extractItemValuePairs(html: str) -> dict[str, str]:
    """HTML 표 → ``{첫 cell text: 마지막 cell text}`` 단순 dict.

    finance pipeline 의 간단한 (item, value) 추출 입구. 항목명 (첫 col) + 금액 (마지막 col)
    매핑. header row + 다중 cell row 자동 처리.

    Args:
        html: HTML ``<table>`` string.

    Returns:
        ``{item: value}`` dict. parse 실패 또는 빈 표는 빈 dict.

    Example:
        >>> extractItemValuePairs('<table><tr><th>구분</th><th>금액</th></tr><tr><td>매출</td><td align="right">100</td></tr></table>')
        {'매출': '100'}

    Raises:
        없음 — parseHtmlTable 위임, parse 실패는 빈 dict 로 흡수한다.
    """
    parsed = parseHtmlTable(html)
    if parsed is None:
        return {}
    out: dict[str, str] = {}
    # header row skip
    for row in parsed.rows[parsed.headerRowCount :]:
        if len(row.cells) < 2:
            continue
        item = row.cells[0].text
        value = row.cells[-1].text
        if item and value:
            out[item] = value
    return out


def flattenTableCells(html: str) -> list[str]:
    """본문 내 *모든* ``<table>`` 의 cell text 를 문서 순서 flat list 로.

    ``parseHtmlTable`` (첫 표 1 개) 과 달리 KRX 수시공시처럼 여러 ``<table>`` block 으로
    구성된 본문 전체를 훑어 라벨→값 인접 탐색용 평탄 셀 시퀀스를 만든다. colspan/rowspan
    은 펼치지 않고 원본 cell 1 회 (라벨/값 인접성은 cell 순서로 충분). 태그 제거 + 공백
    정규화 (``itertext`` join). lxml recover 로 깨진 HTML 흡수.

    Args:
        html: 공시 본문 HTML (다중 ``<table>`` 허용).

    Returns:
        list[str] — 문서 순서 cell text. parse 실패/비표는 빈 list.

    Example:
        >>> flattenTableCells('<table><tr><td>계약금액(원)</td><td>100</td></tr></table>')
        ['계약금액(원)', '100']

    Raises:
        없음 — XMLSyntaxError silent + 빈 list.
    """
    if not html or "<table" not in html:
        return []
    try:
        parser = etree.HTMLParser(recover=True)
        root = etree.fromstring(html, parser)
    except (etree.XMLSyntaxError, ValueError):
        return []
    if root is None:
        return []
    out: list[str] = []
    for table in root.iter("table"):
        for tr in _findTrs(table):
            for td in tr:
                if isinstance(td.tag, str) and td.tag in ("td", "th"):
                    out.append(" ".join("".join(td.itertext()).split()))
    return out


def cellGrid(html: str) -> list[list[HtmlTableCell]]:
    """rowspan/colspan 을 *모두 펼친* cell grid (rectangular).

    multi-row header 또는 cell 병합 표를 정규화된 R × C grid 로. 각 cell 은 원본
    HtmlTableCell 의 reference 공유 (병합된 cell 은 같은 instance 가 grid 의 여러
    좌표에 등장).

    Args:
        html: HTML ``<table>`` string.

    Returns:
        ``grid[row][col]`` 양식 2D list. parse 실패 시 빈 list.

    Example:
        >>> g = cellGrid('<table><tr><td colspan="2">병합</td></tr><tr><td>a</td><td>b</td></tr></table>')
        >>> g[0][0].text == g[0][1].text  # colspan 으로 같은 cell 이 두 좌표에
        True

    Raises:
        없음 — parseHtmlTable 위임, parse 실패는 빈 list 로 흡수한다.
    """
    parsed = parseHtmlTable(html)
    if parsed is None:
        return []
    grid: list[list[HtmlTableCell | None]] = []
    # rowspan tracking — 각 col 의 남은 row span 카운트
    spanCarry: dict[int, tuple[HtmlTableCell, int]] = {}  # col → (cell, remaining_rows)
    for row in parsed.rows:
        outRow: list[HtmlTableCell | None] = []
        col = 0
        cellIdx = 0
        while col < parsed.maxCols or cellIdx < len(row.cells):
            # 이전 row 의 rowspan carry
            if col in spanCarry:
                carriedCell, remaining = spanCarry[col]
                outRow.append(carriedCell)
                if remaining > 1:
                    spanCarry[col] = (carriedCell, remaining - 1)
                else:
                    del spanCarry[col]
                col += 1
                continue
            if cellIdx < len(row.cells):
                cell = row.cells[cellIdx]
                cellIdx += 1
                for offset in range(cell.colspan):
                    outRow.append(cell)
                if cell.rowspan > 1:
                    for offset in range(cell.colspan):
                        spanCarry[col + offset] = (cell, cell.rowspan - 1)
                col += cell.colspan
            else:
                break
        grid.append(outRow)
    # 마지막 row 들 (rowspan carry 만 있는 가상 row) — 표가 명시적으로 끝났으면 skip
    # 일반적으로 sections 의 표는 자연 종료되므로 추가 처리 X
    return grid
