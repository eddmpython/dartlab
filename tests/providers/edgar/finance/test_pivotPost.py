"""mirror smoke — edgar/finance/pivotPost.py (split helper).

분할 helper 모듈의 임포트 가능성 + 룰 7 mirror 슬롯 충족.
"""

from __future__ import annotations

import polars as pl
import pytest

pytestmark = pytest.mark.unit


def test_import() -> None:
    import dartlab.providers.edgar.finance.pivotPost as mod

    assert mod is not None


def test_calendarize_period_columns_renames_colliding_chain_simultaneously() -> None:
    from dartlab.providers.edgar.finance.pivotPost import _calendarizePeriodColumns

    fiscal = pl.DataFrame(
        {
            "tag": ["Revenues"],
            "2023-Q4": [90.0],
            "2024-Q1": [120.0],
        }
    )

    calendar = _calendarizePeriodColumns(
        fiscal,
        {
            "2023-Q4": "2023-Q3",
            "2024-Q1": "2023-Q4",
        },
    )

    assert calendar.columns == ["tag", "2023-Q3", "2023-Q4"]
    assert calendar.row(0, named=True) == {
        "tag": "Revenues",
        "2023-Q3": 90.0,
        "2023-Q4": 120.0,
    }


def test_calendarize_period_columns_resolves_transition_collision_deterministically() -> None:
    from dartlab.providers.edgar.finance.pivotPost import _calendarizePeriodColumns

    fiscal = pl.DataFrame(
        {
            "tag": ["Revenues", "NetIncomeLoss"],
            "2023-Q4": [90.0, 10.0],
            "2024-Q1": [120.0, None],
        }
    )

    calendar = _calendarizePeriodColumns(fiscal, {"2024-Q1": "2023-Q4"})

    assert calendar["2023-Q4"].to_list() == [120.0, 10.0]
