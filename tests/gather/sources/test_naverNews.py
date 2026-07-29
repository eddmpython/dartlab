"""네이버 뉴스 소스 (naverNews) 단위 테스트.

market 가드 · 무키 graceful · <b>태그/엔티티 정리 · 응답 파싱 · archive canonical.
네트워크 미사용 (getKey/_fetchAsync stub + _parseItems 직접).
"""

from __future__ import annotations

import asyncio

import pytest

from dartlab.gather.sources import naverNews
from dartlab.gather.sources.naverNews import _clean, _parseItems
from dartlab.gather.sources.newsSchema import NEWS_ARCHIVE_SCHEMA
from dartlab.gather.types import NewsItem

pytestmark = pytest.mark.unit


def test_clean_strips_tags_and_entities() -> None:
    """<b> 등 태그 제거 + HTML 엔티티 unescape + strip."""
    assert _clean("<b>삼성</b>전자 &amp; SK") == "삼성전자 & SK"
    assert _clean(None) == ""
    assert _clean("  plain  ") == "plain"


def test_fetch_non_kr_market_raises() -> None:
    """market != KR → 명시적 입력 오류."""
    with pytest.raises(ValueError, match="KR 시장"):
        asyncio.run(naverNews._fetchAsync("query", market="US"))


@pytest.mark.parametrize(
    "kwargs",
    [
        {"query": ""},
        {"query": "query", "display": 0},
        {"query": "query", "sort": "bad"},
        {"query": "query", "pages": 0},
    ],
)
def test_fetch_invalid_input_raises_before_credentials(kwargs: dict) -> None:
    """입력 오류는 자격증명/source 실패로 오인하지 않는다."""
    query = kwargs.pop("query")
    with pytest.raises(ValueError):
        asyncio.run(naverNews._fetchAsync(query, **kwargs))


def test_fetch_missing_credentials_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """자격증명 미설정은 정상 무데이터가 아닌 source 설정 오류."""
    from dartlab.gather.types import SourceUnavailableError

    monkeypatch.setattr(naverNews, "getKey", lambda *a, **k: None)
    with pytest.raises(SourceUnavailableError, match="자격증명"):
        asyncio.run(naverNews._fetchAsync("query", market="KR"))


def test_parse_items() -> None:
    """검색 응답 JSON → NewsItem (url=originallink, source=도메인, description=스니펫)."""
    data = {
        "items": [
            {
                "title": "<b>삼성</b>전자 &amp; SK",
                "description": "<b>스니펫</b> 내용",
                "originallink": "https://www.yna.co.kr/view/1",
                "link": "https://n.news.naver.com/x",
                "pubDate": "Mon, 08 Jun 2026 12:34:56 +0900",
            },
            {"title": "링크없음", "description": "d", "pubDate": "Mon, 08 Jun 2026 00:00:00 +0900"},
        ]
    }
    items = _parseItems(data)
    assert len(items) == 1  # 링크 없는 항목 skip
    it = items[0]
    assert it.title == "삼성전자 & SK"
    assert it.description == "스니펫 내용"
    assert it.url == "https://www.yna.co.kr/view/1"  # originallink 우선
    assert it.source == "yna.co.kr"  # www. 제거
    assert it.date == "2026-06-08"


def test_parse_items_rejects_malformed_schema() -> None:
    """items schema 손상을 정상 빈 뉴스로 바꾸지 않는다."""
    from dartlab.gather.types import SourceUnavailableError

    with pytest.raises(SourceUnavailableError, match="items"):
        _parseItems({"items": "broken"})


def test_archive_canonical_columns(monkeypatch: pytest.MonkeyPatch) -> None:
    """fetchHeadlinesForArchive → canonical 17컬럼 + description 채움."""
    item = NewsItem(
        date="2026-06-08",
        title="t",
        source="yna.co.kr",
        url="https://x/a",
        description="snippet",
    )

    async def _stub(query, *, market="KR", **kw):
        return [item]

    monkeypatch.setattr(naverNews, "_fetchAsync", _stub)
    df = naverNews.fetchHeadlinesForArchive(["삼성전자"], market="KR", days=3650)
    assert set(df.columns) == set(NEWS_ARCHIVE_SCHEMA.keys())
    assert df.height == 1
    assert df["description"][0] == "snippet"
    assert df["market"][0] == "KR"


def test_archive_non_kr_raises() -> None:
    """market != KR은 정상 무데이터가 아니라 입력 오류다."""
    with pytest.raises(ValueError, match="KR 시장"):
        naverNews.fetchHeadlinesForArchive(["q"], market="US")


class _FakeResp:
    def __init__(self, items: list[dict], status_code: int = 200) -> None:
        self._items = items
        self.status_code = status_code

    def raise_for_status(self) -> None:  # noqa: D401
        pass

    def json(self) -> dict:
        return {"items": self._items}


class _FakeClient:
    """start 페이징 stub — page 0(start=1) 100건, page 1(start=101) 50건(짧음→마지막), 이후 호출 안 됨."""

    def __init__(self, calls: list[int]) -> None:
        self._calls = calls

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a) -> None:
        pass

    async def get(self, url, *, params, headers, timeout):  # noqa: ANN001
        start = params["start"]
        self._calls.append(start)
        if start == 1:
            items = [
                {"title": f"t{i}", "originallink": f"https://x/{i}", "pubDate": "Mon, 08 Jun 2026 00:00:00 +0900"}
                for i in range(100)
            ]
        elif start == 101:
            # 50건(<display) — 마지막 페이지. 1건은 page0 와 url 중복(dedup 검증).
            items = [
                {"title": f"t{i}", "originallink": f"https://x/{i}", "pubDate": "Mon, 08 Jun 2026 00:00:00 +0900"}
                for i in range(99, 149)
            ]
        else:
            items = []
        return _FakeResp(items)


def test_fetch_paging_accumulates_dedups_and_stops(monkeypatch: pytest.MonkeyPatch) -> None:
    """pages>1 → start 페이징 누적 + url dedup + 짧은 페이지에서 조기 종료."""
    import types

    import httpx

    monkeypatch.setattr(naverNews, "getKey", lambda *a, **k: "key")
    fakeBreaker = types.SimpleNamespace(
        isOpen=lambda *a, **k: False, recordSuccess=lambda *a, **k: None, recordFailure=lambda *a, **k: None
    )
    monkeypatch.setattr(naverNews, "_circuit_breaker", fakeBreaker)
    monkeypatch.setattr(naverNews, "_health_tracker", types.SimpleNamespace(record=lambda *a, **k: None))
    calls: list[int] = []
    monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **k: _FakeClient(calls))

    items = asyncio.run(naverNews._fetchAsync("삼성전자", market="KR", pages=10))
    # page0 100건 + page1 50건 중 신규 49건(1건 중복) = 149, page1 이 <100 이라 page2 호출 안 됨.
    assert calls == [1, 101]
    assert len(items) == 149
    urls = [it.url for it in items]
    assert len(urls) == len(set(urls))  # dedup


class _Rate429Client:
    """start=1 첫 시도 429 → 재시도 시 200(items). 429 백오프 재시도 검증용."""

    def __init__(self, attempts: list[int]) -> None:
        self._attempts = attempts

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a) -> None:
        pass

    async def get(self, url, *, params, headers, timeout):  # noqa: ANN001
        self._attempts.append(params["start"])
        if len(self._attempts) == 1:
            return _FakeResp([], status_code=429)  # 첫 시도 throttle
        return _FakeResp(
            [{"title": "t", "originallink": "https://x/1", "pubDate": "Mon, 08 Jun 2026 00:00:00 +0900"}],
            status_code=200,
        )


def test_fetch_retries_on_429(monkeypatch: pytest.MonkeyPatch) -> None:
    """429 → 백오프 재시도 후 성공 수집 (대량 fanout 커버리지 균일화)."""
    import types

    import httpx

    monkeypatch.setattr(naverNews, "getKey", lambda *a, **k: "key")
    monkeypatch.setattr(
        naverNews,
        "_circuit_breaker",
        types.SimpleNamespace(
            isOpen=lambda *a, **k: False, recordSuccess=lambda *a, **k: None, recordFailure=lambda *a, **k: None
        ),
    )
    monkeypatch.setattr(naverNews, "_health_tracker", types.SimpleNamespace(record=lambda *a, **k: None))

    async def _noSleep(_):
        return None

    monkeypatch.setattr(naverNews.asyncio, "sleep", _noSleep)
    attempts: list[int] = []
    monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **k: _Rate429Client(attempts))

    items = asyncio.run(naverNews._fetchAsync("삼성전자", market="KR", pages=1))
    assert len(attempts) == 2  # 429 1회 + 재시도 1회
    assert len(items) == 1  # 재시도에서 수집


def test_fetch_partial_page_failure_is_not_returned(monkeypatch: pytest.MonkeyPatch) -> None:
    """첫 페이지를 모았어도 다음 페이지 장애를 부분 성공으로 반환하지 않는다."""
    import types

    import httpx

    from dartlab.gather.types import SourceUnavailableError

    class PartialClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def get(self, url, *, params, headers, timeout):
            if params["start"] == 1:
                return _FakeResp(
                    [
                        {
                            "title": f"t{i}",
                            "originallink": f"https://x/{i}",
                            "pubDate": "Mon, 08 Jun 2026 00:00:00 +0900",
                        }
                        for i in range(100)
                    ]
                )
            raise OSError("second page down")

    monkeypatch.setattr(naverNews, "getKey", lambda *args, **kwargs: "key")
    monkeypatch.setattr(
        naverNews,
        "_circuit_breaker",
        types.SimpleNamespace(
            isOpen=lambda *args, **kwargs: False,
            recordSuccess=lambda *args, **kwargs: None,
            recordFailure=lambda *args, **kwargs: None,
        ),
    )
    monkeypatch.setattr(
        naverNews,
        "_health_tracker",
        types.SimpleNamespace(record=lambda *args, **kwargs: None),
    )
    monkeypatch.setattr(httpx, "AsyncClient", lambda *args, **kwargs: PartialClient())

    with pytest.raises(SourceUnavailableError) as excInfo:
        asyncio.run(naverNews._fetchAsync("삼성전자", market="KR", pages=2))

    assert isinstance(excInfo.value.__cause__, OSError)
