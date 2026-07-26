"""Owner child process의 bounded protocol 상수와 immutable 결과 type."""

from __future__ import annotations

import re
import stat
from dataclasses import dataclass
from typing import Literal

_FORMAT_VERSION = 1
_ARTIFACT_ID_RE = re.compile(r"^[0-9a-f]{64}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_ERROR_CODE_RE = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")
_MAX_CONTROL_FRAMES = 2
_TERMINATE_PROBE_SECONDS = 0.05
_REPARSE_POINT = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x0400)

_STILL_ACTIVE = 259
_THREAD_QUERY_LIMITED_INFORMATION = 0x0800
_PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
_PROCESS_SET_QUOTA = 0x0100
_PROCESS_TERMINATE = 0x0001
_JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9
_JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000

OwnerProcessStatus = Literal[
    "ok",
    "budgetRejected",
    "timedOut",
    "protocolFailed",
    "childFailed",
    "artifactFailed",
    "jobFailed",
    "cleanupFailed",
]


class _ProtocolViolation(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class OwnerProcessPage:
    """Parent가 검증한 한 owner page artifact를 보존한다.

    Capabilities:
        Arrow payload와 child claim을 parent 검증 결과로 결박한다.

    Args:
        모든 field는 ``runOwnerPage`` 성공 경로에서만 구성한다.

    Returns:
        Immutable page bytes와 row, byte, digest 사실을 제공한다.

    Raises:
        Dataclass 생성 자체는 별도 검증 오류를 발생시키지 않는다.

    Example:
        ``page.payloadDigest == hashlib.sha256(page.payload).hexdigest()``.

    Guide:
        Continuation store에는 이 객체의 payload와 row count만 전달한다.

    When:
        Child 종료, 파일 크기와 digest, outer Arrow schema 검증 뒤 생성한다.

    How:
        Parent가 자신이 지정한 artifact 경로를 직접 읽어 구성한다.

    See Also:
        ``OwnerProcessOutcome``.

    Requires:
        Payload는 owner page의 bounded outer Arrow IPC여야 한다.

    AI Context:
        이 객체는 process 사이에서 pickle되지 않고 parent 안에서만 생성된다.
    """

    payload: bytes
    rowCount: int
    byteCount: int
    payloadDigest: str


@dataclass(frozen=True, slots=True)
class OwnerProcessOutcome:
    """한 page child 실행과 정리의 parent 관측 증거를 보존한다.

    Capabilities:
        Status, deadline, IPC, Job Object, process와 worker liveness를 함께 기록한다.

    Args:
        모든 field는 ``runOwnerPage``가 parent 관측값으로 구성한다.

    Returns:
        성공 page 또는 실패 code와 zero-live 증거를 제공한다.

    Raises:
        Dataclass 생성 자체는 별도 검증 오류를 발생시키지 않는다.

    Example:
        ``outcome.status == "ok" and outcome.zeroLive``.

    Guide:
        성공 여부와 무관하게 ``zeroLive``를 release gate로 사용한다.

    When:
        Spawn 전 budget 거부 또는 child와 artifact 정리가 끝난 뒤 반환한다.

    How:
        Parent의 monotonic clock과 Windows liveness API 관측만 기록한다.

    See Also:
        ``OwnerProcessPage``과 ``runOwnerPage``.

    Requires:
        Spawn된 경로는 반환 전에 terminate, kill, Job close, join을 마쳐야 한다.

    AI Context:
        ``cleanupTrace``는 계획이 아니라 실제 호출 순서를 나타낸다.
    """

    status: OwnerProcessStatus
    page: OwnerProcessPage | None
    spawned: bool
    pid: int | None
    threadNativeId: int | None
    publicDeadline: float
    workDeadline: float
    readySeconds: float | None
    elapsedSeconds: float
    deadlineOvershootSeconds: float
    ipcFrameCount: int
    ipcByteCount: int
    cleanupTrace: tuple[str, ...]
    zeroLive: bool
    jobObjectAttempted: bool
    jobObjectAssigned: bool
    jobObjectError: str | None
    errorCode: str | None
