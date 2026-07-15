"""exactEvidenceProbe의 locator와 fail-closed admission 경계를 검증한다."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

from tests._attempts.dartlabUniverse.evidence import (
    EvidenceCandidate,
    EvidenceRequest,
    inspectSearchCatalogEvidence,
    resolveEvidence,
)


def _hashText(value: str) -> str:
    return f"sha256:{hashlib.sha256(value.encode('utf-8')).hexdigest()}"


def _hashValue(value) -> str:
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return _hashText(payload)


def _request() -> EvidenceRequest:
    return EvidenceRequest(
        subjectId="kr:dart:corp:00126380",
        predicate="suppliesTo",
        objectId="kr:dart:corp:00164779",
    )


def _textCandidate(candidateId: str = "text:1") -> EvidenceCandidate:
    content = "삼성전자는 삼성전기에 반도체 부품을 공급한다."
    snippet = "삼성전기에 반도체 부품을 공급"
    start = content.index(snippet)
    return EvidenceCandidate(
        candidateId=candidateId,
        documentId="kr:dart:filing:20260317000632",
        sectionPath="사업의 내용/주요 거래처",
        sectionOrder=17,
        sourceRef="dart:panel:20260317000632#section=17",
        sourcePath="dart/panel/00126380.parquet",
        sourceVersion=f"sha256:{'1' * 64}",
        subjectId=_request().subjectId,
        predicate=_request().predicate,
        objectId=_request().objectId,
        direction="subjectToObject",
        sourcePublishedAt="2026-03-17T08:00:00+09:00",
        availableAt="2026-03-17T09:02:00+09:00",
        locatorKind="text",
        content=content,
        contentHash=_hashText(content),
        charStart=start,
        charEnd=start + len(snippet),
        snippetHash=_hashText(snippet),
    )


def _tableCandidate() -> EvidenceCandidate:
    header = ("거래처", "관계", "매출 비중")
    rows = (("삼성전기", "공급", "12.4%"), ("기타", "공급", "87.6%"))
    return EvidenceCandidate(
        candidateId="table:1",
        documentId="kr:dart:filing:20260317000632",
        sectionPath="사업의 내용/주요 거래처 표",
        sectionOrder=18,
        sourceRef="dart:panel:20260317000632#section=18",
        sourcePath="dart/panel/00126380.parquet",
        sourceVersion=f"sha256:{'2' * 64}",
        subjectId=_request().subjectId,
        predicate=_request().predicate,
        objectId=_request().objectId,
        direction="subjectToObject",
        sourcePublishedAt="2026-03-17T08:00:00Z",
        availableAt="2026-03-17T08:02:00Z",
        locatorKind="table",
        contentHash=_hashValue({"header": header, "rows": rows}),
        tableHeader=header,
        tableRows=rows,
        rowIndex=0,
        headerHash=_hashValue(header),
        rowHash=_hashValue(rows[0]),
    )


def _assertExactTextPointerResolves() -> None:
    resolution = resolveEvidence(_request(), [_textCandidate()])
    assert resolution.status == "resolved"
    assert resolution.pointer is not None
    assert resolution.pointer.textLocator is not None
    assert resolution.pointer.textLocator.charStart == 6
    assert resolution.pointer.tableLocator is None


def _assertExactTablePointerPreservesHeaderAndRow() -> None:
    resolution = resolveEvidence(_request(), [_tableCandidate()])
    assert resolution.status == "resolved"
    assert resolution.pointer is not None
    assert resolution.pointer.tableLocator is not None
    assert resolution.pointer.tableLocator.rowIndex == 0
    assert resolution.pointer.textLocator is None


def _assertWrongEntityAndPredicateFailClosed() -> None:
    wrongEntity = replace(_textCandidate(), subjectId="kr:dart:corp:00000001")
    wrongPredicate = replace(_textCandidate(), predicate="owns")
    assert resolveEvidence(_request(), [wrongEntity]).status == "ambiguousEntity"
    assert resolveEvidence(_request(), [wrongEntity]).pointer is None
    assert resolveEvidence(_request(), [wrongPredicate]).status == "notFound"


def _assertUnknownDirectionAndTimeFailClosed() -> None:
    unknownDirection = replace(_textCandidate(), direction="unknown")
    missingTime = replace(_textCandidate(), sourcePublishedAt="")
    assert resolveEvidence(_request(), [unknownDirection]).status == "directionUnknown"
    assert resolveEvidence(_request(), [missingTime]).status == "timeUnknown"


def _assertMutableSourceVersionFailsClosed() -> None:
    candidate = replace(_textCandidate(), sourceVersion="dartPanel.v1")
    resolution = resolveEvidence(_request(), [candidate])
    assert resolution.status == "sourceVersionMissing"
    assert resolution.pointer is None


def _assertAlteredTextAndTableLocatorFailClosed() -> None:
    text = replace(_textCandidate(), charEnd=len(_textCandidate().content) + 1)
    table = replace(_tableCandidate(), tableHeader=("거래처", "관계", "비중"))
    assert resolveEvidence(_request(), [text]).status == "locatorInvalid"
    assert resolveEvidence(_request(), [table]).status == "locatorInvalid"


def _assertMultipleExactPointersRemainAmbiguous() -> None:
    candidates = [_textCandidate("text:1"), replace(_textCandidate("text:2"), sectionOrder=19)]
    resolution = resolveEvidence(_request(), candidates)
    assert resolution.status == "ambiguousSource"
    assert resolution.pointer is None


def _assertLiveSearchCatalogEvidenceCensus() -> None:
    repoRoot = Path(__file__).resolve().parents[4]
    dryRunRoot = repoRoot / "data" / "dart" / "searchCatalogDryRun"
    census = inspectSearchCatalogEvidence(
        (
            dryRunRoot / "dartPanel.sample" / "dartPanel.catalog_snapshot.parquet",
            dryRunRoot / "edgarPanel.sample" / "edgarPanel.catalog_snapshot.parquet",
            dryRunRoot / "allFilings" / "allFilings.catalog_snapshot.parquet",
        )
    )
    assert census.representative is False
    assert census.catalogFileCount == 3
    assert census.catalogRowCount == 381149
    assert census.sourceRefRowCount == census.catalogRowCount
    assert census.documentRowCount == census.catalogRowCount
    assert census.sectionLocatorRowCount == census.catalogRowCount
    assert census.contentHashRowCount == census.catalogRowCount
    assert census.sourceDataAsOfRowCount == census.catalogRowCount
    assert census.adapterVersionRowCount == census.catalogRowCount
    assert census.exactTextLocatorRowCount == 0
    assert census.exactTableLocatorRowCount == 0
    assert census.exactTimeRowCount == 0
    assert census.immutableSourceVersionRowCount == 0
    assert census.semanticDirectionRowCount == 0
    assert census.assertionEvidenceReadyRowCount == 0
    assert census.reviewedPositiveCount == 0
    assert census.reviewedHardNegativeCount == 0
    assert census.reviewedMetricsReady is False
    assert census.transferMetricsReady is False
    assert census.liveReady is False


def testExactTextPointerResolves() -> None:
    """Exact character boundary와 immutable source가 단일 pointer를 만드는지 검증한다.

    Example
        ``pytest testExactEvidenceProbe.py``

    Raises
        AssertionError: Exact text pointer가 해소되지 않거나 table locator와 혼합될 때.
    """

    _assertExactTextPointerResolves()


def testExactTablePointerPreservesHeaderAndRow() -> None:
    """Table evidence가 header와 exact row를 함께 보존하는지 검증한다.

    Example
        ``pytest testExactEvidenceProbe.py``

    Raises
        AssertionError: Header 또는 row locator가 소실되거나 text locator와 혼합될 때.
    """

    _assertExactTablePointerPreservesHeaderAndRow()


def testWrongEntityAndPredicateFailClosed() -> None:
    """Wrong entity boundary와 predicate hard negative가 수용되지 않는지 검증한다.

    Example
        ``pytest testExactEvidenceProbe.py``

    Raises
        AssertionError: Wrong entity 또는 predicate에 pointer가 생길 때.
    """

    _assertWrongEntityAndPredicateFailClosed()


def testUnknownDirectionAndTimeFailClosed() -> None:
    """Entity direction과 source time 결손을 명시적인 이유로 차단한다.

    Example
        ``pytest testExactEvidenceProbe.py``

    Raises
        AssertionError: Unknown direction 또는 missing time이 수용될 때.
    """

    _assertUnknownDirectionAndTimeFailClosed()


def testMutableSourceVersionFailsClosed() -> None:
    """Adapter label이 immutable source digest를 대신하지 못하는지 검증한다.

    Example
        ``pytest testExactEvidenceProbe.py``

    Raises
        AssertionError: Mutable adapter label이 source version으로 수용될 때.
    """

    _assertMutableSourceVersionFailsClosed()


def testAlteredTextAndTableLocatorFailClosed() -> None:
    """Altered snippet, header, row가 기존 hash로 수용되지 않는지 검증한다.

    Example
        ``pytest testExactEvidenceProbe.py``

    Raises
        AssertionError: Boundary 또는 table hash drift가 수용될 때.
    """

    _assertAlteredTextAndTableLocatorFailClosed()


def testMultipleExactPointersRemainAmbiguous() -> None:
    """복수 exact source를 첫 행으로 자동 선택하지 않는지 검증한다.

    Example
        ``pytest testExactEvidenceProbe.py``

    Raises
        AssertionError: Multiple exact pointer가 첫 행으로 자동 해소될 때.
    """

    _assertMultipleExactPointersRemainAmbiguous()


def testLiveSearchCatalogEvidenceCensus() -> None:
    """381,149행의 section lookup과 assertion evidence gap을 전수 고정한다.

    Example
        ``pytest testExactEvidenceProbe.py``

    Raises
        AssertionError: Live catalog field count 또는 blocker가 기준선과 달라질 때.
    """

    _assertLiveSearchCatalogEvidenceCensus()
