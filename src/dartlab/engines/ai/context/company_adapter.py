"""Facade adapter helpers for AI runtime.

AI layer는 `dartlab.Company` facade와 엔진 내부 구현 차이를 직접 알지 않는다.
이 모듈에서 headline ratios / ratio series 같은 surface 차이를 흡수한다.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

_ADAPTER_ERRORS = (
    AttributeError,
    KeyError,
    OSError,
    RuntimeError,
    TypeError,
    ValueError,
)


def get_headline_ratios(company: Any) -> Any | None:
    """Return RatioResult-like object regardless of facade surface."""
    getter = getattr(company, "getRatios", None)
    if callable(getter):
        try:
            result = getter()
            if result is not None and hasattr(result, "roe"):
                return result
        except _ADAPTER_ERRORS:
            pass

    finance = getattr(company, "finance", None)
    finance_getter = getattr(finance, "getRatios", None)
    if callable(finance_getter):
        try:
            result = finance_getter()
            if result is not None and hasattr(result, "roe"):
                return result
        except _ADAPTER_ERRORS:
            pass

    for candidate in (
        getattr(company, "ratios", None),
        getattr(finance, "ratios", None),
    ):
        if candidate is not None and hasattr(candidate, "roe"):
            return candidate

    return None


def get_ratio_series(company: Any) -> Any | None:
    """Return attribute-style ratio series regardless of tuple/object surface."""
    for candidate in (
        getattr(company, "ratioSeries", None),
        getattr(getattr(company, "finance", None), "ratioSeries", None),
    ):
        if candidate is None:
            continue
        if hasattr(candidate, "roe"):
            return candidate
        if isinstance(candidate, tuple) and len(candidate) == 2:
            series, periods = candidate
            if not isinstance(series, dict):
                continue
            ratio_series = series.get("RATIO", {})
            if not isinstance(ratio_series, dict) or not ratio_series:
                continue
            adapted = SimpleNamespace(periods=periods)
            for key, values in ratio_series.items():
                setattr(adapted, key, values)
            return adapted
    return None
