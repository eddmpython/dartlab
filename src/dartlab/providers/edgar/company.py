"""EDGAR 엔진 내부 Company 본체.

DART Company와 동일한 구조를 제공한다.

사용법::

    from dartlab import Company

    c = Company("AAPL")
    c.corpName             # "Apple Inc."
    c.index                # 수평화 보드 DataFrame
    c.panel("BS")           # 재무상태표 DataFrame
    c.panel("item1Business")        # docs topic DataFrame
    c.trace("BS")          # source provenance
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

from dartlab.core.logger import getLogger

_log = getLogger(__name__)


import polars as pl

from dartlab.core.edgarClient import SUPPORTED_REGULAR_FORMS
from dartlab.core.polarsUtil import isEmptyDf
from dartlab.core.utils.period import dropPeriodsAfter, parseAsOfPeriod
from dartlab.providers._common.filingHelpers import (
    filingRecord,
    filterFilingsByKeyword,
    resolveDateWindow,
    truncateText,
)
from dartlab.providers.edgar.accessor.docsAccessor import _DocsAccessor
from dartlab.providers.edgar.accessor.financeAccessor import _FinanceAccessor
from dartlab.providers.edgar.accessor.profileAccessor import _ProfileAccessor
from dartlab.providers.edgar.docs.sections.topics import _topicChapterLabel

_PERIOD_COLUMN_RE = re.compile(r"^\d{4}(Q[1-4])?$")

_FINANCE_TOPICS = frozenset({"BS", "IS", "CF", "CIS"})


class _EdgarNotesWrapper:
    """DART Notes 객체와 동일 인터페이스를 제공하는 EDGAR notes 래퍼.

    c.notes("inventory") → 카테고리별 구조화 DataFrame
    c.notes.inventory → 동일
    c.notes.keys() → 데이터 있는 카테고리 목록
    c.notes() → TextBlock 원본 검색 (query=None이면 전체)
    """

    def __init__(self, company):
        self._company = company

    def __call__(self, query: str | None = None) -> pl.DataFrame | None:
        # 카테고리명이면 구조화 Notes 반환
        from dartlab.providers.edgar.docs.notesParsers import availableCategories

        if query and query in availableCategories():
            return self._company.docs.notesByCategory(query)
        # 그 외는 TextBlock 원본 검색
        return self._company.docs.notes(query)

    def __getattr__(self, name: str) -> pl.DataFrame | None:
        if name.startswith("_"):
            raise AttributeError(name)
        from dartlab.providers.edgar.docs.notesParsers import availableCategories

        if name in availableCategories():
            return self._company.docs.notesByCategory(name)
        raise AttributeError(f"EDGAR notes에 '{name}' 카테고리 없음. 지원: {availableCategories()}")

    def all(self) -> pl.DataFrame | None:
        """전체 TextBlock 주석을 단일 DataFrame 으로 반환.

        Returns:
            TextBlock 주석 DataFrame 또는 None.

        Raises:
            없음.

        Example:
            >>> c.notes.all()

        LLM Specifications:
            AntiPatterns:
                - 카테고리 키 알면 `c.notes.<카테고리>` 호출이 더 빠름 - `.all()` 은 회사
                  전체 TextBlock 일괄 fetch 라 메모리 사용 크다.
            OutputSchema:
                - pl.DataFrame - `concept` (us-gaap tag) / `value` (XBRL TextBlock 본문) /
                  `period` (분기 키) / `dimensions` (axis 정보). 주석 없으면 None.
            Prerequisites:
                - 본 Company 인스턴스에 `companyfacts.json` (SEC XBRL) 캐시 존재.
            Freshness:
                - SEC EDGAR `data.sec.gov/api/xbrl/companyfacts/CIK*.json` 갱신 시점 (분기 마감 후 ~45 일).
            Dataflow:
                - SEC companyfacts → notesParsers TextBlock 추출 → docs.notes(None) → 본 wrapper.
            TargetMarkets:
                - US (SEC EDGAR) 한정.
        """
        return self._company.docs.notes(None)

    def keys(self) -> list[str]:
        """데이터가 있는 notes 카테고리 목록.

        Returns:
            카테고리 str 리스트 (예: ``["inventory", "leases", ...]``).

        Raises:
            없음.

        Example:
            >>> c.notes.keys()

        LLM Specifications:
            AntiPatterns:
                - 본 list 외 카테고리 호출 → `AttributeError`. caller 가 list 검사 의무.
            OutputSchema:
                - list[str] - 본 회사가 disclose 한 카테고리만. 모든 회사 공통 set 아님.
            Prerequisites:
                - companyfacts.json 캐시 + notesParsers 의 `CATEGORY_LABELS` 매핑.
            Freshness:
                - SEC companyfacts 갱신 시점 (분기 마감 후 ~45 일).
            Dataflow:
                - companyfacts → docs.noteCategories() → 본 wrapper.
            TargetMarkets:
                - US (SEC EDGAR) 한정.
        """
        return self._company.docs.noteCategories()

    def keysKr(self) -> list[str]:
        """한국어 라벨로 변환된 notes 카테고리 목록.

        Returns:
            한국어 라벨 리스트.

        Raises:
            없음.

        Example:
            >>> c.notes.keysKr()

        SeeAlso:
            - ``keys`` - 영어 카테고리 ID 버전. cross-provider 라벨 dispatch 는 본 함수.
            - ``dart.providers.dart.docs.notes`` - KR 패리티.

        Requires:
            - dartlab
            - polars

        Capabilities:
            - ``keys()`` 의 영어 카테고리 ID 를 `CATEGORY_LABELS` 매핑으로 한국어 라벨화.
              누락된 카테고리는 원본 영문 그대로 통과 - Workbench UI 라벨링 용도.

        Guide:
            - "이 회사 어떤 주석 있나 한국어로" → 본 함수.

        AIContext:
            Workbench UI 가 EDGAR notes 카테고리 chip 표시 시 본 함수 사용.
            영문 ID 그대로 노출 시 사용자 인지 비용 → 한국어 매핑 표시.

        LLM Specifications:
            AntiPatterns:
                - 라벨 값으로 다시 ``c.notes.<라벨>`` 호출 → AttributeError. 라벨은 표시용,
                  실 API 는 ``keys()`` 의 영문 ID 사용.
            OutputSchema:
                - list[str] - 한국어 라벨 또는 매핑 없는 원본 영문.
            Prerequisites:
                - notesParsers.CATEGORY_LABELS 정적 매핑.
            Freshness:
                - SEC companyfacts 갱신 시점.
            Dataflow:
                - companyfacts → keys() 영문 ID → CATEGORY_LABELS → 본 함수.
            TargetMarkets:
                - US (SEC EDGAR) 한정.
        """
        from dartlab.providers.edgar.docs.notesParsers import CATEGORY_LABELS

        return [CATEGORY_LABELS.get(k, k) for k in self.keys()]

    def quarterly(self, query: str | None = None) -> pl.DataFrame | None:
        """분기 단위 TextBlock 주석 검색 - ``notes()`` alias.

        Args:
            query: 검색어 (None 이면 전체).

        Returns:
            주석 DataFrame 또는 None.

        Raises:
            없음.

        Example:
            >>> c.notes.quarterly("revenue")

        LLM Specifications:
            AntiPatterns:
                - 본 함수는 alias - 실제로는 10-K + 10-Q 모두 포함, 분기로 필터링 X.
                  엄밀 분기만 원하면 ``c.docs.notes(query)`` 후 period 컬럼 직접 필터.
            OutputSchema:
                - pl.DataFrame - `concept` / `value` / `period` / `dimensions`. 매치 없으면 None.
            Prerequisites:
                - companyfacts.json 캐시.
            Freshness:
                - SEC companyfacts 갱신 시점.
            Dataflow:
                - companyfacts → docs.notes(query) → 본 wrapper.
            TargetMarkets:
                - US (SEC EDGAR) 한정.
        """
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

# topic → chapter / label 매핑 SSOT 는 docs.sections.topics 로 이관(중복 제거). 본 파일은
# _topicChapterLabel 만 import 해 소비한다. _FINANCE_LABELS/_10K_ITEM_LABELS/_10Q_ITEM_LABELS 는 그곳 정본.


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

    def _sortKey(topic: str) -> tuple[int, int, str]:
        if "::" not in topic:
            return (99, 0, topic)
        formType, itemId = topic.split("::", 1)
        formOrder = _FORM_ORDER.get(formType, 9)
        if formType == "10-K":
            itemOrder = _10K_ORDER.get(itemId, 99)
        elif formType == "10-Q":
            itemOrder = _10Q_ORDER.get(itemId, 99)
        else:
            itemOrder = _extractItemNumber(itemId)
        return (formOrder, itemOrder, itemId)

    return sorted(topics, key=_sortKey)


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

    from dartlab.synth.ratioCategories import RATIO_CATEGORIES

    rows: list[dict[str, Any]] = []
    for category, fields in RATIO_CATEGORIES:
        for fieldName in fields:
            values = ratioData.get(fieldName)
            if not values or not any(v is not None for v in values):
                continue
            row: dict[str, Any] = {
                "분류": _RATIO_CATEGORY_LABELS.get(category, category),
                "항목": _RATIO_FIELD_LABELS.get(fieldName, fieldName),
                "_field": fieldName,
            }
            for idx, year in enumerate(years):
                row[str(year)] = values[idx] if idx < len(values) else None
            rows.append(row)

    if not rows:
        return None
    return pl.DataFrame(rows).drop("_field")


def _isPeriodColumn(col: str) -> bool:
    return bool(_PERIOD_COLUMN_RE.fullmatch(col))


# 미래 정보 차단 규칙은 `core.utils.period` 가 정본이다. 예전에는 dart 와 edgar 가 같은
# 열두 줄을 각자 갖고 있었다. 한쪽 경계만 느슨해지면 그 시장 답만 조용히 미래를 봤다.
_filterPeriodColumnsByAsOf = dropPeriodsAfter
_parseAsof = parseAsOfPeriod


class Company:
    """SEC EDGAR 기반 미국 기업 진입점.

    Example::

        c = Company("AAPL")
        c.panel("BS")           # 연도별 재무상태표
        c.panel("IS")           # 연도별 손익계산서
        c.panel("CF")           # 연도별 현금흐름표
        c.panel("CIS")          # 연도별 포괄손익계산서
        c.panel("ratios")       # 재무비율 시계열
        c.panel("item1Business")  # docs topic
        c.topics               # 전체 topic 목록
    """

    @staticmethod
    def canHandle(code: str) -> bool:
        """US ticker (영문 1~5 자) 또는 CIK (10 자리 이하 숫자) 판별 - Company 라우터 게이트.

        Capabilities:
            - 영문 1~5 자 (AAPL/MSFT 등) → True.
            - 10 자리 이하 숫자 (CIK, leading zero 포함 가능) → True.
            - 그 외 (한국어 회사명, 6 자리 숫자 KR stockCode 등) → False.
            - Company 팩토리가 provider 분기 시 사용.

        Args:
            code: ticker 또는 CIK 문자열. strip 자동.

        Returns:
            bool - True 면 EDGAR 처리, False 면 다른 provider (dart/edinet) 시도.

        Example:
            >>> # Company.canHandle("AAPL")  # True
            >>> # Company.canHandle("0000320193")  # True
            >>> # Company.canHandle("005930")  # True (6 자리 숫자도 → False 가 맞으나, 10 자리 이하 숫자라 True 반환됨)
            >>> # Company.canHandle("삼성전자")  # False

        Guide:
            - "EDGAR 처리 가능 코드냐" → 본 함수.
            - Company 팩토리가 dart/edgar/edinet 순서로 priority 따라 호출.
            - 한국어 회사명 → False (resolveCompany 가 다른 경로).

        SeeAlso:
            - ``Company.priority`` - 라우터 우선순위 SSOT.
            - ``dartlab.providers.dart.company.Company.canHandle`` - KR stockCode 판정.
            - operation.apiContract - provider 라우팅 SSOT.

        Requires:
            - re (stdlib) - ticker 패턴 검증.

        AIContext:
            Company 팩토리 내부 라우터. AI 가 사용자 입력 "AAPL" / "0000320193" 받으면 자동
            라우팅. 본 함수 직접 호출 X.

        LLM Specifications:
            AntiPatterns:
                - 6 자리 숫자 (KR 종목코드) 도 본 함수 True 반환 - dart provider 가 먼저 매칭 의무.
                - 영문 6 자 이상 (예 "GOOGLE") → False. ticker 는 최대 5 자 가정.
                - 빈 문자열 → re 매칭 False.
            OutputSchema:
                - 1 bool.
            Prerequisites:
                - 입력이 str.
            Freshness:
                - 정적 규칙. SEC ticker 규칙 변경 시 본 함수 수정.
            Dataflow:
                - 사용자 입력 → Company() factory → 본 함수 → provider 선택.
            TargetMarkets:
                - US (SEC EDGAR) 한정.

        Raises:
            없음.
        """
        s = code.strip()
        if s.isdigit() and len(s) <= 10:
            return True
        return bool(re.match(r"^[A-Za-z]{1,5}$", s))

    @staticmethod
    def priority() -> int:
        """provider 우선순위 - 낮을수록 먼저 시도. EDGAR=20.

        Returns:
            우선순위 int (DART=10, EDGAR=20, EDINET=30).

        Raises:
            없음.

        Example:
            >>> Company.priority()
            20

        LLM Specifications:
            AntiPatterns:
                - 본 값을 외부에서 hard-code 비교 → 라우터 순서 변경 시 회귀. ``priority()`` 호출만.
            OutputSchema:
                - int 상수 20.
            Prerequisites:
                - 없음 (정적 상수).
            Freshness:
                - 라우터 SSOT 변경 시 갱신 (드물다).
            Dataflow:
                - Company 팩토리 → 본 함수 → provider 순위 정렬 → canHandle 시도.
            TargetMarkets:
                - US (SEC EDGAR) - 본 provider 식별자.
        """
        return 20

    def __init__(self, ticker: str):
        """EDGAR US Company 인스턴스 초기화 - ticker/CIK 3-tier 해석 + accessor 4 종 셋업.

        Args:
            ticker: 영문 ticker (``"AAPL"`` / ``"BRK.B"``) 또는 SEC CIK 숫자
                (``"0000320193"`` / ``"320193"``). 영문 정규식 ``[A-Z][A-Z0-9./-]{0,9}``,
                숫자는 길이 ≤ 10. 대소문자 무관 (내부 ``upper()`` 정규화).

        Returns:
            None (생성자).

        Raises:
            ValueError: ``ticker`` 가 빈/비문자열/포맷 위반 또는 SEC tickers/listed universe/
                identity 3 tier 모두 미매치. 메시지에 가능 원인 3 종 포함 (오타/미등록/네트워크).

        Example:
            >>> from dartlab.providers.edgar.company import Company
            >>> c = Company("AAPL")
            >>> c.cik
            '0000320193'

        SeeAlso:
            - ``_resolveTickerRow`` - parquet → listed universe → SEC identity 3-tier 해석.
            - ``providers.edgar.openapi.identity.resolveIssuer`` - SEC ``company_tickers.json`` 조회.
            - ``frame.dataLoader.loadEdgarListedUniverse`` - HF listed universe parquet.

        Requires:
            - polars
            - dartlab.core.memory.BoundedCache (30 entry cap)
            - dartlab.providers.edgar.accessor.* (Docs/Finance/Profile)
            - dartlab.core.edgarClient (lazy SEC API fallback)

        Capabilities:
            - 단일 미국 상장사 facade 진입점 - docs/finance/profile 통합 access.
            - ticker / CIK 양방향 입력 - 사용자 편의.
            - lazy SEC API - local parquet 우선 hit, 미스 시에만 네트워크.

        Guide:
            - "Apple 재무" → ``Company("AAPL").panel("IS")``.
            - "CIK 만 알 때" → ``Company("0000320193")`` (zero-padded 또는 정수 모두 OK).
            - "다종목 순회" → ``with Company(t) as c: ...`` (OomTripwire 보호).

        AIContext:
            Ask Workbench Company facade - LLM 이 첫 호출하는 US provider 엔트리.
            ``co.panel("BS")`` / ``co.notes("inventory")`` 등 모든 후속 호출의 self.

        LLM Specifications:
            AntiPatterns:
                - 회사명 입력 X - EDGAR 는 ticker / CIK strict ("Apple" → ValueError).
                - SEC User-Agent header 미설정 → HTTP 403 (dartlab.core.http 가 처리하나 환경 변수 ``DARTLAB_USER_AGENT`` 권장).
                - ``Company(t)`` 한 인스턴스 다종목 재사용 X - 종목당 신규 Company 강제.
                - ``with`` 누락 다종목 루프 → Polars Rust heap 누적 → OOM.
                - 11 자리 이상 CIK 호출 → 포맷 위반 ValueError.
            OutputSchema:
                - Company 인스턴스 - ``ticker`` (str upper) / ``cik`` (str zero-padded 10)
                  / ``corpName`` (str, tickers.json title) / ``_cache`` (BoundedCache 30).
                - 내부 accessor: ``_docs`` (DocsAccessor) / ``_finance`` (FinanceAccessor)
                  / ``_profileAccessor`` (ProfileAccessor) / ``_reportAccessor`` (lazy None).
            Prerequisites:
                - ``edgar/tickers.parquet`` 캐시 또는 SEC EDGAR API 연결 (User-Agent header 필수).
                - HF listed universe parquet 또는 SEC company_tickers.json origin.
            Freshness:
                - SEC ``company_tickers.json`` 일 단위 갱신. parquet 캐시는 lazy refresh.
                - companyfacts (XBRL) 는 분기 마감 후 ~45 일 지연 (10-Q/10-K 제출 cadence).
            Dataflow:
                - ticker (raw) → ``strip().upper()`` 정규화 → ``_resolveTickerRow``
                - → (tier 1) ``edgar/tickers.parquet`` → (tier 2) listed universe →
                  (tier 3) ``identity.resolveIssuer`` SEC API
                - → ``cik`` zfill(10) + BoundedCache(30) + 3 accessor 인스턴스화 → Company.
            TargetMarkets:
                - US (SEC EDGAR) - NYSE/NASDAQ/AMEX/OTC SEC 등록 종목 한정. 비등록/외국 X.
        """
        if not ticker or not isinstance(ticker, str):
            raise ValueError("ticker는 비어있지 않은 문자열이어야 합니다.")
        cleaned = ticker.strip().upper()
        # CIK (순수 숫자) 또는 ticker (영문+숫자, 1-10자)
        if not (cleaned.isdigit() and len(cleaned) <= 10) and not re.match(r"^[A-Z][A-Z0-9./-]{0,9}$", cleaned):
            raise ValueError(f"올바르지 않은 ticker/CIK: '{ticker}' (예: 'AAPL', '0000320193')")
        self.ticker = cleaned
        from dartlab.core.memory import BoundedCache

        self._cache: BoundedCache = BoundedCache(maxEntries=30)

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

        # public namespace 모두 제거 (P3a/b/c)
        self._docs = _DocsAccessor(self)
        self._finance = _FinanceAccessor(self)
        self._profileAccessor = _ProfileAccessor(self)
        self._reportAccessor = None  # lazy init

    def _resolveTickerRow(self, ticker: str) -> dict | None:
        tickerPath = self._getTickerPath()
        tickerUpper = ticker.upper()

        def _pickRow(df: pl.DataFrame) -> dict | None:
            """ticker 또는 CIK로 SEC 회사 식별 행을 하나 고른다."""
            if "ticker" in df.columns:
                row = df.filter(pl.col("ticker") == ticker)
                if row.is_empty():
                    row = df.filter(pl.col("ticker") == tickerUpper)
                if not row.is_empty():
                    r = row.row(0, named=True)
                    r["cik"] = str(r["cik"]).zfill(10)
                    return r
            if tickerUpper.isdigit() and "cik" in df.columns:
                targetCik = tickerUpper.zfill(10)
                cols = [
                    c for c in ("ticker", "cik", "title", "exchange", "is_exchange_listed", "is_otc") if c in df.columns
                ]
                for r in df.select(cols).iter_rows(named=True):
                    if str(r.get("cik") or "").zfill(10) == targetCik:
                        r["cik"] = targetCik
                        return r
            return None

        if tickerPath is not None and tickerPath.exists():
            df = pl.read_parquet(tickerPath)
            r = _pickRow(df)
            if r is not None:
                return r

        if sys.platform == "emscripten":
            try:
                from dartlab.core.dataLoader import loadData

                r = _pickRow(loadData("tickers", "edgarTickers"))
                if r is not None:
                    return r
            except Exception:  # noqa: BLE001
                return None
            return None

        try:
            from dartlab.core.dataLoader import loadEdgarListedUniverse

            listed = loadEdgarListedUniverse()
            r = _pickRow(listed)
            if r is not None:
                return r
        except (FileNotFoundError, OSError, RuntimeError):
            pass

        try:
            from dartlab.core.edgarClient import resolveIssuer

            return resolveIssuer(tickerUpper)
        except ValueError:
            return None

    def _getTickerPath(self) -> Path | None:
        import dartlab.config as config

        return Path(config.dataDir) / "edgar" / "tickers.parquet"

    def __repr__(self):
        from dartlab.core.htmlRenderer import getHtmlRenderer

        renderer = getHtmlRenderer()
        if renderer is not None:
            text = renderer.renderCompany(self)
            if text is not None:
                return text
        return f"Company('{self.ticker}', {self.corpName})"

    # ── P7: Company context manager + 메모리-safe surface (룰 11 + MemorySafeProvider) ──

    def __enter__(self) -> "Company":
        """context manager 진입 - OomTripwire 시작 + self 반환.

        Example:
            with Company("AAPL") as c:
                c.panel("IS").head()

        Returns:
            self.

        Raises:
            없음.
        """
        from dartlab.core.memory import OomTripwire

        self._oomTripwire = OomTripwire()
        self._oomTripwire.start()
        return self

    def __exit__(self, _excType: object, _excVal: object, _excTb: object) -> None:
        """context manager 종료 - OomTripwire 정지 + BoundedCache evict + RSS 회수.

        Args:
            excType: 예외 type.
            excVal: 예외 인스턴스.
            excTb: traceback.

        Raises:
            없음.
        """
        try:
            tw = getattr(self, "_oomTripwire", None)
            if tw is not None:
                tw.stop()
        except (AttributeError, RuntimeError):
            pass
        try:
            self.cleanupCache()
        except (AttributeError, KeyError, RuntimeError):
            pass

    def cleanupCache(self) -> int:
        """BoundedCache evict + cleanupBetweenCompanies.

        Returns:
            evict 된 entry 수.

        Example:
            >>> c = Company("AAPL")
            >>> c.panel("IS")
            >>> n = c.cleanupCache()

        Raises:
            없음.

        SeeAlso:
            - ``__exit__`` - context manager 종료 시 본 함수 자동 호출.
            - ``memorySnapshot`` - 호출 전/후 RSS 비교.
            - ``dartlab.core.memory.cleanupBetweenCompanies`` - Polars Rust heap 회수 트리거.

        Requires:
            - dartlab
            - polars

        Capabilities:
            - 인스턴스 ``self._cache`` (BoundedCache) 의 모든 entry evict + Polars 네이티브 힙
              `cleanupBetweenCompanies` 호출. multi-company loop 사이에 호출 의무.

        Guide:
            - "다음 회사 진입 전 메모리 정리" → 본 함수 또는 ``with Company(c):`` 컨텍스트.
            - "OOM 위험 회피" → multi-company loop 안 끝마다 호출.

        AIContext:
            AI 가 다종목 batch 처리 (`for ticker in tickers:`) 안에서 본 함수 호출 의무.
            누락 시 Polars Rust heap 누적으로 OOM.

        LLM Specifications:
            AntiPatterns:
                - 호출 없이 다종목 순회 → Rust heap 누적 → OOM.
                - ``gc.collect()`` 만 호출 → Polars 힙은 Python gc 회수 X. 본 함수 의무.
            OutputSchema:
                - int - evict 된 cache entry 수 (0 가능).
            Prerequisites:
                - 본 Company 인스턴스 활성 상태.
            Freshness:
                - 호출 시점 즉시.
            Dataflow:
                - self._cache → clear → cleanupBetweenCompanies → Rust heap 회수.
            TargetMarkets:
                - US (SEC EDGAR) - 본 클래스의 cache 정리.
        """
        from dartlab.core.memory import cleanupBetweenCompanies

        evicted = len(self._cache)
        self._cache.clear()
        cleanupBetweenCompanies(label=f"{self.ticker}_exit")
        return evicted

    def memorySnapshot(self) -> dict[str, int]:
        """캐시 size + 현 RSS snapshot.

        Returns:
            keys: "cacheSize", "rssMb".

        Example:
            >>> c = Company("AAPL")
            >>> c.memorySnapshot()
            {'cacheSize': 5, 'rssMb': 300}

        Raises:
            없음.

        SeeAlso:
            - ``cleanupCache`` - 본 함수가 보여준 RSS 회수.
            - ``dartlab.core.memory.getMemoryMb`` - psutil 기반 RSS 추정.

        Requires:
            - dartlab
            - polars

        Capabilities:
            - ``self._cache`` (BoundedCache) entry 수 + 현 프로세스 RSS (MB) 를 dict 로 합산 반환.
              MemorySafeProvider Protocol 의 측정 entry point.

        Guide:
            - "지금 이 Company 가 얼마나 메모리 쓰나" → 본 함수.
            - "cleanupCache 효과 확인" → 호출 전/후 비교.

        AIContext:
            workbench 가 OOM tripwire 발동 직전 본 함수로 회사별 메모리 분포 표시.
            AI 가 "메모리 어디 쓰나" 답변 시 인용.

        LLM Specifications:
            AntiPatterns:
                - RSS 값을 절대값으로 비교 시 환경 차이 (Windows vs WSL) - 추세만 사용.
                - cacheSize 0 == 메모리 정리 완료 X. Polars Rust heap 은 별도 영역.
            OutputSchema:
                - dict {"cacheSize": int, "rssMb": int}.
            Prerequisites:
                - psutil (`getMemoryMb` 의존).
            Freshness:
                - 호출 시점 즉시.
            Dataflow:
                - psutil RSS + self._cache len → 본 함수 → dict.
            TargetMarkets:
                - US (SEC EDGAR) - 본 클래스 인스턴스 추적.
        """
        from dartlab.core.memory import getMemoryMb

        return {"cacheSize": len(self._cache), "rssMb": int(getMemoryMb())}

    @property
    def fiscalYearEnd(self) -> str | None:
        """회계연도 종료 월-일 (예: AAPL → '09-26', MSFT → '06-30').

        XBRL companyfacts 의 fp='FY' end 날짜에서 가장 자주 등장하는 month-day 추출.
        DART 종목은 12-31 표준 (한국 회계 관습).

        calendar year vs fiscal year 매칭 명시. 회사 간 연도 비교 시 fiscal
        year-end 가 다른 회사를 calendar year 로 매칭하면 잘못된 비교가 된다.

        Returns:
            "MM-DD" 형식 문자열, 데이터 없으면 None.

        Raises:
            없음 (내부 IO 예외는 잡아서 None 반환).

        Example::

            c = Company("AAPL")
            c.fiscalYearEnd  # "09-26" (마지막 토요일 변형 가능)

        SeeAlso:
            - ``dartlab.providers.dart.company.Company.fiscalYearEnd`` - KR 패리티 (12-31 고정).
            - ``finance/scanAccount`` - 본 값을 활용한 분기→연도 매칭.

        Requires:
            - dartlab
            - polars

        Capabilities:
            - companyfacts.parquet 의 fp='FY' 분기 row 들에서 (1) fy 별 mode end 추출
              (2) mode 들의 month-day 다시 mode → 진짜 회계 연말일. 토요일 변형 (52/53 week) 포함.

        Guide:
            - "이 회사 회계연말이 언제냐" → 본 property.
            - "fiscal year 가 calendar year 와 다르냐" → 본 값이 "12-31" 아니면 다름.

        AIContext:
            AI 가 EDGAR 회사를 DART 회사와 비교할 때 매핑 기준. 12-31 가정 시 잘못된
            분기 매칭 (예: 9 월 FY 회사의 Q4 ↔ 12 월 FY 회사의 Q3) 발생.

        LLM Specifications:
            AntiPatterns:
                - 모든 US 회사가 12-31 가정 → AAPL/CSCO/ORCL 등 변형 FY 회사 비교 시 wrong period.
                - 본 값을 ISO date 로 사용 X - "MM-DD" 만, 연도 정보 없음.
            OutputSchema:
                - str "MM-DD" 또는 None (companyfacts 없음).
            Prerequisites:
                - data/edgar/finance/{CIK}.parquet (companyfacts dump).
            Freshness:
                - companyfacts.parquet 갱신 시점. cache 후 인스턴스 lifetime 동안 고정.
            Dataflow:
                - companyfacts.parquet → fp='FY' filter → fy 별 mode → mode of mode → month-day.
            TargetMarkets:
                - US (SEC EDGAR) - XBRL 회계 연도 SSOT.
        """
        cacheKey = "_fiscalYearEnd"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        try:
            from pathlib import Path

            import polars as pl

            cik = str(self.cik).zfill(10)
            path = Path(f"data/edgar/finance/{cik}.parquet")
            if not path.exists():
                self._cache[cacheKey] = None
                return None
            # fy 별 mode (가장 많이 등장하는) end 가 진짜 FY 종료일.
            # 그 중에서 가장 흔한 month-day 가 fiscal year-end.
            lf = pl.scan_parquet(str(path))
            modeEnds = (
                lf.filter(pl.col("fp") == "FY")
                .filter(pl.col("end").is_not_null())
                .filter(pl.col("fy").is_not_null())
                .group_by(["fy", "end"])
                .len()
                .sort(["fy", "len"], descending=[False, True])
                .group_by("fy")
                .head(1)
            )
            df = (
                modeEnds.with_columns(
                    (pl.col("end").dt.month().cast(pl.Int32) * 100 + pl.col("end").dt.day().cast(pl.Int32)).alias("md")
                )
                .group_by("md")
                .len()
                .sort("len", descending=True)
                .head(1)
                .collect(engine="streaming")
            )
            if df.height == 0:
                self._cache[cacheKey] = None
                return None
            md = df.row(0)[0]
            result = f"{md // 100:02d}-{md % 100:02d}"
            self._cache[cacheKey] = result
            return result
        except (FileNotFoundError, OSError, ValueError):
            self._cache[cacheKey] = None
            return None

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
            str - ticker 심볼 (예: "AAPL").

        Raises:
            없음.

        Example::

            c = Company("AAPL")
            c.stockCode  # "AAPL"

        LLM Specifications:
            AntiPatterns:
                - DART 종목코드 6 자리 형식 가정 → US ticker 는 영문 1~5 자. 자릿수 검사 X.
            OutputSchema:
                - str ticker (예 "AAPL"). 비어있을 수 없음.
            Prerequisites:
                - Company 인스턴스 생성 완료.
            Freshness:
                - 인스턴스 lifetime 동안 불변.
            Dataflow:
                - __init__ ticker 정규화 → self.ticker → 본 property.
            TargetMarkets:
                - US (SEC EDGAR) - ticker SSOT.
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
            str - "US".

        Raises:
            없음.

        Example::

            c = Company("AAPL")
            c.market  # "US"

        LLM Specifications:
            AntiPatterns:
                - 시장 세분화 (NYSE vs NASDAQ) 필요 시 본 값으로는 부족 - listing 메타에서 추출.
            OutputSchema:
                - 고정 str "US".
            Prerequisites:
                - 없음 (상수).
            Freshness:
                - 정적. SEC primary market 변경 시 별도 정의.
            Dataflow:
                - 본 property → "US" 상수.
            TargetMarkets:
                - US (SEC EDGAR) 통합 라벨.
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
            str - "USD".

        Raises:
            없음.

        Example::

            c = Company("AAPL")
            c.currency  # "USD"

        LLM Specifications:
            AntiPatterns:
                - 외국 등록 (ADR) 회사도 본 함수 "USD" 반환 - 보고통화 vs 결산통화 차이는 별도 추출 의무.
            OutputSchema:
                - 고정 str "USD".
            Prerequisites:
                - 없음 (상수).
            Freshness:
                - 정적. SEC 회사는 USD reporting 강제.
            Dataflow:
                - 본 property → "USD" 상수.
            TargetMarkets:
                - US (SEC EDGAR) reporting currency.
        """
        return "USD"

    @property
    def quant(self):
        """주가 기술적 분석 - dual access (Phase 8 A3).

        ``c.quant`` (object) 또는 ``c.quant(axis, ...)`` (call) 양식 모두 지원.

        Returns:
            ``CallableAccessor`` - ``c.quant.SMA(...)`` 또는 ``c.quant("SMA")`` 사용.

        Raises:
            없음.

        Example:
            >>> c = Company("AAPL")
            >>> c.quant()              # 사용 가능한 축 목록
            >>> c.quant("returns")     # 주가 수익률

        SeeAlso:
            - ``dartlab.quant.Quant`` - 30 축 SSOT.
            - ``dart.providers.dart.company.Company.quant`` - KR 패리티 (동일 인터페이스).

        Requires:
            - dartlab
            - polars

        Capabilities:
            - ``dartlab.quant.Quant`` 의 30 축 (SMA/EMA/RSI/MACD/Bollinger/ATR/returns 등) 을
              본 회사 ticker 기준으로 호출. property 접근/call 호환 - ``CallableAccessor`` 가
              두 양식 모두 동일 backend dispatch.

        Guide:
            - "이 회사 주가 SMA50" → ``c.quant("SMA", window=50)``.
            - "사용 가능 quant 축" → ``c.quant()`` 빈 호출.

        AIContext:
            workbench 주가 분석 entry. 본 함수는 주가 시계열 origin 만 - 재무 시계열은 ``finance``.
        """
        from dartlab.core.dualAccess import CallableAccessor

        if "_quantAccessor" not in self._cache:
            self._cache["_quantAccessor"] = CallableAccessor(self._quantImpl, name="quant")
        return self._cache["_quantAccessor"]

    def _quantImpl(self, axis=None, *, metric=None, **kwargs):
        """주가 기술적 분석 - 30축 (내부 구현)."""
        from dartlab.quant import Quant

        if axis is None and metric is not None:
            axis = metric
        q = Quant()
        if axis is None:
            return q()
        return q(axis, self.stockCode, **kwargs)

    def macro(self, axis=None, target=None, *, overrides: dict | None = None, **kwargs):
        """시장 매크로 분석 - EDGAR 회사는 US 시장 위임 (Phase 8 A2).

        Args:
            axis: 매크로 축 (None 이면 가이드).
            target: 분석 target.
            overrides: 매크로 override dict.
            **kwargs: 축별 추가 인자.

        Returns:
            ``Macro()`` 결과 객체.

        Raises:
            ValueError: 미지원 axis.

        Example:
            >>> c = Company("AAPL")
            >>> c.macro("yield_curve")

        SeeAlso:
            - ``dartlab.macro.Macro`` - 매크로 axis 카탈로그 SSOT.
            - ``dart.providers.dart.company.Company.macro`` - KR 패리티 (market="KR" 위임).

        Requires:
            - dartlab
            - polars

        Capabilities:
            - 본 회사의 시장 매크로 (yield_curve / inflation / fx / fedFunds 등) 를 US 기준으로
              조회. dart 와 동일 시그니처 - `market="US"` 자동 주입.

        Guide:
            - "US yield curve 영향" → ``c.macro("yield_curve")``.
            - "사용 가능 매크로 축" → ``c.macro()`` 빈 호출.

        AIContext:
            매크로 변수 회사 영향 질문 entry. axis 미정 시 가이드 반환 - AI 가 미지원 axis 추측 대신 빈 호출로 카탈로그 확인.

        LLM Specifications:
            AntiPatterns:
                - market="KR" 강제 시도 → 본 함수는 US 고정. KR 회사는 dart provider 사용.
                - overrides 무한 중첩 → Macro 가 dict 평탄화만 지원.
            OutputSchema:
                - Macro 결과 (axis 별 DataFrame 또는 dict).
            Prerequisites:
                - FRED / ECOS / KRX 데이터 셋업 (Macro 모듈 의존).
            Freshness:
                - Macro 모듈의 origin 별 freshness 위임 (FRED 일/월, 회사 변경 무관).
            Dataflow:
                - Macro(axis, target, market="US") → 본 함수 → axis 결과.
            TargetMarkets:
                - US (SEC EDGAR) 회사 매크로 매핑.
        """
        from dartlab.macro import Macro

        return Macro()(axis, target, market="US", overrides=overrides, company=self, **kwargs)

    # ── Phase 10 H2: story 2차 가공 직접 노출 ──

    def causalWeights(self) -> list[dict]:
        """6막 인과 가중치 (Phase 9 B2).

        Returns:
            인과 weight dict 리스트.

        Raises:
            없음.

        Example:
            >>> c = Company("AAPL")
            >>> c.causalWeights()

        SeeAlso:
            - ``dartlab.story.narrative.buildCausalWeights`` - 본 함수의 implementation.
            - ``valuationImpact`` - 본 가중치를 DCF override 로 변환.
            - ``storyTree`` - 가중치 적용한 3 trajectory DCF.

        Requires:
            - dartlab
            - polars

        Capabilities:
            - 본 회사의 story 6 막 (도입/전개/위기/반전/절정/결말) 각 막에 대한 인과 가중치
              산출. 매출/마진/투자/규제 등 driver 별 weight (총 1.0 normalize).

        Guide:
            - "이 회사 이야기의 핵심 driver" → 본 함수 결과 + ``storyTree`` 결합.

        AIContext:
            workbench narrative 분석 entry. AI 가 사용자에게 "이 회사 핵심 변수는 X" 답할 때 본 함수의 weight 인용.

        LLM Specifications:
            AntiPatterns:
                - weight 의 절대값 비교 X - 회사 간 비교는 정성적 해석만.
                - 가중치 합 1.0 가정 → narrative override 시 깨질 수 있음.
            OutputSchema:
                - list[dict] - 각 dict {"act": str, "driver": str, "weight": float}.
            Prerequisites:
                - finance + sections 데이터 (story.narrative 가 합산).
            Freshness:
                - 호출 시점 (finance + sections origin 의 latest 기준).
            Dataflow:
                - finance/sections → story.narrative.buildCausalWeights → 본 함수.
            TargetMarkets:
                - US (SEC EDGAR) story 매핑.
        """
        import importlib

        buildCausalWeights = importlib.import_module("dartlab.story.narrative").buildCausalWeights
        return buildCausalWeights(self, {})

    def valuationImpact(self) -> dict:
        """인과 체인 → DCF override 힌트 (Phase 9 B3).

        Returns:
            DCF override dict (revenueGrowth, margin, wacc 등).

        Raises:
            없음.

        Example:
            >>> c = Company("AAPL")
            >>> c.valuationImpact()

        SeeAlso:
            - ``causalWeights`` - 본 함수의 입력.
            - ``storyTree`` - 본 override 적용한 3 trajectory DCF.
            - ``dartlab.story.narrative.buildValuationImpact`` - implementation.

        Requires:
            - dartlab
            - polars

        Capabilities:
            - causalWeights 결과를 DCF 파라미터 (revenueGrowth / operatingMargin /
              wacc / terminalGrowth) override 후보로 변환. narrative-driven valuation.

        Guide:
            - "이 회사 narrative 가 valuation 어떻게 바꾸나" → 본 함수 + storyTree 비교.

        AIContext:
            DCF base case 와 narrative 반영 case 의 격차 설명에 본 dict 인용.

        LLM Specifications:
            AntiPatterns:
                - override 값을 절대 정답으로 가정 → narrative 자체가 가설. base/bull/bear 비교 의무.
            OutputSchema:
                - dict {"revenueGrowth": float, "operatingMargin": float, "wacc": float, ...}.
            Prerequisites:
                - causalWeights origin (finance + sections).
            Freshness:
                - 호출 시점.
            Dataflow:
                - finance/sections → causalWeights → buildValuationImpact → 본 함수.
            TargetMarkets:
                - US (SEC EDGAR) narrative-DCF 매핑.
        """
        import importlib

        _narrative = importlib.import_module("dartlab.story.narrative")
        return _narrative.buildValuationImpact(_narrative.buildCausalWeights(self, {}))

    def storyTree(self, *, basePeriod: str | None = None) -> dict:
        """3 trajectory DCF (Phase 10 G2).

        Args:
            basePeriod: 기준 fiscal period. None 이면 최신.

        Returns:
            ``{base, bull, bear}`` trajectory dict.

        Raises:
            없음.

        Example:
            >>> c = Company("AAPL")
            >>> c.storyTree()

        SeeAlso:
            - ``causalWeights`` / ``valuationImpact`` - 본 함수의 입력 가중치.
            - ``dartlab.story.dcf`` - 3 trajectory 계산 모듈.
            - ``narrativeDiff`` - 사용자 가설과 본 tree 비교.

        Requires:
            - dartlab
            - polars

        Capabilities:
            - base / bull / bear 3 시나리오 DCF 시뮬레이션. valuationImpact override 를
              ±1σ 변동시켜 시나리오 별 fair value 산출. basePeriod 미지정 시 최신 분기.

        Guide:
            - "이 회사 가치 시나리오 비교" → 본 함수 결과 dict 3 trajectory.
            - "지금 가격이 base 대비 어느 위치" → result["base"]["fairPrice"] / 현재가.

        AIContext:
            AI 가 "이 회사 비싸냐 싸냐" 답할 때 본 함수 base/bull/bear range 인용. 단일 값 X.

        LLM Specifications:
            AntiPatterns:
                - bull/bear range 좁다고 안전하다 결론 - narrative 가 우상향 편향이면 bear 도 낙관적.
                - basePeriod 가정 (예 분기 마지막) 없이 호출 → 최신 자동, 의도 명확하면 명시.
            OutputSchema:
                - dict {"base": {fairPrice, revenueGrowth, ...}, "bull": ..., "bear": ...}.
            Prerequisites:
                - causalWeights 산출 가능 (finance + sections).
            Freshness:
                - 호출 시점.
            Dataflow:
                - causalWeights → valuationImpact → DCF 3 시나리오 → 본 dict.
            TargetMarkets:
                - US (SEC EDGAR) 회사 valuation 매핑.
        """
        import importlib

        buildStoryTree = importlib.import_module("dartlab.story.storyTree").buildStoryTree
        return buildStoryTree(self, basePeriod=basePeriod)

    def narrativeDiff(self, *, claims: list[str] | None = None) -> list[dict]:
        """claim 제거 시 dFV 변화 (Phase 10 G3).

        Args:
            claims: 영향 분석 대상 claim 리스트. None 이면 전체.

        Returns:
            ``[{claim, dFV, ...}]`` 리스트.

        Raises:
            없음.

        Example:
            >>> c = Company("AAPL")
            >>> c.narrativeDiff(claims=["margin_expansion"])

        SeeAlso:
            - ``storyTree`` - claim 적용된 trajectory.
            - ``causalWeights`` - claim 의 사전 가중치.
            - ``dartlab.story.narrativeDiff.computeImpact`` - implementation.

        Requires:
            - dartlab
            - polars

        Capabilities:
            - 각 narrative claim 을 한 번씩 제거하고 다시 DCF 돌려 fair value 변화 (dFV)
              측정. claim 별 valuation 기여도 정량화. "이 claim 이 valuation 의 X% 설명".

        Guide:
            - "이 회사 valuation 의 핵심 claim 뭐냐" → 본 함수 결과 dFV 큰 순 정렬.

        AIContext:
            workbench 가 narrative 분해 답변 시 claim 별 dFV 인용 - AI 가 "margin expansion 이 valuation 의 30%" 류 정량 진술 가능.

        LLM Specifications:
            AntiPatterns:
                - claim list 일부만 넣고 "주요 claim" 결론 → 전체 list 필수.
                - dFV 의 절대값 외부 비교 → 회사 별 base FV 차이로 직접 비교 무의미.
            OutputSchema:
                - list[dict] - 각 {"claim": str, "dFV": float, "dFVpct": float, ...}.
            Prerequisites:
                - storyTree base trajectory + claims 카탈로그.
            Freshness:
                - 호출 시점.
            Dataflow:
                - claims → storyTree base ↔ claim-removed → dFV 계산 → 본 list.
            TargetMarkets:
                - US (SEC EDGAR) narrative valuation 매핑.
        """
        import importlib

        computeImpact = importlib.import_module("dartlab.story.narrativeDiff").computeImpact
        return computeImpact(self, claims=claims)

    # ── Phase 11 A1: EDGAR 상장사 검색 (DART sync) ──

    @staticmethod
    def listing(*, forceRefresh: bool = False) -> pl.DataFrame:
        """NASDAQ/NYSE 상장 기업 목록 (EDGAR universe).

        Args:
            forceRefresh: 캐시 무시 - 현재 EDGAR 는 자동 캐시라 noop.
                DartCompany.listing 과 시그니처 동기 목적.

        Returns:
            종목코드/회사명/시장구분/cik 컬럼 DataFrame.

        Raises:
            FileNotFoundError: EDGAR universe parquet 부재.

        Example:
            >>> Company.listing().head()

        SeeAlso:
            - ``search`` - keyword 부분 매칭 검색.
            - ``dart.providers.dart.company.Company.listing`` - KR 패리티.
            - ``dartlab.core.dataLoader.loadEdgarListedUniverse`` - origin.

        Requires:
            - dartlab
            - polars

        Capabilities:
            - EDGAR 상장 기업 universe parquet 을 폼별 정규화 컬럼 (종목코드/회사명/시장구분/cik) 으로
              반환. NASDAQ/NYSE/AMEX 통합. forceRefresh 인자는 dart 와 시그니처 동기용.

        Guide:
            - "전체 US 상장 종목 목록" → 본 함수.
            - "특정 회사 찾기" → ``search`` 더 빠름.

        AIContext:
            workbench universe 탐색 시 본 함수 origin. DataFrame 그대로 LLM 에 노출하면 토큰
            낭비 - ``head``/``filter`` 후 보내야.

        LLM Specifications:
            AntiPatterns:
                - 전체 universe 그대로 LLM 컨텍스트 주입 → ~10K 행 토큰 초과.
                - forceRefresh=True 가 실제 fetch 한다고 가정 - EDGAR 는 정적 parquet.
            OutputSchema:
                - pl.DataFrame - 컬럼 ["종목코드", "회사명", "시장구분", "cik"].
            Prerequisites:
                - data/edgar/listed.parquet (`scripts/build/buildEdgarUniverse.py` 산출).
            Freshness:
                - parquet 빌드 시점 (월 1 회 정도). SEC tickers.json 갱신 시 재빌드.
            Dataflow:
                - SEC tickers.json → buildEdgarUniverse → listed.parquet → loadEdgarListedUniverse → 본 함수.
            TargetMarkets:
                - US (SEC EDGAR) NASDAQ/NYSE/AMEX.
        """
        from dartlab.core.dataLoader import loadEdgarListedUniverse

        universe = loadEdgarListedUniverse()
        return universe.select(
            [
                pl.col("ticker").alias("종목코드"),
                pl.col("title").alias("회사명"),
                pl.col("exchange").alias("시장구분"),
                pl.col("cik"),
            ]
        )

    @staticmethod
    def search(keyword: str, *, limit: int | None = None) -> pl.DataFrame:
        """ticker / 회사명 검색. 대소무시 부분 매칭.

        Args:
            keyword: ticker 또는 회사명 부분.
            limit: 최대 행 수. None 이면 무제한.

        Returns:
            종목코드/회사명/시장구분/cik 컬럼 DataFrame.

        Raises:
            FileNotFoundError: EDGAR universe parquet 부재.

        Example:
            >>> Company.search("apple", limit=10)

        SeeAlso:
            - ``listing`` - 전체 universe.
            - ``dart.providers.dart.company.Company.search`` - KR 패리티 (회사명 한글 부분).

        Requires:
            - dartlab
            - polars

        Capabilities:
            - 3-단계 매칭 - (1) ticker 정확 (대문자) (2) ticker 부분 (3) 회사명 부분 (대소무시).
              앞 단계에서 매치 발견 시 뒤 단계 skip. limit 으로 head N.

        Guide:
            - "ticker 모르고 회사 이름만" → 본 함수 + 회사명 일부.
            - "유사 ticker 묶어 찾기" → 본 함수 + 짧은 prefix.

        AIContext:
            AI 가 사용자 입력 "Apple" / "AAPL" / "Inc" 등 모호한 키워드 받았을 때 본 함수로 후보 추출.
            여러 매치 시 첫 N 만 보고 사용자 확인.

        LLM Specifications:
            AntiPatterns:
                - limit 없이 흔한 단어 (예 "Inc", "Corp") 검색 → 수천 row 반환 → 토큰 폭증.
                - 한글 회사명 입력 → US universe 에는 없음 → 빈 결과.
            OutputSchema:
                - pl.DataFrame - 컬럼 ["종목코드", "회사명", "시장구분", "cik"]. 매치 없으면 빈 DF.
            Prerequisites:
                - listing 과 동일 (data/edgar/listed.parquet).
            Freshness:
                - listing 과 동일.
            Dataflow:
                - keyword → 3-단계 filter → universe → head(limit) → 본 함수.
            TargetMarkets:
                - US (SEC EDGAR).
        """
        from dartlab.core.dataLoader import loadEdgarListedUniverse

        kw = keyword.strip()
        if not kw:
            return (
                loadEdgarListedUniverse()
                .head(0)
                .select(
                    [
                        pl.col("ticker").alias("종목코드"),
                        pl.col("title").alias("회사명"),
                        pl.col("exchange").alias("시장구분"),
                        pl.col("cik"),
                    ]
                )
            )
        kw_upper = kw.upper()
        universe = loadEdgarListedUniverse()
        # ticker 매칭 (정확 우선)
        hit = universe.filter(pl.col("ticker") == kw_upper)
        if hit.height == 0:
            hit = universe.filter(pl.col("ticker").str.contains(kw_upper, literal=True))
        if hit.height == 0:
            # 회사명 매칭 (대소무시)
            hit = universe.filter(pl.col("title").str.to_lowercase().str.contains(kw.lower(), literal=True))
        result = hit.select(
            [
                pl.col("ticker").alias("종목코드"),
                pl.col("title").alias("회사명"),
                pl.col("exchange").alias("시장구분"),
                pl.col("cik"),
            ]
        )
        if limit is not None:
            result = result.head(limit)
        return result

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
            None - 브라우저가 자동으로 열림.

        Raises:
            OSError: 포트 점유 시.

        Example::

            c = Company("AAPL")
            c.view()             # localhost:8400 에서 뷰어 실행
            c.view(port=9000)    # 포트 변경

        LLM Specifications:
            AntiPatterns:
                - headless 환경 (CI / docker) 에서 호출 → 브라우저 launch 실패. notebooks/JupyterLab 전용.
                - 이미 점유된 포트 → OSError. caller 가 port 변경 의무.
            OutputSchema:
                - None - side effect (브라우저 자동 open).
            Prerequisites:
                - 로컬 표시 가능 환경 + `dartlab.providers._common.viewer` 의존.
            Freshness:
                - 호출 시점 즉시 (서버 별도 데이터 fetch X).
            Dataflow:
                - self.ticker → launchViewer → FastAPI 서버 + 브라우저 open.
            TargetMarkets:
                - US (SEC EDGAR) - viewer 는 ticker 별 디스패치.
        """
        from dartlab.providers._common.viewer import launchViewer

        launchViewer(self.ticker, port=port)

    def _buildFinanceSeries(self, *, freq: str = "Q", scope: str = "consolidated"):
        """[INTERNAL] EDGAR finance series-tuple 빌더.

        사용자 진입점은 ``c.panel("IS", freq=, scope=)`` 만이다 (api-contract).
        EDGAR 는 ``scope="separate"`` 미지원 (SEC 는 연결만 보고).
        ``freq="YTD"`` 도 미지원 - annual 로 fallback.

        Args:
            freq: ``"Q"`` (분기, 기본) / ``"Y"`` (연간) / ``"YTD"`` (annual fallback).
            scope: ``"consolidated"`` (기본) - separate 는 raise.

        Returns:
            ``(series, periods)`` 또는 None.
        """
        from dartlab.providers.edgar.builder.dataDispatcher import buildFinanceSeries

        return buildFinanceSeries(self, freq=freq, scope=scope)

    # c.BS / c.IS / c.CF / c.CIS property 제거 (Plan v10 P0 - api-contract).
    # 사용자는 c.panel("IS") / c.panel("IS", freq="Y") 사용.

    # c.SCE property 제거 (Plan v10 P1) - c.panel("SCE") 사용

    def _buildRatios(self) -> pl.DataFrame | None:
        """[INTERNAL] EDGAR 재무비율 DataFrame 빌더 - show("ratios") 가 호출."""
        from dartlab.providers.edgar.builder.dataDispatcher import buildRatios

        return buildRatios(self)

    # insights는 analysis 내부 - c.analysis("financial", "종합평가")로 접근

    @property
    def reportModel(self):
        """전문 리포트 계약 모델 - story 블록 + de-gate 밸류에이션을 thesis-led ReportModel(dict).

        랜딩 /report 가 **동일 계약**(contracts/reportModel.ts)을 소비하는 SSOT. self-calc 0.
        dart Company 와 동형 - buildReportModel 위임.

        Returns:
            CallableAccessor: 호출 시 ``_reportModelImpl`` 이 ReportModel dict
            (schemaVersion=2) 반환. 데이터 부족 시 {"skipped": True, ...}.

        Raises:
            없음 - 데이터 부족·빌드 실패는 skipped dict 로 반환.

        Example:
            >>> Company("AAPL").reportModel("valuation")["schemaVersion"]
            2

        SeeAlso:
            - ``dartlab.story.report.buildReportModel`` - backend SSOT.
            - ``story`` - 레거시 Story dataclass(공존).
        """
        from dartlab.core.dualAccess import CallableAccessor

        if "_reportModelAccessor" not in self._cache:
            self._cache["_reportModelAccessor"] = CallableAccessor(self._reportModelImpl, name="reportModel")
        return self._cache["_reportModelAccessor"]

    def _reportModelImpl(self, perspective: str = "full", *, basePeriod: str | None = None) -> dict:
        """reportModel 실제 구현 - buildReportModel(L3) 에 위임."""
        import importlib

        buildReportModel = importlib.import_module("dartlab.story.report").buildReportModel
        return buildReportModel(self, perspective, basePeriod=basePeriod)

    @property
    def story(self):
        """재무 검토 보고서 - dual access.

        ``c.story`` (Story 객체) 또는 ``c.story(section=...)`` (call) 양식 모두 지원.

        Returns:
            ``CallableAccessor`` - 14 섹션 보고서 빌더.

        Raises:
            없음.

        Example:
            >>> c = Company("AAPL")
            >>> c.story()              # 전체 검토서
            >>> c.story("수익성")       # 특정 섹션

        SeeAlso:
            - ``analysis`` - 14 섹션 raw 분석 결과 (본 함수가 합산).
            - ``dartlab.story.registry.buildStory`` - implementation.
            - ``dart.providers.dart.company.Company.story`` - KR 패리티.

        Requires:
            - dartlab
            - polars

        Capabilities:
            - 14 개 보고서 섹션 (수익구조/자금조달/자산구조/현금흐름/수익성/성장성/안정성/효율성/
              종합평가/이익품질/비용구조/자본배분/투자효율/재무정합성) 을 SEC EDGAR 데이터로
              구축. preset (executive/audit/credit/growth/valuation) 으로 톤 조절.

        Guide:
            - "이 회사 재무 통째 검토" → ``c.story()``.
            - "수익성만" → ``c.story("수익성")``.
            - "감사 관점 검토" → ``c.story(preset="audit")``.

        AIContext:
            ``ask`` workbench 가 본 함수 결과를 tool 결과로 받아 AI 답변. 단일 섹션 호출이 토큰 효율.
        """
        from dartlab.core.dualAccess import CallableAccessor

        if "_storyAccessor" not in self._cache:
            self._cache["_storyAccessor"] = CallableAccessor(self._storyImpl, name="story")
        return self._cache["_storyAccessor"]

    def _storyImpl(
        self,
        section: str | None = None,
        layout=None,
        helper: bool | None = None,
        *,
        type: str | None = None,
        template: str | None = None,
        detail: bool | None = None,
        basePeriod: str | None = None,
        hypothesis: str | None = None,
        preset: str | None = None,  # deprecated
        perspective: str | None = None,  # deprecated
    ):
        """재무제표 구조화 보고서 - 기업이야기꾼의 대본.

        Capabilities:
            - 14개 섹션 전체 보고서 (수익구조~재무정합성)
            - 단일 섹션 지정 가능
            - 4개 출력 형식 (rich, html, markdown, json)
            - 프리셋 지원 (executive/audit/credit/growth/valuation)

        Requires:
            데이터: 없음 (SEC EDGAR 자동 수집)

        AIContext:
            - ask() (dartlab.ask) 가 이 결과를 tool 로 소비해 AI 해석 생성
            - ask()에서 재무분석 컨텍스트로 활용

        Guide:
            - "Story the financials" → c.story()
            - "Revenue structure" → c.story("수익구조")
            - "Audit story" → c.story(preset="audit")

        SeeAlso:
            - analysis: 14축 개별 분석 (review가 내부적으로 소비)
            - insights: 7영역 등급 + 이상치 요약

        Args:
            section: 섹션명 ("수익구조" 등). None이면 전체.
            layout: StoryLayout 커스텀. None이면 기본.
            helper: True면 해석 힌트 텍스트 포함.
            preset: 프리셋 이름 (executive/audit/credit/growth/valuation).
            template: 스토리 템플릿 이름.
            detail: False면 요약만 표시.
            basePeriod: 기준 기간.

        Returns:
            Story - 구조화 보고서.

        Example::

            c = Company("AAPL")
            c.story()                # 전체 검토서
            c.story("수익성")         # 특정 섹션
            c.story(preset="audit")  # 감사 검토용
        """
        import importlib

        buildStory = importlib.import_module("dartlab.story.registry").buildStory

        return buildStory(
            self,
            section=section,
            layout=layout,
            helper=helper,
            type=type,
            template=template,
            detail=detail,
            basePeriod=basePeriod,
            hypothesis=hypothesis,
            preset=preset,
            perspective=perspective,
        )

    @property
    def analysis(self):
        """분석 엔진 실행 - dual access.

        Returns:
            ``CallableAccessor`` - 22 축 분석 엔트리.

        Raises:
            없음.

        Example:
            >>> c = Company("AAPL")
            >>> c.analysis()                            # 축 목록
            >>> c.analysis("financial", "수익성")        # 수익성 분석

        SeeAlso:
            - ``story`` - 22 축 결과를 보고서로 합산.
            - ``dartlab.analysis.financial.Analysis`` - 분석 backend SSOT.
            - ``dart.providers.dart.company.Company.analysis`` - KR 패리티.

        Requires:
            - dartlab
            - polars

        Capabilities:
            - 5 그룹 22 축 (financial 14 + valuation 1 + governance 3 + forecast 2 + macro 2)
              개별 분석 dispatch. axis 미지정 시 카탈로그 반환. 본 회사 자동 바인딩.

        Guide:
            - "수익성 분석" → ``c.analysis("financial", "수익성")``.
            - "가능 분석 축 목록" → ``c.analysis()`` 빈 호출.

        AIContext:
            workbench 가 분석 도구 dispatch 시 본 entry. 축 미지정 호출로 capability 먼저 확인.
        """
        from dartlab.core.dualAccess import CallableAccessor

        if "_analysisAccessor" not in self._cache:
            self._cache["_analysisAccessor"] = CallableAccessor(self._analysisImpl, name="analysis")
        return self._cache["_analysisAccessor"]

    def _analysisImpl(self, axis: str | None = None, sub: str | None = None, **kwargs):
        """분석 엔진 실행 - analysis()에 self를 바인딩 (내부 구현).

        Capabilities:
            - 22축 분석 (5 group)
              - financial (14): 수익구조, 자금조달, 자산구조, 현금흐름, 수익성, 성장성, 안정성, 효율성, 종합평가, 이익품질, 비용구조, 자본배분, 투자효율, 재무정합성
              - valuation (1): 가치평가
              - governance (3): 지배구조, 공시변화, 비교분석
              - forecast (2): 매출전망, 예측신호
              - macro (2): 매크로민감도, 밸류에이션밴드
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
            - "지배구조" → c.analysis("governance", "지배구조")

        SeeAlso:
            - story: 분석 결과를 보고서로 조합
            - insights: 재무 인사이트 (간편 요약)
            - ask: AI 기반 해석

        Args:
            axis: 그룹 이름 ("financial", "valuation", "governance", "forecast", "macro") 또는 축 이름. None이면 가이드.
            sub: 그룹 내 하위 축 이름 ("수익성", "가치평가", "매출전망", "지배구조" 등).
            **kwargs: 축별 추가 파라미터.

        Returns:
            분석 결과 객체 또는 축 목록 dict.

        Example::

            c = Company("AAPL")
            c.analysis()                            # 사용 가능한 축 목록 (22축)
            c.analysis("financial", "수익성")        # 수익성 분석
            c.analysis("valuation", "가치평가")       # 가치평가
            c.analysis("governance", "지배구조")      # 지배구조
            c.analysis("forecast", "매출전망")        # 매출전망
        """
        import importlib

        Analysis = importlib.import_module("dartlab.analysis.financial").Analysis

        _analysis = Analysis()
        if axis is None:
            return _analysis()
        if sub is not None:
            return _analysis(axis, sub, company=self, **kwargs)
        return _analysis(axis, company=self, **kwargs)

    def validateStory(self, overrides: dict | None = None) -> dict:
        """Damodaran 스토리 검증 - Possible / Plausible / Probable.

        Args:
            overrides: DCF override dict (선택).

        Returns:
            dict {precedents, plausibility, rules, overall}.

        Raises:
            없음.

        Example:
            >>> c = Company("AAPL")
            >>> c.validateStory()

        SeeAlso:
            - ``storyTree`` / ``causalWeights`` - 검증 대상 story.
            - ``dartlab.analysis.financial.storyValidation`` - 검증 backend.

        Requires:
            - dartlab
            - polars

        Capabilities:
            - Damodaran 의 3 단계 검증 - Possible (precedents) / Plausible (band) / Probable (rules).
              과거 동종 회사 사례 / valuation 범위 / valuation sins 룰 종합 후 overall severity 산출.

        Guide:
            - "이 가정이 그럴듯한가" → 본 함수 결과 plausibility band 확인.
            - "valuation 의 위험 신호" → result["rules"] severity = "critical".

        AIContext:
            AI 가 사용자의 valuation 가정 검토 시 본 함수 결과로 reality check. critical 이면 강한 경고.

        LLM Specifications:
            AntiPatterns:
                - overall "info" 결과를 "안전" 결론 → severity 는 룰 위반 부재일 뿐 valuation 정답 아님.
                - precedents 비교군 자동 선정 - 사용자가 명시 시 다른 결과 가능.
            OutputSchema:
                - dict {"precedents": list, "plausibility": dict, "rules": dict, "overall": str}.
            Prerequisites:
                - storyTree base trajectory + 동종 universe 데이터.
            Freshness:
                - 호출 시점.
            Dataflow:
                - storyTree → precedents+band+sins 3 분석 → severity 종합 → 본 함수.
            TargetMarkets:
                - US (SEC EDGAR) valuation 검증.
        """
        import importlib

        _sv = importlib.import_module("dartlab.analysis.financial.storyValidation")
        calcPlausibilityBand = _sv.calcPlausibilityBand
        calcStoryPrecedents = _sv.calcStoryPrecedents
        calcValuationSins = _sv.calcValuationSins

        precedents = calcStoryPrecedents(self)
        plausibility = calcPlausibilityBand(self)
        rules = calcValuationSins(self)

        order = {"info": 0, "warn": 1, "critical": 2}
        overall = "info"
        rule_sev = rules.get("severity", "info") if rules else "info"
        if order.get(rule_sev, 0) > order.get(overall, 0):
            overall = rule_sev

        return {
            "precedents": precedents,
            "plausibility": plausibility,
            "rules": rules,
            "overall": overall,
        }

    @property
    def credit(self):
        """독립 신용평가 - dual access.

        Returns:
            ``CallableAccessor`` - dCR 20단계 등급 빌더.

        Raises:
            없음.

        Example:
            >>> c = Company("AAPL")
            >>> c.credit()

        SeeAlso:
            - ``dartlab.credit.creditCompany`` - implementation.
            - ``dart.providers.dart.company.Company.credit`` - KR 패리티 (KIS/NICE 와 비교).

        Requires:
            - dartlab
            - polars

        Capabilities:
            - 본 회사를 dartlab 의 독립 dCR 20 단계 등급 (AAA→D) 으로 매핑. S&P/Moody 외부 등급 없이
              finance + leverage + cashflow 자체 분석. detail=True 시 sub-axis breakdown.

        Guide:
            - "이 회사 신용등급" → ``c.credit()`` 또는 ``c.credit("rating")``.
            - "등급 산정 근거" → ``c.credit(detail=True)``.

        AIContext:
            외부 신용평가 미상장/소형 회사도 본 함수로 동일 척도 비교 가능. AI 가 부도위험 답변 시 인용.
        """
        from dartlab.core.dualAccess import CallableAccessor

        if "_creditAccessor" not in self._cache:
            self._cache["_creditAccessor"] = CallableAccessor(self._creditImpl, name="credit")
        return self._cache["_creditAccessor"]

    def _creditImpl(self, axis: str | None = None, *, detail: bool = False, basePeriod: str | None = None):
        """독립 신용평가 - dCR 20단계 등급 (내부 구현)."""
        from dartlab.credit import creditCompany

        return creditCompany(self, axis=axis, detail=detail, basePeriod=basePeriod)

    def gather(self, axis: str | None = None, **kwargs):
        """외부 시장 데이터 수집 - gather()에 self.ticker를 바인딩.

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

        Returns
        -------
        pl.DataFrame | None
            axis=None (가이드):
                axis : str - 축 이름
                label : str - 한글 레이블
                description : str - 설명
                example : str - 사용 예시
            axis="price":
                date : date - 날짜
                open : float - 시가 (USD)
                high : float - 고가 (USD)
                low : float - 저가 (USD)
                close : float - 종가 (USD)
                volume : int - 거래량
            axis="news":
                title : str - 뉴스 제목
                link : str - 기사 URL
                pubDate : str - 발행일
            axis="macro":
                date : date - 날짜
                지표별 컬럼 : float - FRED 거시지표 값
            데이터 없으면 None.

        Raises:
            httpx.HTTPError: 외부 API 호출 실패.

        Example::

            c = Company("AAPL")
            c.gather()              # 사용 가능한 축 목록
            c.gather("price")       # Apple 주가 수집

        LLM Specifications:
            AntiPatterns:
                - 본 함수는 외부 API origin - rate limit / network 실패 가능. caller 가 retry 분기.
                - "price" 축 대량 종목 일괄 호출 → 외부 API 차단. 종목당 sequential.
            OutputSchema:
                - axis 별로 다름 - guide 시 dict / price 시 OHLCV DataFrame / news 시 metadata 등.
            Prerequisites:
                - 인터넷 + axis 별 origin 키 (FRED/yfinance/Naver/etc).
            Freshness:
                - 외부 origin 시점 (price 실시간 + 15 min, news 분 단위, FRED 일 단위).
            Dataflow:
                - getGatherProvider() → entry(axis, ticker, market="US") → 외부 API → 본 함수.
            TargetMarkets:
                - US (SEC EDGAR) - market="US" 자동 주입.
        """
        from dartlab.core.gatherProvider import getGatherProvider

        provider = getGatherProvider()
        if provider is None:
            return None
        return provider.entry(axis, self.ticker, market="US", **kwargs)

    def calendar(self, *, horizonDays: int = 30) -> "pl.DataFrame":
        """다가오는 정기공시 catalyst 일정 - EDGAR/SEC 시장.

        현재 정기공시 cycle 추론은 KR DART 전용 (분기/반기/사업보고서 패턴 기반).
        SEC 의 10-K/10-Q 패턴은 별도 추론기 필요 - 미구현. 빈 DataFrame 반환.
        DartCompany.calendar 와 시그니처 일치 (CompanyProtocol 일관성).

        Args:
            horizonDays: 미래 horizon (기본 30 일). 현재 미사용.

        Returns:
            빈 DataFrame (calendar SCHEMA 형식).

        Raises:
            없음.

        Example:
            >>> c = Company("AAPL")
            >>> c.calendar(horizonDays=60)

        SeeAlso:
            - ``dart.providers.dart.company.Company.calendar`` - KR 패리티 (real cycle 추론).
            - ``dartlab.providers.dart.ops.calendar.OUTPUT_SCHEMA`` - 공통 스키마.

        Requires:
            - dartlab
            - polars

        Capabilities:
            - DartCompany.calendar 와 동일 시그니처 보존용 stub. SEC 10-K/10-Q cycle 추론기 미구현
              상태라 빈 DataFrame 반환. CompanyProtocol 일관성 보장 목적.

        Guide:
            - "EDGAR catalyst 일정" → 본 함수 (현재 빈 결과 - 향후 SEC cycle 추론기 도입 후 구현).

        AIContext:
            AI 가 본 함수 결과 비어있어도 "데이터 없음" 으로 그대로 답해야 - 추정/허위 일정 답변 금지.

        LLM Specifications:
            AntiPatterns:
                - SEC 회사도 12-31 결산 가정해 분기 일정 추정 → fiscalYearEnd 다른 회사 false.
                - 빈 결과 → "공시 없음" 으로 잘못 해석. 본 함수가 미구현이라 빈 반환.
            OutputSchema:
                - pl.DataFrame (OUTPUT_SCHEMA) - 현 빈 행, 컬럼만 보존.
            Prerequisites:
                - 없음 (현재 stub).
            Freshness:
                - 현재 N/A. 향후 SEC submissions API 갱신 시점.
            Dataflow:
                - 현재 빈 → 향후 SEC submissions cycle 추론.
            TargetMarkets:
                - US (SEC EDGAR) - 향후 cycle 추론기 구현 영역.
        """
        from dartlab.providers.dart.ops.calendar import OUTPUT_SCHEMA

        return pl.DataFrame(schema=OUTPUT_SCHEMA)

    def filings(self) -> pl.DataFrame | None:
        """SEC 공시 문서 목록 - 10-K/10-Q 등 정기보고서 목록.

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
            pl.DataFrame - docId | filedAt | formType | ... 또는 None.

        Raises:
            없음.

        Example::

            c = Company("AAPL")
            c.filings()  # Apple SEC filing 목록

        LLM Specifications:
            AntiPatterns:
                - 전체 filings 그대로 AI 컨텍스트 노출 → 회사당 수백 건 → 토큰 폭증. formType 필터 의무.
                - filedAt 정렬 없이 사용 → SEC 응답이 순서 보장 X, caller 가 sort.
            OutputSchema:
                - pl.DataFrame [docId, filedAt, formType, accessionNo, ...] 또는 None.
            Prerequisites:
                - SEC submissions API origin (자동 cache).
            Freshness:
                - SEC submissions 갱신 시점 (실시간 ~ 분 단위).
            Dataflow:
                - SEC submissions API → docs.filings() → 본 함수.
            TargetMarkets:
                - US (SEC EDGAR) 정기/수시공시 목록.
        """
        return self._docs.filings()

    def refreshFromApi(self) -> int:
        """[사용자 선택 경로] SEC companyfacts API로 로컬 finance parquet 갱신.

        Capabilities:
            - SEC companyfacts per-ticker API 호출
            - 로컬 ``data/edgar/finance/{cik}.parquet`` 덮어쓰기
            - 캐시 무효화 → 다음 show/analysis 호출부터 새 데이터 사용

        Policy:
            dartlab 자체 파이프라인은 **SEC 벌크** (``companyfacts.zip`` daily
            + 분기 ``financial-statement-data-sets``) 를 primary 소스로 사용한다.
            이 메서드는 **자동 파이프라인·프리빌드·HF 배포가 사용하지 않는다** -
            사용자가 공시 당일 최신 분기를 즉시 반영하고 싶을 때만 명시적으로 호출.
            상세: ``engines.edgar`` 및 ``operation.apiContract`` "EDGAR 수집 경로".

        Requires:
            인터넷 연결 (data.sec.gov). User-Agent 헤더.

        AIContext:
            - 자동 호출 금지. 사용자가 "API로 새로고침" 같은 명시적 의도일 때만.

        Guide:
            - "최신 실적 반영해줘" → c.refreshFromApi()
            - "SEC에서 직접 다시 받아줘" → c.refreshFromApi()

        SeeAlso:
            - filings: 현재 보유 공시 목록 확인

        Returns:
            저장된 parquet 행 수. 실패 시 0.

        Raises:
            없음 (내부 IO 예외는 잡아서 0 반환).

        Example::

            c = Company("AAPL")
            c.refreshFromApi()  # SEC API로 즉시 최신화

        LLM Specifications:
            AntiPatterns:
                - 자동 파이프라인 안에서 호출 → SEC rate limit 위반. 사용자 즉시 새로고침만.
                - 본 함수 반환 0 = 실패 - caller 가 분기. exception 던지지 않음.
            OutputSchema:
                - int - 저장된 parquet 행 수 (성공) 또는 0 (실패).
            Prerequisites:
                - 인터넷 + data.sec.gov 접근 + SEC 표준 User-Agent.
            Freshness:
                - 호출 시점 SEC companyfacts API (분기 마감 후 ~45 일 latency).
            Dataflow:
                - SEC companyfacts API → EdgarClient → saveFinance → 본 parquet → 캐시 무효화.
            TargetMarkets:
                - US (SEC EDGAR) - 자체 벌크 vs API 두 origin 중 후자 (사용자 명시).
        """
        import polars as _pl

        from dartlab.core.edgarClient import EdgarClient, saveFinance

        cik = str(self.cik).zfill(10)
        client = EdgarClient()
        try:
            path = saveFinance(cik, client=client)
        except (OSError, ValueError, RuntimeError):
            return 0

        for key in list(self._cache.keys()):
            if key.startswith("_finance_") or key in ("_ratios", "_ratioSeries"):
                self._cache.pop(key, None)

        try:
            return _pl.read_parquet(path).height
        except (OSError, _pl.exceptions.PolarsError):
            return 0

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
        """SEC EDGAR filing 검색 - liveFilings 위임.

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
            pl.DataFrame - docId | filedAt | title | formType | docUrl | ...

        Raises:
            httpx.HTTPError: SEC EDGAR API 호출 실패.

        Example::

            c = Company("AAPL")
            c.disclosure()                        # 최근 1년 전체
            c.disclosure(type="10-K")             # 10-K만
            c.disclosure(keyword="earnings")      # 키워드 필터

        LLM Specifications:
            AntiPatterns:
                - DART finalOnly 인자 사용 시도 → EDGAR 는 무시 (raise X). 시그니처 호환 목적만.
                - type 단일 form 지정 - 여러 form 조합 시 liveFilings(forms=[...]) 직접 호출.
            OutputSchema:
                - pl.DataFrame [docId/filedAt/title/formType/docUrl/...] - liveFilings 와 동일.
            Prerequisites:
                - 인터넷 + SEC EDGAR submissions API.
            Freshness:
                - SEC submissions 실시간 (~분 단위).
            Dataflow:
                - 사용자 인자 → liveFilings(start, end, days, keyword, forms) → 본 함수.
            TargetMarkets:
                - US (SEC EDGAR) - DART 동등 disclosure 인터페이스 패리티.
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
        """SEC EDGAR 실시간 filing 목록 - OpenEdgar API 직접 조회.

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
            pl.DataFrame - docId | filedAt | title | formType | docUrl | ...

        Raises:
            httpx.HTTPError: SEC EDGAR API 호출 실패.

        Example::

            c = Company("AAPL")
            c.liveFilings()                           # 최근 filing 20건
            c.liveFilings(forms=["10-K"], limit=5)    # 10-K만 5건

        LLM Specifications:
            AntiPatterns:
                - limit 큰 값 (>100) → SEC API 응답 지연 + 토큰 비용 증가. 보통 20~50.
                - 동일 cacheKey 중복 호출 - 캐시 활용 OK. 다른 시간대 호출 시 cacheKey 자동 갱신.
            OutputSchema:
                - pl.DataFrame [docId, filedAt, title, formType, docUrl, indexUrl, market, ticker,
                  cik, accessionNo, filingUrl, filingIndexUrl, primaryDocument, reportDate].
            Prerequisites:
                - 인터넷 + SEC submissions API + EdgarClient.
            Freshness:
                - SEC submissions 실시간. cache 는 인스턴스 lifetime 동안만.
            Dataflow:
                - resolveDateWindow + forms → OpenEdgar(ticker).filings → filterFilingsByKeyword → 정규화 → head(limit).
            TargetMarkets:
                - US (SEC EDGAR) - SUPPORTED_REGULAR_FORMS 의 10-K/Q/8-K/DEF 14A 등.
        """
        del finalOnly  # EDGAR regular filings에는 finalOnly 개념이 없다.

        startDate, endDate = resolveDateWindow(start, end, days=days)
        normalizedForms = tuple(forms or SUPPORTED_REGULAR_FORMS)
        cacheKey = f"liveFilings:{startDate}:{endDate}:{limit}:{keyword}:{normalizedForms}"
        if cacheKey in self._cache:
            return self._cache[cacheKey]

        from dartlab.core.edgarClient import openEdgar
        from dartlab.core.messaging import progress

        progress(
            f"{self.corpName} 최신 공시 목록 조회 중... "
            f"(SEC EDGAR, {startDate}~{endDate}, forms={','.join(normalizedForms)})"
        )
        df = openEdgar()(self.ticker).filings(
            forms=list(normalizedForms),
            since=startDate,
            until=endDate,
        )
        if isEmptyDf(df):
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
        """filing 원문 읽기 - URL/accessionNo/DataFrame row로 SEC 문서 다운로드.

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
            dict - docId, market, title, docUrl, raw, text, truncated 키 포함.

        Raises:
            ValueError: filing URL/accessionNo 부재.

        Example::

            c = Company("AAPL")
            filings = c.liveFilings(forms=["10-K"], limit=1)
            result = c.readFiling(filings[0])
            _log.info(result["text"][:500])

        LLM Specifications:
            AntiPatterns:
                - maxChars 없이 10-K 호출 → 본문 1MB+ → 토큰 폭증. 항상 maxChars 명시.
                - filing 인자 dict 변형 (예 raw API 응답) → filingRecord 정규화 실패. liveFilings row 사용.
            OutputSchema:
                - dict {docId, market, title, docUrl, indexUrl, raw, text, truncated:bool}.
            Prerequisites:
                - 인터넷 + SEC Archives 접근 + filing URL 또는 accessionNo.
            Freshness:
                - SEC filed 시점 (한 번 filed 후 immutable).
            Dataflow:
                - filing 인자 → URL 정규화 → _downloadFilingSource → _htmlToText → truncate → 본 dict.
            TargetMarkets:
                - US (SEC EDGAR) Archives 본문.
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

        from dartlab.core.edgarClient import downloadFilingSource as _downloadFilingSource
        from dartlab.core.edgarClient import htmlToText as _htmlToText
        from dartlab.core.messaging import progress

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
        """topic 목록 요약 - topic/source/blocks/periods DataFrame.

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
            pl.DataFrame - topic | source | blocks | periods.

        Raises:
            없음.

        Example::

            c = Company("AAPL")
            c.topics  # Apple 전체 topic 목록

        LLM Specifications:
            AntiPatterns:
                - 전체 DataFrame 그대로 LLM 컨텍스트 - 보통 50~100 행이라 OK 지만 source 필터로 줄이는 게 효율.
                - blocks/periods 정수 → topic 깊이 단순 비교 가능, 하지만 docs vs finance 척도 다름.
            OutputSchema:
                - pl.DataFrame [topic, source, blocks:int, periods:int].
            Prerequisites:
                - companyfacts + 10-K sections (둘 다 부재면 빈 DF).
            Freshness:
                - finance/docs 갱신 시점.
            Dataflow:
                - finance.{BS,IS,CF,CIS,ratios} + docs.sections.topic → 합산 + 정렬 → 본 함수.
            TargetMarkets:
                - US (SEC EDGAR) 10-K/10-Q topic 카탈로그.
        """
        cacheKey = "_topicsDataFrame"
        if cacheKey in self._cache:
            return self._cache[cacheKey]

        ordered: list[str] = []
        seen: set[str] = set()

        # 1. finance 제표 먼저
        for stmt in ("BS", "IS", "CF", "CIS"):
            if getattr(self._finance, stmt) is not None:
                ordered.append(stmt)
                seen.add(stmt)

        if self._finance.ratioSeries is not None and "ratios" not in seen:
            ordered.append("ratios")
            seen.add("ratios")

        # 2. docs topics - form별 정렬 (10-K → 10-Q → 20-F → 기타)
        sec = self._docs.sections
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

    @property
    def panel(self):
        """공시 수평화 보드 - 잡는 순간 item × 기간 wide DataFrame (EDGAR panel, US 기본).

        DART ``c.panel`` 의 EDGAR 미러. SEC 10-K/10-Q/20-F 의 item(섹션·표·서술)을 cross-market
        ``PANEL_SCHEMA`` 위에서 항목 × 기간 wide 로 수평화한 보드 (``providers.edgar.panel`` 의 ``Panel``
        기본 ``marketNs="us"``). artifact 는 ``edgar.panel.build`` 가
        SEC full-submission text 를 메모리로 fetch 해 직접 생산(``data/edgar/panel/{ticker}.parquet``).
        원본 ``.txt`` 저장과 별도 셀 artifact 는 없다. native 재무 payload 는 같은 panel row 에 보존한다.
        ``c.panel`` 자체가 ``pl.DataFrame``
        (Panel subclass) - shape/filter 등 polars 연산 그대로. ``c.panel("Risk")`` 로 섹션 행 검색,
        소문자 ``c.panel("is")`` 는 panel payload native, ``c.panel("IS")`` 같은 대문자 강한 소스는
        companyfacts(내부 finance dispatch)로 위임.

        Args:
            없음 (property - self.ticker 사용).

        Returns:
            ``Panel`` 인스턴스(= wide ``pl.DataFrame``). ``c.panel`` 자체가 wide, ``c.panel(key)`` 로
            섹션 검색 / 강한 소스(companyfacts) 주입.

        Raises:
            없음 - artifact 부재 시 빈 DataFrame.

        Example:
            >>> c = Company("AAPL")
            >>> c.panel.shape                          # wide (item × period) - DataFrame 그대로  # doctest: +SKIP
            >>> c.panel("Risk")                        # 섹션명/itemId 행 (raw 공시)  # doctest: +SKIP
            >>> c.panel("IS")                          # 강한 소스 - companyfacts 위임 (내부 finance)  # doctest: +SKIP
            >>> c.panel.search("supply chain")         # 본문 전체검색  # doctest: +SKIP

        SeeAlso:
            - ``providers.edgar.panel.Panel`` - 반환 본체 (pl.DataFrame subclass + __call__, US 기본).
            - ``providers.edgar.panel.build`` - SEC text → panel 단일 artifact + native payload 생산.
            - ``_showImpl`` - 강한 소스(companyfacts finance) dispatch - c.panel 이 주입 재사용 (내부 머신러리).

        Requires:
            - data/edgar/panel/{ticker}.parquet (사전빌드 artifact, edgar.panel.build).

        Capabilities:
            - 한 회사 공시를 item × 기간 wide 로 - 잡는 순간 DataFrame, callable 로 섹션·강한 소스 라우팅.

        Guide:
            - ``c.panel`` 잡으면 wide. ``c.panel("Risk")`` 섹션 검색. 재무는 소문자 native, 대문자 finance.

        AIContext:
            - 상태 없는 lazy read - 매 접근 새 Panel (누적 0). contentRaw 는 외부 untrusted.

        When:
            - 한 회사의 공시 수평화 보드가 EDGAR Company 흐름에서 필요할 때.

        How:
            - self.ticker → Panel(ticker) + _showFn(=_showImpl)/_strongFn(=isStrongTopic) 주입.

        LLM Specifications:
            AntiPatterns:
                - c.panel 결과 캐싱 강제 금지 - 상태 없는 lazy(누적 0).
                - native is/bs/cf 를 별도 셀 artifact 로 기대 금지 - panel 단일 artifact payload 에서 분해.
            OutputSchema:
                - ``Panel`` (wide DataFrame subclass + callable 검색).
            Prerequisites:
                - edgar panel artifact.
            Freshness:
                - 매 접근 read.
            Dataflow:
                - self.ticker → Panel(wide, us) + _nativeFn/_showFn/_strongFn 주입.
            TargetMarkets:
                - US (EDGAR).
        """
        from dartlab.providers.edgar.builder.dataDispatcher import isStrongTopic
        from dartlab.providers.edgar.panel import Panel as _Panel
        from dartlab.providers.edgar.panel.native import readNative

        p = _Panel(self.ticker)
        # facade 주입 (DI, cycle 0) - panel 패키지는 finance 를 import 안 하고 주입된 callable 만 호출.
        #   _nativeFn : is/bs/cf/ratios = panel 단일 artifact payload read-time 분해.
        #   _showFn   : IS/BS/CF/RATIOS = finance(companyfacts) 위임 (내부 _showImpl).
        #   _strongFn : finance 강한 소스 판정(isStrongTopic).
        p._nativeFn = lambda statement, freq, scope, periods: readNative(
            self.ticker,
            statement=statement,
            freq=freq,
            scope=scope,
            periods=periods,
        )
        p._showFn = self._showImpl
        p._strongFn = isStrongTopic
        return p

    def _showImpl(
        self,
        topic: str,
        block: int | None = None,
        *,
        period: str | list[str] | None = None,
        raw: bool = False,
        asOf: str | None = None,
        **_kw: Any,
    ) -> pl.DataFrame | None:
        """topic 데이터 조회 - sections 사상의 핵심 소비 경로 (내부 구현).

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
            - "재무상태표 보여줘" → c.panel("BS")
            - "리스크 팩터 내용 보여줘" → c.panel("risk") 또는 c.panel("10-K::item1ARiskFactors")
            - "2024년 손익만 보고 싶어" → c.panel("IS", period="2024")

        SeeAlso:
            - select: show() 결과에서 행/열 필터
            - trace: topic 데이터 출처 추적
            - sections: 전체 수평화 보드
            - topics: 사용 가능한 topic 목록

        Args:
            topic: topic 이름 (BS, IS, 10-K::item1Business, risk, mdna 등).
            block: blockOrder 인덱스. None이면 블록 목차.
            period: 특정 기간 필터. 리스트면 세로 뷰 (기간 x 항목).

        Returns
        -------
        pl.DataFrame | None
            finance topic (IS/BS/CF/CIS):
                account : str - 계정 식별자 (snakeId)
                2024, 2023, ... : float - 연간 값 (USD)
            ratios topic:
                account : str - 비율명
                2024, 2023, ... : float - 비율값 (%, 배)
            notes topic (inventory, borrowings 등):
                항목 : str - 세부 항목명
                연도 컬럼 : float - 금액 (USD)
            docs topic (10-K 항목):
                block 미지정: block : int, title : str - 블록 목차
                block 지정: 기간 컬럼에 텍스트 내용
            데이터 없으면 None.

        Example::

            c = Company("AAPL")
            c.panel("BS")                          # 재무상태표
            c.panel("10-K::item1ARiskFactors")     # Risk Factors 텍스트
            c.panel("risk")                        # 위와 동일 (alias)
            c.panel("IS", period="2024")           # 2024년만 필터
        """
        from dartlab.providers.edgar.builder.dataDispatcher import showImpl

        result = showImpl(self, topic, block, period=period, raw=raw, **_kw)
        if asOf is None or result is None:
            return result
        return _filterPeriodColumnsByAsOf(result, asOf)

    @staticmethod
    def _transposeToVertical(wide: pl.DataFrame, periods: list[str]) -> pl.DataFrame | None:
        from dartlab.providers.edgar.builder.dataDispatcher import transposeToVertical

        return transposeToVertical(wide, periods)

    def _buildBlockIndex(self, topicRows: pl.DataFrame) -> pl.DataFrame:
        """topic의 블록 목차 DataFrame."""
        from dartlab.providers.edgar.builder.dataDispatcher import buildBlockIndex

        return buildBlockIndex(topicRows)

    @property
    def select(self):
        """``show()`` 결과에서 행/열 필터 - dual access proxy.

        Returns:
            ``CallableAccessor`` - call/attr form 둘 다 ``_selectImpl`` 호출. ``SelectResult``
            반환. 상세는 ``_selectImpl`` docstring.

        Example:
            >>> c = Company("AAPL")
            >>> c.select("IS", ["sales"])    # call form
            >>> c.select.IS(["sales"])       # attr form

        Raises:
            없음 (해당 topic 부재 시 ``_selectImpl`` 이 None 반환).

        SeeAlso:
            - ``_selectImpl`` - 실제 구현.
            - ``show`` - 본 함수의 입력 소스.
            - ``dartlab.frame.select.SelectResult`` - 반환 객체 + ``.chart()`` 체이닝.

        Requires:
            - dartlab
            - polars

        Capabilities:
            - show() 결과에서 indList (행/항목) × colList (열/기간) 동시 필터. SelectResult 로 감싸
              ``.chart()`` / export 체이닝. strict=True 시 매치 0 면 ValueError.

        Guide:
            - "Revenue 만 2024" → ``c.select("IS", "Revenue", "2024")``.
            - "여러 계정 + 여러 연도" → ``c.select("IS", ["Revenue", "Net Income"], ["2024", "2023"])``.

        AIContext:
            AI 가 show() 결과 전부 노출 비용 회피용 - 필요 행/열만 정밀 추출 후 LLM 컨텍스트.
        """
        from dartlab.core.dualAccess import CallableAccessor

        if "_selectAccessor" not in self._cache:
            self._cache["_selectAccessor"] = CallableAccessor(self._selectImpl, name="select")
        return self._cache["_selectAccessor"]

    def _selectImpl(
        self,
        topic: str,
        indList: str | list[str] | None = None,
        colList: str | list[str] | None = None,
        *,
        freq: str = "Q",
        scope: str = "consolidated",
        strict: bool = True,
    ):
        """show() 결과에서 행/열 필터 - 특정 계정 x 특정 기간 추출 (내부 구현).

        Capabilities:
            - show() 결과에서 행(항목)과 열(기간) 동시 필터
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
            indList: 행 필터 - 항목 문자열 또는 리스트.
            colList: 열 필터 - 기간 문자열 또는 리스트.

        Returns
        -------
        SelectResult
            show()와 동일 컬럼 구조에서 indList/colList로 필터된 행/열.
            .chart() 체이닝으로 시각화 가능.
            내부 DataFrame 접근: result.df (pl.DataFrame).
            행 매칭 실패 시 ValueError (strict=True).

        Example::

            c = Company("AAPL")
            c.select("BS", "Total Assets", "2024")
            c.select("IS", ["Revenue", "Net Income"], ["2024", "2023"])
        """
        from dartlab.frame.select import SelectResult
        from dartlab.providers._common.show import selectFromShow

        # show() 가 ValueError 발생하면 그대로 propagate (silent None 차단)
        try:
            df = self._showImpl(topic)
        except (ValueError, KeyError):
            if strict:
                raise
            return None
        if df is None or not isinstance(df, pl.DataFrame):
            if not strict:
                return None
            raise ValueError(
                f"'{topic}' topic 의 데이터를 가져올 수 없습니다 (EDGAR). "
                f"topic 이름을 확인하거나 c.panel('{topic}') 로 직접 호출해보세요."
            )
        if isinstance(indList, str):
            indList = [indList]
        if isinstance(colList, str):
            colList = [colList]

        # 빈 indList → 명시적 안내
        if indList is not None and len(indList) == 0:
            if not strict:
                return None
            raise ValueError(
                "select 의 indList (행 필터) 가 비어 있습니다. "
                "필터링할 항목을 1개 이상 전달하세요. 예: c.select('IS', ['Revenue'])"
            )

        filtered = selectFromShow(df, indList, colList)
        if filtered is None:
            if not strict:
                return None
            # silent None 대신 명시적 ValueError
            available = []
            try:
                if df.width > 0:
                    first_col = df.columns[0]
                    available = df[first_col].drop_nulls().to_list()[:15]
            except (AttributeError, IndexError, TypeError):
                pass
            ind_str = indList if indList else colList
            hint = f"\n  사용 가능한 행 일부: {', '.join(str(a) for a in available)}" if available else ""
            raise ValueError(
                f"'{topic}' topic 에서 {ind_str} 를 찾을 수 없습니다 (EDGAR).{hint}\n"
                f"  c.panel('{topic}') 로 전체 행을 확인하세요."
            )
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
        """topic 데이터 출처 추적 - source provenance 확인.

        Capabilities:
            - topic 데이터가 docs/finance 중 어디서 왔는지 추적
            - 선택 근거(whySelected), 우선순위, 커버리지 정보 포함

        Requires:
            데이터: 없음 (SEC EDGAR 자동 수집)

        AIContext:
            - 데이터 신뢰성 검증에 활용 - 출처와 커버리지 확인

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
            dict - topic, primarySource, whySelected, availableSources 등. 없으면 None.

        Raises:
            없음 (데이터 부재 시 None 반환).

        Example:
            >>> c = Company("AAPL")
            >>> c.trace("BS")                          # finance 출처 확인
            >>> c.trace("10-K::item1ARiskFactors")     # docs 출처 확인

        LLM Specifications:
            AntiPatterns:
                - 본 함수 결과 없이 show() 값만 인용 → AI 환각 위험. 데이터 origin 명시 의무.
                - period 필터는 트레이스 결과에 metadata 만 - 실 row 필터링은 show() 가 처리.
            OutputSchema:
                - dict {topic, period, chapter, label, primarySource, fallbackSources,
                  selectedPayloadRef, availableSources:list, whySelected} 또는 None.
            Prerequisites:
                - show 와 동일 (finance/docs origin).
            Freshness:
                - 호출 시점 (sections + finance index 기준).
            Dataflow:
                - topic → alias 해석 → finance 우선 → docs fallback → source priority 결정 → 본 dict.
            TargetMarkets:
                - US (SEC EDGAR) provenance.
        """
        topic = _TOPIC_ALIASES.get(topic, topic)
        if topic in _FINANCE_TOPICS:
            df = getattr(self._finance, topic)
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
            rs = self._finance.ratioSeries
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

        sec = self._docs.sections
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
        """topic별 메타데이터 인덱스 - chapter/label/kind/source/periods 보드.

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
            pl.DataFrame - ``chapter | topic | label | kind | source | periods | shape | preview``.

        Raises:
            없음 (데이터 부재 시 빈 DataFrame).

        Example:
            >>> c = Company("AAPL")
            >>> c.index  # Apple 전체 topic 인덱스 보드

        LLM Specifications:
            AntiPatterns:
                - preview 컬럼을 본문 대용으로 사용 X - 100 자 미만 잘림. 실 본문은 show() 호출.
                - source 컬럼은 origin priority 결정 후 결과 - 미정의 시 None.
            OutputSchema:
                - pl.DataFrame [chapter, topic, label, kind, source, periods, shape, preview] 또는 빈.
            Prerequisites:
                - topics + trace + finance/docs sections.
            Freshness:
                - 호출 시점 (cached after first build).
            Dataflow:
                - topics → trace 별 source → finance/docs branching → shape/preview 계산 → 본 DF.
            TargetMarkets:
                - US (SEC EDGAR) topic 메타 보드.
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
                df = getattr(self._finance, topic)
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
                rs = self._finance.ratioSeries
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
                sec = self._docs.sections
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
        from dartlab.providers.edgar.builder.dataDispatcher import applyPeriodFilter

        return applyPeriodFilter(payload, period)

    @staticmethod
    def _shapeStr(df: pl.DataFrame | None) -> str:
        from dartlab.providers.edgar.builder.dataDispatcher import shapeStr

        return shapeStr(df)

    @staticmethod
    def _periodsStr(df: pl.DataFrame | None) -> str:
        from dartlab.providers.edgar.builder.dataDispatcher import periodsStr

        return periodsStr(df)

    @staticmethod
    def _previewFinance(df: pl.DataFrame | None) -> str:
        from dartlab.providers.edgar.builder.dataDispatcher import previewFinance

        return previewFinance(df)

    @staticmethod
    def _previewDocsCell(topicRows: pl.DataFrame, periodCols: list[str]) -> str:
        from dartlab.providers.edgar.builder.dataDispatcher import previewDocsCell

        return previewDocsCell(topicRows, periodCols)

    def diff(
        self,
        topic: str | None = None,
        fromPeriod: str | None = None,
        toPeriod: str | None = None,
    ) -> pl.DataFrame | None:
        """기간간 텍스트 변경 비교 - 공시 서술형 diff.

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
            pl.DataFrame - 변경 요약/이력/줄단위 diff. 없으면 None.

        Raises:
            없음.

        Example::

            c = Company("AAPL")
            c.diff()                                          # 전체 변경 요약
            c.diff("10-K::item1ARiskFactors")                 # Risk Factors 변경 이력
            c.diff("10-K::item7Mdna", "2023", "2024")         # MD&A 줄 단위 diff

        LLM Specifications:
            AntiPatterns:
                - 줄 단위 diff (3-인자 호출) 결과를 그대로 LLM 컨텍스트 → 거대 본문 토큰 폭증. 변경 줄만 추출.
                - period 라벨 형식 변형 ("2023Q4" vs "2023") 매칭 X - sections 컬럼명 일치 의무.
            OutputSchema:
                - pl.DataFrame - 호출 모드에 따라 다름: (1) 전체 요약 (2) topic 이력 (3) 줄 단위 diff.
            Prerequisites:
                - docs.sections (10-K/10-Q 본문 + period 컬럼).
            Freshness:
                - sections 갱신 시점.
            Dataflow:
                - docs.sections → 모드 별 diff 함수 (summary/history/lineDiff) → 본 함수.
            TargetMarkets:
                - US (SEC EDGAR) 10-K/Q 변경 추적.
        """
        from dartlab.providers._common.diff import (
            diffSummaryDataFrame,
            lineDiffDataFrame,
            sectionsDiff,
            topicHistoryDataFrame,
        )

        docsSections = self._docs.sections
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
        """공시 텍스트 키워드 빈도 추이 - topic x period x keyword 히트맵.

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
            pl.DataFrame - topic | period | keyword | count. 없으면 None.

        Raises:
            없음.

        Example::

            c = Company("AAPL")
            c.keywordTrend("AI")                              # AI 키워드 추이
            c.keywordTrend(keywords=["AI", "supply chain"])   # 복수 키워드
            c.keywordTrend()                                  # 내장 키워드 전체

        LLM Specifications:
            AntiPatterns:
                - 짧은 키워드 (예 "AI") → 단어 경계 무시 매칭 - "RAID" 도 hit. 정확 매칭 의무 시 정규식.
                - 빈도 절대값 비교 X - 본문 길이 차이 무시. 정규화 (per 1k tokens) 별도.
            OutputSchema:
                - pl.DataFrame [topic, period, keyword, count] 또는 None.
            Prerequisites:
                - docs.sections (10-K/10-Q text 본문).
            Freshness:
                - sections 갱신 시점.
            Dataflow:
                - docs.sections + keywords → keywordFrequency → 본 DF.
            TargetMarkets:
                - US (SEC EDGAR) 10-K/Q 텍스트 분석.
        """
        from dartlab.providers._common.diff import keywordFrequency

        docsSections = self._docs.sections
        if docsSections is None:
            return None
        kws = None
        if keyword:
            kws = [keyword]
        elif keywords:
            kws = keywords
        return keywordFrequency(docsSections, keywords=kws)

    def news(self, *, days: int = 30) -> pl.DataFrame:
        """최근 뉴스 수집 - 종목 관련 뉴스 DataFrame.

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
            pl.DataFrame - 뉴스 제목, 날짜, URL 등 포함.

        Raises:
            httpx.HTTPError: 외부 뉴스 API 호출 실패.

        Example::

            c = Company("AAPL")
            c.news()           # 최근 30일 뉴스
            c.news(days=7)     # 최근 7일

        LLM Specifications:
            AntiPatterns:
                - 본문 그대로 인용 → external untrusted 룰 위반. wrapExternalInResult 마커 후 검증 인용.
                - days 큰 값 (>90) → API rate limit / pagination 비용.
            OutputSchema:
                - pl.DataFrame - 뉴스 제목/날짜/URL/요약 컬럼. provider 부재 시 None.
            Prerequisites:
                - 인터넷 + 뉴스 origin (gatherProvider - Naver/Yahoo/etc).
            Freshness:
                - 외부 origin 실시간 (분 단위).
            Dataflow:
                - getGatherProvider().news(ticker, market="US", days) → 본 함수.
            TargetMarkets:
                - US (SEC EDGAR) - ticker 기반, English news 위주.
        """
        from dartlab.core.gatherProvider import getGatherProvider

        provider = getGatherProvider()
        return provider.news(self.ticker, market="US", days=days) if provider else None

    def watch(
        self,
        topic: str | None = None,
    ) -> pl.DataFrame | None:
        """공시 변화 감지 - 중요도 스코어링 기반 변화 요약.

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
            pl.DataFrame - topic | score | summary 등. 없으면 None.

        Raises:
            없음.

        Example::

            c = Company("AAPL")
            c.watch()                              # 전체 topic 중요도 순 요약
            c.watch("10-K::item1ARiskFactors")     # Risk Factors 상세

        LLM Specifications:
            AntiPatterns:
                - score 임계 hard-code 후 "큰 변화" 결론 X - 회사별 base score 분포 다름.
                - 결과 None ≠ "변화 없음" - sections 부재로 분석 불가일 수 있음.
            OutputSchema:
                - pl.DataFrame [topic, score, summary, fromPeriod, toPeriod, ...] 또는 None.
            Prerequisites:
                - docs.sections (10-K/10-Q 본문).
            Freshness:
                - sections 갱신 시점.
            Dataflow:
                - scan.watch.scanner.scanCompany(self, topic) → toDataframe → 본 함수.
            TargetMarkets:
                - US (SEC EDGAR) 공시 변화 감지.
        """
        import importlib

        scanner = importlib.import_module("dartlab.scan.watch.scanner")
        result = scanner.scanCompany(self, topic=topic)
        if result is None:
            return None
        return result.toDataframe()

    # ── AI 분석 ──

    def ask(
        self,
        question: str,
        *,
        provider: str | None = None,
        model: str | None = None,
        stream: bool = False,
        reflect: bool = False,
        **kwargs,
    ) -> str:
        """LLM에게 이 기업에 대해 질문 - 엔진 계산 결과 기반 AI 해석.

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
            model: 모델명. None이면 provider 최신 기본값.
            stream: 스트리밍 출력 여부.
            reflect: 자기 반성 모드 (답변 품질 자가 검증).

        Returns:
            str - LLM 응답 텍스트. ``stream=True`` 면 ``Generator[str]``.

        Raises:
            ValueError: provider/model 미설정 + 환경변수 키 부재.
            RuntimeError: LLM API 호출 실패.

        Example:
            >>> c = Company("AAPL")
            >>> c.ask("What are the key risks?")
            >>> c.ask("Revenue trend analysis", provider="openai")

        LLM Specifications:
            AntiPatterns:
                - 응답 직접 외부 인용 → AI 환각 검증 의무. dartlab tool 결과 인용만 신뢰.
                - reflect=True 가 항상 더 정확 X - 시간/토큰 비용 2 배. 중요 질문만.
                - stream=True 결과를 list() 로 즉시 수집 → 메모리 부담. 사용자 출력 stream 목적이면 그대로.
            OutputSchema:
                - str (stream=False) 또는 Generator[str] (stream=True).
            Prerequisites:
                - LLM API 키 (DARTLAB_OPENAI_API_KEY 또는 ANTHROPIC_API_KEY 환경변수).
                - dartlab ai/kernel.ask 모듈.
            Freshness:
                - LLM 응답 시점 + 본 회사 데이터 (sections+finance) freshness 의 min.
            Dataflow:
                - question + self.stockCode → ai.kernel.ask → tool calling → 본 함수.
            TargetMarkets:
                - US (SEC EDGAR) - workbench evidence + ask 인터페이스.
        """
        import importlib

        _ask = importlib.import_module("dartlab.ai.kernel").ask
        return _ask(
            question,
            stockCode=self.stockCode,
            provider=provider,
            model=model,
            stream=stream,
            reflect=reflect,
            **kwargs,
        )

    @property
    def _report(self):
        """[INTERNAL] EDGAR report 백엔드 - XBRL 기반. 사용자 API: c.panel(...)."""
        if self._reportAccessor is None:
            from dartlab.providers.edgar.accessor.reportAccessor import _ReportAccessor

            self._reportAccessor = _ReportAccessor(self)
        return self._reportAccessor

    @property
    def report(self):
        """EDGAR report accessor.

        Returns:
            _ReportAccessor: EDGAR XBRL 기반 report accessor.

        Raises:
            없음.

        Example:
            >>> c = Company("AAPL")
            >>> c.report is not None
            True
        """
        return self._report

    # ── DartCompany 동기화 메소드 (test_protocol 방어막) ──
    # 아래 메소드는 DartCompany와 인터페이스를 맞추기 위해 존재한다.
    # DART report 전용 데이터가 필요한 경우 None/빈값을 반환한다.

    # ── Properties (데이터 위임) ──

    @property
    def contextSlices(self) -> pl.DataFrame | None:
        """LLM context window 단위 슬라이스.

        Returns:
            슬라이스 DataFrame 또는 None.

        Raises:
            없음.

        Example:
            >>> c.contextSlices

        LLM Specifications:
            AntiPatterns:
                - 슬라이스 그대로 LLM 컨텍스트 → 회사 한 명당 수십 슬라이스 → 토큰 부담. 필요한 topic 만 필터.
                - 슬라이스 ID 의 안정성 가정 X - 본 회사 sections 갱신 시 ID 재산정.
            OutputSchema:
                - pl.DataFrame [sliceId, topic, period, text, tokenCount] 또는 None.
            Prerequisites:
                - docs.sections + slicer (LLM context budget 적용 chunking).
            Freshness:
                - sections 갱신 시점.
            Dataflow:
                - docs.sections → docs.contextSlices accessor → 본 property.
            TargetMarkets:
                - US (SEC EDGAR) 10-K/Q LLM RAG.
        """
        return self._docs.contextSlices if hasattr(self._docs, "contextSlices") else None

    @property
    def retrievalBlocks(self) -> pl.DataFrame | None:
        """RAG 검색용 chunk 블록.

        Returns:
            ``block_id/text/topic/period`` 컬럼 DataFrame 또는 None.

        Raises:
            없음.

        Example:
            >>> c.retrievalBlocks

        LLM Specifications:
            AntiPatterns:
                - block_id 의 안정성 가정 X - sections 갱신 시 재산정.
                - 본 블록을 벡터 임베딩 사전 계산 가정 X - provider 별 별도 처리.
            OutputSchema:
                - pl.DataFrame [block_id, text, topic, period] 또는 None.
            Prerequisites:
                - docs.sections + retrievalBlocks accessor.
            Freshness:
                - sections 갱신 시점.
            Dataflow:
                - docs.sections → 청킹 → 본 property.
            TargetMarkets:
                - US (SEC EDGAR) 10-K/Q RAG 검색 인덱스.
        """
        return self._docs.retrievalBlocks if hasattr(self._docs, "retrievalBlocks") else None

    @property
    def notes(self):
        """주석 접근자 - EDGAR docs.notes 래핑.

        ``c.notes("inventory")`` (call) 또는 ``c.notes.inventory`` (attr) 양식 지원.

        Returns:
            ``_EdgarNotesWrapper`` 인스턴스.

        Raises:
            없음.

        Example:
            >>> c = Company("AAPL")
            >>> c.notes("inventory")        # 카테고리별 구조화
            >>> c.notes.keys()              # 사용 가능 카테고리

        SeeAlso:
            - ``_EdgarNotesWrapper`` - 본 함수의 반환 래퍼 (.all/.keys/.keysKr/.quarterly).
            - ``dart.providers.dart.company.Company.notes`` - KR 패리티.

        Requires:
            - dartlab
            - polars

        Capabilities:
            - XBRL TextBlock 주석을 카테고리 별로 구조화. DART 의 docs/notes 와 동일 인터페이스 패리티.
              call 시 본문 검색, attr 시 카테고리 직접 dispatch.

        Guide:
            - "이 회사 inventory 주석" → ``c.notes("inventory")``.
            - "어떤 카테고리 있나" → ``c.notes.keys()``.

        AIContext:
            workbench 가 재무제표 footnote 질문 받을 때 본 함수 entry - DART c.notes 와 동일 API.
        """
        from dartlab.core.memory import _CACHE_MISSING

        val = self._cache.get("_notes_wrapper", _CACHE_MISSING)
        if val is _CACHE_MISSING:
            val = _EdgarNotesWrapper(self)
            self._cache["_notes_wrapper"] = val
        return val

    @property
    def facts(self) -> pl.DataFrame | None:
        """topic × period 형태의 통합 facts 테이블.

        Returns:
            facts DataFrame 또는 None.

        Raises:
            없음.

        Example:
            >>> c.facts

        LLM Specifications:
            AntiPatterns:
                - 전체 facts 그대로 노출 → 수백 row × 수십 컬럼 토큰 폭증. topic/period 필터 의무.
                - facts ≠ companyfacts API raw - 본 함수는 dartlab 정규화 결과.
            OutputSchema:
                - pl.DataFrame - topic × period 매트릭스 또는 None.
            Prerequisites:
                - profileAccessor + companyfacts/finance 합산.
            Freshness:
                - finance + sections 갱신 시점.
            Dataflow:
                - companyfacts + finance → profileAccessor.facts → 본 property.
            TargetMarkets:
                - US (SEC EDGAR) 통합 facts.
        """
        return getattr(self._profileAccessor, "facts", None)

    # c.ratioSeries property 제거 (Plan v10 P1) - show("ratios") 사용
    # sector, sectorParams, sceMatrix - EXEMPT (test_protocol.py)

    @property
    def rank(self):
        """피어 그룹 내 랭킹 - EDGAR 는 현재 미지원.

        Returns:
            None (US 피어 랭킹 미구현).

        Raises:
            없음.

        Example:
            >>> c.rank  # None
        """
        return None

    @property
    def sources(self) -> pl.DataFrame:
        """데이터 소스 현황 - EDGAR 는 docs + finance 2 소스.

        Returns:
            source/available/rows/cols/shape 컬럼 DataFrame.

        Raises:
            없음.

        Example:
            >>> c = Company("AAPL")
            >>> c.sources

        SeeAlso:
            - ``trace`` - topic 별 source 추적.
            - ``dart.providers.dart.company.Company.sources`` - KR 패리티 (8 소스).

        Requires:
            - dartlab
            - polars

        Capabilities:
            - 본 회사의 데이터 source (docs/finance) 가용 상태 + 각 source 의 shape 메타.
              DART (8 source) 대비 EDGAR 는 2 source - 시그니처 동기 목적.

        Guide:
            - "이 회사 어떤 데이터 있나" → 본 property.

        AIContext:
            AI 가 sources 확인 후 정확한 origin (docs vs finance) 로 분기. 빈 source 호출 회피.

        LLM Specifications:
            AntiPatterns:
                - 현재 rows/cols/shape 값 0/0/"" 고정 - 향후 실 shape 채울 예정 (skeleton).
                - DART 8 source 와 비교 시 EDGAR 가 적다고 판단 X - XBRL 통합이라 source 그루핑 다름.
            OutputSchema:
                - pl.DataFrame [source, available:bool, rows:int, cols:int, shape:str].
            Prerequisites:
                - 본 Company 인스턴스 (docs/finance accessor 초기화).
            Freshness:
                - 호출 시점.
            Dataflow:
                - self._docs/_finance → 본 함수 → 정적 dict 합산.
            TargetMarkets:
                - US (SEC EDGAR) 2 source.
        """
        rows = []
        for src, accessor in [("docs", self._docs), ("finance", self._finance)]:
            available = accessor is not None
            rows.append({"source": src, "available": available, "rows": 0, "cols": 0, "shape": ""})
        return pl.DataFrame(rows)

    # ── Methods ──

    def table(
        self, topic: str, subtopic: str | None = None, *, numeric: bool = False, period: str | None = None
    ) -> Any:
        """topic 데이터를 테이블 형태로 반환.

        Args:
            topic: topic 이름.
            subtopic: subtopic (현재 미사용).
            numeric: 숫자만 추출 (현재 미사용).
            period: 특정 기간 필터.

        Returns:
            topic DataFrame 또는 None.

        Raises:
            없음.

        Example:
            >>> c = Company("AAPL")
            >>> c.table("BS")

        SeeAlso:
            - ``show`` - 본 함수의 실 backend (현재 단순 위임).
            - ``dart.providers.dart.company.Company.table`` - KR 패리티 (실 subtopic/numeric 처리).

        Requires:
            - dartlab
            - polars

        Capabilities:
            - DartCompany.table 와 동일 시그니처 보존용 wrapper. subtopic/numeric 인자 현재 미사용
              (skeleton) - show() 결과 단순 전달. 향후 EDGAR subtopic 분해 시 확장.

        Guide:
            - "BS table" → ``c.table("BS")`` (show 와 동일).

        AIContext:
            DartCompany API 와 동일 시그니처 - AI 가 cross-provider 코드 작성 시 분기 불필요.

        LLM Specifications:
            AntiPatterns:
                - subtopic / numeric 인자 영향 가정 → 현재 무시. show() 사용이 더 명확.
            OutputSchema:
                - pl.DataFrame - show() 결과 그대로 또는 None.
            Prerequisites:
                - show() 와 동일.
            Freshness:
                - show() 와 동일.
            Dataflow:
                - 사용자 인자 → show(topic, period) → 본 함수.
            TargetMarkets:
                - US (SEC EDGAR) - DART 호환 시그니처.
        """
        df = self._showImpl(topic, period=period)
        if df is None:
            return None
        return df

    def audit(self) -> list | None:
        """감사/내부통제 분석 - EDGAR item9A + item14 기반.

        10-K Item 9A(Controls and Procedures) 텍스트에서 material weakness,
        going concern 등 핵심 키워드를 탐지한다.

        Returns
        -------
        list[dict] | None
            각 dict 키:
                type : str - 발견 유형 (material_weakness/going_concern/
                    ineffective_controls/clean/audit_fees)
                period : str - 해당 기간 (예: "2024")
                severity : str - 심각도 (critical/warning/ok)
                amount : str - 감사 수수료 금액 (audit_fees 유형만)
            발견 없으면 None.

        Raises:
            없음.

        Example:
            >>> c = Company("AAPL")
            >>> c.audit()

        Returns:
            발견 dict 리스트 또는 None. 각 dict 키 위 Returns 표 참조.

        SeeAlso:
            - ``governance`` - Part III item10/12/11 텍스트.
            - ``show("10-K::item9AControlsAndProcedures")`` - 본 함수 origin.

        Requires:
            - dartlab
            - polars

        Capabilities:
            - 10-K Item 9A (내부통제) + Item 14 (감사 수수료) 텍스트에서 키워드 기반 자동 탐지 -
              material weakness / going concern / ineffective controls / clean. 감사 수수료 금액 정규식 추출.

        Guide:
            - "이 회사 내부통제 문제 있나" → 본 함수 결과 severity 확인.
            - "감사 수수료 추세" → audit_fees 발견 amount 컬럼.

        AIContext:
            AI 가 사용자에게 부정/리스크 신호 답할 때 본 함수 출력 인용. severity 가 critical 이면 강한 경고.

        LLM Specifications:
            AntiPatterns:
                - 키워드 매칭만 → false positive (예 "no material weakness") 가능. 본문 컨텍스트 재확인.
                - "clean" 결과 → 진짜 문제 없다는 보장 X, 키워드 미감지일 뿐.
            OutputSchema:
                - list[dict] 각 dict {type, period, severity, amount?} 또는 None.
            Prerequisites:
                - 10-K Item 9A + Item 14 sections 본문.
            Freshness:
                - 10-K 갱신 시점 (연 1 회).
            Dataflow:
                - show("10-K::item9A...") + show("10-K::item14...") → 키워드 매칭 + 정규식 → 본 list.
            TargetMarkets:
                - US (SEC EDGAR) 10-K Part II/III 한정.
        """
        import re

        findings: list[dict] = []
        # Item 9A: 내부통제
        item9a = self._showImpl("10-K::item9AControlsAndProcedures", block=0)
        if item9a is not None:
            from dartlab.providers._common.show import isPeriodColumn

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
        item14 = self._showImpl("10-K::item14PrincipalAccountantFees", block=0)
        if item14 is not None:
            from dartlab.providers._common.show import isPeriodColumn

            pcols = [c for c in item14.columns if isPeriodColumn(c)]
            if pcols:
                latest = pcols[0]
                text = " ".join(str(v) for v in item14[latest].to_list() if v)
                fee_matches = re.findall(r"\$([\d,.]+)\s*(?:million|billion)", text, re.IGNORECASE)
                if fee_matches:
                    findings.append({"type": "audit_fees", "period": latest, "amount": fee_matches[0]})
        return findings or None

    def governance(self, view: str | None = None) -> pl.DataFrame | None:
        """지배구조 분석 - EDGAR item10/item12 기반.

        10-K Part III에서 이사회 구성, 소유 구조 텍스트를 제공한다.
        DART와 달리 구조화된 수치가 아닌 텍스트 데이터이다.

        Returns
        -------
        pl.DataFrame | None
            항목 : str - 분석 영역 (directors/ownership/compensation)
            기간 : str - 데이터 기간 (예: "2024")
            내용 : str - 10-K 텍스트 요약 (최대 500자)
            view="all"/"market"이면 None (EDGAR 미지원).
            데이터 없으면 None.

        Raises:
            없음.

        Example:
            >>> c = Company("AAPL")
            >>> c.governance()

        Args:
            view: "all" 또는 "market" 시 None (EDGAR 미지원). 그 외 dummy.

        Returns:
            지배구조 텍스트 DataFrame (directors/ownership/compensation 항목) 또는 None.

        SeeAlso:
            - ``audit`` - Item 9A/14 감사 관련.
            - ``dart.providers.dart.company.Company.governance`` - KR 패리티 (구조화 수치).

        Requires:
            - dartlab
            - polars

        Capabilities:
            - 10-K Part III 의 Item 10 (Directors) + Item 11 (Compensation) + Item 12 (Ownership)
              텍스트 본문 (500 자 truncate) 을 3 항목 DataFrame 으로 합산. KR 과 달리 구조화 수치 X.

        Guide:
            - "이 회사 이사회 / 임원 보수 / 소유 구조" → 본 함수 텍스트 본문.

        AIContext:
            DART governance 가 정량 수치 반환하는 반면 EDGAR 는 텍스트 origin - AI 가 본문 요약 의무.

        LLM Specifications:
            AntiPatterns:
                - 텍스트 500 자 truncate → 본문 전부 가정 X. 원본은 show("10-K::item10...").
                - view="all"/"market" 호출 시 None - 호출자 분기 의무.
            OutputSchema:
                - pl.DataFrame [항목:str, 기간:str, 내용:str≤500] 또는 None.
            Prerequisites:
                - 10-K Part III sections (Item 10/11/12).
            Freshness:
                - 10-K 갱신 시점 (연 1 회).
            Dataflow:
                - show("10-K::item10/11/12...") → 본문 truncate → 본 DF.
            TargetMarkets:
                - US (SEC EDGAR) 10-K Part III.
        """
        if view in ("all", "market"):
            return None
        rows: list[dict] = []
        for topic_key, label in [
            ("10-K::item10DirectorsAndCorporateGovernance", "directors"),
            ("10-K::item12SecurityOwnership", "ownership"),
            ("10-K::item11ExecutiveCompensation", "compensation"),
        ]:
            df = self._showImpl(topic_key, block=0)
            if df is not None:
                from dartlab.providers._common.show import isPeriodColumn

                pcols = [c for c in df.columns if isPeriodColumn(c)]
                if pcols:
                    latest = pcols[0]
                    text = " ".join(str(v) for v in df[latest].to_list() if v)
                    rows.append({"항목": label, "기간": latest, "내용": text[:500] if text else ""})
        if not rows:
            return None
        return pl.DataFrame(rows)

    def workforce(self, view: str | None = None) -> pl.DataFrame | None:
        """인력 분석 - EDGAR item1 + IS 기반.

        10-K Item 1(Business)에서 직원 수를 추출하고, IS 매출 대비
        1인당 매출을 계산한다.

        Args:
            view: ``"all"``/``"market"`` 이면 None (EDGAR 미지원).

        Returns:
            종목코드/회사명/직원수/기간/1인당매출 컬럼 DataFrame 또는 None.

        Raises:
            없음.

        Example:
            >>> c = Company("AAPL")
            >>> c.workforce()

        SeeAlso:
            - ``governance`` / ``audit`` - 10-K Part III/9A 동일 origin 패밀리.
            - ``dart.providers.dart.company.Company.workforce`` - KR 패리티 (구조화 직원 수).

        Requires:
            - dartlab
            - polars

        Capabilities:
            - 10-K Item 1 (Business) 텍스트에서 6 종 정규식 패턴 ("approximately N employees" 등)
              으로 직원 수 추출. IS Revenue 와 결합해 1 인당 매출 계산. 100 인 이하 매치 무시 (noise).

        Guide:
            - "이 회사 직원 수" → 본 함수 "직원수" 컬럼.
            - "1 인당 매출 효율" → 본 함수 "1인당매출" 컬럼.

        AIContext:
            DART 가 구조화 수치 반환하는 반면 EDGAR 는 텍스트 추출 - 정확도 ~90%. AI 가 환각 vs 실수치 분기.

        LLM Specifications:
            AntiPatterns:
                - 텍스트 추출 정확도 100% 가정 X - 본문 표현 변화 시 None 가능.
                - 1 인당 매출 절대값 회사 간 비교 X - fiscal year 차이/사업부문 차이 큼.
            OutputSchema:
                - pl.DataFrame [종목코드, 회사명, 직원수:int, 기간:str, 1인당매출:float|None] 또는 None.
            Prerequisites:
                - 10-K Item 1 Business sections + IS Revenue (선택).
            Freshness:
                - 10-K 갱신 시점 (연 1 회).
            Dataflow:
                - show("10-K::item1Business") → 정규식 매칭 → IS Revenue → 1 인당 매출 → 본 DF.
            TargetMarkets:
                - US (SEC EDGAR) 10-K Item 1.
        """
        import re

        if view in ("all", "market"):
            return None
        # 모든 block의 텍스트를 합쳐서 employee 패턴 검색
        employee_count: int | None = None
        period: str | None = None
        item1_idx = self._showImpl("10-K::item1Business")
        if item1_idx is None:
            return None
        for row in item1_idx.iter_rows(named=True):
            block_id = row.get("block", 0)
            block_df = self._showImpl("10-K::item1Business", block=block_id)
            if block_df is None:
                continue
            from dartlab.providers._common.show import isPeriodColumn

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
        isDf = self._showImpl("IS")
        if isDf is not None:
            from dartlab.providers._common.show import isPeriodColumn, selectFromShow

            rev_row = selectFromShow(isDf, ["sales"])
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
        """주주환원/자본구조 - EDGAR BS/CF 기반 단일 회사 분석.

        DART와 달리 전종목 횡단비교(view="all")는 미지원.

        Returns
        -------
        pl.DataFrame | None
            종목코드 : str - ticker
            회사명 : str - 회사명
            total_stockholders_equity : float - 자기자본 (USD)
            retained_earnings : float - 이익잉여금 (USD)
            dividends_paid : float - 배당금 지급액 (USD, 있을 때만)
            view="all"/"market"이면 None.

        Raises:
            없음.

        Example:
            >>> c = Company("AAPL")
            >>> c.capital()

        Args:
            view: "all"/"market" 시 None. EDGAR 는 단일 회사만.

        Returns:
            자기자본/이익잉여금/배당 DataFrame 또는 None.

        SeeAlso:
            - ``debt`` - 부채구조 (BS 동일 origin).
            - ``dart.providers.dart.company.Company.capital`` - KR 전종목 횡단 지원.

        Requires:
            - dartlab
            - polars

        Capabilities:
            - BS 의 total_stockholders_equity + retained_earnings + CF 의 dividends_paid 를
              최신 period 1 행 DataFrame 으로 합산. 주주환원 능력 가늠.

        Guide:
            - "이 회사 자본구조" → 본 함수.
            - "배당 가능성" → result["dividends_paid"] / result["retained_earnings"] 비율.

        AIContext:
            AI 가 주주환원 정책 질문 시 본 함수 인용 + show("CF") 의 배당 추세 추가 결합.

        LLM Specifications:
            AntiPatterns:
                - 단일 period 결과로 추세 결론 X - 본 함수는 latest 만, 추세는 show("CF") 사용.
                - view="all" 호출 → KR 와 달리 None. 횡단비교는 dart 만.
            OutputSchema:
                - pl.DataFrame 1 행 [종목코드, 회사명, total_stockholders_equity, retained_earnings, dividends_paid].
            Prerequisites:
                - BS (필수) + CF (선택).
            Freshness:
                - finance 분기 갱신 시점.
            Dataflow:
                - show("BS") + show("CF") → selectFromShow → latest period → 본 DF.
            TargetMarkets:
                - US (SEC EDGAR) 단일 회사 한정.
        """
        if view in ("all", "market"):
            return None
        bs = self._showImpl("BS")
        cf = self._showImpl("CF")
        if bs is None:
            return None
        from dartlab.providers._common.show import selectFromShow

        equity = selectFromShow(bs, ["total_stockholders_equity", "retained_earnings"])
        divs = selectFromShow(cf, ["dividends_paid"]) if cf is not None else None
        if equity is None:
            return None
        rows: list[dict] = [{"종목코드": self.ticker, "회사명": self.corpName}]
        from dartlab.providers._common.show import isPeriodColumn

        pcols = [c for c in equity.columns if isPeriodColumn(c)]
        if pcols:
            latest = pcols[0]
            for row in equity.iter_rows(named=True):
                rows[0][row["snakeId"]] = row.get(latest)
            if divs is not None:
                for row in divs.iter_rows(named=True):
                    rows[0][row["snakeId"]] = row.get(latest)
        return pl.DataFrame(rows)

    def debt(self, view: str | None = None) -> pl.DataFrame | None:
        """부채구조 분석 - EDGAR BS 기반 단일 회사 분석.

        DART와 달리 전종목 횡단비교(view="all")는 미지원.

        Returns
        -------
        pl.DataFrame | None
            종목코드 : str - ticker
            회사명 : str - 회사명
            total_liabilities : float - 부채총계 (USD)
            shortterm_borrowings : float - 단기차입금 (USD)
            longterm_borrowings : float - 장기차입금 (USD)
            current_liabilities : float - 유동부채 (USD)
            noncurrent_liabilities : float - 비유동부채 (USD)
            view="all"/"market"이면 None.

        Raises:
            없음.

        Example:
            >>> c = Company("AAPL")
            >>> c.debt()

        Args:
            view: "all"/"market" 시 None. EDGAR 는 단일 회사만.

        Returns:
            부채구조 DataFrame (total_liabilities/shortterm/longterm/current/noncurrent) 또는 None.

        SeeAlso:
            - ``capital`` - 자본구조 (BS 동일 origin).
            - ``dart.providers.dart.company.Company.debt`` - KR 패리티 (전종목 횡단 지원).

        Requires:
            - dartlab
            - polars

        Capabilities:
            - BS 의 6 부채 계정 (total/short/long/debentures/current/noncurrent_liabilities) 을
              최신 period 1 행 DF 로 추출. 부채 만기 구조 파악 + 단기/장기 비율 분석.

        Guide:
            - "이 회사 부채 구조" → 본 함수.
            - "단기 vs 장기 부채 비율" → result.shortterm_borrowings / longterm_borrowings.

        AIContext:
            AI 가 부도/유동성 위험 답변 시 본 함수 + credit() 결합. 단일 period 라 추세는 show("BS") 별도.

        LLM Specifications:
            AntiPatterns:
                - debt ≠ liabilities - borrowings 가 진짜 차입금, liabilities 는 매입채무 포함.
                - view="all" → KR 와 달리 None. 횡단비교는 dart 만.
            OutputSchema:
                - pl.DataFrame 1 행 [종목코드, 회사명, total_liabilities, shortterm_borrowings, ...].
            Prerequisites:
                - BS 의 부채 계정 (XBRL Liabilities/Borrowings 매핑 후).
            Freshness:
                - finance 분기 갱신 시점.
            Dataflow:
                - show("BS") → selectFromShow(6 accts) → latest period → 본 DF.
            TargetMarkets:
                - US (SEC EDGAR) 단일 회사.
        """
        if view in ("all", "market"):
            return None
        bs = self._showImpl("BS")
        if bs is None:
            return None
        from dartlab.providers._common.show import selectFromShow

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
        from dartlab.providers._common.show import isPeriodColumn

        pcols = [c for c in debt_accts.columns if isPeriodColumn(c)]
        if pcols:
            latest = pcols[0]
            for row in debt_accts.iter_rows(named=True):
                rows[0][row["snakeId"]] = row.get(latest)
        return pl.DataFrame(rows)

    def network(self, view: str | None = None, *, hops: int = 1):
        """기업 네트워크 그래프 - EDGAR 미구현 (cross-provider symmetry placeholder).

        Capabilities:
            - SEC ownership / Form 13F filings 기반 향후 구현.
            - 현 단계 None - dart.network 와 cross-provider symmetric API 보장.

        Args:
            view: None / "members" / "edges" / "cycles" / "peers".
            hops: ego 깊이.

        Returns:
            None - EDGAR 네트워크 prebuild 미구현.

        Guide:
            - "이 회사 그룹 계열사" → 현 단계 KR (dart) 한정. EDGAR 는 향후.

        SeeAlso:
            - ``dart.Company.network`` - KR 한정 구현.

        Requires:
            - 외부 의존 없음 (placeholder).

        AIContext:
            cross-provider symmetric placeholder. AI 가 호출 시 None 받고 "EDGAR 미지원"
            fallback. dart 와 동일 시그니처라 batch 코드 unsafe 검출 회피.

        LLM Specifications:
            AntiPatterns:
                - view/hops 무관 항상 None.
            OutputSchema:
                - None.
            Prerequisites:
                - 없음.
            Freshness:
                - 정적.
            Dataflow:
                - 향후 SEC Form 13F → 본 함수.
            TargetMarkets:
                - US (EDGAR) 한정. 현재 미구현.

        Raises:
            없음.

        Example:
            >>> network(...)
        """
        del view, hops
        return None

    def topicSummaries(self) -> dict[str, str]:
        """topic 별 한 줄 요약 dict - cross-provider symmetric placeholder.

        Capabilities:
            - 현 단계 빈 dict - sections summary 향후 구현.
            - dart.topicSummaries 와 동일 시그니처.

        Returns:
            dict[str, str] - 현재 빈 dict.

        Guide:
            - "이 회사 topic 한 줄씩" → 현 단계 KR (dart) 한정.

        SeeAlso:
            - ``dart.Company.topicSummaries`` - KR 한정 구현.

        Requires:
            - 외부 의존 없음 (placeholder).

        AIContext:
            cross-provider symmetric placeholder.

        LLM Specifications:
            AntiPatterns:
                - 항상 빈 dict.
            OutputSchema:
                - dict[str, str] (empty).
            Prerequisites:
                - 없음.
            Freshness:
                - 정적.
            Dataflow:
                - 향후 sections → 본 함수.
            TargetMarkets:
                - US (EDGAR) 한정. 현재 미구현.

        Raises:
            없음.

        Example:
            >>> topicSummaries(...)
        """
        return {}

    def update(self, *, categories: list[str] | None = None) -> dict[str, int]:
        """누락 공시 증분 수집 - EDGAR bulk re-sync placeholder.

        Capabilities:
            - dart.update 와 동일 시그니처 - categories 별 수집 통계 dict 반환.
            - 현 단계 EDGAR bulk pipeline (companyfactsBulk + 분기 datasetBulk) 가 batch
              처리하므로 종목 1 개 단위 update 는 미구현.

        Args:
            categories: 수집 영역 list 또는 None.

        Returns:
            dict[str, int] - 현재 빈 dict (EDGAR bulk 가 일괄 처리).

        Guide:
            - "이 회사 최신 데이터" → bulk pipeline 의 cron 갱신 대기 또는 ``refreshFromApi()``.

        SeeAlso:
            - ``Company.refreshFromApi`` - SEC API per-ticker 즉시 갱신.
            - ``dart.Company.update`` - KR 한정 종목 단위 update.

        Requires:
            - 외부 의존 없음 (placeholder).

        AIContext:
            cross-provider symmetric placeholder. EDGAR 사용자는 refreshFromApi 안내.

        LLM Specifications:
            AntiPatterns:
                - categories 무관 항상 빈 dict.
            OutputSchema:
                - dict[str, int] (empty).
            Prerequisites:
                - 없음.
            Freshness:
                - 정적.
            Dataflow:
                - 향후 SEC bulk → 본 함수.
            TargetMarkets:
                - US (EDGAR) 한정. 현재 bulk pipeline 위임.

        Raises:
            없음.

        Example:
            >>> update(...)
        """
        del categories
        return {}
