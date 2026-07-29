"""dartlab.gather.domains.yahooChart mirror 슬롯 — smoke import (P-G7.2).

룰 7 (src↔tests 1:1 mirror) 만족용 placeholder. 본격 단위 테스트는 후속.
"""

from __future__ import annotations

import asyncio
import importlib

import pytest

pytestmark = pytest.mark.unit


def test_smoke_import() -> None:
    """``dartlab.gather.domains.yahooChart`` 모듈 import 가능 — 모듈 구조 회귀 차단."""
    importlib.import_module("dartlab.gather.domains.yahooChart")


def test_fetch_history_network_failure_preserves_cause() -> None:
    """Yahoo 요청 장애를 빈 이력으로 바꾸지 않는다."""
    from dartlab.gather.domains import yahooChart
    from dartlab.gather.types import SourceUnavailableError

    class FailingClient:
        async def get(self, *args, **kwargs):
            raise SourceUnavailableError("network down")

    with pytest.raises(SourceUnavailableError) as excInfo:
        asyncio.run(yahooChart.fetchHistory("AAPL", FailingClient()))

    assert isinstance(excInfo.value.__cause__, SourceUnavailableError)


def test_fetch_history_valid_empty_result_returns_empty() -> None:
    """유효한 Yahoo chart result 빈 배열은 정상 무데이터다."""
    from dartlab.gather.domains import yahooChart

    class EmptyResponse:
        def json(self):
            return {"chart": {"result": [], "error": None}}

    class EmptyClient:
        async def get(self, *args, **kwargs):
            return EmptyResponse()

    assert asyncio.run(yahooChart.fetchHistory("AAPL", EmptyClient())) == []


def test_fetch_history_malformed_quote_raises() -> None:
    """timestamp가 있는데 quote schema가 없으면 source 오류다."""
    from dartlab.gather.domains import yahooChart
    from dartlab.gather.types import SourceUnavailableError

    class BadResponse:
        def json(self):
            return {
                "chart": {
                    "result": [{"timestamp": [1], "indicators": {"quote": [{}]}}],
                    "error": None,
                }
            }

    class BadClient:
        async def get(self, *args, **kwargs):
            return BadResponse()

    with pytest.raises(SourceUnavailableError, match="필수 series"):
        asyncio.run(yahooChart.fetchHistory("AAPL", BadClient()))
