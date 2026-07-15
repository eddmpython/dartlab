"""releaseGoldReviewPromotionProbe의 human-only exact gold 승격 경계를 검증한다."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from tests._attempts.dartlabUniverse.fixtures.releaseGoldProbe import (
    evaluateReleaseGold,
    loadSamplingPlan,
)
from tests._attempts.dartlabUniverse.fixtures.releaseGoldReviewPromotionProbe import (
    promoteReviewedDecisions,
)

ROOT = Path(__file__).resolve().parent
HASH_A = f"sha256:{'a' * 64}"
HASH_B = f"sha256:{'b' * 64}"
LOCATOR_ID = "source:locator:test-a"


def _queue(lane: str = "positiveCandidate") -> dict:
    challenge = lane == "hardNegativeChallenge"
    return {
        "candidateId": "review:challenge:test-a" if challenge else "review:candidate:test-a",
        "lane": lane,
        "reviewState": "unreviewed",
        "goldEligible": False,
        "subjectId": "krx:000001" if not challenge else "krx:000002",
        "predicate": "suppliesTo",
        "objectId": "krx:000002" if not challenge else "krx:000001",
        "negativeType": "reversedDirection" if challenge else None,
        "docId": "dart:allFilings:20260102000123#section=0",
        "sectionPath": "사업/관계",
        "sourceRef": "dart:allFilings:20260102000123#section=0",
        "candidateSourceRef": "dart:allFilings:20260102000123#section=0",
        "evidenceText": "나래",
        "market": "KR",
        "language": "ko",
    }


def _binding(candidateId: str = "review:candidate:test-a") -> dict:
    return {
        "candidateId": candidateId,
        "sourceArtifactReady": True,
        "originalSourceVersion": HASH_A,
        "locatorCandidates": [
            {
                "locatorId": LOCATOR_ID,
                "sectionPath": "사업/관계/공급",
                "contentHash": HASH_B,
                "evidenceText": "나래",
                "charStart": 10,
                "charEnd": 12,
                "snippetHash": HASH_B,
            }
        ],
    }


def _reviewBase(candidateId: str = "review:candidate:test-a") -> dict:
    return {
        "schemaVersion": "releaseGoldReviewDecision.v1",
        "candidateId": candidateId,
        "origin": "humanReviewed",
        "reviewMethod": "documentOpened",
        "reviewer": "reviewer-1",
        "reviewedAt": "2026-07-16T10:00:00+09:00",
        "reviewReceiptId": "review:fixture-a",
        "reviewedSourceRef": "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260102000123",
    }


def _positiveDecision() -> dict:
    return {
        **_reviewBase(),
        "decision": "acceptPositive",
        "subjectId": "krx:000001",
        "predicate": "suppliesTo",
        "objectId": "krx:000002",
        "selectedLocatorId": LOCATOR_ID,
        "eventAt": "2026-01-01T00:00:00Z",
        "validFrom": "2026-01-01T00:00:00Z",
        "validTo": None,
        "sourcePublishedAt": "2026-01-02T00:00:00Z",
        "availableAt": "2026-01-02T00:01:00Z",
        "evidenceClass": "A",
        "sourceKind": "DART",
    }


def _negativeDecision() -> dict:
    return {
        **_reviewBase("review:challenge:test-a"),
        "decision": "confirmNegative",
        "subjectId": "krx:000002",
        "predicate": "suppliesTo",
        "objectId": "krx:000001",
        "negativeType": "reversedDirection",
        "reviewReason": "원문은 반대 방향만 입증하며 challenge 방향은 사실이 아니다.",
        "selectedLocatorId": LOCATOR_ID,
    }


def testAcceptPositivePromotesExactHumanReviewedGold() -> None:
    """완전한 positive review를 release admission schema와 exact source locator로 승격한다.

    Capabilities
        Human receipt, confirmed triple, source hash, locator, bitemporal field 승격을 검증한다.
    AIContext
        AI 역할: reviewer decision을 그대로 추적 가능한 gold record로 materialize한다.
    Guide
        한 건을 승격한 뒤 기존 release gold validator가 schema를 수용하는지 확인한다.
    When
        Positive promotion field mapping 또는 admission contract 변경 시 실행한다.
    How
        Fixture queue, binding, accept decision을 compiler와 admission evaluator에 전달한다.
    Requires
        Sampling plan fixture와 content-addressed source locator.
    Returns:
        None.
    Raises:
        AssertionError: Gold field 또는 admission validation이 깨질 때.
    Example:
        ``testAcceptPositivePromotesExactHumanReviewedGold()``
    SeeAlso:
        :func:`promoteReviewedDecisions`.
    """

    positives, negatives, report = promoteReviewedDecisions([_queue()], [_binding()], [_positiveDecision()])
    admission = evaluateReleaseGold(
        positives,
        negatives,
        [],
        loadSamplingPlan(ROOT / "releaseGoldSamplingPlan.json"),
    )
    record = positives[0]

    assert negatives == []
    assert record["sourceVersion"] == HASH_A
    assert record["contentHash"] == HASH_B
    assert record["charStart"] == 10
    assert record["charEnd"] == 12
    assert record["origin"] == "humanReviewed"
    assert record["reviewReceiptId"] == "review:fixture-a"
    assert admission.reviewedPositiveCount == 1
    assert report["promotedPositiveCount"] == 1
    assert report["goldAdmissionReady"] is False


def testConfirmNegativePromotesReviewedChallenge() -> None:
    """사람이 원문에서 반증한 challenge만 hard-negative gold로 승격한다.

    Capabilities
        Negative type, reversed triple, review reason, source receipt 승격을 검증한다.
    AIContext
        AI 역할: machine challenge를 human-reviewed reject와 구분해 compiler에서만 승격한다.
    Guide
        Hard-negative lane과 matching challenge type을 사용해 한 건을 materialize한다.
    When
        Negative review schema 또는 transformation type 변경 시 실행한다.
    How
        Challenge queue, source binding, confirm-negative decision을 compiler에 전달한다.
    Requires
        Content-addressed binding과 document-opened review receipt.
    Returns:
        None.
    Raises:
        AssertionError: Negative identity 또는 human receipt가 누락될 때.
    Example:
        ``testConfirmNegativePromotesReviewedChallenge()``
    SeeAlso:
        :func:`promoteReviewedDecisions`.
    """

    queue = _queue("hardNegativeChallenge")
    binding = _binding(queue["candidateId"])
    positives, negatives, report = promoteReviewedDecisions([queue], [binding], [_negativeDecision()])

    assert positives == []
    assert negatives[0]["negativeType"] == "reversedDirection"
    assert negatives[0]["expectedStatus"] == "reject"
    assert negatives[0]["reviewMethod"] == "documentOpened"
    assert report["promotedHardNegativeCount"] == 1


def testEmptyAndDeferredDecisionsNeverCreateGold() -> None:
    """Decision 부재와 defer review는 어떤 gold record도 생성하지 않는다.

    Capabilities
        No-review 및 inconclusive-review fail-closed behavior를 검증한다.
    AIContext
        AI 역할: 검토 대기 또는 판단 보류를 음성·양성 gold로 추측하지 않는다.
    Guide
        빈 decision과 review reason이 있는 defer decision을 각각 실행한다.
    When
        Dry-run report나 defer semantics 변경 시 실행한다.
    How
        같은 queue 및 binding에 두 decision 상태를 차례로 전달한다.
    Requires
        In-memory queue와 source binding.
    Returns:
        None.
    Raises:
        AssertionError: Decision 없이 record가 승격될 때.
    Example:
        ``testEmptyAndDeferredDecisionsNeverCreateGold()``
    SeeAlso:
        :func:`promoteReviewedDecisions`.
    """

    empty = promoteReviewedDecisions([_queue()], [_binding()], [])
    defer = {
        **_reviewBase(),
        "decision": "defer",
        "reviewReason": "원문 시각을 확인할 추가 receipt가 필요하다.",
    }
    deferred = promoteReviewedDecisions([_queue()], [_binding()], [defer])

    assert empty[0] == empty[1] == []
    assert empty[2]["unreviewedQueueCount"] == 1
    assert deferred[0] == deferred[1] == []
    assert deferred[2]["deferredCount"] == 1
    assert deferred[2]["uniqueReviewReceiptCount"] == 1


def testReviewDecisionJsonSchemaMatchesCompilerInputs() -> None:
    """Published JSON Schema가 positive, negative, defer decision과 human-only origin을 표현한다.

    Capabilities
        Reviewer-facing schema와 compiler fixture의 structural 및 date-time contract를 검증한다.
    AIContext
        AI 역할: 운영자가 compiler field를 추측하지 않고 validation 가능한 decision을 작성하게 한다.
    Guide
        세 valid decision을 schema로 검증하고 machine-origin variant의 validation error를 확인한다.
    When
        Decision schema, compiler required field 또는 review workflow 변경 시 실행한다.
    How
        Draft 2020-12 validator와 format checker로 committed schema를 평가한다.
    Requires
        Jsonschema runtime과 committed decision schema JSON.
    Returns:
        None.
    Raises:
        AssertionError: Valid fixture가 실패하거나 machine origin이 통과할 때.
    Example:
        ``testReviewDecisionJsonSchemaMatchesCompilerInputs()``
    SeeAlso:
        :func:`promoteReviewedDecisions`.
    """

    schema = json.loads((ROOT / "releaseGoldReviewDecision.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    defer = {
        **_reviewBase(),
        "decision": "defer",
        "reviewReason": "추가 source time 확인이 필요하다.",
    }

    validator.validate(_positiveDecision())
    validator.validate(_negativeDecision())
    validator.validate(defer)
    machine = {**_positiveDecision(), "origin": "machineCandidate"}
    assert list(validator.iter_errors(machine))


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda decision: decision.update({"origin": "machineCandidate"}), "origin"),
        (lambda decision: decision.update({"subjectId": "krx:999999"}), "confirmed triple"),
        (lambda decision: decision.update({"selectedLocatorId": "source:locator:missing"}), "selectedLocatorId"),
        (
            lambda decision: decision.update(
                {"sourcePublishedAt": "2026-01-03T00:00:00Z", "availableAt": "2026-01-02T00:00:00Z"}
            ),
            "sourcePublishedAt",
        ),
        (lambda decision: decision.update({"reviewedAt": "2026-07-16T10:00:00"}), "timezone-aware"),
    ],
)
def testPositivePromotionRejectsIncompleteOrMismatchedReview(mutate, message: str) -> None:
    """Machine origin, triple drift, unknown locator, inverted time, naive review time을 거부한다.

    Capabilities
        Positive promotion의 human, identity, locator, bitemporal validation을 검증한다.
    AIContext
        AI 역할: 부분적으로 그럴듯한 decision을 release gold로 통과시키지 않는다.
    Guide
        Valid decision 하나를 각 unsafe variant로 변형해 ValueError를 확인한다.
    When
        Review decision validator 또는 time rule 변경 시 실행한다.
    How
        Parametrized mutator를 decision copy에 적용하고 compiler를 호출한다.
    Requires
        Pytest와 valid base review fixture.
    Args:
        mutate: Decision을 invalid state로 바꾸는 callable.
        message: Expected error message fragment.
    Returns:
        None.
    Raises:
        AssertionError: Unsafe review가 거부되지 않거나 메시지가 다를 때.
    Example:
        ``testPositivePromotionRejectsIncompleteOrMismatchedReview(lambda row: None, 'origin')``
    SeeAlso:
        :func:`promoteReviewedDecisions`.
    """

    decision = deepcopy(_positiveDecision())
    mutate(decision)

    with pytest.raises(ValueError, match=message):
        promoteReviewedDecisions([_queue()], [_binding()], [decision])


def testPromotionRejectsDuplicateAndIncompleteJoinIdentity() -> None:
    """Duplicate review receipt와 queue-binding coverage 결손을 거부한다.

    Capabilities
        Review batch uniqueness 및 source binding 1:1 join invariant를 검증한다.
    AIContext
        AI 역할: 같은 사람 receipt 재사용이나 provenance 없는 decision을 숨기지 않는다.
    Guide
        Binding 0건과 duplicate receipt decision batch를 각각 compiler에 전달한다.
    When
        Batch join 또는 receipt uniqueness 변경 시 실행한다.
    How
        Missing binding 및 두 candidate decision fixture에서 ValueError를 확인한다.
    Requires
        In-memory queue, binding, review fixtures.
    Returns:
        None.
    Raises:
        AssertionError: Incomplete join 또는 duplicate receipt가 허용될 때.
    Example:
        ``testPromotionRejectsDuplicateAndIncompleteJoinIdentity()``
    SeeAlso:
        :func:`promoteReviewedDecisions`.
    """

    with pytest.raises(ValueError, match="coverage"):
        promoteReviewedDecisions([_queue()], [], [])

    secondQueue = {**_queue(), "candidateId": "review:candidate:test-b"}
    secondBinding = {**_binding(), "candidateId": secondQueue["candidateId"]}
    secondDecision = {**_positiveDecision(), "candidateId": secondQueue["candidateId"]}
    with pytest.raises(ValueError, match="duplicate reviewReceiptId"):
        promoteReviewedDecisions(
            [_queue(), secondQueue],
            [_binding(), secondBinding],
            [_positiveDecision(), secondDecision],
        )


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda binding: binding["locatorCandidates"][0].update({"charEnd": 99}), "text boundary"),
        (lambda binding: binding["locatorCandidates"][0].update({"evidenceText": "다온"}), "evidence differs"),
    ],
)
def testPositivePromotionRejectsTamperedSourceBinding(mutate, message: str) -> None:
    """Locator boundary와 candidate evidence가 변조된 source binding을 거부한다.

    Capabilities
        Promotion compiler의 selected locator integrity validation을 검증한다.
    AIContext
        AI 역할: content-addressed receipt 밖에서 수정된 binding을 human gold에 사용하지 않는다.
    Guide
        Valid binding의 span 또는 evidence text를 변조해 명시적 ValueError를 확인한다.
    When
        Source binding schema나 positive promotion locator mapping 변경 시 실행한다.
    How
        Parametrized mutator를 binding copy에 적용하고 compiler를 호출한다.
    Requires
        Pytest와 valid queue, review decision fixtures.
    Args:
        mutate: Binding locator를 invalid state로 바꾸는 callable.
        message: Expected error message fragment.
    Returns:
        None.
    Raises:
        AssertionError: Tampered binding이 승격되거나 오류 메시지가 다를 때.
    Example:
        ``testPositivePromotionRejectsTamperedSourceBinding(lambda row: None, 'text boundary')``
    SeeAlso:
        :func:`promoteReviewedDecisions`.
    """

    binding = deepcopy(_binding())
    mutate(binding)

    with pytest.raises(ValueError, match=message):
        promoteReviewedDecisions([_queue()], [binding], [_positiveDecision()])


def testCommittedPromotionReceiptProvesZeroMachineGold() -> None:
    """Committed dry-run receipt가 queue와 binding을 고정하고 machine gold 0건을 증명한다.

    Capabilities
        Promotion input hashes, empty decision, zero output, blocker receipt를 검증한다.
    AIContext
        AI 역할: source binding 완료를 human review 완료로 오판하지 않는다.
    Guide
        Receipt의 queue 및 binding hash를 실제 file bytes와 비교하고 승격 count를 확인한다.
    When
        Review queue, binding, promotion compiler 또는 dry-run receipt 변경 시 실행한다.
    How
        Repository asset 세 개를 읽어 content address와 zero-promotion invariant를 검사한다.
    Requires
        Committed review queue, source binding, promotion receipt files.
    Returns:
        None.
    Raises:
        AssertionError: Machine row가 승격되거나 input receipt가 stale일 때.
    Example:
        ``testCommittedPromotionReceiptProvesZeroMachineGold()``
    SeeAlso:
        :func:`promoteReviewedDecisions`.
    """

    receipt = json.loads((ROOT / "releaseGoldReviewPromotionReceipt.json").read_text(encoding="utf-8"))
    queueBytes = (ROOT / "releaseGoldReviewQueue.machine.jsonl").read_bytes()
    bindingBytes = (ROOT / "releaseGoldSourceBinding.machine.jsonl").read_bytes()

    assert receipt["queueFile"]["sha256"] == f"sha256:{hashlib.sha256(queueBytes).hexdigest()}"
    assert receipt["bindingFile"]["sha256"] == f"sha256:{hashlib.sha256(bindingBytes).hexdigest()}"
    assert receipt["decisionFile"] is None
    assert receipt["decisionCount"] == 0
    assert receipt["promotedPositiveCount"] == 0
    assert receipt["promotedHardNegativeCount"] == 0
    assert receipt["allPromotedRowsHumanReviewed"] is False
    assert receipt["goldAdmissionReady"] is False
