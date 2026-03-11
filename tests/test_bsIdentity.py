"""BS 항등식 검증 — total_assets ≈ total_liabilities + total_stockholders_equity.

전 벤치마크 종목에서 재무상태표 항등식이 성립하는지 검증한다.
허용 오차: 1% (비지배지분 등의 차이 허용).
"""

import pytest

from tests.conftest import _has_data

BENCHMARK_STOCKS = [
    "005930", "005380", "055550", "035720", "000660",
    "006400", "207940", "003550", "017670", "034730",
]


def _available_stocks():
    return [code for code in BENCHMARK_STOCKS if _has_data(code, "finance")]


requires_bs = pytest.mark.skipif(
    len(_available_stocks()) == 0,
    reason="BS 항등식 검증 종목 finance 데이터 없음",
)


@requires_bs
class TestBSIdentity:
    def test_bs_identity_annual(self):
        """연간 BS: assets ≈ liabilities + equity (오차 1% 이내)."""
        from dartlab import Company

        violations = []
        for code in _available_stocks():
            c = Company(code)
            annual = getattr(c, "annual", None)
            if annual is None:
                continue
            series, periods = annual
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
                    violations.append(
                        f"{code} {period}: "
                        f"assets={a:,.0f}, liab+eq={l + e:,.0f}, "
                        f"diff={pct:.2f}%"
                    )

        if violations:
            msg = f"BS 항등식 위반 {len(violations)}건:\n"
            msg += "\n".join(violations[:10])
            if len(violations) > 10:
                msg += f"\n... 외 {len(violations) - 10}건"
            pytest.fail(msg)

    def test_bs_identity_pass_rate(self):
        """BS 항등식 통과율 ≥ 95%."""
        from dartlab import Company

        total = 0
        passed = 0
        for code in _available_stocks():
            c = Company(code)
            annual = getattr(c, "annual", None)
            if annual is None:
                continue
            series, periods = annual
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
        assert rate >= 95, (
            f"BS 항등식 통과율 {rate:.1f}% < 95% ({passed}/{total})"
        )

    def test_assets_equals_liabilities_and_equity(self):
        """total_liabilities_and_equity가 있으면 total_assets와 정확히 일치해야 함."""
        from dartlab import Company

        for code in _available_stocks():
            c = Company(code)
            annual = getattr(c, "annual", None)
            if annual is None:
                continue
            series, _ = annual
            bs = series.get("BS", {})
            assets = bs.get("total_assets", [])
            lae = bs.get("total_liabilities_and_equity", [])

            if not assets or not lae:
                continue

            for a, le in zip(assets, lae):
                if a is not None and le is not None and a != 0:
                    diff_pct = abs(a - le) / abs(a) * 100
                    assert diff_pct < 0.01, (
                        f"{code}: total_assets({a:,.0f}) != "
                        f"total_liabilities_and_equity({le:,.0f})"
                    )
