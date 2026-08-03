"""설치·공식 로그인·DartLab MCP·기본 런타임을 한 번에 준비한다."""

from __future__ import annotations

import os
import shutil
import subprocess
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from typing import Any

from .discovery import runtimeLoginArgv
from .installManager import InstallPlan, buildInstallPlan, executeInstallPlan
from .mcpBootstrap import McpConnectPlan, buildMcpConnectPlan, executeMcpConnectPlan

_SUPPORTED_SETUP_RUNTIMES = ("codex", "claude")


@dataclass(frozen=True)
class PrerequisitePlan:
    """에이전트 CLI 패키지 관리자를 같은 setup에서 준비하는 계획."""

    key: str
    displayName: str
    argv: tuple[str, ...]


@dataclass(frozen=True)
class SetupPlan:
    """한 번의 사용자 승인으로 수행할 setup 범위."""

    runtimeId: str
    displayName: str
    changes: tuple[str, ...]
    requiresLogin: bool
    prerequisitePlan: PrerequisitePlan | None = None
    installPlan: InstallPlan | None = None
    mcpPlan: McpConnectPlan | None = None
    alreadyReady: bool = False

    @property
    def approvalRequired(self) -> bool:
        """DartLab이 시스템 또는 사용자 설정을 변경하는지 반환한다."""
        return bool(self.prerequisitePlan or self.installPlan or self.mcpPlan or ("DartLab MCP 연결" in self.changes))

    def toDict(self) -> dict[str, Any]:
        """설치 계획과 단일 승인 필요 여부를 공개 응답 사전으로 변환한다."""
        value = asdict(self)
        value["approvalRequired"] = self.approvalRequired
        return value


@dataclass(frozen=True)
class SetupStep:
    """setup 한 단계의 공개 진행 상태."""

    key: str
    status: str
    detail: str


@dataclass(frozen=True)
class SetupResult:
    """기술 준비와 투자 분석 준비를 함께 알리는 최종 영수증."""

    runtimeId: str
    state: str
    investmentReady: bool
    mutationCount: int
    approvalCount: int
    steps: tuple[SetupStep, ...] = field(default_factory=tuple)
    readiness: dict[str, Any] = field(default_factory=dict)
    nextAction: str | None = None

    def toDict(self) -> dict[str, Any]:
        """준비 결과와 단계별 영수증을 공개 응답 사전으로 변환한다."""
        return asdict(self)


@dataclass
class _SetupProgress:
    """setup 단계 사이에서 현재 probe와 공개 영수증 상태를 운반한다."""

    engine: Any
    plan: SetupPlan
    observer: Callable[[SetupStep], None] | None = None
    steps: list[SetupStep] = field(default_factory=list)
    current: dict[str, Any] = field(default_factory=dict)
    mutationCount: int = 0
    approvalCount: int = 0

    def record(self, key: str, status: str, detail: str) -> None:
        """준비 단계의 상태를 누적하고 등록된 관찰자에게 전달한다."""
        step = SetupStep(key, status, detail)
        self.steps.append(step)
        if self.observer is not None:
            self.observer(step)

    def blocked(self, state: str, nextAction: str) -> SetupResult:
        """현재 진행 내역을 보존한 차단 상태의 준비 결과를 만든다."""
        return SetupResult(
            self.plan.runtimeId,
            state,
            False,
            self.mutationCount,
            self.approvalCount,
            tuple(self.steps),
            nextAction=nextAction,
        )


def previewRuntimeSetup(runtimeId: str | None = None, *, engine: Any | None = None) -> SetupPlan:
    """현재 probe에서 필요한 설치·로그인·MCP 변경을 한 계획으로 만든다."""
    runtimeEngine = engine or _runtimeEngine()
    status = runtimeEngine.status(refresh=True)
    runtime = _chooseRuntime(status, runtimeId)
    selected = str(runtime["runtimeId"])
    state = str(runtime.get("state") or "unknown")
    authState = str((runtime.get("auth") or {}).get("state") or "missing")
    mcpConnected = bool((runtime.get("mcp") or {}).get("connected"))
    alreadyReady = bool(runtime.get("groundedReady")) and investmentSemanticReadiness()["ready"]
    changes: list[str] = []
    installPlan = None
    mcpPlan = None
    if state != "ready":
        installPlan = buildInstallPlan(selected)
        prerequisitePlan = _buildPrerequisitePlan(installPlan)
        if prerequisitePlan is not None:
            changes.append(f"{prerequisitePlan.displayName} 자동 설치")
        changes.append("공식 에이전트 CLI 설치")
    else:
        prerequisitePlan = None
    if authState not in {"authenticated", "unsupported"}:
        changes.append("공식 CLI 로그인")
    if not mcpConnected:
        changes.append("DartLab MCP 연결")
        if state == "ready":
            mcpPlan = buildMcpConnectPlan(selected)
    defaultRuntimeId = status.get("defaultRuntimeId")
    if defaultRuntimeId != selected:
        changes.append("기본 분석 런타임 선택")
    return SetupPlan(
        runtimeId=selected,
        displayName=str(runtime.get("displayName") or selected),
        changes=tuple(changes),
        requiresLogin=authState not in {"authenticated", "unsupported"},
        prerequisitePlan=prerequisitePlan,
        installPlan=installPlan,
        mcpPlan=mcpPlan,
        alreadyReady=alreadyReady,
    )


def _alreadyReadyResult(progress: _SetupProgress) -> SetupResult | None:
    """이미 준비된 런타임은 기본 선택만 보정하고 즉시 영수증을 반환한다."""
    if not progress.plan.alreadyReady:
        return None
    progress.current = _runtimeStatus(progress.engine, progress.plan.runtimeId)
    currentDefault = progress.engine.status(refresh=False).get("defaultRuntimeId") or ""
    if currentDefault != progress.plan.runtimeId:
        progress.engine.setDefaultRuntime(progress.plan.runtimeId)
        progress.mutationCount += 1
    semantic = investmentSemanticReadiness()
    progress.record("verify", "skipped", "이미 투자 분석 준비가 완료돼 변경하지 않았습니다.")
    return _result(
        progress.plan.runtimeId,
        progress.current,
        semantic,
        progress.mutationCount,
        progress.approvalCount,
        progress.steps,
    )


def _approvalResult(
    progress: _SetupProgress,
    approved: bool | None,
    confirm: Callable[[SetupPlan], bool] | None,
) -> SetupResult | None:
    """전체 변경 계획에 대한 단일 승인을 처리한다."""
    if not progress.plan.approvalRequired:
        return None
    accepted = bool(confirm(progress.plan)) if approved is None and confirm is not None else bool(approved)
    if not accepted:
        progress.record("approval", "cancelled", "사용자가 setup 변경을 승인하지 않았습니다.")
        return progress.blocked("cancelled", "같은 dartlab setup 명령에서 계획을 승인하세요.")
    progress.approvalCount = 1
    progress.record("approval", "completed", "설치와 DartLab 연결 변경을 한 번 승인했습니다.")
    return None


def _ensureRuntimeInstalled(progress: _SetupProgress) -> SetupResult | None:
    """선행 패키지 관리자와 공식 CLI를 필요한 경우에만 설치한다."""
    if str(progress.current.get("state")) == "ready":
        progress.record("install", "skipped", "설치된 공식 CLI를 그대로 사용합니다.")
        return None
    plan = progress.plan
    if plan.prerequisitePlan is not None and not _installExecutableAvailable(plan.installPlan):
        progress.record("prerequisite", "running", f"{plan.prerequisitePlan.displayName}를 같은 setup에서 설치합니다.")
        try:
            _executePrerequisitePlan(plan.prerequisitePlan)
            _refreshPackageManagerPath()
            if not _installExecutableAvailable(plan.installPlan):
                raise FileNotFoundError("Node.js 설치 후에도 npm 실행 파일을 찾지 못했습니다.")
        except (OSError, subprocess.SubprocessError) as exc:
            progress.record("prerequisite", "failed", f"선행 도구 자동 설치에 실패했습니다: {exc}")
            return progress.blocked(
                "blocked",
                "같은 dartlab setup을 다시 실행하면 완료된 단계는 반복하지 않습니다.",
            )
        progress.mutationCount += 1
        progress.record("prerequisite", "completed", f"{plan.prerequisitePlan.displayName} 실행 파일을 확인했습니다.")
    installPlan = plan.installPlan or buildInstallPlan(plan.runtimeId)
    try:
        _checkInstallPrerequisite(installPlan)
    except FileNotFoundError as exc:
        progress.record("prerequisite", "failed", str(exc))
        return progress.blocked(
            "blocked",
            "지원되는 시스템 패키지 관리자를 준비한 뒤 같은 setup을 다시 실행하세요.",
        )
    progress.record("install", "running", f"{plan.displayName} 공식 CLI를 설치합니다.")
    executeInstallPlan(installPlan, approvedDigest=installPlan.digest)
    progress.mutationCount += 1
    progress.current = _runtimeStatus(progress.engine, plan.runtimeId)
    if str(progress.current.get("state")) != "ready":
        progress.record("install", "failed", "설치 후 실행 파일을 다시 찾지 못했습니다.")
        return progress.blocked(
            "blocked",
            "PATH를 갱신한 뒤 같은 dartlab setup을 다시 실행하세요. 설치는 반복하지 않습니다.",
        )
    progress.record("install", "completed", "설치 후 실행 파일과 버전을 확인했습니다.")
    return None


def _ensureRuntimeAuthenticated(
    progress: _SetupProgress,
    loginExecutor: Callable[[str], subprocess.CompletedProcess[Any]] | None,
) -> SetupResult | None:
    """공식 CLI 로그인 상태를 확인하고 필요하면 동일 setup 흐름에서 시작한다."""
    authState = str((progress.current.get("auth") or {}).get("state") or "missing")
    if authState in {"authenticated", "unsupported"}:
        progress.record("login", "skipped", "기존 공식 CLI 로그인을 그대로 사용합니다.")
        return None
    progress.record("login", "running", "공식 CLI 로그인 절차를 같은 setup 흐름에서 시작합니다.")
    try:
        (loginExecutor or executeInteractiveLogin)(progress.plan.runtimeId)
    except (OSError, subprocess.SubprocessError) as exc:
        progress.record("login", "failed", f"공식 로그인 절차가 완료되지 않았습니다: {exc}")
        return progress.blocked(
            "authPending",
            "같은 dartlab setup을 다시 실행하면 로그인 단계부터 이어집니다.",
        )
    progress.current = _runtimeStatus(progress.engine, progress.plan.runtimeId)
    authState = str((progress.current.get("auth") or {}).get("state") or "missing")
    if authState not in {"authenticated", "unsupported"}:
        progress.record("login", "pending", "공식 로그인 승인이 아직 확인되지 않았습니다.")
        return progress.blocked(
            "authPending",
            "공급자 로그인 승인을 마치면 같은 setup이 남은 단계만 계속합니다.",
        )
    progress.record("login", "completed", "인증 내용은 저장하지 않고 로그인 상태만 확인했습니다.")
    return None


def _ensureRuntimeMcp(progress: _SetupProgress) -> SetupResult | None:
    """DartLab MCP 연결을 적용하고 다시 probe한다."""
    if bool((progress.current.get("mcp") or {}).get("connected")):
        progress.record("mcp", "skipped", "기존 DartLab MCP 연결을 그대로 사용합니다.")
        return None
    connectPlan = buildMcpConnectPlan(progress.plan.runtimeId)
    progress.record("mcp", "running", "DartLab 읽기 전용 분석 도구를 연결합니다.")
    executeMcpConnectPlan(connectPlan, approvedDigest=connectPlan.digest)
    progress.mutationCount += 1
    progress.current = _runtimeStatus(progress.engine, progress.plan.runtimeId)
    if not bool((progress.current.get("mcp") or {}).get("connected")):
        progress.record("mcp", "failed", "공식 CLI 설정에서 DartLab agent profile을 확인하지 못했습니다.")
        return progress.blocked("blocked", "dartlab agent doctor --repair가 필요합니다.")
    progress.record("mcp", "completed", "DartLab agent profile 연결을 확인했습니다.")
    return None


def prepareRuntime(
    runtimeId: str | None = None,
    *,
    approved: bool | None = None,
    engine: Any | None = None,
    confirm: Callable[[SetupPlan], bool] | None = None,
    observer: Callable[[SetupStep], None] | None = None,
    loginExecutor: Callable[[str], subprocess.CompletedProcess[Any]] | None = None,
) -> SetupResult:
    """한 호출 안에서 필요한 단계만 실행하고 준비 완료 상태를 검증한다.

    ``approved=True``는 자동화 환경의 단일 명시 승인이다. ``None``이면 전달된
    confirm을 한 번 호출한다. 공식 로그인 화면의 공급자 동의는 이 승인과 별개다.
    """
    runtimeEngine = engine or _runtimeEngine()
    plan = previewRuntimeSetup(runtimeId, engine=runtimeEngine)
    progress = _SetupProgress(runtimeEngine, plan, observer)
    readyResult = _alreadyReadyResult(progress)
    if readyResult is not None:
        return readyResult
    approvalResult = _approvalResult(progress, approved, confirm)
    if approvalResult is not None:
        return approvalResult
    progress.current = _runtimeStatus(runtimeEngine, plan.runtimeId)
    phaseResult = _ensureRuntimeInstalled(progress)
    if phaseResult is not None:
        return phaseResult
    phaseResult = _ensureRuntimeAuthenticated(progress, loginExecutor)
    if phaseResult is not None:
        return phaseResult
    phaseResult = _ensureRuntimeMcp(progress)
    if phaseResult is not None:
        return phaseResult
    semantic = investmentSemanticReadiness()
    if not semantic["ready"]:
        progress.record("semantic", "failed", "투자 의사결정 계약 또는 핵심 도구가 누락됐습니다.")
        return _result(
            plan.runtimeId,
            progress.current,
            semantic,
            progress.mutationCount,
            progress.approvalCount,
            progress.steps,
        )
    progress.record("semantic", "completed", "투자 메모 계약과 ReadSkill·EngineCall 표면을 확인했습니다.")

    runtimeEngine.setDefaultRuntime(plan.runtimeId)
    if runtimeEngine.status(refresh=False).get("defaultRuntimeId") == plan.runtimeId:
        progress.mutationCount += int("기본 분석 런타임 선택" in plan.changes)
    progress.current = _runtimeStatus(runtimeEngine, plan.runtimeId)
    progress.record("default", "completed", f"{plan.displayName}을 기본 투자 분석 런타임으로 선택했습니다.")
    return _result(
        plan.runtimeId,
        progress.current,
        semantic,
        progress.mutationCount,
        progress.approvalCount,
        progress.steps,
    )


def executeInteractiveLogin(runtimeId: str) -> subprocess.CompletedProcess[Any]:
    """공식 로그인 프로세스에 현재 TTY를 넘기고 인증 원문을 저장하지 않는다."""
    argv = runtimeLoginArgv(runtimeId)
    return subprocess.run(
        list(argv),
        check=True,
        shell=False,
        env={**os.environ, "PYTHONUTF8": "1"},
    )


def executeVisibleLogin(runtimeId: str) -> subprocess.CompletedProcess[Any]:
    """로컬 GUI에서 사용자가 조작할 공식 로그인 창을 열고 완료까지 기다린다."""
    argv = runtimeLoginArgv(runtimeId)
    creationFlags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0) if os.name == "nt" else 0
    return subprocess.run(
        list(argv),
        check=True,
        shell=False,
        env={**os.environ, "PYTHONUTF8": "1"},
        creationflags=creationFlags,
    )


def investmentSemanticReadiness() -> dict[str, Any]:
    """실회사 호출 없이 로컬 MCP의 투자 계약과 핵심 읽기 도구를 점검한다."""
    try:
        from dartlab.ai.tools.registry import listToolNames
        from dartlab.reference.capability import loadCapabilities
        from dartlab.reference.capability.analysisGraph import coveragePacketForQuestion

        tools = set(listToolNames())
        packet = coveragePacketForQuestion("삼성전자 005930 투자 분석해줘")
        capabilities = loadCapabilities()
        checks = {
            "readSkill": "ReadSkill" in tools,
            "engineCall": "EngineCall" in tools,
            "investmentContract": "investment.decision_memo" in packet.get("contractIds", []),
            "reportModel": bool(capabilities.get("Company.reportModel", {}).get("engineCallable")),
        }
    except Exception as exc:  # noqa: BLE001 - doctor 표면은 실패를 상태로 반환한다.
        return {"ready": False, "checks": {}, "detail": f"{type(exc).__name__}: {exc}"}
    return {"ready": all(checks.values()), "checks": checks}


def _runtimeEngine() -> Any:
    from .engine import getRuntimeEngine

    return getRuntimeEngine()


def _chooseRuntime(status: dict[str, Any], requested: str | None) -> dict[str, Any]:
    runtimes = [row for row in status.get("runtimes") or [] if isinstance(row, dict)]
    supported = [
        row
        for row in runtimes
        if row.get("runtimeId") in _SUPPORTED_SETUP_RUNTIMES and bool(row.get("embeddedGrounding", True))
    ]
    if requested:
        if requested not in _SUPPORTED_SETUP_RUNTIMES:
            raise ValueError(
                f"{requested}는 투자 분석 자동 setup 대상이 아닙니다. 지원: {', '.join(_SUPPORTED_SETUP_RUNTIMES)}"
            )
        for row in supported:
            if row.get("runtimeId") == requested:
                return row
        raise KeyError(requested)
    default = status.get("defaultRuntimeId")
    for row in supported:
        if row.get("runtimeId") == default and row.get("groundedReady"):
            return row
    for row in supported:
        if row.get("groundedReady"):
            return row
    for row in supported:
        if row.get("state") == "ready":
            return row
    for preferred in _SUPPORTED_SETUP_RUNTIMES:
        for row in supported:
            if row.get("runtimeId") == preferred:
                return row
    raise RuntimeError("지원하는 설치형 투자 분석 런타임을 찾지 못했습니다.")


def _runtimeStatus(engine: Any, runtimeId: str) -> dict[str, Any]:
    status = engine.status(refresh=True)
    for row in status.get("runtimes") or []:
        if isinstance(row, dict) and row.get("runtimeId") == runtimeId:
            return row
    raise KeyError(runtimeId)


def _checkInstallPrerequisite(plan: InstallPlan) -> None:
    """패키지 관리자가 없을 때 긴 설치 실패 대신 한 번에 정확한 차단 사유를 낸다."""
    executable = plan.argv[0] if plan.argv else ""
    if executable and shutil.which(executable) is None and not os.path.isabs(executable):
        raise FileNotFoundError(
            f"{executable} 실행 파일이 없습니다. Node.js LTS 설치를 먼저 자동화할 수 없는 환경입니다."
        )


def _installExecutableAvailable(plan: InstallPlan | None) -> bool:
    if plan is None or not plan.argv:
        return True
    executable = plan.argv[0]
    return os.path.isabs(executable) and os.path.exists(executable) or shutil.which(executable) is not None


def _buildPrerequisitePlan(plan: InstallPlan) -> PrerequisitePlan | None:
    """npm이 없으면 운영체제 기본 패키지 관리자로 Node.js LTS를 같은 계획에 넣는다."""
    if _installExecutableAvailable(plan):
        return None
    executable = plan.argv[0].casefold() if plan.argv else ""
    if executable not in {"npm", "npm.cmd"}:
        return None
    if os.name == "nt" and shutil.which("winget"):
        return PrerequisitePlan(
            "nodejs",
            "Node.js LTS",
            (
                "winget",
                "install",
                "--id",
                "OpenJS.NodeJS.LTS",
                "--exact",
                "--silent",
                "--accept-package-agreements",
                "--accept-source-agreements",
            ),
        )
    if shutil.which("brew"):
        return PrerequisitePlan("nodejs", "Node.js LTS", ("brew", "install", "node"))
    if os.name != "nt" and getattr(os, "geteuid", lambda: 1)() == 0 and shutil.which("apt-get"):
        return PrerequisitePlan("nodejs", "Node.js/npm", ("apt-get", "install", "-y", "nodejs", "npm"))
    return None


def _executePrerequisitePlan(plan: PrerequisitePlan) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(plan.argv),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=600,
        shell=False,
        check=True,
    )


def _refreshPackageManagerPath() -> None:
    """새 Node 설치 경로를 현재 setup 프로세스에 반영한다."""
    candidates = [
        os.path.join(os.environ.get("ProgramFiles", ""), "nodejs"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "nodejs"),
        os.path.join(os.environ.get("APPDATA", ""), "npm"),
        "/usr/local/bin",
        "/opt/homebrew/bin",
    ]
    current = os.environ.get("PATH", "")
    existing = current.split(os.pathsep)
    prepend = [path for path in candidates if path and os.path.isdir(path) and path not in existing]
    if prepend:
        os.environ["PATH"] = os.pathsep.join([*prepend, current])


def _result(
    runtimeId: str,
    runtime: dict[str, Any],
    semantic: dict[str, Any],
    mutationCount: int,
    approvalCount: int,
    steps: list[SetupStep],
) -> SetupResult:
    runtimeReady = bool(runtime.get("groundedReady"))
    investmentReady = runtimeReady and bool(semantic.get("ready"))
    readiness = {
        "runtimeReady": str(runtime.get("state")) == "ready",
        "authReady": str((runtime.get("auth") or {}).get("state")) in {"authenticated", "unsupported"},
        "mcpReady": bool((runtime.get("mcp") or {}).get("connected")),
        "semanticToolsReady": bool(semantic.get("checks", {}).get("readSkill"))
        and bool(semantic.get("checks", {}).get("engineCall")),
        "investmentContractReady": bool(semantic.get("checks", {}).get("investmentContract"))
        and bool(semantic.get("checks", {}).get("reportModel")),
        "investmentReady": investmentReady,
    }
    return SetupResult(
        runtimeId,
        "ready" if investmentReady else "blocked",
        investmentReady,
        mutationCount,
        approvalCount,
        tuple(steps),
        readiness,
        None if investmentReady else "설치 상태와 투자 계약 검사를 다시 확인하세요.",
    )


__all__ = [
    "SetupPlan",
    "PrerequisitePlan",
    "SetupResult",
    "SetupStep",
    "executeInteractiveLogin",
    "executeVisibleLogin",
    "investmentSemanticReadiness",
    "prepareRuntime",
    "previewRuntimeSetup",
]
