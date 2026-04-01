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


def buildIndex(parquetPaths: list[str] | None = None, *, includeDocs: bool = False, **kwargs) -> int:
    """Ngram 인덱스 빌드. allFilings + (선택) docs 통합."""
    from dartlab.core.search.ngramIndex import buildNgramIndex

    return buildNgramIndex(parquetPaths, includeDocs=includeDocs, **kwargs)


def rebuildIndex(**kwargs) -> int:
    """전체 인덱스 리빌드 — allFilings + docs 통합. (~220초)"""
    return buildIndex(includeDocs=True, **kwargs)


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
    result["stemIndex"] = ngramStats()

    return result


def pushIndex(**kwargs) -> str:
    """stemIndex를 HuggingFace에 업로드."""
    from dartlab.core.search.ngramIndex import pushStemIndex

    return pushStemIndex(**kwargs)


def pullIndex(**kwargs):
    """HuggingFace에서 stemIndex 다운로드."""
    from dartlab.core.search.ngramIndex import pullStemIndex

    return pullStemIndex(**kwargs)


# ── 파생 지식 API ──


def profile(stockCode: str | None = None):
    """기업별 공시 프로필 조회.

    stockCode 지정 시 해당 기업의 공시 요약 dict 반환.
    미지정 시 전체 DataFrame 반환.
    """
    from dartlab.core.search.derived import loadProfile

    return loadProfile(stockCode)


def pulse(topK: int = 10) -> pl.DataFrame:
    """최근 월의 공시 유형별 건수 + 전월 대비 변화."""
    from dartlab.core.search.derived import pulse as _pulse

    return _pulse(topK=topK)


def timeline(typeFilter: str | None = None, periodFilter: str | None = None) -> pl.DataFrame:
    """유형×월 빈도 시계열 조회."""
    from dartlab.core.search.derived import loadTimeline

    return loadTimeline(typeFilter=typeFilter, periodFilter=periodFilter)


def dna(stockCode: str) -> dict:
    """기업의 Disclosure DNA (114차원 유형 빈도 벡터)."""
    from dartlab.core.search.derived import dna as _dna

    return _dna(stockCode)


def similarCompanies(stockCode: str, topK: int = 5) -> pl.DataFrame:
    """공시 패턴이 유사한 기업 탐색 (코사인 유사도)."""
    from dartlab.core.search.derived import similarCompanies as _similar

    return _similar(stockCode, topK=topK)
