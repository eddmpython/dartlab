"""Data Workbench pageable owner가 공유하는 continuation runtime."""

from __future__ import annotations

import math
import os
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from dartlab.data.continuation import (
    ArrowPayloadFacts,
    ContinuationError,
    ContinuationMaintenanceBudget,
    ContinuationPolicy,
    ContinuationStore,
)

MAX_PAGE_ROWS = 100_000
MAX_PAGE_BYTES = 64 * 1024 * 1024
MAX_STATE_BYTES = 512 * 1024
MAX_OWNER_PROCESS_REQUEST_BYTES = 768 * 1024
MAX_OWNER_PROCESS_CONTROL_FRAME_BYTES = 8 * 1024
MAX_OWNER_PROCESS_CONTROL_BYTES = 16 * 1024
OWNER_PROCESS_CLEANUP_GRACE_SECONDS = 0.5
MIN_OWNER_PROCESS_WORK_SECONDS = 8.0
TOKEN_TTL_SECONDS = 24 * 60 * 60
MAINTENANCE_BUDGET = ContinuationMaintenanceBudget(
    maxChains=1,
    maxRootScans=1,
    maxContinuationRows=32,
    maxLedgerScans=32,
    maxCasPrefixes=1,
    maxCasEntries=32,
    maxArtifactDeletes=32,
)


def workbenchRoot() -> Path:
    """Continuation, manifest, materialization이 공유하는 private root를 반환한다.

    Capabilities:
        모든 pageable owner와 immutable generation이 같은 private root를 사용하게 한다.

    Args:
        없음.

    Returns:
        ``DARTLAB_HOME`` 아래의 absolute private workbench 경로.

    Raises:
        없음.

    Example:
        ``root = workbenchRoot()``.

    Guide:
        Caller는 이 경로 아래에 기능별 고정 하위 디렉터리만 추가한다.

    When:
        Continuation store, manifest cache, process artifact, generation 경로를 만들 때 사용한다.

    How:
        ``DARTLAB_HOME`` 또는 사용자 home 아래의 고정 이름을 결합한다.

    See Also:
        ``continuationStore``과 ``ownerProcessArtifactRoot``.

    Requires:
        ``DARTLAB_HOME``을 사용하면 parent와 child가 같은 값을 상속해야 한다.

    AI Context:
        이 root는 private control plane과 immutable materialization CAS의 공통 경계다.
    """

    configured = os.getenv("DARTLAB_HOME")
    home = Path(configured).expanduser() if configured else Path.home() / ".dartlab"
    return Path(os.path.abspath(home / "data-workbench"))


def manifestCachePath(
    assetId: str,
    category: str,
    *,
    create: bool = True,
) -> Path:
    """Resource full-manifest cache의 stable private 경로를 만든다.

    Capabilities:
        Resource identity를 원문 노출 없는 canonical digest 경로로 바꾼다.

    Args:
        assetId: Stable resource asset ID.
        category: DATA_RELEASES category.
        create: ``True``면 cache parent를 만들고, ``False``면 경로만 유도한다.

    Returns:
        Asset과 category identity에서 유도한 JSON cache 경로.

    Raises:
        TypeError: Identity가 canonical JSON으로 표현되지 않을 때.

    Example:
        ``manifestCachePath("resource.edgar", "edgar")``.

    Guide:
        Asset ID와 category를 filename에 직접 넣지 않는다.

    When:
        Resource source pin과 shard payload를 검증할 때 사용한다.

    How:
        두 identity의 canonical digest를 manifest cache filename으로 사용한다.

    See Also:
        ``workbenchRoot``.

    Requires:
        두 identity는 canonical JSON으로 표현할 수 있어야 한다.

    AI Context:
        Cache는 source identity 검증 보조물이며 factor 결과 저장소가 아니다.
    """

    from dartlab.data.continuation import canonicalDigest

    root = workbenchRoot() / "manifest-cache"
    if type(create) is not bool:
        raise TypeError("manifest cache create는 bool이어야 합니다")
    if create:
        root.mkdir(parents=True, exist_ok=True)
    identity = canonicalDigest({"assetId": assetId, "category": category})
    return root / f"{identity}.json"


def ownerProcessArtifactRoot() -> Path:
    """계산형 owner page 자식이 쓰는 private 임시 artifact root를 반환한다.

    Capabilities:
        Continuation control root 아래에서 process artifact 전용 경로를 고정한다.

    Args:
        없음.

    Returns:
        Parent와 spawn child가 같은 방식으로 유도하는 absolute 경로.

    Raises:
        없음. 경로의 생성과 보안 검증은 process supervisor가 수행한다.

    Example:
        ``root = ownerProcessArtifactRoot()``.

    Guide:
        이 경로의 파일은 continuation commit 전에만 존재하는 임시 산출물이다.

    When:
        Owner page process를 시작하거나 종료 후 임시 파일을 회수할 때 사용한다.

    How:
        기존 workbench continuation root에 고정된 하위 디렉터리를 결합한다.

    See Also:
        ``continuationStore``.

    Requires:
        Parent와 child가 같은 ``DARTLAB_HOME`` 환경을 상속해야 한다.

    AI Context:
        이 경로는 영구 factor 저장소가 아니며 성공과 실패 모두에서 파일을 지운다.
    """

    return workbenchRoot() / "continuations" / "owner-process"


def requireDeadline(deadline: float) -> float:
    """Monotonic deadline의 남은 양수 초를 검증해 반환한다.

    Capabilities:
        모든 pageable owner의 timeout 판정을 한 monotonic clock으로 통일한다.

    Args:
        deadline: ``time.perf_counter()`` 기준 절대 deadline.

    Returns:
        현재부터 deadline까지 남은 양수 초.

    Raises:
        ContinuationError: 값이 유효하지 않거나 이미 만료됐을 때.

    Example:
        ``remaining = requireDeadline(deadline)``.

    Guide:
        Blocking 호출 직전과 직후에 반복 호출해 deadline을 재검증한다.

    When:
        Store, source 검증, page 계산의 bounded wait를 시작할 때 사용한다.

    How:
        ``time.perf_counter``와 절대 deadline의 차이를 계산한다.

    See Also:
        ``continuationStore``.

    Requires:
        Deadline은 같은 host monotonic clock에서 계산한 유한한 숫자여야 한다.

    AI Context:
        Wall clock 변경은 continuation timeout 판정에 영향을 주지 않는다.
    """

    if type(deadline) not in {int, float} or not math.isfinite(deadline):
        raise ContinuationError("CONTINUATION_TIMEOUT")
    remaining = float(deadline) - time.perf_counter()
    if remaining <= 0:
        raise ContinuationError("CONTINUATION_TIMEOUT")
    return remaining


def continuationStore(
    *,
    deadline: float,
    payloadValidator: Callable[..., ArrowPayloadFacts],
    runMaintenance: bool = True,
) -> ContinuationStore:
    """공유 ledger를 owner별 Arrow payload validator와 결합한다.

    Capabilities:
        공통 정책과 private root를 owner별 payload schema 검증에 결합한다.

    Args:
        deadline: Store 생성과 maintenance의 monotonic deadline.
        payloadValidator: Owner outer Arrow envelope validator.
        runMaintenance: 작은 bounded cleanup step 실행 여부.

    Returns:
        Resource와 계산 owner가 같은 root에서 사용하는 continuation store.

    Raises:
        ContinuationError: Deadline, private storage 또는 maintenance가 실패할 때.

    Example:
        ``store = continuationStore(deadline=deadline, payloadValidator=validator)``.

    Guide:
        한 public 호출에서 maintenance는 첫 store 생성 때만 실행한다.

    When:
        Continuation issue, context load, redeem, replay를 수행할 때 사용한다.

    How:
        남은 deadline에서 wait 정책을 만들고 bounded maintenance를 선택 실행한다.

    See Also:
        ``requireDeadline``과 ``workbenchRoot``.

    Requires:
        Payload validator는 owner outer Arrow 계약을 fail-closed로 검증해야 한다.

    AI Context:
        Resource page와 계산 owner page는 ledger를 공유하지만 schema는 분리된다.
    """

    remaining = requireDeadline(deadline)
    waitSeconds = min(30.0, remaining)
    policy = ContinuationPolicy(
        maxPageRows=MAX_PAGE_ROWS,
        maxPageBytes=MAX_PAGE_BYTES,
        maxPageLogicalBytes=MAX_PAGE_BYTES,
        maxStateBytes=MAX_STATE_BYTES,
        tokenTtlSeconds=TOKEN_TTL_SECONDS,
        waitSeconds=waitSeconds,
        pollSeconds=min(0.01, waitSeconds),
    )
    store = ContinuationStore(
        workbenchRoot() / "continuations",
        policy=policy,
        payloadValidator=payloadValidator,
    )
    if runMaintenance:
        store.maintain(MAINTENANCE_BUDGET)
        requireDeadline(deadline)
    return store


__all__ = [
    "MAX_PAGE_BYTES",
    "MAX_PAGE_ROWS",
    "MAX_STATE_BYTES",
    "MAX_OWNER_PROCESS_CONTROL_BYTES",
    "MAX_OWNER_PROCESS_CONTROL_FRAME_BYTES",
    "MAX_OWNER_PROCESS_REQUEST_BYTES",
    "MIN_OWNER_PROCESS_WORK_SECONDS",
    "OWNER_PROCESS_CLEANUP_GRACE_SECONDS",
    "continuationStore",
    "manifestCachePath",
    "ownerProcessArtifactRoot",
    "requireDeadline",
    "workbenchRoot",
]
