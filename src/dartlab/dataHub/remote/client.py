"""DataHub versioned HTTP API의 동기 Python client."""

from __future__ import annotations

import time
from typing import Any, Mapping

import httpx

from dartlab.dataHub.continuation import canonicalJsonBytes
from dartlab.dataHub.contracts import DataResult
from dartlab.dataHub.controlPlane.contracts import DataHubJob
from dartlab.dataHub.controlPlane.errors import DataHubControlError
from dartlab.dataHub.controlPlane.policy import (
    MAX_REQUEST_BYTES,
    MAX_RESULT_WIRE_BYTES,
    validateRemoteBaseUrl,
)
from dartlab.dataHub.transport import decodeDataResult


def _raise(response: httpx.Response) -> None:
    """실패 응답을 typed control 오류로 올린다. 성공이면 아무것도 하지 않는다.

    동기 client 와 async client 가 같은 HTTP 계약을 쓰므로 판정도 한 자리에 둔다.
    본문에서 code 를 못 읽거나 아는 code 가 아니면 훼손으로 끝낸다.
    """
    if response.is_success:
        return
    try:
        detail = response.json().get("detail", {})
        code = detail.get("code")
    except (ValueError, AttributeError):
        code = None
    if isinstance(code, str):
        try:
            raise DataHubControlError(code)
        except ValueError:
            pass
    raise DataHubControlError("DATA_HUB_CORRUPT")


def _jobFromTree(value: Any) -> DataHubJob:
    if not isinstance(value, dict):
        raise DataHubControlError("DATA_HUB_CORRUPT")
    tree = dict(value)
    tree.pop("terminal", None)
    try:
        return DataHubJob(**tree)
    except (TypeError, ValueError):
        raise DataHubControlError("DATA_HUB_CORRUPT") from None


def _preflightSubmit(query: Mapping[str, Any], idempotencyKey: str | None, priority: int, maxAttempts: int) -> None:
    try:
        payload = canonicalJsonBytes(
            {
                "query": dict(query),
                "idempotencyKey": idempotencyKey,
                "priority": priority,
                "maxAttempts": maxAttempts,
            }
        )
    except (TypeError, ValueError):
        raise DataHubControlError("DATA_HUB_INVALID") from None
    if len(payload) > MAX_REQUEST_BYTES:
        raise DataHubControlError("DATA_HUB_PAYLOAD_BUDGET")


def _boundedResponse(response: httpx.Response, *, maximum: int) -> bytes:
    contentLength = response.headers.get("content-length")
    if contentLength is not None:
        try:
            if int(contentLength) > maximum:
                raise DataHubControlError("DATA_HUB_PAYLOAD_BUDGET")
        except ValueError:
            raise DataHubControlError("DATA_HUB_CORRUPT") from None
    payload = bytearray()
    for chunk in response.iter_bytes():
        if len(payload) + len(chunk) > maximum:
            raise DataHubControlError("DATA_HUB_PAYLOAD_BUDGET")
        payload.extend(chunk)
    return bytes(payload)


class DataHubClient:
    """Local DataHub와 같은 catalog, query 의미를 쓰는 원격 client."""

    def __init__(
        self,
        baseUrl: str,
        token: str,
        *,
        timeoutSeconds: float = 30,
        transport: httpx.BaseTransport | None = None,
    ):
        if not isinstance(token, str) or len(token) < 32:
            raise ValueError("token은 32자 이상이어야 합니다")
        self.baseUrl = validateRemoteBaseUrl(baseUrl)
        self._client = httpx.Client(
            base_url=self.baseUrl,
            headers={"Authorization": f"Bearer {token}"},
            timeout=timeoutSeconds,
            transport=transport,
        )

    def close(self) -> None:
        """HTTP connection pool을 닫는다."""

        self._client.close()

    def __enter__(self) -> DataHubClient:
        return self

    def __exit__(self, *_args: Any) -> None:
        self.close()

    _raise = staticmethod(_raise)

    def catalog(self, query: Mapping[str, Any] | None = None) -> Mapping[str, Any]:
        """원격 metadata catalog를 조회한다."""

        response = self._client.post("/api/dataHub/v1/catalog", json=None if query is None else dict(query))
        self._raise(response)
        value = response.json()
        if not isinstance(value, dict):
            raise DataHubControlError("DATA_HUB_CORRUPT")
        return value

    def submit(
        self,
        query: Mapping[str, Any],
        *,
        idempotencyKey: str | None = None,
        priority: int = 0,
        maxAttempts: int = 3,
    ) -> DataHubJob:
        """Query를 비동기 durable job으로 제출한다."""

        _preflightSubmit(query, idempotencyKey, priority, maxAttempts)
        response = self._client.post(
            "/api/dataHub/v1/jobs",
            json={
                "query": dict(query),
                "idempotencyKey": idempotencyKey,
                "priority": priority,
                "maxAttempts": maxAttempts,
            },
        )
        self._raise(response)
        return _jobFromTree(response.json())

    def query(
        self,
        query: Mapping[str, Any],
        *,
        wait: bool = True,
        idempotencyKey: str | None = None,
        priority: int = 0,
        maxAttempts: int = 3,
    ) -> DataHubJob | DataResult:
        """Local DataHub와 같은 query를 원격 durable 실행으로 보낸다."""

        job = self.submit(
            query,
            idempotencyKey=idempotencyKey,
            priority=priority,
            maxAttempts=maxAttempts,
        )
        return self.wait(job.jobId) if wait else job

    def job(self, jobId: str) -> DataHubJob:
        """Job 상태를 조회한다."""

        response = self._client.get(f"/api/dataHub/v1/jobs/{jobId}")
        self._raise(response)
        return _jobFromTree(response.json())

    def cancel(self, jobId: str) -> DataHubJob:
        """Job을 취소한다."""

        response = self._client.delete(f"/api/dataHub/v1/jobs/{jobId}")
        self._raise(response)
        return _jobFromTree(response.json())

    def result(self, jobId: str) -> DataResult:
        """성공한 job의 무손실 DataResult를 복원한다."""

        with self._client.stream("GET", f"/api/dataHub/v1/jobs/{jobId}/result") as response:
            payload = _boundedResponse(response, maximum=MAX_RESULT_WIRE_BYTES)
            response._content = payload
            self._raise(response)
        return decodeDataResult(payload)

    def wait(
        self,
        jobId: str,
        *,
        timeoutSeconds: float = 3600,
        pollSeconds: float = 0.25,
    ) -> DataResult:
        """Terminal 상태까지 bounded polling한 뒤 결과를 반환한다."""

        if timeoutSeconds <= 0 or pollSeconds <= 0:
            raise ValueError("timeoutSeconds와 pollSeconds는 양수여야 합니다")
        deadline = time.monotonic() + timeoutSeconds
        while time.monotonic() < deadline:
            job = self.job(jobId)
            if job.state == "succeeded":
                return self.result(jobId)
            if job.state == "cancelled":
                raise DataHubControlError("DATA_HUB_CANCELLED")
            if job.state == "failed":
                code = job.errorCode or "DATA_HUB_ATTEMPTS_EXHAUSTED"
                raise DataHubControlError(code)
            time.sleep(min(pollSeconds, max(0, deadline - time.monotonic())))
        raise TimeoutError("DataHub job wait timeout")

    def __call__(
        self,
        axis: str,
        *,
        query: Mapping[str, Any] | None = None,
        wait: bool = True,
        idempotencyKey: str | None = None,
    ) -> Mapping[str, Any] | DataHubJob | DataResult:
        """Local DataHub와 같은 axis를 원격 실행한다."""

        if axis == "catalog":
            return self.catalog(query)
        if axis != "query" or query is None:
            raise KeyError("dataHub axis는 'catalog' 또는 'query'여야 합니다")
        return self.query(query, wait=wait, idempotencyKey=idempotencyKey)
