from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from dartlab.dataHub.controlPlane import DataHubControlError
from dartlab.dataHub.controlPlane.ledger import DataHubJobLedger

pytestmark = pytest.mark.unit


class FakeClock:
    def __init__(self, value: float = 100.0):
        self.value = value

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


def testSubmitIsIdempotentAndDefaultsToDurableRefresh(tmp_path: Path) -> None:
    ledger = DataHubJobLedger(tmp_path / "control")
    query = {"requests": [{"assetId": "resource.finance"}]}

    first = ledger.submit(query, idempotencyKey="same-request")
    repeated = ledger.submit(query, idempotencyKey="same-request")
    lease = ledger.claim("worker-a")

    assert repeated == first
    assert lease is not None
    assert lease.job.jobId == first.jobId
    assert lease.request["materialization"] == {"mode": "refresh"}
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
    resultPayload = b'{"wire":"result"}'
    ready = ledger.complete(completed.jobId, "worker-a", lease.leaseEpoch, resultPayload)
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
