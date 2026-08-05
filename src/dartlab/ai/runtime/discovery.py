"""설치형 에이전트 CLI 발견과 버전 점검."""

from __future__ import annotations

import re
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .contracts import RuntimeDescriptor, RuntimeProbe, nowIso
from .probeCache import (
    ProbeCache,
    SwrCache,
    authProbeKey,
    backgroundRefresher,
    retryUntilDetermined,
    versionProbeKey,
)
from .registry import loadRuntimeRegistry

_PROBE_CACHE = ProbeCache()
# 인증 probe 캐시. 형제 probe(버전·MCP)와 같은 stale-while-revalidate 계약을 쓴다.
# TTL 은 신선도 표시일 뿐이라 만료돼도 마지막 실측값을 버리지 않는다.
_AUTH_CACHE = SwrCache(15.0)
_AUTH_CACHE_LOCK = _AUTH_CACHE.lock
_AUTH_CACHE_TTL_SECONDS = _AUTH_CACHE.ttlSeconds
# 버전 probe 상한. 형제 probe 는 인증 8초·MCP 20초인데 여기만 5초라 홀로 짧았다.
# `cline --version` 이 단독으로도 3.7초라(실측 2026-08-05) 기기가 조금만 바빠도 상한을
# 넘겨 멀쩡한 CLI 가 unavailable 로 기록됐다. 상한이 CLI 대신 기기 부하를 재고 있었다.
# 형제 중 최솟값과 같은 8 초로 맞춘다. probe 는 화면 대기 경로 밖이라 사용자 비용은 없다.
_VERSION_PROBE_TIMEOUT_SECONDS = 8


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


def _measureRuntime(descriptor: RuntimeDescriptor) -> RuntimeProbe:
    """공식 CLI 를 실제로 실행해 설치와 버전 상태를 측정한다.

    상한 초과는 "동작하지 않는다" 가 아니라 "확인하지 못했다" 다. 둘을 같은 unavailable
    로 적으면 기기가 바쁠 때 멀쩡한 CLI 가 고장난 것으로 화면에 뜬다(실측 2026-08-05).
    실행 파일은 이미 찾았으므로 설치됐다는 사실만은 그대로 남긴다.
    """
    executable = discoverExecutable(descriptor)
    if executable is None:
        return RuntimeProbe(descriptor.runtimeId, "missing")
    try:
        completed = subprocess.run(
            [executable, *descriptor.versionArgs],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=_VERSION_PROBE_TIMEOUT_SECONDS,
            shell=False,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return RuntimeProbe(
            descriptor.runtimeId,
            "unknown",
            executable,
            detail=f"버전 확인이 {_VERSION_PROBE_TIMEOUT_SECONDS}초 안에 끝나지 않았습니다",
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return RuntimeProbe(descriptor.runtimeId, "unavailable", executable, detail=str(exc))
    output = (completed.stdout or completed.stderr).strip().splitlines()
    if completed.returncode != 0:
        return RuntimeProbe(descriptor.runtimeId, "unavailable", executable, detail=(output[0] if output else None))
    return RuntimeProbe(descriptor.runtimeId, "ready", executable, version=(output[0] if output else "unknown"))


def probeRuntime(descriptor: RuntimeDescriptor, *, refresh: bool = False, blocking: bool = True) -> RuntimeProbe:
    """Sig: probeRuntime(descriptor, *, refresh=False, blocking=True) -> RuntimeProbe.

    Args: descriptor와 캐시 무시 여부, 측정 대기 여부를 받는다.
    Returns: 설치 및 버전 상태다.
    Raises: 런타임 오류는 probe의 detail로 변환되어 전파되지 않는다.
    Example: `probeRuntime(registry["codex"])`.

    ``blocking=False`` 는 표시 경로용이다. 아는 값이 있으면 만료됐어도 즉시 돌려주고
    갱신은 백그라운드로 보낸다. 한 번도 측정한 적이 없으면 실행 파일 발견 결과만 붙인
    ``unknown`` 을 돌려준다. 설치되지 않은 CLI 를 설치됐다고 말하지 않는다.
    """
    if refresh:
        return _PROBE_CACHE.put(_measureRuntime(descriptor))
    entry = _PROBE_CACHE.peek(descriptor.runtimeId)
    if entry is not None and entry.fresh:
        return entry.value
    if blocking:
        return _PROBE_CACHE.put(_measureRuntime(descriptor))
    backgroundRefresher().submit(
        versionProbeKey(descriptor.runtimeId),
        lambda: retryUntilDetermined(
            lambda: _PROBE_CACHE.put(_measureRuntime(descriptor)),
            lambda value: value.state != "unknown",
        ),
    )
    if entry is not None:
        return entry.value
    return RuntimeProbe(descriptor.runtimeId, "unknown", discoverExecutable(descriptor))


def probeAllRuntimes(*, refresh: bool = False, blocking: bool = True) -> list[RuntimeProbe]:
    """Sig: probeAllRuntimes(*, refresh=False, blocking=True) -> list[RuntimeProbe].

    Args: refresh는 재측정 여부, blocking은 측정 대기 여부다.
    Returns: 레지스트리 순서의 모든 probe다.
    Example: `ready = [p for p in probeAllRuntimes() if p.state == "ready"]`.

    측정이 필요한 경로에서는 런타임별 probe 가 서로 독립인 CLI 실행이라 병렬로 돌린다.
    순차 실행은 런타임 수에 비례해 상태 조회를 늘렸다(실측 2026-08-04: 상태 refresh
    11.9초). 반환은 레지스트리 순서를 유지해 화면 카드 순서가 실행 순서에 흔들리지 않는다.
    비차단 경로는 캐시 조회와 예약뿐이라 스레드를 쓰지 않는다.
    """
    descriptors = list(loadRuntimeRegistry().values())
    if not blocking and not refresh:
        return [probeRuntime(item, blocking=False) for item in descriptors]
    if len(descriptors) < 2:
        return [probeRuntime(item, refresh=refresh) for item in descriptors]
    with ThreadPoolExecutor(max_workers=len(descriptors), thread_name_prefix="dartlab-runtime-probe") as pool:
        return list(pool.map(lambda item: probeRuntime(item, refresh=refresh), descriptors))


def _measureRuntimeAuth(descriptor: RuntimeDescriptor, executable: str | None) -> dict[str, object]:
    """공식 CLI 인증 명령을 실제로 실행하고 판정 결과만 남긴다."""
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
    except subprocess.TimeoutExpired:
        # 상한 초과는 로그인 실패가 아니라 미판정이다. 판정으로 적으면 기기 부하가 로그인
        # 상태를 뒤집는다.
        return {"state": "unknown", "authenticated": None, "checkedAt": nowIso(), "undetermined": True}
    except (OSError, subprocess.SubprocessError):
        return {"state": "unavailable", "authenticated": False, "checkedAt": nowIso()}
    output = f"{completed.stdout or ''}\n{completed.stderr or ''}"
    pattern = descriptor.authSuccessPattern or ""
    authenticated = completed.returncode == 0 and re.search(pattern, output) is not None
    return {
        "state": "authenticated" if authenticated else "authRequired",
        "authenticated": authenticated,
        "checkedAt": nowIso(),
    }


def probeRuntimeAuth(
    descriptor: RuntimeDescriptor,
    *,
    executable: str | None = None,
    refresh: bool = False,
    blocking: bool = True,
) -> dict[str, object]:
    """CLI 인증 여부만 판정하며 계정 식별자와 원문 출력은 반환하지 않는다.

    형제 probe 와 같은 stale-while-revalidate 캐시를 쓴다. 인증 상태는 사용자가 CLI 에서
    로그인할 때만 바뀌므로 상태 조회마다 CLI 를 재실행할 이유가 없다. ``blocking=False``
    는 마지막 실측값을 즉시 주고 갱신을 백그라운드로 보내며, 기록이 없으면 확인 중임을
    알리는 ``unknown`` 을 돌려준다.
    """
    if not descriptor.authProbeArgs or not descriptor.authSuccessPattern:
        return {"state": "unsupported", "authenticated": None, "checkedAt": nowIso()}

    def _remember() -> dict[str, object]:
        """인증을 실제로 측정하고 판정에 성공했을 때만 기존 값을 갱신한다."""
        measured = _measureRuntimeAuth(descriptor, executable)
        stored = _AUTH_CACHE.put(descriptor.runtimeId, measured, determined=not measured.get("undetermined"))
        return dict(stored)

    if refresh:
        return _remember()
    entry = _AUTH_CACHE.peek(descriptor.runtimeId)
    if entry is not None and entry.fresh:
        return dict(entry.value)
    if blocking:
        return _remember()
    backgroundRefresher().submit(
        authProbeKey(descriptor.runtimeId),
        lambda: retryUntilDetermined(_remember, lambda value: not value.get("undetermined")),
    )
    if entry is not None:
        return dict(entry.value)
    return {"state": "unknown", "authenticated": None, "checkedAt": nowIso(), "pending": True}


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
