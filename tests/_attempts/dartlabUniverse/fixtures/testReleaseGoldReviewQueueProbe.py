"""releaseGoldReviewQueueProbe의 locator, determinism, honesty receipt를 검증한다."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from tests._attempts.dartlabUniverse.fixtures.releaseGoldReviewQueueProbe import buildReviewQueues

HASH_A = f"sha256:{'a' * 64}"
HASH_B = f"sha256:{'b' * 64}"
ROOT = Path(__file__).resolve().parent


def _graph() -> dict:
    return {
        "version": "fixture-v1",
        "nodes": [
            {"id": "000001", "label": "가람"},
            {"id": "000002", "label": "나래"},
            {"id": "000003", "label": "다온"},
            {"id": "000004", "label": "IT"},
        ],
        "links": [
            {"source": "000001", "target": "000002", "type": "supplier", "source_tag": "panel_text"},
            {"source": "000001", "target": "000003", "type": "affiliate", "source_tag": "panel_text"},
            {"source": "000002", "target": "000003", "type": "customer", "source_tag": "panel_table"},
            {"source": "000003", "target": "000004", "type": "investor", "source_tag": "panel_text"},
            {"source": "000001", "target": "000001", "type": "affiliate", "source_tag": "panel_text"},
        ],
    }


def _row(stockCode: str, sourceRef: str, text: str, *, deleted: bool = False) -> dict:
    return {
        "docKey": f"doc:{sourceRef}",
        "source": "dartPanel",
        "sourceRef": sourceRef,
        "sectionKey": "사업/관계",
        "stockCode": stockCode,
        "companyName": {"000001": "가람", "000002": "나래", "000003": "다온"}[stockCode],
        "date": "2026-03-31",
        "reportName": "사업보고서",
        "title": "관계 현황",
        "searchText": text,
        "textHash": "c" * 64,
        "deleted": deleted,
        "sourceDataAsOf": "2026-04-01",
        "sourceAdapterVersion": "fixture-v1",
    }


def _rows() -> list[dict]:
    return [
        _row("000001", "dart:1#section=1", "가람은 나래 및 다온과 거래한다."),
        _row("000002", "dart:2#section=1", "나래는 가람에서 공급받고 다온에 판매한다."),
        _row("000003", "dart:3#section=1", "다온은 나래 및 IT와 관련된다."),
        _row("000001", "dart:deleted#section=1", "나래", deleted=True),
    ]


def testBuildReviewQueuesIsDeterministicAcrossRowOrder() -> None:
    """Catalog row 순서가 바뀌어도 candidate와 challenge identity를 유지한다.

    Capabilities
        Stable hash selection의 row-order independence를 검증한다.
    AIContext
        AI 역할: 실행 순서 차이를 새로운 review 작업으로 오인하지 않게 한다.
    Guide
        같은 snapshot hash와 같은 row set의 정방향 및 역방향 결과를 비교한다.
    When
        Queue selection 또는 candidate identity 알고리즘 변경 시 실행한다.
    How
        Fixture rows를 뒤집어 두 번 build하고 전체 반환값을 비교한다.
    Requires
        In-memory fixture graph와 catalog rows.
    Returns:
        None.
    Raises:
        AssertionError: 반환 queue 또는 receipt가 달라질 때.
    Example:
        ``testBuildReviewQueuesIsDeterministicAcrossRowOrder()``
    SeeAlso:
        :func:`buildReviewQueues`.
    """

    expected = buildReviewQueues(_graph(), _rows(), HASH_A, HASH_B, limit=20)
    actual = buildReviewQueues(_graph(), list(reversed(_rows())), HASH_A, HASH_B, limit=20)

    assert actual == expected


def testPositiveCandidatePinsExactCatalogLocatorWithoutGoldClaim() -> None:
    """Positive candidate가 exact mention 범위와 hash를 고정하되 gold를 주장하지 않는다.

    Capabilities
        Locator integrity와 machine-candidate honesty boundary를 함께 검증한다.
    AIContext
        AI 역할: exact 문자열 발견을 relation 사실 승인으로 과대 해석하지 않는다.
    Guide
        원문 slice, review state, missing field, reviewer receipt를 한 record에서 검사한다.
    When
        Candidate schema나 locator 계산 변경 시 실행한다.
    How
        ``나래`` mention candidate를 찾고 fixture searchText slice와 비교한다.
    Requires
        In-memory fixture graph와 catalog rows.
    Returns:
        None.
    Raises:
        AssertionError: locator 또는 gold boundary가 깨질 때.
    Example:
        ``testPositiveCandidatePinsExactCatalogLocatorWithoutGoldClaim()``
    SeeAlso:
        :func:`buildReviewQueues`.
    """

    positives, _, _ = buildReviewQueues(_graph(), _rows(), HASH_A, HASH_B, limit=20)
    candidate = next(
        record for record in positives if record["sourceRef"] == "dart:1#section=1" and record["mentionLabel"] == "나래"
    )
    sourceText = _rows()[0]["searchText"]

    assert sourceText[candidate["charStart"] : candidate["charEnd"]] == candidate["evidenceText"] == "나래"
    assert candidate["catalogContentHash"] == f"sha256:{'c' * 64}"
    assert candidate["origin"] == "machineCandidate"
    assert candidate["reviewState"] == "unreviewed"
    assert candidate["goldEligible"] is False
    assert candidate["sourceVersion"] is None
    assert candidate["reviewReceiptId"] is None
    assert "predicateAndDirectionHumanConfirmation" in candidate["missingGoldFields"]


def testHardNegativeChallengesRemainUnreviewedAndTraceable() -> None:
    """Negative challenge가 source candidate로 추적되며 reviewed reject를 흉내 내지 않는다.

    Capabilities
        Transformation provenance, unreviewed state, negative type support를 검증한다.
    AIContext
        AI 역할: 기계 반례를 사람이 확인한 hard negative처럼 표시하지 않는다.
    Guide
        각 challenge의 basedOnCandidateId가 positive 또는 self-loop candidate에 연결되는지 본다.
    When
        Negative challenge transformation이나 schema 변경 시 실행한다.
    How
        Queue를 만들고 challenge field 및 대표 type을 검사한다.
    Requires
        In-memory fixture graph와 catalog rows.
    Returns:
        None.
    Raises:
        AssertionError: provenance 또는 review boundary가 깨질 때.
    Example:
        ``testHardNegativeChallengesRemainUnreviewedAndTraceable()``
    SeeAlso:
        :func:`buildReviewQueues`.
    """

    positives, negatives, _ = buildReviewQueues(_graph(), _rows(), HASH_A, HASH_B, limit=20)
    positiveIds = {record["candidateId"] for record in positives}

    assert negatives
    assert all(record["origin"] == "machineChallenge" for record in negatives)
    assert all(record["reviewState"] == "unreviewed" for record in negatives)
    assert all(record["goldEligible"] is False for record in negatives)
    assert all(record["reviewReceiptId"] is None for record in negatives)
    assert any(record["basedOnCandidateId"] in positiveIds for record in negatives)
    assert all(record["evidenceText"] == record["mentionLabel"] for record in negatives)
    assert all(record["contextText"] for record in negatives)
    assert all(record["graphSnapshotHash"] == HASH_A for record in negatives)
    assert {record["negativeType"] for record in negatives} >= {
        "affiliateEntityCollision",
        "reversedDirection",
        "tableHeaderDrift",
    }


def testReceiptExposesCoverageGapsAndDeletedRows() -> None:
    """Receipt가 미지원 release negative type과 삭제 row 제외를 숨기지 않는다.

    Capabilities
        Coverage gap, scanned count, honesty flags, release blocker를 검증한다.
    AIContext
        AI 역할: 300개 파일 생성 자체를 sampling quota 충족으로 오판하지 않는다.
    Guide
        Live graduation에 필요한 US/SEC 및 사람 검토 blocker를 receipt에서 확인한다.
    When
        Report schema, filter 또는 release quota가 바뀔 때 실행한다.
    How
        Deleted-only mention을 포함한 fixture를 build하고 aggregate receipt를 검사한다.
    Requires
        In-memory fixture graph와 catalog rows.
    Returns:
        None.
    Raises:
        AssertionError: gap 또는 deleted filtering이 사라질 때.
    Example:
        ``testReceiptExposesCoverageGapsAndDeletedRows()``
    SeeAlso:
        :func:`buildReviewQueues`.
    """

    positives, negatives, report = buildReviewQueues(_graph(), _rows(), HASH_A, HASH_B, limit=20)

    assert report["scannedCatalogRowCount"] == 4
    assert all(record["sourceRef"] != "dart:deleted#section=1" for record in positives)
    assert all(record["candidateSourceRef"] != "dart:deleted#section=1" for record in negatives)
    assert report["allRowsUnreviewed"] is True
    assert report["allRowsGoldIneligible"] is True
    assert report["locatorParityFailureCount"] == 0
    assert report["goldAdmissionReady"] is False
    assert "classifiedIn" in report["uncoveredReleasePositivePredicates"]
    assert "sameNameDifferentEntity" in report["uncoveredReleaseNegativeTypes"]
    assert "humanReviewMissing" in report["blockers"]
    assert "KRGraphCannotSatisfyUSAndSECQuota" in report["blockers"]


def testCommittedMachineQueueMatchesContentAddressedReceipt() -> None:
    """Committed machine queue 600행과 receipt hash 및 context locator를 검증한다.

    Capabilities
        Generated review asset의 row count, lane, content hash, self-contained locator를 검증한다.
    AIContext
        AI 역할: source 갱신 후 stale queue나 수동 편집 drift를 release 입력으로 쓰지 않는다.
    Guide
        Queue bytes를 직접 hash하고 모든 record의 context slice가 evidenceText인지 확인한다.
    When
        Queue 재생성, source snapshot 변경 또는 fixture release 전 실행한다.
    How
        Repository JSONL 및 receipt JSON을 읽어 content-addressed invariant를 전수 검사한다.
    Requires
        Committed ``releaseGoldReviewQueue.machine.jsonl``과 receipt file.
    Returns:
        None.
    Raises:
        AssertionError: file hash, count, lane 또는 locator가 receipt와 다를 때.
    Example:
        ``testCommittedMachineQueueMatchesContentAddressedReceipt()``
    SeeAlso:
        :func:`buildReviewQueues`.
    """

    queuePath = ROOT / "releaseGoldReviewQueue.machine.jsonl"
    receipt = json.loads((ROOT / "releaseGoldReviewQueueReceipt.json").read_text(encoding="utf-8"))
    queueBytes = queuePath.read_bytes()
    records = [json.loads(line) for line in queueBytes.decode("utf-8").splitlines() if line]

    assert f"sha256:{hashlib.sha256(queueBytes).hexdigest()}" == receipt["queueFile"]["sha256"]
    assert len(records) == receipt["queueFile"]["rowCount"] == 600
    assert sum(record["lane"] == "positiveCandidate" for record in records) == 300
    assert sum(record["lane"] == "hardNegativeChallenge" for record in records) == 300
    assert len({record["candidateId"] for record in records}) == 600
    assert all(record["reviewState"] == "unreviewed" for record in records)
    assert all(record["goldEligible"] is False for record in records)
    for record in records:
        relativeStart = record["charStart"] - record["contextStart"]
        relativeEnd = record["charEnd"] - record["contextStart"]
        assert record["contextText"][relativeStart:relativeEnd] == record["evidenceText"]


@pytest.mark.parametrize(
    ("graphHash", "catalogHash", "limit", "message"),
    [
        ("bad", HASH_B, 1, "graphSnapshotHash"),
        (HASH_A, "bad", 1, "catalogSnapshotHash"),
        (HASH_A, HASH_B, 0, "limit"),
    ],
)
def testBuildReviewQueuesRejectsInvalidBoundary(graphHash: str, catalogHash: str, limit: int, message: str) -> None:
    """Invalid digest와 non-positive limit를 즉시 거부한다.

    Capabilities
        Snapshot identity와 queue size boundary validation을 검증한다.
    AIContext
        AI 역할: 재현 불가능한 source identity로 review queue를 만들지 않는다.
    Guide
        각 invalid input이 명시적인 ValueError를 내는지 확인한다.
    When
        Public builder signature나 validation 변경 시 실행한다.
    How
        Parametrized invalid values를 :func:`buildReviewQueues`에 전달한다.
    Requires
        Pytest와 in-memory fixture graph.
    Args:
        graphHash: Test graph digest.
        catalogHash: Test catalog digest.
        limit: Test queue limit.
        message: Expected error message fragment.
    Returns:
        None.
    Raises:
        AssertionError: invalid input이 거부되지 않거나 메시지가 다를 때.
    Example:
        ``testBuildReviewQueuesRejectsInvalidBoundary('bad', HASH_B, 1, 'graphSnapshotHash')``
    SeeAlso:
        :func:`buildReviewQueues`.
    """

    with pytest.raises(ValueError, match=message):
        buildReviewQueues(deepcopy(_graph()), _rows(), graphHash, catalogHash, limit=limit)
