"""Universe-scale Data Workbench planner attempt tests."""

from __future__ import annotations

import pytest

from dataUniverseQuery import (
    MarketMembership,
    OwnerCapability,
    UniverseSelection,
    UniverseSnapshot,
    compileUniversePlan,
)


def _snapshot() -> UniverseSnapshot:
    return UniverseSnapshot(
        "universe-2026-07-22",
        (
            MarketMembership("US", "edgar", ("0000789019", "0000320193")),
            MarketMembership("KR", "dart", ("035420", "005930", "000660")),
        ),
    )


def testSelectionCanonicalizesMarketsMembershipAndExplicitIds():
    selection = UniverseSelection(
        ("us", "KR", "US"),
        "active",
        ("US:0000320193", "KR:005930", "KR:005930"),
    )

    assert selection.markets == ("KR", "US")
    assert selection.explicitIds == ("KR:005930", "US:0000320193")


def testAllMarketPlanPrefersOwnerBulkAndFallsBackToSubjectFanout():
    selection = UniverseSelection(("US", "KR"), "active")
    capabilities = (
        OwnerCapability("analysis.simulationInputs", "analysis", (), ("KR", "US")),
        OwnerCapability(
            "scan.account",
            "scan",
            (("US", "active"), ("KR", "active")),
            ("KR", "US"),
        ),
    )

    plan = compileUniversePlan(selection, _snapshot(), capabilities)

    bulkTasks = tuple(task for task in plan.tasks if task.assetId == "scan.account")
    fanoutTasks = tuple(task for task in plan.tasks if task.assetId == "analysis.simulationInputs")
    assert [(task.market, task.mode, task.subjectCount) for task in bulkTasks] == [
        ("KR", "ownerBulk", 3),
        ("US", "ownerBulk", 2),
    ]
    assert len(fanoutTasks) == 5
    assert all(task.mode == "subjectFanout" for task in fanoutTasks)
    assert tuple(task.subjectId for task in fanoutTasks) == (
        "KR:000660",
        "KR:005930",
        "KR:035420",
        "US:0000320193",
        "US:0000789019",
    )


def testMarketCoverageKeepsDartAndEdgarSeparate():
    plan = compileUniversePlan(
        UniverseSelection(("KR", "US"), "active"),
        _snapshot(),
        (
            OwnerCapability(
                "scan.account",
                "scan",
                (("KR", "active"), ("US", "active")),
            ),
        ),
    )

    assert [
        (
            row.market,
            row.provider,
            row.executionMode,
            row.expectedSubjects,
            row.plannedSubjects,
            row.status,
        )
        for row in plan.coverage
    ] == [
        ("KR", "dart", "ownerBulk", 3, 3, "complete"),
        ("US", "edgar", "ownerBulk", 2, 2, "complete"),
    ]


def testEquivalentInputsProduceTheSameCanonicalPlan():
    selectionA = UniverseSelection(("US", "KR"), "active")
    selectionB = UniverseSelection(("KR", "US", "KR"), "active")
    capabilitiesA = (
        OwnerCapability("z.asset", "z", (), ("US", "KR")),
        OwnerCapability("a.asset", "a", (("US", "active"), ("KR", "active"))),
    )
    capabilitiesB = tuple(reversed(capabilitiesA))

    first = compileUniversePlan(selectionA, _snapshot(), capabilitiesA)
    second = compileUniversePlan(selectionB, _snapshot(), capabilitiesB)

    assert first.planId == second.planId
    assert first.tasks == second.tasks
    assert first.coverage == second.coverage
    assert [task.assetId for task in first.tasks[:2]] == ["a.asset", "a.asset"]


def testExplicitIdsUseFanoutAndReportMissingMembership():
    selection = UniverseSelection(
        ("KR", "US"),
        "active",
        ("KR:005930", "US:0000320193", "US:missing"),
    )
    capability = OwnerCapability(
        "scan.account",
        "scan",
        (("KR", "active"), ("US", "active")),
        ("KR", "US"),
    )

    plan = compileUniversePlan(selection, _snapshot(), (capability,))

    assert tuple(task.mode for task in plan.tasks) == ("subjectFanout", "subjectFanout")
    assert tuple(task.subjectId for task in plan.tasks) == ("KR:005930", "US:0000320193")
    usCoverage = next(row for row in plan.coverage if row.market == "US")
    assert usCoverage.expectedSubjects == 2
    assert usCoverage.resolvedSubjects == 1
    assert usCoverage.plannedSubjects == 1
    assert usCoverage.status == "partial"
    assert usCoverage.missingIds == ("US:missing",)
    assert usCoverage.gapCodes == ("MEMBERSHIP_ID_NOT_FOUND",)


def testExplicitFilterNeverOverfetchesBulkOnlyOwner():
    selection = UniverseSelection(("KR",), "active", ("KR:005930",))
    bulkOnly = OwnerCapability("scan.account", "scan", (("KR", "active"),))

    plan = compileUniversePlan(selection, _snapshot(), (bulkOnly,))

    assert plan.tasks == ()
    assert plan.coverage[0].status == "failed"
    assert plan.coverage[0].gapCodes == ("OWNER_FILTER_UNSUPPORTED",)


def testMissingMarketMembershipFailsWithCoverageInsteadOfSilentSuccess():
    selection = UniverseSelection(("KR", "JP"), "active")
    capability = OwnerCapability("analysis.simulationInputs", "analysis", (), ("KR", "JP"))

    plan = compileUniversePlan(selection, _snapshot(), (capability,))

    jpCoverage = next(row for row in plan.coverage if row.market == "JP")
    assert jpCoverage.provider is None
    assert jpCoverage.status == "failed"
    assert jpCoverage.gapCodes == ("MEMBERSHIP_UNAVAILABLE",)


def testInvalidSelectionAndDuplicateCapabilityFailBeforePlanning():
    with pytest.raises(ValueError, match="explicitIds"):
        UniverseSelection((), "explicit")
    with pytest.raises(ValueError, match="MARKET:ID"):
        UniverseSelection(("KR",), "active", ("005930",))

    capability = OwnerCapability("scan.account", "scan", (("KR", "active"),))
    with pytest.raises(ValueError, match="고유"):
        compileUniversePlan(
            UniverseSelection(("KR",), "active"),
            _snapshot(),
            (capability, capability),
        )
