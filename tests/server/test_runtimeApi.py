"""Runtime Center API의 승인 계획과 exact evidence receipt 계약."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def testRuntimeInstallEndpointReturnsPlanWithoutExecuting():
    from dartlab.server.api.runtime import planRuntimeInstall

    value = planRuntimeInstall("codex")

    assert value["runtimeId"] == "codex"
    assert value["argv"][:3] == ("npm", "install", "-g")
    assert len(value["digest"]) == 64


def testProductOutcomeVerifyEndpointRequiresExactRegisteredRef(tmp_path, monkeypatch):
    import dartlab.productOutcome as outcomeService
    import dartlab.server.api.runtime as runtimeApi
    from dartlab.productOutcome import advanceOutcome, registerOutcomeEvidence, startOutcome
    from dartlab.server.api.runtime import EvidenceVerifyRequest, verifyProductOutcome

    monkeypatch.setenv("DARTLAB_OUTCOME_DB", str(tmp_path / "outcomes.sqlite3"))
    monkeypatch.setattr(outcomeService, "_DEFAULT_STORE", None)
    outcome = startOutcome(feature="ask")
    for state in ("scoped", "grounded"):
        advanceOutcome(outcome.outcomeId, state)
    registerOutcomeEvidence(outcome.outcomeId, ["tableRef:exact"])
    advanceOutcome(outcome.outcomeId, "delivered")
    monkeypatch.setattr(
        runtimeApi,
        "getRuntimeEngine",
        lambda: type(
            "Engine",
            (),
            {"resolveEvidence": lambda self, outcomeId, refId: {"id": refId, "kind": "tableRef"}},
        )(),
    )

    receipt = verifyProductOutcome(outcome.outcomeId, EvidenceVerifyRequest(refId="tableRef:exact"))

    assert receipt["receipt"]["state"] == "verified"
    assert receipt["evidence"] == {"id": "tableRef:exact", "kind": "tableRef"}
