"""매핑 벤치마크 — 핵심 계정이 다양한 섹터 종목에서 매핑되는지 검증.

fixture parquet 기반 — Company 전체 로드 없이 buildAnnual로 검증.
18개 핵심 계정 x N개 종목으로 매핑 커버리지를 측정한다.
금융업은 IS 일부 계정(sales, cost_of_sales, gross_profit)이 없을 수 있으므로 별도 처리.
"""

import pytest

from tests.fixtureHelper import availableFixtureStocks, buildAnnualFromFixture

pytestmark = pytest.mark.integration

CORE_ACCOUNTS = {
    "IS": [
        "sales",
        "cost_of_sales",
        "gross_profit",
        "operating_profit",
        "net_profit",
    ],
    "BS": [
        "total_assets",
        "current_assets",
        "noncurrent_assets",
        "total_liabilities",
        "current_liabilities",
        "noncurrent_liabilities",
        "total_stockholders_equity",
        "retained_earnings",
        "cash_and_cash_equivalents",
        "inventories",
    ],
    "CF": [
        "operating_cashflow",
        "investing_cashflow",
        "financing_cashflow",
    ],
}

FINANCIAL_SECTOR_EXEMPT_IS = {"sales", "cost_of_sales", "gross_profit"}
FINANCIAL_SECTOR_EXEMPT_BS = {
    "current_assets",
    "noncurrent_assets",
    "current_liabilities",
    "noncurrent_liabilities",
    "inventories",
}

BENCHMARK_STOCKS = [
    ("005930", "삼성전자", "IT"),
    ("005380", "현대자동차", "경기관련소비재"),
    ("055550", "신한지주", "금융"),
    ("035720", "카카오", "커뮤니케이션"),
    ("000660", "SK하이닉스", "IT"),
    ("006400", "삼성SDI", "소재"),
    ("207940", "삼성바이오로직스", "건강관리"),
    ("003550", "LG", "산업재"),
    ("017670", "SK텔레콤", "커뮤니케이션"),
    ("034730", "SK", "산업재"),
]


def _availableStocks():
    available = set(availableFixtureStocks("finance"))
    return [(code, name, sector) for code, name, sector in BENCHMARK_STOCKS if code in available]


def _isExempt(sector: str, stmt: str, acc: str) -> bool:
    """금융업에서 면제되는 계정인지 판별."""
    if sector != "금융":
        return False
    if stmt == "IS" and acc in FINANCIAL_SECTOR_EXEMPT_IS:
        return True
    if stmt == "BS" and acc in FINANCIAL_SECTOR_EXEMPT_BS:
        return True
    return False


@pytest.fixture(scope="module")
def benchmarkResults():
    """전 종목 매핑 결과 수집 (fixture 기반)."""
    stocks = _availableStocks()
    if not stocks:
        pytest.skip("finance fixture가 있는 벤치마크 종목 없음")

    results = {}
    for code, name, sector in stocks:
        annual = buildAnnualFromFixture(code)
        if annual is None or annual[0] is None:
            continue
        series, periods = annual
        hits = {}
        for stmt, accounts in CORE_ACCOUNTS.items():
            for acc in accounts:
                vals = series.get(stmt, {}).get(acc, [])
                nonNull = [v for v in vals if v is not None]
                hits[(stmt, acc)] = len(nonNull) > 0
        results[code] = {
            "name": name,
            "sector": sector,
            "hits": hits,
            "periods": periods,
        }
    return results


_stocks = _availableStocks()

requiresBenchmark = pytest.mark.skipif(
    len(_stocks) == 0,
    reason="벤치마크 종목 finance fixture 없음",
)


@requiresBenchmark
class TestMappingCoverage:
    def test_overall_coverage(self, benchmarkResults):
        """전체 매핑 커버리지 >= 80% (금융업 면제 계정 제외)."""
        total = 0
        mapped = 0
        for code, info in benchmarkResults.items():
            for (stmt, acc), hit in info["hits"].items():
                if _isExempt(info["sector"], stmt, acc):
                    continue
                total += 1
                if hit:
                    mapped += 1
        coverage = mapped / total * 100 if total > 0 else 0
        assert coverage >= 80, f"전체 매핑 커버리지 {coverage:.1f}% < 80% ({mapped}/{total})"

    def test_per_stock_coverage(self, benchmarkResults):
        """각 종목별 매핑 커버리지 >= 60% (금융업 면제 반영)."""
        for code, info in benchmarkResults.items():
            hits = info["hits"]
            applicable = {k: v for k, v in hits.items() if not _isExempt(info["sector"], k[0], k[1])}
            total = len(applicable)
            mapped = sum(1 for h in applicable.values() if h)
            coverage = mapped / total * 100 if total > 0 else 0
            assert coverage >= 60, (
                f"{info['name']}({code}) 매핑 커버리지 {coverage:.1f}% < 60% "
                f"— 미매핑: {[k for k, v in applicable.items() if not v]}"
            )

    def test_revenue_mapped_nonfin(self, benchmarkResults):
        """sales(매출)은 비금융 종목에서 매핑되어야 함."""
        for code, info in benchmarkResults.items():
            if info["sector"] == "금융":
                continue
            assert info["hits"].get(("IS", "sales")), f"{info['name']}({code}): sales 미매핑"

    def test_total_assets_always_mapped(self, benchmarkResults):
        """total_assets는 모든 종목에서 매핑되어야 함."""
        for code, info in benchmarkResults.items():
            assert info["hits"].get(("BS", "total_assets")), f"{info['name']}({code}): total_assets 미매핑"

    def test_total_equity_always_mapped(self, benchmarkResults):
        """total_stockholders_equity는 모든 종목에서 매핑되어야 함."""
        for code, info in benchmarkResults.items():
            assert info["hits"].get(("BS", "total_stockholders_equity")), (
                f"{info['name']}({code}): total_stockholders_equity 미매핑"
            )

    def test_total_liabilities_always_mapped(self, benchmarkResults):
        """total_liabilities는 모든 종목에서 매핑되어야 함."""
        for code, info in benchmarkResults.items():
            assert info["hits"].get(("BS", "total_liabilities")), f"{info['name']}({code}): total_liabilities 미매핑"

    def test_operating_cashflow_always_mapped(self, benchmarkResults):
        """영업활동현금흐름은 모든 종목에서 매핑되어야 함."""
        for code, info in benchmarkResults.items():
            assert info["hits"].get(("CF", "operating_cashflow")), f"{info['name']}({code}): operating_cashflow 미매핑"

    def test_has_multiple_periods(self, benchmarkResults):
        """각 종목의 시계열이 2개 이상 기간을 포함."""
        for code, info in benchmarkResults.items():
            assert len(info["periods"]) >= 2, f"{info['name']}({code}): 기간 {len(info['periods'])}개 (최소 2 필요)"


@requiresBenchmark
class TestMappingConsistency:
    def test_is_operating_profit_consistent(self, benchmarkResults):
        """operating_profit이 전 종목에서 매핑."""
        mapped = sum(1 for info in benchmarkResults.values() if info["hits"].get(("IS", "operating_profit")))
        total = len(benchmarkResults)
        assert mapped >= total * 0.9, f"IS.operating_profit: {mapped}/{total} 종목에서만 매핑"

    def test_bs_universal_accounts(self, benchmarkResults):
        """BS 보편 계정(자산/부채/자본)이 전 종목에서 매핑."""
        universal = ["total_assets", "total_liabilities", "total_stockholders_equity"]
        for acc in universal:
            mapped = sum(1 for info in benchmarkResults.values() if info["hits"].get(("BS", acc)))
            total = len(benchmarkResults)
            assert mapped == total, f"BS.{acc}: {mapped}/{total} 종목에서만 매핑 (100% 필요)"

    def test_cf_accounts_consistent(self, benchmarkResults):
        """CF 핵심 계정이 전 종목 70%+ 에서 매핑."""
        for acc in CORE_ACCOUNTS["CF"]:
            mapped = sum(1 for info in benchmarkResults.values() if info["hits"].get(("CF", acc)))
            total = len(benchmarkResults)
            assert mapped >= total * 0.7, f"CF.{acc}: {mapped}/{total} 종목에서만 매핑 (70% 필요)"


@requiresBenchmark
class TestFinancialValues:
    """매핑된 값이 재무적으로 합리적인지 검증."""

    def test_total_assets_positive(self, benchmarkResults):
        """자산총계는 항상 양수."""
        for code, info in benchmarkResults.items():
            result = buildAnnualFromFixture(code)
            if result is None:
                continue
            series, _ = result
            vals = series.get("BS", {}).get("total_assets", [])
            for v in vals:
                if v is not None:
                    assert v > 0, f"{info['name']}({code}): total_assets={v} <= 0"

    def test_equity_less_than_assets(self, benchmarkResults):
        """자본총계가 자산총계보다 작거나 같아야 함."""
        for code, info in benchmarkResults.items():
            result = buildAnnualFromFixture(code)
            if result is None:
                continue
            series, _ = result
            assets = series.get("BS", {}).get("total_assets", [])
            equity = series.get("BS", {}).get("total_stockholders_equity", [])
            if not assets or not equity:
                continue
            for a, e in zip(assets, equity):
                if a is not None and e is not None:
                    assert e <= a * 1.01, f"{info['name']}({code}): equity({e:,.0f}) > assets({a:,.0f})"

    def test_operating_cashflow_exists(self, benchmarkResults):
        """영업현금흐름이 값을 가지는지."""
        for code, info in benchmarkResults.items():
            result = buildAnnualFromFixture(code)
            if result is None:
                continue
            series, _ = result
            vals = series.get("CF", {}).get("operating_cashflow", [])
            nonNull = [v for v in vals if v is not None]
            assert len(nonNull) > 0, f"{info['name']}({code}): operating_cashflow 값 없음"
