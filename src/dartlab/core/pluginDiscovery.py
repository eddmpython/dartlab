"""L0 bootstrap registry와 caller-owned lazy module loader.

core registry는 구현체 모듈을 알지 않는다. root composition이 bootstrap callback을
등록하고, core seam은 자기 registry key만 요청한다. callback이 실패하면 완료 상태를
남기지 않아 다음 호출이 다시 시도하며, 예외는 원인 그대로 전파한다.
"""

from __future__ import annotations

import importlib
import threading
from collections.abc import Callable, Mapping
from typing import Any, TypeVar

_BOOTSTRAPS: dict[str, Callable[[], None]] = {}
_COMPLETED: set[str] = set()
_IN_PROGRESS: dict[str, int] = {}
_LOCK = threading.RLock()
_STATE_CHANGED = threading.Condition(_LOCK)

_T = TypeVar("_T", bound=Callable[..., Any])


def registerBootstrap(registryKey: str, callback: Callable[[], None]) -> None:
    """상위 composition이 L0 registry의 지연 초기화 callback을 등록한다."""
    if not registryKey or not registryKey.strip():
        raise ValueError("registryKey가 비어 있습니다")
    if not callable(callback):
        raise TypeError("bootstrap callback은 callable이어야 합니다")
    with _LOCK:
        if registryKey in _IN_PROGRESS:
            raise RuntimeError(f"실행 중 bootstrap callback은 교체할 수 없습니다: {registryKey}")
        previous = _BOOTSTRAPS.get(registryKey)
        _BOOTSTRAPS[registryKey] = callback
        if previous is not None and previous is not callback:
            _COMPLETED.discard(registryKey)


def bootstrap(registryKey: str) -> bool:
    """registryKey callback을 성공할 때까지 재시도 가능한 방식으로 한 번 실행한다.

    Returns:
        callback이 등록되어 실행됐거나 이미 완료됐으면 ``True``. composition이
        등록되지 않았으면 ``False``.

    Raises:
        callback 예외를 원인 그대로 전파한다. 실패한 key는 완료 처리하지 않는다.
    """
    threadId = threading.get_ident()
    with _STATE_CHANGED:
        while True:
            if registryKey in _COMPLETED:
                return True
            callback = _BOOTSTRAPS.get(registryKey)
            if callback is None:
                return False
            owner = _IN_PROGRESS.get(registryKey)
            if owner is None:
                _IN_PROGRESS[registryKey] = threadId
                break
            if owner == threadId:
                return False
            _STATE_CHANGED.wait()
    try:
        callback()
    except BaseException:
        with _STATE_CHANGED:
            _IN_PROGRESS.pop(registryKey, None)
            _STATE_CHANGED.notify_all()
        raise
    with _STATE_CHANGED:
        _IN_PROGRESS.pop(registryKey, None)
        _COMPLETED.add(registryKey)
        _STATE_CHANGED.notify_all()
    return True


def resetBootstrapState(registryKey: str | None = None) -> None:
    """bootstrap 완료 상태를 전체 또는 특정 key에 대해 초기화한다.

    실행 중 callback을 초기화하면 완료 여부가 뒤틀리므로 명시적으로 거부한다.
    callback 배선은 composition 소유이므로 이 함수가 제거하지 않는다.
    """
    with _LOCK:
        active = set(_IN_PROGRESS) if registryKey is None else {registryKey} & set(_IN_PROGRESS)
        if active:
            keys = ", ".join(sorted(active))
            raise RuntimeError(f"실행 중 bootstrap은 초기화할 수 없습니다: {keys}")
        if registryKey is None:
            _COMPLETED.clear()
        else:
            _COMPLETED.discard(registryKey)


def callerOwnedDynamicImport(func: _T) -> _T:
    """동적 module path가 L0가 아닌 호출자/entry point 소유임을 Guard에 선언한다."""
    return func


@callerOwnedDynamicImport
def importCallerModule(modulePath: str) -> Any:
    """호출자가 소유한 module path를 import한다."""
    if not modulePath or not modulePath.strip():
        raise ValueError("modulePath가 비어 있습니다")
    return importlib.import_module(modulePath)


def lazyAttribute(moduleName: str, lazyMap: Mapping[str, str], name: str) -> Any:
    """파사드의 명시적 lazy map에서 속성을 해석한다."""
    modulePath = lazyMap.get(name)
    if modulePath is None:
        raise AttributeError(f"module {moduleName!r} has no attribute {name!r}")
    return getattr(importCallerModule(modulePath), name)


__all__ = [
    "bootstrap",
    "callerOwnedDynamicImport",
    "importCallerModule",
    "lazyAttribute",
    "registerBootstrap",
    "resetBootstrapState",
]
