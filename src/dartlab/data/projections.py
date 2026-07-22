"""Owner-native output을 typed Data Workbench projection으로 변환한다."""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping, Sequence
from typing import Any

import polars as pl

from dartlab.data.contracts import (
    AssetRef,
    DataAssetDescriptor,
    DataGap,
    DataPartition,
    DataQuery,
    FactorProjection,
    GraphProjection,
    NarrativeProjection,
    NativeProjection,
    RecordsProjection,
    ResourceProjection,
)
from dartlab.data.evidence import lineageFacet, narrativeFrame, qualityAssertions


def _schema(value: Any) -> tuple[tuple[str, str], ...]:
    if isinstance(value, pl.DataFrame):
        return tuple((name, str(dtype)) for name, dtype in value.schema.items())
    if isinstance(value, Mapping):
        return tuple(sorted((str(key), type(item).__name__) for key, item in value.items()))
    return (("value", type(value).__name__),)


def _rowCount(value: Any) -> int:
    if isinstance(value, pl.DataFrame):
        return value.height
    if isinstance(value, (Mapping, str, bytes)) or value is None:
        return 1
    if isinstance(value, Sequence):
        return len(value)
    return 1


def _isEmpty(value: Any) -> bool:
    """Owner의 실제 결손을 빈 성공 partition으로 바꾸지 않는다."""

    if value is None:
        return True
    if isinstance(value, pl.DataFrame):
        return value.is_empty()
    if isinstance(value, (Mapping, Sequence)) and not isinstance(value, (str, bytes)):
        return len(value) == 0
    if isinstance(value, str):
        return not value.strip()
    return False


def _truncate(value: Any, maxRows: int) -> tuple[Any, bool]:
    if isinstance(value, pl.DataFrame):
        return value.head(maxRows), value.height > maxRows
    if isinstance(value, list):
        return value[:maxRows], len(value) > maxRows
    if isinstance(value, tuple):
        return value[:maxRows], len(value) > maxRows
    return value, False


def _bounded(value: Any, maxRows: int, maxBytes: int) -> tuple[Any, bool]:
    value, truncated = _truncate(value, maxRows)
    if isinstance(value, pl.DataFrame):
        while value.height > 1 and value.estimated_size() > maxBytes:
            value = value.head(max(1, value.height // 2))
            truncated = True
        if value.estimated_size() > maxBytes:
            raise ValueError("projection output이 maxBytes를 초과했습니다")
        return value, truncated
    encoded = repr(value).encode("utf-8")
    if len(encoded) <= maxBytes:
        return value, truncated
    if isinstance(value, (list, tuple)):
        candidate = value
        while len(candidate) > 1 and len(repr(candidate).encode("utf-8")) > maxBytes:
            candidate = candidate[: max(1, len(candidate) // 2)]
            truncated = True
        if len(repr(candidate).encode("utf-8")) <= maxBytes:
            return candidate, truncated
    raise ValueError("projection output이 maxBytes를 초과했습니다")


def _records(value: Any, *, path: str = "$") -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if dataclasses.is_dataclass(value):
        value = dataclasses.asdict(value)
    if isinstance(value, pl.DataFrame):
        for index, row in enumerate(value.iter_rows(named=True)):
            rows.append({"path": f"{path}[{index}]", "recordKind": "row", "value": row})
        return rows
    if isinstance(value, Mapping):
        for key, item in value.items():
            child = f"{path}.{key}"
            if isinstance(item, (Mapping, list, tuple)) or dataclasses.is_dataclass(item):
                rows.extend(_records(item, path=child))
            else:
                rows.append(
                    {
                        "path": child,
                        "recordKind": "scalar",
                        "value": item if isinstance(item, (int, float, bool)) else None,
                        "valueText": None if item is None or isinstance(item, (int, float, bool)) else str(item),
                    }
                )
        return rows
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            rows.extend(_records(item, path=f"{path}[{index}]"))
        return rows
    return [{"path": path, "recordKind": "scalar", "value": value}]


def _factorFrame(
    raw: Any,
    descriptor: DataAssetDescriptor,
    query: DataQuery,
    *,
    measure: str | None,
    receiptRef: str,
) -> tuple[pl.DataFrame | None, tuple[DataGap, ...]]:
    from dartlab.data.factorKernel import foldToCanonical

    declared = dict(descriptor.metadata)
    folded, foldGaps = foldToCanonical(
        raw,
        engine=descriptor.owner,
        axis=descriptor.executorAxis or descriptor.assetId,
        item=measure,
        declared=declared,
    )
    gaps = tuple(
        DataGap(
            code=str(row.get("gapReason") or "FACTOR_FOLD_FAILED"),
            message=str(row.get("observed") or "factor folding gap"),
            assetId=descriptor.assetId,
        )
        for row in foldGaps
    )
    if folded.is_empty():
        return None, gaps or (DataGap("FACTOR_EMPTY", "factor-compatible observation이 없습니다", descriptor.assetId),)
    projection = query.projection
    assert isinstance(projection, FactorProjection)
    declaredUnit = dict(descriptor.metadata).get("unit")
    if projection.unit is None and not declaredUnit:
        return None, gaps + (
            DataGap(
                "FACTOR_UNIT_REQUIRED",
                "owner unit 선언이 없어 FactorProjection.unit을 명시해야 합니다",
                descriptor.assetId,
            ),
        )
    knownAt = query.time.knownAt if query.time else None
    validAt = query.time.validAt if query.time else None
    temporalStatus = "POINT_IN_TIME" if knownAt else "VALID_TIME" if validAt else "LATEST_ONLY"
    unit = projection.unit or str(declaredUnit)
    frequency = projection.frequency or str(query.params.get("freq") or "native")
    availableAt = declared.get("availableAt")
    frame = folded.with_columns(
        pl.lit(descriptor.assetId).alias("assetId"),
        pl.col("item").alias("measureId"),
        pl.col("entity").alias("entityId"),
        pl.col("period").alias("eventAt"),
        pl.lit(str(availableAt) if availableAt is not None else None, dtype=pl.Utf8).alias("availableAt"),
        pl.lit(knownAt, dtype=pl.Utf8).alias("knownAt"),
        pl.lit(unit).alias("unit"),
        pl.lit(frequency).alias("frequency"),
        pl.lit(descriptor.assetVersionId).alias("revisionId"),
        pl.lit(descriptor.sourceRef).alias("sourceRef"),
        pl.lit(receiptRef).alias("evidenceRef"),
        pl.lit(temporalStatus).alias("temporalStatus"),
    ).select(
        "assetId",
        "measureId",
        "entityId",
        "entityName",
        "eventAt",
        "availableAt",
        "knownAt",
        "value",
        "valueText",
        "unit",
        "frequency",
        "revisionId",
        "sourceRef",
        "evidenceRef",
        "status",
        "gapReason",
        "temporalStatus",
    )
    if projection.measures:
        frame = frame.filter(pl.col("measureId").is_in(projection.measures))
        if frame.is_empty():
            return None, gaps + (
                DataGap("FACTOR_MEASURE_NOT_FOUND", ", ".join(projection.measures), descriptor.assetId),
            )
    return frame, gaps


def projectOutput(
    raw: Any,
    descriptor: DataAssetDescriptor,
    query: DataQuery,
    *,
    selector: Mapping[str, str],
    receiptRef: str,
    requestId: str | None = None,
) -> tuple[DataPartition | None, tuple[DataGap, ...]]:
    """Native output을 query projection 하나로 변환하고 schema partition을 만든다.

    Capabilities:
        native 무손실, records tagged union, factor canonical long, graph와 narrative 보존,
        resource locator projection을 제공한다. incompatible projection은 값 실행 뒤 숨기지 않고 gap이다.

    Args:
        raw: owner executor 반환값.
        descriptor: 실행한 asset descriptor.
        query: projection과 budget이 결박된 query.
        selector: subject와 measure 등 partition selector.
        receiptRef: 같은 실행의 evidence receipt ref.

    Returns:
        DataPartition 또는 None과 projection gap tuple.

    Raises:
        없음. projection mismatch는 gap으로 반환한다.
    """
    projection = query.projection
    data = raw
    gaps: tuple[DataGap, ...] = ()
    locatorOnly = isinstance(projection, ResourceProjection) and not projection.includePayload
    if _isEmpty(raw) and not locatorOnly:
        return None, (DataGap("NO_DATA", "owner가 물질화할 데이터를 반환하지 않았습니다", descriptor.assetId),)
    if isinstance(projection, FactorProjection):
        data, gaps = _factorFrame(raw, descriptor, query, measure=selector.get("measure"), receiptRef=receiptRef)
        if data is None:
            return None, gaps
    elif isinstance(projection, RecordsProjection):
        data = _records(raw)
    elif isinstance(projection, GraphProjection):
        if isinstance(raw, Mapping) and ("nodes" in raw or "edges" in raw):
            data = dict(raw)
        elif isinstance(raw, pl.DataFrame):
            data = {"nodes": (), "edges": tuple(raw.iter_rows(named=True))}
        else:
            return None, (DataGap("PROJECTION_INCOMPATIBLE", "graph 구조가 아닌 asset입니다", descriptor.assetId),)
        data["evidence"] = {
            "assetId": descriptor.assetId,
            "revisionId": descriptor.assetVersionId,
            "sourceRef": descriptor.sourceRef,
            "evidenceRef": receiptRef,
        }
    elif isinstance(projection, NarrativeProjection):
        data = narrativeFrame(raw, descriptor, query, selector=selector, receiptRef=receiptRef)
        if data.is_empty():
            return None, (DataGap("PROJECTION_INCOMPATIBLE", "narrative text가 없습니다", descriptor.assetId),)
    elif isinstance(projection, ResourceProjection):
        data = {
            "assetId": descriptor.assetId,
            "sourceRef": descriptor.sourceRef,
            "assetVersionId": descriptor.assetVersionId,
            "visibility": descriptor.visibility,
            "licenseRef": descriptor.licenseRef,
            "payload": raw if projection.includePayload else None,
        }
    elif not isinstance(projection, NativeProjection):
        return None, (DataGap("PROJECTION_UNKNOWN", type(projection).__name__, descriptor.assetId),)

    data, truncated = _bounded(data, query.budget.maxRows, query.budget.maxBytes)
    rowCount = _rowCount(data)
    knownAt = query.time.knownAt if query.time else None
    validAt = query.time.validAt if query.time else None
    temporalStatus = "POINT_IN_TIME" if knownAt else "VALID_TIME" if validAt else "LATEST_ONLY"
    estimatedSize = getattr(data, "estimated_size", None)
    outputBytes = int(estimatedSize()) if callable(estimatedSize) else len(repr(data).encode("utf-8"))
    assertions = qualityAssertions(
        descriptor,
        query,
        rowCount=rowCount,
        outputBytes=outputBytes,
        truncated=truncated,
    )
    partition = DataPartition(
        asset=AssetRef(descriptor.assetId, descriptor.assetVersionId),
        projectionKind=projection.kind,
        data=data,
        schema=_schema(data),
        rowCount=rowCount,
        truncated=truncated,
        selector=tuple(sorted((str(key), str(value)) for key, value in selector.items())),
        temporalStatus=temporalStatus,
        lineageRefs=(descriptor.sourceRef, receiptRef),
        requestId=requestId,
        lineage=lineageFacet(descriptor, receiptRef),
        qualityAssertions=assertions,
    )
    return partition, gaps
