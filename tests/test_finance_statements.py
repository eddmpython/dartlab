"""finance.statements 테스트."""

import polars as pl
import pytest

from tests.conftest import SAMSUNG, requires_samsung

pytestmark = pytest.mark.integration


@requires_samsung
class TestStatements:
    def test_basic(self):
        from dartlab.providers.dart.docs.finance.statements import statements

        r = statements(SAMSUNG)
        assert r is not None
        assert isinstance(r.BS, pl.DataFrame)
        assert isinstance(r.IS, pl.DataFrame)

    def test_cf(self):
        from dartlab.providers.dart.docs.finance.statements import statements

        r = statements(SAMSUNG)
        assert r.CF is not None
        assert len(r.CF) > 0
