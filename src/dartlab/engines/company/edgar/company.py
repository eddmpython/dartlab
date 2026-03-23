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
    c.show("item1Business")        # docs topic DataFrame
    c.trace("BS")          # source provenance
    c.docs.sections        # pure docs source (blockType 분리)
    c.finance.BS           # finance.BS 바로가기
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import polars as pl

from dartlab.engines.company.edgar._docs_accessor import _DocsAccessor
from dartlab.engines.company.edgar._finance_accessor import _FinanceAccessor
from dartlab.engines.company.edgar._profile_accessor import _ProfileAccessor

_PERIOD_COLUMN_RE = re.compile(r"^\d{4}(Q[1-4])?$")

_FINANCE_TOPICS = frozenset({"BS", "IS", "CF", "CIS"})

# ── topic 단축 alias ────────────────────────────────────────────
_TOPIC_ALIASES: dict[str, str] = {
    # 10-K 주요 항목 짧은 이름
    "business": "item1Business",
    "riskFactors": "item1ARiskFactors",
    "risk": "item1ARiskFactors",
    "cybersecurity": "item1CCybersecurity",
    "properties": "item2Properties",
    "legal": "item3LegalProceedings",
    "mdna": "item7Mdna",
    "marketRisk": "item7AMarketRiskDisclosures",
    "governance": "item10DirectorsAndCorporateGovernance",
    "compensation": "item11ExecutiveCompensation",
    "ownership": "item12SecurityOwnership",
    "relatedTx": "item13RelatedTransactions",
    "summary": "fsSummary",
}

# topic → chapter / label 매핑 (DART index와 구조 통일)
_FINANCE_LABELS: dict[str, tuple[str, str]] = {
    "BS": ("Financial Statements", "Balance Sheet"),
    "IS": ("Financial Statements", "Income Statement"),
    "CF": ("Financial Statements", "Cash Flow"),
    "CIS": ("Financial Statements", "Comprehensive Income"),
    "ratios": ("Financial Statements", "Financial Ratios"),
}

# 10-K Item → (chapter, label)
_10K_ITEM_LABELS: dict[str, tuple[str, str]] = {
    "item1Business": ("Part I", "Business"),
    "item1ARiskFactors": ("Part I", "Risk Factors"),
    "item1BUnresolvedStaffComments": ("Part I", "Unresolved Staff Comments"),
    "item1CCybersecurity": ("Part I", "Cybersecurity"),
    "item1DExecutiveOfficers": ("Part I", "Executive Officers"),
    "item2Properties": ("Part I", "Properties"),
    "item3LegalProceedings": ("Part I", "Legal Proceedings"),
    "item4MineSafetyDisclosures": ("Part I", "Mine Safety Disclosures"),
    "item4AExecutiveOfficersOfTheRegistrant": ("Part I", "Executive Officers"),
    "item5MarketForCommonEquity": ("Part II", "Market for Common Equity"),
    "item6Reserved": ("Part II", "Reserved"),
    "item7Mdna": ("Part II", "MD&A"),
    "item7AMarketRiskDisclosures": ("Part II", "Market Risk Disclosures"),
    "item8FinancialStatements": ("Part II", "Financial Statements"),
    "item9ChangesInAccountants": ("Part III", "Changes in Accountants"),
    "item9AControlsAndProcedures": ("Part III", "Controls and Procedures"),
    "item9BOtherInformation": ("Part III", "Other Information"),
    "item9CForeignJurisdictionDisclosures": ("Part III", "Foreign Jurisdiction Disclosures"),
    "item10DirectorsAndCorporateGovernance": ("Part III", "Directors & Corporate Governance"),
    "item11ExecutiveCompensation": ("Part III", "Executive Compensation"),
    "item12SecurityOwnership": ("Part III", "Security Ownership"),
    "item13RelatedTransactions": ("Part III", "Related Transactions"),
    "item14PrincipalAccountantFees": ("Part III", "Principal Accountant Fees"),
    "item15ExhibitsAndSchedules": ("Part IV", "Exhibits & Schedules"),
    "item16Form10KSummary": ("Part IV", "Form 10-K Summary"),
    "item103EnvironmentalDisclosure": ("Regulation S-K", "Environmental Disclosure"),
    "item405RegulationSKDisclosure": ("Regulation S-K", "Regulation S-K Disclosure"),
    "item406RegulationSKCodeOfEthics": ("Regulation S-K", "Code of Ethics"),
}

# 10-Q Part/Item → (chapter, label)
_10Q_ITEM_LABELS: dict[str, tuple[str, str]] = {
    "partIItem1FinancialStatements": ("Part I", "Financial Statements"),
    "partIItem2Mdna": ("Part I", "MD&A"),
    "partIItem3MarketRisk": ("Part I", "Market Risk Disclosures"),
    "partIItem4ControlsAndProcedures": ("Part I", "Controls and Procedures"),
    "partIIItem1LegalProceedings": ("Part II", "Legal Proceedings"),
    "partIIItem1ARiskFactors": ("Part II", "Risk Factors"),
    "partIIItem2UnregisteredSalesAndUseOfProceeds": ("Part II", "Unregistered Sales"),
    "partIIItem3DefaultsUponSeniorSecurities": ("Part II", "Defaults Upon Senior Securities"),
    "partIIItem4MineSafetyDisclosures": ("Part II", "Mine Safety Disclosures"),
    "partIIItem5OtherInformation": ("Part II", "Other Information"),
    "partIIItem6Exhibits": ("Part II", "Exhibits"),
}


_FORM_ORDER = {"10-K": 0, "10-Q": 1, "20-F": 2, "40-F": 3}

# 10-K item 정렬 순서 (SEC 양식 순)
_10K_ORDER: dict[str, int] = {
    "item1Business": 1,
    "item1ARiskFactors": 2,
    "item1BUnresolvedStaffComments": 3,
    "item1CCybersecurity": 4,
    "item1DExecutiveOfficers": 5,
    "item103EnvironmentalDisclosure": 6,
    "item405RegulationSKDisclosure": 7,
    "item406RegulationSKCodeOfEthics": 8,
    "item2Properties": 10,
    "item3LegalProceedings": 11,
    "item4MineSafetyDisclosures": 12,
    "item4AExecutiveOfficersOfTheRegistrant": 13,
    "item5MarketForCommonEquity": 20,
    "item6Reserved": 21,
    "item7Mdna": 22,
    "item7AMarketRiskDisclosures": 23,
    "item8FinancialStatements": 24,
    "item8ASupplementalFinancialInformation": 25,
    "item9ChangesInAccountants": 30,
    "item9AControlsAndProcedures": 31,
    "item9BOtherInformation": 32,
    "item9CForeignJurisdictionDisclosures": 33,
    "item10DirectorsAndCorporateGovernance": 40,
    "item11ExecutiveCompensation": 41,
    "item12SecurityOwnership": 42,
    "item13RelatedTransactions": 43,
    "item14PrincipalAccountantFees": 44,
    "item15ExhibitsAndSchedules": 50,
    "item16Form10KSummary": 51,
}

# 10-Q item 정렬 순서
_10Q_ORDER: dict[str, int] = {
    "partIItem1FinancialStatements": 1,
    "partIItem2Mdna": 2,
    "partIItem3MarketRisk": 3,
    "partIItem4ControlsAndProcedures": 4,
    "partIIItem1LegalProceedings": 10,
    "partIIItem1ARiskFactors": 11,
    "partIIItem2UnregisteredSalesAndUseOfProceeds": 12,
    "partIIItem2CIssuerPurchaseOfEquitySecurities": 13,
    "partIIItem3DefaultsUponSeniorSecurities": 14,
    "partIIItem4MineSafetyDisclosures": 15,
    "partIIItem5OtherInformation": 16,
    "partIIItem6Exhibits": 17,
}


def _sortDocTopics(topics: list[str]) -> list[str]:
    """docs topics를 form별 → item 순으로 정렬."""

    def sortKey(topic: str) -> tuple[int, int, str]:
        if "::" not in topic:
            return (99, 0, topic)
        formType, itemId = topic.split("::", 1)
        formOrder = _FORM_ORDER.get(formType, 9)
        if formType == "10-K":
            itemOrder = _10K_ORDER.get(itemId, 99)
        elif formType == "10-Q":
            itemOrder = _10Q_ORDER.get(itemId, 99)
        else:
            # 20-F, 40-F 등 — itemId에서 숫자 추출하여 정렬
            itemOrder = _extractItemNumber(itemId)
        return (formOrder, itemOrder, itemId)

    return sorted(topics, key=sortKey)


def _extractItemNumber(itemId: str) -> int:
    """itemId에서 item 번호를 추출. "item5AOperatingResults" → 5."""
    m = re.match(r"item(\d+)", itemId)
    if m:
        num = int(m.group(1))
        # sub-item은 부모 뒤에 (item5A → 5*100+1, item16K → 16*100+11)
        subMatch = re.match(r"item\d+([A-Z])", itemId)
        if subMatch:
            return num * 100 + (ord(subMatch.group(1)) - ord("A") + 1)
        return num * 100
    return 9999


def _topicChapterLabel(topic: str) -> tuple[str, str]:
    """topic에서 chapter와 label을 추출."""
    if topic in _FINANCE_LABELS:
        return _FINANCE_LABELS[topic]

    # "10-K::item1Business" → formType="10-K", itemId="item1Business"
    if "::" in topic:
        formType, itemId = topic.split("::", 1)
        if formType == "10-K" and itemId in _10K_ITEM_LABELS:
            return _10K_ITEM_LABELS[itemId]
        if formType == "10-Q" and itemId in _10Q_ITEM_LABELS:
            return _10Q_ITEM_LABELS[itemId]
        # 20-F, 기타 → sectionMappings.json에서 label 역추출
        label = _itemIdToLabel(itemId)
        return (formType, label)

    return ("", topic)


def _itemIdToLabel(itemId: str) -> str:
    """camelCase itemId → 읽기 쉬운 label. "item5AOperatingResults" → "Operating Results"."""
    # prefix 제거: "item5A" + 대문자시작 or "item1" + 대문자시작
    # sub-item letter: 숫자 뒤 대문자 1개 + 바로 뒤가 대문자 (item5AO → A는 sub-item)
    # 단어 시작: 숫자 뒤 대문자 + 소문자 (item1Id → I는 단어 시작)
    m = re.match(r"^(?:partI{1,2})?[Ii]tem(\d+)([A-Z]?)(.*)$", itemId)
    if not m:
        return itemId
    subLetter = m.group(2)
    rest = m.group(3)
    if subLetter and rest and rest[0].isupper():
        # item5A + OperatingResults → sub-item, rest = OperatingResults
        pass
    elif subLetter:
        # item1I + dentity → I는 단어 시작, 붙여야 함
        rest = subLetter + rest
    if not rest:
        return itemId
    # camelCase → spaces
    label = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", rest)
    label = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", label)
    return label


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
    series: dict[str, dict[str, list[Any | None]]],
    years: list[str],
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


def _isPeriodColumn(col: str) -> bool:
    return bool(_PERIOD_COLUMN_RE.fullmatch(col))


class Company:
    """SEC EDGAR 기반 미국 기업 진입점.

    4-namespace 구조::

        c = Company("AAPL")
        c.docs.sections        # topic × period 수평화 (blockType 분리)
        c.docs.filings()       # 문서 목록
        c.show(topic, block)   # blockOrder별 text/table
        c.finance.BS           # 연도별 재무상태표
        c.finance.IS           # 연도별 손익계산서
        c.finance.CF           # 연도별 현금흐름표
        c.finance.CIS          # 연도별 포괄손익계산서
        c.finance.ratioSeries  # 재무비율 시계열
        c.BS                   # finance.BS 바로가기
        c.sections             # docs.sections 바로가기
        c.show(topic)          # 통합 조회 → DataFrame | None
    """

    def __init__(self, ticker: str):
        self.ticker = ticker.upper()
        from dartlab.core.memory import BoundedCache

        self._cache: BoundedCache = BoundedCache(max_entries=30)

        tickerRow = self._resolveTickerRow(self.ticker)
        if tickerRow is None:
            raise ValueError(
                f"'{ticker}'에 해당하는 종목을 찾을 수 없습니다.\n"
                f"\n"
                f"  가능한 원인:\n"
                f"  • ticker 심볼이 올바른지 확인하세요 (예: 'AAPL', 'MSFT')\n"
                f"  • SEC EDGAR에 등록되지 않은 종목일 수 있습니다\n"
                f"  • 인터넷 연결을 확인하세요 (SEC API 조회 필요)"
            )
        self.cik = tickerRow["cik"]
        self.corpName = tickerRow.get("title") or self.ticker

        from dartlab.engines.company.edgar.finance.pivot import buildTimeseries

        ts = buildTimeseries(self.cik)
        if ts is not None:
            self._cache["_ts"] = ts

        self.docs = _DocsAccessor(self)
        self.finance = _FinanceAccessor(self)
        self.profile = _ProfileAccessor(self)

    def _resolveTickerRow(self, ticker: str) -> dict | None:
        tickerPath = self._getTickerPath()
        tickerUpper = ticker.upper()
        if tickerPath is not None and tickerPath.exists():
            df = pl.read_parquet(tickerPath)
            row = df.filter(pl.col("ticker") == ticker)
            if row.is_empty():
                row = df.filter(pl.col("ticker") == tickerUpper)
            if not row.is_empty():
                r = row.row(0, named=True)
                r["cik"] = str(r["cik"]).zfill(10)
                return r

        try:
            from dartlab.core.dataLoader import loadEdgarListedUniverse

            listed = loadEdgarListedUniverse()
            row = listed.filter(pl.col("ticker") == tickerUpper)
            if not row.is_empty():
                r = row.row(0, named=True)
                r["cik"] = str(r["cik"]).zfill(10)
                return r
        except (FileNotFoundError, OSError, RuntimeError):
            pass

        try:
            from dartlab.engines.company.edgar.openapi.identity import resolveIssuer

            return resolveIssuer(tickerUpper)
        except ValueError:
            return None

    def _getTickerPath(self) -> Path | None:
        from dartlab import config

        return Path(config.dataDir) / "edgar" / "tickers.parquet"

    def __repr__(self):
        return f"Company('{self.ticker}', {self.corpName})"

    @property
    def stockCode(self) -> str:
        """서버 API 호환용 — ticker를 stockCode로 노출."""
        return self.ticker

    @property
    def market(self) -> str:
        return "US"

    @property
    def currency(self) -> str:
        return "USD"

    def view(self, *, port: int = 8400) -> None:
        """브라우저에서 공시 뷰어를 엽니다."""
        from dartlab.engines.common.viewer import launchViewer

        launchViewer(self.ticker, port=port)

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
    def SCE(self) -> pl.DataFrame | None:
        return self.finance.SCE

    @property
    def sections(self) -> pl.DataFrame | None:
        """sections — profile.sections 위임 (docs + finance 통합 지도)."""
        return self.profile.sections

    @property
    def ratios(self) -> pl.DataFrame | None:
        """재무비율 시계열 DataFrame."""
        rs = self.finance.ratioSeries
        if rs is None:
            return None
        series, years = rs
        df = _ratioSeriesToDataFrame(series, years)
        if df is not None:
            metaCols = [c for c in df.columns if not _isPeriodColumn(c)]
            periodCols = [c for c in df.columns if _isPeriodColumn(c)]
            periodCols.sort(reverse=True)
            df = df.select(metaCols + periodCols)
        return df

    @property
    def insights(self):
        if "_insights" not in self._cache:
            from dartlab.engines.analysis.insight.pipeline import analyze

            ts = self.timeseries
            annual = self.annual
            if ts is None or annual is None:
                self._cache["_insights"] = None
            else:
                self._cache["_insights"] = analyze(
                    self.cik,
                    company=self,
                    corpName=self.corpName,
                    qSeriesPair=ts,
                    aSeriesPair=annual,
                )
        return self._cache["_insights"]

    def filings(self) -> pl.DataFrame | None:
        return self.docs.filings()

    @property
    def topics(self) -> pl.DataFrame:
        """topic별 요약 DataFrame (topic, source, blocks, periods)."""
        cacheKey = "_topicsDataFrame"
        if cacheKey in self._cache:
            return self._cache[cacheKey]

        ordered: list[str] = []
        seen: set[str] = set()

        # 1. finance 제표 먼저
        for stmt in ("BS", "IS", "CF", "CIS"):
            if getattr(self.finance, stmt) is not None:
                ordered.append(stmt)
                seen.add(stmt)

        if self.finance.ratioSeries is not None and "ratios" not in seen:
            ordered.append("ratios")
            seen.add("ratios")

        # 2. docs topics — form별 정렬 (10-K → 10-Q → 20-F → 기타)
        sec = self.docs.sections
        if sec is not None:
            topicCol = sec["topic"].unique().to_list()
            topicCol = _sortDocTopics(topicCol)
            for topic in topicCol:
                if isinstance(topic, str) and topic not in seen:
                    ordered.append(topic)
                    seen.add(topic)

        # DataFrame으로 변환
        rows: list[dict] = []
        for topic in ordered:
            if sec is not None and topic in sec["topic"].to_list():
                topicRows = sec.filter(pl.col("topic") == topic)
                sources = sorted(topicRows["source"].unique().to_list()) if "source" in topicRows.columns else ["docs"]
                blocks = topicRows["blockOrder"].n_unique() if "blockOrder" in topicRows.columns else topicRows.height
                periodCols = [c for c in topicRows.columns if _isPeriodColumn(c)]
                periods = len(periodCols)
            else:
                sources = ["finance"]
                blocks = 1
                periods = 0
            rows.append(
                {
                    "topic": topic,
                    "source": ",".join(sources),
                    "blocks": blocks,
                    "periods": periods,
                }
            )

        result = pl.DataFrame(rows) if rows else pl.DataFrame({"topic": [], "source": [], "blocks": [], "periods": []})
        self._cache[cacheKey] = result
        return result

    def show(
        self,
        topic: str,
        block: int | None = None,
        *,
        period: str | list[str] | None = None,
        **_kw: Any,
    ) -> pl.DataFrame | None:
        """topic의 데이터를 반환.

        block=None → 블록 목차 DataFrame (block, type, source, preview)
        block=N → 해당 blockOrder의 실제 데이터 DataFrame

        Args:
            topic: topic 이름 (BS, IS, 10-K::item1Business 등)
            block: blockOrder 인덱스. None이면 블록 목차.
            period: 특정 기간 필터. 리스트면 세로 뷰 (기간 × 항목).
        """
        # alias 해석 (riskFactors → item1ARiskFactors 등)
        topic = _TOPIC_ALIASES.get(topic, topic)

        # period가 리스트면 세로 뷰
        if isinstance(period, list):
            wide = self.show(topic, block)
            if wide is None or not isinstance(wide, pl.DataFrame):
                return None
            return self._transposeToVertical(wide, period)

        sec = self.sections
        if sec is None:
            return None

        topicRows = sec.filter(pl.col("topic") == topic)
        if topicRows.is_empty():
            return None

        if block is None:
            blockIndex = self._buildBlockIndex(topicRows)
            if blockIndex.height == 1:
                return self.show(topic, blockIndex["block"][0], period=period)
            return blockIndex

        # 특정 block의 실제 데이터
        source = "docs"
        if "source" in topicRows.columns:
            srcRows = (
                topicRows.filter(pl.col("blockOrder") == block) if "blockOrder" in topicRows.columns else topicRows
            )
            if not srcRows.is_empty():
                source = srcRows["source"][0]

        if source == "finance":
            if topic == "ratios":
                rs = self.finance.ratioSeries
                if rs is None:
                    return None
                series, years = rs
                return self._applyPeriodFilter(_ratioSeriesToDataFrame(series, years), period)
            df = getattr(self.finance, topic, None)
            return self._applyPeriodFilter(df, period) if df is not None else None

        # docs — blockType에 따라 text/table 반환
        periodCols = [c for c in topicRows.columns if _isPeriodColumn(c)]
        if "blockType" in topicRows.columns:
            # blockOrder로 필터 (None이면 blockType으로 대체)
            bt = "text"
            if "blockOrder" in topicRows.columns:
                boFiltered = topicRows.filter(pl.col("blockOrder") == block)
                if not boFiltered.is_empty():
                    bt = boFiltered["blockType"][0]
                else:
                    # blockOrder가 None인 경우 — 인덱스로 접근
                    btList = topicRows["blockType"].to_list()
                    bt = btList[block] if block < len(btList) else "text"

            if bt == "text":
                textRows = topicRows.filter(pl.col("blockType") == "text")
                if textRows.is_empty():
                    return None
                nonNullCols = [c for c in periodCols if textRows[c].null_count() < textRows.height]
                if not nonNullCols:
                    return None
                return self._applyPeriodFilter(textRows.select(nonNullCols), period)
            else:
                tableRows = topicRows.filter(pl.col("blockType") == "table")
                if tableRows.is_empty():
                    return None
                nonNullCols = [c for c in periodCols if tableRows[c].null_count() < tableRows.height]
                if not nonNullCols:
                    return None
                return self._applyPeriodFilter(tableRows.select(nonNullCols), period)

        return self._applyPeriodFilter(topicRows, period)

    @staticmethod
    def _transposeToVertical(wide: pl.DataFrame, periods: list[str]) -> pl.DataFrame | None:
        from dartlab.engines.common.show import transposeToVertical

        return transposeToVertical(wide, periods)

    def _buildBlockIndex(self, topicRows: pl.DataFrame) -> pl.DataFrame:
        """topic의 블록 목차 DataFrame."""
        from dartlab.engines.common.show import buildBlockIndex

        return buildBlockIndex(topicRows)

    def trace(self, topic: str, period: str | None = None) -> dict[str, Any] | None:
        topic = _TOPIC_ALIASES.get(topic, topic)
        if topic in _FINANCE_TOPICS:
            df = getattr(self.finance, topic)
            if df is None:
                return None
            chapter, label = _topicChapterLabel(topic)
            return {
                "topic": topic,
                "period": period,
                "chapter": chapter,
                "label": label,
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
            chapter, label = _topicChapterLabel(topic)
            return {
                "topic": topic,
                "period": period,
                "chapter": chapter,
                "label": label,
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
            topicRows = sec.filter(pl.col("topic") == topic)
            periodCols = [c for c in sec.columns if _isPeriodColumn(c)]
            nonNullPeriods = set()
            hasText = hasTable = False
            if "blockType" in sec.columns:
                hasText = topicRows.filter(pl.col("blockType") == "text").height > 0
                hasTable = topicRows.filter(pl.col("blockType") == "table").height > 0
            for r in topicRows.iter_rows(named=True):
                for c in periodCols:
                    if r.get(c) is not None:
                        nonNullPeriods.add(c)
            chapter, label = _topicChapterLabel(topic)
            return {
                "topic": topic,
                "period": period,
                "chapter": chapter,
                "label": label,
                "primarySource": "docs",
                "fallbackSources": [],
                "selectedPayloadRef": f"docs:{topic}",
                "availableSources": [{"source": "docs", "rows": topicRows.height, "priority": 100}],
                "whySelected": "docs authoritative",
                "periodCount": len(nonNullPeriods),
                "hasText": hasText,
                "hasTable": hasTable,
            }

        return None

    @property
    def index(self) -> pl.DataFrame:
        cacheKey = "_index"
        if cacheKey in self._cache:
            return self._cache[cacheKey]

        rows: list[dict[str, Any]] = []
        for topic in self.topics["topic"].to_list():
            traced = self.trace(topic)
            source = traced["primarySource"] if traced else None
            chapter, label = _topicChapterLabel(topic)

            if topic in _FINANCE_TOPICS:
                df = getattr(self.finance, topic)
                rows.append(
                    {
                        "chapter": chapter,
                        "topic": topic,
                        "label": label,
                        "kind": "finance",
                        "source": source,
                        "periods": self._periodsStr(df),
                        "shape": self._shapeStr(df),
                        "preview": self._previewFinance(df),
                    }
                )
            elif topic == "ratios":
                rs = self.finance.ratioSeries
                if rs is not None:
                    _, years = rs
                    df = _ratioSeriesToDataFrame(*rs)
                    rows.append(
                        {
                            "chapter": chapter,
                            "topic": topic,
                            "label": label,
                            "kind": "finance",
                            "source": source,
                            "periods": f"{years[0]}..{years[-1]}" if len(years) > 1 else (years[0] if years else "-"),
                            "shape": self._shapeStr(df),
                            "preview": f"{df.height} metrics" if df is not None else "-",
                        }
                    )
            else:
                sec = self.docs.sections
                if sec is not None:
                    topicRows = sec.filter(pl.col("topic") == topic)
                    periodCols = [c for c in sec.columns if _isPeriodColumn(c)]
                    if not topicRows.is_empty():
                        # 비어있지 않은 기간 수
                        nonNullPeriods = set()
                        for r in topicRows.iter_rows(named=True):
                            for c in periodCols:
                                if r.get(c) is not None:
                                    nonNullPeriods.add(c)
                        rows.append(
                            {
                                "chapter": chapter,
                                "topic": topic,
                                "label": label,
                                "kind": "docs",
                                "source": source,
                                "periods": f"{periodCols[0]}..{periodCols[-1]}"
                                if len(periodCols) > 1
                                else (periodCols[0] if periodCols else "-"),
                                "shape": f"{len(nonNullPeriods)}기간",
                                "preview": self._previewDocsCell(topicRows, periodCols),
                            }
                        )

        df = (
            pl.DataFrame(rows)
            if rows
            else pl.DataFrame(
                schema={
                    "chapter": pl.Utf8,
                    "topic": pl.Utf8,
                    "label": pl.Utf8,
                    "kind": pl.Utf8,
                    "source": pl.Utf8,
                    "periods": pl.Utf8,
                    "shape": pl.Utf8,
                    "preview": pl.Utf8,
                }
            )
        )
        self._cache[cacheKey] = df
        return df

    def _applyPeriodFilter(self, payload: Any, period: str | None) -> Any:
        if period is None or not isinstance(payload, pl.DataFrame) or payload.is_empty():
            return payload
        requestedPeriod = str(period)
        q4Fallback = f"{requestedPeriod}Q4" if "Q" not in requestedPeriod else None
        exactPeriod = (
            requestedPeriod
            if requestedPeriod in payload.columns
            else (q4Fallback if q4Fallback and q4Fallback in payload.columns else None)
        )
        if exactPeriod is not None:
            keepCols = [c for c in payload.columns if not _isPeriodColumn(c)]
            keepCols.append(exactPeriod)
            result = payload.select(keepCols)
            if exactPeriod != requestedPeriod:
                result = result.rename({exactPeriod: requestedPeriod})
            return result
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
        return f"{periodCols[0]}..{periodCols[-1]}" if len(periodCols) > 1 else periodCols[0]

    @staticmethod
    def _previewFinance(df: pl.DataFrame | None) -> str:
        if df is None or df.is_empty():
            return "-"
        return f"{df.height} accounts"

    @staticmethod
    def _previewDocsCell(topicRows: pl.DataFrame, periodCols: list[str]) -> str:
        for row in topicRows.iter_rows(named=True):
            for col in periodCols:
                val = row.get(col)
                if val is not None:
                    text = str(val).strip().replace("\n", " ")
                    return f"{col}: {text[:100]}" if len(text) > 100 else f"{col}: {text[:80]}"
        return "-"

    def diff(
        self,
        topic: str | None = None,
        fromPeriod: str | None = None,
        toPeriod: str | None = None,
    ) -> pl.DataFrame | None:
        """기간간 텍스트 변경 비교.

        사용법::

            c.diff()                          # 전체 topic 변경 요약
            c.diff("10-K::item1ARiskFactors") # 특정 topic 변경 이력
            c.diff("10-K::item7Mdna", "2023", "2024")  # 줄 단위 diff
        """
        from dartlab.engines.common.docs.diff import (
            diffSummaryDataFrame,
            lineDiffDataFrame,
            sectionsDiff,
            topicHistoryDataFrame,
        )

        docsSections = self.docs.sections
        if docsSections is None:
            return None
        if topic is not None and fromPeriod is not None and toPeriod is not None:
            return lineDiffDataFrame(docsSections, topic, fromPeriod, toPeriod)
        diffResult = sectionsDiff(docsSections)
        if topic is not None:
            return topicHistoryDataFrame(diffResult, topic)
        return diffSummaryDataFrame(diffResult)

    def watch(
        self,
        topic: str | None = None,
    ) -> pl.DataFrame | None:
        """공시 변화 감지 — 중요도 스코어링 기반 변화 요약.

        사용법::

            c.watch()                              # 전체 topic 중요도 순 요약
            c.watch("10-K::item1ARiskFactors")     # 특정 topic 상세
        """
        from dartlab.engines.analysis.watch.scanner import scan_company

        result = scan_company(self, topic=topic)
        if result is None:
            return None
        return result.to_dataframe()

    def eventStudy(
        self,
        event_type: str | None = None,
        *,
        window: object | None = None,
    ) -> pl.DataFrame | None:
        """공시 발표일 전후 주가 비정상 수익률(CAR) 분석.

        사용법::

            c.eventStudy()                       # 전체 공시 → 주가 영향
            c.eventStudy("10-K")                 # 유형별 필터

        의존성: pip install dartlab[event]
        """
        from dartlab.engines.analysis.event.study import analyze_events, impacts_to_dataframe

        result = analyze_events(self, event_type=event_type, window=window)
        if result is None:
            return None
        return impacts_to_dataframe(result.impacts)

    @property
    def esg(self):
        """ESG 공시 분석 — 환경(E)/사회(S)/지배구조(G) 종합 등급.

        사용법::

            c.esg                   # EsgResult
            c.esg.environment       # 환경 pillar 상세
        """
        if not hasattr(self, "_esg_cache"):
            from dartlab.engines.analysis.esg.extractor import analyze_esg

            self._esg_cache = analyze_esg(self)
        return self._esg_cache

    @property
    def supply(self):
        """공급망 분석 — 고객/공급사 관계 + 리스크 스코어링.

        사용법::

            c.supply                # SupplyChainResult
            c.supply.customers      # 주요 고객
            c.supply.riskScore      # 리스크 점수
        """
        if not hasattr(self, "_supply_cache"):
            from dartlab.engines.analysis.supply.risk import analyze_supply_chain

            self._supply_cache = analyze_supply_chain(self)
        return self._supply_cache

    # ── analyst ──

    def forecast(self, *, horizon: int = 3):
        """매출 앙상블 예측."""
        from dartlab.engines.analysis.analyst.revenueForecast import forecastRevenue

        ts = self.finance.timeseries
        series = ts[0] if isinstance(ts, tuple) else ts
        return forecastRevenue(
            series,
            stockCode=self.ticker,
            market="US",
            horizon=horizon,
            currency="USD",
        )

    def valuation(self, *, shares: int | None = None):
        """종합 밸류에이션 (DCF + DDM + 상대가치)."""
        from dartlab.engines.analysis.analyst.valuation import fullValuation

        ts = self.finance.timeseries
        series = ts[0] if isinstance(ts, tuple) else ts
        if shares is None:
            shares = getattr(self.profile, "sharesOutstanding", None)
            if shares:
                shares = int(shares)
        return fullValuation(series, shares=shares, currency="USD")

    # ── AI 분석 ──

    def ask(
        self,
        question: str,
        *,
        include: list[str] | None = None,
        exclude: list[str] | None = None,
        provider: str | None = None,
        model: str | None = None,
        stream: bool = False,
        reflect: bool = False,
        **kwargs,
    ) -> str:
        """LLM에게 이 기업에 대해 질문.

        Example::

            c = Company("AAPL")
            c.ask("What are the key risks?")
            c.ask("Revenue trend analysis", provider="openai")
        """
        from dartlab.engines.ai.runtime.standalone import ask as _ask

        return _ask(
            self,
            question,
            include=include,
            exclude=exclude,
            provider=provider,
            model=model,
            stream=stream,
            reflect=reflect,
            **kwargs,
        )

    def chat(
        self,
        question: str,
        *,
        provider: str | None = None,
        model: str | None = None,
        max_turns: int = 5,
        on_tool_call=None,
        on_tool_result=None,
        **kwargs,
    ) -> str:
        """Agent mode: LLM selects tools for in-depth analysis.

        Example::

            c = Company("AAPL")
            c.chat("Analyze dividend trends and find anomalies")
        """
        from dartlab.engines.ai.runtime.standalone import chat as _chat

        return _chat(
            self,
            question,
            provider=provider,
            model=model,
            max_turns=max_turns,
            on_tool_call=on_tool_call,
            on_tool_result=on_tool_result,
            **kwargs,
        )
