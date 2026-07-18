"""Universe U1 valid time, known time, correction, retraction PIT 검증."""

from __future__ import annotations

from dataclasses import replace

import pytest

from tests._attempts.dartlabUniverse.contracts import (
    EpistemicClass,
    SystemTime,
    TimeRange,
    UniverseStatement,
    VerificationState,
)
from tests._attempts.dartlabUniverse.temporal import asOfFilter, parseInstant, pointInTimeStatements


def _statement(statementId: str, knownAt: str, *, retractedAt: str | None = None):
    return UniverseStatement(
        statementId=statementId,
        subjectRef="du:v1:organization:" + "a" * 64,
        predicate="REVENUE",
        objectRef=None,
        value=100,
        valueType="DECIMAL",
        validTime=TimeRange("2024-01-01T00:00:00Z", "2025-01-01T00:00:00Z"),
        systemTime=SystemTime(knownAt, retractedAt=retractedAt),
        epistemicClass=EpistemicClass.OBSERVED,
        verificationState=VerificationState.VERIFIED,
        evidenceRefs=("evidence",),
    )


def testPointInTimeFiltersValidAndKnownTimeIndependently():
    statement = _statement("original", "2025-03-01T00:00:00Z")
    assert not asOfFilter(statement, "2024-06-01T00:00:00Z", "2025-02-28T23:59:59Z")
    assert asOfFilter(statement, "2024-06-01T00:00:00Z", "2025-03-01T00:00:00Z")
    assert not asOfFilter(statement, "2025-01-01T00:00:00Z", "2025-03-01T00:00:00Z")


def testCorrectionAndRetractionReplayPreservesPastSnapshot():
    original = _statement(
        "original",
        "2025-03-01T00:00:00Z",
        retractedAt="2025-04-01T00:00:00Z",
    )
    corrected = replace(
        _statement("corrected", "2025-04-01T00:00:00Z"),
        value=120,
    )
    before = pointInTimeStatements(
        (original, corrected),
        "2024-06-01T00:00:00Z",
        "2025-03-15T00:00:00Z",
    )
    after = pointInTimeStatements(
        (original, corrected),
        "2024-06-01T00:00:00Z",
        "2025-04-02T00:00:00Z",
    )
    assert [item.statementId for item in before] == ["original"]
    assert [item.statementId for item in after] == ["corrected"]


def testNaiveTemporalInputsAreRejected():
    with pytest.raises(ValueError):
        parseInstant("2026-07-18T00:00:00")
