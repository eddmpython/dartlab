"""히스토리 fallback facade — naver(KR) → naver_global → fmp 순서 (async)."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from typing import cast

from ..domains import HISTORY_FALLBACK, loadDomain
from ..infra.resilience import circuitBreaker
from ..types import CircuitOpenError, SourceAttemptsExhaustedError, SourceUnavailableError

log = logging.getLogger(__name__)


async def fetch(
    stockCode: str,
    *,
    start: str,
    end: str,
    market: str = "KR",
    client=None,
    limit: int | None = None,
) -> list[dict]:
    """히스토리 OHLCV — fallback 체인 (async).

    Capabilities:
        - HISTORY_FALLBACK 체인 — Naver(KR) → naver_global → FMP → Yahoo
        - 첫 성공 source 결과 반환

    AIContext:
        - mixin.history 의 backend — quant 백테스트 데이터 원천

    Guide:
        market="KR" 이면 Naver 최우선. 외 시장은 fallback 체인만.

    When:
        gather.history(start, end) 호출 시.

    How:
        chain 구성 → 순차 시도 → 빈 결과면 다음 fallback.

    Requires:
        네트워크 (외부 OHLCV provider).

    Parameters
    ----------
    stock_code : str
        종목코드/티커 (예: "005930", "AAPL").
    start : str
        조회 시작일 (ISO 형식, 예: "2024-01-01").
    end : str
        조회 종료일 (ISO 형식, 예: "2024-12-31").
    market : str
        시장 코드 ("KR", "US" 등). 기본 "KR".
    client : httpx.AsyncClient | None
        HTTP 클라이언트. None이면 GatherHttpClient 자동 생성.
    limit : int | None
        반환 행수 상한 (가장 최근 N일). None이면 [start, end] 전체.

    Returns
    -------
    list[dict]
        일별 OHLCV 리스트. 각 dict 키:

        - date : str — 거래일 (YYYY-MM-DD)
        - open : float — 시가 (원 또는 해당 통화)
        - high : float — 고가 (원)
        - low : float — 저가 (원)
        - close : float — 종가 (원)
        - volume : int — 거래량 (주)
        - source : str. 실제 응답을 제공한 fallback source
        - fetchedAt : str. facade 수집 완료 시각 (UTC ISO 형식)

        하나 이상의 source가 정상 응답했지만 데이터가 없으면 빈 리스트.

    Raises
    ------
    SourceAttemptsExhaustedError
        모든 fallback source가 실패하거나 circuit open으로 차단된 경우.

    Example
    -------
    >>> rows = await fetch("005930", start="2024-01-01", end="2024-12-31", limit=10)

    See Also:
        ``dartlab.gather.domains.naver.fetchHistory`` — KR primary.
        ``dartlab.gather.domains.fdr.fetchHistory`` — Korean global fallback.
    """
    chain: list[str] = []
    # KR → naver 최우선
    if market == "KR":
        chain.append("naver")
    chain.extend(HISTORY_FALLBACK)
    if "fmp" not in chain:
        chain.append("fmp")
    # 중복 제거 (순서 유지)
    seen: set[str] = set()
    chain = [s for s in chain if not (s in seen or seen.add(s))]  # type: ignore[func-returns-value]

    # client=None이면 자체 생성 (price.py와 동일 패턴)
    if client is None:
        from ..infra.http import GatherHttpClient

        client = GatherHttpClient()

    attempts: list[tuple[str, Exception]] = []
    hadSuccessfulResponse = False

    for source_name in chain:
        if circuitBreaker.isOpen(source_name):
            attempts.append((source_name, CircuitOpenError(f"{source_name} circuit이 open 상태입니다")))
            continue

        try:
            module = loadDomain(source_name)
            fetchHistory = getattr(module, "fetchHistory", None)
            if not callable(fetchHistory):
                raise AttributeError(f"{source_name} source에 fetchHistory callable이 없습니다")

            fetchHistoryAsync = cast(Callable[..., Awaitable[list[dict] | None]], fetchHistory)
            result = await fetchHistoryAsync(
                stockCode,
                client,
                start=start,
                end=end,
                market=market,
            )
            if result is None:
                result = []
            if not isinstance(result, list) or any(not isinstance(row, dict) for row in result):
                raise TypeError(f"{source_name} fetchHistory는 list[dict]를 반환해야 합니다")

            circuitBreaker.recordSuccess(source_name)
            hadSuccessfulResponse = True
            if result:
                fetchedAt = datetime.now(timezone.utc).isoformat()
                rows = [{**row, "source": source_name, "fetchedAt": fetchedAt} for row in result]
                if limit is not None and limit > 0:
                    return rows[-limit:]
                return rows

        except ValueError:
            raise
        except Exception as exc:
            circuitBreaker.recordFailure(source_name)
            attempts.append((source_name, exc))
            log.debug("history fallback %s 실패: %s", source_name, exc)

    if hadSuccessfulResponse:
        return []

    if not attempts:
        attempts.append(("<fallback-chain>", SourceUnavailableError("설정된 history source가 없습니다")))
    error = SourceAttemptsExhaustedError("history", attempts)
    raise error from attempts[-1][1]
