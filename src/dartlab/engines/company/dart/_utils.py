"""DART 엔진 범용 유틸리티.

company.py에서 분리된 모듈-레벨 헬퍼.
"""

from __future__ import annotations

import re
import time
from typing import Any

import polars as pl

_PERIOD_COLUMN_RE = re.compile(r"^\d{4}(Q[1-4])?$")

_DART_FRESHNESS_TTL_DAYS = 90


def _isPeriodColumn(name: str) -> bool:
    return bool(_PERIOD_COLUMN_RE.fullmatch(name))


def _shapeString(df: pl.DataFrame | None) -> str:
    if df is None:
        return "-"
    return f"{df.height}x{df.width}"


def _import_and_call(modulePath: str, funcName: str, stockCode: str, **kwargs) -> Any:
    """모듈을 lazy import하고 함수 호출."""
    import importlib

    mod = importlib.import_module(modulePath)
    func = getattr(mod, funcName)
    return func(stockCode, **kwargs)


def _ensureData(stockCode: str, category: str) -> bool:
    """로컬에 parquet이 있으면 True, 없으면 다운로드 시도 후 결과 반환."""
    from dartlab.core.dataConfig import DATA_RELEASES
    from dartlab.core.dataLoader import _dataDir, _download
    from dartlab.core.guidance import emit

    dest = _dataDir(category) / f"{stockCode}.parquet"
    if dest.exists():
        return True
    label = DATA_RELEASES[category]["label"]
    emit("download:start", stockCode=stockCode, label=label)
    try:
        _download(stockCode, dest, category)
        size = dest.stat().st_size
        sizeStr = f"{size / 1024:.0f}KB" if size < 1024 * 1024 else f"{size / 1024 / 1024:.1f}MB"
        emit("download:done", label=label, sizeStr=sizeStr)
        return True
    except (OSError, RuntimeError):
        if category == "docs":
            emit("hint:missing_docs", stockCode=stockCode, label=label)
        elif category in ("finance", "report"):
            emit("hint:missing_other", stockCode=stockCode, label=label)
        return False


def _checkDartDocsFreshness(stockCode: str, category: str = "docs") -> None:
    """DART docs parquet의 최신성을 확인하고, stale이면 갱신 안내."""
    from dartlab.core.dataLoader import _dataDir
    from dartlab.core.guidance import emit

    path = _dataDir(category) / f"{stockCode}.parquet"
    if not path.exists():
        return

    ageDays = (time.time() - path.stat().st_mtime) / 86400
    if ageDays < _DART_FRESHNESS_TTL_DAYS:
        return

    emit("hint:stale", stockCode=stockCode, ageStr=f"{ageDays:.0f}일")
