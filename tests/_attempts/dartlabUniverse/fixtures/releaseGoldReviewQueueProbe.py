"""Universe release gold를 위한 exact-locator 사람 검토 큐를 만든다.

Capabilities
    그래프 edge와 filing catalog의 exact company-name mention을 결합해 positive 후보와 negative challenge를 만든다.

AIContext
    AI 역할: 기계 후보의 provenance와 결손을 고정하되 human-reviewed gold로 승격하지 않는다.

Guide
    출력의 모든 행은 ``reviewState=unreviewed`` 및 ``goldEligible=false``다. 문서를 연 사람의 판정만 gold가 된다.

When
    U0-G01 reviewed positive 및 hard negative 수집을 시작하거나 source snapshot이 바뀌었을 때 사용한다.

How
    :func:`buildReviewQueues`로 fixture를 평가하거나 CLI로 live graph와 parquet catalog를 결합한다.

Requires
    Pure builder는 standard library만, live CLI는 network와 pyarrow 및 local search catalog를 요구한다.

Raises
    ValueError: graph schema, catalog locator, limit 또는 snapshot digest가 잘못됐을 때.

Example
    ``positive, negative, report = buildReviewQueues(graph, rows, graphHash, catalogHash)``

See Also
    :mod:`tests._attempts.dartlabUniverse.fixtures.releaseGoldProbe`.

결과
    Exact locator는 검토 시작점을 제공하지만 original source version, published/available time, predicate direction은 미확정이다.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from collections.abc import Iterable, Iterator, Mapping, Sequence
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

GRAPH_URL = "https://huggingface.co/datasets/eddmpython/dartlab-data/resolve/main/landing/map/ecosystem.json"
CATALOG_ROOT = Path("data/dart/searchCatalogDryRun")
DEFAULT_CATALOGS = (
    CATALOG_ROOT / "allFilings" / "allFilings.catalog_snapshot.parquet",
    CATALOG_ROOT / "dartPanel.sample" / "dartPanel.catalog_snapshot.parquet",
)
SHA256_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
RAW_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
EDGE_PREDICATES = {
    "supplier": "suppliesTo",
    "customer": "sellsTo",
    "investor": "ownsStakeIn",
    "affiliate": "affiliatedWith",
}
RELEASE_POSITIVE_PREDICATES = {
    "suppliesTo",
    "sellsTo",
    "ownsStakeIn",
    "affiliatedWith",
    "classifiedIn",
    "filed",
}
SUPPORTED_NEGATIVE_TYPES = {
    "affiliateEntityCollision",
    "reversedDirection",
    "selfLoopMention",
    "shortEnglishCommonWord",
    "tableHeaderDrift",
}
RELEASE_NEGATIVE_TYPES = {
    "shortEnglishCommonWord",
    "sameNameDifferentEntity",
    "affiliateEntityCollision",
    "selfLoopMention",
    "reversedDirection",
    "industryPeerAsTradeRelation",
    "preCorrectionConflict",
    "privateListedAliasCollision",
    "sectionTitleOnly",
    "tableHeaderDrift",
    "historicalTickerCollision",
    "crossMarketFuzzyCollision",
}
POSITIVE_GAPS = (
    "originalSourceVersion",
    "sourcePublishedAt",
    "availableAt",
    "eventAtAndValidity",
    "predicateAndDirectionHumanConfirmation",
    "originalDocumentLocatorTransfer",
)
REVIEW_CHECKLIST = (
    "openOriginalDocument",
    "transferLocatorToOriginalDocument",
    "confirmEntityIdentity",
    "confirmPredicateAndDirection",
    "recordEventAndAvailabilityTimes",
    "recordReviewerReceipt",
)
CATALOG_COLUMNS = (
    "docKey",
    "source",
    "sourceRef",
    "sectionKey",
    "stockCode",
    "companyName",
    "date",
    "reportName",
    "title",
    "searchText",
    "textHash",
    "deleted",
    "sourceDataAsOf",
    "sourceAdapterVersion",
)


def _canonicalHash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return f"sha256:{hashlib.sha256(payload.encode('utf-8')).hexdigest()}"


def _requireDigest(value: str, field: str) -> str:
    if not SHA256_PATTERN.fullmatch(value):
        raise ValueError(f"{field} must be sha256 digest")
    return value


def _fileDigest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _textDigest(value: str) -> str:
    return f"sha256:{hashlib.sha256(value.encode('utf-8')).hexdigest()}"


def _catalogContentHash(row: Mapping[str, Any], text: str) -> str:
    value = str(row.get("textHash") or "").lower()
    return f"sha256:{value}" if RAW_SHA256_PATTERN.fullmatch(value) else _textDigest(text)


def _nodeIndex(graph: Mapping[str, Any]) -> dict[str, str]:
    nodes = graph.get("nodes")
    if not isinstance(nodes, list):
        raise ValueError("graph.nodes must be a list")
    index: dict[str, str] = {}
    for node in nodes:
        if not isinstance(node, Mapping):
            raise ValueError("graph node must be an object")
        nodeId = str(node.get("id") or "").strip()
        label = str(node.get("label") or node.get("name") or "").strip()
        if not nodeId or not label:
            raise ValueError("graph node id and label are required")
        index[nodeId] = label
    return index


def _edgeIndex(graph: Mapping[str, Any], nodes: Mapping[str, str]) -> dict[str, tuple[dict[str, str], ...]]:
    links = graph.get("links")
    if not isinstance(links, list):
        raise ValueError("graph.links must be a list")
    incident: dict[str, list[dict[str, str]]] = defaultdict(list)
    for link in links:
        if not isinstance(link, Mapping):
            raise ValueError("graph link must be an object")
        source = str(link.get("source") or "").strip()
        target = str(link.get("target") or "").strip()
        edgeType = str(link.get("type") or "").strip()
        if source not in nodes or target not in nodes or edgeType not in EDGE_PREDICATES:
            continue
        edge = {
            "source": source,
            "target": target,
            "type": edgeType,
            "sourceTag": str(link.get("source_tag") or "unknown"),
            "predicate": EDGE_PREDICATES[edgeType],
        }
        incident[source].append(edge)
        if source != target:
            incident[target].append(edge)
    return {
        stockCode: tuple(
            sorted(edges, key=lambda item: (item["source"], item["target"], item["type"], item["sourceTag"]))
        )
        for stockCode, edges in incident.items()
    }


def _candidateFromMention(
    row: Mapping[str, Any],
    edge: Mapping[str, str],
    nodes: Mapping[str, str],
    graphHash: str,
    catalogHash: str,
) -> dict[str, Any] | None:
    stockCode = str(row.get("stockCode") or "").strip()
    if stockCode not in (edge["source"], edge["target"]):
        return None
    counterpart = edge["target"] if stockCode == edge["source"] else edge["source"]
    mention = nodes[counterpart]
    text = str(row.get("searchText") or "")
    charStart = text.find(mention)
    if charStart < 0:
        return None
    charEnd = charStart + len(mention)
    contextStart = max(0, charStart - 120)
    contextEnd = min(len(text), charEnd + 120)
    contextText = text[contextStart:contextEnd]
    identity = {
        "graph": graphHash,
        "catalog": catalogHash,
        "sourceRef": str(row.get("sourceRef") or ""),
        "edge": [edge["source"], edge["predicate"], edge["target"], edge["sourceTag"]],
        "locator": [charStart, charEnd],
    }
    riskFlags: list[str] = []
    if len(mention) <= 3:
        riskFlags.append("shortNameCollisionRisk")
    if mention.isascii():
        riskFlags.append("asciiNameCollisionRisk")
    if edge["source"] == edge["target"]:
        riskFlags.append("selfLoopRisk")
    return {
        "schemaVersion": "releaseGoldReviewCandidate.v1",
        "candidateId": f"review:candidate:{_canonicalHash(identity).removeprefix('sha256:')[:24]}",
        "lane": "positiveCandidate",
        "origin": "machineCandidate",
        "reviewState": "unreviewed",
        "goldEligible": False,
        "expectedStatus": "reviewRequired",
        "market": "KR",
        "language": "ko",
        "subjectId": f"krx:{edge['source']}",
        "subjectLabel": nodes[edge["source"]],
        "predicate": edge["predicate"],
        "objectId": f"krx:{edge['target']}",
        "objectLabel": nodes[edge["target"]],
        "issuerStockCode": stockCode,
        "issuerCompanyName": str(row.get("companyName") or ""),
        "mentionEntityId": f"krx:{counterpart}",
        "mentionLabel": mention,
        "graphEdgeType": edge["type"],
        "graphSourceTag": edge["sourceTag"],
        "graphSnapshotHash": graphHash,
        "catalogSnapshotHash": catalogHash,
        "docId": str(row.get("docKey") or ""),
        "sourceKind": "DART",
        "catalogSource": str(row.get("source") or ""),
        "sourceRef": str(row.get("sourceRef") or ""),
        "sectionPath": str(row.get("sectionKey") or ""),
        "catalogDate": str(row.get("date") or ""),
        "reportName": str(row.get("reportName") or ""),
        "title": str(row.get("title") or ""),
        "sourceDataAsOf": row.get("sourceDataAsOf"),
        "sourceAdapterVersion": row.get("sourceAdapterVersion"),
        "sourceVersion": None,
        "catalogContentHash": _catalogContentHash(row, text),
        "locatorKind": "catalogText",
        "evidenceText": mention,
        "charStart": charStart,
        "charEnd": charEnd,
        "snippetHash": _textDigest(mention),
        "contextStart": contextStart,
        "contextEnd": contextEnd,
        "contextText": contextText,
        "contextHash": _textDigest(contextText),
        "riskFlags": riskFlags,
        "missingGoldFields": list(POSITIVE_GAPS),
        "reviewChecklist": list(REVIEW_CHECKLIST),
        "reviewDecision": None,
        "reviewer": None,
        "reviewedAt": None,
        "reviewReceiptId": None,
    }


def _challengeFromCandidate(candidate: Mapping[str, Any]) -> dict[str, Any]:
    predicate = str(candidate["predicate"])
    sourceTag = str(candidate["graphSourceTag"])
    mention = str(candidate["mentionLabel"])
    if candidate["subjectId"] == candidate["objectId"]:
        negativeType = "selfLoopMention"
        subjectId, objectId = candidate["subjectId"], candidate["objectId"]
        challengePredicate = predicate
    elif sourceTag == "panel_table":
        negativeType = "tableHeaderDrift"
        subjectId, objectId = candidate["subjectId"], candidate["objectId"]
        challengePredicate = predicate
    elif mention.isascii() and len(mention) <= 3:
        negativeType = "shortEnglishCommonWord"
        subjectId, objectId = candidate["subjectId"], candidate["objectId"]
        challengePredicate = predicate
    elif predicate == "affiliatedWith":
        negativeType = "affiliateEntityCollision"
        subjectId, objectId = candidate["subjectId"], candidate["objectId"]
        challengePredicate = "suppliesTo"
    else:
        negativeType = "reversedDirection"
        subjectId, objectId = candidate["objectId"], candidate["subjectId"]
        challengePredicate = predicate
    identity = [candidate["candidateId"], negativeType, subjectId, challengePredicate, objectId]
    return {
        "schemaVersion": "releaseGoldReviewCandidate.v1",
        "candidateId": f"review:challenge:{_canonicalHash(identity).removeprefix('sha256:')[:24]}",
        "lane": "hardNegativeChallenge",
        "origin": "machineChallenge",
        "reviewState": "unreviewed",
        "goldEligible": False,
        "expectedStatus": "reviewRequired",
        "negativeType": negativeType,
        "subjectId": subjectId,
        "predicate": challengePredicate,
        "objectId": objectId,
        "candidateSourceRef": candidate["sourceRef"],
        "basedOnCandidateId": candidate["candidateId"],
        "sourceCandidateLane": candidate["lane"],
        "market": candidate["market"],
        "language": candidate["language"],
        "graphSnapshotHash": candidate["graphSnapshotHash"],
        "catalogSnapshotHash": candidate["catalogSnapshotHash"],
        "docId": candidate["docId"],
        "sectionPath": candidate["sectionPath"],
        "catalogContentHash": candidate["catalogContentHash"],
        "locatorKind": candidate["locatorKind"],
        "evidenceText": candidate["evidenceText"],
        "charStart": candidate["charStart"],
        "charEnd": candidate["charEnd"],
        "snippetHash": candidate["snippetHash"],
        "contextStart": candidate["contextStart"],
        "contextEnd": candidate["contextEnd"],
        "contextText": candidate["contextText"],
        "contextHash": candidate["contextHash"],
        "mentionLabel": candidate["mentionLabel"],
        "graphEdgeType": candidate["graphEdgeType"],
        "graphSourceTag": candidate["graphSourceTag"],
        "reviewPrompt": "원문을 열어 이 challenge triple이 사실이 아님을 확인하고 근거를 기록한다.",
        "reviewDecision": None,
        "reviewReason": None,
        "reviewer": None,
        "reviewedAt": None,
        "reviewReceiptId": None,
    }


def _balancedSelect(candidates: Sequence[Mapping[str, Any]], limit: int) -> list[dict[str, Any]]:
    byPredicate: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for candidate in candidates:
        if candidate["subjectId"] != candidate["objectId"]:
            byPredicate[str(candidate["predicate"])].append(candidate)
    for records in byPredicate.values():
        records.sort(key=lambda record: str(record["candidateId"]))
    predicates = sorted(byPredicate)
    selected: list[dict[str, Any]] = []
    cursor = 0
    while predicates and len(selected) < limit:
        predicate = predicates[cursor % len(predicates)]
        bucket = byPredicate[predicate]
        if bucket:
            selected.append(dict(bucket.pop(0)))
        predicates = [name for name in predicates if byPredicate[name]]
        cursor += 1
    return selected


def buildReviewQueues(
    graph: Mapping[str, Any],
    catalogRows: Iterable[Mapping[str, Any]],
    graphSnapshotHash: str,
    catalogSnapshotHash: str,
    *,
    limit: int = 300,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Exact mention 기반 positive 후보와 hard-negative challenge를 결정론적으로 만든다.

    Capabilities
        Graph edge, catalog issuer, exact mention을 연결하고 균형 선택과 coverage receipt를 제공한다.

    AIContext
        AI 역할: 검토 입력을 만들 뿐 review receipt나 gold field를 대신 채우지 않는다.

    Guide
        동일 snapshot과 row 집합은 입력 순서와 무관하게 동일 candidate ID와 선택 결과를 낸다.

    When
        Release gold human review queue를 처음 만들거나 snapshot 갱신 후 재생성할 때 호출한다.

    How
        Graph와 catalog rows를 전달하고 반환된 두 queue 및 report를 별도 파일에 보존한다.

    Requires
        Graph node id가 catalog stockCode와 같고 catalog searchText 및 sourceRef가 있어야 한다.

    Args:
        graph: ``nodes``와 ``links``를 가진 ecosystem mapping.
        catalogRows: Search catalog row iterable.
        graphSnapshotHash: Graph bytes의 SHA-256.
        catalogSnapshotHash: Catalog set receipt의 SHA-256.
        limit: Lane별 최대 queue 크기.

    Returns:
        Positive candidate list, hard-negative challenge list, coverage report tuple.

    Raises:
        ValueError: digest, graph schema 또는 limit가 잘못됐을 때.

    Example:
        ``positive, negative, report = buildReviewQueues(graph, rows, graphHash, catalogHash, limit=10)``

    SeeAlso:
        :func:`tests._attempts.dartlabUniverse.fixtures.releaseGoldProbe.evaluateReleaseGold`.
    """

    if limit <= 0:
        raise ValueError("limit must be positive")
    graphHash = _requireDigest(graphSnapshotHash, "graphSnapshotHash")
    catalogHash = _requireDigest(catalogSnapshotHash, "catalogSnapshotHash")
    nodes = _nodeIndex(graph)
    incident = _edgeIndex(graph, nodes)
    candidatesById: dict[str, dict[str, Any]] = {}
    scannedRows = 0
    exactMentionCount = 0
    for row in catalogRows:
        scannedRows += 1
        if bool(row.get("deleted")):
            continue
        stockCode = str(row.get("stockCode") or "").strip()
        if not stockCode or not row.get("sourceRef") or not row.get("searchText"):
            continue
        for edge in incident.get(stockCode, ()):
            candidate = _candidateFromMention(row, edge, nodes, graphHash, catalogHash)
            if candidate is None:
                continue
            exactMentionCount += 1
            candidatesById.setdefault(candidate["candidateId"], candidate)
    allCandidates = sorted(candidatesById.values(), key=lambda record: str(record["candidateId"]))
    positives = _balancedSelect(allCandidates, limit)
    challengeSources = positives + [
        candidate for candidate in allCandidates if candidate["subjectId"] == candidate["objectId"]
    ]
    challengesById: dict[str, dict[str, Any]] = {}
    for candidate in challengeSources:
        challenge = _challengeFromCandidate(candidate)
        challengesById.setdefault(challenge["candidateId"], challenge)
    negativeTypeBuckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for challenge in challengesById.values():
        negativeTypeBuckets[str(challenge["negativeType"])].append(challenge)
    for records in negativeTypeBuckets.values():
        records.sort(key=lambda record: str(record["candidateId"]))
    negatives: list[dict[str, Any]] = []
    types = sorted(negativeTypeBuckets)
    cursor = 0
    while types and len(negatives) < limit:
        negativeType = types[cursor % len(types)]
        bucket = negativeTypeBuckets[negativeType]
        if bucket:
            negatives.append(bucket.pop(0))
        types = [name for name in types if negativeTypeBuckets[name]]
        cursor += 1
    positivePredicates = Counter(str(record["predicate"]) for record in positives)
    negativeTypes = Counter(str(record["negativeType"]) for record in negatives)
    locatorParityFailureCount = sum(
        record["contextText"][record["charStart"] - record["contextStart"] : record["charEnd"] - record["contextStart"]]
        != record["evidenceText"]
        for record in positives + negatives
    )
    observedPredicates = set(positivePredicates)
    observedTypes = set(negativeTypes)
    report = {
        "schemaVersion": "releaseGoldReviewQueueReceipt.v1",
        "selectionMethod": "stableCandidateHashRoundRobinByPredicateAndNegativeType",
        "graphSnapshotHash": graphHash,
        "catalogSnapshotHash": catalogHash,
        "scannedCatalogRowCount": scannedRows,
        "exactMentionCountBeforeDeduplication": exactMentionCount,
        "uniqueCandidateCount": len(allCandidates),
        "positiveCandidateCount": len(positives),
        "hardNegativeChallengeCount": len(negatives),
        "locatorParityFailureCount": locatorParityFailureCount,
        "targetPerLane": limit,
        "positivePredicateCounts": dict(sorted(positivePredicates.items())),
        "uncoveredReleasePositivePredicates": sorted(RELEASE_POSITIVE_PREDICATES - observedPredicates),
        "hardNegativeTypeCounts": dict(sorted(negativeTypes.items())),
        "machineSupportedNegativeTypes": sorted(SUPPORTED_NEGATIVE_TYPES),
        "observedNegativeTypes": sorted(observedTypes),
        "uncoveredReleaseNegativeTypes": sorted(RELEASE_NEGATIVE_TYPES - observedTypes),
        "allRowsUnreviewed": all(record["reviewState"] == "unreviewed" for record in positives + negatives),
        "allRowsGoldIneligible": all(not record["goldEligible"] for record in positives + negatives),
        "goldAdmissionReady": False,
        "blockers": [
            "humanReviewMissing",
            "originalSourceVersionMissing",
            "publishedAndAvailableTimeMissing",
            "predicateDirectionConfirmationMissing",
            "KRGraphCannotSatisfyUSAndSECQuota",
            "releasePositivePredicateCoverageIncomplete",
            "releaseNegativeTypeCoverageIncomplete",
        ],
    }
    return positives, negatives, report


def _iterParquetRows(paths: Sequence[Path]) -> Iterator[dict[str, Any]]:
    try:
        import pyarrow.parquet as parquet
    except ImportError as exc:  # pragma: no cover - environment contract
        raise RuntimeError("pyarrow is required for live review queue generation") from exc
    for path in paths:
        parquetFile = parquet.ParquetFile(path)
        for batch in parquetFile.iter_batches(columns=list(CATALOG_COLUMNS), batch_size=2048):
            yield from batch.to_pylist()


def inspectLiveReviewQueue(
    catalogPaths: Sequence[Path] = DEFAULT_CATALOGS,
    *,
    graphUrl: str = GRAPH_URL,
    limit: int = 300,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Live graph bytes와 local parquet snapshot을 고정해 review queue를 센서스한다.

    Capabilities
        Remote graph 및 local catalog file hash를 계산하고 streaming row scan으로 queue를 생성한다.

    AIContext
        AI 역할: live source receipt를 남겨 재생성 가능성을 높이고 missing source를 숨기지 않는다.

    Guide
        Network graph는 받은 bytes의 hash로, catalog set은 file path, size, hash의 canonical hash로 고정한다.

    When
        Repository의 현재 source snapshot에서 실제 review queue를 생성할 때 호출한다.

    How
        Catalog path를 검증하고 graph를 내려받은 뒤 :func:`buildReviewQueues`에 streaming rows를 넘긴다.

    Requires
        HTTPS network, pyarrow, readable parquet snapshot files.

    Args:
        catalogPaths: 결합할 parquet snapshot 경로들.
        graphUrl: Ecosystem graph JSON URL.
        limit: Lane별 최대 queue 크기.

    Returns:
        Positive candidate list, hard-negative challenge list, live receipt tuple.

    Raises:
        FileNotFoundError: Catalog snapshot이 없을 때.
        RuntimeError: pyarrow가 없을 때.
        ValueError: Graph JSON이나 builder 입력이 잘못됐을 때.

    Example:
        ``positive, negative, report = inspectLiveReviewQueue(limit=300)``

    SeeAlso:
        :func:`buildReviewQueues`.
    """

    paths = tuple(Path(path) for path in catalogPaths)
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"catalog snapshot missing: {missing}")
    request = Request(graphUrl, headers={"User-Agent": "dartlab-universe-review-queue/1"})
    with urlopen(request, timeout=60) as response:  # noqa: S310 - fixed/explicit operator URL
        graphBytes = response.read()
    graph = json.loads(graphBytes.decode("utf-8"))
    graphHash = f"sha256:{hashlib.sha256(graphBytes).hexdigest()}"
    catalogFiles = [
        {"path": path.as_posix(), "size": path.stat().st_size, "sha256": _fileDigest(path)} for path in paths
    ]
    catalogHash = _canonicalHash(catalogFiles)
    positive, negative, report = buildReviewQueues(
        graph,
        _iterParquetRows(paths),
        graphHash,
        catalogHash,
        limit=limit,
    )
    report.update(
        {
            "graphUrl": graphUrl,
            "graphVersion": graph.get("version"),
            "graphNodeCount": len(graph.get("nodes", [])),
            "graphLinkCount": len(graph.get("links", [])),
            "catalogFiles": catalogFiles,
        }
    )
    return positive, negative, report


def _writeJsonl(path: Path, records: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records)
    path.write_text(body, encoding="utf-8")


def _parseArgs() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build an unreviewed Universe release-gold review queue")
    parser.add_argument("--limit", type=int, default=300)
    parser.add_argument("--graph-url", default=GRAPH_URL)
    parser.add_argument("--catalog", action="append", type=Path, dest="catalogs")
    parser.add_argument("--output", type=Path, help="Optional combined JSONL output path")
    parser.add_argument("--receipt", type=Path, help="Optional JSON receipt output path")
    return parser.parse_args()


def _main() -> int:
    args = _parseArgs()
    positive, negative, report = inspectLiveReviewQueue(
        tuple(args.catalogs) if args.catalogs else DEFAULT_CATALOGS,
        graphUrl=args.graph_url,
        limit=args.limit,
    )
    if args.output:
        _writeJsonl(args.output, positive + negative)
        report["queueFile"] = {
            "path": args.output.as_posix(),
            "size": args.output.stat().st_size,
            "sha256": _fileDigest(args.output),
            "rowCount": len(positive) + len(negative),
        }
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
