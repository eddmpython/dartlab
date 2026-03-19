"""KIND 상장법인 검색 회귀 테스트."""

import polars as pl


class TestKindListSearch:
    def test_search_name_treats_keyword_as_literal(self, monkeypatch):
        from dartlab.core.kindList import searchName

        monkeypatch.setattr(
            "dartlab.core.kindList.getKindList",
            lambda: pl.DataFrame(
                {
                    "회사명": ["삼성전자", "카카오뱅크"],
                    "종목코드": ["005930", "323410"],
                }
            ),
        )

        result = searchName("삼성전자\\")
        assert result.height == 0

    def test_search_name_blank_keyword_returns_empty(self, monkeypatch):
        from dartlab.core.kindList import searchName

        monkeypatch.setattr(
            "dartlab.core.kindList.getKindList",
            lambda: pl.DataFrame(
                {
                    "회사명": ["삼성전자"],
                    "종목코드": ["005930"],
                }
            ),
        )

        result = searchName("   ")
        assert result.height == 0
