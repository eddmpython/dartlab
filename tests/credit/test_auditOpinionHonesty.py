"""감사의견은 구조화 원문에 명시된 범주만 판정한다."""

from __future__ import annotations

from types import SimpleNamespace

import polars as pl
import pytest

from dartlab.providers._common.auditOpinion import auditOpinionStatus, normalizeAuditOpinion

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("적정의견", "적정의견"),
        ("한정 의견", "한정의견"),
        ("부적정의견", "부적정의견"),
        ("의견거절", "의견거절"),
        ("unqualified opinion", "적정의견"),
        ("unmodified opinion", "적정의견"),
        ("qualified opinion", "한정의견"),
        ("adverse opinion", "부적정의견"),
        ("disclaimer of opinion", "의견거절"),
    ],
)
def testNormalizeExplicitAuditOpinions(raw: str, expected: str) -> None:
    assert normalizeAuditOpinion(raw) == expected


@pytest.mark.parametrize("raw", [None, "", "-", "해당사항 없음", "반기 검토보고서"])
def testMissingOrReviewIsNotUnmodified(raw: str | None) -> None:
    assert normalizeAuditOpinion(raw) is None
    assert auditOpinionStatus(raw) == "missing"


def testUnknownFootnoteIsAmbiguousNotRiskOrClean() -> None:
    assert normalizeAuditOpinion("(*2)") is None
    assert auditOpinionStatus("(*2)") == "ambiguous"


def testFetchAuditOpinionHonorsBasePeriodAndProvenance() -> None:
    from dartlab.credit.scoring._metricsFetchers import _fetchAuditOpinionEvidence

    audit = SimpleNamespace(
        years=[2023, 2024],
        opinions=["한정의견", "적정의견"],
        auditors=["감사A", "감사B"],
        rceptNos=["20240301000001", "20250301000002"],
    )
    company = SimpleNamespace(market="KOSPI", _report=SimpleNamespace(audit=audit))

    latest = _fetchAuditOpinionEvidence(company)
    historical = _fetchAuditOpinionEvidence(company, basePeriod="2023")

    assert latest["opinion"] == "적정의견"
    assert latest["fiscalPeriod"] == "2024"
    assert latest["source"]["rceptNo"] == "20250301000002"
    assert historical["opinion"] == "한정의견"
    assert historical["fiscalPeriod"] == "2023"


def testPivotAuditPrefersCurrentPeriodAndLatestCorrection() -> None:
    from dartlab.providers.dart.report.pivot import pivotAudit

    base = pl.DataFrame(
        {
            "stockCode": ["000001", "000001", "000001"],
            "apiType": ["auditOpinion"] * 3,
            "year": ["제10기(전기)", "제11기(당기)", "제11기(당기)"],
            "bsns_year": ["제10기(전기)", "제11기(당기)", "제11기(당기)"],
            "quarter": ["4분기"] * 3,
            "stlm_dt": ["2024-12-31"] * 3,
            "rcept_no": ["20250301000001", "20250301000001", "20250302000002"],
            "adt_opinion": ["한정의견", "적정의견", "적정의견"],
            "adtor": ["과거감사인", "현재감사인", "정정감사인"],
        }
    )

    result = pivotAudit("000001", baseDf=base)

    assert result is not None
    assert result.years == [2024]
    assert result.opinions == ["적정의견"]
    assert result.auditors == ["정정감사인"]
    assert result.rceptNos == ["20250302000002"]
