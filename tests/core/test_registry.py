"""L0 DataEntry registry의 불변성·충돌·동시성 계약."""

from __future__ import annotations

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor

import pytest

from dartlab.core.dataEntry import _BUILTIN_ENTRIES, DataEntry
from dartlab.core.registry import (
    BuiltinEntryMutationError,
    PluginNameCollisionError,
    getEntries,
    getEntry,
    getEntrySource,
    registerEntries,
    registerEntry,
    replaceEntriesForSource,
    resolveAlias,
    unregisterEntriesBySource,
    unregisterEntry,
)
from dartlab.core.registry import (
    DataEntry as RegistryDataEntry,
)

pytestmark = [pytest.mark.unit]

_EXPECTED_BUILTIN_NAMES = (
    "annual.IS",
    "annual.BS",
    "annual.CF",
    "timeseries.IS",
    "timeseries.BS",
    "timeseries.CF",
    "BS",
    "IS",
    "CF",
    "notes.receivables",
    "notes.inventory",
    "notes.tangibleAsset",
    "notes.intangibleAsset",
    "notes.investmentProperty",
    "notes.affiliates",
    "notes.borrowings",
    "notes.provisions",
    "notes.eps",
    "notes.lease",
    "notes.segments",
    "notes.costByNature",
    "rawFinance",
    "rawReport",
    "ratios",
    "insight",
    "sector",
    "rank",
    "keywordTrend",
    "news",
)


def _entry(name: str, *, aliases: tuple[str, ...] = ()) -> DataEntry:
    """테스트용 최소 DataEntry를 만든다."""
    return DataEntry(
        name=name,
        label=name,
        category="plugin",
        dataType="custom",
        description=f"{name} test entry",
        aliases=aliases,
    )


def testBuiltinCatalogIsImmutableAndProtected() -> None:
    """내장 tuple과 엔트리는 runtime 제거 API로 훼손할 수 없다."""
    assert isinstance(_BUILTIN_ENTRIES, tuple)
    assert getEntrySource("annual.IS") == "builtin:dartlab"

    with pytest.raises(BuiltinEntryMutationError, match="제거할 수 없습니다"):
        unregisterEntry("annual.IS")

    assert getEntry("annual.IS") is not None


def testBuiltinCatalogOrderAndCategoriesRemainStable() -> None:
    """물리 구조 변경이 내장 이름·순서·category projection을 바꾸지 않는다."""
    assert tuple(entry.name for entry in _BUILTIN_ENTRIES) == _EXPECTED_BUILTIN_NAMES
    assert tuple(entry.name for entry in getEntries()) == _EXPECTED_BUILTIN_NAMES
    assert {
        category: sum(entry.category == category for entry in _BUILTIN_ENTRIES)
        for category in ("finance", "report", "notes", "raw", "analysis")
    } == {
        "finance": 6,
        "report": 3,
        "notes": 12,
        "raw": 2,
        "analysis": 6,
    }


def testBuiltinRoutingContractAndDataEntryReExportRemainStable() -> None:
    """물리 통합이 routing metadata나 registry의 기존 type 표면을 바꾸지 않는다."""
    routingProjection = [
        {
            "name": entry.name,
            "category": entry.category,
            "dataType": entry.dataType,
            "modulePath": entry.modulePath,
            "funcName": entry.funcName,
            "apiType": entry.apiType,
            "notesDispatch": entry.notesDispatch,
            "aliases": entry.aliases,
            "requires": entry.requires,
            "unit": entry.unit,
            "extractorTarget": (None if entry.extractor is None else entry.extractor.__code__.co_names),
        }
        for entry in _BUILTIN_ENTRIES
    ]
    payload = json.dumps(
        routingProjection,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()

    assert RegistryDataEntry is DataEntry
    assert hashlib.sha256(payload).hexdigest() == ("d62a954fbac4c5a8b68cd29c7e9ee6a867b4932be786fa38e124d80b46c2988a")


def testAliasCannotHijackCanonicalName() -> None:
    """플러그인 alias가 내장 canonical 이름을 가로채면 등록 전체를 거부한다."""
    entry = _entry("__registry_alias_hijack", aliases=("annual.IS",))

    with pytest.raises(PluginNameCollisionError, match="canonical 이름과 충돌"):
        registerEntry(entry, source="test:alias-hijack")

    assert getEntry(entry.name) is None
    assert resolveAlias("annual.IS") == "annual.IS"


def testMutableMetadataIsRejected() -> None:
    """frozen dataclass 안에 mutable collection을 넣어 snapshot을 우회할 수 없다."""
    entry = DataEntry(
        name="__registry_mutable_alias",
        label="mutable",
        category="plugin",
        dataType="custom",
        description="mutable alias test",
        aliases=["mutable"],  # type: ignore[arg-type]
    )

    with pytest.raises(TypeError, match="불변 tuple"):
        registerEntry(entry, source="test:mutable")

    assert getEntry(entry.name) is None


def testBatchAliasCollisionRollsBackAllEntries() -> None:
    """같은 batch 안 alias 충돌은 부분 등록 없이 전체 rollback된다."""
    first = _entry("__registry_batch_first", aliases=("__registry_shared_alias",))
    second = _entry("__registry_batch_second", aliases=("__registry_shared_alias",))

    with pytest.raises(PluginNameCollisionError, match="중복"):
        registerEntries((first, second), source="test:batch-collision")

    assert getEntry(first.name) is None
    assert getEntry(second.name) is None


def testSourceReplacementIsAtomicAndTracksProvenance() -> None:
    """source 단위 reload는 이전 묶음을 제거하고 새 묶음만 한 번에 게시한다."""
    source = "test:source-replace"
    oldEntries = (
        _entry("__registry_source_old_a"),
        _entry("__registry_source_old_b"),
    )
    newEntry = _entry("__registry_source_new")
    try:
        registerEntries(oldEntries, source=source)
        replaceEntriesForSource(source, (newEntry,))

        assert all(getEntry(entry.name) is None for entry in oldEntries)
        assert getEntry(newEntry.name) is newEntry
        assert getEntrySource(newEntry.name) == source
    finally:
        unregisterEntriesBySource(source)


def testFailedSourceReplacementKeepsPreviousSnapshot() -> None:
    """새 묶음 검증 실패 시 기존 source 엔트리가 그대로 남는다."""
    source = "test:source-rollback"
    blockerSource = "test:source-blocker"
    oldEntry = _entry("__registry_source_stable")
    blocker = _entry("__registry_source_blocker", aliases=("__registry_taken_alias",))
    replacement = _entry("__registry_source_replacement", aliases=("__registry_taken_alias",))
    try:
        registerEntry(oldEntry, source=source)
        registerEntry(blocker, source=blockerSource)

        with pytest.raises(PluginNameCollisionError, match="중복"):
            replaceEntriesForSource(source, (replacement,))

        assert getEntry(oldEntry.name) is oldEntry
        assert getEntry(replacement.name) is None
    finally:
        unregisterEntriesBySource(source)
        unregisterEntriesBySource(blockerSource)


def testConcurrentSameNameRegistrationHasSingleWinner() -> None:
    """동시 같은 이름 등록은 정확히 하나만 성공하고 중복 snapshot을 만들지 않는다."""
    source = "test:concurrent-collision"
    name = "__registry_concurrent_same"

    def _attempt(index: int) -> bool:
        """한 worker가 같은 canonical 이름 등록을 시도한다."""
        try:
            registerEntry(_entry(name), source=f"{source}:{index}")
        except PluginNameCollisionError:
            return False
        return True

    try:
        with ThreadPoolExecutor(max_workers=16) as executor:
            results = list(executor.map(_attempt, range(32)))
        assert results.count(True) == 1
        assert sum(entry.name == name for entry in getEntries()) == 1
    finally:
        unregisterEntry(name)


def testReturnedListCannotMutateRegistrySnapshot() -> None:
    """호출자가 조회 list를 바꿔도 내부 snapshot은 변하지 않는다."""
    entries = getEntries()
    originalCount = len(entries)
    entries.clear()

    assert len(getEntries()) == originalCount
