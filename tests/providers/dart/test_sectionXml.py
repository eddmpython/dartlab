"""DART 구간 XML 변환 회귀.

`sectionXml` 은 panel 빌드 진입점(`_DartBuildProvider.xmlChunkToMixed`)이 그대로
호출하는데 테스트가 하나도 없었다. 여기 고정하는 것은 무엇이 살아남고 무엇이 버려지는지
그 경계다. 본문이 조용히 사라지면 그 구간은 빈 채로 패널에 실린다.

문서와 실제가 어긋나던 두 곳도 함께 못 박는다. 1x1 표는 문단 프레임이라 HTML 이 아니라
평문이 되고, 깨진 XML 은 원문 그대로가 아니라 lxml 이 건져낸 조각이 된다.
"""

from __future__ import annotations

from dartlab.providers.dart.sectionXml import (
    stripTagsFromCell,
    xmlChunkToMixed,
    xmlChunkToPlain,
)

_REAL_TABLE = (
    '<P>본문</P><TABLE BORDER="1">'
    "<TR><TH>항목</TH><TH>금액</TH></TR>"
    '<TR><TD ALIGN="RIGHT">매출</TD><TD>1,000</TD></TR>'
    "</TABLE>"
)


def testRealTableBecomesHtmlWithAlignmentPreserved() -> None:
    """진짜 데이터 표는 HTML 로 나가고 원본 정렬이 보존된다.

    정렬이 빠지면 뷰어에서 숫자 열이 전부 좌측정렬로 돌아간다. 실제로 그 회귀가 한 번
    있었다.
    """

    result = xmlChunkToMixed(_REAL_TABLE)

    assert result.startswith("본문\n\n<table>")
    assert "<tr><th>항목</th><th>금액</th></tr>" in result
    assert '<td align="right">매출</td>' in result
    assert result.endswith("</table>")


def testSingleCellTableStaysPlainTextBecauseItIsParagraphFraming() -> None:
    """1x1 표는 시각적 문단 틀이지 데이터 표가 아니다. 표로 만들면 노이즈가 된다."""

    result = xmlChunkToMixed('<TABLE BORDER="1"><TR><TD>본문 한 줄</TD></TR></TABLE>')

    assert result == "본문 한 줄"
    assert "<table>" not in result


def testBorderlessMultiCellTableJoinsAsCaptionLines() -> None:
    """테두리 없는 표는 캡션 배치용이라 줄 단위 평문으로 편다.

    셀 사이 구분자는 일반 공백이 아니라 em-space 다. 원본의 칸 간격을 눈으로 살리려는
    선택이라 평범한 공백으로 바뀌면 캡션 정렬이 달라진다.
    """

    result = xmlChunkToMixed('<TABLE BORDER="0"><TR><TD>단위</TD><TD>백만원</TD></TR></TABLE>')

    assert result == "단위 백만원"
    assert "<table>" not in result


def testBoldSpanBecomesHeading() -> None:
    """굵은 SPAN 은 구간 제목이라 heading 으로 올린다."""

    assert xmlChunkToMixed('<SPAN USERMARK="B">제목</SPAN>') == "## 제목"


def testBlankInputProducesEmptyString() -> None:
    """빈 입력은 빈 결과다."""

    assert xmlChunkToMixed("") == ""
    assert xmlChunkToMixed("   ") == ""


def testMalformedXmlKeepsWhatTheParserCanSalvage() -> None:
    """복구 파서를 쓰므로 원문 그대로가 아니라 건져낸 조각이 남는다.

    docstring 은 오랫동안 "parse 실패 시 raw 그대로" 라고 적어 두었지만 `recover=True`
    라 파서가 예외를 올리지 않아 그 경로는 실행되지 않는다.
    """

    assert xmlChunkToMixed("<P>앞</P><TABLE><TR><TD>안닫힘") == "앞안닫힘"


def testUntaggedTextIsDropped() -> None:
    """태그 없는 알몸 텍스트는 살아남지 못한다.

    변환기는 요소 단위로만 훑기 때문에 BODY 직속 텍스트 노드는 어디에도 실리지 않는다.
    입력이 항상 태그된 chunk 라는 전제 위에 서 있다는 뜻이라, 그 전제가 깨지면 본문이
    조용히 사라진다. 지금 동작을 그대로 못 박아 두어 바뀌면 눈에 띄게 한다.
    """

    assert xmlChunkToMixed("그냥 평문") == ""


def testPlainConversionDropsAllMarkupButKeepsOrder() -> None:
    """평문 변환은 태그를 버리되 등장 순서를 지킨다."""

    assert xmlChunkToPlain("<P>가</P><P>나</P>") == "가\n\n나"


def testStripTagsFromCellHandlesMarkupAndMissingValues() -> None:
    """셀 값은 태그를 벗기고, 값이 없으면 빈 문자열이 된다."""

    assert stripTagsFromCell("<b>값</b>") == "값"
    assert stripTagsFromCell(None) == ""
    assert stripTagsFromCell("") == ""
