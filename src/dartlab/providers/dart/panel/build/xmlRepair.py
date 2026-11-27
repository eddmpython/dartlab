"""DART 본문 XML 의 흔한 깨짐을 lxml 이 읽기 전에 고친다.

DART 원문은 글자로 쓴 꺾쇠(``<신 설>``, ``<CE 부문 주요 제품>``, ``<HYOSUNG>``), 엔티티가
아닌 ``&`` (``S&P``, ``R&D``), 속성 값의 겹친 따옴표(``ENG=""Other ..."``,
``ENG="...income""``)와 값 가운데 따옴표(``ENG="Total of "Accumulated ... tax ""``)를 그대로
담는다. ``recover=True`` 파서는 글자 꺾쇠를 요소로 읽고 따옴표가 어긋난 시작 태그를 잃어 태그
짝이 어긋나며, 그 뒤의 장(II~XII)이 앞 장 안으로 들어가거나 문서 끝까지 버려진다(실측 000150
2024 사업보고서: 별도 재무제표 주석 표의 값 가운데 따옴표 뒤로 IV~XII 장이 모두 빠짐).
``&`` 뒤 글자는 조용히 빠진다.

DART 태그는 대문자 이름과 대문자 속성(``DOCUMENT`` 의 ``xmlns:xsi``·``xsi:*`` 만 예외)을
쓰고, 한 문서 안에서 여는 태그와 닫는 태그의 수가 늘 같다(실측: 2015~2026 원문 zip 20 개의
태그 이름 40 개 모두 여는 수 == 닫는 수, 스스로 닫는 태그 0 개). 그래서 두 가지 ``<`` 만
글자로 바꾸고 진짜 태그는 건드리지 않는다.

1. 태그 꼴이 아닌 ``<`` (한글·소문자 이름, 대문자 속성이 아닌 뒷글자).
2. 따옴표를 고친 뒤 부모가 닫힐 때까지 닫히지 않은 여는 ``<`` 와 열린 짝이 없는 닫는 ``<``
   (``<HYOSUNG>``, ``<GS SHOP>``, 진짜 ``<A REFNO=...>`` 가 있는 문서의 글자 ``<A>``, 실측
   000390). 스스로 닫는 ``<NAME/>`` 와 끝이 잘린 문서에서 끝까지 열린 태그는 남긴다.
"""

from __future__ import annotations

import re

# 태그로 남길 '<' 꼴: 주석·선언(<!, <?), 닫는 태그(</NAME>), 여는 태그(<NAME>, <NAME/>,
# <NAME ATTR=...). 이 꼴이 아닌 '<' 는 글자다.
_STRAY_LT = re.compile(
    r"<(?!"
    r"[!?]"
    r"|/[A-Z][A-Z0-9\-]*\s*>"
    r"|[A-Z][A-Z0-9\-]*(?:\s*/?>|\s+(?:[A-Z][A-Z0-9\-]*|xmlns:\w+|xsi:\w+)\s*(?:=|/?>|\s)))"
)
# ENG=""Other receivables" 와 ENG=""...income"" -> ENG="..." (값에 '=' 가 없을 때만, 빈 값 ENG="" 는 둔다)
_LEADING_DOUBLED_QUOTE = re.compile(r'(\s[A-Z][A-Z0-9\-]*)=""([^"<>=]+)""?(?=[\s/>])')
# ENG="...income"" -> ENG="...income"
_TRAILING_DOUBLED_QUOTE = re.compile(r'(\s[A-Z][A-Z0-9\-]*="[^"<>]*)""(?=[\s/>])')
# 속성이 있는 시작 태그 하나(값 안에 '<' '>' 가 없는 꼴만)와 그 안의 속성 시작(NAME=")
_ATTR_TAG = re.compile(r"<[A-Z][A-Z0-9\-]*\s[^<>]*>")
_ATTR_START = re.compile(r'\s(?:[A-Z][A-Z0-9\-]*|xmlns:\w+|xsi:\w+)="')
_TAG_END = re.compile(r"\s*/?>$")
# 이름 엔티티(&amp; &cr;)와 숫자 엔티티(&#123; &#x1F;)가 아닌 '&'
_BARE_AMP = re.compile(r"&(?!(?:[A-Za-z][A-Za-z0-9]*|#[0-9]+|#x[0-9A-Fa-f]+);)")
# 태그 짝을 맞춰 볼 토큰: 주석·CDATA·선언(건너뜀), 닫는 태그(1), 여는 태그 이름(2)과 스스로 닫는 표시(3)
_TAG_TOKEN = re.compile(
    r"<!--.*?-->|<!\[CDATA\[.*?\]\]>|<[!?][^>]*>"
    r"|</([A-Z][A-Z0-9\-]*)\s*>"
    r"|<([A-Z][A-Z0-9\-]*)(?=[\s/>])[^<>]*?(/?)>",
    re.S,
)


def _escapeInnerQuotes(tag: re.Match[str]) -> str:
    """시작 태그 하나의 속성 값 가운데 따옴표를 ``&quot;`` 로 바꾼다.

    속성 값은 ``NAME="`` 뒤에서 시작해 다음 ``NAME="`` (또는 태그 끝 ``>``, ``/>``) 바로 앞의
    마지막 ``"`` 에서 끝난다고 본다. 그 사이의 다른 ``"`` 는 값의 글자다.

    Args:
        tag: ``_ATTR_TAG`` 가 찾은 시작 태그 하나.

    Returns:
        값 가운데 따옴표를 ``&quot;`` 로 바꾼 태그 문자열. 따옴표 수가 속성 수의 두 배이거나,
        어느 값이 ``"`` 로 끝나지 않아 경계를 정할 수 없으면 입력 그대로다.

    Raises:
        없음. 문자열 자르기만 한다.

    Example:
        >>> _escapeInnerQuotes(_ATTR_TAG.match('<TH ENG="Total of "OCI"" WIDTH="1">'))
        '<TH ENG="Total of &quot;OCI&quot;" WIDTH="1">'
    """

    text = tag.group(0)
    starts = list(_ATTR_START.finditer(text))
    if not starts or text.count('"') == 2 * len(starts):
        return text
    end = _TAG_END.search(text)
    tail = end.start() if end else len(text)
    pieces = [text[: starts[0].end()]]
    for i, start in enumerate(starts):
        stop = starts[i + 1].start() if i + 1 < len(starts) else tail
        value = text[start.end() : stop]
        core = value.rstrip()
        if not core.endswith('"'):
            return text
        pieces.append(core[:-1].replace('"', "&quot;") + '"' + value[len(core) :])
        if i + 1 < len(starts):
            pieces.append(text[stop : starts[i + 1].end()])
    pieces.append(text[tail:])
    return "".join(pieces)


def _escapeUnbalancedTags(xml: str) -> str:
    """제 부모가 닫힐 때까지 닫히지 않은 여는 태그와 짝 없는 닫는 태그의 ``<`` 를 ``&lt;`` 로 바꾼다.

    DART 문서는 태그 짝이 늘 맞으므로, 부모의 닫는 태그가 올 때 아직 열려 있는 태그는 글자로
    쓴 꺾쇠다(실측 000390 2023 1분기 보고서의 ``TP FLEX BLACK<A>#(KJ)``: 같은 문서에 진짜
    ``<A REFNO=...>...</A>`` 가 있어 이름만으로는 가를 수 없다). recover 파서는 짝이 어긋난 닫는
    태그마다 지금 요소를 하나씩 닫아, 그 뒤 장이 앞 장 안으로 들어가거나 버려진다. 문서 끝까지
    열린 태그는 끝이 잘린 문서의 진짜 구조(``DOCUMENT``, ``BODY``, 마지막 장)이므로 남긴다.
    recover 파서가 끝에서 닫아 앞 장을 살린다.

    Args:
        xml: 따옴표 수리를 마친 문서 전체 문자열.

    Returns:
        제 자리에서 닫히지 않는 여는 태그와 열린 짝이 없는 닫는 태그의 ``<`` 를 글자로 바꾼
        문자열. 태그 짝이 모두 맞거나 문서 끝에서만 열려 있으면 입력 그대로다.

    Raises:
        없음. 문자열 훑기만 한다.

    Example:
        >>> _escapeUnbalancedTags('<TD>BLACK<A>#(KJ)</TD><A REFNO="1">참조</A>')
        '<TD>BLACK&lt;A>#(KJ)</TD><A REFNO="1">참조</A>'
    """

    stack: list[tuple[str, int]] = []
    textAt: list[int] = []
    for token in _TAG_TOKEN.finditer(xml):
        close, name, selfClose = token.group(1), token.group(2), token.group(3)
        if name:
            if not selfClose:
                stack.append((name, token.start()))
            continue
        if not close:
            continue
        for depth in range(len(stack) - 1, -1, -1):
            if stack[depth][0] == close:
                textAt.extend(pos for _, pos in stack[depth + 1 :])
                del stack[depth:]
                break
        else:
            textAt.append(token.start())
    if not textAt:
        return xml
    pieces: list[str] = []
    last = 0
    for pos in sorted(textAt):
        pieces.append(xml[last:pos])
        pieces.append("&lt;")
        last = pos + 1
    pieces.append(xml[last:])
    return "".join(pieces)


def repairDartXml(xml: str) -> str:
    """DART 본문 XML 의 글자 꺾쇠, 겹친 따옴표, 값 가운데 따옴표, 알몸 ``&`` 를 고친 문자열을 돌려준다.

    Args:
        xml: zip 에서 decode 한 DART 본문 XML 문서 전체 문자열. 닫는 태그 짝을 문서 안에서
            찾으므로 조각이 아니라 문서 전체를 넘긴다.

    Returns:
        같은 문서를 lxml 이 태그 짝을 잃지 않고 읽을 수 있게 고친 문자열. 진짜 태그와
        엔티티는 그대로 두고, 고칠 곳이 없으면 입력과 같은 문자열이다. 두 번 고쳐도 같다.

    Raises:
        없음. 정규식 치환만 한다.

    Example:
        >>> repairDartXml('<TD>정관 <신 설></TD>')
        '<TD>정관 &lt;신 설></TD>'
        >>> repairDartXml('<TH ENG=""Other receivables" WIDTH="1">S&P</TH>')
        '<TH ENG="Other receivables" WIDTH="1">S&amp;P</TH>'
        >>> repairDartXml('<TH ENG="Total of "OCI"" WIDTH="1"></TH>')
        '<TH ENG="Total of &quot;OCI&quot;" WIDTH="1"></TH>'
        >>> repairDartXml('<TD>BLACK<A>#(KJ)</TD><A REFNO="1">참조</A>')
        '<TD>BLACK&lt;A>#(KJ)</TD><A REFNO="1">참조</A>'
    """

    fixed = _STRAY_LT.sub("&lt;", xml)
    fixed = _LEADING_DOUBLED_QUOTE.sub(r'\1="\2"', fixed)
    fixed = _TRAILING_DOUBLED_QUOTE.sub(r'\1"', fixed)
    fixed = _ATTR_TAG.sub(_escapeInnerQuotes, fixed)
    return _escapeUnbalancedTags(_BARE_AMP.sub("&amp;", fixed))


__all__ = ["repairDartXml"]
