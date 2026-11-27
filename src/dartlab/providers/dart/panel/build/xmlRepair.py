"""DART 본문 XML 의 흔한 깨짐을 lxml 이 읽기 전에 고친다.

DART 원문은 글자로 쓴 꺾쇠(``<신 설>``, ``<CE 부문 주요 제품>``, ``<HYOSUNG>``), 엔티티가
아닌 ``&`` (``S&P``, ``R&D``), 속성 값의 겹친 따옴표(``ENG=""Other ..."``,
``ENG="...income""``)를 그대로 담는다. ``recover=True`` 파서는 글자 꺾쇠를 요소로 읽고 겹친
따옴표에서 시작 태그를 잃어 태그 짝이 어긋나며, 그 뒤의 장(II~XII)이 앞 장 안으로 들어간다.
``&`` 뒤 글자는 조용히 빠진다.

DART 태그는 대문자 이름과 대문자 속성(``DOCUMENT`` 의 ``xmlns:xsi``·``xsi:*`` 만 예외)을
쓰고, 한 문서 안에서 여는 태그와 닫는 태그의 수가 늘 같다(실측: 2015~2026 원문 zip 20 개의
태그 이름 40 개 모두 여는 수 == 닫는 수, 스스로 닫는 태그 0 개). 그래서 두 가지 ``<`` 만
글자로 바꾸고 진짜 태그는 건드리지 않는다.

1. 태그 꼴이 아닌 ``<`` (한글·소문자 이름, 대문자 속성이 아닌 뒷글자).
2. 태그 꼴이지만 그 이름의 닫는 태그가 문서 어디에도 없는 여는 ``<`` (``<HYOSUNG>``,
   ``<GS SHOP>``). 스스로 닫는 ``<NAME/>`` 는 남긴다.
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
# 태그 꼴로 남은 여는 태그 이름과 닫는 태그 이름
_OPEN_NAME = re.compile(r"<([A-Z][A-Z0-9\-]*)(?=[\s/>])")
_CLOSE_NAME = re.compile(r"</([A-Z][A-Z0-9\-]*)\s*>")
# ENG=""Other receivables" 와 ENG=""...income"" -> ENG="..." (값에 '=' 가 없을 때만, 빈 값 ENG="" 는 둔다)
_LEADING_DOUBLED_QUOTE = re.compile(r'(\s[A-Z][A-Z0-9\-]*)=""([^"<>=]+)""?(?=[\s/>])')
# ENG="...income"" -> ENG="...income"
_TRAILING_DOUBLED_QUOTE = re.compile(r'(\s[A-Z][A-Z0-9\-]*="[^"<>]*)""(?=[\s/>])')
# 이름 엔티티(&amp; &cr;)와 숫자 엔티티(&#123; &#x1F;)가 아닌 '&'
_BARE_AMP = re.compile(r"&(?!(?:[A-Za-z][A-Za-z0-9]*|#[0-9]+|#x[0-9A-Fa-f]+);)")


def _escapeUnclosedNames(xml: str) -> str:
    """닫는 태그가 문서에 없는 대문자 이름의 여는 ``<`` 를 ``&lt;`` 로 바꾼다.

    Args:
        xml: 태그 꼴이 아닌 ``<`` 를 이미 바꾼 문서 전체 문자열.

    Returns:
        닫는 짝이 없는 이름의 여는 태그(스스로 닫는 ``<NAME/>`` 는 빼고)를 글자로 바꾼
        문자열. 그런 이름이 없으면 입력 그대로다.

    Raises:
        없음. 정규식 치환만 한다.

    Example:
        >>> _escapeUnclosedNames('<P>사보 <HYOSUNG> 수상</P>')
        '<P>사보 &lt;HYOSUNG> 수상</P>'
    """

    unclosed = set(_OPEN_NAME.findall(xml)) - set(_CLOSE_NAME.findall(xml))
    if not unclosed:
        return xml
    names = "|".join(re.escape(name) for name in sorted(unclosed, key=len, reverse=True))
    pattern = re.compile(rf"<(?=(?:{names})(?=[\s/>])(?![^<>]*/>))")
    return pattern.sub("&lt;", xml)


def repairDartXml(xml: str) -> str:
    """DART 본문 XML 의 글자 꺾쇠, 겹친 따옴표, 알몸 ``&`` 를 고친 문자열을 돌려준다.

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
    """

    fixed = _escapeUnclosedNames(_STRAY_LT.sub("&lt;", xml))
    fixed = _LEADING_DOUBLED_QUOTE.sub(r'\1="\2"', fixed)
    fixed = _TRAILING_DOUBLED_QUOTE.sub(r'\1"', fixed)
    return _BARE_AMP.sub("&amp;", fixed)


__all__ = ["repairDartXml"]
