"""calc 함수 메모이제이션 — Company._cache 공유.

analysis()와 review()가 같은 calc 함수를 호출할 때
두 번째 호출은 캐시에서 즉시 반환한다.

Usage::

    from dartlab.analysis.financial._memoize import memoized_calc

    @memoized_calc
    def calcMarginTrend(company, *, basePeriod=None):
        ...
"""

from __future__ import annotations

import functools
from typing import Any, Callable


def memoized_calc(fn: Callable[..., Any]) -> Callable[..., Any]:
    """calc 함수 결과를 Company._cache에 메모이제이션.

    - key: ``_{함수명}:{basePeriod}``
    - Company._cache(BoundedCache)가 없으면 캐시 없이 실행.
    - 결과가 None이어도 캐시한다 (재계산 방지).
    """

    import inspect

    _has_base_period = "basePeriod" in inspect.signature(fn).parameters

    @functools.wraps(fn)
    def wrapper(company: Any, *, basePeriod: str | None = None) -> Any:
        cache = getattr(company, "_cache", None)
        key = f"_{fn.__name__}:{basePeriod}"

        if cache is not None and key in cache:
            return cache[key]

        if _has_base_period:
            result = fn(company, basePeriod=basePeriod)
        else:
            result = fn(company)

        if cache is not None:
            cache[key] = result

        return result

    return wrapper
