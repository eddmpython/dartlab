"""공시 원문 검색 엔진. *(alpha)*

Ngram+Synonym 기본 검색 (모델 불필요, cold start 0ms, precision 95%).
벡터 검색은 optional 보강.

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
    topK: int = 10,
) -> pl.DataFrame:
    """공시 원문 검색 — Ngram+Synonym 기본, 벡터 보강.

    모델 불필요. cold start 0ms.
    """
    corpCode, stockCode = _resolveCorp(corp)

    # Ngram 검색 (기본 — 모델 불필요)
    from dartlab.core.search.ngramIndex import searchNgram

    result = searchNgram(query, corpCode=corpCode, stockCode=stockCode, topK=topK)

    # 날짜 필터
    if result.height > 0:
        if start and "rcept_dt" in result.columns:
            result = result.filter(pl.col("rcept_dt") >= start)
        if end and "rcept_dt" in result.columns:
            result = result.filter(pl.col("rcept_dt") <= end)

    return result


def _resolveCorp(corp: str | None) -> tuple[str | None, str | None]:
    """corp 파라미터 → (corpCode, stockCode) 변환."""
    if not corp:
        return None, None
    if len(corp) == 6 and corp.isdigit():
        return None, corp
    if len(corp) == 8 and corp.isdigit():
        return corp, None
    try:
        from dartlab.gather.listing import searchListing

        match = searchListing(corp)
        if match is not None and match.height > 0:
            return None, match["stock_code"][0]
    except Exception:
        pass
    return None, None


# ── 인덱스 빌드 ──


def buildIndex(parquetPaths: list[str] | None = None, **kwargs) -> int:
    """Ngram 인덱스 빌드. parquet 경로 없으면 전체 수집 데이터 대상.

    벡터 인덱스도 같이 빌드 (vector 의존성 있을 때만).
    """
    from dartlab.core.search.ngramIndex import buildNgramIndex

    # Ngram 인덱스 (항상)
    count = buildNgramIndex(parquetPaths)

    # 벡터 인덱스 (optional)
    try:
        from dartlab.core.search.vectorStore import buildFromParquet

        if parquetPaths:
            for p in parquetPaths:
                buildFromParquet(p, **kwargs)
        else:
            from dartlab.providers.dart.openapi.allFilingsCollector import _META_SUFFIX, _allFilingsDir

            outDir = _allFilingsDir()
            files = sorted(f for f in outDir.glob("*.parquet") if _META_SUFFIX not in f.stem)
            for f in files:
                buildFromParquet(str(f), **kwargs)
    except ImportError:
        pass  # vector 의존성 없으면 건너뜀

    return count


# ── 수집 편의 함수 ──


def collectMeta(startDate: str, endDate: str, **kwargs) -> int:
    """공시 목록 수집 (Phase 1)."""
    from dartlab.providers.dart.openapi.allFilingsCollector import collectMetaRange

    return collectMetaRange(startDate, endDate, **kwargs)


def fillContent(date: str | None = None, **kwargs):
    """공시 원문 채우기 (Phase 2)."""
    from dartlab.providers.dart.openapi.allFilingsCollector import (
        fillContent as _fill,
    )
    from dartlab.providers.dart.openapi.allFilingsCollector import (
        fillContentAll as _fillAll,
    )

    if date:
        return _fill(date, **kwargs)
    return _fillAll(**kwargs)


def stats() -> dict:
    """수집 + 인덱스 통합 통계."""
    from dartlab.core.search.ngramIndex import ngramStats
    from dartlab.providers.dart.openapi.allFilingsCollector import stats as collectorStats

    result = collectorStats()
    result["ngram"] = ngramStats()

    try:
        from dartlab.core.search.vectorStore import indexStats

        result["vector"] = indexStats()
    except ImportError:
        pass

    return result


def pushIndex(**kwargs) -> str:
    """인덱스를 HuggingFace에 업로드."""
    from dartlab.core.search.vectorStore import pushToHub

    return pushToHub(**kwargs)


def pullIndex(**kwargs):
    """HuggingFace에서 인덱스 다운로드."""
    from dartlab.core.search.vectorStore import pullFromHub

    return pullFromHub(**kwargs)
