"""finance.statements 테스트."""

import polars as pl

from tests.conftest import SAMSUNG, requires_samsung


@requires_samsung
class TestStatements:
    def test_basic(self):
        from dartlab.engines.dart.docs.finance.statements import statements

        r = statements(SAMSUNG)
        assert r is not None
        assert isinstance(r.BS, pl.DataFrame)
        assert isinstance(r.IS, pl.DataFrame)

    def test_cf(self):
        from dartlab.engines.dart.docs.finance.statements import statements

        r = statements(SAMSUNG)
        assert r.CF is not None
        assert len(r.CF) > 0
