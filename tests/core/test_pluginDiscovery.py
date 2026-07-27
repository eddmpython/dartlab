"""플러그인 탐색 SSOT 회귀.

"알려진 모듈을 한 번만 import 해서 스스로 등록하게 한다"는 열세 줄이 core 안에 열한 벌
복사돼 있었다. 다른 것은 모듈 목록 상수 이름 하나뿐이고 나머지는 글자까지 같았다.

그렇게 두면 셋째 사본을 만들 때 옆에서 복사하게 되고, 한 곳에서 예외 처리를 넓히거나 로그를
붙여도 나머지 열은 그대로 남는다. 실제로 그중 하나는 재진입 순서가 달라 무한 재귀에 걸릴
수 있는 모양이었다. 먼저 표시하고 나중에 import 하는 순서가 아니면, import 대상 모듈이 같은
탐색을 다시 부를 때 같은 목록을 계속 돈다.

여기서 고정하는 것은 셋이다. 레지스트리마다 한 번만 돈다, 선택 의존성이 없어도 나머지는
등록된다, 재진입해도 무한히 돌지 않는다.
"""

from __future__ import annotations

import pytest

from dartlab.core.pluginDiscovery import _DISCOVERED, discoverOnce, resetDiscovery

pytestmark = [pytest.mark.unit]


@pytest.fixture(autouse=True)
def _isolateDiscovery():
    """전역 기록을 건드리므로 앞뒤로 되돌린다."""
    saved = set(_DISCOVERED)
    resetDiscovery()
    yield
    resetDiscovery()
    _DISCOVERED.update(saved)


def testRunsOnlyOncePerRegistry(monkeypatch: pytest.MonkeyPatch) -> None:
    """두 번째 호출은 아무 것도 import 하지 않아야 한다."""

    calls: list[str] = []
    monkeypatch.setattr(
        "dartlab.core.pluginDiscovery.importlib.import_module", lambda name: calls.append(name) or object()
    )

    discoverOnce("registry.a", ["mod.one", "mod.two"])
    discoverOnce("registry.a", ["mod.one", "mod.two"])

    assert calls == ["mod.one", "mod.two"]


def testDifferentRegistriesAreIndependent(monkeypatch: pytest.MonkeyPatch) -> None:
    """한 레지스트리가 돌았다고 다른 레지스트리가 건너뛰면 안 된다."""

    calls: list[str] = []
    monkeypatch.setattr(
        "dartlab.core.pluginDiscovery.importlib.import_module", lambda name: calls.append(name) or object()
    )

    discoverOnce("registry.a", ["mod.one"])
    discoverOnce("registry.b", ["mod.two"])

    assert calls == ["mod.one", "mod.two"]


def testMissingOptionalModuleDoesNotStopTheRest(monkeypatch: pytest.MonkeyPatch) -> None:
    """선택 의존성이 빠진 설치에서도 나머지 provider 는 등록돼야 한다."""

    loaded: list[str] = []

    def _fake(name: str):
        if name == "mod.missing":
            raise ImportError(name)
        loaded.append(name)
        return object()

    monkeypatch.setattr("dartlab.core.pluginDiscovery.importlib.import_module", _fake)

    discoverOnce("registry.a", ["mod.missing", "mod.present"])

    assert loaded == ["mod.present"]


def testBrokenModuleIsNotSwallowed(monkeypatch: pytest.MonkeyPatch) -> None:
    """의존성 부재와 모듈 자체의 고장은 다른 사건이다. 뒤엣것은 올려 보낸다."""

    def _fake(name: str):
        raise ValueError("모듈 안에서 터짐")

    monkeypatch.setattr("dartlab.core.pluginDiscovery.importlib.import_module", _fake)

    with pytest.raises(ValueError):
        discoverOnce("registry.a", ["mod.broken"])


def testReentrantDiscoveryTerminates(monkeypatch: pytest.MonkeyPatch) -> None:
    """import 대상이 같은 탐색을 다시 불러도 무한히 돌지 않아야 한다."""

    calls: list[str] = []

    def _fake(name: str):
        calls.append(name)
        discoverOnce("registry.a", ["mod.one"])
        return object()

    monkeypatch.setattr("dartlab.core.pluginDiscovery.importlib.import_module", _fake)

    discoverOnce("registry.a", ["mod.one"])

    assert calls == ["mod.one"]


def testRealRegistryStillResolves() -> None:
    """실제 레지스트리가 여전히 provider 를 찾아야 한다. 배선이 끊기면 조용히 None 이 된다."""

    from dartlab.core import listingResolver

    listingResolver._discover()

    assert listingResolver._RESOLVER is not None
