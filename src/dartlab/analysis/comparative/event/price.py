"""주가 데이터 통합 — gather 인프라 기반.

gather/history + gather/domains/yahoo_direct를 활용하여
KR/US 주가 히스토리 + 시장 벤치마크 수익률을 가져온다.

사용법::

    from dartlab.analysis.comparative.event.price import get_prices

    # 한국
    df = get_prices("005930", start="2023-01-01", end="2024-12-31")

    # 미국
    df = get_prices("AAPL", start="2023-01-01", end="2024-12-31", market="US")
"""

from __future__ import annotations

import asyncio
import logging

import polars as pl

log = logging.getLogger(__name__)


def _rows_to_df(rows: list[dict]) -> pl.DataFrame:
    """gather 히스토리 rows → date/close/returns DataFrame."""
    empty = {"date": pl.Date, "close": pl.Float64, "returns": pl.Float64}
    if not rows:
        return pl.DataFrame(schema=empty)

    df = pl.DataFrame(rows)
    df = df.select(
        pl.col("date").cast(pl.Date),
        pl.col("close").cast(pl.Float64),
    ).sort("date")

    df = df.with_columns(
        (pl.col("close") / pl.col("close").shift(1) - 1.0).alias("returns"),
    )
    return df


def _run_async(coro):
    """동기 컨텍스트에서 async 함수 실행."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(lambda: asyncio.run(coro)).result()
    return asyncio.run(coro)


def get_prices(
    stock_code: str,
    *,
    start: str,
    end: str,
    market: str = "KR",
) -> pl.DataFrame:
    """종목의 일별 종가를 가져온다.

    Args:
        stock_code: 종목코드 (KR: "005930", US: "AAPL").
        start: 시작일 (YYYY-MM-DD).
        end: 종료일 (YYYY-MM-DD).
        market: "KR" 또는 "US".

    Returns:
        date, close, returns 컬럼의 DataFrame.
    """
    from dartlab.gather.history import fetch

    rows = _run_async(fetch(stock_code, start=start, end=end, market=market))
    return _rows_to_df(rows)


def get_market_returns(
    *,
    start: str,
    end: str,
    market: str = "KR",
) -> pl.DataFrame:
    """시장 벤치마크 수익률 (KOSPI / S&P 500).

    Args:
        start: 시작일.
        end: 종료일.
        market: "KR" (KOSPI) 또는 "US" (S&P 500).

    Returns:
        date, close, returns 컬럼의 DataFrame.
    """
    from dartlab.gather.domains import yahoo_direct
    from dartlab.gather.http import GatherHttpClient

    ticker = "^KS11" if market == "KR" else "^GSPC"

    async def _fetch():
        client = GatherHttpClient()
        try:
            return await yahoo_direct.fetch_history(ticker, client, start=start, end=end, market="US")
        finally:
            try:
                await client.aclose()
            except AttributeError:
                client.close()

    rows = _run_async(_fetch())
    return _rows_to_df(rows)
