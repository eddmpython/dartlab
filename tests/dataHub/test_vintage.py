"""Data 계층 빈티지 계약과 simulate 호환 표면을 검증한다."""

from __future__ import annotations

import inspect
from dataclasses import replace
from typing import Any, cast

import pytest

import dartlab.dataHub.vintage as dataVintage
import dartlab.simulate.vintage as simulateVintage


def _vintage() -> dataVintage.VintageRef:
    return dataVintage.VintageRef(
        artifactKind="providerObservation",
        provider="edgar",
        artifactId="revenue-20250102",
        artifactHash="a" * 64,
        payloadHash="b" * 64,
        knowledgeAsOf="20250102",
        availableAt="20250102",
        revisionPolicy="asKnown",
        coverage="asOfExact",
        fiscalThrough="20241231",
        sourceRefs=cast(Any, ["source:a", "source:b"]),
    )


def testSimulateVintageReexportsCanonicalObjectsByIdentity() -> None:
    names = (
        "COVERAGE_KINDS",
        "REVISION_POLICIES",
        "VintageError",
        "VintageRef",
        "canonicalPayloadBytes",
        "canonicalPayloadHash",
        "isExactAsKnown",
        "validateVintageRef",
        "worldStatePayloadHash",
    )
    for name in names:
        assert getattr(simulateVintage, name) is getattr(dataVintage, name)
    assert dataVintage.VintageRef.__module__ == "dartlab.dataHub.vintage"
    assert "dartlab.simulate" not in inspect.getsource(dataVintage)


def testCanonicalPayloadAndWorldStateHashesRemainStable() -> None:
    payload = {"b": [2, 1], "a": "한글"}
    assert dataVintage.canonicalPayloadBytes(payload).decode("utf-8") == '{"a":"한글","b":[2,1]}'
    assert (
        dataVintage.canonicalPayloadHash(payload) == "b055c12d03bdf02fea3e2f40c810fd1edf939f51b65038a1f639f27b41fbbd6d"
    )
    assert (
        dataVintage.worldStatePayloadHash(
            {"b": None, "a": 1.5},
            step=2,
            asOf="2025-01-02",
            refs=("source:b", "source:a"),
        )
        == "c1f30badc9fde5a3dd22cd9981fc2ec57bf1e97d16ed747ab9cd55467ad4259c"
    )


def testVintageValidationAndSourceRefNormalizationRemainStable() -> None:
    vintage = _vintage()
    assert vintage.sourceRefs == ("source:a", "source:b")
    assert (
        dataVintage.validateVintageRef(
            vintage,
            decisionAsOf="20250103",
            expectedArtifactKind="providerObservation",
            expectedPayloadHash="b" * 64,
        )
        is vintage
    )
    assert dataVintage.isExactAsKnown(vintage)
    assert not dataVintage.isExactAsKnown(replace(vintage, coverage="periodOnly"))


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("schemaVersion", "other", "vintage protocol mismatch"),
        ("provider", "", "vintage identity fields are incomplete"),
        ("artifactHash", "bad", "vintage artifact hash is invalid"),
        ("contractHash", "bad", "vintage contract hash is invalid"),
        ("receiptId", "bad", "vintage receipt identifier is invalid"),
        ("revisionPolicy", "other", "vintage revision or coverage contract is invalid"),
        ("availableAt", "bad", "invalid vintage availableAt: bad"),
        ("availableAt", "20250103", "vintage evidence is newer than knowledgeAsOf"),
        ("knowledgeAsOf", "20250104", "vintage knowledge is newer than decisionAsOf"),
        ("fiscalThrough", "20250103", "vintage fiscalThrough is newer than availableAt"),
    ),
)
def testVintageValidationErrorsRemainStable(field: str, value: str, message: str) -> None:
    vintage = replace(_vintage(), **{field: value})
    with pytest.raises(dataVintage.VintageError) as caught:
        dataVintage.validateVintageRef(vintage, decisionAsOf="20250103")
    assert str(caught.value) == message


def testExpectedIdentityAndPayloadErrorsRemainStable() -> None:
    vintage = _vintage()
    with pytest.raises(dataVintage.VintageError) as kindError:
        dataVintage.validateVintageRef(vintage, decisionAsOf="20250103", expectedArtifactKind="worldState")
    assert str(kindError.value) == "vintage artifact kind mismatch"

    with pytest.raises(dataVintage.VintageError) as payloadError:
        dataVintage.validateVintageRef(vintage, decisionAsOf="20250103", expectedPayloadHash="c" * 64)
    assert str(payloadError.value) == "vintage payload hash mismatch"

    with pytest.raises(dataVintage.VintageError) as typeError:
        dataVintage.canonicalPayloadBytes({1, 2})
    assert str(typeError.value) == "unsupported vintage payload type: set"
