"""Scan data output consistency unit tests.

Tests _enrichWithKorean column renaming, _COLUMN_RENAME coverage,
and column ordering (종목코드 first, 종목명 second).
All mocked, no real data loading.
"""

from __future__ import annotations

from unittest.mock import patch

import polars as pl
import pytest

pytestmark = pytest.mark.unit


# ── imports ──

from dartlab.scan import _COLUMN_RENAME, _enrichWithKorean

# The function does `import dartlab as _dl; _dl.listing()` internally.
# We patch `dartlab.listing` on the top-level dartlab module.
_LISTING_PATCH = "dartlab.listing"


# ═══════════════════════════════════════════════════════════
# _COLUMN_RENAME coverage
# ═══════════════════════════════════════════════════════════


class TestColumnRenameMapping:
    def test_stockcode_mapped(self):
        assert _COLUMN_RENAME["stockCode"] == "종목코드"

    def test_common_financial_columns_exist(self):
        expected = {
            "opMargin": "영업이익률",
            "netMargin": "순이익률",
            "roe": "ROE",
            "roa": "ROA",
            "per": "PER",
            "pbr": "PBR",
        }
        for eng, kor in expected.items():
            assert _COLUMN_RENAME[eng] == kor, f"Missing or wrong mapping for {eng}"

    def test_growth_columns_exist(self):
        assert "revenueCagr" in _COLUMN_RENAME
        assert "opIncomeCagr" in _COLUMN_RENAME
        assert "netIncomeCagr" in _COLUMN_RENAME

    def test_efficiency_columns_exist(self):
        for col in ("assetTurnover", "invTurnover", "arTurnover", "ccc"):
            assert col in _COLUMN_RENAME, f"Missing mapping for {col}"

    def test_cashflow_columns_exist(self):
        for col in ("ocf", "icf", "finCf", "accrualRatio", "cfToNi"):
            assert col in _COLUMN_RENAME, f"Missing mapping for {col}"

    def test_governance_columns_exist(self):
        for col in ("holderPct", "opinion", "auditor", "stability"):
            assert col in _COLUMN_RENAME, f"Missing mapping for {col}"

    def test_all_values_are_korean(self):
        """All renamed values should be non-empty strings."""
        for key, value in _COLUMN_RENAME.items():
            assert isinstance(value, str)
            assert len(value) > 0


# ═══════════════════════════════════════════════════════════
# _enrichWithKorean — column renaming
# ═══════════════════════════════════════════════════════════


class TestEnrichWithKoreanRename:
    def test_renames_known_columns(self):
        df = pl.DataFrame(
            {
                "stockCode": ["005930"],
                "opMargin": [15.0],
                "roe": [12.0],
            }
        )
        with patch(_LISTING_PATCH, return_value=None):
            result = _enrichWithKorean(df)

        assert "종목코드" in result.columns
        assert "영업이익률" in result.columns
        assert "ROE" in result.columns

    def test_leaves_unknown_columns_unchanged(self):
        df = pl.DataFrame(
            {
                "stockCode": ["005930"],
                "customColumn": [42],
            }
        )
        with patch(_LISTING_PATCH, return_value=None):
            result = _enrichWithKorean(df)

        assert "customColumn" in result.columns

    def test_no_stockcode_column_skips_name_lookup(self):
        df = pl.DataFrame(
            {
                "opMargin": [15.0],
                "roe": [12.0],
            }
        )
        # No stockCode column -> no listing call needed
        result = _enrichWithKorean(df)
        assert "영업이익률" in result.columns
        assert "ROE" in result.columns


# ═══════════════════════════════════════════════════════════
# _enrichWithKorean — 종목명 join + ordering
# ═══════════════════════════════════════════════════════════


class TestEnrichWithKoreanNameJoin:
    def _mock_listing(self):
        """Create a mock listing DataFrame."""
        return pl.DataFrame(
            {
                "종목코드": ["005930", "000660"],
                "종목명": ["삼성전자", "SK하이닉스"],
            }
        )

    def test_adds_company_name_column(self):
        df = pl.DataFrame(
            {
                "stockCode": ["005930", "000660"],
                "opMargin": [15.0, 10.0],
            }
        )
        with patch(_LISTING_PATCH, return_value=self._mock_listing()):
            result = _enrichWithKorean(df)

        assert "종목명" in result.columns

    def test_stockcode_first_column(self):
        df = pl.DataFrame(
            {
                "stockCode": ["005930"],
                "opMargin": [15.0],
                "roe": [12.0],
            }
        )
        with patch(_LISTING_PATCH, return_value=self._mock_listing()):
            result = _enrichWithKorean(df)

        assert result.columns[0] == "종목코드"

    def test_company_name_second_column(self):
        df = pl.DataFrame(
            {
                "stockCode": ["005930"],
                "opMargin": [15.0],
            }
        )
        with patch(_LISTING_PATCH, return_value=self._mock_listing()):
            result = _enrichWithKorean(df)

        assert result.columns[0] == "종목코드"
        assert result.columns[1] == "종목명"

    def test_other_columns_after_name(self):
        df = pl.DataFrame(
            {
                "stockCode": ["005930"],
                "opMargin": [15.0],
                "roe": [12.0],
            }
        )
        with patch(_LISTING_PATCH, return_value=self._mock_listing()):
            result = _enrichWithKorean(df)

        cols = result.columns
        assert cols[0] == "종목코드"
        assert cols[1] == "종목명"
        remaining = cols[2:]
        assert "영업이익률" in remaining
        assert "ROE" in remaining

    def test_listing_returns_none_no_name_column(self):
        df = pl.DataFrame(
            {
                "stockCode": ["005930"],
                "opMargin": [15.0],
            }
        )
        with patch(_LISTING_PATCH, return_value=None):
            result = _enrichWithKorean(df)

        assert "종목명" not in result.columns
        assert result.columns[0] == "종목코드"

    def test_listing_exception_handled_gracefully(self):
        df = pl.DataFrame(
            {
                "stockCode": ["005930"],
                "opMargin": [15.0],
            }
        )
        with patch(_LISTING_PATCH, side_effect=RuntimeError("No data")):
            result = _enrichWithKorean(df)

        # Should not crash, columns still renamed
        assert "종목코드" in result.columns
        assert "영업이익률" in result.columns

    def test_listing_with_alt_column_name(self):
        """listing may use '회사명' instead of '종목명'."""
        listing = pl.DataFrame(
            {
                "종목코드": ["005930"],
                "회사명": ["삼성전자"],
            }
        )
        df = pl.DataFrame(
            {
                "stockCode": ["005930"],
                "opMargin": [15.0],
            }
        )
        with patch(_LISTING_PATCH, return_value=listing):
            result = _enrichWithKorean(df)

        assert "종목명" in result.columns
        assert result["종목명"][0] == "삼성전자"


# ═══════════════════════════════════════════════════════════
# Edge cases
# ═══════════════════════════════════════════════════════════


class TestEnrichEdgeCases:
    def test_empty_dataframe(self):
        df = pl.DataFrame(
            {
                "stockCode": [],
                "opMargin": [],
            }
        ).cast({"stockCode": pl.Utf8, "opMargin": pl.Float64})
        with patch(_LISTING_PATCH, return_value=None):
            result = _enrichWithKorean(df)

        assert result.height == 0
        assert "종목코드" in result.columns

    def test_no_mappable_columns(self):
        df = pl.DataFrame(
            {
                "someCustomCol": [1, 2, 3],
                "anotherCol": ["a", "b", "c"],
            }
        )
        result = _enrichWithKorean(df)
        # No renames, no crash
        assert "someCustomCol" in result.columns
        assert "anotherCol" in result.columns

    def test_multiple_rows_join_correctly(self):
        listing = pl.DataFrame(
            {
                "종목코드": ["005930", "000660", "035420"],
                "종목명": ["삼성전자", "SK하이닉스", "NAVER"],
            }
        )
        df = pl.DataFrame(
            {
                "stockCode": ["005930", "000660", "035420"],
                "roe": [12.0, 15.0, 8.0],
            }
        )
        with patch(_LISTING_PATCH, return_value=listing):
            result = _enrichWithKorean(df)

        assert result.height == 3
        names = result["종목명"].to_list()
        assert names == ["삼성전자", "SK하이닉스", "NAVER"]

    def test_unmatched_stockcode_gets_null_name(self):
        listing = pl.DataFrame(
            {
                "종목코드": ["005930"],
                "종목명": ["삼성전자"],
            }
        )
        df = pl.DataFrame(
            {
                "stockCode": ["005930", "999999"],
                "roe": [12.0, 5.0],
            }
        )
        with patch(_LISTING_PATCH, return_value=listing):
            result = _enrichWithKorean(df)

        assert result.height == 2
        names = result["종목명"].to_list()
        assert names[0] == "삼성전자"
        assert names[1] is None
