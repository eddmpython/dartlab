"""종목 검색 ListingResolver Protocol — DIP (정공법 B).

core/resolve.py 가 gather/listing.py 직접 import 하지 않고 registry 로 접근.
gather/listing.py 가 ListingResolverImpl 등록.

dartKey CredentialProvider, EdgarLoader 와 동일 패턴 (FastAPI startup tasks).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from dartlab.core.pluginDiscovery import discoverOnce

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

# Auto-discovery — gather/krx/listing.py 가 register 하도록 lazy 로드.
_KNOWN_RESOLVER_MODULES: tuple[str, ...] = ("dartlab.gather.krx.listing",)


def _discover() -> None:
    """알려진 ListingResolver 모듈을 한 번만 lazy import . register 트리거.

    한 번만 도는 규칙은 `core.pluginDiscovery` 가 갖는다. 예전에는 이 열세 줄이
    core 안에 열한 벌 복사돼 있었다.
    """
    discoverOnce(__name__, _KNOWN_RESOLVER_MODULES)


def registerListingResolver(resolver: ListingResolver) -> None:
    """ListingResolver 등록 — gather/listing 가 import 시점에 호출."""
    global _RESOLVER
    _RESOLVER = resolver


def getListingResolver() -> ListingResolver | None:
    """현재 등록된 ListingResolver. 미등록이면 None. auto-discovery 트리거."""
    _discover()
    return _RESOLVER
