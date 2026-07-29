"""L2 — news sentiment factor: cross-section IC + 5분위 portfolio (Tetlock 2007).

Phase A/B/C/D archive 의 종목별 sentiment score 를 cross-section factor 로 격상.
다른 어떤 factor 도 못 만드는 narrative alpha 검증 — IC 0.03~0.05 (보수) →
top-bottom 5분위 spread 연 4~8% (예측).

진입점:
    calcNewsSentimentScore(stockCode, asOf, lookbackDays, market)
        → {score, n_headlines, sentiment_label, asOf, lookbackDays}

    buildNewsSentimentUniverse(market, asOf, lookbackDays, *, minHeadlines=1)
        → {stockCode: score} cross-section (KRX listing × archive)

    newsSentimentIC(market, asOf, lookbackDays, forwardDays, *, ohlcvFetcher=None)
        → {ic_pearson, ic_spearman, n_stocks, t_stat, is_significant, quintile_spread}

References:
    - Tetlock (2007) "Giving Content to Investor Sentiment". 신문 sentiment → 시장 수익률.
    - Grinold-Kahn Active Portfolio Management Ch. 5-6 — IC theory.

메모리 가드:
    - @withMemoryBudget(500) — universe build delta 상한
    - BoundedCache `_news_sentiment_*` — universe 결과 캐싱 (LRU)
"""

from __future__ import annotations

import logging
from datetime import date as _date
from datetime import datetime, timedelta

import polars as pl

from dartlab.core.memory import BoundedCache, withMemoryBudget

log = logging.getLogger(__name__)

_CACHE = BoundedCache(maxEntries=50, pressureMb=400.0)


def _toIso(d: str | _date | datetime | None) -> str | None:
    """str/date/datetime → ISO date string."""
    if d is None:
        return None
    if isinstance(d, datetime):
        return d.date().isoformat()
    if isinstance(d, _date):
        return d.isoformat()
    return str(d)


def _resolveStockName(stockCode: str) -> str | None:
    """stockCode → corpName via KRX listing."""
    try:
        from dartlab.gather.krx.listing.registry import codeToName

        return codeToName(stockCode)
    except Exception as exc:
        log.debug("codeToName 실패 %s: %s", stockCode, exc)
        return None


def calcNewsSentimentScore(
    stockCode: str,
    asOf: str | _date | None = None,
    *,
    lookbackDays: int = 30,
    market: str = "KR",
    sentimentModel: str = "lm_dict",
) -> dict:
    """단일 종목 lookback news sentiment score.

    Args:
        stockCode: 종목코드 (예: "005930").
        asOf: 기준일. None 이면 today.
        lookbackDays: 기간 (기본 30).
        market: "KR" | "US".
        sentimentModel: "auto" | "lm_dict" — 대량 cross-section 은 lm_dict (CPU 비용).

    Returns:
        dict — {
            "stockCode": str,
            "score": float (mean sentiment, NaN 가능),
            "n_headlines": int,
            "sentiment_label": "pos" | "neg" | "neutral",
            "asOf": ISO date,
            "lookbackDays": int,
            "corpName": str | None,
        }

    Raises:
        없음 — archive 빈 결과 시 score=NaN, n_headlines=0.
    """
    asOfDate = (
        _date.today() if asOf is None else (asOf if isinstance(asOf, _date) else _date.fromisoformat(_toIso(asOf)))
    )
    startDate = asOfDate - timedelta(days=lookbackDays)
    corpName = _resolveStockName(stockCode)

    from dartlab.gather.bulkData.newsHeadlines import loadNewsArchive
    from dartlab.quant.text.newsSentiment import scoreNewsBatch

    archive = loadNewsArchive(startDate.isoformat(), asOfDate.isoformat(), market, asof=asOfDate.isoformat())
    if archive.is_empty() or "title" not in archive.columns:
        return {
            "stockCode": stockCode,
            "corpName": corpName,
            "score": float("nan"),
            "n_headlines": 0,
            "sentiment_label": "neutral",
            "asOf": asOfDate.isoformat(),
            "lookbackDays": lookbackDays,
        }

    keyword = corpName or stockCode
    filtered = archive.filter(pl.col("title").str.contains(keyword, literal=True))
    if filtered.is_empty():
        return {
            "stockCode": stockCode,
            "corpName": corpName,
            "score": float("nan"),
            "n_headlines": 0,
            "sentiment_label": "neutral",
            "asOf": asOfDate.isoformat(),
            "lookbackDays": lookbackDays,
        }

    scored = scoreNewsBatch(filtered, market=market, model=sentimentModel)
    if "sentiment_score" not in scored.columns:
        return {
            "stockCode": stockCode,
            "corpName": corpName,
            "score": float("nan"),
            "n_headlines": filtered.height,
            "sentiment_label": "neutral",
            "asOf": asOfDate.isoformat(),
            "lookbackDays": lookbackDays,
        }

    mean_score = scored["sentiment_score"].mean()
    n = scored.height
    label = (
        "pos"
        if mean_score is not None and mean_score > 0.05
        else "neg"
        if mean_score is not None and mean_score < -0.05
        else "neutral"
    )
    return {
        "stockCode": stockCode,
        "corpName": corpName,
        "score": float(mean_score) if mean_score is not None else float("nan"),
        "n_headlines": n,
        "sentiment_label": label,
        "asOf": asOfDate.isoformat(),
        "lookbackDays": lookbackDays,
    }


@withMemoryBudget(500)
def buildNewsSentimentUniverse(
    market: str = "KR",
    asOf: str | _date | None = None,
    *,
    lookbackDays: int = 30,
    minHeadlines: int = 1,
    sentimentModel: str = "lm_dict",
    maxStocks: int | None = None,
) -> dict[str, float]:
    """universe cross-section {stockCode: mean_sentiment} — KRX listing × archive.

    Capabilities:
        - archive 1 회 로드 → 종목별 corpName keyword filter → mean sentiment
        - BoundedCache LRU 50 + @withMemoryBudget(500)
        - minHeadlines 컷 (signal/noise 가드)

    Args:
        market: "KR" | "US".
        asOf: 기준일. None 이면 today.
        lookbackDays: 기간.
        minHeadlines: 최소 헤드라인 수 (이하 제외).
        sentimentModel: "lm_dict" (cross-section 비용 가드).
        maxStocks: universe 상한 (테스트용).

    Returns:
        {stockCode: mean_sentiment}.
    """
    asOfDate = (
        _date.today() if asOf is None else (asOf if isinstance(asOf, _date) else _date.fromisoformat(_toIso(asOf)))
    )
    cacheKey = f"_news_sentiment_universe_{market}_{asOfDate.isoformat()}_{lookbackDays}_{minHeadlines}"
    cacheHit, cached = _CACHE.lookup(cacheKey)
    if cacheHit:
        return cached

    startDate = asOfDate - timedelta(days=lookbackDays)

    from dartlab.gather.bulkData.newsHeadlines import loadNewsArchive
    from dartlab.gather.krx.listing.registry import getKindList
    from dartlab.quant.text.newsSentiment import scoreNewsBatch

    archive = loadNewsArchive(startDate.isoformat(), asOfDate.isoformat(), market, asof=asOfDate.isoformat())
    if archive.is_empty() or "title" not in archive.columns:
        _CACHE[cacheKey] = {}
        return {}

    scored = scoreNewsBatch(archive, market=market, model=sentimentModel)
    if "sentiment_score" not in scored.columns or scored.is_empty():
        _CACHE[cacheKey] = {}
        return {}

    listing = getKindList()
    if listing.is_empty():
        _CACHE[cacheKey] = {}
        return {}

    codeCol = "종목코드" if "종목코드" in listing.columns else "stockCode"
    nameCol = "회사명" if "회사명" in listing.columns else "corpName"
    items = list(zip(listing[codeCol].to_list(), listing[nameCol].to_list()))
    if maxStocks:
        items = items[:maxStocks]

    result: dict[str, float] = {}
    titles = scored["title"].to_list()
    scores = scored["sentiment_score"].to_list()
    for code, name in items:
        if not code or not name:
            continue
        matches = [s for t, s in zip(titles, scores) if name in t and s is not None]
        if len(matches) < minHeadlines:
            continue
        result[code] = float(sum(matches) / len(matches))

    _CACHE[cacheKey] = result
    return result


def newsSentimentIC(
    market: str = "KR",
    asOf: str | _date | None = None,
    *,
    lookbackDays: int = 30,
    forwardDays: int = 5,
    ohlcvFetcher=None,
    universe: dict[str, float] | None = None,
    quintiles: int = 5,
) -> dict:
    """news sentiment factor IC + 5분위 spread — Tetlock alpha 검증.

    Capabilities:
        - buildNewsSentimentUniverse → cross-section factor scores
        - forward returns = (close[asOf + forwardDays] / close[asOf] - 1)
        - calcCrossSectionIC (Pearson + Spearman + t-stat)
        - 5분위 long-short spread (top - bottom)

    Args:
        market: "KR" | "US".
        asOf: 기준일.
        lookbackDays: factor lookback.
        forwardDays: forward return horizon.
        ohlcvFetcher: callable(stockCode) → pl.DataFrame (테스트 주입).
            None 이면 dartlab.quant.screen._dataAccessOhlcv.fetchOhlcv.
        universe: 사전 계산된 score dict (None 이면 자동 build).
        quintiles: 분위 수 (기본 5).

    Returns:
        dict — calcCrossSectionIC 결과 + quintile_spread + n_long + n_short.
    """
    asOfDate = (
        _date.today() if asOf is None else (asOf if isinstance(asOf, _date) else _date.fromisoformat(_toIso(asOf)))
    )

    if universe is None:
        universe = buildNewsSentimentUniverse(market=market, asOf=asOfDate, lookbackDays=lookbackDays)

    if not universe:
        return {
            "ic_pearson": float("nan"),
            "ic_spearman": float("nan"),
            "n_stocks": 0,
            "t_stat": None,
            "is_significant": False,
            "quintile_spread": float("nan"),
            "asOf": asOfDate.isoformat(),
        }

    if ohlcvFetcher is None:
        from dartlab.quant.screen._dataAccessOhlcv import fetchOhlcv as _default

        def ohlcvFetcher(code):
            """단일 종목 OHLCV fetch — 시장 컨텍스트 (market) 고정 closure."""
            return _default(code, market=market)

    forwardReturns: dict[str, float] = {}
    endDate = asOfDate + timedelta(days=forwardDays + 7)  # 주말 buffer
    for code in universe:
        try:
            df = ohlcvFetcher(code)
        except Exception as exc:
            log.debug("ohlcv fail %s: %s", code, exc)
            continue
        if df is None or df.is_empty() or "close" not in df.columns or "date" not in df.columns:
            continue
        # date <= asOf 마지막 + date >= asOf + forwardDays 첫 close
        sub = df.filter((pl.col("date") >= asOfDate) & (pl.col("date") <= endDate)).sort("date")
        if sub.height < 2:
            continue
        try:
            p0 = sub["close"][0]
            p1 = sub["close"][-1]
            if p0 and p0 > 0:
                forwardReturns[code] = float(p1 / p0 - 1.0)
        except Exception:
            continue

    from dartlab.quant.factor.ranking import calcCrossSectionIC

    icResult = calcCrossSectionIC(universe, forwardReturns)

    common = sorted(set(universe) & set(forwardReturns))
    spread = float("nan")
    n_long = n_short = 0
    if len(common) >= quintiles * 2:
        sortedByScore = sorted(common, key=lambda c: universe[c])
        chunk = len(sortedByScore) // quintiles
        bottom = sortedByScore[:chunk]
        top = sortedByScore[-chunk:]
        n_short = len(bottom)
        n_long = len(top)
        topMean = sum(forwardReturns[c] for c in top) / len(top)
        botMean = sum(forwardReturns[c] for c in bottom) / len(bottom)
        spread = float(topMean - botMean)

    icResult["quintile_spread"] = spread
    icResult["n_long"] = n_long
    icResult["n_short"] = n_short
    icResult["asOf"] = asOfDate.isoformat()
    return icResult
