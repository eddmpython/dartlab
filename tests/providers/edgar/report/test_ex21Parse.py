"""ex21Parse. EX-21 자회사 파서 단위 (합성 HTML, 네트워크/OOM 무관)."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def test_subsidiaries_table_name_and_jurisdiction():
    from dartlab.providers.edgar.report.ex21Parse import parseSubsidiaries

    html = """
    <table>
      <tr><th>Name of Subsidiary</th><th>Jurisdiction of Incorporation</th></tr>
      <tr><td>Apple Asia Limited</td><td>Hong Kong</td></tr>
      <tr><td>Apple Canada Inc.</td><td>Canada</td></tr>
      <tr><td>Apple Asia Limited</td><td>Hong Kong</td></tr>
    </table>"""
    rows = parseSubsidiaries(html)
    assert rows[0] == {"name": "Apple Asia Limited", "jurisdiction": "Hong Kong"}
    assert len(rows) == 2  # 헤더 제외 + 중복 dedup


def test_no_table_returns_empty():
    from dartlab.providers.edgar.report.ex21Parse import parseSubsidiaries

    assert parseSubsidiaries("<p>Subsidiaries omitted per Item 601(b)(21).</p>") == []
