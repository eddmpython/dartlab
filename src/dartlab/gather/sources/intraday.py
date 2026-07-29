"""분봉 fetch facade. KR Naver 전용 (async).

당일 + 과거 세션 1분봉 OHLCV. domains.naver.fetchIntraday 로 위임한다.
일봉(history)과 달리 KR Naver 만 분봉을 제공하므로 fallback 체인은 없다.
"""

from __future__ import annotations

import logging
from typing import Awaitable, Callable, cast

from ..domains import loadDomain
from ..infra.resilience import circuitBreaker
from ..types import (
    CircuitOpenError,
    SourceAttemptsExhaustedError,
    SourceUnavailableError,
)

log = logging.getLogger(__name__)


async def fetch(
    stockCode: str,
    *,
    market: str = "KR",
    start: str = "",
    end: str = "",
    client=None,
    limit: int | None = None,
) -> list[dict]:
    """1분봉 OHLCV. KR Naver 위임 (async).

    Capabilities: KR Naver 1분봉 (당일 + start/end 과거 세션 + 휴장일 폴백).
    AIContext: mixin.price(interval=...) 의 backend. 분 단위 가격 원천.
    Guide: KR 전용. market 이 "KR" 아니면 ValueError.
    When: gather("price", ..., interval="1m") 호출 시.
    How: loadDomain("naver").fetchIntraday 로 list[dict].

    Parameters
    ----------
    stock_code : str
        종목코드 (예: ``"005930"``).
    market : str
        시장 코드. ``"KR"`` 외에는 ValueError.
    start : str
        시작 시각 (``"2026-07-03"`` 또는 ``"202607030930"``). 빈 문자열이면 당일.
    end : str
        종료 시각. 빈 문자열이면 start 부터 현재까지.
    client : httpx.AsyncClient | None
        HTTP 클라이언트. None이면 GatherHttpClient 자동 생성.
    limit : int | None
        반환 행수 상한 (가장 최근 N분). None이면 전체.

    Returns
    -------
    list[dict]
        1분봉 OHLCV 리스트. 각 dict 키:

        - datetime : str. ISO8601 (``YYYY-MM-DDTHH:MM:SS``, KST)
        - open : float. 시가 (원)
        - high : float. 고가 (원)
        - low : float. 저가 (원)
        - close : float. 종가 (원)
        - volume : int. 누적 거래량 (주)

        유효한 응답에 분봉이 없으면 빈 리스트.

    Raises
    ------
    ValueError
        KR 외 시장 또는 잘못된 종목코드.
    SourceAttemptsExhaustedError
        Naver source가 실패하거나 circuit open인 경우.

    Example
    -------
    >>> rows = await fetch("005930", market="KR")
    >>> past = await fetch("005930", start="2026-07-03")

    Requires
    --------
    네트워크 (``api.stock.naver.com`` minute 엔드포인트) + KR 6 자리 종목코드.
    API 키 불필요.

    See Also
    --------
    dartlab.gather.domains.naver.fetchIntraday : KR 분봉 backend.
    dartlab.gather.sources.history.fetch : 일봉 fallback 체인.
    """
    if market != "KR":
        raise ValueError(f"intraday는 KR 시장만 지원합니다: {market!r}")

    if client is None:
        from ..infra.http import GatherHttpClient

        client = GatherHttpClient()

    if circuitBreaker.isOpen("naver"):
        error = CircuitOpenError("naver circuit breaker가 열려 있습니다")
        raise SourceAttemptsExhaustedError("intraday", [("naver", error)])

    try:
        module = loadDomain("naver")
        fetchIntraday = getattr(module, "fetchIntraday", None)
        if not callable(fetchIntraday):
            raise SourceUnavailableError("naver에 fetchIntraday 구현이 없습니다")
        fetchIntradayFn = cast(Callable[..., Awaitable[list[dict]]], fetchIntraday)
        rows = await fetchIntradayFn(
            stockCode,
            client,
            market=market,
            start=start,
            end=end,
            limit=limit,
        )
        if not isinstance(rows, list):
            raise TypeError(f"naver.fetchIntraday가 list가 아닌 {type(rows).__name__}을 반환했습니다")
        return rows
    except ValueError:
        raise
    except Exception as exc:
        log.warning("intraday source 실패 (%s): %s", stockCode, exc)
        raise SourceAttemptsExhaustedError("intraday", [("naver", exc)]) from exc
