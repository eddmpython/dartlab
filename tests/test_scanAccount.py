"""scanAccount 테스트."""

import pytest

pytestmark = pytest.mark.unit


class TestResolveSjDiv:
    """snakeId → sjDiv 자동 결정."""

    def test_sales(self):
        from dartlab.engines.company.dart.finance.scanAccount import _resolveSjDiv

        assert _resolveSjDiv("sales") == "IS"

    def test_totalAssets(self):
        from dartlab.engines.company.dart.finance.scanAccount import _resolveSjDiv

        assert _resolveSjDiv("total_assets") == "BS"

    def test_operatingCashFlow(self):
        from dartlab.engines.company.dart.finance.scanAccount import _resolveSjDiv

        assert _resolveSjDiv("cash_flows_from_operating_activities") == "CF"

    def test_unknownRaises(self):
        from dartlab.engines.company.dart.finance.scanAccount import _resolveSjDiv

        with pytest.raises(ValueError, match="sortOrder.json"):
            _resolveSjDiv("totally_fake_account_xyz")


class TestParseAmount:
    """금액 파싱."""

    def test_normal(self):
        from dartlab.engines.company.dart.finance.scanAccount import _parseAmount

        assert _parseAmount("1,234,567") == 1234567.0

    def test_negative(self):
        from dartlab.engines.company.dart.finance.scanAccount import _parseAmount

        assert _parseAmount("-500") == -500.0

    def test_none(self):
        from dartlab.engines.company.dart.finance.scanAccount import _parseAmount

        assert _parseAmount(None) is None

    def test_dash(self):
        from dartlab.engines.company.dart.finance.scanAccount import _parseAmount

        assert _parseAmount("-") is None

    def test_empty(self):
        from dartlab.engines.company.dart.finance.scanAccount import _parseAmount

        assert _parseAmount("") is None


class TestScanAccountImport:
    """import 및 시그니처."""

    def test_importable(self):
        from dartlab.engines.company.dart.finance import scanAccount

        assert callable(scanAccount)

    def test_fromInit(self):
        from dartlab.engines.company.dart.finance.scanAccount import scanAccount

        assert callable(scanAccount)


class TestScanAccountReal:
    """실제 데이터 검증."""

    pytestmark = pytest.mark.requires_data

    def test_salesDataFrame(self):
        """sales 스캔이 DataFrame을 반환하고 stockCode 컬럼이 있는지."""
        from dartlab.engines.company.dart.finance.scanAccount import scanAccount

        df = scanAccount("sales")
        assert "stockCode" in df.columns
        assert df.height > 0

    def test_samsungSalesMatch(self):
        """삼성전자 매출이 buildAnnual 결과와 일치하는지."""
        import polars as pl

        from dartlab.engines.company.dart.finance.pivot import buildAnnual
        from dartlab.engines.company.dart.finance.scanAccount import scanAccount

        # buildAnnual 기준값
        annualResult = buildAnnual("005930")
        if annualResult is None:
            pytest.skip("005930 finance 데이터 없음")
        series, years = annualResult
        salesVals = series.get("IS", {}).get("sales")
        if not salesVals:
            pytest.skip("005930 IS sales 없음")

        expected = {}
        for i, y in enumerate(years):
            if i < len(salesVals) and salesVals[i] is not None:
                expected[str(y)] = salesVals[i]

        # scanAccount 결과 (연간 모드로 비교)
        df = scanAccount("sales", annual=True)
        row = df.filter(pl.col("stockCode") == "005930")
        assert row.height == 1, "삼성전자가 결과에 없음"

        # 연도별 대조
        matched = 0
        for year, expectedVal in expected.items():
            if year in row.columns:
                actual = row[year][0]
                if actual is not None and expectedVal is not None:
                    assert abs(actual - expectedVal) < 1.0, f"{year}: expected={expectedVal}, actual={actual}"
                    matched += 1

        assert matched >= 3, f"매칭된 연도가 {matched}개뿐 (최소 3개 필요)"

    def test_bsAccount(self):
        """BS 계정(total_assets) 스캔."""
        from dartlab.engines.company.dart.finance.scanAccount import scanAccount

        df = scanAccount("total_assets", sjDiv="BS")
        assert "stockCode" in df.columns
        assert df.height > 0

    def test_performance(self):
        """전종목 스캔 30초 이내."""
        import time

        from dartlab.engines.company.dart.finance.scanAccount import scanAccount

        t0 = time.time()
        df = scanAccount("sales")
        elapsed = time.time() - t0
        assert elapsed < 30, f"스캔 {elapsed:.1f}초 (30초 초과)"
        assert df.height > 100, f"종목 수 {df.height}개 (최소 100개 필요)"
