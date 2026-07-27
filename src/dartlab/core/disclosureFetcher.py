"""정기공시 disclosure 수집 추상화 — DIP (정공법 B).

gather/calendar.py 의 catalyst 추론은 disclosure history 가 필요하다. providers/dart 직접
호출은 gather → providers cycle 의 원인이라 DisclosureFetcher Protocol 을 두고
providers/dart 가 register 한다.

dartKey CredentialProvider, EdgarLoader, ListingResolver 와 동일 패턴.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from dartlab.core.pluginDiscovery import discoverOnce

if TYPE_CHECKING:
    import polars as pl


@runtime_checkable
class DisclosureFetcher(Protocol):
    """공시 history 수집 추상화 — caller (gather/Calendar) 가 사용."""

    def fetch(self, stockCode: str, *, days: int = 400, type: str = "A") -> "pl.DataFrame | None":
        """정기공시 history DataFrame 반환. 실패 시 None."""
        ...


_FETCHER: DisclosureFetcher | None = None

_KNOWN_FETCHER_MODULES: tuple[str, ...] = ("dartlab.providers.dart.company",)


def _discover() -> None:
    """알려진 DisclosureFetcher 모듈을 한 번만 lazy import . register 트리거.

    한 번만 도는 규칙은 `core.pluginDiscovery` 가 갖는다. 예전에는 이 열세 줄이
    core 안에 열한 벌 복사돼 있었다.
    """
    discoverOnce(__name__, _KNOWN_FETCHER_MODULES)


def registerDisclosureFetcher(fetcher: DisclosureFetcher) -> None:
    """DisclosureFetcher 등록 — providers 가 import 시점에 호출."""
    global _FETCHER
    _FETCHER = fetcher


def getDisclosureFetcher() -> DisclosureFetcher | None:
    """현재 등록된 DisclosureFetcher 반환. 미등록이면 None. auto-discovery 트리거."""
    _discover()
    return _FETCHER
