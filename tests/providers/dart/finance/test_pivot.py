"""providers/dart/finance/pivot.py mirror smoke."""

import polars as pl
import pytest

pytestmark = pytest.mark.unit


def test_imports():
    try:
        import dartlab.providers.dart.finance.pivot  # noqa: F401
    except ImportError as e:
        pytest.skip(f"module import requires data/env: {e}")


def test_build_annual_callable() -> None:
    """buildAnnual() callable smoke."""
    from dartlab.providers.dart.finance.pivot import buildAnnual

    assert callable(buildAnnual)


def test_build_cumulative_callable() -> None:
    """buildCumulative() callable smoke."""
    from dartlab.providers.dart.finance.pivot import buildCumulative

    assert callable(buildCumulative)


def test_build_sce_annual_callable() -> None:
    """buildSceAnnual() callable smoke."""
    from dartlab.providers.dart.finance.pivot import buildSceAnnual

    assert callable(buildSceAnnual)


def test_build_sce_matrix_callable() -> None:
    """buildSceMatrix() callable smoke."""
    from dartlab.providers.dart.finance.pivot import buildSceMatrix

    assert callable(buildSceMatrix)


def test_build_timeseries_callable() -> None:
    """buildTimeseries() callable smoke."""
    from dartlab.providers.dart.finance.pivot import buildTimeseries

    assert callable(buildTimeseries)


def test_clear_finance_cache_callable() -> None:
    """clearFinanceCache() callable smoke."""
    from dartlab.providers.dart.finance.pivot import clearFinanceCache

    assert callable(clearFinanceCache)


def test_normalize_quarter_requires_immediately_previous_quarter() -> None:
    """Q2가 없으면 Q3 누적값에서 Q1을 빼서 가짜 standalone을 만들지 않는다."""
    from dartlab.providers.dart.finance.pivot import _normalizeQ4

    raw = pl.DataFrame(
        {
            "bsns_year": ["2024", "2024"],
            "sj_div": ["IS", "IS"],
            "account_id": ["ifrs-full_Revenue", "ifrs-full_Revenue"],
            "reprt_nm": ["1분기", "3분기"],
            "thstrm_amount": ["100", "330"],
            "thstrm_add_amount": ["100", "330"],
        }
    )

    normalized = _normalizeQ4(raw)
    values = dict(zip(normalized["reprt_nm"].to_list(), normalized["_normalized_amount"].to_list(), strict=True))

    assert values == {"1분기": 100.0, "3분기": None}


def test_normalize_quarter_uses_immediately_previous_quarter() -> None:
    """Q1과 Q2가 연속하면 Q2 누적값을 정상 차감한다."""
    from dartlab.providers.dart.finance.pivot import _normalizeQ4

    raw = pl.DataFrame(
        {
            "bsns_year": ["2024", "2024"],
            "sj_div": ["IS", "IS"],
            "account_id": ["ifrs-full_Revenue", "ifrs-full_Revenue"],
            "reprt_nm": ["1분기", "2분기"],
            "thstrm_amount": ["100", "250"],
            "thstrm_add_amount": ["100", "250"],
        }
    )

    normalized = _normalizeQ4(raw)
    values = dict(zip(normalized["reprt_nm"].to_list(), normalized["_normalized_amount"].to_list(), strict=True))

    assert values == {"1분기": 100.0, "2분기": 150.0}


def test_normalize_quarter_isolates_nonstandard_accounts_with_shared_placeholder_id() -> None:
    """같은 placeholder ID를 쓰는 사내계정끼리 누적 차감값이 섞이지 않는다."""
    from dartlab.providers.dart.finance.pivot import _normalizeQ4

    raw = pl.DataFrame(
        {
            "bsns_year": ["2024"] * 4,
            "sj_div": ["IS"] * 4,
            "account_id": ["-표준계정코드 미사용-"] * 4,
            "account_nm": ["제품매출", "용역매출", "제품매출", "용역매출"],
            "account_detail": ["국내", "국내", "국내", "국내"],
            "reprt_nm": ["1분기", "1분기", "2분기", "2분기"],
            "thstrm_amount": ["100", "40", "260", "90"],
            "thstrm_add_amount": ["100", "40", "260", "90"],
        }
    )

    normalized = _normalizeQ4(raw)
    q2 = normalized.filter(pl.col("reprt_nm") == "2분기").sort("account_nm")

    assert dict(zip(q2["account_nm"].to_list(), q2["_normalized_amount"].to_list(), strict=True)) == {
        "용역매출": 50.0,
        "제품매출": 160.0,
    }
