"""scan 축 함수 단위 테스트 — mock parquet 데이터로 검증.

scan _helpers 유틸리티 + 데이터 로드 경로를 합성 데이터로 테스트한다.
"""

from __future__ import annotations

from unittest.mock import patch

import polars as pl
import pytest

pytestmark = pytest.mark.unit


# ── 1. parse_num ──


class TestParseNum:
    def test_int(self):
        from dartlab.scan._helpers import parse_num

        assert parse_num(42) == 42.0

    def test_float(self):
        from dartlab.scan._helpers import parse_num

        assert parse_num(3.14) == 3.14

    def test_string_number(self):
        from dartlab.scan._helpers import parse_num

        assert parse_num("1,234,567") == 1234567.0

    def test_string_negative(self):
        from dartlab.scan._helpers import parse_num

        assert parse_num("-500") == -500.0

    def test_dash_returns_none(self):
        from dartlab.scan._helpers import parse_num

        assert parse_num("-") is None

    def test_empty_returns_none(self):
        from dartlab.scan._helpers import parse_num

        assert parse_num("") is None
        assert parse_num(None) is None

    def test_invalid_string(self):
        from dartlab.scan._helpers import parse_num

        assert parse_num("N/A") is None


# ── 2. extractAccount ──


class TestExtractAccount:
    def test_match_by_account_id(self):
        from dartlab.scan._helpers import extractAccount

        df = pl.DataFrame(
            {
                "account_id": ["ifrs-full_Revenue", "ifrs-full_CostOfSales"],
                "account_nm": ["매출액", "매출원가"],
                "thstrm_amount": ["1000000", "500000"],
            }
        )
        result = extractAccount(df, {"ifrs-full_Revenue"}, set())
        assert result == 1_000_000.0

    def test_match_by_account_nm(self):
        from dartlab.scan._helpers import extractAccount

        df = pl.DataFrame(
            {
                "account_id": ["X", "Y"],
                "account_nm": ["매출액", "매출원가"],
                "thstrm_amount": ["2000000", "1000000"],
            }
        )
        result = extractAccount(df, set(), {"매출액"})
        assert result == 2_000_000.0

    def test_no_match(self):
        from dartlab.scan._helpers import extractAccount

        df = pl.DataFrame(
            {
                "account_id": ["A"],
                "account_nm": ["기타"],
                "thstrm_amount": ["100"],
            }
        )
        result = extractAccount(df, {"not_exist"}, {"없는계정"})
        assert result is None

    def test_none_amount(self):
        from dartlab.scan._helpers import extractAccount

        df = pl.DataFrame(
            {
                "account_id": ["ifrs-full_Revenue"],
                "account_nm": ["매출액"],
                "thstrm_amount": ["-"],
            }
        )
        result = extractAccount(df, {"ifrs-full_Revenue"}, set())
        assert result is None


# ── 3. _ensureScanData with mock ──


class TestEnsureScanData:
    def test_returns_path_when_exists(self, tmp_path):
        """기존 scan 데이터가 있으면 해당 경로를 반환한다."""
        import dartlab.scan._helpers as helpers

        scan_dir = tmp_path / "scan"
        scan_dir.mkdir()
        (scan_dir / "test.parquet").write_bytes(b"fake")

        # Reset the global flag so _ensureScanData actually checks
        original = helpers._scanDownloaded
        helpers._scanDownloaded = False

        try:
            with patch("dartlab.scan._helpers._ensureScanData") as mock_ensure:
                mock_ensure.return_value = scan_dir
                result = mock_ensure()
                assert result == scan_dir
        finally:
            helpers._scanDownloaded = original


# ── 4. scan_parquets with mock data ──


class TestScanParquets:
    def test_prebuild_scan_parquet(self, tmp_path):
        """프리빌드 scan parquet에서 데이터를 읽는다."""
        from dartlab.scan._helpers import scan_parquets

        # Create a test parquet file
        report_dir = tmp_path / "scan" / "report"
        report_dir.mkdir(parents=True)

        df = pl.DataFrame(
            {
                "stockCode": ["005930", "000660"],
                "year": ["2023", "2023"],
                "quarter": ["4분기", "4분기"],
                "apiType": ["majorHolder", "majorHolder"],
                "name": ["이재용", "최태원"],
                "pct": ["20.0", "15.0"],
            }
        )
        df.write_parquet(str(report_dir / "majorHolder.parquet"))

        with patch("dartlab.scan._helpers._ensureScanData", return_value=tmp_path / "scan"):
            result = scan_parquets(
                "majorHolder",
                ["stockCode", "year", "quarter", "name", "pct"],
            )
            assert result.height == 2
            assert "stockCode" in result.columns


# ── 5. find_latest_year ──


class TestFindLatestYear:
    def test_finds_year_with_enough_data(self):
        from dartlab.scan._helpers import find_latest_year

        rows = [{"year": "2023", "value": str(i)} for i in range(600)]
        rows += [{"year": "2022", "value": str(i)} for i in range(600)]
        df = pl.DataFrame(rows)
        assert find_latest_year(df, "value", min_count=500) == "2023"

    def test_skips_sparse_year(self):
        from dartlab.scan._helpers import find_latest_year

        rows_2023 = [{"year": "2023", "value": ""} for _ in range(600)]
        rows_2022 = [{"year": "2022", "value": str(i)} for i in range(600)]
        df = pl.DataFrame(rows_2023 + rows_2022)
        assert find_latest_year(df, "value", min_count=500) == "2022"

    def test_returns_none_if_no_year_qualifies(self):
        from dartlab.scan._helpers import find_latest_year

        rows = [{"year": "2023", "value": None} for _ in range(10)]
        df = pl.DataFrame(rows)
        assert find_latest_year(df, "value", min_count=500) is None


# ── 6. pick_best_quarter ──


class TestPickBestQuarter:
    def test_prefers_q2(self):
        from dartlab.scan._helpers import pick_best_quarter

        df = pl.DataFrame(
            {
                "quarter": ["1분기", "2분기", "3분기", "4분기"],
                "value": [1, 2, 3, 4],
            }
        )
        result = pick_best_quarter(df)
        assert result.height == 1
        assert result["quarter"][0] == "2분기"

    def test_falls_back_to_q4(self):
        from dartlab.scan._helpers import pick_best_quarter

        df = pl.DataFrame(
            {
                "quarter": ["1분기", "4분기"],
                "value": [1, 4],
            }
        )
        result = pick_best_quarter(df)
        assert result["quarter"][0] == "4분기"


# ── 7. parse_date_year ──


class TestParseDateYear:
    def test_dot_format(self):
        from dartlab.scan._helpers import parse_date_year

        assert parse_date_year("2023.06.15") == 2023

    def test_dash_format(self):
        from dartlab.scan._helpers import parse_date_year

        assert parse_date_year("2022-12-31") == 2022

    def test_none(self):
        from dartlab.scan._helpers import parse_date_year

        assert parse_date_year(None) is None
        assert parse_date_year("") is None
        assert parse_date_year("-") is None

    def test_out_of_range(self):
        from dartlab.scan._helpers import parse_date_year

        assert parse_date_year("1800.01.01") is None


# ── 8. QUARTER_ORDER constant ──


class TestQuarterOrder:
    def test_q2_has_highest_priority(self):
        from dartlab.scan._helpers import QUARTER_ORDER

        assert QUARTER_ORDER["2분기"] < QUARTER_ORDER["4분기"]
        assert QUARTER_ORDER["2분기"] < QUARTER_ORDER["3분기"]
        assert QUARTER_ORDER["2분기"] < QUARTER_ORDER["1분기"]
