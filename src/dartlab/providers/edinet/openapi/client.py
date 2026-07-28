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

import httpx

from dartlab.core.requestPacing import waitMinInterval

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
        self._session = httpx.Client(follow_redirects=True)
        self._lastRequestAt = 0.0

    def _wait(self) -> None:
        waitMinInterval(self._lastRequestAt, self.minInterval)

    @property
    def _headers(self) -> dict[str, str]:
        return {"Ocp-Apim-Subscription-Key": self.apiKey}

    def _get(self, url: str, params: dict[str, Any] | None = None) -> httpx.Response:
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
            except httpx.HTTPStatusError as exc:
                lastErr = exc
                status = exc.response.status_code
                if status not in (429, 500, 502, 503, 504) or attempt == self.maxRetries - 1:
                    raise EdinetApiError(f"EDINET API 요청 실패 ({status}): {url}") from exc
                time.sleep(2**attempt)
            except httpx.HTTPError as exc:
                lastErr = exc
                if attempt == self.maxRetries - 1:
                    raise EdinetApiError(f"EDINET API 네트워크 오류: {url}") from exc
                time.sleep(2**attempt)
        raise EdinetApiError(f"EDINET API 요청 실패: {url}") from lastErr

    # ── 서류 목록 ──

    def listDocuments(
        self,
        period: str,
        *,
        docType: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """특정 날짜의 제출 서류 목록 조회.

        Args:
            period: 조회일 (YYYY-MM-DD).
            docType: 서류 유형 필터 (예: ``"120"`` = 유가증권보고서).
            limit: 최대 항목 수. None 이면 무제한.

        Returns:
            서류 dict 리스트. 각 dict 에 docID, filerName, edinetCode 등 포함.

        Example:
            >>> client.listDocuments("2026-05-01", docType="120", limit=50)

        Raises:
            없음.

        Capabilities:
            - <TODO: 함수 핵심 책임 요약>

        Guide:
            - <TODO: 사용 시나리오>

        AIContext:
            <TODO: AI 호출 컨텍스트>

        LLM Specifications:
            AntiPatterns:
                - <TODO: 안티패턴>
            OutputSchema:
                - <TODO: 출력 형태>
            Prerequisites:
                - <TODO: 사전조건>
            Freshness:
                - <TODO: 데이터 freshness>
            Dataflow:
                - <TODO: 데이터 흐름>
            TargetMarkets:
                - <TODO: 대상 시장>

        SeeAlso:
            - <TODO: 관련 함수/엔진>

        Requires:
            - httpx
            - time
        """
        params: dict[str, Any] = {
            "period": period,
            "type": 2,  # type=2: 메타데이터 포함
        }
        resp = self._get(f"{BASE_URL}/documents.json", params=params)
        data = resp.json()

        results: list[dict[str, Any]] = data.get("results", [])
        if docType:
            results = [d for d in results if d.get("docTypeCode") == docType]
        if limit is not None:
            results = results[:limit]
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

        Raises:
            없음.

        Example:
            >>> downloadDocument(...)

        Capabilities:
            - <TODO: 함수 핵심 책임 요약>

        Guide:
            - <TODO: 사용 시나리오>

        AIContext:
            <TODO: AI 호출 컨텍스트>

        LLM Specifications:
            AntiPatterns:
                - <TODO: 안티패턴>
            OutputSchema:
                - <TODO: 출력 형태>
            Prerequisites:
                - <TODO: 사전조건>
            Freshness:
                - <TODO: 데이터 freshness>
            Dataflow:
                - <TODO: 데이터 흐름>
            TargetMarkets:
                - <TODO: 대상 시장>

        SeeAlso:
            - <TODO: 관련 함수/엔진>

        Requires:
            - httpx
            - time
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

    def listEdinetCodes(self, *, limit: int | None = None) -> list[dict[str, Any]]:
        """EDINET 코드 목록 (기업 마스터) 다운로드.

        Args:
            limit: 최대 항목 수. None 이면 무제한.

        Returns:
            기업 dict 리스트 (edinetCode, filerName, securitiesCode 등).

        Example:
            >>> client.listEdinetCodes(limit=100)

        Raises:
            없음.

        Capabilities:
            - <TODO: 함수 핵심 책임 요약>

        Guide:
            - <TODO: 사용 시나리오>

        AIContext:
            <TODO: AI 호출 컨텍스트>

        LLM Specifications:
            AntiPatterns:
                - <TODO: 안티패턴>
            OutputSchema:
                - <TODO: 출력 형태>
            Prerequisites:
                - <TODO: 사전조건>
            Freshness:
                - <TODO: 데이터 freshness>
            Dataflow:
                - <TODO: 데이터 흐름>
            TargetMarkets:
                - <TODO: 대상 시장>

        SeeAlso:
            - <TODO: 관련 함수/엔진>

        Requires:
            - httpx
            - time
        """
        resp = self._get(f"{BASE_URL}/edinetcode.json")
        data = resp.json()
        results: list[dict[str, Any]] = data.get("results", [])
        if limit is not None:
            results = results[:limit]
        return results

    def iterDocuments(
        self,
        period: str,
        *,
        docType: str | None = None,
        limit: int | None = None,
    ):
        """``listDocuments`` 의 iterator pair (룰 10).

        Args:
            period: 조회일 (YYYY-MM-DD).
            docType: 서류 유형 필터.
            limit: 최대 항목 수. None 이면 무제한.

        Yields:
            서류 dict.

        Example:
            >>> for doc in client.iterDocuments("2026-05-01", limit=10):
            ...     print(doc["docID"])

        Raises:
            없음.

        Capabilities:
            - <TODO: 함수 핵심 책임 요약>

        Guide:
            - <TODO: 사용 시나리오>

        AIContext:
            <TODO: AI 호출 컨텍스트>

        LLM Specifications:
            AntiPatterns:
                - <TODO: 안티패턴>
            OutputSchema:
                - <TODO: 출력 형태>
            Prerequisites:
                - <TODO: 사전조건>
            Freshness:
                - <TODO: 데이터 freshness>
            Dataflow:
                - <TODO: 데이터 흐름>
            TargetMarkets:
                - <TODO: 대상 시장>

        SeeAlso:
            - <TODO: 관련 함수/엔진>

        Requires:
            - httpx
            - time
        """
        yield from self.listDocuments(period, docType=docType, limit=limit)

    def iterEdinetCodes(self, *, limit: int | None = None):
        """``listEdinetCodes`` 의 iterator pair (룰 10).

        Args:
            limit: 최대 항목 수. None 이면 무제한.

        Yields:
            기업 dict.

        Example:
            >>> for ec in client.iterEdinetCodes(limit=100):
            ...     print(ec["edinetCode"])

        Raises:
            없음.

        Capabilities:
            - <TODO: 함수 핵심 책임 요약>

        Guide:
            - <TODO: 사용 시나리오>

        AIContext:
            <TODO: AI 호출 컨텍스트>

        LLM Specifications:
            AntiPatterns:
                - <TODO: 안티패턴>
            OutputSchema:
                - <TODO: 출력 형태>
            Prerequisites:
                - <TODO: 사전조건>
            Freshness:
                - <TODO: 데이터 freshness>
            Dataflow:
                - <TODO: 데이터 흐름>
            TargetMarkets:
                - <TODO: 대상 시장>

        SeeAlso:
            - <TODO: 관련 함수/엔진>

        Requires:
            - httpx
            - time
        """
        yield from self.listEdinetCodes(limit=limit)
