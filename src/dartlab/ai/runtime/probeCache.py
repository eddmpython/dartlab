"""런타임 probe 의 stale-while-revalidate 캐시와 단일 비행 백그라운드 갱신기."""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any

from .contracts import RuntimeProbe

logger = logging.getLogger(__name__)

# 동시에 띄우는 CLI probe 수의 상한. 각 probe 는 Node CLI 콜드스타트라 대기가 아니라
# CPU 를 쓴다. 전부 한꺼번에 띄우면 서로 CPU 를 뺏어 멀쩡한 CLI 가 자기 상한을 넘긴다
# (실측 2026-08-05: 9 건 동시에서 `cline --version` 5 초 상한 초과 오판, 전체 18.5초).
# 겹치기의 목적은 대기를 포개는 것이지 동시 기동 수를 늘리는 게 아니다.
PROBE_CONCURRENCY = 3
# 백그라운드 실측이 판정에 실패했을 때의 재시도. 부하로 인한 일시 실패를 곧장 "확인 실패"
# 로 굳히면 멀쩡한 CLI 앞에서 사용자가 버튼을 눌러야 한다(실측 2026-08-06: 서버 기동과
# 겹친 첫 실측에서 claude MCP·cline 버전이 상한 초과). 아무도 기다리지 않는 경로라
# 재시도 비용은 사용자에게 보이지 않는다. 화면 대기 경로는 재시도하지 않는다.
PROBE_RETRY_ATTEMPTS = 2
PROBE_RETRY_DELAY_SECONDS = 1.5


def versionProbeKey(runtimeId: str) -> str:
    """버전 probe 의 단일 비행 키다."""
    return f"version:{runtimeId}"


def authProbeKey(runtimeId: str) -> str:
    """인증 probe 의 단일 비행 키다."""
    return f"auth:{runtimeId}"


def mcpProbeKey(runtimeId: str) -> str:
    """DartLab MCP probe 의 단일 비행 키다."""
    return f"mcp:{runtimeId}"


def retryUntilDetermined(
    work: Callable[[], Any],
    isDetermined: Callable[[Any], bool],
    *,
    attempts: int = PROBE_RETRY_ATTEMPTS,
    delaySeconds: float = PROBE_RETRY_DELAY_SECONDS,
) -> Any:
    """Sig: retryUntilDetermined(work, isDetermined, *, attempts, delaySeconds) -> Any.

    Args: work 는 실측, isDetermined 는 판정 성립 여부 판별이다.
    Returns: 마지막 실측 결과다.
    Example: `retryUntilDetermined(measure, lambda probe: probe.state != "unknown")`.

    판정에 실패하면 짧게 쉬었다 다시 잰다. 상한 초과는 대개 그 순간 기기가 바빴다는
    뜻이고 잠시 뒤에는 성립한다. 백그라운드 전용이라 사용자 대기에 더해지지 않는다.
    """
    value = work()
    for _ in range(max(0, attempts - 1)):
        if isDetermined(value):
            return value
        time.sleep(delaySeconds)
        value = work()
    return value


@dataclass(frozen=True)
class CachedValue:
    """마지막으로 실측한 값과 그 값의 신선도, 그리고 판정 성립 여부."""

    value: Any
    storedAt: float
    fresh: bool
    determined: bool = True


class SwrCache:
    """TTL 을 폐기 시점이 아니라 신선도 표시로만 쓰는 캐시.

    Capabilities: 만료된 값도 버리지 않고 stale 표시와 함께 즉시 돌려준다.
    Args: ttlSeconds 는 값을 fresh 로 볼 시간이다.
    Returns: peek 은 신선도를 붙인 CachedValue, get 은 fresh 일 때만 값이다.
    Example: `entry = cache.peek("claude")`.
    Guide: 채우는 데 TTL 보다 오래 걸리는 probe 는 만료 즉시 폐기하면 캐시가 영원히 빈다.
        실측 2026-08-05 에서 상태 조회 1 회가 12~15 초인데 TTL 이 15 초라, 사람 속도로
        재방문하면 매번 전량 재측정이었다(15.5초 / 7.5초 / 12.8초). 값을 남겨 두면
        재방문은 즉시 답하고 갱신만 뒤에서 돈다.
    SeeAlso: `runtime.discovery`, `runtime.mcpBootstrap`.
    Requires: 저장 값은 호출자가 소유권을 나누지 않는 불변 또는 복사본이어야 한다.
    AIContext: 표시용 스냅샷과 실행 직전 판정은 다른 요구다. 후자는 blocking 경로를 쓴다.
    LLM Specifications: AntiPatterns=drop on expiry; OutputSchema=CachedValue;
        Prerequisites=none; Freshness=ttlSeconds; Dataflow=probe to snapshot;
        TargetMarkets=all.
    """

    def __init__(self, ttlSeconds: float = 15.0):
        self.ttlSeconds = ttlSeconds
        self._values: dict[str, CachedValue] = {}
        self._lock = threading.RLock()

    @property
    def lock(self) -> threading.RLock:
        """외부에서 캐시를 직접 검사할 때 잡을 재진입 lock 이다."""
        return self._lock

    def peek(self, key: str) -> CachedValue | None:
        """Sig: peek(key) -> CachedValue | None.

        Args: key 는 캐시 키다.
        Returns: 만료 여부를 fresh 로 표시한 마지막 실측값 또는 None 이다.
        Example: `entry = cache.peek("claude")`.
        """
        with self._lock:
            entry = self._values.get(key)
            if entry is None:
                return None
            return CachedValue(
                entry.value,
                entry.storedAt,
                time.monotonic() - entry.storedAt <= self.ttlSeconds,
                entry.determined,
            )

    def get(self, key: str) -> Any | None:
        """Sig: get(key) -> Any | None.

        Args: key 는 캐시 키다.
        Returns: TTL 안의 값이며 만료됐으면 None 이다.
        Example: `value = cache.get("claude")`.
        """
        entry = self.peek(key)
        return entry.value if entry is not None and entry.fresh else None

    def put(self, key: str, value: Any, *, determined: bool = True) -> Any:
        """Sig: put(key, value, *, determined=True) -> Any.

        Args: key 와 저장할 실측값, 그리고 이번 실측이 판정에 성공했는지다.
        Returns: 실제로 유효한 값(판정 실패면 기존 판정값)을 반환한다.
        Example: `cache.put("claude", probe)`.

        판정하지 못한 결과는 이미 판정된 값을 덮지 않는다. probe 실패는 "동작하지
        않는다" 가 아니라 "확인하지 못했다" 다. 그대로 덮으면 기기가 바쁠 때마다 멀쩡한
        CLI 가 고장난 것으로 기록된다(실측 2026-08-05: CPU 포화에서 `cline --version`
        상한 초과가 unavailable 로 남았다). 덮지 않으면 stale 로 남아 곧 다시 시도한다.
        """
        with self._lock:
            entry = self._values.get(key)
            if not determined and entry is not None and entry.determined:
                return entry.value
            self._values[key] = CachedValue(value, time.monotonic(), True, determined)
        return value

    def clear(self, key: str | None = None) -> None:
        """Sig: clear(key=None) -> None.

        Args: key 가 없으면 전체를 지운다.
        Returns: None.
        Example: `cache.clear("claude")`.
        """
        with self._lock:
            if key is None:
                self._values.clear()
            else:
                self._values.pop(key, None)

    def __contains__(self, key: object) -> bool:
        """만료 여부와 무관하게 실측 기록이 남아 있는지 알린다."""
        with self._lock:
            return key in self._values

    def __len__(self) -> int:
        """보관 중인 실측 기록 수다."""
        with self._lock:
            return len(self._values)

    def __iter__(self) -> Iterator[str]:
        """보관 중인 캐시 키를 순회한다."""
        with self._lock:
            return iter(list(self._values))


class BackgroundRefresher:
    """같은 키의 느린 probe 를 동시에 하나만 돌리는 단일 비행 실행기.

    Capabilities: 표시 경로가 기다리지 않도록 실측을 데몬 스레드로 밀어낸다.
    Args: maxWorkers 는 동시에 도는 probe 수다.
    Returns: submit 은 이번 호출이 실제로 작업을 띄웠는지 알린다.
    Example: `refresher.submit("mcp:claude", work)`.
    Guide: UI 가 짧은 주기로 폴링해도 CLI 프로세스가 중복 생성되지 않아야 한다.
    SeeAlso: `runtime.engine` 의 비차단 status.
    Requires: work 는 인자 없는 호출체이며 예외를 밖으로 던져도 안전하다.
    AIContext: 결과는 캐시에만 남는다. 호출자는 다음 조회에서 값을 본다.
    LLM Specifications: AntiPatterns=spawn per poll; OutputSchema=bool;
        Prerequisites=none; Freshness=on demand; Dataflow=key to daemon thread;
        TargetMarkets=all.
    """

    def __init__(self, maxWorkers: int = PROBE_CONCURRENCY):
        self._pool = ThreadPoolExecutor(max_workers=maxWorkers, thread_name_prefix="dartlab-probe-refresh")
        self._inflight: set[str] = set()
        self._lock = threading.Lock()

    def submit(self, key: str, work: Callable[[], Any]) -> bool:
        """Sig: submit(key, work) -> bool.

        Args: key 는 단일 비행 식별자이고 work 는 실제 probe 다.
        Returns: 이번 호출이 작업을 띄웠으면 True 다.
        Example: `refresher.submit("auth:codex", work)`.
        """
        with self._lock:
            if key in self._inflight:
                return False
            self._inflight.add(key)

        def _run() -> None:
            try:
                work()
            except Exception:  # noqa: BLE001 - 백그라운드 갱신 실패가 표시 경로를 죽이면 안 된다.
                logger.exception("런타임 probe 백그라운드 갱신 실패: %s", key)
            finally:
                with self._lock:
                    self._inflight.discard(key)

        try:
            self._pool.submit(_run)
        except RuntimeError:
            with self._lock:
                self._inflight.discard(key)
            return False
        return True

    def pending(self) -> frozenset[str]:
        """지금 백그라운드에서 도는 probe 키 집합이다."""
        with self._lock:
            return frozenset(self._inflight)

    def isPending(self, key: str) -> bool:
        """해당 키의 probe 가 백그라운드에서 도는 중인지 알린다."""
        with self._lock:
            return key in self._inflight

    def wait(self, timeoutSeconds: float = 30.0) -> bool:
        """Sig: wait(timeoutSeconds=30.0) -> bool.

        Args: timeoutSeconds 는 최대 대기 시간이다.
        Returns: 대기 안에 모든 작업이 끝났으면 True 다.
        Example: `refresher.wait(10.0)`.
        """
        deadline = time.monotonic() + timeoutSeconds
        while time.monotonic() < deadline:
            if not self.pending():
                return True
            time.sleep(0.02)
        return not self.pending()


_REFRESHER = BackgroundRefresher()


def backgroundRefresher() -> BackgroundRefresher:
    """Sig: backgroundRefresher() -> BackgroundRefresher.

    Args: 없음.
    Returns: 프로세스가 공유하는 단일 비행 갱신기다.
    Example: `backgroundRefresher().submit(key, work)`.
    """
    return _REFRESHER


class ProbeCache:
    """설치·버전 probe 전용 SwrCache 어댑터."""

    def __init__(self, ttlSeconds: float = 15.0):
        self._cache = SwrCache(ttlSeconds)

    @property
    def ttlSeconds(self) -> float:
        """fresh 로 볼 시간이다."""
        return self._cache.ttlSeconds

    @property
    def lock(self) -> threading.RLock:
        """캐시 내부 재진입 lock 이다."""
        return self._cache.lock

    def peek(self, runtimeId: str) -> CachedValue | None:
        """Sig: peek(runtimeId) -> CachedValue | None.

        Args: runtimeId 는 캐시 키다.
        Returns: 만료돼도 마지막 probe 를 신선도와 함께 반환한다.
        Example: `entry = cache.peek("codex")`.
        """
        return self._cache.peek(runtimeId)

    def get(self, runtimeId: str) -> RuntimeProbe | None:
        """Sig: get(runtimeId) -> RuntimeProbe | None.

        Args: runtimeId는 캐시 키다.
        Returns: TTL 안의 probe 또는 None이다.
        Example: `cached = cache.get("codex")`.
        """
        return self._cache.get(runtimeId)

    def put(self, probe: RuntimeProbe) -> RuntimeProbe:
        """Sig: put(probe) -> RuntimeProbe.

        Args: probe는 저장할 점검 결과다.
        Returns: 실제로 유효한 probe다. 판정 실패는 기존 판정값을 덮지 않는다.
        Example: `cache.put(probe)`.
        """
        return self._cache.put(probe.runtimeId, probe, determined=probe.state != "unknown")

    def clear(self, runtimeId: str | None = None) -> None:
        """Sig: clear(runtimeId=None) -> None.

        Args: runtimeId가 없으면 전체 캐시를 지운다.
        Returns: None.
        Example: `cache.clear("codex")`.
        """
        self._cache.clear(runtimeId)

    def __contains__(self, runtimeId: object) -> bool:
        """실측 기록이 남아 있는지 알린다."""
        return runtimeId in self._cache
