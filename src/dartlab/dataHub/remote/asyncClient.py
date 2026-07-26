"""DataHub versioned HTTP API의 asyncio client."""

from __future__ import annotations

import asyncio
import time
from typing import Any, Mapping

import httpx

from dartlab.dataHub.contracts import DataResult
from dartlab.dataHub.controlPlane.contracts import DataHubJob
from dartlab.dataHub.controlPlane.errors import DataHubControlError
from dartlab.dataHub.transport import decodeDataResult

from .client import _jobFromTree


class AsyncDataHubClient:
    """Event loop를 막지 않는 원격 DataHub client."""

    def __init__(
        self,
        baseUrl: str,
        token: str,
        *,
        timeoutSeconds: float = 30,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        if not isinstance(baseUrl, str) or not baseUrl.startswith(("http://", "https://")):
            raise ValueError("baseUrl은 http 또는 https URL이어야 합니다")
        if not isinstance(token, str) or len(token) < 32:
            raise ValueError("token은 32자 이상이어야 합니다")
        self._client = httpx.AsyncClient(
            base_url=baseUrl.rstrip("/"),
            headers={"Authorization": f"Bearer {token}"},
            timeout=timeoutSeconds,
            transport=transport,
        )

    async def close(self) -> None:
        """HTTP connection pool을 닫는다."""

        await self._client.aclose()

    async def __aenter__(self) -> AsyncDataHubClient:
        return self

    async def __aexit__(self, *_args: Any) -> None:
        await self.close()

    @staticmethod
    def _raise(response: httpx.Response) -> None:
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

    async def catalog(self, query: Mapping[str, Any] | None = None) -> Mapping[str, Any]:
        """원격 metadata catalog를 비동기로 조회한다."""

        response = await self._client.post(
            "/api/dataHub/v1/catalog",
            json=None if query is None else dict(query),
        )
        self._raise(response)
        value = response.json()
        if not isinstance(value, dict):
            raise DataHubControlError("DATA_HUB_CORRUPT")
        return value

    async def submit(
        self,
        query: Mapping[str, Any],
        *,
        idempotencyKey: str | None = None,
        priority: int = 0,
        maxAttempts: int = 3,
    ) -> DataHubJob:
        """Query를 비동기 durable job으로 제출한다."""

        response = await self._client.post(
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

    async def query(
        self,
        query: Mapping[str, Any],
        *,
        wait: bool = True,
        idempotencyKey: str | None = None,
        priority: int = 0,
        maxAttempts: int = 3,
    ) -> DataHubJob | DataResult:
        """Local DataHub와 같은 query를 event loop 친화적으로 실행한다."""

        job = await self.submit(
            query,
            idempotencyKey=idempotencyKey,
            priority=priority,
            maxAttempts=maxAttempts,
        )
        return await self.wait(job.jobId) if wait else job

    async def job(self, jobId: str) -> DataHubJob:
        """Job 상태를 비동기로 조회한다."""

        response = await self._client.get(f"/api/dataHub/v1/jobs/{jobId}")
        self._raise(response)
        return _jobFromTree(response.json())

    async def result(self, jobId: str) -> DataResult:
        """성공한 job의 DataResult를 비동기로 읽는다."""

        response = await self._client.get(f"/api/dataHub/v1/jobs/{jobId}/result")
        self._raise(response)
        return decodeDataResult(response.content)

    async def cancel(self, jobId: str) -> DataHubJob:
        """Job을 비동기로 취소한다."""

        response = await self._client.delete(f"/api/dataHub/v1/jobs/{jobId}")
        self._raise(response)
        return _jobFromTree(response.json())

    async def wait(
        self,
        jobId: str,
        *,
        timeoutSeconds: float = 3600,
        pollSeconds: float = 0.25,
    ) -> DataResult:
        """Terminal 상태까지 event loop 친화적으로 기다린다."""

        if timeoutSeconds <= 0 or pollSeconds <= 0:
            raise ValueError("timeoutSeconds와 pollSeconds는 양수여야 합니다")
        deadline = time.monotonic() + timeoutSeconds
        while time.monotonic() < deadline:
            job = await self.job(jobId)
            if job.state == "succeeded":
                return await self.result(jobId)
            if job.state == "cancelled":
                raise DataHubControlError("DATA_HUB_CANCELLED")
            if job.state == "failed":
                code = job.errorCode or "DATA_HUB_ATTEMPTS_EXHAUSTED"
                raise DataHubControlError(code)
            await asyncio.sleep(min(pollSeconds, max(0, deadline - time.monotonic())))
        raise TimeoutError("DataHub job wait timeout")

    async def __call__(
        self,
        axis: str,
        *,
        query: Mapping[str, Any] | None = None,
        wait: bool = True,
        idempotencyKey: str | None = None,
    ) -> Mapping[str, Any] | DataHubJob | DataResult:
        """Local DataHub와 같은 axis를 비동기 원격 실행한다."""

        if axis == "catalog":
            return await self.catalog(query)
        if axis != "query" or query is None:
            raise KeyError("dataHub axis는 'catalog' 또는 'query'여야 합니다")
        return await self.query(query, wait=wait, idempotencyKey=idempotencyKey)
