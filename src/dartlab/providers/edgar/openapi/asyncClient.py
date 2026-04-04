"""비동기 EDGAR API 클라이언트 — 배치 수집 전용.

SEC public API rate limit: 10 req/s per User-Agent.
0.12s interval = ~8 req/s (안전 마진).
"""

from __future__ import annotations

import asyncio
from typing import Any

import httpx

from dartlab.providers.edgar.openapi.client import (
    DEFAULT_USER_AGENT,
    EdgarApiError,
)

# 전체 워커 공유 세마포어 — 동시 요청 8개 제한
# 이벤트 루프별로 세마포어를 생성해야 함 (루프 간 공유 불가)
_LOOP_SEMAPHORES: dict[int, asyncio.Semaphore] = {}


def _getSemaphore() -> asyncio.Semaphore:
    """현재 이벤트 루프에 바인딩된 세마포어 반환."""
    loop = asyncio.get_running_loop()
    loopId = id(loop)
    if loopId not in _LOOP_SEMAPHORES:
        _LOOP_SEMAPHORES[loopId] = asyncio.Semaphore(8)
        # 이전 루프의 세마포어 정리 (메모리 누수 방지)
        stale = [k for k in _LOOP_SEMAPHORES if k != loopId]
        for k in stale:
            del _LOOP_SEMAPHORES[k]
    return _LOOP_SEMAPHORES[loopId]


class AsyncEdgarClient:
    """비동기 SEC API 클라이언트 (배치 수집 전용).

    DART의 AsyncDartClient 패턴을 SEC에 이식.
    API 키 불필요 — User-Agent가 식별자.
    """

    def __init__(
        self,
        *,
        userAgent: str | None = None,
        minInterval: float = 0.12,
        timeout: float = 30.0,
        maxRetries: int = 3,
    ):
        self._userAgent = userAgent or DEFAULT_USER_AGENT
        self._client = httpx.AsyncClient(
            follow_redirects=True,
            timeout=timeout,
        )
        self._minInterval = max(float(minInterval), 0.0)
        self._maxRetries = max(int(maxRetries), 1)
        self._lastRequest = 0.0
        self.exhausted = False

    @property
    def headers(self) -> dict[str, str]:
        return {"User-Agent": self._userAgent}

    async def _throttle(self) -> None:
        """rate limit 준수."""
        now = asyncio.get_event_loop().time()
        elapsed = now - self._lastRequest
        if elapsed < self._minInterval:
            await asyncio.sleep(self._minInterval - elapsed)
        self._lastRequest = asyncio.get_event_loop().time()

    async def getJson(self, url: str) -> dict[str, Any]:
        """URL에서 JSON 반환. 429/5xx 시 재시도."""
        sem = _getSemaphore()
        lastErr: Exception | None = None

        for attempt in range(self._maxRetries):
            async with sem:
                await self._throttle()
                try:
                    resp = await self._client.get(url, headers=self.headers)
                    self._lastRequest = asyncio.get_event_loop().time()

                    if resp.status_code == 429:
                        self.exhausted = True
                        await asyncio.sleep(2**attempt)
                        continue

                    resp.raise_for_status()
                    data = resp.json()
                    if not isinstance(data, dict):
                        raise EdgarApiError(f"JSON object expected: {url}")
                    return data

                except httpx.HTTPStatusError as exc:
                    lastErr = exc
                    status = exc.response.status_code
                    if status in (429, 500, 502, 503, 504) and attempt < self._maxRetries - 1:
                        await asyncio.sleep(2**attempt)
                        continue
                    raise EdgarApiError(f"SEC API ({status}): {url}") from exc

                except httpx.HTTPError as exc:
                    lastErr = exc
                    if attempt < self._maxRetries - 1:
                        await asyncio.sleep(2**attempt)
                        continue
                    raise EdgarApiError(f"SEC API 네트워크 오류: {url}") from exc

        raise EdgarApiError(f"SEC API 요청 실패 (재시도 초과): {url}") from lastErr

    async def getBytes(self, url: str) -> bytes:
        """URL에서 바이너리 반환."""
        sem = _getSemaphore()
        lastErr: Exception | None = None

        for attempt in range(self._maxRetries):
            async with sem:
                await self._throttle()
                try:
                    resp = await self._client.get(url, headers=self.headers, timeout=60)
                    self._lastRequest = asyncio.get_event_loop().time()

                    if resp.status_code == 429:
                        self.exhausted = True
                        await asyncio.sleep(2**attempt)
                        continue

                    resp.raise_for_status()
                    return resp.content

                except httpx.HTTPStatusError as exc:
                    lastErr = exc
                    status = exc.response.status_code
                    if status in (429, 500, 502, 503, 504) and attempt < self._maxRetries - 1:
                        await asyncio.sleep(2**attempt)
                        continue
                    raise EdgarApiError(f"SEC API ({status}): {url}") from exc

                except httpx.HTTPError as exc:
                    lastErr = exc
                    if attempt < self._maxRetries - 1:
                        await asyncio.sleep(2**attempt)
                        continue
                    raise EdgarApiError(f"SEC API 네트워크 오류: {url}") from exc

        raise EdgarApiError(f"SEC API 바이너리 요청 실패: {url}") from lastErr

    async def close(self) -> None:
        """HTTP 클라이언트 연결을 닫는다."""
        await self._client.aclose()
