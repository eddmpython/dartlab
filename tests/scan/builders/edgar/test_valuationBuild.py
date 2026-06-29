"""EDGAR scan valuation 빌더 — XBRL primitive(shares·EPS·equity·netIncome) + 현재가에서
marketCap/per/pbr 계산이 KR valuation.parquet 동형 행을 내는지. 합성 facts 사용 → 네트워크/OOM 무관.
"""

from __future__ import annotations

import polars as pl
import pytest

pytestmark = pytest.mark.unit

_AS_OF = "2026-06-30T00:00:00+00:00"


def _facts(rows: list[dict]) -> pl.DataFrame:
    """computeValuationRow 입력 facts 합성 — namespace·tag·val·fp·form·filed·end 컬럼."""
    from datetime import date

    base = {"fp": "FY", "form": "10-K", "filed": date(2025, 11, 1), "end": date(2025, 9, 30)}
    return pl.DataFrame([{**base, **r} for r in rows])


def test_valuation_full():
    """shares·EPS·equity 모두 있으면 marketCap=price×shares, per=price/EPS, pbr=marketCap/equity."""
    from dartlab.scan.builders.edgar.valuationBuild import computeValuationRow

    facts = _facts(
        [
            {"namespace": "dei", "tag": "EntityCommonStockSharesOutstanding", "val": 1_000_000.0},
            {"namespace": "us-gaap", "tag": "EarningsPerShareDiluted", "val": 5.0},
            {"namespace": "us-gaap", "tag": "StockholdersEquity", "val": 2_000_000.0},
            {"namespace": "us-gaap", "tag": "NetIncomeLoss", "val": 500_000.0},
        ]
    )
    row = computeValuationRow(facts, "TEST", 100.0, asOf=_AS_OF)
    assert row is not None
    assert row["marketCap"] == 100.0 * 1_000_000  # 1e8
    assert row["per"] == 20.0  # 100 / 5
    assert row["pbr"] == 50.0  # 1e8 / 2e6
    assert row["stockCode"] == "TEST"


def test_valuation_eps_fallback_to_earnings():
    """EPS 결측이면 per = marketCap / netIncome 폴백."""
    from dartlab.scan.builders.edgar.valuationBuild import computeValuationRow

    facts = _facts(
        [
            {"namespace": "dei", "tag": "EntityCommonStockSharesOutstanding", "val": 1_000_000.0},
            {"namespace": "us-gaap", "tag": "StockholdersEquity", "val": 2_000_000.0},
            {"namespace": "us-gaap", "tag": "NetIncomeLoss", "val": 1_000_000.0},
        ]
    )
    row = computeValuationRow(facts, "NOEPS", 50.0, asOf=_AS_OF)
    assert row is not None
    assert row["per"] == 50.0  # marketCap 5e7 / netIncome 1e6
    assert row["pbr"] == 25.0


def test_valuation_no_price_excluded():
    """현재가 없으면 marketCap/per/pbr 모두 계산 불가 → None(밸류 비표시가 정직)."""
    from dartlab.scan.builders.edgar.valuationBuild import computeValuationRow

    facts = _facts(
        [
            {"namespace": "dei", "tag": "EntityCommonStockSharesOutstanding", "val": 1_000_000.0},
            {"namespace": "us-gaap", "tag": "StockholdersEquity", "val": 2_000_000.0},
        ]
    )
    assert computeValuationRow(facts, "NOPX", None, asOf=_AS_OF) is None


def test_valuation_negative_eps_no_per():
    """적자(EPS≤0·netIncome≤0)면 per=None, 그러나 marketCap·pbr 은 유지."""
    from dartlab.scan.builders.edgar.valuationBuild import computeValuationRow

    facts = _facts(
        [
            {"namespace": "dei", "tag": "EntityCommonStockSharesOutstanding", "val": 1_000_000.0},
            {"namespace": "us-gaap", "tag": "EarningsPerShareDiluted", "val": -2.0},
            {"namespace": "us-gaap", "tag": "StockholdersEquity", "val": 4_000_000.0},
            {"namespace": "us-gaap", "tag": "NetIncomeLoss", "val": -1_000_000.0},
        ]
    )
    row = computeValuationRow(facts, "LOSS", 40.0, asOf=_AS_OF)
    assert row is not None
    assert row["per"] is None  # 적자 → PER 무의미
    assert row["marketCap"] == 40_000_000.0
    assert row["pbr"] == 10.0
