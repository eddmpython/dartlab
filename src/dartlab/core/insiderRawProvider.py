"""DART 내부자 거래 raw fetch 추상화 — DIP (정공법 B).

providers/dart/ops/insiderTrades.py 의 ``fetchInsiderTradingRaw`` /
``fetchMajorShareholdersRaw`` (KR DART OpenAPI elestock/majorstock) 를 gather/sources/
insider.py 가 lazy import → L1 cross (gather → providers) 의 한 축.

InsiderRawProvider Protocol 을 core 에 두고 providers/dart/ops/insiderTrades 가 register.
gather 는 core import 만 — providers 직접 의존 0. providers → core (downward) 단방향만 유지.

GatherProvider/CredentialProvider/LoaderProvider/ListingResolver/DisclosureFetcher/
FinanceDocAccessor/HtmlRenderer 와 동일 패턴.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from dartlab.core.pluginDiscovery import bootstrap


@runtime_checkable
class InsiderRawProvider(Protocol):
    """KR DART 내부자 거래 raw fetch 추상화 — gather/sources/insider 가 사용."""

    async def fetchInsiderTradingRaw(self, stockCode: str, *, limit: int | None = None) -> list[dict[str, Any]]:
        """임원/주요주주 주식 거래 내역 raw dict — DART elestock.json."""
        ...

    async def fetchMajorShareholdersRaw(self, stockCode: str, *, limit: int | None = None) -> list[dict[str, Any]]:
        """5% 이상 대량보유 변동 raw dict — DART majorstock.json."""
        ...


_PROVIDER: InsiderRawProvider | None = None


def _discover() -> None:
    """root composition이 등록한 InsiderRawProvider bootstrap을 실행한다."""
    bootstrap(__name__)


def registerInsiderRawProvider(provider: InsiderRawProvider) -> None:
    """InsiderRawProvider 등록 — providers/dart/ops/insiderTrades 가 import 시점에 호출."""
    global _PROVIDER
    _PROVIDER = provider


def getInsiderRawProvider() -> InsiderRawProvider | None:
    """현재 등록된 InsiderRawProvider 반환. 미등록이면 None. auto-discovery 트리거."""
    _discover()
    return _PROVIDER
