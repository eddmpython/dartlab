"""
실험 ID: 058-005
실험명: EDGAR Company 확장 프로토타입 — docs/finance/profile namespace

목적:
- DART Company의 4-namespace 구조를 EDGAR에 적용하는 프로토타입을 검증한다.
- docs(sections/filings/show) + finance(BS/IS/CF/ratios) + profile(merged) + 루트 property

가설:
1. 기존 EDGAR Company + sections pipeline + finance pivot으로 DART와 동일한 구조가 가능하다.
2. profile.sections는 docs.sections 기반에 finance authoritative 정보를 보강할 수 있다.

방법:
1. 프로토타입 클래스로 전체 namespace 구현
2. AAPL/MSFT/TSLA에서 동작 검증
3. DART Company와 인터페이스 대조

결과 (실험 후 작성):

결론:

실험일: 2026-03-13
"""

from __future__ import annotations

from typing import Any

import polars as pl

from dartlab import config
from dartlab.core.dataLoader import loadData
from dartlab.engines.company.edgar.docs.sections.pipeline import sections as buildSections
from dartlab.engines.company.edgar.finance.pivot import buildAnnual, buildTimeseries


class _DocsAccessor:

    def __init__(self, company: _CompanyProto):
        self._company = company

    @property
    def sections(self) -> pl.DataFrame | None:
        key = "_docs_sections"
        if key not in self._company._cache:
            self._company._cache[key] = buildSections(self._company.ticker)
        return self._company._cache[key]

    def filings(self) -> pl.DataFrame | None:
        key = "_docs_filings"
        if key in self._company._cache:
            return self._company._cache[key]

        df = loadData(self._company.ticker, category="edgarDocs")
        if df is None or df.is_empty():
            self._company._cache[key] = None
            return None

        cols = ["period_key", "form_type", "accession_no", "filed_date"]
        available = [c for c in cols if c in df.columns]
        result = (
            df.select(available)
            .unique(subset=["accession_no"])
            .sort("period_key", descending=True)
        )
        self._company._cache[key] = result
        return result

    def show(self, topic: str, period: str | None = None) -> str | None:
        sec = self.sections
        if sec is None:
            return None

        topicRow = sec.filter(pl.col("topic") == topic)
        if topicRow.is_empty():
            return None

        if period is not None:
            if period not in topicRow.columns:
                return None
            return topicRow[period][0]

        periods = [c for c in topicRow.columns if c != "topic"]
        for p in periods:
            val = topicRow[p][0]
            if val is not None:
                return val
        return None


class _FinanceAccessor:

    def __init__(self, company: _CompanyProto):
        self._company = company

    @property
    def timeseries(self):
        return self._company._cache.get("_ts")

    @property
    def annual(self):
        if "_annual" not in self._company._cache:
            self._company._cache["_annual"] = buildAnnual(self._company.cik)
        return self._company._cache["_annual"]

    def _stmtDf(self, stmtKey: str) -> pl.DataFrame | None:
        annual = self.annual
        if annual is None:
            return None
        series, years = annual
        stmtData = series.get(stmtKey)
        if not stmtData:
            return None

        rows = []
        for snakeId, values in stmtData.items():
            row: dict[str, Any] = {"account": snakeId}
            for i, year in enumerate(years):
                row[str(year)] = values[i] if i < len(values) else None
            rows.append(row)
        return pl.DataFrame(rows) if rows else None

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
        if "_ratioSeries" not in self._company._cache:
            annual = self.annual
            if annual is None:
                self._company._cache["_ratioSeries"] = None
            else:
                aSeries, years = annual
                from dartlab.engines.common.finance.ratios import calcRatioSeries, toSeriesDict
                rs = calcRatioSeries(aSeries, years)
                self._company._cache["_ratioSeries"] = toSeriesDict(rs)
        return self._company._cache["_ratioSeries"]


class _CompanyProto:

    def __init__(self, ticker: str):
        from pathlib import Path

        self.ticker = ticker.upper()
        self._cache: dict[str, Any] = {}

        tickerPath = Path(config.dataDir) / "edgar" / "tickers.parquet"
        df = pl.read_parquet(tickerPath)
        row = df.filter(pl.col("ticker") == self.ticker)
        if row.is_empty():
            raise ValueError(f"ticker not found: {ticker}")
        r = row.row(0, named=True)
        self.cik = str(r["cik"]).zfill(10)
        self.corpName = r.get("title") or self.ticker

        ts = buildTimeseries(self.cik)
        if ts is not None:
            self._cache["_ts"] = ts

        self.docs = _DocsAccessor(self)
        self.finance = _FinanceAccessor(self)

    @property
    def market(self) -> str:
        return "US"

    @property
    def currency(self) -> str:
        return "USD"

    @property
    def BS(self) -> pl.DataFrame | None:
        return self.finance.BS

    @property
    def IS(self) -> pl.DataFrame | None:
        return self.finance.IS

    @property
    def CF(self) -> pl.DataFrame | None:
        return self.finance.CF

    @property
    def sections(self) -> pl.DataFrame | None:
        return self.docs.sections

    @property
    def ratios(self):
        return self.finance.ratios

    @property
    def insights(self):
        if "_insights" not in self._cache:
            from dartlab.engines.analysis.insight.pipeline import analyze
            ts = self.finance.timeseries
            annual = self.finance.annual
            if ts is None or annual is None:
                self._cache["_insights"] = None
            else:
                self._cache["_insights"] = analyze(
                    self.cik,
                    corpName=self.corpName,
                    qSeriesPair=ts,
                    aSeriesPair=annual,
                )
        return self._cache["_insights"]

    def show(self, topic: str, period: str | None = None) -> Any:
        if topic in ("BS", "IS", "CF"):
            return getattr(self.finance, topic)
        return self.docs.show(topic, period)

    def __repr__(self):
        return f"Company('{self.ticker}', {self.corpName})"


def main() -> None:
    print("=== 058-005 EDGAR Company 확장 프로토타입 ===\n")

    for ticker in ["AAPL", "MSFT", "TSLA"]:
        print(f"--- {ticker} ---")
        c = _CompanyProto(ticker)
        print(f"  repr: {c}")
        print(f"  market: {c.market}, currency: {c.currency}")

        bs = c.BS
        if bs is not None:
            print(f"  BS: {bs.height} accounts × {len(bs.columns) - 1} years")
        else:
            print(f"  BS: None")

        isdf = c.IS
        if isdf is not None:
            print(f"  IS: {isdf.height} accounts × {len(isdf.columns) - 1} years")

        cf = c.CF
        if cf is not None:
            print(f"  CF: {cf.height} accounts × {len(cf.columns) - 1} years")

        sec = c.sections
        if sec is not None:
            print(f"  sections: {sec.height} topics × {len(sec.columns) - 1} periods")

        filings = c.docs.filings()
        if filings is not None:
            print(f"  filings: {filings.height}")

        ratios = c.ratios
        if ratios is not None:
            print(f"  ratios: {type(ratios).__name__}")

        insights = c.insights
        if insights is not None:
            print(f"  insights: {type(insights).__name__}")

        text = c.show("10-K::item1Business")
        if text:
            print(f"  show('10-K::item1Business'): {len(text)} chars")

        text2 = c.show("BS")
        if text2 is not None:
            print(f"  show('BS'): {text2.height} rows DataFrame")

        print()


if __name__ == "__main__":
    main()
