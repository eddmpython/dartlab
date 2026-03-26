"""주가 데이터 통합.

yfinance를 통해 KR/US 주가를 가져온다. 선택적 의존성.

사용법::

    from dartlab.analysis.comparative.event.price import get_prices

    # 한국 — 005930.KS 형식으로 변환
    df = get_prices("005930", start="2023-01-01", end="2024-12-31")

    # 미국
    df = get_prices("AAPL", start="2023-01-01", end="2024-12-31")
"""

from __future__ import annotations

import polars as pl


def _yf_ticker(stock_code: str, market: str = "KR") -> str:
    """종목코드를 yfinance ticker로 변환."""
    if market == "KR":
        return f"{stock_code}.KS"
    return stock_code


def _ensure_yfinance():
    """yfinance 설치 확인."""
    try:
        import yfinance  # noqa: F401
    except ImportError:
        raise ImportError(
            "주가 데이터에는 yfinance가 필요합니다.\n설치: pip install yfinance\n또는: pip install dartlab[event]"
        )


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
    _ensure_yfinance()
    import yfinance as yf

    ticker = _yf_ticker(stock_code, market)
    data = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)

    if data.empty:
        return pl.DataFrame(schema={"date": pl.Date, "close": pl.Float64, "returns": pl.Float64})

    # pandas → polars 변환
    data = data.reset_index()

    # yfinance가 MultiIndex 컬럼을 반환하는 경우 처리
    if hasattr(data.columns, "levels"):
        data.columns = [c[0] if isinstance(c, tuple) else c for c in data.columns]

    df = pl.from_pandas(data[["Date", "Close"]].rename(columns={"Date": "date", "Close": "close"}))
    df = df.with_columns(
        pl.col("date").cast(pl.Date),
        pl.col("close").cast(pl.Float64),
    )
    df = df.sort("date")

    # 일별 수익률 계산
    df = df.with_columns(
        (pl.col("close") / pl.col("close").shift(1) - 1.0).alias("returns"),
    )

    return df


def get_market_returns(
    *,
    start: str,
    end: str,
    market: str = "KR",
) -> pl.DataFrame:
    """시장 벤치마크 수익률.

    Args:
        start: 시작일.
        end: 종료일.
        market: "KR" (KOSPI) 또는 "US" (S&P 500).

    Returns:
        date, close, returns 컬럼의 DataFrame.
    """
    _ensure_yfinance()
    import yfinance as yf

    ticker = "^KS11" if market == "KR" else "^GSPC"
    data = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)

    if data.empty:
        return pl.DataFrame(schema={"date": pl.Date, "close": pl.Float64, "returns": pl.Float64})

    data = data.reset_index()
    if hasattr(data.columns, "levels"):
        data.columns = [c[0] if isinstance(c, tuple) else c for c in data.columns]

    df = pl.from_pandas(data[["Date", "Close"]].rename(columns={"Date": "date", "Close": "close"}))
    df = df.with_columns(
        pl.col("date").cast(pl.Date),
        pl.col("close").cast(pl.Float64),
    )
    df = df.sort("date")
    df = df.with_columns(
        (pl.col("close") / pl.col("close").shift(1) - 1.0).alias("returns"),
    )

    return df
