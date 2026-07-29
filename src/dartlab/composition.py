"""DartLab built-in 구현체의 lazy composition root.

L0는 Protocol과 registry만 소유한다. 이 모듈이 구체 gather/providers/viz 구현 경로를
소유하고 callback을 주입하므로, core에는 상위 모듈명이나 import가 남지 않는다.
"""

from __future__ import annotations

import importlib
import threading
from collections.abc import Callable

from dartlab.core.pluginDiscovery import registerBootstrap

_CONFIGURED = False
_LOCK = threading.Lock()


def _moduleBootstrap(*moduleNames: str) -> Callable[[], None]:
    """모듈 import 자체가 core registry 등록을 수행하는 callback을 만든다."""

    def load() -> None:
        """선언된 구현 모듈을 순서대로 불러 registry 등록 부작용을 실행한다."""
        for moduleName in moduleNames:
            importlib.import_module(moduleName)

    return load


def _financeAccessorBootstrap() -> None:
    from dartlab.core.di import setFinanceAccessor
    from dartlab.gather.accessors import DefaultFinanceAccessor

    setFinanceAccessor(DefaultFinanceAccessor())


def _quantAccessorBootstrap() -> None:
    from dartlab.core.di import setQuantAccessor
    from dartlab.gather.accessors import DefaultQuantAccessor

    setQuantAccessor(DefaultQuantAccessor())


def _industryAccessorBootstrap() -> None:
    from dartlab.core.di import setIndustryAccessor
    from dartlab.gather.accessors import DefaultIndustryAccessor

    setIndustryAccessor(DefaultIndustryAccessor())


def _macroProviderBootstrap() -> None:
    from dartlab.core.di import setMacroProvider
    from dartlab.gather.macroProvider import DefaultMacroProvider

    setMacroProvider(DefaultMacroProvider())


_MODULE_BOOTSTRAPS: dict[str, tuple[str, ...]] = {
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

_FACTORY_BOOTSTRAPS: dict[str, Callable[[], None]] = {
    "dartlab.core.di:finance": _financeAccessorBootstrap,
    "dartlab.core.di:quant": _quantAccessorBootstrap,
    "dartlab.core.di:industry": _industryAccessorBootstrap,
    "dartlab.core.di:macro": _macroProviderBootstrap,
}


def configureBuiltins() -> None:
    """내장 구현의 lazy callback을 L0 registry key에 한 번 등록한다."""
    global _CONFIGURED
    with _LOCK:
        if _CONFIGURED:
            return
        for registryKey, moduleNames in _MODULE_BOOTSTRAPS.items():
            registerBootstrap(registryKey, _moduleBootstrap(*moduleNames))
        for registryKey, callback in _FACTORY_BOOTSTRAPS.items():
            registerBootstrap(registryKey, callback)
        _CONFIGURED = True


__all__ = ["configureBuiltins"]
