"""scenarioSim native panel contract tests."""

from __future__ import annotations

import polars as pl

from dartlab.analysis.forecast.scenarioSim import (
    _quarterlyValues,
    computeSeasonality,
    quarterlyValues,
    seasonalSharesFromYearQuarters,
)


def testQuarterlyValuesResolvesNativePanelAccountLabels():
    df = pl.DataFrame(
        {
            "account": ["매출액", "매출총이익", "영업이익"],
            "label": ["매출액 (주27)", "매출총이익", "영업이익"],
            "2024Q1": ["1,000", "400", "120"],
            "2024Q2": ["2,000", "800", "240"],
            "2024Q3": ["3,000", "1,200", "360"],
            "2024Q4": ["4,000", "1,600", "480"],
        }
    )

    assert _quarterlyValues(df, "sales", "2024") == [1000.0, 2000.0, 3000.0, 4000.0]
    assert _quarterlyValues(df, "gross_profit", "2024") == [400.0, 800.0, 1200.0, 1600.0]
    assert _quarterlyValues(df, "operating_profit", "2024") == [120.0, 240.0, 360.0, 480.0]


def testQuarterlyValuesPartialYearKeepsPublishedOnly():
    """공개 verb: 미발표 분기는 키 부재 (0 채움 없음), 4개 미만도 그대로 반환."""
    df = pl.DataFrame({"account": ["매출액"], "2026Q1": ["1,000"], "2026Q2": ["2,000"]})
    assert quarterlyValues(df, "sales", "2026") == {"2026Q1": 1000.0, "2026Q2": 2000.0}
    assert quarterlyValues(df, "sales", "2025") == {}
    assert quarterlyValues(None, "sales", "2026") == {}
    # 계절성 계약: 4분기 완비 연도 없음 -> 균등 fallback
    assert computeSeasonality(df, "sales", ["2026"]) == [0.25, 0.25, 0.25, 0.25]


def testComputeSeasonalitySharesSumToOne():
    df = pl.DataFrame(
        {
            "account": ["매출액"],
            "2024Q1": ["1,000"],
            "2024Q2": ["2,000"],
            "2024Q3": ["3,000"],
            "2024Q4": ["4,000"],
        }
    )
    w = computeSeasonality(df, "sales", ["2024"])
    assert abs(sum(w) - 1.0) < 1e-9
    assert w == [0.1, 0.2, 0.3, 0.4]


def testSeasonalSharesCoreSkipsIncompleteYearsAndAveragesAbs():
    # 미완비 연도(3개) 제외 · 음수 분기는 절대값 비중 · 2개년 평균
    byYear = {
        "2023": [1.0, 1.0, 1.0, 1.0],
        "2024": [-2.0, 2.0, 2.0, 2.0],
        "2025": [5.0, 5.0, 5.0],
    }
    w = seasonalSharesFromYearQuarters(byYear)
    assert w == [0.25, 0.25, 0.25, 0.25]
    assert seasonalSharesFromYearQuarters({}) == [0.25, 0.25, 0.25, 0.25]
    assert seasonalSharesFromYearQuarters({"2024": [1.0, 2.0, 3.0, 4.0]}) == [0.1, 0.2, 0.3, 0.4]
