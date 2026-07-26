"""Production DataHub control plane runtime."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from dartlab.dataHub.pagingRuntime import dataHubRoot

from .ledger import DataHubJobLedger


def dataHubControlRoot() -> Path:
    """DataHub private control plane root를 반환한다."""

    return dataHubRoot() / "control-plane"


@lru_cache(maxsize=4)
def _cachedJobLedger(rootText: str) -> DataHubJobLedger:
    return DataHubJobLedger(Path(rootText))


def dataHubJobLedger() -> DataHubJobLedger:
    """현재 private root의 production job ledger를 재사용한다."""

    return _cachedJobLedger(str(dataHubControlRoot()))
