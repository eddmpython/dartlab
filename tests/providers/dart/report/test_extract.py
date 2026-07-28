"""providers/dart/report/extract.py mirror smoke — P6."""

import pytest

pytestmark = pytest.mark.unit


def test_imports():
    try:
        import dartlab.providers.dart.report.extract  # noqa: F401
    except ImportError as e:
        pytest.skip(f"module import requires data/env: {e}")


def test_extract_annual_callable() -> None:
    """extractAnnual() callable smoke."""
    from dartlab.providers.dart.report.extract import extractAnnual

    assert callable(extractAnnual)


def test_extract_clean_callable() -> None:
    """extractClean() callable smoke."""
    from dartlab.providers.dart.report.extract import extractClean

    assert callable(extractClean)


def test_extract_raw_callable() -> None:
    """extractRaw() callable smoke."""
    from dartlab.providers.dart.report.extract import extractRaw

    assert callable(extractRaw)


def test_extract_result_callable() -> None:
    """extractResult() callable smoke."""
    from dartlab.providers.dart.report.extract import extractResult

    assert callable(extractResult)


def test_extract_raw_falls_back_to_settlement_year() -> None:
    """사업연도가 기수 라벨이면 결산일에서 연도를 얻는다.

    감사 계열 세 apiType (auditOpinion · auditContract · nonAuditContract) 은 사업연도
    자리에 "제57기 1분기" 처럼 기수를 담는다. 네 자리 숫자가 없어 연도가 null 이 되고
    연도 필터가 행을 통째로 버렸다. 삼성전자 감사의견은 원본 93 행을 갖고도 0 행이었고
    감사의견 시계열이 어느 회사에서나 비어 있었다.
    """
    import polars as pl

    from dartlab.providers.dart.report.extract import extractRaw

    base = pl.DataFrame(
        {
            "stockCode": ["005930", "005930"],
            "apiType": ["auditOpinion", "auditOpinion"],
            "year": ["제57기 1분기\n(당분기)", "2024"],
            "quarter": ["1분기", "4분기"],
            "stlm_dt": ["2025-03-31", "2024-12-31"],
            "adt_opinion": ["적정", "적정"],
        }
    )
    out = extractRaw("005930", "auditOpinion", baseDf=base)

    assert out is not None
    assert out.height == 2  # 기수 라벨 행이 살아남는다
    assert sorted(out["year"].to_list()) == [2024, 2025]
