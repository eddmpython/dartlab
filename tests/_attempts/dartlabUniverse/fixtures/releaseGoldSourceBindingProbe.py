"""Universe review queue를 local original source artifact의 exact locator에 결속한다.

Capabilities
    DART receipt와 issuer key로 original Parquet를 찾고 file SHA-256, row hash, exact char locator를 만든다.

AIContext
    AI 역할: catalog mention을 원본 locator 후보로 이전하되 ambiguous locator와 missing time을 숨기지 않는다.

Guide
    Binding은 source artifact provenance다. Predicate 판정, publication time, availability time, human receipt는 만들지 않는다.

When
    U0-G02 review queue 생성 후 human reviewer에게 원본 행 선택지를 제공할 때 사용한다.

How
    :func:`buildOriginalSourceBindings`로 in-memory source를 검증하거나 CLI로 local Parquet를 전수 결속한다.

Requires
    Pure builder는 standard library만, live inspection은 pyarrow와 local DART source Parquet를 요구한다.

Raises
    ValueError: queue schema, source digest, receipt number 또는 locator limit가 잘못됐을 때.

Example
    ``bindings, report = inspectOriginalSourceBindings(queueRecords)``

See Also
    :mod:`tests._attempts.dartlabUniverse.fixtures.releaseGoldReviewQueueProbe`.

결과
    Exact source locator는 자동 보강하지만 reviewer만 relation과 시간을 승인할 수 있다.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

SHA256_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
RECEIPT_PATTERN = re.compile(r"(?<!\d)(\d{14})(?!\d)")
DEFAULT_QUEUE = Path("tests/_attempts/dartlabUniverse/fixtures/releaseGoldReviewQueue.machine.jsonl")
SOURCE_COLUMNS = {
    "allFilings": ("rcept_no", "content_raw"),
    "dartPanel": ("rceptNo", "blockOrder", "sectionPath", "contentRaw"),
}
BINDING_GAPS = (
    "sourcePublishedAt",
    "availableAt",
    "eventAtAndValidity",
    "predicateAndDirectionHumanConfirmation",
    "publicDocumentLocatorHumanConfirmation",
    "reviewReceipt",
)


def _canonicalHash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return f"sha256:{hashlib.sha256(payload.encode('utf-8')).hexdigest()}"


def _textHash(value: str) -> str:
    return f"sha256:{hashlib.sha256(value.encode('utf-8')).hexdigest()}"


def _fileHash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _receiptNo(record: Mapping[str, Any]) -> str:
    sourceRef = record.get("sourceRef") or record.get("candidateSourceRef")
    match = RECEIPT_PATTERN.search(str(sourceRef or ""))
    if match is None:
        raise ValueError(f"candidate {record.get('candidateId')} sourceRef has no 14-digit receipt")
    return match.group(1)


def _sourceRelativePath(record: Mapping[str, Any], receiptNo: str) -> str:
    catalogSource = str(record.get("catalogSource") or "")
    if catalogSource == "allFilings":
        catalogDate = str(record.get("catalogDate") or "")
        sourceDate = catalogDate if re.fullmatch(r"\d{8}", catalogDate) else receiptNo[:8]
        return f"data/dart/allFilings/{sourceDate}.parquet"
    if catalogSource == "dartPanel":
        stockCode = str(record.get("issuerStockCode") or "").strip()
        if not stockCode:
            raise ValueError(f"candidate {record.get('candidateId')} issuerStockCode is required")
        return f"data/dart/panel/{stockCode}.parquet"
    raise ValueError(f"unsupported catalogSource: {catalogSource}")


def _occurrences(text: str, needle: str) -> list[int]:
    starts: list[int] = []
    cursor = 0
    while True:
        start = text.find(needle, cursor)
        if start < 0:
            return starts
        starts.append(start)
        cursor = start + max(1, len(needle))


def _contextSimilarity(reference: str, candidate: str) -> float:
    normalizedReference = re.sub(r"\s+", "", reference)
    normalizedCandidate = re.sub(r"\s+", "", candidate)
    width = 3
    referenceGrams = {
        normalizedReference[index : index + width] for index in range(max(0, len(normalizedReference) - width + 1))
    }
    candidateGrams = {
        normalizedCandidate[index : index + width] for index in range(max(0, len(normalizedCandidate) - width + 1))
    }
    if not referenceGrams:
        return 0.0
    return round(len(referenceGrams & candidateGrams) / len(referenceGrams), 6)


def _sourceRowPayload(catalogSource: str, row: Mapping[str, Any]) -> tuple[str, int | None, str, str]:
    if catalogSource == "allFilings":
        content = str(row.get("content_raw") or "")
        return content, None, "", str(row.get("rcept_no") or "")
    content = str(row.get("contentRaw") or "")
    rawOrder = row.get("blockOrder")
    blockOrder = int(rawOrder) if isinstance(rawOrder, int) else None
    return content, blockOrder, str(row.get("sectionPath") or ""), str(row.get("rceptNo") or "")


def _buildBinding(
    record: Mapping[str, Any],
    artifactRows: Sequence[Mapping[str, Any]],
    sourceVersion: str,
    sourcePath: str,
    locatorLimit: int,
) -> dict[str, Any]:
    candidateId = str(record.get("candidateId") or "").strip()
    if not candidateId:
        raise ValueError("candidateId is required")
    if record.get("reviewState") != "unreviewed" or record.get("goldEligible") is not False:
        raise ValueError(f"candidate {candidateId} must remain unreviewed and gold-ineligible")
    if not SHA256_PATTERN.fullmatch(sourceVersion):
        raise ValueError(f"source digest invalid for {sourcePath}")
    receiptNo = _receiptNo(record)
    catalogSource = str(record.get("catalogSource") or "")
    evidenceText = str(record.get("evidenceText") or "")
    if not evidenceText:
        raise ValueError(f"candidate {candidateId} evidenceText is required")
    receiptRows: list[tuple[int, Mapping[str, Any]]] = []
    for row in artifactRows:
        _, _, _, rowReceipt = _sourceRowPayload(catalogSource, row)
        if rowReceipt == receiptNo:
            receiptRows.append((len(receiptRows), row))
    locators: list[dict[str, Any]] = []
    totalLocatorCount = 0
    referenceContext = str(record.get("contextText") or "")
    for receiptRowIndex, row in receiptRows:
        content, blockOrder, sectionPath, _ = _sourceRowPayload(catalogSource, row)
        contentHash = _textHash(content)
        rowKey = _canonicalHash(
            {
                "sourcePath": sourcePath,
                "receiptNo": receiptNo,
                "receiptRowIndex": receiptRowIndex,
                "blockOrder": blockOrder,
                "sectionPath": sectionPath,
                "contentHash": contentHash,
            }
        )
        for charStart in _occurrences(content, evidenceText):
            totalLocatorCount += 1
            charEnd = charStart + len(evidenceText)
            contextStart = max(0, charStart - 120)
            contextEnd = min(len(content), charEnd + 120)
            contextText = content[contextStart:contextEnd]
            locatorIdentity = {
                "candidateId": candidateId,
                "rowKey": rowKey,
                "charStart": charStart,
                "charEnd": charEnd,
            }
            locators.append(
                {
                    "locatorId": f"source:locator:{_canonicalHash(locatorIdentity).removeprefix('sha256:')[:24]}",
                    "rowKey": rowKey,
                    "receiptRowIndex": receiptRowIndex,
                    "receiptNo": receiptNo,
                    "blockOrder": blockOrder,
                    "sectionPath": sectionPath,
                    "contentColumn": "content_raw" if catalogSource == "allFilings" else "contentRaw",
                    "contentHash": contentHash,
                    "evidenceText": evidenceText,
                    "charStart": charStart,
                    "charEnd": charEnd,
                    "snippetHash": _textHash(evidenceText),
                    "contextStart": contextStart,
                    "contextEnd": contextEnd,
                    "contextText": contextText,
                    "contextHash": _textHash(contextText),
                    "contextSimilarity": _contextSimilarity(referenceContext, contextText),
                }
            )
    locators.sort(
        key=lambda item: (
            -item["contextSimilarity"],
            item["receiptRowIndex"],
            item["charStart"],
            item["locatorId"],
        )
    )
    locators = locators[:locatorLimit]
    if not receiptRows:
        status = "sourceRowMissing"
    elif totalLocatorCount == 0:
        status = "exactMentionMissing"
    elif totalLocatorCount == 1:
        status = "exactUnique"
    elif totalLocatorCount > locatorLimit:
        status = "exactAmbiguousTruncated"
    else:
        status = "exactAmbiguous"
    bindingIdentity = {
        "candidateId": candidateId,
        "sourcePath": sourcePath,
        "sourceVersion": sourceVersion,
        "receiptNo": receiptNo,
        "locatorIds": [locator["locatorId"] for locator in locators],
        "totalLocatorCount": totalLocatorCount,
    }
    return {
        "schemaVersion": "releaseGoldSourceBinding.v1",
        "bindingId": f"source:binding:{_canonicalHash(bindingIdentity).removeprefix('sha256:')[:24]}",
        "candidateId": candidateId,
        "candidateLane": record.get("lane"),
        "sourceRef": record.get("sourceRef") or record.get("candidateSourceRef"),
        "catalogSource": catalogSource,
        "originalSourcePath": sourcePath,
        "originalSourceVersion": sourceVersion,
        "originalReceiptNo": receiptNo,
        "bindingStatus": status,
        "receiptRowCount": len(receiptRows),
        "exactLocatorCount": totalLocatorCount,
        "returnedLocatorCount": len(locators),
        "locatorLimit": locatorLimit,
        "locatorCandidates": locators,
        "locatorSelectionMethod": "normalizedTrigramCoverageThenSourceOrder",
        "bestContextSimilarity": locators[0]["contextSimilarity"] if locators else None,
        "sourceArtifactReady": status in {"exactUnique", "exactAmbiguous", "exactAmbiguousTruncated"},
        "reviewState": "unreviewed",
        "goldEligible": False,
        "missingGoldFields": list(BINDING_GAPS),
        "selectedLocatorId": None,
    }


def buildOriginalSourceBindings(
    queueRecords: Sequence[Mapping[str, Any]],
    sourceArtifactRows: Mapping[str, Sequence[Mapping[str, Any]]],
    sourceArtifactHashes: Mapping[str, str],
    *,
    locatorLimit: int = 10,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Review queue를 supplied original source rows와 exact evidence mention으로 결속한다.

    Capabilities
        Candidate마다 receipt row, source file version, exact char locator 목록과 ambiguity 상태를 만든다.

    AIContext
        AI 역할: 자동으로 source 후보를 찾지만 ambiguous locator를 임의 선택하거나 gold로 승격하지 않는다.

    Guide
        Artifact mapping key는 repository-relative source path이며 hash는 file SHA-256이어야 한다.

    When
        Source binding 알고리즘 unit test 또는 preloaded source artifact 결속에 호출한다.

    How
        Queue, path별 source row, path별 digest를 전달하고 binding 및 aggregate report를 받는다.

    Requires
        Queue challenge도 ``catalogSource``, ``issuerStockCode``, exact evidenceText를 자체 포함해야 한다.

    Args:
        queueRecords: U0-G02 machine review queue records.
        sourceArtifactRows: Relative path별 original source row sequence.
        sourceArtifactHashes: Relative path별 SHA-256 mapping.
        locatorLimit: Candidate 하나에 반환할 최대 locator 수.

    Returns:
        Stable binding list와 coverage report tuple.

    Raises:
        ValueError: Queue identity, source path, hash 또는 locator limit가 잘못됐을 때.

    Example:
        ``bindings, report = buildOriginalSourceBindings(queue, rowsByPath, hashesByPath)``

    SeeAlso:
        :func:`inspectOriginalSourceBindings`.
    """

    if locatorLimit <= 0:
        raise ValueError("locatorLimit must be positive")
    candidateIds = [str(record.get("candidateId") or "") for record in queueRecords]
    if len(candidateIds) != len(set(candidateIds)):
        raise ValueError("duplicate candidateId")
    bindings: list[dict[str, Any]] = []
    for record in sorted(queueRecords, key=lambda item: str(item.get("candidateId") or "")):
        receiptNo = _receiptNo(record)
        sourcePath = _sourceRelativePath(record, receiptNo)
        rows = sourceArtifactRows.get(sourcePath)
        sourceVersion = sourceArtifactHashes.get(sourcePath)
        if rows is None or sourceVersion is None:
            binding = {
                "schemaVersion": "releaseGoldSourceBinding.v1",
                "bindingId": f"source:binding:{_canonicalHash([record.get('candidateId'), sourcePath, 'missing']).removeprefix('sha256:')[:24]}",
                "candidateId": record.get("candidateId"),
                "candidateLane": record.get("lane"),
                "sourceRef": record.get("sourceRef") or record.get("candidateSourceRef"),
                "catalogSource": record.get("catalogSource"),
                "originalSourcePath": sourcePath,
                "originalSourceVersion": None,
                "originalReceiptNo": receiptNo,
                "bindingStatus": "sourceFileMissing",
                "receiptRowCount": 0,
                "exactLocatorCount": 0,
                "returnedLocatorCount": 0,
                "locatorLimit": locatorLimit,
                "locatorCandidates": [],
                "locatorSelectionMethod": "normalizedTrigramCoverageThenSourceOrder",
                "bestContextSimilarity": None,
                "sourceArtifactReady": False,
                "reviewState": "unreviewed",
                "goldEligible": False,
                "missingGoldFields": ["originalSourceVersion", *BINDING_GAPS],
                "selectedLocatorId": None,
            }
        else:
            binding = _buildBinding(record, rows, sourceVersion, sourcePath, locatorLimit)
        bindings.append(binding)
    statuses = Counter(str(binding["bindingStatus"]) for binding in bindings)
    laneReady = Counter(str(binding["candidateLane"]) for binding in bindings if binding["sourceArtifactReady"])
    locatorCount = sum(int(binding["exactLocatorCount"]) for binding in bindings)
    report = {
        "schemaVersion": "releaseGoldSourceBindingReceipt.v1",
        "queueRecordCount": len(queueRecords),
        "bindingCount": len(bindings),
        "sourceArtifactCount": len(sourceArtifactRows),
        "sourceArtifactReadyCount": sum(bool(binding["sourceArtifactReady"]) for binding in bindings),
        "bindingStatusCounts": dict(sorted(statuses.items())),
        "readyLaneCounts": dict(sorted(laneReady.items())),
        "exactLocatorCount": locatorCount,
        "locatorParityFailureCount": sum(
            locator["contextText"][
                locator["charStart"] - locator["contextStart"] : locator["charEnd"] - locator["contextStart"]
            ]
            != locator["evidenceText"]
            for binding in bindings
            for locator in binding["locatorCandidates"]
        ),
        "allRowsUnreviewed": all(binding["reviewState"] == "unreviewed" for binding in bindings),
        "allRowsGoldIneligible": all(not binding["goldEligible"] for binding in bindings),
        "goldAdmissionReady": False,
        "blockers": [
            "humanLocatorSelectionMissing",
            "humanPredicateDirectionConfirmationMissing",
            "sourcePublishedAtMissing",
            "availableAtMissing",
            "eventAtAndValidityMissing",
            "reviewReceiptMissing",
        ],
    }
    return bindings, report


def _loadLiveSourceArtifacts(
    queueRecords: Sequence[Mapping[str, Any]], repoRoot: Path
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, str], list[dict[str, Any]]]:
    try:
        import pyarrow as arrow
        import pyarrow.compute as compute
        import pyarrow.parquet as parquet
    except ImportError as exc:  # pragma: no cover - environment contract
        raise RuntimeError("pyarrow is required for live original source binding") from exc
    receiptsByPath: dict[str, set[str]] = defaultdict(set)
    sourceByPath: dict[str, str] = {}
    for record in queueRecords:
        receiptNo = _receiptNo(record)
        sourcePath = _sourceRelativePath(record, receiptNo)
        receiptsByPath[sourcePath].add(receiptNo)
        sourceByPath[sourcePath] = str(record.get("catalogSource") or "")
    existingPaths = [sourcePath for sourcePath in sorted(receiptsByPath) if (repoRoot / sourcePath).is_file()]
    with ThreadPoolExecutor(max_workers=min(8, max(1, len(existingPaths)))) as executor:
        digests = list(executor.map(lambda sourcePath: _fileHash(repoRoot / sourcePath), existingPaths))
    hashesByPath = dict(zip(existingPaths, digests, strict=True))
    rowsByPath: dict[str, list[dict[str, Any]]] = {}
    artifactReceipts: list[dict[str, Any]] = []
    for sourcePath in existingPaths:
        catalogSource = sourceByPath[sourcePath]
        columns = SOURCE_COLUMNS[catalogSource]
        table = parquet.read_table(repoRoot / sourcePath, columns=list(columns))
        receiptColumn = columns[0]
        requested = sorted(receiptsByPath[sourcePath])
        filtered = table.filter(
            compute.is_in(
                table[receiptColumn],
                value_set=arrow.array(requested, type=table[receiptColumn].type),
            )
        )
        rowsByPath[sourcePath] = filtered.to_pylist()
        artifactReceipts.append(
            {
                "path": sourcePath,
                "size": (repoRoot / sourcePath).stat().st_size,
                "sha256": hashesByPath[sourcePath],
                "requestedReceiptCount": len(requested),
                "matchedRowCount": filtered.num_rows,
            }
        )
    return rowsByPath, hashesByPath, artifactReceipts


def inspectOriginalSourceBindings(
    queueRecords: Sequence[Mapping[str, Any]],
    *,
    repoRoot: Path = Path("."),
    locatorLimit: int = 10,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Local original Parquet를 content-address해 queue 전체 source binding을 생성한다.

    Capabilities
        Queue가 참조하는 source file만 읽고 receipt row filtering, parallel SHA-256, binding receipt를 만든다.

    AIContext
        AI 역할: live source coverage를 전수 센서스하고 missing 또는 ambiguous 항목을 reviewer에게 노출한다.

    Guide
        ``repoRoot``는 ``data/dart``를 포함한 repository root이며 출력은 입력 queue 순서와 무관하다.

    When
        Committed review queue를 local original source snapshot에 다시 결속할 때 호출한다.

    How
        Source path를 queue에서 유도하고 file hash와 filtered rows를 pure builder에 전달한다.

    Requires
        Pyarrow와 queue가 참조하는 local ``data/dart/allFilings`` 및 ``data/dart/panel`` files.

    Args:
        queueRecords: Machine review queue records.
        repoRoot: Repository root path.
        locatorLimit: Candidate 하나에 반환할 최대 locator 수.

    Returns:
        Original source binding list와 live source receipt tuple.

    Raises:
        RuntimeError: Pyarrow가 없을 때.
        ValueError: Queue 또는 digest contract가 잘못됐을 때.

    Example:
        ``bindings, report = inspectOriginalSourceBindings(queue, repoRoot=Path('.'))``

    SeeAlso:
        :func:`buildOriginalSourceBindings`.
    """

    root = repoRoot.resolve()
    rowsByPath, hashesByPath, artifactReceipts = _loadLiveSourceArtifacts(queueRecords, root)
    bindings, report = buildOriginalSourceBindings(
        queueRecords,
        rowsByPath,
        hashesByPath,
        locatorLimit=locatorLimit,
    )
    expectedPaths = {_sourceRelativePath(record, _receiptNo(record)) for record in queueRecords}
    report.update(
        {
            "expectedSourceArtifactCount": len(expectedPaths),
            "missingSourceArtifacts": sorted(expectedPaths - set(rowsByPath)),
            "sourceArtifacts": artifactReceipts,
        }
    )
    return bindings, report


def _loadJsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _writeJsonl(path: Path, records: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records)
    path.write_text(body, encoding="utf-8")


def _parseArgs() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bind Universe review queue to original local source artifacts")
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--locator-limit", type=int, default=10)
    parser.add_argument("--output", type=Path, help="Optional source binding JSONL path")
    parser.add_argument("--receipt", type=Path, help="Optional source binding receipt JSON path")
    return parser.parse_args()


def _main() -> int:
    args = _parseArgs()
    queueBytes = args.queue.read_bytes()
    queueRecords = [json.loads(line) for line in queueBytes.decode("utf-8").splitlines() if line]
    bindings, report = inspectOriginalSourceBindings(
        queueRecords,
        repoRoot=args.repo_root,
        locatorLimit=args.locator_limit,
    )
    report["queueFile"] = {
        "path": args.queue.as_posix(),
        "size": len(queueBytes),
        "sha256": f"sha256:{hashlib.sha256(queueBytes).hexdigest()}",
        "rowCount": len(queueRecords),
    }
    if args.output:
        _writeJsonl(args.output, bindings)
        report["bindingFile"] = {
            "path": args.output.as_posix(),
            "size": args.output.stat().st_size,
            "sha256": _fileHash(args.output),
            "rowCount": len(bindings),
        }
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
