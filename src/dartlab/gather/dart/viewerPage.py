"""DART viewer index와 section HTML을 해석하는 gather-owned parser."""

from __future__ import annotations

import html as htmlModule
import re
from dataclasses import dataclass
from urllib.parse import urlencode

from lxml import html as lxmlHtml
from lxml.etree import ParserError
from lxml.html import HtmlElement

from dartlab.core.htmlMarkdown import lxmlTableToMarkdown

from .types import ViewerPageParseError

DART_MAIN_BASE = "https://dart.fss.or.kr/dsaf001/main.do"
DART_VIEWER_BASE = "https://dart.fss.or.kr/report/viewer.do"

_NODE_KEYS = "text|id|rcpNo|dcmNo|eleId|offset|length|dtd|tocNo"
_JS_LITERAL_PATTERN = r"""(?:"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')"""
_NODE_ASSIGNMENT_RE = re.compile(
    rf"""
    (?P<node>node[12])\s*
    \[\s*['"](?P<key>{_NODE_KEYS})['"]\s*\]\s*=\s*
    (?P<value>{_JS_LITERAL_PATTERN}|\d+)\s*;
    """,
    re.VERBOSE,
)
_NODE_TEXT_MARKER_RE = re.compile(r"""node[12]\s*\[\s*['"]text['"]\s*\]""")
_SINGLE_PAGE_RE = re.compile(
    rf"""
    \bviewDoc\s*\(\s*
    (?P<rcpNo>{_JS_LITERAL_PATTERN})\s*,\s*
    (?P<dcmNo>{_JS_LITERAL_PATTERN})\s*,\s*
    (?P<eleId>{_JS_LITERAL_PATTERN})\s*,\s*
    (?P<offset>{_JS_LITERAL_PATTERN})\s*,\s*
    (?P<length>{_JS_LITERAL_PATTERN})\s*,\s*
    (?P<dtd>{_JS_LITERAL_PATTERN})
    \s*(?:,\s*{_JS_LITERAL_PATTERN})?\s*\)
    """,
    re.VERBOSE,
)
_DIRECT_VIEW_DOC_MARKER_RE = re.compile(r"""\bviewDoc\s*\(\s*['"]""")
_WHITESPACE_RE = re.compile(r"[^\S\r\n]+")
_REMOVABLE_TAGS = ("script", "style", "meta", "link", "header", "footer", "nav", "noscript")


@dataclass(frozen=True, slots=True)
class ViewerSubDocument:
    """DART viewer section 위치와 표시 제목."""

    title: str
    url: str
    order: int
    rceptNo: str


def _decodeJsLiteral(token: str) -> str:
    if len(token) < 2 or token[0] not in {'"', "'"} or token[-1] != token[0]:
        raise ViewerPageParseError(f"잘못된 JavaScript 문자열 literal: {token!r}")
    quote = token[0]

    body = token[1:-1]
    decoded: list[str] = []
    index = 0
    escapes = {
        '"': '"',
        "'": "'",
        "\\": "\\",
        "/": "/",
        "b": "\b",
        "f": "\f",
        "n": "\n",
        "r": "\r",
        "t": "\t",
    }
    while index < len(body):
        char = body[index]
        if char != "\\":
            decoded.append(char)
            index += 1
            continue
        if index + 1 >= len(body):
            raise ViewerPageParseError(f"끝나지 않은 JavaScript escape: {token!r}")
        escape = body[index + 1]
        if escape in escapes:
            decoded.append(escapes[escape])
            index += 2
            continue
        if escape in {"u", "x"}:
            width = 4 if escape == "u" else 2
            encoded = body[index + 2 : index + 2 + width]
            if len(encoded) != width or not all(char in "0123456789abcdefABCDEF" for char in encoded):
                raise ViewerPageParseError(f"잘못된 JavaScript unicode escape: {token!r}")
            decoded.append(chr(int(encoded, 16)))
            index += width + 2
            continue
        raise ViewerPageParseError(f"지원하지 않는 JavaScript escape: \\{escape}")
    return "".join(decoded)


def _decodeAssignmentValue(token: str) -> str:
    return _decodeJsLiteral(token) if token[0] in {'"', "'"} else token


def _extractNodeRecords(content: str) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    current: dict[str, str] | None = None

    for match in _NODE_ASSIGNMENT_RE.finditer(content):
        node = match.group("node")
        key = match.group("key")
        value = _decodeAssignmentValue(match.group("value"))
        if key == "text":
            if current is not None:
                records.append(current)
            current = {"_node": node, "text": value}
            continue
        if current is None:
            raise ViewerPageParseError(f"{node} 레코드의 text보다 {key}가 먼저 선언됐습니다")
        if current["_node"] != node:
            raise ViewerPageParseError(f"{current['_node']} 레코드 도중 text 없는 {node}.{key} 선언이 나타났습니다")
        if key in current:
            raise ViewerPageParseError(f"{node} 레코드에 {key}가 중복 선언됐습니다")
        current[key] = value

    if current is not None:
        records.append(current)
    return records


def _requireDigits(record: dict[str, str], key: str, *, recordIndex: int) -> str:
    value = record[key]
    if not value.isdigit():
        raise ViewerPageParseError(f"viewer 레코드 {recordIndex}의 {key}가 숫자가 아닙니다: {value!r}")
    return value


def _toSubDocument(
    record: dict[str, str],
    *,
    rceptNo: str,
    recordIndex: int,
) -> ViewerSubDocument:
    required = {"text", "rcpNo", "dcmNo", "eleId", "offset", "length", "dtd"}
    missing = sorted(required.difference(record))
    if missing:
        raise ViewerPageParseError(f"viewer 레코드 {recordIndex}에 필수 필드가 없습니다: {', '.join(missing)}")

    embeddedRceptNo = _requireDigits(record, "rcpNo", recordIndex=recordIndex)
    if embeddedRceptNo != rceptNo:
        raise ViewerPageParseError(f"viewer 응답 접수번호가 요청과 다릅니다: 요청={rceptNo}, 응답={embeddedRceptNo}")

    params = {
        "rcpNo": embeddedRceptNo,
        "dcmNo": _requireDigits(record, "dcmNo", recordIndex=recordIndex),
        "eleId": _requireDigits(record, "eleId", recordIndex=recordIndex),
        "offset": _requireDigits(record, "offset", recordIndex=recordIndex),
        "length": _requireDigits(record, "length", recordIndex=recordIndex),
        "dtd": record["dtd"],
    }
    if not params["dtd"]:
        raise ViewerPageParseError(f"viewer 레코드 {recordIndex}의 dtd가 비었습니다")

    return ViewerSubDocument(
        title=htmlModule.unescape(record["text"]).strip(),
        url=f"{DART_VIEWER_BASE}?{urlencode(params)}",
        order=recordIndex,
        rceptNo=rceptNo,
    )


def _parseSinglePage(content: str, rceptNo: str) -> ViewerSubDocument | None:
    match = _SINGLE_PAGE_RE.search(content)
    if match is None:
        return None
    record = {key: _decodeJsLiteral(value) for key, value in match.groupdict().items()}
    record["text"] = ""

    root = _parseHtmlRoot(content)
    titles = root.xpath("//title//text()")
    if titles:
        record["text"] = " ".join(str(value) for value in titles).strip()
    return _toSubDocument(record, rceptNo=rceptNo, recordIndex=0)


def _parseHtmlRoot(content: str) -> HtmlElement:
    try:
        return lxmlHtml.fromstring(content)
    except (ParserError, TypeError, ValueError) as exc:
        raise ViewerPageParseError("DART viewer HTML tree를 구성하지 못했습니다") from exc


def _replaceElementWithText(element: HtmlElement, replacement: str) -> None:
    parent = element.getparent()
    if parent is None:
        element.clear()
        element.text = replacement
        return

    combined = replacement + (element.tail or "")
    previous = element.getprevious()
    if previous is None:
        parent.text = (parent.text or "") + combined
    else:
        previous.tail = (previous.tail or "") + combined
    parent.remove(element)


def _dropElement(element: HtmlElement) -> None:
    parent = element.getparent()
    if parent is None:
        element.clear()
        return
    element.drop_tree()


def parseSubDocs(content: str, rceptNo: str) -> list[ViewerSubDocument]:
    """DART viewer index HTML에서 strict section 메타를 추출한다.

    Capabilities:
        node1/node2 assignment와 단일 ``viewDoc`` 호출을 따옴표 및 공백 변형에 관계없이
        해석하고, HTTPS viewer URL을 안전하게 조립한다.
    AIContext:
        접수번호 하나를 원문 section 목록으로 바꾸는 DART gather 내부 경계다.
    Guide:
        section이 실제로 없는 페이지는 빈 목록이다. 구조 흔적이 있는데 필드가 손상됐거나
        접수번호가 다르면 ``ViewerPageParseError``를 발생시킨다.
    When:
        DART viewer index 응답을 section별 URL과 제목으로 바꿀 때.
    How:
        bounded assignment tokenizer로 node 레코드를 모으고 필수 필드와 접수번호를 검증한
        뒤 HTTPS URL을 조립한다.
    Requires:
        ``content``는 디코딩된 viewer index HTML이고 ``rceptNo``는 검증된 접수번호다.
    SeeAlso:
        ``htmlToText``는 반환된 section URL의 본문을 evidence text로 바꾼다.

    Args:
        content: 디코딩된 DART viewer index HTML.
        rceptNo: 요청한 14자리 접수번호.

    Returns:
        viewer section 순서대로 정렬된 ``ViewerSubDocument`` 목록.

    Example:
        >>> parseSubDocs("<html></html>", "20240315000123")
        []

    Raises:
        TypeError: 입력 타입이 문자열이 아닌 경우.
        ViewerPageParseError: viewer 구조가 손상됐거나 요청과 응답이 불일치한 경우.
    """
    if not isinstance(content, str) or not isinstance(rceptNo, str):
        raise TypeError("content와 rceptNo는 문자열이어야 합니다")

    records = _extractNodeRecords(content)
    if records:
        return [_toSubDocument(record, rceptNo=rceptNo, recordIndex=index) for index, record in enumerate(records)]

    singlePage = _parseSinglePage(content, rceptNo)
    if singlePage is not None:
        return [singlePage]

    if _NODE_TEXT_MARKER_RE.search(content) or _DIRECT_VIEW_DOC_MARKER_RE.search(content):
        raise ViewerPageParseError("viewer 구조 흔적은 있지만 지원되는 section 메타를 해석하지 못했습니다")
    return []


def htmlToText(html: str) -> str:
    """DART section HTML을 표 보존 text로 정규화한다.

    Capabilities:
        실행 태그와 chrome을 제거하고, 최상위 표는 공용 markdown SSOT로 바꾸며, inline
        단어 경계와 block 줄 경계를 보존한다.
    AIContext:
        외부 DART 원문을 검색 및 인용 가능한 textual evidence로 만드는 parser다.
    Guide:
        빈 HTML은 빈 문자열이다. 표 span이 안전 범위를 벗어나면 원인 예외를 숨기지 않는다.
    When:
        DART viewer section 응답을 검색, 인용, DataFrame 저장용 text로 바꿀 때.
    How:
        lxml tree에서 실행 요소를 제거하고 최상위 표를 공용 bounded markdown으로 교체한
        뒤 block과 inline 공백을 정규화한다.
    Requires:
        ``html``은 디코딩된 문자열이고 lxml HTML parser를 사용할 수 있어야 한다.
    SeeAlso:
        ``parseSubDocs``는 section URL과 제목을 추출한다.

    Args:
        html: 디코딩된 DART section HTML.

    Returns:
        block 줄 경계와 markdown 표를 보존한 정규화 text.

    Example:
        >>> htmlToText("<p>매출 증가</p>")
        '매출 증가'

    Raises:
        TypeError: 입력이 문자열이 아닌 경우.
        HtmlTableShapeError: 표가 안전한 markdown grid 한계를 벗어난 경우.
    """
    if not isinstance(html, str):
        raise TypeError("html은 문자열이어야 합니다")
    if not html.strip():
        return ""

    root = _parseHtmlRoot(html)
    for tagName in _REMOVABLE_TAGS:
        for element in list(root.iter(tagName)):
            _dropElement(element)

    tables = [element for element in root.iter("table") if next(element.iterancestors("table"), None) is None]
    for table in tables:
        markdown = lxmlTableToMarkdown(table)
        if markdown:
            _replaceElementWithText(table, f"\n{markdown}\n")
        else:
            _replaceElementWithText(table, "")

    for lineBreak in list(root.iter("br")):
        _replaceElementWithText(lineBreak, "\n")
    for tagName in ("p", "div", "li", "h1", "h2", "h3", "h4"):
        for block in root.iter(tagName):
            block.tail = "\n" + (block.tail or "")

    text = root.text_content()
    lines = [_WHITESPACE_RE.sub(" ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line).strip()
