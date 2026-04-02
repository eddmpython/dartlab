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

from dartlab.providers.edgar._docs_accessor import _DocsAccessor
from dartlab.providers.edgar._finance_accessor import _FinanceAccessor
from dartlab.providers.edgar._profile_accessor import _ProfileAccessor
from dartlab.providers.edgar.openapi.submissions import SUPPORTED_REGULAR_FORMS
from dartlab.providers.filingHelpers import filingRecord, filterFilingsByKeyword, resolveDateWindow, truncateText

_PERIOD_COLUMN_RE = re.compile(r"^\d{4}(Q[1-4])?$")

_FINANCE_TOPICS = frozenset({"BS", "IS", "CF", "CIS"})


class _EdgarNotesWrapper:
    """DART Notes 객체와 동일 인터페이스를 제공하는 EDGAR notes 래퍼."""

    def __init__(self, company):
        self._company = company

    def __call__(self, query: str | None = None) -> pl.DataFrame | None:
        return self._company.docs.notes(query)

    def all(self) -> pl.DataFrame | None:
        return self._company.docs.notes(None)

    def keys(self) -> list[str]:
        return []

    def keys_kr(self) -> list[str]:
        return []

    def quarterly(self, query: str | None = None) -> pl.DataFrame | None:
        return self._company.docs.notes(query)


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

    from dartlab.core.finance.ratios import RATIO_CATEGORIES

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

    @staticmethod
    def canHandle(code: str) -> bool:
        """US ticker (영문 1~5자) 또는 CIK (숫자) 판별."""
        s = code.strip()
        if s.isdigit() and len(s) <= 10:
            return True
        return bool(re.match(r"^[A-Za-z]{1,5}$", s))

    @staticmethod
    def priority() -> int:
        """provider 우선순위 — 낮을수록 먼저 시도. EDGAR=20."""
        return 20

    def __init__(self, ticker: str):
        if not ticker or not isinstance(ticker, str):
            raise ValueError("ticker는 비어있지 않은 문자열이어야 합니다.")
        cleaned = ticker.strip().upper()
        # CIK (순수 숫자) 또는 ticker (영문+숫자, 1-10자)
        if not (cleaned.isdigit() and len(cleaned) <= 10) and not re.match(r"^[A-Z][A-Z0-9./-]{0,9}$", cleaned):
            raise ValueError(f"올바르지 않은 ticker/CIK: '{ticker}' (예: 'AAPL', '0000320193')")
        self.ticker = cleaned
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

        self.docs = _DocsAccessor(self)
        self.finance = _FinanceAccessor(self)
        self._profileAccessor = _ProfileAccessor(self)
        self._reportAccessor = None  # lazy init

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
            from dartlab.providers.edgar.openapi.identity import resolveIssuer

            return resolveIssuer(tickerUpper)
        except ValueError:
            return None

    def _getTickerPath(self) -> Path | None:
        from dartlab import config

        return Path(config.dataDir) / "edgar" / "tickers.parquet"

    def __repr__(self):
        try:
            from dartlab.display.richCompany import renderCompany

            return renderCompany(self)
        except ImportError:
            return f"Company('{self.ticker}', {self.corpName})"

    @property
    def stockCode(self) -> str:
        """서버 API 호환용 ticker 식별자.

        Capabilities:
            - DART Company와 동일한 stockCode 인터페이스 제공
            - 서버 API, export, AI 컨텍스트에서 종목 식별에 사용

        Requires:
            데이터: 없음 (인스턴스 속성)

        AIContext:
            - 서버 API/export에서 종목 식별 키로 사용

        Guide:
            - "이 기업 ticker가 뭐야?" → c.stockCode

        SeeAlso:
            - market: 시장 식별자
            - currency: 통화 식별자

        Returns:
            str — ticker 심볼 (예: "AAPL").

        Example::

            c = Company("AAPL")
            c.stockCode  # "AAPL"
        """
        return self.ticker

    @property
    def market(self) -> str:
        """거래소 시장 식별자.

        Capabilities:
            - 미국 시장 "US" 고정 반환
            - 멀티마켓 분기 로직에서 시장 판별에 사용

        Requires:
            데이터: 없음 (상수)

        AIContext:
            - 시장 구분에 따른 분석 분기 판별에 사용

        Guide:
            - "이 기업 시장이 어디야?" → c.market

        SeeAlso:
            - stockCode: ticker 식별자
            - currency: 통화 식별자

        Returns:
            str — "US".

        Example::

            c = Company("AAPL")
            c.market  # "US"
        """
        return "US"

    @property
    def currency(self) -> str:
        """통화 식별자.

        Capabilities:
            - 미국 달러 "USD" 고정 반환
            - 재무제표 금액 단위 표시, 밸류에이션 통화 기준에 사용

        Requires:
            데이터: 없음 (상수)

        AIContext:
            - 재무 수치 통화 단위 명시에 사용

        Guide:
            - "이 기업 통화가 뭐야?" → c.currency

        SeeAlso:
            - stockCode: ticker 식별자
            - market: 시장 식별자

        Returns:
            str — "USD".

        Example::

            c = Company("AAPL")
            c.currency  # "USD"
        """
        return "USD"

    # quant는 analysis 축 — c.analysis("quant", "기술적분석")으로 접근

    def view(self, *, port: int = 8400) -> None:
        """브라우저에서 공시 뷰어를 열어 sections/index를 시각화.

        Capabilities:
            - 로컬 서버 기동 후 브라우저에서 sections 탐색
            - topic별 텍스트/테이블, 기간 비교를 인터랙티브로 확인

        Requires:
            데이터: sections (SEC EDGAR 자동 수집)

        AIContext:
            - 시각적 탐색 도구로, CLI/노트북이 아닌 브라우저 환경 제공

        Guide:
            - "공시 내용을 브라우저에서 보고 싶어" → c.view()

        SeeAlso:
            - sections: 수평화 보드 원본 데이터
            - index: topic 메타데이터 보드
            - show: 특정 topic 데이터 조회

        Args:
            port: 로컬 서버 포트 (기본 8400).

        Returns:
            None — 브라우저가 자동으로 열림.

        Example::

            c = Company("AAPL")
            c.view()             # localhost:8400 에서 뷰어 실행
            c.view(port=9000)    # 포트 변경
        """
        from dartlab.core.viewer import launchViewer

        launchViewer(self.ticker, port=port)

    @property
    def timeseries(self):
        """분기별 재무 시계열 — (series dict, years list) 튜플.

        Capabilities:
            - SEC XBRL 분기별 재무 시계열 원본
            - BS/IS/CF/CIS 전 제표 계정의 분기 수치

        Requires:
            데이터: 없음 (SEC EDGAR 자동 수집)

        AIContext:
            - ask()/chat()에서 추세 분석, 성장률 계산 컨텍스트

        Guide:
            - "분기별 재무 데이터 원본이 필요해" → c.timeseries
            - "분기별 추세를 보고 싶어" → c.timeseries로 원본 조회 후 분석

        SeeAlso:
            - annual: 연간 재무 시계열
            - BS, IS, CF, CIS: 제표별 DataFrame
            - ratios: 재무비율 시계열

        Returns:
            tuple[dict, list[str]] — (계정별 시계열 dict, 기간 리스트) 또는 None.

        Example::

            c = Company("AAPL")
            c.timeseries  # 분기별 시계열 데이터
        """
        return self.finance.timeseries

    @property
    def annual(self):
        """연간 재무 시계열 — (series dict, years list) 튜플.

        Capabilities:
            - SEC XBRL 연간 재무 시계열 원본
            - 분기 집계가 아닌 10-K 기준 연간 수치

        Requires:
            데이터: 없음 (SEC EDGAR 자동 수집)

        AIContext:
            - ask()/chat()에서 연간 추세, YoY 비교 컨텍스트

        Guide:
            - "연간 재무 데이터 원본이 필요해" → c.annual
            - "YoY 비교를 하고 싶어" → c.annual로 연도별 원본 조회

        SeeAlso:
            - timeseries: 분기별 재무 시계열
            - BS, IS, CF, CIS: 제표별 DataFrame
            - ratios: 재무비율 시계열

        Returns:
            tuple[dict, list[str]] — (계정별 시계열 dict, 연도 리스트) 또는 None.

        Example::

            c = Company("AAPL")
            c.annual  # 연간 시계열 데이터
        """
        return self.finance.annual

    @property
    def BS(self) -> pl.DataFrame | None:
        """재무상태표 (Balance Sheet) — 계정명 x 기간 DataFrame.

        Capabilities:
            - SEC XBRL 정규화 재무상태표
            - 최대 10년 분기/연도 시계열

        Requires:
            데이터: 없음 (SEC EDGAR 자동 수집)

        AIContext:
            - ask()/chat()에서 자산/부채/자본 구조 분석 컨텍스트

        Guide:
            - "재무상태표 보여줘" → c.BS 또는 c.show("BS")
            - "자산 구조가 어떻게 돼?" → c.BS로 확인

        SeeAlso:
            - IS: 손익계산서
            - CF: 현금흐름표
            - CIS: 포괄손익계산서
            - select: 특정 계정/기간 필터
            - show: topic 통합 조회

        Returns:
            pl.DataFrame — 계정명 | 2024Q4 | 2024Q3 | ... 또는 None.

        Example::

            c = Company("AAPL")
            c.BS  # Apple 재무상태표
        """
        return self.finance.BS

    @property
    def IS(self) -> pl.DataFrame | None:
        """손익계산서 (Income Statement) — 계정명 x 기간 DataFrame.

        Capabilities:
            - SEC XBRL 정규화 손익계산서
            - 매출, 영업이익, 순이익 등 수익성 계정 시계열

        Requires:
            데이터: 없음 (SEC EDGAR 자동 수집)

        AIContext:
            - ask()/chat()에서 수익성, 마진 분석 컨텍스트

        Guide:
            - "손익계산서 보여줘" → c.IS 또는 c.show("IS")
            - "매출 추이가 어떻게 돼?" → c.IS로 확인

        SeeAlso:
            - BS: 재무상태표
            - CF: 현금흐름표
            - CIS: 포괄손익계산서
            - select: 특정 계정/기간 필터
            - show: topic 통합 조회

        Returns:
            pl.DataFrame — 계정명 | 2024Q4 | 2024Q3 | ... 또는 None.

        Example::

            c = Company("AAPL")
            c.IS  # Apple 손익계산서
        """
        return self.finance.IS

    @property
    def CF(self) -> pl.DataFrame | None:
        """현금흐름표 (Cash Flow) — 계정명 x 기간 DataFrame.

        Capabilities:
            - SEC XBRL 정규화 현금흐름표
            - 영업/투자/재무 활동별 현금흐름 시계열

        Requires:
            데이터: 없음 (SEC EDGAR 자동 수집)

        AIContext:
            - ask()/chat()에서 현금 창출력, FCF 분석 컨텍스트

        Guide:
            - "현금흐름표 보여줘" → c.CF 또는 c.show("CF")
            - "FCF가 얼마야?" → c.CF로 영업/투자 현금흐름 확인

        SeeAlso:
            - BS: 재무상태표
            - IS: 손익계산서
            - CIS: 포괄손익계산서
            - select: 특정 계정/기간 필터
            - show: topic 통합 조회

        Returns:
            pl.DataFrame — 계정명 | 2024Q4 | 2024Q3 | ... 또는 None.

        Example::

            c = Company("AAPL")
            c.CF  # Apple 현금흐름표
        """
        return self.finance.CF

    @property
    def CIS(self) -> pl.DataFrame | None:
        """포괄손익계산서 (Comprehensive Income) — 계정명 x 기간 DataFrame.

        Capabilities:
            - SEC XBRL 정규화 포괄손익계산서
            - 기타포괄손익 항목 시계열

        Requires:
            데이터: 없음 (SEC EDGAR 자동 수집)

        AIContext:
            - ask()/chat()에서 포괄손익 구성 분석 컨텍스트

        Guide:
            - "포괄손익계산서 보여줘" → c.CIS 또는 c.show("CIS")
            - "기타포괄손익이 뭐가 있어?" → c.CIS로 확인

        SeeAlso:
            - BS: 재무상태표
            - IS: 손익계산서
            - CF: 현금흐름표
            - SCE: 자본변동표
            - show: topic 통합 조회

        Returns:
            pl.DataFrame — 계정명 | 2024Q4 | 2024Q3 | ... 또는 None.

        Example::

            c = Company("AAPL")
            c.CIS  # Apple 포괄손익계산서
        """
        return self.finance.CIS

    @property
    def SCE(self) -> pl.DataFrame | None:
        """자본변동표 (Statement of Changes in Equity) — 계정명 x 기간 DataFrame.

        Capabilities:
            - SEC XBRL 정규화 자본변동표
            - 자본금, 이익잉여금, 자기주식 등 자본 구성 변동 시계열

        Requires:
            데이터: 없음 (SEC EDGAR 자동 수집)

        AIContext:
            - ask()/chat()에서 자본 구조 변동, 자사주 매입 분석 컨텍스트

        Guide:
            - "자본변동표 보여줘" → c.SCE
            - "자사주 매입 내역이 궁금해" → c.SCE로 확인

        SeeAlso:
            - BS: 재무상태표
            - CIS: 포괄손익계산서
            - show: topic 통합 조회

        Returns:
            pl.DataFrame — 계정명 | 2024Q4 | 2024Q3 | ... 또는 None.

        Example::

            c = Company("AAPL")
            c.SCE  # Apple 자본변동표
        """
        return self.finance.SCE

    @property
    def sections(self) -> pl.DataFrame | None:
        """sections — docs + finance 통합 지도 (topic x period 수평화).

        Capabilities:
            - 10-K/10-Q/20-F 문서 항목 + 재무제표를 단일 DataFrame으로 통합
            - topic별 blockType(text/table), 기간별 셀 구조

        Requires:
            데이터: 없음 (SEC EDGAR 자동 수집)

        AIContext:
            - ask()/chat()에서 기업 전체 공시 구조 파악 컨텍스트

        Guide:
            - "전체 공시 지도를 보고 싶어" → c.sections
            - "어떤 topic이 있는지 전체 구조를 보여줘" → c.sections

        SeeAlso:
            - topics: topic 목록 요약
            - index: topic 메타데이터 보드
            - show: 특정 topic 조회
            - diff: 기간간 텍스트 변화 비교

        Returns:
            pl.DataFrame — topic | blockType | blockOrder | 2024 | 2023 | ... 또는 None.

        Example::

            c = Company("AAPL")
            c.sections  # Apple 전체 sections 지도
        """
        return self._profileAccessor.sections

    @property
    def ratios(self) -> pl.DataFrame | None:
        """재무비율 시계열 — category x metric x 기간 DataFrame.

        Capabilities:
            - 수익성/안정성/성장성/효율성/현금흐름 5대 카테고리 30+ 지표
            - 최대 10년 연도별 시계열

        Requires:
            데이터: 없음 (SEC EDGAR 자동 수집)

        AIContext:
            - ask()/chat()에서 재무 건전성, 추세 비교 컨텍스트

        Guide:
            - "재무비율 보여줘" → c.ratios 또는 c.show("ratios")
            - "ROE 추이가 어떻게 돼?" → c.ratios로 확인

        SeeAlso:
            - insights: 재무비율 기반 자동 등급/해설
            - BS, IS, CF: 원본 재무제표
            - timeseries: 분기별 원본 시계열

        Returns:
            pl.DataFrame — category | metric | 2024 | 2023 | ... 또는 None.

        Example::

            c = Company("AAPL")
            c.ratios  # Apple 재무비율 시계열
        """
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
        """재무 인사이트 분석 결과 — 자동 등급/해설 (lazy 계산).

        Capabilities:
            - 수익성/안정성/성장성/효율성/현금흐름 5대 영역 자동 등급
            - 각 영역별 핵심 지표 해설 텍스트

        Requires:
            데이터: 없음 (SEC EDGAR 자동 수집)

        AIContext:
            - ask()/chat()에서 재무 건전성 요약 컨텍스트

        Guide:
            - "재무 상태가 어때?" → c.insights로 자동 등급 확인
            - "재무 건전성 요약" → c.insights

        SeeAlso:
            - ratios: 재무비율 시계열 원본
            - analysis: 분석 엔진 (insights보다 심화)
            - ask: AI 기반 해석

        Returns:
            AnalysisResult — 영역별 등급/해설 객체 또는 None.

        Example::

            c = Company("AAPL")
            c.insights  # Apple 재무 인사이트
        """
        if "_insights" not in self._cache:
            from dartlab.analysis.financial.insight.pipeline import analyze

            ts = self.timeseries
            annual = self.annual
            if ts is None or annual is None:
                return None  # 캐시하지 않음 — 다음 호출에서 재시도
            else:
                self._cache["_insights"] = analyze(
                    self.cik,
                    company=self,
                    corpName=self.corpName,
                    qSeriesPair=ts,
                    aSeriesPair=annual,
                )
        return self._cache["_insights"]

    def review(
        self,
        section: str | None = None,
        layout=None,
        helper: bool | None = None,
        *,
        preset: str | None = None,
        template: str | None = None,
        detail: bool | None = None,
        basePeriod: str | None = None,
    ):
        """재무제표 구조화 보고서 — 14개 섹션 데이터 검토서.

        Capabilities:
            - 14개 섹션 전체 보고서 (수익구조~재무정합성)
            - 단일 섹션 지정 가능
            - 4개 출력 형식 (rich, html, markdown, json)
            - 프리셋 지원 (executive/audit/credit/growth/valuation)

        Requires:
            데이터: 없음 (SEC EDGAR 자동 수집)

        AIContext:
            - reviewer()가 이 결과를 소비하여 AI 해석 생성
            - ask()에서 재무분석 컨텍스트로 활용

        Guide:
            - "Review the financials" → c.review()
            - "Revenue structure" → c.review("수익구조")
            - "Audit review" → c.review(preset="audit")

        SeeAlso:
            - analysis: 14축 개별 분석 (review가 내부적으로 소비)
            - insights: 7영역 등급 + 이상치 요약

        Args:
            section: 섹션명 ("수익구조" 등). None이면 전체.
            layout: ReviewLayout 커스텀. None이면 기본.
            helper: True면 해석 힌트 텍스트 포함.
            preset: 프리셋 이름 (executive/audit/credit/growth/valuation).
            template: 스토리 템플릿 이름.
            detail: False면 요약만 표시.
            basePeriod: 기준 기간.

        Returns:
            Review — 구조화 보고서.

        Example::

            c = Company("AAPL")
            c.review()                # 전체 검토서
            c.review("수익성")         # 특정 섹션
            c.review(preset="audit")  # 감사 검토용
        """
        from dartlab.review.registry import buildReview

        return buildReview(
            self,
            section=section,
            layout=layout,
            helper=helper,
            preset=preset,
            template=template,
            detail=detail,
            basePeriod=basePeriod,
        )

    def analysis(self, axis: str | None = None, sub: str | None = None, **kwargs):
        """분석 엔진 실행 — analysis()에 self를 바인딩.

        Capabilities:
            - 14축 재무분석 + forecast + valuation
            - 2-level 호출: c.analysis("financial", "수익성"), c.analysis("valuation", "가치평가")
            - axis 없이 호출하면 사용 가능한 축 목록 반환

        Requires:
            데이터: 없음 (SEC EDGAR 자동 수집)

        AIContext:
            - ask()/chat()에서 심화 분석 패키지 선택 컨텍스트

        Guide:
            - "재무 분석 해줘" → c.analysis("financial", "수익성")
            - "어떤 분석이 가능해?" → c.analysis()로 축 목록 확인
            - "가치평가 해줘" → c.analysis("valuation", "가치평가")
            - "매출전망" → c.analysis("forecast", "매출전망")

        SeeAlso:
            - review: 분석 결과를 보고서로 조합
            - insights: 재무 인사이트 (간편 요약)
            - ask: AI 기반 해석

        Args:
            axis: 그룹 이름 ("financial", "valuation", "forecast") 또는 축 이름. None이면 가이드.
            sub: 그룹 내 하위 축 이름 ("수익성", "가치평가", "매출전망" 등).
            **kwargs: 축별 추가 파라미터.

        Returns:
            분석 결과 객체 또는 축 목록 dict.

        Example::

            c = Company("AAPL")
            c.analysis()                            # 사용 가능한 축 목록
            c.analysis("financial", "profitability") # 수익성 분석
            c.analysis("valuation", "가치평가")       # 가치평가
            c.analysis("forecast", "매출전망")        # 매출전망
        """
        from dartlab.analysis.financial import Analysis

        _analysis = Analysis()
        if axis is None:
            return _analysis()
        if sub is not None:
            return _analysis(axis, sub, company=self, **kwargs)
        return _analysis(axis, company=self, **kwargs)

    def credit(self, axis: str | None = None, *, detail: bool = False, basePeriod: str | None = None):
        """독립 신용평가 — dCR 20단계 등급."""
        from dartlab.credit import creditCompany

        return creditCompany(self, axis=axis, detail=detail, basePeriod=basePeriod)

    def gather(self, axis: str | None = None, **kwargs):
        """외부 시장 데이터 수집 — gather()에 self.ticker를 바인딩.

        Capabilities:
            - 주가, 뉴스, 매크로 등 외부 데이터 소스 수집
            - axis 없이 호출하면 사용 가능한 축 목록 반환

        Requires:
            데이터: 인터넷 연결 (외부 API 호출)

        AIContext:
            - ask()/chat()에서 주가, 뉴스 등 외부 컨텍스트 보강

        Guide:
            - "주가 데이터가 필요해" → c.gather("price")
            - "어떤 외부 데이터를 수집할 수 있어?" → c.gather()

        SeeAlso:
            - news: 뉴스 수집 (gather("news") 바로가기)
            - analysis: 분석 영역 (수집 데이터를 소비)

        Args:
            axis: 수집 축 이름 (예: "price", "news"). None이면 축 목록.
            **kwargs: 축별 추가 파라미터.

        Returns:
            수집 결과 DataFrame 또는 축 목록.

        Example::

            c = Company("AAPL")
            c.gather()              # 사용 가능한 축 목록
            c.gather("price")       # Apple 주가 수집
        """
        from dartlab.gather.entry import GatherEntry

        _gather = GatherEntry()
        if axis is None:
            return _gather()
        return _gather(axis, self.ticker, market="US", **kwargs)

    def filings(self) -> pl.DataFrame | None:
        """SEC 공시 문서 목록 — 10-K/10-Q 등 정기보고서 목록.

        Capabilities:
            - 사전 수집된 filing 메타데이터 조회
            - formType, filedAt, accessionNo 등 컬럼 포함

        Requires:
            데이터: 없음 (SEC EDGAR 자동 수집)

        AIContext:
            - 보유 공시 목록 확인으로 분석 범위 결정에 활용

        Guide:
            - "이 회사 공시 목록 보여줘" → c.filings()
            - "어떤 보고서가 있어?" → c.filings()로 보유 문서 확인

        SeeAlso:
            - disclosure: SEC filing 검색 (기간/유형/키워드 필터)
            - liveFilings: 실시간 최신 filing 조회
            - readFiling: filing 원문 읽기

        Returns:
            pl.DataFrame — docId | filedAt | formType | ... 또는 None.

        Example::

            c = Company("AAPL")
            c.filings()  # Apple SEC filing 목록
        """
        return self.docs.filings()

    def disclosure(
        self,
        start: str | None = None,
        end: str | None = None,
        *,
        days: int = 365,
        type: str | None = None,
        keyword: str | None = None,
        finalOnly: bool = False,
    ) -> pl.DataFrame:
        """SEC EDGAR filing 검색 — liveFilings 위임.

        Capabilities:
            - 기간/유형/키워드 필터로 SEC filing 검색
            - DART disclosure()와 동일한 인터페이스

        Requires:
            데이터: 인터넷 연결 (SEC EDGAR API)

        AIContext:
            - 최근 공시 빈도/유형으로 기업 이벤트 감지에 활용

        Guide:
            - "최근 공시 뭐 나왔어?" → c.disclosure(days=30)
            - "10-K만 보고 싶어" → c.disclosure(type="10-K")

        SeeAlso:
            - liveFilings: 실시간 최신 filing (정규화 포맷)
            - readFiling: filing 원문 텍스트 읽기
            - filings: 사전 수집된 filing 목록

        Args:
            start: 시작일 (YYYY-MM-DD). None이면 end 기준 days일 전.
            end: 종료일 (YYYY-MM-DD). None이면 오늘.
            days: 기간 일수 (기본 365).
            type: form 유형 필터 (예: "10-K").
            keyword: 제목 키워드 필터.
            finalOnly: EDGAR에서는 미사용 (DART 호환 파라미터).

        Returns:
            pl.DataFrame — docId | filedAt | title | formType | docUrl | ...

        Example::

            c = Company("AAPL")
            c.disclosure()                        # 최근 1년 전체
            c.disclosure(type="10-K")             # 10-K만
            c.disclosure(keyword="earnings")      # 키워드 필터
        """
        return self.liveFilings(start, end, days=days, keyword=keyword, forms=[type] if type else None)

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
    ) -> pl.DataFrame:
        """SEC EDGAR 실시간 filing 목록 — OpenEdgar API 직접 조회.

        Capabilities:
            - SEC EDGAR submissions API에서 최신 filing 실시간 조회
            - form 유형, 기간, 키워드 복합 필터
            - readFiling()과 연계하여 원문 읽기 가능

        Requires:
            데이터: 인터넷 연결 (SEC EDGAR API)

        AIContext:
            - 최신 공시 모니터링으로 기업 이벤트 실시간 감지
            - readFiling()과 조합하여 최신 공시 원문 분석

        Guide:
            - "최신 공시 목록 보여줘" → c.liveFilings()
            - "10-K만 최근 5건" → c.liveFilings(forms=["10-K"], limit=5)

        SeeAlso:
            - readFiling: filing 원문 텍스트 읽기
            - disclosure: 기간/유형/키워드 검색 (liveFilings 위임)
            - filings: 사전 수집된 filing 목록

        Args:
            start: 시작일 (YYYY-MM-DD).
            end: 종료일 (YYYY-MM-DD).
            days: 기간 일수. start/end 미지정 시 사용.
            limit: 최대 반환 건수 (기본 20).
            keyword: 제목/설명 키워드 필터.
            forms: form 유형 리스트 (예: ["10-K", "10-Q"]). None이면 전체.
            finalOnly: EDGAR에서는 미사용.

        Returns:
            pl.DataFrame — docId | filedAt | title | formType | docUrl | ...

        Example::

            c = Company("AAPL")
            c.liveFilings()                           # 최근 filing 20건
            c.liveFilings(forms=["10-K"], limit=5)    # 10-K만 5건
        """
        del finalOnly  # EDGAR regular filings에는 finalOnly 개념이 없다.

        startDate, endDate = resolveDateWindow(start, end, days=days)
        normalizedForms = tuple(forms or SUPPORTED_REGULAR_FORMS)
        cacheKey = f"liveFilings:{startDate}:{endDate}:{limit}:{keyword}:{normalizedForms}"
        if cacheKey in self._cache:
            return self._cache[cacheKey]

        from dartlab.core.guidance import progress
        from dartlab.providers.edgar.openapi.edgar import OpenEdgar

        progress(
            f"{self.corpName} 최신 공시 목록 조회 중... "
            f"(SEC EDGAR, {startDate}~{endDate}, forms={','.join(normalizedForms)})"
        )
        df = OpenEdgar()(self.ticker).filings(
            forms=list(normalizedForms),
            since=startDate,
            until=endDate,
        )
        if df is None or df.is_empty():
            result = pl.DataFrame(
                schema={
                    "docId": pl.Utf8,
                    "filedAt": pl.Utf8,
                    "title": pl.Utf8,
                    "formType": pl.Utf8,
                    "docUrl": pl.Utf8,
                    "indexUrl": pl.Utf8,
                    "market": pl.Utf8,
                    "ticker": pl.Utf8,
                    "cik": pl.Utf8,
                    "accessionNo": pl.Utf8,
                    "filingUrl": pl.Utf8,
                    "filingIndexUrl": pl.Utf8,
                    "primaryDocument": pl.Utf8,
                    "reportDate": pl.Utf8,
                }
            )
            self._cache[cacheKey] = result
            return result

        normalized = (
            filterFilingsByKeyword(
                df,
                keyword=keyword,
                columns=["title", "primary_doc_description", "form"],
            )
            .with_columns(
                [
                    pl.col("accession_no").cast(pl.Utf8).alias("docId"),
                    pl.col("filing_date").cast(pl.Utf8).alias("filedAt"),
                    pl.col("title").cast(pl.Utf8).alias("title"),
                    pl.col("form").cast(pl.Utf8).alias("formType"),
                    pl.col("filing_url").cast(pl.Utf8).alias("docUrl"),
                    pl.col("filing_index_url").cast(pl.Utf8).alias("indexUrl"),
                    pl.lit("US").alias("market"),
                    pl.col("ticker").cast(pl.Utf8).alias("ticker"),
                    pl.col("cik").cast(pl.Utf8).alias("cik"),
                    pl.col("accession_no").cast(pl.Utf8).alias("accessionNo"),
                    pl.col("filing_url").cast(pl.Utf8).alias("filingUrl"),
                    pl.col("filing_index_url").cast(pl.Utf8).alias("filingIndexUrl"),
                    pl.col("primary_document").cast(pl.Utf8).alias("primaryDocument"),
                    pl.col("report_date").cast(pl.Utf8).alias("reportDate"),
                ]
            )
            .select(
                [
                    "docId",
                    "filedAt",
                    "title",
                    "formType",
                    "docUrl",
                    "indexUrl",
                    "market",
                    "ticker",
                    "cik",
                    "accessionNo",
                    "filingUrl",
                    "filingIndexUrl",
                    "primaryDocument",
                    "reportDate",
                ]
            )
        )
        result = normalized.head(limit) if limit > 0 else normalized
        self._cache[cacheKey] = result
        return result

    def readFiling(
        self,
        filing: Any,
        *,
        maxChars: int | None = None,
    ) -> dict[str, Any]:
        """filing 원문 읽기 — URL/accessionNo/DataFrame row로 SEC 문서 다운로드.

        Capabilities:
            - filing URL, accessionNo 문자열, liveFilings() row 모두 지원
            - HTML 자동 텍스트 변환, maxChars 기준 truncate

        Requires:
            데이터: 인터넷 연결 (SEC EDGAR 문서 다운로드)

        AIContext:
            - ask()/chat()에서 특정 filing 원문을 읽어 심층 분석에 활용

        Guide:
            - "이 공시 원문 읽어줘" → c.readFiling(filing)
            - "최신 10-K 내용 보여줘" → liveFilings()로 조회 후 readFiling()

        SeeAlso:
            - liveFilings: 실시간 filing 목록 (readFiling 입력 소스)
            - disclosure: filing 검색
            - show: topic 기반 조회 (수평화된 데이터)

        Args:
            filing: filing URL(str), accessionNo(str), 또는 liveFilings() row.
            maxChars: 최대 문자수. None이면 전체.

        Returns:
            dict — docId, market, title, docUrl, raw, text, truncated 키 포함.

        Example::

            c = Company("AAPL")
            filings = c.liveFilings(forms=["10-K"], limit=1)
            result = c.readFiling(filings[0])
            print(result["text"][:500])
        """
        record = filingRecord(filing) or {}

        if isinstance(filing, str):
            if filing.startswith("http://") or filing.startswith("https://"):
                docUrl = filing.strip()
                accessionNo = ""
            else:
                docUrl = ""
                accessionNo = filing.strip()
        else:
            docUrl = str(record.get("docUrl") or record.get("filingUrl") or "")
            accessionNo = str(record.get("accessionNo") or record.get("docId") or "")

        primaryDocument = str(record.get("primaryDocument") or "")
        if not docUrl and accessionNo and primaryDocument:
            accessionNoDash = accessionNo.replace("-", "")
            docUrl = f"https://www.sec.gov/Archives/edgar/data/{self.cik}/{accessionNoDash}/{primaryDocument}"
        if not docUrl and accessionNo:
            candidates = self.liveFilings(limit=50)
            matched = candidates.filter(pl.col("docId") == accessionNo) if not candidates.is_empty() else None
            if matched is not None and matched.height > 0:
                row = matched.row(0, named=True)
                docUrl = str(row.get("docUrl") or "")
                accessionNo = str(row.get("accessionNo") or accessionNo)
                primaryDocument = str(row.get("primaryDocument") or primaryDocument)

        if not docUrl:
            raise ValueError("EDGAR filing 읽기에는 filing URL 또는 accessionNo가 필요합니다.")

        from dartlab.core.guidance import progress
        from dartlab.providers.edgar.docs.fetch import _downloadFilingSource, _htmlToText

        progress(f"{self.corpName} 공시 원문 다운로드 중... ({accessionNo or Path(docUrl).name})")
        filingPayload = {
            "filingUrl": docUrl,
            "accessionNumber": accessionNo,
        }
        rawText = _downloadFilingSource(filingPayload)
        progress(f"{self.corpName} 공시 원문 정리 중... ({accessionNo or Path(docUrl).name})")
        normalizedText = _htmlToText(rawText) if "<" in rawText and ">" in rawText else rawText
        textPreview, truncated = truncateText(normalizedText, maxChars=maxChars)
        rawPreview, _ = truncateText(rawText, maxChars=maxChars)
        return {
            "docId": accessionNo,
            "market": "US",
            "title": record.get("title") or "",
            "docUrl": docUrl,
            "indexUrl": record.get("indexUrl") or record.get("filingIndexUrl") or "",
            "raw": rawPreview,
            "text": textPreview,
            "truncated": truncated,
        }

    @property
    def topics(self) -> pl.DataFrame:
        """topic 목록 요약 — topic/source/blocks/periods DataFrame.

        Capabilities:
            - finance(BS/IS/CF/CIS/ratios) + docs(10-K/10-Q 항목) 전체 topic 열거
            - 각 topic의 source, 블록 수, 기간 수 요약

        Requires:
            데이터: 없음 (SEC EDGAR 자동 수집)

        AIContext:
            - 사용 가능한 topic 목록으로 질문 라우팅 판단에 활용

        Guide:
            - "어떤 topic이 있어?" → c.topics
            - "분석 가능한 항목 목록" → c.topics로 확인

        SeeAlso:
            - sections: 전체 수평화 보드
            - index: topic 메타데이터 보드
            - show: 특정 topic 데이터 조회

        Returns:
            pl.DataFrame — topic | source | blocks | periods.

        Example::

            c = Company("AAPL")
            c.topics  # Apple 전체 topic 목록
        """
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
        """topic 데이터 조회 — sections 사상의 핵심 소비 경로.

        Capabilities:
            - finance topic(BS/IS/CF/CIS/ratios) + docs topic(10-K/10-Q 항목) 통합 조회
            - block=None이면 블록 목차, block=N이면 해당 블록 실제 데이터
            - period 리스트 전달 시 세로 뷰 (기간 x 항목) 변환
            - 단축 alias 지원: "risk" → "item1ARiskFactors", "mdna" → "item7Mdna"

        Requires:
            데이터: 없음 (SEC EDGAR 자동 수집)

        AIContext:
            - ask()/chat()에서 특정 topic 원문/수치 조회 컨텍스트

        Guide:
            - "재무상태표 보여줘" → c.show("BS")
            - "리스크 팩터 내용 보여줘" → c.show("risk") 또는 c.show("10-K::item1ARiskFactors")
            - "2024년 손익만 보고 싶어" → c.show("IS", period="2024")

        SeeAlso:
            - select: show() 결과에서 행/열 필터
            - trace: topic 데이터 출처 추적
            - sections: 전체 수평화 보드
            - topics: 사용 가능한 topic 목록

        Args:
            topic: topic 이름 (BS, IS, 10-K::item1Business, risk, mdna 등).
            block: blockOrder 인덱스. None이면 블록 목차.
            period: 특정 기간 필터. 리스트면 세로 뷰 (기간 x 항목).

        Returns:
            pl.DataFrame — 블록 목차 또는 실제 데이터. 없으면 None.

        Example::

            c = Company("AAPL")
            c.show("BS")                          # 재무상태표
            c.show("10-K::item1ARiskFactors")     # Risk Factors 텍스트
            c.show("risk")                        # 위와 동일 (alias)
            c.show("IS", period="2024")           # 2024년만 필터
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
        from dartlab.core.show import transposeToVertical

        return transposeToVertical(wide, periods)

    def _buildBlockIndex(self, topicRows: pl.DataFrame) -> pl.DataFrame:
        """topic의 블록 목차 DataFrame."""
        from dartlab.core.show import buildBlockIndex

        return buildBlockIndex(topicRows)

    def select(
        self,
        topic: str,
        indList: str | list[str] | None = None,
        colList: str | list[str] | None = None,
    ):
        """show() 결과에서 행/열 필터 — 특정 계정 x 특정 기간 추출.

        Capabilities:
            - show() 결과에서 행(계정명)과 열(기간) 동시 필터
            - SelectResult 객체로 반환하여 체이닝/export 가능

        Requires:
            데이터: 없음 (SEC EDGAR 자동 수집)

        AIContext:
            - ask()/chat()에서 특정 계정 x 기간 조합을 정밀 추출

        Guide:
            - "Total Assets 2024년 값만 보여줘" → c.select("BS", "Total Assets", "2024")
            - "매출과 순이익 최근 2년" → c.select("IS", ["Revenue", "Net Income"], ["2024", "2023"])

        SeeAlso:
            - show: topic 전체 데이터 조회 (select의 입력 소스)
            - trace: topic 출처 추적

        Args:
            topic: topic 이름 (BS, IS 등).
            indList: 행 필터 — 계정명 문자열 또는 리스트.
            colList: 열 필터 — 기간 문자열 또는 리스트.

        Returns:
            SelectResult — 필터된 DataFrame 래퍼. 없으면 None.

        Example::

            c = Company("AAPL")
            c.select("BS", "Total Assets", "2024")
            c.select("IS", ["Revenue", "Net Income"], ["2024", "2023"])
        """
        from dartlab.core.select import SelectResult
        from dartlab.core.show import selectFromShow

        df = self.show(topic)
        if df is None or not isinstance(df, pl.DataFrame):
            return None
        if isinstance(indList, str):
            indList = [indList]
        if isinstance(colList, str):
            colList = [colList]
        filtered = selectFromShow(df, indList, colList)
        if filtered is None:
            return None
        return SelectResult(
            filtered,
            topic,
            {
                "stockCode": getattr(self, "stockCode", self.ticker),
                "corpName": self.corpName,
                "currency": self.currency,
            },
        )

    def trace(self, topic: str, period: str | None = None) -> dict[str, Any] | None:
        """topic 데이터 출처 추적 — source provenance 확인.

        Capabilities:
            - topic 데이터가 docs/finance 중 어디서 왔는지 추적
            - 선택 근거(whySelected), 우선순위, 커버리지 정보 포함

        Requires:
            데이터: 없음 (SEC EDGAR 자동 수집)

        AIContext:
            - 데이터 신뢰성 검증에 활용 — 출처와 커버리지 확인

        Guide:
            - "이 데이터 어디서 왔어?" → c.trace("BS")
            - "docs에서 온 건지 finance에서 온 건지" → c.trace(topic)

        SeeAlso:
            - show: topic 데이터 조회
            - sections: 전체 수평화 보드
            - index: topic 메타데이터 보드

        Args:
            topic: topic 이름 (BS, IS, 10-K::item1ARiskFactors 등).
            period: 특정 기간 필터 (선택).

        Returns:
            dict — topic, primarySource, whySelected, availableSources 등. 없으면 None.

        Example::

            c = Company("AAPL")
            c.trace("BS")                          # finance 출처 확인
            c.trace("10-K::item1ARiskFactors")     # docs 출처 확인
        """
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
        """topic별 메타데이터 인덱스 — chapter/label/kind/source/periods 보드.

        Capabilities:
            - 전체 topic의 chapter, label, kind(finance/docs), source, periods, shape 요약
            - sections 수평화 보드의 메타 레이어

        Requires:
            데이터: 없음 (SEC EDGAR 자동 수집)

        AIContext:
            - 전체 topic 구조를 한눈에 파악하여 분석 계획 수립에 활용

        Guide:
            - "전체 인덱스 보여줘" → c.index
            - "어떤 데이터가 있는지 요약" → c.index로 메타 정보 확인

        SeeAlso:
            - topics: topic 목록 간단 요약
            - sections: 전체 수평화 보드 원본
            - show: 특정 topic 데이터 조회
            - view: 브라우저에서 시각적 탐색

        Returns:
            pl.DataFrame — chapter | topic | label | kind | source | periods | shape | preview.

        Example::

            c = Company("AAPL")
            c.index  # Apple 전체 topic 인덱스 보드
        """
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
        """기간간 텍스트 변경 비교 — 공시 서술형 diff.

        Capabilities:
            - 전체 topic 변경 요약 (topic 없이 호출)
            - 특정 topic의 기간별 변경 이력
            - 두 기간 지정 시 줄 단위 diff (추가/삭제/변경)

        Requires:
            데이터: 없음 (SEC EDGAR 자동 수집)

        AIContext:
            - ask()/chat()에서 공시 변경 포인트 감지 및 해석에 활용

        Guide:
            - "전체적으로 뭐가 바뀌었어?" → c.diff()
            - "리스크 팩터 변경 내역" → c.diff("10-K::item1ARiskFactors")
            - "2023→2024 MD&A 비교" → c.diff("10-K::item7Mdna", "2023", "2024")

        SeeAlso:
            - watch: 변화 중요도 스코어링 (diff보다 요약)
            - keywordTrend: 키워드 빈도 추이
            - show: topic 데이터 조회

        Args:
            topic: topic 이름. None이면 전체 변경 요약.
            fromPeriod: 비교 시작 기간 (예: "2023").
            toPeriod: 비교 종료 기간 (예: "2024").

        Returns:
            pl.DataFrame — 변경 요약/이력/줄단위 diff. 없으면 None.

        Example::

            c = Company("AAPL")
            c.diff()                                          # 전체 변경 요약
            c.diff("10-K::item1ARiskFactors")                 # Risk Factors 변경 이력
            c.diff("10-K::item7Mdna", "2023", "2024")         # MD&A 줄 단위 diff
        """
        from dartlab.core.docs.diff import (
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

    def keywordTrend(
        self,
        keyword: str | None = None,
        keywords: list[str] | None = None,
    ) -> pl.DataFrame | None:
        """공시 텍스트 키워드 빈도 추이 — topic x period x keyword 히트맵.

        Capabilities:
            - 10-K/10-Q 서술형 텍스트에서 키워드 등장 빈도 추적
            - 단일 키워드 또는 복수 키워드 동시 추적
            - 키워드 미지정 시 내장 기본 키워드(AI, risk 등) 전체 분석

        Requires:
            데이터: 없음 (SEC EDGAR 자동 수집)

        AIContext:
            - 공시 텍스트 내 특정 주제의 강조도 변화를 추적

        Guide:
            - "AI라는 단어가 공시에서 얼마나 자주 나와?" → c.keywordTrend("AI")
            - "여러 키워드 추이를 한번에" → c.keywordTrend(keywords=["AI", "supply chain"])

        SeeAlso:
            - diff: 기간간 텍스트 변경 비교
            - watch: 변화 중요도 스코어링
            - show: topic 원문 조회

        Args:
            keyword: 단일 키워드 문자열.
            keywords: 복수 키워드 리스트. keyword와 동시 지정 시 keyword 우선.

        Returns:
            pl.DataFrame — topic | period | keyword | count. 없으면 None.

        Example::

            c = Company("AAPL")
            c.keywordTrend("AI")                              # AI 키워드 추이
            c.keywordTrend(keywords=["AI", "supply chain"])   # 복수 키워드
            c.keywordTrend()                                  # 내장 키워드 전체
        """
        from dartlab.core.docs.diff import keywordFrequency

        docsSections = self.docs.sections
        if docsSections is None:
            return None
        kws = None
        if keyword:
            kws = [keyword]
        elif keywords:
            kws = keywords
        return keywordFrequency(docsSections, keywords=kws)

    def news(self, *, days: int = 30) -> pl.DataFrame:
        """최근 뉴스 수집 — 종목 관련 뉴스 DataFrame.

        Capabilities:
            - 종목명/ticker 기반 최근 뉴스 수집
            - 기간 조절 가능 (기본 30일)

        Requires:
            데이터: 인터넷 연결 (뉴스 API)

        AIContext:
            - ask()/chat()에서 최근 이벤트 맥락 파악에 활용

        Guide:
            - "최근 뉴스 뭐 있어?" → c.news()
            - "지난 1주일 뉴스만" → c.news(days=7)

        SeeAlso:
            - gather: 외부 데이터 수집 (뉴스 포함)
            - watch: 공시 변화 감지
            - disclosure: SEC filing 검색

        Args:
            days: 수집 기간 일수 (기본 30).

        Returns:
            pl.DataFrame — 뉴스 제목, 날짜, URL 등 포함.

        Example::

            c = Company("AAPL")
            c.news()           # 최근 30일 뉴스
            c.news(days=7)     # 최근 7일
        """
        from dartlab.gather import getDefaultGather

        return getDefaultGather().news(self.ticker, market="US", days=days)

    def watch(
        self,
        topic: str | None = None,
    ) -> pl.DataFrame | None:
        """공시 변화 감지 — 중요도 스코어링 기반 변화 요약.

        Capabilities:
            - 기간간 공시 텍스트 변화를 중요도 점수로 자동 스코어링
            - topic 미지정 시 전체 topic 중요도 순 정렬
            - 특정 topic 지정 시 해당 topic 상세 변화 분석

        Requires:
            데이터: 없음 (SEC EDGAR 자동 수집)

        AIContext:
            - ask()/chat()에서 주목할 공시 변화 포인트 자동 감지에 활용

        Guide:
            - "뭐가 중요하게 바뀌었어?" → c.watch()
            - "리스크 팩터 변화 상세" → c.watch("10-K::item1ARiskFactors")

        SeeAlso:
            - diff: 기간간 텍스트 변경 비교 (줄 단위)
            - keywordTrend: 키워드 빈도 추이
            - show: topic 데이터 조회

        Args:
            topic: topic 이름. None이면 전체 topic 요약.

        Returns:
            pl.DataFrame — topic | score | summary 등. 없으면 None.

        Example::

            c = Company("AAPL")
            c.watch()                              # 전체 topic 중요도 순 요약
            c.watch("10-K::item1ARiskFactors")     # Risk Factors 상세
        """
        from dartlab.scan.watch.scanner import scan_company

        result = scan_company(self, topic=topic)
        if result is None:
            return None
        return result.to_dataframe()

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
        """LLM에게 이 기업에 대해 질문 — 엔진 계산 결과 기반 AI 해석.

        Capabilities:
            - 질문 분류 → 분석 패키지 선택 → 엔진 계산 → LLM 해석
            - include/exclude로 컨텍스트 범위 조절
            - 복수 LLM provider 지원 (openai, ollama 등)

        Requires:
            데이터: LLM API 키 설정 (dartlab ai 또는 환경변수)

        AIContext:
            AI가 분석 전 과정을 주도. dartlab 엔진을 도구로 호출하여 분석 수행.

        Guide:
            - "이 기업 리스크가 뭐야?" → c.ask("What are the key risks?")
            - "매출 추세 분석해줘" → c.ask("Revenue trend analysis")

        SeeAlso:
            - chat: agent mode (tool calling으로 심화 분석)
            - analysis: 분석 엔진 (ask의 컨텍스트 소스)
            - insights: 재무 인사이트 (ask의 컨텍스트 소스)

        Args:
            question: 자연어 질문.
            include: 포함할 컨텍스트 키 리스트.
            exclude: 제외할 컨텍스트 키 리스트.
            provider: LLM provider 이름 (예: "openai", "ollama").
            model: 모델명 (예: "gpt-4o").
            stream: 스트리밍 출력 여부.
            reflect: 자기 반성 모드 (답변 품질 자가 검증).

        Returns:
            str — LLM 응답 텍스트.

        Example::

            c = Company("AAPL")
            c.ask("What are the key risks?")
            c.ask("Revenue trend analysis", provider="openai")
        """
        from dartlab.ai.runtime.standalone import ask as _ask

        return _ask(
            question,
            company=self,
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
        """Agent mode — LLM이 tool calling으로 심화 분석 수행.

        Capabilities:
            - ask() 결과 위에서 LLM이 부족한 부분을 tool 호출로 보충
            - 최대 max_turns 반복으로 원본 탐색, 비교 분석, 메타 질문 처리
            - tool_call/tool_result 콜백으로 진행 과정 모니터링

        Requires:
            데이터: LLM API 키 설정 (tool calling 지원 provider 필요)

        AIContext:
            - Tier 2 AI: LLM이 자율적으로 저수준 tool을 호출하여 심화 탐색

        Guide:
            - "배당 추이를 깊이 분석해줘" → c.chat("Analyze dividend trends and find anomalies")
            - "MSFT와 마진 비교" → c.chat("Compare margins with MSFT")

        SeeAlso:
            - ask: 단일 질문 응답 (chat보다 간편, tool calling 없음)
            - analysis: 분석 엔진
            - select: 특정 계정/기간 필터

        Args:
            question: 자연어 질문.
            provider: LLM provider 이름.
            model: 모델명.
            max_turns: 최대 tool calling 반복 횟수 (기본 5).
            on_tool_call: tool 호출 시 콜백.
            on_tool_result: tool 결과 수신 시 콜백.

        Returns:
            str — LLM 최종 응답 텍스트.

        Example::

            c = Company("AAPL")
            c.chat("Analyze dividend trends and find anomalies")
            c.chat("Compare margins with MSFT", provider="openai")
        """
        from dartlab.ai.runtime.standalone import chat as _chat

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

    @property
    def report(self):
        """EDGAR report 네임스페이스 — XBRL 기반 구조화 데이터."""
        if self._reportAccessor is None:
            from dartlab.providers.edgar._report_accessor import _ReportAccessor

            self._reportAccessor = _ReportAccessor(self)
        return self._reportAccessor

    # ── DartCompany 동기화 메소드 (test_protocol 방어막) ──
    # 아래 메소드는 DartCompany와 인터페이스를 맞추기 위해 존재한다.
    # DART report 전용 데이터가 필요한 경우 None/빈값을 반환한다.

    # ── Properties (데이터 위임) ──

    @property
    def contextSlices(self) -> pl.DataFrame | None:
        return self.docs.contextSlices if hasattr(self.docs, "contextSlices") else None

    @property
    def retrievalBlocks(self) -> pl.DataFrame | None:
        return self.docs.retrievalBlocks if hasattr(self.docs, "retrievalBlocks") else None

    @property
    def notes(self):
        """주석 접근자 — EDGAR docs.notes를 래핑하여 DART Notes와 동일 인터페이스 제공."""
        if "_notes_wrapper" not in self._cache:
            self._cache["_notes_wrapper"] = _EdgarNotesWrapper(self)
        return self._cache["_notes_wrapper"]

    @property
    def profile(self):
        return self._profileAccessor

    @property
    def cumulative(self):
        """누적 시계열 — EDGAR는 연간 데이터가 곧 누적이므로 annual 위임."""
        return self.finance.annual

    @property
    def ratioSeries(self):
        return self.finance.ratioSeries if hasattr(self.finance, "ratioSeries") else None

    # sector, sectorParams, sceMatrix — EXEMPT 등록 (test_protocol.py)
    # 이유: KRX 섹터 인프라 / DART SCE 구조와 상이

    @property
    def rank(self):
        return None  # US 피어 랭킹 미지원 (향후 구현 예정)

    @property
    def sources(self) -> pl.DataFrame:
        """데이터 소스 현황 — EDGAR는 docs + finance 2개 소스."""
        rows = []
        for src, accessor in [("docs", self.docs), ("finance", self.finance)]:
            available = accessor is not None
            rows.append({"source": src, "available": available, "rows": 0, "cols": 0, "shape": ""})
        return pl.DataFrame(rows)

    # ── Methods ──

    def reviewer(
        self,
        section: str | None = None,
        layout=None,
        helper: bool | None = None,
        guide: str | None = None,
        *,
        preset: str | None = None,
        detail: bool | None = None,
        basePeriod: str | None = None,
    ):
        """AI 분석 보고서 — review() + 섹션별 AI 종합의견."""
        from dartlab.review.registry import buildReview

        return buildReview(self, section=section, layout=layout, basePeriod=basePeriod)

    def table(
        self, topic: str, subtopic: str | None = None, *, numeric: bool = False, period: str | None = None
    ) -> Any:
        """topic 데이터를 테이블 형태로 반환."""
        df = self.show(topic, period=period)
        if df is None:
            return None
        return df

    def getTimeseries(self, period: str = "q", fsDivPref: str = "CFS"):
        """재무 시계열 데이터."""
        if period == "y":
            return self.finance.annual
        return self.finance.timeseries

    def audit(self) -> list | None:
        """감사/내부통제 분석 — EDGAR item9A + item14 기반.

        10-K Item 9A(Controls and Procedures) 텍스트에서 material weakness,
        going concern 등 핵심 키워드를 탐지한다.
        """
        import re

        findings: list[dict] = []
        # Item 9A: 내부통제
        item9a = self.show("10-K::item9AControlsAndProcedures", block=0)
        if item9a is not None:
            from dartlab.core.show import isPeriodColumn

            pcols = [c for c in item9a.columns if isPeriodColumn(c)]
            if pcols:
                latest = pcols[0]
                text = " ".join(str(v) for v in item9a[latest].to_list() if v)
                text_lower = text.lower()
                if "material weakness" in text_lower:
                    findings.append({"type": "material_weakness", "period": latest, "severity": "critical"})
                if "going concern" in text_lower:
                    findings.append({"type": "going_concern", "period": latest, "severity": "critical"})
                if "not effective" in text_lower or "ineffective" in text_lower:
                    findings.append({"type": "ineffective_controls", "period": latest, "severity": "warning"})
                if not findings:
                    findings.append({"type": "clean", "period": latest, "severity": "ok"})
        # Item 14: 감사 수수료
        item14 = self.show("10-K::item14PrincipalAccountantFees", block=0)
        if item14 is not None:
            from dartlab.core.show import isPeriodColumn

            pcols = [c for c in item14.columns if isPeriodColumn(c)]
            if pcols:
                latest = pcols[0]
                text = " ".join(str(v) for v in item14[latest].to_list() if v)
                fee_matches = re.findall(r"\$([\d,.]+)\s*(?:million|billion)", text, re.IGNORECASE)
                if fee_matches:
                    findings.append({"type": "audit_fees", "period": latest, "amount": fee_matches[0]})
        return findings or None

    def governance(self, view: str | None = None) -> pl.DataFrame | None:
        """지배구조 분석 — EDGAR item10/item12 기반.

        10-K Part III에서 이사회 구성, 소유 구조 텍스트를 제공한다.
        DART와 달리 구조화된 수치가 아닌 텍스트 데이터이다.
        """
        if view in ("all", "market"):
            return None
        rows: list[dict] = []
        for topic_key, label in [
            ("10-K::item10DirectorsAndCorporateGovernance", "directors"),
            ("10-K::item12SecurityOwnership", "ownership"),
            ("10-K::item11ExecutiveCompensation", "compensation"),
        ]:
            df = self.show(topic_key, block=0)
            if df is not None:
                from dartlab.core.show import isPeriodColumn

                pcols = [c for c in df.columns if isPeriodColumn(c)]
                if pcols:
                    latest = pcols[0]
                    text = " ".join(str(v) for v in df[latest].to_list() if v)
                    rows.append({"항목": label, "기간": latest, "내용": text[:500] if text else ""})
        if not rows:
            return None
        return pl.DataFrame(rows)

    def workforce(self, view: str | None = None) -> pl.DataFrame | None:
        """인력 분석 — EDGAR item1 + IS 기반.

        10-K Item 1(Business)에서 직원 수를 추출하고, IS 매출 대비
        1인당 매출을 계산한다.
        """
        import re

        if view in ("all", "market"):
            return None
        # 모든 block의 텍스트를 합쳐서 employee 패턴 검색
        employee_count: int | None = None
        period: str | None = None
        item1_idx = self.show("10-K::item1Business")
        if item1_idx is None:
            return None
        for row in item1_idx.iter_rows(named=True):
            block_id = row.get("block", 0)
            block_df = self.show("10-K::item1Business", block=block_id)
            if block_df is None:
                continue
            from dartlab.core.show import isPeriodColumn

            pcols = [c for c in block_df.columns if isPeriodColumn(c)]
            if not pcols:
                continue
            # 이 block에 있는 기간 중 첫 번째 사용
            block_period = pcols[0]
            if period is None:
                period = block_period
            if block_period not in block_df.columns:
                continue
            text = " ".join(str(v) for v in block_df[block_period].to_list() if v)
            # 다양한 패턴: "approximately N employees", "N full-time employees", "had N employees"
            patterns = [
                r"(?:approximately|about|over|nearly|had)\s+([\d,]+)\s+(?:full.?time\s+)?employee",
                r"([\d,]+)\s+full.?time\s+employee",
                r"([\d,]+)\s+employee",
                r"employee(?:s)?\s+(?:was|were|of)\s+(?:approximately\s+)?([\d,]+)",
                r"headcount\s+(?:of\s+)?(?:approximately\s+)?([\d,]+)",
                r"workforce\s+(?:of\s+)?(?:approximately\s+)?([\d,]+)",
            ]
            for pat in patterns:
                matches = re.findall(pat, text, re.IGNORECASE)
                for m in matches:
                    cleaned = (m if isinstance(m, str) else m[-1]).replace(",", "").strip()
                    if cleaned and cleaned.isdigit() and int(cleaned) > 100:
                        employee_count = int(cleaned)
                        break
                if employee_count:
                    break
            if employee_count:
                break
        if employee_count is None:
            return None
        # 1인당 매출 계산
        rev_per_employee = None
        is_df = self.IS
        if is_df is not None:
            from dartlab.core.show import isPeriodColumn, selectFromShow

            rev_row = selectFromShow(is_df, ["sales"])
            if rev_row is not None:
                pcols = [c for c in rev_row.columns if isPeriodColumn(c)]
                if pcols:
                    rev = rev_row[pcols[0]][0]
                    if rev:
                        rev_per_employee = rev / employee_count
        return pl.DataFrame(
            [
                {
                    "종목코드": self.ticker,
                    "회사명": self.corpName,
                    "직원수": employee_count,
                    "기간": period,
                    "1인당매출": rev_per_employee,
                }
            ]
        )

    def capital(self, view: str | None = None) -> pl.DataFrame | None:
        """주주환원/자본구조 — EDGAR BS/CF 기반 단일 회사 분석.

        DART와 달리 전종목 횡단비교(view="all")는 미지원.
        """
        if view in ("all", "market"):
            return None  # 전종목 횡단비교 미지원
        bs = self.BS
        cf = self.CF
        if bs is None:
            return None
        from dartlab.core.show import selectFromShow

        equity = selectFromShow(bs, ["total_stockholders_equity", "retained_earnings"])
        divs = selectFromShow(cf, ["dividends_paid"]) if cf is not None else None
        if equity is None:
            return None
        rows: list[dict] = [{"종목코드": self.ticker, "회사명": self.corpName}]
        from dartlab.core.show import isPeriodColumn

        pcols = [c for c in equity.columns if isPeriodColumn(c)]
        if pcols:
            latest = pcols[0]
            for row in equity.iter_rows(named=True):
                rows[0][row["account"]] = row.get(latest)
            if divs is not None:
                for row in divs.iter_rows(named=True):
                    rows[0][row["account"]] = row.get(latest)
        return pl.DataFrame(rows)

    def debt(self, view: str | None = None) -> pl.DataFrame | None:
        """부채구조 분석 — EDGAR BS 기반 단일 회사 분석.

        DART와 달리 전종목 횡단비교(view="all")는 미지원.
        """
        if view in ("all", "market"):
            return None
        bs = self.BS
        if bs is None:
            return None
        from dartlab.core.show import selectFromShow

        debt_accts = selectFromShow(
            bs,
            [
                "total_liabilities",
                "shortterm_borrowings",
                "longterm_borrowings",
                "debentures",
                "current_liabilities",
                "noncurrent_liabilities",
            ],
        )
        if debt_accts is None:
            return None
        rows: list[dict] = [{"종목코드": self.ticker, "회사명": self.corpName}]
        from dartlab.core.show import isPeriodColumn

        pcols = [c for c in debt_accts.columns if isPeriodColumn(c)]
        if pcols:
            latest = pcols[0]
            for row in debt_accts.iter_rows(named=True):
                rows[0][row["account"]] = row.get(latest)
        return pl.DataFrame(rows)
