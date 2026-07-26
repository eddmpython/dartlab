"""DART raw XML chunk → panel/section view 입력 양식 변환.

DART zip XML 의 TITLE 직속 본문 (P / SPAN / TABLE / TABLE-GROUP / COLGROUP / TR /
TD 등 *모든 태그 그대로*) raw XML chunk 를 사람이 읽을 mixed/plain text 로 변환한다.
panel contentRaw 가 DART 공시 본문 SSOT 이다.

본 모듈은 내부 legacy parser 단계에서 호출되어:

- ``stripTags=False`` (viewer): markdown/HTML mixed → 진짜 데이터 표 (BORDER="1") 는
  HTML ``<table rowspan colspan>`` 그대로 보존, paragraph framing / caption layout
  (BORDER="0" 또는 1×1 단일 cell) 은 plain text. ``<SPAN USERMARK="B">`` (bold) 는
  ``## `` markdown heading prefix. ``<TABLE-GROUP>`` 안 nested TITLE/P/TABLE 은
  parent 본문에 흡수.
- ``stripTags=True`` (show / agent / analysis): 모든 태그 제거 + plain text. HTML
  table 도 cell text 만 추출 (xml itertext).

옛 markdown/HTML mixed 저장 양식은 폐기. 변환은 read/build 시점에서 raw XML을 대상으로 수행한다.
"""

from __future__ import annotations

import re
from typing import Iterator

from lxml import etree

_MULTISPACE_RE = re.compile(r"\s+")
_RE_WHITESPACE = re.compile(r"\s+")
_RE_MULTI_NEWLINE = re.compile(r"\n{3,}")


def _elemText(elem) -> str:
    """element 안 모든 itertext concat (no separator) + 다중 공백 정리 + strip.

    DART XML 의 ``<P>`` 안에는 ``<SPAN>`` 가 word-wrap 단위로 다수 분할된다. ``" ".join``
    로 join 시 word boundary 의 공백 추가 → 의도 깨짐. concat 후 multi-space →
    single space 정리.
    """
    raw = "".join(elem.itertext())
    return _MULTISPACE_RE.sub(" ", raw).strip()


def _findDirectTRs(table) -> Iterator:
    """``<TABLE>`` 직속 + ``<TBODY>``/``<THEAD>``/``<TFOOT>`` 안 TR 만 (nested TABLE 의 TR 제외)."""
    for child in table:
        if not isinstance(child.tag, str):
            continue
        if child.tag == "TR":
            yield child
        elif child.tag in ("TBODY", "THEAD", "TFOOT"):
            for sub in child:
                if isinstance(sub.tag, str) and sub.tag == "TR":
                    yield sub


def _escapeHtml(text: str) -> str:
    """raw text → HTML entity escape (``&`` ``<`` ``>``)."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _cellTextPreservingBreaks(cell) -> str:
    """TD/TH cell → text. 직속 P 가 ≥ 2 면 P 별 줄바꿈 보존, 아니면 itertext join.

    DART XML 의 BORDER="0" paragraph-framing case — 단일 TD 안에 chapter 전체 본문
    이 다수 P 로 들어있다. ``" ".join(cell.itertext())`` 로 join 하면 P 사이 줄바꿈
    이 사라져 사용자 화면에 가/나/다/라 항목이 같은 라인으로 흐른다. P 별 줄바꿈
    보존이 정공.
    """
    directPs = [c for c in cell if isinstance(c.tag, str) and c.tag == "P"]
    if len(directPs) >= 2:
        lines: list[str] = []
        for p in directPs:
            t = "".join(p.itertext())
            t = _MULTISPACE_RE.sub(" ", t).strip()
            if t:
                lines.append(t)
        return "\n".join(lines)
    text = "".join(cell.itertext())
    text = _MULTISPACE_RE.sub(" ", text).strip()
    return text


_VALID_ALIGN = frozenset({"left", "center", "right", "justify"})
_VALID_VALIGN = frozenset({"top", "middle", "bottom", "baseline"})


def _normAlign(raw: str, valid: frozenset[str]) -> str:
    """DART XML ALIGN/VALIGN 속성 정규화 — uppercase → lowercase + whitelist 검증."""
    if not raw:
        return ""
    v = raw.strip().lower()
    return v if v in valid else ""


def _tableToHtml(table) -> str:
    """``<TABLE>`` → HTML ``<table>`` (rowspan/colspan + ALIGN/VALIGN 보존).

    DART XML 의 ``<TABLE BORDER="0">`` 양식은 시각 무 (paragraph framing / caption
    layout). 1×1 단일 cell 도 paragraph framing → plain text return. 진짜 데이터
    표 (BORDER="1" 또는 multi-row/col 병합) 만 HTML ``<table>`` emit. cell 안 직속
    P 가 ≥ 2 면 P 별 줄바꿈 보존.

    ALIGN/VALIGN 보존 (plan snazzy-wibbling-origami PR-1b): DART 원본 ``<TD ALIGN="RIGHT">``
    의 ALIGN 속성을 ``<td align="right">`` 로 emit. viewer (sanitize whitelist 가 이미
    ``align`` 허용) 에서 숫자 cell 우측정렬이 원본대로 보존된다. 옛 구현은 ALIGN 을
    cell.get() 호출조차 안 해 viewer 에서 모든 cell 이 좌측정렬 회귀 (2026-05-28
    사용자 발견). VALIGN 도 동일 패턴.
    """
    border = (table.get("BORDER", "1") or "1").strip()
    isBorderless = border in ("0", "")

    # rows of [(tag, colspan, rowspan, align, valign, text)]
    collected: list[list[tuple[str, str, str, str, str, str]]] = []
    for tr in _findDirectTRs(table):
        cells: list[tuple[str, str, str, str, str, str]] = []
        for cell in tr:
            if not isinstance(cell.tag, str) or cell.tag not in ("TD", "TH", "TU", "TE"):
                continue
            tag = "th" if cell.tag in ("TH", "TU") else "td"
            colspan = cell.get("COLSPAN", "1") or "1"
            rowspan = cell.get("ROWSPAN", "1") or "1"
            align = _normAlign(cell.get("ALIGN", "") or "", _VALID_ALIGN)
            valign = _normAlign(cell.get("VALIGN", "") or "", _VALID_VALIGN)
            text = _cellTextPreservingBreaks(cell)
            cells.append((tag, colspan, rowspan, align, valign, text))
        if cells:
            collected.append(cells)
    if not collected:
        return ""

    # 1×1 paragraph framing — plain text
    if len(collected) == 1 and len(collected[0]) == 1:
        only = collected[0][0]
        if only[1] in ("1", "") and only[2] in ("1", ""):
            return only[5]

    # BORDER="0" multi-cell caption — em-space join + 줄바꿈 row 구분
    if isBorderless:
        lines: list[str] = []
        for cells in collected:
            texts = [c[5] for c in cells if c[5]]
            if texts:
                lines.append(" ".join(texts))
        return "\n".join(lines)

    # 진짜 데이터 표 — HTML <table>. cell 안 \n (multi-P paragraph framing) 은
    # <br/> 로 치환해야 _splitContentBlocks 의 line-by-line table detection 이
    # 같은 td 안에서 새 line 으로 잘못 인식하지 않음 (2026-05-27 회귀 fix).
    out: list[str] = ["<table>"]
    for cells in collected:
        rowOut: list[str] = ["<tr>"]
        for tag, colspan, rowspan, align, valign, text in cells:
            attrs = ""
            if colspan and colspan != "1":
                attrs += f' colspan="{int(colspan)}"'
            if rowspan and rowspan != "1":
                attrs += f' rowspan="{int(rowspan)}"'
            if align:
                attrs += f' align="{align}"'
            if valign:
                attrs += f' valign="{valign}"'
            escaped = _escapeHtml(text).replace("\n", "<br/>")
            rowOut.append(f"<{tag}{attrs}>{escaped}</{tag}>")
        rowOut.append("</tr>")
        out.append("".join(rowOut))
    out.append("</table>")
    return "\n".join(out)


_SENTENCE_END_SUFFIX = ("다.", "요.", "니다.", ".", "?", "!", ")", "]", ":", ";", "다", "요")
_P_MERGE_MAX_LEN = 20


def _canMergePs(prev: str, nxt: str, maxLen: int) -> bool:
    """두 P 가 DART XML word-wrap 결함으로 분할된 case 인지 판정."""
    if not prev or not nxt:
        return False
    if len(prev) > maxLen or len(nxt) > maxLen:
        return False
    if prev.startswith("## ") or nxt.startswith("## "):
        return False
    if prev.startswith("|") or nxt.startswith("|"):
        return False
    if prev.startswith("<table") or nxt.startswith("<table"):
        return False
    if prev.endswith(_SENTENCE_END_SUFFIX):
        return False
    return True


def _mergeShortPs(parts: list[str], maxLen: int = _P_MERGE_MAX_LEN) -> list[str]:
    """인접한 짧은 P 들을 같은 line 으로 합침 (DART XML word-wrap 결함 복원)."""
    if len(parts) <= 1:
        return parts
    result: list[str] = []
    buf = parts[0]
    for nxt in parts[1:]:
        if _canMergePs(buf, nxt, maxLen):
            buf = buf + nxt
        else:
            result.append(buf)
            buf = nxt
    result.append(buf)
    return result


def _walkElementToMixed(elem, parts: list[str]) -> None:
    """element → markdown/HTML mixed string parts 누적 (parseSectionsByTitle 의 옛 _walk 로직 이동)."""
    tag = elem.tag
    if not isinstance(tag, str):
        return
    if tag == "P":
        t = _elemText(elem)
        if t:
            parts.append(t)
        return
    if tag == "SPAN":
        usermark = (elem.get("USERMARK", "") or "").strip()
        t = _elemText(elem)
        if t:
            isBold = "B" in usermark.split()
            if isBold and len(t) < 80:
                parts.append(f"## {t}")
            else:
                parts.append(t)
        return
    if tag == "TABLE":
        html = _tableToHtml(elem)
        if html:
            parts.append(html)
        return
    if tag == "TABLE-GROUP":
        # TABLE-GROUP 안 nested TITLE/P/TABLE 을 parent 본문에 흡수
        for descendant in elem.iter():
            dtag = descendant.tag
            if not isinstance(dtag, str):
                continue
            if dtag in ("TITLE", "COVER-TITLE"):
                t = _elemText(descendant)
                if t:
                    parts.append(f"## {t}")
            elif dtag == "TABLE":
                parent = descendant.getparent()
                if parent is not None and parent.tag == "TABLE-GROUP":
                    html = _tableToHtml(descendant)
                    if html:
                        parts.append(html)
            elif dtag == "P":
                parent = descendant.getparent()
                if parent is not None and parent.tag == "TABLE-GROUP":
                    t = _elemText(descendant)
                    if t:
                        parts.append(t)
        return


def _wrapAsBody(rawXml: str) -> str:
    """raw XML chunks join → ``<BODY>`` wrap (lxml parse 용)."""
    return f"<BODY>{rawXml}</BODY>"


def xmlChunkToMixed(rawXml: str) -> str:
    """raw XML chunks → markdown/HTML mixed string.

    DART zip XML 의 TITLE 직속 본문 raw chunks (P/SPAN/TABLE/TABLE-GROUP 등 모든
    태그 보존) 를 lxml parse → 각 leaf element 별 변환:

    - ``<P>`` → plain text line
    - ``<SPAN USERMARK="B">`` → ``## `` heading prefix
    - ``<TABLE BORDER="1">`` → HTML ``<table>`` (rowspan/colspan 보존)
    - ``<TABLE BORDER="0">`` → plain text (caption layout)
    - ``<TABLE-GROUP>`` → nested TITLE/P/TABLE 흡수

    XML 등장 순서 그대로 (alternating text/table 보존). 옛 ``parseSectionsByTitle``
    의 emit 결과와 동일 양식.

    Args:
        rawXml: TITLE 직속 raw XML chunks join 결과.

    Returns:
        markdown/HTML mixed string — legacy parser pipeline 의 ``_splitContentBlocks``
        가 받을 양식.

    Raises:
        없음. 다만 파서를 `recover=True` 로 쓰기 때문에 깨진 XML 이 예외를 올리지 않고,
        아래 `except` 폴백은 실질적으로 실행되지 않는다. 깨진 입력은 파서가 건져낸
        조각만 남는다. 태그 없는 알몸 텍스트는 요소가 아니라 아예 살아남지 못한다.

    Example:
        1x1 표는 데이터 표가 아니라 문단 프레임이라 HTML 이 아닌 평문이 된다.
        아래는 진짜 데이터 표다.

        >>> xmlChunkToMixed('<TABLE BORDER="1"><TR><TD>a</TD><TD>b</TD></TR></TABLE>')
        '<table>\\n<tr><td>a</td><td>b</td></tr>\\n</table>'
    """
    if not rawXml or not rawXml.strip():
        return ""
    parser = etree.XMLParser(recover=True, huge_tree=True)
    try:
        root = etree.fromstring(_wrapAsBody(rawXml).encode("utf-8"), parser)
    except (etree.XMLSyntaxError, ValueError):
        return rawXml  # fallback — XML parse 실패 시 raw 그대로
    if root is None:
        return rawXml
    parts: list[str] = []
    for child in root:
        _walkElementToMixed(child, parts)
    merged = _mergeShortPs(parts)
    text = "\n\n".join(p for p in merged if p).strip()
    text = _RE_MULTI_NEWLINE.sub("\n\n", text)
    return text


def xmlChunkToPlain(rawXml: str) -> str:
    """raw XML chunks → plain text (모든 태그 제거).

    stripTags=True 일 때 사용. HTML table 도 cell text 만 추출 (xml itertext).
    show / agent / analysis 호환 양식. markdown prefix (``## ``) 도 추가 안 함.

    Args:
        rawXml: TITLE 직속 raw XML chunks join 결과.

    Returns:
        plain text — 모든 XML 태그 제거. 다중 공백 정리.

    Raises:
        없음 — XML parse 실패 시 rawXml 그대로 반환 (fallback).

    Example:
        >>> xmlChunkToPlain('<P>본문</P><TABLE><TR><TD>cell</TD></TR></TABLE>')
        '본문\\n\\ncell'
    """
    if not rawXml or not rawXml.strip():
        return ""
    parser = etree.XMLParser(recover=True, huge_tree=True)
    try:
        root = etree.fromstring(_wrapAsBody(rawXml).encode("utf-8"), parser)
    except (etree.XMLSyntaxError, ValueError):
        return rawXml
    if root is None:
        return rawXml
    lines: list[str] = []
    for child in root:
        ctag = child.tag
        if not isinstance(ctag, str):
            continue
        text = " ".join(child.itertext()).strip()
        text = _MULTISPACE_RE.sub(" ", text)
        if text:
            lines.append(text)
    return "\n\n".join(lines).strip()


_HTML_TAG_RE = re.compile(r"<[^>]+>")


def stripTagsFromCell(cellValue) -> str:
    """sections wide DataFrame 의 cell value (mixed string) → plain text.

    HTML ``<table>...<tr>...<td>...`` 의 cell text 만 추출 + 모든 HTML/XML 태그 제거.
    markdown ``## heading`` prefix 도 plain text. show / agent / analysis 호환.

    Args:
        cellValue: sections cell value (string or None).

    Returns:
        plain text — 태그 제거 + 다중 공백 정리.

    Raises:
        없음.

    Example:
        >>> stripTagsFromCell('## 7. 매출채권\\n<table><tr><td>구분</td><td>금액</td></tr></table>')
        '## 7. 매출채권\\n구분 금액'
    """
    if not cellValue:
        return ""
    if not isinstance(cellValue, str):
        return ""
    if "<" not in cellValue:
        return cellValue
    # HTML <table> 의 cell text 만 추출 (rowspan/colspan 무시, lxml 파서 빠름).
    # 단순 regex 로도 충분 — DOMPurify 단계의 sanitize 가 frontend 영역, 여기는 backend.
    text = _HTML_TAG_RE.sub(" ", cellValue)
    # 다중 공백 single space, 그러나 줄바꿈 보존
    lines = []
    for ln in text.splitlines():
        cleaned = _MULTISPACE_RE.sub(" ", ln).strip()
        if cleaned:
            lines.append(cleaned)
    return "\n".join(lines)


def stripTagsFromSectionsDf(df, periodCols=None):
    """sections wide DataFrame 의 모든 period column cell → plain text.

    period column 양식 — ``2026Q1`` / ``2025Q4`` / ``2025`` 등. ``periodCols=None``
    이면 ``df.columns`` 에서 ``20\\d\\d`` prefix 자동 감지.

    Args:
        df: panel text wide DataFrame.
        periodCols: 강제 지정 — None 이면 자동 감지.

    Returns:
        같은 schema 의 DataFrame — period column cell 만 stripTagsFromCell 적용.

    Raises:
        없음 — df=None 이면 None 반환.

    Example:
        >>> from dartlab import Company
        >>> from dartlab.providers.dart.sectionXml import stripTagsFromSectionsDf
        >>> df = stripTagsFromSectionsDf(Company('005930').panel("사업의 내용"))
    """
    if df is None:
        return None
    import polars as pl

    if periodCols is None:
        periodCols = [c for c in df.columns if c[:2] in ("20", "19") and any(ch.isdigit() for ch in c)]
    if not periodCols:
        return df
    return df.with_columns(
        [pl.col(c).map_elements(stripTagsFromCell, return_dtype=pl.Utf8).alias(c) for c in periodCols]
    )


__all__ = [
    "xmlChunkToMixed",
    "xmlChunkToPlain",
    "stripTagsFromCell",
    "stripTagsFromSectionsDf",
]
