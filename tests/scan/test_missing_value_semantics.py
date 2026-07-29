"""L1.5 scan 결측 의미 회귀.

계정이 없다는 사실을 0으로 바꾸면 당좌비율, CCC, FCF와 등급이 실제보다
좋거나 나쁜 숫자로 확정된다. KR과 EDGAR 축이 같은 결측 계약을 지키는지 검사한다.
"""

from __future__ import annotations

import polars as pl

from dartlab.scan.financial.cashflow import _classifyPattern
from dartlab.scan.financial.growth import _classifyPattern as _classifyGrowthPattern
from dartlab.scan.financial.growth import _gradeGrowth
from dartlab.scan.financial.profitability import _gradeProfitability


def _edgarFrame(**values: float | None) -> pl.DataFrame:
    frame = pl.DataFrame({"stockCode": ["TEST"], "corpName": ["Test Corp"]})
    numeric = [pl.Series(key, [value], dtype=pl.Float64) for key, value in values.items()]
    return frame.hstack(numeric)


def test_kr_grades_do_not_turn_missing_metrics_into_losses() -> None:
    assert _gradeGrowth(None, None) == "자료부족"
    assert _gradeProfitability(None, None) == "자료부족"
    assert _classifyGrowthPattern(None, -20.0, None) == "자료부족"


def test_kr_cashflow_pattern_requires_all_three_cashflow_directions() -> None:
    assert _classifyPattern(100.0, None, None) == "자료부족"
    assert _classifyPattern(100.0, 0.0, 0.0) == "현금축적형"


def test_edgar_liquidity_does_not_assume_missing_inventory_is_zero(monkeypatch) -> None:
    import dartlab.scan.builders.edgar.scan as scan

    frame = _edgarFrame(current_assets=200.0, current_liabilities=100.0, inventories=None)
    monkeypatch.setattr(scan, "scanEdgarAccounts", lambda _accounts: frame)

    row = scan._scanLiquidity().row(0, named=True)

    assert row["currentRatio"] == 200.0
    assert row["quickRatio"] is None
    assert row["grade"] == "우수"


def test_edgar_efficiency_does_not_make_zero_day_ccc_from_missing_accounts(monkeypatch) -> None:
    import dartlab.scan.builders.edgar.scan as scan

    frame = _edgarFrame(
        sales=100.0,
        total_assets=None,
        inventories=None,
        trade_and_other_receivables=None,
        trade_and_other_payables=None,
    )
    monkeypatch.setattr(scan, "scanEdgarAccounts", lambda _accounts: frame)

    row = scan._scanEfficiency().row(0, named=True)

    assert row["ccc"] is None
    assert row["grade"] == "자료부족"


def test_edgar_cashflow_does_not_make_fcf_from_missing_capex(monkeypatch) -> None:
    import dartlab.scan.builders.edgar.scan as scan

    frame = _edgarFrame(
        operating_cashflow=100.0,
        investing_cashflow=None,
        financing_cash_flow=None,
        capex=None,
        sales=500.0,
    )
    monkeypatch.setattr(scan, "scanEdgarAccounts", lambda _accounts: frame)

    row = scan._scanCashflow().row(0, named=True)

    assert row["fcf"] is None
    assert row["pattern"] == "자료부족"


def test_edgar_debt_does_not_grade_a_missing_row_as_high_risk(monkeypatch) -> None:
    import dartlab.scan.builders.edgar.scan as scan

    frame = _edgarFrame(
        total_liabilities=None,
        total_stockholders_equity=None,
        shortterm_borrowings=None,
        longterm_borrowings=None,
        operating_profit=None,
        interest_expense=None,
    )
    monkeypatch.setattr(scan, "scanEdgarAccounts", lambda _accounts: frame)

    row = scan._scanDebt().row(0, named=True)

    assert row["debtRatio"] is None
    assert row["shortTermRatio"] is None
    assert row["riskLevel"] == "자료부족"


def test_edgar_debt_keeps_known_zero_borrowing_distinct_from_missing(monkeypatch) -> None:
    import dartlab.scan.builders.edgar.scan as scan

    frame = _edgarFrame(
        total_liabilities=50.0,
        total_stockholders_equity=100.0,
        shortterm_borrowings=0.0,
        longterm_borrowings=0.0,
        operating_profit=10.0,
        interest_expense=0.0,
    )
    monkeypatch.setattr(scan, "scanEdgarAccounts", lambda _accounts: frame)

    row = scan._scanDebt().row(0, named=True)

    assert row["debtRatio"] == 50.0
    assert row["shortTermRatio"] == 0.0
    assert row["icr"] is None
    assert row["riskLevel"] == "안전"


def test_edgar_valuation_does_not_make_zero_ebitda_from_missing_inputs(monkeypatch) -> None:
    import dartlab.scan.builders.edgar.scan as scan

    frame = _edgarFrame(
        net_profit=None,
        total_stockholders_equity=None,
        total_assets=None,
        total_liabilities=None,
        cash_and_cash_equivalents=None,
        operating_profit=None,
        depreciation_amortization=None,
    )
    monkeypatch.setattr(scan, "scanEdgarAccounts", lambda _accounts: frame)

    row = scan._scanValuation().row(0, named=True)

    assert row["ebitda"] is None


def test_edgar_dividend_does_not_call_missing_data_no_dividend(monkeypatch) -> None:
    import dartlab.scan.builders.edgar.scan as scan

    frame = _edgarFrame(dividends_paid=None, net_profit=None)
    monkeypatch.setattr(scan, "scanEdgarAccounts", lambda _accounts: frame)

    row = scan._scanDividendTrend().row(0, named=True)

    assert row["dividendAmount"] is None
    assert row["grade"] == "자료부족"


def test_edgar_capital_does_not_call_missing_data_neutral(monkeypatch) -> None:
    import dartlab.scan.builders.edgar.scan as scan

    frame = _edgarFrame(dividends_paid=None, net_profit=None, treasury_stock=None)
    monkeypatch.setattr(scan, "scanEdgarAccounts", lambda _accounts: frame)

    row = scan._scanCapital().row(0, named=True)

    assert row["classification"] == "자료부족"
