"""L4 priceShockNews — 역방향 event study: |AR|>kσ shock 자동 검출 + 인접 뉴스.

사용자 직설: "왜 -5% 빠졌지" 를 자동 답함. 1 년 종목 일별 AR 의 σ → ±k 임계
밖 일자 = shock event. 각 shock 에 대해 ±newsContextDays news 첨부 + 옵션
newsImpact 위임으로 CAR/t-stat 풀 계산.

진입점:
    priceShockNews(stockCode, *, market, periodDays, thresholdSigma,
                   ohlcvFetcher, benchmarkFetcher, newsLoader,
                   computeImpact=False)
    → dict — stockCode/period/n_shocks/shock_events (list[dict])/threshold

메모리 가드:
    @withMemoryBudget(400) — 1 년 + news 검색 <400MB.
    BoundedCache `_price_shock_*` (LRU 30/300MB).
"""

from __future__ import annotations

import logging
from datetime import date as _date
from datetime import datetime, timedelta
from typing import Callable

import numpy as np
import polars as pl

from dartlab.core.memory import BoundedCache, withMemoryBudget

log = logging.getLogger(__name__)

_CACHE = BoundedCache(maxEntries=30, pressureMb=300.0)


def _toDate(d: str | _date | datetime | None) -> _date:
    """str/date/datetime → date."""
    if d is None:
        return _date.today()
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, _date):
        return d
    return _date.fromisoformat(str(d))


@withMemoryBudget(400)
def priceShockNews(
    stockCode: str,
    *,
    market: str = "KR",
    asOf: str | _date | datetime | None = None,
    periodDays: int = 365,
    thresholdSigma: float = 3.0,
    newsContextDays: int = 3,
    computeImpact: bool = False,
    topNews: int = 5,
    keyword: str | None = None,
    ohlcvFetcher: Callable[[str, str], pl.DataFrame | None] | None = None,
    benchmarkFetcher: Callable[[str], pl.DataFrame | None] | None = None,
    newsLoader: Callable[[str, str, str], pl.DataFrame] | None = None,
) -> dict:
    """|AR|>thresholdSigma 일자 자동 검출 + 각 shock 의 인접 ±newsContextDays news.

    Args:
        stockCode: 종목코드.
        market: "KR" | "US".
        asOf: 분석 기준일 (기본 today). period = [asOf-periodDays, asOf].
        periodDays: 분석 기간 (기본 365).
        thresholdSigma: |AR|>kσ 임계 (기본 3.0).
        newsContextDays: shock 일자 ±N 일 news.
        computeImpact: True 시 각 shock 에 newsImpact (CAR/t-stat) 위임.
        topNews: shock 별 news top N.
        keyword: news 필터 키워드 (None 이면 corpName resolve).
        ohlcvFetcher/benchmarkFetcher/newsLoader: DI mock 주입.

    Returns:
        dict — stockCode/period_start/period_end/n_shocks/threshold_sigma/
        sigma_obs/shock_events (list[{date, ar, ar_pct, z_score, direction,
        is_significant, news (list), car?, tStat?}])
    """
    asOfDate = _toDate(asOf)
    cacheKey = f"_price_shock_{market}_{stockCode}_{asOfDate.isoformat()}_{periodDays}_{thresholdSigma}_{computeImpact}"
    cacheHit, cached = _CACHE.lookup(cacheKey)
    if cacheHit:
        return cached

    if ohlcvFetcher is None:
        from dartlab.synth.marketDataAccess import fetchOhlcv as _default_o

        def ohlcvFetcher(c, m):
            """default ohlcv fetcher."""
            return _default_o(c, market=m)

    if benchmarkFetcher is None:
        from dartlab.synth.marketDataAccess import fetchBenchmark as _default_b

        def benchmarkFetcher(m):
            """default benchmark fetcher — KR=KOSPI, US=SPY."""
            return _default_b(market=m)

    if newsLoader is None:
        from dartlab.gather.bulkData.newsHeadlines import loadNewsArchive

        def newsLoader(s, e, m):
            """default news loader — loadNewsArchive 위임."""
            try:
                return loadNewsArchive(s, e, m)
            except Exception:
                return pl.DataFrame()

    stockDf = ohlcvFetcher(stockCode, market)
    benchDf = benchmarkFetcher(market)
    if stockDf is None or stockDf.is_empty() or benchDf is None or benchDf.is_empty():
        result = {"stockCode": stockCode, "error": "ohlcv unavailable"}
        _CACHE[cacheKey] = result
        return result

    periodStart = asOfDate - timedelta(days=periodDays)
    s = (
        stockDf.select("date", pl.col("close").alias("close_stock"))
        .filter((pl.col("date") >= periodStart) & (pl.col("date") <= asOfDate))
        .sort("date")
    )
    b = benchDf.select("date", pl.col("close").alias("close_bench")).sort("date")
    merged = s.join(b, on="date", how="inner").sort("date")
    if merged.height < 30:
        result = {"stockCode": stockCode, "error": "history too short"}
        _CACHE[cacheKey] = result
        return result

    stockClose = merged["close_stock"].to_numpy().astype(np.float64)
    benchClose = merged["close_bench"].to_numpy().astype(np.float64)
    stockRet = np.diff(stockClose) / stockClose[:-1]
    benchRet = np.diff(benchClose) / benchClose[:-1]

    # market model α/β from full window (간이 — newsImpact 는 별도 estimation window)
    X = np.column_stack([np.ones(len(benchRet)), benchRet])
    try:
        beta, *_ = np.linalg.lstsq(X, stockRet, rcond=None)
    except np.linalg.LinAlgError:
        beta = np.array([0.0, 1.0])
    alpha, betaB = float(beta[0]), float(beta[1])
    expected = alpha + betaB * benchRet
    ar = stockRet - expected
    sigma = float(np.std(ar, ddof=1)) if ar.size > 2 else 0.0
    if sigma == 0.0:
        result = {"stockCode": stockCode, "error": "zero AR variance"}
        _CACHE[cacheKey] = result
        return result

    threshold = thresholdSigma * sigma
    shockIdxs = np.where(np.abs(ar) > threshold)[0]
    dates = merged["date"].to_list()[1:]  # diff array 1 짧음

    if keyword is None:
        try:
            from dartlab.gather.krx.listing.registry import codeToName

            keyword = codeToName(stockCode) or stockCode
        except Exception:
            keyword = stockCode

    shock_events: list[dict] = []
    for idx in shockIdxs:
        d = dates[idx]
        ar_val = float(ar[idx])
        z = ar_val / sigma
        newsStart = (d - timedelta(days=newsContextDays)).isoformat()
        newsEnd = (d + timedelta(days=newsContextDays)).isoformat()
        newsDf = newsLoader(newsStart, newsEnd, market)
        newsItems: list[dict] = []
        if not newsDf.is_empty() and "title" in newsDf.columns:
            filtered = newsDf.filter(pl.col("title").str.contains(keyword, literal=True))
            wanted = [
                c
                for c in ("date", "title", "url", "source", "sentiment_score", "sentiment_label")
                if c in filtered.columns
            ]
            if wanted:
                newsItems = filtered.select(wanted).head(topNews).to_dicts()

        ev = {
            "date": d.isoformat() if hasattr(d, "isoformat") else str(d),
            "ar": round(ar_val, 5),
            "ar_pct": round(ar_val * 100, 2),
            "z_score": round(float(z), 2),
            "direction": "up" if ar_val > 0 else "down",
            "is_significant": bool(abs(z) > 1.96),
            "n_news": len(newsItems),
            "news": newsItems,
        }

        if computeImpact:
            from dartlab.analysis.eventStudy.newsImpact import newsImpact

            impact = newsImpact(
                stockCode,
                d,
                market=market,
                keyword=keyword,
                ohlcvFetcher=ohlcvFetcher,
                benchmarkFetcher=benchmarkFetcher,
                newsLoader=newsLoader,
            )
            if "error" not in impact:
                ev["car"] = impact["car"]
                ev["carPct"] = impact["carPct"]
                ev["tStat"] = impact["tStat"]

        shock_events.append(ev)

    result = {
        "stockCode": stockCode,
        "market": market,
        "period_start": periodStart.isoformat(),
        "period_end": asOfDate.isoformat(),
        "period_days": periodDays,
        "threshold_sigma": thresholdSigma,
        "sigma_obs": round(sigma, 5),
        "alpha": round(alpha, 5),
        "beta": round(betaB, 3),
        "n_shocks": len(shock_events),
        "shock_events": shock_events,
    }
    _CACHE[cacheKey] = result
    return result
