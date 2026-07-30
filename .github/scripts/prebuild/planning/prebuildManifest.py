"""Prebuild manifest helpers.

The CI script keeps IO orchestration in ``prebuildData.py``. This module holds
small deterministic helpers for artifact paths and local category counts.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

SCAN_BASE_ARTIFACTS: tuple[str, ...] = (
    "changes.parquet",
    "finance.parquet",
    "finance-lite.parquet",
    "sharesOutstanding.parquet",
    "network/affiliateDocs.parquet",
    "salesByProduct.parquet",
    "narrativeMetrics.parquet",
    "valuation.parquet",
    "docsIndex.parquet",
    "corpProfile.parquet",
    "_scanBuildState.json",
)


def categoryFileCount(dataDir: str, category: str, dataReleases: Mapping[str, Mapping[str, str]]) -> int:
    """Return local file count for a released data category."""
    catDir = Path(dataDir) / dataReleases[category]["dir"]
    return sum(1 for p in catDir.rglob("*") if p.is_file()) if catDir.exists() else 0


def scanArtifactRelPaths(scanDir: str, reportApiTypes: Sequence[str], noteConcepts: Sequence[str] = ()) -> list[str]:
    """Return fixed scan artifact paths without opening HF tree listing.

    note/{concept}.parquet 도 base-seed 대상에 포함해 incremental 사이클이 주석 횡단면을 HF 에서
    직접 seed 하게 한다 (note 축이 조용히 DARK 로 회귀하는 것을 방지). 404 는 seed 단계가 관대 처리.
    """
    rels = [f"{scanDir}/{name}" for name in SCAN_BASE_ARTIFACTS]
    rels.extend(f"{scanDir}/report/{apiType}.parquet" for apiType in reportApiTypes)
    rels.extend(f"{scanDir}/note/{concept}.parquet" for concept in noteConcepts)
    return rels
