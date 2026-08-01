"""quant 거버넌스가 감사의견 결측을 긍정 점수로 만들지 않는 회귀."""

from __future__ import annotations

import polars as pl
import pytest

pytestmark = pytest.mark.unit


def _rows(opinion: str | None) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "adt_opinion": [opinion],
            "year": ["2024"],
            "quarter": ["4분기"],
            "stlm_dt": ["2024-12-31"],
            "rcept_no": ["20250301000001"],
        }
    )


def testLatestAuditOpinionRejectsMissingAndUnknown() -> None:
    from dartlab.quant.text.governance import _latestAuditOpinion

    assert _latestAuditOpinion(_rows(None)) is None
    assert _latestAuditOpinion(_rows("(*2)")) is None


def testLatestAuditOpinionDoesNotMatchAdverseAsUnmodified() -> None:
    from dartlab.quant.text.governance import _latestAuditOpinion

    result = _latestAuditOpinion(_rows("부적정의견"))
    assert result is not None
    assert result["opinion"] == "부적정의견"


@pytest.mark.parametrize(("raw", "expected"), [("적정의견", 100), ("한정의견", 40), ("부적정의견", 0)])
def testGovernanceQuantScoresOnlyObservedOpinion(
    monkeypatch: pytest.MonkeyPatch,
    raw: str,
    expected: int,
) -> None:
    from dartlab.quant.text import governance

    frame = _rows(raw).with_columns(pl.lit("000001").alias("stockCode")).lazy()
    monkeypatch.setattr(governance, "resolveMarket", lambda *_args, **_kwargs: "KR")
    monkeypatch.setattr(
        governance,
        "loadScanParquet",
        lambda name, _market: frame if name == "auditOpinion" else None,
    )

    result = governance.calcGovernanceQuant("000001")
    assert result["subScores"]["audit"] == expected
    assert result["availableData"] == ["auditOpinion"]


def testGovernanceQuantDoesNotAwardUnknownOpinion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from dartlab.quant.text import governance

    frame = _rows("(*2)").with_columns(pl.lit("000001").alias("stockCode")).lazy()
    monkeypatch.setattr(governance, "resolveMarket", lambda *_args, **_kwargs: "KR")
    monkeypatch.setattr(
        governance,
        "loadScanParquet",
        lambda name, _market: frame if name == "auditOpinion" else None,
    )

    result = governance.calcGovernanceQuant("000001")
    assert result["governanceScore"] is None
    assert "auditOpinion" not in result["availableData"]
