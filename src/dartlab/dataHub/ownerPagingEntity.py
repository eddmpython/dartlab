"""Owner source shard 검증과 entity 단위 factor 실행."""

from __future__ import annotations

import hashlib
import importlib
from collections.abc import Sequence

import polars as pl

from dartlab.dataHub.continuation import ContinuationError
from dartlab.dataHub.contracts import DataAssetDescriptor
from dartlab.dataHub.ownerPagingModels import (
    _DIGEST_RE,
    _MAX_ENTITY_PARAMS,
    _EntityRef,
    _OwnerEntry,
    _OwnerTask,
    _VerifiedEntitySource,
)
from dartlab.dataHub.ownerPagingPayload import _framePayload
from dartlab.dataHub.ownerPagingState import _requestedMeasures
from dartlab.dataHub.pagingRuntime import manifestCachePath, requireDeadline
from dartlab.dataHub.projection.output import projectOutput


def _requestRef(task: _OwnerTask, entityId: str) -> str:
    from dartlab.dataHub.execution import _requestRef as requestRef

    return requestRef(
        task.descriptor,
        task.query,
        {"subject": entityId},
        task.requestId,
    )


def _failureEntry(
    task: _OwnerTask,
    ordinal: int,
    entity: _EntityRef,
    code: str,
    message: str,
) -> _OwnerEntry:
    return _OwnerEntry(
        requestId=task.requestId,
        assetId=task.descriptor.assetId,
        assetVersionId=task.descriptor.assetVersionId,
        sourcePin=task.sourcePin,
        queryPin=task.queryPin,
        entityOrdinal=ordinal,
        entityId=entity.entityId,
        sourceEntityId=entity.sourceEntityId,
        status="failed",
        gapCodes=(code,),
        gapMessages=(message,),
    )


def _sourcePayloadParams(descriptor: DataAssetDescriptor) -> tuple[str | None, str | None]:
    metadata = dict(descriptor.metadata)
    payloadParam = metadata.get("sourcePayloadParam")
    integrityParam = metadata.get("sourceIntegrityParam")
    return (
        payloadParam if isinstance(payloadParam, str) and payloadParam else None,
        integrityParam if isinstance(integrityParam, str) and integrityParam else None,
    )


def _entityParamMap(descriptor: DataAssetDescriptor) -> tuple[tuple[str, str], ...]:
    """Universe snapshot parameter 이름을 owner executor keyword에 연결한다.

    Args:
        descriptor: Owner asset의 immutable catalog descriptor.

    Returns:
        ``(snapshotName, executorKeyword)`` pair tuple.

    Raises:
        ValueError: 선언이 중복되거나 bounded string pair가 아닐 때.

    Example:
        ``_entityParamMap(descriptor)``.
    """

    raw = dict(descriptor.metadata).get("entityParamMap", ())
    if not isinstance(raw, (tuple, list)) or len(raw) > _MAX_ENTITY_PARAMS:
        raise ValueError("owner paging entity parameter 선언이 유효하지 않습니다")
    pairs: list[tuple[str, str]] = []
    for item in raw:
        if (
            not isinstance(item, (tuple, list))
            or len(item) != 2
            or not isinstance(item[0], str)
            or not item[0]
            or not isinstance(item[1], str)
            or not item[1]
        ):
            raise ValueError("owner paging entity parameter 선언이 유효하지 않습니다")
        pairs.append((item[0], item[1]))
    if len({source for source, _target in pairs}) != len(pairs) or len({target for _source, target in pairs}) != len(
        pairs
    ):
        raise ValueError("owner paging entity parameter 선언이 중복됩니다")
    return tuple(pairs)


def _prepareEntitySources(
    candidates: Sequence[tuple[_OwnerTask, int]],
    *,
    deadline: float,
) -> dict[tuple[str, int], _VerifiedEntitySource]:
    grouped: dict[tuple[str, str, str], list[tuple[_OwnerTask, int, str]]] = {}
    for task, ordinal in candidates:
        entity = task.entities[ordinal]
        if entity.sourceEntityId is None:
            continue
        grouped.setdefault(
            (task.sourceAssetId, task.sourceCategory, task.ownerSourcePin),
            [],
        ).append((task, ordinal, entity.sourceEntityId))

    prepared: dict[tuple[str, int], _VerifiedEntitySource] = {}
    for (sourceAssetId, sourceCategory, ownerSourcePin), groupedCandidates in grouped.items():
        requireDeadline(deadline)
        try:
            module = importlib.import_module("dartlab.providers.resourceStream.workbench")
            verify = getattr(module, "verifyResourceShardPayloads")
            verified = verify(
                sourceAssetId,
                sourceCategory,
                tuple(sourceId for _task, _ordinal, sourceId in groupedCandidates),
                ownerSourcePin,
                manifestCachePath(
                    sourceAssetId,
                    sourceCategory,
                    create=False,
                ),
                allowMissing=True,
                readOnlyCache=True,
            )
        except ContinuationError:
            raise
        except Exception as error:
            errorCode = getattr(error, "code", None)
            if errorCode in {
                "OFFLINE_NETWORK_BLOCKED",
                "PAGEABLE_EAGER_WRITE_BLOCKED",
            }:
                raise ContinuationError(errorCode) from None
            raise ContinuationError("CONTINUATION_SOURCE_STALE") from None
        requireDeadline(deadline)
        byCompany: dict[str, _VerifiedEntitySource] = {}
        requestedIds = {sourceId for _task, _ordinal, sourceId in groupedCandidates}
        for payload in verified:
            companyId = getattr(payload, "companyId", None)
            encodedBytes = getattr(payload, "encodedBytes", None)
            integrityDigest = getattr(payload, "integrityDigest", None)
            if (
                not isinstance(companyId, str)
                or companyId not in requestedIds
                or type(encodedBytes) is not bytes
                or not encodedBytes
                or not isinstance(integrityDigest, str)
                or not _DIGEST_RE.fullmatch(integrityDigest)
                or hashlib.sha256(encodedBytes).hexdigest() != integrityDigest
            ):
                raise ContinuationError("CONTINUATION_SOURCE_STALE")
            current = _VerifiedEntitySource(encodedBytes, integrityDigest)
            previous = byCompany.setdefault(companyId, current)
            if previous != current:
                raise ContinuationError("CONTINUATION_SOURCE_STALE")
        for task, ordinal, sourceId in groupedCandidates:
            source = byCompany.get(sourceId)
            if source is not None:
                prepared[(task.requestId, ordinal)] = source
    return prepared


def _executeEntity(
    task: _OwnerTask,
    ordinal: int,
    verifiedSource: _VerifiedEntitySource | None = None,
) -> _OwnerEntry:
    entity = task.entities[ordinal]
    descriptor = task.descriptor
    sourcePayloadParam, sourceIntegrityParam = _sourcePayloadParams(descriptor)
    if sourcePayloadParam is not None or sourceIntegrityParam is not None:
        if (
            sourcePayloadParam is None
            or sourceIntegrityParam is None
            or entity.sourceEntityId is None
            or verifiedSource is None
        ):
            return _failureEntry(
                task,
                ordinal,
                entity,
                "FEATURE_SOURCE_MISSING",
                "현재 runtime에 이 entity의 pinned local source가 없습니다",
            )
    try:
        if descriptor.executorModule is None or descriptor.executorAttribute is None:
            raise ValueError("callable executor 경로가 없습니다")
        module = importlib.import_module(descriptor.executorModule)
        executor = getattr(module, descriptor.executorAttribute)
        if not callable(executor):
            raise TypeError("callable executor가 아닙니다")
        kwargs = dict(task.query.params)
        if descriptor.measureParam:
            if descriptor.measureParam in kwargs:
                raise ValueError(f"{descriptor.measureParam}은 factor projection이 소유합니다")
            kwargs[descriptor.measureParam] = _requestedMeasures(task.query)
        if descriptor.subjectParam:
            kwargs[descriptor.subjectParam] = entity.entityId
        sourceEntityParam = dict(descriptor.metadata).get("sourceEntityParam")
        if entity.sourceEntityId is not None and isinstance(sourceEntityParam, str) and sourceEntityParam:
            kwargs[sourceEntityParam] = entity.sourceEntityId
        entityParams = dict(entity.params)
        for snapshotName, executorKeyword in _entityParamMap(descriptor):
            value = entityParams.get(snapshotName)
            if value is None:
                return _failureEntry(
                    task,
                    ordinal,
                    entity,
                    "FEATURE_ENTITY_METADATA_MISSING",
                    f"universe snapshot parameter가 없습니다: {snapshotName}",
                )
            kwargs[executorKeyword] = value
        if verifiedSource is not None and sourcePayloadParam is not None and sourceIntegrityParam is not None:
            kwargs[sourcePayloadParam] = verifiedSource.payload
            kwargs[sourceIntegrityParam] = verifiedSource.integrityDigest
        if task.query.time is not None:
            if task.query.time.validAt is not None and descriptor.validTimeParam:
                kwargs[descriptor.validTimeParam] = task.query.time.validAt
            if task.query.time.knownAt is not None and descriptor.knowledgeTimeParam:
                kwargs[descriptor.knowledgeTimeParam] = task.query.time.knownAt
        raw = executor(**kwargs)
    except FileNotFoundError:
        return _failureEntry(
            task,
            ordinal,
            entity,
            "FEATURE_SOURCE_MISSING",
            "현재 runtime에 이 entity의 pinned local source가 없습니다",
        )
    except (TypeError, ValueError):
        return _failureEntry(
            task,
            ordinal,
            entity,
            "FEATURE_ENTITY_UNAVAILABLE",
            "owner가 이 entity의 coherent feature state를 구성하지 못했습니다",
        )
    except Exception as error:
        if getattr(error, "code", None) in {
            "OFFLINE_NETWORK_BLOCKED",
            "PAGEABLE_EAGER_WRITE_BLOCKED",
        }:
            raise
        return _failureEntry(
            task,
            ordinal,
            entity,
            "FEATURE_ENTITY_EXECUTION_FAILED",
            "owner feature 실행이 실패했습니다",
        )
    try:
        requestRef = _requestRef(task, entity.entityId)
        partition, gaps = projectOutput(
            raw,
            descriptor,
            task.query,
            selector={"subject": entity.entityId},
            receiptRef=requestRef,
            requestId=task.requestId,
        )
    except Exception as error:
        if getattr(error, "code", None) in {
            "OFFLINE_NETWORK_BLOCKED",
            "PAGEABLE_EAGER_WRITE_BLOCKED",
        }:
            raise
        return _failureEntry(
            task,
            ordinal,
            entity,
            "FEATURE_PROJECTION_FAILED",
            "owner feature 결과가 공통 factor 계약을 통과하지 못했습니다",
        )
    if (
        partition is None
        or partition.truncated
        or not isinstance(partition.data, pl.DataFrame)
        or partition.data.is_empty()
        or partition.contentHash is None
        or partition.lineage is None
    ):
        codes = tuple(gap.code for gap in gaps) or ("FEATURE_ENTITY_EMPTY",)
        messages = tuple(gap.message for gap in gaps) or ("owner가 bounded factor row를 반환하지 않았습니다",)
        return _OwnerEntry(
            requestId=task.requestId,
            assetId=descriptor.assetId,
            assetVersionId=descriptor.assetVersionId,
            sourcePin=task.sourcePin,
            queryPin=task.queryPin,
            entityOrdinal=ordinal,
            entityId=entity.entityId,
            sourceEntityId=entity.sourceEntityId,
            status="failed",
            gapCodes=codes[:64],
            gapMessages=messages[:64],
        )
    payload = _framePayload(partition.data)
    return _OwnerEntry(
        requestId=task.requestId,
        assetId=descriptor.assetId,
        assetVersionId=descriptor.assetVersionId,
        sourcePin=task.sourcePin,
        queryPin=task.queryPin,
        entityOrdinal=ordinal,
        entityId=entity.entityId,
        sourceEntityId=entity.sourceEntityId,
        status="ok",
        gapCodes=tuple(gap.code for gap in gaps)[:64],
        gapMessages=tuple(gap.message for gap in gaps)[:64],
        receiptRef=partition.lineage.runId,
        contentHash=partition.contentHash,
        temporalStatus=partition.temporalStatus,
        payload=payload,
    )
