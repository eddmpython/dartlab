"""releaseGoldSourceBindingProbe의 source version, locator, ambiguity 경계를 검증한다."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from tests._attempts.dartlabUniverse.fixtures.releaseGoldSourceBindingProbe import (
    buildOriginalSourceBindings,
)

HASH_A = f"sha256:{'a' * 64}"
HASH_B = f"sha256:{'b' * 64}"
ALL_PATH = "data/dart/allFilings/20260102.parquet"
PANEL_PATH = "data/dart/panel/000001.parquet"
ROOT = Path(__file__).resolve().parent


def _candidate(candidateId: str = "review:candidate:test-a") -> dict:
    return {
        "candidateId": candidateId,
        "lane": "positiveCandidate",
        "reviewState": "unreviewed",
        "goldEligible": False,
        "catalogSource": "allFilings",
        "sourceRef": "dart:allFilings:20260102000123#section=0",
        "issuerStockCode": "000001",
        "evidenceText": "나래",
    }


def _challenge() -> dict:
    return {
        "candidateId": "review:challenge:test-b",
        "lane": "hardNegativeChallenge",
        "reviewState": "unreviewed",
        "goldEligible": False,
        "catalogSource": "dartPanel",
        "candidateSourceRef": "dart:panel:20260103000456#section=0",
        "issuerStockCode": "000001",
        "evidenceText": "다온",
    }


def _artifacts() -> tuple[dict, dict]:
    rows = {
        ALL_PATH: [
            {"rcept_no": "20260102000123", "content_raw": "가람은 나래와 거래한다."},
            {"rcept_no": "20260102000999", "content_raw": "무관한 행"},
        ],
        PANEL_PATH: [
            {
                "rceptNo": "20260103000456",
                "blockOrder": 1,
                "sectionPath": "사업/관계",
                "contentRaw": "다온과 관계가 있다. 다온은 별도 문맥이다.",
            },
            {
                "rceptNo": "20260103000456",
                "blockOrder": 2,
                "sectionPath": "주석/관계",
                "contentRaw": "다온이 다시 나온다.",
            },
        ],
    }
    hashes = {ALL_PATH: HASH_A, PANEL_PATH: HASH_B}
    return rows, hashes


def testBuildOriginalSourceBindingsPinsUniqueOriginalLocator() -> None:
    """AllFilings candidate를 source file hash와 유일한 raw-text locator에 결속한다.

    Capabilities
        Exact unique source binding의 file, row, content, char hash를 검증한다.
    AIContext
        AI 역할: catalog locator 대신 original artifact locator를 review 선택지로 제공한다.
    Guide
        한 번만 등장하는 ``나래`` mention의 binding과 context parity를 검사한다.
    When
        Original source locator schema 또는 hashing 변경 시 실행한다.
    How
        In-memory allFilings row와 queue candidate를 pure builder에 전달한다.
    Requires
        Standard-library fixture와 valid SHA-256 digest.
    Returns:
        None.
    Raises:
        AssertionError: Source version이나 exact locator가 달라질 때.
    Example:
        ``testBuildOriginalSourceBindingsPinsUniqueOriginalLocator()``
    SeeAlso:
        :func:`buildOriginalSourceBindings`.
    """

    rows, hashes = _artifacts()
    bindings, report = buildOriginalSourceBindings([_candidate()], rows, hashes)
    binding = bindings[0]
    locator = binding["locatorCandidates"][0]

    assert binding["bindingStatus"] == "exactUnique"
    assert binding["originalSourcePath"] == ALL_PATH
    assert binding["originalSourceVersion"] == HASH_A
    assert binding["exactLocatorCount"] == 1
    assert locator["receiptNo"] == "20260102000123"
    assert locator["evidenceText"] == "나래"
    assert (
        locator["contextText"][
            locator["charStart"] - locator["contextStart"] : locator["charEnd"] - locator["contextStart"]
        ]
        == "나래"
    )
    assert report["sourceArtifactReadyCount"] == 1
    assert report["locatorParityFailureCount"] == 0


def testAmbiguousPanelBindingReturnsCandidatesWithoutChoosing() -> None:
    """Panel의 다중 exact occurrence를 모두 ambiguity로 남기고 자동 선택하지 않는다.

    Capabilities
        Multi-row, multi-occurrence locator와 truncation receipt를 검증한다.
    AIContext
        AI 역할: 반복 회사명 중 관계를 입증하는 행을 임의로 고르지 않는다.
    Guide
        세 occurrence를 limit 2로 요청해 truncated 상태와 null selection을 확인한다.
    When
        Panel source binding이나 locator limit 변경 시 실행한다.
    How
        Challenge record와 반복 mention panel rows를 pure builder에 전달한다.
    Requires
        In-memory panel source rows.
    Returns:
        None.
    Raises:
        AssertionError: Ambiguity가 숨겨지거나 locator가 자동 선택될 때.
    Example:
        ``testAmbiguousPanelBindingReturnsCandidatesWithoutChoosing()``
    SeeAlso:
        :func:`buildOriginalSourceBindings`.
    """

    rows, hashes = _artifacts()
    bindings, _ = buildOriginalSourceBindings([_challenge()], rows, hashes, locatorLimit=2)
    binding = bindings[0]

    assert binding["bindingStatus"] == "exactAmbiguousTruncated"
    assert binding["exactLocatorCount"] == 3
    assert binding["returnedLocatorCount"] == 2
    assert binding["selectedLocatorId"] is None
    assert binding["reviewState"] == "unreviewed"
    assert binding["goldEligible"] is False
    assert {locator["receiptRowIndex"] for locator in binding["locatorCandidates"]} == {0}


def testMissingSourceAndReceiptRemainDistinctFailClosedStates() -> None:
    """Source file 부재와 file 안 receipt row 부재를 서로 다른 blocker로 보존한다.

    Capabilities
        Missing artifact 및 missing source row 상태 분리를 검증한다.
    AIContext
        AI 역할: source 결손을 exact mention 0건이라는 하나의 상태로 뭉개지 않는다.
    Guide
        하나는 artifact mapping을 빼고 다른 하나는 receipt가 없는 row를 공급한다.
    When
        Source readiness report나 missing-path 처리 변경 시 실행한다.
    How
        두 candidate를 개별 builder 호출로 평가해 status를 비교한다.
    Requires
        In-memory queue records와 partial artifact mappings.
    Returns:
        None.
    Raises:
        AssertionError: Missing 상태가 혼합되거나 gold eligible이 될 때.
    Example:
        ``testMissingSourceAndReceiptRemainDistinctFailClosedStates()``
    SeeAlso:
        :func:`buildOriginalSourceBindings`.
    """

    missingFile, _ = buildOriginalSourceBindings([_candidate()], {}, {})
    missingRow, _ = buildOriginalSourceBindings(
        [_candidate()],
        {ALL_PATH: [{"rcept_no": "20260102000999", "content_raw": "나래"}]},
        {ALL_PATH: HASH_A},
    )

    assert missingFile[0]["bindingStatus"] == "sourceFileMissing"
    assert missingFile[0]["originalSourceVersion"] is None
    assert missingRow[0]["bindingStatus"] == "sourceRowMissing"
    assert missingRow[0]["originalSourceVersion"] == HASH_A
    assert missingFile[0]["goldEligible"] is missingRow[0]["goldEligible"] is False


def testBindingSelectionIsIndependentOfQueueOrder() -> None:
    """Queue 입력 순서가 달라도 binding identity와 aggregate receipt를 재현한다.

    Capabilities
        Candidate sorting과 content-addressed binding determinism을 검증한다.
    AIContext
        AI 역할: reviewer batch 순서 변경을 source provenance 변경으로 오인하지 않는다.
    Guide
        같은 source rows에 정방향 및 역방향 queue를 전달해 결과 전체를 비교한다.
    When
        Binding ordering, ID 또는 report aggregation 변경 시 실행한다.
    How
        두 candidate queue의 순서만 바꿔 builder를 두 번 호출한다.
    Requires
        In-memory allFilings 및 panel artifacts.
    Returns:
        None.
    Raises:
        AssertionError: Queue 순서에 따라 binding이나 report가 달라질 때.
    Example:
        ``testBindingSelectionIsIndependentOfQueueOrder()``
    SeeAlso:
        :func:`buildOriginalSourceBindings`.
    """

    rows, hashes = _artifacts()
    queue = [_candidate(), _challenge()]

    assert buildOriginalSourceBindings(queue, rows, hashes) == buildOriginalSourceBindings(
        list(reversed(queue)), rows, hashes
    )


def testCommittedLiveBindingsMatchContentAddressedReceipt() -> None:
    """Committed 600 binding의 file hash, coverage, locator parity, review boundary를 검증한다.

    Capabilities
        Live binding JSONL과 receipt의 content address 및 전수 invariant를 검증한다.
    AIContext
        AI 역할: source file 또는 queue 갱신 뒤 stale binding을 reviewer에게 제공하지 않는다.
    Guide
        Binding bytes를 hash하고 600 record와 returned locator 전체를 순회한다.
    When
        Live binding 재생성, source snapshot 변경 또는 fixture release 전 실행한다.
    How
        Repository binding JSONL과 receipt JSON을 읽어 recorded hash와 aggregate를 비교한다.
    Requires
        Committed source binding JSONL 및 receipt assets.
    Returns:
        None.
    Raises:
        AssertionError: Hash, count, locator 또는 unreviewed boundary가 다를 때.
    Example:
        ``testCommittedLiveBindingsMatchContentAddressedReceipt()``
    SeeAlso:
        :func:`buildOriginalSourceBindings`.
    """

    bindingPath = ROOT / "releaseGoldSourceBinding.machine.jsonl"
    receipt = json.loads((ROOT / "releaseGoldSourceBindingReceipt.json").read_text(encoding="utf-8"))
    bindingBytes = bindingPath.read_bytes()
    bindings = [json.loads(line) for line in bindingBytes.decode("utf-8").splitlines() if line]

    assert f"sha256:{hashlib.sha256(bindingBytes).hexdigest()}" == receipt["bindingFile"]["sha256"]
    assert len(bindings) == receipt["bindingFile"]["rowCount"] == 600
    assert sum(binding["sourceArtifactReady"] for binding in bindings) == 597
    assert receipt["sourceArtifactCount"] == receipt["expectedSourceArtifactCount"] == 306
    assert receipt["locatorParityFailureCount"] == 0
    assert receipt["bindingStatusCounts"]["sourceRowMissing"] == 3
    assert all(binding["reviewState"] == "unreviewed" for binding in bindings)
    assert all(binding["goldEligible"] is False for binding in bindings)
    assert all(binding["selectedLocatorId"] is None for binding in bindings)
    for binding in bindings:
        for locator in binding["locatorCandidates"]:
            relativeStart = locator["charStart"] - locator["contextStart"]
            relativeEnd = locator["charEnd"] - locator["contextStart"]
            assert locator["contextText"][relativeStart:relativeEnd] == locator["evidenceText"]


@pytest.mark.parametrize(
    ("queue", "rows", "hashes", "limit", "message"),
    [
        ([_candidate(), _candidate()], {}, {}, 50, "duplicate candidateId"),
        ([_candidate()], {ALL_PATH: []}, {ALL_PATH: "bad"}, 50, "source digest"),
        ([_candidate()], {}, {}, 0, "locatorLimit"),
        ([{**_candidate(), "reviewState": "reviewed"}], {ALL_PATH: []}, {ALL_PATH: HASH_A}, 50, "unreviewed"),
    ],
)
def testBuildOriginalSourceBindingsRejectsUnsafeBoundary(
    queue: list[dict], rows: dict, hashes: dict, limit: int, message: str
) -> None:
    """Duplicate identity, mutable digest, invalid limit, pre-reviewed machine row를 거부한다.

    Capabilities
        Public builder의 identity, provenance, size, review-state validation을 검증한다.
    AIContext
        AI 역할: 불변 source와 review separation이 깨진 binding을 생성하지 않는다.
    Guide
        Parametrized unsafe input 각각이 명시적인 ValueError를 내야 한다.
    When
        Builder validation이나 queue schema 변경 시 실행한다.
    How
        Invalid queue 및 artifact mappings를 :func:`buildOriginalSourceBindings`에 전달한다.
    Requires
        Pytest와 in-memory fixtures.
    Args:
        queue: Test queue records.
        rows: Test source rows mapping.
        hashes: Test source digest mapping.
        limit: Test locator limit.
        message: Expected error fragment.
    Returns:
        None.
    Raises:
        AssertionError: Unsafe input이 거부되지 않거나 오류 메시지가 다를 때.
    Example:
        ``testBuildOriginalSourceBindingsRejectsUnsafeBoundary([], {}, {}, 0, 'locatorLimit')``
    SeeAlso:
        :func:`buildOriginalSourceBindings`.
    """

    with pytest.raises(ValueError, match=message):
        buildOriginalSourceBindings(deepcopy(queue), deepcopy(rows), deepcopy(hashes), locatorLimit=limit)
