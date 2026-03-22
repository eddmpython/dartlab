"""Gather HTTP 클라이언트 — 도메인별 rate limit + semaphore + retry (async).

다른 도메인: asyncio.gather() 병렬
같은 도메인: asyncio.Semaphore + sliding window rate limiter 순차
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

import httpx

from .types import DomainConfig, RateLimitExceededError, SourceUnavailableError

log = logging.getLogger(__name__)

# ══════════════════════════════════════
# 도메인별 정책 레지스트리
# ══════════════════════════════════════

DOMAIN_POLICY: dict[str, DomainConfig] = {
    # 국내 — 민감 도메인, 넉넉한 지터
    "m.stock.naver.com": DomainConfig(rpm=30, concurrency=2, jitter_min=0.5, jitter_max=2.0),
    "finance.naver.com": DomainConfig(rpm=30, concurrency=2, jitter_min=0.5, jitter_max=2.0),
    "data-api.krx.co.kr": DomainConfig(rpm=30, concurrency=2, jitter_min=0.3, jitter_max=1.5),
    "ecos.bok.or.kr": DomainConfig(rpm=30, concurrency=2, jitter_min=0.3, jitter_max=1.5),
    # 해외 — 상대적 관대
    "query1.finance.yahoo.com": DomainConfig(rpm=20, concurrency=2, jitter_min=0.2, jitter_max=1.0),
    "query2.finance.yahoo.com": DomainConfig(rpm=20, concurrency=2, jitter_min=0.2, jitter_max=1.0),
    "financialmodelingprep.com": DomainConfig(rpm=4, concurrency=1, timeout=15.0, jitter_min=1.0, jitter_max=3.0),
}

_DEFAULT_POLICY = DomainConfig(rpm=30, concurrency=2)

_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15",
]


# ══════════════════════════════════════
# Event loop 안전 실행 헬퍼
# ══════════════════════════════════════

_thread_pool = ThreadPoolExecutor(max_workers=1)


def run_async(coro):
    """코루틴을 동기 컨텍스트에서 안전하게 실행.

    이미 event loop가 실행 중이면(FastAPI/Slack 등) 별도 스레드에서 새 loop 생성.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    # 이미 loop 실행 중 → 별도 스레드
    return _thread_pool.submit(asyncio.run, coro).result()


# ══════════════════════════════════════
# Async Rate Limiter + Semaphore
# ══════════════════════════════════════


class _AsyncRateLimiter:
    """도메인별 sliding window rate limiter (async)."""

    __slots__ = ("_domain", "_rpm", "_window", "_timestamps", "_lock")

    def __init__(self, domain: str, rpm: int = 30) -> None:
        self._domain = domain
        self._rpm = rpm
        self._window = 60.0
        self._timestamps: list[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self, timeout: float = 30.0) -> None:
        deadline = time.monotonic() + timeout
        while True:
            async with self._lock:
                now = time.monotonic()
                cutoff = now - self._window
                self._timestamps = [t for t in self._timestamps if t > cutoff]
                if len(self._timestamps) < self._rpm:
                    self._timestamps.append(now)
                    return
                wait = self._timestamps[0] + self._window - now
            if time.monotonic() > deadline:
                raise RateLimitExceededError(f"{self._domain} RPM={self._rpm} 초과")
            await asyncio.sleep(min(wait + 0.05, 1.0))


# ══════════════════════════════════════
# 통합 HTTP 클라이언트 (async)
# ══════════════════════════════════════


class GatherHttpClient:
    """도메인별 rate limit + semaphore + retry + connection pooling.

    - 같은 도메인: RPM 제한 내 + asyncio.Semaphore 동시 연결 제한
    - 다른 도메인: asyncio.gather()로 진짜 병렬 (caller 측)
    - httpx.AsyncClient로 커넥션 풀링
    - 지수 백오프 재시도 (최대 3회)
    """

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0, connect=5.0),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
            headers={
                "Accept": "text/html,application/json",
                "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
                "User-Agent": random.choice(_USER_AGENTS),
            },
            follow_redirects=True,
        )
        self._limiters: dict[str, _AsyncRateLimiter] = {}
        self._semaphores: dict[str, asyncio.Semaphore] = {}

    def _get_policy(self, domain: str) -> DomainConfig:
        return DOMAIN_POLICY.get(domain, _DEFAULT_POLICY)

    def _get_limiter(self, domain: str) -> _AsyncRateLimiter:
        if domain not in self._limiters:
            policy = self._get_policy(domain)
            self._limiters[domain] = _AsyncRateLimiter(domain, policy.rpm)
        return self._limiters[domain]

    def _get_semaphore(self, domain: str) -> asyncio.Semaphore:
        if domain not in self._semaphores:
            policy = self._get_policy(domain)
            self._semaphores[domain] = asyncio.Semaphore(policy.concurrency)
        return self._semaphores[domain]

    async def get(
        self,
        url: str,
        *,
        params: dict | None = None,
        headers: dict | None = None,
        timeout: float | None = None,
        max_retries: int = 3,
    ) -> httpx.Response:
        """GET 요청 — rate limit + semaphore + 재시도 (async).

        Raises:
            SourceUnavailableError: 모든 재시도 실패.
        """
        domain = urlparse(url).netloc
        policy = self._get_policy(domain)
        limiter = self._get_limiter(domain)
        semaphore = self._get_semaphore(domain)
        req_timeout = timeout or policy.timeout

        last_exc: Exception | None = None
        for attempt in range(max_retries):
            # 랜덤 지터: 동일 도메인 연속 호출 시 버스트 패턴 방지
            jitter = random.uniform(policy.jitter_min, policy.jitter_max)
            await asyncio.sleep(jitter)

            await limiter.acquire()
            async with semaphore:
                try:
                    req_headers = {"User-Agent": random.choice(_USER_AGENTS)}
                    if headers:
                        req_headers.update(headers)
                    resp = await self._client.get(
                        url,
                        params=params,
                        headers=req_headers,
                        timeout=req_timeout,
                    )
                    if resp.status_code == 429:
                        wait = 2**attempt + random.uniform(0.1, 0.5)
                        log.warning("%s 429 rate limited, %.1fs 대기", domain, wait)
                        await asyncio.sleep(wait)
                        continue
                    if resp.status_code >= 500:
                        wait = 2**attempt + random.uniform(0.1, 0.5)
                        log.warning("%s %d 서버 오류, %.1fs 대기", domain, resp.status_code, wait)
                        await asyncio.sleep(wait)
                        continue
                    resp.raise_for_status()
                    return resp
                except httpx.HTTPError as exc:
                    last_exc = exc
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2**attempt + random.uniform(0.1, 0.5))

        raise SourceUnavailableError(f"{domain} 요청 실패 ({max_retries}회 재시도): {last_exc}")

    async def close(self) -> None:
        """HTTP 클라이언트 종료."""
        await self._client.aclose()
