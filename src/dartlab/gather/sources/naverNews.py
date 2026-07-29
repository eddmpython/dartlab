"""네이버 검색 API 뉴스 소스 — 제목+스니펫 (private, 언론사 저작권).

네이버 오픈 '검색' API (``https://openapi.naver.com/v1/search/news.json``). 헤더
``X-Naver-Client-Id`` / ``X-Naver-Client-Secret`` 인증 (dataCredentials naver/
naverSecret 공급자). 응답 ``items[]``: title·description(둘 다 ``<b>`` 하이라이트
태그 + HTML 엔티티 포함)·originallink·link·pubDate.

⚠ 라이선스: 결과는 **언론사 저작권**. 공개 재배포 금지 → private 캐시 전용
(``news/private/naver``, KRX 시세 선례와 동형, newsSources.naver.visibility="private").
라이브 표시·서버사이드 read 는 의도된 용도라 OK — 공개 HF 벌크 적재만 금지.

rss(news.py)와 동형: ``_fetchAsync`` (query) + ``fetchHeadlinesForArchive`` (팬아웃).
인증 헤더 + 별도 host 라 shared GatherHttpClient 대신 격리된 httpx 를 쓴다
(``client`` 인자는 시그니처 대칭 목적 — 내부 미사용).
"""

from __future__ import annotations

import asyncio
import logging
import re
import time
from datetime import datetime, timedelta, timezone
from html import unescape
from urllib.parse import urlparse

import polars as pl

from dartlab.core.providers.dataCredentials import getKey

from ..infra.resilience import circuitBreaker as _circuit_breaker
from ..infra.resilience import healthTracker as _health_tracker
from ..types import CircuitOpenError, NewsItem, SourceUnavailableError
from .newsSchema import coerceToCanonical

log = logging.getLogger(__name__)

_SOURCE_NAME = "naver_news"
_ENDPOINT = "https://openapi.naver.com/v1/search/news.json"
_TAG_RE = re.compile(r"<[^>]+>")


def _clean(s: str | None) -> str:
    """``<b>`` 등 태그 제거 + HTML 엔티티 unescape + strip."""
    if not s:
        return ""
    return unescape(_TAG_RE.sub("", s)).strip()


def _parsePubDate(s: str) -> str | None:
    """네이버 pubDate (RFC822 ``+0900``) → ``'YYYY-MM-DD'`` (실패 None)."""
    try:
        return str(datetime.strptime(s, "%a, %d %b %Y %H:%M:%S %z").date())
    except (ValueError, TypeError):
        return None


def _parseItems(data: object) -> list[NewsItem]:
    """네이버 검색 응답 JSON → list[NewsItem] (url=originallink, description=스니펫)."""
    if not isinstance(data, dict):
        raise SourceUnavailableError("Naver news 응답 schema가 객체가 아닙니다")
    rawItems = data.get("items")
    if not isinstance(rawItems, list):
        raise SourceUnavailableError("Naver news items가 배열이 아닙니다")
    items: list[NewsItem] = []
    for it in rawItems:
        if not isinstance(it, dict):
            raise SourceUnavailableError("Naver news item이 객체가 아닙니다")
        link = (it.get("originallink") or it.get("link") or "").strip()
        if not link:
            continue
        pubDate = str(it.get("pubDate") or "")
        parsedDate = _parsePubDate(pubDate)
        if pubDate and parsedDate is None:
            raise SourceUnavailableError(f"Naver news pubDate를 해석할 수 없습니다: {pubDate!r}")
        netloc = urlparse(link).netloc
        source = netloc[4:] if netloc.startswith("www.") else netloc
        items.append(
            NewsItem(
                date=parsedDate or "",
                title=_clean(it.get("title")),
                source=source or "naver",
                url=link,
                description=_clean(it.get("description")),
            )
        )
    return items


_NAVER_START_MAX = 1000  # 검색 API start 상한 (start+display-1 ≤ 1000 → display=100 이면 최대 10 페이지)
_RATE_RETRIES = 3  # 429/5xx 페이지 재시도 횟수 (대량 fanout 커버리지 균일화).
_RATE_BACKOFF = 0.6  # 재시도 백오프 기준(초) — attempt 마다 ×(n+1) 선형 증가.


async def _fetchAsync(
    query: str,
    *,
    market: str = "KR",
    display: int = 100,
    sort: str = "date",
    pages: int = 1,
    client=None,
) -> list[NewsItem]:
    """네이버 뉴스 검색 (async) — 인증 헤더 + circuit breaker + start 페이징. KR 전용.

    Parameters
    ----------
    query : str
        검색어 (기업명/키워드).
    market : str
        시장. ``"KR"`` 외에는 ValueError (네이버=국내 전용).
    display : int
        페이지당 건수 (1~100, 네이버 상한 100).
    sort : str
        ``"date"`` (최신순) | ``"sim"`` (정확도순).
    pages : int
        ``start`` 페이징 깊이 (1=최근 100건, 최대 10=최근 1000건). 종목당 백필 깊이.
        date desc 정렬이라 페이지가 깊을수록 과거. 빈 페이지에서 조기 종료.
    client
        시그니처 대칭용 — 내부 미사용 (격리 httpx).

    Returns
    -------
    list[NewsItem]
        date·title·source·url·description (url dedup). 정상 무데이터면 빈 리스트.

    Raises
    ------
    ValueError
        query, market, display, sort 또는 pages 입력 계약 위반.
    CircuitOpenError
        Naver news circuit이 open인 경우.
    SourceUnavailableError
        자격증명 미설정, 요청, JSON 또는 schema 실패.
    """
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Naver news query는 비어 있지 않은 문자열이어야 합니다")
    if not isinstance(market, str) or market.upper() != "KR":
        raise ValueError(f"Naver news는 KR 시장만 지원합니다: {market!r}")
    if not isinstance(display, int) or display < 1:
        raise ValueError(f"Naver news display는 1 이상의 정수여야 합니다: {display!r}")
    if sort not in {"date", "sim"}:
        raise ValueError(f"Naver news sort는 date/sim만 지원합니다: {sort!r}")
    if not isinstance(pages, int) or pages < 1:
        raise ValueError(f"Naver news pages는 1 이상의 정수여야 합니다: {pages!r}")
    clientId = getKey("naver")
    clientSecret = getKey("naverSecret")
    if not clientId or not clientSecret:
        raise SourceUnavailableError("Naver news 자격증명이 설정되지 않았습니다")
    if _circuit_breaker.isOpen(_SOURCE_NAME):
        raise CircuitOpenError("naver_news circuit breaker가 열려 있습니다")

    disp = min(max(display, 1), 100)
    headers = {"X-Naver-Client-Id": clientId, "X-Naver-Client-Secret": clientSecret}
    maxPages = max(1, min(pages, _NAVER_START_MAX // disp))

    out: list[NewsItem] = []
    seen: set[str] = set()
    t0 = time.monotonic()
    try:
        import httpx

        async with httpx.AsyncClient() as ac:
            for page in range(maxPages):
                start = 1 + page * disp
                if start > _NAVER_START_MAX:
                    break
                params = {"query": query, "display": disp, "start": start, "sort": sort}
                # 429(rate limit)/5xx 는 백오프 재시도 — 대량 fanout 에서 종목별 커버리지 균일화.
                resp = None
                for attempt in range(_RATE_RETRIES + 1):
                    resp = await ac.get(_ENDPOINT, params=params, headers=headers, timeout=10.0)
                    if resp.status_code == 429 or resp.status_code >= 500:
                        if attempt < _RATE_RETRIES:
                            await asyncio.sleep(_RATE_BACKOFF * (attempt + 1))
                            continue
                    break
                if resp is None:
                    raise SourceUnavailableError("Naver news 응답을 받지 못했습니다")
                resp.raise_for_status()
                batch = _parseItems(resp.json())
                if not batch:
                    break  # 더 이상 과거 결과 없음 → 조기 종료
                for it in batch:
                    if it.url and it.url not in seen:
                        seen.add(it.url)
                        out.append(it)
                if len(batch) < disp:
                    break  # 마지막 페이지 (total 소진)
        latency = time.monotonic() - t0
        _circuit_breaker.recordSuccess(_SOURCE_NAME)
        _health_tracker.record(_SOURCE_NAME, success=True, latency=latency)
        return out
    except Exception as exc:
        latency = time.monotonic() - t0
        _circuit_breaker.recordFailure(_SOURCE_NAME)
        _health_tracker.record(_SOURCE_NAME, success=False, latency=latency)
        log.debug("naver fetch 실패 (page 누적 %d): %s", len(out), exc)
        if isinstance(exc, SourceUnavailableError):
            raise
        raise SourceUnavailableError(f"Naver news 요청 실패: {query!r}") from exc


def fetchHeadlinesForArchive(
    queries: list[str],
    *,
    market: str = "KR",
    days: int = 1,
    concurrency: int = 8,
    limit: int | None = None,
    pages: int = 1,
) -> pl.DataFrame:
    """네이버 뉴스 다중 쿼리 fan-out — archive 진입점 (rss 와 동형 시그니처).

    Sig: ``fetchHeadlinesForArchive(queries, *, market, days, concurrency, limit, pages) -> pl.DataFrame``

    Capabilities:
        - N 쿼리 비동기 fan-out (Semaphore 제한)
        - 쿼리당 start 페이징 (``pages`` 1~10, 최대 1000건/쿼리 — 백필 깊이)
        - url dedup (첫 매치 query 유지)
        - days 윈도우 cutoff 필터 (date ≥ today-days; ``days=0`` = cutoff 없음 = 깊은 백필)
        - canonical 17컬럼 (description=스니펫 채움, enrichment=null)

    AIContext:
        syncNaverNews.py 의 일별 cron 단일 진입점. private 경로(news/private/naver)
        로만 적재 — 공개 dartlab-data 안 감.

    Guide:
        KR 전용 — 타 시장은 네트워크 미접근 빈 결과. days 윈도우는 pubDate 기준
        cutoff. 결과는 언론사 저작권 — 공개 재배포 금지 (private 캐시 전용).

    When:
        syncNaverNews 일별 cron + 운영자 수동 백필.

    How:
        쿼리별 _fetchAsync 비동기 fan-out → url dedup → days cutoff →
        coerceToCanonical 1회.

    Requires:
        dataCredentials naver/naverSecret 쌍 (X-Naver-Client-Id/Secret) + 네트워크.
        무키 → 빈 결과 (예외 없음).

    Args:
        queries: 검색 시드 (종목명+키워드).
        market: ``"KR"`` 외 빈 DataFrame.
        days: 최근 N일 윈도우. 기본 1. ``0`` 이면 cutoff 미적용(백필 — 모은 전부 유지).
        concurrency: 동시 fetch 상한.
        limit: 반환 행 상한 (date desc 정렬 후). None=전체.
        pages: 쿼리당 start 페이징 깊이 (1=최근 100건, 10=최근 1000건). 백필 시 ↑.

    Returns:
        pl.DataFrame — newsSchema.NEWS_ARCHIVE_SCHEMA canonical 17컬럼. 빈 결과 동일 schema.

    Raises:
        ValueError / CircuitOpenError / SourceUnavailableError — 입력 또는 개별 쿼리 실패.

    Example:
        >>> # fetchHeadlinesForArchive(["삼성전자","SK하이닉스"], market="KR", days=1)

    See Also:
        ``gather.sources.news.fetchHeadlinesForArchive``: rss 동형 진입점.
        ``gather.sources.newsIo.writeDailyParquet``: 적재 공유 IO.
    """
    if not queries:
        return coerceToCanonical(None)
    if not isinstance(market, str) or market.upper() != "KR":
        raise ValueError(f"Naver news archive는 KR 시장만 지원합니다: {market!r}")

    from ..infra.http import runAsync

    sem = asyncio.Semaphore(max(1, concurrency))

    async def _one(q: str) -> tuple[str, list[NewsItem]]:
        async with sem:
            return q, await _fetchAsync(q, market=market, pages=pages)

    async def _gatherAll() -> list[tuple[str, list[NewsItem]]]:
        return await asyncio.gather(*(_one(q) for q in queries))

    pairs = runAsync(_gatherAll())
    capturedAt = datetime.now(tz=timezone.utc)

    # dedup 은 (query, url) 단위 — 한 기사가 여러 종목을 동시 언급하면 각 종목(query)이 자기
    # 행을 보존해야 byCompany 폴딩에서 종목별로 다 잡힌다. url 전역 dedup 은 형제 종목에 기사를
    # 빼앗겨(에코프로비엠↔에코프로) 커버리지가 들쭉날쭉해진다. (_fetchAsync 가 query 내 url 은 이미 dedup.)
    rows: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for q, items in pairs:
        for it in items:
            key = (q, it.url)
            if not it.url or key in seen:
                continue
            seen.add(key)
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
    df = pl.DataFrame(rows).with_columns(pl.col("date").cast(pl.Date, strict=False))
    if days and days > 0:
        cutoff = (datetime.now(tz=timezone.utc) - timedelta(days=days)).date()
        df = df.filter(pl.col("date").is_not_null() & (pl.col("date") >= cutoff))
    df = df.sort(["date", "url"], descending=[True, False])
    df = coerceToCanonical(df)
    return df.head(limit) if limit is not None else df
