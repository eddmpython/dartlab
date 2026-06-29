"""Gather HTTP 클라이언트 — 도메인별 rate limit + semaphore + retry (async).

다른 도메인: asyncio.gather() 병렬
같은 도메인: asyncio.Semaphore + sliding window rate limiter 순차
"""

from __future__ import annotations

import asyncio
import contextlib
import contextvars
import logging
import random
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

import httpx

from ..types import DomainConfig, RateLimitExceededError, SourceUnavailableError
from . import quota

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
    # 국내 — DART 공시 viewer (무인증)
    "dart.fss.or.kr": DomainConfig(rpm=20, concurrency=2, jitter_min=0.5, jitter_max=2.0),
    # 해외 — 네이버 글로벌
    "api.stock.naver.com": DomainConfig(rpm=30, concurrency=2, jitter_min=0.5, jitter_max=2.0),
    # 해외 — Yahoo v8 Chart API
    "query2.finance.yahoo.com": DomainConfig(rpm=10, concurrency=1, jitter_min=1.0, jitter_max=3.0),
    # 해외 — FMP (fallback)
    "financialmodelingprep.com": DomainConfig(rpm=4, concurrency=1, timeout=15.0, jitter_min=1.0, jitter_max=3.0),
    # 뉴스
    "news.google.com": DomainConfig(rpm=20, concurrency=2, jitter_min=0.3, jitter_max=1.5),
    # 증권사 리서치 보드 — 민감 도메인, 보수적 지터 (스크래핑 예의)
    "securities.miraeasset.com": DomainConfig(rpm=15, concurrency=1, jitter_min=0.5, jitter_max=2.0),
    "m.nhqv.com": DomainConfig(rpm=15, concurrency=1, jitter_min=0.5, jitter_max=2.0),
    "www.myasset.com": DomainConfig(rpm=15, concurrency=1, jitter_min=0.5, jitter_max=2.0),
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

_threadLoop: asyncio.AbstractEventLoop | None = None
_threadPool = ThreadPoolExecutor(max_workers=1)
_activeProxy: contextvars.ContextVar[str | None] = contextvars.ContextVar("dartlabGatherProxy", default=None)
# 프록시 풀(여러 프록시 회전) — useProxyPool 이 itertools.cycle 을 세팅, _resolveProxy 가 요청마다 회전.
_activeProxyPool: contextvars.ContextVar[object | None] = contextvars.ContextVar("dartlabGatherProxyPool", default=None)


def _getThreadLoop() -> asyncio.AbstractEventLoop:
    """별도 스레드 전용 persistent event loop 반환.

    기존 loop가 없거나 닫혀 있으면 새로 생성한다.
    loop를 닫지 않으므로 httpx connection pool 재사용이 가능하다.

    Returns
    -------
    asyncio.AbstractEventLoop
        스레드 전용 event loop 인스턴스.
    """
    global _threadLoop
    if _threadLoop is None or _threadLoop.is_closed():
        _threadLoop = asyncio.new_event_loop()
    return _threadLoop


def _runInThreadLoop(coro):
    """persistent loop에서 코루틴을 동기적으로 실행.

    loop를 닫지 않으므로 이후 호출에서도 동일 loop를 재사용한다.

    Parameters
    ----------
    coro : Coroutine
        실행할 코루틴 객체.

    Returns
    -------
    Any
        코루틴의 반환값. 타입은 전달된 코루틴에 따라 다르다.
    """
    loop = _getThreadLoop()
    return loop.run_until_complete(coro)


def runAsync(coro):
    """코루틴을 동기 컨텍스트에서 안전하게 실행.

    이미 event loop가 실행 중이면(Marimo/FastAPI 등) 별도 스레드의
    persistent loop에서 실행. httpx connection pool 재사용 가능.

    Parameters
    ----------
    coro : Coroutine
        실행할 코루틴 객체.

    Returns
    -------
    Any
        코루틴의 반환값. 타입은 전달된 코루틴에 따라 다르다.

    Raises
    ------
    없음
        코루틴 내부 예외는 호출자에게 전파.

    Example
    -------
    >>> result = runAsync(coro)

    Capabilities
    ------------
    persistent thread loop 사용 — Marimo/FastAPI 환경 호환.
    AIContext: 동기 컨텍스트에서 async 코드 호출 진입.
    Guide: 이미 loop 실행 중이면 ThreadPoolExecutor 위임.
    When: notebook / CLI / Jupyter 환경에서 async fetch 호출 시.
    How: ``asyncio.get_running_loop()`` 확인 → 분기 (direct vs thread submit).

    Requires
    --------
    ``_threadPool`` (ThreadPoolExecutor) + ``_threadLoop`` (persistent loop).

    See Also
    --------
    GatherHttpClient : 본 함수의 caller.
    """
    # coro 누수 차단 — 어떤 경로로 raise 되든 coro.close() 보장.
    # (이전: _getThreadLoop / threadPool 실패 시 coro 가 await 안 되어 RuntimeWarning 발생)
    ctx = contextvars.copy_context()
    try:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            # loop 없음 — 직접 실행 (persistent loop 사용)
            return ctx.run(_runInThreadLoop, coro)
        # 이미 loop 실행 중 → 별도 스레드의 persistent loop
        return _threadPool.submit(lambda: ctx.run(_runInThreadLoop, coro)).result()
    except BaseException:
        # coro 가 await 됐다면 close 는 no-op. await 전 raise 면 cleanup.
        try:
            coro.close()
        except Exception:  # noqa: BLE001
            pass
        raise


# ══════════════════════════════════════
# Async Rate Limiter + Semaphore
# ══════════════════════════════════════


class _AsyncRateLimiter:
    """도메인별 sliding window rate limiter + 최소 간격 (async)."""

    __slots__ = ("_domain", "_rpm", "_min_interval", "_window", "_timestamps", "_lock")

    def __init__(self, domain: str, rpm: int = 30, minInterval: float = 0.0) -> None:
        self._domain = domain
        self._rpm = rpm
        self._min_interval = minInterval
        self._window = 60.0
        self._timestamps: list[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self, timeout: float = 30.0) -> None:
        """속도 제한 슬롯 획득 (윈도우 내 최대 요청 수 준수).

        Capabilities: sliding window rate limiter + 최소 간격 보장.
        AIContext: GatherHttpClient 의 도메인별 rate limit 진입.
        Guide: timeout 초과 시 RateLimitExceededError raise.
        When: GatherHttpClient.get/post 의 매 요청 직전.
        How: lock → window 비교 + min_interval 대기 → timestamp append.

        Parameters
        ----------
        timeout : float
            슬롯 획득 대기 최대 시간 (초). 기본 30.0.

        Raises
        ------
        RateLimitExceededError
            timeout 내 슬롯 획득 실패 시.

        Requires
        --------
        ``self._lock`` + ``self._timestamps`` + ``self._rpm`` + ``self._window``.

        Example
        -------
        >>> await limiter.acquire(timeout=10.0)

        See Also
        --------
        GatherHttpClient.get · post : 본 메서드 caller.
        """
        deadline = time.monotonic() + timeout
        while True:
            async with self._lock:
                now = time.monotonic()
                # 최소 간격 대기 — 마지막 요청 이후 min_interval 경과 필수
                if self._min_interval > 0 and self._timestamps:
                    elapsed = now - self._timestamps[-1]
                    if elapsed < self._min_interval:
                        wait_interval = self._min_interval - elapsed
                        # lock 해제 후 대기
                        break_for_interval = True
                    else:
                        break_for_interval = False
                else:
                    break_for_interval = False

                if break_for_interval:
                    pass  # lock 밖에서 대기
                else:
                    cutoff = now - self._window
                    self._timestamps = [t for t in self._timestamps if t > cutoff]
                    if len(self._timestamps) < self._rpm:
                        self._timestamps.append(now)
                        return
                    wait_interval = self._timestamps[0] + self._window - now

            if time.monotonic() > deadline:
                raise RateLimitExceededError(f"{self._domain} RPM={self._rpm} 초과")
            await asyncio.sleep(min(wait_interval + 0.05, self._min_interval or 1.0))


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
        self._client = self._makeClient()
        self._proxyClients: dict[str, httpx.AsyncClient] = {}
        self._limiters: dict[str, _AsyncRateLimiter] = {}
        self._semaphores: dict[str, asyncio.Semaphore] = {}

    def _makeClient(self, *, proxy: str | None = None) -> httpx.AsyncClient:
        """공통 옵션으로 httpx AsyncClient 생성."""
        return httpx.AsyncClient(
            timeout=httpx.Timeout(10.0, connect=5.0),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
            headers={
                "Accept": "text/html,application/json",
                "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
                "User-Agent": random.choice(_USER_AGENTS),
            },
            follow_redirects=True,
            proxy=proxy,
        )

    def _getClientForProxy(self, proxy: str | None) -> httpx.AsyncClient:
        """proxy 별 connection pool 재사용. None 이면 기본 client."""
        if not proxy:
            return self._client
        if proxy not in self._proxyClients:
            self._proxyClients[proxy] = self._makeClient(proxy=proxy)
        return self._proxyClients[proxy]

    @contextlib.contextmanager
    def useProxy(self, proxy: str | None):
        """현재 gather 호출 범위에 사용자 프록시를 적용한다.

        Capabilities:
            - ``dartlab.gather(..., proxy=...)`` 의 공통 HTTP 적용 범위 제공.
            - ``contextvars`` 로 proxy URL 을 저장해 nested async 호출과
              ``runAsync`` thread-loop 경로까지 전파.
            - proxy URL 별 ``httpx.AsyncClient`` connection pool 재사용.

        AIContext:
            AI 역할: 공개 답변에서는 ``dartlab.gather`` 의 공통 옵션으로만
            설명한다. 내부 HTTP client 를 직접 열거나 ``requests`` 호출로
            우회하는 안내는 하지 않는다.

        Guide:
            이 context manager 는 네트워크 경로 선택만 담당한다. rate-limit,
            semaphore, jitter, retry, quota guard 는 ``get``/``post`` 경로에서
            기존과 동일하게 적용된다.

        When:
            ``GatherEntry._run`` 이 ``proxy`` kwarg 를 받은 gather 호출 범위를
            실행할 때.

        How:
            ``_activeProxy`` contextvar 에 URL 을 기록하고, ``get``/``post`` 가
            명시 proxy 가 없을 때 ``_resolveProxy`` 로 현재 값을 읽는다.

        Args:
            proxy: 사용자 제공 HTTP(S) 프록시 URL. None 또는 빈 값이면 기본
                direct client 를 그대로 사용한다.

        Returns:
            context manager — ``with client.useProxy(proxy): ...`` 블록 안에서
            GatherHttpClient GET/POST 요청에 proxy context 를 제공한다.

        Raises:
            없음. contextvar set/reset 만 수행하며, 실제 네트워크 오류는
            ``get``/``post`` 호출에서 ``SourceUnavailableError`` 로 처리된다.

        Example:
            >>> client = GatherHttpClient()
            >>> with client.useProxy("http://user:pass@host:port"):
            ...     response = runAsync(client.get("https://example.com"))

        Requires:
            ``contextvars`` 런타임 + ``GatherHttpClient`` 인스턴스. proxy URL 의
            유효성 검증과 인증 실패 처리는 httpx transport 에 위임한다.

        SeeAlso:
            GatherEntry._run : public ``proxy`` kwarg 를 이 context 로 연결.
            get : context proxy 를 적용하는 GET 요청.
            post : context proxy 를 적용하는 POST 요청.

        LLM Specifications:
            AntiPatterns:
                - proxy 를 rate-limit 우회 기능으로 설명.
                - 프록시 인증정보를 로그/답변/문서에 그대로 노출.
                - ``dartlab.gather`` 를 거치지 않고 내부 client 사용법을 공개 계약으로 안내.
            OutputSchema:
                - context manager : object — with 블록에서 proxy context 제공
            Prerequisites:
                - 사용자 제공 HTTP(S) proxy URL.
                - 요청 경로가 ``GatherHttpClient.get/post`` 를 사용해야 함.
            Freshness:
                데이터 freshness 를 바꾸지 않는다. 네트워크 경로만 변경한다.
            Dataflow:
                GatherEntry._run(proxy=...) → useProxy → GatherHttpClient.get/post → httpx.AsyncClient(proxy=...).
            TargetMarkets:
                - KR
                - US
                - GLOBAL (GatherHttpClient 경유 source 한정)
        """
        if not proxy:
            yield
            return
        token = _activeProxy.set(proxy)
        try:
            yield
        finally:
            _activeProxy.reset(token)

    @contextlib.contextmanager
    def useProxyPool(self, proxies: list[str] | None):
        """현재 gather 호출 범위에 프록시 풀(회전)을 적용 — 요청마다 다음 프록시 사용.

        Sig: ``with client.useProxyPool([p1, p2, ...]): ...``

        Capabilities: 여러 프록시를 round-robin 회전 → 동시 요청이 서로 다른 IP 로 분산.
            rate limit/semaphore 가 (도메인×프록시)별이라 프록시 수만큼 throughput 확장.
        AIContext: ``dartlab.gather(..., proxies=[...])`` 의 공통 HTTP 적용 범위. proxy 우회 기능으로
            설명 금지, 인증정보 노출 금지.
        Guide: 프록시 *미지정*(None/빈 리스트)이면 기본 direct 단일 client + 도메인 단위 rate limit
            = 안전 직렬(기존 동작 불변). 풀 지정 시에만 회전·분산.
        When: ``GatherEntry._run`` 이 ``proxies`` kwarg 를 받은 gather 호출 범위를 실행할 때.
        How: ``_activeProxyPool`` contextvar 에 ``itertools.cycle(proxies)`` 를 세팅하고,
            ``get``/``post`` 가 명시 proxy 없을 때 ``_resolveProxy`` 로 다음 프록시를 회전 획득.

        Args:
            proxies: HTTP(S) 프록시 URL 리스트. None/빈 리스트면 기본(direct) — 안전 직렬(기존 동작).

        Returns:
            context manager — 블록 안 GET/POST 가 풀에서 회전. proxy 인증정보는 로그/답변 노출 금지.

        Raises:
            없음. contextvar set/reset 만 수행 — 네트워크 오류는 get/post 에서 처리.

        Example:
            >>> with client.useProxyPool(["http://a:1", "http://b:1"]):
            ...     runAsync(crawl())

        Requires:
            ``contextvars`` 런타임 + ``GatherHttpClient`` 인스턴스. 풀의 각 URL 유효성/인증은
            httpx transport 에 위임.

        SeeAlso:
            useProxy : 단일 프록시 적용.
            _resolveProxy : 요청별 proxy 결정(명시 > 풀 회전 > 단일).
            GatherEntry._run : 공개 ``proxies`` kwarg 를 이 context 로 연결.
        """
        if not proxies:
            yield
            return
        import itertools

        token = _activeProxyPool.set(itertools.cycle(list(proxies)))
        try:
            yield
        finally:
            _activeProxyPool.reset(token)

    def _resolveProxy(self, proxy: str | None) -> str | None:
        """요청별 proxy → 없으면 풀(회전) → 없으면 현재 gather 호출 범위의 단일 proxy."""
        if proxy:
            return proxy
        pool = _activeProxyPool.get()
        if pool is not None:
            return next(pool)  # type: ignore[call-overload]
        return _activeProxy.get()

    def _getPolicy(self, domain: str) -> DomainConfig:
        """도메인별 정책 반환. 미등록 도메인은 기본 정책 사용.

        Parameters
        ----------
        domain : str
            호스트명 (예: ``"m.stock.naver.com"``).

        Returns
        -------
        DomainConfig
            rpm : int — 분당 최대 요청 수 (회)
            concurrency : int — 동시 연결 제한 수 (개)
            timeout : float — 요청 타임아웃 (초)
            jitter_min : float — 최소 지터 딜레이 (초)
            jitter_max : float — 최대 지터 딜레이 (초)
        """
        return DOMAIN_POLICY.get(domain, _DEFAULT_POLICY)

    def _getLimiter(self, domain: str, proxy: str | None = None) -> _AsyncRateLimiter:
        """(도메인×프록시)별 rate limiter (lazy). proxy=None 이면 도메인 단위(기존 안전 기본).

        Parameters
        ----------
        domain : str
            호스트명.
        proxy : str | None
            적용 프록시. 풀 회전 시 프록시마다 독립 RPM budget → throughput 확장.

        Returns
        -------
        _AsyncRateLimiter
            해당 (도메인, 프록시) 의 sliding window rate limiter.
        """
        key = domain if not proxy else f"{domain}|{proxy}"
        if key not in self._limiters:
            policy = self._getPolicy(domain)
            self._limiters[key] = _AsyncRateLimiter(key, policy.rpm, policy.minInterval)
        return self._limiters[key]

    def _getSemaphore(self, domain: str, proxy: str | None = None) -> asyncio.Semaphore:
        """(도메인×프록시)별 동시 연결 세마포어 (lazy). proxy=None 이면 도메인 단위(기존 안전 기본).

        Parameters
        ----------
        domain : str
            호스트명.
        proxy : str | None
            적용 프록시. 풀 회전 시 프록시마다 독립 동시성.

        Returns
        -------
        asyncio.Semaphore
            해당 (도메인, 프록시) 의 동시 요청 수 제한 세마포어.
        """
        key = domain if not proxy else f"{domain}|{proxy}"
        if key not in self._semaphores:
            policy = self._getPolicy(domain)
            self._semaphores[key] = asyncio.Semaphore(policy.concurrency)
        return self._semaphores[key]

    async def get(
        self,
        url: str,
        *,
        params: dict | None = None,
        headers: dict | None = None,
        timeout: float | None = None,
        maxRetries: int = 3,
        proxy: str | None = None,
    ) -> httpx.Response:
        """GET 요청 — rate limit + semaphore + 재시도 (async).

        Capabilities: 도메인별 jitter + rate limit + semaphore + 429/5xx 지수 backoff retry.
        AIContext: gather 의 모든 외부 GET 호출 단일 진입점 (naver/yahoo/krx/etc).
        Guide: 도메인별 RPM/concurrency/jitter 자동 적용.
        When: gather domains/* 의 모든 fetch 호출 시.
        How: jitter → limiter.acquire → semaphore → httpx GET → 429/5xx retry.

        Parameters
        ----------
        url : str
            요청 URL.
        params : dict | None
            쿼리 파라미터.
        headers : dict | None
            추가 HTTP 헤더.
        timeout : float | None
            요청 타임아웃 (초). None이면 도메인 정책 기본값.
        max_retries : int
            최대 재시도 횟수 (회). 기본 3.
        proxy : str | None
            사용자 제공 HTTP(S) 프록시 URL. 예: ``"http://user:pass@host:port"``.

        Returns
        -------
        httpx.Response
            HTTP 응답 객체. status_code, text, json() 등 사용 가능.

        Raises
        ------
        SourceUnavailableError
            모든 재시도 실패 시.

        Requires
        --------
        ``DOMAIN_POLICY`` 등록 (미등록 도메인은 _DEFAULT_POLICY).

        Example
        -------
        >>> resp = await client.get("https://example.com/api")

        See Also
        --------
        post : POST 변형.
        _AsyncRateLimiter.acquire : rate limit slot 획득.
        """
        domain = urlparse(url).netloc
        policy = self._getPolicy(domain)
        resolvedProxy = self._resolveProxy(proxy)
        limiter = self._getLimiter(domain, resolvedProxy)
        semaphore = self._getSemaphore(domain, resolvedProxy)
        req_timeout = timeout or policy.timeout
        req_client = self._getClientForProxy(resolvedProxy)

        # Sprint 1 PR2 — 일일 quota 사전 차단 (80% 도달 시 fallback chain 으로 즉시 전환)
        if not quota.checkDaily(domain):
            log.warning("%s 일일 quota 80%% 초과 — 사전 차단", domain)
            raise SourceUnavailableError(f"{domain} 일일 quota 80% 초과 (DAILY_LIMITS)")

        last_exc: Exception | None = None
        for attempt in range(maxRetries):
            # 랜덤 지터: 동일 도메인 연속 호출 시 버스트 패턴 방지
            jitter = random.uniform(policy.jitter_min, policy.jitter_max)
            await asyncio.sleep(jitter)

            await limiter.acquire()
            async with semaphore:
                try:
                    req_headers = {"User-Agent": random.choice(_USER_AGENTS)}
                    if headers:
                        req_headers.update(headers)
                    resp = await req_client.get(
                        url,
                        params=params,
                        headers=req_headers,
                        timeout=req_timeout,
                    )
                    quota.record(domain)  # 응답 받음 = quota 1 회 소비
                    if resp.status_code == 429:
                        base = 2**attempt
                        wait = base * (attempt + 1) + random.uniform(0.5, 2.0)
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
                    quota.record(domain)  # 네트워크 실패도 vendor 측 cap 소비로 간주
                    last_exc = exc
                    if attempt < maxRetries - 1:
                        await asyncio.sleep(2**attempt + random.uniform(0.1, 0.5))

        raise SourceUnavailableError(f"{domain} 요청 실패 ({maxRetries}회 재시도): {last_exc}")

    async def post(
        self,
        url: str,
        *,
        data: dict | None = None,
        json: dict | None = None,
        headers: dict | None = None,
        timeout: float | None = None,
        maxRetries: int = 3,
        proxy: str | None = None,
    ) -> httpx.Response:
        """POST 요청 -- rate limit + semaphore + 재시도 (async).

        Capabilities: GET 동행 — POST 메서드 + form/json body 지원.
        AIContext: KRX OpenAPI 같은 POST 전용 도메인 진입.
        Guide: data (form) 또는 json 둘 중 하나만 사용 권장.
        When: KRX bulk fetch / 인증 토큰 POST 등 시.
        How: jitter → limiter → semaphore → httpx POST → 429/5xx retry.

        Parameters
        ----------
        url : str
            요청 URL.
        data : dict | None
            form-encoded 요청 본문.
        json : dict | None
            JSON 요청 본문.
        headers : dict | None
            추가 HTTP 헤더.
        timeout : float | None
            요청 타임아웃 (초). None이면 도메인 정책 기본값.
        max_retries : int
            최대 재시도 횟수 (회). 기본 3.
        proxy : str | None
            사용자 제공 HTTP(S) 프록시 URL.

        Returns
        -------
        httpx.Response
            HTTP 응답 객체. status_code, text, json() 등 사용 가능.

        Raises
        ------
        SourceUnavailableError
            모든 재시도 실패 시.

        Requires
        --------
        DOMAIN_POLICY 등록 + httpx.AsyncClient.

        Example
        -------
        >>> resp = await client.post("https://example.com/api", json={"k": "v"})

        See Also
        --------
        get : GET 변형.
        """
        domain = urlparse(url).netloc
        policy = self._getPolicy(domain)
        resolvedProxy = self._resolveProxy(proxy)
        limiter = self._getLimiter(domain, resolvedProxy)
        semaphore = self._getSemaphore(domain, resolvedProxy)
        req_timeout = timeout or policy.timeout
        req_client = self._getClientForProxy(resolvedProxy)

        # Sprint 1 PR2 — 일일 quota 사전 차단 (POST 동행)
        if not quota.checkDaily(domain):
            log.warning("%s 일일 quota 80%% 초과 — POST 사전 차단", domain)
            raise SourceUnavailableError(f"{domain} 일일 quota 80% 초과 (DAILY_LIMITS)")

        last_exc: Exception | None = None
        for attempt in range(maxRetries):
            jitter = random.uniform(policy.jitter_min, policy.jitter_max)
            await asyncio.sleep(jitter)

            await limiter.acquire()
            async with semaphore:
                try:
                    req_headers = {"User-Agent": random.choice(_USER_AGENTS)}
                    if headers:
                        req_headers.update(headers)
                    resp = await req_client.post(
                        url,
                        data=data,
                        json=json,
                        headers=req_headers,
                        timeout=req_timeout,
                    )
                    quota.record(domain)
                    if resp.status_code == 429:
                        base = 2**attempt
                        wait = base * (attempt + 1) + random.uniform(0.5, 2.0)
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
                    quota.record(domain)
                    last_exc = exc
                    if attempt < maxRetries - 1:
                        await asyncio.sleep(2**attempt + random.uniform(0.1, 0.5))

        raise SourceUnavailableError(f"{domain} POST 요청 실패 ({maxRetries}회 재시도): {last_exc}")

    async def close(self) -> None:
        """HTTP 클라이언트 종료. 내부 httpx.AsyncClient의 커넥션 풀을 정리.

        Capabilities: httpx.AsyncClient.aclose 위임 — connection pool 정리.
        AIContext: GatherHttpClient 리소스 회수 — Gather.close 의 backend.
        Guide: async — await 필요. context manager exit 위치 적절.
        When: dartlab 종료 / 명시 cleanup 시.
        How: ``await self._client.aclose()``.

        Returns
        -------
        None

        Raises
        ------
        없음
            aclose 는 graceful.

        Requires
        --------
        ``self._client`` (httpx.AsyncClient) 가용.

        Example
        -------
        >>> await client.close()

        See Also
        --------
        engine.Gather.close : 본 메서드 caller.
        """
        await self._client.aclose()
        for client in self._proxyClients.values():
            await client.aclose()
        self._proxyClients.clear()
