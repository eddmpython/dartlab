"""EDGAR scan helpers — edgarCikToTicker 가 다중티커 CIK 에서 대표(보통주·첫) 티커를 채택하는지.

합성 universe → 네트워크/OOM 무관.
"""

from __future__ import annotations

import polars as pl
import pytest

pytestmark = pytest.mark.unit


def test_cik_to_ticker_first_wins_for_multiticker():
    """다중티커 CIK 는 첫 티커(보통주) 채택 — 마지막(우선주·구조화상품) 아님."""
    from dartlab.scan.builders.edgar.helpers import edgarCikToTicker

    univ = pl.DataFrame(
        {
            "cik": ["19617", "19617", "19617", "320193"],
            "ticker": ["JPM", "JPM-PC", "VYLD", "AAPL"],  # SEC 순서: 보통주 우선
        }
    )
    m = edgarCikToTicker(univ)
    assert m["0000019617"] == "JPM"  # 첫 티커(VYLD/우선주 아님)
    assert m["0000320193"] == "AAPL"


def test_cik_to_ticker_skips_empty_and_zero_pads():
    """빈 ticker 행 제외 + CIK 10자리 zero-pad 키."""
    from dartlab.scan.builders.edgar.helpers import edgarCikToTicker

    univ = pl.DataFrame({"cik": ["78003", "1234"], "ticker": ["PFE", None]})
    m = edgarCikToTicker(univ)
    assert m == {"0000078003": "PFE"}  # None ticker 제외, zero-pad
