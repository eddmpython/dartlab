"""설치형 에이전트 CLI 발견과 버전 점검."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .contracts import RuntimeDescriptor, RuntimeProbe
from .probeCache import ProbeCache
from .registry import loadRuntimeRegistry

_PROBE_CACHE = ProbeCache()


def discoverExecutable(descriptor: RuntimeDescriptor) -> str | None:
    """Sig: discoverExecutable(descriptor) -> str | None.

    Args: descriptor는 실행 파일 후보를 가진 매니페스트다.
    Returns: 발견한 절대 실행 경로 또는 None이다.
    Example: `path = discoverExecutable(descriptor)`.
    """
    for candidate in descriptor.executableCandidates:
        found = shutil.which(candidate)
        if found:
            return str(Path(found).resolve())
    return None


def probeRuntime(descriptor: RuntimeDescriptor, *, refresh: bool = False) -> RuntimeProbe:
    """Sig: probeRuntime(descriptor, *, refresh=False) -> RuntimeProbe.

    Args: descriptor와 캐시 무시 여부를 받는다.
    Returns: 설치 및 버전 상태다.
    Raises: 런타임 오류는 probe의 detail로 변환되어 전파되지 않는다.
    Example: `probeRuntime(registry["codex"])`.
    """
    if not refresh and (cached := _PROBE_CACHE.get(descriptor.runtimeId)) is not None:
        return cached
    executable = discoverExecutable(descriptor)
    if executable is None:
        return _PROBE_CACHE.put(RuntimeProbe(descriptor.runtimeId, "missing"))
    try:
        completed = subprocess.run(
            [executable, *descriptor.versionArgs],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
            shell=False,
            check=False,
        )
        output = (completed.stdout or completed.stderr).strip().splitlines()
        if completed.returncode != 0:
            return _PROBE_CACHE.put(
                RuntimeProbe(descriptor.runtimeId, "unavailable", executable, detail=(output[0] if output else None))
            )
        return _PROBE_CACHE.put(
            RuntimeProbe(descriptor.runtimeId, "ready", executable, version=(output[0] if output else "unknown"))
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return _PROBE_CACHE.put(RuntimeProbe(descriptor.runtimeId, "unavailable", executable, detail=str(exc)))


def probeAllRuntimes(*, refresh: bool = False) -> list[RuntimeProbe]:
    """Sig: probeAllRuntimes(*, refresh=False) -> list[RuntimeProbe].

    Args: refresh는 TTL 캐시 무시 여부다.
    Returns: 레지스트리 순서의 모든 probe다.
    Example: `ready = [p for p in probeAllRuntimes() if p.state == "ready"]`.
    """
    return [probeRuntime(item, refresh=refresh) for item in loadRuntimeRegistry().values()]
