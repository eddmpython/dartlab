"""DART와 EDGAR listed equity universe owner resolver tests."""

from __future__ import annotations

import polars as pl
import pytest

from dartlab.providers.universe import listedEquityUniverse


def testKrUniverseUsesCanonicalSixDigitIdentity(monkeypatch):
    monkeypatch.setattr(
        "dartlab.gather.krx.listing.registry.getKindList",
        lambda: pl.DataFrame(
            {
                "종목코드": ["5930", "000660"],
                "회사명": ["삼성전자", "SK하이닉스"],
                "시장구분": ["유가", "유가"],
            }
        ),
    )

    frame = listedEquityUniverse(market="KR")

    assert frame["entityId"].to_list() == ["000660", "005930"]
    assert frame["provider"].unique().to_list() == ["dart"]


def testUsUniverseKeepsTickerAndCikIdentity(monkeypatch):
    monkeypatch.setattr(
        "dartlab.core.dataLoader.loadEdgarTargetUniverse",
        lambda tier="all": pl.DataFrame(
            {
                "ticker": ["aapl"],
                "cik": ["320193"],
                "title": ["Apple"],
                "exchange": ["Nasdaq"],
            }
        ),
    )

    frame = listedEquityUniverse(market="US")

    assert frame.row(0, named=True) == {
        "entityId": "AAPL",
        "sourceEntityId": "0000320193",
        "name": "Apple",
        "exchange": "Nasdaq",
        "market": "US",
        "provider": "edgar",
    }


@pytest.mark.parametrize(
    ("kwargs", "code"),
    [
        ({"market": "JP"}, "UNIVERSE_MARKET_UNSUPPORTED"),
        ({"market": "KR", "membership": "allKnown"}, "UNIVERSE_MEMBERSHIP_UNSUPPORTED"),
        ({"market": "KR", "asOf": "2025-01-01"}, "UNIVERSE_PIT_UNSUPPORTED"),
    ],
)
def testUnsupportedUniverseContractsFailClosed(kwargs, code):
    with pytest.raises(ValueError, match=code):
        listedEquityUniverse(**kwargs)
