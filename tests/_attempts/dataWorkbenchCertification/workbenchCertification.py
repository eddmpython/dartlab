"""Descriptor 기반 selector planning을 검증하는 순수 attempt."""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True)
class SelectorContract:
    """Asset 하나의 선택자 입력 계약."""

    assetId: str
    selectorKind: Literal["none", "subject", "measure"] = "none"
    selectorRequired: bool = False


@dataclass(frozen=True, slots=True)
class SelectorPlan:
    """실행할 selector와 실행 전 gap."""

    selectors: tuple[tuple[tuple[str, str], ...], ...]
    gapCode: str | None = None


def planSelectors(
    contract: SelectorContract,
    *,
    subjects: tuple[str, ...] = (),
    measures: tuple[str, ...] = (),
    locatorOnly: bool = False,
) -> SelectorPlan:
    """Descriptor 계약만으로 bounded selector plan을 만든다."""

    if locatorOnly:
        return SelectorPlan(((),))
    values = subjects if contract.selectorKind == "subject" else measures if contract.selectorKind == "measure" else ()
    if values:
        key = contract.selectorKind
        return SelectorPlan(tuple(((key, value),) for value in values))
    if contract.selectorRequired:
        return SelectorPlan((), "MISSING_SELECTOR")
    return SelectorPlan(((),))


def executeWindow(
    tasks: tuple[tuple[str, Callable[[], object]], ...],
    *,
    maxConcurrency: int,
) -> tuple[tuple[str, object], ...]:
    """독립 실행은 병렬화하고 결과 순서는 입력 순서로 고정한다."""

    with ThreadPoolExecutor(max_workers=maxConcurrency) as pool:
        futures = tuple((taskId, pool.submit(call)) for taskId, call in tasks)
        return tuple((taskId, future.result()) for taskId, future in futures)
