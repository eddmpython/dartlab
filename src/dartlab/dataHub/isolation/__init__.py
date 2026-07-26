"""자식 프로세스 격리 계층.

owner page 와 eager seal 은 각각 fresh spawn 자식에서 실행한다. Windows 는 Job Object
kill-on-close, POSIX 는 process group 봉쇄로 손자까지 회수하고, sandbox 가 write 와
network 를 fail-closed 로 막는다. 부모는 cursor 와 commit 만 소유한다.
"""

from __future__ import annotations

from dartlab.dataHub.isolation.eagerProcess import (
    EagerSeal,
    eagerCodePin,
    eagerResultAt,
    packEagerSeal,
    unpackEagerSeal,
    validateEagerSeal,
)
from dartlab.dataHub.isolation.eagerSandbox import (
    EagerSandboxViolation,
    enforceEagerSandbox,
    enforceProcessSandbox,
)
from dartlab.dataHub.isolation.eagerSupervisor import (
    EagerProcessOutcome,
    runEagerSeal,
)
from dartlab.dataHub.isolation.ownerProcess import runOwnerPage
from dartlab.dataHub.isolation.ownerProcessModels import (
    OwnerProcessOutcome,
    OwnerProcessPage,
)
from dartlab.dataHub.isolation.processLifecycle import (
    becomeProcessGroupLeader,
    processGroupAlive,
    stopProcessGroup,
    waitProcessGroupZero,
)

__all__ = [
    "EagerProcessOutcome",
    "EagerSandboxViolation",
    "EagerSeal",
    "OwnerProcessOutcome",
    "OwnerProcessPage",
    "becomeProcessGroupLeader",
    "eagerCodePin",
    "eagerResultAt",
    "enforceEagerSandbox",
    "enforceProcessSandbox",
    "packEagerSeal",
    "processGroupAlive",
    "runEagerSeal",
    "runOwnerPage",
    "stopProcessGroup",
    "unpackEagerSeal",
    "validateEagerSeal",
    "waitProcessGroupZero",
]
