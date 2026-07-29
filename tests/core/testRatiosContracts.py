"""재무비율의 결측, 기간, 업종 정책 계약 회귀."""

from __future__ import annotations

import pytest

from dartlab.core.ratios import calcRatios, calcRatioSeries

pytestmark = pytest.mark.unit


def _baseAnnualSeries() -> dict[str, dict[str, list[float | None]]]:
    return {
        "IS": {
            "sales": [100.0, 100.0, 100.0, 100.0],
            "operating_profit": [20.0, 20.0, 20.0, 20.0],
            "net_profit": [10.0, 10.0, 10.0, 10.0],
            "profit_before_tax": [100.0, 100.0, 100.0, 100.0],
            "income_tax_expense": [0.0, 0.0, 0.0, 50.0],
        },
        "BS": {
            "total_assets": [200.0, 200.0, 200.0, 200.0],
            "total_liabilities": [100.0, 100.0, 100.0, 100.0],
            "total_stockholders_equity": [100.0, 100.0, 100.0, 100.0],
            "owners_of_parent_equity": [100.0, 100.0, 100.0, 100.0],
            "shortterm_borrowings": [0.0, 0.0, 0.0, 0.0],
            "longterm_borrowings": [0.0, 0.0, 0.0, 0.0],
            "debentures": [0.0, 0.0, 0.0, 0.0],
            "cash_and_cash_equivalents": [0.0, 0.0, 0.0, 0.0],
        },
        "CF": {
            "operating_cashflow": [15.0, 15.0, 15.0, 15.0],
        },
    }


def testAnnualRoicUsesLatestPeriodTaxRate() -> None:
    """연간 ROIC는 4개년 평균이 아니라 최신 기간 세율을 사용한다."""
    result = calcRatios(_baseAnnualSeries(), annual=True)

    assert result.effectiveTaxRate == 50.0
    assert result.roic == 10.0


def testExplicitZeroEquityDoesNotFallThroughToAnotherAccount() -> None:
    """명시된 0은 결측이 아니므로 대체 계정 값으로 바뀌지 않는다."""
    series = _baseAnnualSeries()
    series["BS"]["total_stockholders_equity"][-1] = 0.0
    series["BS"]["owners_of_parent_equity"][-1] = 50.0

    result = calcRatios(series, annual=True)

    assert result.totalEquity == 0.0
    assert result.ownersEquity == 50.0
    assert result.debtRatio is None


def testAllNullFinancialKeysDoNotMaskGeneralRatios() -> None:
    """값이 전혀 없는 금융업 placeholder 계정은 업종 증거가 아니다."""
    series = _baseAnnualSeries()
    series["IS"].update(
        {
            "interest_income": [None] * 4,
            "net_interest_income": [None] * 4,
        }
    )
    series["BS"].update(
        {
            "loans": [None] * 4,
            "deposits_from_customers": [None] * 4,
        }
    )

    result = calcRatios(series, annual=True)

    assert result.operatingMargin == 20.0
    assert result.currentRatio is None


def testSeriesTaxFallsBackFromAllNullPrimaryAccount() -> None:
    """주 계정이 전부 결측이면 실제 값이 있는 대체 세금 계정을 사용한다."""
    series = _baseAnnualSeries()
    series["IS"]["income_tax_expense"] = [None] * 4
    series["IS"]["income_taxes"] = [10.0, 20.0, 30.0, 40.0]

    result = calcRatioSeries(series, ["2021", "2022", "2023", "2024"], annual=True, yoyLag=1)

    assert result.effectiveTaxRate == [10.0, 20.0, 30.0, 40.0]


def testQuarterlyRatioSeriesUsesTrailingFourQuarterFlows() -> None:
    """분기 series는 최신 한 분기가 아니라 최근 네 분기 flow를 사용한다."""
    series = _baseAnnualSeries()
    for statement in series.values():
        for snakeId, values in statement.items():
            statement[snakeId] = values + values

    quarterly = calcRatioSeries(
        series, [f"202{year}Q{quarter}" for year in (3, 4) for quarter in range(1, 5)], annual=False, yoyLag=4
    )
    annual = calcRatioSeries(series, [str(year) for year in range(2017, 2025)], annual=True, yoyLag=1)

    assert quarterly.revenue[-1] == 400.0
    assert annual.revenue[-1] == 100.0


def testRatioSeriesRequiresExplicitInputGranularity() -> None:
    """호출자가 연간과 분기를 명시하지 않으면 조용히 연간으로 계산하지 않는다."""
    with pytest.raises(TypeError, match="annual"):
        calcRatioSeries(_baseAnnualSeries(), ["2024"], yoyLag=1)


@pytest.mark.parametrize("override", ["", "industrial", "unknown"])
def testInvalidArchetypeOverrideRaises(override: str) -> None:
    """알 수 없는 업종 정책은 비율을 임의로 마스킹하지 않고 거부한다."""
    with pytest.raises(ValueError, match="archetypeOverride"):
        calcRatios(_baseAnnualSeries(), annual=True, archetypeOverride=override)


@pytest.mark.parametrize("yoyLag", [0, -1, True, 1.5])
def testInvalidYoyLagRaises(yoyLag: object) -> None:
    """시계열 성장률 간격은 양의 정수여야 한다."""
    with pytest.raises(ValueError, match="yoyLag"):
        calcRatioSeries(_baseAnnualSeries(), ["2024"], annual=True, yoyLag=yoyLag)
