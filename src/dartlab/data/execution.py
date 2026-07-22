"""Unified Data Workbench bounded execution과 result assembly."""

from __future__ import annotations

import dataclasses
import hashlib
import importlib
import json
import time
from collections.abc import Mapping, Sequence
from typing import Any

from dartlab.data.catalog import buildCatalog
from dartlab.data.contracts import (
    AssetRef,
    Coverage,
    DataAssetDescriptor,
    DataGap,
    DataQuery,
    DataResult,
    FactorProjection,
    ResourceProjection,
)
from dartlab.data.projections import projectOutput


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


def _receipt(descriptor: DataAssetDescriptor, query: DataQuery, selector: Mapping[str, str]) -> str:
    payload = {
        "assetVersionId": descriptor.assetVersionId,
        "query": query,
        "selector": dict(selector),
    }
    return f"data-execution:{hashlib.sha256(_canonical(payload)).hexdigest()}"


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
    if query.time.validAt is not None and "validAt" not in support:
        return DataGap(
            "VALID_TIME_UNSUPPORTED",
            "owner가 validAt 절단을 지원하지 않습니다",
            descriptor.assetId,
        )
    return None


def _selectors(descriptor: DataAssetDescriptor, query: DataQuery) -> tuple[dict[str, str], ...]:
    declared = dict(descriptor.metadata)
    stockRequired = declared.get("stockRequired") is True or descriptor.owner in {"analysis", "credit", "quant"}
    targetRequired = declared.get("targetRequired") is True or bool(declared.get("listFn"))
    if stockRequired and query.subjects:
        return tuple({"subject": subject} for subject in query.subjects)
    projectionMeasures = query.projection.measures if isinstance(query.projection, FactorProjection) else ()
    measures = query.measures or projectionMeasures
    if targetRequired and measures:
        return tuple({"measure": measure} for measure in measures)
    if query.subjects and descriptor.owner in {"gather", "industry"}:
        return tuple({"subject": subject} for subject in query.subjects)
    return ({},)


def _engineCall(descriptor: DataAssetDescriptor, query: DataQuery, selector: Mapping[str, str]) -> Any:
    import dartlab

    engine = getattr(dartlab, descriptor.owner)
    kwargs = dict(query.params)
    subject = selector.get("subject")
    measure = selector.get("measure")
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
        return int(estimatedSize())
    return len(repr(value).encode("utf-8"))


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
    requested = tuple(dict.fromkeys(str(assetId) for assetId in assetIds if str(assetId)))
    if not requested:
        raise ValueError("query assets가 비었습니다")
    if len(requested) > query.budget.maxAssets:
        raise ValueError("assets가 query budget을 초과했습니다")
    catalog = buildCatalog()
    byId = {asset.assetId: asset for asset in catalog.assets}
    descriptors: list[DataAssetDescriptor] = []
    gaps: list[DataGap] = list(catalog.gaps)
    for assetId in requested:
        descriptor = byId.get(assetId)
        if descriptor is None:
            gaps.append(DataGap("ASSET_NOT_FOUND", assetId, assetId))
            continue
        if not descriptor.queryable:
            gaps.append(DataGap("ASSET_NOT_QUERYABLE", "catalog-only 또는 policy 차단 asset", assetId))
            continue
        descriptors.append(descriptor)

    partitions = []
    receipts: list[str] = []
    remainingRows = query.budget.maxRows
    remainingBytes = query.budget.maxBytes
    deadline = time.perf_counter() + query.budget.timeoutMs / 1000
    stopExecution = False
    for descriptor in descriptors:
        if stopExecution:
            break
        temporalGap = _temporalGap(descriptor, query)
        if temporalGap:
            gaps.append(temporalGap)
            continue
        for selector in _selectors(descriptor, query):
            if remainingRows <= 0 or remainingBytes <= 0:
                gaps.append(
                    DataGap("QUERY_BUDGET_EXHAUSTED", "전체 query 결과 예산이 소진됐습니다", descriptor.assetId)
                )
                stopExecution = True
                break
            if time.perf_counter() >= deadline:
                gaps.append(DataGap("QUERY_TIMEOUT", "query 실행 기한을 초과했습니다", descriptor.assetId))
                stopExecution = True
                break
            receiptRef = _receipt(descriptor, query, selector)
            try:
                raw = _execute(descriptor, query, selector)
                if time.perf_counter() >= deadline:
                    gaps.append(DataGap("QUERY_TIMEOUT", "owner 실행이 query 기한을 초과했습니다", descriptor.assetId))
                    stopExecution = True
                    break
                partitionBudget = dataclasses.replace(
                    query.budget,
                    maxRows=remainingRows,
                    maxBytes=remainingBytes,
                )
                partitionQuery = dataclasses.replace(query, budget=partitionBudget)
                partition, projectionGaps = projectOutput(
                    raw,
                    descriptor,
                    partitionQuery,
                    selector=selector,
                    receiptRef=receiptRef,
                )
                gaps.extend(projectionGaps)
                if partition is not None:
                    partitions.append(partition)
                    receipts.append(receiptRef)
                    remainingRows -= partition.rowCount
                    remainingBytes -= _outputBytes(partition.data)
            except Exception as exc:
                gaps.append(
                    DataGap(
                        "ASSET_EXECUTION_FAILED",
                        f"{type(exc).__name__}: {exc}",
                        descriptor.assetId,
                        selector.get("subject"),
                    )
                )

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
    resolvedRefs = tuple(AssetRef(item.assetId, item.assetVersionId) for item in descriptors)
    contractHash = hashlib.sha256(_canonical({"assets": resolvedRefs, "query": query})).hexdigest()
    lineageRefs = tuple(dict.fromkeys(ref for partition in partitions for ref in partition.lineageRefs))
    continuation = "row-budget" if any(partition.truncated for partition in partitions) else None
    return DataResult(
        status=status,
        partitions=tuple(partitions),
        assets=resolvedRefs,
        snapshotId=catalog.snapshotId,
        contractHash=contractHash,
        coverage=Coverage(len(requested), len(descriptors), succeeded, failures),
        gaps=tuple(gaps),
        lineageRefs=lineageRefs,
        executionReceipts=tuple(receipts),
        continuation=continuation,
    )
