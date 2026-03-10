"""SEC EDGAR 기반 미국 기업 분석 클래스.

Company와 동일한 핵심 인터페이스를 제공하되, EDGAR 데이터를 사용한다.

사용법::

    from dartlab import USCompany

    c = USCompany("AAPL")
    c.timeseries           # (series, periods) 분기별
    c.annual               # (series, years) 연도별
    c.ratios               # RatioResult
    c.insights             # AnalysisResult (7영역 등급)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

_log = logging.getLogger("dartlab.usCompany")


class USCompany:
    """SEC EDGAR 기반 미국 기업 진입점.

    Example::

        c = USCompany("AAPL")
        c.timeseries           # (series, periods) 분기별
        c.ratios               # RatioResult
        c.insights             # AnalysisResult
    """

    def __init__(self, ticker: str):
        self.ticker = ticker.upper()
        self._cache: dict[str, Any] = {}

        cik = self._resolveCik(self.ticker)
        if cik is None:
            raise ValueError(f"'{ticker}'에 해당하는 CIK를 찾을 수 없음")
        self.cik = cik
        self.corpName = self.ticker

        from dartlab.engines.edgar.finance.pivot import buildTimeseries
        ts = buildTimeseries(self.cik)
        if ts is None:
            raise ValueError(f"'{self.ticker}' (CIK: {self.cik}) EDGAR 재무 데이터 없음")
        self._cache["_ts"] = ts

    def _resolveCik(self, ticker: str) -> str | None:
        """ticker → CIK 변환."""
        tickerPath = self._getTickerPath()
        if tickerPath is None or not tickerPath.exists():
            return None

        import polars as pl
        df = pl.read_parquet(tickerPath)
        row = df.filter(pl.col("ticker") == ticker)
        if row.is_empty():
            row = df.filter(pl.col("ticker") == ticker.upper())
        if row.is_empty():
            return None
        return str(row["cik"][0]).zfill(10)

    def _getTickerPath(self) -> Path | None:
        """tickers.parquet 경로. data/edgar/ 루트에 위치."""
        from dartlab import config
        return Path(config.dataDir) / "edgar" / "tickers.parquet"

    def __repr__(self):
        return f"USCompany('{self.ticker}', cik='{self.cik}')"

    @property
    def timeseries(self):
        """분기별 standalone 시계열 (series, periods)."""
        return self._cache.get("_ts")

    @property
    def annual(self):
        """연도별 시계열 (series, years)."""
        if "_annual" not in self._cache:
            from dartlab.engines.edgar.finance.pivot import buildAnnual
            self._cache["_annual"] = buildAnnual(self.cik)
        return self._cache["_annual"]

    @property
    def ratios(self):
        """재무비율 (RatioResult)."""
        if "_ratios" not in self._cache:
            from dartlab.engines.common.finance.ratios import calcRatios
            annual = self.annual
            if annual is None:
                self._cache["_ratios"] = None
            else:
                aSeries, _ = annual
                self._cache["_ratios"] = calcRatios(aSeries, annual=True)
        return self._cache["_ratios"]

    @property
    def insights(self):
        """종합 인사이트 (AnalysisResult)."""
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

    @property
    def market(self) -> str:
        """시장 코드."""
        return "US"
