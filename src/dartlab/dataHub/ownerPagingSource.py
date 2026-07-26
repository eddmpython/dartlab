"""Owner paging universe source와 continuation pin 검증."""

from __future__ import annotations

import dataclasses
import hmac
import importlib
from collections.abc import Mapping, Sequence
from typing import Any

from dartlab.dataHub.continuation import (
    ContinuationError,
    ContinuationPins,
    arrowSchemaDigest,
    bytesDigest,
    canonicalDigest,
)
from dartlab.dataHub.ownerPagingEntity import _entityParamMap
from dartlab.dataHub.ownerPagingModels import (
    _FORMAT_VERSION,
    _OUTER_SCHEMA,
    _PAGE_KIND,
    _EntityRef,
    _OwnerSession,
    _OwnerTask,
)
from dartlab.dataHub.ownerPagingState import _requestedMeasures, _sourcePin
from dartlab.dataHub.pagingRuntime import manifestCachePath
from dartlab.dataHub.universe import ResolvedMarket


def _ownerFacade() -> Any:
    """현재 호환 파사드의 monkeypatch seam을 반환한다."""

    import dartlab.dataHub.ownerPaging as facade

    return facade


def _resourceSourcePin(assetId: str, category: str) -> str:
    module = importlib.import_module("dartlab.providers.resourceStream.workbench")
    describe = getattr(module, "describeResource")
    description = describe(assetId, category, manifestCachePath(assetId, category))
    if getattr(description, "resourceId", None) != assetId or getattr(description, "category", None) != category:
        raise ValueError("owner paging source identity가 다릅니다")
    sourcePin = getattr(description, "sourcePin", None)
    if not isinstance(sourcePin, str) or not sourcePin.startswith("resource-source-full:"):
        raise ValueError("owner paging source pin이 full identity가 아닙니다")
    return sourcePin


def _entities(
    membership: ResolvedMarket,
    parameterNames: Sequence[str] = (),
) -> tuple[_EntityRef, ...]:
    byEntity = membership.sourceIdByEntity()
    paramsByEntity = membership.paramsByEntity()
    return tuple(
        _EntityRef(
            entityId,
            byEntity.get(entityId),
            tuple((name, value) for name, value in paramsByEntity.get(entityId, ()) if name in parameterNames),
        )
        for entityId in membership.entityIds
    )


def _hydrateTask(task: _OwnerTask) -> _OwnerTask:
    """Universe 를 재해소해 비어 있는 엔티티 목록을 채운다.

    Args:
        task: durable state 에서 복원한 owner task.

    Returns:
        엔티티가 채워진 task. 이미 채워져 있으면 그대로 반환한다.

    Raises:
        ContinuationError: universe snapshot, provider, membership, 엔티티 수가
            발급 시점과 다를 때 `CONTINUATION_SOURCE_STALE`.

    Example:
        ``task = _hydrateTask(task)``.

    Guide:
        엔티티 목록은 durable state 에 담지 않는다. 담으면 엔티티 수에 비례해 state 가
        커져 두 시장 혼합 등록이 예산을 넘긴다.

    When:
        `_decodeSession` 이 복원 직후 한 번만 호출한다. 소비처는 항상 채워진 세션을 본다.

    How:
        같은 selection 으로 universe 를 다시 해소하고 `_entities` 로 목록을 재구성한다.

    See Also:
        ``_entities`` 와 ``_currentTaskSourcePin``.

    Requires:
        도출 동일성은 membershipDigest, descriptor, ownerCodePin 세 pin 이 보장한다.

    AI Context:
        local-only universe snapshot 만 읽고 원천 provider 는 접촉하지 않는다.
    """

    if task.entities:
        return task
    resolved = _ownerFacade().resolveUniverse(task.selection)
    if resolved.gaps or resolved.snapshotId != task.universeSnapshotId:
        raise ContinuationError("CONTINUATION_SOURCE_STALE")
    membership = resolved.byMarket().get(task.market)
    if (
        membership is None
        or membership.provider != task.provider
        or membership.membershipDigest != task.membershipDigest
    ):
        raise ContinuationError("CONTINUATION_SOURCE_STALE")
    entities = _entities(
        membership,
        tuple(source for source, _target in _entityParamMap(task.descriptor)),
    )
    if len(entities) != task.entityCount:
        raise ContinuationError("CONTINUATION_SOURCE_STALE")
    return dataclasses.replace(task, entities=entities)


def _currentTaskSourcePin(task: _OwnerTask) -> str:
    resolved = _ownerFacade().resolveUniverse(task.selection)
    if resolved.gaps or resolved.snapshotId != task.universeSnapshotId:
        raise ContinuationError("CONTINUATION_SOURCE_STALE")
    membership = resolved.byMarket().get(task.market)
    expectedEntities = (
        ()
        if membership is None
        else _entities(
            membership,
            tuple(source for source, _target in _entityParamMap(task.descriptor)),
        )
    )
    if (
        membership is None
        or membership.provider != task.provider
        or membership.membershipDigest != task.membershipDigest
        or expectedEntities != task.entities
    ):
        raise ContinuationError("CONTINUATION_SOURCE_STALE")
    return _sourcePin(
        task.ownerSourcePin,
        membership.membershipDigest,
        _requestedMeasures(task.query),
    )


def _contractDigest(session: _OwnerSession) -> str:
    return canonicalDigest(
        {
            "format": _PAGE_KIND,
            "version": _FORMAT_VERSION,
            "contractHash": session.contractHash,
            "tasks": [
                {
                    "requestId": task.requestId,
                    "assetId": task.descriptor.assetId,
                    "assetVersionId": task.descriptor.assetVersionId,
                    "ownerCodePin": task.ownerCodePin,
                    "queryPin": task.queryPin,
                    "membershipDigest": task.membershipDigest,
                    "sourceAssetId": task.sourceAssetId,
                    "sourceCategory": task.sourceCategory,
                    "entityCount": task.entityCount,
                }
                for task in session.tasks
            ],
        }
    )


def _pins(
    session: _OwnerSession,
    queryPayload: bytes,
    sourcePins: Mapping[str, str],
) -> ContinuationPins:
    return ContinuationPins(
        sourceDigest=canonicalDigest(dict(sourcePins)),
        queryDigest=bytesDigest(queryPayload),
        contractDigest=_contractDigest(session),
        schemaDigest=arrowSchemaDigest(_OUTER_SCHEMA),
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
