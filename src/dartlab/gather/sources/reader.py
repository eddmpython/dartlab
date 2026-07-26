"""URL -> 마크다운 추출 -- Jina Reader + httpx/BS4 fallback.

단일 URL의 본문을 마크다운 텍스트로 변환한다.
- 1차: Jina Reader API (r.jina.ai/{url})
- fallback: httpx + BeautifulSoup 직접 파싱
"""

from __future__ import annotations

import logging
import time

from ..infra.cache import GatherCache
from ..infra.resilience import circuitBreaker as _cb
from ..infra.resilience import healthTracker as _ht

log = logging.getLogger(__name__)

TTL_READ = 3600  # 1시간

_MAX_CONTENT_LENGTH = 8000  # LLM 컨텍스트 안전 한도 (문자)

_cache = GatherCache(maxEntries=50)

_JINA_PREFIX = "https://r.jina.ai/"


# ══════════════════════════════════════
# Jina Reader
# ══════════════════════════════════════


def _readJina(url: str) -> str:
    """Jina Reader API로 URL 본문을 마크다운으로 변환.

    r.jina.ai 프록시를 통해 웹 페이지를 마크다운으로 추출한다.
    결과는 _MAX_CONTENT_LENGTH(8000자)로 잘린다.

    Parameters
    ----------
    url : str
        추출할 웹 페이지 URL.

    Returns
    -------
    str
        마크다운 형식의 본문 텍스트 (최대 8000자).

    Raises
    ------
    httpx.HTTPStatusError
        HTTP 응답 상태가 4xx/5xx인 경우.
    """
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
    """httpx + BeautifulSoup으로 URL 본문을 플레인 텍스트로 추출.

    script/style/nav/footer 등 비본문 태그를 제거한 뒤
    article > main > body 순으로 본문 영역을 탐색한다.
    결과는 _MAX_CONTENT_LENGTH(8000자)로 잘린다.

    Parameters
    ----------
    url : str
        추출할 웹 페이지 URL.

    Returns
    -------
    str
        줄바꿈 구분 플레인 텍스트 (최대 8000자).

    Raises
    ------
    httpx.HTTPStatusError
        HTTP 응답 상태가 4xx/5xx인 경우.
    """
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

    Capabilities:
        - Jina Reader (primary) → BS4 fallback
        - 캐시 TTL 적용
        - 본문은 untrusted external — caller 가 wrapExternalInResult 필요

    AIContext:
        - AI 엔진의 외부 본문 fetch 도구 (ai/tools 가 호출)
        - 본문은 untrusted, 직접 instruction 으로 사용 금지

    Guide:
        Jina 가 정제된 markdown 으로 본문 추출. 실패 시 BS4 raw HTML 추출.

    When:
        AI 가 외부 URL 본문 inline 분석 필요 시.

    How:
        url → Jina Reader API → markdown → cache → return.

    Args:
        url: ``http://`` 또는 ``https://`` 로 시작하는 본문 추출 대상 URL.

    Returns:
        추출된 텍스트. 실패 시 오류 메시지 문자열.

    Requires:
        네트워크 (Jina Reader API + 대상 URL).

    Raises:
        없음 — Jina/BS4 실패는 fallback 후 오류 메시지 문자열로 반환.

    Example:
        >>> readUrl("https://example.com/article")

    See Also:
        ``dartlab.ai.tools.formatting.wrapExternalInResult`` — untrusted 마커.
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
    if not _cb.isOpen("jina"):
        t0 = time.monotonic()
        try:
            result = _readJina(url)
            _cb.recordSuccess("jina")
            _ht.record(source="jina", success=True, latency=time.monotonic() - t0)
        except (OSError, ValueError, RuntimeError) as e:
            log.warning("Jina Reader 실패 (%s): %s", url, e)
            _cb.recordFailure("jina")
            _ht.record(source="jina", success=False, latency=time.monotonic() - t0)

    # 2차: BS4 fallback
    if not result and not _cb.isOpen("bs4_reader"):
        t0 = time.monotonic()
        try:
            result = _readBs4(url)
            _cb.recordSuccess("bs4_reader")
            _ht.record(source="bs4_reader", success=True, latency=time.monotonic() - t0)
        except (OSError, ValueError, RuntimeError) as e:
            log.warning("BS4 Reader 실패 (%s): %s", url, e)
            _cb.recordFailure("bs4_reader")
            _ht.record(source="bs4_reader", success=False, latency=time.monotonic() - t0)

    if not result:
        return f"[오류] URL 내용을 추출할 수 없습니다: {url}"

    _cache.put(cacheKey, result, TTL_READ)
    return result
