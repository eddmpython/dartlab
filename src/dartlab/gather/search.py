"""웹 검색 백엔드 -- Tavily + DuckDuckGo fallback.

Gather 엔진 인프라(CircuitBreaker, HealthTracker, GatherCache) 재사용.
환경변수 기반 graceful degradation:
- TAVILY_API_KEY 있으면 Tavily 1차
- duckduckgo-search 설치되어 있으면 fallback
- 둘 다 없으면 안내 메시지 반환
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass

from .cache import GatherCache, TTL_DEFAULT
from .resilience import circuit_breaker as _cb
from .resilience import health_tracker as _ht

log = logging.getLogger(__name__)

TTL_SEARCH = 1800  # 30분

_MAX_RESULTS = 8


@dataclass(frozen=True, slots=True)
class SearchResult:
    """검색 결과 단일 항목."""

    title: str
    url: str
    snippet: str
    source: str  # "tavily" | "duckduckgo"
    published: str | None = None


# ── 모듈 레벨 캐시 싱글턴 ──

_cache = GatherCache(max_entries=100)


# ══════════════════════════════════════
# Tavily 백엔드
# ══════════════════════════════════════


def _tavilyAvailable() -> bool:
    """Tavily SDK + API 키 존재 여부."""
    if not os.environ.get("TAVILY_API_KEY"):
        return False
    try:
        import tavily  # noqa: F401

        return True
    except ImportError:
        return False


def _searchTavily(query: str, *, maxResults: int = _MAX_RESULTS, days: int | None = None) -> list[SearchResult]:
    """Tavily API 검색."""
    from tavily import TavilyClient

    client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
    kwargs: dict = {
        "query": query,
        "max_results": maxResults,
        "search_depth": "basic",
        "include_answer": False,
    }
    if days is not None and days > 0:
        kwargs["days"] = days

    resp = client.search(**kwargs)
    results: list[SearchResult] = []
    for item in resp.get("results", []):
        results.append(
            SearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                snippet=item.get("content", ""),
                source="tavily",
                published=item.get("published_date"),
            )
        )
    return results


# ══════════════════════════════════════
# DuckDuckGo 백엔드
# ══════════════════════════════════════


def _ddgAvailable() -> bool:
    """duckduckgo-search 패키지 존재 여부."""
    try:
        from duckduckgo_search import DDGS  # noqa: F401

        return True
    except ImportError:
        return False


def _searchDdg(query: str, *, maxResults: int = _MAX_RESULTS) -> list[SearchResult]:
    """DuckDuckGo 검색."""
    from duckduckgo_search import DDGS

    results: list[SearchResult] = []
    with DDGS() as ddgs:
        for item in ddgs.text(query, max_results=maxResults):
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("href", ""),
                    snippet=item.get("body", ""),
                    source="duckduckgo",
                )
            )
    return results


def _searchDdgNews(query: str, *, maxResults: int = _MAX_RESULTS) -> list[SearchResult]:
    """DuckDuckGo 뉴스 검색."""
    from duckduckgo_search import DDGS

    results: list[SearchResult] = []
    with DDGS() as ddgs:
        for item in ddgs.news(query, max_results=maxResults):
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("body", ""),
                    source="duckduckgo",
                    published=item.get("date"),
                )
            )
    return results


# ══════════════════════════════════════
# 통합 검색 API
# ══════════════════════════════════════


def webSearch(
    query: str,
    *,
    maxResults: int = _MAX_RESULTS,
    days: int | None = None,
) -> list[SearchResult]:
    """웹 검색 -- Tavily -> DuckDuckGo fallback.

    Returns:
        검색 결과 리스트. 검색 패키지가 없으면 빈 리스트.
    """
    # 캐시 확인
    cacheKey = f"search:{query}:{maxResults}:{days}"
    cached = _cache.get(cacheKey)
    if cached is not None:
        return cached  # type: ignore[return-value]

    results: list[SearchResult] = []

    # 1차: Tavily
    if _tavilyAvailable() and not _cb.is_open("tavily"):
        t0 = time.monotonic()
        try:
            results = _searchTavily(query, maxResults=maxResults, days=days)
            _cb.record_success("tavily")
            _ht.record(source="tavily", success=True, latency=time.monotonic() - t0)
        except (OSError, ValueError, KeyError, RuntimeError) as e:
            log.warning("Tavily 검색 실패: %s", e)
            _cb.record_failure("tavily")
            _ht.record(source="tavily", success=False, latency=time.monotonic() - t0)

    # 2차: DuckDuckGo fallback
    if not results and _ddgAvailable() and not _cb.is_open("duckduckgo"):
        t0 = time.monotonic()
        try:
            results = _searchDdg(query, maxResults=maxResults)
            _cb.record_success("duckduckgo")
            _ht.record(source="duckduckgo", success=True, latency=time.monotonic() - t0)
        except (OSError, ValueError, RuntimeError) as e:
            log.warning("DuckDuckGo 검색 실패: %s", e)
            _cb.record_failure("duckduckgo")
            _ht.record(source="duckduckgo", success=False, latency=time.monotonic() - t0)

    if results:
        _cache.put(cacheKey, results, TTL_SEARCH)

    return results


def newsSearch(
    query: str,
    *,
    maxResults: int = _MAX_RESULTS,
    days: int | None = None,
) -> list[SearchResult]:
    """뉴스 검색 -- Tavily(topic=news) -> DuckDuckGo news fallback."""
    cacheKey = f"news_search:{query}:{maxResults}:{days}"
    cached = _cache.get(cacheKey)
    if cached is not None:
        return cached  # type: ignore[return-value]

    results: list[SearchResult] = []

    # 1차: Tavily (topic=news)
    if _tavilyAvailable() and not _cb.is_open("tavily"):
        t0 = time.monotonic()
        try:
            from tavily import TavilyClient

            client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
            kwargs: dict = {
                "query": query,
                "max_results": maxResults,
                "search_depth": "basic",
                "topic": "news",
                "include_answer": False,
            }
            if days is not None and days > 0:
                kwargs["days"] = days
            resp = client.search(**kwargs)
            for item in resp.get("results", []):
                results.append(
                    SearchResult(
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        snippet=item.get("content", ""),
                        source="tavily",
                        published=item.get("published_date"),
                    )
                )
            _cb.record_success("tavily")
            _ht.record(source="tavily", success=True, latency=time.monotonic() - t0)
        except (OSError, ValueError, KeyError, RuntimeError) as e:
            log.warning("Tavily 뉴스 검색 실패: %s", e)
            _cb.record_failure("tavily")
            _ht.record(source="tavily", success=False, latency=time.monotonic() - t0)

    # 2차: DuckDuckGo news
    if not results and _ddgAvailable() and not _cb.is_open("duckduckgo"):
        t0 = time.monotonic()
        try:
            results = _searchDdgNews(query, maxResults=maxResults)
            _cb.record_success("duckduckgo")
            _ht.record(source="duckduckgo", success=True, latency=time.monotonic() - t0)
        except (OSError, ValueError, RuntimeError) as e:
            log.warning("DuckDuckGo 뉴스 검색 실패: %s", e)
            _cb.record_failure("duckduckgo")
            _ht.record(source="duckduckgo", success=False, latency=time.monotonic() - t0)

    if results:
        _cache.put(cacheKey, results, TTL_SEARCH)

    return results


def searchAvailable() -> dict[str, bool]:
    """검색 백엔드 가용성 확인."""
    return {
        "tavily": _tavilyAvailable(),
        "duckduckgo": _ddgAvailable(),
        "any": _tavilyAvailable() or _ddgAvailable(),
    }


def formatResults(results: list[SearchResult], *, maxChars: int = 4000) -> str:
    """검색 결과를 LLM 컨텍스트용 마크다운으로 포맷."""
    if not results:
        return "(검색 결과 없음)"

    lines: list[str] = []
    total = 0
    for i, r in enumerate(results, 1):
        entry = f"**{i}. [{r.title}]({r.url})**"
        if r.published:
            entry += f" ({r.published})"
        entry += f"\n{r.snippet}\n"
        if total + len(entry) > maxChars:
            lines.append(f"... ({len(results) - i + 1}건 생략)")
            break
        lines.append(entry)
        total += len(entry)

    return "\n".join(lines)
