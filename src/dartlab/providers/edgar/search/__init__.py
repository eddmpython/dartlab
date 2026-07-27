"""EDGAR search — SEC Full-Text Search wrapper.

Implementation status
---------------------
- 구현 상태: **구현 완료 (v1, thin wrapper)**
- 대응 dart 모듈: ``providers/dart/search/`` (5 파일 / 4266 줄) — ngram + BM25
  자체 인덱스 빌드 + searchScope.
- SEC EDGAR 측 본질:
  - SEC 가 **EDGAR Full-Text Search API** 공식 제공 (``https://efts.sec.gov/
    LATEST/search-index``). dart 측처럼 자체 인덱스 빌드 불필요.
  - thin wrapper — SEC API 호출 + 응답 dataframe 정규화. dart 와 LOC 평형 X.

공개 surface
------------
- ``search(query, ...)`` — 단발 검색 (limit ≤ pageSize 결과 반환).
- ``fetchHits(query, ...)`` — fetch-prefix alias (룰 8 limit + 룰 10 iter pair).
- ``iterHits(query, ..., pageSize, maxPages)`` — streaming page generator.

NOTE: SEC efts.sec.gov fetch 본체는 gather/edgar/search 로 이관(수집 일원화) —
본 패키지는 lazy ``__getattr__`` re-export shim(providers↛gather module-level 회피).
공개명 ``dartlab.providers.edgar.search.{search,fetchHits,iterHits}`` 보존.
"""

from __future__ import annotations

from dartlab.core.pluginDiscovery import lazyAttribute

# NOTE: search/fetchHits/iterHits 는 아래 ``__getattr__`` 로 런타임 lazy 재노출
# (``_LAZY`` 문자열 importlib) — providers↛gather 단방향 유지 위해 static import 는 두지 않는다.

__all__ = ["search", "fetchHits", "iterHits"]

_LAZY = {
    "search": "dartlab.gather.edgar.search",
    "fetchHits": "dartlab.gather.edgar.search",
    "iterHits": "dartlab.gather.edgar.search",
}


def __getattr__(name: str):
    """lazy re-export — SEC FTS fetch 를 접근 시점에만 gather 에서 import."""
    return lazyAttribute(__name__, _LAZY, name)
