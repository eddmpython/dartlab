"""Owner-native output을 typed Data Workbench projection으로 변환한다."""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping, Sequence
from typing import Any

import polars as pl

from dartlab.dataHub.contracts import (
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
from dartlab.dataHub.identity.contentSeal import contentHash, executionReceipt
from dartlab.dataHub.projection.evidence import lineageFacet, narrativeFrame, qualityAssertions
from dartlab.dataHub.transport.valueCodec import ValueCodecError, encodedValueSize, encodeValueTree

_RECEIPT_PLACEHOLDER = f"data-execution:{'0' * 64}"


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
        while value.height > 1 and encodedValueSize(value) > maxBytes:
            value = value.head(max(1, value.height // 2))
            truncated = True
        if encodedValueSize(value) > maxBytes:
            raise ValueCodecError("PROJECTION_BYTE_BUDGET")
        return value, truncated
    try:
        encodeValueTree(value, maxBytes=maxBytes)
        return value, truncated
    except ValueCodecError as error:
        if error.code != "PROJECTION_BYTE_BUDGET":
            raise
    if isinstance(value, (list, tuple)):
        candidate = value
        while len(candidate) > 1:
            try:
                encodeValueTree(candidate, maxBytes=maxBytes)
                return candidate, True
            except ValueCodecError as error:
                if error.code != "PROJECTION_BYTE_BUDGET":
                    raise
            candidate = candidate[: max(1, len(candidate) // 2)]
            truncated = True
    raise ValueCodecError("PROJECTION_BYTE_BUDGET")


def _records(value: Any, *, path: str = "$") -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
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
    subject: str | None,
    market: str | None,
    receiptRef: str,
) -> tuple[pl.DataFrame | None, tuple[DataGap, ...]]:
    from dartlab.dataHub.feature.query import FeatureQueryError, featureObservationSetFromValue

    try:
        featureDataset = featureObservationSetFromValue(raw)
    except FeatureQueryError as error:
        return None, (DataGap(error.code, str(error), descriptor.assetId),)
    if featureDataset is not None:
        return _featureObservationFrame(
            featureDataset,
            descriptor,
            query,
            measure=measure,
            subject=subject,
            market=market,
            receiptRef=receiptRef,
        )
    if (
        query.time is not None
        and query.time.knownAt is not None
        and dict(descriptor.metadata).get("observationPIT") is True
    ):
        return None, (
            DataGap(
                "FEATURE_OBSERVATION_ENVELOPE_REQUIRED",
                "observationPIT owner가 검증 가능한 feature observation envelope를 반환하지 않았습니다",
                descriptor.assetId,
                subject,
            ),
        )

    from dartlab.dataHub.projection.factorKernel import foldToCanonical

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
    marketUnit = dict(descriptor.marketUnits).get(market) if market is not None else None
    if projection.unit is None and not marketUnit and not declaredUnit:
        return None, gaps + (
            DataGap(
                "FACTOR_UNIT_REQUIRED",
                "owner unit 선언이 없어 FactorProjection.unit을 명시해야 합니다",
                descriptor.assetId,
            ),
        )
    validAt = query.time.validAt if query.time else None
    temporalStatus = "VALID_TIME" if validAt else "LATEST_ONLY"
    unit = projection.unit or marketUnit or str(declaredUnit)
    frequency = projection.frequency or str(query.params.get("freq") or "native")
    availableAt = declared.get("availableAt")
    entityExpression = (
        pl.concat_str(pl.lit(market), pl.col("entity").cast(pl.Utf8), separator=":")
        if market is not None
        else pl.col("entity").cast(pl.Utf8)
    )
    frame = folded.with_columns(
        pl.lit(descriptor.assetId).alias("assetId"),
        pl.col("item").alias("measureId"),
        entityExpression.alias("entityId"),
        pl.col("entity").cast(pl.Utf8).alias("sourceEntityId"),
        pl.lit(market, dtype=pl.Utf8).alias("market"),
        pl.col("period").alias("eventAt"),
        pl.lit(str(availableAt) if availableAt is not None else None, dtype=pl.Utf8).alias("availableAt"),
        pl.lit(None, dtype=pl.Utf8).alias("knownAt"),
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
        "sourceEntityId",
        "market",
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


def _selectionContractGap(result, projection, descriptor: DataAssetDescriptor) -> DataGap | None:
    """읽어 온 관측이 projection 이 선언한 뜻과 맞는지 본다. 어긋나면 gap.

    단위와 주기는 관측 자체의 의미다. projection 이 다른 값을 적었다고 그것으로 덮어쓰면
    숫자는 그대로인데 뜻만 바뀐 결과가 나간다. 그래서 맞추는 대신 실패로 끝낸다.
    """
    if not result.selections:
        return DataGap("FACTOR_EMPTY", "feature observation이 없습니다", descriptor.assetId)
    if projection.unit is not None and any(item.observation.unit != projection.unit for item in result.selections):
        return DataGap(
            "FACTOR_UNIT_MISMATCH",
            "FeatureProjection.unit은 observation 의미를 덮어쓸 수 없습니다",
            descriptor.assetId,
        )
    if projection.frequency is not None and any(
        item.observation.frequency != projection.frequency for item in result.selections
    ):
        return DataGap(
            "FACTOR_FREQUENCY_MISMATCH",
            "FeatureProjection.frequency는 observation 의미를 덮어쓸 수 없습니다",
            descriptor.assetId,
        )
    return None


def _resolveEntityIds(
    requestedSubjects,
    *,
    availableEntities: tuple[str, ...],
    requestedMarket: str | None,
    descriptor: DataAssetDescriptor,
) -> tuple[list[str], DataGap | None]:
    """요청한 종목 표기를 canonical entityId 로 해소한다.

    시장 접두어가 붙었으면 asset 의 시장과 어긋나지 않는지 보고, 안 붙었으면 asset 의 시장을
    씌운다. 둘 다 없으면 무엇으로 해소할지 정할 근거가 없어 실패로 끝낸다. 추측해서 붙이면
    다른 시장의 같은 코드를 조용히 집을 수 있다.

    Returns:
        ``(entityIds, gap)``. gap 이 있으면 목록은 쓰지 않는다.
    """
    entityIds: list[str] = []
    for raw in requestedSubjects:
        requested = str(raw).strip()
        if ":" in requested:
            entityMarket, _separator, entity = requested.partition(":")
            canonical = f"{entityMarket.upper()}:{entity}"
            if requestedMarket is not None and entityMarket.upper() != requestedMarket:
                return [], DataGap(
                    "FEATURE_MARKET_MISMATCH",
                    f"requested market {entityMarket.upper()}가 asset market {requestedMarket}와 다릅니다",
                    descriptor.assetId,
                    requested,
                )
            matches = tuple(entityId for entityId in availableEntities if entityId.casefold() == canonical.casefold())
        elif requestedMarket is not None:
            canonical = f"{requestedMarket}:{requested}"
            matches = tuple(entityId for entityId in availableEntities if entityId.casefold() == canonical.casefold())
        else:
            return [], DataGap(
                "FEATURE_MARKET_REQUIRED",
                f"{requested}를 canonical entityId로 해소할 market이 없습니다",
                descriptor.assetId,
                requested,
            )
        entityIds.extend(matches or (canonical,))
    return entityIds, None


def _featureObservationFrame(
    dataset: Any,
    descriptor: DataAssetDescriptor,
    query: DataQuery,
    *,
    measure: str | None,
    subject: str | None,
    market: str | None,
    receiptRef: str,
) -> tuple[pl.DataFrame | None, tuple[DataGap, ...]]:
    """검증된 observation dataset을 실제 bitemporal factor view로 투영한다."""

    from dartlab.dataHub.feature.query import FeatureQueryError, FeatureReadQuery, readFeatures

    projection = query.projection
    assert isinstance(projection, FactorProjection)
    featureIds = projection.measures or query.measures or ((measure,) if measure is not None else ())
    availableEntities = tuple(sorted({item.entityId for item in dataset.observations}))
    declaredMarket = dict(descriptor.metadata).get("market")
    requestedMarket = (market or (str(declaredMarket) if declaredMarket is not None else "")).upper() or None
    requestedSubjects = (subject,) if subject is not None else query.subjects
    entityIds, resolveGap = _resolveEntityIds(
        requestedSubjects,
        availableEntities=availableEntities,
        requestedMarket=requestedMarket,
        descriptor=descriptor,
    )
    if resolveGap is not None:
        return None, (resolveGap,)
    knownAt = query.time.knownAt if query.time else None
    validAt = query.time.validAt if query.time else None
    try:
        result = readFeatures(
            dataset,
            FeatureReadQuery(
                featureIds=tuple(featureIds),
                entityIds=tuple(dict.fromkeys(entityIds)),
                validAt=validAt,
                knownAt=knownAt,
                mode="pointInTime" if knownAt is not None else "history",
            ),
        )
    except FeatureQueryError as error:
        return None, (DataGap(error.code, str(error), descriptor.assetId, subject),)
    gaps = tuple(
        DataGap(
            "FEATURE_OBSERVATION_MISSING",
            f"{featureId}/{entityId}",
            descriptor.assetId,
            entityId,
        )
        for featureId, entityId in result.missing
    )
    selectionGap = _selectionContractGap(result, projection, descriptor)
    if selectionGap is not None:
        if not result.selections:
            # 고른 관측이 하나도 없을 때는 앞서 모은 결손이 이미 이유를 말한다. 그것이
            # 비어 있을 때만 "비었다" 를 새로 적는다. 둘을 겹쳐 적으면 같은 사실이 두 번 나간다.
            return None, gaps or (selectionGap,)
        return None, gaps + (selectionGap,)
    if result.mode == "pointInTime":
        gaps += tuple(
            DataGap(
                "FEATURE_OBSERVATION_CONDITIONAL",
                f"{item.featureId}/{item.observation.entityId}",
                descriptor.assetId,
                item.observation.entityId,
            )
            for item in result.selections
            if not item.exactAsKnown
        )
    rows = []
    for item in result.selections:
        observation = item.observation
        entityMarket, separator, _entity = observation.entityId.partition(":")
        if separator and requestedMarket is not None and entityMarket != requestedMarket:
            # 돌려받은 관측이 요청한 시장과 다르면 그것은 다른 회사다. 붙여서 내보내면
            # 사용자는 자기가 물어본 종목의 값으로 읽는다.
            return None, gaps + (
                DataGap(
                    "FEATURE_MARKET_MISMATCH",
                    f"observation market {entityMarket}가 요청 market {requestedMarket}와 다릅니다",
                    descriptor.assetId,
                    observation.entityId,
                ),
            )
        effectiveMarket = entityMarket if separator else requestedMarket
        canonicalEntity = (
            observation.entityId
            if separator or effectiveMarket is None
            else f"{effectiveMarket}:{observation.entityId}"
        )
        rows.append(
            {
                "assetId": descriptor.assetId,
                "measureId": item.featureId,
                "featureVersionId": item.featureVersionId,
                "entityId": canonicalEntity,
                "sourceEntityId": _entity if separator else observation.entityId,
                "market": effectiveMarket,
                "entityName": None,
                "eventAt": observation.eventAt,
                "availableAt": observation.availableAt,
                "knownAt": observation.knowledgeAsOf,
                "value": float(observation.value),
                "valueText": None,
                "unit": observation.unit,
                "frequency": observation.frequency,
                "revisionId": observation.revisionId,
                "sourceRef": observation.vintage.artifactId,
                "evidenceRef": receiptRef,
                "status": "ok" if item.exactAsKnown else "conditional",
                "gapReason": None if item.exactAsKnown else "conditionalRevisionCoverage",
                "temporalStatus": "POINT_IN_TIME" if knownAt is not None else "OBSERVATION_HISTORY",
                "featureRegistryHash": result.registryHash,
                "featureObservationSetHash": result.observationSetHash,
                "featureQueryHash": result.queryHash,
                "providerId": observation.providerId,
                "datasetId": observation.datasetId,
                "signalId": observation.signalId,
                "timing": observation.timing,
                "transformId": observation.transformId,
                "evidenceRole": observation.evidenceRole,
                "availabilityPrecision": observation.availabilityPrecision,
                "normalizationRuleHash": observation.normalizationRuleHash,
                "revisionPolicy": observation.vintage.revisionPolicy,
                "coverage": observation.vintage.coverage,
                "vintagePayloadHash": observation.vintage.payloadHash,
                "vintageArtifactHash": observation.vintage.artifactHash,
                "vintageContractHash": observation.vintage.contractHash or None,
                "vintageReceiptId": observation.vintage.receiptId or None,
                "observationId": observation.observationId,
            }
        )
    return pl.DataFrame(rows, strict=False), gaps


def _semanticContent(data: Any, projection: Any) -> Any:
    """projection이 생성한 순환 provenance만 content hash 입력에서 제거한다."""

    if isinstance(projection, (FactorProjection, NarrativeProjection)):
        if isinstance(data, pl.DataFrame) and "evidenceRef" in data.columns:
            return data.drop("evidenceRef")
    if isinstance(projection, GraphProjection) and isinstance(data, Mapping):
        semantic = dict(data)
        evidence = semantic.get("evidence")
        if isinstance(evidence, Mapping):
            semantic["evidence"] = {key: value for key, value in evidence.items() if key != "evidenceRef"}
        return semantic
    return data


def _bindReceipt(data: Any, projection: Any, receiptRef: str) -> Any:
    """content에서 유도한 최종 receipt를 projection provenance에 다시 결박한다."""

    if isinstance(projection, (FactorProjection, NarrativeProjection)):
        if isinstance(data, pl.DataFrame) and "evidenceRef" in data.columns:
            return data.with_columns(pl.lit(receiptRef).alias("evidenceRef"))
    if isinstance(projection, GraphProjection) and isinstance(data, Mapping):
        bound = dict(data)
        evidence = bound.get("evidence")
        if isinstance(evidence, Mapping):
            bound["evidence"] = {**evidence, "evidenceRef": receiptRef}
        return bound
    return data


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
        receiptRef: 실제 결과와 결합할 deterministic request ref.

    Returns:
        DataPartition 또는 None과 projection gap tuple.

    Raises:
        없음. projection mismatch는 gap으로 반환한다.
    """
    projection = query.projection
    data = raw
    gaps: tuple[DataGap, ...] = ()
    if (
        query.time is not None
        and query.time.knownAt is not None
        and dict(descriptor.metadata).get("observationPIT") is True
        and not isinstance(projection, FactorProjection)
    ):
        return None, (
            DataGap(
                "FEATURE_PIT_PROJECTION_REQUIRED",
                "observationPIT asset은 검증된 관측 envelope를 보존하는 FactorProjection이 필요합니다",
                descriptor.assetId,
                selector.get("subject"),
            ),
        )
    locatorOnly = isinstance(projection, ResourceProjection) and not projection.includePayload
    if _isEmpty(raw) and not locatorOnly:
        return None, (DataGap("NO_DATA", "owner가 물질화할 데이터를 반환하지 않았습니다", descriptor.assetId),)
    if isinstance(projection, FactorProjection):
        data, gaps = _factorFrame(
            raw,
            descriptor,
            query,
            measure=selector.get("measure"),
            subject=selector.get("subject"),
            market=selector.get("market"),
            receiptRef=_RECEIPT_PLACEHOLDER,
        )
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
            "evidenceRef": _RECEIPT_PLACEHOLDER,
        }
    elif isinstance(projection, NarrativeProjection):
        data = narrativeFrame(raw, descriptor, query, selector=selector, receiptRef=_RECEIPT_PLACEHOLDER)
        if data.is_empty():
            return None, (DataGap("PROJECTION_INCOMPATIBLE", "narrative text가 없습니다", descriptor.assetId),)
    elif isinstance(projection, ResourceProjection):
        sourcePin = raw.get("sourcePin") if locatorOnly and isinstance(raw, Mapping) else None
        if locatorOnly and (type(sourcePin) is not str or not sourcePin.startswith("resource-source-full:")):
            return None, (
                DataGap(
                    "RESOURCE_SOURCE_UNVERIFIED", "resource locator의 full source pin이 없습니다", descriptor.assetId
                ),
            )
        data = {
            "assetId": descriptor.assetId,
            "sourceRef": f"{descriptor.sourceRef}#{sourcePin}" if sourcePin is not None else descriptor.sourceRef,
            "sourcePin": sourcePin,
            "assetVersionId": descriptor.assetVersionId,
            "visibility": descriptor.visibility,
            "licenseRef": descriptor.licenseRef,
            "payload": raw if projection.includePayload else None,
        }
    elif not isinstance(projection, NativeProjection):
        return None, (DataGap("PROJECTION_UNKNOWN", type(projection).__name__, descriptor.assetId),)

    data, truncated = _bounded(data, query.budget.maxRows, query.budget.maxBytes)
    contentHashRef = contentHash(_semanticContent(data, projection))
    finalReceiptRef = executionReceipt(receiptRef, contentHashRef)
    data = _bindReceipt(data, projection, finalReceiptRef)
    rowCount = _rowCount(data)
    knownAt = query.time.knownAt if query.time else None
    validAt = query.time.validAt if query.time else None
    temporalStatus = "POINT_IN_TIME" if knownAt else "VALID_TIME" if validAt else "LATEST_ONLY"
    if isinstance(data, pl.DataFrame) and data.height and "temporalStatus" in data.columns:
        statuses = tuple(data["temporalStatus"].drop_nulls().unique().to_list())
        if len(statuses) == 1:
            temporalStatus = str(statuses[0])
    from dartlab.dataHub.transport.valueCodec import encodedValueSize

    outputBytes = encodedValueSize(data)
    assertions = qualityAssertions(
        descriptor,
        query,
        rowCount=rowCount,
        outputBytes=outputBytes,
        truncated=truncated,
        contentHash=contentHashRef,
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
        lineageRefs=(descriptor.sourceRef, finalReceiptRef),
        requestId=requestId,
        lineage=lineageFacet(descriptor, finalReceiptRef),
        qualityAssertions=assertions,
        contentHash=contentHashRef,
    )
    return partition, gaps
