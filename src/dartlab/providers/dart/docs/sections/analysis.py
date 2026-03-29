"""sections DataFrame 파생 분석 — freq 투영, semantic/structure registry."""

from __future__ import annotations

import re

import polars as pl

from dartlab.providers.dart.docs.sections._common import periodOrderValue, sortPeriods
from dartlab.providers.dart.docs.sections.pipeline import _joinPathSegments, _splitPathSegments


def projectFreqRows(
    df: pl.DataFrame,
    *,
    freqScope: str,
    includeMixed: bool = True,
) -> pl.DataFrame:
    """sections DataFrame를 freq 기준으로 투영한다."""
    if df.is_empty() or "freqScope" not in df.columns:
        return df

    scope = str(freqScope).strip().lower()
    if scope == "all":
        return df
    if scope not in {"annual", "quarterly", "mixed"}:
        raise ValueError(f"unsupported freqScope: {freqScope}")

    allowed = {scope}
    if includeMixed and scope in {"annual", "quarterly"}:
        allowed.add("mixed")

    return df.filter(pl.col("freqScope").is_in(sorted(allowed)))


def _emptySemanticRegistryFrame() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "topic": pl.Utf8,
            "textNodeType": pl.Utf8,
            "textLevel": pl.Int64,
            "freqScope": pl.Utf8,
            "textSemanticPathKey": pl.Utf8,
            "textSemanticParentPathKey": pl.Utf8,
            "rowCount": pl.Int64,
            "rawPathCount": pl.Int64,
            "rawPaths": pl.List(pl.Utf8),
            "rawParentPaths": pl.List(pl.Utf8),
            "semanticPathCount": pl.Int64,
            "semanticPaths": pl.List(pl.Utf8),
            "sourceBlockOrders": pl.List(pl.Int64),
            "segmentKeys": pl.List(pl.Utf8),
            "latestAnnualPeriod": pl.Utf8,
            "latestQuarterlyPeriod": pl.Utf8,
            "hasCollision": pl.Boolean,
        }
    )


def _emptyStructureRegistryFrame() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "topic": pl.Utf8,
            "textNodeType": pl.Utf8,
            "textLevel": pl.Int64,
            "freqScope": pl.Utf8,
            "textComparablePathKey": pl.Utf8,
            "textComparableParentPathKey": pl.Utf8,
            "rowCount": pl.Int64,
            "rawSemanticPathCount": pl.Int64,
            "rawSemanticPaths": pl.List(pl.Utf8),
            "rawSemanticParentPaths": pl.List(pl.Utf8),
            "rawSemanticLeafCount": pl.Int64,
            "rawSemanticLeafs": pl.List(pl.Utf8),
            "sourceBlockOrders": pl.List(pl.Int64),
            "segmentKeys": pl.List(pl.Utf8),
            "latestAnnualPeriod": pl.Utf8,
            "latestQuarterlyPeriod": pl.Utf8,
            "activePeriodCount": pl.Int64,
            "activePeriods": pl.List(pl.Utf8),
            "activePathCounts": pl.List(pl.Int64),
            "minActivePathCount": pl.Int64,
            "maxActivePathCount": pl.Int64,
            "earliestPathCount": pl.Int64,
            "latestPathCount": pl.Int64,
            "multiPathPeriods": pl.List(pl.Utf8),
            "structurePattern": pl.Utf8,
            "hasCollision": pl.Boolean,
        }
    )


def _emptyStructureEventsFrame() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "topic": pl.Utf8,
            "textNodeType": pl.Utf8,
            "textLevel": pl.Int64,
            "freqScope": pl.Utf8,
            "textComparablePathKey": pl.Utf8,
            "textComparableParentPathKey": pl.Utf8,
            "periodLane": pl.Utf8,
            "fromPeriod": pl.Utf8,
            "toPeriod": pl.Utf8,
            "fromPathCount": pl.Int64,
            "toPathCount": pl.Int64,
            "fromPaths": pl.List(pl.Utf8),
            "toPaths": pl.List(pl.Utf8),
            "addedPaths": pl.List(pl.Utf8),
            "removedPaths": pl.List(pl.Utf8),
            "eventType": pl.Utf8,
        }
    )


def _emptyStructureSummaryFrame() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "topic": pl.Utf8,
            "textNodeType": pl.Utf8,
            "textLevel": pl.Int64,
            "freqScope": pl.Utf8,
            "textComparablePathKey": pl.Utf8,
            "textComparableParentPathKey": pl.Utf8,
            "structurePattern": pl.Utf8,
            "hasCollision": pl.Boolean,
            "activePeriodCount": pl.Int64,
            "activePeriods": pl.List(pl.Utf8),
            "latestPeriod": pl.Utf8,
            "latestPeriodLane": pl.Utf8,
            "latestPathCount": pl.Int64,
            "multiPathPeriods": pl.List(pl.Utf8),
            "eventCount": pl.Int64,
            "latestEventType": pl.Utf8,
            "latestEventFromPeriod": pl.Utf8,
            "latestEventToPeriod": pl.Utf8,
            "latestEventLane": pl.Utf8,
        }
    )


def _emptyStructureChangesFrame() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "topic": pl.Utf8,
            "textNodeType": pl.Utf8,
            "textLevel": pl.Int64,
            "freqScope": pl.Utf8,
            "textComparablePathKey": pl.Utf8,
            "textComparableParentPathKey": pl.Utf8,
            "structurePattern": pl.Utf8,
            "hasCollision": pl.Boolean,
            "activePeriodCount": pl.Int64,
            "activePeriods": pl.List(pl.Utf8),
            "latestPeriod": pl.Utf8,
            "latestPeriodLane": pl.Utf8,
            "latestPathCount": pl.Int64,
            "multiPathPeriods": pl.List(pl.Utf8),
            "eventCount": pl.Int64,
            "latestEventType": pl.Utf8,
            "latestEventFromPeriod": pl.Utf8,
            "latestEventToPeriod": pl.Utf8,
            "latestEventLane": pl.Utf8,
            "anchorPeriod": pl.Utf8,
            "anchorPeriodLane": pl.Utf8,
            "isLatest": pl.Boolean,
            "isStale": pl.Boolean,
        }
    )


def _structureGroupColumns() -> list[str]:
    return [
        "topic",
        "textNodeType",
        "textLevel",
        "freqScope",
        "textComparablePathKey",
        "textComparableParentPathKey",
    ]


def _normalizeStructureGroupDtypes(frame: pl.DataFrame) -> pl.DataFrame:
    casts: list[pl.Expr] = []
    stringCols = ["topic", "textNodeType", "freqScope", "textComparablePathKey", "textComparableParentPathKey"]
    for colName in stringCols:
        if colName in frame.columns:
            casts.append(pl.col(colName).cast(pl.Utf8).alias(colName))
    if "textLevel" in frame.columns:
        casts.append(pl.col("textLevel").cast(pl.Int64).alias("textLevel"))
    return frame.with_columns(casts) if casts else frame


def _periodLane(period: str | None) -> str | None:
    if not isinstance(period, str) or not period:
        return None
    if period.endswith("Q1"):
        return "q1"
    if period.endswith("Q2"):
        return "q2"
    if period.endswith("Q3"):
        return "q3"
    return "annual"


def _allowedStructurePeriodLanes(freqScope: str | None) -> set[str] | None:
    scope = str(freqScope).strip().lower() if isinstance(freqScope, str) else "all"
    if scope == "annual":
        return {"annual"}
    if scope == "quarterly":
        return {"q1", "q2", "q3"}
    return None


def _structurePatternRank(pattern: str | None) -> int:
    order = {
        "parallel": 7,
        "split_merge": 6,
        "split": 5,
        "merge": 4,
        "reassigned": 3,
        "moved": 2,
        "variant": 1,
        "same": 0,
    }
    return order.get(str(pattern), 0)


def _pathCollection(paths: object) -> list[str]:
    if isinstance(paths, pl.Series):
        values = paths.to_list()
    elif isinstance(paths, list):
        values = paths
    else:
        return []
    return [str(path) for path in values if isinstance(path, str) and path]


def _intCollection(values: object) -> list[int]:
    if isinstance(values, pl.Series):
        rawValues = values.to_list()
    elif isinstance(values, list):
        rawValues = values
    else:
        return []

    result: list[int] = []
    for value in rawValues:
        if isinstance(value, bool):
            continue
        if isinstance(value, int):
            result.append(value)
            continue
        if isinstance(value, float) and value.is_integer():
            result.append(int(value))
    return result


def _path_leafs(paths: object) -> list[str]:
    values = _pathCollection(paths)
    leafs = sorted({segments[-1] for path in values if (segments := _splitPathSegments(path))})
    return leafs


def _isBusinessUnitComparablePath(path: str | None) -> bool:
    return isinstance(path, str) and any(segment == "사업부문현황" for segment in _splitPathSegments(path))


def _periodsWithMultiplePaths(payload: object) -> list[str]:
    if not isinstance(payload, dict):
        return []
    periods = payload.get("activePeriods")
    counts = payload.get("activePathCounts")
    if not isinstance(periods, list) or not isinstance(counts, list):
        return []

    result: list[str] = []
    for period, count in zip(periods, counts, strict=False):
        if isinstance(period, str) and isinstance(count, (int, float)) and int(count) > 1:
            result.append(period)
    return result


def _changedPaths(fromPaths: list[str], toPaths: list[str]) -> tuple[list[str], list[str]]:
    added = [path for path in toPaths if path not in fromPaths]
    removed = [path for path in fromPaths if path not in toPaths]
    return added, removed


def _structureTransitionType(comparablePathKey: str | None, fromPaths: list[str], toPaths: list[str]) -> str:
    if fromPaths == toPaths:
        return "stable"

    fromCount = len(fromPaths)
    toCount = len(toPaths)
    fromLeafs = _path_leafs(fromPaths)
    toLeafs = _path_leafs(toPaths)
    fromParents = {_joinPathSegments(_splitPathSegments(path)[:-1]) for path in fromPaths if _splitPathSegments(path)}
    toParents = {_joinPathSegments(_splitPathSegments(path)[:-1]) for path in toPaths if _splitPathSegments(path)}
    fromParents.discard(None)
    toParents.discard(None)

    if fromCount == 1 and toCount == 1:
        if set(fromLeafs) == set(toLeafs) and fromParents != toParents:
            return "moved"
        if _isBusinessUnitComparablePath(comparablePathKey) and set(fromLeafs) != set(toLeafs):
            return "reassigned"
        return "variant"
    if fromCount == 1 and toCount > 1:
        return "split"
    if fromCount > 1 and toCount == 1:
        return "merge"
    return "parallel_change"


def _structurePattern(payload: object) -> str:
    if isinstance(payload, dict):
        values = _pathCollection(payload.get("rawSemanticPaths"))
        comparablePathKey = payload.get("textComparablePathKey")
        activeCounts = _intCollection(payload.get("activePathCounts"))
    else:
        values = _pathCollection(payload)
        comparablePathKey = None
        activeCounts = []

    if len(values) <= 1:
        return "same"

    parents = {_joinPathSegments(_splitPathSegments(path)[:-1]) for path in values if _splitPathSegments(path)}
    parents.discard(None)
    leafs = _path_leafs(values)

    if activeCounts and max(activeCounts) <= 1:
        if len(leafs) == 1 and len(parents) > 1:
            return "moved"
        if _isBusinessUnitComparablePath(str(comparablePathKey)) and len(leafs) > 1:
            return "reassigned"
        return "variant"

    if len(leafs) == 1 and len(parents) > 1:
        if activeCounts and max(activeCounts) > 1:
            return "parallel"
        return "moved"

    if activeCounts:
        earliestCount = activeCounts[0]
        latestCount = activeCounts[-1]
        minCount = min(activeCounts)
        maxCount = max(activeCounts)
        if earliestCount <= 1 and latestCount > 1:
            return "split"
        if earliestCount > 1 and latestCount <= 1:
            return "merge"
        if minCount <= 1 and maxCount > 1:
            return "split_merge"
        return "parallel"

    return "variant"


def _structurePeriodActivity(textScoped: pl.DataFrame, *, freqScope: str = "all") -> pl.DataFrame | None:
    groupCols = _structureGroupColumns()
    periodCols = sortPeriods([str(col) for col in textScoped.columns if re.fullmatch(r"^\d{4}(Q[1-4])?$", str(col))])
    allowedLanes = _allowedStructurePeriodLanes(freqScope)
    if allowedLanes is not None:
        periodCols = [period for period in periodCols if _periodLane(period) in allowedLanes]
    if not periodCols:
        return None

    periodActivity = (
        textScoped.select(groupCols + ["textSemanticPathKey"] + periodCols)
        .unpivot(
            index=groupCols + ["textSemanticPathKey"],
            on=periodCols,
            variable_name="period",
            value_name="payload",
        )
        .filter(pl.col("payload").is_not_null() & (pl.col("payload").cast(pl.Utf8).str.len_chars() > 0))
        .with_columns(pl.col("period").map_elements(periodOrderValue, return_dtype=pl.Int64).alias("periodOrder"))
        .group_by(groupCols + ["period", "periodOrder"], maintain_order=True)
        .agg(pl.col("textSemanticPathKey").drop_nulls().unique().sort().alias("activeRawSemanticPaths"))
        .with_columns(pl.col("activeRawSemanticPaths").list.len().alias("activePathCount"))
        .sort(groupCols + ["periodOrder"])
    )
    return None if periodActivity.is_empty() else periodActivity


def semanticRegistry(
    df: pl.DataFrame | None,
    *,
    topic: str | None = None,
    freqScope: str = "all",
    includeMixed: bool = True,
) -> pl.DataFrame:
    """textSemanticPathKey 기준 semantic registry를 만든다."""
    if df is None or df.is_empty():
        return _emptySemanticRegistryFrame()

    required = {"topic", "textSemanticPathKey", "textPathKey", "segmentKey"}
    if not required.issubset(set(df.columns)):
        return _emptySemanticRegistryFrame()

    scoped = df
    if freqScope != "all":
        scoped = projectFreqRows(scoped, freqScope=freqScope, includeMixed=includeMixed)
    if topic is not None:
        scoped = scoped.filter(pl.col("topic") == topic)
    if scoped.is_empty():
        return _emptySemanticRegistryFrame()

    textScoped = scoped
    if "blockType" in textScoped.columns:
        textScoped = textScoped.filter(pl.col("blockType") == "text")
    if "textStructural" in textScoped.columns:
        textScoped = textScoped.filter(pl.col("textStructural") != False)  # noqa: E712
    textScoped = textScoped.filter(pl.col("textSemanticPathKey").is_not_null() & pl.col("textPathKey").is_not_null())
    if textScoped.is_empty():
        return _emptySemanticRegistryFrame()

    rawPathExpr = (
        pl.col("textPathVariants").list.explode().drop_nulls().unique().sort()
        if "textPathVariants" in textScoped.columns
        else pl.col("textPathKey").drop_nulls().unique().sort()
    )
    rawParentExpr = (
        pl.col("textParentPathVariants").list.explode().drop_nulls().unique().sort()
        if "textParentPathVariants" in textScoped.columns
        else pl.col("textParentPathKey").drop_nulls().unique().sort()
    )
    semanticPathExpr = (
        pl.col("textSemanticPathVariants").list.explode().drop_nulls().unique().sort()
        if "textSemanticPathVariants" in textScoped.columns
        else pl.col("textSemanticPathKey").drop_nulls().unique().sort()
    )

    registry = (
        textScoped.group_by(
            [
                "topic",
                "textNodeType",
                "textLevel",
                "freqScope",
                "textSemanticPathKey",
                "textSemanticParentPathKey",
            ],
            maintain_order=True,
        )
        .agg(
            [
                pl.len().alias("rowCount"),
                rawPathExpr.alias("rawPaths"),
                rawParentExpr.alias("rawParentPaths"),
                semanticPathExpr.alias("semanticPaths"),
                pl.col("sourceBlockOrder").drop_nulls().unique().sort().alias("sourceBlockOrders"),
                pl.col("segmentKey").drop_nulls().unique().sort().alias("segmentKeys"),
                pl.col("latestAnnualPeriod").drop_nulls().max().alias("latestAnnualPeriod"),
                pl.col("latestQuarterlyPeriod").drop_nulls().max().alias("latestQuarterlyPeriod"),
            ]
        )
        .with_columns(
            [
                pl.col("rawPaths").list.len().alias("rawPathCount"),
                pl.col("semanticPaths").list.len().alias("semanticPathCount"),
            ]
        )
        .with_columns((pl.col("rawPathCount") > 1).alias("hasCollision"))
        .sort(["topic", "textSemanticPathKey", "textNodeType", "textLevel", "freqScope"])
    )
    return registry


def structureRegistry(
    df: pl.DataFrame | None,
    *,
    topic: str | None = None,
    freqScope: str = "all",
    includeMixed: bool = True,
    nodeType: str | None = None,
) -> pl.DataFrame:
    """Comparable slot spine 기준 structure registry를 만든다."""
    if df is None or df.is_empty():
        return _emptyStructureRegistryFrame()

    required = {"topic", "textComparablePathKey", "textSemanticPathKey", "segmentKey"}
    if not required.issubset(set(df.columns)):
        return _emptyStructureRegistryFrame()

    scoped = df
    if freqScope != "all":
        scoped = projectFreqRows(scoped, freqScope=freqScope, includeMixed=includeMixed)
    if topic is not None:
        scoped = scoped.filter(pl.col("topic") == topic)
    if scoped.is_empty():
        return _emptyStructureRegistryFrame()

    textScoped = scoped
    if "blockType" in textScoped.columns:
        textScoped = textScoped.filter(pl.col("blockType") == "text")
    if "textStructural" in textScoped.columns:
        textScoped = textScoped.filter(pl.col("textStructural") != False)  # noqa: E712
    normalizedNodeType = str(nodeType).strip().lower() if isinstance(nodeType, str) and nodeType.strip() else None
    if normalizedNodeType is not None and "textNodeType" in textScoped.columns:
        textScoped = textScoped.filter(pl.col("textNodeType") == normalizedNodeType)
    textScoped = textScoped.filter(
        pl.col("textComparablePathKey").is_not_null() & pl.col("textSemanticPathKey").is_not_null()
    )
    if textScoped.is_empty():
        return _emptyStructureRegistryFrame()

    groupCols = _structureGroupColumns()
    periodActivity = _structurePeriodActivity(textScoped, freqScope=freqScope)
    periodActivitySummary: pl.DataFrame | None = None
    if periodActivity is not None:
        periodActivitySummary = periodActivity.group_by(groupCols, maintain_order=True).agg(
            [
                pl.len().alias("activePeriodCount"),
                pl.col("period").alias("activePeriods"),
                pl.col("activePathCount").alias("activePathCounts"),
                pl.col("activePathCount").min().alias("minActivePathCount"),
                pl.col("activePathCount").max().alias("maxActivePathCount"),
                pl.col("activePathCount").first().alias("earliestPathCount"),
                pl.col("activePathCount").last().alias("latestPathCount"),
            ]
        )

    registry = textScoped.group_by(groupCols, maintain_order=True).agg(
        [
            pl.len().alias("rowCount"),
            pl.col("textSemanticPathKey").drop_nulls().unique().sort().alias("rawSemanticPaths"),
            pl.col("textSemanticParentPathKey").drop_nulls().unique().sort().alias("rawSemanticParentPaths"),
            pl.col("sourceBlockOrder").drop_nulls().unique().sort().alias("sourceBlockOrders"),
            pl.col("segmentKey").drop_nulls().unique().sort().alias("segmentKeys"),
            pl.col("latestAnnualPeriod").drop_nulls().max().alias("latestAnnualPeriod"),
            pl.col("latestQuarterlyPeriod").drop_nulls().max().alias("latestQuarterlyPeriod"),
        ]
    )
    if periodActivitySummary is not None:
        registry = registry.join(periodActivitySummary, on=groupCols, how="left", nulls_equal=True)
    else:
        registry = registry.with_columns(
            [
                pl.lit(0).cast(pl.Int64).alias("activePeriodCount"),
                pl.lit([], dtype=pl.List(pl.Utf8)).alias("activePeriods"),
                pl.lit([], dtype=pl.List(pl.Int64)).alias("activePathCounts"),
                pl.lit(0).cast(pl.Int64).alias("minActivePathCount"),
                pl.lit(0).cast(pl.Int64).alias("maxActivePathCount"),
                pl.lit(0).cast(pl.Int64).alias("earliestPathCount"),
                pl.lit(0).cast(pl.Int64).alias("latestPathCount"),
            ]
        )

    registry = (
        registry.with_columns(
            [
                pl.col("rawSemanticPaths").list.len().alias("rawSemanticPathCount"),
                pl.col("rawSemanticPaths")
                .map_elements(_path_leafs, return_dtype=pl.List(pl.Utf8))
                .alias("rawSemanticLeafs"),
            ]
        )
        .with_columns(
            [
                pl.col("rawSemanticLeafs").list.len().alias("rawSemanticLeafCount"),
                pl.struct(["activePeriods", "activePathCounts"])
                .map_elements(_periodsWithMultiplePaths, return_dtype=pl.List(pl.Utf8))
                .alias("multiPathPeriods"),
                pl.struct(["rawSemanticPaths", "textComparablePathKey", "activePathCounts"])
                .map_elements(_structurePattern, return_dtype=pl.Utf8)
                .alias("structurePattern"),
            ]
        )
        .with_columns((pl.col("rawSemanticPathCount") > 1).alias("hasCollision"))
        .sort(["topic", "textComparablePathKey", "textNodeType", "textLevel", "freqScope"])
    )
    return _normalizeStructureGroupDtypes(registry)


def structureCollisions(
    df: pl.DataFrame | None,
    *,
    topic: str | None = None,
    freqScope: str = "all",
    includeMixed: bool = True,
    nodeType: str | None = None,
) -> pl.DataFrame:
    """structureRegistry에서 경로 충돌이 발생한 항목만 필터링하여 반환한다."""
    registry = structureRegistry(
        df,
        topic=topic,
        freqScope=freqScope,
        includeMixed=includeMixed,
        nodeType=nodeType,
    )
    if registry.is_empty():
        return registry
    return registry.filter(pl.col("hasCollision"))


def structureEvents(
    df: pl.DataFrame | None,
    *,
    topic: str | None = None,
    freqScope: str = "all",
    includeMixed: bool = True,
    changedOnly: bool = True,
    nodeType: str | None = None,
) -> pl.DataFrame:
    """기간 간 텍스트 구조 변화 이벤트(추가/삭제/변경)를 감지하여 반환한다."""
    if df is None or df.is_empty():
        return _emptyStructureEventsFrame()

    required = {"topic", "textComparablePathKey", "textSemanticPathKey", "segmentKey"}
    if not required.issubset(set(df.columns)):
        return _emptyStructureEventsFrame()

    scoped = df
    if freqScope != "all":
        scoped = projectFreqRows(scoped, freqScope=freqScope, includeMixed=includeMixed)
    if topic is not None:
        scoped = scoped.filter(pl.col("topic") == topic)
    if scoped.is_empty():
        return _emptyStructureEventsFrame()

    textScoped = scoped
    if "blockType" in textScoped.columns:
        textScoped = textScoped.filter(pl.col("blockType") == "text")
    if "textStructural" in textScoped.columns:
        textScoped = textScoped.filter(pl.col("textStructural") != False)  # noqa: E712
    normalizedNodeType = str(nodeType).strip().lower() if isinstance(nodeType, str) and nodeType.strip() else None
    if normalizedNodeType is not None and "textNodeType" in textScoped.columns:
        textScoped = textScoped.filter(pl.col("textNodeType") == normalizedNodeType)
    textScoped = textScoped.filter(
        pl.col("textComparablePathKey").is_not_null() & pl.col("textSemanticPathKey").is_not_null()
    )
    if textScoped.is_empty():
        return _emptyStructureEventsFrame()

    periodActivity = _structurePeriodActivity(textScoped, freqScope=freqScope)
    if periodActivity is None:
        return _emptyStructureEventsFrame()

    groupCols = _structureGroupColumns()
    rows: list[dict[str, object]] = []
    groupFrame = periodActivity.group_by(groupCols, maintain_order=True).agg(
        [
            pl.col("period").alias("periods"),
            pl.col("activeRawSemanticPaths").alias("pathsByPeriod"),
            pl.col("activePathCount").alias("pathCounts"),
        ]
    )
    for entry in groupFrame.iter_rows(named=True):
        periods = entry.get("periods")
        pathsByPeriod = entry.get("pathsByPeriod")
        pathCounts = entry.get("pathCounts")
        if not isinstance(periods, list) or not isinstance(pathsByPeriod, list) or not isinstance(pathCounts, list):
            continue
        lanes: dict[str, list[int]] = {}
        for idx, period in enumerate(periods):
            lane = _periodLane(period)
            if lane is None:
                continue
            lanes.setdefault(lane, []).append(idx)

        for lane, indices in lanes.items():
            if len(indices) < 2:
                continue
            for pos in range(1, len(indices)):
                fromIdx = indices[pos - 1]
                toIdx = indices[pos]
                fromPeriod = periods[fromIdx]
                toPeriod = periods[toIdx]
                fromPaths = _pathCollection(pathsByPeriod[fromIdx])
                toPaths = _pathCollection(pathsByPeriod[toIdx])
                if not isinstance(fromPeriod, str) or not isinstance(toPeriod, str) or not fromPaths or not toPaths:
                    continue
                eventType = _structureTransitionType(entry.get("textComparablePathKey"), fromPaths, toPaths)
                if changedOnly and eventType == "stable":
                    continue
                addedPaths, removedPaths = _changedPaths(fromPaths, toPaths)
                rows.append(
                    {
                        "topic": entry.get("topic"),
                        "textNodeType": entry.get("textNodeType"),
                        "textLevel": entry.get("textLevel"),
                        "freqScope": entry.get("freqScope"),
                        "textComparablePathKey": entry.get("textComparablePathKey"),
                        "textComparableParentPathKey": entry.get("textComparableParentPathKey"),
                        "periodLane": lane,
                        "fromPeriod": fromPeriod,
                        "toPeriod": toPeriod,
                        "fromPathCount": int(pathCounts[fromIdx]),
                        "toPathCount": int(pathCounts[toIdx]),
                        "fromPaths": fromPaths,
                        "toPaths": toPaths,
                        "addedPaths": addedPaths,
                        "removedPaths": removedPaths,
                        "eventType": eventType,
                    }
                )

    if not rows:
        return _emptyStructureEventsFrame()
    return pl.DataFrame(rows, schema=_emptyStructureEventsFrame().schema).sort(
        ["topic", "textComparablePathKey", "fromPeriod", "toPeriod", "textNodeType", "textLevel"]
    )


def structureSummary(
    df: pl.DataFrame | None,
    *,
    topic: str | None = None,
    freqScope: str = "all",
    includeMixed: bool = True,
    nodeType: str | None = None,
) -> pl.DataFrame:
    """구조 레지스트리와 이벤트를 결합한 경로별 요약 DataFrame을 반환한다."""
    registry = structureRegistry(
        df,
        topic=topic,
        freqScope=freqScope,
        includeMixed=includeMixed,
        nodeType=nodeType,
    )
    if registry.is_empty():
        return _emptyStructureSummaryFrame()

    groupCols = _structureGroupColumns()
    summary = registry.select(
        groupCols
        + [
            "structurePattern",
            "hasCollision",
            "activePeriodCount",
            "activePeriods",
            "latestPathCount",
            "multiPathPeriods",
        ]
    ).with_columns(
        [
            pl.col("activePeriods").list.last().alias("latestPeriod"),
            pl.col("activePeriods")
            .list.last()
            .map_elements(_periodLane, return_dtype=pl.Utf8)
            .alias("latestPeriodLane"),
        ]
    )
    summary = _normalizeStructureGroupDtypes(summary)

    events = structureEvents(
        df,
        topic=topic,
        freqScope=freqScope,
        includeMixed=includeMixed,
        changedOnly=True,
        nodeType=nodeType,
    )
    if not events.is_empty():
        eventSummary = (
            events.with_columns(
                pl.col("toPeriod").map_elements(periodOrderValue, return_dtype=pl.Int64).alias("toOrder")
            )
            .sort(groupCols + ["toOrder"])
            .group_by(groupCols, maintain_order=True)
            .agg(
                [
                    pl.len().alias("eventCount"),
                    pl.col("eventType").last().alias("latestEventType"),
                    pl.col("fromPeriod").last().alias("latestEventFromPeriod"),
                    pl.col("toPeriod").last().alias("latestEventToPeriod"),
                    pl.col("periodLane").last().alias("latestEventLane"),
                ]
            )
        )
        eventSummary = _normalizeStructureGroupDtypes(eventSummary)
        summary = summary.join(eventSummary, on=groupCols, how="left", nulls_equal=True)
    else:
        summary = summary.with_columns(
            [
                pl.lit(0).cast(pl.Int64).alias("eventCount"),
                pl.lit(None, dtype=pl.Utf8).alias("latestEventType"),
                pl.lit(None, dtype=pl.Utf8).alias("latestEventFromPeriod"),
                pl.lit(None, dtype=pl.Utf8).alias("latestEventToPeriod"),
                pl.lit(None, dtype=pl.Utf8).alias("latestEventLane"),
            ]
        )

    if "eventCount" in summary.columns:
        summary = summary.with_columns(pl.col("eventCount").fill_null(0))

    for colName in ["latestEventType", "latestEventFromPeriod", "latestEventToPeriod", "latestEventLane"]:
        if colName not in summary.columns:
            summary = summary.with_columns(pl.lit(None, dtype=pl.Utf8).alias(colName))

    return summary.sort(["topic", "textComparablePathKey", "textNodeType", "textLevel", "freqScope"])


def structureChanges(
    df: pl.DataFrame | None,
    *,
    topic: str | None = None,
    freqScope: str = "all",
    includeMixed: bool = True,
    nodeType: str | None = None,
    latestOnly: bool = True,
    changedOnly: bool = True,
) -> pl.DataFrame:
    """구조 변경이 감지된 경로를 최신 기간 기준으로 필터링하여 반환한다."""
    summary = structureSummary(
        df,
        topic=topic,
        freqScope=freqScope,
        includeMixed=includeMixed,
        nodeType=nodeType,
    )
    if summary.is_empty():
        return _emptyStructureChangesFrame()

    allowedAnchorLanes = _allowedStructurePeriodLanes(freqScope)
    latestPeriods = [
        period
        for period in summary["latestPeriod"].to_list()
        if isinstance(period, str)
        and period
        and (allowedAnchorLanes is None or _periodLane(period) in allowedAnchorLanes)
    ]
    anchorPeriod = max(latestPeriods, key=periodOrderValue) if latestPeriods else None
    anchorLane = _periodLane(anchorPeriod)

    changes = summary.with_columns(
        [
            pl.lit(anchorPeriod, dtype=pl.Utf8).alias("anchorPeriod"),
            pl.lit(anchorLane, dtype=pl.Utf8).alias("anchorPeriodLane"),
            (pl.col("latestPeriod") == anchorPeriod).alias("isLatest"),
            (pl.col("latestPeriod") != anchorPeriod).alias("isStale"),
            pl.col("structurePattern").map_elements(_structurePatternRank, return_dtype=pl.Int64).alias("_patternRank"),
        ]
    )

    if changedOnly:
        changes = changes.filter(pl.col("eventCount") > 0)
    if latestOnly:
        changes = changes.filter(pl.col("isLatest"))
    if changes.is_empty():
        return _emptyStructureChangesFrame()

    return (
        changes.sort(
            ["isLatest", "eventCount", "_patternRank", "latestPathCount", "textComparablePathKey"],
            descending=[True, True, True, True, False],
        )
        .drop("_patternRank")
        .select(_emptyStructureChangesFrame().columns)
    )


def semanticCollisions(
    df: pl.DataFrame | None,
    *,
    topic: str | None = None,
    freqScope: str = "all",
    includeMixed: bool = True,
) -> pl.DataFrame:
    """semantic registry에서 raw path 충돌 그룹만 반환한다."""
    registry = semanticRegistry(df, topic=topic, freqScope=freqScope, includeMixed=includeMixed)
    if registry.is_empty():
        return registry
    return registry.filter(pl.col("hasCollision"))
