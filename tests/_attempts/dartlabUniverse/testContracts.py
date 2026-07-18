"""Universe U1 canonical JSON, statement, evidence fail-closed 계약."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime

import pytest

from tests._attempts.dartlabUniverse.canonical import canonicalDigest, canonicalJson
from tests._attempts.dartlabUniverse.contracts import (
    EpistemicClass,
    SystemTime,
    TimeRange,
    UniverseEvidence,
    UniverseStatement,
    VerificationState,
    Visibility,
    validateEvidence,
    validateStatement,
)


def _statement(**overrides):
    base = UniverseStatement(
        statementId="du:v1:statement:" + "a" * 64,
        subjectRef="du:v1:organization:" + "b" * 64,
        predicate="REVENUE",
        objectRef=None,
        value=100,
        valueType="DECIMAL",
        validTime=TimeRange("2025-01-01T00:00:00Z", "2026-01-01T00:00:00Z"),
        systemTime=SystemTime("2025-03-01T00:00:00Z"),
        epistemicClass=EpistemicClass.OBSERVED,
        verificationState=VerificationState.VERIFIED,
        evidenceRefs=("du:v1:evidence:" + "c" * 64,),
        visibility=Visibility.LOCAL,
    )
    return replace(base, **overrides)


def testCanonicalJsonNormalizesUnicodeUtcAndRejectsAmbiguity():
    composed = {"name": "é", "at": datetime.fromisoformat("2026-07-18T09:00:00+09:00")}
    decomposed = {"name": "e\u0301", "at": datetime.fromisoformat("2026-07-18T00:00:00+00:00")}

    assert canonicalJson(composed) == canonicalJson(decomposed)
    assert canonicalDigest({"v": -0.0}) == canonicalDigest({"v": 0.0})
    with pytest.raises(ValueError):
        canonicalJson({"v": float("nan")})
    with pytest.raises(ValueError):
        canonicalJson({"at": datetime(2026, 7, 18)})
    with pytest.raises(ValueError):
        canonicalJson({"é": 1, "e\u0301": 2})


def testStatementValidationEnforcesEpistemicInvariants():
    assert validateStatement(_statement()).valid

    invalid = _statement(
        objectRef="du:v1:organization:" + "d" * 64,
        evidenceRefs=(),
        confidence=1.1,
        visibility=Visibility.UNKNOWN,
    )
    codes = {issue.code for issue in validateStatement(invalid).issues}
    assert codes == {
        "CONFIDENCE_RANGE",
        "OBJECT_VALUE_XOR",
        "OBSERVED_EVIDENCE_REQUIRED",
        "UNKNOWN_VISIBILITY",
    }

    simulated = _statement(
        epistemicClass=EpistemicClass.SIMULATED,
        evidenceRefs=(),
        derivationRef=None,
        assumptionRefs=(),
    )
    simulatedCodes = {issue.code for issue in validateStatement(simulated).issues}
    assert simulatedCodes == {"DERIVATION_REQUIRED", "SIMULATION_ASSUMPTION_REQUIRED"}


def testEvidenceRequiresExactLocatorAndPinnedSourceRevision():
    evidence = UniverseEvidence(
        evidenceId="du:v1:evidence:" + "e" * 64,
        sourceKind="EDGAR",
        sourceRef="eddmpython/dartlab-data",
        sourceRevision="f" * 40,
        resourceVersionId="du:v1:file-version:" + "1" * 64,
        locator=(("cik", "0000320193"), ("accession", "0000320193-25-000001"), ("form", "10-K")),
        contentDigest="2" * 64,
        retrievedAt="2026-07-18T00:00:00Z",
        visibility=Visibility.PUBLIC,
    )
    revisions = (("eddmpython/dartlab-data", "f" * 40),)
    assert validateEvidence(evidence, revisions).valid

    invalid = replace(evidence, locator=(("cik", "0000320193"),), sourceRevision="0" * 40)
    codes = {issue.code for issue in validateEvidence(invalid, revisions).issues}
    assert codes == {"LOCATOR_FIELD_REQUIRED", "SOURCE_REVISION_MISMATCH"}
