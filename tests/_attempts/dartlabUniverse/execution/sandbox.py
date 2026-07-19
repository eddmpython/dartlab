"""격리 worker 환경과 Python audit write guard."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class SandboxViolation(PermissionError):
    pass


@dataclass(slots=True)
class AuditGuard:
    allowlist: tuple[Path, ...]
    events: list[tuple[str, str]] = field(default_factory=list)
    installed: bool = False

    def _allowed(self, rawPath: Any) -> bool:
        if isinstance(rawPath, int):
            return True
        try:
            path = Path(os.fspath(rawPath)).resolve()
        except (TypeError, ValueError, OSError):
            return False
        return any(path == root or path.is_relative_to(root) for root in self.allowlist)

    def hook(self, event: str, args: tuple[Any, ...]) -> None:
        mutatingPath = None
        if event == "open" and args:
            mode = args[1] if len(args) > 1 else "r"
            flags = args[2] if len(args) > 2 else 0
            writeMode = isinstance(mode, str) and any(token in mode for token in "wax+")
            writeFlags = isinstance(flags, int) and bool(
                flags
                & (
                    getattr(os, "O_WRONLY", 1)
                    | getattr(os, "O_RDWR", 2)
                    | getattr(os, "O_CREAT", 0x100)
                    | getattr(os, "O_TRUNC", 0x200)
                    | getattr(os, "O_APPEND", 8)
                )
            )
            if writeMode or writeFlags:
                mutatingPath = args[0]
        elif (
            event
            in {
                "os.remove",
                "os.rmdir",
                "os.mkdir",
                "os.rename",
                "os.replace",
                "os.chmod",
                "os.truncate",
                "shutil.copyfile",
                "shutil.copymode",
                "shutil.copystat",
            }
            and args
        ):
            mutatingPath = args[0]
        if mutatingPath is not None:
            self.events.append((event, os.fspath(mutatingPath)))
            if not self._allowed(mutatingPath):
                raise SandboxViolation(f"WRITE_OUTSIDE_ALLOWLIST:{event}")
            if event in {"os.rename", "os.replace", "shutil.copyfile"} and len(args) > 1 and not self._allowed(args[1]):
                raise SandboxViolation(f"WRITE_OUTSIDE_ALLOWLIST:{event}:destination")
        if event.startswith("subprocess") or event in {"os.system", "os.spawn", "os.posix_spawn"}:
            self.events.append((event, "process"))
            raise SandboxViolation(f"SUBPROCESS_BLOCKED:{event}")
        if event.startswith("socket"):
            self.events.append((event, "network"))
            raise SandboxViolation(f"NETWORK_BLOCKED:{event}")


def buildWorkerEnvironment(workerRoot: str | Path) -> dict[str, str]:
    """모든 일반 write 위치를 worker root 아래로 강제한다."""
    root = Path(workerRoot).resolve()
    paths = {
        "DARTLAB_DATA_DIR": root / "data",
        "DARTLAB_LINEAGE_DIR": root / "lineage",
        "HOME": root / "home",
        "USERPROFILE": root / "home",
        "XDG_CACHE_HOME": root / "cache",
        "TEMP": root / "tmp",
        "TMP": root / "tmp",
        "UNIVERSE_OUTPUT_DIR": root / "output",
        "PYTHONPYCACHEPREFIX": root / "pycache",
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    secretMarkers = ("API_KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL", "PRIVATE_KEY")
    environment = {
        key: value for key, value in os.environ.items() if not any(marker in key.upper() for marker in secretMarkers)
    }
    environment.update({key: path.as_posix() for key, path in paths.items()})
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["DARTLAB_UNIVERSE_WORKER_ROOT"] = root.as_posix()
    return environment


def installWriteGuard(allowlist: tuple[str | Path, ...]) -> AuditGuard:
    """현재 process에 audit hook을 설치한다. Worker process 안에서만 호출해야 한다."""
    roots = tuple(Path(path).resolve() for path in allowlist)
    if not roots:
        raise ValueError("write allowlist는 비어 있을 수 없음")
    guard = AuditGuard(allowlist=roots, installed=True)
    sys.addaudithook(guard.hook)
    return guard


def protectedPathDigests(paths: tuple[str | Path, ...]) -> tuple[tuple[str, str], ...]:
    """보호 경로의 regular file 상대경로와 byte를 재귀 digest한다."""
    import hashlib

    records = []
    for raw in paths:
        root = Path(raw).resolve()
        if not root.exists():
            records.append((root.as_posix(), "MISSING"))
            continue
        if root.is_file():
            records.append((root.as_posix(), hashlib.sha256(root.read_bytes()).hexdigest()))
            continue
        digest = hashlib.sha256()
        for path in sorted(item for item in root.rglob("*") if item.is_file() and not item.is_symlink()):
            digest.update(path.relative_to(root).as_posix().encode("utf-8"))
            digest.update(b"\0")
            digest.update(hashlib.sha256(path.read_bytes()).digest())
        records.append((root.as_posix(), digest.hexdigest()))
    return tuple(records)
