"""Universe assertion-grade document evidence pointer와 admission을 검증한다.

Capabilities
    Filing, section, exact text span 또는 table row, source version, 이중 시간, entity direction을 결속한다.

AIContext
    AI 역할: section 검색 결과를 exact assertion evidence로 과대 승격하지 않고 결손을 fail closed로 남긴다.

Guide
    Synthetic resolver contract와 local search catalog의 live readiness census를 분리한다.

When
    U0-E01 exact document evidence와 source schema drift를 검증할 때 사용한다.

How
    :func:`resolveEvidence`로 후보를 판정하고 :func:`inspectSearchCatalogEvidence`로 live gap을 센서스한다.

Requires
    Live census 실행 시 Polars와 local search catalog parquet가 필요하다.

Raises
    ValueError: request, locator, timestamp, hash 또는 immutable source version이 잘못됐을 때.

Example
    ``resolution = resolveEvidence(request, candidates)``

See Also
    :mod:`tests._attempts.dartlabUniverse.identity.entityIdentityProbe`.

결과
    Synthetic resolver 8/8은 통과했고 live catalog 381,149행의 assertion-grade evidence는 0행이다.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable

SHA256_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
DOCUMENT_ID_PATTERN = re.compile(r"^(kr:dart:filing:\d{14}|us:sec:filing:\d{10}-\d{2}-\d{6})$")
DIRECTIONS = {"subjectToObject", "objectToSubject", "undirected", "unknown"}
LOCATOR_KINDS = {"text", "table"}


def _hashText(value: str) -> str:
    return f"sha256:{hashlib.sha256(value.encode('utf-8')).hexdigest()}"


def _hashValue(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return _hashText(payload)


def _timestamp(value: str, label: str) -> str:
    if not value:
        raise ValueError(f"{label} is required")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"invalid {label}: {value}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{label} must be timezone-aware")
    return parsed.astimezone(UTC).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class EvidenceRequest:
    """Evidence가 입증해야 할 exact subject, predicate, object와 방향을 고정한다."""

    subjectId: str
    predicate: str
    objectId: str
    direction: str = "subjectToObject"

    def __post_init__(self) -> None:
        if not self.subjectId or not self.predicate or not self.objectId:
            raise ValueError("evidence request identity fields are required")
        if self.direction not in DIRECTIONS - {"unknown"}:
            raise ValueError(f"unsupported request direction: {self.direction}")


@dataclass(frozen=True)
class EvidenceCandidate:
    """Resolver가 검증하기 전 source content와 locator 후보를 보존한다."""

    candidateId: str
    documentId: str
    sectionPath: str
    sectionOrder: int
    sourceRef: str
    sourcePath: str
    sourceVersion: str
    subjectId: str
    predicate: str
    objectId: str
    direction: str
    sourcePublishedAt: str
    availableAt: str
    locatorKind: str
    content: str = ""
    contentHash: str = ""
    charStart: int = -1
    charEnd: int = -1
    snippetHash: str = ""
    tableHeader: tuple[str, ...] = ()
    tableRows: tuple[tuple[str, ...], ...] = ()
    rowIndex: int = -1
    headerHash: str = ""
    rowHash: str = ""


@dataclass(frozen=True)
class TextLocator:
    """UTF-8 decoded section content 안의 exact character boundary와 snippet hash를 보존한다."""

    charStart: int
    charEnd: int
    snippetHash: str


@dataclass(frozen=True)
class TableLocator:
    """Section table 안의 exact header와 row index, row hash를 함께 보존한다."""

    rowIndex: int
    headerHash: str
    rowHash: str


@dataclass(frozen=True)
class EvidencePointer:
    """Assertion에서 다시 열 수 있는 immutable source와 exact locator를 결속한다."""

    evidenceId: str
    documentId: str
    sectionPath: str
    sectionOrder: int
    sourceRef: str
    sourcePath: str
    sourceVersion: str
    subjectId: str
    predicate: str
    objectId: str
    direction: str
    sourcePublishedAt: str
    availableAt: str
    contentHash: str
    locatorKind: str
    textLocator: TextLocator | None = None
    tableLocator: TableLocator | None = None


@dataclass(frozen=True)
class EvidenceResolution:
    """Resolved pointer 또는 명시적인 fail-closed 이유를 반환한다."""

    status: str
    pointer: EvidencePointer | None
    candidateIds: tuple[str, ...]
    reasons: tuple[str, ...]


def _baseReason(candidate: EvidenceCandidate) -> str:
    if not DOCUMENT_ID_PATTERN.fullmatch(candidate.documentId):
        return "documentInvalid"
    if not candidate.sectionPath or candidate.sectionOrder < 0 or not candidate.sourceRef or not candidate.sourcePath:
        return "sourceUnavailable"
    if not SHA256_PATTERN.fullmatch(candidate.sourceVersion):
        return "sourceVersionMissing"
    if candidate.direction == "unknown" or candidate.direction not in DIRECTIONS:
        return "directionUnknown"
    try:
        publishedAt = _timestamp(candidate.sourcePublishedAt, "sourcePublishedAt")
        availableAt = _timestamp(candidate.availableAt, "availableAt")
    except ValueError:
        return "timeUnknown"
    if publishedAt > availableAt:
        return "timeUnknown"
    if candidate.locatorKind not in LOCATOR_KINDS:
        return "locatorInvalid"
    return ""


def _locator(candidate: EvidenceCandidate) -> tuple[TextLocator | None, TableLocator | None]:
    if not SHA256_PATTERN.fullmatch(candidate.contentHash):
        raise ValueError("contentHash must be a SHA-256 digest")
    if candidate.locatorKind == "text":
        if _hashText(candidate.content) != candidate.contentHash:
            raise ValueError("content hash mismatch")
        if (
            candidate.charStart < 0
            or candidate.charEnd <= candidate.charStart
            or candidate.charEnd > len(candidate.content)
        ):
            raise ValueError("text character boundary is invalid")
        snippet = candidate.content[candidate.charStart : candidate.charEnd]
        if _hashText(snippet) != candidate.snippetHash:
            raise ValueError("text snippet hash mismatch")
        return TextLocator(candidate.charStart, candidate.charEnd, candidate.snippetHash), None

    tableValue = {"header": candidate.tableHeader, "rows": candidate.tableRows}
    if _hashValue(tableValue) != candidate.contentHash:
        raise ValueError("table content hash mismatch")
    if not candidate.tableHeader or candidate.rowIndex < 0 or candidate.rowIndex >= len(candidate.tableRows):
        raise ValueError("table row boundary is invalid")
    row = candidate.tableRows[candidate.rowIndex]
    if len(row) != len(candidate.tableHeader):
        raise ValueError("table row width differs from header")
    if _hashValue(candidate.tableHeader) != candidate.headerHash or _hashValue(row) != candidate.rowHash:
        raise ValueError("table header or row hash mismatch")
    return None, TableLocator(candidate.rowIndex, candidate.headerHash, candidate.rowHash)


def _pointer(candidate: EvidenceCandidate) -> EvidencePointer:
    textLocator, tableLocator = _locator(candidate)
    identityPayload = {
        "documentId": candidate.documentId,
        "sectionPath": candidate.sectionPath,
        "sectionOrder": candidate.sectionOrder,
        "sourceVersion": candidate.sourceVersion,
        "subjectId": candidate.subjectId,
        "predicate": candidate.predicate,
        "objectId": candidate.objectId,
        "direction": candidate.direction,
        "contentHash": candidate.contentHash,
        "textLocator": asdict(textLocator) if textLocator else None,
        "tableLocator": asdict(tableLocator) if tableLocator else None,
    }
    return EvidencePointer(
        evidenceId=f"evidence:{_hashValue(identityPayload).removeprefix('sha256:')}",
        documentId=candidate.documentId,
        sectionPath=candidate.sectionPath,
        sectionOrder=candidate.sectionOrder,
        sourceRef=candidate.sourceRef,
        sourcePath=candidate.sourcePath,
        sourceVersion=candidate.sourceVersion,
        subjectId=candidate.subjectId,
        predicate=candidate.predicate,
        objectId=candidate.objectId,
        direction=candidate.direction,
        sourcePublishedAt=_timestamp(candidate.sourcePublishedAt, "sourcePublishedAt"),
        availableAt=_timestamp(candidate.availableAt, "availableAt"),
        contentHash=candidate.contentHash,
        locatorKind=candidate.locatorKind,
        textLocator=textLocator,
        tableLocator=tableLocator,
    )


def resolveEvidence(
    request: EvidenceRequest,
    candidates: Iterable[EvidenceCandidate],
) -> EvidenceResolution:
    """Exact assertion boundary와 immutable source를 모두 만족하는 단일 evidence만 해소한다.

    Capabilities
        Entity, predicate, direction, time, source version, text 또는 table locator를 순서대로 검증한다.

    AIContext
        AI 역할: fuzzy entity, whole-section snippet, adapter version을 exact evidence로 대신하지 않는다.

    Args
        request: 입증할 exact claim boundary.
        candidates: Source content를 포함한 evidence 후보.

    Returns
        단일 pointer 또는 가장 구체적인 거부 상태.

    Example
        ``result = resolveEvidence(request, [candidate])``

    Guide
        Resolved가 아니면 pointer는 항상 None이다.

    When
        Assertion admission 전에 evidence 후보를 검증할 때 호출한다.

    How
        Predicate, endpoints, direction 뒤 source와 locator를 fail closed로 검사한다.

    Requires
        Exact entity ID와 provider document ID가 필요하다.

    See Also
        :func:`inspectSearchCatalogEvidence`.

    Raises
        ValueError: request 자체가 유효하지 않을 때.
    """

    pool = tuple(candidates)
    predicateMatches = tuple(candidate for candidate in pool if candidate.predicate == request.predicate)
    if not predicateMatches:
        return EvidenceResolution("notFound", None, (), ("predicateNotFound",))
    entityMatches = tuple(
        candidate
        for candidate in predicateMatches
        if candidate.subjectId == request.subjectId and candidate.objectId == request.objectId
    )
    if not entityMatches:
        return EvidenceResolution(
            "ambiguousEntity",
            None,
            tuple(candidate.candidateId for candidate in predicateMatches),
            ("exactEntityBoundaryMissing",),
        )
    directionMatches = tuple(candidate for candidate in entityMatches if candidate.direction == request.direction)
    if not directionMatches:
        return EvidenceResolution(
            "directionUnknown",
            None,
            tuple(candidate.candidateId for candidate in entityMatches),
            ("exactDirectionMissing",),
        )

    validPointers: list[EvidencePointer] = []
    rejected: list[tuple[str, str]] = []
    for candidate in directionMatches:
        reason = _baseReason(candidate)
        if reason:
            rejected.append((candidate.candidateId, reason))
            continue
        try:
            validPointers.append(_pointer(candidate))
        except ValueError:
            rejected.append((candidate.candidateId, "locatorInvalid"))

    if len(validPointers) > 1:
        return EvidenceResolution(
            "ambiguousSource",
            None,
            tuple(candidate.candidateId for candidate in directionMatches),
            ("multipleExactPointers",),
        )
    if len(validPointers) == 1:
        pointer = validPointers[0]
        return EvidenceResolution(
            "resolved", pointer, tuple(candidate.candidateId for candidate in directionMatches), ()
        )

    reasons = tuple(dict.fromkeys(reason for _, reason in rejected)) or ("sourceUnavailable",)
    return EvidenceResolution(reasons[0], None, tuple(candidateId for candidateId, _ in rejected), reasons)


@dataclass(frozen=True)
class SearchCatalogEvidenceCensus:
    """Search catalog의 section lookup과 assertion-grade evidence readiness를 분리한다."""

    schemaVersion: str
    representative: bool
    catalogFileCount: int
    catalogRowCount: int
    sourceRefRowCount: int
    documentRowCount: int
    sectionLocatorRowCount: int
    contentHashRowCount: int
    sourceDataAsOfRowCount: int
    adapterVersionRowCount: int
    exactTextLocatorRowCount: int
    exactTableLocatorRowCount: int
    exactTimeRowCount: int
    immutableSourceVersionRowCount: int
    semanticDirectionRowCount: int
    assertionEvidenceReadyRowCount: int
    reviewedPositiveCount: int
    reviewedHardNegativeCount: int
    reviewedMetricsReady: bool
    transferMetricsReady: bool
    liveReady: bool
    blockerReasons: tuple[str, ...]

    def toDict(self) -> dict[str, Any]:
        """JSON compatible evidence census payload를 반환한다.

        Returns
            Census dataclass를 mapping으로 바꾼 값.

        Example
            ``payload = census.toDict()``

        Requires
            Dataclass fields가 JSON compatible scalar를 가져야 한다.

        Raises
            TypeError: 향후 JSON 비호환 field가 추가됐을 때 encoder가 발생시킬 수 있다.
        """

        return asdict(self)


def _nonemptyExpression(pl, name: str, columns: set[str]):
    if name not in columns:
        return pl.lit(False)
    return pl.col(name).cast(pl.Utf8, strict=False).fill_null("").str.strip_chars() != ""


def _sha256Expression(pl, name: str, columns: set[str]):
    if name not in columns:
        return pl.lit(False)
    return pl.col(name).cast(pl.Utf8, strict=False).fill_null("").str.contains(r"^sha256:[0-9a-f]{64}$")


def inspectSearchCatalogEvidence(catalogPaths: Iterable[str | Path]) -> SearchCatalogEvidenceCensus:
    """Local search catalog의 section pointer와 exact evidence field coverage를 전수 센서스한다.

    Capabilities
        DART panel, EDGAR panel, allFilings의 locator, time, version, semantics coverage를 계수한다.

    AIContext
        AI 역할: sourceRef 100%를 assertion evidence 100%로 오독하지 않게 한다.

    Args
        catalogPaths: 센서스할 catalog snapshot parquet 경로.

    Returns
        Field별 전수 행 수와 reviewed gold, transfer blocker.

    Example
        ``census = inspectSearchCatalogEvidence(paths)``

    Guide
        Adapter version과 dataAsOf는 immutable source version과 availability timestamp가 아니다.

    When
        Search catalog schema 또는 source adapter가 갱신된 뒤 실행한다.

    How
        각 parquet를 독립 스캔하고 exact admission에 필요한 필드의 논리곱을 계수한다.

    Requires
        Polars와 한 개 이상의 catalog parquet가 필요하다.

    See Also
        :func:`resolveEvidence`.

    Raises
        ValueError: catalog path가 비었거나 parquet가 없을 때.
        OSError: parquet schema 또는 data를 읽지 못할 때.
    """

    paths = tuple(Path(path) for path in catalogPaths)
    if not paths or any(not path.is_file() for path in paths):
        raise ValueError("all evidence catalog paths must exist")
    import polars as pl

    totals = {
        "rows": 0,
        "sourceRef": 0,
        "document": 0,
        "section": 0,
        "contentHash": 0,
        "sourceDataAsOf": 0,
        "adapterVersion": 0,
        "text": 0,
        "table": 0,
        "time": 0,
        "version": 0,
        "semantic": 0,
        "ready": 0,
    }
    for path in paths:
        schema = set(pl.scan_parquet(path).collect_schema().names())
        sourceRef = _nonemptyExpression(pl, "sourceRef", schema)
        document = _nonemptyExpression(pl, "docKey", schema)
        section = (
            sourceRef & document & _nonemptyExpression(pl, "sectionKey", schema) & pl.col("sectionOrder").is_not_null()
            if "sectionOrder" in schema
            else pl.lit(False)
        )
        contentHash = _nonemptyExpression(pl, "textHash", schema)
        sourceDataAsOf = _nonemptyExpression(pl, "sourceDataAsOf", schema)
        adapterVersion = _nonemptyExpression(pl, "sourceAdapterVersion", schema)
        text = (
            _nonemptyExpression(pl, "charStart", schema)
            & _nonemptyExpression(pl, "charEnd", schema)
            & _sha256Expression(pl, "snippetHash", schema)
        )
        table = (
            _nonemptyExpression(pl, "rowKey", schema)
            & _nonemptyExpression(pl, "headerHash", schema)
            & _nonemptyExpression(pl, "rowHash", schema)
        )
        time = _nonemptyExpression(pl, "sourcePublishedAt", schema) & _nonemptyExpression(pl, "availableAt", schema)
        version = _sha256Expression(pl, "sourceVersion", schema)
        semantic = _nonemptyExpression(pl, "predicate", schema) & (
            pl.col("direction").is_in(tuple(DIRECTIONS - {"unknown"})) if "direction" in schema else pl.lit(False)
        )
        ready = section & contentHash & (text | table) & time & version & semantic
        expressions = {
            "rows": pl.len(),
            "sourceRef": sourceRef.sum(),
            "document": document.sum(),
            "section": section.sum(),
            "contentHash": contentHash.sum(),
            "sourceDataAsOf": sourceDataAsOf.sum(),
            "adapterVersion": adapterVersion.sum(),
            "text": text.sum(),
            "table": table.sum(),
            "time": time.sum(),
            "version": version.sum(),
            "semantic": semantic.sum(),
            "ready": ready.sum(),
        }
        counts = pl.scan_parquet(path).select(**expressions).collect().row(0, named=True)
        for name, value in counts.items():
            totals[name] += int(value)

    blockers = (
        "exactTextLocatorMissing",
        "exactTableLocatorMissing",
        "sourcePublishedAtOrAvailableAtMissing",
        "rowLevelImmutableSourceVersionMissing",
        "predicateOrDirectionMissing",
        "reviewedPositiveGoldMissing",
        "reviewedHardNegativeGoldMissing",
        "publicTransferMetricsMissing",
    )
    return SearchCatalogEvidenceCensus(
        schemaVersion="searchCatalogEvidenceCensus.v1",
        representative=False,
        catalogFileCount=len(paths),
        catalogRowCount=totals["rows"],
        sourceRefRowCount=totals["sourceRef"],
        documentRowCount=totals["document"],
        sectionLocatorRowCount=totals["section"],
        contentHashRowCount=totals["contentHash"],
        sourceDataAsOfRowCount=totals["sourceDataAsOf"],
        adapterVersionRowCount=totals["adapterVersion"],
        exactTextLocatorRowCount=totals["text"],
        exactTableLocatorRowCount=totals["table"],
        exactTimeRowCount=totals["time"],
        immutableSourceVersionRowCount=totals["version"],
        semanticDirectionRowCount=totals["semantic"],
        assertionEvidenceReadyRowCount=totals["ready"],
        reviewedPositiveCount=0,
        reviewedHardNegativeCount=0,
        reviewedMetricsReady=False,
        transferMetricsReady=False,
        liveReady=False,
        blockerReasons=blockers,
    )


def main() -> int:
    """세 local search catalog snapshot의 evidence readiness를 JSON으로 출력한다.

    Capabilities
        U0-E01 live catalog의 section lookup과 assertion evidence field gap을 재측정한다.

    AIContext
        AI 역할: section sourceRef coverage와 assertion admission readiness를 분리한다.

    Returns
        성공 시 0.

    Example
        ``python exactEvidenceProbe.py``

    Guide
        Stdout JSON을 원장과 비교하고 결손 exact field를 추정해 채우지 않는다.

    When
        Search catalog snapshot 또는 source adapter가 갱신된 뒤 실행한다.

    How
        세 deterministic catalog path를 :func:`inspectSearchCatalogEvidence`에 전달한다.

    Requires
        Local search catalog parquet와 Polars가 필요하다.

    See Also
        :func:`inspectSearchCatalogEvidence`.

    Raises
        ValueError: 필수 snapshot이 없을 때.
        OSError: parquet를 읽지 못할 때.
    """

    repoRoot = Path(__file__).resolve().parents[4]
    dryRunRoot = repoRoot / "data" / "dart" / "searchCatalogDryRun"
    census = inspectSearchCatalogEvidence(
        (
            dryRunRoot / "dartPanel.sample" / "dartPanel.catalog_snapshot.parquet",
            dryRunRoot / "edgarPanel.sample" / "edgarPanel.catalog_snapshot.parquet",
            dryRunRoot / "allFilings" / "allFilings.catalog_snapshot.parquet",
        )
    )
    print(json.dumps(census.toDict(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
