"""root composition과 L0 registry seam 배선 회귀."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from dartlab import composition
from dartlab.core import pluginDiscovery

pytestmark = [pytest.mark.unit]

REPO_ROOT = Path(__file__).resolve().parents[2]


def testBuiltinCompositionOwnsEveryConcreteModulePath() -> None:
    """core 밖 concrete 구현 경로는 composition의 선언 표 한 곳에만 있다."""
    assert composition._MODULE_BOOTSTRAPS == {
        "dartlab.core.credentials": ("dartlab.gather.dart.keys",),
        "dartlab.core.dartBuild": ("dartlab.providers.dart.build",),
        "dartlab.core.dartClient": ("dartlab.gather.dart.client",),
        "dartlab.core.disclosureFetcher": ("dartlab.providers.dart.company",),
        "dartlab.core.edgarBuild": ("dartlab.providers.edgar.buildSeam",),
        "dartlab.core.edgarClient": ("dartlab.gather.edgar.client",),
        "dartlab.core.gatherProvider": ("dartlab.gather.entry",),
        "dartlab.core.htmlRenderer": ("dartlab.viz.display.htmlRenderer",),
        "dartlab.core.insiderRawProvider": ("dartlab.providers.dart.ops.insiderTrades",),
        "dartlab.core.listingResolver": ("dartlab.gather.krx.listing",),
        "dartlab.core.loaders": (
            "dartlab.providers.edgar.docs.loader",
            "dartlab.providers.edgar.bulk",
        ),
        "dartlab.core.panelTableAccessor": ("dartlab.providers.dart.parse.panelExportGrid",),
        "dartlab.core.render": ("dartlab.viz",),
    }
    expectedKeys = set(composition._MODULE_BOOTSTRAPS) | set(composition._FACTORY_BOOTSTRAPS)
    assert expectedKeys <= set(pluginDiscovery._BOOTSTRAPS)


def testModuleBootstrapPreservesOrderAndPropagatesFailure(monkeypatch: pytest.MonkeyPatch) -> None:
    """복수 구현 bootstrap은 선언 순서로 실행하며 중간 오류를 삼키지 않는다."""
    loaded: list[str] = []

    def load(moduleName: str):
        loaded.append(moduleName)
        if moduleName == "broken":
            raise ImportError("broken implementation")
        return object()

    monkeypatch.setattr(composition.importlib, "import_module", load)
    callback = composition._moduleBootstrap("first", "broken", "never")

    with pytest.raises(ImportError, match="broken implementation"):
        callback()
    assert loaded == ["first", "broken"]


def testFactoryBootstrapCanRecreateDefaultAfterReset() -> None:
    """DI setter의 ``None`` reset 뒤 기본 구현을 새 인스턴스로 다시 만든다."""
    from dartlab.core import di

    registryKey = "dartlab.core.di:finance"
    original = di._financeAccessor
    wasCompleted = registryKey in pluginDiscovery._COMPLETED
    try:
        di.setFinanceAccessor(None)
        first = di.getFinanceAccessor()
        di.setFinanceAccessor(None)
        second = di.getFinanceAccessor()
        assert type(second) is type(first)
        assert second is not first
    finally:
        di._financeAccessor = original
        if wasCompleted:
            pluginDiscovery._COMPLETED.add(registryKey)
        else:
            pluginDiscovery._COMPLETED.discard(registryKey)


def testPaletteCompatibilitySurfaceSharesL0Objects() -> None:
    """viz 호환 경로가 L0 palette를 복제하지 않고 같은 객체를 노출한다."""
    from dartlab.core import palette as corePalette
    from dartlab.viz import palette as vizPalette

    assert vizPalette.COLORS is corePalette.COLORS
    assert vizPalette.INTENT_MAP is corePalette.INTENT_MAP
    assert vizPalette.TONE_MAP is corePalette.TONE_MAP
    assert vizPalette.resolveColor(intent="positive") == corePalette.COLORS[3]


def testAllBuiltInSeamsResolveInFreshProcess() -> None:
    """fresh process에서 모든 내장 registry가 실제 구현체를 찾아야 한다."""
    script = """
from dartlab.core.credentials import listCredentialProviders
from dartlab.core.dartBuild import getDartBuildProvider
from dartlab.core.dartClient import getDartFetchProvider
from dartlab.core.disclosureFetcher import getDisclosureFetcher
from dartlab.core.edgarBuild import getEdgarBuildProvider
from dartlab.core.edgarClient import getEdgarFetchProvider
from dartlab.core.gatherProvider import getGatherProvider
from dartlab.core.htmlRenderer import getHtmlRenderer
from dartlab.core.insiderRawProvider import getInsiderRawProvider
from dartlab.core.listingResolver import getListingResolver
from dartlab.core.loaders import listLoaders
from dartlab.core.panelTableAccessor import getPanelTableAccessor
from dartlab.core.render import getRenderer
from dartlab.core.di import (
    getFinanceAccessor,
    getIndustryAccessor,
    getMacroProvider,
    getQuantAccessor,
)

assert "dart_api_key" in listCredentialProviders()
assert getDartBuildProvider() is not None
assert getDartFetchProvider() is not None
assert getDisclosureFetcher() is not None
assert getEdgarBuildProvider() is not None
assert getEdgarFetchProvider() is not None
assert getGatherProvider() is not None
assert getHtmlRenderer() is not None
assert getInsiderRawProvider() is not None
assert getListingResolver() is not None
assert {"edgar", "edgarDocs"} <= set(listLoaders())
assert getPanelTableAccessor() is not None
assert getRenderer() is not None
assert getFinanceAccessor() is not None
assert getQuantAccessor() is not None
assert getIndustryAccessor() is not None
assert getMacroProvider() is not None
"""
    result = subprocess.run(
        [sys.executable, "-X", "utf8", "-c", script],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
