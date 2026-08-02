from __future__ import annotations

import sqlite3

import pytest

from dartlab.productOutcome import OUTCOME_STATES, OutcomeStore


def testOutcomeStorePersistsCompleteLifecycle(tmp_path):
    path = tmp_path / "outcomes.sqlite3"
    store = OutcomeStore(path)
    record = store.start("opaque-1", feature="ask")
    assert record.state == "started"
    for state in OUTCOME_STATES[1:]:
        record = store.advance(record.outcomeId, state)
    assert OutcomeStore(path).get("opaque-1").state == "retained"
    assert store.snapshot(feature="ask")["states"]["retained"] == 1


def testOutcomeStoreRejectsSkippedAndRepeatedTransitions(tmp_path):
    store = OutcomeStore(tmp_path / "outcomes.sqlite3")
    store.start("opaque-1", feature="ask")
    with pytest.raises(ValueError):
        store.advance("opaque-1", "delivered")
    store.advance("opaque-1", "scoped")
    with pytest.raises(ValueError):
        store.advance("opaque-1", "scoped")


def testOutcomeDatabaseNeverStoresSensitiveAiFields(tmp_path):
    path = tmp_path / "outcomes.sqlite3"
    OutcomeStore(path).start("opaque-1", feature="ask")
    with sqlite3.connect(path) as database:
        columns = {
            row[1]
            for table in ("product_outcomes", "product_outcome_evidence")
            for row in database.execute(f"PRAGMA table_info({table})")
        }
    forbidden = {"prompt", "question", "answer", "provider", "model", "tokens", "path"}
    assert columns.isdisjoint(forbidden)


def testExactEvidenceReceiptIsRequiredAndIdempotent(tmp_path):
    store = OutcomeStore(tmp_path / "outcomes.sqlite3")
    store.start("opaque-1", feature="ask")
    for state in ("scoped", "grounded"):
        store.advance("opaque-1", state)
    store.registerEvidence("opaque-1", ["tableRef:exact"])
    store.advance("opaque-1", "delivered")

    with pytest.raises(KeyError):
        store.verifyEvidence("opaque-1", "tableRef:other")

    assert store.verifyEvidence("opaque-1", "tableRef:exact").state == "verified"
    assert store.verifyEvidence("opaque-1", "tableRef:exact").state == "verified"

    with sqlite3.connect(store.path) as database:
        values = [row[0] for row in database.execute("SELECT ref_hash FROM product_outcome_evidence")]
    assert values and "tableRef:exact" not in values
