"""U0 metadata-only census의 wall clock과 peak memory를 측정한다."""

from __future__ import annotations

import time
import tracemalloc
from collections.abc import Callable

from .canonical import BenchmarkReport, CensusResult


def runMetadataCensusBenchmark(
    census: Callable[[], CensusResult],
    *,
    targetSeconds: float = 60.0,
) -> tuple[CensusResult, BenchmarkReport]:
    """Census 한 번의 duration과 Python peak memory를 측정한다.

    Args:
        census: 인자 없이 `CensusResult`를 반환하는 callable.
        targetSeconds: G0 metadata census 목표 초.

    Returns:
        census 결과와 benchmark report tuple.

    Raises:
        ValueError: targetSeconds가 양수가 아닌 경우.

    Example:
        ``result, report = runMetadataCensusBenchmark(runFullCensus)``.
    """
    if targetSeconds <= 0:
        raise ValueError("targetSeconds는 양수여야 함")
    tracemalloc.start()
    started = time.perf_counter()
    try:
        result = census()
        duration = time.perf_counter() - started
        _, peakMemory = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    report = BenchmarkReport(
        durationSeconds=duration,
        discoveredFileCount=result.coverage.discoveredFileCount,
        discoveredByteCount=result.coverage.discoveredByteCount,
        networkOperationCount=len(result.discovery.networkOperations),
        payloadBodiesRead=result.discovery.payloadBodiesRead,
        peakMemoryBytes=peakMemory,
        targetSeconds=targetSeconds,
        targetMet=duration <= targetSeconds,
        censusDigest=result.snapshotDigest,
    )
    return result, report
