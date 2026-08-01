"""원격 control plane에서 lease를 받아 DataHub query를 실행하는 worker."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any, Callable

import httpx

from dartlab.dataHub.cancellation import CancellationToken, activeCancellation
from dartlab.dataHub.controlPlane.policy import validateRemoteBaseUrl
from dartlab.dataHub.entry import dataHub
from dartlab.dataHub.telemetry import dataHubLogger, recordFailure
from dartlab.dataHub.transport import encodeDataResult

_log = dataHubLogger(__name__)


@dataclass(frozen=True, slots=True)
class WorkerRun:
    """Worker의 한 claim 시도 결과."""

    claimed: bool
    jobId: str | None
    completed: bool
    leaseLost: bool


class DataHubWorker:
    """여러 host에서 동일 control plane을 소비하는 pull worker."""

    def __init__(
        self,
        baseUrl: str,
        token: str,
        workerId: str,
        *,
        leaseSeconds: float = 120,
        requestTimeoutSeconds: float = 30,
        transport: httpx.BaseTransport | None = None,
        queryRunner: Callable[..., Any] = dataHub,
    ):
        if not isinstance(workerId, str) or not workerId or len(workerId) > 512:
            raise ValueError("workerId는 1자 이상 512자 이하여야 합니다")
        if leaseSeconds < 15 or leaseSeconds > 3600:
            raise ValueError("leaseSeconds는 15초 이상 3600초 이하여야 합니다")
        self.workerId = workerId
        self.leaseSeconds = float(leaseSeconds)
        self._queryRunner = queryRunner
        self._client = httpx.Client(
            base_url=validateRemoteBaseUrl(baseUrl),
            headers={"Authorization": f"Bearer {token}"},
            timeout=requestTimeoutSeconds,
            transport=transport,
        )

    def close(self) -> None:
        """Worker HTTP connection pool을 닫는다."""

        self._client.close()

    def _heartbeatLoop(
        self,
        jobId: str,
        leaseEpoch: int,
        stop: threading.Event,
        lost: threading.Event,
        cancelToken: CancellationToken | None = None,
    ) -> None:
        interval = max(5.0, self.leaseSeconds / 3)
        while not stop.wait(interval):
            try:
                response = self._client.post(
                    f"/api/dataHub/v1/workers/jobs/{jobId}/heartbeat",
                    json={
                        "workerId": self.workerId,
                        "leaseEpoch": leaseEpoch,
                        "leaseSeconds": self.leaseSeconds,
                    },
                )
                if not response.is_success:
                    lost.set()
                    if cancelToken is not None:
                        cancelToken.cancel()
                    return
            except httpx.HTTPError:
                lost.set()
                if cancelToken is not None:
                    cancelToken.cancel()
                return

    def _fail(
        self,
        jobId: str,
        leaseEpoch: int,
        *,
        errorCode: str = "DATA_HUB_WORKER_FAILED",
        retryable: bool = True,
    ) -> None:
        try:
            self._client.post(
                f"/api/dataHub/v1/workers/jobs/{jobId}/fail",
                json={
                    "workerId": self.workerId,
                    "leaseEpoch": leaseEpoch,
                    "errorCode": errorCode,
                    "retryDelaySeconds": min(60, 2**leaseEpoch),
                    "retryable": retryable,
                },
            )
        except httpx.HTTPError:
            return

    def runOnce(self) -> WorkerRun:
        """Job 하나를 claim하고 실행하며 없으면 즉시 반환한다."""

        claimResponse = self._client.post(
            "/api/dataHub/v1/workers/claims",
            json={
                "workerId": self.workerId,
                "leaseSeconds": self.leaseSeconds,
            },
        )
        claimResponse.raise_for_status()
        lease = claimResponse.json().get("lease")
        if lease is None:
            return WorkerRun(claimed=False, jobId=None, completed=False, leaseLost=False)
        job = lease.get("job")
        request = lease.get("request")
        leaseEpoch = lease.get("leaseEpoch")
        if (
            not isinstance(job, dict)
            or not isinstance(job.get("jobId"), str)
            or not isinstance(request, dict)
            or type(leaseEpoch) is not int
        ):
            raise RuntimeError("DataHub lease 응답이 유효하지 않습니다")
        jobId = job["jobId"]
        requestDigest = job.get("requestDigest")
        if not isinstance(requestDigest, str):
            raise RuntimeError("DataHub lease request digest가 유효하지 않습니다")
        stop = threading.Event()
        lost = threading.Event()
        cancelToken = CancellationToken("leaseLost")
        heartbeat = threading.Thread(
            target=self._heartbeatLoop,
            args=(jobId, leaseEpoch, stop, lost, cancelToken),
            name=f"dataHub-heartbeat-{jobId[:8]}",
            daemon=True,
        )
        heartbeat.start()
        try:
            # lease 를 잃으면 실행 중인 query 도 다음 page 경계에서 멈춘다. 이 배선이
            # 없으면 취소된 job 이 자기 timeout 까지 머신 하나를 계속 태운다.
            with activeCancellation(cancelToken):
                result = self._queryRunner("query", query=request)
            payload = encodeDataResult(result)
            if lost.is_set():
                return WorkerRun(claimed=True, jobId=jobId, completed=False, leaseLost=True)
            complete = self._client.post(
                f"/api/dataHub/v1/workers/jobs/{jobId}/complete",
                params={"leaseEpoch": leaseEpoch},
                headers={
                    "X-DataHub-Worker": self.workerId,
                    "X-DataHub-Request-Digest": requestDigest,
                },
                content=payload,
            )
            if complete.status_code == 409:
                return WorkerRun(claimed=True, jobId=jobId, completed=False, leaseLost=True)
            if complete.status_code in {413, 422}:
                try:
                    code = complete.json()["detail"]["code"]
                except (ValueError, KeyError, TypeError):
                    code = "DATA_HUB_WORKER_FAILED"
                self._fail(jobId, leaseEpoch, errorCode=code, retryable=False)
                return WorkerRun(claimed=True, jobId=jobId, completed=False, leaseLost=False)
            complete.raise_for_status()
            return WorkerRun(claimed=True, jobId=jobId, completed=True, leaseLost=False)
        except Exception:
            # 원격 운영자는 고정 code 하나만 받는다. 원인은 이 side channel 에만 남는다.
            recordFailure(_log, "DATA_HUB_WORKER_FAILED", context={"jobId": jobId, "workerId": self.workerId})
            if not lost.is_set():
                self._fail(jobId, leaseEpoch)
            return WorkerRun(
                claimed=True,
                jobId=jobId,
                completed=False,
                leaseLost=lost.is_set(),
            )
        finally:
            stop.set()
            heartbeat.join(timeout=5)

    def runForever(
        self,
        *,
        idleSeconds: float = 1,
        stop: threading.Event | None = None,
    ) -> None:
        """Stop event가 설정될 때까지 bounded polling한다."""

        if idleSeconds <= 0 or idleSeconds > 60:
            raise ValueError("idleSeconds는 0초 초과 60초 이하여야 합니다")
        stopEvent = stop or threading.Event()
        while not stopEvent.is_set():
            outcome = self.runOnce()
            if not outcome.claimed:
                stopEvent.wait(idleSeconds)
