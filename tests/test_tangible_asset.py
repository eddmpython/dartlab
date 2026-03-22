"""finance.tangibleAsset 테스트."""

import polars as pl
import pytest

from tests.conftest import SAMSUNG, requires_samsung

pytestmark = pytest.mark.integration


@requires_samsung
class TestTangibleAsset:
    def test_basic(self):
        from dartlab.engines.company.dart.docs.finance.tangibleAsset import tangibleAsset

        r = tangibleAsset(SAMSUNG)
        assert r is not None
        assert r.corpName == "삼성전자"
        assert r.nYears >= 1

    def test_reliability(self):
        from dartlab.engines.company.dart.docs.finance.tangibleAsset import tangibleAsset

        r = tangibleAsset(SAMSUNG)
        assert r is not None
        assert r.reliability in ("high", "low")

    def test_movements(self):
        from dartlab.engines.company.dart.docs.finance.tangibleAsset import tangibleAsset

        r = tangibleAsset(SAMSUNG)
        assert r is not None
        assert r.movements is not None
        assert len(r.movements) >= 1
        for year, mvs in r.movements.items():
            assert len(mvs) >= 1
            for mv in mvs:
                assert len(mv.categories) >= 1
                assert len(mv.rows) >= 1

    def test_movement_df(self):
        from dartlab.engines.company.dart.docs.finance.tangibleAsset import tangibleAsset

        r = tangibleAsset(SAMSUNG)
        assert r is not None
        if r.movementDf is not None:
            assert isinstance(r.movementDf, pl.DataFrame)
            assert "카테고리" in r.movementDf.columns
