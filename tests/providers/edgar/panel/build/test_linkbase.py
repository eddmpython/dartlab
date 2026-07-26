"""EDGAR panel linkbase — EX-101.PRE(role→concept) + EX-101.LAB(라벨) (data 0)."""

from __future__ import annotations

import pytest

from ..synthData import synthLab, synthPre

pytestmark = pytest.mark.unit


def test_parse_presentation_roles_and_order() -> None:
    from dartlab.providers.edgar.panel.build.linkbase import parsePresentation

    roles = parsePresentation(synthPre())
    bsRole = next(r for r in roles if "BalanceSheets" in r)
    concepts = [e["conceptKey"] for e in roles[bsRole]]
    assert "us-gaap:Assets" in concepts and "us-gaap:StockholdersEquity" in concepts
    assert len(roles[bsRole]) == 5  # 5 BS concept
    # order 정렬 — 첫 concept order 최소
    assert roles[bsRole][0]["order"] <= roles[bsRole][1]["order"]


def test_parse_labels_standard() -> None:
    from dartlab.providers.edgar.panel.build.linkbase import parseLabels

    labels = parseLabels(synthLab())
    assert labels.get("us-gaap:Assets") == "Total assets"
    assert labels.get("us-gaap:Revenues") == "Total revenues"


def test_parse_linkbase_loc_attribute_order_independent() -> None:
    """실제 SEC PRE/LAB 는 xlink:label 이 xlink:href 보다 먼저 올 수 있다."""
    from dartlab.providers.edgar.panel.build.linkbase import parseLabels, parsePresentation

    pre = """
    <link:linkbase>
      <link:presentationLink xlink:role="http://x/role/StatementConsolidatedBalanceSheets">
        <link:loc xlink:type="locator" xlink:label="loc_assets" xlink:href="https://x#us-gaap_Assets"/>
        <link:presentationArc order="1" xlink:from="root" xlink:to="loc_assets"/>
      </link:presentationLink>
    </link:linkbase>
    """
    lab = """
    <link:linkbase>
      <link:loc xlink:type="locator" xlink:label="loc_assets" xlink:href="https://x#us-gaap_Assets"/>
      <link:labelArc xlink:from="loc_assets" xlink:to="lab_assets"/>
      <link:label xlink:label="lab_assets" xlink:role="http://www.xbrl.org/2003/role/label">Assets</link:label>
    </link:linkbase>
    """

    roleRows = next(iter(parsePresentation(pre).values()))
    assert roleRows[0]["conceptKey"] == "us-gaap:Assets"
    assert parseLabels(lab)["us-gaap:Assets"] == "Assets"
