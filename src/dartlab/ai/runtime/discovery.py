"""설치형 에이전트 CLI 발견과 버전 점검."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

from .contracts import RuntimeDescriptor, RuntimeProbe, nowIso
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


def probeRuntimeAuth(descriptor: RuntimeDescriptor, *, executable: str | None = None) -> dict[str, object]:
    """CLI 인증 여부만 판정하며 계정 식별자와 원문 출력은 반환하지 않는다."""
    if not descriptor.authProbeArgs or not descriptor.authSuccessPattern:
        return {"state": "unsupported", "authenticated": None, "checkedAt": nowIso()}
    resolved = executable or discoverExecutable(descriptor)
    if resolved is None:
        return {"state": "missing", "authenticated": False, "checkedAt": nowIso()}
    try:
        completed = subprocess.run(
            [resolved, *descriptor.authProbeArgs],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=8,
            shell=False,
            check=False,
        )
        output = f"{completed.stdout or ''}\n{completed.stderr or ''}"
        authenticated = completed.returncode == 0 and re.search(descriptor.authSuccessPattern, output) is not None
        return {
            "state": "authenticated" if authenticated else "authRequired",
            "authenticated": authenticated,
            "checkedAt": nowIso(),
        }
    except (OSError, subprocess.SubprocessError):
        return {"state": "unavailable", "authenticated": False, "checkedAt": nowIso()}


def runtimeLoginArgv(runtimeId: str) -> tuple[str, ...]:
    """매니페스트와 발견된 실행 파일에서 공식 대화형 로그인 argv를 만든다."""
    from .drivers.base import runtimeExecutableArgv

    descriptor = loadRuntimeRegistry()[runtimeId]
    if not descriptor.loginArgs:
        raise ValueError(f"{runtimeId}는 자동 안내 가능한 로그인 명령이 없습니다")
    executable = discoverExecutable(descriptor)
    if executable is None:
        raise FileNotFoundError(runtimeId)
    return (*runtimeExecutableArgv(descriptor, executable), *descriptor.loginArgs)
