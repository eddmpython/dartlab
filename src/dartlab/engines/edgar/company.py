"""EDGAR 엔진 내부 Company 본체.

DART Company와 동일한 구조를 제공한다.

- docs: sections 수평화 (topic × period), filings, show
- finance: BS/IS/CF/CIS/timeseries/annual/ratios
- 공개 인터페이스: index / show / trace

사용법::

    from dartlab import Company

    c = Company("AAPL")
    c.corpName             # "Apple Inc."
    c.index                # 수평화 보드 DataFrame
    c.show("BS")           # 재무상태표 DataFrame
    c.show("10-K::item1Business")  # topic content (str)
    c.trace("BS")          # source provenance
    c.docs.sections        # pure docs source
    c.finance.BS           # finance.BS 바로가기
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

import polars as pl

_log = logging.getLogger("dartlab.engines.edgar.company")

_PERIOD_COLUMN_RE = re.compile(r"^\d{4}(Q[1-4])?$")

_FINANCE_TOPICS = frozenset({"BS", "IS", "CF", "CIS"})

_RATIO_FIELD_LABELS: dict[str, str] = {
    "roe": "ROE (%)",
    "roa": "ROA (%)",
    "operatingMargin": "Operating Margin (%)",
    "netMargin": "Net Margin (%)",
    "grossMargin": "Gross Margin (%)",
    "ebitdaMargin": "EBITDA Margin (%)",
    "costOfSalesRatio": "COGS Ratio (%)",
    "sgaRatio": "SG&A Ratio (%)",
    "debtRatio": "Debt Ratio (%)",
    "currentRatio": "Current Ratio (%)",
    "quickRatio": "Quick Ratio (%)",
    "equityRatio": "Equity Ratio (%)",
    "interestCoverage": "Interest Coverage (x)",
    "netDebtRatio": "Net Debt Ratio (%)",
    "noncurrentRatio": "Non-current Ratio (%)",
    "revenueGrowth": "Revenue YoY (%)",
    "operatingProfitGrowth": "Operating Profit YoY (%)",
    "netProfitGrowth": "Net Profit YoY (%)",
    "assetGrowth": "Asset YoY (%)",
    "equityGrowthRate": "Equity YoY (%)",
    "totalAssetTurnover": "Asset Turnover (x)",
    "inventoryTurnover": "Inventory Turnover (x)",
    "receivablesTurnover": "Receivables Turnover (x)",
    "payablesTurnover": "Payables Turnover (x)",
    "fcf": "FCF",
    "operatingCfMargin": "Operating CF Margin (%)",
    "operatingCfToNetIncome": "Operating CF / Net Income (%)",
    "capexRatio": "Capex Ratio (%)",
    "dividendPayoutRatio": "Dividend Payout Ratio (%)",
    "revenue": "Revenue",
    "operatingProfit": "Operating Profit",
    "netProfit": "Net Profit",
    "totalAssets": "Total Assets",
    "totalEquity": "Total Equity",
    "operatingCashflow": "Operating Cashflow",
}

_RATIO_CATEGORY_LABELS: dict[str, str] = {
    "profitability": "Profitability",
    "stability": "Stability",
    "growth": "Growth",
    "efficiency": "Efficiency",
    "cashflow": "Cashflow",
    "absolute": "Absolute",
}


def _ratioSeriesToDataFrame(
    series: dict[str, dict[str, list[Any | None]]], years: list[str],
) -> pl.DataFrame | None:
    ratioData = series.get("RATIO")
    if not ratioData:
        return None

    from dartlab.engines.common.finance.ratios import RATIO_CATEGORIES

    rows: list[dict[str, Any]] = []
    for category, fields in RATIO_CATEGORIES:
        for fieldName in fields:
            values = ratioData.get(fieldName)
            if not values or not any(v is not None for v in values):
                continue
            row: dict[str, Any] = {
                "category": _RATIO_CATEGORY_LABELS.get(category, category),
                "metric": _RATIO_FIELD_LABELS.get(fieldName, fieldName),
                "_field": fieldName,
            }
            for idx, year in enumerate(years):
                row[str(year)] = values[idx] if idx < len(values) else None
            rows.append(row)

    if not rows:
        return None
    df = pl.DataFrame(rows)
    return df.drop("_field")


class _DocsAccessor:
    """EDGAR docs namespace. sections 수평화가 유일한 기초 경로."""

    def __init__(self, company: Company):
        self._company = company

    @property
    def sections(self) -> pl.DataFrame | None:
        key = "_docs_sections"
        if key not in self._company._cache:
            from dartlab.engines.edgar.docs.sections.pipeline import sections
            self._company._cache[key] = sections(self._company.ticker)
        return self._company._cache[key]

    def filings(self) -> pl.DataFrame | None:
        key = "_docs_filings"
        if key in self._company._cache:
            return self._company._cache[key]

        from dartlab.core.dataLoader import loadData
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

        result = pl.DataFrame(rows) if rows else None
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


class Company:
    """SEC EDGAR 기반 미국 기업 진입점.

    4-namespace 구조::

        c = Company("AAPL")
        c.docs.sections        # topic × period 수평화
        c.docs.filings()       # 문서 목록
        c.docs.show(topic)     # topic content 조회
        c.finance.BS           # 연도별 재무상태표
        c.finance.IS           # 연도별 손익계산서
        c.finance.CF           # 연도별 현금흐름표
        c.finance.CIS          # 연도별 포괄손익계산서
        c.finance.ratios       # 재무비율
        c.BS                   # finance.BS 바로가기
        c.sections             # docs.sections 바로가기
        c.show(topic)          # 통합 조회
    """

    def __init__(self, ticker: str):
        self.ticker = ticker.upper()
        self._cache: dict[str, Any] = {}

        tickerRow = self._resolveTickerRow(self.ticker)
        if tickerRow is None:
            raise ValueError(f"'{ticker}'에 해당하는 CIK를 찾을 수 없음")
        self.cik = tickerRow["cik"]
        self.corpName = tickerRow.get("title") or self.ticker

        from dartlab.engines.edgar.finance.pivot import buildTimeseries
        ts = buildTimeseries(self.cik)
        if ts is not None:
            self._cache["_ts"] = ts

        self.docs = _DocsAccessor(self)
        self.finance = _FinanceAccessor(self)

    def _resolveTickerRow(self, ticker: str) -> dict | None:
        tickerPath = self._getTickerPath()
        if tickerPath is None or not tickerPath.exists():
            return None

        df = pl.read_parquet(tickerPath)
        row = df.filter(pl.col("ticker") == ticker)
        if row.is_empty():
            row = df.filter(pl.col("ticker") == ticker.upper())
        if row.is_empty():
            return None
        r = row.row(0, named=True)
        r["cik"] = str(r["cik"]).zfill(10)
        return r

    def _getTickerPath(self) -> Path | None:
        from dartlab import config
        return Path(config.dataDir) / "edgar" / "tickers.parquet"

    def __repr__(self):
        return f"Company('{self.ticker}', {self.corpName})"

    @property
    def market(self) -> str:
        return "US"

    @property
    def currency(self) -> str:
        return "USD"

    @property
    def timeseries(self):
        return self._cache.get("_ts")

    @property
    def annual(self):
        return self.finance.annual

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
    def CIS(self) -> pl.DataFrame | None:
        return self.finance.CIS

    @property
    def sections(self) -> pl.DataFrame | None:
        return self.docs.sections

    @property
    def ratios(self):
        return self.finance.ratios

    @property
    def ratioSeries(self):
        return self.finance.ratioSeries

    @property
    def insights(self):
        if "_insights" not in self._cache:
            from dartlab.engines.insight.pipeline import analyze
            ts = self.timeseries
            annual = self.annual
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

    def filings(self) -> pl.DataFrame | None:
        return self.docs.filings()

    @property
    def topics(self) -> list[str]:
        cacheKey = "_topics"
        if cacheKey in self._cache:
            return self._cache[cacheKey]

        ordered: list[str] = []
        seen: set[str] = set()

        for stmt in ("BS", "IS", "CF", "CIS"):
            if getattr(self.finance, stmt) is not None:
                ordered.append(stmt)
                seen.add(stmt)

        if self.finance.ratioSeries is not None and "ratios" not in seen:
            ordered.append("ratios")
            seen.add("ratios")

        sec = self.docs.sections
        if sec is not None:
            for topic in sec["topic"].to_list():
                if isinstance(topic, str) and topic not in seen:
                    ordered.append(topic)
                    seen.add(topic)

        self._cache[cacheKey] = ordered
        return ordered

    def show(self, topic: str, *, period: str | None = None, **_kw: Any) -> Any:
        if topic in _FINANCE_TOPICS:
            df = getattr(self.finance, topic)
            return self._applyPeriodFilter(df, period)

        if topic == "ratios":
            rs = self.finance.ratioSeries
            if rs is None:
                return None
            series, years = rs
            df = _ratioSeriesToDataFrame(series, years)
            return self._applyPeriodFilter(df, period)

        content = self.docs.show(topic, period)
        if content is not None:
            return content

        return None

    def trace(self, topic: str, period: str | None = None) -> dict[str, Any] | None:
        if topic in _FINANCE_TOPICS:
            df = getattr(self.finance, topic)
            if df is None:
                return None
            return {
                "topic": topic,
                "period": period,
                "primarySource": "finance",
                "fallbackSources": [],
                "selectedPayloadRef": f"finance:{topic}",
                "availableSources": [{"source": "finance", "rows": df.height, "priority": 300}],
                "whySelected": "finance authoritative",
            }

        if topic == "ratios":
            rs = self.finance.ratioSeries
            if rs is None:
                return None
            series, years = rs
            df = _ratioSeriesToDataFrame(series, years)
            rowCount = df.height if df is not None else None
            yearCount = len(years)
            if df is not None and rowCount >= 20 and yearCount >= 5:
                coverage = "full"
            elif df is not None and rowCount > 0:
                coverage = "partial"
            else:
                coverage = "missing"
            return {
                "topic": topic,
                "period": period,
                "primarySource": "finance",
                "fallbackSources": [],
                "selectedPayloadRef": "finance:RATIO",
                "availableSources": [{"source": "finance", "rows": 1, "priority": 300}],
                "whySelected": "finance authoritative",
                "rowCount": rowCount,
                "yearCount": yearCount,
                "coverage": coverage,
            }

        sec = self.docs.sections
        if sec is not None and topic in sec["topic"].to_list():
            return {
                "topic": topic,
                "period": period,
                "primarySource": "docs",
                "fallbackSources": [],
                "selectedPayloadRef": f"docs:{topic}",
                "availableSources": [{"source": "docs", "rows": 1, "priority": 100}],
                "whySelected": "docs authoritative",
            }

        return None

    @property
    def index(self) -> pl.DataFrame:
        cacheKey = "_index"
        if cacheKey in self._cache:
            return self._cache[cacheKey]

        rows: list[dict[str, Any]] = []
        for topic in self.topics:
            traced = self.trace(topic)
            source = traced["primarySource"] if traced else None

            if topic in _FINANCE_TOPICS:
                df = getattr(self.finance, topic)
                rows.append({
                    "topic": topic,
                    "kind": "finance",
                    "source": source,
                    "periods": self._periodsStr(df),
                    "shape": self._shapeStr(df),
                    "preview": self._previewFinance(df),
                })
            elif topic == "ratios":
                rs = self.finance.ratioSeries
                if rs is not None:
                    _, years = rs
                    df = _ratioSeriesToDataFrame(*rs)
                    rows.append({
                        "topic": topic,
                        "kind": "finance",
                        "source": source,
                        "periods": f"{years[-1]}..{years[0]}" if len(years) > 1 else (years[0] if years else "-"),
                        "shape": self._shapeStr(df),
                        "preview": f"{df.height} metrics" if df is not None else "-",
                    })
            else:
                sec = self.docs.sections
                if sec is not None:
                    topicRow = sec.filter(pl.col("topic") == topic)
                    periodCols = [c for c in sec.columns if c != "topic"]
                    if not topicRow.is_empty():
                        nonNull = sum(1 for c in periodCols if topicRow[c][0] is not None)
                        rows.append({
                            "topic": topic,
                            "kind": "docs",
                            "source": source,
                            "periods": f"{periodCols[-1]}..{periodCols[0]}" if len(periodCols) > 1 else (periodCols[0] if periodCols else "-"),
                            "shape": f"1x{nonNull}",
                            "preview": self._previewDocsCell(topicRow, periodCols),
                        })

        df = pl.DataFrame(rows) if rows else pl.DataFrame(schema={
            "topic": pl.Utf8, "kind": pl.Utf8, "source": pl.Utf8,
            "periods": pl.Utf8, "shape": pl.Utf8, "preview": pl.Utf8,
        })
        self._cache[cacheKey] = df
        return df

    def _applyPeriodFilter(self, payload: Any, period: str | None) -> Any:
        if period is None or not isinstance(payload, pl.DataFrame) or payload.is_empty():
            return payload
        if period in payload.columns:
            keepCols = [c for c in ("account", "category", "metric", "topic") if c in payload.columns]
            keepCols.append(period)
            return payload.select(keepCols)
        return payload

    @staticmethod
    def _shapeStr(df: pl.DataFrame | None) -> str:
        if df is None:
            return "-"
        return f"{df.height}x{df.width}"

    @staticmethod
    def _periodsStr(df: pl.DataFrame | None) -> str:
        if df is None:
            return "-"
        periodCols = [c for c in df.columns if _PERIOD_COLUMN_RE.fullmatch(c)]
        if not periodCols:
            return "-"
        return f"{periodCols[-1]}..{periodCols[0]}" if len(periodCols) > 1 else periodCols[0]

    @staticmethod
    def _previewFinance(df: pl.DataFrame | None) -> str:
        if df is None or df.is_empty():
            return "-"
        return f"{df.height} accounts"

    @staticmethod
    def _previewDocsCell(topicRow: pl.DataFrame, periodCols: list[str]) -> str:
        for col in periodCols:
            val = topicRow[col][0]
            if val is not None:
                text = str(val).strip().replace("\n", " ")
                return f"{col}: {text[:100]}" if len(text) > 100 else f"{col}: {text[:80]}"
        return "-"
