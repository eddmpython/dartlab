"""Unified Data Workbench bounded execution과 result assembly."""

from __future__ import annotations

import dataclasses
import hashlib
import time
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError

from dartlab.dataHub.catalog import buildCatalog
from dartlab.dataHub.contentSeal import resultSnapshotId
from dartlab.dataHub.continuation import ContinuationError
from dartlab.dataHub.contracts import (
    AssetRef,
    Coverage,
    DataAssetDescriptor,
    DataGap,
    DataQuery,
    DataResult,
    UniverseCoverage,
)
from dartlab.dataHub.executionSupport import (
    _activeQuery,
    _callableCall,
    _canonical,
    _compiledRequests,
    _engineCall,
    _execute,
    _ExecutionTask,
    _executionWindows,
    _failedUniverseCoverage,
    _outputBytes,
    _requestedMeasures,
    _requestRef,
    _resourceCall,
    _selectors,
    _temporalGap,
    _universeCoverage,
)
from dartlab.dataHub.materialization import MaterializationDirective, MaterializationError
from dartlab.dataHub.projections import projectOutput
from dartlab.dataHub.universe import ResolvedUniverse, resolveUniverse


def _systemicFailureResult(
    code: str,
    message: str,
    *,
    assets: Sequence[AssetRef] = (),
    snapshotId: str = "data-snapshot:materialization-unavailable",
    contractHash: str = "0" * 64,
    requestedAssets: int = 0,
    resolvedAssets: int = 0,
) -> DataResult:
    """Typed control-plane 실패를 비밀값 없는 public result로 닫는다."""

    return DataResult(
        status="failed",
        partitions=(),
        assets=tuple(assets),
        snapshotId=snapshotId,
        contractHash=contractHash,
        coverage=Coverage(requestedAssets, resolvedAssets, 0, 1),
        gaps=(DataGap(code, message, systemic=True),),
        lineageRefs=(),
        executionReceipts=(),
    )


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
    materialization = query.materialization
    query = dataclasses.replace(
        query,
        materialization=MaterializationDirective(),
    )
    if query.continuation is not None:
        if assetIds:
            raise ValueError("continuation query는 assets override를 허용하지 않습니다")
        from dartlab.dataHub.pagingRouter import resumeDataPaging

        try:
            return resumeDataPaging(
                query.continuation,
                deadline=deadline,
                startedAt=startedAt,
            )
        except (ContinuationError, MaterializationError) as error:
            return _systemicFailureResult(error.code, str(error))

    if materialization.mode in {"reuse", "offline"}:
        from dartlab.dataHub.materialization.query import replayMaterializedQuery

        try:
            replayed = replayMaterializedQuery(
                assetIds,
                query,
                materialization,
                deadline=deadline,
            )
        except (ContinuationError, MaterializationError) as error:
            return _systemicFailureResult(
                error.code,
                str(error),
            )
        if replayed is not None:
            return replayed

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

    if materialization.mode != "runtime":
        resolvedRefs = tuple(
            dict.fromkeys(AssetRef(descriptor.assetId, descriptor.assetVersionId) for _, descriptor, _ in resolved)
        )
        contractHash = hashlib.sha256(_canonical({"assets": resolvedRefs, "query": query})).hexdigest()
        if query.completeness == "requireComplete" or gaps or not resolved:
            code = (
                "PAGEABLE_REQUIRE_COMPLETE_UNSUPPORTED"
                if query.completeness == "requireComplete"
                else "PAGEABLE_PLAN_INCOMPLETE"
            )
            return DataResult(
                status="failed",
                partitions=(),
                assets=resolvedRefs,
                snapshotId=catalog.snapshotId,
                contractHash=contractHash,
                coverage=Coverage(len(requested), len(resolved), 0, 1),
                gaps=(
                    DataGap(
                        code,
                        "materialization composite 계획을 완전하게 고정할 수 없습니다",
                        systemic=False,
                    ),
                ),
                lineageRefs=(),
                executionReceipts=(),
            )
        try:
            from dartlab.dataHub.compositePaging import prepareCompositePaging
            from dartlab.dataHub.materialization.query import (
                materializeCompositeQuery,
            )

            plan = prepareCompositePaging(
                assetIds,
                query,
                requestedAssets=len(requested),
                snapshotId=catalog.snapshotId,
                contractHash=contractHash,
                resolved=resolved,
                deadline=deadline,
            )
            return materializeCompositeQuery(
                plan,
                query,
                deadline=deadline,
            )
        except MaterializationError as error:
            code = error.code
            message = str(error)
        except ContinuationError as error:
            code = error.code
            message = str(error)
        except Exception:
            code = "MATERIALIZATION_NOT_READY"
            message = "materialization generation을 게시하지 못했습니다"
        return _systemicFailureResult(
            code,
            message,
            assets=resolvedRefs,
            snapshotId=catalog.snapshotId,
            contractHash=contractHash,
            requestedAssets=len(requested),
            resolvedAssets=len(resolved),
        )

    from dartlab.dataHub.ownerPaging import executeInitialOwnerPaging, isPageableOwner
    from dartlab.dataHub.resourcePaging import executeInitialResourcePaging, isPageableResource

    resourcePaging = tuple(isPageableResource(descriptor, activeQuery) for _, descriptor, activeQuery in resolved)
    ownerPaging = tuple(isPageableOwner(descriptor, activeQuery) for _, descriptor, activeQuery in resolved)
    hasPageable = any(resourcePaging) or any(ownerPaging)
    allResourcePaging = bool(resourcePaging) and all(resourcePaging)
    allOwnerPaging = bool(ownerPaging) and all(ownerPaging)
    if hasPageable and not (allResourcePaging or allOwnerPaging):
        resolvedRefs = tuple(
            dict.fromkeys(AssetRef(descriptor.assetId, descriptor.assetVersionId) for _, descriptor, _ in resolved)
        )
        contractHash = hashlib.sha256(_canonical({"assets": resolvedRefs, "query": query})).hexdigest()
        from dartlab.dataHub.compositePaging import executeInitialCompositePaging

        return executeInitialCompositePaging(
            assetIds,
            query,
            requestedAssets=len(requested),
            snapshotId=catalog.snapshotId,
            contractHash=contractHash,
            resolved=resolved,
            hasPlanningGaps=bool(gaps),
            deadline=deadline,
        )

    if any(resourcePaging):
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

    if any(ownerPaging):
        resolvedRefs = tuple(
            dict.fromkeys(AssetRef(descriptor.assetId, descriptor.assetVersionId) for _, descriptor, _ in resolved)
        )
        contractHash = hashlib.sha256(_canonical({"assets": resolvedRefs, "query": query})).hexdigest()
        return executeInitialOwnerPaging(
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
    elif any(gap.systemic for gap in gaps):
        # D09 장애 정직성. universe resolver 부재, provider discovery 실패, 빈 universe 같은
        # systemic gap 은 다른 asset 하나가 성공했다는 이유로 partial 로 내려가지 않는다.
        # 단일 asset 의 정상 결손과 provider 전체 장애를 같은 등급으로 숨기지 않기 위함이다.
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
