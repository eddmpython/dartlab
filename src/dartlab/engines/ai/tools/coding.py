"""Provider-agnostic coding backend runtime."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CodingTaskResult:
    """Normalized result from a coding backend."""

    backend: str
    answer: str
    sandbox: str
    model: str
    usage: dict[str, int] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class CodingBackend(ABC):
    """Abstract coding backend that can execute workspace tasks."""

    name: str
    label: str
    description: str

    @abstractmethod
    def inspect(self) -> dict[str, Any]:
        """Return backend capability/status metadata."""

    @abstractmethod
    def run_task(
        self,
        prompt: str,
        *,
        sandbox: str = "workspace-write",
        model: str | None = None,
        timeout_seconds: int = 300,
    ) -> CodingTaskResult:
        """Execute a coding task."""

    def check_available(self) -> bool:
        info = self.inspect()
        return bool(info.get("available", False))


class CodexCodingBackend(CodingBackend):
    """Codex CLI-backed coding executor."""

    name = "codex"
    label = "Codex CLI"
    description = "OpenAI Codex CLI를 사용해 워크스페이스 코드 작업을 실행합니다."

    def inspect(self) -> dict[str, Any]:
        from dartlab.engines.ai.providers.support.codex_cli import inspect_codex_cli

        info = inspect_codex_cli()
        sandbox_modes = info.get("sandboxModes") or []
        return {
            "name": self.name,
            "label": self.label,
            "description": self.description,
            "installed": bool(info.get("installed")),
            "authenticated": bool(info.get("authenticated")),
            "available": bool(info.get("installed") and info.get("authenticated")),
            "configuredModel": info.get("configuredModel"),
            "version": info.get("version"),
            "sandboxModes": sandbox_modes,
            "supportsWorkspaceWrite": "workspace-write" in sandbox_modes,
            "supportsDangerFullAccess": "danger-full-access" in sandbox_modes,
        }

    def run_task(
        self,
        prompt: str,
        *,
        sandbox: str = "workspace-write",
        model: str | None = None,
        timeout_seconds: int = 300,
    ) -> CodingTaskResult:
        from dartlab.engines.ai.providers.support.codex_cli import run_codex_exec

        info = self.inspect()
        if not info.get("installed"):
            raise FileNotFoundError("Codex CLI가 설치되어 있지 않습니다. 먼저 `codex --version`이 동작해야 합니다.")
        if not info.get("authenticated"):
            raise PermissionError("Codex CLI 로그인이 필요합니다. `codex login`을 실행하세요.")

        sandbox_modes = set(info.get("sandboxModes") or [])
        selected_sandbox = sandbox
        if sandbox_modes and sandbox not in sandbox_modes:
            selected_sandbox = "workspace-write" if "workspace-write" in sandbox_modes else "read-only"

        answer, usage = run_codex_exec(
            prompt,
            model=model or None,
            sandbox=selected_sandbox,
            timeout=timeout_seconds,
        )
        return CodingTaskResult(
            backend=self.name,
            answer=answer,
            sandbox=selected_sandbox,
            model=model or info.get("configuredModel") or "CLI default",
            usage=usage,
            metadata={
                "version": info.get("version"),
                "configuredModel": info.get("configuredModel"),
            },
        )


class CodingRuntime:
    """Registry/executor for coding backends."""

    def __init__(self, name: str = "default"):
        self.name = name
        self._backends: dict[str, CodingBackend] = {}
        self._default_backend: str | None = None

    def register_backend(self, backend: CodingBackend, *, default: bool = False) -> None:
        self._backends[backend.name] = backend
        if default or self._default_backend is None:
            self._default_backend = backend.name

    def get_backend(self, name: str | None = None) -> CodingBackend:
        backend_name = name or self._default_backend
        if not backend_name or backend_name not in self._backends:
            available = ", ".join(f"`{key}`" for key in self._backends) or "(없음)"
            raise KeyError(f"등록되지 않은 coding backend입니다: {name}. 사용 가능: {available}")
        return self._backends[backend_name]

    def list_backend_names(self) -> list[str]:
        return list(self._backends.keys())

    def inspect_backends(self) -> list[dict[str, Any]]:
        return [backend.inspect() for backend in self._backends.values()]

    def run_task(
        self,
        prompt: str,
        *,
        backend: str | None = None,
        sandbox: str = "workspace-write",
        model: str | None = None,
        timeout_seconds: int = 300,
    ) -> CodingTaskResult:
        selected_backend = self.get_backend(backend)
        return selected_backend.run_task(
            prompt,
            sandbox=sandbox,
            model=model,
            timeout_seconds=timeout_seconds,
        )


def create_coding_runtime(name: str = "runtime", *, include_defaults: bool = True) -> CodingRuntime:
    runtime = CodingRuntime(name=name)
    if include_defaults:
        runtime.register_backend(CodexCodingBackend(), default=True)
    return runtime


_DEFAULT_CODING_RUNTIME = create_coding_runtime(name="default")


def get_default_coding_runtime() -> CodingRuntime:
    return _DEFAULT_CODING_RUNTIME


def set_default_coding_runtime(runtime: CodingRuntime) -> None:
    global _DEFAULT_CODING_RUNTIME
    _DEFAULT_CODING_RUNTIME = runtime
