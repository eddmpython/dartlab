"""EDGAR finance namespace — XBRL 정규화 재무 데이터."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import polars as pl

if TYPE_CHECKING:
    from dartlab.engines.edgar.company import Company


class _FinanceAccessor:
    """EDGAR finance namespace. XBRL 정규화 재무 데이터."""

    def __init__(self, company: Company):
        self._company = company

    @property
    def timeseries(self):
        return self._company._cache.get("_ts")

    @property
    def annual(self):
        if "_annual" not in self._company._cache:
            from dartlab.engines.edgar.finance.pivot import buildAnnual

            self._company._cache["_annual"] = buildAnnual(self._company.cik)
        return self._company._cache["_annual"]

    def _stmtDf(self, stmtKey: str) -> pl.DataFrame | None:
        cacheKey = f"_finance_{stmtKey}"
        if cacheKey in self._company._cache:
            return self._company._cache[cacheKey]

        annual = self.annual
        if annual is None:
            self._company._cache[cacheKey] = None
            return None

        series, years = annual
        stmtData = series.get(stmtKey)
        if not stmtData:
            self._company._cache[cacheKey] = None
            return None

        rows = []
        for snakeId, values in stmtData.items():
            row: dict[str, Any] = {"account": snakeId}
            for i, year in enumerate(years):
                row[str(year)] = values[i] if i < len(values) else None
            rows.append(row)

        if not rows:
            self._company._cache[cacheKey] = None
            return None

        result = pl.DataFrame(rows)
        # 기간 컬럼 역순 정렬
        periodCols = [c for c in result.columns if c != "account"]
        result = result.select(["account"] + periodCols[::-1])
        self._company._cache[cacheKey] = result
        return result

    @property
    def BS(self) -> pl.DataFrame | None:
        return self._stmtDf("BS")

    @property
    def IS(self) -> pl.DataFrame | None:
        return self._stmtDf("IS")

    @property
    def CF(self) -> pl.DataFrame | None:
        return self._stmtDf("CF")

    @property
    def CIS(self) -> pl.DataFrame | None:
        return self._stmtDf("CI")

    @property
    def ratios(self):
        if "_ratios" not in self._company._cache:
            from dartlab.engines.common.finance.ratios import calcRatios

            annual = self.annual
            if annual is None:
                self._company._cache["_ratios"] = None
            else:
                aSeries, _ = annual
                self._company._cache["_ratios"] = calcRatios(aSeries, annual=True)
        return self._company._cache["_ratios"]

    @property
    def ratioSeries(self):
        cacheKey = "_ratioSeries"
        if cacheKey in self._company._cache:
            return self._company._cache[cacheKey]
        annual = self.annual
        if annual is None:
            return None
        aSeries, years = annual
        from dartlab.engines.common.finance.ratios import calcRatioSeries, toSeriesDict

        rs = calcRatioSeries(aSeries, years)
        result = toSeriesDict(rs)
        self._company._cache[cacheKey] = result
        return result

    @property
    def SCE(self) -> pl.DataFrame | None:
        cacheKey = "_finance_SCE"
        if cacheKey in self._company._cache:
            return self._company._cache[cacheKey]
        from dartlab.engines.edgar.finance.pivot import buildSce

        result = buildSce(self._company.cik)
        self._company._cache[cacheKey] = result
        return result

    def explore(self, query: str) -> pl.DataFrame | None:
        """XBRL 태그 검색 — 전 기간 값 탐색."""
        from dartlab.engines.edgar.finance.explore import explore

        return explore(self._company.cik, query)

    def listTags(self) -> pl.DataFrame | None:
        """보고된 모든 us-gaap 태그 목록."""
        from dartlab.engines.edgar.finance.explore import listTags

        return listTags(self._company.cik)
