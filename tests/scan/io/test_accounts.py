"""scan 계정 집계의 숫자 및 재무제표 구분 계약."""

from __future__ import annotations

import polars as pl
import pytest

from dartlab.scan.io.accounts import aggregateAccountValues

pytestmark = pytest.mark.unit


def test_aggregateAccountValues_parsesAmountsAndHonorsStatementDivision() -> None:
    frame = pl.DataFrame(
        {
            "stockCode": ["A", "A", "A", "B", "B", "B"],
            "sj_div": ["BS", "IS", "IS", "IS", "IS", "IS"],
            "account_id": ["Revenue", "Revenue", "OperatingIncome", "Revenue", "Revenue", "OperatingIncome"],
            "account_nm": ["매출액", "매출액", "영업이익", "매출액", "매출액", "영업이익"],
            "thstrm_amount": ["9,999", "1,234", "△300", "-", "(2,000)", "25%"],
        }
    )

    result = aggregateAccountValues(
        frame,
        ["stockCode"],
        {
            "revenue": ({"Revenue"}, {"매출액"}, {"IS", "CIS"}),
            "operatingIncome": ({"OperatingIncome"}, {"영업이익"}, {"IS", "CIS"}),
        },
    ).sort("stockCode")

    assert result["revenue"].to_list() == [1234.0, -2000.0]
    assert result["operatingIncome"].to_list() == [-300.0, 25.0]


def test_aggregateAccountValues_missingColumnsReturnsTypedEmpty() -> None:
    result = aggregateAccountValues(
        pl.DataFrame({"stockCode": ["A"]}),
        ["stockCode"],
        {"revenue": ({"Revenue"}, {"매출액"}, None)},
    )

    assert result.is_empty()
    assert result.schema == {"stockCode": pl.String, "revenue": pl.Float64}
