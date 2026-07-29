"""scan 계정 집계의 숫자 및 재무제표 구분 계약."""

from __future__ import annotations

import polars as pl
import pytest

from dartlab.scan.io.accounts import aggregateAccountValues, aggregateLatestAccountValues

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


def test_aggregateAccountValues_missingColumnsRaises() -> None:
    with pytest.raises(ValueError, match="필요한 컬럼"):
        aggregateAccountValues(
            pl.DataFrame({"stockCode": ["A"]}),
            ["stockCode"],
            {"revenue": ({"Revenue"}, {"매출액"}, None)},
        )


def test_aggregateLatestAccountValues_uses_company_period_and_statement() -> None:
    """회사별 연결 우선과 최신 분기를 적용하고 계정의 statement를 지킨다."""

    frame = pl.DataFrame(
        {
            "stockCode": ["A", "A", "A", "A", "B"],
            "bsns_year": ["2024", "2025", "2025", "2025", "2024"],
            "reprt_nm": ["4분기", "1분기", "4분기", "4분기", "4분기"],
            "fs_nm": ["연결재무제표", "연결재무제표", "연결재무제표", "별도재무제표", "별도재무제표"],
            "sj_div": ["IS", "IS", "IS", "IS", "IS"],
            "account_id": ["Revenue", "Revenue", "OperatingIncome", "Revenue", "Revenue"],
            "account_nm": ["매출액", "매출액", "영업이익", "매출액", "매출액"],
            "thstrm_amount": ["100", "30", "200", "999", "80"],
        }
    )
    specs = {
        "revenue": ({"Revenue"}, {"매출액"}, {"IS"}),
        "operatingIncome": ({"OperatingIncome"}, {"영업이익"}, {"IS"}),
    }

    result = aggregateLatestAccountValues(frame, specs).sort("stockCode")

    assert result["stockCode"].to_list() == ["A", "B"]
    assert result["bsns_year"].to_list() == ["2025", "2024"]
    assert result["revenue"].to_list() == [None, 80.0]
    assert result["operatingIncome"].to_list() == [200.0, None]
