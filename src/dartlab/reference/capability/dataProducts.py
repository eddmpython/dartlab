"""Owner-local dataProduct provider discovery shared by capability consumers.

Provider module은 plain mapping만 노출한다. lower owner는 reference나 data를 import하지 않고,
상위 catalog consumer가 metadata를 읽는다. 중앙 엔진 이름 목록을 만들지 않는다.
"""

from __future__ import annotations

import importlib
import importlib.util
import pkgutil
from collections.abc import Mapping
from pathlib import Path
from typing import Any


def _filesystemProviderExists(moduleInfo: Any) -> bool | None:
    """FileFinder package에서 dataProduct module 존재 여부를 import 없이 확인한다."""

    finderPath = getattr(getattr(moduleInfo, "module_finder", None), "path", None)
    if not isinstance(finderPath, str):
        return None
    root = Path(finderPath)
    if not root.is_dir():
        return None
    package = root / str(moduleInfo.name)
    return (package / "dataProduct.py").is_file() or (package / "dataProduct" / "__init__.py").is_file()


def discoverDataProductProviders(
    *,
    layers: frozenset[str] | None = None,
) -> tuple[tuple[Mapping[str, Any], ...], tuple[str, ...]]:
    """Installed top-level package의 dataProduct mapping을 자동 발견한다.

    Args:
        layers: 포함할 optional architecture layer 집합.

    Returns:
        Owner 순으로 정렬된 descriptor와 안전한 discovery error tuple.

    Raises:
        없음. Provider별 import와 계약 오류는 error tuple로 격리한다.

    Example:
        ``providers, errors = discoverDataProductProviders(layers=frozenset({"L2"}))``.
    """
    import dartlab

    providers: list[Mapping[str, Any]] = []
    errors: list[str] = []
    for moduleInfo in pkgutil.iter_modules(dartlab.__path__):
        if not moduleInfo.ispkg:
            continue
        providerName = f"dartlab.{moduleInfo.name}.dataProduct"
        try:
            filesystemStatus = _filesystemProviderExists(moduleInfo)
            if filesystemStatus is False:
                continue
            if filesystemStatus is None and importlib.util.find_spec(providerName) is None:
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
    """Owner provider에서 axis registry target을 derived view로 만든다.

    Args:
        없음.

    Returns:
        Owner, registry module, attribute tuple의 정렬된 sequence.

    Raises:
        없음.

    Example:
        ``targets = axisRegistryTargets()``.
    """
    providers, _ = discoverDataProductProviders()
    targets = []
    for provider in providers:
        for registry in provider.get("registries", ()):
            targets.append((str(provider["owner"]), str(registry["module"]), str(registry["attribute"])))
    return tuple(sorted(targets))


def callableModuleTargets() -> dict[str, tuple[str, str | None]]:
    """Owner provider에서 root callable doc target을 derived view로 만든다.

    Args:
        없음.

    Returns:
        Owner에서 callable module과 optional attribute로 가는 mapping.

    Raises:
        없음.

    Example:
        ``targets = callableModuleTargets()``.
    """
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
