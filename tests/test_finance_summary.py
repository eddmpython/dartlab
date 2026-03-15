"""finance.summary (fsSummary) 테스트."""

import polars as pl

from tests.conftest import SAMSUNG, requires_samsung


@requires_samsung
class TestAnalyze:
    def test_basic(self):
        from dartlab.engines.dart.docs.finance.summary import fsSummary

        r = fsSummary(SAMSUNG)
        assert r is not None
        assert r.corpName == "삼성전자"
        assert isinstance(r.FS, pl.DataFrame)
        assert len(r.FS) > 0

    def test_bs_is(self):
        from dartlab.engines.dart.docs.finance.summary import fsSummary

        r = fsSummary(SAMSUNG)
        assert r.BS is not None
        assert r.IS is not None
        assert len(r.BS) > 0
        assert len(r.IS) > 0

    def test_matching_rate(self):
        from dartlab.engines.dart.docs.finance.summary import fsSummary

        r = fsSummary(SAMSUNG)
        assert r.allRate >= 0.8
