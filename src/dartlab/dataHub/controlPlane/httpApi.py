"""DataHub remote client와 worker가 공유하는 versioned HTTP API."""

from __future__ import annotations

import dataclasses
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request, Response

from dartlab.dataHub.catalog import buildCatalog
from dartlab.dataHub.entry import _catalogQuery
from dartlab.dataHub.transport import decodeDataResult

from .auth import DataHubAuthPolicy
from .errors import DataHubControlError
from .ledger import DataHubJobLedger
from .runtime import dataHubJobLedger

_MEDIA_TYPE = "application/vnd.dartlab.datahub-result+json"
_MAINTENANCE_MAXIMUM = 32


def _httpError(error: DataHubControlError) -> HTTPException:
    status = {
        "DATA_HUB_INVALID": 400,
        "DATA_HUB_NOT_FOUND": 404,
        "DATA_HUB_CONFLICT": 409,
        "DATA_HUB_LEASE_LOST": 409,
        "DATA_HUB_NOT_READY": 425,
        "DATA_HUB_CANCELLED": 410,
        "DATA_HUB_AUTH_REQUIRED": 401,
        "DATA_HUB_PAYLOAD_BUDGET": 413,
        "DATA_HUB_CORRUPT": 422,
    }.get(error.code, 500)
    return HTTPException(status_code=status, detail={"code": error.code, "message": str(error)})


def buildDataHubRouter(
    *,
    ledger: DataHubJobLedger | None = None,
    authPolicy: DataHubAuthPolicy | None = None,
) -> APIRouter:
    """주입 가능한 ledger와 role 인증으로 DataHub router를 만든다."""

    router = APIRouter(prefix="/api/dataHub/v1", tags=["dataHub"])

    def activeLedger() -> DataHubJobLedger:
        """주입값 또는 기본 런타임 ledger를 반환한다."""

        return ledger if ledger is not None else dataHubJobLedger()

    def authorize(value: str | None, *, role: str) -> None:
        """요청 token이 지정한 역할에 허용되는지 검증한다."""

        policy = authPolicy if authPolicy is not None else DataHubAuthPolicy.fromEnvironment()
        policy.authorize(value, role=role)

    @router.post("/catalog")
    def catalog(
        payload: dict[str, Any] | None = None,
        authorization: str | None = Header(default=None),
    ):
        """현재 DataHub asset catalog snapshot을 반환한다."""

        try:
            authorize(authorization, role="client")
            result = buildCatalog(_catalogQuery(payload))
            return {
                "status": result.status,
                "assets": [dataclasses.asdict(asset) for asset in result.assets],
                "snapshotId": result.snapshotId,
                "coverage": dataclasses.asdict(result.coverage),
                "gaps": [dataclasses.asdict(gap) for gap in result.gaps],
            }
        except DataHubControlError as error:
            raise _httpError(error) from None
        except (TypeError, ValueError) as error:
            raise HTTPException(
                status_code=400,
                detail={"code": "DATA_HUB_INVALID", "message": str(error)},
            ) from None

    @router.post("/jobs", status_code=202)
    def submit(
        payload: dict[str, Any],
        authorization: str | None = Header(default=None),
    ):
        """비동기 DataHub query job을 ledger에 제출한다."""

        try:
            authorize(authorization, role="client")
            if not isinstance(payload, dict) or not isinstance(payload.get("query"), dict):
                raise DataHubControlError("DATA_HUB_INVALID")
            ledger = activeLedger()
            # 제출 한 번마다 작은 bounded 정리 step 을 태운다. 별도 스케줄러나 daemon 없이
            # 만료 lease 재queue 와 retention 초과 terminal job, CAS payload 를 회수한다.
            # claim 은 원자 경합 hot path 라 여기에 붙이지 않는다.
            ledger.maintain(maximum=_MAINTENANCE_MAXIMUM)
            job = ledger.submit(
                payload["query"],
                idempotencyKey=payload.get("idempotencyKey"),
                priority=payload.get("priority", 0),
                maxAttempts=payload.get("maxAttempts", 3),
            )
            return job.asTree()
        except DataHubControlError as error:
            raise _httpError(error) from None

    @router.get("/jobs/{jobId}")
    def status(
        jobId: str,
        authorization: str | None = Header(default=None),
    ):
        """지정한 DataHub job의 현재 상태를 반환한다."""

        try:
            authorize(authorization, role="client")
            return activeLedger().get(jobId).asTree()
        except DataHubControlError as error:
            raise _httpError(error) from None

    @router.delete("/jobs/{jobId}")
    def cancel(
        jobId: str,
        authorization: str | None = Header(default=None),
    ):
        """대기 또는 실행 중인 DataHub job을 취소한다."""

        try:
            authorize(authorization, role="client")
            return activeLedger().cancel(jobId).asTree()
        except DataHubControlError as error:
            raise _httpError(error) from None

    @router.get("/jobs/{jobId}/result")
    def result(
        jobId: str,
        authorization: str | None = Header(default=None),
    ):
        """완료된 DataHub job의 봉인 결과 payload를 반환한다."""

        try:
            authorize(authorization, role="client")
            payload = activeLedger().readResult(jobId)
            return Response(content=payload, media_type=_MEDIA_TYPE)
        except DataHubControlError as error:
            raise _httpError(error) from None

    @router.post("/workers/claims")
    def claim(
        payload: dict[str, Any],
        authorization: str | None = Header(default=None),
    ):
        """대기 중인 job 하나를 worker lease로 인계한다."""

        try:
            authorize(authorization, role="worker")
            workerId = payload.get("workerId")
            if not isinstance(workerId, str):
                raise DataHubControlError("DATA_HUB_INVALID")
            lease = activeLedger().claim(
                workerId,
                leaseSeconds=payload.get("leaseSeconds", 60),
            )
            return {"lease": None if lease is None else lease.asTree()}
        except DataHubControlError as error:
            raise _httpError(error) from None

    @router.post("/workers/jobs/{jobId}/heartbeat")
    def heartbeat(
        jobId: str,
        payload: dict[str, Any],
        authorization: str | None = Header(default=None),
    ):
        """worker가 소유한 job lease의 만료 시각을 연장한다."""

        try:
            authorize(authorization, role="worker")
            job = activeLedger().heartbeat(
                jobId,
                payload.get("workerId"),
                payload.get("leaseEpoch"),
                leaseSeconds=payload.get("leaseSeconds", 60),
            )
            return job.asTree()
        except DataHubControlError as error:
            raise _httpError(error) from None

    @router.post("/workers/jobs/{jobId}/complete")
    async def complete(
        jobId: str,
        request: Request,
        leaseEpoch: int,
        workerId: str = Header(alias="X-DataHub-Worker"),
        authorization: str | None = Header(default=None),
    ):
        """worker 결과를 검증해 성공 상태로 원자적으로 확정한다."""

        try:
            authorize(authorization, role="worker")
            payload = await request.body()
            decodeDataResult(payload)
            job = activeLedger().complete(jobId, workerId, leaseEpoch, payload)
            return job.asTree()
        except DataHubControlError as error:
            raise _httpError(error) from None

    @router.post("/workers/jobs/{jobId}/fail")
    def fail(
        jobId: str,
        payload: dict[str, Any],
        authorization: str | None = Header(default=None),
    ):
        """worker 실패를 기록하고 정책에 따라 재시도 상태를 정한다."""

        try:
            authorize(authorization, role="worker")
            job = activeLedger().fail(
                jobId,
                payload.get("workerId"),
                payload.get("leaseEpoch"),
                errorCode=payload.get("errorCode"),
                retryDelaySeconds=payload.get("retryDelaySeconds", 0),
            )
            return job.asTree()
        except DataHubControlError as error:
            raise _httpError(error) from None

    return router
