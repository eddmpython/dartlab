"""Production root and policy for immutable DataHub generations."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from dartlab.dataHub.pagingRuntime import MAX_PAGE_BYTES, dataHubRoot

from .contracts import MaintenanceBudget, MaterializationPolicy
from .store import MaterializationStore

MAINTENANCE_BUDGET = MaintenanceBudget(
    maxReaderLeases=8,
    maxGenerationTransitions=1,
    maxPageReferences=32,
    maxArtifacts=32,
)


def materializationRoot() -> Path:
    """공통 private DataHub root 아래 generation 저장 경로를 반환한다."""

    return dataHubRoot() / "materializations"


@lru_cache(maxsize=8)
def _cachedMaterializationStore(
    rootText: str,
    pageTimeoutMs: int,
) -> MaterializationStore:
    """동일 process의 root와 timeout 조합별 검증된 store를 재사용한다."""

    pageSeconds = pageTimeoutMs / 1000
    return MaterializationStore(
        Path(rootText),
        policy=MaterializationPolicy(
            maxPageRows=1,
            maxPageBytes=MAX_PAGE_BYTES,
            maxPageLogicalBytes=MAX_PAGE_BYTES,
            builderLeaseSeconds=max(300.0, pageSeconds * 2),
            readerLeaseSeconds=60.0,
        ),
    )


def materializationStore(
    *,
    pageTimeoutMs: int = 30_000,
    runMaintenance: bool = False,
) -> MaterializationStore:
    """Page deadline보다 긴 builder lease를 가진 production store를 재사용한다.

    ``runMaintenance`` 는 ``pagingRuntime.continuationStore`` 와 같은 계약이다. 공개 query
    진입 한 번마다 작은 bounded GC step 을 실행해 별도 스케줄러나 daemon 없이 expired
    reader, stale BUILDING, retention 초과 READY generation, unreferenced CAS 를 회수한다.
    page 읽기 경로는 이 flag 를 켜지 않는다. 켜지 않으면 ``readyRetentionSeconds`` 가 영원히
    발동하지 않아 원천 digest 가 바뀔 때마다 전종목 generation 사본이 누적된다.
    """

    if type(pageTimeoutMs) is not int or pageTimeoutMs <= 0:
        raise ValueError("pageTimeoutMs는 양의 int여야 합니다")
    store = _cachedMaterializationStore(
        str(materializationRoot()),
        pageTimeoutMs,
    )
    if runMaintenance:
        store.maintain(MAINTENANCE_BUDGET)
    return store
