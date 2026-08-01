"""RunPython 제한 실행의 AST, import, 파일 경계.

RunPython은 Python 언어 전체를 보안 sandbox로 만들지 않는다. 이 모듈은 분석에
필요하지 않은 동적 실행, 운영체제, 네트워크, 자격증명, 임의 파일 접근 경로를
fail-closed로 제거하고 신뢰된 분석 코드만 좁은 표면에서 실행하게 한다.
"""

from __future__ import annotations

import ast
import builtins
import logging
import os
import os.path
import tempfile
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)

_ALLOWED_IMPORT_TARGETS = frozenset(
    {
        "collections",
        "dartlab",
        "datetime",
        "decimal",
        "fractions",
        "functools",
        "itertools",
        "json",
        "math",
        "operator",
        "pathlib",
        "polars",
        "re",
        "statistics",
        "tempfile",
        "time",
    }
)
_BLOCKED_DARTLAB_IMPORT_PREFIXES = (
    "dartlab.Fred",
    "dartlab.OpenDart",
    "dartlab.OpenEdgar",
    "dartlab.ai",
    "dartlab.ask",
    "dartlab.channel",
    "dartlab.cli",
    "dartlab.collect",
    "dartlab.collectAll",
    "dartlab.config",
    "dartlab.core.credentialLifecycle",
    "dartlab.core.credentials",
    "dartlab.core.env",
    "dartlab.core.providers",
    "dartlab.gather.credentials",
    "dartlab.gather.dart.keys",
    "dartlab.mcp",
    "dartlab.server",
    "dartlab.setup",
)
_BLOCKED_IMPORT_MEMBERS = frozenset(
    {
        "operator.attrgetter",
        "operator.methodcaller",
        "tempfile.NamedTemporaryFile",
        "tempfile.SpooledTemporaryFile",
        "tempfile.TemporaryDirectory",
        "tempfile.TemporaryFile",
        "tempfile.mkdtemp",
        "tempfile.mkstemp",
        "tempfile.mktemp",
    }
)
_BLOCKED_DYNAMIC_CALLS = frozenset(
    {
        "__import__",
        "breakpoint",
        "compile",
        "delattr",
        "dir",
        "eval",
        "exec",
        "getattr",
        "globals",
        "input",
        "locals",
        "setattr",
        "vars",
    }
)
_BLOCKED_ANY_ATTRIBUTES = frozenset(
    {
        "ask",
        "chmod",
        "chdir",
        "collect",
        "collectAll",
        "config",
        "credentialLifecycle",
        "credentials",
        "dataDir",
        "environb",
        "environ",
        "execv",
        "execve",
        "execvp",
        "execvpe",
        "fork",
        "forkpty",
        "getcwd",
        "getCredentialProvider",
        "getenv",
        "getSecretStore",
        "glob",
        "hardlink_to",
        "iterdir",
        "import_module",
        "lchmod",
        "listCredentialProviders",
        "listdir",
        "kill",
        "mkdir",
        "mkdtemp",
        "mktemp",
        "mkstemp",
        "methodcaller",
        "modules",
        "NamedTemporaryFile",
        "open",
        "owner",
        "popen",
        "prefetch",
        "providers",
        "putenv",
        "readlink",
        "reloadPlugins",
        "rename",
        "replace",
        "rglob",
        "rmdir",
        "samefile",
        "scandir",
        "secretStore",
        "spawnl",
        "spawnle",
        "spawnlp",
        "spawnlpe",
        "spawnv",
        "spawnve",
        "spawnvp",
        "spawnvpe",
        "stat",
        "setup",
        "SpooledTemporaryFile",
        "symlink_to",
        "system",
        "TemporaryDirectory",
        "TemporaryFile",
        "touch",
        "unlink",
        "unsetenv",
        "walk",
        "attrgetter",
        "apiKey",
        "accessToken",
        "access_token",
        "refreshToken",
        "refresh_token",
    }
)
_BLOCKED_ATTRIBUTE_PREFIXES = ("read_", "scan_", "sink_", "write_")


def _assertSafeAst(code: str) -> None:
    """실행 직전 AST에서 import, 동적 호출, 파일/환경 우회를 거절한다."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                _assertAllowedImport(alias.name)
        elif isinstance(node, ast.ImportFrom):
            moduleName = str(node.module or "")
            _assertAllowedImport(moduleName)
            if any(alias.name == "*" for alias in node.names):
                raise PermissionError("RunPython: wildcard import는 허용되지 않습니다.")
            for alias in node.names:
                if alias.name.startswith("_"):
                    raise PermissionError("RunPython: private symbol import는 허용되지 않습니다.")
                _assertAllowedImport(f"{moduleName}.{alias.name}")

    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id == "__builtins__":
            raise PermissionError("RunPython: __builtins__ 직접 접근은 허용되지 않습니다.")

        if isinstance(node, ast.Attribute):
            attr = node.attr
            if attr.startswith("_"):
                raise PermissionError(f"RunPython: private/dunder attribute '{attr}' 접근은 허용되지 않습니다.")
            if attr in _BLOCKED_ANY_ATTRIBUTES or attr.startswith(_BLOCKED_ATTRIBUTE_PREFIXES):
                raise PermissionError(f"RunPython: 파일, 환경, 동적 실행 attribute '{attr}' 접근은 허용되지 않습니다.")

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in _BLOCKED_DYNAMIC_CALLS:
            raise PermissionError(f"RunPython: 동적 실행 함수 '{node.func.id}' 호출은 허용되지 않습니다.")


def _assertAllowedImport(name: str) -> None:
    root = name.split(".", 1)[0]
    if root not in _ALLOWED_IMPORT_TARGETS:
        raise PermissionError(f"RunPython: '{root}' 모듈 import는 허용되지 않습니다.")
    if any(part.startswith("_") for part in name.split(".")):
        raise PermissionError(f"RunPython: private 모듈 '{name}' import는 허용되지 않습니다.")
    if name in _BLOCKED_IMPORT_MEMBERS:
        raise PermissionError(f"RunPython: 파일 또는 동적 attribute helper '{name}' import는 허용되지 않습니다.")
    if any(name == prefix or name.startswith(prefix + ".") for prefix in _BLOCKED_DARTLAB_IMPORT_PREFIXES):
        raise PermissionError(f"RunPython: 민감한 DartLab 모듈 '{name}' import는 허용되지 않습니다.")


def _defaultSafeRoots() -> list[str]:
    """파일 읽기 허용 root: 저장소, artifact, tool result, 임시 디렉터리."""
    home = os.path.expanduser("~")
    repoRoot = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
    roots: list[str] = [
        repoRoot,
        os.path.join(home, "dartlab-artifacts"),
        os.path.join(home, ".dartlab", "artifacts"),
        os.path.join(home, ".dartlab", "ask_artifacts"),
        os.path.join(home, ".dartlab", "tool-results"),
        os.path.abspath("./tmp"),
        tempfile.gettempdir(),
    ]
    if os.path.exists("/tmp"):
        roots.append("/tmp")
    return [os.path.realpath(os.path.normpath(root)) for root in roots]


def _defaultWriteRoots() -> list[str]:
    """파일 쓰기 허용 root: 산출물과 임시 디렉터리. 저장소 원본은 제외한다."""
    home = os.path.expanduser("~")
    repoRoot = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
    roots = [
        os.path.join(home, "dartlab-artifacts"),
        os.path.join(home, ".dartlab", "artifacts"),
        os.path.join(home, ".dartlab", "ask_artifacts"),
        os.path.join(home, ".dartlab", "tool-results"),
        os.path.join(repoRoot, "tmp"),
        os.path.abspath("./tmp"),
        tempfile.gettempdir(),
    ]
    if os.path.exists("/tmp"):
        roots.append("/tmp")
    return [os.path.realpath(os.path.normpath(root)) for root in roots]


_DENIED_NAMES = frozenset(
    {
        ".netrc",
        ".npmrc",
        "credentials.json",
        "id_ed25519",
        "id_rsa",
        "oauth.json",
        "oauth_token.json",
        "secrets.json",
    }
)
_DENIED_SUFFIXES = (".key", ".p12", ".pem", ".pfx")
_DENIED_PARTS = frozenset({".aws", ".git", ".ssh", "node_modules"})


def _isDeniedPath(path: str) -> bool:
    normalized = os.path.normpath(path)
    name = os.path.basename(normalized).lower()
    if name in _DENIED_NAMES or name == ".env" or name.startswith(".env."):
        return True
    if name.endswith(_DENIED_SUFFIXES):
        return True
    return bool(_DENIED_PARTS.intersection(part.lower() for part in normalized.split(os.sep)))


def _safeOpenFactory(
    safeRoots: list[str] | None = None,
    writeRoots: list[str] | None = None,
) -> Callable[..., Any]:
    """built-in open을 읽기 root, 더 좁은 쓰기 root, 자격증명 denylist로 제한한다."""
    roots = [os.path.realpath(os.path.normpath(root)) for root in (safeRoots or _defaultSafeRoots())]
    writable = [
        os.path.realpath(os.path.normpath(root))
        for root in (writeRoots if writeRoots is not None else (safeRoots or _defaultWriteRoots()))
    ]
    realOpen = open

    def safeOpen(file: Any, mode: str = "r", *args: Any, **kwargs: Any) -> Any:
        try:
            pathString = os.fspath(file)
        except TypeError as exc:
            raise PermissionError("RunPython: file descriptor 직접 open은 허용되지 않습니다.") from exc
        absolutePath = os.path.realpath(os.path.abspath(pathString))
        isWrite = any(flag in mode for flag in ("w", "a", "x", "+"))
        allowedRoots = writable if isWrite else roots
        if kwargs.get("opener") is not None:
            raise PermissionError("RunPython: custom file opener는 허용되지 않습니다.")
        if _isDeniedPath(absolutePath) or not _isUnderSafeRoots(absolutePath, allowedRoots):
            raise PermissionError(
                f"RunPython: 파일 접근은 안전한 비자격증명 경로만 허용 ({', '.join(allowedRoots)}). "
                f"시도된 경로: {absolutePath}. 문서 읽기는 Read, 결과 저장은 SaveArtifact를 사용하세요."
            )
        return realOpen(file, mode, *args, **kwargs)

    return safeOpen


def _isUnderSafeRoots(absolutePath: str, roots: list[str]) -> bool:
    """해석된 절대 경로가 root와 같거나 그 하위인지 판정한다."""
    for root in roots:
        try:
            if os.path.commonpath((absolutePath, root)) == root:
                return True
        except ValueError:
            logger.debug("RunPython safe-root comparison rejected incompatible paths", exc_info=True)
            continue
    return False


def _safeImport(
    name: str,
    globalVars: dict[str, Any] | None = None,
    localVars: dict[str, Any] | None = None,
    fromlist: tuple[str, ...] = (),
    level: int = 0,
) -> Any:
    """사용자 코드의 import를 계산용 모듈 allowlist로 제한한다."""
    _assertAllowedImport(name)
    return builtins.__import__(name, globalVars, localVars, fromlist, level)


def _safeBuiltins() -> dict[str, Any]:
    """분석 코드에 필요한 비동적 built-in만 제공한다."""
    names = {
        "ArithmeticError",
        "AssertionError",
        "AttributeError",
        "Exception",
        "IndexError",
        "KeyError",
        "LookupError",
        "RuntimeError",
        "StopIteration",
        "TypeError",
        "ValueError",
        "ZeroDivisionError",
        "__build_class__",
        "abs",
        "all",
        "any",
        "bool",
        "bytes",
        "callable",
        "chr",
        "complex",
        "dict",
        "divmod",
        "enumerate",
        "filter",
        "float",
        "format",
        "frozenset",
        "hasattr",
        "hex",
        "int",
        "isinstance",
        "issubclass",
        "iter",
        "len",
        "list",
        "map",
        "max",
        "min",
        "next",
        "object",
        "oct",
        "ord",
        "pow",
        "print",
        "range",
        "repr",
        "reversed",
        "round",
        "set",
        "slice",
        "sorted",
        "str",
        "sum",
        "super",
        "tuple",
        "type",
        "zip",
    }
    safe = {name: getattr(builtins, name) for name in names}
    safe["__import__"] = _safeImport
    safe["open"] = _safeOpenFactory()
    return safe
