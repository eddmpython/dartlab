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

from dartlab.core.pluginDiscovery import discoverOnce


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

_KNOWN_PROVIDER_MODULES: tuple[str, ...] = ("dartlab.providers.dart.ops.insiderTrades",)


def _discover() -> None:
    """알려진 InsiderRawProvider 모듈을 한 번만 lazy import . register 트리거.

    한 번만 도는 규칙은 `core.pluginDiscovery` 가 갖는다. 예전에는 이 열세 줄이
    core 안에 열한 벌 복사돼 있었다.
    """
    discoverOnce(__name__, _KNOWN_PROVIDER_MODULES)


def registerInsiderRawProvider(provider: InsiderRawProvider) -> None:
    """InsiderRawProvider 등록 — providers/dart/ops/insiderTrades 가 import 시점에 호출."""
    global _PROVIDER
    _PROVIDER = provider


def getInsiderRawProvider() -> InsiderRawProvider | None:
    """현재 등록된 InsiderRawProvider 반환. 미등록이면 None. auto-discovery 트리거."""
    _discover()
    return _PROVIDER
