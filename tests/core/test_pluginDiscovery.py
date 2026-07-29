"""L0 bootstrap registry와 caller-owned module loader 회귀."""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from dartlab.core import pluginDiscovery
from dartlab.core.pluginDiscovery import (
    bootstrap,
    importCallerModule,
    lazyAttribute,
    registerBootstrap,
)

pytestmark = [pytest.mark.unit]


@pytest.fixture(autouse=True)
def _isolateBootstrapRegistry():
    """전역 bootstrap 상태를 테스트 전후의 정확한 snapshot으로 되돌린다."""
    savedBootstraps = dict(pluginDiscovery._BOOTSTRAPS)
    savedCompleted = set(pluginDiscovery._COMPLETED)
    savedInProgress = dict(pluginDiscovery._IN_PROGRESS)
    yield
    pluginDiscovery._BOOTSTRAPS.clear()
    pluginDiscovery._BOOTSTRAPS.update(savedBootstraps)
    pluginDiscovery._COMPLETED.clear()
    pluginDiscovery._COMPLETED.update(savedCompleted)
    pluginDiscovery._IN_PROGRESS.clear()
    pluginDiscovery._IN_PROGRESS.update(savedInProgress)


def testBootstrapRunsOnlyOnceAfterSuccess() -> None:
    """성공한 callback은 같은 registry key에서 한 번만 실행된다."""
    calls: list[str] = []
    registerBootstrap("test.once", lambda: calls.append("called"))

    assert bootstrap("test.once") is True
    assert bootstrap("test.once") is True
    assert calls == ["called"]


def testDifferentBootstrapKeysAreIndependent() -> None:
    """한 registry 완료 상태가 다른 registry를 건너뛰게 하지 않는다."""
    calls: list[str] = []
    registerBootstrap("test.a", lambda: calls.append("a"))
    registerBootstrap("test.b", lambda: calls.append("b"))

    assert bootstrap("test.a") is True
    assert bootstrap("test.b") is True
    assert calls == ["a", "b"]


def testMissingBootstrapReturnsFalse() -> None:
    """composition이 등록하지 않은 key는 조용한 성공으로 오인하지 않는다."""
    assert bootstrap("test.missing") is False


def testBootstrapFailurePropagatesAndRetries() -> None:
    """내부 ImportError를 삼키거나 완료 처리하지 않고 다음 호출에서 재시도한다."""
    attempts = 0

    def flaky() -> None:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise ImportError("implementation import failed")

    registerBootstrap("test.retry", flaky)

    with pytest.raises(ImportError, match="implementation import failed"):
        bootstrap("test.retry")
    assert "test.retry" not in pluginDiscovery._COMPLETED
    assert bootstrap("test.retry") is True
    assert attempts == 2


def testReentrantBootstrapTerminates() -> None:
    """같은 callback의 재진입은 무한 재귀 없이 현재 호출에 제어를 돌려준다."""
    nested: list[bool] = []

    def callback() -> None:
        nested.append(bootstrap("test.reentrant"))

    registerBootstrap("test.reentrant", callback)

    assert bootstrap("test.reentrant") is True
    assert nested == [False]


def testConcurrentBootstrapWaitsForSingleSuccessfulCallback() -> None:
    """동시 최초 호출도 미등록 상태를 반환하지 않고 같은 성공 결과를 기다린다."""
    entered = threading.Event()
    release = threading.Event()
    calls = 0

    def callback() -> None:
        nonlocal calls
        calls += 1
        entered.set()
        assert release.wait(timeout=2)

    registerBootstrap("test.concurrent", callback)
    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(bootstrap, "test.concurrent")
        assert entered.wait(timeout=2)
        second = executor.submit(bootstrap, "test.concurrent")
        release.set()
        assert first.result(timeout=2) is True
        assert second.result(timeout=2) is True
    assert calls == 1


def testCallerOwnedModuleLoaderPropagatesImportError(monkeypatch: pytest.MonkeyPatch) -> None:
    """caller-owned 동적 경계도 import 실패를 원인 그대로 전파한다."""

    def fail(modulePath: str):
        raise ImportError(f"cannot import {modulePath}")

    monkeypatch.setattr(pluginDiscovery.importlib, "import_module", fail)

    with pytest.raises(ImportError, match="cannot import plugin.example"):
        importCallerModule("plugin.example")


def testLazyAttributeKeepsPythonAttributeContract(monkeypatch: pytest.MonkeyPatch) -> None:
    """정의된 이름은 해석하고 정의되지 않은 이름은 AttributeError를 낸다."""

    class Loaded:
        value = 42

    monkeypatch.setattr(pluginDiscovery.importlib, "import_module", lambda _: Loaded)

    assert lazyAttribute("facade", {"value": "plugin.example"}, "value") == 42
    with pytest.raises(AttributeError, match="has no attribute"):
        lazyAttribute("facade", {"value": "plugin.example"}, "missing")
