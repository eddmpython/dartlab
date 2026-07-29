"""dartlab.gather.mixins.price mirror 슬롯 — smoke import (P-G7.2).

룰 7 (src↔tests 1:1 mirror) 만족용 placeholder. 본격 단위 테스트는 후속.
"""

from __future__ import annotations

import importlib

import polars as pl
import pytest

pytestmark = pytest.mark.unit


def test_smoke_import() -> None:
    """``dartlab.gather.mixins.price`` 모듈 import 가능 — 모듈 구조 회귀 차단."""
    importlib.import_module("dartlab.gather.mixins.price")


def test_price_auto_detects_us_ticker() -> None:
    """Gather.price("AAPL") 는 market 인자 없이 US history 로 라우팅한다."""
    from dartlab.gather.mixins.price import _GatherPriceMixin

    seen = {}

    class Dummy:
        def history(self, stockCode, *, start, end, market):
            seen.update({"stockCode": stockCode, "start": start, "end": end, "market": market})
            return pl.DataFrame({"date": [], "close": []})

    result = _GatherPriceMixin.price(Dummy(), "AAPL")

    assert isinstance(result, pl.DataFrame)
    assert seen["stockCode"] == "AAPL"
    assert seen["market"] == "US"


# --- price(interval=...) 분봉 경로 ---


def test_interval_minutes_parsing() -> None:
    """일봉 alias 는 None, 분봉 문자열은 양의 정수 분."""
    from dartlab.gather.mixins.price import _intervalMinutes

    assert _intervalMinutes("1d") is None
    assert _intervalMinutes(None) is None
    assert _intervalMinutes("day") is None
    assert _intervalMinutes("1m") == 1
    assert _intervalMinutes("3m") == 3
    assert _intervalMinutes("5m") == 5
    assert _intervalMinutes("15m") == 15
    assert _intervalMinutes("bad") is None


@pytest.mark.parametrize(
    ("stockCode", "interval", "match"),
    [
        ("", "1d", "stockCode"),
        ("005930", "bad", "interval"),
        ("005930", "0m", "interval"),
    ],
)
def test_price_rejects_invalid_public_input(stockCode: str, interval: str, match: str) -> None:
    """public price 입력 오류를 일봉 fallback이나 source 장애로 오인하지 않는다."""
    from dartlab.gather.engine import Gather

    with pytest.raises(ValueError, match=match):
        Gather().price(stockCode, interval=interval)


def test_resample_minutes_aggregates_ohlcv() -> None:
    """1분봉 4행을 3분봉으로 리샘플 = 첫3분 버킷 + 남은1분 버킷, OHLCV 집계."""
    from datetime import datetime

    from dartlab.gather.mixins.price import _resampleMinutes

    df = pl.DataFrame(
        {
            "datetime": [
                datetime(2026, 7, 6, 9, 0),
                datetime(2026, 7, 6, 9, 1),
                datetime(2026, 7, 6, 9, 2),
                datetime(2026, 7, 6, 9, 3),
            ],
            "open": [10.0, 11.0, 12.0, 13.0],
            "high": [10.5, 11.5, 12.5, 13.5],
            "low": [9.5, 10.5, 11.5, 12.5],
            "close": [11.0, 12.0, 13.0, 14.0],
            "volume": [100, 200, 300, 400],
        }
    )
    out = _resampleMinutes(df, 3).sort("datetime")

    assert out.height == 2
    first = out.row(0, named=True)
    assert first["open"] == 10.0
    assert first["close"] == 13.0
    assert first["high"] == 12.5
    assert first["low"] == 9.5
    assert first["volume"] == 600


def test_price_routes_interval_to_intraday_else_daily() -> None:
    """interval 이 분봉이면 _intradayFrame, 기본이면 history 로 라우팅."""
    from dartlab.gather.mixins.price import _GatherPriceMixin

    seen: dict = {}

    class Dummy:
        def _intradayFrame(self, stockCode, *, market, interval, start, end):
            seen.update({"path": "intraday", "interval": interval, "market": market})
            return pl.DataFrame({"datetime": [], "close": []})

        def history(self, stockCode, *, start, end, market):
            seen.update({"path": "daily", "market": market})
            return pl.DataFrame({"date": [], "close": []})

    r = _GatherPriceMixin.price(Dummy(), "005930", interval="1m")
    assert isinstance(r, pl.DataFrame)
    assert seen["path"] == "intraday"
    assert seen["interval"] == "1m"

    seen.clear()
    _GatherPriceMixin.price(Dummy(), "005930")
    assert seen["path"] == "daily"


def test_history_cache_isolated_by_resolved_market(monkeypatch: pytest.MonkeyPatch) -> None:
    from dartlab.gather.engine import Gather
    from dartlab.gather.mixins import price as priceMixin

    calls: list[str] = []

    async def fakeFetch(stockCode, *, start, end, market, client):
        calls.append(market)
        return [{"date": "2026-01-02", "close": 1.0 if market == "KR" else 2.0}]

    monkeypatch.setattr(priceMixin._history, "fetch", fakeFetch)
    gather = Gather()

    kr = gather.history("005930", start="2026-01-01", end="2026-01-31", market="KR")
    us = gather.history("005930", start="2026-01-01", end="2026-01-31", market="US")
    krAgain = gather.history("005930", start="2026-01-01", end="2026-01-31", market="KR")

    assert calls == ["KR", "US"]
    assert kr["close"][0] == krAgain["close"][0] == 1.0
    assert us["close"][0] == 2.0


def test_flow_rejects_non_kr_market() -> None:
    """KR 전용 flow는 미지원 시장을 정상 무데이터로 위장하지 않는다."""
    from dartlab.gather.engine import Gather

    with pytest.raises(ValueError, match="KR 시장"):
        Gather().flow("AAPL", market="US")


def test_revenue_consensus_rejects_unsupported_market() -> None:
    """미배선 US를 정상 컨센서스 0건으로 위장하지 않는다."""
    from dartlab.gather.engine import Gather

    with pytest.raises(ValueError, match="KR 시장"):
        Gather().revenueConsensus("AAPL", market="US")


def test_revenue_consensus_preserves_source_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """public caller가 Naver 실패를 빈 목록으로 삼키지 않는다."""
    from dartlab.gather import domains
    from dartlab.gather.engine import Gather
    from dartlab.gather.types import SourceUnavailableError

    async def fail(*_args, **_kwargs):
        raise SourceUnavailableError("finance endpoint down")

    domain = type("Domain", (), {"fetchRevenueConsensus": fail})
    monkeypatch.setattr(domains, "loadDomain", lambda _name: domain)

    with pytest.raises(SourceUnavailableError, match="finance endpoint down"):
        Gather().revenueConsensus("005930")


def test_price_snapshot_preserves_source_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """public Gather.price snapshot이 source aggregate를 None으로 삼키지 않는다."""
    from dartlab.gather.engine import Gather
    from dartlab.gather.mixins import price as priceMixin
    from dartlab.gather.types import SourceAttemptsExhaustedError, SourceUnavailableError

    error = SourceAttemptsExhaustedError(
        "price",
        [("naver", SourceUnavailableError("network down"))],
    )

    async def fail(*args, **kwargs):
        raise error

    monkeypatch.setattr(priceMixin._price, "fetch", fail)

    with pytest.raises(SourceAttemptsExhaustedError) as excInfo:
        Gather().price("005930", snapshot=True)

    assert excInfo.value is error


def test_intraday_public_caller_preserves_source_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """public Gather.price 분봉 경로가 source 실패를 빈 DataFrame으로 바꾸지 않는다."""
    from dartlab.gather.engine import Gather
    from dartlab.gather.mixins import price as priceMixin
    from dartlab.gather.types import SourceAttemptsExhaustedError, SourceUnavailableError

    error = SourceAttemptsExhaustedError(
        "intraday",
        [("naver", SourceUnavailableError("network down"))],
    )

    async def fail(*args, **kwargs):
        raise error

    monkeypatch.setattr(priceMixin._intraday, "fetch", fail)

    with pytest.raises(SourceAttemptsExhaustedError) as excInfo:
        Gather().price("005930", interval="1m")

    assert excInfo.value is error
