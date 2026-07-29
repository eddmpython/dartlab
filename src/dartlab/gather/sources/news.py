"""기업별 뉴스 수집 — Google News RSS (async, Gather 인프라 통합)."""

from __future__ import annotations

import asyncio
import logging
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from html import unescape

import polars as pl

from ..infra.resilience import circuitBreaker as _circuit_breaker
from ..infra.resilience import healthTracker as _health_tracker
from ..types import CircuitOpenError, NewsItem, SourceUnavailableError
from .newsSchema import coerceToCanonical

log = logging.getLogger(__name__)

_KR_RSS = "https://news.google.com/rss/search?q={query}+when:{days}d&hl=ko&gl=KR&ceid=KR:ko"
_US_RSS = "https://news.google.com/rss/search?q={query}+stock+when:{days}d&hl=en-US&gl=US&ceid=US:en"

_SOURCE_NAME = "google_news"

# 라이브 verb 표면 (lean) — archive 는 newsSchema.NEWS_ARCHIVE_SCHEMA(17) canonical.
_EMPTY_SCHEMA = {
    "date": pl.Date,
    "title": pl.Utf8,
    "source": pl.Utf8,
    "url": pl.Utf8,
    "description": pl.Utf8,
    "provider": pl.Utf8,
    "fetchedAt": pl.Utf8,
}


def _parseDate(dateStr: str) -> datetime:
    """RSS pubDate 문자열을 datetime으로 파싱.

    RFC 822 형식 두 가지(timezone 약어 / offset)를 순서대로 시도한다.

    Parameters
    ----------
    dateStr : str
        RSS ``<pubDate>`` 값 (예: ``"Tue, 15 Apr 2026 09:30:00 GMT"``).

    Returns
    -------
    datetime
        파싱 성공 시 datetime 객체.

    Raises
    ------
    ValueError
        지원하는 RFC 822 형식이 아닐 때.
    """
    for fmt in ("%a, %d %b %Y %H:%M:%S %Z", "%a, %d %b %Y %H:%M:%S %z"):
        try:
            return datetime.strptime(dateStr, fmt)
        except ValueError:
            continue
    raise ValueError(f"지원하지 않는 RSS pubDate 형식: {dateStr!r}")


def _parseRss(data: str, *, days: int = 30) -> list[NewsItem]:
    """RSS XML 문자열을 파싱하여 NewsItem 리스트로 변환.

    cutoff(현재 시각 - days) 이전 기사는 제외한다.
    XML 파싱 실패는 ValueError로 전달한다.

    Parameters
    ----------
    data : str
        RSS XML 원본 문자열.
    days : int, optional
        최근 N일 이내 기사만 포함 (기본 30일).

    Returns
    -------
    list[NewsItem]
        date : str — 발행일 (``"YYYY-MM-DD"`` 형식).
        title : str — 기사 제목 (HTML 엔티티 디코딩 완료).
        source : str — 언론사명.
        url : str — 기사 링크.
    """
    items: list[NewsItem] = []
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise ValueError("Google News RSS XML을 해석할 수 없습니다") from exc

    cutoff = datetime.now() - timedelta(days=days)
    for item in root.iter("item"):
        title = item.findtext("title", "")
        link = item.findtext("link", "")
        pubDate = item.findtext("pubDate", "")
        source = item.findtext("source", "")
        dt = _parseDate(pubDate)
        if dt.replace(tzinfo=None) >= cutoff:
            items.append(
                NewsItem(
                    date=str(dt.date()),
                    title=unescape(title),
                    source=source,
                    url=link,
                )
            )
    return items


async def _fetchAsync(
    query: str,
    *,
    market: str = "KR",
    days: int = 30,
    client=None,
) -> list[NewsItem]:
    """뉴스 수집 (async) — GatherHttpClient 사용, circuit breaker 적용.

    Parameters
    ----------
    query : str
        검색 쿼리 (기업명 또는 티커).
    market : str
        시장 코드. ``"KR"`` (한국어) 또는 ``"US"`` (영문). 기본 ``"KR"``.
    days : int
        최근 N일 이내 뉴스만 수집 (일). 기본 30.
    client
        GatherHttpClient 인스턴스. None이면 임시 httpx.AsyncClient 사용.

    Returns
    -------
    list[NewsItem]
        date : str — 발행일 (YYYY-MM-DD)
        title : str — 기사 제목
        source : str — 언론사명
        url : str — 기사 링크
        정상 응답에 기사가 없으면 빈 리스트.

    Raises
    ------
    ValueError
        market/days 입력 계약 위반.
    CircuitOpenError
        Google News circuit이 열려 있을 때.
    SourceUnavailableError
        네트워크, HTTP 또는 RSS 해석 실패.
    """
    market = market.upper()
    if market not in {"KR", "US"}:
        raise ValueError(f"news market은 KR/US만 지원합니다: {market!r}")
    if days < 1:
        raise ValueError(f"days는 1 이상이어야 합니다: {days}")
    if _circuit_breaker.isOpen(_SOURCE_NAME):
        raise CircuitOpenError(f"{_SOURCE_NAME} circuit이 open 상태입니다")

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
        _circuit_breaker.recordSuccess(_SOURCE_NAME)
        _health_tracker.record(_SOURCE_NAME, success=True, latency=latency)
        return items
    except Exception as exc:
        latency = time.monotonic() - t0
        _circuit_breaker.recordFailure(_SOURCE_NAME)
        _health_tracker.record(_SOURCE_NAME, success=False, latency=latency)
        raise SourceUnavailableError(f"{_SOURCE_NAME} 조회 실패: {query!r}") from exc


def toDataFrame(items: list[NewsItem], *, provider: str = _SOURCE_NAME) -> pl.DataFrame:
    """NewsItem 리스트 → pl.DataFrame 변환.

    Capabilities:
        - 빈 리스트도 동일 스키마 빈 DataFrame 반환 (consistency)
        - provider/fetchedAt provenance 동행
        - 최신순 정렬 (date desc)

    AIContext:
        - 뉴스 fetch 결과를 polars 분석 흐름으로 brigde

    Guide:
        items 가 빈 리스트면 _EMPTY_SCHEMA 의 빈 DataFrame.

    When:
        _fetchAsync 결과 후 표 형태로 변환할 때.

    How:
        list[NewsItem] → dict rows → DataFrame → date sort.

    Requires:
        polars (모듈 import).

    Parameters
    ----------
    items : list[NewsItem]
        변환할 뉴스 항목 리스트.

    Returns
    -------
    pl.DataFrame
        date : date — 발행일
        title : str — 기사 제목
        source : str — 언론사명
        url : str — 기사 링크
        최신순 정렬. 빈 리스트이면 빈 DataFrame (동일 스키마).

    Raises
    ------
    없음
        빈 리스트는 빈 DataFrame 반환.

    Example
    -------
    >>> items = [NewsItem(date="2024-01-01", title="t", source="s", url="u")]
    >>> toDataFrame(items)

    See Also:
        ``_fetchAsync`` — items 의 생성.
    """
    if not items:
        return pl.DataFrame(schema=_EMPTY_SCHEMA)
    fetchedAt = datetime.now(timezone.utc).isoformat()
    rows = [
        {
            "date": i.date,
            "title": i.title,
            "source": i.source,
            "url": i.url,
            "description": i.description,
            "provider": provider,
            "fetchedAt": fetchedAt,
        }
        for i in items
    ]
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
    limit: int | None = None,
) -> pl.DataFrame:
    """기업명/티커로 뉴스 검색 (동기 래퍼, 하위호환).

    Capabilities:
        - sync wrapper (async _fetchAsync → runAsync 으로 변환)
        - DataFrame 결과 (limit slice)

    AIContext:
        - 동기 흐름 caller (analysis/Company) 에서 직접 호출

    Guide:
        async 컨텍스트라면 ``_fetchAsync`` 직접 사용 권장.

    When:
        sync caller 가 뉴스 DataFrame 필요 시.

    How:
        query + market + days → _fetchAsync → toDataFrame → .head(limit).

    Args:
        query: 기업명 또는 티커.
        market: "KR" 또는 "US".
        days: 최근 N일.
        limit: 반환 행수 상한 (가장 최근 N건). None이면 전체.

    Returns:
        (date, title, source, url) DataFrame.

    Requires:
        네트워크 (Google News RSS).

    Raises:
        없음 — Google News RSS 파싱 실패는 빈 DataFrame 반환.

    Example:
        >>> df = fetchNews("삼성전자", market="KR", days=7, limit=10)

    See Also:
        ``_fetchAsync`` — async backend.
    """
    from ..infra.http import runAsync

    items = runAsync(_fetchAsync(query, market=market, days=days))
    df = toDataFrame(items, provider=_SOURCE_NAME)
    if limit is not None and limit > 0:
        return df.head(limit)
    return df


# archive 스키마는 newsSchema.NEWS_ARCHIVE_SCHEMA(17 canonical) — 옛 _ARCHIVE_SCHEMA 폐기.


def fetchHeadlinesForArchive(
    queries: list[str],
    *,
    market: str = "KR",
    days: int = 1,
    concurrency: int = 8,
    limit: int | None = None,
) -> pl.DataFrame:
    """RSS 헤드라인 다중 쿼리 fan-out — archive cron 진입점.

    Capabilities:
        - N 쿼리 비동기 fan-out (asyncio.gather, concurrency 제한)
        - url 기준 dedup (첫 매치 query 유지)
        - captured_at (수집 시각, UTC) + query (검색 시드) 추가 컬럼
        - TTL 캐시 우회 (archive 는 매 cron fresh 필요)

    AIContext:
        Phase A (news archive forward-only) 의 daily cron 단일 진입점.
        결과 DataFrame 을 `data/news/public/rss/{market}/{YYYY}-{MM}-{DD}.parquet`
        upsert 하는 caller (`syncNewsHeadlines.main`) 가 사용.

    Guide:
        days=1 (기본) 은 어제~오늘 수집 — 일 1~2 회 cron 시 적합.
        days=7 시 RSS 가 헤드라인 중복 비율 ↑ — dedup 으로 처리되지만
        cron 빈도 ↑ + days ↓ 가 안정적.

    When:
        `.github/scripts/sync/syncNewsHeadlines.py main()` 호출 시.

    How:
        queries 를 asyncio.Semaphore(concurrency) 로 게이트 → 각 query 별
        `_fetchAsync` 호출 → 결과 NewsItem 평탄화 → url dedup →
        captured_at + query + market 컬럼 부착 → pl.DataFrame.

    Args:
        queries: 검색 시드 (KOSPI200 종목명 + 매크로 키워드 등).
        market: "KR" | "US".
        days: 최근 N 일 윈도우. 기본 1.
        concurrency: 동시 fetch 상한. RSS 비공식 rate-limit 보호.
        limit: 반환 행 상한 (date desc 정렬 후 head). None=전체.

    Returns:
        pl.DataFrame — newsSchema.NEWS_ARCHIVE_SCHEMA canonical 17컬럼
        (description=빈값, enrichment=null). 빈 결과 시 동일 schema 빈 DataFrame.

    Raises:
        없음 — 개별 쿼리 실패는 빈 결과로 흡수 (circuit breaker 가드).

    Example::

        df = fetchHeadlinesForArchive(["삼성전자","SK하이닉스"], market="KR", days=1)
        # → (date, title, source, url, market="KR", query, captured_at)

    Requires:
        네트워크 (Google News RSS). 결과 본문은 untrusted external 메타데이터.

    See Also:
        ``_fetchAsync``: 단일 쿼리 backend.
        ``toDataFrame``: 단일 쿼리 결과 변환.
    """
    if not queries:
        return coerceToCanonical(None)

    from ..infra.http import runAsync

    sem = asyncio.Semaphore(max(1, concurrency))

    async def _one(q: str) -> tuple[str, list[NewsItem]]:
        async with sem:
            items = await _fetchAsync(q, market=market, days=days)
            return q, items

    async def _gatherAll() -> list[tuple[str, list[NewsItem]]]:
        return await asyncio.gather(*(_one(q) for q in queries))

    pairs = runAsync(_gatherAll())
    capturedAt = datetime.now(tz=timezone.utc)

    rows: list[dict] = []
    seen: set[str] = set()
    for q, items in pairs:
        for it in items:
            if not it.url or it.url in seen:
                continue
            seen.add(it.url)
            rows.append(
                {
                    "date": it.date,
                    "title": it.title,
                    "source": it.source,
                    "url": it.url,
                    "market": market.upper(),
                    "query": q,
                    "captured_at": capturedAt,
                    "description": it.description,
                }
            )

    if not rows:
        return coerceToCanonical(None)
    df = pl.DataFrame(rows)
    df = df.with_columns(pl.col("date").cast(pl.Date))
    df = df.sort(["date", "url"], descending=[True, False])
    df = coerceToCanonical(df)
    return df.head(limit) if limit is not None else df


def iterFetchNews(
    query: str,
    *,
    market: str = "KR",
    days: int = 30,
    batchSize: int = 100,
):
    """fetchNews 의 streaming pair — DataFrame 을 batchSize 행씩 yield (A 트랙 I2).

    Capabilities: DataFrame 을 batchSize 단위 slice yield.
    AIContext: news sentiment scoring 의 chunk 처리 진입점.
    Guide: fetchNews 가 None/empty 면 yield 없음.
    When: 메모리 효율 chunk 처리 필요 시.
    How: fetchNews → df.slice(i, batchSize) iterate.

    Args:
        query: 검색어.
        market: "KR" 또는 "US". 기본 "KR".
        days: 최근 N일.
        batchSize: batch 크기.

    Yields:
        pl.DataFrame — 각 batch.

    Raises:
        없음.

    Example::

        for batch in iterFetchNews("삼성전자", batchSize=20): score(batch)

    Requires: 네트워크.
    See Also: ``fetchNews``.
    """
    df = fetchNews(query, market=market, days=days)
    if df is None or df.is_empty():
        return
    height = df.height
    for i in range(0, height, batchSize):
        yield df.slice(i, batchSize)
