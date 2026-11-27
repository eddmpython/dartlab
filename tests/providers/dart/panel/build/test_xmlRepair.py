"""``providers/dart/panel/build/xmlRepair.py`` 의 DART 본문 XML 수리 계약.

DART 원문의 글자 꺾쇠(``<신 설>``, 진짜 태그와 이름이 같은 ``<A>``), 겹친 따옴표
(``ENG=""Other ..."``), 값 가운데 따옴표(``ENG="Total of "Accumulated ..."``), 알몸 ``&`` 가
lxml recover 파서에서 태그 짝을 어긋나게 해 뒤 장(II~XII)이 앞 장 표 한 칸에 묻히거나 빠지던
결함의 회귀를 막는다 (실측 005380·051910·035420·000150·000390 보고서).
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit

# 글자 꺾쇠가 표 칸에 있는 두 장짜리 사업보고서 꼴.
_BURIED = (
    "<DOCUMENT><BODY>"
    "<SECTION-1><TITLE>I. 회사의 개요</TITLE>"
    "<TABLE><TBODY><TR><TD>제2조 <신 설></TD><TD><CE 부문 주요 제품></TD></TR></TBODY></TABLE>"
    "</SECTION-1>"
    "<SECTION-1><TITLE>II. 사업의 내용</TITLE><P>본문</P></SECTION-1>"
    "</BODY></DOCUMENT>"
)


def _misplacedSections(xml: str) -> tuple[int, int]:
    """recover 파서로 읽은 SECTION-1 수와 그 가운데 BODY 바로 아래가 아닌(앞 장에 묻힌) 수를 돌려준다."""

    from lxml import etree

    parser = etree.XMLParser(recover=True, huge_tree=True)
    root = etree.fromstring(xml.encode("utf-8"), parser)
    sections = root.findall(".//SECTION-1")
    buried = sum(1 for s in sections if s.getparent().tag != "BODY")
    return len(sections), buried


def test_stray_angle_brackets_become_text_and_chapters_stay_at_body_level() -> None:
    """글자 꺾쇠는 &lt; 로 바뀌고, 뒤 장이 앞 장 안에 묻히지 않는다."""

    from dartlab.providers.dart.panel.build.xmlRepair import repairDartXml

    assert _misplacedSections(_BURIED)[1] > 0, "수리 전 문서가 장 묻힘을 재현해야 시험이 뜻을 가진다"

    fixed = repairDartXml(_BURIED)

    assert "제2조 &lt;신 설>" in fixed
    assert "&lt;CE 부문 주요 제품>" in fixed
    assert _misplacedSections(fixed) == (2, 0)


def test_buried_chapter_is_found_by_walker_after_repair() -> None:
    """수리한 문서에서 walker 가 II 장을 제 장으로 읽는다."""

    from lxml import etree

    from dartlab.providers.dart.panel.build import walkSections
    from dartlab.providers.dart.panel.build.xmlRepair import repairDartXml

    def chapters(xml: str) -> set[str]:
        """recover 파서로 읽은 문서에서 walker 가 낸 장 이름 집합."""

        parser = etree.XMLParser(recover=True, huge_tree=True)
        root = etree.fromstring(xml.encode("utf-8"), parser)
        return {str(row["chapter"]) for row in walkSections(root, "v2")}

    assert "II. 사업의 내용" not in chapters(_BURIED)
    assert chapters(repairDartXml(_BURIED)) == {"I. 회사의 개요", "II. 사업의 내용"}


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ('<TH ENG=""Other receivables" WIDTH="1"></TH>', '<TH ENG="Other receivables" WIDTH="1"></TH>'),
        ('<TH ENG="Other income"" WIDTH="1"></TH>', '<TH ENG="Other income" WIDTH="1"></TH>'),
        ('<TH ENG=""Gain income""></TH>', '<TH ENG="Gain income"></TH>'),
        ('<TH ENG=""Gain income""/>', '<TH ENG="Gain income"/>'),
        ('<TD ENG="" WIDTH="1"></TD>', '<TD ENG="" WIDTH="1"></TD>'),
    ],
)
def test_doubled_attribute_quotes_are_fixed_and_empty_values_kept(raw: str, expected: str) -> None:
    """속성 값의 앞·뒤·앞뒤 겹친 따옴표를 고치고 빈 값 ENG="" 는 둔다."""

    from dartlab.providers.dart.panel.build.xmlRepair import repairDartXml

    assert repairDartXml(raw) == expected


# 재무제표 주석 표 머리 칸의 영어 이름 값 가운데 따옴표 뒤로 다음 장이 오는 꼴 (실측 000150 2024
# 사업보고서). 그런 시작 태그 하나는 recover 가 견디고, 둘이면 조상 태그가 모두 닫혀 IV 장이 버려진다.
_INNER_TH = (
    '<TH ENG="Total of "Accumulated other comprehensive  income After income tax "" WIDTH="141"><P>합계</P></TH>'
)
_INNER_QUOTED = (
    "<DOCUMENT><BODY>"
    "<SECTION-1><TITLE>III. 재무에 관한 사항</TITLE><SECTION-2><TITLE>5. 재무제표 주석</TITLE>"
    f"<TABLE><THEAD><TR>{_INNER_TH}{_INNER_TH}</TR></THEAD><TBODY><TR><TD>1</TD></TR></TBODY></TABLE>"
    "</SECTION-2></SECTION-1>"
    "<SECTION-1><TITLE>IV. 이사의 경영진단 및 분석의견</TITLE><P>본문</P></SECTION-1>"
    "</BODY></DOCUMENT>"
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (
            '<TH ENG="Total of "Accumulated income After tax "" WIDTH="141" HEIGHT="76"></TH>',
            '<TH ENG="Total of &quot;Accumulated income After tax &quot;" WIDTH="141" HEIGHT="76"></TH>',
        ),
        ('<TH ENG="Gain on "FVOCI" assets" ROWSPAN="2"/>', '<TH ENG="Gain on &quot;FVOCI&quot; assets" ROWSPAN="2"/>'),
        ('<TD ENG="a "b""  WIDTH="1"></TD>', '<TD ENG="a &quot;b&quot;"  WIDTH="1"></TD>'),
        ('<TD ENG="a > "b"" WIDTH="1"></TD>', '<TD ENG="a > "b"" WIDTH="1"></TD>'),
    ],
)
def test_inner_attribute_quotes_become_entities(raw: str, expected: str) -> None:
    """속성 값 가운데 따옴표는 &quot; 가 되고, 값 경계를 정할 수 없는 태그는 그대로다."""

    from dartlab.providers.dart.panel.build.xmlRepair import repairDartXml

    assert repairDartXml(raw) == expected


def test_chapter_after_inner_quoted_attribute_is_kept() -> None:
    """값 가운데 따옴표가 있는 표 뒤의 IV 장을 수리한 문서에서 walker 가 제 장으로 읽는다."""

    from lxml import etree

    from dartlab.providers.dart.panel.build import walkSections
    from dartlab.providers.dart.panel.build.xmlRepair import repairDartXml

    def chapters(xml: str) -> set[str]:
        """recover 파서로 읽은 문서에서 walker 가 낸 장 이름 집합."""

        parser = etree.XMLParser(recover=True, huge_tree=True)
        root = etree.fromstring(xml.encode("utf-8"), parser)
        return {str(row["chapter"]) for row in walkSections(root, "v2")}

    assert "IV. 이사의 경영진단 및 분석의견" not in chapters(_INNER_QUOTED), (
        "수리 전 문서가 장 빠짐을 재현해야 시험이 뜻을 가진다"
    )
    assert chapters(repairDartXml(_INNER_QUOTED)) == {"III. 재무에 관한 사항", "IV. 이사의 경영진단 및 분석의견"}


# 제품 이름 칸에 글자로 쓴 <A> 가 같은 문서의 진짜 <A REFNO=...> 와 이름이 같은 꼴 (실측 000390
# 2023 1분기 보고서: 이 칸 뒤로 III~XII 장이 빠짐).
_TEXT_A = (
    "<DOCUMENT><BODY>"
    "<SECTION-1><TITLE>I. 회사의 개요</TITLE>"
    '<P><A REFNO="XII. 상세표|NEF-001">상세표 참조</A></P>'
    "<SECTION-2><TITLE>1. 제품</TITLE><TABLE><TBODY><TR>"
    "<TD>TP FLEX BLACK<A>#(KJ)SH22-3436K<A>#(RE.3)SH22-2410W<A>#(BC1)</TD>"
    "</TR></TBODY></TABLE></SECTION-2></SECTION-1>"
    "<SECTION-1><TITLE>II. 사업의 내용</TITLE><P>본문</P></SECTION-1>"
    "</BODY></DOCUMENT>"
)

# 끝이 잘린 문서: DOCUMENT, BODY, 마지막 장이 열린 채 끝난다. recover 파서는 끝에서 닫아 두 장을 읽는다.
_TRUNCATED = (
    "<DOCUMENT><BODY>"
    "<SECTION-1><TITLE>I. 회사의 개요</TITLE><P>가</P></SECTION-1>"
    "<SECTION-1><TITLE>II. 사업의 내용</TITLE><P>나"
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ('<TD>BLACK<A>#(KJ)</TD><A REFNO="1">참조</A>', '<TD>BLACK&lt;A>#(KJ)</TD><A REFNO="1">참조</A>'),
        ("<P>가</B>나</P><B>굵게</B>", "<P>가&lt;/B>나</P><B>굵게</B>"),
        ("<BODY><P>가<B>굵게</P></BODY>", "<BODY><P>가&lt;B>굵게</P></BODY>"),
        ('<TD><A REFNO="1"><B>참조</B></A><BR/></TD>', '<TD><A REFNO="1"><B>참조</B></A><BR/></TD>'),
        (_TRUNCATED, _TRUNCATED),
    ],
)
def test_unbalanced_tags_become_text(raw: str, expected: str) -> None:
    """부모가 닫힐 때 열려 있는 태그와 열린 짝이 없는 닫는 태그는 글자가 되고, 짝이 맞는 태그와 끝이 잘린 문서의 열린 태그는 그대로다."""

    from dartlab.providers.dart.panel.build.xmlRepair import repairDartXml

    assert repairDartXml(raw) == expected


def test_chapter_after_text_tag_with_real_tag_name_is_kept() -> None:
    """진짜 태그와 이름이 같은 글자 꺾쇠 <A> 뒤의 II 장을 수리한 문서에서 walker 가 제 장으로 읽는다."""

    from lxml import etree

    from dartlab.providers.dart.panel.build import walkSections
    from dartlab.providers.dart.panel.build.xmlRepair import repairDartXml

    def chapters(xml: str) -> set[str]:
        """recover 파서로 읽은 문서에서 walker 가 낸 장 이름 집합."""

        parser = etree.XMLParser(recover=True, huge_tree=True)
        root = etree.fromstring(xml.encode("utf-8"), parser)
        return {str(row["chapter"]) for row in walkSections(root, "v2")}

    assert "II. 사업의 내용" not in chapters(_TEXT_A), "수리 전 문서가 장 빠짐을 재현해야 시험이 뜻을 가진다"
    fixed = repairDartXml(_TEXT_A)
    assert "TP FLEX BLACK&lt;A>#(KJ)" in fixed
    assert chapters(fixed) == {"I. 회사의 개요", "II. 사업의 내용"}
    assert chapters(repairDartXml(_TRUNCATED)) == {"I. 회사의 개요", "II. 사업의 내용"}, (
        "끝이 잘린 문서의 장을 잃지 않는다"
    )


def test_uppercase_text_brackets_without_closing_tag_become_text() -> None:
    """대문자로 쓴 글자 꺾쇠(<HYOSUNG>, <GS SHOP>)는 닫는 태그가 문서에 없어 글자가 되고, 짝이 있는 태그와 <PGBRK/> 는 남는다."""

    from dartlab.providers.dart.panel.build.xmlRepair import repairDartXml

    raw = "<P>사보 <HYOSUNG>, 뉴욕 <GS SHOP> 수상<PGBRK/></P><IB>본문</IB>"
    assert repairDartXml(raw) == "<P>사보 &lt;HYOSUNG>, 뉴욕 &lt;GS SHOP> 수상<PGBRK/></P><IB>본문</IB>"


def test_bare_ampersand_is_escaped_and_entities_are_kept() -> None:
    """S&P 의 & 는 &amp; 가 되고 이름·숫자 엔티티는 그대로다."""

    from dartlab.providers.dart.panel.build.xmlRepair import repairDartXml

    raw = "<P>S&P R&D &amp; &#123; &#x1F; &cr; A & B</P>"
    assert repairDartXml(raw) == "<P>S&amp;P R&amp;D &amp; &#123; &#x1F; &cr; A &amp; B</P>"


@pytest.mark.parametrize(
    "doc",
    [
        '<?xml version="1.0" encoding="utf-8"?>',
        "<!-- 주석 -->",
        '<DOCUMENT xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="dart4.xsd"></DOCUMENT>',
        '<TABLE-GROUP ACLASS="BS"></TABLE-GROUP>',
        "<TD/>",
        "<TD />",
        "<TD></TD >",
        "<SECTION-1></SECTION-1>",
        '<TD\nCOLSPAN="2"></TD>',
        '<TE USERMARK="F-BT14"></TE>',
        "<P></P>",
    ],
)
def test_real_dart_tags_are_untouched(doc: str) -> None:
    """DART 의 대문자 태그 꼴(선언, 주석, 네임스페이스, 줄바꿈 속성, 닫는 짝)은 바꾸지 않는다."""

    from dartlab.providers.dart.panel.build.xmlRepair import repairDartXml

    assert repairDartXml(doc) == doc


def test_repair_is_idempotent() -> None:
    """두 번 고쳐도 한 번 고친 것과 같다."""

    from dartlab.providers.dart.panel.build.xmlRepair import repairDartXml

    raw = _BURIED + _INNER_QUOTED + _TEXT_A + '<TH ENG=""Other receivables"">S&P</TH>'
    once = repairDartXml(raw)
    assert repairDartXml(once) == once


@pytest.mark.parametrize("encoding", ["utf-8", "cp949"])
def test_decode_applies_repair_for_both_encodings(encoding: str) -> None:
    """zip 본문 decode 가 utf-8·cp949 어느 쪽이든 수리를 적용한다."""

    from dartlab.providers.dart.panel.build.refScan.zipScanWorker import _decodeXmlBytes

    text = _decodeXmlBytes("<TD>제2조 <신 설> S&P</TD>".encode(encoding))
    assert text == "<TD>제2조 &lt;신 설> S&amp;P</TD>"
