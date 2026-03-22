"""장애 방어 — Circuit Breaker + Source Health Tracker."""

from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum

# ══════════════════════════════════════
# Circuit Breaker
# ══════════════════════════════════════


class _State(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class _CircuitState:
    state: _State = _State.CLOSED
    failure_count: int = 0
    opened_at: float = 0.0


class CircuitBreaker:
    """소스별 circuit breaker.

    - closed → open: 연속 ``failure_threshold`` 회 실패
    - open → half_open: ``recovery_timeout`` 초 경과 후 1회 시도
    - half_open → closed: 성공 시 / open: 실패 시
    """

    __slots__ = ("_failure_threshold", "_recovery_timeout", "_circuits", "_lock")

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 300.0,
    ) -> None:
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._circuits: dict[str, _CircuitState] = {}
        self._lock = threading.Lock()

    def _get(self, source: str) -> _CircuitState:
        if source not in self._circuits:
            self._circuits[source] = _CircuitState()
        return self._circuits[source]

    def is_open(self, source: str) -> bool:
        """소스가 차단 상태인지 확인. half_open 전환도 처리.

        half_open은 1회만 허용 — 첫 호출이 허용되면 즉시 OPEN으로 되돌려
        다른 스레드의 동시 통과를 방지한다. record_success()에서 CLOSED로 전환.
        """
        with self._lock:
            cs = self._get(source)
            if cs.state == _State.CLOSED:
                return False
            if cs.state == _State.HALF_OPEN:
                # 1회 시도 허용 후 즉시 OPEN 복귀 (동시 통과 방지)
                cs.state = _State.OPEN
                cs.opened_at = time.monotonic()
                return False
            # OPEN — recovery timeout 경과 시 1회 시도 허용
            if time.monotonic() - cs.opened_at >= self._recovery_timeout:
                # 타이머 리셋 후 이번 1회만 허용 (다음 호출은 다시 차단)
                cs.opened_at = time.monotonic()
                return False
            return True

    def record_success(self, source: str) -> None:
        with self._lock:
            cs = self._get(source)
            cs.state = _State.CLOSED
            cs.failure_count = 0

    def record_failure(self, source: str) -> None:
        with self._lock:
            cs = self._get(source)
            cs.failure_count += 1
            if cs.state == _State.HALF_OPEN:
                # half_open에서 실패 → 다시 open
                cs.state = _State.OPEN
                cs.opened_at = time.monotonic()
            elif cs.failure_count >= self._failure_threshold:
                cs.state = _State.OPEN
                cs.opened_at = time.monotonic()

    def state(self, source: str) -> str:
        """현재 상태 문자열 반환 (디버깅용)."""
        with self._lock:
            return self._get(source).state.value


# ══════════════════════════════════════
# Source Health Tracker
# ══════════════════════════════════════


@dataclass
class _HealthRecord:
    timestamp: float
    success: bool
    latency: float = 0.0


@dataclass
class _SourceHealth:
    records: deque[_HealthRecord] = field(default_factory=lambda: deque(maxlen=100))

    @property
    def score(self) -> float:
        """health_score = success_rate × 0.7 + latency_score × 0.3."""
        if not self.records:
            return 0.5  # 데이터 없으면 중립
        successes = sum(1 for r in self.records if r.success)
        success_rate = successes / len(self.records)
        # latency_score: 평균 응답시간 기반 (1초 이하 = 1.0, 10초 = 0.0)
        latencies = [r.latency for r in self.records if r.success and r.latency > 0]
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            latency_score = max(0.0, 1.0 - avg_latency / 10.0)
        else:
            latency_score = 0.5
        return success_rate * 0.7 + latency_score * 0.3


class SourceHealthTracker:
    """소스별 건강도 추적 — sliding window 100건."""

    __slots__ = ("_sources", "_lock")

    def __init__(self) -> None:
        self._sources: dict[str, _SourceHealth] = {}
        self._lock = threading.Lock()

    def record(self, source: str, *, success: bool, latency: float = 0.0) -> None:
        with self._lock:
            if source not in self._sources:
                self._sources[source] = _SourceHealth()
            self._sources[source].records.append(
                _HealthRecord(
                    timestamp=time.monotonic(),
                    success=success,
                    latency=latency,
                )
            )

    def score(self, source: str) -> float:
        with self._lock:
            if source not in self._sources:
                return 0.5
            return self._sources[source].score

    def reorder(self, chain: tuple[str, ...] | list[str]) -> list[str]:
        """fallback 체인을 health score 높은 순으로 재정렬.

        원본 순서를 존중하되 health 차이가 유의미하면(0.2+) 재정렬.
        """
        scored = [(name, self.score(name)) for name in chain]
        # 안정적 정렬: score 같으면 원래 순서 유지
        scored.sort(key=lambda x: -x[1])
        # 1위와 나머지 차이가 0.2 미만이면 원래 순서 유지
        if len(scored) > 1 and scored[0][1] - scored[-1][1] < 0.2:
            return list(chain)
        return [name for name, _ in scored]


# ── 모듈 레벨 싱글턴 ──

circuit_breaker = CircuitBreaker()
health_tracker = SourceHealthTracker()
