"""OpenDART HTTP 클라이언트.

- 멀티 키 로테이션 (키 여러 개 → rate limit 분산)
- rate limit 자동 조절 + 초과 시 다음 키로 전환 재시도
- 응답 → Polars DataFrame 변환
- 에러 코드 구조화 처리 (013 = 빈 DataFrame 옵션)
"""

from __future__ import annotations

import os
import random
import threading
import time
from dataclasses import dataclass, field
from typing import Any

import httpx
import polars as pl

from dartlab.core.dartClient import DartApiError, registerDartFetchProvider
from dartlab.core.logger import getLogger
from dartlab.gather.dart.keys import resolveDartKeys

_log = getLogger(__name__)

BASE_URL = "https://opendart.fss.or.kr/api"

# 키 020 (rate limit) 시 cooldown — DART 분당 580 rpm 회복 대기.
_COOLDOWN_SEC = 60.0

# 전송 계층 일시 장애(연결 끊김·read 타임아웃·일시 5xx) 한정 재시도 횟수·백오프(지수, 초).
# DART 가 응답 없이 끊거나(RemoteProtocolError) 일시 5xx 를 낼 때 단발 실패가 파이프라인 잡 전체를
# 죽이던 갭 방어(Original SSOT Sync dart-reconcile). status(013/020) cooldown 은 호출자 루프가 담당.
# 연결 단계 실패(ConnectTimeout·ConnectError)는 이 경로로 세지 않고 아래 _CONNECT_* 경로가 따로 맡는다.
_TRANSIENT_RETRIES = 3
_TRANSIENT_BACKOFF_SEC = 0.5

# 연결 단계(TCP connect) 타임아웃 상한(초). 예전에는 connect 타임아웃이 요청 전체 timeout(30/60초)과
# 같아서 불통 구간에서는 시도 한 번이 60초씩 걸렸고, 재시도 3회가 같은 불통 구간 안에서 다 소진됐다
# (KindList "Fetch OpenDART CORPCODE.xml" 182초 = connect 60초 x 3). 연결 단계만 줄여 불통을 빨리
# 감지하고, read·write·pool 은 호출자가 준 timeout 을 그대로 쓴다.
_CONNECT_TIMEOUT_SEC = 10.0

# 연결 단계 실패 전용 백오프(초, 끝값 반복)와 jitter 비율(±20%). 요청이 송신되기 전 실패라 재시도가
# 안전하다. OpenDART 는 단일 A 레코드라 TCP 연결이 수 분(실측 3~7분) 막히는 구간이 있어 0.5초·1초
# 백오프로는 그 구간을 넘기지 못한다. 시도 횟수는 env DARTLAB_DART_CONNECT_RETRY_ATTEMPTS 로 정한다.
# 기본 3 은 대화형 사용자가 수 분씩 멈추지 않게 하려는 값이고(최소 1, 정수가 아니면 기본값),
# CI 워크플로는 6 으로 올려 약 4분 20초 구간을 버틴다(connect 10초 x 6 + 대기 5+15+30+60+90초,
# jitter 별도).
_CONNECT_BACKOFF_SEC = (5.0, 15.0, 30.0, 60.0, 90.0)
_CONNECT_BACKOFF_JITTER = 0.2
_CONNECT_RETRY_ENV = "DARTLAB_DART_CONNECT_RETRY_ATTEMPTS"
_CONNECT_RETRY_DEFAULT = 3


def _connectRetryAttempts() -> int:
    """연결 단계 실패 최대 시도 횟수를 env 에서 읽는다.

    Returns:
        int: ``DARTLAB_DART_CONNECT_RETRY_ATTEMPTS`` 값(최소 1). 미설정이거나 정수가 아니면 기본 3.
    """
    try:
        return max(1, int(os.environ.get(_CONNECT_RETRY_ENV, str(_CONNECT_RETRY_DEFAULT))))
    except ValueError:
        return _CONNECT_RETRY_DEFAULT


def _connectBackoffWait(failureIndex: int) -> float:
    """연결 단계 실패 뒤 대기 초를 돌려준다.

    ``_CONNECT_BACKOFF_SEC`` 순서대로 쓰고 끝값을 반복하며, ±20% jitter 를 곱해 병렬 워커와
    재실행이 같은 순간에 몰려 다시 붙지 않게 흩는다.

    Args:
        failureIndex: 0 부터 세는 연결 실패 순번.

    Returns:
        float: 대기 초.
    """
    base = _CONNECT_BACKOFF_SEC[min(failureIndex, len(_CONNECT_BACKOFF_SEC) - 1)]
    return base * random.uniform(1.0 - _CONNECT_BACKOFF_JITTER, 1.0 + _CONNECT_BACKOFF_JITTER)


@dataclass
class _KeySlot:
    """단일 API 키 + per-key throttle 상태. 스레드별 slot 예약으로 간섭 차단."""

    key: str
    nextAvailable: float = 0.0  # epoch — 다음 요청 가능 시각 (예약 포함)
    coolDownUntil: float = 0.0  # 020 발생 시 회복 시각
    failures: int = 0  # 누적 실패 (디버그)
    inFlight: int = 0  # 현재 진행 중 요청 수


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
                "DART API 키가 필요합니다.\n"
                "  설정 방법 (우선순위 순):\n"
                "  1. DartClient(apiKey='...')  직접 전달\n"
                "  2. 환경변수 DART_API_KEY 또는 DART_API_KEYS(쉼표 구분) 설정\n"
                "  3. 프로젝트 루트 .env 파일에 DART_API_KEY=... 작성\n"
                "  발급: https://opendart.fss.or.kr → 인증키 신청"
            )
        self._minInterval = 60.0 / requestsPerMinute
        self._slots: list[_KeySlot] = [_KeySlot(key=k) for k in self._keys]
        self._poolLock = threading.Lock()
        # httpx.Client 는 thread-safe (per docs) — 단일 인스턴스 공유 OK.
        self._session = httpx.Client(follow_redirects=True)

    @staticmethod
    def _resolveKeys(apiKey: str | None, apiKeys: list[str] | None) -> list[str]:
        """키 탐색 우선순위: 파라미터 → 환경변수 → .env 파일."""
        return resolveDartKeys(apiKey=apiKey, apiKeys=apiKeys)

    @property
    def currentKey(self) -> str:
        """현재 사용 중인 DART API 키를 반환한다.

        Args:
            (인자 자동 생성).

        Raises:
            없음.

        Example:
            >>> currentKey(...)

        Returns:
            str — 현재 활성 키.

        LLM Specifications:
            AntiPatterns:
                - DartApiError (status="013" 등) 미처리 → 예외 propagate. caller try/except 의무.
                - 단일 키로 분당 580 req 초과 → rate limit. 멀티 키 (DART_API_KEYS) 사용.
            OutputSchema:
                - pl.DataFrame / dict / bytes — endpoint 별.
            Prerequisites:
                - 인터넷 + DART_API_KEY 또는 DART_API_KEYS.
            Freshness:
                - DART OpenAPI 실시간 (분 단위).
            Dataflow:
                - 사용자 인자 → httpx → DART API → 응답 정규화 → 본 함수.
            TargetMarkets:
                - KR (DART) 한정.
        """
        return self._slots[0].key

    def _acquireSlot(self) -> tuple[_KeySlot, float]:
        """순차 키 소진 패턴 — `.github/scripts/sync/syncRecent.py` 와 동일.

        DART per-IP anti-abuse 는 매 요청 다른 키 rotation 을 abuse 로 분류.
        finance/syncRecent 가 차단 0 으로 동작했던 이유 = 키 1개로 580 rpm 소진
        후 다음 키. 본 method 도 같은 패턴:
        1. 첫 가용 slot (cooldown 안 걸린 것) 반환 — 매 요청 동일 키
        2. 같은 slot 의 throttle (slot.nextAvailable) 만 caller 가 sleep
        3. 020 발생 → _markCoolDown 으로 60s 잠금 → 자동 다음 slot
        4. 모든 slot cooldown → 가장 빨리 풀리는 slot 의 cooldown 시각까지 대기

        스레드 안전: _poolLock 안에서 slot 선택 + nextAvailable 예약.
        """
        now = time.monotonic()
        with self._poolLock:
            # 1. cooldown 안 걸린 첫 slot 사용 (sequential exhausted)
            for s in self._slots:
                if s.coolDownUntil <= now:
                    startAt = max(now, s.nextAvailable)
                    s.nextAvailable = startAt + self._minInterval
                    s.inFlight += 1
                    return s, max(0.0, startAt - now)
            # 2. 전부 cooldown — 가장 빨리 풀리는 slot 대기
            best = min(self._slots, key=lambda s: s.coolDownUntil)
            startAt = best.coolDownUntil
            best.nextAvailable = startAt + self._minInterval
            best.inFlight += 1
            return best, max(0.0, startAt - now)

    def _releaseSlot(self, slot: _KeySlot) -> None:
        with self._poolLock:
            slot.inFlight = max(0, slot.inFlight - 1)

    def _markCoolDown(self, slot: _KeySlot) -> None:
        with self._poolLock:
            slot.coolDownUntil = time.monotonic() + _COOLDOWN_SEC
            slot.failures += 1

    def _allSlotsCoolingDown(self) -> bool:
        now = time.monotonic()
        with self._poolLock:
            return all(s.coolDownUntil > now for s in self._slots)

    def _getWithTransientRetry(self, url: str, params: dict[str, Any], timeout: float) -> httpx.Response:
        """전송 계층 일시 장애에 한정 재시도하는 GET. 연결 단계 실패는 긴 백오프로 따로 재시도한다.

        애플리케이션 status(013/020 등)와 무관한 전송 계층 장애만 이 계층에서 흡수한다. 슬롯·키
        로테이션·020 cooldown 은 호출자 루프가 그대로 맡고, 4xx·정상 응답은 즉시 반환해 호출자가
        status 를 판정한다. 실패는 두 갈래로 나눠 시도 횟수를 따로 센다.

        1. 연결 단계 실패(``httpx.ConnectTimeout``·``httpx.ConnectError``). 요청이 송신되기 전이라
           재시도가 안전하다. OpenDART 는 단일 A 레코드라 TCP 연결이 수 분(실측 3~7분) 막히는 구간이
           있는데, 예전에는 connect 타임아웃이 요청 전체 timeout 과 같고 백오프가 0.5초·1초라 3회가
           모두 같은 불통 구간 안에서 소진돼 잡이 죽었다. 이제 connect 타임아웃은
           ``min(timeout, 10)`` 초로 줄여 불통을 빨리 감지하고, ``_CONNECT_BACKOFF_SEC``
           (5·15·30·60·90초, 끝값 반복, ±20% jitter)만큼 기다린 뒤 다시 붙는다. 시도 횟수는 env
           ``DARTLAB_DART_CONNECT_RETRY_ATTEMPTS`` (기본 3, 최소 1, 정수가 아니면 3)로 정한다.
        2. 그 밖의 전송 장애(``httpx.RemoteProtocolError``·``httpx.ReadTimeout`` 등)와 일시 5xx.
           DART 가 드물게 응답 없이 끊거나 일시 5xx 를 내던 단발 장애로, 예전엔 재시도 없이
           propagate 돼 한 번의 끊김이 파이프라인 잡 전체를 죽였다(Original SSOT Sync
           dart-reconcile). ``_TRANSIENT_RETRIES`` 회까지 ``_TRANSIENT_BACKOFF_SEC`` 지수
           백오프(0.5초, 1초)로 짧게 재시도한다.

        어느 한 갈래라도 시도 횟수를 다 쓰면 그 갈래의 마지막 예외를 그대로 올린다.

        Args:
            url: 요청 URL.
            params: 쿼리 파라미터 (crtfc_key 포함).
            timeout: 요청 타임아웃 (초). read·write·pool 에 그대로 쓰고 connect 만
                ``min(timeout, 10)`` 초로 줄인다.

        Returns:
            httpx.Response: 전송 성공 응답 (status_code < 500 보장, 2xx 는 비보장).
            raise_for_status / status 판정은 호출자 책임.

        Raises:
            httpx.ConnectTimeout | httpx.ConnectError: 연결 단계 재시도 소진 후 마지막 예외.
            httpx.TransportError | httpx.HTTPStatusError: 그 밖의 전송 장애·5xx 재시도 소진 후 마지막 예외.

        Example:
            >>> callable(DartClient._getWithTransientRetry)
            True
        """
        requestTimeout = httpx.Timeout(timeout, connect=min(timeout, _CONNECT_TIMEOUT_SEC))
        connectAttempts = _connectRetryAttempts()
        connectFailures = 0
        transientFailures = 0
        lastExc: Exception
        while True:
            try:
                resp = self._session.get(url, params=params, timeout=requestTimeout)
            except (httpx.ConnectTimeout, httpx.ConnectError) as exc:
                # 연결 단계 실패. 요청 미송신이라 재시도가 안전하고, 긴 백오프로 불통 구간을 넘긴다.
                connectFailures += 1
                if connectFailures >= connectAttempts:
                    raise
                wait = _connectBackoffWait(connectFailures - 1)
                # url 은 BASE_URL/endpoint 뿐이다(crtfc_key 는 params 라 로그에 남지 않는다).
                _log.warning(
                    "DART 연결 실패 %s: %s, %.1f초 후 재시도 (%d/%d) url=%s",
                    type(exc).__name__,
                    exc,
                    wait,
                    connectFailures,
                    connectAttempts - 1,
                    url,
                )
                time.sleep(wait)
                continue
            except httpx.TransportError as exc:  # 연결 끊김·read 타임아웃 등 그 밖의 전송 계층 장애
                lastExc = exc
            else:
                if resp.status_code < 500:
                    return resp
                lastExc = httpx.HTTPStatusError(
                    f"DART 일시 서버 오류 {resp.status_code}", request=resp.request, response=resp
                )
            transientFailures += 1
            if transientFailures >= _TRANSIENT_RETRIES:
                raise lastExc
            time.sleep(_TRANSIENT_BACKOFF_SEC * (2 ** (transientFailures - 1)))

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

        Raises:
            없음.

        Example:
            >>> getJson(...)

        Args:
            endpoint: DART API endpoint (예 "company.json").
            params: 요청 파라미터 dict. None 이면 빈 dict.
            emptyOn013: True 면 DART status="013" (조회 결과 없음) 을 빈 결과로 변환.

        Returns:
            dict[str, Any] — DART OpenAPI JSON 응답.

        SeeAlso:
            - ``resolveDartKeys`` — 멀티 키 resolve.
            - ``Dart`` facade — 본 client wrapper.

        Requires:
            - dartlab
            - httpx
            - polars
            - time

        Capabilities:
            - DART OpenAPI HTTP 호출 + 멀티 키 로테이션 + rate limit 분산 + DataFrame 변환.
              에러 코드 013 (empty result) 옵션 처리.

        Guide:
            - 사용자 facade 는 ``Dart()`` — 본 클래스 직접 사용 X.

        AIContext:
            internal HTTP client — AI 직접 호출 X.

        LLM Specifications:
            AntiPatterns:
                - DartApiError (status="013" 등) 미처리 → 예외 propagate. caller try/except 의무.
                - 단일 키로 분당 580 req 초과 → rate limit. 멀티 키 (DART_API_KEYS) 사용.
            OutputSchema:
                - pl.DataFrame / dict / bytes — endpoint 별.
            Prerequisites:
                - 인터넷 + DART_API_KEY 또는 DART_API_KEYS.
            Freshness:
                - DART OpenAPI 실시간 (분 단위).
            Dataflow:
                - 사용자 인자 → httpx → DART API → 응답 정규화 → 본 함수.
            TargetMarkets:
                - KR (DART) 한정.
        """
        url = f"{BASE_URL}/{endpoint}"
        cooldownAttempts = 0
        maxCooldownAttempts = max(2 * len(self._slots), 4)
        while cooldownAttempts < maxCooldownAttempts:
            slot, sleepFor = self._acquireSlot()
            if sleepFor > 0:
                time.sleep(sleepFor)
            try:
                merged = {"crtfc_key": slot.key}
                if params:
                    merged.update(params)
                resp = self._getWithTransientRetry(url, merged, 30)
                resp.raise_for_status()
                data = resp.json()
                status = data.get("status", "000")
                if status == "000":
                    return data
                if status == "013" and emptyOn013:
                    return {}
                if status == "020":
                    self._markCoolDown(slot)
                    cooldownAttempts += 1
                    if self._allSlotsCoolingDown():
                        time.sleep(1.0)
                    continue
                msg = data.get("message", _ERROR_MESSAGES.get(status, "알 수 없는 오류"))
                raise DartApiError(status, msg)
            finally:
                self._releaseSlot(slot)

        msg = _ERROR_MESSAGES.get("020", "요청 제한 초과")
        raise DartApiError("020", f"{msg} (모든 키 cooldown)")

    def getBytes(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> bytes:
        """바이너리 엔드포인트 호출 (ZIP, XML 다운로드 등).

        JSON 에러 응답도 감지하고, rate limit 시 키 로테이션.

        Args:
            endpoint: 인자.
            params: 인자.

        Raises:
            없음.

        Example:
            >>> getBytes(...)

        Returns:
            bytes — DART OpenAPI binary 응답.

        SeeAlso:
            - ``resolveDartKeys`` — 멀티 키 resolve.
            - ``Dart`` facade — 본 client wrapper.

        Requires:
            - dartlab
            - httpx
            - polars
            - time

        Capabilities:
            - DART OpenAPI HTTP 호출 + 멀티 키 로테이션 + rate limit 분산 + DataFrame 변환.
              에러 코드 013 (empty result) 옵션 처리.

        Guide:
            - 사용자 facade 는 ``Dart()`` — 본 클래스 직접 사용 X.

        AIContext:
            internal HTTP client — AI 직접 호출 X.

        LLM Specifications:
            AntiPatterns:
                - DartApiError (status="013" 등) 미처리 → 예외 propagate. caller try/except 의무.
                - 단일 키로 분당 580 req 초과 → rate limit. 멀티 키 (DART_API_KEYS) 사용.
            OutputSchema:
                - pl.DataFrame / dict / bytes — endpoint 별.
            Prerequisites:
                - 인터넷 + DART_API_KEY 또는 DART_API_KEYS.
            Freshness:
                - DART OpenAPI 실시간 (분 단위).
            Dataflow:
                - 사용자 인자 → httpx → DART API → 응답 정규화 → 본 함수.
            TargetMarkets:
                - KR (DART) 한정.
        """
        url = f"{BASE_URL}/{endpoint}"
        cooldownAttempts = 0
        maxCooldownAttempts = max(2 * len(self._slots), 4)
        while cooldownAttempts < maxCooldownAttempts:
            slot, sleepFor = self._acquireSlot()
            if sleepFor > 0:
                time.sleep(sleepFor)
            try:
                merged = {"crtfc_key": slot.key}
                if params:
                    merged.update(params)
                resp = self._getWithTransientRetry(url, merged, 60)
                resp.raise_for_status()
                # OpenDART 는 바이너리 에러 시에도 JSON 반환 가능.
                contentType = resp.headers.get("Content-Type", "")
                if "application/json" in contentType or "text/json" in contentType:
                    data = resp.json()
                    status = data.get("status", "000")
                    if status == "020":
                        self._markCoolDown(slot)
                        cooldownAttempts += 1
                        if self._allSlotsCoolingDown():
                            time.sleep(1.0)
                        continue
                    if status != "000":
                        msg = data.get("message", _ERROR_MESSAGES.get(status, "알 수 없는 오류"))
                        raise DartApiError(status, msg)
                return resp.content
            finally:
                self._releaseSlot(slot)

        raise DartApiError("020", "요청 제한 초과 (모든 키 cooldown)")

    def getDf(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        listKey: str = "list",
    ) -> pl.DataFrame:
        """JSON → Polars DataFrame. 데이터 없으면 빈 DataFrame.

        Args:
            endpoint: 인자.
            params: 인자.
            listKey: 인자.

        Raises:
            없음.

        Example:
            >>> getDf(...)

        Returns:
            pl.DataFrame — DART OpenAPI 응답 정규화 결과.

        SeeAlso:
            - ``resolveDartKeys`` — 멀티 키 resolve.
            - ``Dart`` facade — 본 client wrapper.

        Requires:
            - dartlab
            - httpx
            - polars
            - time

        Capabilities:
            - DART OpenAPI HTTP 호출 + 멀티 키 로테이션 + rate limit 분산 + DataFrame 변환.
              에러 코드 013 (empty result) 옵션 처리.

        Guide:
            - 사용자 facade 는 ``Dart()`` — 본 클래스 직접 사용 X.

        AIContext:
            internal HTTP client — AI 직접 호출 X.

        LLM Specifications:
            AntiPatterns:
                - DartApiError (status="013" 등) 미처리 → 예외 propagate. caller try/except 의무.
                - 단일 키로 분당 580 req 초과 → rate limit. 멀티 키 (DART_API_KEYS) 사용.
            OutputSchema:
                - pl.DataFrame / dict / bytes — endpoint 별.
            Prerequisites:
                - 인터넷 + DART_API_KEY 또는 DART_API_KEYS.
            Freshness:
                - DART OpenAPI 실시간 (분 단위).
            Dataflow:
                - 사용자 인자 → httpx → DART API → 응답 정규화 → 본 함수.
            TargetMarkets:
                - KR (DART) 한정.
        """
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
        """자동 페이지네이션 → 전체 결과 Polars DataFrame.

        Args:
            endpoint: 인자.
            params: 인자.
            listKey: 인자.
            pageSize: 인자.

        Raises:
            없음.

        Example:
            >>> getDfAll(...)

        Returns:
            pl.DataFrame — DART OpenAPI 응답 정규화 결과.

        SeeAlso:
            - ``resolveDartKeys`` — 멀티 키 resolve.
            - ``Dart`` facade — 본 client wrapper.

        Requires:
            - dartlab
            - httpx
            - polars
            - time

        Capabilities:
            - DART OpenAPI HTTP 호출 + 멀티 키 로테이션 + rate limit 분산 + DataFrame 변환.
              에러 코드 013 (empty result) 옵션 처리.

        Guide:
            - 사용자 facade 는 ``Dart()`` — 본 클래스 직접 사용 X.

        AIContext:
            internal HTTP client — AI 직접 호출 X.

        LLM Specifications:
            AntiPatterns:
                - DartApiError (status="013" 등) 미처리 → 예외 propagate. caller try/except 의무.
                - 단일 키로 분당 580 req 초과 → rate limit. 멀티 키 (DART_API_KEYS) 사용.
            OutputSchema:
                - pl.DataFrame / dict / bytes — endpoint 별.
            Prerequisites:
                - 인터넷 + DART_API_KEY 또는 DART_API_KEYS.
            Freshness:
                - DART OpenAPI 실시간 (분 단위).
            Dataflow:
                - 사용자 인자 → httpx → DART API → 응답 정규화 → 본 함수.
            TargetMarkets:
                - KR (DART) 한정.
        """
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


# ── DartFetchProvider 구현 + register (정공법 B — DIP) ─────────────
# providers build/read 가 core.dartClient seam 으로 client·키를 얻는다 (providers↛gather).


class _DartFetchProvider:
    """core.dartClient.DartFetchProvider 구현 — gather 가 DART fetch 전담."""

    def makeClient(self, apiKey=None, apiKeys=None, requestsPerMinute=580):
        """멀티 키 DartClient 인스턴스 생성.

        Args:
            apiKey: 단일 DART API 키 (None=env/.env 해소).
            apiKeys: 다중 키 list (rate-limit 분산).
            requestsPerMinute: 분당 요청 상한 (키별).

        Returns:
            DartClient — 멀티 키 rate-limit HTTP 클라이언트.

        Raises:
            없음.

        Example:
            >>> _DartFetchProvider().makeClient()  # doctest: +SKIP
        """
        return DartClient(apiKey=apiKey, apiKeys=apiKeys, requestsPerMinute=requestsPerMinute)

    def resolveKeys(self, apiKey=None, apiKeys=None):
        """DART API 키 list resolve."""
        return resolveDartKeys(apiKey=apiKey, apiKeys=apiKeys)

    def hasKey(self):
        """DART API 키 설정 여부."""
        from dartlab.gather.dart.keys import hasDartApiKey

        return hasDartApiKey()

    def call(self, module, func, *args, **kwargs):
        """gather/dart.<module>.<func> 위임 호출 (fetch orchestration — providers seam).

        Args:
            module: gather/dart 하위 모듈명 (예 "dart", "allFilingsCollector").
            func: 모듈 내 함수/심볼명.
            *args: 위임 함수로 forward.
            **kwargs: 위임 함수로 forward.

        Returns:
            위임 함수의 반환값 (fetch orchestration 출력).

        Raises:
            ImportError: module 미존재. AttributeError: func 미존재.

        Example:
            >>> _DartFetchProvider().call("allFilingsCollector", "metaSuffix")  # doctest: +SKIP
        """
        import importlib

        mod = importlib.import_module(f"dartlab.gather.dart.{module}")
        return getattr(mod, func)(*args, **kwargs)


registerDartFetchProvider(_DartFetchProvider())
