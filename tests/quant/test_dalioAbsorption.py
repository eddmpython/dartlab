"""Dalio *Principles for Navigating Big Debt Crises* 흡수 테스트.

L0 SSOT (core/finance/crisisDetector.py) Dalio 함수 + GHS regime 확장 검증.
"""

from __future__ import annotations

import pytest

# ── L0 — dalioDebtCyclePhase 역사 케이스 ──────────────────────


@pytest.mark.unit
def test_dalioDebtCyclePhase_1982_volcker():
    from dartlab.credit.monitoring.crisisDetector import dalioDebtCyclePhase

    r = dalioDebtCyclePhase(totalDebtToGdp=150, debtServiceYoY=4.0, creditGap=-3.0, realRate=6.0, gdpGrowth=-2.0)
    assert r.phase == "deflationaryDepression"
    assert r.phaseLabel == "디플레이션 공황"


@pytest.mark.unit
def test_dalioDebtCyclePhase_2007_housing():
    from dartlab.credit.monitoring.crisisDetector import dalioDebtCyclePhase

    r = dalioDebtCyclePhase(totalDebtToGdp=240, debtServiceYoY=5.0, creditGap=10.0, realRate=0.5, gdpGrowth=2.0)
    assert r.phase == "topBubble"


@pytest.mark.unit
def test_dalioDebtCyclePhase_2013_beautiful():
    from dartlab.credit.monitoring.crisisDetector import dalioDebtCyclePhase

    r = dalioDebtCyclePhase(totalDebtToGdp=240, debtServiceYoY=-2.0, creditGap=2.0, realRate=-1.0, gdpGrowth=2.0)
    assert r.phase == "beautifulDeleveraging"


@pytest.mark.unit
def test_dalioDebtCyclePhase_1975_reflationary():
    from dartlab.credit.monitoring.crisisDetector import dalioDebtCyclePhase

    r = dalioDebtCyclePhase(totalDebtToGdp=130, debtServiceYoY=2.0, creditGap=5.0, realRate=-3.0, gdpGrowth=-0.5)
    assert r.phase == "reflationary"


@pytest.mark.unit
def test_dalioDebtCyclePhase_missing_inputs_unavailable():
    from dartlab.credit.monitoring.crisisDetector import dalioDebtCyclePhase

    r = dalioDebtCyclePhase()
    assert r.phase is None
    assert r.status == "unavailable"
    assert isinstance(r.signals, list)


@pytest.mark.unit
def test_dalioPolicyLeverStatus_missing_is_not_spare():
    from dartlab.credit.monitoring.crisisDetector import dalioPolicyLeverStatus

    r = dalioPolicyLeverStatus(policyRate=5.0)
    assert r.monetary == "spare"
    assert r.fiscal == "unknown"
    assert r.exhaustionScore is None
    assert r.status == "partial"


# ── L0 — dalioPolicyLeverStatus 소진도 ───────────────────────


@pytest.mark.unit
def test_dalioPolicyLeverStatus_all_maxed():
    from dartlab.credit.monitoring.crisisDetector import dalioPolicyLeverStatus

    r = dalioPolicyLeverStatus(policyRate=0.1, publicDebtToGdp=150, creditGap=10, fxFlexibility="pegged")
    assert r.monetary == "maxed"
    assert r.fiscal == "maxed"
    assert r.credit == "maxed"
    assert r.fx == "maxed"
    assert r.exhaustionScore == 12  # 모두 maxed (3×4)


@pytest.mark.unit
def test_dalioPolicyLeverStatus_all_spare():
    from dartlab.credit.monitoring.crisisDetector import dalioPolicyLeverStatus

    r = dalioPolicyLeverStatus(policyRate=5.0, publicDebtToGdp=50, creditGap=0, fxFlexibility="flexible")
    assert r.monetary == "spare"
    assert r.fiscal == "spare"
    assert r.credit == "spare"
    assert r.fx == "spare"
    assert r.exhaustionScore == 4  # 모두 spare (1×4)


@pytest.mark.unit
def test_dalioPolicyLeverStatus_partial_mix():
    from dartlab.credit.monitoring.crisisDetector import dalioPolicyLeverStatus

    r = dalioPolicyLeverStatus(policyRate=1.5, publicDebtToGdp=100, creditGap=5, fxFlexibility="managed")
    assert r.monetary == "partial"
    assert r.fiscal == "partial"
    assert r.credit == "partial"
    assert r.fx == "partial"
    assert r.exhaustionScore == 8  # 모두 partial (2×4)


# ── L0 — GHS regime 확장 ────────────────────────────────────


@pytest.mark.unit
def test_ghsCrisisScore_deflation_regime():
    from dartlab.credit.monitoring.crisisDetector import ghsCrisisScore

    r = ghsCrisisScore(creditGrowth3y=-2.0, assetPriceGrowth3y=-10.0, realRate=3.0)
    assert r.regime == "deflation"
    assert r.regimeLabel == "디플레이션형"


@pytest.mark.unit
def test_ghsCrisisScore_inflation_regime():
    from dartlab.credit.monitoring.crisisDetector import ghsCrisisScore

    r = ghsCrisisScore(creditGrowth3y=10.0, assetPriceGrowth3y=60.0, realRate=-1.0)
    assert r.regime == "inflation"
    assert r.regimeLabel == "인플레이션형"


@pytest.mark.unit
def test_ghsCrisisScore_no_regime_without_realrate():
    from dartlab.credit.monitoring.crisisDetector import ghsCrisisScore

    # realRate 미제공 → regime None (후방 호환)
    r = ghsCrisisScore(creditGrowth3y=5.0, assetPriceGrowth3y=20.0)
    assert r.regime is None
    assert r.regimeLabel is None


@pytest.mark.unit
def test_ghsCrisisScore_legacy_positional_args():
    """기존 코드의 positional 2-arg 호출이 깨지지 않음 (후방 호환)."""
    from dartlab.credit.monitoring.crisisDetector import ghsCrisisScore

    r = ghsCrisisScore(5.0, 20.0)
    assert r.score >= 0
    assert r.zone in {"normal", "caution", "elevated", "danger"}
