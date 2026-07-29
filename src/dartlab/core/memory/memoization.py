"""Company 계산 cache key와 signature-preserving single-flight decorator."""

from __future__ import annotations

import functools
import hashlib
import inspect
import threading
from collections.abc import Callable, MutableMapping
from typing import Any

from dartlab.core.memory.cache import _CACHE_MISSING, BoundedCache

_ownerLock = threading.Lock()
_ownersByName: dict[str, set[str]] = {}


def _semanticDigest(
    bound: inspect.BoundArguments,
) -> str:
    semantic = tuple(
        (name, repr(value))
        for name, value in bound.arguments.items()
        if name not in {"company", "self", "overrides", "basePeriod"}
    )
    if not semantic:
        return ""
    payload = repr(semantic).encode("utf-8")
    return hashlib.blake2b(payload, digest_size=10).hexdigest()


def memoizedCalc(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Company 계산 결과를 의미 인자와 owner별로 안전하게 메모이제이션한다.

    Capabilities:
        임의 함수 signature 전달, owner namespace, 의미 인자 key, atomic hit와
        BoundedCache single-flight를 제공한다.
    AIContext:
        analysis·credit·quant의 166개 계산이 같은 Company cache를 안전하게 공유한다.
    Guide:
        ``overrides``가 truthy면 가정값 오염을 막기 위해 cache를 우회한다.
    When:
        Company를 첫 인자로 받고 결정론적 결과를 만드는 비싼 계산 함수에 적용한다.
    How:
        기존 단순 함수 key는 보존하고 동명 owner나 추가 의미 인자만 namespace/digest를 붙인다.
    Requires:
        첫 인자는 ``_cache``를 선택적으로 가진 Company 호환 객체여야 한다.
    Raises:
        원본 함수, signature binding 또는 cache가 낸 예외를 그대로 전달한다.
    Args:
        fn: 메모이제이션할 callable.
    Returns:
        원본 signature와 metadata를 보존한 callable.
    Example:
        >>> @memoizedCalc
        ... def calc(company, *, basePeriod=None):
        ...     return 1
    SeeAlso:
        BoundedCache.getOrCreate
    """
    signature = inspect.signature(fn)
    parameters = signature.parameters
    hasBasePeriod = "basePeriod" in parameters
    hasOverrides = "overrides" in parameters
    owner = f"{fn.__module__}.{fn.__qualname__}"
    with _ownerLock:
        owners = _ownersByName.setdefault(fn.__name__, set())
        owners.add(owner)

    @functools.wraps(fn)
    def _wrapper(company: Any, *args: Any, **kwargs: Any) -> Any:
        bound = signature.bind(company, *args, **kwargs)
        bound.apply_defaults()
        overrides = bound.arguments.get("overrides") if hasOverrides else None
        if overrides:
            return fn(company, *args, **kwargs)

        cache = getattr(company, "_cache", None)
        if cache is None:
            return fn(company, *args, **kwargs)
        if not isinstance(cache, (BoundedCache, MutableMapping)):
            return fn(company, *args, **kwargs)

        basePeriod = bound.arguments.get("basePeriod") if hasBasePeriod else None
        namespace = owner if len(owners) > 1 else fn.__name__
        digest = _semanticDigest(bound)
        suffix = f":{basePeriod}" if not digest else f":{basePeriod}:{digest}"
        key = f"_{namespace}{suffix}"

        def _build() -> Any:
            return fn(company, *args, **kwargs)

        if isinstance(cache, BoundedCache):
            return cache.getOrCreate(key, _build)

        cached = cache.get(key, _CACHE_MISSING)
        if cached is not _CACHE_MISSING:
            return cached
        result = _build()
        if result is not None:
            cache[key] = result
        return result

    return _wrapper


__all__ = ["memoizedCalc"]
