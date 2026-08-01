from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from dartlab.dataHub.contracts import Coverage, DataGap, DataResult
from dartlab.dataHub.controlPlane import DataHubControlError
from dartlab.dataHub.controlPlane.ledger import DataHubJobLedger
from dartlab.dataHub.controlPlane.resultContract import buildExpectedResultContract
from dartlab.dataHub.entry import _dataQuery
from dartlab.dataHub.transport import encodeDataResult

pytestmark = pytest.mark.unit


class FakeClock:
    def __init__(self, value: float = 100.0):
        self.value = value

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


def _failedResult(query) -> DataResult:
    parsed = _dataQuery(query)
    assert parsed is not None
    expected = buildExpectedResultContract(parsed)
    return DataResult(
        status="failed",
        partitions=(),
        assets=expected.assets,
        snapshotId=expected.catalogSnapshotId,
        contractHash=expected.contractHash,
        coverage=Coverage(expected.requestedAssets, expected.resolvedAssets, 0, 1),
        gaps=(DataGap("FIXTURE_NO_DATA", "fixture"),),
        lineageRefs=(),
        executionReceipts=(),
    )


def testSubmitIsIdempotentAndDefaultsToDurableRefresh(tmp_path: Path) -> None:
    ledger = DataHubJobLedger(tmp_path / "control")
    query = {"requests": [{"assetId": "resource.finance"}]}

    first = ledger.submit(query, idempotencyKey="same-request")
    repeated = ledger.submit(query, idempotencyKey="same-request")
    lease = ledger.claim("worker-a")

    assert repeated == first
    assert lease is not None
    assert lease.job.jobId == first.jobId
    assert lease.request["materialization"] == {"mode": "refresh", "receipt": None}
    with pytest.raises(DataHubControlError) as conflict:
        ledger.submit(
            {"requests": [{"assetId": "resource.edgar"}]},
            idempotencyKey="same-request",
        )
    assert conflict.value.code == "DATA_HUB_CONFLICT"


def testConcurrentWorkersClaimJobExactlyOnce(tmp_path: Path) -> None:
    ledger = DataHubJobLedger(tmp_path / "control")
    ledger.submit({"requests": [{"assetId": "resource.finance"}]})
    barrier = threading.Barrier(8)

    def claim(index: int):
        barrier.wait()
        return ledger.claim(f"worker-{index}")

    with ThreadPoolExecutor(max_workers=8) as executor:
        leases = tuple(executor.map(claim, range(8)))

    claimed = tuple(lease for lease in leases if lease is not None)
    assert len(claimed) == 1
    assert claimed[0].job.attemptCount == 1


def testExpiredLeaseRequeuesThenExhaustsAttempts(tmp_path: Path) -> None:
    clock = FakeClock()
    ledger = DataHubJobLedger(tmp_path / "control", clock=clock)
    job = ledger.submit(
        {"requests": [{"assetId": "resource.finance"}]},
        maxAttempts=2,
    )
    first = ledger.claim("worker-a", leaseSeconds=10)
    assert first is not None

    clock.advance(11)
    second = ledger.claim("worker-b", leaseSeconds=10)
    assert second is not None
    assert second.job.jobId == job.jobId
    assert second.job.attemptCount == 2

    clock.advance(11)
    assert ledger.claim("worker-c") is None
    terminal = ledger.get(job.jobId)
    assert terminal.state == "failed"
    assert terminal.errorCode == "DATA_HUB_ATTEMPTS_EXHAUSTED"


def testCompleteReadCancelAndBoundedMaintenance(tmp_path: Path) -> None:
    clock = FakeClock()
    ledger = DataHubJobLedger(tmp_path / "control", clock=clock)
    completed = ledger.submit({"requests": [{"assetId": "resource.finance"}]})
    lease = ledger.claim("worker-a")
    assert lease is not None
    resultPayload = encodeDataResult(_failedResult(lease.request))
    ready = ledger.complete(
        completed.jobId,
        "worker-a",
        lease.leaseEpoch,
        resultPayload,
        requestDigest=lease.job.requestDigest,
    )
    assert ready.state == "succeeded"
    assert ledger.readResult(completed.jobId) == resultPayload

    clock.advance(1)
    cancelled = ledger.submit({"requests": [{"assetId": "resource.edgar"}]})
    assert ledger.cancel(cancelled.jobId).state == "cancelled"
    with pytest.raises(DataHubControlError) as unavailable:
        ledger.readResult(cancelled.jobId)
    assert unavailable.value.code == "DATA_HUB_CANCELLED"

    clock.advance(100)
    report = ledger.maintain(maximum=1, retentionSeconds=10)
    assert report.jobsDeleted == 1
    assert report.artifactsDeleted >= 1
    assert ledger.get(cancelled.jobId).state == "cancelled"


def testSubmitRejectsBudgetThatCannotFitTheResultWire(tmp_path):
    """결과가 wire 상한을 넘길 예산은 제출에서 막는다. 계산 후 재시도로 낭비하지 않는다."""

    ledger = DataHubJobLedger(tmp_path / "jobs")
    oversized = {
        "requests": [{"assetId": "scan.ratio", "requestId": "r"}],
        "budget": {"maxBytes": 64 * 1024 * 1024},
    }

    with pytest.raises(DataHubControlError) as captured:
        ledger.submit(oversized)
    assert captured.value.code == "DATA_HUB_PAYLOAD_BUDGET"

    fits = {
        "requests": [{"assetId": "scan.ratio", "requestId": "r"}],
        "budget": {"maxBytes": 4 * 1024 * 1024},
    }
    assert ledger.submit(fits).jobId


def testDurableQueryCanonicalizesDefaultsAndNullContinuation(tmp_path):
    ledger = DataHubJobLedger(tmp_path / "jobs")
    omitted = ledger.submit(
        {"requests": [{"assetId": "analysis.simulationInputs"}]},
        idempotencyKey="canonical",
    )
    explicit = ledger.submit(
        {
            "subjects": [],
            "measures": [],
            "requests": [{"assetId": "analysis.simulationInputs"}],
            "continuation": None,
            "budget": {"maxBytes": 12_517_376},
        },
        idempotencyKey="canonical",
    )
    lease = ledger.claim("worker")

    assert explicit == omitted
    assert lease is not None
    assert lease.request["continuation"] is None
    assert lease.request["materialization"] == {"mode": "refresh", "receipt": None}
    assert lease.request["budget"]["maxBytes"] == 12_517_376


def testMaintenanceCannotDeleteNewlyRereferencedCas(tmp_path):
    clock = FakeClock()
    ledger = DataHubJobLedger(tmp_path / "jobs", clock=clock)
    old = ledger.submit({"requests": [{"assetId": "analysis.simulationInputs"}]})
    ledger.cancel(old.jobId)
    clock.advance(100)
    deleting = threading.Event()
    release = threading.Event()
    originalDelete = ledger.artifacts.deleteBytes

    def blockedDelete(digest):
        deleting.set()
        assert release.wait(5)
        return originalDelete(digest)

    ledger.artifacts.deleteBytes = blockedDelete
    with ThreadPoolExecutor(max_workers=2) as executor:
        maintenance = executor.submit(ledger.maintain, maximum=1, retentionSeconds=10)
        assert deleting.wait(5)
        submitted = executor.submit(
            ledger.submit,
            {"requests": [{"assetId": "analysis.simulationInputs"}]},
        )
        assert not submitted.done()
        release.set()
        maintenance.result(timeout=10)
        new = submitted.result(timeout=10)

    lease = ledger.claim("worker")
    assert lease is not None
    assert lease.job.jobId == new.jobId
