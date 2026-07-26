"""Data Workbench continuation-aware lazy page scan tests."""

from __future__ import annotations

import time
from dataclasses import replace
from typing import Any, cast

import polars as pl
import pytest

import dartlab.dataHub.pageScan as pageScanModule
from dartlab.dataHub.contracts import (
    AssetRef,
    Coverage,
    DataPartition,
    DataResult,
)
from dartlab.dataHub.pageScan import (
    PageScanCheckpoint,
    PageScanError,
    iterDataArrowBatches,
    iterDataResultPages,
)

_SNAPSHOT = "data-snapshot:" + "a" * 64
_CONTRACT = "b" * 64
_UNIVERSE = "resource-universe:" + "c" * 64
_ASSETS = (
    AssetRef("resource.finance", "asset:" + "d" * 64),
    AssetRef("resource.edgar", "asset:" + "e" * 64),
)


def _partition(pageNumber: int, rows: int = 2) -> DataPartition:
    frame = pl.DataFrame(
        {
            "page": [pageNumber] * rows,
            "value": list(range((pageNumber - 1) * rows, pageNumber * rows)),
        }
    )
    return DataPartition(
        asset=_ASSETS[0],
        projectionKind="native",
        data=frame,
        schema=tuple((name, str(dtype)) for name, dtype in frame.schema.items()),
        rowCount=frame.height,
        truncated=False,
        selector=(),
        temporalStatus="LATEST_ONLY",
        lineageRefs=(f"page:{pageNumber}",),
        requestId="dartAll",
    )


def _result(
    pageNumber: int,
    token: str | None,
    *,
    status: str | None = None,
    assets: tuple[AssetRef, ...] = _ASSETS,
    snapshotId: str = _SNAPSHOT,
    contractHash: str = _CONTRACT,
    universeSnapshotId: str | None = _UNIVERSE,
    rows: int = 2,
) -> DataResult:
    partition = _partition(pageNumber, rows)
    return DataResult(
        status=status or ("partial" if token is not None else "ok"),
        partitions=(partition,),
        assets=assets,
        snapshotId=snapshotId,
        contractHash=contractHash,
        coverage=Coverage(2, 2, 1, 0),
        gaps=(),
        lineageRefs=partition.lineageRefs,
        executionReceipts=(f"receipt:{pageNumber}",),
        continuation=token,
        universeSnapshotId=universeSnapshotId,
    )


def testIterPagesIsLazyUsesTokenOnlyCallerAndCheckpointsBeforeYield() -> None:
    pages = {
        "token-1": _result(2, "token-2"),
        "token-2": _result(3, None),
    }
    calls: list[str] = []
    checkpoints: list[PageScanCheckpoint] = []

    def caller(token: str) -> DataResult:
        calls.append(token)
        return pages[token]

    iterator = iterDataResultPages(
        _result(1, "token-1"),
        queryCaller=caller,
        checkpoint=checkpoints.append,
    )

    first = next(iterator)
    assert first.partitions[0].data["page"].item(0) == 1
    assert calls == []
    assert [(item.pageNumber, item.nextToken, item.complete) for item in checkpoints] == [(1, "token-1", False)]

    assert [page.partitions[0].data["page"].item(0) for page in iterator] == [2, 3]
    assert calls == ["token-1", "token-2"]
    assert [(item.pageNumber, item.nextToken, item.complete) for item in checkpoints] == [
        (1, "token-1", False),
        (2, "token-2", False),
        (3, None, True),
    ]
    assert checkpoints[-1].assets == tuple((asset.assetId, asset.assetVersionId) for asset in _ASSETS)


def testDefaultCallerUsesExactPublicTokenOnlyQuery(monkeypatch: pytest.MonkeyPatch) -> None:
    import dartlab

    calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def fakeData(*args: object, **kwargs: object) -> DataResult:
        calls.append((args, kwargs))
        return _result(2, None)

    monkeypatch.setattr(dartlab, "dataHub", fakeData)

    pages = list(iterDataResultPages(_result(1, "opaque-token")))

    assert len(pages) == 2
    assert calls == [(("query",), {"query": {"continuation": "opaque-token"}})]


def testDataResultMethodsExposeOneFlowPageAndArrowConsumption(monkeypatch: pytest.MonkeyPatch) -> None:
    import dartlab

    monkeypatch.setattr(dartlab, "dataHub", lambda *_args, **_kwargs: _result(2, None, rows=2))
    pages = list(_result(1, "opaque-token", rows=2).iterPages())
    batches = list(_result(1, "opaque-token", rows=2).iterAllArrowBatches(maxRows=1, maxBytes=1024))

    assert [page.partitions[0].data["page"].item(0) for page in pages] == [1, 2]
    assert [batch.num_rows for _key, batch in batches] == [1, 1, 1, 1]


def testMaxPagesStopsBeforeAnotherOwnerCall() -> None:
    calls: list[str] = []
    iterator = iterDataResultPages(
        _result(1, "token-1"),
        maxPages=1,
        queryCaller=lambda token: calls.append(token) or _result(2, None),
    )

    assert next(iterator).status == "partial"
    with pytest.raises(PageScanError) as captured:
        next(iterator)

    assert captured.value.code == "PAGE_SCAN_MAX_PAGES"
    assert calls == []


def testDeadlineStopsBeforeInitialPageAndAfterSlowResume(monkeypatch: pytest.MonkeyPatch) -> None:
    expired = iterDataResultPages(_result(1, None), deadline=time.monotonic() - 1)
    with pytest.raises(PageScanError) as captured:
        next(expired)
    assert captured.value.code == "PAGE_SCAN_DEADLINE"

    clock = iter((10.0, 10.0, 12.0))
    monkeypatch.setattr(pageScanModule.time, "monotonic", lambda: next(clock))
    iterator = iterDataResultPages(
        _result(1, "token-1"),
        deadline=11.0,
        queryCaller=lambda _token: _result(2, None),
    )
    assert next(iterator).status == "partial"
    with pytest.raises(PageScanError) as captured:
        next(iterator)
    assert captured.value.code == "PAGE_SCAN_DEADLINE"


def testRepeatedContinuationTokenFailsBeforeDuplicatePageYield() -> None:
    iterator = iterDataResultPages(
        _result(1, "token-loop"),
        queryCaller=lambda _token: _result(2, "token-loop"),
    )

    assert next(iterator).status == "partial"
    with pytest.raises(PageScanError) as captured:
        next(iterator)
    assert captured.value.code == "PAGE_SCAN_TOKEN_LOOP"


@pytest.mark.parametrize(
    ("replacement", "value"),
    [
        ("snapshotId", "data-snapshot:" + "f" * 64),
        ("contractHash", "0" * 64),
        ("assets", (AssetRef("resource.finance", "asset:" + "1" * 64),)),
        ("universeSnapshotId", "resource-universe:" + "2" * 64),
    ],
)
def testCrossPageIdentityDriftFailsClosed(replacement: str, value: object) -> None:
    drifted = replace(_result(2, None), **{replacement: value})
    iterator = iterDataResultPages(_result(1, "token-1"), queryCaller=lambda _token: drifted)

    next(iterator)
    with pytest.raises(PageScanError) as captured:
        next(iterator)
    assert captured.value.code == "PAGE_SCAN_IDENTITY_DRIFT"


def testFailedPageAndResumeExceptionAreSanitized() -> None:
    failed = _result(1, None, status="failed")
    with pytest.raises(PageScanError) as captured:
        next(iterDataResultPages(failed))
    assert captured.value.code == "PAGE_SCAN_PAGE_FAILED"

    token = "secret-continuation-token"

    def failResume(_token: str) -> DataResult:
        raise RuntimeError(token)

    iterator = iterDataResultPages(_result(1, token), queryCaller=failResume, maxPageRetries=0)
    next(iterator)
    with pytest.raises(PageScanError) as captured:
        next(iterator)
    assert captured.value.code == "PAGE_SCAN_RESUME_FAILED"
    assert token not in str(captured.value)
    assert token not in repr(captured.value)


def testTransientPageFailureIsRetriedWithSameTokenUntilSweepCompletes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """일시 실패한 page는 같은 token으로 재시도해 전종목 sweep을 완주시킨다."""

    monkeypatch.setattr(pageScanModule.time, "sleep", lambda _seconds: None)
    seen: list[str] = []

    def flakyResume(token: str) -> DataResult:
        seen.append(token)
        if len(seen) == 1:
            return _result(2, None, status="failed")
        if len(seen) == 2:
            raise RuntimeError("transient owner glitch")
        return _result(2, None)

    pages = list(iterDataResultPages(_result(1, "page-two-token"), queryCaller=flakyResume))

    assert [page.partitions[0].data["page"].item(0) for page in pages] == [1, 2]
    assert seen == ["page-two-token"] * 3


def testRetryBudgetExhaustionRaisesTheOriginalTransientCode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """재시도를 다 써도 실패하면 원래 transient code를 그대로 올린다."""

    monkeypatch.setattr(pageScanModule.time, "sleep", lambda _seconds: None)
    attempts: list[str] = []

    def alwaysFailing(token: str) -> DataResult:
        attempts.append(token)
        return _result(2, None, status="failed")

    iterator = iterDataResultPages(
        _result(1, "page-two-token"),
        queryCaller=alwaysFailing,
        maxPageRetries=2,
    )
    next(iterator)
    with pytest.raises(PageScanError) as captured:
        next(iterator)
    assert captured.value.code == "PAGE_SCAN_PAGE_FAILED"
    assert len(attempts) == 3


def testNonTransientPageFailureIsNotRetried(monkeypatch: pytest.MonkeyPatch) -> None:
    """Identity drift 같은 결정적 위반은 재시도해도 같으므로 즉시 올린다."""

    monkeypatch.setattr(pageScanModule.time, "sleep", lambda _seconds: None)
    attempts: list[str] = []

    def driftingResume(token: str) -> DataResult:
        attempts.append(token)
        return _result(2, None, contractHash="f" * 64)

    iterator = iterDataResultPages(_result(1, "page-two-token"), queryCaller=driftingResume)
    next(iterator)
    with pytest.raises(PageScanError) as captured:
        next(iterator)
    assert captured.value.code == "PAGE_SCAN_IDENTITY_DRIFT"
    assert len(attempts) == 1


def testUnknownPageStatusAndCheckpointReprFailClosed() -> None:
    invalid = _result(1, None, status="unknown")
    with pytest.raises(PageScanError) as captured:
        next(iterDataResultPages(invalid))
    assert captured.value.code == "PAGE_SCAN_RESULT_INVALID"

    checkpoints: list[PageScanCheckpoint] = []
    secret = "secret-next-token"
    next(
        iterDataResultPages(
            _result(1, secret),
            queryCaller=lambda _token: _result(2, None),
            checkpoint=checkpoints.append,
        )
    )
    assert secret not in repr(checkpoints[0])


def testArrowBatchesSpanEveryPageWithIndependentBounds() -> None:
    checkpoints: list[PageScanCheckpoint] = []
    batches = list(
        iterDataArrowBatches(
            _result(1, "token-1", rows=3),
            queryCaller=lambda _token: _result(2, None, rows=3),
            checkpoint=checkpoints.append,
            maxRows=1,
            maxBytes=1024,
        )
    )

    assert [key for key, _batch in batches] == ["dartAll"] * 6
    assert [batch.num_rows for _key, batch in batches] == [1] * 6
    assert [batch.column("page")[0].as_py() for _key, batch in batches] == [1, 1, 1, 2, 2, 2]
    assert [checkpoint.pageNumber for checkpoint in checkpoints] == [1, 2]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"maxPages": 0},
        {"maxPages": cast(Any, True)},
        {"deadline": float("nan")},
        {"checkpoint": cast(Any, "not-callable")},
        {"queryCaller": cast(Any, "not-callable")},
        {"maxPageRetries": -1},
        {"maxPageRetries": 17},
        {"maxPageRetries": cast(Any, True)},
    ],
)
def testInvalidScanArgumentsFailBeforeYield(kwargs: dict[str, object]) -> None:
    with pytest.raises(PageScanError) as captured:
        next(iterDataResultPages(_result(1, None), **cast(Any, kwargs)))
    assert captured.value.code == "PAGE_SCAN_ARGUMENT_INVALID"


@pytest.mark.parametrize("name", ["maxRows", "maxBytes"])
def testInvalidArrowBudgetFailsClosed(name: str) -> None:
    kwargs = {name: 0}
    with pytest.raises(PageScanError) as captured:
        next(iterDataArrowBatches(_result(1, None), **cast(Any, kwargs)))
    assert captured.value.code == "PAGE_SCAN_ARGUMENT_INVALID"
