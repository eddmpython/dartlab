"""Composite lower lane의 immutable 계획 adapter."""

from __future__ import annotations

import importlib
from collections.abc import Mapping
from typing import Any

from dartlab.dataHub.continuation import ContinuationError, arrowSchemaDigest, canonicalDigest
from dartlab.dataHub.contracts import DataAssetDescriptor, DataQuery, ResourceProjection
from dartlab.dataHub.paging.composite.models import (
    _CONTROL_BASE_BYTES,
    _CONTROL_PER_LANE_BYTES,
    _EAGER_SCHEMA,
)
from dartlab.dataHub.paging.composite.state import (
    _descriptorCodec,
    _isSafeEagerLane,
    _jsonLoad,
    _packLowerSession,
    _pinsTree,
    _queryTree,
    _strictTree,
)
from dartlab.dataHub.paging.runtime import MAX_PAGE_BYTES, MAX_PAGE_ROWS, requireDeadline


class CompositePlanAdapterMixin:
    """Lower owner 내부 계약을 child token 없이 outer scheduler에 연결한다."""

    def plan(
        self,
        requestId: str,
        requestIndex: int,
        descriptor: DataAssetDescriptor,
        query: DataQuery,
        *,
        snapshotId: str,
        contractHash: str,
        deadline: float,
    ) -> Mapping[str, Any]:
        """요청 종류에 맞는 resource, owner, eager lane 계획을 만든다."""
        requireDeadline(deadline)
        resource = importlib.import_module("dartlab.dataHub.paging.resource")
        owner = importlib.import_module("dartlab.dataHub.paging.owner")
        if resource.isPageableResource(descriptor, query):
            return self._planResource(
                requestId,
                descriptor,
                query,
                snapshotId=snapshotId,
                contractHash=contractHash,
            )
        if owner.isPageableOwner(descriptor, query):
            return self._planOwner(
                requestId,
                descriptor,
                query,
                snapshotId=snapshotId,
                contractHash=contractHash,
            )
        return self._planEager(
            requestId,
            descriptor,
            query,
            snapshotId=snapshotId,
            contractHash=contractHash,
            deadline=deadline,
        )

    @staticmethod
    def _planResource(
        requestId: str,
        descriptor: DataAssetDescriptor,
        query: DataQuery,
        *,
        snapshotId: str,
        contractHash: str,
    ) -> Mapping[str, Any]:
        module = importlib.import_module("dartlab.dataHub.paging.resource")
        boundary = module._ownerBoundary()
        task = module._descriptionTask(boundary, requestId, descriptor, query)
        session = module._ResourceSession(
            snapshotId=snapshotId,
            contractHash=contractHash,
            requestedAssets=1,
            pageMaxRows=min(query.budget.maxRows, MAX_PAGE_ROWS),
            pageMaxBytes=min(query.budget.maxBytes, MAX_PAGE_BYTES),
            pageMaxLogicalBytes=min(query.budget.maxBytes, MAX_PAGE_BYTES),
            pageMaxShards=module._MAX_PAGE_SHARDS,
            pageTimeoutMs=query.budget.timeoutMs,
            tasks=(task,),
        )
        queryPayload = module._queryPayload((descriptor.assetId,), query)
        pins = module._pins(session, queryPayload, {requestId: task.sourcePin})
        return {
            "laneKind": "resource",
            "privateState": {
                "query": _jsonLoad(queryPayload),
                "session": _jsonLoad(module._encodeSession(session)),
                "pins": _pinsTree(pins),
            },
            "sourceDigest": pins.sourceDigest,
            "contractDigest": pins.contractDigest,
            "schemaDigest": pins.schemaDigest,
        }

    @staticmethod
    def _planOwner(
        requestId: str,
        descriptor: DataAssetDescriptor,
        query: DataQuery,
        *,
        snapshotId: str,
        contractHash: str,
    ) -> Mapping[str, Any]:
        module = importlib.import_module("dartlab.dataHub.paging.owner")
        task = module._plannedTask(requestId, descriptor, query)
        declaredCap = dict(descriptor.metadata).get("pageMaxEntities", 8)
        if type(declaredCap) is not int or declaredCap <= 0:
            raise ValueError("pageMaxEntities 선언이 유효하지 않습니다")
        session = module._OwnerSession(
            snapshotId=snapshotId,
            contractHash=contractHash,
            requestedAssets=1,
            universeSnapshotId=task.universeSnapshotId,
            pageMaxRows=min(query.budget.maxRows, MAX_PAGE_ROWS),
            pageMaxBytes=min(query.budget.maxBytes, MAX_PAGE_BYTES),
            pageMaxLogicalBytes=min(query.budget.maxBytes, MAX_PAGE_BYTES),
            pageMaxEntities=min(declaredCap, module._MAX_PAGE_ENTITIES),
            pageTimeoutMs=query.budget.timeoutMs,
            maxConcurrency=query.budget.maxConcurrency,
            tasks=(task,),
        )
        queryPayload = module._queryPayload((descriptor.assetId,), query)
        pins = module._pins(session, queryPayload, {requestId: task.sourcePin})
        sessionPayload = module._encodeSession(session)
        return {
            "laneKind": "owner",
            "privateState": {
                "query": _jsonLoad(queryPayload),
                "packedSession": _packLowerSession(sessionPayload),
                "pins": _pinsTree(pins),
            },
            "sourceDigest": pins.sourceDigest,
            "contractDigest": pins.contractDigest,
            "schemaDigest": pins.schemaDigest,
        }

    @staticmethod
    def _planEager(
        requestId: str,
        descriptor: DataAssetDescriptor,
        query: DataQuery,
        *,
        snapshotId: str,
        contractHash: str,
        deadline: float,
    ) -> Mapping[str, Any]:
        requireDeadline(deadline)
        execution = importlib.import_module("dartlab.dataHub.execution")
        descriptorTree, _decodeDescriptor, _ownerQueryTree, _ownerDecodeQuery, _ownerCodePin = _descriptorCodec()
        temporalGap = execution._temporalGap(descriptor, query)
        if temporalGap is not None:
            raise ContinuationError(temporalGap.code)
        selectors, selectorGaps = execution._selectors(descriptor, query)
        if selectorGaps or not selectors:
            raise ContinuationError(selectorGaps[0].code if selectorGaps else "EAGER_SELECTOR_EMPTY")
        universeSnapshotId = None
        if query.universe is not None:
            universe = importlib.import_module("dartlab.dataHub.catalog.universe").resolveUniverse(query.universe)
            requireDeadline(deadline)
            if universe.gaps:
                raise ContinuationError(universe.gaps[0].code)
            universeSnapshotId = universe.snapshotId
        descriptorValue = descriptorTree(descriptor)
        queryValue = _queryTree(query)
        safeLocator = _isSafeEagerLane(descriptor, query)
        sealed = None
        if safeLocator:
            eagerMode = "locator"
            codePin = canonicalDigest({"descriptor": descriptorValue})
            locator = execution._resourceCall(descriptor, query, selectors[0])
            sourcePin = locator.get("sourcePin") if isinstance(locator, Mapping) else None
            if type(sourcePin) is not str or not sourcePin.startswith("resource-source-full:"):
                raise ContinuationError("CONTINUATION_SOURCE_STALE")
            sourceDigest = canonicalDigest(
                {
                    "assetId": descriptor.assetId,
                    "assetVersionId": descriptor.assetVersionId,
                    "sourceRef": descriptor.sourceRef,
                    "sourcePin": sourcePin,
                    "universeSnapshotId": universeSnapshotId,
                }
            )
        else:
            if descriptor.executorKind not in {"callable", "engineAxis"}:
                raise ContinuationError("PAGEABLE_EAGER_EXECUTOR_UNSUPPORTED")
            eagerProcess = importlib.import_module("dartlab.dataHub.isolation.eagerProcess")
            supervisor = importlib.import_module("dartlab.dataHub.isolation.eagerSupervisor")
            codePin = eagerProcess.eagerCodePin(
                descriptor,
                requestedMeasures=execution._requestedMeasures(query),
            )
            availableBytes = query.budget.maxBytes - (_CONTROL_BASE_BYTES + _CONTROL_PER_LANE_BYTES)
            maxBundleBytes = min(eagerProcess._MAX_BUNDLE_BYTES, availableBytes)
            if maxBundleBytes <= eagerProcess._BUNDLE_OVERHEAD_BYTES:
                raise ContinuationError("PAGEABLE_EAGER_SEAL_BUDGET")
            outcome = supervisor.runEagerSeal(
                descriptor,
                query,
                selectors,
                requestId=requestId,
                snapshotId=snapshotId,
                contractHash=contractHash,
                universeSnapshotId=universeSnapshotId,
                publicDeadline=deadline,
                codePin=codePin,
                maxBundleBytes=maxBundleBytes,
            )
            if outcome.status != "ok" or outcome.seal is None or not outcome.zeroLive:
                raise ContinuationError(outcome.errorCode or "PAGEABLE_EAGER_PROCESS_FAILED")
            eagerMode = "sealed"
            sealed = eagerProcess.packEagerSeal(outcome.seal)
            sourceDigest = canonicalDigest(
                {
                    "format": "composite-eager-content-v1",
                    "assetId": descriptor.assetId,
                    "assetVersionId": descriptor.assetVersionId,
                    "bundleDigest": outcome.seal.payloadDigest,
                    "universeSnapshotId": universeSnapshotId,
                }
            )
        contractDigest = canonicalDigest(
            {
                "format": "composite-eager-v2",
                "contractHash": contractHash,
                "descriptor": descriptorValue,
                "query": queryValue,
                "codePin": codePin,
                "eagerMode": eagerMode,
                "selectors": selectors,
            }
        )
        return {
            "laneKind": "eager",
            "privateState": {
                "descriptor": descriptorValue,
                "query": queryValue,
                "selectors": [_strictTree(selector) for selector in selectors],
                "cursor": 0,
                "snapshotId": snapshotId,
                "contractHash": contractHash,
                "universeSnapshotId": universeSnapshotId,
                "codePin": codePin,
                "eagerMode": eagerMode,
                "sealed": sealed,
            },
            "sourceDigest": sourceDigest,
            "contractDigest": contractDigest,
            "schemaDigest": arrowSchemaDigest(_EAGER_SCHEMA),
        }
