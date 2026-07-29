"""dartlab.gather.ecos.series mirror 슬롯 — smoke import (P-G7.2).

룰 7 (src↔tests 1:1 mirror) 만족용 placeholder. 본격 단위 테스트는 후속.
"""

from __future__ import annotations

import importlib
import types

import pytest

pytestmark = pytest.mark.unit


def test_smoke_import() -> None:
    """``dartlab.gather.ecos.series`` 모듈 import 가능 — 모듈 구조 회귀 차단."""
    importlib.import_module("dartlab.gather.ecos.series")


def test_fetch_series_invalid_value_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """손상된 DATA_VALUE를 결측치로 바꾸지 않는다."""
    from dartlab.gather.ecos import series
    from dartlab.gather.ecos.types import CatalogEntry, EcosError

    entry = CatalogEntry("TEST", "테스트", "테스트", "D", "unit", "", "T", "I")
    monkeypatch.setattr(series._cache, "get", lambda *args, **kwargs: None)
    monkeypatch.setattr(series._cache, "put", lambda *args, **kwargs: None)
    monkeypatch.setattr(series._catalog, "getEntry", lambda indicatorId: entry)
    client = types.SimpleNamespace(get=lambda **kwargs: [{"TIME": "20260102", "DATA_VALUE": "broken"}])

    with pytest.raises(EcosError, match="DATA_VALUE"):
        series.fetchSeries(client, "TEST")
