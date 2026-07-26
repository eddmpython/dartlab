"""DataHub 비동기 control plane의 durable job 계약."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping

JobState = Literal["queued", "leased", "succeeded", "failed", "cancelled"]


@dataclass(frozen=True, slots=True)
class DataHubJob:
    """외부에 노출해도 되는 digest 중심 job 상태."""

    jobId: str
    state: JobState
    requestDigest: str
    priority: int
    attemptCount: int
    maxAttempts: int
    createdAt: float
    updatedAt: float
    availableAt: float
    leaseEpoch: int
    leaseExpiresAt: float | None
    resultDigest: str | None
    errorCode: str | None

    @property
    def terminal(self) -> bool:
        """Job이 더 이상 상태 전이를 기다리지 않는지 반환한다."""

        return self.state in {"succeeded", "failed", "cancelled"}

    def asTree(self) -> dict[str, Any]:
        """HTTP와 Python client가 공유하는 JSON tree를 반환한다."""

        return {
            "jobId": self.jobId,
            "state": self.state,
            "requestDigest": self.requestDigest,
            "priority": self.priority,
            "attemptCount": self.attemptCount,
            "maxAttempts": self.maxAttempts,
            "createdAt": self.createdAt,
            "updatedAt": self.updatedAt,
            "availableAt": self.availableAt,
            "leaseEpoch": self.leaseEpoch,
            "leaseExpiresAt": self.leaseExpiresAt,
            "resultDigest": self.resultDigest,
            "errorCode": self.errorCode,
            "terminal": self.terminal,
        }


@dataclass(frozen=True, slots=True)
class DataHubLease:
    """원격 worker가 독점 실행하는 한 job lease."""

    job: DataHubJob
    workerDigest: str
    leaseEpoch: int
    leaseExpiresAt: float
    request: Mapping[str, Any]

    def asTree(self) -> dict[str, Any]:
        """Worker transport용 lease tree를 반환한다."""

        return {
            "job": self.job.asTree(),
            "leaseEpoch": self.leaseEpoch,
            "leaseExpiresAt": self.leaseExpiresAt,
            "request": dict(self.request),
        }


@dataclass(frozen=True, slots=True)
class DataHubMaintenanceReport:
    """한 번의 bounded maintenance가 처리한 job 수."""

    leasesRequeued: int
    leasesFailed: int
    jobsDeleted: int
    artifactsDeleted: int
