"""루트 Compare facade.

시장별 compare 본체는 엔진 내부에 둔다.
- DART: ``dartlab.engines.dart.compare``
- EDGAR: ``dartlab.engines.edgar.compare``

이 모듈은 사용자용 통합 라우팅과 mixed-market 비교만 담당한다.
"""

from __future__ import annotations

import logging
from typing import Any

import polars as pl

from dartlab.company import Company
_log = logging.getLogger("dartlab.compare")


def _resolveCompany(arg: Any):
    if isinstance(arg, str):
        return Company(arg)
    return arg


class _MixedCompare:
    """KR/US 혼합 비교용 공통 facade."""

    def __init__(self, *args: Any):
        if len(args) < 2:
            raise ValueError("비교하려면 최소 2개 기업이 필요합니다")
        self.companies = [_resolveCompany(a) for a in args]
        self._cache: dict[str, Any] = {}

    def __repr__(self):
        names = [c.corpName for c in self.companies]
        return f"Compare({', '.join(names)})"

    def _baseRow(self, c) -> dict[str, Any]:
        return {
            "name": c.corpName,
            "market": c.market,
            "id": getattr(c, "ticker", None) or getattr(c, "stockCode", ""),
            "currency": c.currency,
        }

    @property
    def ratios(self) -> pl.DataFrame:
        cacheKey = "_ratios"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        rows = []
        for c in self.companies:
            row = self._baseRow(c)
            r = c.ratios
            if r is not None:
                for key, value in r.__dict__.items():
                    row[key] = value
            rows.append(row)
        df = pl.DataFrame(rows)
        self._cache[cacheKey] = df
        return df

    @property
    def scale(self) -> pl.DataFrame:
        cacheKey = "_scale"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        fields = [
            "revenueTTM", "operatingIncomeTTM", "netIncomeTTM", "totalAssets",
            "totalEquity", "totalLiabilities", "cash", "marketCap", "fcf", "netDebt",
        ]
        rows = []
        for c in self.companies:
            row = self._baseRow(c)
            r = c.ratios
            if r is not None:
                for field in fields:
                    row[field] = getattr(r, field, None)
            rows.append(row)
        df = pl.DataFrame(rows)
        self._cache[cacheKey] = df
        return df

    @property
    def insights(self) -> pl.DataFrame:
        cacheKey = "_insights"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        areas = ["performance", "profitability", "health", "cashflow", "governance", "risk", "opportunity"]
        rows = []
        for c in self.companies:
            row = self._baseRow(c)
            ins = c.insights
            if ins is not None:
                for area in areas:
                    result = getattr(ins, area, None)
                    row[area] = result.grade if result else None
                row["profile"] = ins.profile
            rows.append(row)
        df = pl.DataFrame(rows)
        self._cache[cacheKey] = df
        return df


def Compare(*args: Any):
    """시장 구성에 따라 적절한 compare 구현을 반환."""
    if len(args) < 2:
        raise ValueError("비교하려면 최소 2개 기업이 필요합니다")

    companies = [_resolveCompany(a) for a in args]
    markets = {c.market for c in companies}

    if markets == {"KR"}:
        from dartlab.engines.dart.compare import Compare as _DartCompare
        return _DartCompare(*companies)
    if markets == {"US"}:
        from dartlab.engines.edgar.compare import Compare as _EdgarCompare
        return _EdgarCompare(*companies)
    return _MixedCompare(*companies)
