"""복합 재무 점수의 입력 완전성 계약 회귀 테스트."""

from copy import deepcopy

import pytest

from dartlab.core.ratios import calcRatios, calcRatioSeries

pytestmark = pytest.mark.unit


_COMPLETE_SERIES = {
    "IS": {
        "sales": [80.0, 90.0, 100.0],
        "operating_profit": [12.0, 15.0, 18.0],
        "net_profit": [7.0, 9.0, 12.0],
        "gross_profit": [30.0, 35.0, 41.0],
        "profit_before_tax": [9.0, 12.0, 15.0],
    },
    "BS": {
        "total_assets": [150.0, 170.0, 190.0],
        "total_liabilities": [80.0, 82.0, 84.0],
        "total_stockholders_equity": [70.0, 88.0, 106.0],
        "current_assets": [50.0, 58.0, 67.0],
        "current_liabilities": [35.0, 37.0, 39.0],
        "retained_earnings": [30.0, 38.0, 48.0],
        "issued_capital": [10.0, 10.0, 10.0],
        "longterm_borrowings": [20.0, 18.0, 16.0],
        "debentures": [5.0, 5.0, 5.0],
    },
    "CF": {
        "operating_cashflow": [10.0, 13.0, 16.0],
    },
}


_COMPOSITE_FIELDS = (
    "piotroskiFScore",
    "altmanZScore",
    "altmanZppScore",
    "springateSScore",
    "zmijewskiXScore",
)


def test_complete_inputs_produce_composite_scores():
    result = calcRatios(_COMPLETE_SERIES, annual=True)

    assert all(getattr(result, field) is not None for field in _COMPOSITE_FIELDS)


def test_missing_income_does_not_become_zero_valued_composite_inputs():
    sparse = {
        "IS": {},
        "BS": {
            "total_assets": [100.0, 110.0],
            "total_liabilities": [60.0, 65.0],
            "total_stockholders_equity": [40.0, 45.0],
            "current_assets": [40.0, 45.0],
            "current_liabilities": [20.0, 22.0],
            "retained_earnings": [10.0, 12.0],
        },
        "CF": {},
    }

    result = calcRatios(sparse, annual=True)

    assert all(getattr(result, field) is None for field in _COMPOSITE_FIELDS)


def test_each_required_signal_is_present_before_publishing_score():
    missingOperatingCashflow = deepcopy(_COMPLETE_SERIES)
    missingOperatingCashflow["CF"].pop("operating_cashflow")
    result = calcRatios(missingOperatingCashflow, annual=True)

    assert result.piotroskiFScore is None
    assert result.altmanZScore is not None


def test_ratio_series_keeps_incomplete_scores_as_none():
    incomplete = deepcopy(_COMPLETE_SERIES)
    incomplete["BS"].pop("current_assets")
    years = ["2022", "2023", "2024"]

    result = calcRatioSeries(incomplete, years, yoyLag=1)

    assert result.piotroskiFScore == [None, None, None]
    assert result.altmanZScore == [None, None, None]


def test_ratio_series_publishes_score_only_after_comparison_period_exists():
    result = calcRatioSeries(_COMPLETE_SERIES, ["2022", "2023", "2024"], yoyLag=1)

    assert result.piotroskiFScore[0] is None
    assert all(score is not None for score in result.piotroskiFScore[1:])
    assert all(score is not None for score in result.altmanZScore)
