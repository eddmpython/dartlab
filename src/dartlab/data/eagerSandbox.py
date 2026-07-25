"""Eager continuation child를 offline, read-only 실행 경계로 고정한다.

Capabilities:
    Refresh 환경 차단, strict offline socket guard, source filesystem write 차단을 제공한다.

Args:
    ``enforceProcessSandbox``는 parent가 만든 단일 artifact path를 받는다.

Returns:
    없음. Child process 전역에 fail-closed guard를 설치한다.

Raises:
    EagerSandboxViolation: 허용 artifact 밖 write 또는 offline 해제 시도.

Example:
    ``enforceProcessSandbox(parentArtifactPath)``.

Guide:
    Owner import 전에 한 번 호출하고 process 종료까지 해제하지 않는다.

When:
    Mixed continuation이 callable 또는 engine axis를 fresh child에서 실행할 때 사용한다.

How:
    Python write primitive와 core offlineGuard를 process-local로 패치한다.

See Also:
    ``dartlab.data.eagerProcess``과 ``dartlab.core.offlineGuard``.

Requires:
    Artifact file과 그 private parent directory는 parent가 미리 만들어야 한다.

AI Context:
    Query params나 owner code는 refresh와 network guard를 해제할 수 없다.

Security Boundary:
    설치된 trusted owner의 우발적인 network와 file write를 차단한다. Windows Job
    Object와 Python audit hook은 임의 native syscall, ctypes 공격을 막는 OS sandbox가
    아니다.
"""

from __future__ import annotations

import builtins
import importlib
import io
import os
import sys
from pathlib import Path
from typing import Any

_WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_TRUNC | getattr(os, "O_TMPFILE", 0)
_ARROW_PARQUET_MODULE = "pyarrow." + "parquet"


class EagerSandboxViolation(RuntimeError):
    """Eager child가 read-only 또는 strict offline 경계를 넘었다."""

    code = "PAGEABLE_EAGER_WRITE_BLOCKED"


def _patchAttributes(target: Any, names: tuple[str, ...], replacement: Any) -> None:
    for name in names:
        if hasattr(target, name):
            try:
                setattr(target, name, replacement)
            except (AttributeError, TypeError):
                raise EagerSandboxViolation(
                    f"known native writer를 차단하지 못했습니다: {type(target).__name__}.{name}"
                ) from None


def _loadedModule(name: str) -> Any | None:
    module = sys.modules.get(name)
    spec = getattr(module, "__spec__", None)
    if module is None or getattr(spec, "_initializing", False):
        return None
    return module


def _patchLoadedWriters(
    denyWriter: Any,
    patchedModules: set[str],
) -> None:
    """이미 import된 native dataframe writer를 patch하고 future import hook과 결합한다."""

    polars = _loadedModule("polars")
    if (
        polars is not None
        and "polars" not in patchedModules
        and all(hasattr(polars, name) for name in ("DataFrame", "LazyFrame", "Series"))
    ):
        _patchAttributes(
            polars.DataFrame,
            tuple(name for name in dir(polars.DataFrame) if name.startswith("write_") or name == "serialize"),
            denyWriter,
        )
        _patchAttributes(
            polars.LazyFrame,
            tuple(name for name in dir(polars.LazyFrame) if name.startswith("sink_") or name == "serialize"),
            denyWriter,
        )
        _patchAttributes(polars.Series, ("serialize",), denyWriter)
        patchedModules.add("polars")

    numpy = _loadedModule("numpy")
    if numpy is not None and "numpy" not in patchedModules and hasattr(numpy, "save"):
        _patchAttributes(
            numpy,
            ("memmap", "save", "savetxt", "savez", "savez_compressed"),
            denyWriter,
        )
        patchedModules.add("numpy")
    numpyFormat = _loadedModule("numpy.lib.format")
    if numpyFormat is not None and "numpy.lib.format" not in patchedModules:
        _patchAttributes(
            numpyFormat,
            (
                "open_memmap",
                "write_array",
                "write_array_header_1_0",
                "write_array_header_2_0",
            ),
            denyWriter,
        )
        patchedModules.add("numpy.lib.format")

    pandas = _loadedModule("pandas")
    if (
        pandas is not None
        and "pandas" not in patchedModules
        and all(hasattr(pandas, name) for name in ("DataFrame", "Series"))
    ):
        pandasWriters = (
            "to_clipboard",
            "to_csv",
            "to_excel",
            "to_feather",
            "to_gbq",
            "to_hdf",
            "to_html",
            "to_json",
            "to_latex",
            "to_markdown",
            "to_orc",
            "to_parquet",
            "to_pickle",
            "to_sql",
            "to_stata",
            "to_xml",
        )
        _patchAttributes(pandas.DataFrame, pandasWriters, denyWriter)
        _patchAttributes(pandas.Series, pandasWriters, denyWriter)
        _patchAttributes(
            pandas,
            ("ExcelWriter", "HDFStore", "to_pickle"),
            denyWriter,
        )
        patchedModules.add("pandas")

    pyarrow = _loadedModule("pyarrow")
    if pyarrow is not None and "pyarrow" not in patchedModules and hasattr(pyarrow, "output_stream"):
        _patchAttributes(
            pyarrow,
            ("OSFile", "PythonFile", "memory_map", "output_stream"),
            denyWriter,
        )
        patchedModules.add("pyarrow")
    moduleWriters = {
        "pyarrow.csv": ("write_csv",),
        "pyarrow.dataset": ("write_dataset",),
        "pyarrow.feather": ("write_feather",),
        "pyarrow.fs": ("copy_files",),
        "pyarrow.orc": ("ORCWriter", "write_table"),
        _ARROW_PARQUET_MODULE: (
            "ParquetWriter",
            "write_metadata",
            "write_table",
            "write_to_dataset",
        ),
    }
    for moduleName, names in moduleWriters.items():
        module = _loadedModule(moduleName)
        if module is not None and moduleName not in patchedModules:
            _patchAttributes(module, names, denyWriter)
            patchedModules.add(moduleName)


def _absolute(value: Any) -> str | None:
    if isinstance(value, int):
        return None
    try:
        return os.path.normcase(os.path.abspath(os.fspath(value)))
    except (TypeError, ValueError, OSError):
        return None


def enforceProcessSandbox(artifactPath: Path) -> None:
    """Owner 또는 eager child에 strict offline과 artifact-only write guard를 설치한다."""

    allowed = _absolute(artifactPath)
    if allowed is None or not artifactPath.is_file():
        raise EagerSandboxViolation("parent eager artifact가 준비되지 않았습니다")
    os.environ["DARTLAB_NO_REFRESH"] = "1"
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    sys.dont_write_bytecode = True

    from dartlab.core import offlineGuard

    offlineGuard.enforceOffline(strict=True)

    def denyRelease() -> None:
        """Child 생존 중 offline guard 해제를 거부한다."""
        raise EagerSandboxViolation("eager child offline guard는 해제할 수 없습니다")

    offlineGuard.releaseOffline = denyRelease

    originalImport = builtins.__import__
    originalImportModule = importlib.import_module
    originalOpen = builtins.open
    originalIoOpen = io.open
    originalOsOpen = os.open
    originalRename = os.rename
    originalReplace = os.replace
    originalRemove = os.remove
    originalUnlink = os.unlink
    allowedDescriptors: set[int] = set()

    def requireAllowed(path: Any) -> None:
        """쓰기 대상이 parent가 허용한 artifact인지 검증한다."""
        if isinstance(path, int) and path in allowedDescriptors:
            return
        if _absolute(path) != allowed:
            raise EagerSandboxViolation(f"eager child source write 차단: path={path!r}")

    def rememberDescriptor(stream: Any) -> Any:
        """허용 artifact의 열린 descriptor를 후속 감사에 등록한다."""
        try:
            descriptor = stream if isinstance(stream, int) else stream.fileno()
        except (AttributeError, OSError, ValueError):
            return stream
        if isinstance(descriptor, int):
            allowedDescriptors.add(descriptor)
        return stream

    def auditWrite(event: str, args: tuple[Any, ...]) -> None:
        """Python audit event에서 filesystem 변경을 fail-closed로 막는다."""
        if event == "open":
            path = args[0] if args else None
            mode = args[1] if len(args) > 1 else None
            flags = args[2] if len(args) > 2 else 0
            writeMode = isinstance(mode, str) and any(flag in mode for flag in ("w", "a", "x", "+"))
            writeFlags = isinstance(flags, int) and bool(flags & _WRITE_FLAGS)
            if writeMode or writeFlags:
                requireAllowed(path)
            return
        if event in {"os.rename", "os.replace"}:
            if len(args) < 2:
                raise EagerSandboxViolation("eager child rename 인자가 유효하지 않습니다")
            requireAllowed(args[0])
            requireAllowed(args[1])
            return
        if event in {
            "os.chmod",
            "os.chown",
            "os.link",
            "os.mkdir",
            "os.remove",
            "os.removexattr",
            "os.rmdir",
            "os.setxattr",
            "os.symlink",
            "os.truncate",
            "os.unlink",
            "os.utime",
        }:
            if not args:
                raise EagerSandboxViolation(f"eager child filesystem event 인자가 없습니다: event={event}")
            requireAllowed(args[0])
            return
        if event == "sqlite3.connect":
            database = args[0] if args else None
            inMemory = database == ":memory:" or (
                isinstance(database, str) and database.startswith("file:") and "mode=memory" in database
            )
            if not inMemory:
                requireAllowed(database)
            return
        if event in {
            "os.exec",
            "os.posix_spawn",
            "os.spawn",
            "os.system",
            "subprocess.Popen",
        }:
            raise EagerSandboxViolation(f"eager child process 생성 차단: event={event}")

    sys.addaudithook(auditWrite)

    def guardedOpen(file, mode="r", *args, **kwargs):
        """Built-in open 쓰기를 허용 artifact 하나로 제한한다."""
        writing = any(flag in mode for flag in ("w", "a", "x", "+"))
        if writing:
            requireAllowed(file)
        stream = originalOpen(file, mode, *args, **kwargs)
        return rememberDescriptor(stream) if writing else stream

    def guardedIoOpen(file, mode="r", *args, **kwargs):
        """io.open 쓰기를 허용 artifact 하나로 제한한다."""
        writing = any(flag in mode for flag in ("w", "a", "x", "+"))
        if writing:
            requireAllowed(file)
        stream = originalIoOpen(file, mode, *args, **kwargs)
        return rememberDescriptor(stream) if writing else stream

    def guardedOsOpen(path, flags, *args, **kwargs):
        """os.open 쓰기를 허용 artifact 하나로 제한한다."""
        if flags & _WRITE_FLAGS:
            requireAllowed(path)
            return rememberDescriptor(originalOsOpen(path, flags, *args, **kwargs))
        return originalOsOpen(path, flags, *args, **kwargs)

    def guardedMkdir(path, *args, **kwargs):
        """새 directory 생성을 거부하고 기존 directory 확인만 허용한다."""
        if not os.path.isdir(path):
            raise EagerSandboxViolation(f"eager child directory write 차단: path={os.fspath(path)!r}")
        return None

    def guardedMakedirs(name, mode=0o777, existOk=False, **kwargs):
        """재귀 directory 생성을 거부하고 기존 directory 확인만 허용한다."""
        if "exist_ok" in kwargs:
            if existOk is not False:
                raise TypeError("existOk과 exist_ok를 동시에 지정할 수 없습니다")
            existOk = kwargs.pop("exist_ok")
        if kwargs:
            unknown = next(iter(kwargs))
            raise TypeError(f"예상하지 못한 keyword argument: {unknown}")
        del mode, existOk
        if not os.path.isdir(name):
            raise EagerSandboxViolation(f"eager child directory write 차단: path={os.fspath(name)!r}")
        return None

    def guardedRename(source, destination, *args, **kwargs):
        """Rename 양쪽 경로를 허용 artifact로 제한한다."""
        requireAllowed(source)
        requireAllowed(destination)
        return originalRename(source, destination, *args, **kwargs)

    def guardedReplace(source, destination, *args, **kwargs):
        """Replace 양쪽 경로를 허용 artifact로 제한한다."""
        requireAllowed(source)
        requireAllowed(destination)
        return originalReplace(source, destination, *args, **kwargs)

    def guardedRemove(path, *args, **kwargs):
        """Remove 대상을 허용 artifact로 제한한다."""
        requireAllowed(path)
        return originalRemove(path, *args, **kwargs)

    def guardedUnlink(path, *args, **kwargs):
        """Unlink 대상을 허용 artifact로 제한한다."""
        requireAllowed(path)
        return originalUnlink(path, *args, **kwargs)

    def guardedRmdir(path, *args, **kwargs):
        """Child의 directory 삭제를 항상 거부한다."""
        raise EagerSandboxViolation(f"eager child directory 삭제 차단: path={os.fspath(path)!r}")

    def denyWriter(*args, **kwargs):
        """알려진 native dataframe writer와 sink 호출을 거부한다."""
        del args, kwargs
        raise EagerSandboxViolation("eager child native dataframe writer와 sink는 사용할 수 없습니다")

    patchedModules: set[str] = set()

    def guardedImport(
        name,
        globals=None,
        locals=None,
        fromlist=(),
        level=0,
    ):
        """Import 뒤 새로 로드된 native writer도 즉시 차단한다."""
        module = originalImport(name, globals, locals, fromlist, level)
        _patchLoadedWriters(denyWriter, patchedModules)
        return module

    def guardedImportModule(name, package=None):
        """importlib 경로로 로드된 native writer도 즉시 차단한다."""
        module = originalImportModule(name, package)
        _patchLoadedWriters(denyWriter, patchedModules)
        return module

    builtins.__import__ = guardedImport
    importlib.import_module = guardedImportModule
    builtins.open = guardedOpen
    io.open = guardedIoOpen
    os.open = guardedOsOpen
    os.mkdir = guardedMkdir
    os.makedirs = guardedMakedirs
    os.rename = guardedRename
    os.replace = guardedReplace
    os.remove = guardedRemove
    os.unlink = guardedUnlink
    os.rmdir = guardedRmdir
    _patchLoadedWriters(denyWriter, patchedModules)


def enforceEagerSandbox(artifactPath: Path) -> None:
    """기존 eager child 호출면에서 공통 process sandbox를 설치한다."""

    enforceProcessSandbox(artifactPath)


__all__ = [
    "EagerSandboxViolation",
    "enforceEagerSandbox",
    "enforceProcessSandbox",
]
