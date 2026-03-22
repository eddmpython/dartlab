"""FRED 엔진 단위 테스트 — mock 기반 (실제 API 호출 없음)."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

import polars as pl
import pytest

pytestmark = pytest.mark.unit


# ── types ──


class TestTypes:
    def test_series_meta_frozen(self):
        from dartlab.engines.gather.fred.types import SeriesMeta

        meta = SeriesMeta(
            id="GDP",
            title="Gross Domestic Product",
            frequency="Quarterly",
            units="Billions of Dollars",
            seasonal_adjustment="Seasonally Adjusted",
            observation_start="1947-01-01",
            observation_end="2024-01-01",
            last_updated="2024-03-28",
        )
        assert meta.id == "GDP"
        assert meta.frequency == "Quarterly"
        with pytest.raises(AttributeError):
            meta.id = "GDPC1"

    def test_catalog_entry_frozen(self):
        from dartlab.engines.gather.fred.types import CatalogEntry

        e = CatalogEntry("GDP", "GDP (명목)", "growth", "Quarterly", "Billions of Dollars", "미국 명목 GDP")
        assert e.group == "growth"

    def test_error_hierarchy(self):
        from dartlab.engines.gather.fred.types import (
            AuthenticationError,
            FredError,
            RateLimitError,
            SeriesNotFoundError,
        )

        assert issubclass(RateLimitError, FredError)
        assert issubclass(SeriesNotFoundError, FredError)
        assert issubclass(AuthenticationError, FredError)


# ── client ──


class TestClient:
    def test_no_api_key_raises(self):
        from dartlab.engines.gather.fred.client import FredClient
        from dartlab.engines.gather.fred.types import AuthenticationError

        with patch.dict("os.environ", {}, clear=True):
            # 환경변수도 없고 인자도 없으면 에러
            with pytest.raises(AuthenticationError):
                FredClient(api_key="")

    def test_multi_key_parsing(self):
        from dartlab.engines.gather.fred.client import FredClient

        client = FredClient(api_key="key1,key2,key3")
        assert len(client._keys) == 3
        assert client._resolve_key() == "key1"
        client._rotate_key()
        assert client._resolve_key() == "key2"

    def test_rate_limit_tracking(self):
        from dartlab.engines.gather.fred.client import FredClient

        client = FredClient(api_key="test_key")
        # 타임스탬프 추적이 동작하는지 확인
        client._rate_limit()
        assert len(client._timestamps) == 1


# ── catalog ──


class TestCatalog:
    def test_groups_exist(self):
        from dartlab.engines.gather.fred.catalog import get_groups

        groups = get_groups()
        assert "growth" in groups
        assert "inflation" in groups
        assert "rates" in groups
        assert "employment" in groups
        assert "markets" in groups
        assert "housing" in groups
        assert "money" in groups
        assert len(groups) == 7

    def test_all_ids_nonempty(self):
        from dartlab.engines.gather.fred.catalog import get_all_ids

        ids = get_all_ids()
        assert len(ids) >= 40

    def test_group_ids(self):
        from dartlab.engines.gather.fred.catalog import get_group_ids

        growth = get_group_ids("growth")
        assert "GDP" in growth
        assert "GDPC1" in growth

    def test_find_entry(self):
        from dartlab.engines.gather.fred.catalog import find_entry

        e = find_entry("UNRATE")
        assert e is not None
        assert e.group == "employment"
        assert find_entry("NONEXISTENT") is None

    def test_to_dataframe(self):
        from dartlab.engines.gather.fred.catalog import to_dataframe

        df = to_dataframe()
        assert isinstance(df, pl.DataFrame)
        assert "id" in df.columns
        assert "group" in df.columns
        assert df.height >= 40

    def test_to_dataframe_group(self):
        from dartlab.engines.gather.fred.catalog import to_dataframe

        df = to_dataframe("rates")
        assert df.height >= 5
        assert all(row == "rates" for row in df["group"].to_list())

    def test_no_duplicate_ids(self):
        from dartlab.engines.gather.fred.catalog import get_all_ids

        ids = get_all_ids()
        assert len(ids) == len(set(ids)), f"중복 시리즈 ID: {[x for x in ids if ids.count(x) > 1]}"


# ── series (mock) ──


class TestSeriesMock:
    def _mock_client(self, observations):
        client = MagicMock()
        client.get.return_value = {"observations": observations}
        return client

    def test_fetch_series_basic(self):
        from dartlab.engines.gather.fred.series import fetch_series

        obs = [
            {"date": "2024-01-01", "value": "100.5"},
            {"date": "2024-02-01", "value": "101.2"},
            {"date": "2024-03-01", "value": "."},
        ]
        client = self._mock_client(obs)
        df = fetch_series(client, "TEST")

        assert isinstance(df, pl.DataFrame)
        assert df.height == 3
        assert df["date"].dtype == pl.Date
        assert df["value"][0] == 100.5
        assert df["value"][2] is None

    def test_fetch_multi(self):
        from dartlab.engines.gather.fred.series import fetch_multi

        call_count = [0]

        def mock_get(endpoint, **params):
            call_count[0] += 1
            sid = params.get("series_id", "A")
            return {
                "observations": [
                    {"date": "2024-01-01", "value": str(call_count[0] * 10)},
                    {"date": "2024-02-01", "value": str(call_count[0] * 20)},
                ]
            }

        client = MagicMock()
        client.get.side_effect = mock_get

        df = fetch_multi(client, ["A", "B"])
        assert "A" in df.columns
        assert "B" in df.columns
        assert df.height == 2

    def test_search_series(self):
        from dartlab.engines.gather.fred.series import search_series

        client = MagicMock()
        client.get.return_value = {
            "seriess": [
                {
                    "id": "GDP",
                    "title": "Gross Domestic Product",
                    "frequency": "Quarterly",
                    "units": "Billions of Dollars",
                    "seasonal_adjustment_short": "SA",
                    "popularity": 95,
                },
            ]
        }

        df = search_series(client, "GDP")
        assert df.height == 1
        assert df["id"][0] == "GDP"

    def test_fetch_meta(self):
        from dartlab.engines.gather.fred.series import fetch_meta

        client = MagicMock()
        client.get.return_value = {
            "seriess": [
                {
                    "id": "GDP",
                    "title": "GDP",
                    "frequency": "Quarterly",
                    "units": "Billions",
                    "seasonal_adjustment": "SA",
                    "observation_start": "1947-01-01",
                    "observation_end": "2024-01-01",
                    "last_updated": "2024-03-28",
                    "notes": "",
                }
            ]
        }
        meta = fetch_meta(client, "GDP")
        assert meta.id == "GDP"


# ── transform ──


class TestTransform:
    def _sample_df(self, n=24):
        import polars as pl
        from datetime import date, timedelta

        dates = [date(2022, 1, 1) + timedelta(days=30 * i) for i in range(n)]
        values = [100 + i * 2.5 for i in range(n)]
        return pl.DataFrame({"date": dates, "value": values}).with_columns(pl.col("date").cast(pl.Date))

    def test_yoy(self):
        from dartlab.engines.gather.fred.transform import yoy

        df = self._sample_df()
        result = yoy(df)
        assert "value_yoy" in result.columns
        # 처음 12개는 null (12개월 전 데이터 없음)
        assert result["value_yoy"][0] is None

    def test_mom(self):
        from dartlab.engines.gather.fred.transform import mom

        df = self._sample_df()
        result = mom(df)
        assert "value_mom" in result.columns
        assert result["value_mom"][0] is None
        assert result["value_mom"][1] is not None

    def test_diff(self):
        from dartlab.engines.gather.fred.transform import diff

        df = self._sample_df()
        result = diff(df)
        assert "value_diff1" in result.columns
        assert result["value_diff1"][1] == pytest.approx(2.5)

    def test_moving_average(self):
        from dartlab.engines.gather.fred.transform import moving_average

        df = self._sample_df()
        result = moving_average(df, window=3)
        assert "value_ma3" in result.columns

    def test_normalize(self):
        from dartlab.engines.gather.fred.transform import normalize

        df = self._sample_df()
        result = normalize(df)
        assert "value_norm" in result.columns
        assert result["value_norm"][0] == pytest.approx(100.0)

    def test_correlation(self):
        from dartlab.engines.gather.fred.transform import correlation

        df = pl.DataFrame(
            {
                "date": [date(2024, 1, 1), date(2024, 2, 1), date(2024, 3, 1), date(2024, 4, 1)],
                "A": [1.0, 2.0, 3.0, 4.0],
                "B": [2.0, 4.0, 6.0, 8.0],
            }
        )
        result = correlation(df)
        assert result.height == 2
        # A와 B는 완전 상관
        assert result.filter(pl.col("column") == "A")["B"][0] == pytest.approx(1.0)

    def test_lead_lag(self):
        from dartlab.engines.gather.fred.transform import lead_lag

        df = pl.DataFrame(
            {
                "A": list(range(30)),
                "B": list(range(30)),
            }
        ).cast(pl.Float64)
        result = lead_lag(df, "A", "B", max_lag=3)
        assert "lag" in result.columns
        assert "correlation" in result.columns
        assert result.height == 7  # -3 to +3


# ── cache ──


class TestCache:
    def test_put_get(self):
        from dartlab.engines.gather.fred import cache

        cache.clear()
        df = pl.DataFrame({"date": [date(2024, 1, 1)], "value": [100.0]})
        cache.put("TEST", None, None, None, None, df)
        result = cache.get("TEST", None, None, None, None)
        assert result is not None
        assert result.height == 1

    def test_cache_miss(self):
        from dartlab.engines.gather.fred import cache

        cache.clear()
        result = cache.get("MISS", None, None, None, None)
        assert result is None


# ── spec ──


class TestSpec:
    def test_build_spec(self):
        from dartlab.engines.gather.fred.spec import buildSpec

        spec = buildSpec()
        assert spec["name"] == "fred"
        assert "catalog_groups" in spec
        assert len(spec["tools"]) == 5
        assert spec["total_catalog_series"] >= 40


# ── Fred facade (mock) ──


class TestFredFacade:
    def test_repr(self):
        """Fred repr에 카탈로그 수와 그룹이 포함."""
        with patch("dartlab.engines.gather.fred.client.FredClient.__init__", return_value=None):
            from dartlab.engines.gather.fred import Fred

            f = Fred.__new__(Fred)
            f._client = MagicMock()
            r = repr(f)
            assert "catalog=" in r
            assert "groups=" in r
