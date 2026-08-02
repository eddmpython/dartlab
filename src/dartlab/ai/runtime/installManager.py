"""명시적 승인 뒤에만 실행되는 CLI 설치 계획."""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import asdict, dataclass

from .contracts import RuntimeDescriptor
from .registry import loadRuntimeRegistry


@dataclass(frozen=True)
class InstallPlan:
    """설치 실행 전에 사용자에게 보여 줄 결정론적 계획."""

    runtimeId: str
    argv: tuple[str, ...]
    officialUrl: str
    digest: str

    def toDict(self) -> dict[str, object]:
        """Sig: toDict() -> dict[str, object].

        Args: 없음.
        Returns: 설치 승인 UI용 dict다.
        Example: `plan.toDict()["digest"]`.
        """
        return asdict(self)


def buildInstallPlan(runtimeId: str) -> InstallPlan:
    """Sig: buildInstallPlan(runtimeId) -> InstallPlan.

    Args: runtimeId는 설치 대상 런타임이다.
    Returns: argv와 무결성 digest를 가진 계획이다.
    Raises: KeyError if runtimeId is unknown.
    Example: `plan = buildInstallPlan("cline")`.
    """
    descriptor: RuntimeDescriptor = loadRuntimeRegistry()[runtimeId]
    canonical = json.dumps(
        {"runtimeId": runtimeId, "argv": descriptor.installArgs, "officialUrl": descriptor.officialUrl},
        separators=(",", ":"),
        ensure_ascii=False,
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return InstallPlan(runtimeId, descriptor.installArgs, descriptor.officialUrl, digest)


def executeInstallPlan(plan: InstallPlan, *, approvedDigest: str) -> subprocess.CompletedProcess[str]:
    """Sig: executeInstallPlan(plan, *, approvedDigest) -> CompletedProcess[str].

    Args: plan과 사용자가 승인한 동일 digest를 받는다.
    Returns: 설치 프로세스 완료 결과다.
    Raises: PermissionError if digest differs; CalledProcessError on install failure.
    Example: `executeInstallPlan(plan, approvedDigest=plan.digest)`.
    """
    current = buildInstallPlan(plan.runtimeId)
    if approvedDigest != plan.digest or current != plan:
        raise PermissionError("설치 계획 digest가 현재 계획과 일치하지 않습니다")
    return subprocess.run(
        list(plan.argv),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
        shell=False,
        check=True,
    )
