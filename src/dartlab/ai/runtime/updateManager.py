"""설치형 런타임 업데이트 계획."""

from __future__ import annotations

from .installManager import InstallPlan, buildInstallPlan, executeInstallPlan


def buildUpdatePlan(runtimeId: str) -> InstallPlan:
    """Sig: buildUpdatePlan(runtimeId) -> InstallPlan.

    Args: runtimeId는 업데이트 대상이다.
    Returns: 설치와 같은 승인 가능한 최신화 계획이다.
    Raises: KeyError if runtimeId is unknown.
    Example: `plan = buildUpdatePlan("codex")`.
    """
    return buildInstallPlan(runtimeId)


def executeUpdatePlan(plan: InstallPlan, *, approvedDigest: str):
    """Sig: executeUpdatePlan(plan, *, approvedDigest) -> CompletedProcess[str].

    Args: 업데이트 계획과 승인 digest다.
    Returns: 실행 결과다.
    Raises: PermissionError or CalledProcessError on failure.
    Example: `executeUpdatePlan(plan, approvedDigest=plan.digest)`.
    """
    return executeInstallPlan(plan, approvedDigest=approvedDigest)
