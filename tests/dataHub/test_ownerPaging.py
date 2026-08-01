"""계산형 owner의 전종목 continuation과 replay 계약 tests."""

from __future__ import annotations

import dataclasses
import hashlib
import subprocess
import sys
import threading
import time
from typing import Any, cast

import polars as pl
import pytest

import dartlab.analysis.financial.dataAssets as dataAssets
import dartlab.dataHub.catalog as dataCatalog
import dartlab.dataHub.paging.owner as ownerPaging
import dartlab.dataHub.paging.owner.entity as ownerPagingEntity
from dartlab.dataHub import (
    DataQuery,
    DataResult,
    FactorProjection,
    QueryBudget,
    TimeContext,
    UniverseSelection,
    data,
)
from dartlab.dataHub.catalog.universe import ResolvedMarket, ResolvedUniverse
from dartlab.dataHub.feature.observation import makeVariableObservation
from dartlab.dataHub.feature.query import buildFeatureObservationSet
from dartlab.dataHub.feature.registry import StateVariableSpec, buildStateVariableRegistry
from dartlab.dataHub.identity.vintage import VintageRef
from dartlab.dataHub.isolation.ownerProcess import OwnerProcessPage

_DIGEST = "1" * 64
_NORMALIZATION = "2" * 64
_SOURCE_PAYLOAD = b"synthetic-edgar-shard"
_SOURCE_PAYLOAD_DIGEST = hashlib.sha256(_SOURCE_PAYLOAD).hexdigest()


def _universe(size: int = 66) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "cik": [f"{index + 1:010d}" for index in range(size)],
            "ticker": [f"T{index:03d}" for index in range(size)],
            "title": [f"Test {index}" for index in range(size)],
            "exchange": ["Nasdaq"] * size,
            "is_exchange_listed": [True] * size,
            "is_otc": [False] * size,
        }
    )


def _dataset(subject: str, value: float = 100.0):
    entityId = f"US:{subject}"
    spec = StateVariableSpec(
        variableId="financial.revenue",
        signalId="financial.revenue",
        providerId="edgar",
        datasetId="companyfacts",
        unit="USD",
        role="observedFeature",
        evidenceRole="observed",
        frequency="quarter",
        timing="flow",
        transformId="identity",
        maxStalenessDays=500,
    )
    registry = buildStateVariableRegistry((spec,))
    vintage = VintageRef(
        artifactKind="companyfacts",
        provider="edgar",
        artifactId=entityId,
        artifactHash=_DIGEST,
        payloadHash=_DIGEST,
        knowledgeAsOf="20250115",
        availableAt="20250115",
        revisionPolicy="asKnown",
        coverage="asOfExact",
        fiscalThrough="20241231",
    )
    observation = makeVariableObservation(
        providerId="edgar",
        datasetId="companyfacts",
        entityId=entityId,
        signalId="financial.revenue",
        value=value,
        unit="USD",
        frequency="quarter",
        timing="flow",
        transformId="identity",
        evidenceRole="observed",
        eventAt="20241231",
        availableAt="20250115",
        knowledgeAsOf="20250115",
        availabilityPrecision="date",
        revisionId=f"revision-{subject}",
        vintage=vintage,
        normalizationRuleHash=_NORMALIZATION,
    )
    return buildFeatureObservationSet(registry, (observation,))


def _install(
    monkeypatch: pytest.MonkeyPatch,
    *,
    failing: set[str] | None = None,
) -> tuple[list[str], list[str]]:
    monkeypatch.setattr(
        "dartlab.core.dataLoader.loadEdgarTargetUniverse",
        lambda tier="all", **_kwargs: _universe(),
    )
    sourceCalls: list[str] = []
    ownerCalls: list[str] = []

    def sourcePin(_assetId: str, _category: str) -> str:
        sourceCalls.append("source-v1")
        return "resource-source-full:source-v1"

    def owner(
        *,
        subject: str,
        knownAt: str,
        measures: tuple[str, ...],
        sourceEntityId: str | None = None,
        sourcePayload: bytes | None = None,
        sourceIntegrityDigest: str | None = None,
    ):
        assert knownAt == "20250201"
        assert measures in {(), ("financial.revenue",)}
        assert sourceEntityId is not None
        assert sourcePayload == _SOURCE_PAYLOAD
        assert sourceIntegrityDigest == _SOURCE_PAYLOAD_DIGEST
        ownerCalls.append(subject)
        if failing and subject in failing:
            raise ValueError("private failure")
        return _dataset(subject, float(int(subject[1:]) + 1))

    def prepare(
        candidates: tuple[tuple[ownerPaging._OwnerTask, int], ...],
        *,
        deadline: float,
    ) -> dict[tuple[str, int], ownerPaging._VerifiedEntitySource]:
        assert deadline > time.perf_counter()
        return {
            (task.requestId, ordinal): ownerPaging._VerifiedEntitySource(
                _SOURCE_PAYLOAD,
                _SOURCE_PAYLOAD_DIGEST,
            )
            for task, ordinal in candidates
        }

    def runPage(
        session: ownerPaging._OwnerSession,
        *,
        deadline: float,
    ) -> OwnerProcessPage:
        candidates = ownerPaging._candidates(session)
        verified = ownerPaging._prepareEntitySources(
            candidates,
            deadline=deadline,
        )
        entries = ownerPaging._boundedEntries(
            candidates,
            session,
            deadline=deadline,
            verifiedSources=verified,
        )
        payload = ownerPaging._encodePage(
            entries,
            maxPageRows=session.pageMaxRows,
            maxPageBytes=session.pageMaxBytes,
            maxLogicalBytes=session.pageMaxLogicalBytes,
        )
        rowCount = sum(
            0 if entry.payload is None else ownerPaging.inspectArrowIpcPayload(entry.payload).rowCount
            for entry in entries
        )
        decoded = ownerPaging._decodePage(
            payload,
            claimedRowCount=rowCount,
            maxPageRows=session.pageMaxRows,
            maxPageBytes=session.pageMaxBytes,
            maxLogicalBytes=session.pageMaxLogicalBytes,
        )
        return OwnerProcessPage(
            payload=payload,
            rowCount=decoded.facts.rowCount,
            byteCount=len(payload),
            payloadDigest=hashlib.sha256(payload).hexdigest(),
        )

    monkeypatch.setattr(ownerPaging, "_resourceSourcePin", sourcePin)
    monkeypatch.setattr(ownerPaging, "_prepareEntitySources", prepare)
    monkeypatch.setattr(ownerPaging, "_runOwnerPageProcess", runPage)
    monkeypatch.setattr(dataAssets, "edgarFinancialFeatures", owner)
    return sourceCalls, ownerCalls


def _query() -> DataQuery:
    return DataQuery(
        universe=UniverseSelection(("US",)),
        projection=FactorProjection(measures=("financial.revenue",)),
        time=TimeContext(knownAt="20250201"),
        budget=QueryBudget(maxRows=100, maxBytes=8 * 1024 * 1024, timeoutMs=30_000),
    )


def _dartQuery(*, params: dict[str, Any] | None = None) -> DataQuery:
    return DataQuery(
        universe=UniverseSelection(("KR",)),
        projection=FactorProjection(measures=("financial.revenue",)),
        time=TimeContext(knownAt="20250520"),
        params={} if params is None else params,
        budget=QueryBudget(maxRows=100, maxBytes=8 * 1024 * 1024, timeoutMs=30_000),
    )


def _installDartUniverse(
    monkeypatch: pytest.MonkeyPatch,
    *,
    entityParams: tuple[tuple[str, tuple[tuple[str, str], ...]], ...],
) -> None:
    selection = UniverseSelection(("KR",))
    membership = ResolvedMarket(
        market="KR",
        provider="dart",
        entityIds=("005930",),
        membershipDigest=_DIGEST,
        sourceEntityIds=(("005930", "005930"),),
        entityParams=entityParams,
    )
    resolved = ResolvedUniverse(
        snapshotId="universe:test-kr",
        selection=selection,
        markets=(membership,),
        gaps=(),
    )
    monkeypatch.setattr(ownerPaging, "resolveUniverse", lambda _selection: resolved)
    monkeypatch.setattr(
        ownerPaging,
        "_resourceSourcePin",
        lambda _assetId, _category: "resource-source-full:dart-source-v1",
    )


def testDartEntityParameterIsPinnedRoundTrippedAndInjected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _installDartUniverse(
        monkeypatch,
        entityParams=(("005930", (("fiscalYearEndMonth", "12"),)),),
    )
    descriptor = next(
        asset for asset in dataCatalog.buildCatalog().assets if asset.assetId == "analysis.dartFinancialFeatures"
    )
    task = ownerPaging._plannedTask("dart-features", descriptor, _dartQuery())
    session = ownerPaging._OwnerSession(
        snapshotId="test-snapshot",
        contractHash=_DIGEST,
        requestedAssets=1,
        universeSnapshotId=task.universeSnapshotId,
        pageMaxRows=100,
        pageMaxBytes=8 * 1024 * 1024,
        pageMaxLogicalBytes=8 * 1024 * 1024,
        pageMaxEntities=1,
        pageTimeoutMs=30_000,
        maxConcurrency=1,
        tasks=(task,),
    )
    decoded = ownerPaging._decodeSession(ownerPaging._encodeSession(session))
    captured: list[dict[str, Any]] = []

    def owner(**kwargs: Any) -> None:
        captured.append(kwargs)
        raise ValueError("parameter boundary test")

    monkeypatch.setattr(dataAssets, "dartFinancialFeatures", owner)
    entry = ownerPaging._executeEntity(
        decoded.tasks[0],
        0,
        ownerPaging._VerifiedEntitySource(_SOURCE_PAYLOAD, _SOURCE_PAYLOAD_DIGEST),
    )

    assert decoded.tasks[0].entities[0].params == (("fiscalYearEndMonth", "12"),)
    assert captured == [
        {
            "subject": "005930",
            "sourceEntityId": "005930",
            "fiscalYearEndMonth": "12",
            "sourcePayload": _SOURCE_PAYLOAD,
            "sourceIntegrityDigest": _SOURCE_PAYLOAD_DIGEST,
            "knownAt": "20250520",
            # DART owner 도 measure pushdown 을 선언하므로 요청 measure 가 함께 내려간다.
            # 요청하지 않은 measure 를 owner 가 계산하지 않게 하는 것이 pushdown 의 본질이다.
            "measures": ("financial.revenue",),
        }
    ]
    assert entry.gapCodes == ("FEATURE_ENTITY_UNAVAILABLE",)


def testDartEntityParameterMissingOrQueryOverrideFailsBeforeOwner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    descriptor = next(
        asset for asset in dataCatalog.buildCatalog().assets if asset.assetId == "analysis.dartFinancialFeatures"
    )
    _installDartUniverse(monkeypatch, entityParams=(("005930", ()),))
    with pytest.raises(ValueError, match="entity parameter"):
        ownerPaging._plannedTask("dart-features", descriptor, _dartQuery())

    _installDartUniverse(
        monkeypatch,
        entityParams=(("005930", (("fiscalYearEndMonth", "12"),)),),
    )
    with pytest.raises(ValueError, match="source parameter"):
        ownerPaging._plannedTask(
            "dart-features",
            descriptor,
            _dartQuery(params={"fiscalYearEndMonth": 3}),
        )


def testOneQueryPagesWholeListedUniverseWithoutExternalSubjectLoop(monkeypatch: pytest.MonkeyPatch) -> None:
    _sourceCalls, ownerCalls = _install(monkeypatch)

    first = cast(DataResult, data("query", "analysis.edgarFinancialFeatures", query=_query()))
    pages = list(first.iterPages())

    assert [len(page.partitions) for page in pages] == [64, 2]
    assert [partition.selector[-1][1] for page in pages for partition in page.partitions] == [
        f"T{index:03d}" for index in range(66)
    ]
    assert ownerCalls == [f"T{index:03d}" for index in range(66)]
    assert pages[0].continuation is not None
    assert pages[-1].continuation is None
    assert pages[-1].universeCoverage[0].status == "complete"
    assert pages[-1].universeCoverage[0].returnedEntities == 66


def testEntityFailureAdvancesCursorAndKeepsCumulativeCoverage(monkeypatch: pytest.MonkeyPatch) -> None:
    _install(monkeypatch, failing={"T003"})

    pages = list(cast(DataResult, data("query", "analysis.edgarFinancialFeatures", query=_query())).iterPages())
    entities = [row["entityId"] for page in pages for partition in page.partitions for row in partition.data.to_dicts()]

    assert len(entities) == 65
    assert "US:T003" not in entities
    failure = next(gap for page in pages for gap in page.gaps if gap.subject == "T003")
    assert failure.code == "FEATURE_ENTITY_UNAVAILABLE"
    finalCoverage = pages[-1].universeCoverage[0]
    assert finalCoverage.status == "partial"
    assert finalCoverage.returnedEntities == 65
    assert finalCoverage.missingEntities == 1
    assert finalCoverage.missingSample == ("T003",)


def testCommittedContinuationReplayDoesNotTouchOwnerOrSource(monkeypatch: pytest.MonkeyPatch) -> None:
    sourceCalls, ownerCalls = _install(monkeypatch)
    first = cast(DataResult, data("query", "analysis.edgarFinancialFeatures", query=_query()))
    token = first.continuation
    assert token is not None
    second = cast(DataResult, cast(Any, data)("query", query={"continuation": token}))
    sourceCount = len(sourceCalls)
    ownerCount = len(ownerCalls)

    monkeypatch.setattr(
        ownerPaging,
        "_resourceSourcePin",
        lambda _assetId, _category: pytest.fail("committed replay는 source를 다시 읽으면 안 됩니다"),
    )
    monkeypatch.setattr(
        dataCatalog,
        "buildCatalog",
        lambda: pytest.fail("committed replay는 catalog를 다시 읽으면 안 됩니다"),
    )
    monkeypatch.setattr(
        dataAssets,
        "edgarFinancialFeatures",
        lambda **_kwargs: pytest.fail("committed replay는 owner code를 다시 읽으면 안 됩니다"),
    )
    monkeypatch.setattr(
        ownerPaging,
        "_runOwnerPageProcess",
        lambda *_args, **_kwargs: pytest.fail("committed replay는 process를 다시 만들면 안 됩니다"),
    )
    replay = cast(DataResult, cast(Any, data)("query", query={"continuation": token}))

    assert replay.dataSnapshotId == second.dataSnapshotId
    assert [partition.contentHash for partition in replay.partitions] == [
        partition.contentHash for partition in second.partitions
    ]
    assert len(sourceCalls) == sourceCount
    assert len(ownerCalls) == ownerCount


def testUncommittedContinuationRejectsSourceDriftBeforeOwnerCall(monkeypatch: pytest.MonkeyPatch) -> None:
    _sourceCalls, ownerCalls = _install(monkeypatch)
    first = cast(DataResult, data("query", "analysis.edgarFinancialFeatures", query=_query()))
    token = first.continuation
    assert token is not None
    ownerCount = len(ownerCalls)

    def staleSource(*_args: object, **_kwargs: object):
        raise ownerPaging.ContinuationError("CONTINUATION_SOURCE_STALE")

    monkeypatch.setattr(ownerPaging, "_prepareEntitySources", staleSource)

    resumed = cast(DataResult, cast(Any, data)("query", query={"continuation": token}))

    assert resumed.status == "failed"
    assert resumed.gaps[0].code == "CONTINUATION_SOURCE_STALE"
    assert len(ownerCalls) == ownerCount


def testCandidateSourcesUseOnePinnedBatchAndKeepMissingEntityOutOfOwner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from dartlab.providers.resourceStream import workbench as resourceWorkbench

    monkeypatch.setattr(
        "dartlab.core.dataLoader.loadEdgarTargetUniverse",
        lambda tier="all", **_kwargs: _universe(),
    )
    monkeypatch.setattr(
        ownerPaging,
        "_resourceSourcePin",
        lambda _assetId, _category: "resource-source-full:source-v1",
    )
    descriptor = next(
        asset for asset in dataCatalog.buildCatalog().assets if asset.assetId == "analysis.edgarFinancialFeatures"
    )
    task = ownerPaging._plannedTask("features", descriptor, _query())
    calls: list[tuple[str, ...]] = []
    cacheCreates: list[bool] = []

    def cachePath(
        _assetId: str,
        _category: str,
        *,
        create: bool = True,
    ) -> str:
        cacheCreates.append(create)
        return "fixture-manifest.json"

    def verify(
        _assetId: str,
        _category: str,
        companyIds: tuple[str, ...],
        _sourcePin: str,
        _cachePath: object,
        *,
        allowMissing: bool,
        readOnlyCache: bool,
    ):
        calls.append(companyIds)
        assert allowMissing is True
        assert readOnlyCache is True
        return (
            resourceWorkbench.VerifiedResourceShardPayload(
                companyId=companyIds[0],
                relativePath=f"{companyIds[0]}.parquet",
                integrityDigest=_SOURCE_PAYLOAD_DIGEST,
                encodedBytes=_SOURCE_PAYLOAD,
            ),
        )

    monkeypatch.setattr(resourceWorkbench, "verifyResourceShardPayloads", verify)
    monkeypatch.setattr(
        ownerPagingEntity,
        "manifestCachePath",
        cachePath,
    )
    prepared = ownerPaging._prepareEntitySources(
        ((task, 0), (task, 1)),
        deadline=time.perf_counter() + 5,
    )

    assert calls == [(task.entities[0].sourceEntityId, task.entities[1].sourceEntityId)]
    assert cacheCreates == [False]
    assert prepared[("features", 0)].payload == _SOURCE_PAYLOAD
    assert ("features", 1) not in prepared
    missing = ownerPaging._executeEntity(task, 1)
    assert missing.gapCodes == ("FEATURE_SOURCE_MISSING",)


def testCandidateSourceBoundaryRejectsFalsePayloadDigest(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from dartlab.providers.resourceStream import workbench as resourceWorkbench

    monkeypatch.setattr(
        "dartlab.core.dataLoader.loadEdgarTargetUniverse",
        lambda tier="all", **_kwargs: _universe(),
    )
    monkeypatch.setattr(
        ownerPaging,
        "_resourceSourcePin",
        lambda _assetId, _category: "resource-source-full:source-v1",
    )
    descriptor = next(
        asset for asset in dataCatalog.buildCatalog().assets if asset.assetId == "analysis.edgarFinancialFeatures"
    )
    task = ownerPaging._plannedTask("features", descriptor, _query())
    monkeypatch.setattr(
        resourceWorkbench,
        "verifyResourceShardPayloads",
        lambda *_args, **_kwargs: (
            resourceWorkbench.VerifiedResourceShardPayload(
                companyId=task.entities[0].sourceEntityId or "",
                relativePath="0000000001.parquet",
                integrityDigest="0" * 64,
                encodedBytes=_SOURCE_PAYLOAD,
            ),
        ),
    )

    with pytest.raises(ownerPaging.ContinuationError) as error:
        ownerPaging._prepareEntitySources(
            ((task, 0),),
            deadline=time.perf_counter() + 5,
        )
    assert error.value.code == "CONTINUATION_SOURCE_STALE"


@pytest.mark.parametrize(
    "expectedCode",
    (
        "CONTINUATION_SECURITY_FAILED",
        "OFFLINE_NETWORK_BLOCKED",
        "PAGEABLE_EAGER_WRITE_BLOCKED",
    ),
)
def testCandidateSourceBoundaryPreservesTypedSecurityCause(
    monkeypatch: pytest.MonkeyPatch,
    expectedCode: str,
) -> None:
    from dartlab.providers.resourceStream import workbench as resourceWorkbench

    monkeypatch.setattr(
        "dartlab.core.dataLoader.loadEdgarTargetUniverse",
        lambda tier="all", **_kwargs: _universe(),
    )
    monkeypatch.setattr(
        ownerPaging,
        "_resourceSourcePin",
        lambda _assetId, _category: "resource-source-full:source-v1",
    )
    descriptor = next(
        asset for asset in dataCatalog.buildCatalog().assets if asset.assetId == "analysis.edgarFinancialFeatures"
    )
    task = ownerPaging._plannedTask("features", descriptor, _query())

    class CodedBoundaryError(RuntimeError):
        code = expectedCode

    def failVerify(*_args: object, **_kwargs: object) -> None:
        if expectedCode == "CONTINUATION_SECURITY_FAILED":
            raise ownerPaging.ContinuationError(expectedCode)
        raise CodedBoundaryError("private boundary detail")

    monkeypatch.setattr(
        resourceWorkbench,
        "verifyResourceShardPayloads",
        failVerify,
    )
    with pytest.raises(ownerPaging.ContinuationError) as error:
        ownerPaging._prepareEntitySources(
            ((task, 0),),
            deadline=time.perf_counter() + 5,
        )

    assert error.value.code == expectedCode


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("assetVersionId", "analysis.edgarFinancialFeatures:changed"),
        ("label", "변경된 owner descriptor"),
    ),
)
def testUncommittedContinuationRejectsCatalogContractDriftBeforeOwnerCall(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: str,
) -> None:
    _sourceCalls, ownerCalls = _install(monkeypatch)
    first = cast(DataResult, data("query", "analysis.edgarFinancialFeatures", query=_query()))
    token = first.continuation
    assert token is not None
    ownerCount = len(ownerCalls)
    catalog = dataCatalog.buildCatalog()
    assets = tuple(
        dataclasses.replace(asset, **{field: value}) if asset.assetId == "analysis.edgarFinancialFeatures" else asset
        for asset in catalog.assets
    )
    monkeypatch.setattr(dataCatalog, "buildCatalog", lambda: dataclasses.replace(catalog, assets=assets))

    resumed = cast(DataResult, cast(Any, data)("query", query={"continuation": token}))

    assert resumed.status == "failed"
    assert resumed.gaps[0].code == "CONTINUATION_CONTRACT_STALE"
    assert len(ownerCalls) == ownerCount


def testUncommittedContinuationRejectsOwnerCodeDriftBeforeOwnerCall(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _sourceCalls, ownerCalls = _install(monkeypatch)
    first = cast(DataResult, data("query", "analysis.edgarFinancialFeatures", query=_query()))
    token = first.continuation
    assert token is not None
    ownerCount = len(ownerCalls)

    def changedOwner(*, subject: str, knownAt: str, sourceEntityId: str | None = None):
        ownerCalls.append(f"changed:{subject}:{knownAt}:{sourceEntityId}")
        return _dataset(subject, -1.0)

    monkeypatch.setattr(dataAssets, "edgarFinancialFeatures", changedOwner)

    resumed = cast(DataResult, cast(Any, data)("query", query={"continuation": token}))

    assert resumed.status == "failed"
    assert resumed.gaps[0].code == "CONTINUATION_CONTRACT_STALE"
    assert len(ownerCalls) == ownerCount


def testOwnerCodePinIsStableAcrossFreshProcess() -> None:
    descriptor = next(
        asset for asset in dataCatalog.buildCatalog().assets if asset.assetId == "analysis.edgarFinancialFeatures"
    )
    expected = ownerPaging._ownerCodePin(descriptor)
    script = (
        "from dartlab.dataHub.catalog import buildCatalog;"
        "from dartlab.dataHub.paging.owner import _ownerCodePin;"
        "descriptor=next(asset for asset in buildCatalog().assets "
        "if asset.assetId=='analysis.edgarFinancialFeatures');"
        "print(_ownerCodePin(descriptor))"
    )

    completed = subprocess.run(
        [sys.executable, "-X", "utf8", "-c", script],
        check=True,
        capture_output=True,
        text=True,
    )

    assert completed.stdout.strip() == expected


def testRequestedMeasuresBindOwnerQueryCodeAndSourcePins(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install(monkeypatch)
    descriptor = next(
        asset for asset in dataCatalog.buildCatalog().assets if asset.assetId == "analysis.edgarFinancialFeatures"
    )
    revenue = ownerPaging._plannedTask("revenue", descriptor, _query())
    marginQuery = dataclasses.replace(
        _query(),
        projection=FactorProjection(measures=("financial.operatingMargin",)),
    )
    margin = ownerPaging._plannedTask("margin", descriptor, marginQuery)

    assert revenue.queryPin != margin.queryPin
    assert revenue.ownerCodePin != margin.ownerCodePin
    assert revenue.sourcePin != margin.sourcePin


def testJsonMappingProvidesSameOneQueryPagingSurface(monkeypatch: pytest.MonkeyPatch) -> None:
    _install(monkeypatch)

    first = cast(
        DataResult,
        cast(Any, data)(
            "query",
            query={
                "requests": [
                    {
                        "assetId": "analysis.edgarFinancialFeatures",
                        "requestId": "usPit",
                        "universe": {"markets": ["US"], "membership": "listed"},
                        "projection": {"kind": "factor", "measures": ["financial.revenue"]},
                        "time": {"knownAt": "20250201"},
                    }
                ],
                "budget": {
                    "maxRows": 100,
                    "maxBytes": 8 * 1024 * 1024,
                    "timeoutMs": 30_000,
                },
            },
        ),
    )

    assert first.status == "partial"
    assert first.continuation is not None
    assert first.partitions[0].requestId == "usPit"


def testRequireCompleteFailsBeforeOwnerButMixedUsesOuterChain(monkeypatch: pytest.MonkeyPatch) -> None:
    _sourceCalls, ownerCalls = _install(monkeypatch)
    requireComplete = cast(
        DataResult,
        data(
            "query",
            "analysis.edgarFinancialFeatures",
            query=DataQuery(
                universe=UniverseSelection(("US",)),
                projection=FactorProjection(),
                time=TimeContext(knownAt="20250201"),
                completeness="requireComplete",
            ),
        ),
    )
    assert requireComplete.gaps[0].code == "PAGEABLE_REQUIRE_COMPLETE_UNSUPPORTED"
    assert ownerCalls == []

    mixed = cast(
        DataResult,
        cast(Any, data)(
            "query",
            query={
                "requests": [
                    {
                        "assetId": "analysis.edgarFinancialFeatures",
                        "requestId": "features",
                        "universe": {"markets": ["US"]},
                        "projection": {"kind": "factor"},
                        "time": {"knownAt": "20250201"},
                    },
                    {
                        "assetId": "resource.finance",
                        "requestId": "locator",
                        "subjects": ["005930"],
                        "projection": {"kind": "resource"},
                    },
                ]
            },
        ),
    )

    assert mixed.status == "partial"
    assert [gap.code for gap in mixed.gaps] == ["FEATURE_OBSERVATION_CONDITIONAL"] * 64
    assert {gap.requestId for gap in mixed.gaps} == {"features"}
    assert [partition.requestId for partition in mixed.partitions] == ["features"] * 64 + ["locator"]
    assert mixed.continuation is not None
    resumed = cast(DataResult, cast(Any, data)("query", query={"continuation": mixed.continuation}))
    assert resumed.status == "ok"
    assert [gap.code for gap in resumed.gaps] == ["FEATURE_OBSERVATION_CONDITIONAL"] * 3
    assert "64회" in resumed.gaps[0].message
    assert [partition.requestId for partition in resumed.partitions] == ["features"] * 2
    assert ownerCalls == [f"T{index:03d}" for index in range(66)]


def testMixedOwnerAndMonkeypatchedEagerFailsCodePinBeforeAnyOwner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _sourceCalls, ownerCalls = _install(monkeypatch)
    simulationCalls: list[dict[str, Any]] = []

    def simulationInputs(**kwargs: Any) -> dict[str, Any]:
        simulationCalls.append(kwargs)
        return {"simulation": kwargs}

    monkeypatch.setattr(dataAssets, "simulationInputs", simulationInputs)
    result = cast(
        DataResult,
        cast(Any, data)(
            "query",
            query={
                "requests": [
                    {
                        "assetId": "analysis.edgarFinancialFeatures",
                        "requestId": "features",
                        "universe": {"markets": ["US"]},
                        "projection": {"kind": "factor"},
                        "time": {"knownAt": "20250201"},
                    },
                    {
                        "assetId": "analysis.simulationInputs",
                        "requestId": "unsafe",
                        "subjects": ["AAPL"],
                    },
                ]
            },
        ),
    )

    assert result.status == "failed"
    assert result.gaps[0].code == "PAGEABLE_EAGER_CODE_PIN_FAILED"
    assert ownerCalls == []
    assert simulationCalls == []


def testMixedOuterResumeRejectsOwnerSourceDriftWithoutRerunningAnyLane(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _sourceCalls, ownerCalls = _install(monkeypatch)
    import dartlab.dataHub.execution as executionModule

    locatorCalls: list[str] = []
    originalExecute = executionModule._execute

    def execute(descriptor: Any, query: Any, selector: Any) -> Any:
        locatorCalls.append(descriptor.assetId)
        return originalExecute(descriptor, query, selector)

    monkeypatch.setattr(executionModule, "_execute", execute)
    first = cast(
        DataResult,
        cast(Any, data)(
            "query",
            query={
                "requests": [
                    {
                        "assetId": "analysis.edgarFinancialFeatures",
                        "requestId": "features",
                        "universe": {"markets": ["US"]},
                        "projection": {"kind": "factor"},
                        "time": {"knownAt": "20250201"},
                    },
                    {
                        "assetId": "resource.finance",
                        "requestId": "locator",
                        "subjects": ["005930", "000660"],
                        "projection": {"kind": "resource"},
                    },
                ]
            },
        ),
    )
    token = first.continuation
    assert [gap.code for gap in first.gaps] == ["FEATURE_OBSERVATION_CONDITIONAL"] * 64, (
        first.gaps,
        first.coverage,
        [partition.requestId for partition in first.partitions],
        locatorCalls,
    )
    assert first.coverage.failedPartitions == 0
    assert token is not None
    ownerCount = len(ownerCalls)
    locatorCount = len(locatorCalls)
    changed = _universe().with_columns(
        pl.when(pl.col("ticker") == "T009").then(pl.lit("9999999999")).otherwise(pl.col("cik")).alias("cik")
    )
    monkeypatch.setattr(
        "dartlab.core.dataLoader.loadEdgarTargetUniverse",
        lambda tier="all", **_kwargs: changed,
    )

    stale = cast(DataResult, cast(Any, data)("query", query={"continuation": token}))

    assert stale.status == "failed"
    assert stale.gaps[0].code == "CONTINUATION_SOURCE_STALE"
    assert len(ownerCalls) == ownerCount
    assert len(locatorCalls) == locatorCount
    monkeypatch.setattr(
        "dartlab.core.dataLoader.loadEdgarTargetUniverse",
        lambda tier="all", **_kwargs: _universe(),
    )
    recovered = cast(DataResult, cast(Any, data)("query", query={"continuation": token}))
    assert recovered.status == "ok", (recovered.gaps, recovered.continuation, recovered.coverage)
    assert [gap.code for gap in recovered.gaps] == ["FEATURE_OBSERVATION_CONDITIONAL"] * 3
    assert "64회" in recovered.gaps[0].message
    assert len(ownerCalls) == ownerCount + 2
    assert len(locatorCalls) == locatorCount


def testUniverseSourceIdentityDriftFailsBeforeOwnerCall(monkeypatch: pytest.MonkeyPatch) -> None:
    _sourceCalls, ownerCalls = _install(monkeypatch)
    first = cast(DataResult, data("query", "analysis.edgarFinancialFeatures", query=_query()))
    token = first.continuation
    assert token is not None
    ownerCount = len(ownerCalls)
    changed = _universe().with_columns(
        pl.when(pl.col("ticker") == "T009").then(pl.lit("9999999999")).otherwise(pl.col("cik")).alias("cik")
    )
    monkeypatch.setattr(
        "dartlab.core.dataLoader.loadEdgarTargetUniverse",
        lambda tier="all", **_kwargs: changed,
    )

    resumed = cast(DataResult, cast(Any, data)("query", query={"continuation": token}))

    assert resumed.status == "failed"
    assert resumed.gaps[0].code == "CONTINUATION_SOURCE_STALE"
    assert len(ownerCalls) == ownerCount


def testExplicitSubjectKeepsExistingEagerSubjectFanoutPath(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, Any]] = []

    def owner(**kwargs: Any):
        calls.append(kwargs)
        return _dataset(str(kwargs["subject"]))

    monkeypatch.setattr(dataAssets, "edgarFinancialFeatures", owner)
    monkeypatch.setattr(
        ownerPaging,
        "_resourceSourcePin",
        lambda _assetId, _category: pytest.fail("explicit subject는 universe source를 읽으면 안 됩니다"),
    )

    result = cast(
        DataResult,
        data(
            "query",
            "analysis.edgarFinancialFeatures",
            query=DataQuery(
                subjects=("T000",),
                projection=FactorProjection(),
                time=TimeContext(knownAt="20250201"),
            ),
        ),
    )

    assert result.status == "partial"
    assert [gap.code for gap in result.gaps] == ["FEATURE_OBSERVATION_CONDITIONAL"]
    assert result.continuation is None
    assert calls == [
        {
            "knownAt": "20250201",
            "measures": (),
            "subject": "T000",
        }
    ]


def testRowBudgetCutsPageBeforeEntityCapWithoutLossOrDuplication(monkeypatch: pytest.MonkeyPatch) -> None:
    _install(monkeypatch)
    query = dataclasses.replace(_query(), budget=QueryBudget(maxRows=3, maxBytes=8 * 1024 * 1024))

    pages = list(cast(DataResult, data("query", "analysis.edgarFinancialFeatures", query=query)).iterPages())

    assert [len(page.partitions) for page in pages] == [3] * 22
    assert [dict(partition.selector)["subject"] for page in pages for partition in page.partitions] == [
        f"T{index:03d}" for index in range(66)
    ]


def testHistoricalUniverseFailsClosedBeforeSourceOrOwnerCall(monkeypatch: pytest.MonkeyPatch) -> None:
    sourceCalls, ownerCalls = _install(monkeypatch)
    query = dataclasses.replace(
        _query(),
        universe=UniverseSelection(("US",), asOf="2025-01-01"),
    )

    result = cast(DataResult, data("query", "analysis.edgarFinancialFeatures", query=query))

    assert result.status == "failed"
    assert result.gaps[0].code == "UNIVERSE_PIT_UNSUPPORTED"
    assert sourceCalls == []
    assert ownerCalls == []


def testChildPageIdentityIsRejectedBeforeContinuationCommit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install(monkeypatch)
    validRunner = ownerPaging._runOwnerPageProcess

    def corruptRunner(
        session: ownerPaging._OwnerSession,
        *,
        deadline: float,
    ) -> OwnerProcessPage:
        validPage = validRunner(session, deadline=deadline)
        decoded = ownerPaging._decodePage(
            validPage.payload,
            claimedRowCount=validPage.rowCount,
            maxPageRows=session.pageMaxRows,
            maxPageBytes=session.pageMaxBytes,
            maxLogicalBytes=session.pageMaxLogicalBytes,
        )
        entries = (
            dataclasses.replace(
                decoded.entries[0],
                assetId="analysis.tamperedOwner",
            ),
            *decoded.entries[1:],
        )
        payload = ownerPaging._encodePage(
            entries,
            maxPageRows=session.pageMaxRows,
            maxPageBytes=session.pageMaxBytes,
            maxLogicalBytes=session.pageMaxLogicalBytes,
        )
        return OwnerProcessPage(
            payload=payload,
            rowCount=validPage.rowCount,
            byteCount=len(payload),
            payloadDigest=hashlib.sha256(payload).hexdigest(),
        )

    monkeypatch.setattr(ownerPaging, "_runOwnerPageProcess", corruptRunner)

    result = cast(
        DataResult,
        data("query", "analysis.edgarFinancialFeatures", query=_query()),
    )

    assert result.status == "failed"
    assert result.continuation is None
    assert result.gaps[0].code == "CONTINUATION_CORRUPT"


def testSameConcurrencyGroupExecutesSerially(monkeypatch: pytest.MonkeyPatch) -> None:
    _install(monkeypatch)
    descriptor = next(
        asset for asset in dataCatalog.buildCatalog().assets if asset.assetId == "analysis.edgarFinancialFeatures"
    )
    descriptor = dataclasses.replace(descriptor, concurrencyGroup="shared-owner")
    task = ownerPaging._plannedTask("first", descriptor, _query())
    second = dataclasses.replace(task, requestId="second")
    session = ownerPaging._OwnerSession(
        snapshotId="test-snapshot",
        contractHash=_DIGEST,
        requestedAssets=2,
        universeSnapshotId=task.universeSnapshotId,
        pageMaxRows=100,
        pageMaxBytes=8 * 1024 * 1024,
        pageMaxLogicalBytes=8 * 1024 * 1024,
        pageMaxEntities=2,
        pageTimeoutMs=5_000,
        maxConcurrency=2,
        tasks=(task, second),
    )
    lock = threading.Lock()
    active = 0
    maxActive = 0

    def execute(activeTask: ownerPaging._OwnerTask, ordinal: int):
        nonlocal active, maxActive
        with lock:
            active += 1
            maxActive = max(maxActive, active)
        time.sleep(0.03)
        with lock:
            active -= 1
        entity = activeTask.entities[ordinal]
        return ownerPaging._failureEntry(
            activeTask,
            ordinal,
            entity,
            "TEST_FAILURE",
            "동시성 계약 test",
        )

    monkeypatch.setattr(ownerPaging, "_executeEntity", execute)

    entries = ownerPaging._boundedEntries(
        ((task, 0), (second, 0)),
        session,
        deadline=time.perf_counter() + 5,
    )

    assert len(entries) == 2
    assert maxActive == 1


def testDifferentConcurrencyGroupsExecuteInParallelWithinBudget(monkeypatch: pytest.MonkeyPatch) -> None:
    _install(monkeypatch)
    descriptor = next(
        asset for asset in dataCatalog.buildCatalog().assets if asset.assetId == "analysis.edgarFinancialFeatures"
    )
    first = ownerPaging._plannedTask("first", descriptor, _query())
    second = dataclasses.replace(
        first,
        requestId="second",
        descriptor=dataclasses.replace(descriptor, concurrencyGroup="independent-owner"),
    )
    session = ownerPaging._OwnerSession(
        snapshotId="test-snapshot",
        contractHash=_DIGEST,
        requestedAssets=2,
        universeSnapshotId=first.universeSnapshotId,
        pageMaxRows=100,
        pageMaxBytes=8 * 1024 * 1024,
        pageMaxLogicalBytes=8 * 1024 * 1024,
        pageMaxEntities=2,
        pageTimeoutMs=5_000,
        maxConcurrency=2,
        tasks=(first, second),
    )
    barrier = threading.Barrier(2)
    lock = threading.Lock()
    active = 0
    maxActive = 0

    def execute(activeTask: ownerPaging._OwnerTask, ordinal: int):
        nonlocal active, maxActive
        with lock:
            active += 1
            maxActive = max(maxActive, active)
        barrier.wait(timeout=2)
        with lock:
            active -= 1
        entity = activeTask.entities[ordinal]
        return ownerPaging._failureEntry(
            activeTask,
            ordinal,
            entity,
            "TEST_FAILURE",
            "동시성 계약 test",
        )

    monkeypatch.setattr(ownerPaging, "_executeEntity", execute)

    entries = ownerPaging._boundedEntries(
        ((first, 0), (second, 0)),
        session,
        deadline=time.perf_counter() + 5,
    )

    assert len(entries) == 2
    assert maxActive == 2


def testMultipleOwnerRequestsRotateAcrossPagesWithoutStarvation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install(monkeypatch)
    descriptor = next(
        asset for asset in dataCatalog.buildCatalog().assets if asset.assetId == "analysis.edgarFinancialFeatures"
    )
    first = ownerPaging._plannedTask("first", descriptor, _query())
    tasks = (
        first,
        dataclasses.replace(first, requestId="second"),
        dataclasses.replace(first, requestId="third"),
    )
    session = ownerPaging._OwnerSession(
        snapshotId="test-snapshot",
        contractHash=_DIGEST,
        requestedAssets=3,
        universeSnapshotId=first.universeSnapshotId,
        pageMaxRows=100,
        pageMaxBytes=8 * 1024 * 1024,
        pageMaxLogicalBytes=8 * 1024 * 1024,
        pageMaxEntities=2,
        pageTimeoutMs=5_000,
        maxConcurrency=1,
        tasks=tasks,
    )
    seenPages: list[list[str]] = []

    for _ in range(3):
        candidates = ownerPaging._candidates(session)
        entries = tuple(
            ownerPaging._failureEntry(
                task,
                ordinal,
                task.entities[ordinal],
                "TEST_FAILURE",
                "fairness test",
            )
            for task, ordinal in candidates
        )
        seenPages.append([entry.requestId for entry in entries])
        session = dataclasses.replace(
            session,
            tasks=ownerPaging._updatedTasks(session, entries),
            nextTaskIndex=ownerPaging._nextTaskIndex(session, entries),
        )
        session = ownerPaging._decodeSession(ownerPaging._encodeSession(session))

    assert seenPages == [
        ["first", "second"],
        ["third", "first"],
        ["second", "third"],
    ]
