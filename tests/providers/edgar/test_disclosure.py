"""disclosure.py mirror test (P-PR7+8 skeleton)."""

import pytest

pytestmark = pytest.mark.unit


def test_imports() -> None:
    """모듈 import smoke."""
    from dartlab.providers.edgar import disclosure

    assert hasattr(disclosure, "parseForm4Xml")
    assert hasattr(disclosure, "parseDef14aHtml")
    assert hasattr(disclosure, "parseEightKHtml")
    assert hasattr(disclosure, "STANDARD_8K_ITEMS")


def test_parse_form4_xml_skeleton_empty() -> None:
    """form4 skeleton — 빈 DataFrame."""
    from dartlab.providers.edgar.disclosure import parseForm4Xml

    df = parseForm4Xml("")
    assert df.is_empty()
    assert "insider" in df.columns


def test_parse_def14a_html_skeleton_empty() -> None:
    """def14a skeleton — 빈 DataFrame."""
    from dartlab.providers.edgar.disclosure import parseDef14aHtml

    df = parseDef14aHtml("")
    assert df.is_empty()
    assert "name" in df.columns


def test_parse_eight_k_html_skeleton_empty() -> None:
    """eightK skeleton — 빈 DataFrame."""
    from dartlab.providers.edgar.disclosure import parseEightKHtml

    df = parseEightKHtml("")
    assert df.is_empty()


def test_item_label_lookup() -> None:
    """8-K STANDARD_8K_ITEMS lookup."""
    from dartlab.providers.edgar.disclosure import itemLabel

    assert itemLabel("2.02") == "Results of Operations and Financial Condition"


@pytest.mark.parametrize(
    "block",
    [
        "<script>var hidden = 'Item 9.01 fake';</script >",
        '<script type="text/javascript">var hidden = 1;</script foo="bar">',
        "<SCRIPT>var hidden = 1;</SCRIPT\t\n bar>",
        "<Script\tsrc='x.js'>var hidden = 1;</sCrIpT>",
        "<style>.hidden { color: red; }</style >",
        '<STYLE media="all">.hidden {}</style\nfoo>',
        "<script/>var hidden = 1;</script/>",
        "<script>\nvar hidden = 1;\n</script>",
    ],
)
def test_strip_html_tags_drops_script_style_end_tag_variants(block: str) -> None:
    """공백/속성/줄바꿈이 붙은 끝 태그와 대소문자 변형도 script/style 블록 끝으로 인식한다."""
    from dartlab.providers.edgar.disclosure import _stripHtmlTags

    text = _stripHtmlTags(f"<p>Before</p>{block}<p>After</p>")

    assert text == "Before After"
    assert "hidden" not in text


@pytest.mark.parametrize(
    "html",
    [
        "<scripts>kept body</scripts><p>After</p></script>",
        "<stylesheet>kept body</stylesheet><p>After</p></style>",
        "<script-x>kept body</script-x><p>After</p></script>",
    ],
)
def test_strip_html_tags_keeps_lookalike_tag_content(html: str) -> None:
    """<scripts> 처럼 이름만 비슷한 태그는 script 블록 시작이 아니라서 본문이 남는다."""
    from dartlab.providers.edgar.disclosure import _stripHtmlTags

    assert _stripHtmlTags(html) == "kept body After"


def test_parse_eight_k_ignores_item_text_inside_script_with_spaced_end_tag() -> None:
    """script 안의 가짜 Item 헤더는 끝 태그가 `</script >` 여도 8-K item 으로 잡히지 않는다."""
    from dartlab.providers.edgar.disclosure import parseEightKHtml

    html = (
        "<html><body>"
        "<script>var x = 1. Item 5.02 Departure of Directors</script >"
        "<p>Item 2.02 Results of Operations and Financial Condition</p>"
        "<p>Quarterly revenue body.</p>"
        "</body></html>"
    )
    df = parseEightKHtml(html)

    assert df["item"].to_list() == ["2.02"]
    assert "Departure" not in df["text"][0]
