"""비동기 EDGAR API 클라이언트 — 배치 수집 전용.

SEC public API rate limit: 10 req/s per User-Agent.
0.12s interval = ~8 req/s (안전 마진).
"""

from __future__ import annotations

import asyncio
from typing import Any

import httpx

from dartlab.core.edgarClient import (
    DEFAULT_USER_AGENT,
    EdgarApiError,
)
from dartlab.core.requestPacing import awaitMinInterval

# 이벤트 루프별 세마포어 (루프 간 공유 불가)
_LOOP_SEMAPHORES: dict[int, asyncio.Semaphore] = {}


def _getSemaphore() -> asyncio.Semaphore:
    """현재 이벤트 루프에 바인딩된 세마포어 반환."""
    loop = asyncio.get_running_loop()
    loopId = id(loop)
    if loopId not in _LOOP_SEMAPHORES:
        _LOOP_SEMAPHORES[loopId] = asyncio.Semaphore(8)
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
        """SEC API 호출에 사용되는 HTTP headers.

        Returns:
            ``{"User-Agent": ...}`` dict.

        Raises:
            없음.

        Example:
            >>> AsyncEdgarClient().headers

        LLM Specifications:
            AntiPatterns:
                - SEC User-Agent 헤더 미설정 → 403 Forbidden. 본 클래스 자동 주입.
                - rate limit (10 req/s) 초과 → 차단. minInterval 0.12 기본.
                - 동시 워커 >> 세마포어 (8) → 추가 wait, 효율 손실.
            OutputSchema:
                - dict / bytes — endpoint 별.
            Prerequisites:
                - 인터넷 + SEC EDGAR public API (키 불요).
            Freshness:
                - SEC EDGAR 실시간 (분 단위).
            Dataflow:
                - 인자 → 세마포어 → httpx → SEC API → 정규화 → 본 함수.
            TargetMarkets:
                - US (SEC EDGAR) 배치 수집.
        """
        return {"User-Agent": self._userAgent}

    async def _throttle(self) -> None:
        """rate limit 준수."""
        self._lastRequest = await awaitMinInterval(self._lastRequest, self._minInterval)

    async def _requestWithRetry(self, url: str, *, timeout: float | None = None) -> httpx.Response:
        """공용 재시도 로직. 429/5xx 시 exponential backoff."""
        sem = _getSemaphore()
        lastErr: Exception | None = None

        for attempt in range(self._maxRetries):
            async with sem:
                await self._throttle()
                try:
                    kwargs: dict[str, Any] = {"headers": self.headers}
                    if timeout is not None:
                        kwargs["timeout"] = timeout
                    resp = await self._client.get(url, **kwargs)
                    self._lastRequest = asyncio.get_event_loop().time()

                    if resp.status_code == 429:
                        self.exhausted = True
                        await asyncio.sleep(2**attempt)
                        continue

                    resp.raise_for_status()
                    return resp

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

    async def getJson(self, url: str) -> dict[str, Any]:
        """URL 에서 JSON 반환.

        Args:
            url: SEC API endpoint URL.

        Returns:
            JSON dict.

        Raises:
            EdgarApiError: API 호출 실패 또는 JSON object 아님.

        Example:
            >>> await AsyncEdgarClient().getJson("https://data.sec.gov/...")

        SeeAlso:
            - ``EdgarClient`` — 동기 버전 (단건 호출용).

        Requires:
            - asyncio
            - dartlab
            - httpx

        Capabilities:
            - SEC API 비동기 호출 + 세마포어 기반 rate limit. asyncio batch 수집 backend.

        Guide:
            - 운영자 batch 수집 — 사용자 API 직접 호출 X.

        AIContext:
            internal async client — AI 직접 호출 X.

        LLM Specifications:
            AntiPatterns:
                - SEC User-Agent 헤더 미설정 → 403 Forbidden. 본 클래스 자동 주입.
                - rate limit (10 req/s) 초과 → 차단. minInterval 0.12 기본.
                - 동시 워커 >> 세마포어 (8) → 추가 wait, 효율 손실.
            OutputSchema:
                - dict / bytes — endpoint 별.
            Prerequisites:
                - 인터넷 + SEC EDGAR public API (키 불요).
            Freshness:
                - SEC EDGAR 실시간 (분 단위).
            Dataflow:
                - 인자 → 세마포어 → httpx → SEC API → 정규화 → 본 함수.
            TargetMarkets:
                - US (SEC EDGAR) 배치 수집.
        """
        resp = await self._requestWithRetry(url)
        data = resp.json()
        if not isinstance(data, dict):
            raise EdgarApiError(f"JSON object expected: {url}")
        return data

    async def getBytes(self, url: str) -> bytes:
        """URL 에서 바이너리 반환.

        Args:
            url: SEC endpoint URL.

        Returns:
            raw bytes.

        Raises:
            EdgarApiError: API 호출 실패.

        Example:
            >>> await AsyncEdgarClient().getBytes("https://...")

        SeeAlso:
            - ``EdgarClient`` — 동기 버전 (단건 호출용).

        Requires:
            - asyncio
            - dartlab
            - httpx

        Capabilities:
            - SEC API 비동기 호출 + 세마포어 기반 rate limit. asyncio batch 수집 backend.

        Guide:
            - 운영자 batch 수집 — 사용자 API 직접 호출 X.

        AIContext:
            internal async client — AI 직접 호출 X.

        LLM Specifications:
            AntiPatterns:
                - SEC User-Agent 헤더 미설정 → 403 Forbidden. 본 클래스 자동 주입.
                - rate limit (10 req/s) 초과 → 차단. minInterval 0.12 기본.
                - 동시 워커 >> 세마포어 (8) → 추가 wait, 효율 손실.
            OutputSchema:
                - dict / bytes — endpoint 별.
            Prerequisites:
                - 인터넷 + SEC EDGAR public API (키 불요).
            Freshness:
                - SEC EDGAR 실시간 (분 단위).
            Dataflow:
                - 인자 → 세마포어 → httpx → SEC API → 정규화 → 본 함수.
            TargetMarkets:
                - US (SEC EDGAR) 배치 수집.
        """
        resp = await self._requestWithRetry(url, timeout=60)
        return resp.content

    async def close(self) -> None:
        """HTTP 클라이언트 연결을 닫는다.

        Raises:
            없음.

        Example:
            >>> await AsyncEdgarClient().close()

        SeeAlso:
            - ``EdgarClient`` — 동기 버전 (단건 호출용).

        Requires:
            - asyncio
            - dartlab
            - httpx

        Capabilities:
            - SEC API 비동기 호출 + 세마포어 기반 rate limit. asyncio batch 수집 backend.

        Guide:
            - 운영자 batch 수집 — 사용자 API 직접 호출 X.

        AIContext:
            internal async client — AI 직접 호출 X.
        """
        await self._client.aclose()
