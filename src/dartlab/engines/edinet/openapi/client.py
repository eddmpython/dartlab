"""EDINET API v2 HTTP 클라이언트.

EDINET API v2 엔드포인트:
- /api/v2/documents.json — 서류 목록 (날짜별)
- /api/v2/documents/{docID} — 서류 다운로드 (ZIP)

API 키 발급:
  1. https://api.edinet-fsa.go.jp/api/auth/index.aspx?mode=1 접속
  2. 팝업 차단 해제 필수 (api.edinet-fsa.go.jp 허용)
  3. 전화번호 입력 시 국가코드 +81 선택, "80-XXXX-XXXX" 형식 (0 제외)
  4. 연락처 등록 후 API 키 화면에 표시

인증 방식:
  - 쿼리 파라미터: ?Subscription-Key=YOUR_KEY
  - 또는 헤더: Ocp-Apim-Subscription-Key: YOUR_KEY

환경변수: EDINET_API_KEY
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

import requests

BASE_URL = "https://api.edinet-fsa.go.jp/api/v2"

# 서류 유형 코드 (docTypeCode)
DOC_TYPE_YUHO = "120"  # 有価証券報告書 (유가증권보고서 = 사업보고서)
DOC_TYPE_HANKI = "130"  # 半期報告書 (반기보고서)
DOC_TYPE_SHIHANKI = "140"  # 四半期報告書 (분기보고서)

# 다운로드 type 파라미터
DOWNLOAD_XBRL = 1  # XBRL
DOWNLOAD_PDF = 2  # PDF
DOWNLOAD_CSV = 5  # CSV (재무 데이터)


class EdinetApiError(RuntimeError):
    """EDINET API 호출 오류."""


class EdinetClient:
    """EDINET API v2 클라이언트.

    원칙:
    - polite pacing (초당 1회 이하 권장)
    - 명시적 예외 전파
    - source-native JSON 유지
    """

    def __init__(
        self,
        *,
        apiKey: str | None = None,
        minInterval: float = 1.0,
        timeout: float = 60.0,
        maxRetries: int = 3,
    ):
        self.apiKey = apiKey or os.environ.get("EDINET_API_KEY", "")
        if not self.apiKey:
            raise EdinetApiError(
                "EDINET API 키가 필요합니다. "
                "EDINET_API_KEY 환경변수를 설정하거나 apiKey 파라미터를 전달하세요.\n"
                "발급: https://api.edinet-fsa.go.jp/api/auth/index.aspx?mode=1\n"
                "주의: 브라우저 팝업 차단 해제 필요 (api.edinet-fsa.go.jp 허용)"
            )
        self.minInterval = max(float(minInterval), 0.0)
        self.timeout = float(timeout)
        self.maxRetries = max(int(maxRetries), 1)
        self._session = requests.Session()
        self._lastRequestAt = 0.0

    def _wait(self) -> None:
        if self.minInterval <= 0:
            return
        now = time.monotonic()
        elapsed = now - self._lastRequestAt
        if elapsed < self.minInterval:
            time.sleep(self.minInterval - elapsed)

    @property
    def _headers(self) -> dict[str, str]:
        return {"Ocp-Apim-Subscription-Key": self.apiKey}

    def _get(self, url: str, params: dict[str, Any] | None = None) -> requests.Response:
        """공통 GET 요청 + 재시도."""
        lastErr: Exception | None = None
        for attempt in range(self.maxRetries):
            self._wait()
            try:
                resp = self._session.get(
                    url,
                    params=params,
                    headers=self._headers,
                    timeout=self.timeout,
                )
                self._lastRequestAt = time.monotonic()
                resp.raise_for_status()
                return resp
            except requests.HTTPError as exc:
                lastErr = exc
                status = exc.response.status_code if exc.response is not None else None
                if status not in (429, 500, 502, 503, 504) or attempt == self.maxRetries - 1:
                    raise EdinetApiError(f"EDINET API 요청 실패 ({status}): {url}") from exc
                time.sleep(2**attempt)
            except requests.RequestException as exc:
                lastErr = exc
                if attempt == self.maxRetries - 1:
                    raise EdinetApiError(f"EDINET API 네트워크 오류: {url}") from exc
                time.sleep(2**attempt)
        raise EdinetApiError(f"EDINET API 요청 실패: {url}") from lastErr

    # ── 서류 목록 ──

    def listDocuments(
        self,
        date: str,
        *,
        docType: str | None = None,
    ) -> list[dict[str, Any]]:
        """특정 날짜의 제출 서류 목록 조회.

        Args:
            date: 조회일 (YYYY-MM-DD).
            docType: 서류 유형 필터 (예: "120" = 유가증권보고서).

        Returns:
            서류 dict 리스트. 각 dict에 docID, filerName, edinetCode 등 포함.
        """
        params: dict[str, Any] = {
            "date": date,
            "type": 2,  # type=2: 메타데이터 포함
        }
        resp = self._get(f"{BASE_URL}/documents.json", params=params)
        data = resp.json()

        results: list[dict[str, Any]] = data.get("results", [])
        if docType:
            results = [d for d in results if d.get("docTypeCode") == docType]
        return results

    # ── 서류 다운로드 ──

    def downloadDocument(
        self,
        docId: str,
        saveDir: str | Path,
        *,
        downloadType: int = DOWNLOAD_CSV,
    ) -> Path:
        """서류 ZIP 다운로드.

        Args:
            docId: 서류 ID.
            saveDir: 저장 디렉토리.
            downloadType: 1=XBRL, 2=PDF, 5=CSV.

        Returns:
            저장된 ZIP 파일 경로.
        """
        saveDir = Path(saveDir)
        saveDir.mkdir(parents=True, exist_ok=True)

        params: dict[str, Any] = {
            "type": downloadType,
        }
        resp = self._get(f"{BASE_URL}/documents/{docId}", params=params)

        zipPath = saveDir / f"{docId}.zip"
        zipPath.write_bytes(resp.content)
        return zipPath

    # ── EDINET 코드 목록 ──

    def listEdinetCodes(self) -> list[dict[str, Any]]:
        """EDINET 코드 목록 (기업 마스터) 다운로드.

        Returns:
            기업 dict 리스트 (edinetCode, filerName, securitiesCode 등).
        """
        resp = self._get(f"{BASE_URL}/edinetcode.json")
        data = resp.json()
        return data.get("results", [])
