"""Unified Data Workbench bounded execution과 result assembly."""

from __future__ import annotations

import dataclasses
import hashlib
import time
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError

from dartlab.dataHub.catalog import buildCatalog
from dartlab.dataHub.catalog.universe import ResolvedUniverse, resolveUniverse
from dartlab.dataHub.continuation import ContinuationError
from dartlab.dataHub.contracts import (
    AssetRef,
    Coverage,
    DataAssetDescriptor,
    DataCatalogResult,
    DataGap,
    DataQuery,
    DataRequest,
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
from dartlab.dataHub.identity.contentSeal import resultSnapshotId
from dartlab.dataHub.materialization import MaterializationDirective, MaterializationError
from dartlab.dataHub.projection.output import projectOutput
from dartlab.dataHub.telemetry import dataHubLogger, recordFailure

_log = dataHubLogger(__name__)


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


def _resolvedIdentity(
    resolved: Sequence[tuple[str, DataAssetDescriptor, DataQuery]], query: DataQuery
) -> tuple[tuple[AssetRef, ...], str]:
    """해결된 asset 집합의 참조 목록과 계약 해시를 만든다.

    같은 두 줄이 네 자리에서 되풀이되고 있었다. 되풀이 자체보다, 그중 한 곳만 고치면 나머지
    셋과 해시가 갈라진다는 것이 문제다. 계약 해시는 세대 재사용 판정에 쓰이므로 갈라지면
    조용히 다른 세대를 집는다.
    """
    resolvedRefs = tuple(
        dict.fromkeys(AssetRef(descriptor.assetId, descriptor.assetVersionId) for _, descriptor, _ in resolved)
    )
    contractHash = hashlib.sha256(_canonical({"assets": resolvedRefs, "query": query})).hexdigest()
    return resolvedRefs, contractHash


def _pageableEntryPoint(resourcePaging: tuple[bool, ...], ownerPaging: tuple[bool, ...]):
    """페이징 레인 진입점을 고른다. 전부 eager 면 None.

    세 갈래가 각자 같은 인자 묶음을 만들어 넘기고 있었고, 그 앞에서 계약 해시를 세 번 따로
    계산했다. 갈리는 것은 어느 함수를 부르느냐 하나뿐이라 그것만 남긴다.

    한 asset 이라도 페이징이면 섞어 쓸 수 없다. 레인이 서로 다른 이어받기 상태를 쓰기
    때문에, 일부만 페이징인 경우는 composite 가 받아 하나로 묶는다.
    """
    if not (any(resourcePaging) or any(ownerPaging)):
        return None
    allResource = bool(resourcePaging) and all(resourcePaging)
    allOwner = bool(ownerPaging) and all(ownerPaging)
    if not (allResource or allOwner):
        from dartlab.dataHub.paging.composite import executeInitialCompositePaging

        return executeInitialCompositePaging
    if any(resourcePaging):
        from dartlab.dataHub.paging.resource import executeInitialResourcePaging

        return executeInitialResourcePaging
    from dartlab.dataHub.paging.owner import executeInitialOwnerPaging

    return executeInitialOwnerPaging


def _resolveAgainstCatalog(
    requested: Sequence[tuple[str, DataRequest, DataQuery]], catalog: DataCatalogResult
) -> tuple[list[tuple[str, DataAssetDescriptor, DataQuery]], list[DataGap]]:
    """요청을 카탈로그 descriptor 로 해석하고, 못 찾거나 막힌 것은 gap 으로 돌린다."""
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
    return resolved, gaps


def _materializeComposite(
    assetIds: Sequence[str],
    query: DataQuery,
    *,
    catalog: DataCatalogResult,
    requested: Sequence[tuple[str, DataRequest, DataQuery]],
    resolved: Sequence[tuple[str, DataAssetDescriptor, DataQuery]],
    gaps: Sequence[DataGap],
    deadline: float,
) -> DataResult:
    """runtime 이 아닌 요청을 세대로 굽는 경로. 계획을 완전히 고정할 수 없으면 실패로 닫는다.

    굽기는 재사용을 전제로 하므로 계획이 흔들리면 안 된다. 결손이 하나라도 있으면 그 세대는
    나중에 다른 결과를 낼 수 있어, 부분 성공을 돌려주는 대신 이유를 적어 실패로 끝낸다.
    """
    resolvedRefs, contractHash = _resolvedIdentity(resolved, query)
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
        from dartlab.dataHub.materialization.query import materializeCompositeQuery
        from dartlab.dataHub.paging.composite import prepareCompositePaging

        plan = prepareCompositePaging(
            assetIds,
            query,
            requestedAssets=len(requested),
            snapshotId=catalog.snapshotId,
            contractHash=contractHash,
            resolved=resolved,
            deadline=deadline,
        )
        return materializeCompositeQuery(plan, query, deadline=deadline)
    except (MaterializationError, ContinuationError) as error:
        code = error.code
        message = str(error)
    except Exception:
        recordFailure(_log, "MATERIALIZATION_NOT_READY")
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


def _planExecutionTasks(
    resolved: Sequence[tuple[str, DataAssetDescriptor, DataQuery]],
) -> tuple[list[_ExecutionTask], list[DataGap], set[str], list[UniverseCoverage]]:
    """해결된 asset 을 실행 단위로 펼친다. universe 해석과 selector 전개가 여기서 끝난다.

    실행 루프와 분리하는 이유는 둘이 서로 다른 실패를 다루기 때문이다. 여기서 나는 실패는
    "무엇을 실행할지 정하지 못함"(시점 미지원, universe 해석 실패, selector 부재)이고,
    실행 루프의 실패는 "정한 것을 못 가져옴"이다. 한 함수에 있으면 그 둘이 섞여 보인다.
    """
    tasks: list[_ExecutionTask] = []
    gaps: list[DataGap] = []
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
            universeCoverage.extend(
                _uncoveredMarkets(requestId, descriptor, activeQuery, selectors, selectorGaps, resolvedUniverse)
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
    return tasks, gaps, universeSnapshots, universeCoverage


def _uncoveredMarkets(
    requestId: str,
    descriptor: DataAssetDescriptor,
    activeQuery: DataQuery,
    selectors: Sequence[dict],
    selectorGaps: Sequence[DataGap],
    resolvedUniverse: ResolvedUniverse | None,
) -> list[UniverseCoverage]:
    """요청한 시장 중 실행 계획에 한 줄도 못 들어간 것을 적는다.

    빠진 시장을 조용히 두면 결과가 그 시장을 다뤘는데 자료가 없었던 것처럼 읽힌다. 실제로는
    계획 단계에서 통째로 빠진 것이다.
    """
    plannedMarkets = {selector["market"] for selector in selectors if "market" in selector}
    selectorCodes = tuple(dict.fromkeys(gap.code for gap in selectorGaps))
    resolverCodes = tuple(dict.fromkeys(gap.code for gap in resolvedUniverse.gaps)) if resolvedUniverse else ()
    universeByMarket = resolvedUniverse.byMarket() if resolvedUniverse is not None else {}
    rows: list[UniverseCoverage] = []
    for market in activeQuery.universe.markets:
        if market in plannedMarkets:
            continue
        codes = selectorCodes or resolverCodes or ("UNIVERSE_UNSUPPORTED",)
        rows.append(
            _failedUniverseCoverage(
                requestId,
                descriptor,
                market,
                resolvedUniverse.snapshotId if resolvedUniverse else None,
                universeByMarket.get(market),
                codes,
            )
        )
    return rows


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
        from dartlab.dataHub.paging.router import resumeDataPaging

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
    resolved, gaps = _resolveAgainstCatalog(requested, catalog)

    if materialization.mode != "runtime":
        return _materializeComposite(
            assetIds,
            query,
            catalog=catalog,
            requested=requested,
            resolved=resolved,
            gaps=gaps,
            deadline=deadline,
        )

    from dartlab.dataHub.paging.owner import isPageableOwner
    from dartlab.dataHub.paging.resource import isPageableResource

    resourcePaging = tuple(isPageableResource(descriptor, activeQuery) for _, descriptor, activeQuery in resolved)
    ownerPaging = tuple(isPageableOwner(descriptor, activeQuery) for _, descriptor, activeQuery in resolved)
    pagingEntry = _pageableEntryPoint(resourcePaging, ownerPaging)
    if pagingEntry is not None:
        _, contractHash = _resolvedIdentity(resolved, query)
        return pagingEntry(
            assetIds,
            query,
            requestedAssets=len(requested),
            snapshotId=catalog.snapshotId,
            contractHash=contractHash,
            resolved=resolved,
            hasPlanningGaps=bool(gaps),
            deadline=deadline,
        )

    tasks, planGaps, universeSnapshots, universeCoverage = _planExecutionTasks(resolved)
    gaps.extend(planGaps)

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

    _appendUnexecutedCoverage(tasks, universeCoverage)
    return _assembleEagerResult(
        query,
        catalog=catalog,
        requested=requested,
        resolved=resolved,
        partitions=partitions,
        receipts=receipts,
        gaps=gaps,
        universeSnapshots=universeSnapshots,
        universeCoverage=universeCoverage,
    )


def _appendUnexecutedCoverage(tasks: Sequence[_ExecutionTask], universeCoverage: list[UniverseCoverage]) -> None:
    """예산이나 기한 때문에 아예 안 돌아간 task 를 coverage 에 적는다.

    안 적으면 그 시장이 조회됐는데 결과가 없었던 것으로 읽힌다. 실제로는 순서가 뒤라서
    차례가 오지 않은 것이다.
    """
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


def _eagerStatus(query: DataQuery, *, producedPartitions: int, gaps: Sequence[DataGap]) -> tuple[str, bool]:
    """실행 결과의 등급과 부분 결과를 버릴지 여부를 정한다.

    Returns:
        ``(status, discardPartials)``. 두 번째 값이 참이면 행과 영수증을 함께 버린다.
    """
    if query.completeness == "requireComplete" and gaps:
        return "failed", True
    if producedPartitions == 0:
        return "failed", False
    if any(gap.systemic for gap in gaps):
        # D09 장애 정직성. universe resolver 부재, provider discovery 실패, 빈 universe 같은
        # systemic gap 은 다른 asset 하나가 성공했다는 이유로 partial 로 내려가지 않는다.
        # 단일 asset 의 정상 결손과 provider 전체 장애를 같은 등급으로 숨기지 않기 위함이다.
        return "failed", False
    if gaps:
        return "partial", False
    return "ok", False


def _universeSnapshotId(universeSnapshots: set[str]) -> str | None:
    """여러 universe 를 하나의 식별자로 접는다. 하나뿐이면 그대로 쓴다."""
    if len(universeSnapshots) == 1:
        return next(iter(universeSnapshots))
    if not universeSnapshots:
        return None
    return f"universe-query:{hashlib.sha256(_canonical(tuple(sorted(universeSnapshots)))).hexdigest()}"


def _assembleEagerResult(
    query: DataQuery,
    *,
    catalog: DataCatalogResult,
    requested: Sequence[tuple[str, DataRequest, DataQuery]],
    resolved: Sequence[tuple[str, DataAssetDescriptor, DataQuery]],
    partitions: list,
    receipts: list[str],
    gaps: list[DataGap],
    universeSnapshots: set[str],
    universeCoverage: list[UniverseCoverage],
) -> DataResult:
    """실행 산출물을 하나의 결과 봉투로 닫는다.

    성적표, 영수증, lineage, 품질단언이 전부 같은 `partitions` 에서 나오도록 한 자리에
    모아 둔다. 예전에는 개수를 먼저 세고 나중에 행을 버려서 세 증적이 서로 다른 말을 했다.
    """
    # 성적표는 asset 단위 실패 수다. catalog discovery gap 은 데이터 실패가 아니고,
    # 한 asset 이 gap 을 여러 개 만들어도 실패는 하나다. gaps 개수를 그대로 쓰면
    # 두 방향 모두로 성적표가 부정확해진다.
    catalogGapKeys = {(gap.code, gap.assetId, gap.requestId) for gap in catalog.gaps}
    dataGaps = [gap for gap in gaps if (gap.code, gap.assetId, gap.requestId) not in catalogGapKeys]
    failedAssets = len({(gap.requestId, gap.assetId) for gap in dataGaps})

    status, discardPartials = _eagerStatus(query, producedPartitions=len(partitions), gaps=gaps)
    if discardPartials:
        # 부분 결과를 안 받겠다고 한 요청이다. 행을 버리면 그 행에서 나온 성적표와 영수증도
        # 같이 버려야 한다.
        partitions = []
        receipts = []

    resolvedRefs, contractHash = _resolvedIdentity(resolved, query)
    universeSnapshotId = _universeSnapshotId(universeSnapshots)
    return DataResult(
        status=status,
        partitions=tuple(partitions),
        assets=resolvedRefs,
        snapshotId=catalog.snapshotId,
        contractHash=contractHash,
        coverage=Coverage(len(requested), len(resolved), len(partitions), failedAssets),
        gaps=tuple(gaps),
        lineageRefs=tuple(dict.fromkeys(ref for partition in partitions for ref in partition.lineageRefs)),
        executionReceipts=tuple(receipts),
        continuation=None,
        qualityAssertions=tuple(assertion for partition in partitions for assertion in partition.qualityAssertions),
        universeSnapshotId=universeSnapshotId,
        universeCoverage=tuple(universeCoverage),
        dataSnapshotId=resultSnapshotId(
            catalogSnapshotId=catalog.snapshotId,
            contractHash=contractHash,
            partitions=partitions,
            universeSnapshotId=universeSnapshotId,
        ),
    )
