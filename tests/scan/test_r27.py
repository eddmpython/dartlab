"""R27 audit 회귀 테스트 — scan 엔진.

R27 audit 결과 scan 엔진은 silent failure 0 건 — 이미 명시적 에러 처리.
회귀 방지용 source check.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def test_scan_unknown_axis_raises_value_error():
    """없는 축은 ValueError. silent None 이면 회귀."""
    import dartlab

    with pytest.raises(ValueError, match="알 수 없는 scan 축"):
        dartlab.scan("없는축")


def test_scan_empty_string_raises_value_error():
    """빈 문자열도 ValueError."""
    import dartlab

    with pytest.raises(ValueError, match="알 수 없는 scan 축"):
        dartlab.scan("")


def test_scan_rejects_unknown_market_instead_of_using_kr_data():
    """알 수 없는 시장을 KR 결과로 대체하면 시장 간 데이터가 섞인다."""
    import dartlab

    with pytest.raises(ValueError, match="지원하지 않는 market"):
        dartlab.scan("profitability", market="MARS")


def test_market_rejection_points_to_indexName_for_exchanges():
    """막기만 하고 다른 길을 안 알려주면 찾아 헤맨다.

    실측(2026-08-06): "코스피에서" 를 요구한 스크리닝이 market 으로 막힌 뒤 fields 카탈로그를
    market, 시장, listing 으로 세 번 뒤지고 listing 과 dataHub.catalog 까지 열었다. market 은
    국가 코드이고 거래소는 screen spec 의 indexName 이 받는다.
    """
    import dartlab

    with pytest.raises(ValueError, match="indexName"):
        dartlab.scan("profitability", market="KOSPI")


def test_scan_rejects_us_for_kr_only_axis():
    """US 미지원 축은 KR 구현으로 fallback하지 않는다."""
    import dartlab

    with pytest.raises(ValueError, match="지원하지 않습니다"):
        dartlab.scan("governance", market="US")


def test_scan_rejects_unsupported_as_of_instead_of_returning_current_data():
    """과거 시점 요청에 현재 자료를 반환하면 결과의 기준일을 오인한다."""
    import dartlab

    with pytest.raises(ValueError, match="asOf 시점 고정"):
        dartlab.scan("profitability", asOf="2024-12-31")


def test_scan_rejects_unknown_us_option_instead_of_swallowing_typo(monkeypatch):
    """EDGAR 구현의 ``**kwargs``가 옵션 오타를 삼키지 않는다."""
    import dartlab

    with pytest.raises(ValueError, match="지원하지 않는 옵션"):
        dartlab.scan("profitability", market="US", typoOption=True)


def test_us_result_uses_common_target_filter_and_column_contract(monkeypatch):
    """US dispatcher도 공통 target 필터와 공개 한글 컬럼 후처리를 거친다."""
    import polars as pl

    import dartlab
    import dartlab.scan.scanClass as scan_class

    raw = pl.DataFrame(
        {
            "stockCode": ["AAPL", "MSFT"],
            "corpName": ["Apple Inc.", "Microsoft Corp."],
            "opMargin": [30.0, 40.0],
        }
    )
    monkeypatch.setattr(scan_class, "_edgarDispatch", lambda _axis, _kwargs: raw)

    result = dartlab.scan("profitability", "MSFT", market="US")

    assert result["종목코드"].to_list() == ["MSFT"]
    assert result["종목명"].to_list() == ["Microsoft Corp."]
    assert result["영업이익률"].to_list() == [40.0]


def test_scan_none_returns_guide():
    """None 입력 = 무인자 = 가이드 DataFrame."""
    import polars as pl

    import dartlab

    r = dartlab.scan(None)
    assert isinstance(r, pl.DataFrame)
    assert "axis" in r.columns
    assert "label" in r.columns
    assert "description" in r.columns
    assert "example" in r.columns
    assert len(r) >= 15


def test_scan_no_args_returns_guide():
    """무인자 호출 = 가이드 DataFrame."""
    import polars as pl

    import dartlab

    r = dartlab.scan()
    assert isinstance(r, pl.DataFrame)
    assert len(r) >= 15
