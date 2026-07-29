"""4축 수집 facade 추상화 — DIP (정공법 B).

providers/{dart,edgar}/company.py 의 Company.news() / Company.gather() 메서드가
gather/entry.py + gather/__init__.py 의 GatherEntry / getDefaultGather 를 lazy import →
양방향 cycle (gather → providers · providers → gather) 의 한 축.

GatherProvider Protocol 을 core 에 두고 gather 가 register. providers 는 core import 만 —
gather 직접 의존 0. gather → providers (raw data 위임) 단방향만 유지.

CredentialProvider/LoaderProvider/ListingResolver/DisclosureFetcher/FinanceDocAccessor/
HtmlRenderer 와 동일 패턴.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from dartlab.core.pluginDiscovery import bootstrap


@runtime_checkable
class GatherProvider(Protocol):
    """4축 수집 facade 추상화 — providers 의 Company.news/gather 가 사용."""

    def news(self, query: str, *, market: str = "KR", days: int = 30) -> Any | None:
        """뉴스 수집 — gather.news 위임. 미설치 시 None."""
        ...

    def entry(self, axis: str | None = None, stockCode: str | None = None, **kwargs: Any) -> Any:
        """4축 entry 위임 — axis None 이면 axis 목록, 있으면 axis 호출."""
        ...


_PROVIDER: GatherProvider | None = None


def _discover() -> None:
    """root composition이 등록한 GatherProvider bootstrap을 실행한다."""
    bootstrap(__name__)


def registerGatherProvider(provider: GatherProvider) -> None:
    """GatherProvider 등록 — gather/entry 가 import 시점에 호출."""
    global _PROVIDER
    _PROVIDER = provider


def getGatherProvider() -> GatherProvider | None:
    """현재 등록된 GatherProvider 반환. 미등록이면 None. auto-discovery 트리거."""
    _discover()
    return _PROVIDER
