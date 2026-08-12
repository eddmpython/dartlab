"""제품 smoke의 데이터 재현성과 네트워크 격리 계약."""

from __future__ import annotations

import time
from types import SimpleNamespace

import pytest

from tests.audit import productSmoke

pytestmark = pytest.mark.unit


def testFixtureModeBuildsCleanCheckoutDataAndEnablesStrictOffline(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.delenv("DARTLAB_PRODUCT_SMOKE_OFFLINE", raising=False)
    tmp = SimpleNamespace(name=str(tmp_path))

    fixtureEnv = productSmoke._dataEnv("fixtures", tmp)
    dataRoot = tmp_path / "data"

    assert fixtureEnv["DARTLAB_PRODUCT_SMOKE_OFFLINE"] == "1"
    assert fixtureEnv["DARTLAB_NO_REFRESH"] == "1"
    assert fixtureEnv["DARTLAB_DATA_DIR"] == str(dataRoot)
    assert (dataRoot / "dart/scan/finance.parquet").is_file()
    assert (dataRoot / "dart/scan/changes.parquet").is_file()
    assert (dataRoot / "dart/scan/sharesOutstanding.parquet").is_file()
    assert (dataRoot / "dart/scan/valuation.parquet").is_file()
    assert (dataRoot / "dart/panel/005930.parquet").is_file()
    assert (dataRoot / "kindList/corpList.parquet").stat().st_mtime >= time.time() - 60


def testEmptyModeKeepsColdStartNetworkPathVisible(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.delenv("DARTLAB_PRODUCT_SMOKE_OFFLINE", raising=False)

    emptyEnv = productSmoke._dataEnv("empty", SimpleNamespace(name=str(tmp_path)))

    assert "DARTLAB_PRODUCT_SMOKE_OFFLINE" not in emptyEnv


def testScenarioIsolationUsesStrictOffline(monkeypatch: pytest.MonkeyPatch) -> None:
    from dartlab.core import offlineGuard

    calls: list[bool] = []
    monkeypatch.setenv("DARTLAB_PRODUCT_SMOKE_OFFLINE", "1")
    monkeypatch.setattr(offlineGuard, "enforceOffline", lambda *, strict=False: calls.append(strict))

    assert productSmoke._enforceScenarioIsolation() is True
    assert calls == [True]
