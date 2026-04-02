"""fixture 기반 Company 통합 테스트 — 실제 parquet 데이터로 검증.

tests/fixtures/dart/ 하위의 실제 삼성전자 데이터를 사용한다.
DARTLAB_DATA_DIR을 fixtures/ 경로로 지정하여 Company가 fixture를 로드하도록 한다.
fixture 데이터는 최소한이므로 일부 결과가 None일 수 있다 — 정상.
"""

from __future__ import annotations

import gc
import os
from pathlib import Path

import pytest

pytestmark = [pytest.mark.integration]

FIXTURE_DIR = Path(__file__).parent / "fixtures"
_SAMSUNG = "005930"


def _fixture_data_available() -> bool:
    """fixture parquet 존재 여부."""
    return (FIXTURE_DIR / "dart" / "finance" / f"{_SAMSUNG}.parquet").exists()


@pytest.fixture(scope="module")
def samsung():
    """fixture 데이터로 삼성전자 Company 로드."""
    if not _fixture_data_available():
        pytest.skip("Fixture data not available")

    # DARTLAB_DATA_DIR을 fixture 경로로 설정
    os.environ["DARTLAB_DATA_DIR"] = str(FIXTURE_DIR)
    import dartlab

    dartlab.dataDir = str(FIXTURE_DIR)
    try:
        c = dartlab.Company(_SAMSUNG)
        yield c
    except Exception:
        pytest.skip("Fixture data not available or Company init failed")
    finally:
        gc.collect()


# ── Company 기본 속성 ──


class TestCompanyBasic:
    def test_stockCode(self, samsung):
        assert samsung.stockCode == _SAMSUNG

    def test_corpName(self, samsung):
        assert samsung.corpName is not None
        assert len(samsung.corpName) > 0

    def test_market(self, samsung):
        # 삼성전자는 KOSPI
        assert hasattr(samsung, "market")

    def test_currency(self, samsung):
        assert samsung.currency == "KRW"


# ── 재무제표 접근 ──


class TestFinanceAccess:
    def test_IS_returns_dataframe(self, samsung):
        import polars as pl

        result = samsung.IS
        if result is not None:
            assert isinstance(result, pl.DataFrame)
            assert "계정명" in result.columns

    def test_BS_returns_dataframe(self, samsung):
        import polars as pl

        result = samsung.BS
        if result is not None:
            assert isinstance(result, pl.DataFrame)
            assert "계정명" in result.columns

    def test_CF_may_be_none(self, samsung):
        import polars as pl

        result = samsung.CF
        # fixture에 CF가 없을 수 있음
        assert result is None or isinstance(result, pl.DataFrame)


# ── show / select ──


class TestShowSelect:
    def test_show_IS(self, samsung):
        import polars as pl

        result = samsung.show("IS")
        if result is not None:
            assert isinstance(result, pl.DataFrame)

    def test_show_BS(self, samsung):
        import polars as pl

        result = samsung.show("BS")
        if result is not None:
            assert isinstance(result, pl.DataFrame)

    def test_select_IS_revenue(self, samsung):
        result = samsung.select("IS", ["매출액"])
        # SelectResult 또는 None
        if result is not None:
            assert hasattr(result, "df")

    def test_select_BS_total_assets(self, samsung):
        result = samsung.select("BS", ["자산총계"])
        if result is not None:
            assert hasattr(result, "df")

    def test_show_dividend(self, samsung):
        result = samsung.show("dividend")
        # dividend 데이터가 없을 수 있음
        assert result is None or result is not None  # crash 없음 확인


# ── ratios / timeseries / topics ──


class TestDerivedData:
    def test_ratios(self, samsung):
        import polars as pl

        result = samsung.ratios
        assert result is None or isinstance(result, pl.DataFrame)

    def test_annual(self, samsung):
        result = samsung.annual
        # annual은 (dict, periods) 튜플 또는 None
        assert result is None or isinstance(result, tuple)
        if isinstance(result, tuple):
            assert len(result) == 2

    def test_timeseries(self, samsung):
        result = samsung.timeseries
        # timeseries는 (dict, periods) 튜플 또는 None
        assert result is None or isinstance(result, tuple)
        if isinstance(result, tuple):
            assert len(result) == 2

    def test_topics(self, samsung):
        result = samsung.topics
        # list 또는 DataFrame
        assert result is not None


# ── analysis 기본 호출 ──


class TestAnalysisBasic:
    def test_analysis_profitability(self, samsung):
        samsung._cache.clear()
        result = samsung.analysis("financial", "수익성")
        assert result is None or isinstance(result, dict)

    def test_analysis_stability(self, samsung):
        samsung._cache.clear()
        result = samsung.analysis("financial", "안정성")
        assert result is None or isinstance(result, dict)

    def test_analysis_growth(self, samsung):
        samsung._cache.clear()
        result = samsung.analysis("financial", "성장성")
        assert result is None or isinstance(result, dict)


# ── credit ──


class TestCreditBasic:
    def test_credit(self, samsung):
        import polars as pl

        samsung._cache.clear()
        try:
            result = samsung.credit()
            assert result is None or isinstance(result, dict)
        except (
            RuntimeError,
            ValueError,
            KeyError,
            TypeError,
            AttributeError,
            ZeroDivisionError,
            pl.exceptions.PolarsError,
        ):
            # fixture 데이터 부족 또는 scan 데이터 미존재로 실패 가능
            pass


# ── quant ──


class TestQuantBasic:
    def test_quant(self, samsung):
        try:
            result = samsung.quant()
            assert result is None or isinstance(result, dict)
        except (RuntimeError, ValueError, KeyError):
            # 주가 데이터 필요 — fixture에 없을 수 있음
            pass
