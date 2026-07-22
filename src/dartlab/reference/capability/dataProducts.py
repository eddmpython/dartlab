"""Owner-local dataProduct provider discovery shared by capability consumers.

Provider module은 plain mapping만 노출한다. lower owner는 reference나 data를 import하지 않고,
상위 catalog consumer가 metadata를 읽는다. 중앙 엔진 이름 목록을 만들지 않는다.
"""

from __future__ import annotations

import importlib
import importlib.util
import pkgutil
from collections.abc import Mapping
from typing import Any


def discoverDataProductProviders(
    *,
    layers: frozenset[str] | None = None,
) -> tuple[tuple[Mapping[str, Any], ...], tuple[str, ...]]:
    """Installed top-level package의 dataProduct mapping을 자동 발견한다."""
    import dartlab

    providers: list[Mapping[str, Any]] = []
    errors: list[str] = []
    for moduleInfo in pkgutil.iter_modules(dartlab.__path__):
        if not moduleInfo.ispkg:
            continue
        providerName = f"dartlab.{moduleInfo.name}.dataProduct"
        try:
            if importlib.util.find_spec(providerName) is None:
                continue
            module = importlib.import_module(providerName)
            descriptor = getattr(module, "DATA_PRODUCT_DESCRIPTOR", None)
            if not isinstance(descriptor, Mapping):
                raise TypeError("DATA_PRODUCT_DESCRIPTOR가 mapping이 아님")
            if descriptor.get("owner") != moduleInfo.name:
                raise ValueError("owner가 package 이름과 다름")
            if layers is not None and descriptor.get("layer") not in layers:
                continue
            providers.append(descriptor)
        except Exception as exc:
            errors.append(f"{providerName}:{type(exc).__name__}")
    return tuple(sorted(providers, key=lambda item: str(item["owner"]))), tuple(sorted(errors))


def axisRegistryTargets() -> tuple[tuple[str, str, str], ...]:
    """Owner provider에서 axis registry target을 derived view로 만든다."""
    providers, _ = discoverDataProductProviders()
    targets = []
    for provider in providers:
        for registry in provider.get("registries", ()):
            targets.append((str(provider["owner"]), str(registry["module"]), str(registry["attribute"])))
    return tuple(sorted(targets))


def callableModuleTargets() -> dict[str, tuple[str, str | None]]:
    """Owner provider에서 root callable doc target을 derived view로 만든다."""
    providers, _ = discoverDataProductProviders()
    targets: dict[str, tuple[str, str | None]] = {}
    for provider in providers:
        callableSpec = provider.get("callable")
        if not isinstance(callableSpec, Mapping):
            continue
        targets[str(provider["owner"])] = (
            str(callableSpec["module"]),
            str(callableSpec["attribute"]) if callableSpec.get("attribute") is not None else None,
        )
    return targets
