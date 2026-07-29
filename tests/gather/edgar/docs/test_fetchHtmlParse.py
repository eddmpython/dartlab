"""mirror smoke — edgar/docs/fetchHtmlParse.py (split helper).

분할 helper 모듈의 임포트 가능성 + 룰 7 mirror 슬롯 충족.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def test_import() -> None:
    """clean-interpreter import smoke — pytest 세션 import-order 순환 면역."""
    import subprocess
    import sys

    code = "import dartlab.gather.edgar.docs.fetchHtmlParse"
    r = subprocess.run([sys.executable, "-X", "utf8", "-c", code], capture_output=True, text=True, timeout=180)
    assert r.returncode == 0, r.stderr


def test_table_markdown_uses_core_ssot() -> None:
    from bs4 import BeautifulSoup

    from dartlab.core.htmlMarkdown import tableToMarkdown
    from dartlab.gather.edgar.docs.fetchHtmlParse import _tableToMarkdown

    table = BeautifulSoup(
        "<table><tr><th>A</th><th>B|C</th></tr><tr><td>1</td><td>2</td></tr></table>",
        "lxml",
    ).find("table")

    assert table is not None
    assert _tableToMarkdown is tableToMarkdown
    assert _tableToMarkdown(table) == "| A | B｜C |\n| --- | --- |\n| 1 | 2 |"
