"""DART 엔진 내부 Company 본체.

사용법::

    from dartlab.providers.dart.company import Company

    c = Company("005930")       # 한국 (DART)
    c = Company("삼성전자")      # 한국 (회사명)
    c.BS                        # 재무상태표 DataFrame
    c.ratios                    # 재무비율
    c.insights                  # 인사이트 등급
"""

from __future__ import annotations

import gc
import re
from typing import Any

import polars as pl

pl.Config.set_fmt_str_lengths(80)
pl.Config.set_tbl_width_chars(200)

from dartlab.core.dataLoader import (
    DART_VIEWER,
    buildIndex,
    extractCorpName,
    loadData,
)

# ── 모듈 레지스트리 (core/registry.py에서 자동 생성) ──
# (모듈 import 경로, 함수명, 한글 라벨, primary DataFrame 추출)
# fsSummary/statements는 내부 디스패치 전용 (BS/IS/CF property가 statements를 호출)
from dartlab.core.registry import getEntry as _getEntry
from dartlab.core.registry import getModuleEntries as _getModuleEntries
from dartlab.gather.listing import (
    codeToName,
    getKindList,
    nameToCode,
    searchName,
)

from dartlab.providers.dart._docs_accessor import _DocsAccessor
from dartlab.providers.dart._finance_accessor import _FinanceAccessor
from dartlab.providers.dart._finance_helpers import (
    _RATIO_TEMPLATE_FIELDS,
    _financeCisAnnual,
    _financeCisQuarterly,
    _financeToDataFrame,
    _ratioArchetypeOverrideForIndustryGroup,
    _ratioResultHasHeadlineSignal,
    _ratioSeriesToDataFrame,
    _ratioTemplateKeyForIndustryGroup,
    _sceToDataFrame,
    _shouldFallbackToAnnualRatios,
)
from dartlab.providers.dart._profile_accessor import _ProfileAccessor
from dartlab.providers.dart._report_accessor import _ReportAccessor
from dartlab.providers.dart._sections_source import _SectionsSource
from dartlab.providers.dart._utils import (
    _checkDartDocsFreshness,
    _ensureAllData,
    _ensureData,
    _import_and_call,
    _isPeriodColumn,
    _shapeString,
)
from dartlab.providers.dart.docs.notes import Notes
from dartlab.providers.filingHelpers import filingRecord, filterFilingsByKeyword, resolveDateWindow, truncateText

# 플러그인 등록 후 재구축 가능하도록 lazy 초기화
_MODULE_REGISTRY: list[tuple[str, str, str, Any]] | None = None
_MODULE_INDEX: dict[str, int] | None = None
_ALL_PROPERTIES: list[tuple[str, str]] | None = None


def _get_module_registry() -> list[tuple[str, str, str, Any]]:
    """lazy 모듈 레지스트리 — 최초 접근 시 구축."""
    global _MODULE_REGISTRY, _MODULE_INDEX
    if _MODULE_REGISTRY is None:
        _MODULE_REGISTRY = [
            ("dartlab.providers.dart.docs.finance.summary", "fsSummary", "요약재무정보", None),
            ("dartlab.providers.dart.docs.finance.statements", "statements", "재무제표", None),
        ] + [(e.modulePath, e.funcName, e.label, e.extractor) for e in _getModuleEntries()]
        _MODULE_INDEX = {entry[1]: i for i, entry in enumerate(_MODULE_REGISTRY)}
    return _MODULE_REGISTRY


def _get_module_index() -> dict[str, int]:
    """lazy 모듈 인덱스 — 최초 접근 시 구축."""
    global _MODULE_INDEX
    if _MODULE_INDEX is None:
        _get_module_registry()
    return _MODULE_INDEX  # type: ignore[return-value]


def _get_all_properties() -> list[tuple[str, str]]:
    """lazy all() 순서 목록 — 최초 접근 시 구축."""
    global _ALL_PROPERTIES
    if _ALL_PROPERTIES is None:
        _ALL_PROPERTIES = [
            ("BS", "재무상태표"),
            ("IS", "손익계산서"),
            ("CF", "현금흐름표"),
        ]
        for entry in _get_module_registry():
            name = entry[1]
            if name in ("fsSummary", "statements", "companyOverview"):
                continue
            _ALL_PROPERTIES.append((name, entry[2]))
    return _ALL_PROPERTIES


def rebuild_module_registry() -> None:
    """플러그인 등록 후 호출 — 모듈 레지스트리 캐시 무효화."""
    global _MODULE_REGISTRY, _MODULE_INDEX, _ALL_PROPERTIES
    _MODULE_REGISTRY = None
    _MODULE_INDEX = None
    _ALL_PROPERTIES = None


_CHAPTER_TITLES: dict[str, str] = {
    "I": "I. 회사의 개요",
    "II": "II. 사업의 내용",
    "III": "III. 재무에 관한 사항",
    "IV": "IV. 이사의 경영진단 및 분석의견",
    "V": "V. 감사인의 감사의견등",
    "VI": "VI. 이사회등회사의기관및계열회사에관한사항",
    "VII": "VII. 주주에 관한 사항",
    "VIII": "VIII. 임원 및 직원 등에 관한 사항",
    "IX": "IX. 이해관계자와의 거래내용",
    "X": "X. 그 밖에 투자자 보호를 위하여 필요한 사항",
    "XI": "XI. 재무제표등",
    "XII": "XII. 상세표 및 부속명세서",
}

_CHAPTER_ORDER: dict[str, int] = {chapter: idx for idx, chapter in enumerate(_CHAPTER_TITLES, start=1)}
_REPORT_TOPIC_TO_API_TYPE: dict[str, str] = {
    "audit": "auditOpinion",
}
_API_TYPE_TO_TOPIC: dict[str, str] = {v: k for k, v in _REPORT_TOPIC_TO_API_TYPE.items()}
# ── topic 단축 alias ────────────────────────────────────────────
# show("board") → show("boardOfDirectors") 등 짧은 이름으로 접근 가능
_TOPIC_ALIASES: dict[str, str] = {
    # 지배구조 / 경영
    "board": "boardOfDirectors",
    "directors": "boardOfDirectors",
    "pay": "executivePay",
    "holder": "majorHolder",
    "holders": "holderOverview",
    "meeting": "shareholderMeeting",
    # 위험 / 공시
    "contingent": "contingentLiability",
    "relatedParty": "relatedPartyTx",
    "risk": "riskDerivative",
    "control": "internalControl",
    # 자산 / 투자
    "tangible": "tangibleAsset",
    "intangible": "intangibleAsset",
    "material": "rawMaterial",
    "cost": "costByNature",
    "sales": "salesOrder",
    "product": "productService",
    "invested": "investedCompany",
    "investment": "investmentInOther",
    # 기타
    "overview": "companyOverview",
    "history": "companyHistory",
    "articles": "articlesOfIncorporation",
    "capital": "shareCapital",
    "capitalChange": "capitalChange",
    "stock": "stockTotal",
    "treasury": "treasuryStock",
    "summary": "fsSummary",
}

_TOPIC_LABELS: dict[str, str] = {
    "businessOverview": "사업의 개요",
    "businessStatus": "사업현황",
    "consolidatedNotes": "연결재무제표 주석",
    "consolidatedStatements": "연결재무제표",
    "financialNotes": "재무제표 주석",
    "financialStatements": "재무제표",
    "financialSoundnessOtherReference": "재무건전성 기타참고",
    "governanceOverview": "지배구조 개요",
    "majorContractsAndRnd": "주요계약 및 R&D",
    "mdna": "경영진단 및 분석의견",
    "segmentFinancialSummary": "부문별 재무요약",
    "investmentInOtherDetail": "타법인출자 상세",
    "stockAdministration": "주식사무",
    "stockPriceTrend": "주가 추이",
    "appendixSchedule": "상세표",
    "investorProtection": "투자자보호",
    "disclosureChanges": "공시내용 변경",
    "subsequentEvents": "후발사건",
    "expertConfirmation": "전문가확인",
    "subsidiaryDetail": "종속회사 상세",
    "affiliateGroupDetail": "계열회사 상세",
    "rndDetail": "연구개발 상세",
    "otherReference": "기타참고사항",
    "otherReferences": "기타참고사항",
    "operatingFacilities": "생산설비",
    # subtopic에 등장하는 내부 topic명 한글화
    "marketRisk": "시장위험",
    "liquidityRisk": "유동성위험",
    "capitalRisk": "자본위험",
    "creditRisk": "신용위험",
    "derivativeExposure": "파생상품 노출",
    "fxRisk": "환율위험",
    "fairValueRisk": "공정가치위험",
    "interestRateRisk": "이자율위험",
    "priceRisk": "가격위험",
    "segmentIct": "ICT 부문",
    "segmentOther": "기타 부문",
    "segmentDigitalMedia": "디지털미디어 부문",
    "salesOrder": "매출 및 수주",
    "rawMaterial": "원재료 및 설비",
    "riskDerivative": "위험관리 및 파생상품",
    "costByNature": "비용의 성격별 분류",
    "segments": "부문정보",
}

_RCEPT_NO_PATTERN = re.compile(r"[?&]rcpNo=(\d{14})")


def listExportModules() -> list[tuple[str, str]]:
    """Excel/export용 DART 공개 모듈 목록."""
    return list(_get_all_properties())


class Company:
    """DART 기반 한국 상장기업 분석.

    기본 사용 모델은 index / show / trace다.

    - ``index``: sections 뼈대 위에 finance/report가 채워진 수평화 보드
    - ``show(topic)``: 특정 topic의 실제 payload(DataFrame)
    - ``trace(topic, period)``: 선택 source와 provenance

    3개 데이터 소스를 강점 기반으로 선별하여 제공:

    - **finance** (XBRL 정규화): BS/IS/CIS/CF/SCE, timeseries, annual, ratios
    - **report** (DART API 정형): 28개 apiType 체계, 현재 가용 항목 중심 structured disclosure
    - **docs** (HTML 파싱): 서술형(business, mdna), K-IFRS 주석(notes), 거버넌스, 리스크 등

    소스 우선순위:
    - docs sections 수평화가 구조의 spine
    - finance가 숫자 재무 authoritative source
    - report가 정형 공시 authoritative source
    - Company는 이 세 source를 merged board로 제공한다

    Example::

        c = Company("005930")           # 삼성전자
        c.index                          # 전체 수평화 보드
        c.show("BS")                     # 재무상태표
        c.show("salesOrder")             # sections 기반 subtopic DataFrame
        c.show("costByNature")           # sections/detailTopic 우선 + legacy fallback
        c.trace("dividend")              # source provenance
        c.finance.CIS                    # 포괄손익계산서
        c.finance.SCE                    # 자본변동표
        c.report.treasuryStock           # 정형 공시
        c.docs.sections                  # pure docs source view
    """

    @staticmethod
    def canHandle(code: str) -> bool:
        """DART 종목코드(6자) 또는 한글 회사명이면 처리 가능."""
        if re.match(r"^[0-9A-Za-z]{6}$", code):
            return True
        if any("\uac00" <= ch <= "\ud7a3" for ch in code):
            return True
        return False

    @staticmethod
    def priority() -> int:
        """낮을수록 먼저 시도. DART=10 (기본 provider)."""
        return 10

    def __init__(self, codeOrName: str):
        normalized = codeOrName.strip()
        if re.match(r"^[0-9A-Za-z]{6}$", normalized):
            self.stockCode = normalized.upper()
        else:
            code = nameToCode(normalized)
            if code is None:
                raise ValueError(f"'{normalized}'에 해당하는 종목을 찾을 수 없음")
            self.stockCode = code
        from dartlab.core.memory import BoundedCache

        self._cache: BoundedCache = BoundedCache(max_entries=30)

        _dataStatus = _ensureAllData(self.stockCode)
        self._hasDocs = _dataStatus.get("docs", False)
        self._freshnessResult = None
        if self._hasDocs:
            self._freshnessResult = _checkDartDocsFreshness(self.stockCode, "docs")
        self._hasFinanceParquet = _dataStatus.get("finance", False)
        self._hasReport = _dataStatus.get("report", False)

        corpName = codeToName(self.stockCode)
        if corpName:
            self.corpName = corpName
        elif self._hasDocs:
            df = loadData(self.stockCode, category="docs", columns=["corp_name"])
            self.corpName = extractCorpName(df)
        else:
            self.corpName = self.stockCode

        # finance는 lazy — 첫 접근 시 _ensureFinanceLoaded()에서 검증
        self._financeChecked = False

        if not self._hasDocs and not self._hasFinanceParquet and not self._hasReport:
            from dartlab.core.guidance import emit

            emit("error:no_data", stockCode=self.stockCode, raise_as=ValueError)

        self._hintedKeys: set[str] = set()  # 동일 안내 반복 방지

        self._notesAccessor = Notes(self) if self._hasDocs else None
        self.docs = _DocsAccessor(self)
        self.finance = _FinanceAccessor(self)
        self.report = _ReportAccessor(self)
        self._profileAccessor = _ProfileAccessor(self)

    def __repr__(self):
        try:
            from dartlab.display.richCompany import renderCompany

            return renderCompany(self)
        except ImportError:
            return f"Company({self.stockCode}, {self.corpName})"

    def _hintOnce(self, key: str, prop: str, category: str = "docs") -> None:
        """동일 안내를 세션 내 1회만 출력."""
        if key in self._hintedKeys:
            return
        self._hintedKeys.add(key)
        from dartlab.core.guidance import emit

        emit(f"hint:no_{category}", stockCode=self.stockCode, prop=prop)

    def _financeProperty(self, name: str):
        """finance accessor 위임 + hint."""
        result = getattr(self.finance, name)
        if result is None:
            self._hintOnce(name, name, "finance")
        return result

    def topicSummaries(self) -> dict[str, str]:
        """토픽별 요약 dict — AI가 경로 탐색에 사용.

        각 docs topic의 최신 기간 첫 텍스트에서 200자 요약을 추출한다.
        finance topic은 고정 설명을 반환한다.
        """
        cacheKey = "_topicSummaries"
        if cacheKey in self._cache:
            return self._cache[cacheKey]

        summaries: dict[str, str] = {}

        # finance 고정 설명
        _FINANCE_SUMMARIES = {
            "BS": "재무상태표 — 자산, 부채, 자본 잔액",
            "IS": "손익계산서 — 매출, 영업이익, 당기순이익",
            "CIS": "포괄손익계산서 — 기타포괄손익 포함",
            "CF": "현금흐름표 — 영업/투자/재무 활동 현금",
            "SCE": "자본변동표 — 자본 구성요소별 변동",
            "ratios": "재무비율 — 수익성/안정성/성장성/효율성/밸류에이션",
        }
        summaries.update(_FINANCE_SUMMARIES)

        # docs topic 요약 — 최신 기간 첫 텍스트 200자
        if self._hasDocs:
            raw = loadData(
                self.stockCode,
                category="docs",
                sinceYear=2016,
                columns=["year", "report_type", "section_order", "section_title", "section_content"],
            )
            if raw is not None and not raw.is_empty() and "section_content" in raw.columns:
                from dartlab.core.reportSelector import selectReport
                from dartlab.providers.dart.docs.sections.mapper import mapSectionTitle

                # 최신 연도의 사업보고서에서 추출
                years = sorted(
                    {str(y) for y in raw["year"].drop_nulls().to_list()},
                    reverse=True,
                )
                for year in years:
                    report = selectReport(raw, year, reportKind="annual")
                    if report is None or report.is_empty():
                        continue
                    scoped = (
                        report.filter(pl.col("section_content").is_not_null())
                        .sort("section_order")
                    )
                    seen: set[str] = set()
                    for row in scoped.iter_rows(named=True):
                        rawTitle = str(row.get("section_title") or "").strip()
                        topic = mapSectionTitle(rawTitle)
                        if not topic or topic in seen or topic in summaries:
                            continue
                        seen.add(topic)
                        content = str(row.get("section_content") or "").strip()
                        if not content:
                            continue
                        # 첫 200자 (줄바꿈 → 공백)
                        preview = content.replace("\n", " ").replace("  ", " ")[:200].strip()
                        if preview:
                            summaries[topic] = preview
                    break  # 최신 연도만

        self._cache[cacheKey] = summaries
        return summaries

    @property
    def _analyzer(self):
        """sections 구조 분석기 (lazy)."""
        cacheKey = "_sectionsAnalyzer"
        if cacheKey not in self._cache:
            from dartlab.providers.dart._sectionsAnalyzer import SectionsAnalyzer

            self._cache[cacheKey] = SectionsAnalyzer(self)
        return self._cache[cacheKey]

    @property
    def _hasFinance(self) -> bool:
        """finance 사용 가능 여부 — lazy check 포함."""
        self._ensureFinanceLoaded()
        return self._hasFinanceParquet

    # ── 내부 호출 ──

    def _call_module(self, name: str, **kwargs) -> Any:
        """모듈 호출 + 캐싱. Notes에서도 사용."""
        if not self._hasDocs:
            return None
        cacheKey = f"{name}:{sorted(kwargs.items())}" if kwargs else name
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        idx = _get_module_index()[name]
        entry = _get_module_registry()[idx]
        result = _import_and_call(entry[0], entry[1], self.stockCode, **kwargs)
        self._cache[cacheKey] = result
        return result

    def _call_notesDetail(self, keyword: str) -> Any:
        """notesDetail 호출 (키워드별 캐싱)."""
        if not self._hasDocs:
            return None
        cacheKey = f"notesDetail:{keyword}"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        result = _import_and_call(
            "dartlab.providers.dart.docs.finance.notesDetail",
            "notesDetail",
            self.stockCode,
            keyword=keyword,
        )
        self._cache[cacheKey] = result
        return result

    def _get_primary(self, name: str, **kwargs) -> Any:
        """모듈 호출 후 primary DataFrame 추출."""
        from dartlab import config

        cacheKey = f"{name}:{sorted(kwargs.items())}" if kwargs else name
        idx = _get_module_index()[name]
        entry = _get_module_registry()[idx]
        label = entry[2]

        if config.verbose and cacheKey not in self._cache and name != "sections":
            print(f"  ▶ {self.corpName} · {label}")

        result = self._call_module(name, **kwargs)
        extractor = entry[3]
        if result is None:
            return None
        if extractor is None:
            return result
        return extractor(result)

    # ── 인덱스·메타 ──

    @staticmethod
    def listing(*, forceRefresh: bool = False) -> pl.DataFrame:
        """KRX 전체 상장법인 목록 (KIND 기준).

        Capabilities:
            - KOSPI + KOSDAQ 전체 상장법인
            - 종목코드, 종목명, 시장구분, 업종

        Args:
            forceRefresh: True면 캐시 무시, KIND에서 재다운로드.

        Returns:
            pl.DataFrame — code, name, market, sector 등.

        Requires:
            데이터: listing (자동 다운로드)
        """
        return getKindList(forceRefresh=forceRefresh)

    @staticmethod
    def search(keyword: str) -> pl.DataFrame:
        """회사명 부분 검색 (KIND 목록 기준).

        Args:
            keyword: 검색어 (부분 일치).

        Returns:
            pl.DataFrame — 매칭 종목 목록.
        """
        return searchName(keyword)

    @staticmethod
    def resolve(codeOrName: str) -> str | None:
        """종목코드 또는 회사명 → 종목코드 변환.

        Args:
            codeOrName: 종목코드 ("005930") 또는 종목명 ("삼성전자").

        Returns:
            str | None — 6자리 종목코드. 못 찾으면 None.
        """
        normalized = codeOrName.strip()
        if re.match(r"^[0-9A-Za-z]{6}$", normalized):
            return normalized.upper()
        return nameToCode(normalized)

    @staticmethod
    def codeName(stockCode: str) -> str | None:
        """종목코드 → 회사명 변환.

        Args:
            stockCode: 6자리 종목코드.

        Returns:
            str | None — 회사명. 못 찾으면 None.
        """
        return codeToName(stockCode)

    @staticmethod
    def status() -> pl.DataFrame:
        """로컬에 보유한 전체 종목 인덱스.

        Capabilities:
            - 로컬 데이터 현황 (종목별 docs/finance/report 보유 여부)
            - 최종 업데이트 일시

        Returns:
            pl.DataFrame — 종목코드, 회사명, docs/finance/report 유무, 최종일시.
        """
        return buildIndex()

    def _filings(self) -> pl.DataFrame:
        """이 종목의 공시 문서 목록 + DART 뷰어 링크."""
        if not self._hasDocs:
            return pl.DataFrame(
                schema={
                    "year": pl.Utf8,
                    "rceptDate": pl.Utf8,
                    "rceptNo": pl.Utf8,
                    "reportType": pl.Utf8,
                    "dartUrl": pl.Utf8,
                }
            )
        df = loadData(self.stockCode)
        docs = (
            df.select("year", "rcept_date", "rcept_no", "report_type")
            .unique(subset=["rcept_no"])
            .with_columns(
                pl.lit(DART_VIEWER).add(pl.col("rcept_no")).alias("dartUrl"),
            )
            .rename(
                {
                    "report_type": "reportType",
                    "rcept_date": "rceptDate",
                    "rcept_no": "rceptNo",
                }
            )
            .sort("year", "rceptDate", descending=[True, True])
        )
        return docs

    def filings(self) -> pl.DataFrame | None:
        """공시 문서 목록 + DART 뷰어 링크.

        Capabilities:
            - 로컬에 보유한 공시 문서 목록
            - 기간별, 문서유형별 정리
            - DART 뷰어 링크 포함

        Returns:
            pl.DataFrame | None — year, rceptDate, rceptNo, reportNm, viewerUrl 등.

        AIContext:
            - 어떤 공시가 보유돼 있는지 확인하여 분석 범위 결정에 활용

        Guide:
            - "이 회사 공시 목록 보여줘" → c.filings()
            - "어떤 보고서가 있어?" → c.filings()로 보유 문서 확인

        SeeAlso:
            - disclosure: OpenDART API 기반 실시간 공시 목록 (로컬 보유가 아닌 전체)
            - liveFilings: 최신 공시 실시간 조회
            - update: 누락 공시 증분 수집

        Requires:
            데이터: docs (자동 다운로드)
        """
        return self._filings()

    def update(self, *, categories: list[str] | None = None) -> dict[str, int]:
        """누락된 최신 공시를 증분 수집.

        Capabilities:
            - DART API로 최신 공시 확인 후 누락분만 수집
            - 카테고리별 선택 수집

        Args:
            categories: ["finance", "docs", "report"]. None이면 전체.

        Returns:
            dict — {카테고리: 수집 건수}.

        AIContext:
            - 데이터 최신성 유지에 활용 — 분석 전 자동 갱신 트리거 가능

        Guide:
            - "최신 공시 반영해줘" → c.update()
            - "데이터 업데이트" → c.update()로 증분 수집

        SeeAlso:
            - filings: 현재 보유 공시 목록 확인
            - disclosure: OpenDART 전체 공시 조회

        Requires:
            API 키: DART_API_KEY
        """
        from dartlab.providers.dart.openapi.freshness import collectMissing

        return collectMissing(self.stockCode, categories=categories)

    def _docsTopicManifest(self) -> pl.DataFrame:
        """→ SectionsAnalyzer.topicManifest()."""
        return self._analyzer.topicManifest()

    def _docsSectionTopics(self) -> list[str]:
        """→ SectionsAnalyzer.sectionTopics()."""
        return self._analyzer.sectionTopics()

    def _docsTopicOutline(self, topic: str | None = None) -> pl.DataFrame:
        """→ SectionsAnalyzer.topicOutline()."""
        return self._analyzer.topicOutline(topic=topic)

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
        """OpenDART 전체 공시 목록 조회.

        Capabilities:
            - 전체 공시유형 조회 (정기, 주요사항, 발행, 지분, 외부감사 등)
            - 기간, 유형, 키워드 필터링
            - 최종보고서만 필터 (정정 이전 제외)

        Args:
            start: 조회 시작일 (YYYYMMDD 또는 YYYY-MM-DD). None이면 최근 days일.
            end: 조회 종료일. None이면 오늘.
            days: start/end 없을 때 최근 일수. 기본 365.
            type: 공시유형 필터 (A=정기, B=주요사항, C=발행, D=지분, E=기타, F=외부감사). None이면 전체.
            keyword: 제목/회사명 키워드 필터.
            finalOnly: True면 최종보고서만 (정정 이전 제외).

        Returns:
            pl.DataFrame -- docId, filedAt, title, formType 등 공시 목록.

        Requires:
            API 키: DART_API_KEY

        Example::

            c = Company("005930")
            c.disclosure()                  # 최근 1년 전체 공시
            c.disclosure(days=30)           # 최근 30일
            c.disclosure(type="A")          # 정기공시만
            c.disclosure(keyword="사업보고서")

        AIContext:
            - 특정 유형 공시 존재 여부 확인 → 분석 범위 동적 결정
            - 최근 공시 빈도/유형 패턴으로 기업 이벤트 감지

        Guide:
            - "최근 공시 뭐 나왔어?" → c.disclosure(days=30)
            - "주요사항 공시 있어?" → c.disclosure(type="B")
            - "사업보고서 언제 나왔어?" → c.disclosure(keyword="사업보고서")

        SeeAlso:
            - liveFilings: 실시간 최신 공시 (정규화된 포맷)
            - readFiling: 공시 원문 텍스트 읽기
            - filings: 로컬 보유 공시 목록
        """
        from dartlab.providers.dart.openapi.dart import Dart

        d = Dart()
        s = d(self.stockCode)
        df = s.filings(start, end, type=type, final=finalOnly)
        if df.is_empty():
            return df
        if keyword:
            df = filterFilingsByKeyword(df, keyword=keyword, columns=["report_nm", "corp_name", "flr_nm"])
        return df

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
        """OpenDART 기준 실시간 공시 목록 조회.

        Capabilities:
            - OpenDART API 실시간 공시 조회
            - 기간, 건수, 키워드 필터링
            - 정규화된 컬럼 (docId, filedAt, title, formType 등)

        Args:
            start: 조회 시작일 (YYYYMMDD 또는 YYYY-MM-DD). None이면 최근 days일.
            end: 조회 종료일. None이면 오늘.
            days: start/end 없을 때 최근 일수. None이면 기본값 적용.
            limit: 최대 반환 건수. 기본 20.
            keyword: 제목/회사명 키워드 필터.
            forms: 미사용 (DART는 forms 개념 없음).
            finalOnly: True면 최종보고서만 (정정 이전 제외).

        Returns:
            pl.DataFrame -- docId, filedAt, title, formType, docUrl, viewerUrl 등 정규화된 공시 목록.

        Requires:
            API 키: DART_API_KEY

        Example::

            c = Company("005930")
            c.liveFilings()                 # 최근 공시 20건
            c.liveFilings(days=7)           # 최근 7일
            c.liveFilings(keyword="배당")   # 키워드 필터

        AIContext:
            - 최신 공시 모니터링으로 기업 이벤트(배당, 유증, 합병 등) 실시간 감지
            - readFiling()과 조합하여 최신 공시 원문 분석

        Guide:
            - "최근 공시 확인해줘" → c.liveFilings()
            - "이번 주 공시 있어?" → c.liveFilings(days=7)
            - "배당 관련 공시" → c.liveFilings(keyword="배당")

        SeeAlso:
            - disclosure: 과거 전체 공시 이력 조회
            - readFiling: 공시 원문 텍스트 읽기
            - watch: 공시 변화 중요도 스코어링
        """
        del forms  # DART는 forms 개념이 없다.

        startDate, endDate = resolveDateWindow(start, end, days=days)
        cacheKey = f"liveFilings:{startDate}:{endDate}:{limit}:{keyword}:{finalOnly}"
        if cacheKey in self._cache:
            return self._cache[cacheKey]

        from dartlab.core.guidance import progress
        from dartlab.providers.dart.openapi.dart import OpenDart

        progress(f"{self.corpName} 최신 공시 목록 조회 중... (OpenDART, {startDate}~{endDate})")
        df = OpenDart().filings(
            self.stockCode,
            startDate,
            endDate,
            final=finalOnly,
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
                    "corpName": pl.Utf8,
                    "stockCode": pl.Utf8,
                    "rceptNo": pl.Utf8,
                    "reportNm": pl.Utf8,
                    "viewerUrl": pl.Utf8,
                    "corpCls": pl.Utf8,
                }
            )
            self._cache[cacheKey] = result
            return result

        normalized = (
            filterFilingsByKeyword(df, keyword=keyword, columns=["report_nm", "corp_name", "flr_nm"])
            .with_columns(
                [
                    pl.col("rcept_no").cast(pl.Utf8).alias("docId"),
                    pl.col("rcept_dt").cast(pl.Utf8).alias("filedAt"),
                    pl.col("report_nm").cast(pl.Utf8).alias("title"),
                    pl.col("report_nm").cast(pl.Utf8).alias("formType"),
                    pl.lit(DART_VIEWER).add(pl.col("rcept_no").cast(pl.Utf8)).alias("docUrl"),
                    pl.lit(DART_VIEWER).add(pl.col("rcept_no").cast(pl.Utf8)).alias("indexUrl"),
                    pl.lit("KR").alias("market"),
                    pl.col("corp_name").cast(pl.Utf8).alias("corpName"),
                    pl.col("stock_code").cast(pl.Utf8).alias("stockCode"),
                    pl.col("rcept_no").cast(pl.Utf8).alias("rceptNo"),
                    pl.col("report_nm").cast(pl.Utf8).alias("reportNm"),
                    pl.lit(DART_VIEWER).add(pl.col("rcept_no").cast(pl.Utf8)).alias("viewerUrl"),
                    pl.col("corp_cls").cast(pl.Utf8).alias("corpCls"),
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
                    "corpName",
                    "stockCode",
                    "rceptNo",
                    "reportNm",
                    "viewerUrl",
                    "corpCls",
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
        sections: bool = False,
    ) -> dict[str, Any]:
        """접수번호 또는 liveFilings row로 공시 원문을 읽는다.

        Capabilities:
            - 접수번호(str) 직접 지정 또는 DataFrame row 자동 파싱
            - 전문 텍스트 또는 ZIP 기반 구조화 섹션 반환
            - 텍스트 길이 제한 (truncation) 지원

        Args:
            filing: 접수번호(str) 또는 disclosure()/liveFilings() row.
            maxChars: 텍스트 최대 길이 (sections=False일 때만 적용).
            sections: True면 ZIP 기반 구조화된 섹션 목록 반환.

        Returns:
            dict -- rceptNo, viewerUrl, text/sections 등 원문 정보.

        Requires:
            API 키: DART_API_KEY

        Example::

            c = Company("005930")
            result = c.readFiling("20240315000123")
            result = c.readFiling("20240315000123", sections=True)

        AIContext:
            - 공시 원문 텍스트를 LLM 컨텍스트에 주입하여 심층 분석 수행
            - sections=True로 구조화하면 특정 섹션만 선택적 분석 가능

        Guide:
            - "이 공시 내용 보여줘" → c.readFiling(접수번호)
            - "공시 원문 분석해줘" → c.readFiling()으로 원문 확보 후 ask()로 분석

        SeeAlso:
            - liveFilings: 최신 공시 목록에서 접수번호 확인
            - disclosure: 과거 공시 목록에서 접수번호 확인
        """
        record = filingRecord(filing) or {}

        if isinstance(filing, str):
            text = filing.strip()
            if text.isdigit():
                rceptNo = text
                viewerUrl = f"{DART_VIEWER}{text}"
            else:
                match = _RCEPT_NO_PATTERN.search(text)
                rceptNo = match.group(1) if match else ""
                viewerUrl = text
        else:
            viewerUrl = str(record.get("viewerUrl") or record.get("docUrl") or "")
            rceptNo = str(record.get("rceptNo") or record.get("docId") or "")
            if not rceptNo and viewerUrl:
                match = _RCEPT_NO_PATTERN.search(viewerUrl)
                if match:
                    rceptNo = match.group(1)

        if not rceptNo:
            raise ValueError("DART filing 읽기에는 rceptNo 또는 rcpNo가 포함된 viewer URL이 필요합니다.")

        from dartlab.core.guidance import progress

        if sections:
            from dartlab.providers.dart.openapi.client import DartClient
            from dartlab.providers.dart.openapi.zipCollector import _collectOneZip

            progress(f"{self.corpName} 공시 ZIP 다운로드 중... ({rceptNo})")
            client = DartClient()
            parsed = _collectOneZip(client, rceptNo)
            return {
                "docId": rceptNo,
                "market": "KR",
                "title": record.get("title") or record.get("reportNm") or record.get("report_nm") or "",
                "docUrl": viewerUrl or f"{DART_VIEWER}{rceptNo}",
                "viewerUrl": viewerUrl or f"{DART_VIEWER}{rceptNo}",
                "sections": parsed or [],
            }

        from dartlab.providers.dart.openapi.dart import OpenDart

        progress(f"{self.corpName} 공시 원문 다운로드 중... ({rceptNo})")
        rawText = OpenDart().documentText(rceptNo)
        progress(f"{self.corpName} 공시 원문 정리 중... ({rceptNo})")
        rawPreview, truncated = truncateText(rawText, maxChars=maxChars)
        return {
            "docId": rceptNo,
            "market": "KR",
            "title": record.get("title") or record.get("reportNm") or "",
            "docUrl": viewerUrl or f"{DART_VIEWER}{rceptNo}",
            "viewerUrl": viewerUrl or f"{DART_VIEWER}{rceptNo}",
            "raw": rawPreview,
            "text": rawPreview,
            "truncated": truncated,
        }

    # ── 원본 데이터 (property) ──

    @property
    def rawDocs(self) -> pl.DataFrame | None:
        """공시 문서 원본 parquet 전체 (가공 전).

        Capabilities:
            - HuggingFace docs 카테고리 원본 데이터 직접 접근
            - 가공/정규화 이전 상태 그대로 반환

        Returns:
            pl.DataFrame | None -- 원본 docs parquet. 데이터 없으면 None.

        Requires:
            데이터: HuggingFace docs parquet (자동 다운로드)

        Example::

            c = Company("005930")
            c.rawDocs              # 삼성전자 공시 문서 원본
            c.rawDocs.columns      # 컬럼 목록 확인

        AIContext:
            - 원본 데이터 구조 파악 — 파싱 전 상태로 디버깅/검증에 활용

        Guide:
            - "원본 공시 데이터 보여줘" → c.rawDocs
            - "가공 전 데이터 확인" → c.rawDocs

        SeeAlso:
            - sections: docs 가공 후 topic x period 통합 지도
            - rawFinance: 재무제표 원본 데이터
            - rawReport: 정기보고서 원본 데이터
        """
        if not self._hasDocs:
            self._hintOnce("rawDocs", "rawDocs", "docs")
            return None
        cacheKey = "_rawDocs"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        df = loadData(self.stockCode, category="docs")
        self._cache[cacheKey] = df
        return df

    @property
    def rawFinance(self) -> pl.DataFrame | None:
        """재무제표 원본 parquet 전체 (가공 전).

        Capabilities:
            - HuggingFace finance 카테고리 원본 데이터 직접 접근
            - XBRL 정규화 이전 상태 그대로 반환

        Returns:
            pl.DataFrame | None -- 원본 finance parquet. 데이터 없으면 None.

        Requires:
            데이터: HuggingFace finance parquet (자동 다운로드)

        Example::

            c = Company("005930")
            c.rawFinance           # 삼성전자 재무제표 원본
            c.rawFinance.columns   # 컬럼 목록 확인

        AIContext:
            - XBRL 정규화 전 원본 구조 파악 — 매핑 검증에 활용

        Guide:
            - "원본 재무 데이터 보여줘" → c.rawFinance
            - "XBRL 원본 확인" → c.rawFinance

        SeeAlso:
            - BS: 가공된 재무상태표
            - IS: 가공된 손익계산서
            - rawDocs: 공시 문서 원본
        """
        if not self._hasFinanceParquet:
            self._hintOnce("rawFinance", "rawFinance", "finance")
            return None
        cacheKey = "_rawFinance"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        df = loadData(self.stockCode, category="finance")
        self._cache[cacheKey] = df
        return df

    @property
    def rawReport(self) -> pl.DataFrame | None:
        """정기보고서 원본 parquet 전체 (가공 전).

        Capabilities:
            - HuggingFace report 카테고리 원본 데이터 직접 접근
            - 정기보고서 API 데이터 가공 이전 상태 반환

        Returns:
            pl.DataFrame | None -- 원본 report parquet. 데이터 없으면 None.

        Requires:
            데이터: HuggingFace report parquet (자동 다운로드)

        Example::

            c = Company("005930")
            c.rawReport            # 삼성전자 정기보고서 원본
            c.rawReport.columns    # 컬럼 목록 확인

        AIContext:
            - 정기보고서 API 원본 확인 — report topic 매핑 검증에 활용

        Guide:
            - "원본 보고서 데이터 보여줘" → c.rawReport
            - "정기보고서 원본 확인" → c.rawReport

        SeeAlso:
            - rawDocs: 공시 문서 원본
            - rawFinance: 재무제표 원본
            - show: 가공된 topic 데이터 조회
        """
        if not self._hasReport:
            self._hintOnce("rawReport", "rawReport", "report")
            return None
        cacheKey = "_rawReport"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        df = loadData(self.stockCode, category="report")
        self._cache[cacheKey] = df
        return df

    @property
    def notes(self):
        """K-IFRS 주석사항 접근자.

        Capabilities:
            - K-IFRS 재무제표 주석(notes) 데이터 접근
            - 주석 항목별 조회

        Returns:
            NotesAccessor -- 주석사항 조회 객체.

        Requires:
            데이터: HuggingFace finance parquet (자동 다운로드)

        Example::

            c = Company("005930")
            c.notes                # 주석사항 접근자

        AIContext:
            - K-IFRS 주석에서 회계정책, 우발부채, 관계사 거래 등 정성 정보 추출

        Guide:
            - "주석사항 보여줘" → c.notes
            - "회계정책 확인" → c.notes에서 해당 항목 조회

        SeeAlso:
            - BS: 재무상태표 (주석이 보충하는 본문)
            - rawFinance: 재무 원본 데이터
        """
        return self._notesAccessor

    def _docsSectionsFreq(self, freqScope: str, *, includeMixed: bool = True) -> pl.DataFrame | None:
        """→ SectionsAnalyzer.sectionsFreq()."""
        return self._analyzer.sectionsFreq(freqScope, includeMixed=includeMixed)

    def _docsSectionsOrdered(self, *, recentFirst: bool = True, annualAsQ4: bool = True) -> pl.DataFrame | None:
        """→ SectionsAnalyzer.sectionsOrdered()."""
        return self._analyzer.sectionsOrdered(recentFirst=recentFirst, annualAsQ4=annualAsQ4)

    def _docsSectionsCoverage(
        self, *, topic: str | None = None, recentFirst: bool = True, annualAsQ4: bool = True
    ) -> pl.DataFrame | None:
        """→ SectionsAnalyzer.sectionsCoverage()."""
        return self._analyzer.sectionsCoverage(topic=topic, recentFirst=recentFirst, annualAsQ4=annualAsQ4)

    def _docsSectionsSemanticRegistry(
        self,
        *,
        topic: str | None = None,
        freqScope: str = "all",
        includeMixed: bool = True,
        collisionsOnly: bool = False,
    ) -> pl.DataFrame | None:
        """→ SectionsAnalyzer.sectionsSemanticRegistry()."""
        return self._analyzer.sectionsSemanticRegistry(
            topic=topic, freqScope=freqScope, includeMixed=includeMixed, collisionsOnly=collisionsOnly
        )

    def _docsSectionsStructureRegistry(
        self,
        *,
        topic: str | None = None,
        freqScope: str = "all",
        includeMixed: bool = True,
        collisionsOnly: bool = False,
        nodeType: str | None = None,
    ) -> pl.DataFrame | None:
        """→ SectionsAnalyzer.sectionsStructureRegistry()."""
        return self._analyzer.sectionsStructureRegistry(
            topic=topic,
            freqScope=freqScope,
            includeMixed=includeMixed,
            collisionsOnly=collisionsOnly,
            nodeType=nodeType,
        )

    def _docsSectionsStructureEvents(
        self,
        *,
        topic: str | None = None,
        freqScope: str = "all",
        includeMixed: bool = True,
        changedOnly: bool = True,
        nodeType: str | None = None,
    ) -> pl.DataFrame | None:
        """→ SectionsAnalyzer.sectionsStructureEvents()."""
        return self._analyzer.sectionsStructureEvents(
            topic=topic,
            freqScope=freqScope,
            includeMixed=includeMixed,
            changedOnly=changedOnly,
            nodeType=nodeType,
        )

    def _docsSectionsStructureSummary(
        self,
        *,
        topic: str | None = None,
        freqScope: str = "all",
        includeMixed: bool = True,
        nodeType: str | None = None,
    ) -> pl.DataFrame | None:
        """→ SectionsAnalyzer.sectionsStructureSummary()."""
        return self._analyzer.sectionsStructureSummary(
            topic=topic, freqScope=freqScope, includeMixed=includeMixed, nodeType=nodeType
        )

    def _docsSectionsStructureChanges(
        self,
        *,
        topic: str | None = None,
        freqScope: str = "all",
        includeMixed: bool = True,
        nodeType: str | None = None,
        latestOnly: bool = True,
        changedOnly: bool = True,
    ) -> pl.DataFrame | None:
        """→ SectionsAnalyzer.sectionsStructureChanges()."""
        return self._analyzer.sectionsStructureChanges(
            topic=topic,
            freqScope=freqScope,
            includeMixed=includeMixed,
            nodeType=nodeType,
            latestOnly=latestOnly,
            changedOnly=changedOnly,
        )

    def _retrievalBlocks(self) -> pl.DataFrame | None:
        if not self._hasDocs:
            return None
        cacheKey = "retrievalBlocks"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        from dartlab.providers.dart.docs.sections import retrievalBlocks

        result = retrievalBlocks(self.stockCode)
        self._cache[cacheKey] = result
        return result

    def _contextSlices(self) -> pl.DataFrame | None:
        if not self._hasDocs:
            return None
        cacheKey = "contextSlices"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        from dartlab.providers.dart.docs.sections import contextSlices

        result = contextSlices(self.stockCode)
        self._cache[cacheKey] = result
        return result

    def _topicSubtables(self, topic: str):
        """→ SectionsAnalyzer.topicSubtables()."""
        return self._analyzer.topicSubtables(topic)

    def _sectionsSubtopicWide(self, topic: str) -> pl.DataFrame | None:
        """→ SectionsAnalyzer.subtopicWide()."""
        return self._analyzer.subtopicWide(topic)

    def _sectionsSubtopicLong(self, topic: str) -> pl.DataFrame | None:
        """→ SectionsAnalyzer.subtopicLong()."""
        return self._analyzer.subtopicLong(topic)

    def _safePrimary(self, name: str) -> pl.DataFrame | None:
        try:
            payload = self._get_primary(name)
        except (KeyError, ValueError, TypeError, FileNotFoundError, AttributeError):
            import logging

            logging.getLogger(__name__).debug("_safePrimary(%s) failed", name, exc_info=True)
            return None
        return payload if isinstance(payload, pl.DataFrame) else None

    def _sceMatrix(self):
        if not self._hasFinance:
            return None
        cacheKey = "_sceMatrix_CFS"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        from dartlab.providers.dart.finance.pivot import buildSceMatrix

        result = buildSceMatrix(self.stockCode)
        self._cache[cacheKey] = result
        return result

    def _sceSeriesAnnual(self):
        if not self._hasFinance:
            return None
        cacheKey = "_sceAnnual_CFS"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        from dartlab.providers.dart.finance.pivot import buildSceAnnual

        result = buildSceAnnual(self.stockCode)
        self._cache[cacheKey] = result
        return result

    def _sce(self) -> pl.DataFrame | None:
        cacheKey = "_sceDataFrame_CFS"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        result = self._sceSeriesAnnual()
        if result is None:
            self._cache[cacheKey] = None
            return None
        series, years = result
        df = _sceToDataFrame(series, years)
        self._cache[cacheKey] = df
        return df

    def _financeCisAnnual(self):
        if not self._hasFinance:
            return None
        cacheKey = "_financeCISAnnual_CFS"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        result = _financeCisAnnual(self.stockCode, "CFS")
        self._cache[cacheKey] = result
        return result

    def _financeCisQuarterly(self):
        """CIS 분기별 시계열 (연간 합산 없이)."""
        if not self._hasFinance:
            return None
        cacheKey = "_financeCISQuarterly_CFS"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        result = _financeCisQuarterly(self.stockCode, "CFS")
        self._cache[cacheKey] = result
        return result

    def _ratioSeries(self):
        if not self._hasFinance:
            return None
        cacheKey = "_ratioSeries_Q_CFS"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        qResult = self.finance.timeseries
        if qResult is None:
            return None
        qSeries, periods = qResult
        # 2016-Q1 → 2016Q1 포맷 통일
        normalizedPeriods = [p.replace("-", "") for p in periods]
        from dartlab.core.finance.ratios import calcRatioSeries, toSeriesDict

        archetypeOverride = _ratioArchetypeOverrideForIndustryGroup(getattr(self.sector, "industryGroup", None))
        rs = calcRatioSeries(qSeries, normalizedPeriods, archetypeOverride=archetypeOverride, yoyLag=4)
        result = toSeriesDict(rs)
        self._cache[cacheKey] = result
        return result

    def _financeOrDocsStatement(self, sjDiv: str) -> pl.DataFrame | None:
        if sjDiv == "CIS":
            cisQ = self._financeCisQuarterly() if self._hasFinance else None
            if cisQ is not None:
                series, periods = cisQ
                normalizedPeriods = [p.replace("-", "") for p in periods]
                df = _financeToDataFrame(series, normalizedPeriods, "CIS")
                if df is not None:
                    return df
        df = self._financeStmt(sjDiv) if self._hasFinance else None
        if df is not None:
            return df
        r = self._call_module("statements")
        return getattr(r, sjDiv, None) if r else None

    # ── 재무제표 (property) ──
    # finance(XBRL) 우선 → docs fallback

    def _financeStmt(self, sjDiv: str) -> pl.DataFrame | None:
        """finance 분기별 시계열에서 sjDiv DataFrame 생성 (캐싱)."""
        cacheKey = f"_financeStmt_{sjDiv}"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        qResult = self.timeseries
        if qResult is None:
            return None
        series, periods = qResult
        # 2016-Q1 → 2016Q1 포맷 통일
        normalizedPeriods = [p.replace("-", "") for p in periods]
        df = _financeToDataFrame(series, normalizedPeriods, sjDiv)
        self._cache[cacheKey] = df
        return df

    @property
    def BS(self) -> pl.DataFrame | None:
        """재무상태표 (Balance Sheet) — 계정명 × 기간 DataFrame.

        Capabilities:
            - XBRL 정규화 재무상태표 (finance 우선)
            - docs 서술형 fallback
            - 최대 10년 분기별 시계열

        AIContext:
            - ask()/chat()에서 자산/부채/자본 구조 분석 컨텍스트

        Guide:
            - "재무상태표 보여줘" → c.BS
            - "자산/부채 구조" → c.BS로 확인
            - "유동비율은?" → c.ratios 또는 c.BS에서 계산

        SeeAlso:
            - IS: 손익계산서 (수익성 분석)
            - CF: 현금흐름표 (현금창출력)
            - ratios: 재무비율 (BS 기반 안정성 비율 포함)
            - select: 특정 계정만 추출 + 시각화

        Returns:
            pl.DataFrame — 계정명 | 2024Q4 | 2024Q3 | ... 또는 None.

        Requires:
            데이터: finance 또는 docs (자동 다운로드)

        Example::

            c = Company("005930")
            c.BS  # 재무상태표
        """
        return self._financeProperty("BS")

    @property
    def IS(self) -> pl.DataFrame | None:
        """손익계산서 (Income Statement) — 계정명 × 기간 DataFrame.

        Capabilities:
            - XBRL 정규화 손익계산서 (finance 우선)
            - docs 서술형 fallback
            - 최대 10년 분기별 시계열

        AIContext:
            - ask()/chat()에서 수익성/매출 구조 분석 컨텍스트

        Guide:
            - "손익계산서 보여줘" → c.IS
            - "매출/영업이익 추이" → c.IS 또는 c.select("IS", ["매출액", "영업이익"])
            - "수익 구조 분석" → c.IS + c.analysis("수익구조")

        SeeAlso:
            - BS: 재무상태표 (자산/부채 구조)
            - CF: 현금흐름표 (실제 현금 기반)
            - CIS: 포괄손익계산서 (기타포괄손익 포함)
            - select: 특정 계정 추출 + 시각화

        Returns:
            pl.DataFrame — 계정명 | 2024Q4 | 2024Q3 | ... 또는 None.

        Requires:
            데이터: finance 또는 docs (자동 다운로드)

        Example::

            c = Company("005930")
            c.IS  # 손익계산서
        """
        return self._financeProperty("IS")

    @property
    def CIS(self) -> pl.DataFrame | None:
        """포괄손익계산서 (Comprehensive Income Statement) — 계정명 × 기간 DataFrame.

        Capabilities:
            - XBRL 정규화 포괄손익계산서 (finance 우선)
            - docs 서술형 fallback
            - 기타포괄손익 항목 포함

        AIContext:
            - ask()/chat()에서 기타포괄손익/총포괄이익 분석 컨텍스트

        Guide:
            - "포괄손익계산서 보여줘" → c.CIS
            - "기타포괄손익 항목은?" → c.CIS

        SeeAlso:
            - IS: 일반 손익계산서 (당기순이익까지)
            - SCE: 자본변동표 (포괄손익이 자본에 미치는 영향)

        Returns:
            pl.DataFrame — 계정명 | 2024Q4 | 2024Q3 | ... 또는 None.

        Requires:
            데이터: finance 또는 docs (자동 다운로드)

        Example::

            c = Company("005930")
            c.CIS  # 포괄손익계산서
        """
        return self._financeProperty("CIS")

    @property
    def CF(self) -> pl.DataFrame | None:
        """현금흐름표 (Cash Flow Statement) — 계정명 × 기간 DataFrame.

        Capabilities:
            - XBRL 정규화 현금흐름표 (finance 우선)
            - docs 서술형 fallback
            - 영업/투자/재무 활동 분류

        AIContext:
            - ask()/chat()에서 현금창출력/투자/재무활동 분석 컨텍스트

        Guide:
            - "현금흐름표 보여줘" → c.CF
            - "영업현금흐름 추이" → c.select("CF", ["영업활동으로인한현금흐름"])
            - "FCF 확인" → c.ratios에서 FCF 비율 또는 c.CF에서 직접 계산

        SeeAlso:
            - IS: 손익계산서 (발생주의 vs 현금주의 비교)
            - BS: 재무상태표 (현금성자산 확인)
            - ratios: 재무비율 (현금흐름 관련 비율 포함)

        Returns:
            pl.DataFrame — 계정명 | 2024Q4 | 2024Q3 | ... 또는 None.

        Requires:
            데이터: finance 또는 docs (자동 다운로드)

        Example::

            c = Company("005930")
            c.CF  # 현금흐름표
        """
        return self._financeProperty("CF")

    @property
    def sections(self) -> pl.DataFrame | None:
        """sections — docs + finance + report 통합 지도.

        docs 수평화 위에 finance/report를 같은 topic 안에 끼워넣는다.
        - docs에 있는 topic (dividend 등) → docs 블록 뒤에 report 행 append
        - docs에 없는 topic (BS, auditContract 등) → 해당 chapter에 독립 삽입

        Capabilities:
            - topic × period 수평화 통합 DataFrame
            - docs/finance/report 3-source 병합
            - show(topic)/trace(topic)/diff() 의 근간 데이터

        AIContext:
            - 회사 전체 지도 — 모든 분석의 출발점
            - ask()/chat()에서 topic 탐색 컨텍스트

        Guide:
            - "이 회사 전체 데이터 지도" → c.sections
            - "어떤 topic이 있어?" → c.sections 또는 c.topics

        SeeAlso:
            - topics: sections 기반 topic 요약 (더 간결)
            - show: 특정 topic 데이터 조회
            - index: 전체 구조 메타데이터 목차

        Returns:
            pl.DataFrame — chapter | topic | period | source | ... 또는 None.

        Requires:
            데이터: docs (필수), finance/report (선택, 자동 다운로드)

        Example::

            c = Company("005930")
            c.sections  # 전체 sections 지도
        """
        cacheKey = "_sections"
        if cacheKey in self._cache:
            return self._cache[cacheKey]

        sectionsSource = self.docs.sections
        if sectionsSource is None:
            self._hintOnce("sections", "sections", "docs")
            self._cache[cacheKey] = None
            return None

        docsSec = sectionsSource.raw
        periodCols = [c for c in docsSec.columns if _isPeriodColumn(c)]
        chapterMap = self._chapterMap()

        if "source" not in docsSec.columns:
            docsSec = docsSec.with_columns(pl.lit("docs").alias("source"))

        docsSchema = dict(docsSec.schema)
        if "source" not in docsSchema:
            docsSchema["source"] = pl.Utf8
        metaCols = [c for c in docsSec.columns if c not in periodCols]

        # finance/report에서 추가할 행 수집
        # key: topic → (chapter, source, maxBlockOrder)
        topicExtras: dict[str, list[dict[str, Any]]] = {}

        def _baseExtraRow(*, chapter: str, topic: str, source: str) -> dict[str, Any]:
            row = {col: None for col in metaCols}
            row.update(
                {
                    "chapter": chapter,
                    "topic": topic,
                    "blockType": "table",
                    "source": source,
                }
            )
            for p in periodCols:
                row[p] = None
            return row

        if self._hasFinance:
            for ft in ("BS", "IS", "CIS", "CF", "SCE"):
                if getattr(self.finance, ft, None) is not None:
                    topicExtras.setdefault(ft, []).append(_baseExtraRow(chapter="III", topic=ft, source="finance"))
            if self._ratioSeries() is not None:
                topicExtras.setdefault("ratios", []).append(
                    _baseExtraRow(chapter="III", topic="ratios", source="finance")
                )

        if self.rawReport is not None:
            try:
                for apiType in self.report.availableApiTypes:
                    topic = apiType
                    if topic in _API_TYPE_TO_TOPIC:
                        topic = _API_TYPE_TO_TOPIC[topic]
                    chapter = chapterMap.get(topic, "X")
                    topicExtras.setdefault(topic, []).append(
                        _baseExtraRow(chapter=chapter, topic=topic, source="report")
                    )
            except (ValueError, KeyError, AttributeError) as e:
                import logging

                logging.getLogger(__name__).warning("sections report merge failed for %s: %s", self.stockCode, e)

        if not topicExtras:
            self._cache[cacheKey] = docsSec
            return docsSec

        # topic 순서대로 순회하면서 extra 행을 끼워넣기
        docsTopics = docsSec.get_column("topic").drop_nulls().unique(maintain_order=True).to_list()

        schema = docsSchema

        result_frames: list[pl.DataFrame] = []
        insertedExtras: set[str] = set()

        for topic in docsTopics:
            # 이 topic의 docs 행
            topicDocs = docsSec.filter(pl.col("topic") == topic)
            result_frames.append(topicDocs)

            # 이 topic에 대응하는 extra 행 → docs 블록 뒤에 append
            if topic in topicExtras:
                maxBo = topicDocs["blockOrder"].max()
                nextBo = (maxBo + 1) if maxBo is not None else 0
                for extra in topicExtras[topic]:
                    extra["blockOrder"] = nextBo
                    nextBo += 1
                result_frames.append(pl.DataFrame(topicExtras[topic], schema=schema))
                insertedExtras.add(topic)

        # docs에 없는 extra topic → 해당 chapter 위치에 독립 삽입
        orphanRows: list[dict[str, Any]] = []
        for topic, extras in topicExtras.items():
            if topic in insertedExtras:
                continue
            for extra in extras:
                extra["blockOrder"] = 0
                orphanRows.append(extra)

        if orphanRows:
            # chapter별로 그룹핑해서 해당 chapter의 마지막에 삽입
            orphanDf = pl.DataFrame(orphanRows, schema=schema)
            # result_frames 끝에 chapter 순서로 삽입
            for ch in _CHAPTER_TITLES.keys():
                chOrphans = orphanDf.filter(pl.col("chapter") == ch)
                if not chOrphans.is_empty():
                    # 해당 chapter의 마지막 위치 찾기
                    insertIdx = len(result_frames)
                    for i, f in enumerate(result_frames):
                        if "chapter" in f.columns:
                            chapters = f["chapter"].to_list()
                            if ch in chapters:
                                insertIdx = i + 1
                    result_frames.insert(insertIdx, chOrphans)

        if not result_frames:
            from dartlab.providers.dart.docs.sections import reorderPeriodColumns

            result = reorderPeriodColumns(docsSec, descending=True, annualAsQ4=True)
            self._cache[cacheKey] = result
            return result

        merged = pl.concat(result_frames, how="diagonal_relaxed")

        from dartlab.providers.dart.docs.sections import reorderPeriodColumns

        merged = reorderPeriodColumns(merged, descending=True, annualAsQ4=True)
        self._cache[cacheKey] = merged
        return merged

    def _profileTable(self) -> pl.DataFrame | None:
        cacheKey = "_sectionProfileTable"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        from dartlab.providers.dart.docs.sections.artifacts import loadSectionProfileTable

        table = loadSectionProfileTable()
        self._cache[cacheKey] = table
        return table

    def _chapterMap(self) -> dict[str, str]:
        cacheKey = "_chapterMap"
        if cacheKey in self._cache:
            return self._cache[cacheKey]

        mapping: dict[str, str] = {
            "BS": "III",
            "IS": "III",
            "CIS": "III",
            "CF": "III",
            "SCE": "III",
            "ratios": "III",
            "audit": "V",
            "auditContract": "V",
            "nonAuditContract": "V",
            "majorHolder": "VII",
            "majorHolderChange": "VII",
            "minorityHolder": "VII",
            "treasuryStock": "VII",
            "stockTotal": "VII",
            "capitalChange": "VII",
            "shareholderMeeting": "VII",
            "employee": "VIII",
            "executive": "VIII",
            "topPay": "VIII",
            "unregisteredExecutivePay": "VIII",
            "executivePayAllTotal": "VIII",
            "executivePayIndividual": "VIII",
            "investedCompany": "IX",
            "relatedPartyTx": "IX",
            "publicOfferingUsage": "X",
            "privateOfferingUsage": "X",
            "corporateBond": "X",
            "shortTermBond": "X",
            "auditOpinion": "V",
            "outsideDirector": "VI",
            "executivePayByType": "VIII",
            "executivePayTotal": "VIII",
        }

        table = self._profileTable()
        if table is not None and not table.is_empty():
            canonicalCol = "canonicalTopic" if "canonicalTopic" in table.columns else "topic"
            grouped = (
                table.filter(pl.col(canonicalCol).is_not_null(), pl.col("chapter").is_not_null())
                .group_by([canonicalCol, "chapter"])
                .agg(pl.len().alias("count"))
                .sort(["count", canonicalCol], descending=[True, False])
            )
            for row in grouped.iter_rows(named=True):
                topic = row.get(canonicalCol)
                chapter = row.get("chapter")
                if isinstance(topic, str) and isinstance(chapter, str) and topic not in mapping:
                    mapping[topic] = chapter

        self._cache[cacheKey] = mapping
        return mapping

    def _chapterForTopic(self, topic: str) -> str:
        if topic in self._chapterMap():
            return self._chapterMap()[topic]
        if self.notes is not None:
            from dartlab.providers.dart.docs.notes import _REGISTRY as _NOTES_REGISTRY

            if topic in _NOTES_REGISTRY:
                return "XI"
        return "XII"

    def _boardTopics(self) -> list[str]:
        cacheKey = "_boardTopics"
        if cacheKey in self._cache:
            return self._cache[cacheKey]

        ordered = self._docsSectionTopics()
        seen = set(ordered)

        if self._hasFinanceParquet:
            for ft in ("BS", "IS", "CIS", "CF", "SCE", "ratios"):
                if ft in seen:
                    continue
                ordered.append(ft)
                seen.add(ft)

        self._cache[cacheKey] = ordered
        return ordered

    def _topicLabel(self, topic: str) -> str:
        if topic == "CIS":
            return "포괄손익계산서"
        if topic == "SCE":
            return "자본변동표"
        if topic in _TOPIC_LABELS:
            return _TOPIC_LABELS[topic]
        entry = _getEntry(topic)
        if entry is not None:
            return entry.label
        for name, label in _get_all_properties():
            if name == topic:
                return label
        return topic

    def _buildBlockIndex(self, topicRows: pl.DataFrame) -> pl.DataFrame:
        """topic의 블록 목차 DataFrame."""
        from dartlab.core.show import buildBlockIndex

        return buildBlockIndex(topicRows)

    def _showFinanceTopic(self, topic: str, *, period: str | None = None) -> pl.DataFrame | None:
        """finance source topic의 실제 데이터 반환."""
        if topic == "ratios":
            ratioSeries = self._ratioSeries()
            if ratioSeries is None:
                return None
            series, years = ratioSeries
            templateKey = _ratioTemplateKeyForIndustryGroup(getattr(self.sector, "industryGroup", None))
            fieldNames = _RATIO_TEMPLATE_FIELDS.get(templateKey)
            return self._applyPeriodFilter(_ratioSeriesToDataFrame(series, years, fieldNames=fieldNames), period)
        df = getattr(self.finance, topic, None)
        if df is None:
            return None
        return self._applyPeriodFilter(df, period)

    def _traceFinanceTopic(self, topic: str, *, period: str | None = None) -> dict[str, Any] | None:
        """finance authoritative topic provenance를 facts 빌드 없이 직접 계산."""
        from dartlab.providers.dart.docs.sections import rawPeriod

        requestedPeriod = rawPeriod(period) if isinstance(period, str) else period
        rows: list[tuple[str, str]] = []

        def collect(series: dict[str, list[Any]] | None, years: list[Any], payloadTopic: str) -> None:
            if not series:
                return
            for item, values in series.items():
                for idx, year in enumerate(years):
                    if requestedPeriod is not None and str(year) != requestedPeriod:
                        continue
                    value = values[idx] if idx < len(values) else None
                    if value is None:
                        continue
                    rows.append((f"finance:{payloadTopic}:{item}", f"{item}={value}"))

        if topic in {"BS", "IS", "CF"}:
            annual = self.finance.annual
            if annual is None:
                return None
            series, years = annual
            collect(series.get(topic), years, topic)
        elif topic == "CIS":
            annual = self._financeCisAnnual()
            if annual is None:
                return None
            series, years = annual
            collect(series.get("CIS"), years, "CIS")
        elif topic == "SCE":
            annual = self._sceSeriesAnnual()
            if annual is None:
                return None
            series, years = annual
            collect(series.get("SCE"), years, "SCE")
        else:
            return None

        if not rows:
            return None

        payloadRef, summary = rows[0]
        return {
            "topic": topic,
            "period": requestedPeriod,
            "primarySource": "finance",
            "fallbackSources": [],
            "selectedPayloadRef": payloadRef,
            "availableSources": [
                {
                    "source": "finance",
                    "rows": len(rows),
                    "payloadRef": payloadRef,
                    "summary": summary,
                    "priority": 300,
                }
            ],
            "whySelected": "finance authoritative priority",
        }

    def _showReportTopic(self, topic: str, *, period: str | None = None, raw: bool = False) -> pl.DataFrame | None:
        """report source topic의 실제 데이터 반환."""
        return self._applyPeriodFilter(self._reportFrame(topic, raw=raw), period)

    def _showSegmentsSub(self, sub: str) -> pl.DataFrame | None:
        """segments 하위 topic → DataFrame."""
        segResult = self._call_module("segments")
        if segResult is None:
            return None
        typeMap = {"region": "region", "product": "product", "composition": "segment"}
        tableType = typeMap.get(sub)
        if tableType is None:
            return None
        table = segResult.latestTable(tableType)
        if table is None:
            return None
        return table.toDataFrame()

    def _showDirectTopic(self, topic: str, *, period: str | None = None, raw: bool = False) -> pl.DataFrame | None:
        """sections 외 경로에서 직접 회수 가능한 topic fallback."""
        if self._hasReport:
            try:
                report_api_types = set(getattr(self.report, "apiTypes", []) or [])
            except (AttributeError, TypeError, ValueError):
                report_api_types = set()
            if topic in report_api_types:
                result = self._showReportTopic(topic, period=period, raw=raw)
                if isinstance(result, pl.DataFrame):
                    return result

        notes = self.notes
        if notes is not None and hasattr(notes, "keys"):
            try:
                note_keys = set(notes.keys())
            except (AttributeError, TypeError, ValueError):
                note_keys = set()
            if topic in note_keys:
                try:
                    result = getattr(notes, topic)
                except (AttributeError, KeyError, RuntimeError, TypeError, ValueError):
                    result = None
                if isinstance(result, pl.DataFrame):
                    return self._applyPeriodFilter(result, period)

        primary = self._safePrimary(topic)
        if isinstance(primary, pl.DataFrame):
            return self._applyPeriodFilter(primary, period)
        return None

    def _showSectionBlock(
        self,
        topicFrame: pl.DataFrame,
        *,
        block: int | None = None,
        period: str | None = None,
    ) -> pl.DataFrame | None:
        """sections topicFrame에서 blockOrder별 text/table 반환.

        block=None → topic 전체 (blockOrder 순서, text는 원문, table은 수평화)
        block=N → 해당 blockOrder의 블록만 반환
        """
        if "blockType" not in topicFrame.columns or "blockOrder" not in topicFrame.columns:
            return self._applyPeriodFilter(topicFrame, period)

        periodCols = [c for c in topicFrame.columns if _isPeriodColumn(c)]

        if block is not None:
            # 특정 blockOrder만
            boRows = topicFrame.filter(pl.col("blockOrder") == block)
            if boRows.is_empty():
                return None
            bt = boRows["blockType"][0]
            if bt == "text":
                keepCols = [c for c in periodCols if c in boRows.columns]
                nonNullCols = [c for c in keepCols if boRows[c].null_count() < boRows.height]
                if not nonNullCols:
                    return None
                return self._applyPeriodFilter(boRows.select(nonNullCols), period)
            elif bt == "table":
                result = self._horizontalizeTableBlock(topicFrame, block, periodCols, period)
                if result is not None:
                    return result
                # 수평화 실패(이력형/목록형 등) → 원본 텍스트 fallback
                keepCols = [c for c in periodCols if c in boRows.columns]
                nonNullCols = [c for c in keepCols if boRows[c].null_count() < boRows.height]
                if nonNullCols:
                    return self._applyPeriodFilter(boRows.select(nonNullCols), period)
            return None

        # block=None → 전체 topic (text 원문 + table 수평화, blockOrder 순서)
        return self._applyPeriodFilter(topicFrame, period)

    @staticmethod
    def _stripUnitHeader(sub: list[str]) -> list[str] | None:
        """단위행/기준일행이 헤더인 서브테이블 → 단위행 제거 + 나머지 반환."""
        from dartlab.providers.dart._table_horizontalizer import stripUnitHeader

        return stripUnitHeader(sub)

    def _horizontalizeTableBlock(
        self,
        topicFrame: pl.DataFrame,
        blockOrder: int,
        periodCols: list[str],
        period: str | None = None,
    ) -> pl.DataFrame | None:
        """table 블록을 기간 간 수평화 — 항목×기간 매트릭스."""
        from dartlab.providers.dart._table_horizontalizer import horizontalizeTableBlock

        df = horizontalizeTableBlock(topicFrame, blockOrder, periodCols, period)
        if df is None:
            return None
        return self._applyPeriodFilter(df, period)

    def _reportFrame(self, topic: str, *, raw: bool = False) -> pl.DataFrame | None:
        if self.report is None:
            return None
        apiType = _REPORT_TOPIC_TO_API_TYPE.get(topic, topic)
        try:
            if apiType not in self.report.apiTypes:
                return None
            return self._reportFrameInner(apiType, topic, raw=raw)
        except (
            pl.exceptions.ColumnNotFoundError,
            pl.exceptions.InvalidOperationError,
            pl.exceptions.SchemaError,
            RuntimeError,
        ):
            return None

    def _reportFrameInner(self, apiType: str, topic: str, *, raw: bool = False) -> pl.DataFrame | None:
        """report apiType의 정제된 DataFrame 반환."""
        from dartlab.providers.dart._report_accessor import reportFrameInner

        return reportFrameInner(self.stockCode, apiType, topic, raw=raw)

    def _applyPeriodFilter(self, payload: Any, period: str | None) -> Any:
        if period is None or not isinstance(payload, pl.DataFrame) or payload.is_empty():
            return payload
        from dartlab.providers.dart.docs.sections import rawPeriod

        requestedPeriod = str(period)
        normalizedPeriod = rawPeriod(period)

        # exact match first, then normalized (Q4 → annual alias), then Q4 expansion
        q4Fallback = f"{requestedPeriod}Q4" if "Q" not in requestedPeriod else None
        exactPeriod = (
            normalizedPeriod
            if normalizedPeriod in payload.columns
            else (
                requestedPeriod
                if requestedPeriod in payload.columns
                else (q4Fallback if q4Fallback and q4Fallback in payload.columns else None)
            )
        )
        if exactPeriod is not None:
            keepCols = [c for c in payload.columns if not _isPeriodColumn(c)]
            keepCols.append(exactPeriod)
            result = payload.select(keepCols)
            if exactPeriod != requestedPeriod:
                result = result.rename({exactPeriod: requestedPeriod})
            return result

        if "period" in payload.columns:
            return payload.filter(pl.col("period") == normalizedPeriod)
        if "year" in payload.columns:
            return payload.filter(pl.col("year").cast(pl.Utf8) == normalizedPeriod)
        return payload

    def show(
        self,
        topic: str,
        block: int | None = None,
        *,
        period: str | list[str] | None = None,
        raw: bool = False,
    ) -> pl.DataFrame | None:
        """topic의 데이터를 반환.

        Capabilities:
            - 120+ topic 접근 (재무제표, 사업내용, 지배구조, 임원현황 등)
            - 기간별 수평화 (topic × period 매트릭스)
            - 블록 단위 drill-down (목차 → 상세)
            - docs/finance/report 3개 소스 자동 통합
            - 세로 뷰 (period 리스트 전달 시)

        Args:
            topic: topic 이름 (BS, IS, CF, dividend, companyOverview 등). c.topics로 전체 목록.
            block: blockOrder 인덱스. None이면 블록 목차 (블록 1개면 바로 데이터).
            period: 특정 기간 필터 ("2023", "2024Q2"). 리스트면 세로 뷰 (기간 × 항목).
            raw: True면 원본 그대로 (정제 없이).

        Returns:
            pl.DataFrame | None — topic 데이터. 블록 목차 또는 실제 데이터.

        Requires:
            데이터: docs (자동 다운로드). finance topic은 finance 데이터도 필요.

        Example::

            c = dartlab.Company("005930")
            c.show("BS")                   # 재무상태표
            c.show("IS", period="2023")    # 2023년 손익계산서
            c.show("dividend")             # 배당
            c.show("IS", period=["2022", "2023"])  # 세로 비교

        AIContext:
            - 120+ topic에 대한 단일 접근점 — LLM이 데이터를 조회하는 핵심 도구
            - period 리스트로 기간 비교 뷰 생성 가능

        Guide:
            - "배당 정보 보여줘" → c.show("dividend")
            - "사업 개요 확인" → c.show("businessOverview")
            - "2023년 손익계산서" → c.show("IS", period="2023")
            - "연도별 비교" → c.show("IS", period=["2022", "2023"])

        SeeAlso:
            - select: show() 결과에서 특정 행/열 필터 + 차트
            - trace: 데이터 출처 추적
            - topics: 사용 가능한 topic 전체 목록
            - diff: 기간간 텍스트 변경 비교
        """
        # alias 해석 (board → boardOfDirectors 등)
        topic = _TOPIC_ALIASES.get(topic, topic)

        # period가 리스트면 세로 뷰: 먼저 전체 데이터 → transpose
        if isinstance(period, list):
            wide = self.show(topic, block, raw=raw)
            if wide is None or not isinstance(wide, pl.DataFrame):
                return None
            return self._transposeToVertical(wide, period)

        # segments 하위 topic (segments:region, segments:product, segments:composition)
        if topic.startswith("segments:"):
            return self._showSegmentsSub(topic.split(":", 1)[1])

        if topic in {"BS", "IS", "CF", "CIS", "SCE", "ratios"}:
            if block not in (None, 0):
                return None
            result = self._showFinanceTopic(topic, period=period)
            if topic in {"IS", "BS", "CIS", "CF", "SCE"} and isinstance(result, pl.DataFrame) and result.width > 0:
                result = self._cleanFinanceDataFrame(result, topic)
            return result if isinstance(result, pl.DataFrame) else None

        # 전체 sections 캐시가 있으면 재사용, 없으면 해당 topic만 부분 빌드
        if "_sections" in self._cache:
            sec = self._cache["_sections"]
        else:
            docsSections = self.docs.sections
            if docsSections is not None:
                partialDocs = docsSections.forTopics({topic})
                if partialDocs is not None and "source" not in partialDocs.columns:
                    partialDocs = partialDocs.with_columns(pl.lit("docs").alias("source"))
                sec = partialDocs
            else:
                sec = None
        if sec is None:
            return self._showDirectTopic(topic, period=period, raw=raw) if block in (None, 0) else None

        topicRows = sec.filter(pl.col("topic") == topic)
        if topicRows.is_empty():
            if block in (None, 0):
                direct = self._showDirectTopic(topic, period=period, raw=raw)
                if isinstance(direct, pl.DataFrame):
                    return direct
            import difflib

            all_topics = sec["topic"].unique().sort().to_list() if "topic" in sec.columns else []
            similar = difflib.get_close_matches(topic, all_topics, n=3, cutoff=0.4)
            if similar:
                import warnings

                warnings.warn(
                    f"'{topic}' topic을 찾을 수 없습니다. "
                    f"유사한 topic: {', '.join(similar)}. "
                    f"전체 목록은 c.topics로 확인하세요.",
                    stacklevel=2,
                )
            return None

        if block is None:
            # 블록 목차 반환
            blockIndex = self._buildBlockIndex(topicRows)
            if blockIndex.height == 1:
                # 블록이 1개면 바로 데이터 반환
                return self.show(topic, blockIndex["block"][0], period=period, raw=raw)
            return blockIndex

        # 특정 block의 실제 데이터
        boRows = topicRows.filter(pl.col("blockOrder") == block)
        if boRows.is_empty():
            return None

        source = boRows["source"][0] if "source" in boRows.columns else "docs"
        bt = boRows["blockType"][0]

        if source == "finance":
            result = self._showFinanceTopic(topic, period=period)
        elif source == "report":
            result = self._showReportTopic(topic, period=period, raw=raw)
        else:
            # docs — text 또는 table 수평화
            result = self._showSectionBlock(
                sec.filter(pl.col("topic") == topic),
                block=block,
                period=period,
            )

        if (
            topic in {"IS", "BS", "CIS", "CF", "SCE"}
            and isinstance(result, pl.DataFrame)
            and "계정명" in result.columns
        ):
            result = self._cleanFinanceDataFrame(result, topic)

        return result if isinstance(result, pl.DataFrame) else None

    @staticmethod
    def _transposeToVertical(wide: pl.DataFrame, periods: list[str]) -> pl.DataFrame | None:
        from dartlab.core.show import transposeToVertical

        return transposeToVertical(wide, periods)

    @staticmethod
    def _cleanFinanceDataFrame(df: pl.DataFrame, sjDiv: str) -> pl.DataFrame:
        """재무제표 DataFrame 후처리: all-null 행 제거, CF 고유 정리."""
        periodCols = [c for c in df.columns if _isPeriodColumn(c)]
        if not periodCols:
            return df
        # CF 고유: 당기순이익 제거 (standalone 차분 오류), 영문 계정명 제거
        if sjDiv == "CF":
            df = df.filter(~pl.col("계정명").is_in(["당기순이익", "법인세비용차감전순이익"]))
            df = df.filter(~pl.col("계정명").str.contains(r"^[a-z_]+$"))
        # 공통: all-null 행 제거 (모든 기간이 null인 행)
        notAllNull = pl.any_horizontal([pl.col(c).is_not_null() for c in periodCols])
        df = df.filter(notAllNull)
        # 공통: 같은 계정명 중복행 병합 (coalesce — 먼저 나온 행 우선)
        if df["계정명"].n_unique() < df.height:
            import logging

            dupes = df.group_by("계정명").len().filter(pl.col("len") > 1)
            logging.getLogger(__name__).debug(
                "%s: 동의어 계정 %d건 병합 (먼저 나온 값 우선): %s",
                sjDiv,
                dupes.height,
                dupes["계정명"].to_list()[:5],
            )
            # 계정명 기준으로 병합 — snakeId가 다른 동의어 계정도 합침
            hasSnakeId = "snakeId" in df.columns
            aggCols = [c for c in periodCols]
            extraAgg = []
            if hasSnakeId:
                extraAgg = [pl.col("snakeId").first().alias("snakeId")]
            merged = df.group_by("계정명", maintain_order=True).agg(
                extraAgg + [pl.col(c).drop_nulls().first().alias(c) for c in aggCols]
            )
            # 컬럼 순서 복원
            df = merged.select([c for c in df.columns if c in merged.columns])
        return df

    _FINANCE_TOPICS = frozenset({"BS", "IS", "CF", "CIS", "SCE"})

    # ── docs multi-block select 지원 ──────────────────────────

    def _buildDocsItemIndex(
        self, topic: str
    ) -> dict[str, list[tuple[int, pl.DataFrame]]]:
        """topic의 모든 테이블 블록을 수평화하고 항목명 역인덱스를 빌드."""
        from dartlab.core.show import normalizeItemKey

        cacheKey = f"_docsItemIdx_{topic}"
        cached = self._cache.get(cacheKey)
        if cached is not None:
            return cached

        # 전체 sections 캐시가 있으면 재사용, 없으면 해당 topic만 부분 빌드
        if "_sections" in self._cache:
            sec = self._cache["_sections"]
        else:
            docsSections = self.docs.sections
            sec = docsSections.forTopics({topic}) if docsSections is not None else None
        if sec is None:
            self._cache[cacheKey] = {}
            return {}

        topicRows = sec.filter(pl.col("topic") == topic)
        if topicRows.is_empty():
            self._cache[cacheKey] = {}
            return {}

        blockIndex = self._buildBlockIndex(topicRows)
        periodCols = [c for c in topicRows.columns if _isPeriodColumn(c)]

        idx: dict[str, list[tuple[int, pl.DataFrame]]] = {}

        for row in blockIndex.iter_rows(named=True):
            bo = row["block"]
            bt = row.get("type", "text")
            src = row.get("source", "docs")
            if bt != "table" or src != "docs":
                continue

            from dartlab.providers.dart._table_horizontalizer import (
                horizontalizeTableBlock,
            )

            hDf = horizontalizeTableBlock(topicRows, bo, periodCols)
            if hDf is None or hDf.is_empty():
                continue

            itemCol = "항목" if "항목" in hDf.columns else None
            if itemCol is None:
                for c in hDf.columns:
                    if not _isPeriodColumn(c):
                        itemCol = c
                        break
            if itemCol is None:
                continue

            for val in hDf[itemCol].to_list():
                if val is None:
                    continue
                nk = normalizeItemKey(str(val))
                idx.setdefault(nk, []).append((bo, hDf))

        self._cache[cacheKey] = idx
        return idx

    def _selectFromDocsTopic(
        self,
        topic: str,
        indList: list[str],
        colList: list[str] | None,
    ) -> pl.DataFrame | None:
        """역인덱스에서 indList 항목을 cascade 매칭으로 찾아 추출."""
        from dartlab.core.show import normalizeItemKey, selectFromShow

        idx = self._buildDocsItemIndex(topic)
        if not idx:
            return None

        normQueries = [normalizeItemKey(q) for q in indList]
        allNormKeys = list(idx.keys())

        # cascade: exact → contains → fuzzy
        matched: list[tuple[int, pl.DataFrame]] = []
        matchedKeys: set[str] = set()

        # 1) exact
        for nq in normQueries:
            if nq in idx and nq not in matchedKeys:
                matched.extend(idx[nq])
                matchedKeys.add(nq)

        # 2) contains
        if not matched:
            for nq in normQueries:
                for nk in allNormKeys:
                    if (nq in nk or nk in nq) and nk not in matchedKeys:
                        matched.extend(idx[nk])
                        matchedKeys.add(nk)

        # 3) fuzzy
        if not matched:
            import difflib

            for nq in normQueries:
                close = difflib.get_close_matches(nq, allNormKeys, n=3, cutoff=0.7)
                for ck in close:
                    if ck not in matchedKeys:
                        matched.extend(idx[ck])
                        matchedKeys.add(ck)

        if not matched:
            return None

        # 블록별 DataFrame에서 selectFromShow로 행/열 필터
        parts: list[pl.DataFrame] = []
        seenBo: set[int] = set()
        for bo, hDf in matched:
            if bo in seenBo:
                continue
            seenBo.add(bo)
            filtered = selectFromShow(hDf, indList, colList)
            if filtered is not None:
                parts.append(filtered)

        if not parts:
            return None
        if len(parts) == 1:
            return parts[0]
        return pl.concat(parts, how="diagonal_relaxed")

    def _selectFromDocsTopicAll(
        self,
        topic: str,
        indList: list[str] | None,
        colList: list[str] | None,
    ) -> pl.DataFrame | None:
        """multi-block docs topic: indList/colList 조합 처리.

        indList가 있으면 cascade 매칭, None이면 전체 항목.
        colList는 기간 필터.
        """
        from dartlab.core.show import selectFromShow

        if indList is not None:
            return self._selectFromDocsTopic(topic, indList, colList)

        # indList=None → 전체 테이블 블록 수평화 결과 concat + colList 필터
        idx = self._buildDocsItemIndex(topic)
        if not idx:
            return None

        seenBo: set[int] = set()
        parts: list[pl.DataFrame] = []
        for entries in idx.values():
            for bo, hDf in entries:
                if bo in seenBo:
                    continue
                seenBo.add(bo)
                filtered = selectFromShow(hDf, None, colList)
                if filtered is not None:
                    parts.append(filtered)

        if not parts:
            return None
        if len(parts) == 1:
            return parts[0]
        return pl.concat(parts, how="diagonal_relaxed")

    def select(
        self,
        topic: str,
        indList: str | list[str] | None = None,
        colList: str | list[str] | None = None,
    ):
        """show() 결과에서 행(indList) + 열(colList) 필터.

        Capabilities:
            - show() 결과에서 특정 계정/항목만 추출
            - 기간 필터링 (특정 연도만)
            - .chart() 체이닝으로 바로 시각화
            - 한글/영문 계정명 모두 지원

        Args:
            topic: IS, BS, CF, CIS, SCE 또는 docs topic.
            indList: 행 필터. 한글 계정명/snakeId/항목명. 단일 str도 가능.
            colList: 열(기간) 필터. 단일 str도 가능.

        Returns:
            SelectResult — DataFrame 위임 + .chart() 체이닝. 없으면 None.

        Requires:
            데이터: docs (자동 다운로드)

        Example::

            c.select("IS", ["매출액", "영업이익"])
            c.select("IS", ["매출액"]).chart()
            c.select("BS", ["자본총계"], ["2024", "2023"])

        AIContext:
            - 특정 계정의 시계열 추출 — 추세 분석 및 차트 생성의 기본 도구
            - .chart() 체이닝으로 시각화까지 한 번에

        Guide:
            - "매출액 추이 그래프" → c.select("IS", ["매출액"]).chart()
            - "영업이익만 뽑아줘" → c.select("IS", ["영업이익"])
            - "2023-2024 자본 비교" → c.select("BS", ["자본총계"], ["2024", "2023"])

        SeeAlso:
            - show: 전체 topic ��이터 조회 (select의 원본)
            - table: docs 마크다운 테이블 구조화 파싱
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

        # multi-block docs topic 감지 → 역인덱스 경로
        isBlockIndex = (
            isinstance(df, pl.DataFrame)
            and "block" in df.columns
            and "type" in df.columns
            and "preview" in df.columns
            and topic not in self._FINANCE_TOPICS
        )
        if isBlockIndex and (indList is not None or colList is not None):
            filtered = self._selectFromDocsTopicAll(topic, indList, colList)
        else:
            filtered = selectFromShow(df, indList, colList)
        if filtered is None:
            return None
        return SelectResult(
            filtered,
            topic,
            {
                "stockCode": self.stockCode,
                "corpName": self.corpName,
                "currency": self.currency,
            },
        )

    def trace(self, topic: str, period: str | None = None) -> dict[str, Any] | None:
        """topic 데이터의 출처(docs/finance/report)와 선택 근거 추적.

        Capabilities:
            - topic별 데이터 출처 확인 (docs, finance, report)
            - 출처 선택 이유 (우선순위, fallback 경로)
            - 각 출처별 데이터 행 수, 기간 수, 커버리지

        Args:
            topic: topic 이름.
            period: 특정 기간. None이면 전체.

        Returns:
            dict — primarySource, fallbackSources, whySelected, availableSources 등.

        Requires:
            데이터: docs + finance + report (보유한 것만 추적)

        Example::

            c.trace("BS")           # 재무상태표 출처
            c.trace("dividend")     # 배당 데이터 출처

        AIContext:
            - 데이터 출처 신뢰도 판단 — finance > report > docs 우선순위 확인
            - 분석 결과의 근거 투명성 확보

        Guide:
            - "이 데이터 어디서 온 거야?" → c.trace("BS")
            - "데이터 출처 확인" → c.trace(topic)

        SeeAlso:
            - show: topic 데이터 조회 (trace로 출처 확인 후 열람)
            - sources: 3개 source 전체 가용 현황
        """
        topic = _TOPIC_ALIASES.get(topic, topic)
        if topic == "docsStatus" and not self._hasDocs:
            return {
                "topic": topic,
                "period": period,
                "primarySource": "docs",
                "fallbackSources": [],
                "selectedPayloadRef": None,
                "availableSources": [],
                "whySelected": "docs unavailable",
            }
        if topic == "ratios":
            ratioSeries = self._ratioSeries()
            templateKey = _ratioTemplateKeyForIndustryGroup(getattr(self.sector, "industryGroup", None))
            rowCount = None
            yearCount = None
            coverage = "missing"
            if ratioSeries is not None:
                series, years = ratioSeries
                fieldNames = _RATIO_TEMPLATE_FIELDS.get(templateKey)
                ratioFrame = _ratioSeriesToDataFrame(series, years, fieldNames=fieldNames)
                rowCount = None if ratioFrame is None else ratioFrame.height
                yearCount = len(years)
                if ratioFrame is not None and rowCount >= 30 and yearCount >= 5:
                    coverage = "full"
                elif ratioFrame is not None and rowCount > 0:
                    coverage = "partial"
            return {
                "topic": topic,
                "period": period,
                "primarySource": "finance",
                "fallbackSources": [],
                "selectedPayloadRef": "finance:RATIO",
                "availableSources": []
                if ratioSeries is None
                else [
                    {
                        "source": "finance",
                        "rows": 1,
                        "payloadRef": "finance:RATIO",
                        "summary": "annual ratio series"
                        if templateKey is None
                        else f"annual ratio series ({templateKey} template)",
                        "priority": 300,
                    }
                ],
                "whySelected": "finance authoritative priority"
                if templateKey is None
                else f"finance authoritative priority with {templateKey} industry template",
                "template": templateKey or "general",
                "rowCount": rowCount,
                "yearCount": yearCount,
                "coverage": coverage,
            }
        if topic in {"BS", "IS", "CF", "CIS", "SCE"}:
            result = self._traceFinanceTopic(topic, period=period)
            if result is not None:
                return result
        return self._profileAccessor.trace(topic, period=period)

    def diff(
        self,
        topic: str | None = None,
        fromPeriod: str | None = None,
        toPeriod: str | None = None,
    ) -> pl.DataFrame | None:
        """기간간 텍스트 변경 비교.

        Capabilities:
            - 전체 topic 변경 요약 (변경량 스코어링)
            - 특정 topic 기간별 변경 이력
            - 두 기간 줄 단위 diff (추가/삭제/변경)

        Args:
            topic: topic 이름. None이면 전체 변경 요약.
            fromPeriod: 비교 시작 기간 ("2023").
            toPeriod: 비교 끝 기간 ("2024").

        Returns:
            pl.DataFrame | None — 변경 요약, 히스토리, 또는 줄 단위 diff.

        Requires:
            데이터: docs (2개 이상 기간 필요)

        Example::

            c.diff()                                    # 전체 변경 요약
            c.diff("businessOverview")                  # 사업개요 변경 이력
            c.diff("businessOverview", "2023", "2024")  # 줄 단위 diff

        AIContext:
            - 기간간 공시 변경 감지 — 사업 방향 전환, 리스크 요인 변화 탐지
            - watch()보다 세밀한 줄 단위 변경 추적

        Guide:
            - "공시에서 뭐가 바뀌었어?" → c.diff()
            - "사업개요 변경 이력" → c.diff("businessOverview")
            - "2023 vs 2024 차이" → c.diff("businessOverview", "2023", "2024")

        SeeAlso:
            - watch: 변화 중요도 스코어링 (diff보다 요약적)
            - keywordTrend: 키워드 ��도 추이 (텍스트 변화의 다른 관점)
            - show: 특정 기간 원문 조회
        """
        if topic is not None:
            topic = _TOPIC_ALIASES.get(topic, topic)
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
        """공시 텍스트 키워드 빈도 추이 (topic x period x keyword).

        Capabilities:
            - 공시 텍스트에서 키워드 빈도 추이 분석
            - 54개 내장 키워드 세트 (AI, ESG, 탄소중립 등)
            - topic별 x 기간별 빈도 매트릭스
            - 복수 키워드 동시 검색

        Args:
            keyword: 단일 키워드. None이면 내장 키워드 전체.
            keywords: 복수 키워드 리스트.

        Returns:
            pl.DataFrame | None — topic x period x keyword 빈도.

        Requires:
            데이터: docs (자동 다운로드)

        Example::

            c.keywordTrend("AI")
            c.keywordTrend(keywords=["AI", "ESG"])
            c.keywordTrend()                  # 54개 내장 키워드 전체

        AIContext:
            - 공시 텍스트의 키워드 빈도 변화로 전략 방향 전환 감지
            - AI, ESG, 탄소중립 등 트렌드 키워드 모니터링

        Guide:
            - "AI 언급 추이" → c.keywordTrend("AI")
            - "ESG 관련 변화" → c.keywordTrend("ESG")
            - "전체 키워드 트렌드" → c.keywordTrend()

        SeeAlso:
            - diff: 텍스트 줄 단위 변경 비교 (키워드가 아닌 전체 변경)
            - watch: 변화 중요도 스코어링
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
        """최근 뉴스 수집.

        Capabilities:
            - Google News RSS 기반 뉴스 수집
            - 제목, 날짜, 소스, 링크
            - 기간 조절 가능

        Args:
            days: 최근 N일. 기본 30.

        Returns:
            pl.DataFrame — title, date, source, link.

        Requires:
            없음 (공개 RSS)

        Example::

            c.news()           # 최근 30일
            c.news(days=7)     # 최근 7일

        AIContext:
            - 최근 뉴스로 시장 반응, 이슈, 이벤트 파악
            - ask()/chat()에서 정성적 시장 맥락 보충

        Guide:
            - "최근 뉴스 보여줘" → c.news()
            - "이번 주 뉴스" → c.news(days=7)

        SeeAlso:
            - liveFilings: 최신 공시 (뉴스가 아닌 공식 공시)
            - gather: 뉴스 포함 4축 외부 데이터 수집
        """
        from dartlab.gather import getDefaultGather

        return getDefaultGather().news(self.corpName, market="KR", days=days)

    def watch(
        self,
        topic: str | None = None,
    ) -> pl.DataFrame | None:
        """공시 변화 감지 — 중요도 스코어링 기반 변화 요약.

        Capabilities:
            - 전체 topic 변화 중요도 스코어링
            - 텍스트 변화량 + 재무 영향 통합 평가
            - 특정 topic 상세 변화 내역

        Args:
            topic: topic 이름. None이면 전체 중요도 순 요약.

        Returns:
            pl.DataFrame | None — topic, score, changeType, details 등.

        Requires:
            데이터: docs (자동 다운로드)

        Example::

            c.watch()                    # 전체 중요도 순
            c.watch("riskManagement")    # 특정 topic

        AIContext:
            - 공시 변화 중요도 자동 평가 — 분석 우선순위 결정에 활용
            - 텍스트 변화량 + 재무 영향 통합 스코어

        Guide:
            - "뭐가 크게 바뀌었어?" → c.watch()
            - "리스크 관련 변화" → c.watch("riskManagement")

        SeeAlso:
            - diff: 줄 단위 상세 변경 비교 (watch보다 세밀)
            - keywordTrend: 키워드 빈도 추이
        """
        from dartlab.scan.watch.scanner import scan_company

        result = scan_company(self, topic=topic)
        if result is None:
            return None
        return result.to_dataframe()

    def review(self, section: str | None = None, layout=None, helper: bool | None = None, *, preset: str | None = None, detail: bool | None = None, basePeriod: str | None = None):
        """재무제표 구조화 보고서 — 14개 섹션 데이터 검토서.

        Capabilities:
            - 14개 섹션 전체 보고서 (수익구조~재무정합성)
            - 단일 섹션 지정 가능
            - 4개 출력 형식 (rich, html, markdown, json)
            - 섹션간 순환 서사 자동 감지
            - 프리셋 지원 (executive/audit/credit/growth/valuation)
            - detail=False로 요약만 표시
            - 레이아웃 커스텀

        AIContext:
            - reviewer()가 이 결과를 소비하여 AI 해석 생성
            - ask()에서 재무분석 컨텍스트로 활용

        Args:
            section: 섹션명 ("수익구조" 등). None이면 전체.
            layout: ReviewLayout 커스텀. None이면 기본.
            helper: True면 해석 힌트 텍스트 포함. None이면 자동.
            preset: 프리셋명 ("executive"/"audit"/"credit"/"growth"/"valuation"). None이면 전체.
            detail: True면 전체 블록, False면 섹션 요약만. None이면 preset 기본값 또는 True.

        Returns:
            Review — 구조화 보고서.

        Requires:
            데이터: finance + report (자동 다운로드)

        Example::

            c.review()                        # 전체 검토서
            c.review("수익구조")                # 특정 섹션
            c.review(preset="audit")          # 감사/회계 검토용
            c.review(preset="executive")      # 경영진 요약
            c.review(detail=False)            # 전 섹션 요약만

        Guide:
            - "재무 검토서 만들어줘" -> c.review()
            - "수익구조 분석" -> c.review("수익구조")
            - "감사용 리뷰" -> c.review(preset="audit")
            - "요약만 보여줘" -> c.review(detail=False)
            - "AI 의견 포함 보고서" -> c.reviewer() (review + AI 해석)

        SeeAlso:
            - reviewer: review() + AI 섹션별 종합의견 (AI 해석 포함)
            - analysis: 14축 개별 분석 (review가 내부적으로 소비)
            - insights: 7영역 등급 + 이상치 요약
        """
        from dartlab.review.registry import buildReview

        return buildReview(self, section=section, layout=layout, helper=helper, preset=preset, detail=detail, basePeriod=basePeriod)

    def reviewer(self, section: str | None = None, layout=None, helper: bool | None = None, guide: str | None = None, *, preset: str | None = None, detail: bool | None = None, basePeriod: str | None = None):
        """AI 분석 보고서 — review() + 섹션별 AI 종합의견.

        Capabilities:
            - review() 데이터 위에 AI 섹션별 종합의견 추가
            - 도메인 특화 가이드로 분석 관점 지정 가능
            - 각 섹션 시작에 AI 해석 삽입

        AIContext:
            - review() 결과(재무비율, 추세, 동종업계 비교)를 LLM에 제공
            - LLM이 각 섹션을 해석하여 종합의견 생성
            - guide 파라미터로 분석 관점 커스텀

        Args:
            section: 섹션명. None이면 전체.
            layout: ReviewLayout 커스텀.
            helper: True면 해석 힌트 포함.
            guide: AI에게 전달할 분석 관점 ("반도체 사이클 관점에서 평가해줘").

        Returns:
            Review — AI 의견이 포함된 보고서.

        Requires:
            AI: provider 설정 (dartlab.setup() 참조)
            데이터: finance + report (자동 다운로드)

        Example::

            c.reviewer()
            c.reviewer("수익구조")
            c.reviewer(guide="반도체 사이클 관점에서 평가해줘")

        Guide:
            - "AI가 분석한 보고서" → c.reviewer()
            - "반도체 관점에서 분석" → c.reviewer(guide="반도체 사이클 관점에서 평가해줘")
            - "특정 섹션만 AI 분석" → c.reviewer("수익구조")

        SeeAlso:
            - review: AI 없는 순수 데이터 검토서 (reviewer의 기반)
            - ask: 자유 질문 기반 AI 분석
            - chat: 에이전트 모드 심화 분석
        """
        from dartlab.review.registry import buildReview

        return buildReview(self, section=section, layout=layout, basePeriod=basePeriod)

    def analysis(self, axis: str | None = None, **kwargs):
        """재무제표 완전 분석 — 14축, 단일 종목 심층.

        Capabilities:
            - 14축 분석: 수익구조, 자금조달, 자산구조, 현금흐름, 수익성, 성장성, 안정성, 효율성, 종합평가, 이익품질, 비용구조, 자본배분, 투자효율, 재무정합성
            - 축 없이 호출 시 14축 가이드 반환
            - 개별 축 분석 시 Company 바인딩 (self 자동 전달)

        AIContext:
            - ask()/chat()에서 분석 결과를 컨텍스트로 주입
            - review/reviewer가 내부적으로 analysis 결과를 소비

        Args:
            axis: 분석 축 이름. None이면 14축 가이드 반환.
            **kwargs: 축별 추가 옵션.

        Returns:
            pl.DataFrame — 축별 분석 결과. axis=None이면 14축 가이드 DataFrame.

        Requires:
            데이터: finance (자동 다운로드)

        Example::

            c = Company("005930")
            c.analysis()              # 14축 가이드
            c.analysis("수익구조")     # 수익구조 분석

        Guide:
            - "14축 분석 뭐가 있어?" → c.analysis() (가이드 반환)
            - "수익구조 분석해줘" → c.analysis("수익구조")
            - "안정성 분석" → c.analysis("안정성")

        SeeAlso:
            - review: 14축 분석을 14개 섹션 보고서로 조합
            - insights: 7영역 등급 요약 (analysis보다 요약적)
            - ratios: 재무비율 시계열 (analysis의 입력 데이터)
        """
        from dartlab.analysis.financial import Analysis

        _analysis = Analysis()
        if axis is None:
            return _analysis()
        return _analysis(axis, self, **kwargs)

    def gather(self, axis: str | None = None, **kwargs):
        """외부 시장 데이터 수집 — 4축 (price/flow/macro/news).

        Capabilities:
            - price: OHLCV 주가 시계열 (KR Naver / US Yahoo)
            - flow: 외국인/기관 수급 동향 (KR 전용)
            - macro: ECOS(KR) / FRED(US) 거시지표 시계열
            - news: Google News RSS 뉴스 수집
            - 자동 fallback 체인, circuit breaker, TTL 캐시

        AIContext:
            - ask()/chat()에서 주가/수급/거시 데이터를 컨텍스트로 주입
            - 기업 분석 시 시장 데이터 보충 자료로 활용

        Args:
            axis: 축 이름 ("price", "flow", "macro", "news"). None이면 가이드 반환.
            **kwargs: market, start, end, days 등 축별 옵션.

        Returns:
            pl.DataFrame — 축별 시계열 데이터. axis=None이면 4축 가이드 DataFrame.

        Requires:
            price/flow/news: 없음 (공개 API)
            macro: API 키 -- ECOS_API_KEY (KR) 또는 FRED_API_KEY (US)

        Example::

            c = Company("005930")
            c.gather()                 # 4축 가이드
            c.gather("price")          # 주가 시계열
            c.gather("news")           # 뉴스

        Guide:
            - "주가 데이터" → c.gather("price")
            - "외국인/기관 수급" → c.gather("flow")
            - "거시경제 지표" → c.gather("macro")
            - "뉴스 수집" → c.gather("news") 또는 c.news()

        SeeAlso:
            - news: 뉴스 전용 단축 메서드
            - ask: gather 데이터를 컨텍스트로 활용한 AI 분석
        """
        from dartlab.gather.entry import GatherEntry

        _gather = GatherEntry()
        if axis is None:
            return _gather()
        return _gather(axis, self.stockCode, **kwargs)

    def table(
        self,
        topic: str,
        subtopic: str | None = None,
        *,
        numeric: bool = False,
        period: str | None = None,
    ) -> Any:
        """subtopic wide 셀의 markdown table을 구조화 DataFrame으로 파싱.

        Capabilities:
            - docs 원문의 markdown table을 Polars DataFrame으로 변환
            - subtopic 지정으로 특정 표만 추출
            - numeric 모드로 금액 문자열을 float 변환
            - period 필터로 특정 기간 컬럼만 선택

        Args:
            topic: docs topic 이름
            subtopic: 파싱할 subtopic 이름 (None이면 첫 번째 subtopic)
            numeric: True이면 금액 문자열을 float로 변환
            period: 기간 필터 (예: "2024")

        Returns:
            ParsedSubtopicTable (df, subtopic, columns) 또는 파싱 불가 시 None

        Requires:
            데이터: docs (자동 다운로드)

        Example::

            c.table("employee")                    # 첫 번째 subtopic
            c.table("employee", "직원현황")         # 특정 subtopic
            c.table("employee", numeric=True)       # 숫자 변환

        AIContext:
            - docs 원문 테이블을 구조화하여 정량 분석에 활용
            - numeric=True로 금액 문자열을 수치화하면 계산 가능

        Guide:
            - "직원 현황 테이블" → c.table("employee")
            - "표 데이터를 숫자로" → c.table(topic, numeric=True)

        SeeAlso:
            - show: topic 전체 데이터 (table은 subtopic 단위 파싱)
            - select: show() 결과에서 행/열 필터
        """
        result = self._topicSubtables(topic)
        if result is None:
            return None
        from dartlab.providers.dart.docs.sections import parseSubtopicTable

        parsed = parseSubtopicTable(result, subtopic, numeric=numeric)
        if parsed is None:
            return None
        if period is not None and parsed.df is not None:
            periodCols = [c for c in parsed.df.columns if c != "항목"]
            matchedCols = [c for c in periodCols if period in c]
            if matchedCols:
                from dataclasses import replace

                filteredDf = parsed.df.select(["항목", *matchedCols])
                return replace(parsed, df=filteredDf)
        return parsed

    @property
    def topics(self) -> pl.DataFrame:
        """topic별 요약 DataFrame -- 전체 데이터 지도.

        Capabilities:
            - docs/finance/report 모든 source의 topic을 하나의 DataFrame으로 통합
            - chapter 순서대로 정렬, 각 topic의 블록 수/기간 수/최신 기간 표시
            - 어떤 데이터가 있는지 한눈에 파악

        AIContext:
            - LLM이 가용 topic 목록을 파악하는 데 사용
            - 분석 범위 결정 시 참조

        Guide:
            - "어떤 데이터가 있어?" → c.topics
            - "topic 목록" → c.topics

        SeeAlso:
            - show: 특정 topic 데이터 조회
            - sections: topic x period 전체 지도 (topics보다 상세)
            - index: 전체 구조 메타데이터 목차

        Returns:
            pl.DataFrame -- 컬럼: order, chapter, topic, source, blocks, periods, latestPeriod

        Requires:
            데이터: docs/finance/report 중 하나 이상 (자동 다운로드)

        Example::

            c = Company("005930")
            c.topics                   # 전체 topic 요약
            c.topics.filter(pl.col("source") == "finance")  # finance만
        """
        cacheKey = "_topicsDataFrame"
        if cacheKey in self._cache:
            return self._cache[cacheKey]

        docsManifest = self._docsTopicManifest()
        rows = docsManifest.to_dicts() if not docsManifest.is_empty() else []
        seen = {str(row["topic"]) for row in rows if isinstance(row.get("topic"), str)}

        financeRows: list[dict[str, Any]] = []
        if self._hasFinanceParquet:
            raw = loadData(self.stockCode, category="finance", columns=["bsns_year"])
            years = (
                sorted({str(year) for year in raw["bsns_year"].drop_nulls().to_list() if str(year) != "2015"})
                if raw is not None and not raw.is_empty() and "bsns_year" in raw.columns
                else []
            )
            latestPeriod = years[-1] if years else None
            for idx, topic in enumerate(("BS", "IS", "CIS", "CF", "SCE", "ratios")):
                if topic in seen:
                    continue
                financeRows.append(
                    {
                        "order": 3000 + idx,
                        "chapter": "III",
                        "topic": topic,
                        "source": "finance",
                        "blocks": 1,
                        "periods": len(years),
                        "latestPeriod": latestPeriod,
                    }
                )

        combined = rows + financeRows
        if not combined:
            result = self._emptyTopicManifest()
        else:
            result = (
                pl.DataFrame(combined, strict=False)
                .with_columns(pl.col("chapter").replace(_CHAPTER_ORDER).cast(pl.Int64).alias("_chapterOrder"))
                .sort(["_chapterOrder", "order", "topic"])
                .drop("_chapterOrder")
            )
        self._cache[cacheKey] = result
        return result

    @property
    def sources(self) -> pl.DataFrame:
        """docs/finance/report 3개 source의 가용 현황 요약.

        Capabilities:
            - 3개 데이터 source(docs, finance, report) 존재 여부/규모 한눈에 확인
            - 각 source의 row/col 수와 shape 문자열 제공
            - 데이터 로드 전 가용성 사전 점검

        Returns:
            pl.DataFrame -- 컬럼: source, available, rows, cols, shape

        Requires:
            없음 (메타데이터만 조회, 데이터 파싱 불필요)

        Example::

            c = Company("005930")
            c.sources                  # 3행 DataFrame

        AIContext:
            - 데이터 가용성 사전 점검 — 분석 가능 범위 판단의 기초

        Guide:
            - "데이터 뭐가 있어?" → c.sources
            - "docs/finance/report 상태" → c.sources

        SeeAlso:
            - topics: topic 단위 상세 데이터 지도
            - trace: 특정 topic의 출처 추적
        """
        rows = []
        for source, raw in (
            ("docs", self.rawDocs),
            ("finance", self.rawFinance),
            ("report", self.rawReport),
        ):
            rows.append(
                {
                    "source": source,
                    "available": raw is not None,
                    "rows": raw.height if raw is not None else None,
                    "cols": raw.width if raw is not None else None,
                    "shape": _shapeString(raw),
                }
            )
        return pl.DataFrame(rows)

    @property
    def index(self) -> pl.DataFrame:
        """현재 공개 Company 구조 인덱스 DataFrame -- 전체 데이터 목차.

        Capabilities:
            - docs sections + finance + report 전체를 하나의 목차로 통합
            - 각 항목의 chapter, topic, label, kind, source, periods, shape, preview 제공
            - sections 메타데이터 + 존재 확인만으로 구성 (파서 미호출, lazy)
            - viewer/렌더러가 소비하는 메타데이터 원천

        AIContext:
            - LLM이 Company 전체 구조를 파악하는 핵심 진입점
            - ask()에서 어떤 데이터를 참조할지 결정하는 기초 정보

        Guide:
            - "전체 목차 보여줘" → c.index
            - "어떤 데이터가 있는지 구조적으로" → c.index

        SeeAlso:
            - topics: topic 단위 요약 (index보다 간결)
            - sections: 전체 sections 지도 (index의 원본)
            - profile: 통합 프로필 접근자

        Returns:
            pl.DataFrame -- 컬럼: chapter, topic, label, kind, source, periods, shape, preview

        Requires:
            데이터: docs/finance/report 중 하나 이상 (자동 다운로드)

        Example::

            c = Company("005930")
            c.index                    # 전체 구조 목차
            c.index.filter(pl.col("source") == "docs")  # docs 항목만
        """
        cacheKey = "_lazyIndex"
        if cacheKey in self._cache:
            return self._cache[cacheKey]

        rows: list[dict[str, Any]] = []

        if not self._hasDocs:
            rows.append(
                {
                    "chapter": "안내",
                    "topic": "docsStatus",
                    "label": "사업보고서",
                    "kind": "notice",
                    "source": "docs",
                    "periods": "-",
                    "shape": "missing",
                    "preview": "현재 사업보고서 부재",
                    "_sortKey": (0, 0),
                }
            )

        rows.extend(self._indexFinanceRows())
        rows.extend(self._indexDocsRows())
        rows.extend(self._indexReportRows(existingTopics={r["topic"] for r in rows}))

        rows.sort(key=lambda r: r.get("_sortKey", (99, 999)))
        for r in rows:
            r.pop("_sortKey", None)

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

    def _indexFinanceRows(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        _STMT_ORDER = {"BS": 0, "IS": 1, "CIS": 2, "CF": 3, "SCE": 4}
        for stmt in ("BS", "IS", "CIS", "CF", "SCE"):
            df = getattr(self, stmt, None)
            if df is None:
                continue
            periodCols = [c for c in df.columns if _isPeriodColumn(c)]
            periods = (
                f"{periodCols[0]}..{periodCols[-1]}" if len(periodCols) > 1 else (periodCols[0] if periodCols else "-")
            )
            rows.append(
                {
                    "chapter": _CHAPTER_TITLES.get("III", "III"),
                    "topic": stmt,
                    "label": self._topicLabel(stmt),
                    "kind": "finance",
                    "source": "finance",
                    "periods": periods,
                    "shape": _shapeString(df),
                    "preview": f"{df.height} accounts",
                    "_sortKey": (3, _STMT_ORDER[stmt]),
                }
            )

        rsPair = self._ratioSeries() if self._hasFinance else None
        if rsPair is not None:
            series, years = rsPair
            ratioData = series.get("RATIO", {})
            from dartlab.core.finance.ratios import RATIO_CATEGORIES

            metricCount = sum(
                1
                for _, fields in RATIO_CATEGORIES
                for f in fields
                if ratioData.get(f) and any(v is not None for v in ratioData[f])
            )
            periods = f"{years[0]}..{years[-1]}" if len(years) > 1 else (years[0] if years else "-")
            rows.append(
                {
                    "chapter": _CHAPTER_TITLES.get("III", "III"),
                    "topic": "ratios",
                    "label": "재무비율",
                    "kind": "finance",
                    "source": "finance",
                    "periods": periods,
                    "shape": f"{metricCount}x{len(years) + 2}",
                    "preview": f"{metricCount} metrics",
                    "_sortKey": (3, 5),
                }
            )
        return rows

    def _indexDocsRows(self) -> list[dict[str, Any]]:
        if not self._hasDocs:
            return []

        from dartlab.providers.dart.docs.sections import displayPeriod, formatPeriodRange, sortPeriods
        from dartlab.providers.dart.docs.sections.pipeline import (
            _expandStructuredRows,
            _reportRowsToTopicRows,
            _rowFreqMeta,
            applyProjections,
            chapterTeacherTopics,
            detailTopicForTopic,
            iterPeriodSubsets,
            projectionSuppressedTopics,
        )

        topicMap: dict[tuple[str, str], dict[str, str]] = {}
        rowOrder: dict[tuple[str, str], dict[str, int | str | None]] = {}
        periodRows: dict[str, list[dict[str, object]]] = {}
        validPeriods: list[str] = []
        latestAnnualRows: list[dict[str, object]] | None = None
        suppressed = projectionSuppressedTopics()

        for periodKey, reportKind, contentCol, subset in iterPeriodSubsets(self.stockCode):
            validPeriods.append(periodKey)
            topicRows = _reportRowsToTopicRows(subset, contentCol)
            periodRows[periodKey] = topicRows
            if reportKind == "annual" and latestAnnualRows is None:
                latestAnnualRows = topicRows

        if not validPeriods:
            return []

        teacherTopics = chapterTeacherTopics(latestAnnualRows or [])
        validPeriods = sortPeriods(validPeriods)
        latestPeriod = validPeriods[-1]

        def representativePeriodRank(period: str | None) -> int:
            if not isinstance(period, str):
                return -1
            year = int(period[:4])
            quarter = {"Q1": 1, "Q2": 2, "Q3": 3}.get(period[4:], 4)
            return (year * 10) + quarter

        topicChapter: dict[str, str] = {}
        topicFirstSeq: dict[str, tuple[int, int]] = {}

        # Clone sections ordering semantics without materializing the full sections DataFrame.
        for periodIdx, periodKey in enumerate(validPeriods):
            projected = applyProjections(periodRows.pop(periodKey, []), teacherTopics)
            for row in _expandStructuredRows(projected):
                chapter = row.get("chapter")
                topic = row.get("topic")
                text = row.get("text")
                blockType = row.get("blockType", "text")
                segmentKey = row.get("segmentKey")
                if not isinstance(chapter, str) or not isinstance(topic, str) or not isinstance(text, str):
                    continue
                if topic not in topicChapter:
                    topicChapter[topic] = chapter
                if topic in suppressed.get(chapter, set()):
                    continue
                if detailTopicForTopic(topic) is not None:
                    continue
                if not isinstance(blockType, str):
                    blockType = "text"
                if not isinstance(segmentKey, str) or not segmentKey:
                    continue

                key = (topic, segmentKey)
                topicMap.setdefault(key, {})[periodKey] = text

                majorNum = int(row.get("majorNum", 99))
                sortOrder = int(row.get("sortOrder", 999999))
                if topic not in topicFirstSeq or (majorNum, sortOrder) < topicFirstSeq[topic]:
                    topicFirstSeq[topic] = (majorNum, sortOrder)

                orderInfo = rowOrder.setdefault(
                    key,
                    {
                        "latestRank": 999999999,
                        "latestMissing": 1,
                        "firstRank": 999999999,
                        "sourceBlockOrder": int(row.get("sourceBlockOrder") or 0),
                        "segmentOrder": int(row.get("segmentOrder") or 0),
                        "segmentOccurrence": int(row.get("segmentOccurrence") or 1),
                        "_repPeriod": None,
                    },
                )
                orderInfo["firstRank"] = min(int(orderInfo["firstRank"]), sortOrder)
                orderInfo["sourceBlockOrder"] = min(
                    int(orderInfo["sourceBlockOrder"]), int(row.get("sourceBlockOrder") or 0)
                )
                orderInfo["segmentOrder"] = min(int(orderInfo["segmentOrder"]), int(row.get("segmentOrder") or 0))
                orderInfo["segmentOccurrence"] = min(
                    int(orderInfo["segmentOccurrence"]), int(row.get("segmentOccurrence") or 1)
                )
                if periodKey == latestPeriod:
                    orderInfo["latestMissing"] = 0
                    orderInfo["latestRank"] = min(int(orderInfo["latestRank"]), sortOrder)

                prevRank = representativePeriodRank(orderInfo.get("_repPeriod"))
                currRank = representativePeriodRank(periodKey)
                if currRank >= prevRank:
                    orderInfo["_repPeriod"] = periodKey

            if periodIdx % 4 == 3:
                gc.collect()

        if not topicMap:
            return []

        freqMetaByKey = {key: _rowFreqMeta(periodMap) for key, periodMap in topicMap.items()}
        topicKeysByTopic: dict[str, list[tuple[str, str]]] = {}
        for key in topicMap:
            topicKeysByTopic.setdefault(key[0], []).append(key)

        topicIndex: dict[str, int] = {}
        for topic, _seq in sorted(topicFirstSeq.items(), key=lambda item: item[1]):
            topicIndex[topic] = len(topicIndex)

        freqPriority = {"mixed": 0, "annual": 1, "quarterly": 2, "none": 3}

        def topicRowSortKey(key: tuple[str, str]) -> tuple[int, int, int, int, int, int, int, int, str]:
            topic, segmentKey = key
            majorNum, firstSeq = topicFirstSeq.get(topic, (99, 999999))
            topicIdx = topicIndex.get(topic, 999999)
            info = rowOrder.get(key, {})
            freqMeta = freqMetaByKey.get(key, {})
            return (
                majorNum,
                firstSeq,
                topicIdx,
                freqPriority.get(str(freqMeta.get("freqScope") or "none"), 9),
                int(info.get("latestMissing", 1)),
                int(info.get("latestRank", 999999999)),
                int(info.get("firstRank", 999999999)),
                int(info.get("segmentOccurrence", 1)),
                str(segmentKey),
            )

        descendingPeriods = sortPeriods(validPeriods, descending=True)
        periodRange = formatPeriodRange(descendingPeriods, descending=True, annualAsQ4=True)
        sortedTopics = [topic for topic, _seq in sorted(topicFirstSeq.items(), key=lambda item: item[1])]

        rows: list[dict[str, Any]] = []
        for rowIdx, topic in enumerate(sortedTopics):
            topicKeys = sorted(topicKeysByTopic.get(topic, []), key=topicRowSortKey)
            periodCount = 0
            preview = "-"
            for period in descendingPeriods:
                firstText: str | None = None
                anyNonNull = False
                for key in topicKeys:
                    value = topicMap.get(key, {}).get(period)
                    if value is None:
                        continue
                    anyNonNull = True
                    if firstText is None:
                        firstText = str(value)
                if anyNonNull:
                    periodCount += 1
                    if preview == "-" and firstText is not None:
                        previewText = firstText.replace("\n", " ").strip()[:80]
                        preview = f"{displayPeriod(period, annualAsQ4=True)}: {previewText}"

            chapter = topicChapter.get(topic) or self._chapterForTopic(topic)
            chapterNum = _CHAPTER_ORDER.get(chapter, 12)
            rows.append(
                {
                    "chapter": _CHAPTER_TITLES.get(chapter, chapter),
                    "topic": topic,
                    "label": self._topicLabel(topic),
                    "kind": "docs",
                    "source": "docs",
                    "periods": periodRange,
                    "shape": f"{periodCount}기간",
                    "preview": preview,
                    "_sortKey": (chapterNum, 100 + rowIdx),
                }
            )
        return rows

    def _indexReportRows(self, *, existingTopics: set[str] | None = None) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        if not self._hasReport:
            return rows

        from dartlab.providers.dart.report.types import API_TYPE_LABELS, API_TYPES

        existing = existingTopics or set()
        for rIdx, apiType in enumerate(API_TYPES):
            if apiType in existing:
                continue
            df = self.report.extract(apiType)
            if df is None or df.is_empty():
                continue
            chapter = self._chapterForTopic(apiType)
            chapterNum = _CHAPTER_ORDER.get(chapter, 12)
            rows.append(
                {
                    "chapter": _CHAPTER_TITLES.get(chapter, chapter),
                    "topic": apiType,
                    "label": API_TYPE_LABELS.get(apiType, apiType),
                    "kind": "report",
                    "source": "report",
                    "periods": "-",
                    "shape": _shapeString(df),
                    "preview": API_TYPE_LABELS.get(apiType, apiType),
                    "_sortKey": (chapterNum, 200 + rIdx),
                }
            )
        return rows

    @property
    def profile(self) -> _ProfileAccessor:
        """docs spine + finance/report merge layer -- 통합 프로필 접근자.

        Capabilities:
            - docs sections를 spine으로, finance/report 데이터를 merge하여 통합 뷰 제공
            - profile.sections로 source 우선순위(finance > report > docs) 적용된 sections 접근
            - profile.show(topic)으로 merge된 결과 조회

        AIContext:
            - c.sections는 내부적으로 profile.sections를 반환
            - 분석/리뷰에서 통합된 데이터를 소비하는 기본 경로

        Guide:
            - "통합 프로필" → c.profile
            - "merge된 sections" → c.profile.sections

        SeeAlso:
            - sections: profile.sections의 단축 접근
            - show: profile 기반 topic 데이터 조회

        Returns:
            _ProfileAccessor -- sections, show(), topics 메서드 제공

        Requires:
            데이터: docs (자동 다운로드). finance/report는 있으면 자동 merge.

        Example::

            c = Company("005930")
            c.profile.sections         # 통합 sections
            c.profile.show("BS")       # merge된 재무상태표
        """
        return self._profileAccessor

    @property
    def retrievalBlocks(self) -> pl.DataFrame | None:
        """원문 markdown 보존 retrieval block DataFrame.

        Capabilities:
            - docs 원문을 markdown 형태 그대로 보존한 검색용 블록
            - 각 블록은 topic/subtopic/period 단위로 분할
            - RAG, 벡터 검색, 원문 참조에 최적화된 포맷

        AIContext:
            - ask()/chat()에서 원문 기반 답변 생성 시 소스로 사용
            - retrieval 기반 컨텍스트 주입의 원천 데이터

        Guide:
            - "원문 검색용 블록" → c.retrievalBlocks
            - "RAG용 데이터" → c.retrievalBlocks

        SeeAlso:
            - contextSlices: retrievalBlocks를 LLM 윈도우에 맞게 슬라이싱한 결과
            - sections: 구조화된 데이터 지도 (retrievalBlocks의 원본)

        Returns:
            pl.DataFrame | None -- 컬럼: topic, subtopic, period, content 등. docs 없으면 None.

        Requires:
            데이터: docs (자동 다운로드)

        Example::

            c = Company("005930")
            c.retrievalBlocks          # 전체 retrieval 블록
        """
        return self.docs.retrievalBlocks

    @property
    def contextSlices(self) -> pl.DataFrame | None:
        """LLM 투입용 context slice DataFrame.

        Capabilities:
            - retrievalBlocks를 LLM 컨텍스트 윈도우에 맞게 슬라이싱
            - 토큰 예산 내에서 최대한 많은 관련 정보를 담는 압축 포맷
            - topic/period 기준 우선순위 정렬

        AIContext:
            - ask()/chat()의 시스템 프롬프트에 직접 주입되는 데이터
            - LLM이 소비하는 최종 형태의 컨텍스트

        Guide:
            - "LLM에 들어가는 컨텍스트" → c.contextSlices
            - "AI가 보는 데이터" → c.contextSlices

        SeeAlso:
            - retrievalBlocks: 슬라이싱 전 전체 retrieval 블록
            - ask: contextSlices를 내부적으로 소비하는 AI 질문 인터페이스

        Returns:
            pl.DataFrame | None -- 슬라이싱된 context 블록. docs 없으면 None.

        Requires:
            데이터: docs (자동 다운로드)

        Example::

            c = Company("005930")
            c.contextSlices            # LLM용 context 슬라이스
        """
        return self.docs.contextSlices

    # ── financeEngine (숫자 재무 데이터) ──

    def _ensureFinanceLoaded(self) -> None:
        """lazy finance: 첫 접근 시 buildTimeseries 실행."""
        if self._financeChecked:
            return
        self._financeChecked = True
        if not self._hasFinanceParquet:
            return
        from dartlab.providers.dart.finance.pivot import buildTimeseries

        ts = buildTimeseries(self.stockCode)
        if ts is not None:
            self._cache["_finance_q_CFS"] = ts
        else:
            self._hasFinanceParquet = False

    def _getFinanceBuild(self, period: str = "q", fsDivPref: str = "CFS"):
        """finance parquet 시계열 빌드 (캐싱).

        Args:
            period: "q" (분기별 standalone), "y" (연도별), "cum" (분기별 누적).
            fsDivPref: "CFS" (연결) 또는 "OFS" (별도).
        """
        cacheKey = f"_finance_{period}_{fsDivPref}"
        if cacheKey in self._cache:
            return self._cache[cacheKey]

        from dartlab.providers.dart.finance.pivot import (
            _aggregateAnnual,
            _aggregateCumulative,
            buildTimeseries,
        )

        if period == "q":
            result = buildTimeseries(self.stockCode, fsDivPref=fsDivPref)
        else:
            qResult = self._getFinanceBuild("q", fsDivPref=fsDivPref)
            if qResult is None:
                result = None
            else:
                series, periods = qResult
                if period == "y":
                    result = _aggregateAnnual(series, periods)
                elif period == "cum":
                    result = _aggregateCumulative(series, periods)
                else:
                    result = qResult
        self._cache[cacheKey] = result
        return result

    def getTimeseries(self, period: str = "q", fsDivPref: str = "CFS"):
        """Deprecated — use ``c.timeseries`` property instead.

        Args:
            period: "q" (분기별 standalone), "y" (연도별), "cum" (분기별 누적).
            fsDivPref: "CFS" (연결) 또는 "OFS" (별도).
        """
        import warnings

        warnings.warn(
            "getTimeseries()는 deprecated입니다. c.timeseries / c.annual / c.cumulative를 사용하세요.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._getFinanceBuild(period, fsDivPref)

    def _getRatiosInternal(self, fsDivPref: str = "CFS"):
        """내부용 재무비율 계산 (deprecation 없음)."""
        cacheKey = f"_ratios_{fsDivPref}"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        from dartlab.core.finance.ratios import calcRatios

        archetypeOverride = _ratioArchetypeOverrideForIndustryGroup(getattr(self.sector, "industryGroup", None))
        ts = self._getFinanceBuild("q", fsDivPref)
        result = None
        if ts is not None:
            series, _ = ts
            result = calcRatios(series, archetypeOverride=archetypeOverride)

        if _shouldFallbackToAnnualRatios(result, archetypeOverride):
            annual = self._getFinanceBuild("y", fsDivPref)
            if annual is not None:
                annualSeries, _ = annual
                annualResult = calcRatios(annualSeries, annual=True, archetypeOverride=archetypeOverride)
                if _ratioResultHasHeadlineSignal(annualResult):
                    result = annualResult

        self._cache[cacheKey] = result
        return result

    @property
    def ratios(self) -> pl.DataFrame | None:
        """재무비율 시계열 (분류/항목 x 기간 DataFrame).

        Capabilities:
            - 수익성/안정성/성장성/효율성/밸류에이션 5대 분류
            - 분기별 시계열 비율 자동 계산
            - finance XBRL 기반 정확한 비율

        AIContext:
            - ask()/chat()에서 재무 건전성/수익성 평가의 핵심 데이터
            - insights, review가 내부적으로 ratios를 소비

        Guide:
            - "재무비율 보여줘" → c.ratios
            - "ROE 추이" → c.ratios에서 ROE 행 확인
            - "부채비율은?" → c.ratios에서 안정성 분류 확인

        SeeAlso:
            - ratioSeries: dict 구조 재무비율 (프로그래밍 용도)
            - insights: 재무비율 기반 등급 + 이상치 분석
            - select: c.select("ratios", ["ROE"]) 특정 비율 추출

        Returns:
            pl.DataFrame — 분류 | 항목 | 2025Q3 | 2025Q2 | ... 또는 None.

        Requires:
            데이터: finance (자동 다운로드)

        Example::

            c = Company("005930")
            c.ratios  # 분류 | 항목 | 2025Q3 | 2025Q2 | ...
        """
        rs = self._ratioSeries()
        if rs is None:
            self._hintOnce("ratios", "ratios", "finance")
            return None
        series, periods = rs
        df = _ratioSeriesToDataFrame(series, periods)
        if df is not None:
            # 기간 컬럼 역순 정렬
            metaCols = [c for c in df.columns if not _isPeriodColumn(c)]
            periodCols = [c for c in df.columns if _isPeriodColumn(c)]
            periodCols.sort(key=lambda p: (int(p[:4]), int(p[-1])), reverse=True)
            df = df.select(metaCols + periodCols)
        return df

    @property
    def timeseries(self):
        """분기별 standalone 시계열 (연결 기준).

        Capabilities:
            - BS/IS/CF 계정별 분기 standalone 시계열
            - 최대 10년 분기별 데이터
            - finance XBRL 정규화 기반

        AIContext:
            - insights, forecast, valuation 등 분석 엔진의 핵심 입력 데이터
            - 분기별 추세 분석의 기초

        Guide:
            - "분기별 시계열 데이터" → c.timeseries
            - "매출 분기별 추이" → series, periods = c.timeseries; series["IS"]["sales"]

        SeeAlso:
            - annual: 연도별 집계 시계열
            - cumulative: 분기별 누적(YTD) 시계열
            - BS: DataFrame 형태 재무상태표 (timeseries의 다른 뷰)

        Returns:
            (series, periods) 또는 None.
            series = {"BS": {"snakeId": [값...]}, "IS": {...}, "CF": {...}}
            periods = ["2016-Q1", "2016-Q2", ..., "2024-Q4"]

        Requires:
            데이터: finance (자동 다운로드)

        Example::

            c = Company("005930")
            series, periods = c.timeseries
            series["IS"]["sales"]  # 분기별 매출 시계열
        """
        return self._financeProperty("timeseries")

    @property
    def annual(self):
        """연도별 시계열 (연결 기준).

        Capabilities:
            - BS/IS/CF 계정별 연도 시계열
            - 분기 데이터를 연도 단위로 집계
            - finance XBRL 정규화 기반

        AIContext:
            - 연도 단위 추세 분석 — forecast, ratioSeries의 기초 데이터

        Guide:
            - "연���별 시계열" → c.annual
            - "연간 매출 추이" → series, years = c.annual; series["IS"]["sales"]

        SeeAlso:
            - timeseries: 분기별 시계열 (더 세밀)
            - cumulative: 분기별 누적 시계열
            - ratioSeries: 연도별 재무비율 시계열

        Returns:
            (series, years) 또는 None.

        Requires:
            데이터: finance (자동 다운로드)

        Example::

            c = Company("005930")
            series, years = c.annual
            series["IS"]["sales"]  # 연도별 매출 시계열
        """
        return self._financeProperty("annual")

    @property
    def cumulative(self):
        """분기별 누적 시계열 (연결 기준).

        Capabilities:
            - IS/CF 계정별 분기 누적(YTD) 시계열
            - Q1→Q2→Q3→Q4 누적 합산
            - finance XBRL 정규화 기반

        AIContext:
            - Q4 누적이 연간 실적 — 연중 진행률 파악에 활용

        Guide:
            - "누적 시계열" → c.cumulative
            - "올해 누적 매출" → series, periods = c.cumulative

        SeeAlso:
            - timeseries: 분기별 standalone (누적이 아닌 개별 분기)
            - annual: 연도별 집계

        Returns:
            (series, periods) 또는 None.

        Requires:
            데이터: finance (자동 다운로드)

        Example::

            c = Company("005930")
            series, periods = c.cumulative
        """
        return self._financeProperty("cumulative")

    @property
    def sceMatrix(self):
        """자본변동표 연도별 매트릭스 (연결 기준).

        Capabilities:
            - 원인(cause) x 세부(detail) x 연도 3차원 매트릭스
            - 자본 구성요소별 변동 원인 추적
            - finance XBRL 정규화 기반

        AIContext:
            - 자본 변동 원인 분석 — 배당/자사주/유증 등 자본 이벤트 추적

        Guide:
            - "자본변동표 매트릭스" → c.sceMatrix
            - "자본 변동 원인 추적" → matrix, years = c.sceMatrix

        SeeAlso:
            - SCE: DataFrame 형태 자본변동표 (sceMatrix의 2D 뷰)
            - BS: 재무상태표 (자본 잔액 확인)
            - capital: 주주환원 분석 (배당/자사주)

        Returns:
            (matrix, years) 또는 None.
            matrix[year][cause][detail] = 금액
            years = ["2016", ..., "2024"]

        Requires:
            데이터: finance (자동 다운로드)

        Example::

            c = Company("005930")
            matrix, years = c.sceMatrix
            matrix["2024"]["net_income"]["retained_earnings"]
        """
        return self._financeProperty("sceMatrix")

    @property
    def SCE(self):
        """자본변동표 (Statement of Changes in Equity) — 계정명 × 연도 DataFrame.

        Capabilities:
            - XBRL 정규화 자본변동표
            - 연결 기준 자본 구성요소별 변동
            - 연도별 시계열

        AIContext:
            - ask()/chat()에서 자본 구조 변동 분석 컨텍스트

        Guide:
            - "자본변동표 보여줘" → c.SCE
            - "자본 구성 변화" → c.SCE

        SeeAlso:
            - sceMatrix: 3차원 매트릭스 형태 (원인별 상세 추적)
            - CIS: 포괄손익계산서 (자본변동의 원천)
            - BS: 재무상태표 (자본 잔액)

        Returns:
            pl.DataFrame — 계정명 | 2024 | 2023 | ... 또는 None.

        Requires:
            데이터: finance (자동 다운로드)

        Example::

            c = Company("005930")
            c.SCE  # 자본변동표
        """
        return self._financeProperty("SCE")

    @property
    def ratioSeries(self):
        """재무비율 연도별 시계열 (IS/BS/CF와 동일한 dict 구조).

        Capabilities:
            - 수익성/안정성/성장성/효율성/밸류에이션 비율
            - 연도별 dict 구조 (timeseries/annual과 동일 형태)
            - finance XBRL 기반 정확한 비율

        AIContext:
            - 프로그래밍 방식 비율 접근 — insights/analysis 엔진이 내부적으로 소비

        Guide:
            - "비율 시계열 dict" → c.ratioSeries
            - "ROE 연도별 리스트" → series, years = c.ratioSeries; series["RATIO"]["roe"]

        SeeAlso:
            - ratios: DataFrame 형태 재무비율 (사용자 열람용)
            - annual: 연도별 재무 시계열 (비율이 아닌 원본 금액)

        Returns:
            ({"RATIO": {snakeId: [v1, v2, ...]}}, years) 또는 None.

        Requires:
            데이터: finance (자동 다운로드)

        Example::

            c = Company("005930")
            series, years = c.ratioSeries
            series["RATIO"]["roe"]  # [8.69, 13.20, 16.55, ...]
        """
        return self._financeProperty("ratioSeries")

    # ── 섹터 분류 ──

    @property
    def sector(self):
        """WICS 투자 섹터 분류 (KIND 업종 + 키워드 기반).

        Capabilities:
            - WICS 11대 섹터 + 하위 산업그룹 자동 분류
            - KIND 업종명 + 주요제품 키워드 기반 매칭
            - override 테이블 우선 → 키워드 → 업종명 순 fallback

        Returns:
            SectorInfo (sector, industryGroup, confidence, source).

        Requires:
            데이터: KIND 상장사 목록 (자동 로드)

        Example::

            c = Company("005930")
            c.sector              # SectorInfo(IT/반도체와반도체장비, conf=1.00, src=override)
            c.sector.sector       # Sector.IT
            c.sector.industryGroup  # IndustryGroup.SEMICONDUCTOR

        AIContext:
            - 섹터 분류 결과로 동종업계 비교, 섹터 파라미터 자동 선택
            - analysis/valuation에서 섹터별 벤치마크 기준으로 활용

        Guide:
            - "이 회사 어떤 섹터야?" → c.sector
            - "업종 분류" → c.sector

        SeeAlso:
            - sectorParams: 섹터별 밸���에이션 파라미터 (할인율, PER 등)
            - rank: 섹�� 내 규모 순위
            - insights: 섹터 기준 등급 평가
        """
        cacheKey = "_sector"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        from dartlab.core.sector import classify

        kindDf = getKindList()
        row = kindDf.filter(pl.col("종목코드") == self.stockCode)
        kindIndustry = row["업종"][0] if row.height > 0 and "업종" in kindDf.columns else None
        mainProducts = row["주요제품"][0] if row.height > 0 and "주요제품" in kindDf.columns else None
        result = classify(self.corpName or "", kindIndustry, mainProducts)
        self._cache[cacheKey] = result
        return result

    @property
    def sectorParams(self):
        """현재 종목의 섹터별 밸류에이션 파라미터.

        Capabilities:
            - 섹터별 할인율, 성장률, PER 멀티플 제공
            - 섹터 분류 결과에 연동된 파라미터 자동 선택

        Returns:
            SectorParams (discountRate, growthRate, perMultiple, ...).

        Requires:
            데이터: sector 분류 결과 (자동 연산)

        Example::

            c = Company("005930")
            c.sectorParams.perMultiple   # 15
            c.sectorParams.discountRate  # 13.0

        AIContext:
            - valuation()에서 DCF 할인율, 성장률 자동 적용
            - 섹터 특성 반영된 밸류에이션 파라미터

        Guide:
            - "이 섹터 할인율은?" → c.sectorParams.discountRate
            - "PER 멀티플" → c.sectorParams.perMultiple

        SeeAlso:
            - sector: 섹터 분류 정보 (sectorParams의 기반)
            - valuation: 밸류에이션 (sectorParams를 내부적으로 소비)
        """
        cacheKey = "_sectorParams"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        from dartlab.core.sector import getParams

        result = getParams(self.sector)
        self._cache[cacheKey] = result
        return result

    # ── 규모 랭크 ──

    @property
    def rank(self):
        """전체 시장 + 섹터 내 규모 순위 (매출/자산/성장률).

        스냅샷이 없으면 None 반환. buildSnapshot()으로 사전 빌드 필요.

        Capabilities:
            - 전체 시장 내 매출/자산 순위
            - 섹터 내 상대 순위
            - 매출 성장률 기반 규모 분류 (large/mid/small)

        Returns:
            RankInfo 또는 스냅샷 미빌드 시 None.

        Requires:
            데이터: buildSnapshot() 사전 실행 필요

        Example::

            from dartlab.analysis.financial.insight import buildSnapshot
            buildSnapshot()

            c = Company("005930")
            c.rank                    # RankInfo(삼성전자, 매출 2/2192, 섹터 2/467, large)
            c.rank.revenueRank        # 2
            c.rank.revenueRankInSector # 2
            c.rank.sizeClass          # "large"

        AIContext:
            - 시장/섹터 내 상대 위치 파악 — 피어 비교 분석의 기초
            - sizeClass로 대형/중형/소형주 분류

        Guide:
            - "이 회사 순위는?" → c.rank
            - "시장에서 몇 등이야?" → c.rank.revenueRank
            - "대형주야?" → c.rank.sizeClass

        SeeAlso:
            - sector: 섹터 분류 (rank의 기준 그룹)
            - insights: 종합 등급 평가
        """
        cacheKey = "_rank"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        from dartlab.scan.rank import getRank

        result = getRank(self.stockCode)
        self._cache[cacheKey] = result
        return result

    # ── 인사이트 분석 ──

    @property
    def insights(self):
        """종합 인사이트 분석 (7영역 등급 + 이상치 + 요약).

        Capabilities:
            - 7영역 등급 평가 (실적, 수익성, 성장, 안정성, 현금흐름, 효율, 밸류에이션)
            - 이상치 자동 탐지 (급변, 임계 초과)
            - 텍스트 요약 + 투자 프로파일 분류

        Returns:
            AnalysisResult 또는 finance 데이터 없으면 None.

        Requires:
            데이터: finance (자동 다운로드)

        Example::

            c = Company("005930")
            c.insights.grades()       # {'performance': 'A', ...}
            c.insights.summary        # "삼성전자는 실적, 재무건전성 등..."
            c.insights.anomalies      # [Anomaly(...), ...]
            c.insights.profile        # "premium"

        AIContext:
            - ask()/chat()에서 재무 건전성 종합 판단의 핵심 데이터
            - 7영역 등급 + 이상치 + 투자 프로파일을 컨텍스트로 주입

        Guide:
            - "이 회사 재무 등급은?" → c.insights.grades()
            - "이상 징후 있어?" → c.insights.anomalies
            - "투자 프로파일" → c.insights.profile

        SeeAlso:
            - analysis: 14축 개별 상세 분석 (insights보다 세밀)
            - review: 14섹션 보고서 (insights를 내부적으로 참조)
            - ratios: 재무비율 시계열 (insights의 입력 데이터)
        """
        if not self._hasFinance:
            self._hintOnce("insights", "insights", "finance")
            return None
        cacheKey = "_insights"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        from dartlab.analysis.financial.insight import analyze

        result = analyze(
            self.stockCode,
            company=self,
            qSeriesPair=self.timeseries,
            aSeriesPair=self.annual,
        )
        self._cache[cacheKey] = result
        return result

    def audit(self):
        """감사 리스크 종합 분석.

        Capabilities:
            - 감사의견 추이 (적정/한정/부적정/의견거절)
            - 감사인 변경 이력 + 사유
            - 계속기업 불확실성 플래그
            - 핵심감사사항 (KAM) 추출
            - 내부회계관리제도 검토의견

        Args:
            없음 (self 바인딩).

        Returns:
            dict — opinion, auditorChanges, goingConcern, kam, internalControl.

        Requires:
            데이터: docs + report (자동 다운로드)

        Example::

            c = Company("005930")
            c.audit()

        AIContext:
            - 감사 리스크 종합 평가 — 투자 의사결정의 핵심 안전장치
            - 감사의견 변경, 계속기업 불확실성은 최고 경고 수준

        Guide:
            - "감사의견 확인" → c.audit()
            - "감사인 바뀌었어?" → c.audit()["auditorChanges"]
            - "계속기업 의문은?" → c.audit()["goingConcern"]

        SeeAlso:
            - governance: 지배구조 분석 (감사위원회 구성 포함)
            - insights: 종합 등급 (감사 리스크도 반영)
            - review: 재무정합성 섹션에서 감사 결과 활용
        """
        from dartlab.analysis.financial.insight.pipeline import analyzeAudit

        return analyzeAudit(self)

    def forecast(self, *, horizon: int = 3):
        """매출 앙상블 예측 (다중 모델 가중 평균).

        Capabilities:
            - 선형회귀 + CAGR + 이동평균 앙상블
            - 섹터별 성장률 보정
            - 신뢰구간 (상한/하한) 제공

        Args:
            horizon: 예측 기간 (연 단위, 기본 3년).

        Returns:
            ForecastResult — predicted, upper, lower, models, weights.

        Requires:
            데이터: finance (자동 다운로드)

        Example::

            c = Company("005930")
            c.forecast()
            c.forecast(horizon=5)

        AIContext:
            - 매출 예측 결과를 valuation, simulation과 조합하여 종합 전망 생성
            - 신뢰구간으로 불확실성 정도 전달

        Guide:
            - "매출 예측해줘" → c.forecast()
            - "5년 예측" → c.forecast(horizon=5)
            - "예측 신뢰구간" → result.upper, result.lower

        SeeAlso:
            - valuation: 예측 기반 적정가치 산출
            - simulation: 시나리오별 영향 추정
            - annual: 예측의 입력 데이터 (과거 연도별 실적)
        """
        from dartlab.analysis.forecast.revenueForecast import forecastRevenue

        ts = self.finance.timeseries
        series = ts[0] if isinstance(ts, tuple) else ts
        return forecastRevenue(
            series,
            stockCode=self.stockCode,
            sectorKey=getattr(self, "sectorKey", None),
            market="KR",
            horizon=horizon,
            currency="KRW",
        )

    def valuation(self, *, shares: int | None = None):
        """종합 밸류에이션 (DCF + DDM + 상대가치).

        Capabilities:
            - DCF (현금흐름 할인) 모델
            - DDM (배당 할인) 모델
            - 상대가치 (PER/PBR/EV-EBITDA) 비교
            - 모델별 적정가 + 종합 가중 평균

        Args:
            shares: 발행주식수 (None이면 profile에서 자동 조회).

        Returns:
            ValuationResult — dcf, ddm, relative, composite.

        Requires:
            데이터: finance (자동 다운로드)

        Example::

            c = Company("005930")
            c.valuation()
            c.valuation(shares=5_969_782_550)

        AIContext:
            - DCF/DDM/상대가치 종합 적정가치 — 투자 판단의 핵심 출력
            - ask()에서 "적정가치" 질문 시 자동으로 이 결과 활용

        Guide:
            - "적정가치 구해줘" → c.valuation()
            - "DCF 밸류에이션" → c.valuation().dcf
            - "PER 기준 가치" → c.valuation().relative

        SeeAlso:
            - forecast: 매출 예측 (valuation의 입력)
            - sectorParams: 섹터별 할인율/멀티플 (valuation이 내부 사용)
            - simulation: 시나리오별 가치 변동 추정
        """
        from dartlab.analysis.valuation.valuation import fullValuation

        ts = self.finance.timeseries
        series = ts[0] if isinstance(ts, tuple) else ts
        if shares is None:
            shares = getattr(self.profile, "sharesOutstanding", None)
            if shares:
                shares = int(shares)
        return fullValuation(series, shares=shares, currency="KRW")

    def simulation(self, *, scenarios: list[str] | None = None):
        """경제 시나리오 시뮬레이션 (거시경제 충격 → 재무 영향).

        Capabilities:
            - 기본 시나리오: 금리인상, 경기침체, 원화약세, 수요급감 등
            - 시나리오별 매출/영업이익/현금흐름 영향 추정
            - 섹터 민감도 반영

        Args:
            scenarios: 시뮬레이션할 시나리오 이름 리스트 (None이면 전체).

        Returns:
            dict — 시나리오별 영향 추정치. finance 없으면 None.

        Requires:
            데이터: finance (자동 다운로드)

        Example::

            c = Company("005930")
            c.simulation()
            c.simulation(scenarios=["금리인상", "경기침체"])

        AIContext:
            - 거시경제 충격 시나리오별 재무 영향 정량화
            - ask()에서 리스크 질문 시 시뮬레이션 결과 컨텍스트로 활용

        Guide:
            - "금리인상 영향은?" → c.simulation(scenarios=["금리인상"])
            - "경기침체 시 실적 전망" → c.simulation(scenarios=["경기침체"])
            - "전체 시나리오 분석" → c.simulation()

        SeeAlso:
            - forecast: 기본 시나리오 매출 예측
            - valuation: 적정가치 산출
            - gather: 거시경제 지표 수집 (macro 축)
        """
        from dartlab.analysis.forecast.simulation import simulateAllScenarios

        ts = self.finance.timeseries
        if ts is None:
            return None
        series = ts[0] if isinstance(ts, tuple) else ts
        return simulateAllScenarios(
            series,
            sectorKey=getattr(self, "sectorKey", None),
            scenarios=scenarios,
        )

    def research(self, *, sections: list[str] | None = None, includeMarket: bool = True):
        """종합 기업분석 리포트 (재무 + 시장 + 공시 통합).

        Capabilities:
            - 재무 분석 (수익성, 성장, 안정성, 현금흐름)
            - 시장 포지션 + 섹터 비교
            - 공시 기반 정성 분석 (사업모델, 리스크)
            - 섹션별 선택적 생성

        Args:
            sections: 포함할 섹션 리스트 (None이면 전체).
            includeMarket: 시장 데이터 포함 여부 (기본 True).

        Returns:
            ResearchReport — 섹션별 분석 결과 통합 객체.

        Requires:
            데이터: finance + docs (자동 다운로드)

        Example::

            c = Company("005930")
            c.research()
            c.research(sections=["financial", "risk"])

        AIContext:
            - 재무 + 시장 + 공시 통합 리포트 — ask()에서 종합 분석 컨텍스트
            - 섹션별 선택적 생성으로 필요한 부분만 딥다이브

        Guide:
            - "종합 리서치 보고서" → c.research()
            - "재무+리스크만 분석" → c.research(sections=["financial", "risk"])

        SeeAlso:
            - review: 14섹션 구조화 보고서 (research보다 구조적)
            - insights: 7영역 등급 요약 (research보다 간결)
            - analysis: 14축 개별 분석
        """
        cacheKey = "_research"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        from dartlab.analysis.financial.research import generateResearch

        result = generateResearch(self, sections=sections, includeMarket=includeMarket)
        self._cache[cacheKey] = result
        return result

    @property
    def market(self) -> str:
        """시장 코드 (DART 제공자는 항상 KR).

        SeeAlso:
            - currency: 통화 코드

        Returns:
            str — "KR".

        Example::

            c = Company("005930")
            c.market  # "KR"
        """
        return "KR"

    @property
    def currency(self) -> str:
        """통화 코드 (DART 제공자는 항상 KRW).

        SeeAlso:
            - market: 시장 코드

        Returns:
            str — "KRW".

        Example::

            c = Company("005930")
            c.currency  # "KRW"
        """
        return "KRW"

    # ── network (관계 지도) ──────────────────────────────────

    def _ensureNetwork(self) -> tuple[dict, dict] | None:
        """network 파이프라인 캐싱 → (data, full)."""
        if "_network_data" not in self._cache:
            from dartlab.scan.network import build_graph, export_full

            data = build_graph(verbose=False)
            self._cache["_network_data"] = data
            self._cache["_network_full"] = export_full(data)
        return self._cache["_network_data"], self._cache["_network_full"]

    def network(self, view: str | None = None, *, hops: int = 1):
        """관계 네트워크 (지분출자 + 그룹 계열사 지도).

        Capabilities:
            - 그룹 계열사 목록 (members)
            - 출자/피출자 연결 + 지분율 (edges)
            - 순환출자 경로 탐지 (cycles)
            - ego 서브그래프 (peers)
            - 인터랙티브 네트워크 시각화 (브라우저)

        Args:
            view: None이면 시각화(NetworkView), "members"/"edges"/"cycles"/"peers"이면 DataFrame.
            hops: peers/시각화 뷰에서 홉 수.

        Returns:
            NetworkView (view=None) 또는 DataFrame (view 지정 시). 데이터 없으면 None.

        Requires:
            데이터: DART 대량보유/임원 공시 (자동 수집)

        Example::

            c = Company("005930")
            c.network()              # → NetworkView (.show()로 브라우저)
            c.network().show()       # 브라우저 오픈
            c.network("members")     # 같은 그룹 계열사 DataFrame
            c.network("edges")       # 출자/지분 연결 DataFrame
            c.network("cycles")      # 순환출자 경로 DataFrame
            c.network("peers")       # 이 회사 중심 서브그래프 DataFrame

        AIContext:
            - 그룹 계열사/출자 구조 파악 — 지배구조 분석의 기초 데이터
            - 순환출자 탐지로 거버넌스 리스크 감지

        Guide:
            - "계열사 관계도" → c.network() 또는 c.network().show()
            - "같은 그룹 계열사" → c.network("members")
            - "출자/지분 구조" → c.network("edges")
            - "순환출자 있어?" → c.network("cycles")

        SeeAlso:
            - governance: 이사회/감사위원/최대주주 분석
            - capital: 주주환원 분석
        """
        result = self._ensureNetwork()
        if result is None:
            return None
        data, full = result
        code = self.stockCode
        group = data["code_to_group"].get(code, self.corpName or code)

        if view is None:
            from dartlab.scan.network import export_ego
            from dartlab.tools.network import render_network

            ego = export_ego(data, full, code, hops=hops)
            center_name = data["code_to_name"].get(code, code)
            return render_network(
                ego["nodes"],
                ego["edges"],
                f"{center_name} 관계 네트워크",
                center_id=code,
            )
        if view == "members":
            return self._networkMembers(data, code, group)
        if view == "edges":
            return self._networkEdges(full, code)
        if view == "cycles":
            return self._networkCycles(data, code)
        if view == "peers":
            return self._networkPeers(data, full, code, hops=hops)
        return None

    def _networkMembers(self, data: dict, code: str, group: str) -> pl.DataFrame:
        """같은 그룹 계열사 목록."""
        members = [n for n in data["all_node_ids"] if data["code_to_group"].get(n) == group]
        rows = []
        for m in sorted(members):
            meta = data["listing_meta"].get(m, {})
            rows.append(
                {
                    "종목코드": m,
                    "회사명": meta.get("name", m),
                    "시장": meta.get("market", ""),
                    "업종": meta.get("industry", ""),
                    "자기": m == code,
                }
            )
        return pl.DataFrame(rows)

    def _networkEdges(self, full: dict, code: str) -> pl.DataFrame:
        """이 회사의 출자/지분 연결."""
        node_map = {n["id"]: n for n in full["nodes"]}
        rows = []
        for e in full["edges"]:
            if e["type"] == "person_shareholder":
                continue
            if e["source"] == code:
                target = e["target"]
                node = node_map.get(target)
                rows.append(
                    {
                        "종목코드": target,
                        "회사명": node["label"] if node else target,
                        "유형": e["type"],
                        "방향": "출자 →",
                        "목적": e.get("purpose", ""),
                        "지분율": e.get("ownershipPct"),
                        "그룹": node["group"] if node else "",
                    }
                )
            elif e["target"] == code:
                source = e["source"]
                node = node_map.get(source)
                rows.append(
                    {
                        "종목코드": source,
                        "회사명": node["label"] if node else source,
                        "유형": e["type"],
                        "방향": "← 피출자",
                        "목적": e.get("purpose", ""),
                        "지분율": e.get("ownershipPct"),
                        "그룹": node["group"] if node else "",
                    }
                )
        if not rows:
            return pl.DataFrame(
                schema={
                    "종목코드": pl.Utf8,
                    "회사명": pl.Utf8,
                    "유형": pl.Utf8,
                    "방향": pl.Utf8,
                    "목적": pl.Utf8,
                    "지분율": pl.Float64,
                    "그룹": pl.Utf8,
                }
            )
        return pl.DataFrame(rows).sort("지분율", descending=True, nulls_last=True)

    def _networkCycles(self, data: dict, code: str) -> pl.DataFrame:
        """이 회사가 포함된 순환출자 경로."""
        rows = []
        for i, cy in enumerate(data["cycles"]):
            if code not in cy:
                continue
            path = " → ".join(data["code_to_name"].get(c, c) for c in cy)
            rows.append({"번호": i + 1, "경로": path, "길이": len(cy) - 1})
        if not rows:
            return pl.DataFrame(schema={"번호": pl.Int64, "경로": pl.Utf8, "길이": pl.Int64})
        return pl.DataFrame(rows)

    def _networkPeers(self, data: dict, full: dict, code: str, *, hops: int = 1) -> pl.DataFrame:
        """이 회사 중심 서브그래프 (ego 뷰) → DataFrame."""
        from dartlab.scan.network import export_ego

        ego = export_ego(data, full, code, hops=hops)
        rows = []
        for n in ego["nodes"]:
            if n["type"] != "company":
                continue
            rows.append(
                {
                    "종목코드": n["id"],
                    "회사명": n["label"],
                    "그룹": n["group"],
                    "업종": n.get("industry", ""),
                    "연결수": n["degree"],
                    "자기": n["id"] == code,
                }
            )
        if not rows:
            return pl.DataFrame(
                schema={
                    "종목코드": pl.Utf8,
                    "회사명": pl.Utf8,
                    "그룹": pl.Utf8,
                    "업종": pl.Utf8,
                    "연결수": pl.Int64,
                    "자기": pl.Boolean,
                }
            )
        df = pl.DataFrame(rows)
        return df.sort("연결수", descending=True)

    # ── governance (지배구조) ─────────────────────────────────

    def _ensureGovernance(self) -> pl.DataFrame | None:
        if "_governance" not in self._cache:
            from dartlab.scan.governance import scan_governance

            self._cache["_governance"] = scan_governance(verbose=False)
        return self._cache["_governance"]

    def governance(self, view: str | None = None) -> pl.DataFrame | None:
        """지배구조 분석 (이사회, 감사위원, 최대주주).

        Capabilities:
            - 사외이사 비율 + 감사위원회 구성
            - 최대주주 지분율 + 특수관계인
            - 시장 전체 거버넌스 횡단 비교

        Args:
            view: None → 이 회사 행, "all" → 전체, "market" → 시장별 요약.

        Returns:
            DataFrame 또는 데이터 없으면 None.

        Requires:
            데이터: DART 정기보고서 (자동 수집)

        Example::

            c = Company("005930")
            c.governance()           # 삼성전자 거버넌스
            c.governance("all")      # 전체 상장사

        AIContext:
            - 지배구조 리스크 평가 — 사외이사/감사위원/최대주주 정량 데이터
            - 시장 횡단 비교로 상대적 거버넌스 수준 판단

        Guide:
            - "지배구조 분석" → c.governance()
            - "사외이사 비율은?" → c.governance()
            - "전체 상장사 거버넌스 비교" → c.governance("all")

        SeeAlso:
            - network: 출자/계열사 관계 (거버넌스의 다른 관점)
            - audit: 감사 리스크 (감사위원회와 연관)
        """
        return self._scanView(self._ensureGovernance(), view)

    # ── workforce (인력) ───────────────────────────────────

    def _ensureWorkforce(self) -> pl.DataFrame | None:
        if "_workforce" not in self._cache:
            from dartlab.scan.workforce import scan_workforce

            self._cache["_workforce"] = scan_workforce(verbose=False)
        return self._cache["_workforce"]

    def workforce(self, view: str | None = None) -> pl.DataFrame | None:
        """인력/급여 분석 (직원수, 평균급여, 근속연수).

        Capabilities:
            - 직원수 + 정규직/비정규직 비율
            - 평균 급여 + 1인당 매출
            - 평균 근속연수
            - 시장 전체 인력 횡단 비교

        Args:
            view: None → 이 회사 행, "all" → 전체, "market" → 시장별 요약.

        Returns:
            DataFrame 또는 데이터 없으면 None.

        Requires:
            데이터: DART 정기보고서 (자동 수집)

        Example::

            c = Company("005930")
            c.workforce()            # 삼성전자 인력 현황
            c.workforce("all")       # 전체 상장사

        AIContext:
            - 인력 효율성/근무환경 정량 평가 — 1인당 매출, 급여 수준 비교
            - 시장 횡단 비교로 인적자원 경쟁력 판단

        Guide:
            - "직원 현황" → c.workforce()
            - "평균 급여는?" → c.workforce()
            - "전체 상장사 인력 비교" → c.workforce("all")

        SeeAlso:
            - governance: 이사회/감사위원 구성 (인력의 다른 관점)
            - show: c.show("employee")로 docs 기반 직원 상세
        """
        return self._scanView(self._ensureWorkforce(), view)

    # ── capital (주주환원) ─────────────────────────────────

    def _ensureCapital(self) -> pl.DataFrame | None:
        if "_capital" not in self._cache:
            from dartlab.scan.capital import scan_capital

            self._cache["_capital"] = scan_capital(verbose=False)
        return self._cache["_capital"]

    def capital(self, view: str | None = None) -> pl.DataFrame | None:
        """주주환원 분석 (배당, 자사주, 총환원율).

        Capabilities:
            - 배당수익률 + 배당성향 추이
            - 자사주 매입/소각 이력
            - 총주주환원율 (배당 + 자사주)
            - 시장 전체 주주환원 횡단 비교

        Args:
            view: None → 이 회사 행, "all" → 전체, "market" → 시장별 요약.

        Returns:
            DataFrame 또는 데이터 없으면 None.

        Requires:
            데이터: DART 정기보고서 (자동 수집)

        Example::

            c = Company("005930")
            c.capital()              # 삼성전자 주주환원
            c.capital("all")         # 전체 상장사

        AIContext:
            - 주주환원 정책 평가 — 배당수익률/성향/자사주 정량 데이터
            - 시장 횡단 비교로 상대적 환원 수준 판단

        Guide:
            - "배당 정보" → c.capital() 또는 c.show("dividend")
            - "주주환원율은?" → c.capital()
            - "전체 상장사 배당 비교" → c.capital("all")

        SeeAlso:
            - show: c.show("dividend")로 docs 기반 배당 상세
            - sceMatrix: 자본변동표 (배당/자사주가 자본에 미치는 영향)
            - debt: 부채 구조 (자본 정책의 다른 면)
        """
        return self._scanView(self._ensureCapital(), view)

    # ── debt (부채 구조) ──────────────────────────────────

    def _ensureDebt(self) -> pl.DataFrame | None:
        if "_debt" not in self._cache:
            from dartlab.scan.debt import scan_debt

            self._cache["_debt"] = scan_debt(verbose=False)
        return self._cache["_debt"]

    def debt(self, view: str | None = None) -> pl.DataFrame | None:
        """부채 구조 분석 (차입금, 부채비율, 만기 구조).

        Capabilities:
            - 총차입금 + 순차입금 규모
            - 부채비율 + 차입금의존도
            - 단기/장기 차입금 비율
            - 시장 전체 부채 구조 횡단 비교

        Args:
            view: None → 이 회사 행, "all" → 전체, "market" → 시장별 요약.

        Returns:
            DataFrame 또는 데이터 없으면 None.

        Requires:
            데이터: DART 정기보고서 (자동 수집)

        Example::

            c = Company("005930")
            c.debt()                 # 삼성전자 부채 구조
            c.debt("all")            # 전체 상장사

        AIContext:
            - 부채 구조/건전성 정량 평가 — 차입금 의존도, 만기 구조
            - 시장 횡단 비교로 상대적 재무 안정성 판단

        Guide:
            - "부채 구조 분석" → c.debt()
            - "부채비율은?" → c.debt() 또는 c.ratios
            - "전체 상장사 부채 비교" → c.debt("all")

        SeeAlso:
            - BS: 재무상태표 (부채 원본 데이터)
            - ratios: 재무비율 (부채비율 포함)
            - capital: 주주환원 (자본 정책의 다른 면)
        """
        return self._scanView(self._ensureDebt(), view)

    # ── scan view 공통 헬퍼 ───────────────────────────────

    def _scanView(self, df: pl.DataFrame | None, view: str | None) -> pl.DataFrame | None:
        """scan DataFrame에서 view별 필터."""
        if df is None or df.is_empty():
            return None
        if view == "all":
            return df
        if view == "market":
            return self._scanMarketSummary(df)
        # 기본: 이 회사 행
        code = self.stockCode
        row = df.filter(pl.col("종목코드") == code)
        return row if not row.is_empty() else None

    def _scanMarketSummary(self, df: pl.DataFrame) -> pl.DataFrame:
        """시장별 요약 통계."""
        from dartlab.scan._helpers import load_listing

        _, _, _, listing_meta = load_listing()
        code_to_market = {code: meta.get("market", "") for code, meta in listing_meta.items()}
        df_with_market = df.with_columns(
            pl.col("종목코드")
            .replace_strict(code_to_market, default="미분류")
            .replace("", "미분류")
            .fill_null("미분류")
            .alias("시장")
        )
        numeric_cols = [c for c in df.columns if c != "종목코드" and df[c].dtype in (pl.Float64, pl.Int64)]
        if not numeric_cols:
            return df_with_market.group_by("시장").len()
        aggs = [pl.len().alias("종목수")]
        for c in numeric_cols:
            aggs.append(pl.col(c).mean().alias(f"{c}_평균"))
            aggs.append(pl.col(c).median().alias(f"{c}_중간값"))
        return df_with_market.group_by("시장").agg(aggs).sort("종목수", descending=True)

    def view(self, *, port: int = 8400) -> None:
        """브라우저에서 공시 뷰어를 엽니다.

        Capabilities:
            - 로컬 서버 기반 공시 뷰어 실행
            - 브라우저에서 sections/index 탐색

        Args:
            port: 로컬 서버 포트. 기본 8400.

        Returns:
            None

        Requires:
            데이터: HuggingFace docs parquet (자동 다운로드)

        Example::

            c = Company("005930")
            c.view()

        AIContext:
            - 시각적 탐색 인터페이스 — 사용자가 브라우저에서 직접 데이터 탐색

        Guide:
            - "공시 뷰어 열어줘" → c.view()
            - "브라우저에서 보기" → c.view()

        SeeAlso:
            - index: 뷰어가 소비하는 메타데이터 (프로그래밍 접근)
            - sections: 뷰어의 원본 데��터
        """
        from dartlab.core.viewer import launchViewer

        launchViewer(self.stockCode, port=port)

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

        Capabilities:
            - 엔진 계산 결과를 컨텍스트로 조립하여 LLM에 전달
            - 질문 분류 기반 분석 패키지 자동 선택 (financial, valuation, risk 등)
            - 멀티 provider 지원 (openai, ollama, codex 등)
            - 스트리밍 응답 지원

        AIContext:
            AI가 분석 전 과정을 주도. dartlab 엔진(analysis, scan, gather 등)을
            도구로 호출하여 데이터 수집, 계산, 판단, 해석을 수행.

        Args:
            question: 질문 텍스트.
            include: 포함할 분석 패키지 목록. None이면 자동 선택.
            exclude: 제외할 분석 패키지 목록.
            provider: LLM provider 이름 (openai, ollama, codex 등). None이면 기본값.
            model: 모델명. None이면 provider 기본값.
            stream: True면 스트리밍 제너레이터 반환.
            reflect: True면 답변 후 자기 평가 수행.
            **kwargs: provider별 추가 옵션.

        Returns:
            str -- LLM 응답 텍스트. stream=True면 Generator[str].

        Requires:
            API 키: LLM provider API 키 (OPENAI_API_KEY 등)

        Example::

            c = Company("005930")
            c.ask("영업이익률 추세는?")
            c.ask("핵심 리스크 3가지", provider="codex")

            # 스트리밍
            for chunk in c.ask("배당 분석해줘", stream=True):
                print(chunk, end="")

        Guide:
            - "영업이익률 분석해줘" → c.ask("영업이익률 추세는?")
            - "AI한테 질문하고 싶어" → c.ask("질문")
            - "스트리밍으로 답변받기" → c.ask("질문", stream=True)

        SeeAlso:
            - chat: 에이전트 모드 (tool calling 기반 심화 분석)
            - reviewer: 구조화된 AI 보고서 (자유 질문이 아닌 섹션별)
            - review: AI 없는 데이터 검토서
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
        """에이전트 모드: LLM이 도구를 선택하여 심화 분석.

        Capabilities:
            - Tier 2 LLM 주도 분석 (tool calling)
            - LLM이 부족한 정보를 자율적으로 도구 호출하여 보충
            - 원본 시계열, 공시 텍스트 검색, 복수 기업 비교 등 심화 탐색
            - 멀티 턴 대화 지원

        AIContext:
            Tier 2 에이전트 모드. Tier 1 결과를 본 LLM이 부족하다고 판단하면
            저수준 tool(시계열 조회, 공시 검색 등)을 직접 호출하여 심화 분석.

        Args:
            question: 질문 텍스트.
            provider: LLM provider 이름. None이면 기본값.
            model: 모델명. None이면 provider 기본값.
            max_turns: 최대 tool calling 턴 수. 기본 5.
            on_tool_call: tool 호출 시 콜백.
            on_tool_result: tool 결과 수신 시 콜백.
            **kwargs: provider별 추가 옵션.

        Returns:
            str -- LLM 최종 응답 텍스트.

        Requires:
            API 키: tool calling 지원 LLM provider API 키

        Example::

            c = Company("005930")
            c.chat("배당 추세를 분석하고 이상 징후를 찾아줘")

        Guide:
            - "심층 분석해줘" → c.chat("질문")
            - "AI가 직접 데이터 찾아서 분석" → c.chat("질문")
            - "여러 단계 분석 필요한 질문" → c.chat("복합 질문")

        SeeAlso:
            - ask: 단일 턴 질문 (chat보다 빠르지만 덜 심층)
            - reviewer: 구조화된 AI 보고서
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
