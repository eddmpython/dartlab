"""KIND 상장법인 검색 회귀 테스트."""

import sys

import pytest

pytestmark = pytest.mark.unit

import polars as pl


def _listingMod():
    """GatherEntry가 attribute 접근을 가로채므로 sys.modules에서 직접 가져온다."""
    from dartlab.gather.listing import searchName  # noqa: F401 — 모듈 로드 보장

    return sys.modules["dartlab.gather.listing"]


class TestKindListSearch:
    def test_search_name_treats_keyword_as_literal(self, monkeypatch):
        from dartlab.gather.listing import searchName

        monkeypatch.setattr(
            _listingMod(),
            "getKindList",
            lambda **_kw: pl.DataFrame(
                {
                    "회사명": ["삼성전자", "카카오뱅크"],
                    "종목코드": ["005930", "323410"],
                }
            ),
        )

        result = searchName("삼성전자\\")
        assert result.height == 0

    def test_search_name_blank_keyword_returns_empty(self, monkeypatch):
        from dartlab.gather.listing import searchName

        monkeypatch.setattr(
            _listingMod(),
            "getKindList",
            lambda **_kw: pl.DataFrame(
                {
                    "회사명": ["삼성전자"],
                    "종목코드": ["005930"],
                }
            ),
        )

        result = searchName("   ")
        assert result.height == 0
