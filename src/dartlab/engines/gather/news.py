"""기업별 뉴스 수집 — Google News RSS (async, Gather 인프라 통합)."""

from __future__ import annotations

import logging
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from html import unescape

import polars as pl

from .resilience import circuit_breaker as _circuit_breaker
from .resilience import health_tracker as _health_tracker
from .types import NewsItem

log = logging.getLogger(__name__)

_KR_RSS = "https://news.google.com/rss/search?q={query}+when:{days}d&hl=ko&gl=KR&ceid=KR:ko"
_US_RSS = "https://news.google.com/rss/search?q={query}+stock+when:{days}d&hl=en-US&gl=US&ceid=US:en"

_SOURCE_NAME = "google_news"

_EMPTY_SCHEMA = {"date": pl.Date, "title": pl.Utf8, "source": pl.Utf8, "url": pl.Utf8}


def _parseDate(dateStr: str) -> datetime | None:
    """RSS date 파싱."""
    for fmt in ("%a, %d %b %Y %H:%M:%S %Z", "%a, %d %b %Y %H:%M:%S %z"):
        try:
            return datetime.strptime(dateStr, fmt)
        except ValueError:
            continue
    return None


def _parseRss(data: str, *, days: int = 30) -> list[NewsItem]:
    """RSS XML → NewsItem 리스트."""
    items: list[NewsItem] = []
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        return items

    cutoff = datetime.now() - timedelta(days=days)
    for item in root.iter("item"):
        title = item.findtext("title", "")
        link = item.findtext("link", "")
        pubDate = item.findtext("pubDate", "")
        source = item.findtext("source", "")
        dt = _parseDate(pubDate)
        if dt and dt.replace(tzinfo=None) >= cutoff:
            items.append(NewsItem(
                date=str(dt.date()),
                title=unescape(title),
                source=source,
                url=link,
            ))
    return items


async def _fetchAsync(
    query: str,
    *,
    market: str = "KR",
    days: int = 30,
    client=None,
) -> list[NewsItem]:
    """뉴스 수집 (async) — GatherHttpClient 사용, circuit breaker 적용."""
    if _circuit_breaker.is_open(_SOURCE_NAME):
        log.debug("news circuit breaker open — skip")
        return []

    template = _KR_RSS if market == "KR" else _US_RSS
    url = template.format(query=query, days=days)

    t0 = time.monotonic()
    try:
        if client is not None:
            resp = await client.get(url, timeout=10.0)
            data = resp.text
        else:
            import httpx
            async with httpx.AsyncClient(follow_redirects=True) as ac:
                resp = await ac.get(url, timeout=10.0)
                resp.raise_for_status()
                data = resp.text

        items = _parseRss(data, days=days)
        latency = time.monotonic() - t0
        _circuit_breaker.record_success(_SOURCE_NAME)
        _health_tracker.record(_SOURCE_NAME, success=True, latency=latency)
        return items
    except (ImportError, OSError, TimeoutError, ValueError, ConnectionError) as exc:
        latency = time.monotonic() - t0
        _circuit_breaker.record_failure(_SOURCE_NAME)
        _health_tracker.record(_SOURCE_NAME, success=False, latency=latency)
        log.debug("news fetch 실패: %s", exc)
        return []


def toDataFrame(items: list[NewsItem]) -> pl.DataFrame:
    """NewsItem 리스트 → pl.DataFrame 변환."""
    if not items:
        return pl.DataFrame(schema=_EMPTY_SCHEMA)
    rows = [{"date": i.date, "title": i.title, "source": i.source, "url": i.url} for i in items]
    df = pl.DataFrame(rows)
    if "date" in df.columns:
        df = df.with_columns(pl.col("date").cast(pl.Date))
        df = df.sort("date", descending=True)
    return df


def fetchNews(
    query: str,
    *,
    market: str = "KR",
    days: int = 30,
) -> pl.DataFrame:
    """기업명/티커로 뉴스 검색 (동기 래퍼, 하위호환).

    Args:
        query: 기업명 또는 티커.
        market: "KR" 또는 "US".
        days: 최근 N일.

    Returns:
        (date, title, source, url) DataFrame.
    """
    from .http import run_async

    items = run_async(_fetchAsync(query, market=market, days=days))
    return toDataFrame(items)
