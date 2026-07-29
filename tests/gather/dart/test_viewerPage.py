"""DART viewer page parser와 HTML text 변환 회귀."""

from __future__ import annotations

from urllib.parse import parse_qs, urlparse

import pytest

pytestmark = pytest.mark.unit


def _nodeRecord(
    *,
    node: str = "node1",
    title: str = "1. 회사의 개요",
    rceptNo: str = "20240315000123",
    dcmNo: str = "9999999",
    eleId: str = "1",
    offset: str = "0",
    length: str = "12345",
    dtd: str = "dart4.xsd",
) -> str:
    return "\n".join(
        [
            f" {node}['text'] = \"{title}\";",
            f" {node}['dtd'] = \"{dtd}\";",
            f" {node}['length'] = \"{length}\";",
            f" {node}['offset'] = \"{offset}\";",
            f" {node}['eleId'] = \"{eleId}\";",
            f" {node}['dcmNo'] = \"{dcmNo}\";",
            f" {node}['rcpNo'] = \"{rceptNo}\";",
        ]
    )


def test_htmlToText_preserves_table_markdown() -> None:
    from dartlab.gather.dart.viewerPage import htmlToText

    html = "<p>단락 1</p><table><tr><th>A</th><th>B</th></tr><tr><td>1</td><td>2</td></tr></table><p>단락 2</p>"
    text = htmlToText(html)
    assert "단락 1" in text
    assert "단락 2" in text
    assert "| A | B |" in text


def test_htmlToText_strips_script_style() -> None:
    from dartlab.gather.dart.viewerPage import htmlToText

    text = htmlToText("<script>alert(1)</script><style>p{color:red}</style><p>본문</p>")
    assert text == "본문"


def test_htmlToText_preserves_inline_word_boundary_and_angle() -> None:
    from dartlab.gather.dart.viewerPage import htmlToText

    assert htmlToText("<p><span>A</span> <span>&lt;</span> <span>B</span></p>") == "A < B"


def test_parseSubDocs_multi_page() -> None:
    from dartlab.gather.dart.viewerPage import parseSubDocs

    content = (
        " node1['text'] = \"1. 회사의 개요\";\n"
        " node1['id'] = \"01\";\n"
        " node1['rcpNo'] = \"20240315000123\";\n"
        " node1['dcmNo'] = \"9999999\";\n"
        " node1['eleId'] = \"0\";\n"
        " node1['offset'] = \"0\";\n"
        " node1['length'] = \"12345\";\n"
        " node1['dtd'] = \"dart3.xsd\";\n"
        " node1['tocNo'] = \"01\";\n"
    )

    result = parseSubDocs(content, "20240315000123")

    assert len(result) == 1
    assert result[0].title == "1. 회사의 개요"
    assert result[0].order == 0
    assert result[0].rceptNo == "20240315000123"
    assert result[0].url.startswith("https://dart.fss.or.kr/report/viewer.do?")


def test_parseSubDocs_empty_when_no_match() -> None:
    from dartlab.gather.dart.viewerPage import parseSubDocs

    assert parseSubDocs("<html><body>no nodes</body></html>", "20240315000123") == []


def test_parseSubDocs_accepts_node_order_and_node2() -> None:
    from dartlab.gather.dart.viewerPage import parseSubDocs

    content = (
        _nodeRecord(title="A&B", dtd="dart 4.xsd")
        + "\n"
        + _nodeRecord(
            node="node2",
            title="두 번째",
            eleId="2",
            offset="123",
            length="456",
        )
    )

    result = parseSubDocs(content, "20240315000123")

    assert [item.order for item in result] == [0, 1]
    assert [item.title for item in result] == ["A&B", "두 번째"]
    assert parse_qs(urlparse(result[0].url).query) == {
        "rcpNo": ["20240315000123"],
        "dcmNo": ["9999999"],
        "eleId": ["1"],
        "offset": ["0"],
        "length": ["12345"],
        "dtd": ["dart 4.xsd"],
    }


def test_parseSubDocs_single_page_supports_double_quotes() -> None:
    from dartlab.gather.dart.viewerPage import parseSubDocs

    content = (
        "<html><title>단일 문서</title><script>"
        'viewDoc( "20240315000123" , "12" , "3" , "0" , "99" , "dart4.xsd", "" );'
        "</script></html>"
    )

    result = parseSubDocs(content, "20240315000123")
    assert len(result) == 1
    assert result[0].title == "단일 문서"
    assert result[0].url.startswith("https://")


def test_parseSubDocs_single_page_decodes_escape() -> None:
    from dartlab.gather.dart.viewerPage import parseSubDocs

    content = (
        "<html><title>단일</title><script>"
        r"viewDoc('20240315000123', '12', '3', '0', '99', 'dart\u0034.xsd', '');"
        "</script></html>"
    )

    assert "dtd=dart4.xsd" in parseSubDocs(content, "20240315000123")[0].url


@pytest.mark.parametrize(
    "content, message",
    [
        (
            "node1['text'] = \"손상\"; node1['rcpNo'] = \"20240315000123\";",
            "필수 필드",
        ),
        (
            _nodeRecord() + "\nnode1['rcpNo'] = \"20240315000123\";",
            "중복 선언",
        ),
        (
            _nodeRecord(rceptNo="20240315000999"),
            "요청과 다릅니다",
        ),
        (
            "node1['text'] = unsupported;",
            "해석하지 못했습니다",
        ),
        (
            _nodeRecord() + "\nnode2['rcpNo'] = \"20240315000123\";",
            "text 없는",
        ),
    ],
)
def test_parseSubDocs_rejects_structural_damage(content: str, message: str) -> None:
    from dartlab.gather.dart.types import ViewerPageParseError
    from dartlab.gather.dart.viewerPage import parseSubDocs

    with pytest.raises(ViewerPageParseError, match=message):
        parseSubDocs(content, "20240315000123")
