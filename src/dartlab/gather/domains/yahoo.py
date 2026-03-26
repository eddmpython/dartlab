"""Yahoo Finance 데이터 수집 — yfinance 기반 주가 + 히스토리.

yfinance는 선택적 의존성. 미설치 시 None 반환.
yfinance 자체가 동기 라이브러리이므로 fetch_price/fetch_history는 동기 유지.
async 컨텍스트에서는 asyncio.to_thread()로 호출.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

import polars as pl

from ..types import GatherResult, PriceSnapshot

log = logging.getLogger(__name__)


def _yf_ticker(stock_code: str, market: str = "KR") -> str:
    """종목코드를 yfinance ticker로 변환."""
    if market == "KR":
        return f"{stock_code}.KS"
    return stock_code


def _ensure_yfinance():
    """yfinance 설치 확인. 없으면 ImportError."""
    try:
        import yfinance  # noqa: F401
    except ImportError:
        raise ImportError(
            "주가 데이터에는 yfinance가 필요합니다.\n설치: pip install yfinance\n또는: pip install dartlab[event]"
        )


# ══════════════════════════════════════
# 주가
# ══════════════════════════════════════


def fetch_price(stock_code: str, client=None, *, market: str = "KR") -> PriceSnapshot | None:
    """yfinance → 현재가 + 52주 범위.

    client 파라미터는 도메인 인터페이스 통일용 (yfinance는 자체 HTTP 사용).
    """
    try:
        _ensure_yfinance()
        import yfinance as yf
    except ImportError:
        log.debug("yfinance 미설치 — yahoo price skip")
        return None

    ticker = _yf_ticker(stock_code, market)
    try:
        info = yf.Ticker(ticker).info
    except (ValueError, KeyError, OSError) as exc:
        log.warning("yahoo price 실패 (%s): %s", stock_code, exc)
        return None

    if not info or "regularMarketPrice" not in info:
        return None

    current = info.get("regularMarketPrice", 0)
    if not current:
        return None

    return PriceSnapshot(
        current=float(current),
        change=float(info.get("regularMarketChange", 0) or 0),
        change_pct=float(info.get("regularMarketChangePercent", 0) or 0),
        high_52w=float(info.get("fiftyTwoWeekHigh", 0) or 0),
        low_52w=float(info.get("fiftyTwoWeekLow", 0) or 0),
        volume=int(info.get("regularMarketVolume", 0) or 0),
        market_cap=float(info.get("marketCap", 0) or 0),
        per=info.get("trailingPE"),
        pbr=info.get("priceToBook"),
        dividend_yield=info.get("dividendYield"),
        source="yahoo",
        fetched_at=datetime.now(timezone.utc).isoformat(),
    )


# ══════════════════════════════════════
# 히스토리
# ══════════════════════════════════════


def fetch_history(
    stock_code: str,
    *,
    start: str,
    end: str,
    market: str = "KR",
) -> pl.DataFrame:
    """yfinance → 일별 히스토리 DataFrame (date, close, returns)."""
    _ensure_yfinance()
    import yfinance as yf

    ticker = _yf_ticker(stock_code, market)
    data = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)

    empty_schema = {"date": pl.Date, "close": pl.Float64, "returns": pl.Float64}
    if data.empty:
        return pl.DataFrame(schema=empty_schema)

    data = data.reset_index()
    # yfinance MultiIndex 컬럼 처리
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


def fetch_market_returns(
    *,
    start: str,
    end: str,
    market: str = "KR",
) -> pl.DataFrame:
    """시장 벤치마크 수익률 (KOSPI / S&P 500)."""
    ticker_code = "^KS11" if market == "KR" else "^GSPC"
    return fetch_history(ticker_code, start=start, end=end, market="US")


# ══════════════════════════════════════
# 통합 수집
# ══════════════════════════════════════


async def fetch_all(stock_code: str, client=None, *, market: str = "KR") -> GatherResult:
    """yahoo에서 가져올 수 있는 모든 데이터를 수집.

    yfinance는 동기 라이브러리 → asyncio.to_thread()로 블로킹 회피.
    """
    result = GatherResult(domain="yahoo")
    try:
        result.price = await asyncio.to_thread(fetch_price, stock_code, client, market=market)
    except ImportError:
        result.error = "yfinance 미설치"
    except OSError as exc:
        result.error = str(exc)
    return result
