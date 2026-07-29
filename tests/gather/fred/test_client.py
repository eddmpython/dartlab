"""dartlab.gather.fred.client mirror 슬롯 — smoke import (P-G7.2).

룰 7 (src↔tests 1:1 mirror) 만족용 placeholder. 본격 단위 테스트는 후속.
"""

from __future__ import annotations

import importlib

import pytest

pytestmark = pytest.mark.unit


def test_smoke_import() -> None:
    """``dartlab.gather.fred.client`` 모듈 import 가능 — 모듈 구조 회귀 차단."""
    importlib.import_module("dartlab.gather.fred.client")


def test_network_failure_is_wrapped_as_fred_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """재시도 후 네트워크 원인을 FredError에 연결한다."""
    import httpx

    from dartlab.gather.fred.client import FredClient
    from dartlab.gather.fred.types import FredError

    class FailingSession:
        def get(self, *args, **kwargs):
            raise httpx.ConnectError("offline")

    client = object.__new__(FredClient)
    client._keys = ["key"]
    client._key_idx = 0
    client._session = FailingSession()
    client._timestamps = []
    monkeypatch.setattr(FredClient, "_backoff", staticmethod(lambda attempt: None))

    with pytest.raises(FredError) as excInfo:
        client.get("/series/observations", series_id="TEST")

    assert isinstance(excInfo.value.__cause__, httpx.ConnectError)
