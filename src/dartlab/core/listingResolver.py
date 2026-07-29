"""종목 검색 ListingResolver Protocol — DIP (정공법 B).

core/resolve.py 가 gather/listing.py 직접 import 하지 않고 registry 로 접근.
gather/listing.py 가 ListingResolverImpl 등록.

dartKey CredentialProvider, EdgarLoader 와 동일 패턴 (FastAPI startup tasks).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from dartlab.core.pluginDiscovery import bootstrap

if TYPE_CHECKING:
    import polars as pl


@runtime_checkable
class ListingResolver(Protocol):
    """종목 (회사명 ↔ stockCode) 검색 추상화.

    구현 위치: gather/listing.py 의 GatherListingResolver.
    """

    def search(self, query: str) -> "pl.DataFrame | None":
        """회사명 substring/prefix 검색."""
        ...

    def fuzzy(self, query: str, *, maxResults: int = 5) -> "pl.DataFrame | None":
        """초성/Levenshtein fuzzy 검색."""
        ...

    def codeToName(self, stockCode: str) -> "str | None":
        """stockCode → 회사명 변환."""
        ...

    def nameToCode(self, corpName: str) -> "str | None":
        """회사명 → stockCode 변환."""
        ...

    def kindList(self, *, forceRefresh: bool = False) -> "pl.DataFrame":
        """KIND 상장법인 목록 DataFrame 반환."""
        ...


_RESOLVER: ListingResolver | None = None


def _discover() -> None:
    """root composition이 등록한 ListingResolver bootstrap을 실행한다."""
    bootstrap(__name__)


def registerListingResolver(resolver: ListingResolver) -> None:
    """ListingResolver 등록 — gather/listing 가 import 시점에 호출."""
    global _RESOLVER
    _RESOLVER = resolver


def getListingResolver() -> ListingResolver | None:
    """현재 등록된 ListingResolver. 미등록이면 None. auto-discovery 트리거."""
    _discover()
    return _RESOLVER
