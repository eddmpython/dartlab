"""U0 census와 U1 snapshot 위에만 서는 Universe 전용 execution kernel."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from .canonical import CapabilityCensus
from .execution.admission import AdmissionDecision, ExecutionPolicy, ExecutionRequest, admitExecution
from .execution.receipts import ExecutionReceipt, ExecutionStore, ReplayResult, replayExecution
from .execution.registry import UniverseCapabilityRegistry, buildCapabilityRegistry
from .execution.runner import CancelToken, runCapability
from .provenance import UniverseSnapshot


@dataclass(slots=True)
class UniverseKernel:
    snapshot: UniverseSnapshot
    registry: UniverseCapabilityRegistry
    policy: ExecutionPolicy
    executionStore: ExecutionStore

    @classmethod
    def build(
        cls,
        census: CapabilityCensus,
        snapshot: UniverseSnapshot,
        policy: ExecutionPolicy,
    ) -> "UniverseKernel":
        if snapshot.capabilityCatalogDigest != census.digest:
            raise ValueError("snapshot capability digest와 U2 census가 다름")
        registry = buildCapabilityRegistry(census)
        effectivePolicy = replace(policy, expectedSnapshotId=snapshot.snapshotId)
        store = ExecutionStore(Path(effectivePolicy.controlRoot))
        return cls(snapshot=snapshot, registry=registry, policy=effectivePolicy, executionStore=store)

    def admit(self, request: ExecutionRequest) -> AdmissionDecision:
        return admitExecution(request, self.registry, self.policy)

    def run(self, request: ExecutionRequest, cancelToken: CancelToken | None = None) -> ExecutionReceipt:
        decision = self.admit(request)
        return runCapability(decision, cancelToken or CancelToken())

    def replay(self, executionId: str) -> ReplayResult:
        receipt = self.executionStore.loadReceipt(executionId)
        if receipt is None:
            raise KeyError(executionId)
        if receipt.snapshotId != self.snapshot.snapshotId:
            raise ValueError("execution receipt가 현재 kernel snapshot에 속하지 않음")
        return replayExecution(receipt, self.executionStore)
