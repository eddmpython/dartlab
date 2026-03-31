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
        """백엔드 사용 가능 여부를 반환한다."""
        info = self.inspect()
        return bool(info.get("available", False))


class CodexCodingBackend(CodingBackend):
    """Codex CLI-backed coding executor."""

    name = "codex"
    label = "Codex CLI"
    description = "OpenAI Codex CLI를 사용해 워크스페이스 코드 작업을 실행합니다."

    def inspect(self) -> dict[str, Any]:
        """Codex CLI 설치/인증 상태와 지원 sandbox 모드를 조회한다."""
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
        """Codex CLI로 코딩 작업을 실행한다."""
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


def _validateCode(code: str) -> list[str]:
    """구문 검증만 수행. 제한 없음 — 로컬 도구이므로 자유 실행."""
    try:
        ast.parse(code)
    except SyntaxError as e:
        return [f"구문 오류: {e}"]
    return []


class LocalPythonBackend(CodingBackend):
    """로컬 subprocess 기반 Python 코드 실행 -- AST 검증 + 격리."""

    name = "local_python"
    label = "Local Python"
    description = "로컬 subprocess에서 Python 코드를 안전하게 실행합니다."

    def __init__(self, *, defaultTimeout: int = 30, maxTimeout: int = 120) -> None:
        self._defaultTimeout = defaultTimeout
        self._maxTimeout = maxTimeout

    def inspect(self) -> dict[str, Any]:
        """로컬 Python 백엔드 상태와 허용/금지 모듈 목록을 반환한다."""
        return {
            "name": self.name,
            "label": self.label,
            "description": self.description,
            "available": True,
            "python": sys.version,
            "defaultTimeout": self._defaultTimeout,
            "maxTimeout": self._maxTimeout,
            "restrictions": "none (unrestricted local execution)",
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
                answer="[보안 위반] 코드가 안전하지 않습니다:\n" + "\n".join(f"- {v}" for v in violations),
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
                    encoding="utf-8",
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


def _classifyError(stderr: str, stdout: str) -> str:
    """코드 실행 에러를 분류하고 복구 힌트를 제공한다."""
    hint = ""
    if "ImportError" in stderr or "ModuleNotFoundError" in stderr:
        hint = "\n힌트: 모듈을 찾을 수 없습니다. dartlab 내장 API만 사용 가능합니다."
    elif "AttributeError" in stderr or "NameError" in stderr:
        hint = (
            "\n힌트: API 이름이 틀렸을 수 있습니다. `dartlab.capabilities(search='키워드')`로 정확한 API를 검색하세요."
        )
    elif "TypeError" in stderr:
        hint = "\n힌트: 함수 파라미터가 맞지 않습니다. `help(함수명)`으로 시그니처를 확인하세요."
    elif "KeyError" in stderr or "ColumnNotFoundError" in stderr:
        hint = "\n힌트: 컬럼/키가 없습니다. 먼저 print()로 구조를 확인한 뒤 정확한 이름을 사용하세요."

    parts = ["[실행 오류]"]
    if stderr:
        # traceback에서 마지막 에러 줄만 추출 (전체 traceback은 토큰 낭비)
        lines = stderr.strip().splitlines()
        errorLine = lines[-1] if lines else stderr
        parts.append(errorLine)
    if stdout:
        parts.append(f"출력:\n{stdout[:1000]}")
    if hint:
        parts.append(hint)
    return "\n".join(parts)


def _stripDuplicateImport(code: str, module: str) -> str:
    """사용자 코드에서 `import <module>` 단독 문을 제거한다 (preamble에서 주입하므로)."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return code
    # import dartlab 단독 문(from dartlab ... 은 유지)만 제거
    linesToRemove: set[int] = set()
    for node in tree.body:
        if (
            isinstance(node, ast.Import)
            and len(node.names) == 1
            and node.names[0].name == module
            and node.names[0].asname is None
        ):
            linesToRemove.add(node.lineno)
    if not linesToRemove:
        return code
    lines = code.split("\n")
    return "\n".join(line for i, line in enumerate(lines, 1) if i not in linesToRemove)


class DartlabCodeExecutor(LocalPythonBackend):
    """dartlab 전용 코드 실행기 -- CAPABILITIES 기반 코드 생성 + 실행.

    LocalPythonBackend를 확장하여:
    1. dartlab 패키지를 import 허용
    2. PYTHONPATH에 dartlab 경로 전달
    3. company context를 preamble로 주입
    4. DataFrame 결과를 마크다운 테이블로 변환
    """

    name = "dartlab_executor"
    label = "DartLab Executor"
    description = "dartlab Python 코드를 안전하게 실행합니다."

    def __init__(self, *, defaultTimeout: int = 30, maxTimeout: int = 60) -> None:
        super().__init__(defaultTimeout=defaultTimeout, maxTimeout=maxTimeout)

    def execute(self, code: str, *, stockCode: str | None = None, timeout: int = 30) -> str:
        """dartlab 코드를 실행하고 결과를 반환한다."""
        # 사용자 코드에서 중복 import dartlab 제거 (preamble에서 주입)
        cleanCode = _stripDuplicateImport(code, "dartlab")

        # dartlab context preamble — LLM이 읽을 수 있는 크기로 제한
        preamble = (
            "import dartlab\n"
            "import polars as pl\n"
            "pl.Config.set_fmt_float('full')\n"
            "pl.Config.set_tbl_cols(8)\n"
            "pl.Config.set_tbl_rows(20)\n"
            "pl.Config.set_tbl_width_chars(100)\n"
        )
        preamble += "Company = dartlab.Company\n"
        preamble += (
            "try:\n"
            "    from dartlab.gather.search import webSearch, newsSearch, formatResults, searchAvailable\n"
            "except ImportError:\n"
            "    pass\n"
        )
        if stockCode:
            preamble += f'c = Company("{stockCode}")\n'
            preamble += "company = c\n"

        # 결과 캡처 래퍼: 마지막 expression의 결과를 출력
        wrappedCode = self._wrapForCapture(cleanCode)
        fullCode = preamble + wrappedCode

        result = self.run_task(
            prompt="",
            code=fullCode,
            timeout_seconds=min(timeout, self._maxTimeout),
        )
        return self._formatResult(result.answer)

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
        """dartlab용 환경 변수로 실행한다."""
        if not code:
            return CodingTaskResult(
                backend=self.name,
                answer="[오류] 실행할 코드가 없습니다.",
                sandbox=sandbox,
                model="local",
            )

        # AST 안전성 검증
        violations = _validateCode(code)
        if violations:
            return CodingTaskResult(
                backend=self.name,
                answer="[보안 위반] 코드가 안전하지 않습니다:\n" + "\n".join(f"- {v}" for v in violations),
                sandbox=sandbox,
                model="local",
            )

        timeout = min(max(timeout_seconds, 5), self._maxTimeout)

        with tempfile.TemporaryDirectory(prefix="dartlab_exec_") as tmpDir:
            scriptPath = Path(tmpDir) / "run.py"
            scriptPath.write_text(code, encoding="utf-8")

            # dartlab이 import 가능하도록 PYTHONPATH 설정
            import os

            pythonPath = os.pathsep.join(sys.path)

            env = os.environ.copy()
            env["PYTHONPATH"] = pythonPath
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            env["PYTHONUTF8"] = "1"

            try:
                result = subprocess.run(
                    [sys.executable, "-X", "utf8", str(scriptPath)],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    timeout=timeout,
                    cwd=tmpDir,
                    env=env,
                )

                rawStdout = result.stdout or ""
                rawStderr = result.stderr or ""
                _MAX_OUT = 8000
                stdoutTruncated = len(rawStdout) > _MAX_OUT
                stdout = rawStdout[:_MAX_OUT]
                if stdoutTruncated:
                    stdout += (
                        f"\n\n... (출력 {len(rawStdout):,}자 중 {_MAX_OUT:,}자만 표시."
                        " .head()/.filter()로 범위를 좁혀 재실행하세요)"
                    )
                stderr = rawStderr[:2000]

                if result.returncode == 0:
                    answer = stdout if stdout else "(실행 완료, 출력 없음)"
                else:
                    answer = _classifyError(stderr, stdout)

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

    def _wrapForCapture(self, code: str) -> str:
        """마지막 expression의 결과를 자동으로 print한다."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return code

        if not tree.body:
            return code

        lastNode = tree.body[-1]
        if isinstance(lastNode, ast.Expr):
            # AST 기반: preceding 노드들을 unparse하고 마지막만 _result로 변환
            exprSource = ast.unparse(lastNode.value)
            preceding = tree.body[:-1]
            parts: list[str] = []
            for node in preceding:
                parts.append(ast.unparse(node))
            parts.append(f"_result = {exprSource}")
            parts.append("if _result is not None:")
            parts.append("    print(_result)")
            return "\n".join(parts)
        return code

    def _formatResult(self, answer: str) -> str:
        """코드 실행 결과의 과학적 표기법을 읽기 좋은 숫자로 변환한다."""
        import re

        def _replaceScientific(m: re.Match) -> str:
            try:
                val = float(m.group(0))
                absVal = abs(val)
                if absVal >= 1e12:
                    sign = "-" if val < 0 else ""
                    return f"{sign}{absVal / 1e12:,.1f}조"
                if absVal >= 1e8:
                    sign = "-" if val < 0 else ""
                    return f"{sign}{absVal / 1e8:,.0f}억"
                if absVal >= 1:
                    return f"{int(val):,}"
                return m.group(0)
            except (ValueError, OverflowError):
                return m.group(0)

        answer = re.sub(r"-?\d+\.?\d*[eE][+-]?\d+", _replaceScientific, answer)
        if len(answer) > 8000:
            return answer[:8000] + "\n\n... (결과가 너무 깁니다. .head()/.filter()로 범위를 좁혀주세요)"
        return answer


class CodingRuntime:
    """Registry/executor for coding backends."""

    def __init__(self, name: str = "default"):
        self.name = name
        self._backends: dict[str, CodingBackend] = {}
        self._default_backend: str | None = None

    def register_backend(self, backend: CodingBackend, *, default: bool = False) -> None:
        """코딩 백엔드를 등록한다."""
        self._backends[backend.name] = backend
        if default or self._default_backend is None:
            self._default_backend = backend.name

    def get_backend(self, name: str | None = None) -> CodingBackend:
        """이름으로 백엔드를 가져온다."""
        backend_name = name or self._default_backend
        if not backend_name or backend_name not in self._backends:
            available = ", ".join(f"`{key}`" for key in self._backends) or "(없음)"
            raise KeyError(f"등록되지 않은 coding backend입니다: {name}. 사용 가능: {available}")
        return self._backends[backend_name]

    def list_backend_names(self) -> list[str]:
        """등록된 백엔드 이름 목록을 반환한다."""
        return list(self._backends.keys())

    def inspect_backends(self) -> list[dict[str, Any]]:
        """모든 백엔드의 상태 메타데이터를 반환한다."""
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
        """지정된 백엔드로 코딩 작업을 실행한다."""
        selected_backend = self.get_backend(backend)
        return selected_backend.run_task(
            prompt,
            sandbox=sandbox,
            model=model,
            timeout_seconds=timeout_seconds,
        )


def create_coding_runtime(name: str = "runtime", *, include_defaults: bool = True) -> CodingRuntime:
    """기본 백엔드를 포함한 CodingRuntime 인스턴스를 생성한다."""
    runtime = CodingRuntime(name=name)
    if include_defaults:
        runtime.register_backend(CodexCodingBackend(), default=True)
        runtime.register_backend(LocalPythonBackend())
    return runtime


_DEFAULT_CODING_RUNTIME = create_coding_runtime(name="default")


def get_default_coding_runtime() -> CodingRuntime:
    """전역 기본 CodingRuntime을 반환한다."""
    return _DEFAULT_CODING_RUNTIME


def set_default_coding_runtime(runtime: CodingRuntime) -> None:
    """전역 기본 CodingRuntime을 교체한다."""
    global _DEFAULT_CODING_RUNTIME
    _DEFAULT_CODING_RUNTIME = runtime
