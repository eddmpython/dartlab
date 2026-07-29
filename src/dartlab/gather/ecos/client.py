"""ECOS REST API 클라이언트 — rate limit + retry."""

from __future__ import annotations

import logging
import time

import httpx

from dartlab.core.providers.dataCredentials import getKey

from .types import AuthenticationError, EcosError, RateLimitError

log = logging.getLogger(__name__)

_BASE_URL = "https://ecos.bok.or.kr/api"

# 30 RPM (gather/http.py 도메인 정책과 일치)
_RATE_LIMIT_RPM = 30
_RATE_LIMIT_WINDOW = 60.0


class EcosClient:
    """한국은행 ECOS REST API 클라이언트.

    - 환경변수 ``ECOS_API_KEY`` 에서 키 해석
    - 30 RPM 레이트 리밋
    - 5xx 지수 백오프 재시도 (최대 3회)
    - 무료 발급: https://ecos.bok.or.kr/api/#/
    """

    def __init__(self, apiKey: str | None = None) -> None:
        raw = getKey("ecos", apiKey) or ""
        if not raw:
            raise AuthenticationError(
                "ECOS API 키가 없습니다. "
                "환경변수 ECOS_API_KEY를 설정하거나 Ecos(apiKey=...) 인자를 전달하세요.\n"
                "무료 발급: https://ecos.bok.or.kr/api/#/"
            )
        self._key = raw.strip()
        self._session = httpx.Client(headers={"User-Agent": "dartlab-ecos/1.0"}, follow_redirects=True)
        self._timestamps: list[float] = []

    def get(
        self,
        tableCode: str,
        freq: str,
        startDate: str,
        endDate: str,
        itemCode: str = "",
        *,
        startIdx: int = 1,
        endIdx: int = 100_000,
    ) -> list[dict]:
        """StatisticSearch 조회 → row 리스트 반환.

        Capabilities: ECOS StatisticSearch endpoint GET + 30 RPM rate limit + 429/5xx 재시도.
        AIContext: ECOS 모든 시계열 조회의 단일 HTTP 진입점.
        Guide: URL path 방식 (key/json/kr/start/end/table/freq/startDate/endDate/item).
        When: series.fetchSeries / catalog 모든 ECOS API 호출 시.
        How: rate limit 대기 → GET → 200 parseResponse / 429 retry / 4xx raise.

        Args:
            tableCode: 통계표코드 (예: "722Y001").
            freq: 주기 (D/M/Q/A).
            startDate: 시작일 (ECOS 형식).
            endDate: 종료일 (ECOS 형식).
            itemCode: 항목코드.
            startIdx: 시작 인덱스.
            endIdx: 종료 인덱스.

        Returns:
            row 딕셔너리 리스트.

        Raises:
            EcosError: HTTP 4xx 응답 또는 최대 재시도 초과.
            RateLimitError: 429 rate limit (재시도 후에도 회복 안 됨).

        Requires:
            ``ECOS_API_KEY`` 환경변수 — 무료 발급 ``https://ecos.bok.or.kr/api/``.

        Example:
            >>> c = EcosClient()
            >>> rows = c.get("722Y001", "D", "20240101", "20241231", "0101000")

        See Also:
            close : 세션 정리.
            series.fetchSeries : 본 메서드의 caller.
        """
        # URL 경로 방식: /서비스/키/json/kr/시작/종료/테이블/주기/시작일/종료일/항목
        url = (
            f"{_BASE_URL}/StatisticSearch/{self._key}/json/kr"
            f"/{startIdx}/{endIdx}/{tableCode}/{freq}/{startDate}/{endDate}"
        )
        if itemCode:
            url += f"/{itemCode}"

        last_exc: Exception | None = None
        for attempt in range(3):
            self._rateLimit()
            try:
                resp = self._session.get(url, timeout=30)
            except httpx.HTTPError as exc:
                last_exc = exc
                self._backoff(attempt)
                continue

            if resp.status_code == 200:
                try:
                    data = resp.json()
                except ValueError as exc:
                    raise EcosError("ECOS 응답 JSON을 해석할 수 없습니다") from exc
                return self._parseResponse(data)

            if resp.status_code == 429:
                log.warning("ECOS rate limit hit, backing off (attempt %d)", attempt + 1)
                self._backoff(attempt)
                last_exc = RateLimitError(f"429 Too Many Requests (attempt {attempt + 1})")
                continue

            if resp.status_code in (500, 502, 503, 504):
                log.warning("ECOS server error %d, retrying", resp.status_code)
                self._backoff(attempt)
                last_exc = EcosError(f"HTTP {resp.status_code}")
                continue

            # 4xx 기타
            raise EcosError(f"HTTP {resp.status_code}: {resp.text[:200]}")

        if isinstance(last_exc, EcosError):
            raise last_exc
        if last_exc is not None:
            raise EcosError("ECOS 요청 실패 (최대 재시도 초과)") from last_exc
        raise EcosError("ECOS 요청 실패 (최대 재시도 초과)")

    def close(self) -> None:
        """HTTP 세션 종료.

        Capabilities: httpx.Client.close 위임.
        AIContext: EcosClient 리소스 정리 진입.
        Guide: idempotent — 두 번 호출 graceful.
        When: dartlab 종료 / Ecos facade close 시.
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
        >>> c = EcosClient()
        >>> c.close()

        See Also
        --------
        facade.Ecos.close : 본 메서드의 caller.
        """
        self._session.close()

    # ── private ──

    @staticmethod
    def _parseResponse(data: object) -> list[dict]:
        """ECOS JSON 응답 파싱.

        Parameters
        ----------
        data : dict
            ECOS REST API 원본 JSON 응답.

        Returns
        -------
        list[dict]
            ``StatisticSearch.row`` 리스트. 데이터 없으면 빈 리스트.

        Raises
        ------
        EcosError
            ECOS 에러 코드가 INFO-000/INFO-200 이외일 때.
        """
        if not isinstance(data, dict):
            raise EcosError("ECOS 응답 schema가 객체가 아닙니다")

        # 에러 응답 체크
        if "RESULT" in data:
            resultInfo = data["RESULT"]
            if not isinstance(resultInfo, dict):
                raise EcosError("ECOS RESULT가 객체가 아닙니다")
            code = resultInfo.get("CODE", "")
            msg = resultInfo.get("MESSAGE", "")
            if code == "INFO-200":
                return []  # 데이터 없음
            if code != "INFO-000":
                raise EcosError(f"[{code}] {msg}")

        if "StatisticSearch" not in data:
            raise EcosError("ECOS 응답에 StatisticSearch가 없습니다")

        search = data["StatisticSearch"]
        if not isinstance(search, dict):
            raise EcosError("ECOS StatisticSearch가 객체가 아닙니다")
        if "row" not in search:
            raise EcosError("ECOS StatisticSearch에 row가 없습니다")
        rawRows = search["row"]
        rows = rawRows if isinstance(rawRows, list) else [rawRows]
        if not all(isinstance(row, dict) for row in rows):
            raise EcosError("ECOS StatisticSearch row가 객체가 아닙니다")
        return rows

    def _rateLimit(self) -> None:
        """슬라이딩 윈도우 레이트 리밋 (30 RPM).

        Returns
        -------
        None
            윈도우 초과 시 대기 후 반환.
        """
        now = time.monotonic()
        cutoff = now - _RATE_LIMIT_WINDOW
        self._timestamps = [t for t in self._timestamps if t > cutoff]
        if len(self._timestamps) >= _RATE_LIMIT_RPM:
            wait = self._timestamps[0] + _RATE_LIMIT_WINDOW - now + 0.1
            if wait > 0:
                log.debug("ECOS rate limit: waiting %.1fs", wait)
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
