"""analysis/story 감사의견 결측과 기간 경계를 보존한다."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

pytestmark = pytest.mark.unit


def testAuditTrendHonorsBasePeriodAndKeepsEvidence() -> None:
    from dartlab.analysis.financial.governance import calcAuditOpinionTrend

    audit = SimpleNamespace(
        years=[2023, 2024],
        opinions=["한정의견", "적정의견"],
        auditors=["감사A", "감사B"],
        rceptNos=["20240301000001", "20250301000002"],
    )
    company = SimpleNamespace(_report=SimpleNamespace(audit=audit), _cache={})

    result = calcAuditOpinionTrend(company, basePeriod="2023")

    assert result is not None
    assert len(result["history"]) == 1
    row = result["history"][0]
    assert row["year"] == 2023
    assert row["opinion"] == "한정의견"
    assert row["status"] == "observed"
    assert row["source"]["rceptNo"] == "20240301000001"


def testUnknownOpinionIsExcludedFromGovernanceScoreAndAnomaly() -> None:
    from dartlab.analysis.financial.insight._anomalyDeep import _auditOpinionFlag
    from dartlab.analysis.financial.insight._gradingGovernanceSignals import _auditOpinionSignal

    details = []
    risks = []
    audit = SimpleNamespace(opinions=["(*2)"])

    assert _auditOpinionSignal(audit, details, risks) == (0, 0)
    assert details == []
    assert risks == []
    assert _auditOpinionFlag(["(*2)"]) is None


def testAdverseOpinionStillProducesExplicitRisk() -> None:
    from dartlab.analysis.financial.insight._anomalyDeep import _auditOpinionFlag
    from dartlab.analysis.financial.insight._gradingGovernanceSignals import _auditOpinionSignal

    details = []
    risks = []
    audit = SimpleNamespace(opinions=["부적정의견"])

    assert _auditOpinionSignal(audit, details, risks) == (-2, 2)
    assert risks
    anomaly = _auditOpinionFlag(["부적정의견"])
    assert anomaly is not None
    assert anomaly.severity == "danger"


def testStoryLabelsMissingAndAmbiguousOpinion() -> None:
    from dartlab.story.builders.governance import auditOpinionTrendBlock

    blocks = auditOpinionTrendBlock(
        {
            "history": [
                {"year": 2023, "opinion": None, "status": "missing"},
                {"year": 2024, "opinion": None, "status": "ambiguous"},
            ]
        }
    )

    table = blocks[-1].df
    assert table["감사의견"].to_list() == ["자료부족", "판정불가"]
