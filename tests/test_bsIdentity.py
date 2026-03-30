"""BS 항등식 검증 — total_assets ≈ total_liabilities + total_stockholders_equity.

fixture parquet 기반 — Company 전체 로드 없이 buildAnnual로 검증.
허용 오차: 1% (비지배지분 등의 차이 허용).
"""

import pytest

from tests.fixtureHelper import availableFixtureStocks, buildAnnualFromFixture

pytestmark = pytest.mark.integration

BENCHMARK_STOCKS = [
    "005930",
    "005380",
    "055550",
    "035720",
    "000660",
    "006400",
    "207940",
    "003550",
    "017670",
    "034730",
]


def _availableStocks():
    available = set(availableFixtureStocks("finance"))
    return [code for code in BENCHMARK_STOCKS if code in available]


_stocks = _availableStocks()

requires_bs = pytest.mark.skipif(
    len(_stocks) == 0,
    reason="BS 항등식 검증 종목 fixture 없음",
)


@requires_bs
class TestBSIdentity:
    def test_bs_identity_annual(self):
        """연간 BS: assets ≈ liabilities + equity (오차 1% 이내)."""
        violations = []
        for code in _stocks:
            result = buildAnnualFromFixture(code)
            if result is None:
                continue
            series, periods = result
            bs = series.get("BS", {})
            assets = bs.get("total_assets", [])
            liabilities = bs.get("total_liabilities", [])
            equity = bs.get("total_stockholders_equity", [])

            if not assets or not liabilities or not equity:
                continue

            for i, period in enumerate(periods):
                if i >= len(assets) or i >= len(liabilities) or i >= len(equity):
                    break
                a = assets[i]
                l = liabilities[i]
                e = equity[i]
                if a is None or l is None or e is None:
                    continue
                if a == 0:
                    continue

                diff = abs(a - (l + e))
                pct = diff / abs(a) * 100

                if pct > 1.0:
                    violations.append(f"{code} {period}: assets={a:,.0f}, liab+eq={l + e:,.0f}, diff={pct:.2f}%")

        if violations:
            msg = f"BS 항등식 위반 {len(violations)}건:\n"
            msg += "\n".join(violations[:10])
            if len(violations) > 10:
                msg += f"\n... 외 {len(violations) - 10}건"
            pytest.fail(msg)

    def test_bs_identity_pass_rate(self):
        """BS 항등식 통과율 ≥ 95%."""
        total = 0
        passed = 0
        for code in _stocks:
            result = buildAnnualFromFixture(code)
            if result is None:
                continue
            series, periods = result
            bs = series.get("BS", {})
            assets = bs.get("total_assets", [])
            liabilities = bs.get("total_liabilities", [])
            equity = bs.get("total_stockholders_equity", [])

            if not assets or not liabilities or not equity:
                continue

            for i in range(min(len(assets), len(liabilities), len(equity))):
                a, l, e = assets[i], liabilities[i], equity[i]
                if a is None or l is None or e is None:
                    continue
                if a == 0:
                    continue
                total += 1
                diff = abs(a - (l + e))
                pct = diff / abs(a) * 100
                if pct <= 1.0:
                    passed += 1

        assert total > 0, "BS 항등식 검증할 데이터 없음"
        rate = passed / total * 100
        assert rate >= 95, f"BS 항등식 통과율 {rate:.1f}% < 95% ({passed}/{total})"

    def test_assets_equals_liabilities_and_equity(self):
        """total_liabilities_and_equity가 있으면 total_assets와 정확히 일치해야 함."""
        for code in _stocks:
            result = buildAnnualFromFixture(code)
            if result is None:
                continue
            series, _ = result
            bs = series.get("BS", {})
            assets = bs.get("total_assets", [])
            lae = bs.get("total_liabilities_and_equity", [])

            if not assets or not lae:
                continue

            for a, le in zip(assets, lae):
                if a is not None and le is not None and a != 0:
                    diffPct = abs(a - le) / abs(a) * 100
                    assert diffPct < 0.01, f"{code}: total_assets({a:,.0f}) != total_liabilities_and_equity({le:,.0f})"
