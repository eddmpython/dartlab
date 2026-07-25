"""Owner paging universe source와 continuation pin 검증."""

from __future__ import annotations

import hmac
import importlib
from collections.abc import Mapping, Sequence
from typing import Any

from dartlab.data.continuation import (
    ContinuationError,
    ContinuationPins,
    arrowSchemaDigest,
    bytesDigest,
    canonicalDigest,
)
from dartlab.data.ownerPagingEntity import _entityParamMap
from dartlab.data.ownerPagingModels import (
    _FORMAT_VERSION,
    _OUTER_SCHEMA,
    _PAGE_KIND,
    _EntityRef,
    _OwnerSession,
    _OwnerTask,
)
from dartlab.data.ownerPagingState import _requestedMeasures, _sourcePin
from dartlab.data.pagingRuntime import manifestCachePath
from dartlab.data.universe import ResolvedMarket


def _ownerFacade() -> Any:
    """현재 호환 파사드의 monkeypatch seam을 반환한다."""

    import dartlab.data.ownerPaging as facade

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
                    "entityCount": len(task.entities),
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
