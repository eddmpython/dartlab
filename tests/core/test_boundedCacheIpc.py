"""Phase C-2 — ``BoundedCache`` 의 IPC mmap backing 회귀.

검증:
  1. ``_sections`` prefix + ``pl.DataFrame`` 값 set 시 IPC 파일 자동 생성.
  2. evict 후 다시 get 하면 mmap 으로 reload (RSS 절감).
  3. EMERGENCY clear 후에도 IPC 파일 잔존 → 다음 get 성공.
  4. ``_sections`` 외 prefix 는 IPC 영향 0 (기존 동작).
  5. DataFrame 아닌 값 (dict, tuple) 도 IPC 미적용 (호환 보존).
"""

from __future__ import annotations

import shutil
import tempfile
from collections.abc import Callable, Generator
from pathlib import Path
from typing import Any

import polars as pl
import pytest

pytestmark = pytest.mark.unit


@pytest.fixture
def makeCache() -> Generator[Callable[..., Any], None, None]:
    """테스트가 만든 IPC 임시 디렉터리를 현재 구현에서도 정확히 회수한다."""
    from dartlab.core.memory import BoundedCache, CachePolicy

    caches: list[Any] = []

    def _make(**kwargs: Any) -> Any:
        kwargs.setdefault("policy", CachePolicy(ipcBackedKeys=frozenset({"_sections"})))
        cache = BoundedCache(**kwargs)
        caches.append(cache)
        return cache

    yield _make

    tempRoot = Path(tempfile.gettempdir()).resolve()
    for cache in caches:
        cacheDir = getattr(cache, "_ipc_cache_dir", None)
        cache.clear()
        if cacheDir is None:
            continue
        resolved = Path(cacheDir).resolve()
        if resolved.parent == tempRoot and resolved.name.startswith("dartlab-cache-"):
            shutil.rmtree(resolved, ignore_errors=True)


def test_sections_value_writes_ipc(makeCache) -> None:
    from dartlab.core.memory import BoundedCache

    cache: BoundedCache = makeCache(maxEntries=10)
    df = pl.DataFrame({"topic": ["a"], "value": [1.0]})

    cache["_sections"] = df

    ipcPath = cache._ipcPath("_sections")
    assert ipcPath.exists(), f"IPC 파일 미생성: {ipcPath}"


def test_evicted_key_reloaded_from_ipc(makeCache) -> None:
    """store dict 에서 manual delete 후 __getitem__ 이 mmap reload."""
    from dartlab.core.memory import BoundedCache

    cache: BoundedCache = makeCache(maxEntries=10)
    df = pl.DataFrame({"topic": ["a", "b"], "value": [1.0, 2.0]})

    cache["_sections"] = df
    assert "_sections" in cache._store

    # 인위 evict — IPC 는 남음
    del cache._store["_sections"]
    assert "_sections" not in cache._store
    assert cache._ipcPath("_sections").exists()

    # __getitem__ 가 mmap reload
    reloaded = cache["_sections"]
    assert reloaded.height == 2
    assert reloaded.get_column("value").to_list() == [1.0, 2.0]


def test_emergency_clear_preserves_ipc(makeCache) -> None:
    """EMERGENCY clear (store dict 비움) 후에도 IPC 잔존 → 재호출 성공."""
    from dartlab.core.memory import BoundedCache

    cache: BoundedCache = makeCache(maxEntries=10)
    df = pl.DataFrame({"topic": ["a"], "value": [1.0]})
    cache["_sections"] = df

    # EMERGENCY simulate — store 전체 clear
    cache._store.clear()

    # IPC 통해 재진입
    assert "_sections" in cache
    reloaded = cache["_sections"]
    assert reloaded.equals(df)


def test_non_sections_prefix_no_ipc(makeCache) -> None:
    """_sections 외 prefix 는 IPC 미생성 (기존 동작)."""
    from dartlab.core.memory import BoundedCache

    cache: BoundedCache = makeCache(maxEntries=10)
    df = pl.DataFrame({"a": [1]})

    cache["_finance_q_CFS"] = df
    cache["_quant_ohlcv"] = df
    cache["_calcRoicTimeline"] = {"key": "value"}

    assert cache._ipc_cache_dir is None


def test_similar_sections_prefix_is_not_ipc_backed(makeCache) -> None:
    """EDGAR 정책은 prefix가 아니라 정확한 _sections 소유값 하나만 backing한다."""
    from dartlab.core.memory import BoundedCache

    cache: BoundedCache = makeCache(maxEntries=10)
    cache["_sectionsMeta"] = pl.DataFrame({"value": [1]})

    assert cache._ipc_cache_dir is None


def test_default_cache_has_no_provider_specific_ipc_policy() -> None:
    """일반 BoundedCache는 EDGAR 값을 추측해 임시 파일을 만들지 않는다."""
    from dartlab.core.memory import BoundedCache

    cache = BoundedCache(memorySampler=lambda: 0.0)
    cache["_sections"] = pl.DataFrame({"value": [1]})

    assert cache._ipc_cache_dir is None
    cache.clear()


def test_non_dataframe_value_no_ipc(makeCache) -> None:
    """_sections prefix 라도 DataFrame 아닌 값은 IPC 미적용."""
    from dartlab.core.memory import BoundedCache

    cache: BoundedCache = makeCache(maxEntries=10)

    cache["_sections"] = {"period": "2024Q4"}  # dict, not DataFrame
    assert "_sections" in cache._store
    assert cache._ipc_cache_dir is None


def test_missing_key_raises_after_no_ipc(makeCache) -> None:
    """IPC 도 없고 store 에도 없으면 KeyError."""
    from dartlab.core.memory import BoundedCache

    cache: BoundedCache = makeCache(maxEntries=10)
    with pytest.raises(KeyError):
        _ = cache["_sections"]


def test_get_reloads_disk_backed_value(makeCache) -> None:
    """atomic lazy-build가 사용하는 get도 IPC 값을 실제로 복구해야 한다."""
    from dartlab.core.memory import BoundedCache

    cache: BoundedCache = makeCache(maxEntries=10)
    expected = pl.DataFrame({"value": [1, 2]})
    cache["_sections"] = expected
    del cache._store["_sections"]

    actual = cache.get("_sections")

    assert isinstance(actual, pl.DataFrame)
    assert actual.equals(expected)


def test_pop_removes_memory_and_ipc_value(makeCache) -> None:
    """pop한 값이 디스크에서 다시 부활하면 dict 호환 계약 위반이다."""
    from dartlab.core.memory import BoundedCache

    cache: BoundedCache = makeCache(maxEntries=10)
    expected = pl.DataFrame({"value": [1]})
    cache["_sections"] = expected
    ipcPath = cache._ipcPath("_sections")

    popped = cache.pop("_sections")

    assert popped.equals(expected)
    assert "_sections" not in cache
    assert not ipcPath.exists()


def test_clear_removes_memory_and_ipc_values(makeCache) -> None:
    """clear 뒤에는 contains/get/item 어느 경로에서도 값이 남지 않는다."""
    from dartlab.core.memory import BoundedCache

    cache: BoundedCache = makeCache(maxEntries=10)
    cache["_sections"] = pl.DataFrame({"value": [1]})
    ipcPath = cache._ipcPath("_sections")

    cache.clear()

    assert len(cache) == 0
    assert cache.keys() == []
    assert "_sections" not in cache
    assert cache.get("_sections") is None
    assert not ipcPath.exists()


def test_non_dataframe_update_invalidates_old_ipc(makeCache) -> None:
    """DataFrame을 일반 값으로 갱신한 뒤 옛 IPC가 stale 값을 되살리지 않는다."""
    from dartlab.core.memory import BoundedCache

    cache: BoundedCache = makeCache(maxEntries=10)
    cache["_sections"] = pl.DataFrame({"value": [1]})
    cache["_sections"] = {"value": "new"}
    del cache._store["_sections"]

    assert "_sections" not in cache
    assert cache.get("_sections") is None


def test_ipc_path_normalization_cannot_alias_distinct_keys(makeCache) -> None:
    """서로 다른 cache key가 같은 IPC 파일을 공유해 값을 오염시키지 않는다."""
    from dartlab.core.memory import BoundedCache

    cache: BoundedCache = makeCache(maxEntries=10)

    assert cache._ipcPath("_sections:a/b") != cache._ipcPath("_sections:a?b")


def test_ipc_directory_is_lazy_and_clear_removes_it(makeCache) -> None:
    """일반 cache 인스턴스는 빈 임시 디렉터리를 만들지 않고 IPC 사용 후 회수한다."""
    from dartlab.core.memory import BoundedCache

    cache: BoundedCache = makeCache(maxEntries=10)
    assert cache._ipc_cache_dir is None

    cache["_sections"] = pl.DataFrame({"value": [1]})
    cacheDir = cache._ipc_cache_dir
    assert cacheDir is not None and cacheDir.exists()

    cache.clear()
    assert not cacheDir.exists()
    assert cache._ipc_cache_dir is None
