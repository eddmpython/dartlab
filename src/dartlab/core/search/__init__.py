"""공시 원문 시맨틱 검색 엔진. *(alpha)*

``dartlab.search()`` 로 공시 원문을 자연어로 검색한다.

사용법::

    import dartlab

    dartlab.search("유상증자 결정")                    # 공시 검색
    dartlab.search("대표이사 변경", corp="005930")      # 종목 필터
    dartlab.search("전환사채", start="20240101")        # 기간 필터
"""

from __future__ import annotations

import polars as pl


def search(
    query: str,
    *,
    corp: str | None = None,
    start: str | None = None,
    end: str | None = None,
    type: str | None = None,
    topK: int = 10,
) -> pl.DataFrame | None:
    """공시 원문 시맨틱 검색."""
    from dartlab.core.search.vectorStore import search as vectorSearch

    # corp이 종목코드가 아닌 회사명이면 → 종목코드로 변환
    corpCode = None
    stockCode = None
    if corp:
        if len(corp) == 6 and corp.isdigit():
            stockCode = corp
        elif len(corp) == 8 and corp.isdigit():
            corpCode = corp
        else:
            # 회사명 → 종목코드 변환
            try:
                from dartlab.gather.listing import searchListing
                match = searchListing(corp)
                if match is not None and match.height > 0:
                    stockCode = match["stock_code"][0]
            except Exception:
                pass

    result = vectorSearch(
        query,
        corpCode=corpCode,
        stockCode=stockCode,
        topK=topK,
    )

    if result is None or result.height == 0:
        return None

    # start/end/type 필터
    if start and "rcept_dt" in result.columns:
        result = result.filter(pl.col("rcept_dt") >= start)
    if end and "rcept_dt" in result.columns:
        result = result.filter(pl.col("rcept_dt") <= end)
    if type and "report_nm" in result.columns:
        from dartlab.providers.dart.openapi.disclosure import FILING_TYPES
        typeName = FILING_TYPES.get(type, "")
        if typeName:
            result = result.filter(pl.col("report_nm").str.contains(typeName))

    return result.with_columns(
        pl.lit("filing").alias("resultType"),
    )


# ── 수집 편의 함수 (core/search에서 collector 위임) ──


def collectMeta(startDate: str, endDate: str, **kwargs) -> int:
    """공시 목록 수집 (Phase 1). providers/dart/openapi에 위임."""
    from dartlab.providers.dart.openapi.allFilingsCollector import collectMetaRange
    return collectMetaRange(startDate, endDate, **kwargs)


def fillContent(date: str | None = None, **kwargs):
    """공시 원문 채우기 (Phase 2). providers/dart/openapi에 위임."""
    from dartlab.providers.dart.openapi.allFilingsCollector import (
        fillContent as _fill,
        fillContentAll as _fillAll,
    )
    if date:
        return _fill(date, **kwargs)
    return _fillAll(**kwargs)


def buildIndex(parquetPath: str | None = None, **kwargs) -> int:
    """벡터 인덱스 빌드. parquet 경로 없으면 전체 수집 데이터 대상."""
    from dartlab.core.search.vectorStore import buildFromParquet

    if parquetPath:
        return buildFromParquet(parquetPath, **kwargs)

    # 전체 수집 데이터
    from dartlab.providers.dart.openapi.allFilingsCollector import _allFilingsDir, _META_SUFFIX
    outDir = _allFilingsDir()
    files = sorted(f for f in outDir.glob("*.parquet") if _META_SUFFIX not in f.stem)
    if not files:
        return 0

    total = 0
    for f in files:
        count = buildFromParquet(str(f), **kwargs)
        total += count
    return total


def stats() -> dict:
    """수집 + 인덱스 통합 통계."""
    from dartlab.providers.dart.openapi.allFilingsCollector import stats as collectorStats
    from dartlab.core.search.vectorStore import indexStats

    result = collectorStats()
    result["vector"] = indexStats()
    return result


def pushIndex(**kwargs) -> str:
    """벡터 인덱스를 HuggingFace에 업로드 (로컬 GPU 빌드 후)."""
    from dartlab.core.search.vectorStore import pushToHub
    return pushToHub(**kwargs)


def pullIndex(**kwargs):
    """HuggingFace에서 사전 빌드된 벡터 인덱스 다운로드."""
    from dartlab.core.search.vectorStore import pullFromHub
    return pullFromHub(**kwargs)
