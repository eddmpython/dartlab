"""FRED API HTTP 클라이언트 — rate limit + retry + multi-key rotation."""

from __future__ import annotations

import logging
import time

import httpx

from dartlab.core.providers.dataCredentials import getKey

from .types import AuthenticationError, FredError, RateLimitError, SeriesNotFoundError

log = logging.getLogger(__name__)

_BASE_URL = "https://api.stlouisfed.org/fred"

# 120 requests per minute
_RATE_LIMIT_RPM = 120
_RATE_LIMIT_WINDOW = 60.0


class FredClient:
    """FRED REST API 클라이언트.

    - 환경변수 ``FRED_API_KEY`` 에서 키 해석 (콤마 구분 multi-key 지원)
    - 120 RPM 레이트 리밋
    - 429/5xx 지수 백오프 재시도 (최대 3회)
    """

    def __init__(self, apiKey: str | None = None) -> None:
        raw = getKey("fred", apiKey) or ""
        self._keys: list[str] = [k.strip() for k in raw.split(",") if k.strip()]
        if not self._keys:
            raise AuthenticationError(
                "FRED API 키가 없습니다. "
                "환경변수 FRED_API_KEY를 설정하거나 Fred(api_key=...) 인자를 전달하세요.\n"
                "무료 발급: https://fred.stlouisfed.org/docs/api/api_key.html"
            )
        self._key_idx = 0
        self._session = httpx.Client(headers={"User-Agent": "dartlab-fred/1.0"}, follow_redirects=True)
        # sliding window rate limiter
        self._timestamps: list[float] = []

    # ── public ──

    def get(self, endpoint: str, **params) -> dict:
        """GET 요청 → JSON dict.

        Capabilities: FRED REST GET + 120 RPM rate limit + 429/5xx 지수 backoff retry + key rotation.
        AIContext: FRED 모든 series/category/release 호출의 단일 HTTP 진입점.
        Guide: api_key 환경변수 (multi-key 콤마 분리) — 429 시 자동 rotate.
        When: series/catalog/transform 모든 FRED API 호출 시.
        How: rate limit 대기 → GET → 200 OK / 429 retry / 4xx raise / 5xx retry.

        Parameters
        ----------
        endpoint : str
            FRED 엔드포인트 경로 (예: ``/series/observations``).
        **params
            쿼리 파라미터 (api_key, file_type 자동 추가).

        Returns
        -------
        dict
            FRED API JSON 응답 딕셔너리.

        Raises
        ------
        SeriesNotFoundError
            시리즈를 찾을 수 없을 때.
        AuthenticationError
            API 키가 유효하지 않을 때 (403).
        FredError
            기타 API 오류 또는 3회 재시도 초과.

        Requires
        --------
        ``FRED_API_KEY`` 환경변수 (또는 ``apiKey=`` 인자) — 무료 발급
        ``https://fred.stlouisfed.org/docs/api/api_key.html``.

        Example
        -------
        >>> c = FredClient()
        >>> data = c.get("/series/observations", series_id="GDP")

        See Also
        --------
        close : 세션 정리.
        series.fetchSeries · catalog : 본 메서드 caller.
        """
        params.setdefault("file_type", "json")
        params["api_key"] = self._resolveKey()
        url = f"{_BASE_URL}{endpoint}"

        last_exc: Exception | None = None
        for attempt in range(3):
            self._rateLimit()
            try:
                resp = self._session.get(url, params=params, timeout=30)
            except httpx.HTTPError as exc:
                last_exc = exc
                self._backoff(attempt)
                continue

            if resp.status_code == 200:
                try:
                    data = resp.json()
                except ValueError as exc:
                    raise FredError("FRED 응답 JSON을 해석할 수 없습니다") from exc
                if not isinstance(data, dict):
                    raise FredError("FRED 응답 schema가 객체가 아닙니다")
                return data

            if resp.status_code == 429:
                log.warning("FRED rate limit hit, backing off (attempt %d)", attempt + 1)
                self._rotateKey()
                self._backoff(attempt)
                last_exc = RateLimitError(f"429 Too Many Requests (attempt {attempt + 1})")
                continue

            if resp.status_code in (500, 502, 503, 504):
                log.warning("FRED server error %d, retrying", resp.status_code)
                self._backoff(attempt)
                last_exc = FredError(f"Server error {resp.status_code}")
                continue

            # 400 계열 — 즉시 실패
            body = resp.text
            if "Bad Request" in body and "series_id" in body.lower():
                raise SeriesNotFoundError(f"시리즈를 찾을 수 없습니다: {params.get('series_id', '?')}")
            if resp.status_code == 403:
                raise AuthenticationError("FRED API 키가 유효하지 않습니다.")
            raise FredError(f"FRED API 오류 {resp.status_code}: {body[:200]}")

        if isinstance(last_exc, FredError):
            raise last_exc
        if last_exc is not None:
            raise FredError("FRED API 요청 실패 (3회 재시도 초과)") from last_exc
        raise FredError("FRED API 요청 실패 (3회 재시도 초과)")

    def close(self) -> None:
        """세션 닫기.

        Capabilities: httpx.Client.close 위임.
        AIContext: FredClient 리소스 정리 — context exit / 명시 cleanup 진입.
        Guide: idempotent — 두 번 호출 graceful.
        When: dartlab 종료 / Fred facade close 시.
        How: ``self._session.close()``.

        Returns
        -------
        None

        Raises
        ------
        없음
            httpx 세션 close 는 graceful.

        Requires
        --------
        ``self._session`` (httpx.Client) 가용.

        Example
        -------
        >>> c = FredClient()
        >>> c.close()

        See Also
        --------
        facade.Fred.close : 본 메서드의 caller.
        """
        self._session.close()

    # ── internal ──

    def _resolveKey(self) -> str:
        """현재 인덱스의 API 키 반환.

        Returns
        -------
        str
            현재 활성 FRED API 키.
        """
        return self._keys[self._key_idx % len(self._keys)]

    def _rotateKey(self) -> None:
        """다음 API 키로 로테이션 (multi-key 지원).

        Returns
        -------
        None
            키가 1개뿐이면 아무 동작 없음.
        """
        if len(self._keys) > 1:
            self._key_idx = (self._key_idx + 1) % len(self._keys)

    def _rateLimit(self) -> None:
        """슬라이딩 윈도우 120 RPM 제한.

        Returns
        -------
        None
            윈도우 초과 시 대기 후 반환.
        """
        now = time.monotonic()
        cutoff = now - _RATE_LIMIT_WINDOW
        self._timestamps = [t for t in self._timestamps if t > cutoff]
        if len(self._timestamps) >= _RATE_LIMIT_RPM:
            wait = self._timestamps[0] - cutoff
            if wait > 0:
                log.debug("Rate limit: sleeping %.2fs", wait)
                time.sleep(wait)
        self._timestamps.append(time.monotonic())

    @staticmethod
    def _backoff(attempt: int) -> None:
        """지수 백오프.

        Parameters
        ----------
        attempt : int
            현재 재시도 횟수 (0부터). 대기 시간 = min(2^attempt, 8) (초).

        Returns
        -------
        None
        """
        delay = min(2**attempt, 8)
        time.sleep(delay)
