"""ECOS REST API 클라이언트 — rate limit + retry."""

from __future__ import annotations

import logging
import os
import time

import requests

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
        raw = apiKey or os.environ.get("ECOS_API_KEY", "")
        if not raw:
            raise AuthenticationError(
                "ECOS API 키가 없습니다. "
                "환경변수 ECOS_API_KEY를 설정하거나 Ecos(apiKey=...) 인자를 전달하세요.\n"
                "무료 발급: https://ecos.bok.or.kr/api/#/"
            )
        self._key = raw.strip()
        self._session = requests.Session()
        self._session.headers["User-Agent"] = "dartlab-ecos/1.0"
        self._timestamps: list[float] = []

    def get(
        self,
        tableCode: str,
        frequency: str,
        startDate: str,
        endDate: str,
        itemCode: str = "",
        *,
        startIdx: int = 1,
        endIdx: int = 100_000,
    ) -> list[dict]:
        """StatisticSearch 조회 → row 리스트 반환.

        Args:
            tableCode: 통계표코드 (예: "722Y001").
            frequency: 주기 (D/M/Q/A).
            startDate: 시작일 (ECOS 형식).
            endDate: 종료일 (ECOS 형식).
            itemCode: 항목코드.
            startIdx: 시작 인덱스.
            endIdx: 종료 인덱스.

        Returns:
            row 딕셔너리 리스트.
        """
        # URL 경로 방식: /서비스/키/json/kr/시작/종료/테이블/주기/시작일/종료일/항목
        url = (
            f"{_BASE_URL}/StatisticSearch/{self._key}/json/kr"
            f"/{startIdx}/{endIdx}/{tableCode}/{frequency}/{startDate}/{endDate}"
        )
        if itemCode:
            url += f"/{itemCode}"

        last_exc: Exception | None = None
        for attempt in range(3):
            self._rateLimit()
            try:
                resp = self._session.get(url, timeout=30)
            except requests.RequestException as exc:
                last_exc = exc
                self._backoff(attempt)
                continue

            if resp.status_code == 200:
                return self._parseResponse(resp.json())

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

        raise last_exc or EcosError("요청 실패 (최대 재시도 초과)")

    def close(self) -> None:
        """HTTP 세션 종료."""
        self._session.close()

    # ── private ──

    @staticmethod
    def _parseResponse(data: dict) -> list[dict]:
        """ECOS JSON 응답 파싱."""
        # 에러 응답 체크
        if "RESULT" in data:
            code = data["RESULT"].get("CODE", "")
            msg = data["RESULT"].get("MESSAGE", "")
            if code == "INFO-200":
                return []  # 데이터 없음
            if code != "INFO-000":
                raise EcosError(f"[{code}] {msg}")

        if "StatisticSearch" not in data:
            return []

        rows = data["StatisticSearch"].get("row", [])
        return rows if isinstance(rows, list) else [rows]

    def _rateLimit(self) -> None:
        """슬라이딩 윈도우 레이트 리밋."""
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
        """지수 백오프."""
        delay = min(2**attempt, 8)
        time.sleep(delay)
