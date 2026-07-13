from __future__ import annotations

import math
from dataclasses import replace

import pytest

from dartlab.analysis.financial.stepProjection import FinancialParameters, FinancialState
from dartlab.simulate.financialBridge import bridgeFinancialPaths, buildFinancialBridgeLaw
from dartlab.simulate.financialWorld import FinancialWorldInputs, buildFinancialStrategy, runFinancialStrategies
from dartlab.simulate.world import (
    ScenarioPath,
    SimulationSpecError,
    bindAdmittedPathContent,
    issueLawCertificate,
)


def _path(*, frequency: str = "year", admitted: bool = True) -> ScenarioPath:
    path = ScenarioPath(
        "macro",
        (
            {"gdpChange": -0.02, "rateChange": 0.01},
            {"gdpChange": 0.03, "rateChange": -0.005},
        ),
        frequency=frequency,
        validationStatus="admitted" if admitted else "retrospectiveOnly",
        certificateId="a" * 64 if admitted else "",
        maxAdmittedStep=2 if admitted else 0,
    )
    return bindAdmittedPathContent((path,))[0] if admitted else path


def _law(*, evidenceKind: str = "explicitAssumption"):
    law = buildFinancialBridgeLaw(
        factorUnits={"gdpChange": "ratioChangePerYear", "rateChange": "ratioChangePerYear"},
        demandLogCoefficients={"gdpChange": 1.5},
        marginChangeCoefficients={"gdpChange": 0.2},
        debtRateChangeCoefficients={"rateChange": 1.0},
        baseDebtRate=0.04,
        evidenceKind=evidenceKind,
    )
    if evidenceKind == "measuredAssociation":
        evidence = tuple(
            {"step": step, "metric": "oosSkill", "estimate": 0.1, "threshold": 0.0, "operator": "gt"} for step in (1, 2)
        )
        law = replace(
            law,
            certificate=issueLawCertificate(
                law,
                evidenceRows=evidence,
                knowledgeAsOf="20250101",
                historyStatus="asKnown",
                frequency="year",
                rules="positive OOS skill",
            ),
        )
    return law


def testBridgeProducesFinancialShocksAndCarriesDebtRate():
    result = bridgeFinancialPaths((_path(),), _law())
    steps = result.paths[0].steps
    assert steps[0]["demandGrowth"] == pytest.approx(math.expm1(-0.03))
    assert steps[0]["marginChange"] == pytest.approx(-0.004)
    assert steps[0]["debtRate"] == pytest.approx(0.05)
    assert steps[1]["debtRate"] == pytest.approx(0.045)


def testExplicitAssumptionDowngradesAdmittedSourcePath():
    result = bridgeFinancialPaths((_path(),), _law())
    assert result.paths[0].validationStatus == "retrospectiveOnly"
    assert "bridgeEvidence:explicitAssumption" in result.audit.warnings


def testAdmittedMeasuredBridgePreservesAdmissionWithCombinedCertificate():
    result = bridgeFinancialPaths((_path(),), _law(evidenceKind="measuredAssociation"))
    assert result.paths[0].validationStatus == "admitted"
    assert len(result.paths[0].certificateId) == 64
    assert result.paths[0].certificateId != _path().certificateId
    assert result.paths[0].maxAdmittedStep == 2


def testWeeklyMacroPathCannotEnterAnnualFinancialBridge():
    with pytest.raises(SimulationSpecError, match="step contract mismatch"):
        bridgeFinancialPaths((_path(frequency="week"),), _law())


def testBridgedPathRunsThroughFinancialStateAndClosesAccounting():
    paths = bridgeFinancialPaths((_path(),), _law()).paths
    inputs = FinancialWorldInputs(
        state=FinancialState(
            revenue=100.0,
            latentDemandRevenue=100.0,
            operatingMargin=0.15,
            cash=20.0,
            debt=30.0,
            receivables=10.0,
            inventories=10.0,
            payables=10.0,
            ppe=50.0,
            otherNetAssets=0.0,
            equity=50.0,
        ),
        parameters=FinancialParameters(0.2, 0.1, 0.1, 0.1, 2.4, 0.2),
        asOf="20250101",
        refs=("synthetic-company",),
        warnings=(),
    )
    strategy = buildFinancialStrategy(
        "baseline",
        capexRatio=(0.08, 0.08),
        inventoryRatio=(0.10, 0.10),
        borrow=(0.0, 0.0),
        repay=(0.0, 0.0),
        isBaseline=True,
    )
    run = runFinancialStrategies(inputs, paths, (strategy,), debtLimit=100.0, maxFinancing=50.0)
    assert all(abs(step.after["identityResidual"]) < 1e-8 for step in run.traces[0].steps)
    assert run.traces[0].steps[0].shocks == paths[0].steps[0]
    assert run.decisionStatus == "conditionalOnly"
