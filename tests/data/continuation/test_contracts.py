"""Continuation contract secrecy and canonical digest locks."""

from __future__ import annotations

import math

import pytest

from dartlab.data.continuation import (
    ContinuationError,
    ContinuationMaintenanceBudget,
    ContinuationPage,
    ContinuationPins,
    ContinuationPolicy,
    ContinuationQueryState,
    IssuedContinuation,
    LoadedContinuationContext,
    PageEnvelope,
    bytesDigest,
    canonicalDigest,
    canonicalJsonBytes,
)


def testCanonicalDigestIsStableAcrossMappingOrder():
    assert canonicalDigest({"market": "KR", "limit": 3}) == canonicalDigest({"limit": 3, "market": "KR"})
    queryBytes = canonicalJsonBytes({"market": "KR"})
    assert bytesDigest(queryBytes) == canonicalDigest({"market": "KR"})


def testSecretBearingContractsHidePlaintextFromRepr():
    token = "dltc1." + "A" * 43
    query = b"private-query-text"
    cursor = b"private-cursor-text"
    state = ContinuationQueryState(query, cursor)
    pins = ContinuationPins(*(canonicalDigest(value) for value in ("source", "query", "contract", "schema")))
    issued = IssuedContinuation(token, canonicalDigest("token"), 10.0)
    context = LoadedContinuationContext(canonicalDigest("token"), state, pins, 1.0, 10.0)
    envelope = PageEnvelope(b"private-page", 1, state)
    page = ContinuationPage(
        "cas:sha256:" + "0" * 64,
        "0" * 64,
        b"private-page",
        1,
        12,
        pins.schemaDigest,
        token,
        False,
        "1" * 64,
    )

    rendered = " ".join(repr(value) for value in (state, issued, context, envelope, page))
    assert token not in rendered
    assert query.decode() not in rendered
    assert cursor.decode() not in rendered
    assert "private-page" not in rendered


def testContinuationErrorOnlyAcceptsSafeRegisteredCodes():
    error = ContinuationError("CONTINUATION_EXPIRED")
    assert error.code == "CONTINUATION_EXPIRED"
    assert "secret" not in str(error)
    assert repr(error) == "ContinuationError(code='CONTINUATION_EXPIRED')"


@pytest.mark.parametrize(
    ("fieldName", "value"),
    [
        (fieldName, value)
        for fieldName in (
            "maxPageRows",
            "maxPageBytes",
            "maxPageLogicalBytes",
            "maxStateBytes",
            "maxTokenIssueAttempts",
        )
        for value in (True, 1.5, "1", 0)
    ],
)
def testPolicyIntegerBoundsRejectWrongNumericTypes(fieldName, value):
    with pytest.raises(ValueError):
        ContinuationPolicy(**{fieldName: value})


@pytest.mark.parametrize(
    "fieldName",
    (
        "maxChains",
        "maxRootScans",
        "maxContinuationRows",
        "maxLedgerScans",
        "maxCasPrefixes",
        "maxCasEntries",
        "maxArtifactDeletes",
    ),
)
@pytest.mark.parametrize("value", (True, 1.5, "1", 0))
def testMaintenanceBudgetRequiresExactPositiveIntegers(fieldName, value):
    with pytest.raises(ValueError):
        ContinuationMaintenanceBudget(**{fieldName: value})


def testMaintenanceBudgetCapsFanoutPrefixes():
    with pytest.raises(ValueError):
        ContinuationMaintenanceBudget(maxCasPrefixes=257)


@pytest.mark.parametrize(
    ("fieldName", "value"),
    [
        (fieldName, value)
        for fieldName in (
            "tokenTtlSeconds",
            "leaseSeconds",
            "waitSeconds",
            "pollSeconds",
            "pruneGraceSeconds",
            "artifactStageSeconds",
        )
        for value in (True, "1", 0, math.nan, math.inf, -math.inf, 10**1000)
    ],
)
def testPolicyTimeBoundsRejectNonFiniteAndWrongNumericTypes(fieldName, value):
    with pytest.raises(ValueError):
        ContinuationPolicy(**{fieldName: value})


@pytest.mark.parametrize(
    "value",
    (
        {1: "would-collide-with-string-key"},
        {"number": math.nan},
        {"number": math.inf},
        {"number": -math.inf},
    ),
)
def testCanonicalJsonRejectsAmbiguousOrNonFiniteTrees(value):
    with pytest.raises((TypeError, ValueError)):
        canonicalJsonBytes(value)


def testCanonicalJsonRejectsCycles():
    value = []
    value.append(value)

    with pytest.raises(ValueError):
        canonicalJsonBytes(value)


@pytest.mark.parametrize("rowCount", (True, 1.5, "1", -1))
def testPageEnvelopeRequiresExactNonnegativeIntegerRows(rowCount):
    with pytest.raises(ValueError):
        PageEnvelope(b"payload", rowCount)
