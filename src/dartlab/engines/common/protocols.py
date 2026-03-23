"""DART/EDGAR Company 공통 Protocol — 구조적 타이핑."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

import polars as pl


@runtime_checkable
class CompanyProtocol(Protocol):
    """Company 공통 인터페이스.

    DART Company와 EDGAR Company 모두 이 Protocol을 만족한다.
    """

    corpName: str
    market: str
    currency: str

    @property
    def index(self) -> pl.DataFrame: ...

    @property
    def topics(self) -> pl.DataFrame: ...

    @property
    def sections(self) -> pl.DataFrame | None: ...

    @property
    def BS(self) -> pl.DataFrame | None: ...

    @property
    def IS(self) -> pl.DataFrame | None: ...

    @property
    def CF(self) -> pl.DataFrame | None: ...

    @property
    def CIS(self) -> pl.DataFrame | None: ...

    def show(
        self,
        topic: str,
        block: int | None = None,
        *,
        period: str | list[str] | None = None,
    ) -> pl.DataFrame | None: ...

    def trace(self, topic: str, period: str | None = None) -> dict[str, Any] | None: ...

    def diff(
        self,
        topic: str | None = None,
        fromPeriod: str | None = None,
        toPeriod: str | None = None,
    ) -> pl.DataFrame | None: ...

    def filings(self) -> pl.DataFrame | None: ...

    def liveFilings(
        self,
        start: str | None = None,
        end: str | None = None,
        *,
        days: int | None = None,
        limit: int = 20,
        keyword: str | None = None,
        forms: list[str] | tuple[str, ...] | None = None,
        finalOnly: bool = False,
    ) -> pl.DataFrame: ...

    def readFiling(
        self,
        filing: Any,
        *,
        maxChars: int | None = None,
    ) -> dict[str, Any]: ...

    def view(self, *, port: int = 8400) -> None: ...

    def ask(
        self,
        question: str,
        *,
        include: list[str] | None = None,
        exclude: list[str] | None = None,
        provider: str | None = None,
        model: str | None = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> str | Any: ...

    def chat(
        self,
        question: str,
        *,
        provider: str | None = None,
        model: str | None = None,
        max_turns: int = 5,
        **kwargs: Any,
    ) -> str: ...


@runtime_checkable
class DocsProtocol(Protocol):
    """docs namespace 공통 인터페이스."""

    @property
    def sections(self) -> pl.DataFrame | None: ...

    def filings(self) -> pl.DataFrame | None: ...


@runtime_checkable
class FinanceProtocol(Protocol):
    """finance namespace 공통 인터페이스."""

    @property
    def BS(self) -> pl.DataFrame | None: ...

    @property
    def IS(self) -> pl.DataFrame | None: ...

    @property
    def CF(self) -> pl.DataFrame | None: ...

    @property
    def CIS(self) -> pl.DataFrame | None: ...

    @property
    def ratios(self) -> Any: ...


@runtime_checkable
class ProfileProtocol(Protocol):
    """profile namespace 공통 인터페이스."""

    @property
    def sections(self) -> pl.DataFrame | None: ...

    def trace(self, topic: str, period: str | None = None) -> dict[str, Any] | None: ...
