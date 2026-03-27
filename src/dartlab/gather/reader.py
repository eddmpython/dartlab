"""URL -> 마크다운 추출 -- Jina Reader + httpx/BS4 fallback.

단일 URL의 본문을 마크다운 텍스트로 변환한다.
- 1차: Jina Reader API (r.jina.ai/{url})
- fallback: httpx + BeautifulSoup 직접 파싱
"""

from __future__ import annotations

import logging
import time

from .cache import GatherCache
from .resilience import circuit_breaker as _cb
from .resilience import health_tracker as _ht

log = logging.getLogger(__name__)

TTL_READ = 3600  # 1시간

_MAX_CONTENT_LENGTH = 8000  # LLM 컨텍스트 안전 한도 (문자)

_cache = GatherCache(max_entries=50)

_JINA_PREFIX = "https://r.jina.ai/"


# ══════════════════════════════════════
# Jina Reader
# ══════════════════════════════════════


def _readJina(url: str) -> str:
    """Jina Reader API로 URL -> 마크다운 변환."""
    import httpx

    headers: dict[str, str] = {
        "Accept": "text/markdown",
        "X-No-Cache": "true",
    }
    resp = httpx.get(f"{_JINA_PREFIX}{url}", headers=headers, timeout=15.0, follow_redirects=True)
    resp.raise_for_status()
    return resp.text[:_MAX_CONTENT_LENGTH]


# ══════════════════════════════════════
# httpx + BeautifulSoup fallback
# ══════════════════════════════════════


def _readBs4(url: str) -> str:
    """httpx + BeautifulSoup으로 URL 본문 추출."""
    import httpx
    from bs4 import BeautifulSoup

    resp = httpx.get(
        url,
        timeout=15.0,
        follow_redirects=True,
        headers={"User-Agent": "Mozilla/5.0 (compatible; dartlab/1.0)"},
    )
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # script, style 태그 제거
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    # article > main > body 순으로 본문 추출
    content = None
    for selector in ("article", "main", "[role='main']", "body"):
        content = soup.select_one(selector)
        if content:
            break

    if content is None:
        content = soup

    text = content.get_text(separator="\n", strip=True)

    # 연속 빈 줄 제거
    lines = [line for line in text.splitlines() if line.strip()]
    return "\n".join(lines)[:_MAX_CONTENT_LENGTH]


# ══════════════════════════════════════
# 통합 API
# ══════════════════════════════════════


def readUrl(url: str) -> str:
    """URL 본문을 마크다운/텍스트로 추출.

    Returns:
        추출된 텍스트. 실패 시 오류 메시지 문자열.
    """
    if not url or not url.startswith(("http://", "https://")):
        return f"[오류] 유효한 URL이 아닙니다: {url}"

    # 캐시
    cacheKey = f"read:{url}"
    cached = _cache.get(cacheKey)
    if cached is not None:
        return cached  # type: ignore[return-value]

    result = ""

    # 1차: Jina Reader
    if not _cb.is_open("jina"):
        t0 = time.monotonic()
        try:
            result = _readJina(url)
            _cb.record_success("jina")
            _ht.record(source="jina", success=True, latency=time.monotonic() - t0)
        except (OSError, ValueError, RuntimeError) as e:
            log.warning("Jina Reader 실패 (%s): %s", url, e)
            _cb.record_failure("jina")
            _ht.record(source="jina", success=False, latency=time.monotonic() - t0)

    # 2차: BS4 fallback
    if not result and not _cb.is_open("bs4_reader"):
        t0 = time.monotonic()
        try:
            result = _readBs4(url)
            _cb.record_success("bs4_reader")
            _ht.record(source="bs4_reader", success=True, latency=time.monotonic() - t0)
        except (OSError, ValueError, RuntimeError) as e:
            log.warning("BS4 Reader 실패 (%s): %s", url, e)
            _cb.record_failure("bs4_reader")
            _ht.record(source="bs4_reader", success=False, latency=time.monotonic() - t0)

    if not result:
        return f"[오류] URL 내용을 추출할 수 없습니다: {url}"

    _cache.put(cacheKey, result, TTL_READ)
    return result
