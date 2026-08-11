"""제품 smoke의 네트워크 격리 계약."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from tests.audit import productSmoke

pytestmark = pytest.mark.unit


def testFixtureAndEmptyModesEnableStrictOffline(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.delenv("DARTLAB_PRODUCT_SMOKE_OFFLINE", raising=False)

    fixtureEnv = productSmoke._dataEnv("fixtures", None)
    emptyEnv = productSmoke._dataEnv("empty", SimpleNamespace(name=str(tmp_path)))

    assert fixtureEnv["DARTLAB_PRODUCT_SMOKE_OFFLINE"] == "1"
    assert emptyEnv["DARTLAB_PRODUCT_SMOKE_OFFLINE"] == "1"


def testScenarioIsolationUsesStrictOffline(monkeypatch: pytest.MonkeyPatch) -> None:
    from dartlab.core import offlineGuard

    calls: list[bool] = []
    monkeypatch.setenv("DARTLAB_PRODUCT_SMOKE_OFFLINE", "1")
    monkeypatch.setattr(offlineGuard, "enforceOffline", lambda *, strict=False: calls.append(strict))

    assert productSmoke._enforceScenarioIsolation() is True
    assert calls == [True]
