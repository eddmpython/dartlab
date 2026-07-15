"""redistributionReceiptProbe의 public policy 경계를 검증한다."""

from __future__ import annotations

from dataclasses import replace

import pytest

from tests._attempts.dartlabUniverse.policy import (
    ProjectionField,
    SourceFieldRef,
    assessPublicProjection,
    buildRedistributionReceipt,
    inspectReceiptCoverage,
    validateRedistributionReceipt,
)
from tests._attempts.dartlabUniverse.snapshot import currentSourceIds

AS_OF = "2026-07-15T12:00:00Z"


def _receipt(
    sourceId: str = "sourceA",
    *,
    decision: str = "public",
    allowedFields: tuple[str, ...] = ("value",),
):
    return buildRedistributionReceipt(
        sourceId=sourceId,
        allowedFields=allowedFields if decision in {"public", "metadataOnly"} else (),
        prohibitedFields=("secret",),
        attributionText="Source A",
        attributionUrl="https://example.test/source-a",
        policyVersion="policy-2026-01",
        reviewedAt="2026-01-01T00:00:00Z",
        expiresAt="2027-01-01T00:00:00Z",
        reviewer="operator-1",
        decision=decision,
    )


def _field(
    fieldId: str = "output",
    *,
    projectionClass: str = "derived",
    refs: tuple[tuple[str, str], ...] = (("sourceA", "value"),),
    expectedPublic: bool | None = None,
) -> ProjectionField:
    return ProjectionField(
        fieldId=fieldId,
        projectionClass=projectionClass,
        lineage=tuple(SourceFieldRef(sourceId, fieldPath) for sourceId, fieldPath in refs),
        expectedPublic=expectedPublic,
    )


def _assertCanonicalReceipt() -> None:
    first = _receipt(allowedFields=("value", "name", "value"))
    second = _receipt(allowedFields=("name", "value"))
    assert first.receiptId == second.receiptId
    assert first.allowedFields == ("name", "value")
    assert validateRedistributionReceipt(first, asOf=AS_OF).valid is True


def testCanonicalReceiptIsOrderIndependent() -> None:
    """Receipt field 순서와 중복이 canonical ID를 바꾸지 않는다.

    Args
        없음.

    Example
        pytest가 canonical receipt ID를 검증한다.

    Requires
        synthetic receipt fixture.

    Raises
        AssertionError: canonicalization이 불안정할 때.
    """

    _assertCanonicalReceipt()


def _assertTamperBlocked() -> None:
    receipt = _receipt()
    tampered = replace(receipt, attributionText="Changed")
    validation = validateRedistributionReceipt(tampered, asOf=AS_OF)
    assert validation.valid is False
    assert validation.reason == "receiptIdMismatch"


def testTamperedReceiptIsBlocked() -> None:
    """Canonical payload가 바뀐 receipt를 차단한다.

    Args
        없음.

    Example
        pytest가 tampered receipt 차단을 검증한다.

    Requires
        synthetic receipt fixture.

    Raises
        AssertionError: receipt tampering이 통과할 때.
    """

    _assertTamperBlocked()


def _assertPublicFieldAdmission() -> None:
    report = assessPublicProjection(
        [_field(expectedPublic=True)],
        [_receipt()],
        asOf=AS_OF,
    )
    assert report.admittedFieldCount == 1
    assert report.blockedFieldCount == 0
    assert report.reviewedExpectationCount == 1
    assert report.falseAcceptCount == 0
    assert report.falseRejectCount == 0


def testReviewedPublicFieldIsAdmitted() -> None:
    """Valid public receipt의 exact allowed field를 승인한다.

    Args
        없음.

    Example
        pytest가 positive public admission을 검증한다.

    Requires
        synthetic public receipt.

    Raises
        AssertionError: valid public field가 차단될 때.
    """

    _assertPublicFieldAdmission()


def _assertBlockedDecision(decision: str, expectedReason: str) -> None:
    receipts = [] if decision == "unknown" else [_receipt(decision=decision)]
    report = assessPublicProjection(
        [_field(expectedPublic=False)],
        receipts,
        asOf=AS_OF,
    )
    assert report.admittedFieldCount == 0
    assert report.falseAcceptCount == 0
    assert report.fields[0].reasons == (expectedReason,)


@pytest.mark.parametrize(
    ("decision", "expectedReason"),
    [
        ("unknown", "missingReceipt"),
        ("localOnly", "localOnlySource"),
        ("blocked", "blockedSource"),
    ],
)
def testUnknownAndBlockedDecisionsHaveNoFalseAccept(decision: str, expectedReason: str) -> None:
    """Unknown, localOnly, blocked source를 public에서 차단한다.

    Args
        decision: fixture source decision.
        expectedReason: 예상 reason code.

    Returns
        없음.

    Example
        pytest가 세 fail-closed decision을 검증한다.

    Requires
        synthetic policy fixtures.

    Raises
        AssertionError: 차단 source가 public으로 승인될 때.
    """

    _assertBlockedDecision(decision, expectedReason)


def _assertExpiredBlocked() -> None:
    receipt = _receipt()
    report = assessPublicProjection(
        [_field(expectedPublic=False)],
        [receipt],
        asOf="2027-01-01T00:00:00Z",
    )
    assert report.admittedFieldCount == 0
    assert report.fields[0].reasons == ("expiredReceipt",)


def testExpiredReceiptIsBlockedAtBoundary() -> None:
    """expiresAt 경계부터 receipt를 차단한다.

    Args
        없음.

    Example
        pytest가 expiry boundary를 검증한다.

    Requires
        synthetic receipt fixture.

    Raises
        AssertionError: 만료 receipt가 승인될 때.
    """

    _assertExpiredBlocked()


def _assertProhibitedWins() -> None:
    report = assessPublicProjection(
        [_field(refs=(("sourceA", "secret"),), expectedPublic=False)],
        [_receipt()],
        asOf=AS_OF,
    )
    assert report.admittedFieldCount == 0
    assert report.fields[0].reasons == ("prohibitedField",)


def testProhibitedFieldWinsOverSourceDecision() -> None:
    """Public source라도 prohibited field는 차단한다.

    Args
        없음.

    Example
        pytest가 prohibited field precedence를 검증한다.

    Requires
        synthetic receipt fixture.

    Raises
        AssertionError: prohibited field가 승인될 때.
    """

    _assertProhibitedWins()


def _assertMetadataBoundary() -> None:
    receipt = _receipt(decision="metadataOnly", allowedFields=("title",))
    fields = [
        _field(
            "meta",
            projectionClass="metadata",
            refs=(("sourceA", "title"),),
            expectedPublic=True,
        ),
        _field(
            "derived",
            projectionClass="derived",
            refs=(("sourceA", "title"),),
            expectedPublic=False,
        ),
    ]
    report = assessPublicProjection(fields, [receipt], asOf=AS_OF)
    byId = {field.fieldId: field for field in report.fields}
    assert byId["meta"].admitted is True
    assert byId["derived"].reasons == ("metadataOnlySource",)


def testMetadataOnlyDoesNotApproveDerivedContent() -> None:
    """Metadata field 허용을 derived content 허용으로 확대하지 않는다.

    Args
        없음.

    Example
        pytest가 metadata boundary를 검증한다.

    Requires
        synthetic metadataOnly receipt.

    Raises
        AssertionError: metadataOnly가 derived를 승인할 때.
    """

    _assertMetadataBoundary()


def _assertBlockedUpstreamPoisonsDerived() -> None:
    field = _field(
        refs=(("sourceA", "value"), ("sourceB", "value")),
        expectedPublic=False,
    )
    receipts = [_receipt("sourceA"), _receipt("sourceB", decision="localOnly")]
    report = assessPublicProjection([field], receipts, asOf=AS_OF)
    assert report.admittedFieldCount == 0
    assert report.fields[0].reasons == ("localOnlySource",)
    assert report.falseAcceptCount == 0


def testBlockedUpstreamPoisonsDerivedField() -> None:
    """Mixed lineage의 localOnly upstream이 derived output 전체를 차단한다.

    Args
        없음.

    Example
        pytest가 upstream fail-closed를 검증한다.

    Requires
        synthetic mixed lineage fixture.

    Raises
        AssertionError: 금지 upstream 파생값이 승인될 때.
    """

    _assertBlockedUpstreamPoisonsDerived()


def _assertCurrentCoverageBlocked() -> None:
    report = inspectReceiptCoverage(currentSourceIds(), [], asOf=AS_OF)
    assert report.sourceCount == 10
    assert report.receiptCount == 0
    assert report.validPublicReceiptCount == 0
    assert report.publicReady is False
    assert report.reasonCounts == {"missingReceipt": 10}


def testCurrentSourceSetHasNoImplicitPolicyApproval() -> None:
    """U0-S01 source 10개를 receipt 없이 자동 승인하지 않는다.

    Args
        없음.

    Example
        pytest가 current source coverage honest gap을 검증한다.

    Requires
        currentSourceIds contract.

    Raises
        AssertionError: empty registry가 public ready일 때.
    """

    _assertCurrentCoverageBlocked()


def _assertDuplicateReceiptRejected() -> None:
    receipt = _receipt()
    with pytest.raises(ValueError, match="duplicate receipt sourceId"):
        assessPublicProjection([_field()], [receipt, receipt], asOf=AS_OF)


def testDuplicateReceiptSourceIsRejected() -> None:
    """Source 하나에 receipt 두 개가 동시에 적용되지 못하게 한다.

    Args
        없음.

    Example
        pytest가 duplicate receipt rejection을 검증한다.

    Requires
        synthetic receipt fixture.

    Raises
        AssertionError: duplicate receipt가 조용히 수용될 때.
    """

    _assertDuplicateReceiptRejected()
