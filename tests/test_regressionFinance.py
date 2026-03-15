"""회귀 테스트 — 매핑/피벗 변경 후 핵심 재무 값이 후퇴하지 않는지 검증.

삼성전자 2023년 연간 데이터를 golden value로 사용한다.
매핑 로직 변경 시 이 테스트가 깨지면 의도적 변경인지 확인 필요.
"""

import pytest

from tests.conftest import SAMSUNG, _has_data

requires_samsung_finance = pytest.mark.skipif(not _has_data(SAMSUNG, "finance"), reason="삼성전자 finance 데이터 없음")

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


def _get_annual_value(series, periods, stmt, snakeId, year):
    """연도별 값 추출."""
    if year not in periods:
        return None
    idx = periods.index(year)
    vals = series.get(stmt, {}).get(snakeId, [])
    if idx < len(vals):
        return vals[idx]
    return None


@requires_samsung_finance
class TestRegressionSamsung:
    @pytest.fixture(scope="class")
    def samsung_annual(self):
        from dartlab import Company

        c = Company(SAMSUNG)
        annual = getattr(c, "annual", None)
        if annual is None:
            pytest.skip("삼성전자 annual 데이터 없음")
        return annual

    def test_golden_year_exists(self, samsung_annual):
        """golden year가 periods에 포함."""
        series, periods = samsung_annual
        assert GOLDEN_YEAR in periods, f"{GOLDEN_YEAR}이 periods에 없음: {periods}"

    def test_bs_golden_values(self, samsung_annual):
        """BS golden values가 오차 1% 이내."""
        series, periods = samsung_annual
        for snakeId, expected in GOLDEN_BS.items():
            actual = _get_annual_value(series, periods, "BS", snakeId, GOLDEN_YEAR)
            assert actual is not None, f"BS.{snakeId} {GOLDEN_YEAR} 값 없음"
            diff_pct = abs(actual - expected) / abs(expected) * 100
            assert diff_pct <= TOLERANCE_PCT, (
                f"BS.{snakeId} {GOLDEN_YEAR}: expected={expected:,.0f}, actual={actual:,.0f}, diff={diff_pct:.2f}%"
            )

    def test_is_golden_values(self, samsung_annual):
        """IS golden values가 오차 1% 이내."""
        series, periods = samsung_annual
        for snakeId, expected in GOLDEN_IS.items():
            actual = _get_annual_value(series, periods, "IS", snakeId, GOLDEN_YEAR)
            assert actual is not None, f"IS.{snakeId} {GOLDEN_YEAR} 값 없음"
            diff_pct = abs(actual - expected) / abs(expected) * 100
            assert diff_pct <= TOLERANCE_PCT, (
                f"IS.{snakeId} {GOLDEN_YEAR}: expected={expected:,.0f}, actual={actual:,.0f}, diff={diff_pct:.2f}%"
            )

    def test_bs_identity_golden(self, samsung_annual):
        """golden year BS 항등식."""
        series, periods = samsung_annual
        a = _get_annual_value(series, periods, "BS", "total_assets", GOLDEN_YEAR)
        l = _get_annual_value(series, periods, "BS", "total_liabilities", GOLDEN_YEAR)
        e = _get_annual_value(series, periods, "BS", "total_stockholders_equity", GOLDEN_YEAR)
        assert a is not None and l is not None and e is not None
        diff_pct = abs(a - (l + e)) / abs(a) * 100
        assert diff_pct <= 0.5, f"BS 항등식 실패: assets={a:,.0f}, liab+eq={l + e:,.0f}, diff={diff_pct:.2f}%"

    def test_periods_count(self, samsung_annual):
        """삼성전자 시계열이 5년 이상."""
        _, periods = samsung_annual
        assert len(periods) >= 5, f"기간 수 {len(periods)} < 5"

    def test_operating_cashflow_exists(self, samsung_annual):
        """삼성전자 영업현금흐름이 golden year에 값 존재."""
        series, periods = samsung_annual
        val = _get_annual_value(series, periods, "CF", "operating_cashflow", GOLDEN_YEAR)
        assert val is not None, "CF.operating_cashflow 2023 값 없음"
        assert val > 0, f"CF.operating_cashflow 2023 = {val:,.0f} (양수 기대)"
