"""Production root and policy for immutable Data Workbench generations."""

from __future__ import annotations

from pathlib import Path

from dartlab.data.pagingRuntime import MAX_PAGE_BYTES, workbenchRoot

from .contracts import MaterializationPolicy
from .store import MaterializationStore


def materializationRoot() -> Path:
    """공통 private workbench root 아래 generation 저장 경로를 반환한다."""

    return workbenchRoot() / "materializations"


def materializationStore(*, pageTimeoutMs: int = 30_000) -> MaterializationStore:
    """Page deadline보다 긴 builder lease를 가진 production store를 연다."""

    if type(pageTimeoutMs) is not int or pageTimeoutMs <= 0:
        raise ValueError("pageTimeoutMs는 양의 int여야 합니다")
    pageSeconds = pageTimeoutMs / 1000
    return MaterializationStore(
        materializationRoot(),
        policy=MaterializationPolicy(
            maxPageRows=1,
            maxPageBytes=MAX_PAGE_BYTES,
            maxPageLogicalBytes=MAX_PAGE_BYTES,
            builderLeaseSeconds=max(300.0, pageSeconds * 2),
            readerLeaseSeconds=60.0,
        ),
    )
