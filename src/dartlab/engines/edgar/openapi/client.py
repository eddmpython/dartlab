"""EDGAR OpenAPI 공통 HTTP 클라이언트."""

from __future__ import annotations

import time
from typing import Any

import requests

DEFAULT_USER_AGENT = "DartLab eddmpython@gmail.com"
DEFAULT_BASE_URL = "https://data.sec.gov"
DEFAULT_SEC_URL = "https://www.sec.gov"


class EdgarApiError(RuntimeError):
    """SEC API 호출 오류."""


class EdgarClient:
    """SEC public API 클라이언트.

    원칙:
    - source-native JSON 응답 유지
    - polite pacing + 재시도
    - 실패는 명시적 예외로 전파
    """

    def __init__(
        self,
        *,
        userAgent: str | None = None,
        email: str | None = None,
        minInterval: float = 0.2,
        timeout: float = 30.0,
        maxRetries: int = 3,
    ):
        self.userAgent = self._buildUserAgent(userAgent=userAgent, email=email)
        self.minInterval = max(float(minInterval), 0.0)
        self.timeout = float(timeout)
        self.maxRetries = max(int(maxRetries), 1)
        self._session = requests.Session()
        self._lastRequestAt = 0.0

    @staticmethod
    def _buildUserAgent(*, userAgent: str | None, email: str | None) -> str:
        if userAgent:
            return userAgent
        if email:
            return f"DartLab {email}"
        return DEFAULT_USER_AGENT

    @property
    def headers(self) -> dict[str, str]:
        return {"User-Agent": self.userAgent}

    def _wait(self) -> None:
        if self.minInterval <= 0:
            return
        now = time.monotonic()
        elapsed = now - self._lastRequestAt
        if elapsed < self.minInterval:
            time.sleep(self.minInterval - elapsed)

    def getJson(self, url: str) -> dict[str, Any]:
        lastErr: Exception | None = None
        for attempt in range(self.maxRetries):
            self._wait()
            try:
                resp = self._session.get(url, headers=self.headers, timeout=self.timeout)
                self._lastRequestAt = time.monotonic()
                resp.raise_for_status()
                data = resp.json()
                if not isinstance(data, dict):
                    raise EdgarApiError(f"JSON object expected: {url}")
                return data
            except requests.HTTPError as exc:
                lastErr = exc
                status = exc.response.status_code if exc.response is not None else None
                if status not in (429, 500, 502, 503, 504) or attempt == self.maxRetries - 1:
                    raise EdgarApiError(f"SEC API 요청 실패 ({status}): {url}") from exc
                time.sleep(2**attempt)
            except requests.RequestException as exc:
                lastErr = exc
                if attempt == self.maxRetries - 1:
                    raise EdgarApiError(f"SEC API 네트워크 오류: {url}") from exc
                time.sleep(2**attempt)
        if lastErr is not None:
            raise EdgarApiError(f"SEC API 요청 실패: {url}") from lastErr
        raise EdgarApiError(f"SEC API 요청 실패: {url}")
