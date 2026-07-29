"""dartlab.gather.domains.naverGlobal mirror 슬롯 — smoke import (P-G7.2).

룰 7 (src↔tests 1:1 mirror) 만족용 placeholder. 본격 단위 테스트는 후속.
"""

from __future__ import annotations

import asyncio
import importlib

import pytest

pytestmark = pytest.mark.unit


def test_smoke_import() -> None:
    """``dartlab.gather.domains.naverGlobal`` 모듈 import 가능 — 모듈 구조 회귀 차단."""
    importlib.import_module("dartlab.gather.domains.naverGlobal")


def test_fetch_history_reuters_failure_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reuters code 확인 요청 전멸은 매핑 없음으로 위장하지 않는다."""
    from dartlab.gather.domains import naverGlobal
    from dartlab.gather.types import SourceUnavailableError

    async def noThrottle():
        return None

    class FailingClient:
        async def get(self, *args, **kwargs):
            raise SourceUnavailableError("network down")

    naverGlobal._REUTERS_CACHE.clear()
    monkeypatch.setattr(naverGlobal, "_SUFFIXES", [""])
    monkeypatch.setattr(naverGlobal, "_throttle", noThrottle)

    with pytest.raises(SourceUnavailableError) as excInfo:
        asyncio.run(naverGlobal.fetchHistory("AAPL", FailingClient()))

    assert isinstance(excInfo.value.__cause__, SourceUnavailableError)


def test_fetch_history_partial_page_failure_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """앞 페이지를 받았어도 다음 페이지 장애를 부분 성공으로 반환하지 않는다."""
    from dartlab.gather.domains import naverGlobal
    from dartlab.gather.types import SourceUnavailableError

    async def resolveCode(*args, **kwargs):
        return "AAPL.O"

    async def noThrottle():
        return None

    class FakeResponse:
        def json(self):
            return {
                "priceInfos": [
                    {
                        "localDate": "20260102",
                        "openPrice": 100,
                        "highPrice": 110,
                        "lowPrice": 90,
                        "closePrice": 105,
                        "accumulatedTradingVolume": 1000,
                    }
                ]
            }

    class PartialClient:
        def __init__(self):
            self.calls = 0

        async def get(self, *args, **kwargs):
            self.calls += 1
            if self.calls == 1:
                return FakeResponse()
            raise SourceUnavailableError("second page down")

    monkeypatch.setattr(naverGlobal, "_resolveReutersCode", resolveCode)
    monkeypatch.setattr(naverGlobal, "_throttle", noThrottle)

    with pytest.raises(SourceUnavailableError) as excInfo:
        asyncio.run(naverGlobal.fetchHistory("AAPL", PartialClient()))

    assert isinstance(excInfo.value.__cause__, SourceUnavailableError)


def test_fetch_history_valid_empty_page_returns_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    """유효한 priceInfos 빈 배열은 정상 무데이터다."""
    from dartlab.gather.domains import naverGlobal

    async def resolveCode(*args, **kwargs):
        return "AAPL.O"

    async def noThrottle():
        return None

    class EmptyResponse:
        def json(self):
            return {"priceInfos": []}

    class EmptyClient:
        async def get(self, *args, **kwargs):
            return EmptyResponse()

    monkeypatch.setattr(naverGlobal, "_resolveReutersCode", resolveCode)
    monkeypatch.setattr(naverGlobal, "_throttle", noThrottle)

    assert asyncio.run(naverGlobal.fetchHistory("AAPL", EmptyClient())) == []
