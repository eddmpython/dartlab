"""DART document.xml → panel title-row list.

원본 XML 의 ``<TITLE ATOC="Y" AASSOCNOTE="D-0-3-1-0">`` 명시 hierarchy 와
``<TABLE>`` rowspan/colspan + ``<SPAN USERMARK="F-14 B">`` 가/나/다 bold marker
를 직접 사용 → legacy parser layer 의 regex 추론을 builder 단에서 사전 해결.

기존 SECTION-1/SECTION-2 통째 본문 추출은 chapter 본문이 4MB 통째로 cell 에
들어가 legacy parser layer 가 regex 로 하위 title 을 분리 → 추론 오류 다발. 본 모듈의
``parseSectionsByTitle`` 은 각 ``<TITLE>`` 별로
row 를 분리하고 직속 본문만 attach — title 별 cell value 가 작아짐 +
hierarchy (AASSOCNOTE / ATOCID) 보존.

회귀 보장:
- ``section_title`` / ``section_content`` 컬럼 호환 — 기존 caller 영향 0.
- 추가 컬럼 ``atocid`` / ``assocnote`` — legacy parser layer 가 활용 가능 (optional).
- 005930 검증: 1 rcept × 57 sub-doc → 144 TITLE-level rows, panel parity
  regression 0.

호출:
    >>> from dartlab.providers.dart.panel.build.titleRows import parseSectionsByTitle
    >>> rows = parseSectionsByTitle(xmlContent)
    >>> rows[0]
    {'order': 0, 'title': '사 업 보 고 서', 'content': '...', 'atocid': '402', 'assocnote': 'COVER'}
"""

from __future__ import annotations

import re
from typing import Any

from lxml import etree

# TR 순회는 sectionXml 이 정본 (같은 DART XML 표를 읽는 유일 구현). 여기서 재선언하면
# 한쪽만 고쳐지는 표류가 생긴다.
from dartlab.providers.dart.sectionXml import _findDirectTRs

_MULTISPACE_RE = re.compile(r"\s+")


def _elemText(elem) -> str:
    """element 안 모든 itertext concat (no separator) + 다중 공백 정리 + strip.

    DART XML 의 ``<P>`` 안에는 ``<SPAN>`` 가 word-wrap 단위로 다수 분할된다 (시각적
    한 줄당 한 SPAN). 회귀 사례 (005930 분기보고서):
        ``<SPAN>지역별로 보면, 국내</SPAN><SPAN>에서</SPAN><SPAN>는 </SPAN>``
    ``" ".join`` 로 join 시 "지역별로 보면, 국내 에서 는" 처럼 공백 추가 → 의도
    "지역별로 보면, 국내에서는" 망가짐. 단어 끊김도 동일 (예 "메모리" →
    ``<SPAN>메</SPAN><SPAN>모리</SPAN>`` → " 메 모리").

    concat 후 multiple-space → single space 정리. 영어 단어 사이 SPAN boundary 의
    경우 source 의 공백이 SPAN 안 trailing/leading 에 포함되어 있어 손실 없음.
    """
    raw = "".join(elem.itertext())
    return _MULTISPACE_RE.sub(" ", raw).strip()


def _escapeHtml(text: str) -> str:
    """raw text → HTML entity escape (`& < >`)."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _tableToMarkdown(table) -> str:
    """XML ``<TABLE>`` → HTML table 문자열. rowspan/colspan attribute 보존.

    이전 구현은 markdown table 문법 (`| ... |`) 출력이라 GFM 이 rowspan 미지원 →
    DART HTML 의 multi-row header (`<th rowspan>`) 가 평탄화돼 stair-step row 다수.
    회귀 사례 (005930 차입금/재고자산 multi-row header 시각 깨짐).

    본 구현은 HTML 그대로 출력 (`<table><tr><td rowspan colspan>...`) — frontend 가
    sanitize 후 raw HTML 렌더하면 원본 DART 표 시각 fidelity 100% 회복.

    함수명은 호환 위해 ``_tableToMarkdown`` 유지 (caller 영향 0). 출력 형식 변경만.
    downstream ``classifyContent`` / ``buildMarkdownBlocks`` 의 table line 검출은
    `<table` prefix 도 인식하도록 동행 수정.

    nested ``<TABLE>`` 차단 — 외부 TR / cell 만. nested table cell 내용은
    itertext 로 inline (별도 row 안 만듦). 회귀 차단: 기존 ``iter('TR')`` +
    ``.//TD`` 가 nested table 의 TR/cell 까지 외부에 포함시켜 한 table 420MB+
    markdown 폭발 (035720 회귀).
    """
    # 1차 pass — TR/cell 수집. DART XML 의 시각 무 `<TABLE BORDER="0">` 양식은 시각상
    # table 아니라 layout 도구 (paragraph framing / caption+unit / 정렬 보조). 좁은
    # viewer column 에서 본문 한 cell 한 줄 펼침 + 가로 스크롤 트리거 회귀 차단.
    border = (table.get("BORDER", "1") or "1").strip()
    isBorderless = border in ("0", "")

    collected: list[list[tuple[str, str, str, str]]] = []  # rows of [(tag, colspan, rowspan, text)]
    for tr in _findDirectTRs(table):
        cells: list[tuple[str, str, str, str]] = []
        for cell in tr:
            if not isinstance(cell.tag, str) or cell.tag not in ("TD", "TH", "TU", "TE"):
                continue
            tag = "th" if cell.tag in ("TH", "TU") else "td"
            colspan = cell.get("COLSPAN", "1") or "1"
            rowspan = cell.get("ROWSPAN", "1") or "1"
            text = " ".join(cell.itertext()).strip().replace("\n", " ")
            cells.append((tag, colspan, rowspan, text))
        if cells:
            collected.append(cells)
    if not collected:
        return ""

    # 단일 cell paragraph framing — 1 row × 1 col + 병합 없음 → plain text
    if len(collected) == 1 and len(collected[0]) == 1:
        only = collected[0][0]
        if only[1] in ("1", "") and only[2] in ("1", ""):
            return only[3]

    # BORDER="0" 시각 무 layout table — paragraph + (단위) caption 양식. table tag 없이
    # cell text 들 em-space ( ) 로 join + 줄바꿈으로 row 구분. multi-row 도 단순
    # 줄바꿈 caption block 으로. 진짜 multi-col 데이터 table 은 BORDER="1" 양식 유지.
    if isBorderless:
        lines: list[str] = []
        for cells in collected:
            texts = [c[3] for c in cells if c[3]]
            if texts:
                lines.append(" ".join(texts))
        return "\n".join(lines)

    out: list[str] = ["<table>"]
    for cells in collected:
        rowOut: list[str] = ["<tr>"]
        for tag, colspan, rowspan, text in cells:
            attrs = ""
            if colspan and colspan != "1":
                attrs += f' colspan="{int(colspan)}"'
            if rowspan and rowspan != "1":
                attrs += f' rowspan="{int(rowspan)}"'
            rowOut.append(f"<{tag}{attrs}>{_escapeHtml(text)}</{tag}>")
        rowOut.append("</tr>")
        out.append("".join(rowOut))
    out.append("</table>")
    return "\n".join(out)


# Phase B-5: DART XML 의 `<P>` word-wrap 분할 결함 복원. 한 시각적 line 의 단어들이
# 다수 `<P>` 로 부서져 있는 패턴 (예: <P>사업부문별</P><P>현황</P>) 을 같은 line 으로
# 합침. 회귀 사례: "사업부문별" / "현황" 두 P 가 legacy parser layer 의 textPath build 에서
# "사업부문별 > " (현황 잘림) 으로 잘려나가던 것을 "사업부문별현황" 한 단위로 복원.
_SENTENCE_END_SUFFIX = ("다.", "요.", "니다.", ".", "?", "!", ")", "]", ":", ";", "다", "요")
_P_MERGE_MAX_LEN = 20


def _mergeShortPs(parts: list[str], maxLen: int = _P_MERGE_MAX_LEN) -> list[str]:
    """인접한 짧은 P 들을 같은 line 으로 합침 (DART XML word-wrap 결함 복원).

    조건 모두 만족 시 prev + curr 합침 (공백 0):
    1. prev 와 curr 둘 다 ``maxLen`` 이하 (default 20 chars).
    2. prev 가 sentence-end (다./요./니다././?/!/)/].).) 가 아님.
    3. prev 와 curr 둘 다 markdown heading prefix (``## ``) 아님.
    4. prev 와 curr 둘 다 markdown table prefix (``|``) 아님.

    word-wrap 인 경우 source XML 에 공백 의도가 없으므로 ``join("")`` 사용 — Phase B-4
    의 SPAN concat 과 동일 원칙.
    """
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


def _canMergePs(prev: str, nxt: str, maxLen: int) -> bool:
    """두 P 가 word-wrap 결함으로 분할된 case 인지 판정."""
    if not prev or not nxt:
        return False
    if len(prev) > maxLen or len(nxt) > maxLen:
        return False
    if prev.startswith("## ") or nxt.startswith("## "):
        return False
    if prev.startswith("|") or nxt.startswith("|"):
        return False
    if prev.endswith(_SENTENCE_END_SUFFIX):
        return False
    return True


def parseSectionsByTitle(xmlContent: str) -> list[dict[str, Any]]:
    """DART document.xml → ``<TITLE>`` 별 섹션 row list.

    Args:
        xmlContent: document.xml 의 XML 문자열 (UTF-8 decoded).

    Returns:
        list[dict] — 각 dict 는 ``order``/``title``/``content``/``atocid``/``assocnote`` 키.

        - ``order``: TITLE 의 document order (0-indexed).
        - ``title``: ``<TITLE>`` text.
        - ``content``: 그 TITLE 직속 body (다음 TITLE 까지의 ``<P>``/``<SPAN>``/``<TABLE>``).
          ``<SPAN USERMARK="... B">`` (가/나/다 bold marker) 는 markdown ``## prefix``
          로 변환. ``<TABLE>`` 은 markdown table 로 변환 (rowspan 자동 보존).
        - ``atocid``: ``<TITLE ATOCID>`` (TOC unique ID, 없으면 ``""``).
        - ``assocnote``: ``<TITLE AASSOCNOTE>`` (path-id 예 ``D-0-3-1-0``,
          ``D``=document / ``L``=list / ``0``=skip / ``{chapter}`` / ``{sub}`` / ``{subsub}``).

    Raises:
        없음.

    Example:
        >>> with open("20260310002820.xml", encoding="utf-8") as f:
        ...     xml = f.read()
        >>> rows = parseSectionsByTitle(xml)
        >>> len(rows)  # 144 (vs 기존 SECTION-1/2 = 57)
        144
        >>> rows[3]
        {'order': 3, 'title': 'I. 회사의 개요', 'atocid': '3', 'assocnote': '', ...}
    """
    parser = etree.XMLParser(recover=True, huge_tree=True)
    try:
        root = etree.fromstring(xmlContent.encode("utf-8"), parser)
    except (etree.XMLSyntaxError, ValueError):
        return []
    if root is None:
        return []
    body = root.find(".//BODY")
    if body is None:
        return []

    sections: list[dict[str, Any]] = []
    currentTitle: dict[str, Any] | None = None
    bodyParts: list[str] = []
    order = 0

    def _flush() -> None:
        nonlocal currentTitle, bodyParts, order
        if currentTitle is not None:
            # raw XML chunks join — legacy parser layer (xmlAdapter) 가 markdown/HTML
            # mixed 또는 plain text 로 stripTags 파라미터로 변환.
            currentTitle["content"] = "\n".join(p for p in bodyParts if p).strip()
            currentTitle["order"] = order
            sections.append(currentTitle)
            order += 1
        bodyParts = []
        currentTitle = None

    # 명시 DFS — TITLE 단위로 분리하고 TITLE 직속 본문 (다음 TITLE 까지의 element 들)
    # 의 *raw XML chunk* 를 그대로 보존. P/SPAN/TABLE/COLGROUP/TR/TD 등 모든 태그 살려.
    # panel reader 가 stripTags 파라미터로 markdown/HTML 변환 또는 plain text 추출.
    # 원본 XML chunk 는 panel contentRaw 에 보존한다.
    def _walk(elem) -> None:
        nonlocal currentTitle
        tag = elem.tag
        if not isinstance(tag, str):
            return
        if tag in ("TITLE", "COVER-TITLE"):
            _flush()
            currentTitle = {
                "atocid": elem.get("ATOCID", "") or "",
                "assocnote": elem.get("AASSOCNOTE", "") or "",
                "title": _elemText(elem),
                "content": "",
            }
            return  # TITLE 의 descendants 는 title text 안에 이미 흡수
        # leaf body elements — raw XML chunk emit (descendants 포함, etree.tostring)
        if tag in ("P", "SPAN", "TABLE", "TABLE-GROUP"):
            if currentTitle is not None:
                try:
                    xml_str = etree.tostring(elem, encoding="unicode").strip()
                    if xml_str:
                        bodyParts.append(xml_str)
                except (ValueError, TypeError):
                    pass
            return  # descend X — etree.tostring 이 이미 descendants 포함
        # container (SECTION-1/SECTION-2 등) — descend
        for child in elem:
            _walk(child)

    for child in body:
        _walk(child)
    _flush()
    return sections


# 한 row 의 section_content 최대 size — panel build/parser 공유 한도.
# core.dartConstants 정본 (회귀 차단: polars row_tuples PyObject 변환이 4MB+ panic.
# 1MB 안전선 + pa.string() 32-bit offset column total 한도 회피).
from dartlab.core.dartConstants import MAX_CELL_BYTES  # noqa: E402


def splitLargeContent(text: str, maxBytes: int = MAX_CELL_BYTES) -> list[str]:
    """text 가 maxBytes 초과 시 paragraph (``\\n\\n``) → line 단위로 분할.

    회귀 사례: 4MB+ string 의 polars ``row_tuples`` PyObject 변환 panic. 본 helper
    가 1MB 안전선으로 split → multiple row 분할 (같은 atocid/assocnote 유지,
    section_order 만 split index 만큼 증가).

    Args:
        text: 원본 string.
        maxBytes: per-cell 최대 char 수 (기본 1MB).

    Returns:
        분할된 list[str] — 각 원소 ≤ maxBytes char.

    Raises:
        없음.

    Example:
        >>> chunks = splitLargeContent("..." * 500000)
        >>> all(len(c) <= MAX_CELL_BYTES for c in chunks)
        True
    """
    if len(text) <= maxBytes:
        return [text]
    parts: list[str] = []
    buf: list[str] = []
    bufLen = 0
    for para in text.split("\n\n"):
        pLen = len(para)
        if pLen > maxBytes:
            if buf:
                parts.append("\n\n".join(buf))
                buf = []
                bufLen = 0
            lineBuf: list[str] = []
            lineLen = 0
            for ln in para.split("\n"):
                if lineLen + len(ln) + 1 > maxBytes and lineBuf:
                    parts.append("\n".join(lineBuf))
                    lineBuf = []
                    lineLen = 0
                lineBuf.append(ln)
                lineLen += len(ln) + 1
            if lineBuf:
                parts.append("\n".join(lineBuf))
            continue
        if bufLen + pLen + 2 > maxBytes and buf:
            parts.append("\n\n".join(buf))
            buf = []
            bufLen = 0
        buf.append(para)
        bufLen += pLen + 2
    if buf:
        parts.append("\n\n".join(buf))
    return parts


__all__ = ["parseSectionsByTitle", "splitLargeContent", "MAX_CELL_BYTES"]
