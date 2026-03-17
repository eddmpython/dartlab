"""OpenEdgar — SEC public API 편의 facade."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import polars as pl

from dartlab.engines.edgar.openapi.client import EdgarClient
from dartlab.engines.edgar.openapi.facts import (
    getCompanyConceptJson,
    getCompanyFactsJson,
    getFrameJson,
)
from dartlab.engines.edgar.openapi.identity import resolveIssuer, searchIssuers
from dartlab.engines.edgar.openapi.saver import saveDocs as _saveDocs
from dartlab.engines.edgar.openapi.saver import saveFinance as _saveFinance
from dartlab.engines.edgar.openapi.submissions import filingsFrame, getSubmissionsJson


class OpenEdgar:
    """SEC public API facade.

    Examples
    --------
    >>> from dartlab import OpenEdgar
    >>> e = OpenEdgar()
    >>> aapl = e("AAPL")
    >>> aapl.info()
    >>> aapl.filings(forms=["10-K", "10-Q"])
    >>> aapl.saveFinance()
    """

    def __init__(
        self,
        *,
        userAgent: str | None = None,
        email: str | None = None,
    ):
        self._client = EdgarClient(userAgent=userAgent, email=email)

    def search(self, query: str) -> pl.DataFrame:
        return searchIssuers(query, self._client)

    def company(self, tickerOrCik: str) -> dict[str, Any]:
        return resolveIssuer(tickerOrCik, self._client)

    def submissionsJson(self, tickerOrCik: str) -> dict[str, Any]:
        cik = self.company(tickerOrCik)["cik"]
        return getSubmissionsJson(cik, self._client)

    def filings(
        self,
        tickerOrCik: str,
        *,
        forms: list[str] | tuple[str, ...] | None = None,
        since: str | None = None,
        until: str | None = None,
    ) -> pl.DataFrame:
        info = self.company(tickerOrCik)
        submissions = getSubmissionsJson(info["cik"], self._client)
        return filingsFrame(
            submissions,
            ticker=info["ticker"],
            title=info["title"],
            forms=forms,
            since=since,
            until=until,
            client=self._client,
        )

    def companyFactsJson(self, tickerOrCik: str) -> dict[str, Any]:
        cik = self.company(tickerOrCik)["cik"]
        return getCompanyFactsJson(cik, self._client)

    def companyConceptJson(
        self,
        tickerOrCik: str,
        taxonomy: str,
        tag: str,
    ) -> dict[str, Any]:
        cik = self.company(tickerOrCik)["cik"]
        return getCompanyConceptJson(cik, taxonomy, tag, self._client)

    def frameJson(
        self,
        taxonomy: str,
        tag: str,
        unit: str,
        period: str,
    ) -> dict[str, Any]:
        return getFrameJson(taxonomy, tag, unit, period, self._client)

    def __call__(self, tickerOrCik: str) -> OpenEdgarCompany:
        return OpenEdgarCompany(self, tickerOrCik)

    def __repr__(self) -> str:
        return f"OpenEdgar(userAgent={self._client.userAgent!r})"


class OpenEdgarCompany:
    """회사 단위 EDGAR convenience proxy."""

    def __init__(self, edgar: OpenEdgar, tickerOrCik: str):
        self._edgar = edgar
        self._identity = edgar.company(tickerOrCik)

    @property
    def ticker(self) -> str:
        return str(self._identity["ticker"])

    @property
    def cik(self) -> str:
        return str(self._identity["cik"])

    def info(self) -> dict[str, Any]:
        return dict(self._identity)

    def submissionsJson(self) -> dict[str, Any]:
        return getSubmissionsJson(self.cik, self._edgar._client)

    def filings(
        self,
        *,
        forms: list[str] | tuple[str, ...] | None = None,
        since: str | None = None,
        until: str | None = None,
    ) -> pl.DataFrame:
        submissions = self.submissionsJson()
        return filingsFrame(
            submissions,
            ticker=self.ticker,
            title=str(self._identity.get("title") or self.ticker),
            forms=forms,
            since=since,
            until=until,
            client=self._edgar._client,
        )

    def companyFactsJson(self) -> dict[str, Any]:
        return getCompanyFactsJson(self.cik, self._edgar._client)

    def companyConceptJson(self, taxonomy: str, tag: str) -> dict[str, Any]:
        return getCompanyConceptJson(self.cik, taxonomy, tag, self._edgar._client)

    def saveDocs(self, *, sinceYear: int = 2009) -> Path:
        return _saveDocs(self.ticker, sinceYear=sinceYear)

    def saveFinance(self) -> Path:
        return _saveFinance(self.cik, client=self._edgar._client)

    def __repr__(self) -> str:
        return f"OpenEdgarCompany('{self.ticker}')"

