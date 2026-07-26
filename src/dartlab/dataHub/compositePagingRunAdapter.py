"""Composite lower lane의 검증, 실행, 결과 복원 adapter."""

from __future__ import annotations

import dataclasses
import hmac
import importlib
from collections.abc import Mapping
from types import SimpleNamespace
from typing import Any

from dartlab.dataHub.compositePagingModels import _EAGER_SCHEMA, _LaneAllocation, _LanePage
from dartlab.dataHub.compositePagingPayload import _decodeEagerResult, _encodeEagerResult
from dartlab.dataHub.compositePagingState import (
    _decodePins,
    _decodeQuery,
    _descriptorCodec,
    _isSafeEagerLane,
    _jsonLoad,
    _packLowerSession,
    _pinsTree,
    _requireDigest,
    _requireText,
    _samePins,
    _unpackLowerSession,
)
from dartlab.dataHub.continuation import (
    ContinuationError,
    ContinuationPins,
    ContinuationQueryState,
    arrowSchemaDigest,
    canonicalDigest,
    canonicalJsonBytes,
)
from dartlab.dataHub.contracts import (
    AssetRef,
    Coverage,
    DataAssetDescriptor,
    DataGap,
    DataPartition,
    DataQuery,
    DataResult,
    QueryBudget,
    UniverseCoverage,
)
from dartlab.dataHub.identity.contentSeal import resultSnapshotId
from dartlab.dataHub.pagingRuntime import requireDeadline


class CompositeRunAdapterMixin:
    """Lower lane의 검증과 한 page 실행을 제공한다."""

    def validate(self, lane: Mapping[str, Any], *, deadline: float) -> Any:
        """Lower lane 종류에 맞춰 source와 continuation pin을 검증한다."""
        requireDeadline(deadline)
        kind = lane["laneKind"]
        if kind == "resource":
            return self._validateResource(lane, deadline=deadline)
        if kind == "owner":
            return self._validateOwner(lane, deadline=deadline)
        if kind == "eager":
            return self._validateEager(lane, deadline=deadline)
        raise ContinuationError("CONTINUATION_CORRUPT")

    @staticmethod
    def _lowerState(lane: Mapping[str, Any]) -> tuple[bytes, bytes, ContinuationPins]:
        private = lane["privateState"]
        if not isinstance(private, dict):
            raise ContinuationError("CONTINUATION_CORRUPT")
        if set(private) == {"query", "session", "pins"}:
            sessionPayload = canonicalJsonBytes(private["session"])
        elif set(private) == {"query", "packedSession", "pins"}:
            sessionPayload = _unpackLowerSession(private["packedSession"])
        else:
            raise ContinuationError("CONTINUATION_CORRUPT")
        queryPayload = canonicalJsonBytes(private["query"])
        return queryPayload, sessionPayload, _decodePins(private["pins"])

    @classmethod
    def _validateResource(cls, lane: Mapping[str, Any], *, deadline: float) -> Any:
        module = importlib.import_module("dartlab.dataHub.resourcePaging")
        queryPayload, sessionPayload, expectedPins = cls._lowerState(lane)
        module._validateQueryPayload(queryPayload)
        session = module._decodeSession(sessionPayload)
        boundary = module._ownerBoundary()
        sourcePins, preparedReads = module._currentSourcePins(boundary, session, deadline=deadline)
        currentPins = module._pins(session, queryPayload, sourcePins)
        _samePins(expectedPins, currentPins)
        if not hmac.compare_digest(lane["sourceDigest"], currentPins.sourceDigest):
            raise ContinuationError("CONTINUATION_SOURCE_STALE")
        if not hmac.compare_digest(lane["contractDigest"], currentPins.contractDigest):
            raise ContinuationError("CONTINUATION_CONTRACT_STALE")
        return boundary, preparedReads

    @classmethod
    def _validateOwner(cls, lane: Mapping[str, Any], *, deadline: float) -> Any:
        module = importlib.import_module("dartlab.dataHub.ownerPaging")
        queryPayload, sessionPayload, expectedPins = cls._lowerState(lane)
        module._validateQueryPayload(queryPayload)
        session = module._decodeSession(sessionPayload)
        module._requireTaskContracts(session, deadline=deadline)
        sourcePins = module._requireTaskSources(session, deadline=deadline)
        currentPins = module._pins(session, queryPayload, sourcePins)
        _samePins(expectedPins, currentPins)
        if not hmac.compare_digest(lane["sourceDigest"], currentPins.sourceDigest):
            raise ContinuationError("CONTINUATION_SOURCE_STALE")
        if not hmac.compare_digest(lane["contractDigest"], currentPins.contractDigest):
            raise ContinuationError("CONTINUATION_CONTRACT_STALE")
        return None

    @staticmethod
    def _eagerState(lane: Mapping[str, Any]) -> tuple[DataAssetDescriptor, DataQuery, dict[str, Any]]:
        private = lane["privateState"]
        expected = {
            "descriptor",
            "query",
            "selectors",
            "cursor",
            "snapshotId",
            "contractHash",
            "universeSnapshotId",
            "codePin",
            "eagerMode",
            "sealed",
        }
        if not isinstance(private, dict) or set(private) != expected:
            raise ContinuationError("CONTINUATION_CORRUPT")
        _descriptorTree, decodeDescriptor, _ownerQueryTree, _ownerDecodeQuery, _ownerCodePin = _descriptorCodec()
        descriptor = decodeDescriptor(private["descriptor"])
        query = _decodeQuery(private["query"])
        selectors = private["selectors"]
        cursor = private["cursor"]
        if (
            not isinstance(selectors, list)
            or not selectors
            or any(
                not isinstance(selector, dict)
                or any(type(key) is not str or type(value) is not str for key, value in selector.items())
                for selector in selectors
            )
            or type(cursor) is not int
            or not 0 <= cursor < len(selectors)
            or private["eagerMode"] not in {"locator", "sealed"}
            or (private["eagerMode"] == "locator") != (private["sealed"] is None)
        ):
            raise ContinuationError("CONTINUATION_CORRUPT")
        return descriptor, query, private

    @classmethod
    def _validateEager(cls, lane: Mapping[str, Any], *, deadline: float) -> Any:
        descriptor, query, private = cls._eagerState(lane)
        if private["eagerMode"] == "sealed":
            eagerProcess = importlib.import_module("dartlab.dataHub.isolation.eagerProcess")
            seal = eagerProcess.validateEagerSeal(
                private["sealed"],
                selectors=private["selectors"],
                descriptor=descriptor,
                requestId=lane["requestId"],
                snapshotId=_requireText(private["snapshotId"]),
                contractHash=_requireDigest(private["contractHash"]),
            )
            requireDeadline(deadline)
            currentSource = canonicalDigest(
                {
                    "format": "composite-eager-content-v1",
                    "assetId": descriptor.assetId,
                    "assetVersionId": descriptor.assetVersionId,
                    "bundleDigest": seal.payloadDigest,
                    "universeSnapshotId": private["universeSnapshotId"],
                }
            )
            if not hmac.compare_digest(currentSource, lane["sourceDigest"]):
                raise ContinuationError("CONTINUATION_SOURCE_STALE")
            return seal
        if not _isSafeEagerLane(descriptor, query):
            raise ContinuationError("CONTINUATION_CONTRACT_STALE")
        catalog = importlib.import_module("dartlab.dataHub.execution").buildCatalog()
        requireDeadline(deadline)
        if catalog.status != "ok":
            raise ContinuationError("CONTINUATION_CONTRACT_STALE")
        current = {item.assetId: item for item in catalog.assets}.get(descriptor.assetId)
        descriptorTree, _decodeDescriptor, _queryTree, _decodeQuery, ownerCodePin = _descriptorCodec()
        if current is None or canonicalJsonBytes(descriptorTree(current)) != canonicalJsonBytes(
            descriptorTree(descriptor)
        ):
            raise ContinuationError("CONTINUATION_CONTRACT_STALE")
        currentCodePin = (
            ownerCodePin(current)
            if current.executorKind == "callable"
            else canonicalDigest({"descriptor": descriptorTree(current)})
        )
        if not hmac.compare_digest(currentCodePin, _requireDigest(private["codePin"])):
            raise ContinuationError("CONTINUATION_CONTRACT_STALE")
        if query.universe is not None:
            universe = importlib.import_module("dartlab.dataHub.catalog.universe").resolveUniverse(query.universe)
            requireDeadline(deadline)
            if universe.gaps or universe.snapshotId != private["universeSnapshotId"]:
                raise ContinuationError("CONTINUATION_SOURCE_STALE")
        currentSource = canonicalDigest(
            {
                "assetId": current.assetId,
                "assetVersionId": current.assetVersionId,
                "sourceRef": current.sourceRef,
                "universeSnapshotId": private["universeSnapshotId"],
            }
        )
        if not hmac.compare_digest(currentSource, lane["sourceDigest"]):
            raise ContinuationError("CONTINUATION_SOURCE_STALE")
        return None

    def materialize(
        self,
        lane: Mapping[str, Any],
        allocation: _LaneAllocation,
        *,
        deadline: float,
        validation: Any,
    ) -> _LanePage:
        """Lower lane에 배정된 예산으로 한정된 page를 실행한다."""
        requireDeadline(deadline)
        kind = lane["laneKind"]
        if kind == "resource":
            return self._materializeResource(lane, allocation, deadline=deadline, validation=validation)
        if kind == "owner":
            return self._materializeOwner(lane, allocation, deadline=deadline)
        if kind == "eager":
            return self._materializeEager(lane, allocation, deadline=deadline)
        raise ContinuationError("CONTINUATION_CORRUPT")

    @classmethod
    def _materializeResource(
        cls,
        lane: Mapping[str, Any],
        allocation: _LaneAllocation,
        *,
        deadline: float,
        validation: Any,
    ) -> _LanePage:
        module = importlib.import_module("dartlab.dataHub.resourcePaging")
        queryPayload, sessionPayload, expectedPins = cls._lowerState(lane)
        session = module._decodeSession(sessionPayload)
        session = dataclasses.replace(
            session,
            pageMaxRows=allocation.maxRows,
            pageMaxBytes=allocation.maxBytes,
            pageMaxLogicalBytes=allocation.maxBytes,
        )
        boundary, preparedReads = validation
        envelope = module._materialize(
            ContinuationQueryState(queryPayload, module._encodeSession(session)),
            boundary,
            deadline=deadline,
            preparedReads=preparedReads,
        )
        nextPrivate = None
        if envelope.nextState is not None:
            nextPrivate = {
                "query": _jsonLoad(envelope.nextState.queryPayload),
                "session": _jsonLoad(envelope.nextState.cursorPayload),
                "pins": _pinsTree(expectedPins),
            }
        return _LanePage(
            payload=envelope.payload,
            claimedRows=envelope.rowCount,
            schemaDigest=expectedPins.schemaDigest,
            nextPrivateState=nextPrivate,
            attempted=envelope.rowCount,
            succeededRows=envelope.rowCount,
            succeededPartitions=1 if envelope.rowCount else 0,
            failedItems=0,
            gapCodes=(),
            done=nextPrivate is None,
        )

    @classmethod
    def _materializeOwner(
        cls,
        lane: Mapping[str, Any],
        allocation: _LaneAllocation,
        *,
        deadline: float,
    ) -> _LanePage:
        module = importlib.import_module("dartlab.dataHub.ownerPaging")
        queryPayload, sessionPayload, expectedPins = cls._lowerState(lane)
        session = module._decodeSession(sessionPayload)
        session = dataclasses.replace(
            session,
            pageMaxRows=allocation.maxRows,
            pageMaxBytes=allocation.maxBytes,
            pageMaxLogicalBytes=allocation.maxBytes,
            pageMaxEntities=min(session.pageMaxEntities, allocation.maxRows),
            maxConcurrency=allocation.maxConcurrency,
        )
        envelope = module._materialize(
            ContinuationQueryState(queryPayload, module._encodeSession(session)),
            deadline=deadline,
            sourcesPrevalidated=True,
        )
        decoded = module._decodePage(
            envelope.payload,
            claimedRowCount=envelope.rowCount,
            maxPageRows=session.pageMaxRows,
            maxPageBytes=session.pageMaxBytes,
            maxLogicalBytes=session.pageMaxLogicalBytes,
        )
        succeededRows = sum(
            table.num_rows
            for entry, table in zip(decoded.entries, decoded.tables, strict=True)
            if entry.status == "ok" and table is not None
        )
        gapCodes = tuple(code for entry in decoded.entries for code in entry.gapCodes)
        failedItems = sum(entry.status == "failed" for entry in decoded.entries)
        nextPrivate = None
        if envelope.nextState is not None:
            nextPrivate = {
                "query": _jsonLoad(envelope.nextState.queryPayload),
                "packedSession": _packLowerSession(envelope.nextState.cursorPayload),
                "pins": _pinsTree(expectedPins),
            }
        return _LanePage(
            payload=envelope.payload,
            claimedRows=envelope.rowCount,
            schemaDigest=expectedPins.schemaDigest,
            nextPrivateState=nextPrivate,
            attempted=len(decoded.entries),
            succeededRows=succeededRows,
            succeededPartitions=sum(entry.status == "ok" for entry in decoded.entries),
            failedItems=failedItems,
            gapCodes=gapCodes,
            done=nextPrivate is None,
        )

    @classmethod
    def _materializeEager(
        cls,
        lane: Mapping[str, Any],
        allocation: _LaneAllocation,
        *,
        deadline: float,
    ) -> _LanePage:
        descriptor, query, private = cls._eagerState(lane)
        if private["eagerMode"] == "sealed":
            cursor = int(private["cursor"])
            payload = importlib.import_module("dartlab.dataHub.isolation.eagerProcess").eagerResultAt(
                private["sealed"],
                selectors=private["selectors"],
                index=cursor,
            )
            if len(payload) > allocation.maxBytes:
                raise ContinuationError("PAGEABLE_EAGER_SEAL_RESULT_BUDGET")
            result = _decodeEagerResult(payload)
            succeededRows = sum(partition.rowCount for partition in result.partitions)
            if succeededRows > allocation.maxRows:
                raise ContinuationError("CONTINUATION_ROW_BUDGET")
            nextCursor = cursor + 1
            done = nextCursor >= len(private["selectors"])
            return _LanePage(
                payload=payload,
                claimedRows=1,
                schemaDigest=arrowSchemaDigest(_EAGER_SCHEMA),
                nextPrivateState=None if done else dict(private) | {"cursor": nextCursor},
                attempted=1,
                succeededRows=succeededRows,
                succeededPartitions=len(result.partitions),
                failedItems=len(result.gaps),
                gapCodes=tuple(gap.code for gap in result.gaps),
                done=done,
            )
        execution = importlib.import_module("dartlab.dataHub.execution")
        selector = dict(private["selectors"][private["cursor"]])
        remainingMs = max(1, int(requireDeadline(deadline) * 1000))
        budget = QueryBudget(
            maxRows=allocation.maxRows,
            maxBytes=allocation.maxBytes,
            timeoutMs=min(query.budget.timeoutMs, remainingMs),
            maxAssets=1,
            maxSubjects=query.budget.maxSubjects,
            maxConcurrency=allocation.maxConcurrency,
        )
        activeQuery = dataclasses.replace(query, budget=budget)
        requestRef = execution._requestRef(descriptor, activeQuery, selector, lane["requestId"])
        partitions: tuple[DataPartition, ...] = ()
        gaps: list[DataGap] = []
        universeCoverage: tuple[UniverseCoverage, ...] = ()
        try:
            raw = execution._execute(descriptor, activeQuery, selector)
            requireDeadline(deadline)
            membership = None
            if activeQuery.universe is not None:
                resolved = importlib.import_module("dartlab.dataHub.catalog.universe").resolveUniverse(
                    activeQuery.universe
                )
                membership = resolved.byMarket().get(selector.get("market"))
            task = execution._ExecutionTask(
                lane["requestId"],
                descriptor,
                activeQuery,
                selector,
                requestRef,
                membership,
                private["universeSnapshotId"],
            )
            coverageRow = execution._universeCoverage(task, raw)
            if coverageRow is not None:
                universeCoverage = (coverageRow,)
            partition, projectionGaps = importlib.import_module("dartlab.dataHub.projection.output").projectOutput(
                raw,
                descriptor,
                activeQuery,
                selector=selector,
                receiptRef=requestRef,
                requestId=lane["requestId"],
            )
            gaps.extend(
                dataclasses.replace(gap, requestId=gap.requestId or lane["requestId"]) for gap in projectionGaps
            )
            if partition is not None:
                partitions = (partition,)
                if partition.truncated:
                    gaps.append(
                        DataGap(
                            "CONTINUATION_UNSUPPORTED",
                            "eager owner 결과가 selector 예산에서 잘렸습니다",
                            descriptor.assetId,
                            requestId=lane["requestId"],
                        )
                    )
        except ContinuationError:
            raise
        except Exception:
            gaps.append(
                DataGap(
                    "ASSET_EXECUTION_FAILED",
                    "eager owner 실행이 실패했습니다",
                    descriptor.assetId,
                    requestId=lane["requestId"],
                )
            )
        nextCursor = int(private["cursor"]) + 1
        done = nextCursor >= len(private["selectors"])
        assets = (AssetRef(descriptor.assetId, descriptor.assetVersionId),)
        lineageRefs = tuple(dict.fromkeys(ref for partition in partitions for ref in partition.lineageRefs))
        receipts = tuple(
            dict.fromkeys(partition.lineage.runId for partition in partitions if partition.lineage is not None)
        )
        result = DataResult(
            status="failed" if not partitions and gaps else "partial" if gaps else "ok",
            partitions=partitions,
            assets=assets,
            snapshotId=_requireText(private["snapshotId"]),
            contractHash=_requireDigest(private["contractHash"]),
            coverage=Coverage(1, 1, len(partitions), len(gaps)),
            gaps=tuple(gaps),
            lineageRefs=lineageRefs,
            executionReceipts=receipts,
            continuation=None,
            qualityAssertions=tuple(assertion for partition in partitions for assertion in partition.qualityAssertions),
            universeSnapshotId=private["universeSnapshotId"],
            universeCoverage=universeCoverage,
            dataSnapshotId=resultSnapshotId(
                catalogSnapshotId=private["snapshotId"],
                contractHash=private["contractHash"],
                partitions=partitions,
                universeSnapshotId=private["universeSnapshotId"],
            ),
        )
        payload = _encodeEagerResult(result, maxBytes=allocation.maxBytes)
        nextPrivate = None if done else dict(private) | {"cursor": nextCursor}
        return _LanePage(
            payload=payload,
            claimedRows=1,
            schemaDigest=arrowSchemaDigest(_EAGER_SCHEMA),
            nextPrivateState=nextPrivate,
            attempted=1,
            succeededRows=sum(partition.rowCount for partition in partitions),
            succeededPartitions=len(partitions),
            failedItems=len(gaps),
            gapCodes=tuple(gap.code for gap in gaps),
            done=done,
        )

    def result(
        self,
        lane: Mapping[str, Any],
        row: Mapping[str, Any],
        *,
        pageRef: str,
    ) -> DataResult:
        """Lower lane의 저장 행을 원래 공개 결과 계약으로 복원한다."""
        kind = lane["laneKind"]
        if kind == "eager":
            return _decodeEagerResult(row["childPayload"])
        queryPayload, sessionPayload, _pins = self._lowerState(lane)
        del queryPayload
        moduleName = "dartlab.dataHub.resourcePaging" if kind == "resource" else "dartlab.dataHub.ownerPaging"
        module = importlib.import_module(moduleName)
        session = module._decodeSession(sessionPayload)
        if kind == "resource":
            session = dataclasses.replace(
                session,
                pageMaxRows=row["childMaxRows"],
                pageMaxBytes=row["childMaxBytes"],
                pageMaxLogicalBytes=row["childMaxBytes"],
            )
        else:
            session = dataclasses.replace(
                session,
                pageMaxRows=row["childMaxRows"],
                pageMaxBytes=row["childMaxBytes"],
                pageMaxLogicalBytes=row["childMaxBytes"],
                pageMaxEntities=min(session.pageMaxEntities, row["childMaxRows"]),
                maxConcurrency=row["childMaxConcurrency"],
            )
        page = SimpleNamespace(
            payload=row["childPayload"],
            rowCount=row["childClaimedRows"],
            pageRef=pageRef,
            nextToken=None if row["done"] else "composite-private-progress",
        )
        return dataclasses.replace(module._resultFromPage(session, page), continuation=None)
