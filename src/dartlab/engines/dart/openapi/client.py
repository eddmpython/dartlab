"""OpenDART HTTP 클라이언트.

- 멀티 키 로테이션 (키 여러 개 → rate limit 분산)
- rate limit 자동 조절 + 초과 시 다음 키로 전환 재시도
- 응답 → Polars DataFrame 변환
- 에러 코드 구조화 처리 (013 = 빈 DataFrame 옵션)
"""

from __future__ import annotations

import os
import time
from typing import Any

import polars as pl
import requests

BASE_URL = "https://opendart.fss.or.kr/api"

_ERROR_MESSAGES: dict[str, str] = {
    "000": "정상",
    "010": "등록되지 않은 API 키",
    "011": "사용할 수 없는 API 키",
    "013": "조회된 데이터가 없음",
    "020": "요청 제한 초과",
    "100": "필드 오류",
    "800": "시스템 점검 중",
    "900": "정의되지 않은 오류",
}


class DartApiError(Exception):
    """OpenDART API 에러."""

    def __init__(self, status: str, message: str):
        self.status = status
        self.message = message
        super().__init__(f"[{status}] {message}")


class DartClient:
    """OpenDART API 클라이언트 — 멀티 키 로테이션 지원.

    Parameters
    ----------
    apiKey : str | None
        단일 API 키.
    apiKeys : list[str] | None
        복수 API 키 (로테이션). apiKey보다 우선.
    requestsPerMinute : int
        키당 분당 최대 요청 수 (기본 580).

    키 탐색 순서:
    1. apiKeys 파라미터
    2. apiKey 파라미터
    3. 환경변수 DART_API_KEYS (쉼표 구분)
    4. 환경변수 DART_API_KEY (단일)
    """

    def __init__(
        self,
        apiKey: str | None = None,
        apiKeys: list[str] | None = None,
        requestsPerMinute: int = 580,
    ):
        self._keys = self._resolveKeys(apiKey, apiKeys)
        if not self._keys:
            raise ValueError(
                "API 키가 필요합니다.\n"
                "  Dart(apiKey='...')  또는\n"
                "  Dart(apiKeys=['k1','k2'])  또는\n"
                "  환경변수 DART_API_KEY / DART_API_KEYS 설정"
            )
        self._keyIndex = 0
        self._minInterval = 60.0 / requestsPerMinute
        self._lastRequestTime = 0.0
        self._session = requests.Session()

    @staticmethod
    def _resolveKeys(apiKey: str | None, apiKeys: list[str] | None) -> list[str]:
        """키 탐색 우선순위."""
        if apiKeys:
            return [k.strip() for k in apiKeys if k.strip()]
        if apiKey:
            return [apiKey.strip()]
        envKeys = os.environ.get("DART_API_KEYS", "")
        if envKeys:
            return [k.strip() for k in envKeys.split(",") if k.strip()]
        envKey = os.environ.get("DART_API_KEY", "")
        if envKey:
            return [envKey.strip()]
        return []

    @property
    def currentKey(self) -> str:
        return self._keys[self._keyIndex]

    def _rotateKey(self) -> bool:
        """다음 키로 전환. 더 이상 없으면 False."""
        if len(self._keys) <= 1:
            return False
        self._keyIndex = (self._keyIndex + 1) % len(self._keys)
        return True

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._lastRequestTime
        if elapsed < self._minInterval:
            time.sleep(self._minInterval - elapsed)
        self._lastRequestTime = time.monotonic()

    def getJson(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        *,
        emptyOn013: bool = False,
    ) -> dict[str, Any]:
        """JSON 엔드포인트 호출.

        Parameters
        ----------
        emptyOn013 : bool
            True면 '013' (데이터 없음) 시 에러 대신 빈 dict 반환.
        """
        triedKeys = 0
        while triedKeys < len(self._keys):
            self._throttle()
            url = f"{BASE_URL}/{endpoint}"
            merged = {"crtfc_key": self.currentKey}
            if params:
                merged.update(params)

            resp = self._session.get(url, params=merged, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            status = data.get("status", "000")
            if status == "000":
                return data
            if status == "013" and emptyOn013:
                return {}
            if status == "020" and self._rotateKey():
                triedKeys += 1
                time.sleep(1)
                continue

            msg = data.get("message", _ERROR_MESSAGES.get(status, "알 수 없는 오류"))
            raise DartApiError(status, msg)

        msg = _ERROR_MESSAGES.get("020", "요청 제한 초과")
        raise DartApiError("020", f"{msg} (모든 키 소진)")

    def getBytes(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> bytes:
        """바이너리 엔드포인트 호출 (ZIP, XML 다운로드 등).

        JSON 에러 응답도 감지하고, rate limit 시 키 로테이션.
        """
        triedKeys = 0
        while triedKeys < len(self._keys):
            self._throttle()
            url = f"{BASE_URL}/{endpoint}"
            merged = {"crtfc_key": self.currentKey}
            if params:
                merged.update(params)

            resp = self._session.get(url, params=merged, timeout=60)
            resp.raise_for_status()

            # OpenDART는 바이너리 에러 시에도 JSON을 반환할 수 있음
            contentType = resp.headers.get("Content-Type", "")
            if "application/json" in contentType or "text/json" in contentType:
                data = resp.json()
                status = data.get("status", "000")
                if status == "020" and self._rotateKey():
                    triedKeys += 1
                    time.sleep(1)
                    continue
                if status != "000":
                    msg = data.get("message", _ERROR_MESSAGES.get(status, "알 수 없는 오류"))
                    raise DartApiError(status, msg)

            return resp.content

        raise DartApiError("020", "요청 제한 초과 (모든 키 소진)")

    def getDf(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        listKey: str = "list",
    ) -> pl.DataFrame:
        """JSON → Polars DataFrame. 데이터 없으면 빈 DataFrame."""
        data = self.getJson(endpoint, params, emptyOn013=True)
        rows = data.get(listKey, [])
        if not rows:
            return pl.DataFrame()
        return pl.DataFrame(rows)

    def getDfAll(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        listKey: str = "list",
        pageSize: int = 100,
    ) -> pl.DataFrame:
        """자동 페이지네이션 → 전체 결과 Polars DataFrame."""
        merged = dict(params) if params else {}
        merged["page_count"] = str(pageSize)

        allRows: list[dict] = []
        page = 1

        while True:
            merged["page_no"] = str(page)
            data = self.getJson(endpoint, merged, emptyOn013=True)
            rows = data.get(listKey, [])
            if not rows:
                break
            allRows.extend(rows)

            totalPage = int(data.get("total_page", 1))
            if page >= totalPage:
                break
            page += 1

        if not allRows:
            return pl.DataFrame()
        return pl.DataFrame(allRows)
