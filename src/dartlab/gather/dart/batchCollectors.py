"""dart/openapi batch 단일 종목 비동기 수집기 — batch.py 분할 (규칙 3 LoC).

_collectFinance / _collectReport + ProcessPool 헬퍼.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import httpx
import polars as pl

from dartlab.core.dartClient import DartApiError

# batch ↔ batchCollectors 양방향 import 회피 — AsyncDartClient 는 type annotation
# (`from __future__ import annotations` 효과로 string lazy), 10 상수/helper 는 함수 본문
# 안만 사용 → 각 함수 시작 lazy import.
if TYPE_CHECKING:
    from dartlab.gather.dart.batch import AsyncDartClient

# ── 단일 종목 수집 (비동기) ──


async def _collectFinance(
    stockCode: str,
    corpCode: str,
    corpName: str,
    client: AsyncDartClient,
    *,
    incremental: bool = True,
    onPeriod=None,
    targetPeriods: list[tuple[str, str]] | None = None,
) -> int:
    """finance 수집 (CFS+OFS). 반환: 저장된 행 수.

    Args:
        targetPeriods: list.json에서 발견한 정확한 (bsns_year, reprt_code) 리스트.
            지정하면 88분기 차집합 우회. 누락 검사도 이 리스트로만 한정.
            None이면 기존 _buildAllPeriods 88분기 전체 + 차집합 (heavy fallback).
    """
    from dartlab.core.dartBuild import enrichFinance, save, saveReplacingByKeys
    from dartlab.gather.dart.batch import (
        _CODE_TO_QUARTER,
        _buildAllPeriods,
        _dataPath,
        _existingFinancePeriods,
    )

    path = _dataPath("finance", stockCode)

    if targetPeriods is not None:
        # list.json 기반 경로: 발견된 (year, code)는 기존 period가 있어도 다시 수집한다.
        # 정정 공시는 rcept_no가 새롭지만 period는 동일하므로 period 존재 여부로 skip하면 안 된다.
        periods = list(targetPeriods)
    else:
        # 기존 fallback: 88분기 전체 차집합 (heavy)
        allPeriods = _buildAllPeriods()
        if incremental:
            existing = _existingFinancePeriods(path)
            periods = [(y, c) for y, c in allPeriods if (y, c) not in existing]
        else:
            periods = allPeriods

    if not periods:
        return 0

    frames: list[pl.DataFrame] = []
    totalPeriods = len(periods)
    for pIdx, (bsnsYear, reprtCode) in enumerate(periods):
        if client.exhausted:
            raise DartApiError("020", "요청 제한 초과로 finance 수집이 완료되지 않았습니다")
        quarter = _CODE_TO_QUARTER.get(reprtCode, "Q4")
        if onPeriod:
            onPeriod(f"finance {pIdx + 1}/{totalPeriods} {bsnsYear}{quarter}")
        # CFS (연결) + OFS (별도) 양쪽 수집
        for fsDiv in ("CFS", "OFS"):
            if client.exhausted:
                raise DartApiError("020", "요청 제한 초과로 finance 수집이 완료되지 않았습니다")
            df = await client.getDf(
                "fnlttSinglAcntAll.json",
                {
                    "corp_code": corpCode,
                    "bsns_year": bsnsYear,
                    "reprt_code": reprtCode,
                    "fs_div": fsDiv,
                },
            )
            if df is None:
                raise RuntimeError(f"finance 응답 상태가 없습니다: {stockCode} {bsnsYear}/{reprtCode}/{fsDiv}")
            if df.height > 0:
                # API 응답에 fs_div가 없으므로 요청한 값을 직접 부여
                if "fs_div" not in df.columns:
                    df = df.with_columns(pl.lit(fsDiv).alias("fs_div"))
                frames.append(df)

    if client.exhausted:
        raise DartApiError("020", "요청 제한 초과로 finance 수집이 완료되지 않았습니다")
    if not frames:
        return 0

    combined = pl.concat(frames, how="diagonal_relaxed")
    enriched = enrichFinance(combined, stockCode, corpName)
    if targetPeriods is not None:
        keyColumns = ["bsns_year", "reprt_code"]
        if "fs_div" in enriched.columns:
            keyColumns.append("fs_div")
        saveReplacingByKeys(enriched, path, keyColumns)
    else:
        save(enriched, path)
    return enriched.height


async def _collectReport(
    stockCode: str,
    corpCode: str,
    corpName: str,
    client: AsyncDartClient,
    *,
    incremental: bool = True,
    onPeriod=None,
    targetPeriods: list[tuple[str, str]] | None = None,
) -> int:
    """report 수집. 반환: 저장된 행 수.

    Args:
        targetPeriods: list.json에서 발견한 정확한 (bsns_year, reprt_code).
            지정하면 88분기 차집합 우회.
    """
    from dartlab.core.dartBuild import enrichReport, save, saveReplacingByKeys
    from dartlab.gather.dart.batch import (
        _CODE_TO_QUARTER_KR,
        _KR_TO_ENG_API_TYPE,
        _PERIODIC_REPORT_CATEGORIES,
        _REPORT_ENDPOINTS,
        _buildAllPeriods,
        _dataPath,
        _existingReportPeriods,
    )

    path = _dataPath("report", stockCode)
    allPeriods = list(targetPeriods) if targetPeriods is not None else _buildAllPeriods()

    if incremental and targetPeriods is None:
        existing = _existingReportPeriods(path)
    else:
        existing = set()

    frames: list[pl.DataFrame] = []
    totalCats = len(_PERIODIC_REPORT_CATEGORIES)
    for catIdx, cat in enumerate(_PERIODIC_REPORT_CATEGORIES):
        endpoint = _REPORT_ENDPOINTS.get(cat)
        if not endpoint:
            continue
        if onPeriod:
            onPeriod(f"report {catIdx + 1}/{totalCats} {cat}")
        for bsnsYear, reprtCode in allPeriods:
            if client.exhausted:
                raise DartApiError("020", "요청 제한 초과로 report 수집이 완료되지 않았습니다")
            quarterKr = _CODE_TO_QUARTER_KR.get(reprtCode, "4분기")
            engApiType = _KR_TO_ENG_API_TYPE.get(cat, cat)
            # 증분: parquet 실제 포맷(year, "N분기", engApiType)으로 비교
            if incremental and (bsnsYear, quarterKr, engApiType) in existing:
                continue

            df = await client.getDf(
                f"{endpoint}.json",
                {"corp_code": corpCode, "bsns_year": bsnsYear, "reprt_code": reprtCode},
            )
            if df is None:
                raise RuntimeError(f"report 응답 상태가 없습니다: {stockCode} {bsnsYear}/{reprtCode}/{cat}")
            if df.height > 0:
                enriched = enrichReport(df, stockCode, corpCode, cat, endpoint)
                frames.append(enriched)
        if client.exhausted:
            raise DartApiError("020", "요청 제한 초과로 report 수집이 완료되지 않았습니다")

    if client.exhausted:
        raise DartApiError("020", "요청 제한 초과로 report 수집이 완료되지 않았습니다")
    if not frames:
        return 0

    combined = pl.concat(frames, how="diagonal_relaxed")
    if targetPeriods is not None:
        saveReplacingByKeys(combined, path, ["year", "quarter", "apiType"])
    else:
        save(combined, path)
    return combined.height


_processPool = None


def _getProcessPool():
    """XML 파싱용 프로세스 풀 (모듈 레벨 싱글톤)."""
    global _processPool
    if _processPool is None:
        import concurrent.futures
        import os

        _processPool = concurrent.futures.ProcessPoolExecutor(
            max_workers=min(4, (os.cpu_count() or 4)),
        )
    return _processPool
