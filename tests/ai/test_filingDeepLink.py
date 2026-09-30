"""정규화된 공시 기간으로 연간 수치 근거를 원문에 연결한다."""

from types import SimpleNamespace

import polars as pl
import pytest

from dartlab.ai.tools.filingDeepLink import attachDocRef, buildPeriodToFiling

pytestmark = pytest.mark.unit


def testCanonicalPeriodsAndAnnualAliasesKeepFilingIdentity():
    company = SimpleNamespace(
        filings=lambda: pl.DataFrame(
            {
                "period": ["2025Q4", "2025Q3"],
                "reportType": ["사업보고서", "분기보고서"],
                "rceptNo": ["20260310002820", "20251101000001"],
                "dartUrl": ["annual", "quarter"],
                "rceptDate": ["20260310", "20251101"],
            }
        )
    )
    mapping = buildPeriodToFiling(company)
    assert attachDocRef({}, "2025FY", mapping)["docId"] == "20260310002820"
    assert attachDocRef({}, "2025Q3", mapping)["sourcePath"] == "quarter"
    assert attachDocRef({}, "2024FY", mapping) == {}
