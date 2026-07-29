"""dartlab.gather.fred.series mirror 슬롯 — smoke import (P-G7.2).

룰 7 (src↔tests 1:1 mirror) 만족용 placeholder. 본격 단위 테스트는 후속.
"""

from __future__ import annotations

import importlib
import types

import pytest

pytestmark = pytest.mark.unit


def test_smoke_import() -> None:
    """``dartlab.gather.fred.series`` 모듈 import 가능 — 모듈 구조 회귀 차단."""
    importlib.import_module("dartlab.gather.fred.series")


def test_fetch_series_invalid_observation_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """손상된 FRED value를 결측치로 바꾸지 않는다."""
    from dartlab.gather.fred import series
    from dartlab.gather.fred.types import FredError

    monkeypatch.setattr(series._cache, "get", lambda *args, **kwargs: None)
    monkeypatch.setattr(series._cache, "put", lambda *args, **kwargs: None)
    client = types.SimpleNamespace(
        get=lambda *args, **kwargs: {"observations": [{"date": "2026-01-02", "value": "broken"}]}
    )

    with pytest.raises(FredError, match="value"):
        series.fetchSeries(client, "TEST")
