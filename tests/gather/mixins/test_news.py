"""dartlab.gather.mixins.news real unit test (A 트랙 O3).

_GatherNewsMixin 의 news/dartDoc 2 메서드 emit wrap 검증.
"""

from __future__ import annotations

import importlib

import polars as pl
import pytest

pytestmark = pytest.mark.unit


def test_smoke_import() -> None:
    """``dartlab.gather.mixins.news`` 모듈 import 가능 — 모듈 구조 회귀 차단."""
    importlib.import_module("dartlab.gather.mixins.news")


def test_news_emits_gather_fetch(monkeypatch: pytest.MonkeyPatch) -> None:
    """news() 가 fetch 완료 시 emitGatherFetch 신호."""
    from dartlab.gather.engine import Gather
    from dartlab.gather.infra import telemetry as telemetryMod
    from dartlab.gather.sources import naverNews as naverMod
    from dartlab.gather.sources import news as newsMod

    captured: list = []
    monkeypatch.setattr(telemetryMod, "_coreEmit", lambda k, **kw: captured.append((k, kw)))

    # KR=네이버 우선 → 네트워크 격리 위해 naver stub([])로 google 폴백 경로 강제.
    async def fakeNaver(query, *, market="KR", client=None, **kw):
        return []

    async def fakeFetchAsync(query, *, market, days, client):
        return []

    monkeypatch.setattr(naverMod, "_fetchAsync", fakeNaver)
    monkeypatch.setattr(newsMod, "_fetchAsync", fakeFetchAsync)
    monkeypatch.setattr(newsMod, "toDataFrame", lambda items, **kwargs: pl.DataFrame())

    g = Gather()
    g.news("삼성전자", market="KR", days=7)

    fetchEmits = [c for c in captured if c[0] == "gather:fetch:done"]
    assert any(kw["axis"] == "news" for _, kw in fetchEmits)


def test_news_cache_isolated_by_days(monkeypatch: pytest.MonkeyPatch) -> None:
    from dartlab.gather.engine import Gather
    from dartlab.gather.sources import news as newsMod

    calls: list[int] = []

    async def fakeFetchAsync(query, *, market, days, client):
        calls.append(days)
        return [{"days": days}]

    monkeypatch.setattr(newsMod, "_fetchAsync", fakeFetchAsync)
    monkeypatch.setattr(newsMod, "toDataFrame", lambda items, **kwargs: pl.DataFrame(items))
    gather = Gather()

    thirty = gather.news("Apple", market="US", days=30)
    one = gather.news("Apple", market="US", days=1)
    thirtyAgain = gather.news("Apple", market="US", days=30)

    assert calls == [30, 1]
    assert thirty["days"][0] == thirtyAgain["days"][0] == 30
    assert one["days"][0] == 1


def test_news_all_sources_failed_preserves_attempts(monkeypatch: pytest.MonkeyPatch) -> None:
    """KR 뉴스 공급자 전멸 시 Naver와 Google 원인이 facade까지 도달한다."""
    from dartlab.gather.engine import Gather
    from dartlab.gather.sources import naverNews as naverMod
    from dartlab.gather.sources import news as newsMod
    from dartlab.gather.types import SourceAttemptsExhaustedError, SourceUnavailableError

    async def failNaver(*args, **kwargs):
        raise SourceUnavailableError("naver down")

    async def failGoogle(*args, **kwargs):
        raise SourceUnavailableError("google down")

    monkeypatch.setattr(naverMod, "_fetchAsync", failNaver)
    monkeypatch.setattr(newsMod, "_fetchAsync", failGoogle)

    with pytest.raises(SourceAttemptsExhaustedError) as excInfo:
        Gather().news("삼성전자", market="KR")

    assert list(excInfo.value.failures) == ["naver_news", "google_news"]


def test_news_valid_empty_response_is_not_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """한 공급자의 정상 빈 응답이 있으면 다른 공급자 장애와 구분해 빈 결과를 반환한다."""
    from dartlab.gather.engine import Gather
    from dartlab.gather.sources import naverNews as naverMod
    from dartlab.gather.sources import news as newsMod
    from dartlab.gather.types import SourceUnavailableError

    async def emptyNaver(*args, **kwargs):
        return []

    async def failGoogle(*args, **kwargs):
        raise SourceUnavailableError("google down")

    monkeypatch.setattr(naverMod, "_fetchAsync", emptyNaver)
    monkeypatch.setattr(newsMod, "_fetchAsync", failGoogle)

    assert Gather().news("삼성전자", market="KR").is_empty()


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"query": ""}, "query"),
        ({"query": "Apple", "market": "JP"}, "market"),
        ({"query": "Apple", "days": 0}, "days"),
    ],
)
def test_news_invalid_input_fails_before_provider(kwargs: dict, match: str) -> None:
    """public news 입력 오류는 provider 실패 aggregate로 오인하지 않는다."""
    from dartlab.gather.engine import Gather

    query = kwargs.pop("query")
    with pytest.raises(ValueError, match=match):
        Gather().news(query, **kwargs)
