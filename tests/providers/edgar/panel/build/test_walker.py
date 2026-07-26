"""EDGAR panel walker — 보드 leaf 분리 + 재무제표 1표/statement 앵커링 (data 0)."""

from __future__ import annotations

from collections import Counter

import pytest

from ..synthData import synthPre, synthPrimaryHtml, synthPrimaryHtmlNoInline

pytestmark = pytest.mark.unit


def _walk():
    from dartlab.providers.edgar.panel.build.linkbase import parsePresentation
    from dartlab.providers.edgar.panel.build.walker import buildStatementConcepts, walkBody

    sc = buildStatementConcepts(parsePresentation(synthPre()))
    return walkBody(synthPrimaryHtml(), formType="10-K", statementConcepts=sc)


def test_walk_anchors_statements() -> None:
    rows = _walk()
    assert rows
    anchored = {r["disclosureKey"] for r in rows if r["disclosureKey"]}
    assert "BS" in anchored and "IS" in anchored  # 각 5 concept 커버리지 ≥5


def test_one_table_per_statement() -> None:
    """statement 당 커버리지 최대 표 1개만 앵커 (note 표 오병합 가드)."""
    c = Counter(r["disclosureKey"] for r in _walk() if r["disclosureKey"])
    assert c["BS"] == 1 and c["IS"] == 1


def test_text_table_split_and_order() -> None:
    rows = _walk()
    types = {r["leafType"] for r in rows}
    assert "text" in types and "table" in types
    orders = [r["blockOrder"] for r in rows]
    assert orders == sorted(orders)  # blockOrder 단조(문서순)


def test_item_heading_detected() -> None:
    rows = _walk()
    assert any(r["sectionLeaf"].startswith("Item 1") for r in rows)


def test_caption_fallback_anchors_ins_era() -> None:
    """inline fact 0 (INS-era) — 표 캡션 제목으로 BS/IS 앵커 (captionToStatement fallback)."""
    from dartlab.providers.edgar.panel.build.linkbase import parsePresentation
    from dartlab.providers.edgar.panel.build.walker import buildStatementConcepts, walkBody

    sc = buildStatementConcepts(parsePresentation(synthPre()))
    rows = walkBody(synthPrimaryHtmlNoInline(), formType="10-K", statementConcepts=sc)
    anchored = Counter(r["disclosureKey"] for r in rows if r["disclosureKey"])
    assert anchored["BS"] == 1 and anchored["IS"] == 1  # 캡션으로 본표 앵커
    # "off-balance sheet" note 표는 BS 오앵커 금지 (statement 당 1개 + off- 음성 룩비하인드)
    assert sum(anchored.values()) == 2
