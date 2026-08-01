"""Piotroski F7와 9점 coverage 계약 회귀."""

from __future__ import annotations

import polars as pl
import pytest

from dartlab.quant.alphas.piotroski import _scoreOne

pytestmark = pytest.mark.unit


def _period(*, improving: bool) -> tuple[pl.DataFrame, pl.DataFrame]:
    cur = pl.DataFrame(
        {
            "fy": [2025],
            "total_assets": [100.0],
            "net_profit": [12.0],
            "operating_cf": [20.0],
            "total_liabilities": [35.0],
            "current_assets": [50.0],
            "current_liabilities": [20.0],
            "gross_profit": [45.0],
            "sales": [120.0],
        }
    )
    prev = pl.DataFrame(
        {
            "fy": [2024],
            "total_assets": [100.0],
            "net_profit": [8.0 if improving else 15.0],
            "operating_cf": [10.0],
            "total_liabilities": [45.0],
            "current_assets": [40.0],
            "current_liabilities": [20.0],
            "gross_profit": [30.0],
            "sales": [100.0],
        }
    )
    return cur, prev


def test_missing_share_ledger_does_not_award_f7_or_total() -> None:
    cur, prev = _period(improving=True)

    result = _scoreOne(cur, prev)

    assert result is not None
    assert result["components"]["noNewShares"] is None
    assert result["total"] is None
    assert result["coverage"] == {"observed": 8, "expected": 9, "scoreEligible": False}


def test_share_increase_fails_f7() -> None:
    cur, prev = _period(improving=True)

    result = _scoreOne(cur, prev, sharesCur=110.0, sharesPrev=100.0)

    assert result is not None
    assert result["components"]["noNewShares"] is False
    assert result["coverage"]["scoreEligible"] is True
    assert result["total"] == result["partialTotal"]


def test_flat_share_count_completes_canonical_nine_signals() -> None:
    cur, prev = _period(improving=True)

    result = _scoreOne(cur, prev, sharesCur=100.0, sharesPrev=100.0)

    assert result is not None
    assert result["components"]["noNewShares"] is True
    assert result["coverage"]["observed"] == 9
    assert result["total"] == 9
