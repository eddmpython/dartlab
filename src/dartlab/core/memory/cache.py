"""정책 주입형 bounded LRU와 충돌 없는 임시 IPC backing."""

from __future__ import annotations

import gc
import hashlib
import logging
import os
import tempfile
import threading
import time
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from dartlab.core.memory.metrics import (
    PRESSURE_EMERGENCY_MB,
    PRESSURE_FATAL_MB,
    getMemoryMb,
)

log = logging.getLogger(__name__)

_CACHE_MISSING: Any = object()
_POP_MISSING: Any = object()


@dataclass(frozen=True)
class CachePolicy:
    """BoundedCache의 선택적 IPC backing 정책."""

    ipcBackedKeys: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        """빈 key는 파일 소유권이 불명확하므로 거부한다."""
        if any(not key for key in self.ipcBackedKeys):
            raise ValueError("ipcBackedKeys는 빈 key를 포함할 수 없습니다")


def lookupCache(cache: Any, key: str) -> tuple[bool, Any]:
    """BoundedCache와 표준 mapping에서 저장된 None과 miss를 구분한다.

    Args:
        cache: ``lookup`` 또는 ``get``을 제공하는 cache 객체.
        key: 조회할 cache key.
    Returns:
        hit이면 ``(True, value)``, miss이면 ``(False, None)``.
    Requires:
        cache는 BoundedCache이거나 dict 호환 ``get``을 제공해야 한다.
    Raises:
        cache의 lookup/get이 낸 예외를 그대로 전달한다.
    Example:
        >>> lookupCache({"empty": None}, "empty")
        (True, None)
    """
    lookup = getattr(cache, "lookup", None)
    if callable(lookup):
        lookupFn = cast(Callable[[str], tuple[bool, Any]], lookup)
        return lookupFn(key)
    cached = cache.get(key, _CACHE_MISSING)
    if cached is _CACHE_MISSING:
        return False, None
    return True, cached


@dataclass
class _BuildState:
    lock: threading.Lock
    users: int = 0


class BoundedCache:
    """thread-safe bounded LRU cache with optional exact-key IPC backing."""

    __slots__ = (
        "_store",
        "_max",
        "_default_max",
        "_pressure_mb",
        "_memorySampler",
        "_lock",
        "_policy",
        "_emergency_at",
        "_ipcTempDir",
        "_ipc_cache_dir",
        "_ipcKeys",
        "_buildLocks",
    )

    def __init__(
        self,
        maxEntries: int = 30,
        pressureMb: float = 800.0,
        *,
        policy: CachePolicy | None = None,
        memorySampler: Callable[[], float] | None = None,
    ) -> None:
        if maxEntries < 1:
            raise ValueError("maxEntries는 1 이상이어야 합니다")
        if pressureMb <= 0 or pressureMb >= PRESSURE_FATAL_MB:
            raise ValueError(f"pressureMb는 0 초과 {PRESSURE_FATAL_MB:g} 미만이어야 합니다")
        self._store: OrderedDict[str, Any] = OrderedDict()
        self._max = maxEntries
        self._default_max = maxEntries
        self._pressure_mb = pressureMb
        self._memorySampler = memorySampler if memorySampler is not None else getMemoryMb
        self._lock = threading.RLock()
        self._policy = policy if policy is not None else CachePolicy()
        self._emergency_at = 0.0
        self._ipcTempDir: tempfile.TemporaryDirectory[str] | None = None
        self._ipc_cache_dir: Path | None = None
        self._ipcKeys: set[str] = set()
        self._buildLocks: dict[str, _BuildState] = {}

    def _ipcBacked(self, key: str) -> bool:
        return key in self._policy.ipcBackedKeys

    def _ensureIpcDir(self) -> Path:
        if self._ipc_cache_dir is None:
            tempDir = tempfile.TemporaryDirectory(prefix="dartlab-cache-")
            self._ipcTempDir = tempDir
            self._ipc_cache_dir = Path(tempDir.name)
        return self._ipc_cache_dir

    def _ipcPath(self, key: str) -> Path:
        cacheDir = self._ensureIpcDir()
        readable = "".join(ch if ch.isalnum() or ch in "_-" else "_" for ch in key)[:48]
        digest = hashlib.blake2b(key.encode("utf-8"), digest_size=10).hexdigest()
        return cacheDir / f"{readable}-{digest}.arrow"

    def _invalidateIpc(self, key: str, *, strict: bool) -> None:
        self._ipcKeys.discard(key)
        if self._ipc_cache_dir is None:
            return
        path = self._ipcPath(key)
        try:
            path.unlink(missing_ok=True)
        except OSError:
            if strict:
                raise
            log.warning("[BoundedCache] stale IPC 삭제 실패: %s", path, exc_info=True)

    def _writeIpc(self, key: str, value: Any) -> None:
        import polars as pl

        path = self._ipcPath(key)
        descriptor, stagingName = tempfile.mkstemp(prefix=f".{path.stem}-", suffix=".tmp", dir=path.parent)
        os.close(descriptor)
        staging = Path(stagingName)
        try:
            value.write_ipc(staging, compression="uncompressed")
            os.replace(staging, path)
        except (OSError, pl.exceptions.PolarsError):
            staging.unlink(missing_ok=True)
            self._invalidateIpc(key, strict=False)
            log.warning("[BoundedCache] IPC write 실패, heap value만 유지: %s", path, exc_info=True)
            return
        self._ipcKeys.add(key)

    def _readIpc(self, key: str) -> Any:
        import polars as pl

        path = self._ipcPath(key)
        try:
            return pl.read_ipc(path, memory_map=True)
        except (OSError, ValueError, pl.exceptions.PolarsError) as exc:
            self._invalidateIpc(key, strict=False)
            log.warning("[BoundedCache] 손상 IPC 무효화: %s", path, exc_info=True)
            raise KeyError(key) from exc

    def __contains__(self, key: str) -> bool:
        with self._lock:
            if key in self._store:
                return True
            if key not in self._ipcKeys or self._ipc_cache_dir is None:
                return False
            return self._ipcPath(key).exists()

    def __getitem__(self, key: str) -> Any:
        with self._lock:
            if key in self._store:
                self._store.move_to_end(key)
                return self._store[key]
            if key not in self._ipcKeys:
                raise KeyError(key)
            value = self._readIpc(key)
            self._store[key] = value
            self._checkPressure(justSetKey=key)
            self._evictResident(protectedKey=key)
            return value

    def __setitem__(self, key: str, value: Any) -> None:
        with self._lock:
            if self._ipcBacked(key):
                import polars as pl

                if isinstance(value, pl.DataFrame):
                    self._writeIpc(key, value)
                else:
                    self._invalidateIpc(key, strict=False)
            if key in self._store:
                self._store.move_to_end(key)
            self._store[key] = value
            self._checkPressure(justSetKey=key)
            self._evictResident(protectedKey=key)

    def __len__(self) -> int:
        with self._lock:
            return len(set(self._store) | self._ipcKeys)

    def _scaledMax(self, divisor: int) -> int:
        return max(self._default_max // divisor, 1)

    def _checkPressure(self, justSetKey: str | None = None) -> None:
        mem = self._memorySampler()
        if mem <= 0:
            return
        if mem > PRESSURE_EMERGENCY_MB:
            self._max = self._scaledMax(8)
            now = time.monotonic()
            if now - self._emergency_at < 1.0:
                self._evictResident(protectedKey=justSetKey)
                return
            self._emergency_at = now
            log.warning("[BoundedCache] EMERGENCY %.0fMB — 현재 값 외 resident evict", mem)
            self._dropResidents(lambda key: key == justSetKey)
            gc.collect()
            return
        if mem > PRESSURE_FATAL_MB:
            log.warning("[BoundedCache] FATAL %.0fMB — 현재 값 외 resident evict", mem)
            self._dropResidents(lambda key: key == justSetKey)
            self._max = self._scaledMax(4)
            gc.collect()
            return
        criticalMb = min(self._pressure_mb * 1.5, PRESSURE_FATAL_MB - 1.0)
        if mem > criticalMb:
            self._max = self._scaledMax(4)
            self._evictResident(protectedKey=justSetKey)
            gc.collect()
            return
        if mem > self._pressure_mb:
            self._max = self._scaledMax(2)
            self._evictResident(protectedKey=justSetKey)
            return
        self._max = self._default_max

    def _dropResidents(self, keep: Callable[[str], bool]) -> None:
        for key in list(self._store):
            if not keep(key):
                del self._store[key]

    def _evictResident(self, *, protectedKey: str | None = None) -> None:
        while len(self._store) > self._max:
            candidate = next((key for key in self._store if key != protectedKey), None)
            if candidate is None:
                break
            del self._store[candidate]

    def keys(self) -> list[str]:
        """memory와 IPC에 존재하는 모든 key snapshot을 반환한다.

        Returns:
            resident LRU 순서 뒤에 disk-only key를 정렬한 독립 list.
        Requires:
            없음.
        Raises:
            없음.
        Example:
            >>> cache = BoundedCache()
            >>> cache.keys()
            []
        """
        with self._lock:
            diskOnly = sorted(self._ipcKeys.difference(self._store))
            return [*self._store, *diskOnly]

    def pop(self, key: str, *args: Any) -> Any:
        """key의 memory와 IPC 값을 함께 제거한다.

        Returns:
            제거한 값. 미등록이고 default가 있으면 default.
        Requires:
            default 인자는 최대 하나만 허용한다.
        Raises:
            KeyError: key와 default가 모두 없을 때.
            TypeError: default를 둘 이상 전달했을 때.
            OSError: IPC 파일을 제거하지 못했을 때.
        Example:
            >>> cache = BoundedCache()
            >>> cache.pop("missing", None) is None
            True
        """
        if len(args) > 1:
            raise TypeError(f"pop expected at most 2 arguments, got {len(args) + 1}")
        with self._lock:
            value = self._store.pop(key, _POP_MISSING)
            if value is _POP_MISSING and key in self._ipcKeys:
                value = self._readIpc(key)
            self._invalidateIpc(key, strict=True)
            if value is not _POP_MISSING:
                return value
            if args:
                return args[0]
            raise KeyError(key)

    def clear(self) -> None:
        """resident와 IPC cache를 모두 제거하고 초기 용량으로 되돌린다.

        Requires:
            없음.
        Raises:
            OSError: 소유한 IPC 임시 디렉터리를 제거하지 못했을 때.
        Example:
            >>> cache = BoundedCache()
            >>> cache.clear()
        """
        with self._lock:
            self._store.clear()
            tempDir = self._ipcTempDir
            if tempDir is not None:
                tempDir.cleanup()
            self._ipcTempDir = None
            self._ipc_cache_dir = None
            self._ipcKeys.clear()
            self._max = self._default_max

    def get(self, key: str, default: Any = None) -> Any:
        """memory 또는 IPC 값을 조회하고 미등록이면 default를 반환한다.

        Returns:
            저장된 값 또는 default.
        Requires:
            없음.
        Raises:
            없음. 손상 IPC는 warning과 무효화 뒤 cache miss로 처리한다.
        Example:
            >>> BoundedCache().get("missing") is None
            True
        """
        try:
            return self[key]
        except KeyError:
            return default

    def lookup(self, key: str) -> tuple[bool, Any]:
        """None을 포함한 저장값과 cache miss를 원자적으로 구분한다.

        Args:
            key: 조회할 cache key.
        Returns:
            hit이면 ``(True, value)``, miss이면 ``(False, None)``.
        Requires:
            없음.
        Raises:
            없음. 손상 IPC는 warning과 무효화 뒤 miss로 처리한다.
        Example:
            >>> cache = BoundedCache(memorySampler=lambda: 0.0)
            >>> cache["empty"] = None
            >>> cache.lookup("empty")
            (True, None)
        """
        try:
            return True, self[key]
        except KeyError:
            return False, None

    def getOrCreate(self, key: str, builder: Callable[[], Any]) -> Any:
        """key별 단일 builder 실행으로 값을 원자적으로 조회하거나 생성한다.

        Args:
            key: 조회하거나 생성할 cache key.
            builder: miss일 때 호출할 무인자 callable.
        Returns:
            cache hit 또는 builder 결과. None은 저장하지 않는다.
        Requires:
            builder는 같은 key에 대해 결정론적이어야 한다.
        Raises:
            builder와 cache 저장 경로가 낸 예외를 그대로 전달한다.
        Example:
            >>> cache = BoundedCache(memorySampler=lambda: 0.0)
            >>> cache.getOrCreate("answer", lambda: 42)
            42
        """
        cached = self.get(key, _CACHE_MISSING)
        if cached is not _CACHE_MISSING:
            return cached
        with self._lock:
            state = self._buildLocks.setdefault(key, _BuildState(threading.Lock()))
            state.users += 1
        try:
            with state.lock:
                cached = self.get(key, _CACHE_MISSING)
                if cached is not _CACHE_MISSING:
                    return cached
                result = builder()
                if result is not None:
                    self[key] = result
                return result
        finally:
            with self._lock:
                state.users -= 1
                if state.users == 0 and self._buildLocks.get(key) is state:
                    del self._buildLocks[key]

    def __del__(self) -> None:
        try:
            self._store.clear()
            if self._ipcTempDir is not None:
                self._ipcTempDir.cleanup()
        except (AttributeError, OSError):
            return


__all__ = [
    "BoundedCache",
    "CachePolicy",
    "lookupCache",
]
