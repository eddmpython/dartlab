"""Unified Data Workbench bounded execution과 result assembly."""

from __future__ import annotations

import dataclasses
import hashlib
import importlib
import json
import time
from collections.abc import Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from typing import Any

from dartlab.data.catalog import buildCatalog
from dartlab.data.contentSeal import resultSnapshotId
from dartlab.data.contracts import (
    AssetRef,
    Coverage,
    DataAssetDescriptor,
    DataGap,
    DataQuery,
    DataRequest,
    DataResult,
    FactorProjection,
    NarrativeProjection,
    ResourceProjection,
    UniverseCoverage,
    projectionKind,
)
from dartlab.data.projections import projectOutput
from dartlab.data.universe import ResolvedMarket, ResolvedUniverse, entityIds, resolveUniverse


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
    if query.time is None:
        return None
    support = set(descriptor.temporalSupport)
    if query.time.knownAt is not None and "knownAt" not in support:
        return DataGap(
            "PIT_UNSUPPORTED",
            "owner가 knownAt vintage를 실제 실행에 전달할 수 없습니다",
            descriptor.assetId,
        )
    if query.time.knownAt is not None and isinstance(query.projection, (FactorProjection, NarrativeProjection)):
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


def _callableCall(descriptor: DataAssetDescriptor, query: DataQuery, selector: Mapping[str, str]) -> Any:
    """Owner-declared callable을 descriptor에 적힌 인자 계약으로 실행한다."""
    if descriptor.executorModule is None or descriptor.executorAttribute is None:
        raise ValueError("callable executor 경로가 없습니다")
    module = importlib.import_module(descriptor.executorModule)
    executor = getattr(module, descriptor.executorAttribute)
    kwargs = dict(query.params)
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


def executeDataQuery(assetIds: Sequence[str], query: DataQuery) -> DataResult:
    """Asset IDs를 resolve, validate, execute, project해 하나의 DataResult로 반환한다.

    Capabilities:
        catalog snapshot 결박, temporal fail-closed, owner public engine 호출, typed projection,
        row budget, systemic failure 구분, receipt와 lineage 동봉을 한 실행 경로에서 제공한다.

    Args:
        assetIds: stable catalog asset ID sequence.
        query: subjects, measures, projection, time, params, budget, completeness.

    Returns:
        DataResult. asset별 native schema는 partition으로 분리된다.

    Raises:
        ValueError: asset 수가 budget을 넘거나 asset ID가 비어 있을 때.
    """
    startedAt = time.perf_counter()
    deadline = startedAt + query.budget.timeoutMs / 1000
    if query.continuation is not None:
        if assetIds:
            raise ValueError("continuation query는 assets override를 허용하지 않습니다")
        from dartlab.data.resourcePaging import resumeResourcePaging

        return resumeResourcePaging(query.continuation, deadline=deadline, startedAt=startedAt)

    requested = _compiledRequests(assetIds, query)
    catalog = buildCatalog()
    byId = {asset.assetId: asset for asset in catalog.assets}
    resolved: list[tuple[str, DataAssetDescriptor, DataQuery]] = []
    gaps: list[DataGap] = list(catalog.gaps)
    for requestId, request, activeQuery in requested:
        descriptor = byId.get(request.assetId)
        if descriptor is None:
            gaps.append(DataGap("ASSET_NOT_FOUND", request.assetId, request.assetId, requestId=requestId))
            continue
        if not descriptor.queryable:
            gaps.append(
                DataGap(
                    "ASSET_NOT_QUERYABLE",
                    "catalog-only 또는 policy 차단 asset",
                    request.assetId,
                    requestId=requestId,
                )
            )
            continue
        resolved.append((requestId, descriptor, activeQuery))

    from dartlab.data.resourcePaging import executeInitialResourcePaging, isPageableResource

    if any(isPageableResource(descriptor, activeQuery) for _, descriptor, activeQuery in resolved):
        resolvedRefs = tuple(
            dict.fromkeys(AssetRef(descriptor.assetId, descriptor.assetVersionId) for _, descriptor, _ in resolved)
        )
        contractHash = hashlib.sha256(_canonical({"assets": resolvedRefs, "query": query})).hexdigest()
        return executeInitialResourcePaging(
            assetIds,
            query,
            requestedAssets=len(requested),
            snapshotId=catalog.snapshotId,
            contractHash=contractHash,
            resolved=resolved,
            hasPlanningGaps=bool(gaps),
            deadline=deadline,
        )

    tasks: list[_ExecutionTask] = []
    universeCache: dict[object, ResolvedUniverse] = {}
    universeSnapshots: set[str] = set()
    universeCoverage: list[UniverseCoverage] = []
    for requestId, descriptor, activeQuery in resolved:
        temporalGap = _temporalGap(descriptor, activeQuery)
        if temporalGap:
            gaps.append(dataclasses.replace(temporalGap, requestId=requestId))
            continue
        resolvedUniverse = None
        if activeQuery.universe is not None:
            resolvedUniverse = universeCache.get(activeQuery.universe)
            if resolvedUniverse is None:
                resolvedUniverse = resolveUniverse(activeQuery.universe)
                universeCache[activeQuery.universe] = resolvedUniverse
            universeSnapshots.add(resolvedUniverse.snapshotId)
            gaps.extend(
                dataclasses.replace(gap, assetId=descriptor.assetId, requestId=requestId)
                for gap in resolvedUniverse.gaps
            )
        selectors, selectorGaps = _selectors(descriptor, activeQuery)
        gaps.extend(dataclasses.replace(gap, requestId=requestId) for gap in selectorGaps)
        universeByMarket = resolvedUniverse.byMarket() if resolvedUniverse is not None else {}
        if activeQuery.universe is not None:
            selectors = tuple(selector for selector in selectors if selector.get("market") in universeByMarket)
        plannedMarkets = {selector["market"] for selector in selectors if "market" in selector}
        if activeQuery.universe is not None:
            selectorCodes = tuple(dict.fromkeys(gap.code for gap in selectorGaps))
            resolverCodes = tuple(dict.fromkeys(gap.code for gap in resolvedUniverse.gaps)) if resolvedUniverse else ()
            for market in activeQuery.universe.markets:
                if market in plannedMarkets:
                    continue
                codes = selectorCodes or resolverCodes or ("UNIVERSE_UNSUPPORTED",)
                universeCoverage.append(
                    _failedUniverseCoverage(
                        requestId,
                        descriptor,
                        market,
                        resolvedUniverse.snapshotId if resolvedUniverse else None,
                        universeByMarket.get(market),
                        codes,
                    )
                )
        for selector in selectors:
            requestRef = _requestRef(descriptor, activeQuery, selector, requestId)
            market = selector.get("market")
            tasks.append(
                _ExecutionTask(
                    requestId,
                    descriptor,
                    activeQuery,
                    selector,
                    requestRef,
                    universeByMarket.get(market) if market else None,
                    resolvedUniverse.snapshotId if resolvedUniverse else None,
                )
            )

    partitions = []
    receipts: list[str] = []
    remainingRows = query.budget.maxRows
    remainingBytes = query.budget.maxBytes
    stopExecution = False
    processedTasks = 0
    maxConcurrency = min(query.budget.maxConcurrency, len(tasks)) if tasks else 1
    for window in _executionWindows(tasks, maxConcurrency):
        if stopExecution:
            break
        executor = ThreadPoolExecutor(max_workers=len(window), thread_name_prefix="dartlab-data")
        futures = tuple(executor.submit(_execute, task.descriptor, task.query, task.selector) for task in window)
        abandonWindow = False
        try:
            for task, future in zip(window, futures, strict=True):
                if remainingRows <= 0 or remainingBytes <= 0:
                    gaps.append(
                        DataGap(
                            "QUERY_BUDGET_EXHAUSTED",
                            "전체 query 결과 예산이 소진됐습니다",
                            task.descriptor.assetId,
                            requestId=task.requestId,
                        )
                    )
                    coverageRow = _universeCoverage(task, gapCodes=("QUERY_BUDGET_EXHAUSTED",))
                    if coverageRow is not None:
                        universeCoverage.append(coverageRow)
                    stopExecution = True
                    abandonWindow = True
                    break
                remainingSeconds = deadline - time.perf_counter()
                if remainingSeconds <= 0:
                    gaps.append(
                        DataGap(
                            "QUERY_TIMEOUT",
                            "query 실행 기한을 초과했습니다",
                            task.descriptor.assetId,
                            requestId=task.requestId,
                        )
                    )
                    coverageRow = _universeCoverage(task, gapCodes=("QUERY_TIMEOUT",))
                    if coverageRow is not None:
                        universeCoverage.append(coverageRow)
                    stopExecution = True
                    abandonWindow = True
                    break
                try:
                    raw = future.result(timeout=remainingSeconds)
                except FutureTimeoutError:
                    gaps.append(
                        DataGap(
                            "QUERY_TIMEOUT",
                            "owner 실행이 query 기한을 초과했습니다",
                            task.descriptor.assetId,
                            task.selector.get("subject"),
                            requestId=task.requestId,
                        )
                    )
                    coverageRow = _universeCoverage(task, gapCodes=("QUERY_TIMEOUT",))
                    if coverageRow is not None:
                        universeCoverage.append(coverageRow)
                    stopExecution = True
                    abandonWindow = True
                    break
                except Exception as exc:
                    gaps.append(
                        DataGap(
                            "ASSET_EXECUTION_FAILED",
                            f"{type(exc).__name__}: {exc}",
                            task.descriptor.assetId,
                            task.selector.get("subject"),
                            requestId=task.requestId,
                        )
                    )
                    coverageRow = _universeCoverage(task, gapCodes=("ASSET_EXECUTION_FAILED",))
                    if coverageRow is not None:
                        universeCoverage.append(coverageRow)
                    processedTasks += 1
                    continue
                if time.perf_counter() > deadline:
                    gaps.append(
                        DataGap(
                            "QUERY_TIMEOUT",
                            "owner 결과가 query 기한 뒤에 도착해 폐기했습니다",
                            task.descriptor.assetId,
                            task.selector.get("subject"),
                            requestId=task.requestId,
                        )
                    )
                    coverageRow = _universeCoverage(task, gapCodes=("QUERY_TIMEOUT",))
                    if coverageRow is not None:
                        universeCoverage.append(coverageRow)
                    stopExecution = True
                    abandonWindow = True
                    break
                coverageRow = _universeCoverage(task, raw)
                if coverageRow is not None:
                    universeCoverage.append(coverageRow)
                    if coverageRow.status == "partial":
                        gaps.append(
                            DataGap(
                                "UNIVERSE_COVERAGE_PARTIAL",
                                (
                                    f"{coverageRow.market} {coverageRow.matchedEntities}/"
                                    f"{coverageRow.requestedEntities} entities matched"
                                ),
                                task.descriptor.assetId,
                                requestId=task.requestId,
                            )
                        )
                    elif coverageRow.status == "unverified":
                        gaps.append(
                            DataGap(
                                "UNIVERSE_COVERAGE_UNVERIFIED",
                                f"{coverageRow.market} owner output에서 entity identity를 확인할 수 없습니다",
                                task.descriptor.assetId,
                                requestId=task.requestId,
                            )
                        )
                tasksAfter = len(tasks) - processedTasks - 1
                reservedRows = min(max(0, remainingRows - 1), tasksAfter)
                reservedBytes = min(max(0, remainingBytes - 1), tasksAfter * 1024)
                partitionBudget = dataclasses.replace(
                    task.query.budget,
                    maxRows=remainingRows - reservedRows,
                    maxBytes=remainingBytes - reservedBytes,
                )
                partitionQuery = dataclasses.replace(task.query, budget=partitionBudget)
                try:
                    partition, projectionGaps = projectOutput(
                        raw,
                        task.descriptor,
                        partitionQuery,
                        selector=task.selector,
                        receiptRef=task.requestRef,
                        requestId=task.requestId,
                    )
                    gaps.extend(
                        dataclasses.replace(gap, requestId=gap.requestId or task.requestId) for gap in projectionGaps
                    )
                    if partition is not None:
                        partitions.append(partition)
                        if partition.lineage is not None:
                            receipts.append(partition.lineage.runId)
                        remainingRows -= partition.rowCount
                        remainingBytes -= _outputBytes(partition.data)
                        if partition.truncated:
                            gaps.append(
                                DataGap(
                                    "CONTINUATION_UNSUPPORTED",
                                    "owner가 pageable source revision과 cursor를 선언하지 않아 이어보기를 발급하지 않았습니다",
                                    task.descriptor.assetId,
                                    task.selector.get("subject"),
                                    requestId=task.requestId,
                                )
                            )
                except Exception as exc:
                    gaps.append(
                        DataGap(
                            "ASSET_EXECUTION_FAILED",
                            f"{type(exc).__name__}: {exc}",
                            task.descriptor.assetId,
                            task.selector.get("subject"),
                            requestId=task.requestId,
                        )
                    )
                processedTasks += 1
        finally:
            for future in futures:
                if abandonWindow:
                    future.cancel()
            executor.shutdown(wait=not abandonWindow, cancel_futures=abandonWindow)

    coveredTaskKeys = {(row.requestId, row.selector) for row in universeCoverage if row.selector}
    for task in tasks:
        if task.universeMarket is None:
            continue
        selectorKey = tuple(sorted((str(key), str(value)) for key, value in task.selector.items()))
        if (task.requestId, selectorKey) in coveredTaskKeys:
            continue
        coverageRow = _universeCoverage(task, gapCodes=("QUERY_NOT_EXECUTED",))
        if coverageRow is not None:
            universeCoverage.append(coverageRow)

    succeeded = len(partitions)
    failures = len(gaps)
    if query.completeness == "requireComplete" and failures:
        status = "failed"
        partitions = []
    elif succeeded == 0:
        status = "failed"
    elif failures:
        status = "partial"
    else:
        status = "ok"
    resolvedRefs = tuple(
        dict.fromkeys(AssetRef(descriptor.assetId, descriptor.assetVersionId) for _, descriptor, _ in resolved)
    )
    contractHash = hashlib.sha256(_canonical({"assets": resolvedRefs, "query": query})).hexdigest()
    lineageRefs = tuple(dict.fromkeys(ref for partition in partitions for ref in partition.lineageRefs))
    continuation = None
    assertions = tuple(assertion for partition in partitions for assertion in partition.qualityAssertions)
    if len(universeSnapshots) == 1:
        universeSnapshotId = next(iter(universeSnapshots))
    elif universeSnapshots:
        universeSnapshotId = (
            f"universe-query:{hashlib.sha256(_canonical(tuple(sorted(universeSnapshots)))).hexdigest()}"
        )
    else:
        universeSnapshotId = None
    dataSnapshotId = resultSnapshotId(
        catalogSnapshotId=catalog.snapshotId,
        contractHash=contractHash,
        partitions=partitions,
        universeSnapshotId=universeSnapshotId,
    )
    return DataResult(
        status=status,
        partitions=tuple(partitions),
        assets=resolvedRefs,
        snapshotId=catalog.snapshotId,
        contractHash=contractHash,
        coverage=Coverage(len(requested), len(resolved), succeeded, failures),
        gaps=tuple(gaps),
        lineageRefs=lineageRefs,
        executionReceipts=tuple(receipts),
        continuation=continuation,
        qualityAssertions=assertions,
        universeSnapshotId=universeSnapshotId,
        universeCoverage=tuple(universeCoverage),
        dataSnapshotId=dataSnapshotId,
    )
