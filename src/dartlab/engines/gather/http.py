"""Gather HTTP 클라이언트 — 도메인별 rate limit + semaphore + retry."""

from __future__ import annotations

import logging
import random
import threading
import time
from urllib.parse import urlparse

import requests

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
# Rate Limiter + Semaphore
# ══════════════════════════════════════


class _DomainRateLimiter:
    """도메인별 sliding window rate limiter. Thread-safe."""

    __slots__ = ("_domain", "_rpm", "_window", "_timestamps", "_lock")

    def __init__(self, domain: str, rpm: int = 30) -> None:
        self._domain = domain
        self._rpm = rpm
        self._window = 60.0
        self._timestamps: list[float] = []
        self._lock = threading.Lock()

    def acquire(self, timeout: float = 30.0) -> None:
        deadline = time.monotonic() + timeout
        while True:
            with self._lock:
                now = time.monotonic()
                cutoff = now - self._window
                self._timestamps = [t for t in self._timestamps if t > cutoff]
                if len(self._timestamps) < self._rpm:
                    self._timestamps.append(now)
                    return
                wait = self._timestamps[0] + self._window - now
            if time.monotonic() > deadline:
                raise RateLimitExceededError(f"{self._domain} RPM={self._rpm} 초과")
            time.sleep(min(wait + 0.05, 1.0))


class _DomainSemaphore:
    """도메인별 동시 연결 제한."""

    __slots__ = ("_semaphore",)

    def __init__(self, max_concurrent: int = 2) -> None:
        self._semaphore = threading.Semaphore(max_concurrent)

    def acquire(self, timeout: float = 30.0) -> bool:
        return self._semaphore.acquire(timeout=timeout)

    def release(self) -> None:
        self._semaphore.release()


# ══════════════════════════════════════
# 통합 HTTP 클라이언트
# ══════════════════════════════════════


class GatherHttpClient:
    """도메인별 rate limit + semaphore + retry + connection pooling.

    - 같은 도메인: RPM 제한 내 순차
    - 다른 도메인: ThreadPoolExecutor 병렬 (caller 측에서)
    - requests.Session 재사용
    - 지수 백오프 재시도 (최대 3회)
    """

    def __init__(self) -> None:
        self._session = requests.Session()
        self._session.headers["Accept"] = "text/html,application/json"
        self._session.headers["Accept-Language"] = "ko-KR,ko;q=0.9,en;q=0.8"
        self._session.headers["User-Agent"] = random.choice(_USER_AGENTS)
        self._limiters: dict[str, _DomainRateLimiter] = {}
        self._semaphores: dict[str, _DomainSemaphore] = {}
        self._lock = threading.Lock()

    def _get_policy(self, domain: str) -> DomainConfig:
        return DOMAIN_POLICY.get(domain, _DEFAULT_POLICY)

    def _get_limiter(self, domain: str) -> _DomainRateLimiter:
        with self._lock:
            if domain not in self._limiters:
                policy = self._get_policy(domain)
                self._limiters[domain] = _DomainRateLimiter(domain, policy.rpm)
            return self._limiters[domain]

    def _get_semaphore(self, domain: str) -> _DomainSemaphore:
        with self._lock:
            if domain not in self._semaphores:
                policy = self._get_policy(domain)
                self._semaphores[domain] = _DomainSemaphore(policy.concurrency)
            return self._semaphores[domain]

    def get(
        self,
        url: str,
        *,
        params: dict | None = None,
        headers: dict | None = None,
        timeout: float | None = None,
        max_retries: int = 3,
    ) -> requests.Response:
        """GET 요청 — rate limit + semaphore + 재시도.

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
            time.sleep(jitter)

            limiter.acquire()
            if not semaphore.acquire(timeout=30.0):
                raise SourceUnavailableError(f"{domain} 동시 연결 제한 초과")
            try:
                req_headers = dict(self._session.headers)
                req_headers["User-Agent"] = random.choice(_USER_AGENTS)
                if headers:
                    req_headers.update(headers)
                resp = self._session.get(url, params=params, headers=req_headers, timeout=req_timeout)
                if resp.status_code == 429:
                    wait = 2**attempt + random.uniform(0.1, 0.5)
                    log.warning("%s 429 rate limited, %.1fs 대기", domain, wait)
                    time.sleep(wait)
                    continue
                if resp.status_code >= 500:
                    wait = 2**attempt + random.uniform(0.1, 0.5)
                    log.warning("%s %d 서버 오류, %.1fs 대기", domain, resp.status_code, wait)
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
                return resp
            except requests.RequestException as exc:
                last_exc = exc
                if attempt < max_retries - 1:
                    time.sleep(2**attempt + random.uniform(0.1, 0.5))
            finally:
                semaphore.release()

        raise SourceUnavailableError(f"{domain} 요청 실패 ({max_retries}회 재시도): {last_exc}")

    def close(self) -> None:
        """HTTP 세션 종료."""
        self._session.close()
