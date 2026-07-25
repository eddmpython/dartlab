"""DART와 EDGAR listed equity universe owner resolver tests."""

from __future__ import annotations

from types import SimpleNamespace

import polars as pl
import pytest

from dartlab.providers.universe import listedEquityUniverse


def testKrUniverseUsesCanonicalSixDigitIdentity(monkeypatch):
    monkeypatch.setattr(
        "dartlab.core.listingResolver.getListingResolver",
        lambda: SimpleNamespace(
            kindList=lambda: pl.DataFrame(
                {
                    "종목코드": ["5930", "000660", "0001a0", "000가00"],
                    "회사명": ["삼성전자", "SK하이닉스", "알파", "잘못된코드"],
                    "시장구분": ["유가", "유가", "코스닥", "코스닥"],
                    "결산월": ["12월", "03월", "12월", "12월"],
                }
            )
        ),
    )

    frame = listedEquityUniverse(market="KR")

    assert frame["entityId"].to_list() == ["0001A0", "000660", "005930"]
    assert frame["provider"].unique().to_list() == ["dart"]
    assert frame["param_fiscalYearEndMonth"].to_list() == [12, 3, 12]


def testUsUniverseKeepsTickerAndCikIdentity(monkeypatch):
    monkeypatch.setattr(
        "dartlab.core.dataLoader.loadEdgarTargetUniverse",
        lambda tier="all", **_kwargs: pl.DataFrame(
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
