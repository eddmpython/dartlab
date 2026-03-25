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


def _collectViaApi(stockCode: str, category: str, label: str) -> bool:
    """DART API로 직접 수집. 단일 종목은 직접 호출, 배치는 batchCollect."""
    from dartlab.core.guidance import emit
    from dartlab.engines.company.dart.openapi.dartKey import resolveDartKeys

    keys = resolveDartKeys()
    if not keys:
        return False

    mode = "병렬" if len(keys) >= 2 else "순차"
    emit("collect:start", stockCode=stockCode, label=label, keyCount=len(keys), mode=mode)

    # 단일 종목 → 직접 호출 (batchCollect 오버헤드 불필요)
    try:
        if category == "docs":
            from dartlab.engines.company.dart.openapi.zipCollector import ZipDocsCollector

            collector = ZipDocsCollector(stockCode)
            return collector.collect() > 0
        elif category == "finance":
            from dartlab.engines.company.dart.openapi.dart import Dart

            d = Dart()
            d(stockCode).saveFinance(2016)
            return True
        elif category == "report":
            from dartlab.engines.company.dart.openapi.dart import Dart

            d = Dart()
            d(stockCode).saveReport(2016)
            return True
    except (ValueError, KeyError, RuntimeError, OSError):
        return False
    return False


def _ensureData(stockCode: str, category: str) -> bool:
    """3단계 폴백: 로컬 → HuggingFace 다운로드 → DART API 자동 수집."""
    from dartlab.core.dataConfig import DATA_RELEASES
    from dartlab.core.dataLoader import _dataDir, _download
    from dartlab.core.guidance import emit

    dest = _dataDir(category) / f"{stockCode}.parquet"

    # 1단계: 로컬에 이미 있음
    if dest.exists():
        return True

    label = DATA_RELEASES[category]["label"]

    # 2단계: HuggingFace 다운로드 (GH Release fallback 포함)
    emit("download:start", stockCode=stockCode, label=label)
    try:
        _download(stockCode, dest, category)
        size = dest.stat().st_size
        sizeStr = f"{size / 1024:.0f}KB" if size < 1024 * 1024 else f"{size / 1024 / 1024:.1f}MB"
        emit("download:done", label=label, sizeStr=sizeStr)
        return True
    except (OSError, RuntimeError):
        pass

    # 3단계: DART API 키 있으면 직접 수집
    from dartlab.engines.company.dart.openapi.dartKey import hasDartApiKey

    hasKey = hasDartApiKey()
    if hasKey:
        if _collectViaApi(stockCode, category, label):
            if dest.exists():
                size = dest.stat().st_size
                sizeStr = f"{size / 1024:.0f}KB" if size < 1024 * 1024 else f"{size / 1024 / 1024:.1f}MB"
                emit("collect:done", label=label, sizeStr=sizeStr)
                return True

    # 실패: 안내 메시지 (hint:missing_docs/other 모두 API 키 유무 자동 분기)
    if category == "docs":
        emit("hint:missing_docs", stockCode=stockCode, label=label)
    else:
        emit("hint:missing_other", stockCode=stockCode, label=label)
    return False


def _ensureAllData(stockCode: str) -> dict[str, bool]:
    """docs/finance/report를 한번에 확인 + 수집."""
    from dartlab.core.dataLoader import _dataDir

    categories = ["docs", "finance", "report"]
    result: dict[str, bool] = {}
    missing: list[str] = []

    # 1단계: 로컬 존재 확인
    for cat in categories:
        dest = _dataDir(cat) / f"{stockCode}.parquet"
        if dest.exists():
            result[cat] = True
        else:
            missing.append(cat)

    if not missing:
        return result

    # 2단계: 카테고리 병렬 수집 (I/O 바운드, 최대 2 워커)
    from concurrent.futures import ThreadPoolExecutor, as_completed

    with ThreadPoolExecutor(max_workers=min(len(missing), 2)) as pool:
        futures = {pool.submit(_ensureData, stockCode, cat): cat for cat in missing}
        for future in as_completed(futures):
            cat = futures[future]
            result[cat] = future.result()
    return result


def _checkDartDocsFreshness(stockCode: str, category: str = "docs"):
    """DART docs parquet 최신성 확인 — L1 HF ETag → L2 TTL → L3 DART API.

    Returns: FreshnessResult | None (L3 체크 결과, API 키 없으면 None).
    """
    from dartlab.core.dataLoader import _checkRemoteFreshness, _dataDir, _download
    from dartlab.core.guidance import emit

    path = _dataDir(category) / f"{stockCode}.parquet"
    if not path.exists():
        return None

    # L1: HF ETag 비교
    isStale = _checkRemoteFreshness(stockCode, path, category)

    if isStale is None:
        # 네트워크 오류 → L2 TTL 폴백 (90일 기준)
        ageDays = (time.time() - path.stat().st_mtime) / 86400
        if ageDays >= _DART_FRESHNESS_TTL_DAYS:
            try:
                _download(stockCode, path, category)
                emit("download:refreshed", stockCode=stockCode)
            except (OSError, RuntimeError):
                emit("hint:stale", stockCode=stockCode, ageStr=f"{ageDays:.0f}일")
    elif isStale:
        # HF에 새 데이터 → 다운로드
        ageDays = (time.time() - path.stat().st_mtime) / 86400
        try:
            _download(stockCode, path, category)
            emit("download:refreshed", stockCode=stockCode)
        except (OSError, RuntimeError):
            emit("hint:stale", stockCode=stockCode, ageStr=f"{ageDays:.0f}일")

    # L3: DART API 직접 조회 — 새 공시가 있는지 rcept_no 비교
    from dartlab.engines.company.dart.openapi.dartKey import hasDartApiKey

    if not hasDartApiKey():
        return None

    from dartlab.engines.company.dart.openapi.freshness import checkFreshness

    result = checkFreshness(stockCode)
    if not result.isFresh:
        latestReport = result.missingFilings[0]["report_nm"] if result.missingFilings else ""
        emit("hint:newFilingsAvailable", stockCode=stockCode, count=result.missingCount, latestReport=latestReport)
    return result
