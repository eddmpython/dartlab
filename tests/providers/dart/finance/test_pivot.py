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


def test_cfs_priority_falls_back_when_ofs_strictly_dominates_coverage(caplog) -> None:
    """한 줄짜리 불완전 CFS가 더 완전한 OFS 시트 전체를 가리지 않는다."""
    from dartlab.providers.dart.finance.pivot import _applyCfsPriority

    raw = pl.DataFrame(
        {
            "bsns_year": ["2024"] * 3,
            "reprt_nm": ["1분기"] * 3,
            "sj_div": ["IS"] * 3,
            "fs_div": ["CFS", "OFS", "OFS"],
            "account_id": ["ifrs-full_Revenue", "ifrs-full_Revenue", "dart_OperatingIncomeLoss"],
            "account_nm": ["매출액", "매출액", "영업이익"],
            "thstrm_amount": ["100", "90", "10"],
        }
    )

    selected = _applyCfsPriority(raw, "CFS")

    assert selected["fs_div"].unique().to_list() == ["OFS"]
    assert set(selected["account_nm"].to_list()) == {"매출액", "영업이익"}
    assert "finance source fallback" in caplog.text


def test_cfs_priority_keeps_preference_when_coverages_differ_without_dominance() -> None:
    """양쪽 계정 구성이 다르면 행 수만으로 source를 바꾸지 않는다."""
    from dartlab.providers.dart.finance.pivot import _applyCfsPriority

    raw = pl.DataFrame(
        {
            "bsns_year": ["2024"] * 3,
            "reprt_nm": ["1분기"] * 3,
            "sj_div": ["IS"] * 3,
            "fs_div": ["CFS", "OFS", "OFS"],
            "account_id": ["ifrs-full_Revenue", "dart_OperatingIncomeLoss", "ifrs-full_ProfitLoss"],
            "account_nm": ["매출액", "영업이익", "당기순이익"],
            "thstrm_amount": ["100", "10", "8"],
        }
    )

    selected = _applyCfsPriority(raw, "CFS")

    assert selected["fs_div"].unique().to_list() == ["CFS"]
    assert selected["account_nm"].to_list() == ["매출액"]


def test_annual_flow_requires_contiguous_complete_quarters() -> None:
    """연간/부분연도 flow는 필요한 분기 하나라도 빠지면 합계를 발행하지 않는다."""
    from dartlab.providers.dart.finance.pivot import _aggregateAnnual

    series = {
        "IS": {
            "complete": [10.0, 20.0, 30.0, 40.0, 5.0, 6.0],
            "accountGap": [10.0, None, 30.0, 40.0, 5.0, None],
        },
        "BS": {"assets": [100.0, 110.0, 120.0, 130.0, 140.0, 150.0]},
        "CF": {},
    }
    periods = ["2024-Q1", "2024-Q2", "2024-Q3", "2024-Q4", "2025-Q1", "2025-Q2"]

    annual, labels = _aggregateAnnual(series, periods)

    assert labels == ["2024", "2025Q2"]
    assert annual["IS"]["complete"] == [100.0, 11.0]
    assert annual["IS"]["accountGap"] == [None, None]
    assert annual["BS"]["assets"] == [130.0, 150.0]


def test_annual_flow_rejects_missing_global_quarter() -> None:
    """Q1+Q3만 존재하는 horizon은 2분기 누락을 건너뛰어 합산하지 않는다."""
    from dartlab.providers.dart.finance.pivot import _aggregateAnnual

    annual, labels = _aggregateAnnual(
        {"IS": {"sales": [10.0, 30.0]}, "BS": {}, "CF": {}},
        ["2025-Q1", "2025-Q3"],
    )

    assert labels == ["2025Q3"]
    assert annual["IS"]["sales"] == [None]


def test_cumulative_flow_requires_every_prior_quarter() -> None:
    """YTD는 Q1부터 현재 분기까지의 horizon과 계정값이 모두 완전해야 한다."""
    from dartlab.providers.dart.finance.pivot import _aggregateCumulative

    cumulative, periods = _aggregateCumulative(
        {
            "IS": {
                "complete": [10.0, 20.0, 30.0],
                "accountGap": [10.0, None, 30.0],
            },
            "BS": {"assets": [100.0, 110.0, 120.0]},
            "CF": {},
        },
        ["2025-Q1", "2025-Q2", "2025-Q3"],
    )

    assert periods == ["2025-Q1", "2025-Q2", "2025-Q3"]
    assert cumulative["IS"]["complete"] == [10.0, 30.0, 60.0]
    assert cumulative["IS"]["accountGap"] == [10.0, None, None]
    assert cumulative["BS"]["assets"] == [100.0, 110.0, 120.0]


def test_cumulative_flow_rejects_missing_global_quarter() -> None:
    """Q2가 horizon에 없으면 Q3를 Q1+Q3의 가짜 YTD로 만들지 않는다."""
    from dartlab.providers.dart.finance.pivot import _aggregateCumulative

    cumulative, _ = _aggregateCumulative(
        {"IS": {"sales": [10.0, 30.0]}, "BS": {}, "CF": {}},
        ["2025-Q1", "2025-Q3"],
    )

    assert cumulative["IS"]["sales"] == [10.0, None]


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
