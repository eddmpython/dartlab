"""Altman 모델별 임계값이 analysis 소비면에서 섞이지 않는 회귀."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from dartlab.analysis.financial import _capitalFunding as funding_module
from dartlab.analysis.financial import _stabilityDistress as distress_module
from dartlab.analysis.financial import stability as stability_module
from dartlab.analysis.financial.insight._distressAxes import _quantAxis
from dartlab.analysis.financial.insight._distressModels import (
    _interpretAltmanZ,
    _interpretAltmanZpp,
    _normalizeZ,
    _normalizeZpp,
)

pytestmark = [pytest.mark.unit]


class _Company:
    def select(self, *_args, **_kwargs):
        return None


class _FinancialCompany(_Company):
    corpName = "테스트지주"


def _ensembleRatios(**overrides):
    values = {
        "altmanZScore": None,
        "altmanZppScore": None,
        "ohlsonProbability": None,
        "ohlsonOScore": None,
        "springateSScore": None,
        "zmijewskiXScore": None,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def testCapitalFlagsUsesZppThresholdInsteadOfZThreshold(monkeypatch: pytest.MonkeyPatch) -> None:
    """Z'' 1.5는 grey이지 Z 원본 distress(<1.81)가 아니다."""
    ratios = SimpleNamespace(altmanZScore=None, altmanZppScore=1.5)
    monkeypatch.setattr(funding_module, "_getRatios", lambda _company: ratios)
    monkeypatch.setattr(funding_module, "_isFinancialCompany", lambda _company: False)

    flags = funding_module.calcCapitalFlags(_Company())

    assert not any("Altman" in message for message, _kind in flags)


def testCapitalFlagsPublishesZppDistressWithItsOwnLabel(monkeypatch: pytest.MonkeyPatch) -> None:
    ratios = SimpleNamespace(altmanZScore=None, altmanZppScore=1.0)
    monkeypatch.setattr(funding_module, "_getRatios", lambda _company: ratios)
    monkeypatch.setattr(funding_module, "_isFinancialCompany", lambda _company: False)

    flags = funding_module.calcCapitalFlags(_Company())

    assert ("Altman Z'' 부실 경계 (1.00)", "warning") in flags


def testCapitalFlagsPrefersZppWhenBothVariantsExist(monkeypatch: pytest.MonkeyPatch) -> None:
    ratios = SimpleNamespace(
        altmanZScore=0.5,
        altmanZppScore=3.0,
        interestCoverage=None,
        currentRatio=None,
        netDebt=None,
        piotroskiFScore=None,
    )
    monkeypatch.setattr(funding_module, "_getRatios", lambda _company: ratios)
    monkeypatch.setattr(funding_module, "_isFinancialCompany", lambda _company: False)

    flags = funding_module.calcCapitalFlags(_Company())

    assert not any("Altman" in message for message, _kind in flags)


def testDistressAxisDoesNotDoubleCountAltmanVariants() -> None:
    ratios = SimpleNamespace(ohlsonProbability=None, altmanZScore=0.5, altmanZppScore=3.0)

    axis, models = _quantAxis(ratios, useMerton=False)

    assert len(models) == 1
    assert models[0].name == "Altman Z''-Score"
    assert len(axis.models) == 1


def testDistressEnsembleDoesNotDoubleCountAltmanVariants(monkeypatch: pytest.MonkeyPatch) -> None:
    ratios = _ensembleRatios(altmanZScore=0.5, altmanZppScore=3.0, springateSScore=1.0)
    monkeypatch.setattr(distress_module, "getRatios", lambda _company: ratios)

    result = distress_module.calcDistressEnsemble(_Company())

    assert result is not None
    assert result["total"] == 2
    assert [model["model"] for model in result["models"]] == ["Altman Z''-Score", "Springate S-Score"]


def testDistressEnsembleFallsBackToOriginalZ(monkeypatch: pytest.MonkeyPatch) -> None:
    ratios = _ensembleRatios(altmanZScore=1.81)
    monkeypatch.setattr(distress_module, "getRatios", lambda _company: ratios)

    result = distress_module.calcDistressEnsemble(_Company())

    assert result is not None
    assert result["models"] == [
        {
            "model": "Altman Z-Score",
            "score": 1.81,
            "verdict": "warning",
            "threshold": "안전 >2.99 / 회색 1.81~2.99 / 위험 <1.81",
        }
    ]


def testDistressEnsembleExcludesAltmanForFinancialCompany(monkeypatch: pytest.MonkeyPatch) -> None:
    ratios = _ensembleRatios(altmanZppScore=0.5, springateSScore=1.0)
    monkeypatch.setattr(distress_module, "getRatios", lambda _company: ratios)

    result = distress_module.calcDistressEnsemble(_FinancialCompany())

    assert result is not None
    assert [model["model"] for model in result["models"]] == ["Springate S-Score"]


def testDistressScoreReturnsStructuredUnavailableWithoutStatements() -> None:
    result = distress_module.calcDistressScore(_Company())

    assert result["status"] == "unavailable"
    assert result["reasonCode"] == "financial_statements_unavailable"
    assert result["missingInputs"] == ["BS", "IS"]


def testStabilityFlagsUsesZppThreshold(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(stability_module, "_isHoldingOrFinancial", lambda _company: False)
    monkeypatch.setattr(stability_module, "calcLeverageTrend", lambda _company, basePeriod=None: None)
    monkeypatch.setattr(stability_module, "calcCoverageTrend", lambda _company, basePeriod=None: None)
    monkeypatch.setattr(
        stability_module,
        "calcDistressScore",
        lambda _company, basePeriod=None: {
            "status": "ok",
            "latestScore": 1.5,
            "diagnosticMeta": {"reference": "Altman Z''"},
        },
    )

    result = stability_module.calcStabilityFlags(_Company())

    assert not any("Altman" in flag for flag in result["flags"])


def testAltmanInterpretationBoundariesMatchEachModel() -> None:
    assert _interpretAltmanZ(1.81).zone == "gray"
    assert _interpretAltmanZ(2.99).zone == "gray"
    assert _interpretAltmanZ(3.0).zone == "safe"
    assert _interpretAltmanZpp(1.1).zone == "gray"
    assert _interpretAltmanZpp(2.6).zone == "gray"
    assert _interpretAltmanZpp(2.61).zone == "safe"
    assert _normalizeZ(1.81) == pytest.approx(100.0)
    assert _normalizeZ(2.99) == pytest.approx(0.0)
    assert _normalizeZpp(1.1) == pytest.approx(100.0)
    assert _normalizeZpp(2.6) == pytest.approx(0.0)
