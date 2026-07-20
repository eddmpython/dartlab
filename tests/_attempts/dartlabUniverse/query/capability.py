"""명시적 U4 capability request를 U2 admission과 격리 runner로 실행한다."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from ..canonical import canonicalDigest
from ..catalog.models import CatalogState
from ..catalog.snapshot import CatalogSnapshot
from ..execution.admission import (
    ExecutionBudget,
    ExecutionPolicy,
    ExecutionRequest,
    admitExecution,
)
from ..execution.receipts import ExecutionReceipt, ExecutionStore, replayExecution
from ..execution.registry import UniverseCapabilityRegistry
from ..execution.runner import CancelToken, runCapability
from ..ids import logicalId
from .models import CapabilityRequest, UniverseQuery, capabilityArgs


@dataclass(frozen=True, slots=True)
class CapabilityExecutionResult:
    executionRef: str
    status: str
    capabilityId: str
    outputRefs: tuple[str, ...]
    receiptDigest: str


class QueryCapabilityExecutor(Protocol):
    def execute(
        self,
        query: UniverseQuery,
        snapshot: CatalogSnapshot,
        request: CapabilityRequest,
    ) -> CapabilityExecutionResult: ...


class CapabilityExecutionAdapter:
    """Query text가 아닌 exact capability ID와 schema-closed args만 실행한다."""

    def __init__(
        self,
        catalog: CatalogState,
        registry: UniverseCapabilityRegistry,
        *,
        controlRoot: Path,
        protectedPaths: tuple[Path, ...],
        allowedRuntimeBoundaries: tuple[str, ...] = ("LOCAL_PYTHON",),
        allowedExecutorPrefixes: tuple[str, ...] = ("dartlab",),
    ) -> None:
        self.catalog = catalog
        self.registry = registry
        self.controlRoot = controlRoot.resolve()
        self.protectedPaths = tuple(item.resolve() for item in protectedPaths)
        self.allowedRuntimeBoundaries = allowedRuntimeBoundaries
        self.allowedExecutorPrefixes = allowedExecutorPrefixes
        self._receiptById: dict[str, ExecutionReceipt] = {}

    def execute(
        self,
        query: UniverseQuery,
        snapshot: CatalogSnapshot,
        request: CapabilityRequest,
    ) -> CapabilityExecutionResult:
        resourceByVersion = {item.resourceVersionId: item for item in self.catalog.resources}
        visibleObjects = {
            item.objectId
            for item in self.catalog.objects
            if item.visibility in query.allowedVisibility
            and all(
                resourceRef in resourceByVersion
                and resourceByVersion[resourceRef].visibility in query.allowedVisibility
                for resourceRef in item.resourceRefs
            )
        }
        if not set(request.targetRefs).issubset(visibleObjects):
            raise ValueError("capability target이 query visibility 밖이거나 catalog object가 아님")
        capability = self.registry.get(request.capabilityId)
        visibilityScope = capability.visibility if capability is not None else query.allowedVisibility[0].value
        budget = ExecutionBudget(maxWallMs=120_000, maxRetries=1)
        requestId = logicalId(
            "execution-request",
            (query.queryId, request.capabilityId, request.targetRefs, request.args, request.seed),
        )
        executionRequest = ExecutionRequest(
            requestId=requestId,
            capabilityId=request.capabilityId,
            snapshotId=snapshot.universeSnapshotId,
            targetRefs=request.targetRefs,
            args=capabilityArgs(request),
            assumptionRefs=request.assumptionRefs,
            visibilityScope=visibilityScope,
            budget=budget,
            priority=5,
            deadline=None,
            idempotencyKey=None,
            requestedBy="dartlab-universe-query",
            seed=request.seed,
        )
        policy = ExecutionPolicy(
            controlRoot=self.controlRoot.as_posix(),
            expectedSnapshotId=snapshot.universeSnapshotId,
            allowedRuntimeBoundaries=self.allowedRuntimeBoundaries,
            allowedVisibilityScopes=tuple(item.value for item in query.allowedVisibility),
            allowedExecutorPrefixes=self.allowedExecutorPrefixes,
            protectedPaths=tuple(item.as_posix() for item in self.protectedPaths),
        )
        decision = admitExecution(executionRequest, self.registry, policy)
        receipt = runCapability(decision, CancelToken())
        self._receiptById[receipt.executionId] = receipt
        return CapabilityExecutionResult(
            executionRef=receipt.executionId,
            status=receipt.status,
            capabilityId=request.capabilityId,
            outputRefs=receipt.outputRefs,
            receiptDigest=canonicalDigest(receipt),
        )

    def verifyExecutionRef(self, executionRef: str) -> bool:
        receipt = self._receiptById.get(executionRef)
        if receipt is None:
            return False
        store = ExecutionStore(self.controlRoot)
        stored = store.loadReceipt(executionRef)
        if stored != receipt:
            return False
        replay = replayExecution(receipt, store)
        return replay.valid and replay.receipt == receipt
