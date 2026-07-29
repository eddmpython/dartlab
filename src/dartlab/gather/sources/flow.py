"""수급 fallback facade — 한국 전용 (naver)."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from typing import cast

from ..domains import FLOW_FALLBACK, loadDomain
from ..infra.resilience import circuitBreaker
from ..types import CircuitOpenError, SourceAttemptsExhaustedError, SourceUnavailableError

log = logging.getLogger(__name__)


async def fetch(
    stockCode: str,
    *,
    market: str = "KR",
    client=None,
    start: str | None = None,
    end: str | None = None,
    limit: int | None = None,
    pageSize: int | None = None,
    sleepSec: float = 0.0,
    marketType: str = "KRX",
    maxPages: int | None = None,
    full: bool = False,
    proxy: str | None = None,
) -> list[dict]:
    """수급 시계열 — fallback 체인 (async). KR만 지원.

    Capabilities:
        - FLOW_FALLBACK 체인 순차 시도 (Naver → 다음)
        - 첫 성공 source 결과 반환

    AIContext:
        - mixin.flow 의 backend — KR 수급 axis 의 source-level 진입점

    Guide:
        market 인자가 "KR" 외이면 ValueError. provider 가 KR 한정.

    When:
        gather.flow() 호출 시 (lazy fallback chain).

    How:
        FLOW_FALLBACK 의 도메인 순서대로 호출 → 첫 성공 결과 .

    Parameters
    ----------
    stock_code : str
        종목코드 (예: "005930").
    market : str
        시장 코드. "KR"만 지원.
    client : httpx.AsyncClient | None
        HTTP 클라이언트. None이면 도메인 내부에서 생성.
    start, end : str | None
        조회 기간. 지정 시 Naver 페이지네이션으로 과거 구간까지 조회.
    limit : int | None
        반환 행수 상한 (가장 최근 N개). None이면 기간 조건까지 조회.
    pageSize : int | None
        호환용 고급 옵션. None이면 source 제한에 맞춰 자동 페이지네이션.
    sleepSec : float
        페이지 호출 사이 대기 시간.
    full : bool
        True면 가능한 전체 이력을 끝까지 자동 수집.
    proxy : str | None
        사용자 제공 HTTP(S) 프록시 URL.

    Returns
    -------
    list[dict]
        수급 시계열 리스트. 각 dict 키:

        - date : str — 거래일 (YYYY-MM-DD)
        - foreignNet : float — 외국인 순매수 (주)
        - institutionNet : float — 기관 순매수 (주)
        - individualNet : float — 개인 순매수 (주)
        - source : str. 실제 응답을 제공한 fallback source
        - fetchedAt : str. facade 수집 완료 시각 (UTC ISO 형식)

        하나 이상의 source가 정상 응답했지만 데이터가 없으면 빈 리스트.

    Requires:
        네트워크 (KR Naver 직접 호출).

    Raises
    ------
    ValueError
        market이 "KR"이 아닌 경우.
    SourceAttemptsExhaustedError
        모든 fallback source가 실패하거나 circuit open으로 차단된 경우.

    Example
    -------
    >>> rows = await fetch("005930", market="KR", limit=20)

    See Also:
        ``dartlab.gather.domains.naver.fetchFlow`` — primary fallback target.
    """
    if market != "KR":
        raise ValueError(f"flow는 KR 시장만 지원합니다: {market!r}")

    attempts: list[tuple[str, Exception]] = []
    hadSuccessfulResponse = False
    for domainName in FLOW_FALLBACK:
        if circuitBreaker.isOpen(domainName):
            attempts.append((domainName, CircuitOpenError(f"{domainName} circuit이 open 상태입니다")))
            continue

        try:
            module = loadDomain(domainName)
            fetchFlow = getattr(module, "fetchFlow", None)
            if not callable(fetchFlow):
                raise AttributeError(f"{domainName} source에 fetchFlow callable이 없습니다")

            fetchFlowAsync = cast(Callable[..., Awaitable[list[dict] | None]], fetchFlow)
            result = await fetchFlowAsync(
                stockCode,
                client,
                start=start,
                end=end,
                limit=limit,
                pageSize=pageSize,
                sleepSec=sleepSec,
                marketType=marketType,
                maxPages=maxPages,
                full=full,
                proxy=proxy,
            )
            if result is None:
                result = []
            if not isinstance(result, list) or any(not isinstance(row, dict) for row in result):
                raise TypeError(f"{domainName} fetchFlow는 list[dict]를 반환해야 합니다")

            circuitBreaker.recordSuccess(domainName)
            hadSuccessfulResponse = True
            if result:
                fetchedAt = datetime.now(timezone.utc).isoformat()
                rows = [{**row, "source": domainName, "fetchedAt": fetchedAt} for row in result]
                if limit is not None and limit > 0:
                    return rows[:limit]
                return rows
        except ValueError:
            raise
        except Exception as exc:
            circuitBreaker.recordFailure(domainName)
            attempts.append((domainName, exc))
            log.debug("flow fallback %s 실패: %s", domainName, exc)

    if hadSuccessfulResponse:
        return []

    if not attempts:
        attempts.append(("<fallback-chain>", SourceUnavailableError("설정된 flow source가 없습니다")))
    error = SourceAttemptsExhaustedError("flow", attempts)
    raise error from attempts[-1][1]
