"""gather/search.py + gather/reader.py 단위 테스트."""

import pytest

pytestmark = pytest.mark.unit


# ══════════════════════════════════════
# search.py
# ══════════════════════════════════════


def test_searchResult_dataclass():
    from dartlab.gather.search import SearchResult

    r = SearchResult(title="t", url="u", snippet="s", source="tavily")
    assert r.title == "t"
    assert r.source == "tavily"
    assert r.published is None


def test_searchAvailable_returns_dict():
    from dartlab.gather.search import searchAvailable

    avail = searchAvailable()
    assert "tavily" in avail
    assert "duckduckgo" in avail
    assert "any" in avail
    assert isinstance(avail["any"], bool)


def test_formatResults_empty():
    from dartlab.gather.search import formatResults

    assert "없음" in formatResults([])


def test_formatResults_with_items():
    from dartlab.gather.search import SearchResult, formatResults

    results = [
        SearchResult(title="Test", url="https://example.com", snippet="Hello", source="tavily", published="2026-01-01"),
        SearchResult(title="Test2", url="https://example2.com", snippet="World", source="duckduckgo"),
    ]
    md = formatResults(results)
    assert "Test" in md
    assert "example.com" in md
    assert "2026-01-01" in md


def test_formatResults_maxChars_truncation():
    from dartlab.gather.search import SearchResult, formatResults

    results = [
        SearchResult(title=f"Title{i}", url=f"https://example.com/{i}", snippet="x" * 200, source="tavily")
        for i in range(20)
    ]
    md = formatResults(results, maxChars=500)
    assert "생략" in md


def test_webSearch_returns_empty_when_no_backends(monkeypatch):
    from dartlab.gather import search

    monkeypatch.setattr(search, "_tavilyAvailable", lambda: False)
    monkeypatch.setattr(search, "_ddgAvailable", lambda: False)

    results = search.webSearch("test query")
    assert results == []


def test_webSearch_uses_cache(monkeypatch):
    from dartlab.gather import search
    from dartlab.gather.search import SearchResult

    callCount = [0]

    def fakeDdg(query, *, maxResults=8):
        callCount[0] += 1
        return [SearchResult(title="cached", url="u", snippet="s", source="duckduckgo")]

    monkeypatch.setattr(search, "_tavilyAvailable", lambda: False)
    monkeypatch.setattr(search, "_ddgAvailable", lambda: True)
    monkeypatch.setattr(search, "_searchDdg", fakeDdg)

    # 캐시 초기화
    search._cache.clear()

    r1 = search.webSearch("cache test")
    r2 = search.webSearch("cache test")
    assert len(r1) == 1
    assert r1 == r2
    assert callCount[0] == 1  # 캐시 히트로 1번만 호출


def test_newsSearch_returns_empty_when_no_backends(monkeypatch):
    from dartlab.gather import search

    monkeypatch.setattr(search, "_tavilyAvailable", lambda: False)
    monkeypatch.setattr(search, "_ddgAvailable", lambda: False)

    results = search.newsSearch("test query")
    assert results == []


# ══════════════════════════════════════
# reader.py
# ══════════════════════════════════════


def test_readUrl_invalid_url():
    from dartlab.gather.reader import readUrl

    result = readUrl("")
    assert "[오류]" in result

    result2 = readUrl("not-a-url")
    assert "[오류]" in result2


def test_readUrl_uses_cache(monkeypatch):
    from dartlab.gather import reader

    callCount = [0]

    def fakeJina(url):
        callCount[0] += 1
        return "# Hello World"

    monkeypatch.setattr(reader, "_readJina", fakeJina)
    reader._cache.clear()

    r1 = reader.readUrl("https://example.com")
    r2 = reader.readUrl("https://example.com")
    assert r1 == "# Hello World"
    assert r1 == r2
    assert callCount[0] == 1


def test_readUrl_fallback_to_bs4(monkeypatch):
    from dartlab.gather import reader

    def failJina(url):
        raise OSError("Jina down")

    def fakeBs4(url):
        return "BS4 content"

    monkeypatch.setattr(reader, "_readJina", failJina)
    monkeypatch.setattr(reader, "_readBs4", fakeBs4)
    reader._cache.clear()
    # circuit breaker 리셋
    from dartlab.gather.resilience import circuit_breaker
    circuit_breaker.record_success("jina")
    circuit_breaker.record_success("bs4_reader")

    result = reader.readUrl("https://example.com/test")
    assert result == "BS4 content"
