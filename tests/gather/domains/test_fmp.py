"""dartlab.gather.domains.fmp mirror 슬롯 — smoke import (P-G7.2).

룰 7 (src↔tests 1:1 mirror) 만족용 placeholder. 본격 단위 테스트는 후속.
"""

from __future__ import annotations

import asyncio
import importlib

import pytest

pytestmark = pytest.mark.unit


def test_smoke_import() -> None:
    """``dartlab.gather.domains.fmp`` 모듈 import 가능 — 모듈 구조 회귀 차단."""
    importlib.import_module("dartlab.gather.domains.fmp")


def test_fetch_history_missing_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """API key 부재는 정상 무데이터가 아니라 source 설정 오류다."""
    from dartlab.gather.domains import fmp
    from dartlab.gather.types import SourceUnavailableError

    monkeypatch.setattr(fmp, "_getApiKey", lambda: None)

    with pytest.raises(SourceUnavailableError, match="FMP_API_KEY"):
        asyncio.run(fmp.fetchHistory("AAPL", object(), start="2026-01-01", end="2026-01-31"))


def test_fetch_history_json_failure_preserves_cause(monkeypatch: pytest.MonkeyPatch) -> None:
    """FMP JSON 파싱 실패 원인을 source 오류에 연결한다."""
    from dartlab.gather.domains import fmp
    from dartlab.gather.types import SourceUnavailableError

    class BadResponse:
        def json(self):
            raise ValueError("invalid json")

    class FakeClient:
        async def get(self, *args, **kwargs):
            return BadResponse()

    monkeypatch.setattr(fmp, "_getApiKey", lambda: "key")

    with pytest.raises(SourceUnavailableError) as excInfo:
        asyncio.run(fmp.fetchHistory("AAPL", FakeClient(), start="2026-01-01", end="2026-01-31"))

    assert isinstance(excInfo.value.__cause__, ValueError)


def test_fetch_history_valid_empty_historical_returns_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    """유효한 historical 빈 배열은 정상 무데이터다."""
    from dartlab.gather.domains import fmp

    class EmptyResponse:
        def json(self):
            return {"symbol": "AAPL", "historical": []}

    class FakeClient:
        async def get(self, *args, **kwargs):
            return EmptyResponse()

    monkeypatch.setattr(fmp, "_getApiKey", lambda: "key")

    assert asyncio.run(fmp.fetchHistory("AAPL", FakeClient(), start="2026-01-01", end="2026-01-31")) == []


def test_fetch_price_missing_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """FMP price의 키 부재는 정상 무데이터가 아니라 설정 오류다."""
    from dartlab.gather.domains import fmp
    from dartlab.gather.types import SourceUnavailableError

    monkeypatch.setattr(fmp, "_getApiKey", lambda: None)

    with pytest.raises(SourceUnavailableError, match="FMP_API_KEY"):
        asyncio.run(fmp.fetchPrice("AAPL", object()))


def test_fetch_price_malformed_quote_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """FMP quote schema 손상이 None으로 사라지지 않는다."""
    from dartlab.gather.domains import fmp
    from dartlab.gather.types import SourceUnavailableError

    class BadResponse:
        def json(self):
            return [{"price": "broken"}]

    class FakeClient:
        async def get(self, *args, **kwargs):
            return BadResponse()

    monkeypatch.setattr(fmp, "_getApiKey", lambda: "key")

    with pytest.raises(SourceUnavailableError, match="price"):
        asyncio.run(fmp.fetchPrice("AAPL", FakeClient()))
