"""providers/dart/finance/sourcePriority.py 계약 검증."""

import polars as pl
import pytest

from dartlab.providers.dart.finance.sourcePriority import applyCfsPriority

pytestmark = pytest.mark.unit


def test_cfs_priority_falls_back_when_ofs_strictly_dominates_coverage(caplog) -> None:
    """한 줄짜리 불완전 CFS가 더 완전한 OFS 시트 전체를 가리지 않는다."""
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

    selected = applyCfsPriority(raw, "CFS")

    assert selected["fs_div"].unique().to_list() == ["OFS"]
    assert set(selected["account_nm"].to_list()) == {"매출액", "영업이익"}
    assert "finance source fallback" in caplog.text


def test_cfs_priority_keeps_preference_when_coverages_differ_without_dominance() -> None:
    """양쪽 계정 구성이 다르면 행 수만으로 source를 바꾸지 않는다."""
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

    selected = applyCfsPriority(raw, "CFS")

    assert selected["fs_div"].unique().to_list() == ["CFS"]
    assert selected["account_nm"].to_list() == ["매출액"]
