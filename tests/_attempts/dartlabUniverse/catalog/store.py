"""Arrow batch를 in-memory DuckDB에만 투영하는 U3 catalog store."""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator

import duckdb
import pyarrow as pa

from ..contracts import Visibility
from .models import CatalogState

_RESOURCE_SCHEMA = pa.schema(
    [
        ("resourceId", pa.string()),
        ("resourceVersionId", pa.string()),
        ("resourceKind", pa.string()),
        ("label", pa.string()),
        ("namespace", pa.string()),
        ("sourceKind", pa.string()),
        ("sourceRef", pa.string()),
        ("sourceRevision", pa.string()),
        ("locator", pa.string()),
        ("contentSelector", pa.string()),
        ("contentDigest", pa.string()),
        ("mediaType", pa.string()),
        ("schemaFingerprint", pa.string()),
        ("byteSize", pa.int64()),
        ("rowCount", pa.int64()),
        ("visibility", pa.string()),
        ("licenseRef", pa.string()),
        ("status", pa.string()),
        ("discoveredAt", pa.string()),
        ("observedAt", pa.string()),
        ("gapReason", pa.string()),
        ("attributes", pa.string()),
    ]
)
_OBJECT_SCHEMA = pa.schema(
    [
        ("schemaVersion", pa.string()),
        ("objectId", pa.string()),
        ("objectVersionId", pa.string()),
        ("objectKind", pa.string()),
        ("canonicalLabel", pa.string()),
        ("aliases", pa.string()),
        ("identifierRefs", pa.string()),
        ("resourceRefs", pa.string()),
        ("primaryResourceVersionId", pa.string()),
        ("epistemicClass", pa.string()),
        ("verificationState", pa.string()),
        ("validTime", pa.string()),
        ("systemTime", pa.string()),
        ("visibility", pa.string()),
        ("attributes", pa.string()),
    ]
)
_EVIDENCE_SCHEMA = pa.schema(
    [
        ("evidenceId", pa.string()),
        ("objectId", pa.string()),
        ("resourceVersionId", pa.string()),
        ("sourceKind", pa.string()),
        ("sourceRef", pa.string()),
        ("sourceRevision", pa.string()),
        ("locator", pa.string()),
        ("selector", pa.string()),
        ("contentDigest", pa.string()),
        ("retrievedAt", pa.string()),
        ("visibility", pa.string()),
        ("licenseRef", pa.string()),
        ("quoteDigest", pa.string()),
    ]
)
_OBJECT_DETAIL_MAX_RESOURCES = 1000
_OBJECT_DETAIL_MAX_EVIDENCE = 5000


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _tableFromRows(
    rows: Iterable[dict[str, object]],
    schema: pa.Schema,
    *,
    batchSize: int = 8192,
) -> pa.Table:
    """Python row 임시 메모리를 batchSize로 제한해 Arrow table을 만든다."""
    batches = []
    pending = []
    for row in rows:
        pending.append(row)
        if len(pending) == batchSize:
            batches.append(pa.RecordBatch.from_pylist(pending, schema=schema))
            pending.clear()
    if pending:
        batches.append(pa.RecordBatch.from_pylist(pending, schema=schema))
    return pa.Table.from_batches(batches, schema=schema)


def _catalogArrowTableStream(
    catalog: CatalogState,
    *,
    allowedVisibility: frozenset[Visibility],
) -> Iterator[tuple[str, pa.Table]]:
    """호출자 visibility로 축소한 Arrow table을 한 종류씩 생성한다."""
    if not allowedVisibility:
        raise ValueError("allowedVisibility는 비어 있을 수 없음")
    visibleResourceVersions: set[str] = set()

    def resourceRows() -> Iterator[dict[str, object]]:
        for item in catalog.resources:
            if item.visibility not in allowedVisibility:
                continue
            visibleResourceVersions.add(item.resourceVersionId)
            yield {
                "resourceId": item.resourceId,
                "resourceVersionId": item.resourceVersionId,
                "resourceKind": item.resourceKind,
                "label": item.label,
                "namespace": item.namespace,
                "sourceKind": item.sourceKind,
                "sourceRef": item.sourceRef,
                "sourceRevision": item.sourceRevision,
                "locator": _json(item.locator),
                "contentSelector": _json(item.contentSelector),
                "contentDigest": item.contentDigest,
                "mediaType": item.mediaType,
                "schemaFingerprint": item.schemaFingerprint,
                "byteSize": item.byteSize,
                "rowCount": item.rowCount,
                "visibility": item.visibility.value,
                "licenseRef": item.licenseRef,
                "status": item.status,
                "discoveredAt": item.discoveredAt,
                "observedAt": item.observedAt,
                "gapReason": item.gapReason,
                "attributes": _json(item.attributes),
            }

    yield "resources", _tableFromRows(resourceRows(), _RESOURCE_SCHEMA)
    visibleObjectIds: set[str] = set()

    def objectRows() -> Iterator[dict[str, object]]:
        for item in catalog.objects:
            if item.visibility not in allowedVisibility or any(
                resourceRef not in visibleResourceVersions for resourceRef in item.resourceRefs
            ):
                continue
            visibleObjectIds.add(item.objectId)
            yield {
                "schemaVersion": item.schemaVersion,
                "objectId": item.objectId,
                "objectVersionId": item.objectVersionId,
                "objectKind": item.objectKind,
                "canonicalLabel": item.canonicalLabel,
                "aliases": _json(item.aliases),
                "identifierRefs": _json(item.identifierRefs),
                "resourceRefs": _json(item.resourceRefs),
                "primaryResourceVersionId": item.resourceRefs[0],
                "epistemicClass": item.epistemicClass.value,
                "verificationState": item.verificationState.value,
                "validTime": _json({"start": item.validTime.start, "end": item.validTime.end}),
                "systemTime": _json(
                    {
                        "knownAt": item.systemTime.knownAt,
                        "observedAt": item.systemTime.observedAt,
                        "ingestedAt": item.systemTime.ingestedAt,
                        "retractedAt": item.systemTime.retractedAt,
                    }
                ),
                "visibility": item.visibility.value,
                "attributes": _json(item.attributes),
            }

    yield "objects", _tableFromRows(objectRows(), _OBJECT_SCHEMA)

    def evidenceRows() -> Iterator[dict[str, object]]:
        for item in catalog.evidence:
            if (
                item.visibility not in allowedVisibility
                or item.resourceVersionId not in visibleResourceVersions
                or item.objectId not in visibleObjectIds
            ):
                continue
            yield {
                "evidenceId": item.evidenceId,
                "objectId": item.objectId,
                "resourceVersionId": item.resourceVersionId,
                "sourceKind": item.sourceKind,
                "sourceRef": item.sourceRef,
                "sourceRevision": item.sourceRevision,
                "locator": _json(item.locator),
                "selector": _json(item.selector),
                "contentDigest": item.contentDigest,
                "retrievedAt": item.retrievedAt,
                "visibility": item.visibility.value,
                "licenseRef": item.licenseRef,
                "quoteDigest": item.quoteDigest,
            }

    yield "evidence", _tableFromRows(evidenceRows(), _EVIDENCE_SCHEMA)


def catalogArrowTables(
    catalog: CatalogState,
    *,
    allowedVisibility: frozenset[Visibility],
) -> dict[str, pa.Table]:
    """호출자 visibility로 축소한 catalog Arrow table을 만든다."""
    return dict(_catalogArrowTableStream(catalog, allowedVisibility=allowedVisibility))


class InMemoryCatalog:
    """Disk catalog를 만들지 않는 DuckDB runtime projection."""

    def __init__(self, catalog: CatalogState):
        self.connection = duckdb.connect(":memory:")
        self.tables: dict[str, pa.Table] = {}
        tableStream = _catalogArrowTableStream(catalog, allowedVisibility=frozenset(Visibility))
        while True:
            try:
                name, table = next(tableStream)
            except StopIteration:
                break
            viewName = f"_{name}_arrow"
            self.connection.register(viewName, table)
            self.connection.execute(f'CREATE TABLE "{name}" AS SELECT * FROM "{viewName}"')
            self.connection.unregister(viewName)
            del table
        self.connection.execute("CREATE UNIQUE INDEX resources_id_idx ON resources(resourceId)")
        self.connection.execute("CREATE UNIQUE INDEX resources_version_idx ON resources(resourceVersionId)")
        self.connection.execute("CREATE UNIQUE INDEX objects_id_idx ON objects(objectId)")
        self.connection.execute("CREATE UNIQUE INDEX evidence_id_idx ON evidence(evidenceId)")

    @staticmethod
    def _row(columns: tuple[str, ...], row: tuple[object, ...] | None) -> dict[str, object] | None:
        return dict(zip(columns, row, strict=True)) if row is not None else None

    @staticmethod
    def _visibilitySql(allowedVisibility: frozenset[Visibility]) -> tuple[str, tuple[str, ...]]:
        if not allowedVisibility:
            raise ValueError("allowedVisibility는 비어 있을 수 없음")
        values = tuple(sorted(item.value for item in allowedVisibility))
        return ", ".join("?" for _ in values), values

    def resourceByVersion(
        self,
        resourceVersionId: str,
        *,
        allowedVisibility: frozenset[Visibility],
    ) -> dict[str, object] | None:
        """Exact immutable resource version을 index lookup한다."""
        placeholders, visibilityValues = self._visibilitySql(allowedVisibility)
        cursor = self.connection.execute(
            f"SELECT * FROM resources WHERE resourceVersionId = ? AND visibility IN ({placeholders})",
            (resourceVersionId, *visibilityValues),
        )
        columns = tuple(item[0] for item in cursor.description)
        return self._row(columns, cursor.fetchone())

    def objectDetail(
        self,
        objectId: str,
        *,
        allowedVisibility: frozenset[Visibility],
    ) -> dict[str, object] | None:
        """Object와 모든 resource/evidence locator를 fail-closed detail로 반환한다."""
        pack = self.objectEvidencePack(objectId, allowedVisibility=allowedVisibility)
        if pack is None:
            return None
        objectRow = dict(pack["object"])
        resources = tuple(pack["resources"])
        evidence = tuple(pack["evidence"])
        primaryRef = str(objectRow["primaryResourceVersionId"])
        primaryResource = next(item for item in resources if item["resourceVersionId"] == primaryRef)
        primaryEvidence = next(item for item in evidence if item["resourceVersionId"] == primaryRef)
        return {
            **objectRow,
            "resourceId": primaryResource["resourceId"],
            "resourceVersionId": primaryResource["resourceVersionId"],
            "resourceKind": primaryResource["resourceKind"],
            "sourceKind": primaryResource["sourceKind"],
            "sourceRef": primaryResource["sourceRef"],
            "sourceRevision": primaryResource["sourceRevision"],
            "resourceLocator": primaryResource["locator"],
            "contentSelector": primaryResource["contentSelector"],
            "contentDigest": primaryResource["contentDigest"],
            "mediaType": primaryResource["mediaType"],
            "schemaFingerprint": primaryResource["schemaFingerprint"],
            "byteSize": primaryResource["byteSize"],
            "rowCount": primaryResource["rowCount"],
            "licenseRef": primaryResource["licenseRef"],
            "discoveredAt": primaryResource["discoveredAt"],
            "observedAt": primaryResource["observedAt"],
            "evidenceId": primaryEvidence["evidenceId"],
            "evidenceLocator": primaryEvidence["locator"],
            "evidenceSelector": primaryEvidence["selector"],
            "retrievedAt": primaryEvidence["retrievedAt"],
            "evidenceLicenseRef": primaryEvidence["licenseRef"],
            "quoteDigest": primaryEvidence["quoteDigest"],
            "resources": resources,
            "evidence": evidence,
        }

    def objectEvidencePack(
        self,
        objectId: str,
        *,
        allowedVisibility: frozenset[Visibility],
    ) -> dict[str, object] | None:
        """다중 resource object의 완전한 evidence pack을 visibility 교집합으로 조회한다."""
        placeholders, visibilityValues = self._visibilitySql(allowedVisibility)
        cursor = self.connection.execute(
            f"""
            SELECT * FROM objects
            WHERE objectId = ? AND visibility IN ({placeholders})
            LIMIT 1
            """,
            (objectId, *visibilityValues),
        )
        columns = tuple(item[0] for item in cursor.description)
        objectRow = self._row(columns, cursor.fetchone())
        if objectRow is None:
            return None
        resourceRefsValue = json.loads(str(objectRow["resourceRefs"]))
        if (
            not isinstance(resourceRefsValue, list)
            or not resourceRefsValue
            or any(not isinstance(item, str) or not item for item in resourceRefsValue)
            or len(resourceRefsValue) != len(set(resourceRefsValue))
        ):
            return None
        resourceRefs = tuple(resourceRefsValue)
        if len(resourceRefs) > _OBJECT_DETAIL_MAX_RESOURCES:
            raise ValueError("object detail resource budget exceeded")
        if objectRow["primaryResourceVersionId"] not in resourceRefs:
            return None
        resourcePlaceholders = ", ".join("?" for _ in resourceRefs)
        resourceCursor = self.connection.execute(
            f"SELECT * FROM resources WHERE resourceVersionId IN ({resourcePlaceholders}) "
            f"AND visibility IN ({placeholders}) ORDER BY resourceVersionId",
            (*resourceRefs, *visibilityValues),
        )
        resourceColumns = tuple(item[0] for item in resourceCursor.description)
        resources = tuple(self._row(resourceColumns, row) for row in resourceCursor.fetchall())
        if {str(item["resourceVersionId"]) for item in resources} != set(resourceRefs):
            return None
        evidenceCursor = self.connection.execute(
            f"SELECT * FROM evidence WHERE objectId = ? "
            f"AND resourceVersionId IN ({resourcePlaceholders}) "
            f"AND visibility IN ({placeholders}) ORDER BY evidenceId "
            f"LIMIT {_OBJECT_DETAIL_MAX_EVIDENCE + 1}",
            (objectId, *resourceRefs, *visibilityValues),
        )
        evidenceColumns = tuple(item[0] for item in evidenceCursor.description)
        evidence = tuple(self._row(evidenceColumns, row) for row in evidenceCursor.fetchall())
        if len(evidence) > _OBJECT_DETAIL_MAX_EVIDENCE:
            raise ValueError("object detail evidence budget exceeded")
        if {str(item["resourceVersionId"]) for item in evidence} != set(resourceRefs):
            return None
        return {"object": objectRow, "resources": resources, "evidence": evidence}

    def close(self) -> None:
        self.connection.close()
        self.tables.clear()

    def __enter__(self) -> "InMemoryCatalog":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()
