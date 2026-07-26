"""EDGAR panel submission — SEC `.txt` SGML 파서 (header + primary + EX-101, data 0)."""

from __future__ import annotations

from datetime import date

import pytest

from ..synthData import synthSubmissionTxt

pytestmark = pytest.mark.unit


def test_parse_header_fields() -> None:
    from dartlab.providers.edgar.panel.build.submission import parseSubmission

    s = parseSubmission(synthSubmissionTxt())
    assert s["form"] == "10-K"
    assert s["cik"] == "0000012345"
    assert s["accession"] == "0000012345-25-000001"
    assert s["periodOfReport"] == date(2024, 12, 31)
    assert s["fiscalYearEnd"] == "1231"
    assert s["name"] == "TEST CORP"


def test_primary_and_ex101_extraction() -> None:
    from dartlab.providers.edgar.panel.build.submission import parseSubmission

    s = parseSubmission(synthSubmissionTxt())
    # primary = 10-K HTML (XBRL wrapper strip 후 html 시작)
    assert "<html" in s["primaryHtml"] and "ix:nonFraction" in s["primaryHtml"]
    assert "<XBRL>" not in s["primaryHtml"]  # wrapper strip
    assert "presentationLink" in s["ex101Pre"]
    assert "us-gaap_Assets" in s["ex101Lab"]


def test_no_xml_prolog_in_primary_text_only() -> None:
    """primary HTML 은 TEXT 본문만 — 다른 DOCUMENT(EX-101) 본문 미혼입."""
    from dartlab.providers.edgar.panel.build.submission import parseSubmission

    s = parseSubmission(synthSubmissionTxt())
    assert "EX-101" not in s["primaryHtml"]
