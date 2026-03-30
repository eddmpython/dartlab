"""회귀 테스트 — 매핑/피벗 변경 후 핵심 재무 값이 후퇴하지 않는지 검증.

fixture parquet 기반 — Company 전체 로드 없이 buildAnnual로 검증.
삼성전자 2023년 연간 데이터를 golden value로 사용한다.
매핑 로직 변경 시 이 테스트가 깨지면 의도적 변경인지 확인 필요.
"""

import pytest

from tests.fixtureHelper import buildAnnualFromFixture, hasFixture

pytestmark = pytest.mark.integration

SAMSUNG = "005930"

requiresSamsungFixture = pytest.mark.skipif(
    not hasFixture(SAMSUNG, "finance"),
    reason="삼성전자 finance fixture 없음",
)

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
    """연도별 값 추출."""
    if year not in periods:
        return None
    idx = periods.index(year)
    vals = series.get(stmt, {}).get(snakeId, [])
    if idx < len(vals):
        return vals[idx]
    return None


@requiresSamsungFixture
class TestRegressionSamsung:
    @pytest.fixture(scope="class")
    def samsungAnnual(self):
        return buildAnnualFromFixture(SAMSUNG)

    def test_golden_year_exists(self, samsungAnnual):
        """golden year가 periods에 포함."""
        _, periods = samsungAnnual
        assert GOLDEN_YEAR in periods, f"{GOLDEN_YEAR}이 periods에 없음: {periods}"

    def test_bs_golden_values(self, samsungAnnual):
        """BS golden values가 오차 1% 이내."""
        series, periods = samsungAnnual
        for snakeId, expected in GOLDEN_BS.items():
            actual = _getAnnualValue(series, periods, "BS", snakeId, GOLDEN_YEAR)
            assert actual is not None, f"BS.{snakeId} {GOLDEN_YEAR} 값 없음"
            diffPct = abs(actual - expected) / abs(expected) * 100
            assert diffPct <= TOLERANCE_PCT, (
                f"BS.{snakeId} {GOLDEN_YEAR}: expected={expected:,.0f}, actual={actual:,.0f}, diff={diffPct:.2f}%"
            )

    def test_is_golden_values(self, samsungAnnual):
        """IS golden values가 오차 1% 이내."""
        series, periods = samsungAnnual
        for snakeId, expected in GOLDEN_IS.items():
            actual = _getAnnualValue(series, periods, "IS", snakeId, GOLDEN_YEAR)
            assert actual is not None, f"IS.{snakeId} {GOLDEN_YEAR} 값 없음"
            diffPct = abs(actual - expected) / abs(expected) * 100
            assert diffPct <= TOLERANCE_PCT, (
                f"IS.{snakeId} {GOLDEN_YEAR}: expected={expected:,.0f}, actual={actual:,.0f}, diff={diffPct:.2f}%"
            )

    def test_bs_identity_golden(self, samsungAnnual):
        """golden year BS 항등식."""
        series, periods = samsungAnnual
        a = _getAnnualValue(series, periods, "BS", "total_assets", GOLDEN_YEAR)
        l = _getAnnualValue(series, periods, "BS", "total_liabilities", GOLDEN_YEAR)
        e = _getAnnualValue(series, periods, "BS", "total_stockholders_equity", GOLDEN_YEAR)
        assert a is not None and l is not None and e is not None
        diffPct = abs(a - (l + e)) / abs(a) * 100
        assert diffPct <= 0.5, f"BS 항등식 실패: assets={a:,.0f}, liab+eq={l + e:,.0f}, diff={diffPct:.2f}%"

    def test_periods_count(self, samsungAnnual):
        """삼성전자 시계열이 3년 이상 (fixture 기준)."""
        _, periods = samsungAnnual
        assert len(periods) >= 3, f"기간 수 {len(periods)} < 3"

    def test_operating_cashflow_exists(self, samsungAnnual):
        """삼성전자 영업현금흐름이 golden year에 값 존재."""
        series, periods = samsungAnnual
        val = _getAnnualValue(series, periods, "CF", "operating_cashflow", GOLDEN_YEAR)
        assert val is not None, "CF.operating_cashflow 2023 값 없음"
        assert val > 0, f"CF.operating_cashflow 2023 = {val:,.0f} (양수 기대)"
