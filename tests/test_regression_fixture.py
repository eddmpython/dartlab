"""CI용 fixture 기반 회귀 테스트 — 삼성전자 golden value 검증.

tests/fixtures/005930.finance.parquet 사용.
로컬 데이터 불필요 — CI에서 항상 실행.

test_regressionFinance.py의 golden value를 fixture parquet + buildAnnual 조합으로
CI에서도 검증할 수 있게 복제한 테스트.
"""

from pathlib import Path
from unittest.mock import patch

import polars as pl
import pytest

pytestmark = pytest.mark.integration

FIXTURE_DIR = Path(__file__).parent / "fixtures"
FIXTURE_FINANCE = FIXTURE_DIR / "005930.finance.parquet"

GOLDEN_YEAR = "2023"

GOLDEN_BS = {
    "total_assets": 455_905_980_000_000,
    "total_liabilities": 92_228_115_000_000,
    "total_stockholders_equity": 363_677_865_000_000,
}

GOLDEN_IS = {
    "sales": 258_935_494_000_000,
    "operating_profit": 6_566_976_000_000,
}

TOLERANCE_PCT = 1.0


def _getAnnualValue(series, periods, stmt, snakeId, year):
    if year not in periods:
        return None
    idx = periods.index(year)
    vals = series.get(stmt, {}).get(snakeId, [])
    if idx < len(vals):
        return vals[idx]
    return None


@pytest.fixture(scope="module")
def samsungAnnual():
    from dartlab.providers.dart.finance.pivot import buildAnnual

    df = pl.read_parquet(FIXTURE_FINANCE)
    with patch("dartlab.core.dataLoader.loadData", return_value=df):
        result = buildAnnual("005930")

    assert result is not None, "buildAnnual returned None for fixture"
    return result


class TestRegressionFixture:
    def test_goldenYearExists(self, samsungAnnual):
        _, periods = samsungAnnual
        assert GOLDEN_YEAR in periods, f"{GOLDEN_YEAR} not in periods: {periods}"

    def test_bsGoldenValues(self, samsungAnnual):
        series, periods = samsungAnnual
        for snakeId, expected in GOLDEN_BS.items():
            actual = _getAnnualValue(series, periods, "BS", snakeId, GOLDEN_YEAR)
            assert actual is not None, f"BS.{snakeId} {GOLDEN_YEAR} is None"
            diffPct = abs(actual - expected) / abs(expected) * 100
            assert diffPct <= TOLERANCE_PCT, (
                f"BS.{snakeId} {GOLDEN_YEAR}: expected={expected:,.0f}, actual={actual:,.0f}, diff={diffPct:.2f}%"
            )

    def test_isGoldenValues(self, samsungAnnual):
        series, periods = samsungAnnual
        for snakeId, expected in GOLDEN_IS.items():
            actual = _getAnnualValue(series, periods, "IS", snakeId, GOLDEN_YEAR)
            assert actual is not None, f"IS.{snakeId} {GOLDEN_YEAR} is None"
            diffPct = abs(actual - expected) / abs(expected) * 100
            assert diffPct <= TOLERANCE_PCT, (
                f"IS.{snakeId} {GOLDEN_YEAR}: expected={expected:,.0f}, actual={actual:,.0f}, diff={diffPct:.2f}%"
            )

    def test_bsIdentity(self, samsungAnnual):
        series, periods = samsungAnnual
        a = _getAnnualValue(series, periods, "BS", "total_assets", GOLDEN_YEAR)
        liab = _getAnnualValue(series, periods, "BS", "total_liabilities", GOLDEN_YEAR)
        eq = _getAnnualValue(series, periods, "BS", "total_stockholders_equity", GOLDEN_YEAR)
        assert a is not None and liab is not None and eq is not None
        diffPct = abs(a - (liab + eq)) / abs(a) * 100
        assert diffPct <= 0.5, f"BS identity failed: assets={a:,.0f}, liab+eq={liab + eq:,.0f}, diff={diffPct:.2f}%"

    def test_periodsCount(self, samsungAnnual):
        _, periods = samsungAnnual
        assert len(periods) >= 3, f"period count {len(periods)} < 3"

    def test_operatingCashflowExists(self, samsungAnnual):
        series, periods = samsungAnnual
        val = _getAnnualValue(series, periods, "CF", "operating_cashflow", GOLDEN_YEAR)
        assert val is not None, "CF.operating_cashflow 2023 is None"
        assert val > 0, f"CF.operating_cashflow 2023 = {val:,.0f} (expected positive)"

    def test_ratiosFromAnnual(self, samsungAnnual):
        from dartlab.core.finance.ratios import calcRatios

        series, _ = samsungAnnual
        ratios = calcRatios(series, annual=True)
        assert ratios is not None
        assert ratios.roe is not None, "ROE should be calculable for Samsung"
        assert ratios.operatingMargin is not None, "Operating margin should exist"
