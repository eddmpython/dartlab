"""정기공시 disclosure 수집 추상화 — DIP (정공법 B).

gather/calendar.py 의 catalyst 추론은 disclosure history 가 필요하다. providers/dart 직접
호출은 gather → providers cycle 의 원인이라 DisclosureFetcher Protocol 을 두고
providers/dart 가 register 한다.

dartKey CredentialProvider, EdgarLoader, ListingResolver 와 동일 패턴.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from dartlab.core.pluginDiscovery import bootstrap

if TYPE_CHECKING:
    import polars as pl


@runtime_checkable
class DisclosureFetcher(Protocol):
    """공시 history 수집 추상화 — caller (gather/Calendar) 가 사용."""

    def fetch(self, stockCode: str, *, days: int = 400, type: str = "A") -> "pl.DataFrame | None":
        """정기공시 history DataFrame 반환. 실패 시 None."""
        ...


_FETCHER: DisclosureFetcher | None = None


def _discover() -> None:
    """root composition이 등록한 DisclosureFetcher bootstrap을 실행한다."""
    bootstrap(__name__)


def registerDisclosureFetcher(fetcher: DisclosureFetcher) -> None:
    """DisclosureFetcher 등록 — providers 가 import 시점에 호출."""
    global _FETCHER
    _FETCHER = fetcher


def getDisclosureFetcher() -> DisclosureFetcher | None:
    """현재 등록된 DisclosureFetcher 반환. 미등록이면 None. auto-discovery 트리거."""
    _discover()
    return _FETCHER
