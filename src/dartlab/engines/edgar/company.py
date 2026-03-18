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

import logging
import re
from pathlib import Path
from typing import Any

import polars as pl

_log = logging.getLogger("dartlab.engines.edgar.company")

_PERIOD_COLUMN_RE = re.compile(r"^\d{4}(Q[1-4])?$")

_FINANCE_TOPICS = frozenset({"BS", "IS", "CF", "CIS"})

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
            df.select(available).unique(subset=["accession_no"]).sort("period_key", descending=False, nulls_last=True)
        )
        self._company._cache[key] = result
        return result


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


class _ProfileAccessor:
    """EDGAR profile namespace — docs spine + finance/report merge layer.

    DART Company.profile과 동일한 사상:
    - docs.sections가 구조적 뼈대
    - finance가 숫자 authoritative → docs 요약재무 대체
    - 서술형/정성 정보는 docs authoritative
    """

    def __init__(self, company: Company):
        self._company = company

    def trace(self, topic: str, period: str | None = None) -> dict[str, Any] | None:
        """topic의 source provenance 반환."""
        if topic in {"BS", "IS", "CIS", "CF"}:
            df = getattr(self._company.finance, topic, None)
            if df is not None:
                return {
                    "topic": topic,
                    "period": period,
                    "primarySource": "finance",
                    "fallbackSources": ["docs"],
                    "whySelected": "finance authoritative priority",
                }

        docsSec = self._company.docs.sections
        if docsSec is not None and topic in docsSec["topic"].to_list():
            return {
                "topic": topic,
                "period": period,
                "primarySource": "docs",
                "fallbackSources": [],
                "whySelected": "docs authoritative priority",
            }
        return None


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
        c.finance.ratios       # 재무비율
        c.profile.trace(topic) # source provenance
        c.BS                   # finance.BS 바로가기
        c.sections             # docs.sections 바로가기
        c.show(topic)          # 통합 조회 → DataFrame | None
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
            from dartlab.engines.edgar.openapi.identity import resolveIssuer

            return resolveIssuer(tickerUpper)
        except ValueError:
            return None

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

    def view(self, *, port: int = 8400) -> None:
        """브라우저에서 공시 뷰어를 엽니다."""
        import socket
        import threading
        import time
        import webbrowser

        def _is_port_in_use(p: int) -> bool:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex(("127.0.0.1", p)) == 0

        if not _is_port_in_use(port):

            def _run():
                import uvicorn

                uvicorn.run("dartlab.server:app", host="127.0.0.1", port=port, log_level="warning")

            t = threading.Thread(target=_run, daemon=True)
            t.start()
            for _ in range(30):
                if _is_port_in_use(port):
                    break
                time.sleep(0.1)

        url = f"http://127.0.0.1:{port}/?company={self.ticker}"
        webbrowser.open(url)

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
        """sections — docs + finance 통합 지도."""
        cacheKey = "_sections"
        if cacheKey in self._cache:
            return self._cache[cacheKey]

        docsSec = self.docs.sections
        if docsSec is None:
            self._cache[cacheKey] = None
            return None

        periodCols = [c for c in docsSec.columns if _isPeriodColumn(c)]

        # source 컬럼 추가
        if "source" not in docsSec.columns:
            docsSec = docsSec.with_columns(pl.lit("docs").alias("source"))

        # finance topics 추가
        extraRows: list[dict[str, Any]] = []
        for ft in ("BS", "IS", "CF", "CIS"):
            df = getattr(self.finance, ft, None)
            if df is not None:
                extraRows.append(
                    {
                        "chapter": "Financial Statements",
                        "topic": ft,
                        "blockType": "table",
                        "blockOrder": 0,
                        "source": "finance",
                        **{p: None for p in periodCols},
                    }
                )
        if self.finance.ratioSeries is not None:
            extraRows.append(
                {
                    "chapter": "Financial Statements",
                    "topic": "ratios",
                    "blockType": "table",
                    "blockOrder": 0,
                    "source": "finance",
                    **{p: None for p in periodCols},
                }
            )

        if not extraRows:
            self._cache[cacheKey] = docsSec
            return docsSec

        extraDf = pl.DataFrame(
            extraRows,
            schema={
                "chapter": pl.Utf8,
                "topic": pl.Utf8,
                "blockType": pl.Utf8,
                "blockOrder": pl.Int64,
                "source": pl.Utf8,
                **{p: pl.Utf8 for p in periodCols},
            },
        )

        merged = pl.concat([docsSec, extraDf], how="diagonal_relaxed")
        self._cache[cacheKey] = merged
        return merged

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

        self._cache[cacheKey] = ordered
        return ordered

    def show(
        self,
        topic: str,
        block: int | None = None,
        *,
        period: str | None = None,
        **_kw: Any,
    ) -> pl.DataFrame | None:
        """topic의 데이터를 반환.

        block=None → 블록 목차 DataFrame (block, type, source, preview)
        block=N → 해당 blockOrder의 실제 데이터 DataFrame

        Args:
            topic: topic 이름 (BS, IS, 10-K::item1Business 등)
            block: blockOrder 인덱스. None이면 블록 목차.
            period: 특정 기간 필터
        """
        sec = self.sections
        if sec is None:
            return None

        topicRows = sec.filter(pl.col("topic") == topic)
        if topicRows.is_empty():
            return None

        if block is None:
            return self._buildBlockIndex(topicRows)

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

    def _buildBlockIndex(self, topicRows: pl.DataFrame) -> pl.DataFrame:
        """topic의 블록 목차 DataFrame."""
        periodCols = [c for c in topicRows.columns if _isPeriodColumn(c)]
        rows = []
        seen: set[int] = set()

        hasBlockOrder = "blockOrder" in topicRows.columns

        for row in topicRows.iter_rows(named=True):
            bt = row.get("blockType", "text")
            source = row.get("source", "docs")

            if hasBlockOrder:
                bo = row.get("blockOrder", 0)
                if bo is None:
                    bo = len(seen)
            else:
                bo = len(seen)

            if bo in seen:
                continue
            seen.add(bo)

            preview = ""
            if source in ("finance", "report"):
                preview = f"({source})"
            else:
                for p in reversed(periodCols):
                    val = row.get(p)
                    if val:
                        preview = str(val)[:50]
                        break
            rows.append({"block": bo, "type": bt, "source": source, "preview": preview})

        return pl.DataFrame(rows)

    def trace(self, topic: str, period: str | None = None) -> dict[str, Any] | None:
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
        for topic in self.topics:
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
        if period in payload.columns:
            keepCols = [c for c in ("account", "category", "metric", "topic", "blockType") if c in payload.columns]
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
        from dartlab.engines.common.docs.diff import sectionsDiff, topicDiff

        docsSections = self.docs.sections
        if docsSections is None:
            return None

        # 줄 단위 상세 diff
        if topic is not None and fromPeriod is not None and toPeriod is not None:
            result = topicDiff(docsSections, topic, fromPeriod, toPeriod)
            if result is None:
                return None
            import difflib

            filtered = docsSections.filter(pl.col("topic") == topic)
            if filtered.height == 0:
                return None
            fromText = str(filtered.item(0, fromPeriod) or "")
            toText = str(filtered.item(0, toPeriod) or "")
            fromLines = fromText.splitlines()
            toLines = toText.splitlines()
            rows: list[dict[str, str | int]] = []
            lineNo = 0
            for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(
                None,
                fromLines,
                toLines,
            ).get_opcodes():
                if tag == "equal":
                    for line in fromLines[i1:i2]:
                        lineNo += 1
                        rows.append({"line": lineNo, "status": " ", "text": line})
                elif tag == "insert":
                    for line in toLines[j1:j2]:
                        lineNo += 1
                        rows.append({"line": lineNo, "status": "+", "text": line})
                elif tag == "delete":
                    for line in fromLines[i1:i2]:
                        lineNo += 1
                        rows.append({"line": lineNo, "status": "-", "text": line})
                elif tag == "replace":
                    for line in fromLines[i1:i2]:
                        lineNo += 1
                        rows.append({"line": lineNo, "status": "-", "text": line})
                    for line in toLines[j1:j2]:
                        lineNo += 1
                        rows.append({"line": lineNo, "status": "+", "text": line})
            return pl.DataFrame(rows) if rows else None

        diffResult = sectionsDiff(docsSections)

        # 특정 topic 변경 이력
        if topic is not None:
            topicEntries = [e for e in diffResult.entries if e.topic == topic]
            if not topicEntries:
                return pl.DataFrame(
                    {
                        "fromPeriod": [],
                        "toPeriod": [],
                        "status": [],
                        "fromLen": [],
                        "toLen": [],
                        "delta": [],
                        "deltaRate": [],
                    }
                )
            return pl.DataFrame(
                [
                    {
                        "fromPeriod": e.fromPeriod,
                        "toPeriod": e.toPeriod,
                        "status": e.status,
                        "fromLen": e.fromLen,
                        "toLen": e.toLen,
                        "delta": e.toLen - e.fromLen,
                        "deltaRate": round((e.toLen - e.fromLen) / e.fromLen, 3) if e.fromLen > 0 else None,
                    }
                    for e in topicEntries
                ]
            )

        # 전체 요약
        return pl.DataFrame(
            [
                {
                    "chapter": s.chapter,
                    "topic": s.topic,
                    "periods": s.totalPeriods,
                    "changed": s.changedCount,
                    "stable": s.stableCount,
                    "changeRate": round(s.changeRate, 3),
                }
                for s in diffResult.summaries
            ]
        )
