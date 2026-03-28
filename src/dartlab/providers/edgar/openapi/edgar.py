"""OpenEdgar — SEC public API 편의 facade."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import polars as pl

from dartlab.providers.edgar.openapi.client import EdgarClient
from dartlab.providers.edgar.openapi.facts import (
    getCompanyConceptJson,
    getCompanyFactsJson,
    getFrameJson,
)
from dartlab.providers.edgar.openapi.identity import resolveIssuer, searchIssuers
from dartlab.providers.edgar.openapi.saver import saveDocs as _saveDocs
from dartlab.providers.edgar.openapi.saver import saveFinance as _saveFinance
from dartlab.providers.edgar.openapi.submissions import filingsFrame, getSubmissionsJson


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
        """티커 또는 회사명으로 SEC 등록 기업을 검색."""
        return searchIssuers(query, self._client)

    def company(self, tickerOrCik: str) -> dict[str, Any]:
        """티커 또는 CIK로 기업 identity 정보를 조회."""
        return resolveIssuer(tickerOrCik, self._client)

    def submissionsJson(self, tickerOrCik: str) -> dict[str, Any]:
        """SEC submissions API 원본 JSON을 반환."""
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
        """정기보고서(10-K/10-Q/20-F) 목록을 DataFrame으로 반환."""
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
        """회사의 전체 XBRL fact 데이터를 JSON으로 반환."""
        cik = self.company(tickerOrCik)["cik"]
        return getCompanyFactsJson(cik, self._client)

    def companyConceptJson(
        self,
        tickerOrCik: str,
        taxonomy: str,
        tag: str,
    ) -> dict[str, Any]:
        """특정 taxonomy/tag 조합의 concept 데이터를 JSON으로 반환."""
        cik = self.company(tickerOrCik)["cik"]
        return getCompanyConceptJson(cik, taxonomy, tag, self._client)

    def frameJson(
        self,
        taxonomy: str,
        tag: str,
        unit: str,
        period: str,
    ) -> dict[str, Any]:
        """특정 기간의 전체 기업 XBRL frame 데이터를 JSON으로 반환."""
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
        """회사 티커 심볼."""
        return str(self._identity["ticker"])

    @property
    def cik(self) -> str:
        """SEC CIK 번호 (10자리 zero-padded)."""
        return str(self._identity["cik"])

    def info(self) -> dict[str, Any]:
        """기업 identity 정보(ticker, cik, title 등)를 dict로 반환."""
        return dict(self._identity)

    def submissionsJson(self) -> dict[str, Any]:
        """이 회사의 SEC submissions 원본 JSON을 반환."""
        return getSubmissionsJson(self.cik, self._edgar._client)

    def filings(
        self,
        *,
        forms: list[str] | tuple[str, ...] | None = None,
        since: str | None = None,
        until: str | None = None,
    ) -> pl.DataFrame:
        """이 회사의 정기보고서 목록을 DataFrame으로 반환."""
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
        """이 회사의 전체 XBRL fact 데이터를 JSON으로 반환."""
        return getCompanyFactsJson(self.cik, self._edgar._client)

    def companyConceptJson(self, taxonomy: str, tag: str) -> dict[str, Any]:
        """이 회사의 특정 taxonomy/tag concept 데이터를 JSON으로 반환."""
        return getCompanyConceptJson(self.cik, taxonomy, tag, self._edgar._client)

    def saveDocs(self, *, sinceYear: int = 2009) -> Path:
        """10-K/10-Q 문서를 수집하여 로컬 parquet로 저장."""
        return _saveDocs(self.ticker, sinceYear=sinceYear)

    def saveFinance(self) -> Path:
        """XBRL companyfacts를 수집하여 로컬 parquet로 저장."""
        return _saveFinance(self.cik, client=self._edgar._client)

    def __repr__(self) -> str:
        return f"OpenEdgarCompany('{self.ticker}')"
