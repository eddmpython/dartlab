"""scan finance prebuild 의 회계분기 → 캘린더 분기 환원 단위 테스트.

`bsns_year + reprt_nm` 직매핑이 결산월 다른 회사에서 misplace 를 만들던
회귀를 막는다 (예: 10월 결산 사업연도 2026 4분기 → 잘못된 2025Q4 같은).

검증 지점:
1. `_toCalendarPeriod` 수학 (모든 결산월 × 4 분기 = 48 케이스)
2. `_estimateFiscalMonthFromAnnualFiling` — 사업보고서 접수일에서 결산월 추정
3. `_calendarizeFiscalColumns` — 12월 결산 identity + 비12월 결산 환원
"""

from __future__ import annotations

import polars as pl
import pytest

from dartlab.scan.builders.kr.core import (
    _calendarizeFiscalColumns,
    _estimateFiscalMonthFromAnnualFiling,
    _toCalendarPeriod,
)


@pytest.mark.unit
def test_toCalendarPeriod_dec_identity():
    """12월 결산은 calendar 와 fiscal 이 일치 (identity)."""
    for q in (1, 2, 3, 4):
        cy, cq = _toCalendarPeriod(2025, q, 12)
        assert (cy, cq) == (2025, q), f"12월 결산 bsns_year=2025 Q{q} 는 {(2025, q)} 여야 함"


@pytest.mark.unit
def test_toCalendarPeriod_mar_shift():
    """3월 결산 bsns_year=2026 = 회계기간 2025.4~2026.3 → 캘린더 환원."""
    assert _toCalendarPeriod(2026, 1, 3) == (2025, 2)  # Q1 (4~6월)
    assert _toCalendarPeriod(2026, 2, 3) == (2025, 3)  # Q2 (7~9월)
    assert _toCalendarPeriod(2026, 3, 3) == (2025, 4)  # Q3 (10~12월)
    assert _toCalendarPeriod(2026, 4, 3) == (2026, 1)  # Q4 (1~3월)


@pytest.mark.unit
def test_toCalendarPeriod_jun_shift():
    """6월 결산 bsns_year=2025 = 회계기간 2024.7~2025.6 → 캘린더 환원."""
    assert _toCalendarPeriod(2025, 1, 6) == (2024, 3)
    assert _toCalendarPeriod(2025, 2, 6) == (2024, 4)
    assert _toCalendarPeriod(2025, 3, 6) == (2025, 1)
    assert _toCalendarPeriod(2025, 4, 6) == (2025, 2)


@pytest.mark.unit
def test_toCalendarPeriod_oct_quarterPattern():
    """10월 결산 (삼성FN리츠 사례) — Q1 종료 2026.1 = 캘린더 Q1."""
    assert _toCalendarPeriod(2026, 1, 10) == (2026, 1)
    assert _toCalendarPeriod(2026, 4, 10) == (2026, 4)


@pytest.mark.unit
def test_estimateFiscalMonth_dec(tmp_path):
    """12월 결산: 사업보고서 접수 = 다음해 3월. rcept_no 첫 8자 = 20250331 → 추정 12월."""
    pf = tmp_path / "12dec.parquet"
    pl.DataFrame(
        {
            "reprt_code": ["11011", "11011", "11013"],
            "rcept_no": ["20250320123456", "20240318999999", "20250515555555"],
        }
    ).write_parquet(str(pf))
    assert _estimateFiscalMonthFromAnnualFiling(pf) == 12


@pytest.mark.unit
def test_estimateFiscalMonth_mar(tmp_path):
    """3월 결산: 사업보고서 접수 = 6월. rcept_no=2025063012... → 추정 3월."""
    pf = tmp_path / "3mar.parquet"
    pl.DataFrame(
        {
            "reprt_code": ["11011", "11011"],
            "rcept_no": ["20250620111111", "20240625222222"],
        }
    ).write_parquet(str(pf))
    assert _estimateFiscalMonthFromAnnualFiling(pf) == 3


@pytest.mark.unit
def test_estimateFiscalMonth_oct(tmp_path):
    """10월 결산: 사업보고서 접수 = 다음해 1월. rcept_no=20260108... → 추정 10월."""
    pf = tmp_path / "10oct.parquet"
    pl.DataFrame(
        {
            "reprt_code": ["11011", "11011"],
            "rcept_no": ["20260108123456", "20250105987654"],
        }
    ).write_parquet(str(pf))
    assert _estimateFiscalMonthFromAnnualFiling(pf) == 10


@pytest.mark.unit
def test_estimateFiscalMonth_modeMostCommon(tmp_path):
    """접수일이 회계연도 전환 등으로 섞이면 최빈값 채택."""
    pf = tmp_path / "mixed.parquet"
    pl.DataFrame(
        {
            "reprt_code": ["11011"] * 4,
            # 3 개는 3월 → 12월 결산, 1 개는 6월 → 3월 결산. 최빈 = 12.
            "rcept_no": ["20250320aa", "20240321bb", "20230322cc", "20250620dd"],
        }
    ).write_parquet(str(pf))
    assert _estimateFiscalMonthFromAnnualFiling(pf) == 12


@pytest.mark.unit
def test_estimateFiscalMonth_noAnnual(tmp_path):
    """사업보고서 (11011) row 없으면 None 반환."""
    pf = tmp_path / "noannual.parquet"
    pl.DataFrame({"reprt_code": ["11013", "11012"], "rcept_no": ["20250515aa", "20250815bb"]}).write_parquet(str(pf))
    assert _estimateFiscalMonthFromAnnualFiling(pf) is None


@pytest.mark.unit
def test_calendarizeFiscalColumns_dec_identity():
    """12월 결산은 변환해도 동일 (identity)."""
    df = pl.DataFrame(
        {
            "bsns_year": ["2025", "2025", "2025", "2025"],
            "reprt_nm": ["1분기", "2분기", "3분기", "4분기"],
        }
    )
    result = _calendarizeFiscalColumns(df, 12)
    assert result["bsns_year"].to_list() == ["2025", "2025", "2025", "2025"]
    assert result["reprt_nm"].to_list() == ["1분기", "2분기", "3분기", "4분기"]


@pytest.mark.unit
def test_calendarizeFiscalColumns_marShift():
    """3월 결산 bsns_year=2026 의 4 분기 → 캘린더 2025Q2/Q3/Q4 + 2026Q1."""
    df = pl.DataFrame({"bsns_year": ["2026"] * 4, "reprt_nm": ["1분기", "2분기", "3분기", "4분기"]})
    result = _calendarizeFiscalColumns(df, 3)
    assert result["bsns_year"].to_list() == ["2025", "2025", "2025", "2026"]
    assert result["reprt_nm"].to_list() == ["2분기", "3분기", "4분기", "1분기"]


@pytest.mark.unit
def test_calendarizeFiscalColumns_nonQuarter_preserved():
    """``reprt_nm`` 이 "N분기" 패턴이 아니면 원본 그대로 보존."""
    df = pl.DataFrame({"bsns_year": ["2025", "2025"], "reprt_nm": ["연간", "1분기"]})
    result = _calendarizeFiscalColumns(df, 3)
    # 연간 row 는 변환 skip (bsns_year 원본 유지), 1분기는 환원
    assert result["bsns_year"].to_list() == ["2025", "2024"]
    assert result["reprt_nm"].to_list() == ["연간", "2분기"]


@pytest.mark.unit
def test_sanityCheckCalendarYears_emits_warning_for_future_year(tmp_path, caplog):
    """``bsns_year > today.year`` row 가 있으면 sanity check warning emit."""
    import logging
    from datetime import date

    from dartlab.scan.builders.kr.core import _sanityCheckCalendarYears

    future_year = str(date.today().year + 1)
    bad = pl.DataFrame(
        {
            "stockCode": ["005930", "000660"],
            "bsns_year": [future_year, future_year],
            "reprt_nm": ["4분기", "1분기"],
        }
    )
    pf = tmp_path / "finance.parquet"
    bad.write_parquet(str(pf))

    with caplog.at_level(logging.WARNING):
        _sanityCheckCalendarYears(pf)

    warnings = " ".join(r.message for r in caplog.records)
    assert "finance/sanity" in warnings
    assert f"bsns_year > {date.today().year}" in warnings
    assert "2개 발견" in warnings


@pytest.mark.unit
def test_sanityCheckCalendarYears_silent_on_normal_data(tmp_path, caplog):
    """정상 데이터 (bsns_year <= today.year) 에는 경고 안 emit."""
    import logging
    from datetime import date

    from dartlab.scan.builders.kr.core import _sanityCheckCalendarYears

    current_year = str(date.today().year)
    good = pl.DataFrame({"stockCode": ["005930"], "bsns_year": [current_year], "reprt_nm": ["4분기"]})
    pf = tmp_path / "finance.parquet"
    good.write_parquet(str(pf))

    with caplog.at_level(logging.WARNING):
        _sanityCheckCalendarYears(pf)

    sanity_warns = [r for r in caplog.records if "finance/sanity" in r.message]
    assert not sanity_warns, f"정상 데이터에 경고 발생: {sanity_warns}"


@pytest.mark.unit
def test_loadCorpProfileMap_missingFile_returnsEmpty(tmp_path, monkeypatch):
    """corpProfile.parquet 없으면 빈 dict (다른 SSOT fallback 으로 위임)."""
    from dartlab.scan.builders.kr.core import _loadCorpProfileMap

    monkeypatch.setattr("dartlab.core.dataLoader._dataDir", lambda _cat: tmp_path)
    assert _loadCorpProfileMap() == {}


@pytest.mark.unit
def test_loadCorpProfileMap_validParquet_extractsMapping(tmp_path, monkeypatch):
    """corpProfile.parquet 가 있으면 stockCode → acc_mt 매핑 정확 추출."""
    from dartlab.scan.builders.kr.core import _loadCorpProfileMap

    pf = tmp_path / "corpProfile.parquet"
    pl.DataFrame(
        {
            "corp_code": ["00126380", "00164742", "00149293"],
            "stockCode": ["005930", "000660", ""],  # 비상장 corp_code 제외 확인
            "corp_name": ["삼성전자", "SK하이닉스", "ABC법인"],
            "acc_mt": ["12", "12", "06"],
        }
    ).write_parquet(str(pf))

    monkeypatch.setattr("dartlab.core.dataLoader._dataDir", lambda _cat: tmp_path)
    result = _loadCorpProfileMap()
    assert result == {"005930": 12, "000660": 12}  # stockCode 빈 row 는 제외


@pytest.mark.unit
def test_loadCorpProfileMap_handlesAccMtVariants(tmp_path, monkeypatch):
    """acc_mt 가 ``"12"`` · ``"12월"`` · ``" 12 "`` 같은 변형도 정상 파싱."""
    from dartlab.scan.builders.kr.core import _loadCorpProfileMap

    pf = tmp_path / "corpProfile.parquet"
    pl.DataFrame(
        {
            "corp_code": ["A", "B", "C", "D"],
            "stockCode": ["100001", "100002", "100003", "100004"],
            "corp_name": ["x"] * 4,
            "acc_mt": ["12", "12월", " 06 ", "invalid"],
        }
    ).write_parquet(str(pf))

    monkeypatch.setattr("dartlab.core.dataLoader._dataDir", lambda _cat: tmp_path)
    result = _loadCorpProfileMap()
    assert result == {"100001": 12, "100002": 12, "100003": 6}  # invalid 는 skip


@pytest.mark.unit
def test_loadJurirStockMap_requires_completed_v2_profile(tmp_path):
    """legacy profile은 legal identity ground truth로 사용하지 않는다."""
    from dartlab.scan.builders.kr.corpProfile import (
        CORP_PROFILE_SCHEMA,
        CorpProfileIdentityError,
        _loadJurirStockMap,
    )

    profile = tmp_path / "corpProfile.parquet"
    pl.DataFrame(
        {
            "corp_code": ["A"],
            "stockCode": ["100001"],
            "corp_name": ["알파"],
            "jurir_no": ["123456-1234567"],
            "bizr_no": [""],
            "acc_mt": ["12"],
            "induty_code": [""],
            "est_dt": [""],
            "corp_cls": ["K"],
            "profileSchemaVersion": [1],
        },
        schema=CORP_PROFILE_SCHEMA,
    ).write_parquet(profile)

    with pytest.raises(CorpProfileIdentityError, match="backfill 미완료"):
        _loadJurirStockMap(profile)


@pytest.mark.unit
def test_loadJurirStockMap_normalizes_and_rejects_duplicate_identity(tmp_path):
    """법인번호는 13자리로 정규화하고 서로 다른 종목의 중복은 실패한다."""
    from dartlab.scan.builders.kr.corpProfile import (
        CORP_PROFILE_SCHEMA,
        CORP_PROFILE_SCHEMA_VERSION,
        CorpProfileIdentityError,
        _loadJurirStockMap,
    )

    profile = tmp_path / "corpProfile.parquet"
    base = {
        "corp_code": ["A"],
        "stockCode": ["100001"],
        "corp_name": ["알파"],
        "jurir_no": ["123456-1234567"],
        "bizr_no": [""],
        "acc_mt": ["12"],
        "induty_code": [""],
        "est_dt": [""],
        "corp_cls": ["K"],
        "profileSchemaVersion": [CORP_PROFILE_SCHEMA_VERSION],
    }
    pl.DataFrame(base, schema=CORP_PROFILE_SCHEMA).write_parquet(profile)

    assert _loadJurirStockMap(profile) == {"1234561234567": "100001"}

    duplicate = {column: values * 2 for column, values in base.items()}
    duplicate["corp_code"] = ["A", "B"]
    duplicate["stockCode"] = ["100001", "100002"]
    pl.DataFrame(duplicate, schema=CORP_PROFILE_SCHEMA).write_parquet(profile)

    with pytest.raises(CorpProfileIdentityError, match="법인등록번호 충돌"):
        _loadJurirStockMap(profile)
