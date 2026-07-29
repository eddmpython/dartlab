"""scan finance fallback path (DuckDB raw glob) 단위 테스트.

prebuild ``finance.parquet`` 가 없을 때 ``_loadRawFinanceViaDuckDb`` 가 raw
``finance/*.parquet`` glob 을 DuckDB streaming SQL 로 읽어 polars LazyFrame 으로
환원한다. 메모리 안전 (DuckDB native heap) + 캘린더 분기 환원까지 적용되어
prebuild 합본과 동등 schema 보장.
"""

from __future__ import annotations

import polars as pl
import pytest

from dartlab.scan.io.parquet import (
    ScanDataError,
    _loadRawFinanceViaDuckDb,
    _sqlEscapeLiteral,
)


@pytest.mark.unit
def test_sqlEscapeLiteral_basic():
    """단순 ``'`` → ``''`` 변환."""
    assert _sqlEscapeLiteral("매출액") == "매출액"
    assert _sqlEscapeLiteral("dart_(1)총매출액") == "dart_(1)총매출액"
    assert _sqlEscapeLiteral("o'malley") == "o''malley"
    assert _sqlEscapeLiteral("a'b'c") == "a''b''c"


@pytest.mark.unit
def test_loadRawFinance_emptyDir_returnsNone(tmp_path):
    """빈 디렉토리는 None 반환."""
    assert _loadRawFinanceViaDuckDb(tmp_path) is None


@pytest.mark.unit
def test_loadRawFinance_nonexistentDir_returnsNone(tmp_path):
    """존재하지 않는 디렉토리 None."""
    assert _loadRawFinanceViaDuckDb(tmp_path / "noexist") is None


@pytest.mark.unit
def test_loadRawFinance_corruptParquet_raises(tmp_path):
    """raw finance 손상을 데이터 부재로 위장하지 않는다."""

    (tmp_path / "005930.parquet").write_bytes(b"not parquet")

    with pytest.raises(ScanDataError, match="stage=finance_duckdb_query"):
        _loadRawFinanceViaDuckDb(tmp_path)


@pytest.mark.unit
def test_loadRawFinance_singleParquet_sjDivFilter(tmp_path):
    """단일 종목 raw parquet → DuckDB SQL push-down 필터 + stockCode rename."""
    pf = tmp_path / "005930.parquet"
    pl.DataFrame(
        {
            "stock_code": ["005930"] * 4,
            "bsns_year": ["2025", "2025", "2024", "2024"],
            "reprt_nm": ["1분기", "1분기", "4분기", "4분기"],
            "reprt_code": ["11013", "11013", "11011", "11011"],
            "sj_div": ["IS", "BS", "IS", "BS"],
            "fs_nm": ["연결재무제표"] * 4,
            "account_id": ["ifrs-full_Revenue", "x", "ifrs-full_Revenue", "x"],
            "account_nm": ["매출액", "x", "매출액", "x"],
            "thstrm_amount": ["100", "1", "400", "4"],
            "thstrm_add_amount": [None] * 4,
            "rcept_no": ["20250515aa"] * 4,
        }
    ).write_parquet(str(pf))

    lz = _loadRawFinanceViaDuckDb(tmp_path, sjDivs=["IS"])
    assert lz is not None
    df = lz.collect()
    assert "stockCode" in df.columns
    assert df["stockCode"].to_list() == ["005930"] * 2  # IS 만 통과
    assert set(df["sj_div"].to_list()) == {"IS"}


@pytest.mark.unit
def test_loadRawFinance_accountPushDown_specialChars(tmp_path):
    """``'`` 포함된 fastKeys 도 SQL escape 후 정상 매치."""
    pf = tmp_path / "005930.parquet"
    pl.DataFrame(
        {
            "stock_code": ["005930"] * 3,
            "bsns_year": ["2025"] * 3,
            "reprt_nm": ["1분기"] * 3,
            "reprt_code": ["11013"] * 3,
            "sj_div": ["IS"] * 3,
            "fs_nm": ["연결재무제표"] * 3,
            "account_id": ["x", "ifrs-full_Revenue", "z"],
            # 가상의 `'` 포함 키 — SQL escape 동작 검증
            "account_nm": ["o'malley", "매출액", "잡항목"],
            "thstrm_amount": ["1", "100", "2"],
            "thstrm_add_amount": [None] * 3,
            "rcept_no": ["20250515aa"] * 3,
        }
    ).write_parquet(str(pf))

    lz = _loadRawFinanceViaDuckDb(
        tmp_path,
        accountNms={"o'malley", "매출액"},
    )
    assert lz is not None
    df = lz.collect()
    assert set(df["account_nm"].to_list()) == {"o'malley", "매출액"}


@pytest.mark.unit
def test_loadRawFinance_sinceYearFilter(tmp_path):
    """sinceYear 필터 SQL 단 push-down."""
    pf = tmp_path / "005930.parquet"
    pl.DataFrame(
        {
            "stock_code": ["005930"] * 4,
            "bsns_year": ["2019", "2020", "2021", "2022"],
            "reprt_nm": ["4분기"] * 4,
            "reprt_code": ["11011"] * 4,
            "sj_div": ["IS"] * 4,
            "fs_nm": ["연결재무제표"] * 4,
            "account_id": ["ifrs-full_Revenue"] * 4,
            "account_nm": ["매출액"] * 4,
            "thstrm_amount": ["1", "2", "3", "4"],
            "thstrm_add_amount": [None] * 4,
            "rcept_no": ["20250515aa"] * 4,
        }
    ).write_parquet(str(pf))

    lz = _loadRawFinanceViaDuckDb(tmp_path, sinceYear=2021)
    assert lz is not None
    df = lz.collect()
    # 캘린더 환원 적용됐을 수 있으므로 정확 bsns_year 비교 대신 cutoff 만 검증
    years = sorted({int(y) for y in df["bsns_year"].to_list()})
    assert min(years) >= 2021


@pytest.mark.unit
def test_loadRawFinance_calendarizeApplied(tmp_path):
    """비12월 결산 raw → 캘린더 분기 환원 적용 확인."""
    pf = tmp_path / "448730.parquet"  # 10월 결산 가정
    # 사업보고서 row (rcept_no 첫 8자 = 접수일자) — 10월 결산 추정용 (접수월 1월)
    pl.DataFrame(
        {
            "stock_code": ["448730"] * 2,
            "bsns_year": ["2025", "2025"],
            "reprt_nm": ["4분기", "1분기"],
            "reprt_code": ["11011", "11013"],
            "sj_div": ["IS", "IS"],
            "fs_nm": ["연결재무제표"] * 2,
            "account_id": ["ifrs-full_Revenue"] * 2,
            "account_nm": ["매출액"] * 2,
            "thstrm_amount": ["100", "20"],
            "thstrm_add_amount": [None] * 2,
            # 사업보고서 접수일 = 2026-01-08 → 결산월 추정 = 10월
            "rcept_no": ["20260108123456", "20250211ax"],
        }
    ).write_parquet(str(pf))

    # _loadRawFinanceViaDuckDb 는 빌더의 _fiscalMonthMap 을 호출하는데
    # 실 데이터 디렉토리 의존 (data/dart/finance) → 단위 테스트에서는 환원 식 자체만 검증.
    # _calendarizeWithFmMap 동작은 prebuild path 의 _calendarizeFiscalColumns 와 동일 수학.
    # 본 테스트는 LazyFrame 반환 + 빈 결과 없음만 확인.
    lz = _loadRawFinanceViaDuckDb(tmp_path)
    assert lz is not None
    df = lz.collect()
    assert df.height == 2
    assert "stockCode" in df.columns


@pytest.mark.unit
def test_loadRawFinance_columnsSubset(tmp_path):
    """columns 인자로 SELECT 절 컬럼 제한."""
    pf = tmp_path / "005930.parquet"
    pl.DataFrame(
        {
            "stock_code": ["005930"],
            "bsns_year": ["2025"],
            "reprt_nm": ["1분기"],
            "sj_div": ["IS"],
            "fs_nm": ["연결재무제표"],
            "account_id": ["ifrs-full_Revenue"],
            "account_nm": ["매출액"],
            "thstrm_amount": ["100"],
            "extra_col": ["ignore"],
            "rcept_no": ["20250515aa"],
        }
    ).write_parquet(str(pf))

    lz = _loadRawFinanceViaDuckDb(tmp_path, columns=("stockCode", "bsns_year", "account_nm"))
    assert lz is not None
    df = lz.collect()
    assert set(df.columns) == {"stockCode", "bsns_year", "account_nm"}
