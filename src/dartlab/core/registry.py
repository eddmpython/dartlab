"""L0 데이터 엔트리 메타데이터 레지스트리.

``core._entries``의 내장 카탈로그와 런타임 플러그인 엔트리를 하나의 불변 snapshot으로
조회한다. Company, notes, API, CLI 같은 소비자별 필터와 표현은 각 호출자가 소유한다.
"""

from __future__ import annotations

import threading
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from dartlab.core._entries import _ENTRIES as _BUILTIN_ENTRIES
from dartlab.core.dataEntry import DataEntry

_BUILTIN_SOURCE = "builtin:dartlab"


class PluginNameCollisionError(ValueError):
    """플러그인 엔트리의 이름 또는 alias가 기존 레지스트리와 충돌."""


class BuiltinEntryMutationError(PermissionError):
    """런타임 API로 내장 엔트리를 제거하려는 시도."""


@dataclass(frozen=True)
class _RegistryState:
    """독자가 한 번에 읽는 불변 registry snapshot."""

    entries: tuple[DataEntry, ...]
    index: Mapping[str, DataEntry]
    byCategory: Mapping[str, tuple[DataEntry, ...]]
    aliasToName: Mapping[str, str]
    sources: Mapping[str, str]


def _validateEntry(entry: DataEntry) -> None:
    """엔트리의 registry 핵심 식별 필드를 fail-closed로 검증한다."""
    if not isinstance(entry, DataEntry):
        raise TypeError(f"entry는 DataEntry여야 합니다: {type(entry).__name__}")
    for fieldName in ("name", "label", "category", "dataType", "description"):
        value = getattr(entry, fieldName)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"DataEntry.{fieldName}은 비어 있지 않은 문자열이어야 합니다")
    for fieldName in ("aliases",):
        if not isinstance(getattr(entry, fieldName), tuple):
            raise TypeError(f"DataEntry.{fieldName}은 불변 tuple이어야 합니다")
    if (entry.modulePath is None) != (entry.funcName is None):
        raise ValueError("DataEntry.modulePath와 funcName은 함께 지정해야 합니다")
    if entry.extractor is not None and not callable(entry.extractor):
        raise TypeError("DataEntry.extractor는 callable 또는 None이어야 합니다")
    if entry.notesDispatch is not None and (
        not isinstance(entry.notesDispatch, tuple)
        or len(entry.notesDispatch) != 2
        or not all(isinstance(item, str) and item.strip() for item in entry.notesDispatch)
    ):
        raise TypeError("DataEntry.notesDispatch는 비어 있지 않은 문자열 2개 tuple이어야 합니다")


def _buildState(
    entries: tuple[DataEntry, ...],
    sources: Mapping[str, str],
) -> _RegistryState:
    """후보 엔트리 전체를 검증한 뒤 게시 가능한 snapshot을 만든다."""
    index: dict[str, DataEntry] = {}
    categories: dict[str, list[DataEntry]] = {}
    for entry in entries:
        _validateEntry(entry)
        if entry.name in index:
            raise PluginNameCollisionError(f"이름 '{entry.name}' 이미 존재")
        index[entry.name] = entry
        categories.setdefault(entry.category, []).append(entry)

    aliases: dict[str, str] = {}
    for entry in entries:
        seen: set[str] = set()
        for alias in entry.aliases:
            if not isinstance(alias, str) or not alias.strip():
                raise ValueError(f"DataEntry '{entry.name}' alias는 비어 있지 않은 문자열이어야 합니다")
            if alias in seen:
                raise PluginNameCollisionError(f"DataEntry '{entry.name}' alias '{alias}' 중복")
            seen.add(alias)
            if alias in index:
                raise PluginNameCollisionError(f"alias '{alias}'가 canonical 이름과 충돌")
            owner = aliases.get(alias)
            if owner is not None:
                raise PluginNameCollisionError(f"alias '{alias}'가 '{owner}'와 '{entry.name}'에 중복")
            aliases[alias] = entry.name

    sourceCopy = dict(sources)
    if set(sourceCopy) != set(index):
        raise ValueError("registry source provenance와 entry 이름 집합이 일치하지 않습니다")
    for name, source in sourceCopy.items():
        if not isinstance(source, str) or not source.strip():
            raise ValueError(f"DataEntry '{name}' source는 비어 있지 않은 문자열이어야 합니다")

    return _RegistryState(
        entries=entries,
        index=MappingProxyType(index),
        byCategory=MappingProxyType({name: tuple(items) for name, items in categories.items()}),
        aliasToName=MappingProxyType(aliases),
        sources=MappingProxyType(sourceCopy),
    )


_WRITE_LOCK = threading.RLock()
_STATE = _buildState(
    tuple(_BUILTIN_ENTRIES),
    {entry.name: _BUILTIN_SOURCE for entry in _BUILTIN_ENTRIES},
)


def _validateSource(source: str) -> None:
    """runtime provenance 식별자를 검증한다."""
    if not isinstance(source, str) or not source.strip():
        raise ValueError("source는 비어 있지 않은 문자열이어야 합니다")
    if source == _BUILTIN_SOURCE:
        raise BuiltinEntryMutationError(f"source '{_BUILTIN_SOURCE}'는 내장 카탈로그 전용입니다")


def registerEntries(entries: tuple[DataEntry, ...], *, source: str = "runtime") -> None:
    """같은 source의 DataEntry 묶음을 검증 후 원자적으로 추가한다.

    이름뿐 아니라 alias와 canonical 이름 사이 충돌도 거부한다. 새 snapshot이 완전히
    검증된 뒤 한 번에 게시되므로 동시 독자는 중간 인덱스를 보지 않는다.

    Args:
        entries: 함께 등록할 불변 DataEntry tuple.
        source: provenance 식별자. 플러그인은 ``plugin:<name>`` 형식을 사용한다.

    Raises:
        TypeError: entries 또는 원소 형식이 잘못됐을 때.
        ValueError: 필수 메타데이터 또는 source가 비었을 때.
        PluginNameCollisionError: 이름 또는 alias가 기존 항목과 충돌할 때.
    """
    if not isinstance(entries, tuple):
        raise TypeError("entries는 DataEntry tuple이어야 합니다")
    _validateSource(source)
    for entry in entries:
        _validateEntry(entry)
    if not entries:
        return

    global _STATE
    with _WRITE_LOCK:
        current = _STATE
        nextSources = dict(current.sources)
        for entry in entries:
            if entry.name in current.index:
                raise PluginNameCollisionError(f"이름 '{entry.name}' 이미 존재")
            nextSources[entry.name] = source
        _STATE = _buildState((*current.entries, *entries), nextSources)


def registerEntry(entry: DataEntry, *, source: str = "runtime") -> None:
    """단일 DataEntry를 검증 후 원자적으로 등록한다."""
    registerEntries((entry,), source=source)


def replaceEntriesForSource(
    source: str,
    entries: tuple[DataEntry, ...],
) -> None:
    """source 소유 엔트리 전체를 검증된 새 묶음으로 원자 교체한다.

    후보 검증이나 충돌 확인이 실패하면 기존 snapshot을 그대로 유지한다. 플러그인 reload가
    부분 등록이나 stale 엔트리를 남기지 않도록 하는 L0 transaction 경계다.
    """
    if not isinstance(entries, tuple):
        raise TypeError("entries는 DataEntry tuple이어야 합니다")
    _validateSource(source)
    for entry in entries:
        _validateEntry(entry)

    global _STATE
    with _WRITE_LOCK:
        current = _STATE
        retained = tuple(item for item in current.entries if current.sources[item.name] != source)
        nextSources = {name: owner for name, owner in current.sources.items() if owner != source}
        for entry in entries:
            nextSources[entry.name] = source
        _STATE = _buildState((*retained, *entries), nextSources)


def unregisterEntriesBySource(source: str) -> int:
    """source 소유 런타임 엔트리를 모두 제거하고 제거 수를 반환한다."""
    _validateSource(source)
    global _STATE
    with _WRITE_LOCK:
        current = _STATE
        removed = sum(1 for owner in current.sources.values() if owner == source)
        if not removed:
            return 0
        retained = tuple(item for item in current.entries if current.sources[item.name] != source)
        nextSources = {name: owner for name, owner in current.sources.items() if owner != source}
        _STATE = _buildState(retained, nextSources)
        return removed


def unregisterEntry(name: str) -> bool:
    """런타임 엔트리를 원자적으로 제거하고 실제 제거 여부를 반환한다.

    내장 카탈로그는 package 불변식이므로 런타임에서 제거할 수 없다. 존재하지 않는 이름은
    멱등 cleanup을 위해 ``False``를 반환한다.

    Raises:
        BuiltinEntryMutationError: 내장 엔트리 제거를 시도할 때.
    """
    global _STATE
    with _WRITE_LOCK:
        current = _STATE
        entry = current.index.get(name)
        if entry is None:
            return False
        if current.sources[name] == _BUILTIN_SOURCE:
            raise BuiltinEntryMutationError(f"내장 DataEntry '{name}'은 제거할 수 없습니다")
        nextEntries = tuple(item for item in current.entries if item.name != name)
        nextSources = dict(current.sources)
        del nextSources[name]
        _STATE = _buildState(nextEntries, nextSources)
        return True


def getEntries(*, category: str | None = None) -> list[DataEntry]:
    """전체 또는 카테고리별 엔트리의 list 사본을 반환한다."""
    state = _STATE
    if category is None:
        return list(state.entries)
    return list(state.byCategory.get(category, ()))


def getEntry(name: str) -> DataEntry | None:
    """canonical 이름으로 단일 엔트리를 조회한다."""
    return _STATE.index.get(name)


def getEntrySource(name: str) -> str | None:
    """엔트리 provenance를 반환한다."""
    return _STATE.sources.get(name)


def resolveAlias(nameOrAlias: str) -> str:
    """등록된 alias를 canonical 엔트리 이름으로 해소한다."""
    return _STATE.aliasToName.get(nameOrAlias, nameOrAlias)


def getCategories() -> list[str]:
    """등록된 카테고리 이름을 선언 순서로 반환한다."""
    return list(_STATE.byCategory)


__all__ = [
    "BuiltinEntryMutationError",
    "DataEntry",
    "PluginNameCollisionError",
    "getCategories",
    "getEntries",
    "getEntry",
    "getEntrySource",
    "registerEntries",
    "registerEntry",
    "replaceEntriesForSource",
    "resolveAlias",
    "unregisterEntriesBySource",
    "unregisterEntry",
]
