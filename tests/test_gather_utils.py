"""gather 유틸 함수 단위 테스트 — search, cache, resilience."""

import pytest

pytestmark = pytest.mark.unit

from dartlab.gather.cache import GatherCache
from dartlab.gather.resilience import CircuitBreaker, SourceHealthTracker
from dartlab.gather.search import SearchResult, formatResults, searchAvailable

# ══════════════════════════════════════
# SearchResult
# ══════════════════════════════════════


class TestSearchResult:
    def test_construction(self):
        r = SearchResult(
            title="Test Title",
            url="https://example.com",
            snippet="Some snippet",
            source="tavily",
        )
        assert r.title == "Test Title"
        assert r.url == "https://example.com"
        assert r.snippet == "Some snippet"
        assert r.source == "tavily"
        assert r.published is None

    def test_published_field(self):
        r = SearchResult(title="T", url="U", snippet="S", source="tavily", published="2024-01-01")
        assert r.published == "2024-01-01"

    def test_frozen(self):
        r = SearchResult(title="T", url="U", snippet="S", source="tavily")
        with pytest.raises(AttributeError):
            r.title = "new"  # type: ignore[misc]


# ══════════════════════════════════════
# searchAvailable
# ══════════════════════════════════════


class TestSearchAvailable:
    def test_no_tavily(self, monkeypatch):
        """TAVILY_API_KEY 없으면 tavily=False."""
        monkeypatch.delenv("TAVILY_API_KEY", raising=False)
        result = searchAvailable()
        assert result["tavily"] is False
        assert result["any"] is False

    def test_with_tavily_key_but_no_sdk(self, monkeypatch):
        """API 키는 있지만 tavily SDK가 없으면 False."""
        monkeypatch.setenv("TAVILY_API_KEY", "test-key")
        from dartlab.gather import search as mod

        monkeypatch.setattr(mod, "_tavilyAvailable", lambda: False)
        result = searchAvailable()
        assert result["tavily"] is False

    def test_with_tavily_available(self, monkeypatch):
        """tavily 사용 가능하면 True."""
        from dartlab.gather import search as mod

        monkeypatch.setattr(mod, "_tavilyAvailable", lambda: True)
        result = searchAvailable()
        assert result["tavily"] is True
        assert result["any"] is True


# ══════════════════════════════════════
# formatResults
# ══════════════════════════════════════


class TestFormatResults:
    def test_empty_list(self):
        assert formatResults([]) == "(검색 결과 없음)"

    def test_single_result(self):
        results = [
            SearchResult(
                title="Hello",
                url="https://example.com",
                snippet="World",
                source="tavily",
            )
        ]
        text = formatResults(results)
        assert "Hello" in text
        assert "https://example.com" in text
        assert "World" in text

    def test_published_date_shown(self):
        results = [
            SearchResult(
                title="T",
                url="http://x.com",
                snippet="S",
                source="tavily",
                published="2024-03-15",
            )
        ]
        text = formatResults(results)
        assert "2024-03-15" in text

    def test_max_chars_truncation(self):
        results = [
            SearchResult(
                title=f"Title {i}",
                url=f"http://example.com/{i}",
                snippet="A" * 200,
                source="tavily",
            )
            for i in range(20)
        ]
        text = formatResults(results, maxChars=500)
        assert "생략" in text

    def test_numbering(self):
        results = [SearchResult(title=f"T{i}", url=f"http://x/{i}", snippet="s", source="t") for i in range(3)]
        text = formatResults(results)
        assert "**1." in text
        assert "**2." in text
        assert "**3." in text


# ══════════════════════════════════════
# GatherCache
# ══════════════════════════════════════


class TestGatherCache:
    def test_put_and_get(self):
        cache = GatherCache(max_entries=10)
        cache.put("key1", "value1", ttl=60)
        assert cache.get("key1") == "value1"

    def test_missing_key(self):
        cache = GatherCache(max_entries=10)
        assert cache.get("nonexistent") is None

    def test_ttl_expiry(self, monkeypatch):
        """TTL 만료 시 None 반환, stale에 보존."""
        from dartlab.gather import cache as cache_mod

        t = [1000.0]

        def fake_monotonic():
            return t[0]

        monkeypatch.setattr(cache_mod.time, "monotonic", fake_monotonic)

        cache = GatherCache(max_entries=10)
        cache.put("k", "v", ttl=10)

        # 아직 만료 안 됨
        assert cache.get("k") == "v"

        # 만료
        t[0] = 1011.0
        assert cache.get("k") is None

        # stale에서 가져올 수 있다
        assert cache.get_stale("k") == "v"

    def test_max_entries_eviction(self):
        cache = GatherCache(max_entries=3)
        cache.put("a", 1, ttl=60)
        cache.put("b", 2, ttl=60)
        cache.put("c", 3, ttl=60)
        cache.put("d", 4, ttl=60)
        # a가 축출됨
        assert cache.size == 3
        assert cache.get("a") is None
        assert cache.get("d") == 4

    def test_invalidate(self):
        cache = GatherCache(max_entries=10)
        cache.put("005930:price", "p", ttl=60)
        cache.put("005930:flow", "f", ttl=60)
        cache.put("000660:price", "p2", ttl=60)
        cache.invalidate("005930")
        assert cache.get("005930:price") is None
        assert cache.get("005930:flow") is None
        assert cache.get("000660:price") == "p2"

    def test_clear(self):
        cache = GatherCache(max_entries=10)
        cache.put("a", 1, ttl=60)
        cache.put("b", 2, ttl=60)
        cache.clear()
        assert cache.size == 0

    def test_put_typed(self):
        cache = GatherCache(max_entries=10)
        cache.put_typed("005930", "price", "data")
        assert cache.get("005930:price") == "data"


# ══════════════════════════════════════
# CircuitBreaker
# ══════════════════════════════════════


class TestCircuitBreaker:
    def test_initially_closed(self):
        cb = CircuitBreaker(failure_threshold=3)
        assert cb.is_open("src") is False
        assert cb.state("src") == "closed"

    def test_opens_after_threshold(self):
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=300.0)
        cb.record_failure("src")
        cb.record_failure("src")
        assert cb.is_open("src") is False
        cb.record_failure("src")
        assert cb.is_open("src") is True

    def test_success_resets(self):
        cb = CircuitBreaker(failure_threshold=2)
        cb.record_failure("src")
        cb.record_failure("src")
        # 서킷 열림
        assert cb.is_open("src") is True
        cb.record_success("src")
        assert cb.is_open("src") is False
        assert cb.state("src") == "closed"

    def test_independent_sources(self):
        cb = CircuitBreaker(failure_threshold=2)
        cb.record_failure("a")
        cb.record_failure("a")
        assert cb.is_open("a") is True
        assert cb.is_open("b") is False


# ══════════════════════════════════════
# SourceHealthTracker
# ══════════════════════════════════════


class TestHealthTracker:
    def test_default_score(self):
        ht = SourceHealthTracker()
        assert ht.score("unknown") == 0.5

    def test_all_success(self):
        ht = SourceHealthTracker()
        for _ in range(10):
            ht.record("src", success=True, latency=0.1)
        score = ht.score("src")
        # success_rate=1.0 * 0.7 + latency_score(high) * 0.3 -> ~1.0
        assert score > 0.9

    def test_all_failure(self):
        ht = SourceHealthTracker()
        for _ in range(10):
            ht.record("src", success=False, latency=0.0)
        score = ht.score("src")
        # success_rate=0 * 0.7 + latency_score * 0.3
        assert score < 0.3

    def test_reorder_significant_difference(self):
        ht = SourceHealthTracker()
        for _ in range(20):
            ht.record("fast", success=True, latency=0.1)
        for _ in range(20):
            ht.record("slow", success=False, latency=5.0)
        result = ht.reorder(["slow", "fast"])
        assert result[0] == "fast"

    def test_reorder_preserves_order_when_similar(self):
        ht = SourceHealthTracker()
        for _ in range(10):
            ht.record("a", success=True, latency=0.1)
            ht.record("b", success=True, latency=0.2)
        result = ht.reorder(["a", "b"])
        assert result == ["a", "b"]
