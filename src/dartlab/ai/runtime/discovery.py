"""설치형 에이전트 CLI 발견과 버전 점검."""

from __future__ import annotations

import re
import shutil
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .contracts import RuntimeDescriptor, RuntimeProbe, nowIso
from .probeCache import ProbeCache
from .registry import loadRuntimeRegistry

_PROBE_CACHE = ProbeCache()
# 인증 probe 캐시. 형제 probe(버전·MCP)는 둘 다 TTL 캐시를 갖는데 인증만 없어서 상태
# 조회마다 CLI 를 다시 실행했다(실측 2026-08-04: 캐시 경로 상태 API 가 1.01초). TTL 은
# 형제와 같은 15초.
_AUTH_CACHE: dict[str, tuple[float, dict[str, object]]] = {}
_AUTH_CACHE_LOCK = threading.Lock()
_AUTH_CACHE_TTL_SECONDS = 15.0


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

    런타임별 probe 는 서로 독립인 CLI 실행이라 병렬로 돌린다. 순차 실행은 런타임 수에
    비례해 상태 조회를 늘렸다(실측 2026-08-04: 상태 refresh 11.9초). 반환은 레지스트리
    순서를 유지해 화면 카드 순서가 실행 순서에 흔들리지 않는다. probe 캐시는 자체 lock 을
    갖고 있어 동시 접근이 안전하다.
    """
    descriptors = list(loadRuntimeRegistry().values())
    if len(descriptors) < 2:
        return [probeRuntime(item, refresh=refresh) for item in descriptors]
    with ThreadPoolExecutor(max_workers=len(descriptors), thread_name_prefix="dartlab-runtime-probe") as pool:
        return list(pool.map(lambda item: probeRuntime(item, refresh=refresh), descriptors))


def probeRuntimeAuth(
    descriptor: RuntimeDescriptor,
    *,
    executable: str | None = None,
    refresh: bool = False,
) -> dict[str, object]:
    """CLI 인증 여부만 판정하며 계정 식별자와 원문 출력은 반환하지 않는다.

    형제 probe 와 같은 TTL 캐시를 쓴다. 인증 상태는 사용자가 CLI 에서 로그인할 때만
    바뀌므로 상태 조회마다 CLI 를 재실행할 이유가 없다.
    """
    if not descriptor.authProbeArgs or not descriptor.authSuccessPattern:
        return {"state": "unsupported", "authenticated": None, "checkedAt": nowIso()}
    if not refresh:
        with _AUTH_CACHE_LOCK:
            cached = _AUTH_CACHE.get(descriptor.runtimeId)
            if cached and time.monotonic() - cached[0] <= _AUTH_CACHE_TTL_SECONDS:
                return dict(cached[1])
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
        result: dict[str, object] = {
            "state": "authenticated" if authenticated else "authRequired",
            "authenticated": authenticated,
            "checkedAt": nowIso(),
        }
    except (OSError, subprocess.SubprocessError):
        result = {"state": "unavailable", "authenticated": False, "checkedAt": nowIso()}
    with _AUTH_CACHE_LOCK:
        _AUTH_CACHE[descriptor.runtimeId] = (time.monotonic(), result)
    return dict(result)


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
