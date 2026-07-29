"""providers/edgar/accessor/financeAccessor.py 공개 artifact 변환 계약."""

from types import SimpleNamespace

import polars as pl
import pytest

pytestmark = pytest.mark.unit


def test_imports():
    try:
        import dartlab.providers.edgar.accessor.financeAccessor  # noqa: F401
    except ImportError as e:
        pytest.skip(f"module import requires data/env: {e}")


def _artifact() -> pl.DataFrame:
    rows = []
    for stmt, values in {
        "IS": [10.0, 20.0, 30.0, 100.0],
        "CF": [5.0, 10.0, 15.0, 50.0],
        "BS": [100.0, 110.0, 120.0, 130.0],
    }.items():
        for index, (reportCode, value) in enumerate(zip(["11013", "11012", "11014", "11011"], values, strict=True)):
            rows.append(
                {
                    "sj_div": stmt,
                    "reprt_code": reportCode,
                    "bsns_year": "2024",
                    "thstrm_amount": value,
                    "account_id": f"{stmt}_account",
                    "account_nm": f"{stmt} 항목",
                    "ord": index,
                }
            )
    return pl.DataFrame(rows)


def test_published_flow_artifact_derives_standalone_q4(monkeypatch: pytest.MonkeyPatch) -> None:
    from dartlab.core import dataLoader
    from dartlab.providers.edgar.accessor.financeAccessor import _FinanceAccessor

    monkeypatch.setattr(dataLoader, "loadData", lambda *args, **kwargs: _artifact())
    accessor = _FinanceAccessor(SimpleNamespace(ticker="TEST", _cache={}))

    income = accessor._stmtDfFromPublishedArtifact("IS")
    cashflow = accessor._stmtDfFromPublishedArtifact("CF")

    assert income is not None and income["2024Q4"][0] == 40.0
    assert cashflow is not None and cashflow["2024Q4"][0] == 20.0


def test_published_balance_artifact_keeps_year_end_balance(monkeypatch: pytest.MonkeyPatch) -> None:
    from dartlab.core import dataLoader
    from dartlab.providers.edgar.accessor.financeAccessor import _FinanceAccessor

    monkeypatch.setattr(dataLoader, "loadData", lambda *args, **kwargs: _artifact())
    accessor = _FinanceAccessor(SimpleNamespace(ticker="TEST", _cache={}))

    balance = accessor._stmtDfFromPublishedArtifact("BS")

    assert balance is not None and balance["2024Q4"][0] == 130.0
