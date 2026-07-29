"""L6 Backend — /api/dartlab/price-events. PriceEventChart 데이터 SSOT.

OHLCV + 일자별 events (disclosure + RSS news + GDELT news) 통합 + 옵션
L4 shocks 자동 마커 + L5 regime band. dartwings DisclosureSection 의
schema 확장.

진입점: GET /api/dartlab/price-events?stockCode=&start=&end=&market=&sources=&discType=&keyword=

응답 dict:
    stockCode/corpName/market/start/end
    ohlc : list[[ts_ms, open, high, low, close, volume]]
    events : {"YYYY-MM-DD": {"disclosures": [...], "news_rss": [...], "news_gdelt": [...]}}
    shocks : list[{date, ar, z_score, direction, is_significant}]
    regime_band : list[{start, end, label, score}]

메모리 가드:
    @withMemoryBudget(1500) + BoundedCache _price_events_ (LRU 50/300MB).
"""

from __future__ import annotations

import logging
from datetime import date as _date
from datetime import datetime, timedelta

import polars as pl
from fastapi import APIRouter, HTTPException, Query

from dartlab.core.memory import BoundedCache, withMemoryBudget

router = APIRouter(prefix="/api/dartlab", tags=["price-events"])
_log = logging.getLogger(__name__)

_CACHE = BoundedCache(maxEntries=50, pressureMb=300.0)

_VALID_SOURCES = {"all", "disclosure", "news_rss", "news_gdelt"}


def _toIso(d: str | _date | None) -> str | None:
    if d is None:
        return None
    if isinstance(d, _date):
        return d.isoformat()
    return str(d)


def _ohlcRows(df: pl.DataFrame) -> list[list]:
    """ohlcv → LWC v5 timestamp+OHLC+volume row."""
    if df is None or df.is_empty():
        return []
    cols = df.columns
    if "date" not in cols or "close" not in cols:
        return []
    rows: list[list] = []
    open_c = df["open"].to_list() if "open" in cols else df["close"].to_list()
    high_c = df["high"].to_list() if "high" in cols else df["close"].to_list()
    low_c = df["low"].to_list() if "low" in cols else df["close"].to_list()
    close_c = df["close"].to_list()
    vol_c = df["volume"].to_list() if "volume" in cols else [0] * df.height
    dates = df["date"].to_list()
    for i, d in enumerate(dates):
        if d is None:
            continue
        ts = int(
            datetime.combine(
                d if isinstance(d, _date) else _date.fromisoformat(str(d)), datetime.min.time()
            ).timestamp()
        )
        rows.append(
            [
                ts,
                float(open_c[i] or 0),
                float(high_c[i] or 0),
                float(low_c[i] or 0),
                float(close_c[i] or 0),
                int(vol_c[i] or 0),
            ]
        )
    return rows


def _fetchEvents(
    stockCode: str,
    corpName: str | None,
    start: _date,
    end: _date,
    market: str,
    sources: str,
    keyword: str | None,
) -> dict[str, dict[str, list[dict]]]:
    """일자별 events dict 빌드 — disclosure + RSS news + GDELT news."""
    events: dict[str, dict[str, list[dict]]] = {}

    want_disc = sources in ("all", "disclosure")
    want_rss = sources in ("all", "news_rss")
    want_gdelt = sources in ("all", "news_gdelt")

    keyword_filter = keyword or corpName or stockCode

    # disclosure
    if want_disc:
        try:
            import dartlab

            c = dartlab.Company(stockCode)
            filings = c.filings(topK=500)
            if filings is not None and not filings.is_empty():
                fdf = (
                    filings.filter(
                        pl.col("date").cast(pl.Utf8).str.slice(0, 10).is_between(start.isoformat(), end.isoformat())
                    )
                    if "date" in filings.columns
                    else filings
                )
                for row in fdf.to_dicts():
                    d = str(row.get("date", ""))[:10]
                    if not d:
                        continue
                    events.setdefault(d, {}).setdefault("disclosures", []).append(
                        {
                            "title": row.get("title") or row.get("report_nm") or "",
                            "rceptNo": row.get("rceptNo") or row.get("rcept_no") or "",
                            "url": row.get("url") or "",
                            "discType": row.get("discType") or row.get("disc_type") or "etc",
                        }
                    )
        except Exception as exc:
            _log.debug("disclosure fetch fail %s: %s", stockCode, exc)

    # news (RSS + GDELT) — loadNewsArchive 통합
    if want_rss or want_gdelt:
        try:
            from dartlab.gather.bulkData.newsHeadlines import loadNewsArchive

            archive = loadNewsArchive(start.isoformat(), end.isoformat(), market)
            if not archive.is_empty() and "title" in archive.columns:
                filtered = archive.filter(pl.col("title").str.contains(keyword_filter, literal=True))
                for row in filtered.to_dicts():
                    d_raw = row.get("date")
                    if d_raw is None:
                        continue
                    d = str(d_raw)[:10]
                    src = (
                        "news_gdelt"
                        if (row.get("source") and "gdelt" in str(row.get("source")).lower())
                        else "news_rss"
                    )
                    if src == "news_rss" and not want_rss:
                        continue
                    if src == "news_gdelt" and not want_gdelt:
                        continue
                    item = {
                        "title": row.get("title") or "",
                        "source": row.get("source") or "",
                        "url": row.get("url") or "",
                        "sentiment_score": row.get("sentiment_score"),
                        "sentiment_label": row.get("sentiment_label"),
                    }
                    if src == "news_gdelt":
                        item["themes"] = row.get("themes") or []
                    events.setdefault(d, {}).setdefault(src, []).append(item)
        except Exception as exc:
            _log.debug("news archive fetch fail: %s", exc)

    return events


@withMemoryBudget(1500)
def buildPriceEventsPayload(
    stockCode: str,
    start: str | _date | None = None,
    end: str | _date | None = None,
    *,
    market: str = "KR",
    sources: str = "all",
    discType: str = "all",
    keyword: str | None = None,
    includeShocks: bool = True,
    includeRegime: bool = True,
) -> dict:
    """price-events payload SSOT (route 분리 — pure function 테스트 가능).

    Args:
        stockCode: 6자리 종목코드.
        start/end: ISO date 또는 None (None 이면 today-365 ~ today).
        market: "KR" | "US".
        sources: "all" | "disclosure" | "news_rss" | "news_gdelt".
        discType: "all" 또는 특정 disc type ("periodic"/"major"/...).
        keyword: news 필터 키워드 (None 이면 corpName resolve).
        includeShocks: L4 priceShockNews 위임 마커 동행.
        includeRegime: L5 narrativeRegime regime band 동행.

    Returns:
        dict — stockCode/corpName/market/start/end/ohlc/events/shocks/regime_band.
    """
    if sources not in _VALID_SOURCES:
        raise ValueError(f"sources must be one of {_VALID_SOURCES}")

    endDate = _date.fromisoformat(_toIso(end)) if end else _date.today()
    startDate = _date.fromisoformat(_toIso(start)) if start else (endDate - timedelta(days=365))

    cacheKey = f"_price_events_{market}_{stockCode}_{startDate.isoformat()}_{endDate.isoformat()}_{sources}_{discType}_{keyword or ''}_{includeShocks}_{includeRegime}"
    cacheHit, cached = _CACHE.lookup(cacheKey)
    if cacheHit:
        return cached

    try:
        from dartlab.gather.krx.listing.registry import codeToName

        corpName = codeToName(stockCode)
    except Exception:
        corpName = None

    # OHLCV
    ohlc: list[list] = []
    try:
        from dartlab.quant.screen._dataAccessOhlcv import fetchOhlcv

        df = fetchOhlcv(stockCode, market=market, start=startDate.isoformat(), end=endDate.isoformat())
        if df is not None and not df.is_empty():
            ohlc = _ohlcRows(df)
    except Exception as exc:
        _log.warning("ohlcv fail %s: %s", stockCode, exc)

    events = _fetchEvents(stockCode, corpName, startDate, endDate, market, sources, keyword)

    # discType filter on disclosures
    if discType != "all":
        for d, slots in events.items():
            if "disclosures" in slots:
                slots["disclosures"] = [it for it in slots["disclosures"] if it.get("discType") == discType]

    shocks: list[dict] = []
    if includeShocks:
        try:
            from dartlab.analysis.eventStudy.priceShockNews import priceShockNews

            sp = priceShockNews(
                stockCode,
                market=market,
                asOf=endDate,
                periodDays=(endDate - startDate).days,
                thresholdSigma=3.0,
            )
            if "shock_events" in sp:
                shocks = [
                    {
                        "date": ev["date"],
                        "ar": ev["ar"],
                        "z_score": ev["z_score"],
                        "direction": ev["direction"],
                        "is_significant": ev["is_significant"],
                    }
                    for ev in sp["shock_events"]
                ]
        except Exception as exc:
            _log.debug("priceShockNews fail %s: %s", stockCode, exc)

    regime_band: list[dict] = []
    if includeRegime:
        try:
            from dartlab.scan.narrativeRegime import scanNarrativeRegime

            r = scanNarrativeRegime(market=market, asOf=endDate, lookbackDays=min((endDate - startDate).days, 90))
            if r.get("regime_shift_significant") and r.get("regime_shift_date"):
                regime_band.append(
                    {
                        "start": r["regime_shift_date"],
                        "end": endDate.isoformat(),
                        "label": r["regime_label"],
                        "score": r["regime_score"],
                    }
                )
        except Exception as exc:
            _log.debug("narrativeRegime fail: %s", exc)

    result = {
        "stockCode": stockCode,
        "corpName": corpName,
        "market": market,
        "start": startDate.isoformat(),
        "end": endDate.isoformat(),
        "ohlc": ohlc,
        "events": events,
        "shocks": shocks,
        "regime_band": regime_band,
    }
    _CACHE[cacheKey] = result
    return result


@router.get("/price-events")
def getPriceEvents(
    stockCode: str = Query(..., min_length=6, max_length=6),
    start: str | None = Query(None),
    end: str | None = Query(None),
    market: str = Query("KR"),
    sources: str = Query("all", pattern="^(all|disclosure|news_rss|news_gdelt)$"),
    discType: str = Query("all"),
    keyword: str | None = Query(None),
    includeShocks: bool = Query(True),
    includeRegime: bool = Query(True),
) -> dict:
    """OHLCV + 일자별 events (disclosure + RSS news + GDELT news) + shocks + regime band."""
    try:
        return buildPriceEventsPayload(
            stockCode,
            start,
            end,
            market=market,
            sources=sources,
            discType=discType,
            keyword=keyword,
            includeShocks=includeShocks,
            includeRegime=includeRegime,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        _log.exception("price-events fail %s", stockCode)
        raise HTTPException(status_code=500, detail=f"내부 오류: {exc}") from exc
