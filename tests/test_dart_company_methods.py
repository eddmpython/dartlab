"""Company 메서드 위임 테스트 — 내부 모듈 mock으로 위임 구조 검증.

mock_company fixture로 데이터 없이 실행. 실제 코드 경로를 거친다.
"""

from __future__ import annotations

import polars as pl
import pytest

pytestmark = pytest.mark.unit


# ══════════════════════════════════════
# 1. show() — Company.show가 topic 데이터를 반환
# ══════════════════════════════════════


class TestShow:
    def test_show_is_returns_dataframe(self, mock_company):
        result = mock_company.show("IS")
        assert isinstance(result, pl.DataFrame)
        assert "계정명" in result.columns
        assert "2024Q4" in result.columns

    def test_show_bs_returns_dataframe(self, mock_company):
        result = mock_company.show("BS")
        assert isinstance(result, pl.DataFrame)

    def test_show_cf_returns_dataframe(self, mock_company):
        result = mock_company.show("CF")
        assert isinstance(result, pl.DataFrame)

    def test_show_unknown_topic_returns_none(self, mock_company):
        result = mock_company.show("nonexistent_topic")
        assert result is None


# ══════════════════════════════════════
# 2. select() — 행 필터 + SelectResult 반환
# ══════════════════════════════════════


class TestSelect:
    def test_select_single_account(self, mock_company):
        result = mock_company.select("IS", ["매출액"])
        assert result is not None
        assert hasattr(result, "df")
        assert result.df.height >= 1

    def test_select_multiple_accounts(self, mock_company):
        result = mock_company.select("IS", ["매출액", "영업이익"])
        assert result is not None
        labels = result.df["계정명"].to_list()
        assert "매출액" in labels
        assert "영업이익" in labels

    def test_select_string_account(self, mock_company):
        """단일 str도 list로 변환되어 동작."""
        result = mock_company.select("IS", "매출액")
        assert result is not None
        assert result.df.height >= 1

    def test_select_unknown_stmt_returns_none(self, mock_company):
        result = mock_company.select("UNKNOWN", ["매출액"])
        assert result is None

    def test_select_returns_period_columns(self, mock_company):
        result = mock_company.select("IS", ["매출액"])
        assert result is not None
        cols = result.df.columns
        period_cols = [c for c in cols if c != "계정명"]
        assert len(period_cols) > 0
        # Q4 분기 컬럼이 존재
        assert any("Q4" in c for c in period_cols)

    def test_select_all_accounts_none(self, mock_company):
        """accounts=None이면 전체 DataFrame 반환."""
        result = mock_company.select("BS")
        assert result is not None
        assert result.df.height == 11  # _BS_ACCOUNTS 길이

    def test_select_missing_account_fills_zeros(self, mock_company):
        """존재하지 않는 계정은 0으로 채운 행 생성."""
        result = mock_company.select("IS", ["존재하지않는계정"])
        assert result is not None
        assert result.df.height == 1
        assert result.df["계정명"][0] == "존재하지않는계정"


# ══════════════════════════════════════
# 3. trace() — 출처 추적
# ══════════════════════════════════════


class TestTrace:
    def test_trace_returns_dict(self, mock_company):
        result = mock_company.trace("사업의 내용")
        assert isinstance(result, dict)
        assert result["topic"] == "사업의 내용"
        assert "source" in result

    def test_trace_with_period(self, mock_company):
        result = mock_company.trace("IS", period="2024")
        assert result is not None
        assert result["period"] == "2024"


# ══════════════════════════════════════
# 4. diff() — 기간 간 변화
# ══════════════════════════════════════


class TestDiff:
    def test_diff_returns_none_on_mock(self, mock_company):
        result = mock_company.diff()
        assert result is None


# ══════════════════════════════════════
# 5. topicSummaries() — topic 목록 + 요약
# ══════════════════════════════════════


class TestTopicSummaries:
    def test_returns_dict(self, mock_company):
        result = mock_company.topicSummaries()
        assert isinstance(result, dict)
        assert "IS" in result
        assert "BS" in result
        assert "CF" in result

    def test_values_are_strings(self, mock_company):
        result = mock_company.topicSummaries()
        for v in result.values():
            assert isinstance(v, str)


# ══════════════════════════════════════
# 6. filings() — 공시 목록
# ══════════════════════════════════════


class TestFilings:
    def test_returns_list(self, mock_company):
        result = mock_company.filings()
        assert isinstance(result, list)


# ══════════════════════════════════════
# 7. listing() — 정적 메서드 (전체 상장사 목록)
# ══════════════════════════════════════


class TestListing:
    def test_listing_returns_dataframe(self, mock_company):
        result = mock_company.listing()
        assert isinstance(result, pl.DataFrame)
        assert "종목코드" in result.columns

    def test_listing_static_call(self):
        """MockCompany.listing()은 정적 메서드로 호출 가능."""
        from tests.conftest import MockCompany

        result = MockCompany.listing()
        assert isinstance(result, pl.DataFrame)


# ══════════════════════════════════════
# 8. search() — 정적 메서드 (종목 검색)
# ══════════════════════════════════════


class TestSearch:
    def test_search_returns_dataframe(self, mock_company):
        result = mock_company.search("삼성")
        assert isinstance(result, pl.DataFrame)
        assert "회사명" in result.columns

    def test_search_static_call(self):
        from tests.conftest import MockCompany

        result = MockCompany.search("삼성")
        assert isinstance(result, pl.DataFrame)


# ══════════════════════════════════════
# 9. Company 속성 검증
# ══════════════════════════════════════


class TestAttributes:
    def test_stock_code(self, mock_company):
        assert mock_company.stockCode == "005930"

    def test_corp_name(self, mock_company):
        assert mock_company.corpName == "삼성전자"

    def test_market(self, mock_company):
        assert mock_company.market == "KOSPI"

    def test_currency(self, mock_company):
        assert mock_company.currency == "KRW"

    def test_insights(self, mock_company):
        ins = mock_company.insights
        assert isinstance(ins, dict)
        assert "overall" in ins

    def test_sector_none(self, mock_company):
        assert mock_company.sector is None

    def test_notes_accessor(self, mock_company):
        assert mock_company.notes.inventory is None
        assert mock_company.notes.borrowings is None

    def test_is_property(self, mock_company):
        assert isinstance(mock_company.IS, pl.DataFrame)

    def test_bs_property(self, mock_company):
        assert isinstance(mock_company.BS, pl.DataFrame)

    def test_cf_property(self, mock_company):
        assert isinstance(mock_company.CF, pl.DataFrame)

    def test_annual_property(self, mock_company):
        assert isinstance(mock_company.annual, pl.DataFrame)

    def test_cumulative_property(self, mock_company):
        assert isinstance(mock_company.cumulative, pl.DataFrame)


# ══════════════════════════════════════
# 10. gather() — 외부 데이터 수집 mock
# ══════════════════════════════════════


class TestGather:
    def test_gather_price(self, mock_company):
        result = mock_company.gather("price")
        assert isinstance(result, pl.DataFrame)
        assert "close" in result.columns

    def test_gather_other_returns_none(self, mock_company):
        assert mock_company.gather("flow") is None
        assert mock_company.gather("macro") is None
        assert mock_company.gather("news") is None


# ══════════════════════════════════════
# 11. empty_mock_company — 모든 데이터 None
# ══════════════════════════════════════


class TestEmptyMock:
    def test_select_returns_none(self, empty_mock_company):
        assert empty_mock_company.select("IS", ["매출액"]) is None

    def test_show_returns_none(self, empty_mock_company):
        assert empty_mock_company.show("IS") is None

    def test_gather_returns_none(self, empty_mock_company):
        assert empty_mock_company.gather("price") is None

    def test_has_attributes(self, empty_mock_company):
        assert empty_mock_company.stockCode == "999999"
        assert empty_mock_company.corpName == "빈회사"


# ══════════════════════════════════════
# 12. Real Company facade — canHandle 라우팅 테스트 (mock provider)
# ══════════════════════════════════════


class TestCompanyFacadeRouting:
    """dartlab.Company() facade의 canHandle 라우팅 로직 테스트."""

    def test_empty_code_raises(self):
        from dartlab.company import Company

        with pytest.raises(ValueError, match="종목코드"):
            Company("")

    def test_whitespace_code_raises(self):
        from dartlab.company import Company

        with pytest.raises(ValueError, match="종목코드"):
            Company("   ")
