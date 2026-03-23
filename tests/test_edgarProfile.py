from __future__ import annotations

import types

import polars as pl
import pytest

pytestmark = pytest.mark.unit


def test_profile_sections_returns_none_for_empty_docs_sections():
    from dartlab.engines.company.edgar._profile_accessor import _ProfileAccessor

    company = types.SimpleNamespace(
        _cache={},
        docs=types.SimpleNamespace(sections=pl.DataFrame()),
    )

    accessor = _ProfileAccessor(company)
    assert accessor.sections is None
    assert company._cache["_sections"] is None
