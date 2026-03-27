"""Provider-agnostic coding backend runtime."""

from __future__ import annotations

import ast
import logging
import subprocess
import sys
import tempfile
import textwrap
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)


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
        from dartlab.ai.providers.support.codex_cli import inspect_codex_cli

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
        from dartlab.ai.providers.support.codex_cli import run_codex_exec

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


# ══════════════════════════════════════
# LocalPythonBackend -- subprocess 기반 안전 실행
# ══════════════════════════════════════

# AST 기반 안전 검증 -- 금지 패턴
_FORBIDDEN_IMPORTS = frozenset({
    "subprocess", "os", "sys", "shutil", "signal", "ctypes",
    "socket", "http", "urllib", "requests", "httpx", "aiohttp",
    "multiprocessing", "threading", "asyncio",
    "pickle", "shelve", "marshal",
    "importlib", "runpy", "code", "codeop",
})

_FORBIDDEN_CALLS = frozenset({
    "exec", "eval", "compile", "__import__", "globals", "locals",
    "getattr", "setattr", "delattr", "breakpoint", "exit", "quit",
    "open",  # 파일 쓰기 방지 (읽기도 차단 -- 데이터는 data 변수로 주입)
})

_ALLOWED_IMPORTS = frozenset({
    "math", "statistics", "json", "datetime", "collections",
    "itertools", "functools", "operator", "decimal", "fractions",
    "re", "textwrap", "string", "copy", "dataclasses", "time",
    "polars", "numpy", "pandas",
})


class _SafetyVisitor(ast.NodeVisitor):
    """AST 방문자 -- 금지 패턴 탐지."""

    def __init__(self) -> None:
        self.violations: list[str] = []

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            modName = alias.name.split(".")[0]
            if modName in _FORBIDDEN_IMPORTS:
                self.violations.append(f"금지된 import: {alias.name}")
            elif modName not in _ALLOWED_IMPORTS:
                self.violations.append(f"허용되지 않은 모듈: {alias.name}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            modName = node.module.split(".")[0]
            if modName in _FORBIDDEN_IMPORTS:
                self.violations.append(f"금지된 import: {node.module}")
            elif modName not in _ALLOWED_IMPORTS:
                self.violations.append(f"허용되지 않은 모듈: {node.module}")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        funcName = ""
        if isinstance(node.func, ast.Name):
            funcName = node.func.id
        elif isinstance(node.func, ast.Attribute):
            funcName = node.func.attr
        if funcName in _FORBIDDEN_CALLS:
            self.violations.append(f"금지된 호출: {funcName}()")
        self.generic_visit(node)


def _validateCode(code: str) -> list[str]:
    """코드 안전성 검증. 위반사항 리스트 반환 (빈 리스트 = 안전)."""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return [f"구문 오류: {e}"]
    visitor = _SafetyVisitor()
    visitor.visit(tree)
    return visitor.violations


class LocalPythonBackend(CodingBackend):
    """로컬 subprocess 기반 Python 코드 실행 -- AST 검증 + 격리."""

    name = "local_python"
    label = "Local Python"
    description = "로컬 subprocess에서 Python 코드를 안전하게 실행합니다."

    def __init__(self, *, defaultTimeout: int = 30, maxTimeout: int = 120) -> None:
        self._defaultTimeout = defaultTimeout
        self._maxTimeout = maxTimeout

    def inspect(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "label": self.label,
            "description": self.description,
            "available": True,
            "python": sys.version,
            "defaultTimeout": self._defaultTimeout,
            "maxTimeout": self._maxTimeout,
            "allowedModules": sorted(_ALLOWED_IMPORTS),
            "forbiddenImports": sorted(_FORBIDDEN_IMPORTS),
        }

    def run_task(
        self,
        prompt: str,
        *,
        sandbox: str = "isolated",
        model: str | None = None,
        timeout_seconds: int = 30,
        code: str | None = None,
        dataJson: str | None = None,
    ) -> CodingTaskResult:
        """Python 코드 실행.

        Args:
            prompt: LLM에게 보낼 프롬프트 (code가 없을 때 사용)
            code: 직접 실행할 Python 코드
            dataJson: 코드에 `data` 변수로 주입할 JSON 문자열
            timeout_seconds: 실행 시간 제한 (초)
        """
        if not code:
            return CodingTaskResult(
                backend=self.name,
                answer="[오류] 실행할 코드가 없습니다. code 파라미터를 전달하세요.",
                sandbox=sandbox,
                model="local",
            )

        # 1. AST 안전성 검증
        violations = _validateCode(code)
        if violations:
            return CodingTaskResult(
                backend=self.name,
                answer=f"[보안 위반] 코드가 안전하지 않습니다:\n" + "\n".join(f"- {v}" for v in violations),
                sandbox=sandbox,
                model="local",
            )

        # 2. 실행 시간 제한 clamp
        timeout = min(max(timeout_seconds, 5), self._maxTimeout)

        # 3. 임시 디렉토리에서 실행
        with tempfile.TemporaryDirectory(prefix="dartlab_code_") as tmpDir:
            scriptPath = Path(tmpDir) / "run.py"

            # 데이터 주입 프리앰블
            preamble = ""
            if dataJson:
                dataPath = Path(tmpDir) / "data.json"
                dataPath.write_text(dataJson, encoding="utf-8")
                preamble = textwrap.dedent(f"""\
                    import json as _json
                    with open({str(dataPath)!r}, encoding="utf-8") as _f:
                        data = _json.load(_f)
                """)

            fullCode = preamble + code
            scriptPath.write_text(fullCode, encoding="utf-8")

            try:
                result = subprocess.run(
                    [sys.executable, "-X", "utf8", str(scriptPath)],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=tmpDir,
                    env={
                        "PATH": "",  # 최소 환경
                        "PYTHONPATH": "",
                        "PYTHONDONTWRITEBYTECODE": "1",
                    },
                )

                stdout = result.stdout[:8000] if result.stdout else ""
                stderr = result.stderr[:2000] if result.stderr else ""

                if result.returncode == 0:
                    answer = stdout if stdout else "(실행 완료, 출력 없음)"
                else:
                    answer = f"[실행 오류] (exit code {result.returncode})\n"
                    if stderr:
                        answer += f"```\n{stderr}\n```\n"
                    if stdout:
                        answer += f"\n출력:\n{stdout}"

                return CodingTaskResult(
                    backend=self.name,
                    answer=answer,
                    sandbox="isolated",
                    model="local",
                    metadata={
                        "returncode": result.returncode,
                        "timeout": timeout,
                        "codeLength": len(code),
                    },
                )

            except subprocess.TimeoutExpired:
                return CodingTaskResult(
                    backend=self.name,
                    answer=f"[시간 초과] {timeout}초 내에 실행이 완료되지 않았습니다.",
                    sandbox="isolated",
                    model="local",
                    metadata={"timeout": timeout},
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
        runtime.register_backend(LocalPythonBackend())
    return runtime


_DEFAULT_CODING_RUNTIME = create_coding_runtime(name="default")


def get_default_coding_runtime() -> CodingRuntime:
    return _DEFAULT_CODING_RUNTIME


def set_default_coding_runtime(runtime: CodingRuntime) -> None:
    global _DEFAULT_CODING_RUNTIME
    _DEFAULT_CODING_RUNTIME = runtime
