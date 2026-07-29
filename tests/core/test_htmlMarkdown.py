"""공용 HTML table markdown 변환 회귀."""

from __future__ import annotations

import pytest
from bs4 import BeautifulSoup

from dartlab.core.htmlMarkdown import HtmlTableShapeError, lxmlTableToMarkdown, tableToMarkdown

pytestmark = pytest.mark.unit


def _table(html: str):
    table = BeautifulSoup(html, "lxml").find("table")
    assert table is not None
    return table


def test_tableToMarkdown_preserves_shape_words_and_pipe() -> None:
    markdown = tableToMarkdown(
        _table(
            "<table>"
            "<tr><th><span>매출</span> <span>구분</span></th><th>값|원</th></tr>"
            "<tr><td>A</td><td>1</td></tr>"
            "</table>"
        )
    )

    assert markdown == "| 매출 구분 | 값｜원 |\n| --- | --- |\n| A | 1 |"


def test_tableToMarkdown_does_not_duplicate_nested_rows() -> None:
    markdown = tableToMarkdown(_table("<table><tr><td>outer<table><tr><td>inner</td></tr></table></td></tr></table>"))

    assert markdown == "| outer inner |\n| --- |"
    assert markdown.count("inner") == 1


def test_tableToMarkdown_expands_rowspan_and_colspan() -> None:
    markdown = tableToMarkdown(
        _table('<table><tr><th rowspan="2">A</th><th colspan="2">B</th></tr><tr><td>C</td><td>D</td></tr></table>')
    )

    assert markdown == "| A | B |  |\n| --- | --- | --- |\n|  | C | D |"


def test_lxmlTableToMarkdown_matches_beautifulsoup_adapter() -> None:
    from lxml.html import fromstring

    html = (
        "<table>"
        '<tr><th rowspan="2">A</th><th colspan="2">B|C</th></tr>'
        "<tr><td><span>D</span> <span>E</span></td><td>F</td></tr>"
        "</table>"
    )

    assert lxmlTableToMarkdown(fromstring(html)) == tableToMarkdown(_table(html))


@pytest.mark.parametrize("span", ["0", "-1", "abc", "257"])
def test_tableToMarkdown_rejects_unsafe_colspan(span: str) -> None:
    with pytest.raises(HtmlTableShapeError, match="colspan"):
        tableToMarkdown(_table(f'<table><tr><td colspan="{span}">x</td></tr></table>'))


def test_tableToMarkdown_enforces_cell_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    import dartlab.core.htmlMarkdown as module

    monkeypatch.setattr(module, "_MAX_TABLE_CELLS", 4)
    with pytest.raises(HtmlTableShapeError, match="grid"):
        tableToMarkdown(_table('<table><tr><td colspan="3">A</td></tr><tr><td colspan="3">B</td></tr></table>'))


def test_tableToMarkdown_empty_table_is_empty() -> None:
    assert tableToMarkdown(_table("<table></table>")) == ""


def test_tableToMarkdown_skips_rows_without_cells() -> None:
    markdown = tableToMarkdown(_table("<table><tr></tr><tr><td>A</td></tr></table>"))
    assert markdown == "| A |\n| --- |"


def test_tableToMarkdown_rejects_non_table_tag() -> None:
    tag = BeautifulSoup("<div>x</div>", "lxml").find("div")
    with pytest.raises(TypeError, match="<table>"):
        tableToMarkdown(tag)
