"""Unified Data Workbench 실행 계획과 owner 호출 지원 함수."""

from __future__ import annotations

import dataclasses
import hashlib
import importlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

from dartlab.data.contracts import (
    DataAssetDescriptor,
    DataGap,
    DataQuery,
    DataRequest,
    FactorProjection,
    NarrativeProjection,
    ResourceProjection,
    UniverseCoverage,
    projectionKind,
)
from dartlab.data.universe import ResolvedMarket, entityIds


@dataclasses.dataclass(frozen=True, slots=True)
class _ExecutionTask:
    """결정적 순서를 가진 owner 실행 단위."""

    requestId: str
    descriptor: DataAssetDescriptor
    query: DataQuery
    selector: Mapping[str, str]
    requestRef: str
    universeMarket: ResolvedMarket | None = None
    universeSnapshotId: str | None = None


def _executionWindows(
    tasks: Sequence[_ExecutionTask],
    maxConcurrency: int,
) -> tuple[tuple[_ExecutionTask, ...], ...]:
    """같은 공유 상태 group을 직렬화하며 독립 task는 병렬 window로 묶는다."""

    pending = list(tasks)
    windows: list[tuple[_ExecutionTask, ...]] = []
    while pending:
        selectedCount = 0
        groups: set[str] = set()
        assetMarkets: set[tuple[str, str | None]] = set()
        for task in pending:
            group = task.descriptor.concurrencyGroup
            if group is not None and group in groups:
                break
            assetMarket = (task.descriptor.assetId, task.selector.get("market"))
            if assetMarket in assetMarkets:
                break
            selectedCount += 1
            assetMarkets.add(assetMarket)
            if group is not None:
                groups.add(group)
            if selectedCount >= maxConcurrency:
                break
        window = tuple(pending[:selectedCount])
        del pending[:selectedCount]
        windows.append(window)
    return tuple(windows)


def _canonical(value: Any) -> bytes:
    def serializeDefault(item: Any) -> Any:
        """실행 영수증 입력을 결정적 JSON 표현으로 변환한다."""

        if dataclasses.is_dataclass(item):
            return {field.name: getattr(item, field.name) for field in dataclasses.fields(item)}
        if isinstance(item, Mapping):
            return dict(item)
        if isinstance(item, (tuple, set, frozenset)):
            return list(item)
        return str(item)

    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=serializeDefault
    ).encode()


def _requestRef(
    descriptor: DataAssetDescriptor,
    query: DataQuery,
    selector: Mapping[str, str],
    requestId: str,
) -> str:
    payload = {
        "assetVersionId": descriptor.assetVersionId,
        "query": query,
        "requestId": requestId,
        "selector": dict(selector),
    }
    return f"data-request:{hashlib.sha256(_canonical(payload)).hexdigest()}"


def _temporalGap(descriptor: DataAssetDescriptor, query: DataQuery) -> DataGap | None:
    metadata = dict(descriptor.metadata)
    if metadata.get("knownAtRequired") is True and (query.time is None or query.time.knownAt is None):
        return DataGap(
            "FEATURE_KNOWN_AT_REQUIRED",
            "owner feature asset은 명시적인 knownAt cutoff가 필요합니다",
            descriptor.assetId,
        )
    if query.time is None:
        return None
    support = set(descriptor.temporalSupport)
    if query.time.knownAt is not None and "knownAt" not in support:
        return DataGap(
            "PIT_UNSUPPORTED",
            "owner가 knownAt vintage를 실제 실행에 전달할 수 없습니다",
            descriptor.assetId,
        )
    observationPit = metadata.get("observationPIT") is True
    if query.time.knownAt is not None and (
        isinstance(query.projection, NarrativeProjection)
        or (isinstance(query.projection, FactorProjection) and not observationPit)
    ):
        return DataGap(
            "OBSERVATION_PIT_METADATA_REQUIRED",
            "canonical projection이 row별 knowledge time과 revision을 보존하지 못해 PIT를 발급하지 않습니다",
            descriptor.assetId,
        )
    if query.time.validAt is not None and "validAt" not in support:
        return DataGap(
            "VALID_TIME_UNSUPPORTED",
            "owner가 validAt 절단을 지원하지 않습니다",
            descriptor.assetId,
        )
    return None


def _selectors(
    descriptor: DataAssetDescriptor,
    query: DataQuery,
) -> tuple[tuple[dict[str, str], ...], tuple[DataGap, ...]]:
    """Descriptor가 선언한 selector 계약으로 실행 partition을 계획한다."""

    if query.universe is not None:
        if descriptor.executionMode != "ownerBulk" or descriptor.universeKind != "listedEquity":
            return (), (
                DataGap(
                    "UNIVERSE_UNSUPPORTED",
                    f"{descriptor.assetId}는 listed equity owner-bulk 실행을 선언하지 않았습니다",
                    descriptor.assetId,
                ),
            )
        if query.universe.explicitIds:
            return (), (
                DataGap(
                    "UNIVERSE_FILTER_UNSUPPORTED",
                    "owner가 explicit entity filter pushdown을 선언하지 않았습니다",
                    descriptor.assetId,
                ),
            )
        if descriptor.marketParam and descriptor.marketParam in query.params:
            return (), (
                DataGap(
                    "UNIVERSE_PARAM_CONFLICT",
                    f"{descriptor.marketParam}은 universe markets가 소유합니다",
                    descriptor.assetId,
                ),
            )

    if isinstance(query.projection, ResourceProjection) and not query.projection.includePayload:
        return ({},), ()
    projectionMeasures = query.projection.measures if isinstance(query.projection, FactorProjection) else ()
    measures = query.measures or projectionMeasures
    values = (
        query.subjects
        if descriptor.selectorKind == "subject"
        else measures
        if descriptor.selectorKind == "measure"
        else ()
    )
    baseSelectors = tuple({descriptor.selectorKind: value} for value in values) if values else ({},)
    required = descriptor.selectorRequired or descriptor.executorKind == "resource"
    if required and not values:
        expected = "subjects" if descriptor.selectorKind == "subject" else "measures"
        return (), (
            DataGap(
                "MISSING_SELECTOR",
                f"{descriptor.assetId} query에는 {expected}가 필요합니다",
                descriptor.assetId,
            ),
        )
    if query.universe is None:
        return baseSelectors, ()

    supportedMarkets = set(descriptor.universeMarkets)
    selectors: list[dict[str, str]] = []
    gaps: list[DataGap] = []
    for market in query.universe.markets:
        if market not in supportedMarkets:
            gaps.append(
                DataGap(
                    "UNIVERSE_MARKET_UNSUPPORTED",
                    f"{descriptor.assetId}는 {market} universe를 지원하지 않습니다",
                    descriptor.assetId,
                )
            )
            continue
        for base in baseSelectors:
            selectors.append(dict(base) | {"market": market})
    return tuple(selectors), tuple(gaps)


def _engineCall(descriptor: DataAssetDescriptor, query: DataQuery, selector: Mapping[str, str]) -> Any:
    import dartlab

    engine = getattr(dartlab, descriptor.owner)
    kwargs = dict(query.params)
    subject = selector.get("subject")
    measure = selector.get("measure")
    market = selector.get("market")
    if market is not None and descriptor.marketParam:
        kwargs[descriptor.marketParam] = market
    if subject is not None and descriptor.subjectParam:
        kwargs[descriptor.subjectParam] = subject
    target = measure
    if subject is not None and descriptor.subjectParam == "target":
        target = None
    if target is not None:
        return engine(descriptor.executorAxis, target, **kwargs)
    return engine(descriptor.executorAxis, **kwargs)


def _resourceCall(descriptor: DataAssetDescriptor, query: DataQuery, selector: Mapping[str, str]) -> Any:
    projection = query.projection
    if isinstance(projection, ResourceProjection) and not projection.includePayload:
        return None
    shardKind = str(dict(descriptor.metadata).get("shardKind", "bulk"))
    if shardKind not in {"company", "series"}:
        raise ValueError(f"RESOURCE_PAYLOAD_UNBOUNDED: shardKind={shardKind}")
    from dartlab.core.dataLoader import loadData

    subject = selector.get("subject")
    if not subject:
        raise ValueError("resource query는 subject가 필요합니다")
    kwargs: dict[str, Any] = {}
    for key in ("sinceYear", "columns", "refresh"):
        if key in query.params:
            kwargs[key] = query.params[key]
    return loadData(subject, descriptor.executorAxis or "panel", **kwargs)


def _requestedMeasures(query: DataQuery) -> tuple[str, ...]:
    """Query-level override 또는 factor projection의 요청 measure를 고정한다."""

    projectionMeasures = query.projection.measures if isinstance(query.projection, FactorProjection) else ()
    return tuple(query.measures or projectionMeasures)


def _callableCall(descriptor: DataAssetDescriptor, query: DataQuery, selector: Mapping[str, str]) -> Any:
    """Owner-declared callable을 descriptor에 적힌 인자 계약으로 실행한다."""
    if descriptor.executorModule is None or descriptor.executorAttribute is None:
        raise ValueError("callable executor 경로가 없습니다")
    module = importlib.import_module(descriptor.executorModule)
    executor = getattr(module, descriptor.executorAttribute)
    kwargs = dict(query.params)
    if descriptor.measureParam:
        if descriptor.measureParam in kwargs:
            raise ValueError(f"{descriptor.measureParam}은 factor projection이 소유합니다")
        kwargs[descriptor.measureParam] = _requestedMeasures(query)
    subject = selector.get("subject")
    if subject is not None and descriptor.subjectParam:
        kwargs[descriptor.subjectParam] = subject
    market = selector.get("market")
    if market is not None and descriptor.marketParam:
        kwargs[descriptor.marketParam] = market
    if query.time is not None:
        if query.time.validAt is not None and descriptor.validTimeParam:
            kwargs[descriptor.validTimeParam] = query.time.validAt
        if query.time.knownAt is not None and descriptor.knowledgeTimeParam:
            kwargs[descriptor.knowledgeTimeParam] = query.time.knownAt
    return executor(**kwargs)


def _execute(descriptor: DataAssetDescriptor, query: DataQuery, selector: Mapping[str, str]) -> Any:
    if descriptor.executorKind == "engineAxis":
        return _engineCall(descriptor, query, selector)
    if descriptor.executorKind == "resource":
        return _resourceCall(descriptor, query, selector)
    if descriptor.executorKind == "callable":
        return _callableCall(descriptor, query, selector)
    raise ValueError("catalog-only asset은 materialize할 수 없습니다")


def _outputBytes(value: Any) -> int:
    estimatedSize = getattr(value, "estimated_size", None)
    if callable(estimatedSize):
        observedSize = estimatedSize()
        if type(observedSize) is not int:
            raise TypeError("owner output byte estimate가 int가 아닙니다")
        return observedSize
    return len(repr(value).encode("utf-8"))


def _universeCoverage(
    task: _ExecutionTask,
    raw: Any | None = None,
    *,
    gapCodes: tuple[str, ...] = (),
) -> UniverseCoverage | None:
    """Owner 결과를 snapshot membership과 비교해 market별 coverage를 만든다."""

    membership = task.universeMarket
    market = task.selector.get("market")
    if membership is None or market is None:
        return None
    expected = frozenset(membership.entityIds)
    selector = tuple(sorted((str(key), str(value)) for key, value in task.selector.items()))
    if gapCodes:
        return UniverseCoverage(
            requestId=task.requestId,
            assetId=task.descriptor.assetId,
            market=market,
            provider=membership.provider,
            executionMode=task.descriptor.executionMode,
            snapshotId=task.universeSnapshotId,
            selector=selector,
            requestedEntities=len(expected),
            returnedEntities=0,
            matchedEntities=0,
            missingEntities=len(expected),
            extraEntities=0,
            status="failed",
            missingSample=tuple(f"{market}:{value}" for value in sorted(expected)[:32]),
            gapCodes=gapCodes,
        )
    observed = entityIds(raw, market)
    if observed is None:
        return UniverseCoverage(
            requestId=task.requestId,
            assetId=task.descriptor.assetId,
            market=market,
            provider=membership.provider,
            executionMode=task.descriptor.executionMode,
            snapshotId=task.universeSnapshotId,
            selector=selector,
            requestedEntities=len(expected),
            returnedEntities=0,
            matchedEntities=0,
            missingEntities=0,
            extraEntities=0,
            status="unverified",
            gapCodes=("UNIVERSE_COVERAGE_UNVERIFIED",),
        )
    matched = expected & observed
    missing = expected - observed
    extra = observed - expected
    status = "complete" if not missing else "partial" if observed else "failed"
    codes = ("UNIVERSE_COVERAGE_PARTIAL",) if missing else ()
    return UniverseCoverage(
        requestId=task.requestId,
        assetId=task.descriptor.assetId,
        market=market,
        provider=membership.provider,
        executionMode=task.descriptor.executionMode,
        snapshotId=task.universeSnapshotId,
        selector=selector,
        requestedEntities=len(expected),
        returnedEntities=len(observed),
        matchedEntities=len(matched),
        missingEntities=len(missing),
        extraEntities=len(extra),
        status=status,
        missingSample=tuple(f"{market}:{value}" for value in sorted(missing)[:32]),
        gapCodes=codes,
    )


def _failedUniverseCoverage(
    requestId: str,
    descriptor: DataAssetDescriptor,
    market: str,
    snapshotId: str | None,
    membership: ResolvedMarket | None,
    gapCodes: tuple[str, ...],
) -> UniverseCoverage:
    expected = membership.entityIds if membership is not None else ()
    provider = membership.provider if membership is not None else None
    return UniverseCoverage(
        requestId=requestId,
        assetId=descriptor.assetId,
        market=market,
        provider=provider,
        executionMode=descriptor.executionMode,
        snapshotId=snapshotId,
        selector=(("market", market),),
        requestedEntities=len(expected),
        returnedEntities=0,
        matchedEntities=0,
        missingEntities=len(expected),
        extraEntities=0,
        status="failed",
        missingSample=tuple(f"{market}:{value}" for value in expected[:32]),
        gapCodes=gapCodes,
    )


def _activeQuery(query: DataQuery, request: DataRequest) -> DataQuery:
    """Query 공통값에 request별 override를 합성한다."""

    subjects = request.subjects or (() if request.universe is not None else query.subjects)
    universe = request.universe if request.universe is not None else None if request.subjects else query.universe
    return dataclasses.replace(
        query,
        subjects=subjects,
        measures=request.measures or query.measures,
        universe=universe,
        projection=request.projection or query.projection,
        time=request.time or query.time,
        params=dict(query.params) | dict(request.params),
        requests=(),
    )


def _compiledRequests(assetIds: Sequence[str], query: DataQuery) -> tuple[tuple[str, DataRequest, DataQuery], ...]:
    """Legacy asset 인자와 혼합 DataRequest를 stable 실행 단위로 합친다."""

    legacyIds = tuple(dict.fromkeys(str(assetId) for assetId in assetIds if str(assetId)))
    requests = [DataRequest(assetId=assetId, requestId=assetId) for assetId in legacyIds]
    requests.extend(query.requests)
    if not requests:
        raise ValueError("query assets가 비었습니다")
    if len(requests) > query.budget.maxAssets:
        raise ValueError("assets가 query budget을 초과했습니다")

    used: set[str] = set()
    compiled = []
    for index, request in enumerate(requests):
        active = _activeQuery(query, request)
        baseId = request.requestId or f"{request.assetId}:{projectionKind(active.projection)}"
        requestId = baseId
        if requestId in used:
            if request.requestId is not None:
                raise ValueError("requestId는 query 안에서 고유해야 합니다")
            requestId = f"{baseId}:{index}"
        used.add(requestId)
        compiled.append((requestId, request, active))
    return tuple(compiled)
