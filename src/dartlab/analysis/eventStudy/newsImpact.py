"""L3 newsImpact — 단일 사건 → CAR + t-stat + 동기간 news context.

calcCAR (MacKinlay 1997) + loadNewsArchive 결합. event window 의 abnormal return
유의성 검정 + ±N 일 news 본 위에 표시. dartwings UI 의 EventSidePanel 의
backend 데이터 SSOT.

진입점:
    newsImpact(stockCode, eventDate, *, market, eventWindow, estimationWindow,
               keyword=None, ohlcvFetcher=None, benchmarkFetcher=None,
               newsLoader=None)
    → dict — car/carPct/tStat/isSignificant/ar/news/interpretation

메모리 가드:
    @withMemoryBudget(200) — 단일 종목 estimation+event window <200MB.
"""

from __future__ import annotations

import logging
from datetime import date as _date
from datetime import datetime, timedelta
from typing import Callable

import numpy as np
import polars as pl

from dartlab.core.logger import logSafe
from dartlab.core.memory import withMemoryBudget

log = logging.getLogger(__name__)


def _toDate(d: str | _date | datetime) -> _date:
    """str/date/datetime → date."""
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, _date):
        return d
    return _date.fromisoformat(str(d))


def _closesToReturns(closes: pl.Series) -> np.ndarray:
    """close Series → log returns array."""
    arr = closes.to_numpy().astype(np.float64)
    if arr.size < 2:
        return np.array([])
    ret = np.diff(arr) / arr[:-1]
    return ret


def _defaultOhlcv(stockCode: str, market: str) -> pl.DataFrame | None:
    """default ohlcv fetcher."""
    try:
        from dartlab.synth.marketDataAccess import fetchOhlcv

        return fetchOhlcv(stockCode, market=market)
    except Exception as exc:
        log.debug("default ohlcv fail %s: %s", logSafe(stockCode), exc)
        return None


def _defaultBenchmark(market: str) -> pl.DataFrame | None:
    """default benchmark fetcher — KOSPI/SPY."""
    try:
        from dartlab.synth.marketDataAccess import fetchBenchmark

        return fetchBenchmark(market=market)
    except Exception as exc:
        log.debug("default benchmark fail: %s", exc)
        return None


def _defaultNewsLoader(start: str, end: str, market: str) -> pl.DataFrame:
    """default news loader — gather.bulkData.newsHeadlines.loadNewsArchive."""
    try:
        from dartlab.gather.bulkData.newsHeadlines import loadNewsArchive

        return loadNewsArchive(start, end, market)
    except Exception as exc:
        log.debug("default newsLoader fail: %s", exc)
        return pl.DataFrame()


@withMemoryBudget(200)
def newsImpact(
    stockCode: str,
    eventDate: str | _date | datetime,
    *,
    market: str = "KR",
    eventWindow: tuple[int, int] = (-1, 5),
    estimationWindow: tuple[int, int] = (-120, -30),
    keyword: str | None = None,
    ohlcvFetcher: Callable[[str, str], pl.DataFrame | None] | None = None,
    benchmarkFetcher: Callable[[str], pl.DataFrame | None] | None = None,
    newsLoader: Callable[[str, str, str], pl.DataFrame] | None = None,
    newsContextDays: int = 3,
) -> dict:
    """단일 사건 → CAR + t-stat + 동기간 news context.

    Args:
        stockCode: 종목코드.
        eventDate: 사건 일자.
        market: "KR" | "US".
        eventWindow: (lo, hi) — eventIdx 상대. 기본 (-1, +5).
        estimationWindow: (lo, hi) — 기본 (-120, -30).
        keyword: news 필터링 키워드 (None 이면 corpName resolve).
        ohlcvFetcher: callable(stockCode, market) → DataFrame (테스트 주입).
        benchmarkFetcher: callable(market) → DataFrame.
        newsLoader: callable(start, end, market) → archive DataFrame.
        newsContextDays: news 동기간 ±N 일.

    Returns:
        dict — stockCode/eventDate/eventIdx/alpha/beta/sigma/car/carPct/tStat/
        isSignificant/ar (list)/news (list[dict])/interpretation.
        실패/데이터 부족 시 error 키 포함.
    """
    ev = _toDate(eventDate)
    ohlcvFetcher = ohlcvFetcher or _defaultOhlcv
    benchmarkFetcher = benchmarkFetcher or _defaultBenchmark
    newsLoader = newsLoader or _defaultNewsLoader

    stockDf = ohlcvFetcher(stockCode, market)
    benchDf = benchmarkFetcher(market)
    if stockDf is None or stockDf.is_empty() or benchDf is None or benchDf.is_empty():
        return {"stockCode": stockCode, "eventDate": ev.isoformat(), "error": "ohlcv unavailable"}
    if "date" not in stockDf.columns or "close" not in stockDf.columns:
        return {"stockCode": stockCode, "eventDate": ev.isoformat(), "error": "ohlcv schema invalid"}

    # 거래일 정렬 + join
    s = stockDf.select("date", pl.col("close").alias("close_stock")).sort("date")
    b = benchDf.select("date", pl.col("close").alias("close_bench")).sort("date")
    merged = s.join(b, on="date", how="inner").sort("date")
    if merged.height < 50:
        return {"stockCode": stockCode, "eventDate": ev.isoformat(), "error": "history too short"}

    # eventIdx = 가장 가까운 거래일
    dates = merged["date"].to_list()
    eventIdx = None
    for i, d in enumerate(dates):
        if d >= ev:
            eventIdx = i
            break
    if eventIdx is None:
        return {"stockCode": stockCode, "eventDate": ev.isoformat(), "error": "event date out of range"}

    stockRet = _closesToReturns(merged["close_stock"])
    benchRet = _closesToReturns(merged["close_bench"])
    # returns array 가 dates 보다 1 짧음 — eventIdx 보정
    retIdx = eventIdx - 1 if eventIdx > 0 else 0

    from dartlab.synth.eventStudy import calcCAR

    carResult = calcCAR(
        stockRet,
        benchRet,
        eventIdx=retIdx,
        estimationWindow=estimationWindow,
        eventWindow=eventWindow,
    )
    if "error" in carResult:
        return {"stockCode": stockCode, "eventDate": ev.isoformat(), "error": carResult["error"]}

    # news context — ±newsContextDays
    newsStart = (ev - timedelta(days=newsContextDays)).isoformat()
    newsEnd = (ev + timedelta(days=newsContextDays)).isoformat()
    newsDf = newsLoader(newsStart, newsEnd, market)
    if keyword is None:
        try:
            from dartlab.gather.krx.listing.registry import codeToName

            keyword = codeToName(stockCode) or stockCode
        except Exception:
            keyword = stockCode

    newsItems: list[dict] = []
    if not newsDf.is_empty() and "title" in newsDf.columns:
        filtered = newsDf.filter(pl.col("title").str.contains(keyword, literal=True))
        wanted = [
            c for c in ("date", "title", "url", "source", "sentiment_score", "sentiment_label") if c in filtered.columns
        ]
        if wanted:
            newsItems = filtered.select(wanted).head(20).to_dicts()

    return {
        "stockCode": stockCode,
        "eventDate": ev.isoformat(),
        "eventIdx": eventIdx,
        "market": market,
        "keyword": keyword,
        "alpha": carResult["alpha"],
        "beta": carResult["beta"],
        "sigma": carResult["sigma"],
        "ar": [float(x) for x in carResult["ar"].tolist()]
        if hasattr(carResult["ar"], "tolist")
        else list(carResult["ar"]),
        "car": carResult["car"],
        "carPct": carResult["carPct"],
        "tStat": carResult["tStat"],
        "isSignificant": carResult["isSignificant"],
        "windowL": carResult["windowL"],
        "news": newsItems,
        "n_news": len(newsItems),
        "interpretation": carResult["interpretation"],
    }
