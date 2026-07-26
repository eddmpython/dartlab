"""Provider 경계, source pin, description task 준비 계층.

형제 lane 인 `ownerPaging*` 과 `compositePaging*` 은 이미 같은 역할로 나뉘어 있다.
이 lane 만 한 파일에 전부 갖고 있어 파일 크기 룰의 800 줄 상한을 넘겼다.
의존 방향은 models, state, payload, source, schedule, results 순 단방향이다.
"""

from __future__ import annotations

import hmac
import importlib
from collections.abc import Mapping
from typing import Any

from dartlab.dataHub.continuation import (
    ArrowPayloadFacts,
    ContinuationError,
    ContinuationPins,
    ContinuationStore,
    arrowSchemaDigest,
    bytesDigest,
    canonicalDigest,
)
from dartlab.dataHub.contracts import (
    DataAssetDescriptor,
    DataQuery,
    NativeProjection,
)
from dartlab.dataHub.pagingRuntime import (
    continuationStore,
    manifestCachePath,
    requireDeadline,
)

from .resourcePagingModels import (
    _FORMAT_VERSION,
    _MULTIPLEX_SCHEMA,
    _OWNER_CONTRACTS_MODULE,
    _OWNER_MODULE,
    _PAGEABLE_PARAM_KEYS,
    _REQUEST_MAPPING_KEYS,
    _OwnerBoundary,
    _ResourceSession,
    _ResourceTask,
    _textDigest,
)
from .resourcePagingPayload import (
    _innerTable,
    _validateMultiplexPayload,
)
from .resourcePagingState import (
    _cursorMapping,
    _cursorPosition,
    _originCursor,
)


def _ownerBoundary() -> _OwnerBoundary:
    """Provider adapter와 request contract를 정적 의존 없이 불러온다."""

    module = importlib.import_module(_OWNER_MODULE)
    contracts = importlib.import_module(_OWNER_CONTRACTS_MODULE)
    describe = getattr(module, "describeResource")
    read = getattr(module, "readResourcePage")
    prepare = getattr(module, "prepareResourceRead", None)
    requestType = getattr(contracts, "ResourceReadRequest")
    if (
        not callable(describe)
        or not callable(read)
        or (prepare is not None and not callable(prepare))
        or not hasattr(requestType, "fromMapping")
    ):
        raise RuntimeError("resource owner boundary가 유효하지 않습니다")
    return _OwnerBoundary(describe, read, requestType, prepare)


def _continuationStore(*, deadline: float, runMaintenance: bool = True) -> ContinuationStore:
    return continuationStore(
        deadline=deadline,
        payloadValidator=_validateMultiplexPayload,
        runMaintenance=runMaintenance,
    )


def _contractDigest(session: _ResourceSession) -> str:
    return canonicalDigest(
        {
            "format": "dartlab-resource-multiplex",
            "version": _FORMAT_VERSION,
            "contractHash": session.contractHash,
            "tasks": [
                {
                    "requestId": task.requestId,
                    "assetId": task.assetId,
                    "assetVersionId": task.assetVersionId,
                    "category": task.category,
                    "requestMapping": task.requestMapping,
                    "sourceShardCount": task.sourceShardCount,
                    "selectedShardCount": task.selectedShardCount,
                    "executionMode": task.executionMode,
                    "provider": task.provider,
                    "market": task.market,
                }
                for task in session.tasks
            ],
        }
    )


def _pins(session: _ResourceSession, queryPayload: bytes, sourcePins: Mapping[str, str]) -> ContinuationPins:
    return ContinuationPins(
        sourceDigest=canonicalDigest(dict(sourcePins)),
        queryDigest=bytesDigest(queryPayload),
        contractDigest=_contractDigest(session),
        schemaDigest=arrowSchemaDigest(_MULTIPLEX_SCHEMA),
    )


def _requireCurrentPins(expected: ContinuationPins, current: ContinuationPins) -> None:
    checks = (
        (expected.sourceDigest, current.sourceDigest, "CONTINUATION_SOURCE_STALE"),
        (expected.queryDigest, current.queryDigest, "CONTINUATION_QUERY_STALE"),
        (expected.contractDigest, current.contractDigest, "CONTINUATION_CONTRACT_STALE"),
        (expected.schemaDigest, current.schemaDigest, "CONTINUATION_SCHEMA_STALE"),
    )
    for expectedValue, currentValue, code in checks:
        if not hmac.compare_digest(expectedValue, currentValue):
            raise ContinuationError(code)


def isPageableResource(descriptor: DataAssetDescriptor, query: DataQuery) -> bool:
    """Descriptor와 projection이 full-universe pageable resource인지 판별한다."""

    return (
        isinstance(query.projection, NativeProjection)
        and not query.subjects
        and descriptor.kind == "resource"
        and descriptor.executorKind == "resource"
        and descriptor.assetId.startswith("resource.")
        and (descriptor.executionMode == "resourceCompanyShard" or descriptor.assetId == "resource.edgar")
    )


def _normalizedRequestMapping(
    boundary: _OwnerBoundary,
    descriptor: DataAssetDescriptor,
    query: DataQuery,
    description: Any,
) -> tuple[dict[str, Any], str]:
    params = dict(query.params)
    if any(type(key) is not str for key in params) or not set(params) <= _PAGEABLE_PARAM_KEYS:
        raise ValueError("pageable resource params가 유효하지 않습니다")
    schemaFields = getattr(description, "schemaFields", None)
    if not isinstance(schemaFields, tuple) or any(
        not isinstance(field, tuple) or len(field) != 2 or any(type(item) is not str for item in field)
        for field in schemaFields
    ):
        raise ValueError("resource description schema가 유효하지 않습니다")
    available = {name for name, _fieldType in schemaFields}
    rawColumns = params.get("columns")
    if rawColumns is None:
        columns = tuple(name for name, _fieldType in schemaFields if name != "contentRaw")
    elif isinstance(rawColumns, (tuple, list)) and all(type(item) is str for item in rawColumns):
        columns = tuple(rawColumns)
    else:
        raise ValueError("resource columns가 유효하지 않습니다")
    if not columns or not set(columns) <= available:
        raise ValueError("resource columns가 description 밖에 있습니다")
    base: dict[str, Any] = {
        "columns": list(columns),
        "predicates": params.get("predicates", []),
        "companyIds": params.get("companyIds", []),
        "includeSourcePath": params.get("includeSourcePath", True),
        "allowRawContent": params.get("allowRawContent", False),
    }
    probe = boundary.requestType.fromMapping(base | {"batchRows": 1, "maxRows": 1, "maxBytes": 1})
    normalized = probe.toMapping()
    semantic = {key: normalized[key] for key in _REQUEST_MAPPING_KEYS}
    ownerQueryPin = probe.queryPin(descriptor.assetId)
    if not isinstance(ownerQueryPin, str) or not ownerQueryPin:
        raise ValueError("resource owner query pin이 비었습니다")
    return semantic, ownerQueryPin


def _descriptionTask(
    boundary: _OwnerBoundary,
    requestId: str,
    descriptor: DataAssetDescriptor,
    query: DataQuery,
    *,
    description: Any | None = None,
) -> _ResourceTask:
    category = descriptor.executorAxis or descriptor.assetId.removeprefix("resource.")
    cachePath = manifestCachePath(descriptor.assetId, category)
    if description is None:
        description = boundary.describe(descriptor.assetId, category, cachePath)
    if (
        getattr(description, "resourceId", None) != descriptor.assetId
        or getattr(description, "category", None) != category
    ):
        raise ValueError("resource description identity가 다릅니다")
    ownerSourcePin = getattr(description, "sourcePin", None)
    if not isinstance(ownerSourcePin, str) or not ownerSourcePin.startswith("resource-source-full:"):
        raise ValueError("resource source pin이 full identity가 아닙니다")
    mapping, ownerQueryPin = _normalizedRequestMapping(boundary, descriptor, query, description)
    sourceShardCount = getattr(description, "shardCount", None)
    if type(sourceShardCount) is not int or sourceShardCount <= 0:
        raise ValueError("resource description shard count가 유효하지 않습니다")
    selectedCompanyIds = mapping["companyIds"]
    if not isinstance(selectedCompanyIds, (tuple, list)):
        raise ValueError("resource selected shard가 유효하지 않습니다")
    selectedShardCount = len(selectedCompanyIds) if selectedCompanyIds else sourceShardCount
    if selectedShardCount <= 0 or selectedShardCount > sourceShardCount:
        raise ValueError("resource selected shard count가 유효하지 않습니다")
    metadata = dict(descriptor.metadata)
    provider = metadata.get("sourceProvider", descriptor.owner)
    market = descriptor.universeMarkets[0] if len(descriptor.universeMarkets) == 1 else "UNKNOWN"
    if not isinstance(provider, str) or not provider or not isinstance(market, str) or not market:
        raise ValueError("resource coverage contract가 유효하지 않습니다")
    return _ResourceTask(
        requestId=requestId,
        assetId=descriptor.assetId,
        assetVersionId=descriptor.assetVersionId,
        category=category,
        sourceRef=descriptor.sourceRef,
        sourcePin=_textDigest(ownerSourcePin),
        queryPin=_textDigest(ownerQueryPin),
        ownerSourcePin=ownerSourcePin,
        ownerQueryPin=ownerQueryPin,
        requestMapping=mapping,
        sourceShardCount=sourceShardCount,
        selectedShardCount=selectedShardCount,
        executionMode=descriptor.executionMode,
        provider=provider,
        market=market,
    )


def _preparedDescriptionTask(
    boundary: _OwnerBoundary,
    requestId: str,
    descriptor: DataAssetDescriptor,
    query: DataQuery,
) -> tuple[_ResourceTask, Any | None]:
    """가능하면 description과 바로 이어질 page가 같은 owner manifest를 쓰게 한다."""

    if boundary.prepare is None:
        return _descriptionTask(boundary, requestId, descriptor, query), None
    category = descriptor.executorAxis or descriptor.assetId.removeprefix("resource.")
    prepared = boundary.prepare(
        descriptor.assetId,
        category,
        manifestCachePath(descriptor.assetId, category),
    )
    description = getattr(prepared, "description", None)
    if description is None or not callable(getattr(prepared, "read", None)):
        raise ValueError("prepared resource owner 계약이 유효하지 않습니다")
    return (
        _descriptionTask(
            boundary,
            requestId,
            descriptor,
            query,
            description=description,
        ),
        prepared,
    )


def _currentSourcePins(
    boundary: _OwnerBoundary,
    session: _ResourceSession,
    *,
    deadline: float,
) -> tuple[dict[str, str], dict[str, Any]]:
    pins = {}
    preparedReads: dict[str, Any] = {}
    for task in session.tasks:
        requireDeadline(deadline)
        if boundary.prepare is None:
            description = boundary.describe(
                task.assetId,
                task.category,
                manifestCachePath(task.assetId, task.category),
            )
        else:
            prepared = boundary.prepare(
                task.assetId,
                task.category,
                manifestCachePath(task.assetId, task.category),
            )
            description = getattr(prepared, "description", None)
            if description is None or not callable(getattr(prepared, "read", None)):
                raise ContinuationError("CONTINUATION_SOURCE_STALE")
            preparedReads[task.requestId] = prepared
        requireDeadline(deadline)
        if (
            getattr(description, "resourceId", None) != task.assetId
            or getattr(description, "category", None) != task.category
            or getattr(description, "shardCount", None) != task.sourceShardCount
        ):
            raise ContinuationError("CONTINUATION_SOURCE_STALE")
        ownerPin = getattr(description, "sourcePin", None)
        if not isinstance(ownerPin, str):
            raise ContinuationError("CONTINUATION_SOURCE_STALE")
        pins[task.requestId] = _textDigest(ownerPin)
    return pins, preparedReads


def _validateOwnerPage(
    task: _ResourceTask,
    page: Any,
    request: Any,
) -> tuple[ArrowPayloadFacts, bytes, dict[str, int], dict[str, int] | None, int]:
    if getattr(page, "resourceId", None) != task.assetId or getattr(page, "category", None) != task.category:
        raise ValueError("owner page identity가 다릅니다")
    payload = getattr(page, "encodedBytes", None)
    encodedByteCount = getattr(page, "encodedByteCount", None)
    actualSchemaFields = getattr(page, "actualSchemaFields", None)
    receipt = getattr(page, "receipt", None)
    if not isinstance(payload, bytes) or encodedByteCount != len(payload) or receipt is None:
        raise ValueError("owner encoded payload claim이 다릅니다")
    integerClaims = ("startRow", "nextRow", "batchCount", "rowCount", "byteCount", "scannedShardCount")
    if (
        any(type(getattr(receipt, name, None)) is not int for name in integerClaims)
        or type(getattr(receipt, "truncated", None)) is not bool
    ):
        raise ValueError("owner receipt type이 다릅니다")
    facts, table, batchCount = _innerTable(payload, logicalLimit=request.maxBytes)
    try:
        startCursor = _cursorMapping(getattr(receipt, "startCursor", None))
        rawNextCursor = getattr(receipt, "nextCursor", None)
        nextCursor = _cursorMapping(rawNextCursor) if rawNextCursor is not None else None
    except (TypeError, ValueError):
        raise ValueError("owner receipt cursor가 다릅니다") from None
    expectedStartCursor = _cursorMapping(task.cursor) if task.cursor is not None else _originCursor()
    parsedSchema = tuple((field.name, str(field.type)) for field in table.schema)
    if actualSchemaFields != parsedSchema:
        raise ValueError("owner actual schema claim이 다릅니다")
    expectedBatchCount = 1 if facts.rowCount else 0
    checks = (
        getattr(receipt, "sourcePin", None) == task.ownerSourcePin,
        getattr(receipt, "queryPin", None) == task.ownerQueryPin,
        getattr(receipt, "integrityMode", None) == "full",
        getattr(receipt, "startRow", None) == task.startRow,
        getattr(receipt, "nextRow", None) == task.startRow + facts.rowCount,
        getattr(receipt, "batchCount", None) == expectedBatchCount,
        getattr(receipt, "rowCount", None) == facts.rowCount,
        startCursor == expectedStartCursor,
        getattr(receipt, "truncated", None) == (nextCursor is not None),
        0 < getattr(receipt, "scannedShardCount", 0) <= request.maxShards,
        getattr(receipt, "scannedShardCount", 0) <= task.selectedShardCount,
        startCursor["shardOrdinal"] < task.selectedShardCount,
        nextCursor is None or nextCursor["shardOrdinal"] < task.selectedShardCount,
        nextCursor is None or _cursorPosition(nextCursor) > _cursorPosition(startCursor),
        0 <= getattr(receipt, "byteCount", -1) <= request.maxBytes,
        facts.rowCount == 0 or getattr(receipt, "byteCount", 0) > 0,
        batchCount == 1,
        _textDigest(getattr(receipt, "sourcePin", "")) == task.sourcePin,
        _textDigest(getattr(receipt, "queryPin", "")) == task.queryPin,
    )
    if not all(checks):
        raise ValueError("owner receipt claim이 다릅니다")
    return facts, payload, startCursor, nextCursor, receipt.scannedShardCount
