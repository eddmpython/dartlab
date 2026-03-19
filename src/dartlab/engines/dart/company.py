"""DART 엔진 내부 Company 본체.

사용법::

    from dartlab.engines.dart.company import Company

    c = Company("005930")       # 한국 (DART)
    c = Company("삼성전자")      # 한국 (회사명)
    c.BS                        # 재무상태표 DataFrame
    c.ratios                    # 재무비율
    c.insights                  # 인사이트 등급
"""

from __future__ import annotations

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
from dartlab.core.kindList import (
    codeToName,
    getKindList,
    nameToCode,
    searchName,
)

# ── 모듈 레지스트리 (core/registry.py에서 자동 생성) ──
# (모듈 import 경로, 함수명, 한글 라벨, primary DataFrame 추출)
# fsSummary/statements는 내부 디스패치 전용 (BS/IS/CF property가 statements를 호출)
from dartlab.core.registry import getEntry as _getEntry
from dartlab.core.registry import getModuleEntries as _getModuleEntries

# ── 분리된 모듈-레벨 헬퍼 re-export (외부 import 경로 유지) ──
from dartlab.engines.dart._diff_helpers import (  # noqa: F401
    _buildTopicChangeLedger,
    _normalizeTextCell,
)

# ── 분리된 accessor 클래스 re-export (외부 import 경로 유지) ──
from dartlab.engines.dart._docs_accessor import _DocsAccessor  # noqa: F401
from dartlab.engines.dart._finance_accessor import _FinanceAccessor  # noqa: F401
from dartlab.engines.dart._finance_helpers import (  # noqa: F401
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
from dartlab.engines.dart._profile_accessor import _ProfileAccessor  # noqa: F401
from dartlab.engines.dart._report_accessor import REPORT_COL_KR as _REPORT_COL_KR  # noqa: F401
from dartlab.engines.dart._report_accessor import _ReportAccessor  # noqa: F401
from dartlab.engines.dart._sections_source import _SectionsSource  # noqa: F401
from dartlab.engines.dart._utils import (  # noqa: F401
    _ensureData,
    _import_and_call,
    _isPeriodColumn,
    _shapeString,
)
from dartlab.engines.dart.docs.notes import Notes

_MODULE_REGISTRY: list[tuple[str, str, str, Any]] = [
    ("dartlab.engines.dart.docs.finance.summary", "fsSummary", "요약재무정보", None),
    ("dartlab.engines.dart.docs.finance.statements", "statements", "재무제표", None),
] + [(e.modulePath, e.funcName, e.label, e.extractor) for e in _getModuleEntries()]

# 모듈명 → 레지스트리 인덱스
_MODULE_INDEX: dict[str, int] = {entry[1]: i for i, entry in enumerate(_MODULE_REGISTRY)}

# all()에서 사용할 순서 (fsSummary, statements 제외 — BS/IS/CF로 대체)
_ALL_PROPERTIES: list[tuple[str, str]] = [
    ("BS", "재무상태표"),
    ("IS", "손익계산서"),
    ("CF", "현금흐름표"),
]
for entry in _MODULE_REGISTRY:
    name = entry[1]
    if name in ("fsSummary", "statements", "companyOverview"):
        continue
    _ALL_PROPERTIES.append((name, entry[2]))

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


def listExportModules() -> list[tuple[str, str]]:
    """Excel/export용 DART 공개 모듈 목록."""
    return list(_ALL_PROPERTIES)


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

    def __init__(self, codeOrName: str):
        normalized = codeOrName.strip()
        if re.match(r"^[0-9A-Za-z]{6}$", normalized):
            self.stockCode = normalized.upper()
        else:
            code = nameToCode(normalized)
            if code is None:
                raise ValueError(f"'{normalized}'에 해당하는 종목을 찾을 수 없음")
            self.stockCode = code
        self._cache: dict[str, Any] = {}

        self._hasDocs = _ensureData(self.stockCode, "docs")
        self._hasFinanceParquet = _ensureData(self.stockCode, "finance")
        self._hasReport = _ensureData(self.stockCode, "report")

        if self._hasDocs:
            df = loadData(self.stockCode, category="docs")
            self.corpName = extractCorpName(df)
        else:
            self.corpName = codeToName(self.stockCode)

        # finance는 lazy — 첫 접근 시 _ensureFinanceLoaded()에서 검증
        self._financeChecked = False

        if not self._hasDocs and not self._hasFinanceParquet and not self._hasReport:
            raise ValueError(
                f"'{self.stockCode}' 데이터를 찾을 수 없습니다.\n"
                f"\n"
                f"  가능한 원인:\n"
                f"  • 종목코드가 올바른지 확인하세요 (6자리, 예: '005930')\n"
                f"  • 비상장 또는 dartlab 데이터셋에 미포함 종목일 수 있습니다\n"
                f"  • 인터넷 연결을 확인하세요 (첫 사용 시 자동 다운로드 필요)\n"
                f"\n"
                f"  종목 검색: dartlab.search('삼성') 또는 dartlab.listing()"
            )

        self._notesAccessor = Notes(self) if self._hasDocs else None
        self.docs = _DocsAccessor(self)
        self.finance = _FinanceAccessor(self)
        self.report = _ReportAccessor(self)
        self._profileAccessor = _ProfileAccessor(self)

    def __repr__(self):
        return f"Company({self.stockCode}, {self.corpName})"

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
        cacheKey = f"{name}:{kwargs}" if kwargs else name
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        idx = _MODULE_INDEX[name]
        entry = _MODULE_REGISTRY[idx]
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
            "dartlab.engines.dart.docs.finance.notesDetail",
            "notesDetail",
            self.stockCode,
            keyword=keyword,
        )
        self._cache[cacheKey] = result
        return result

    def _get_primary(self, name: str, **kwargs) -> Any:
        """모듈 호출 후 primary DataFrame 추출."""
        from dartlab import config

        cacheKey = f"{name}:{kwargs}" if kwargs else name
        idx = _MODULE_INDEX[name]
        entry = _MODULE_REGISTRY[idx]
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
        """KRX 전체 상장법인 목록 (KIND 기준)."""
        return getKindList(forceRefresh=forceRefresh)

    @staticmethod
    def search(keyword: str) -> pl.DataFrame:
        """회사명 부분 검색 (KIND 목록 기준)."""
        return searchName(keyword)

    @staticmethod
    def resolve(codeOrName: str) -> str | None:
        """종목코드 또는 회사명 → 종목코드 변환."""
        normalized = codeOrName.strip()
        if re.match(r"^[0-9A-Za-z]{6}$", normalized):
            return normalized.upper()
        return nameToCode(normalized)

    @staticmethod
    def codeName(stockCode: str) -> str | None:
        """종목코드 → 회사명 변환."""
        return codeToName(stockCode)

    @staticmethod
    def status() -> pl.DataFrame:
        """로컬에 보유한 전체 종목 인덱스."""
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

    def filings(self) -> pl.DataFrame:
        """공시 문서 목록 + DART 뷰어 링크."""
        return self._filings()

    # ── 원본 데이터 (property) ──

    @property
    def rawDocs(self) -> pl.DataFrame | None:
        """공시 문서 원본 parquet 전체 (가공 전)."""
        if not self._hasDocs:
            return None
        cacheKey = "_rawDocs"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        df = loadData(self.stockCode, category="docs")
        self._cache[cacheKey] = df
        return df

    @property
    def rawFinance(self) -> pl.DataFrame | None:
        """재무제표 원본 parquet 전체 (가공 전)."""
        if not self._hasFinanceParquet:
            return None
        cacheKey = "_rawFinance"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        df = loadData(self.stockCode, category="finance")
        self._cache[cacheKey] = df
        return df

    @property
    def rawReport(self) -> pl.DataFrame | None:
        """정기보고서 원본 parquet 전체 (가공 전)."""
        if not self._hasReport:
            return None
        cacheKey = "_rawReport"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        df = loadData(self.stockCode, category="report")
        self._cache[cacheKey] = df
        return df

    @property
    def notes(self):
        """K-IFRS notes accessor (compat)."""
        return self._notesAccessor

    def _docsSectionsCadence(self, cadenceScope: str, *, includeMixed: bool = True) -> pl.DataFrame | None:
        if not self._hasDocs:
            return None
        normalizedScope = str(cadenceScope).strip().lower()
        cacheKey = f"_docsSectionsCadence:{normalizedScope}:{int(includeMixed)}"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        sectionsFrame = self.docs.sections
        if sectionsFrame is None:
            self._cache[cacheKey] = None
            return None
        from dartlab.engines.dart.docs.sections import projectCadenceRows

        result = projectCadenceRows(sectionsFrame, cadenceScope=normalizedScope, includeMixed=includeMixed)
        self._cache[cacheKey] = result
        return result

    def _docsSectionsOrdered(
        self,
        *,
        recentFirst: bool = True,
        annualAsQ4: bool = True,
    ) -> pl.DataFrame | None:
        if not self._hasDocs:
            return None
        cacheKey = f"_docsSectionsOrdered:{int(recentFirst)}:{int(annualAsQ4)}"
        if cacheKey in self._cache:
            return self._cache[cacheKey]

        sectionsFrame = self.docs.sections
        if sectionsFrame is None:
            self._cache[cacheKey] = None
            return None

        from dartlab.engines.dart.docs.sections import reorderPeriodColumns

        result = reorderPeriodColumns(sectionsFrame.raw, descending=recentFirst, annualAsQ4=annualAsQ4)
        self._cache[cacheKey] = result
        return result

    def _docsSectionsCoverage(
        self,
        *,
        topic: str | None = None,
        recentFirst: bool = True,
        annualAsQ4: bool = True,
    ) -> pl.DataFrame | None:
        if not self._hasDocs:
            return None
        topicKey = topic or "*"
        cacheKey = f"_docsSectionsCoverage:{topicKey}:{int(recentFirst)}:{int(annualAsQ4)}"
        if cacheKey in self._cache:
            return self._cache[cacheKey]

        sectionsFrame = self.docs.sections
        if sectionsFrame is None:
            self._cache[cacheKey] = None
            return None

        from dartlab.engines.dart.docs.sections import displayPeriod, sortPeriods

        rawFrame = sectionsFrame.raw
        scoped = rawFrame if topic is None else rawFrame.filter(pl.col("topic") == topic)
        if scoped.is_empty():
            result = pl.DataFrame(
                schema={
                    "topic": pl.Utf8,
                    "period": pl.Utf8,
                    "rawPeriod": pl.Utf8,
                    "rowCount": pl.Int64,
                    "nonNullRows": pl.Int64,
                    "nullRows": pl.Int64,
                    "coverageRatio": pl.Float64,
                }
            )
            self._cache[cacheKey] = result
            return result

        periodCols = sortPeriods([c for c in scoped.columns if _isPeriodColumn(c)], descending=recentFirst)
        topics = scoped.get_column("topic").drop_nulls().unique(maintain_order=True).to_list()
        records: list[dict[str, Any]] = []
        for topicName in topics:
            topicRows = scoped.filter(pl.col("topic") == topicName)
            rowCount = topicRows.height
            if rowCount == 0:
                continue
            for periodCol in periodCols:
                nonNullRows = topicRows.get_column(periodCol).drop_nulls().len()
                records.append(
                    {
                        "topic": str(topicName),
                        "period": displayPeriod(periodCol, annualAsQ4=annualAsQ4),
                        "rawPeriod": periodCol,
                        "rowCount": rowCount,
                        "nonNullRows": nonNullRows,
                        "nullRows": rowCount - nonNullRows,
                        "coverageRatio": (float(nonNullRows) / float(rowCount)) if rowCount else 0.0,
                    }
                )

        result = pl.DataFrame(records, strict=False) if records else pl.DataFrame()
        self._cache[cacheKey] = result
        return result

    def _docsSectionsSemanticRegistry(
        self,
        *,
        topic: str | None = None,
        cadenceScope: str = "all",
        includeMixed: bool = True,
        collisionsOnly: bool = False,
    ) -> pl.DataFrame | None:
        if not self._hasDocs:
            return None
        normalizedScope = str(cadenceScope).strip().lower()
        topicKey = topic or "*"
        cacheKey = (
            f"_docsSectionsSemanticRegistry:{topicKey}:{normalizedScope}:{int(includeMixed)}:{int(collisionsOnly)}"
        )
        if cacheKey in self._cache:
            return self._cache[cacheKey]

        sectionsFrame = self.docs.sections
        if sectionsFrame is None:
            self._cache[cacheKey] = None
            return None

        from dartlab.engines.dart.docs.sections import semanticCollisions, semanticRegistry

        if collisionsOnly:
            result = semanticCollisions(
                sectionsFrame,
                topic=topic,
                cadenceScope=normalizedScope,
                includeMixed=includeMixed,
            )
        else:
            result = semanticRegistry(
                sectionsFrame,
                topic=topic,
                cadenceScope=normalizedScope,
                includeMixed=includeMixed,
            )
        self._cache[cacheKey] = result
        return result

    def _docsSectionsStructureRegistry(
        self,
        *,
        topic: str | None = None,
        cadenceScope: str = "all",
        includeMixed: bool = True,
        collisionsOnly: bool = False,
        nodeType: str | None = None,
    ) -> pl.DataFrame | None:
        if not self._hasDocs:
            return None
        normalizedScope = str(cadenceScope).strip().lower()
        normalizedNodeType = str(nodeType).strip().lower() if isinstance(nodeType, str) and nodeType.strip() else "*"
        topicKey = topic or "*"
        cacheKey = f"_docsSectionsStructureRegistry:{topicKey}:{normalizedScope}:{int(includeMixed)}:{int(collisionsOnly)}:{normalizedNodeType}"
        if cacheKey in self._cache:
            return self._cache[cacheKey]

        sectionsFrame = self.docs.sections
        if sectionsFrame is None:
            self._cache[cacheKey] = None
            return None

        from dartlab.engines.dart.docs.sections import structureCollisions, structureRegistry

        if collisionsOnly:
            result = structureCollisions(
                sectionsFrame,
                topic=topic,
                cadenceScope=normalizedScope,
                includeMixed=includeMixed,
                nodeType=nodeType,
            )
        else:
            result = structureRegistry(
                sectionsFrame,
                topic=topic,
                cadenceScope=normalizedScope,
                includeMixed=includeMixed,
                nodeType=nodeType,
            )
        self._cache[cacheKey] = result
        return result

    def _docsSectionsStructureEvents(
        self,
        *,
        topic: str | None = None,
        cadenceScope: str = "all",
        includeMixed: bool = True,
        changedOnly: bool = True,
        nodeType: str | None = None,
    ) -> pl.DataFrame | None:
        if not self._hasDocs:
            return None
        normalizedScope = str(cadenceScope).strip().lower()
        normalizedNodeType = str(nodeType).strip().lower() if isinstance(nodeType, str) and nodeType.strip() else "*"
        topicKey = topic or "*"
        cacheKey = f"_docsSectionsStructureEvents:{topicKey}:{normalizedScope}:{int(includeMixed)}:{int(changedOnly)}:{normalizedNodeType}"
        if cacheKey in self._cache:
            return self._cache[cacheKey]

        sectionsFrame = self.docs.sections
        if sectionsFrame is None:
            self._cache[cacheKey] = None
            return None

        from dartlab.engines.dart.docs.sections import structureEvents

        result = structureEvents(
            sectionsFrame,
            topic=topic,
            cadenceScope=normalizedScope,
            includeMixed=includeMixed,
            changedOnly=changedOnly,
            nodeType=nodeType,
        )
        self._cache[cacheKey] = result
        return result

    def _docsSectionsStructureSummary(
        self,
        *,
        topic: str | None = None,
        cadenceScope: str = "all",
        includeMixed: bool = True,
        nodeType: str | None = None,
    ) -> pl.DataFrame | None:
        if not self._hasDocs:
            return None
        normalizedScope = str(cadenceScope).strip().lower()
        normalizedNodeType = str(nodeType).strip().lower() if isinstance(nodeType, str) and nodeType.strip() else "*"
        topicKey = topic or "*"
        cacheKey = (
            f"_docsSectionsStructureSummary:{topicKey}:{normalizedScope}:{int(includeMixed)}:{normalizedNodeType}"
        )
        if cacheKey in self._cache:
            return self._cache[cacheKey]

        sectionsFrame = self.docs.sections
        if sectionsFrame is None:
            self._cache[cacheKey] = None
            return None

        from dartlab.engines.dart.docs.sections import structureSummary

        result = structureSummary(
            sectionsFrame,
            topic=topic,
            cadenceScope=normalizedScope,
            includeMixed=includeMixed,
            nodeType=nodeType,
        )
        self._cache[cacheKey] = result
        return result

    def _docsSectionsStructureChanges(
        self,
        *,
        topic: str | None = None,
        cadenceScope: str = "all",
        includeMixed: bool = True,
        nodeType: str | None = None,
        latestOnly: bool = True,
        changedOnly: bool = True,
    ) -> pl.DataFrame | None:
        if not self._hasDocs:
            return None
        normalizedScope = str(cadenceScope).strip().lower()
        normalizedNodeType = str(nodeType).strip().lower() if isinstance(nodeType, str) and nodeType.strip() else "*"
        topicKey = topic or "*"
        cacheKey = (
            f"_docsSectionsStructureChanges:{topicKey}:{normalizedScope}:{int(includeMixed)}:{normalizedNodeType}:"
            f"{int(latestOnly)}:{int(changedOnly)}"
        )
        if cacheKey in self._cache:
            return self._cache[cacheKey]

        sectionsFrame = self.docs.sections
        if sectionsFrame is None:
            self._cache[cacheKey] = None
            return None

        from dartlab.engines.dart.docs.sections import structureChanges

        result = structureChanges(
            sectionsFrame,
            topic=topic,
            cadenceScope=normalizedScope,
            includeMixed=includeMixed,
            nodeType=nodeType,
            latestOnly=latestOnly,
            changedOnly=changedOnly,
        )
        self._cache[cacheKey] = result
        return result

    def _retrievalBlocks(self) -> pl.DataFrame | None:
        if not self._hasDocs:
            return None
        cacheKey = "retrievalBlocks"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        from dartlab.engines.dart.docs.sections import retrievalBlocks

        result = retrievalBlocks(self.stockCode)
        self._cache[cacheKey] = result
        return result

    def _contextSlices(self) -> pl.DataFrame | None:
        if not self._hasDocs:
            return None
        cacheKey = "contextSlices"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        from dartlab.engines.dart.docs.sections import contextSlices

        result = contextSlices(self.stockCode)
        self._cache[cacheKey] = result
        return result

    def _topicSubtables(self, topic: str):
        cacheKey = f"_topicSubtables:{topic}"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        blocks = self._retrievalBlocks()
        if blocks is None or blocks.is_empty():
            self._cache[cacheKey] = None
            return None
        from dartlab.engines.dart.docs.sections import topicSubtables

        result = topicSubtables(blocks, topic)
        self._cache[cacheKey] = result
        return result

    def _sectionsSubtopicWide(self, topic: str) -> pl.DataFrame | None:
        result = self._topicSubtables(topic)
        return None if result is None else result.wide

    def _sectionsSubtopicLong(self, topic: str) -> pl.DataFrame | None:
        result = self._topicSubtables(topic)
        return None if result is None else result.long

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
        from dartlab.engines.dart.finance.pivot import buildSceMatrix

        result = buildSceMatrix(self.stockCode)
        self._cache[cacheKey] = result
        return result

    def _sceSeriesAnnual(self):
        if not self._hasFinance:
            return None
        cacheKey = "_sceAnnual_CFS"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        from dartlab.engines.dart.finance.pivot import buildSceAnnual

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
        from dartlab.engines.common.finance.ratios import calcRatioSeries, toSeriesDict

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
        """재무상태표 DataFrame (finance XBRL 우선, docs fallback)."""
        return self.finance.BS

    @property
    def IS(self) -> pl.DataFrame | None:
        """손익계산서 DataFrame (finance XBRL 우선, docs fallback)."""
        return self.finance.IS

    @property
    def CIS(self) -> pl.DataFrame | None:
        """포괄손익계산서 DataFrame (finance raw CIS 우선, docs fallback)."""
        return self.finance.CIS

    @property
    def CF(self) -> pl.DataFrame | None:
        """현금흐름표 DataFrame (finance XBRL 우선, docs fallback)."""
        return self.finance.CF

    @property
    def sections(self) -> pl.DataFrame | None:
        """sections — docs + finance + report 통합 지도.

        docs 수평화 위에 finance/report를 같은 topic 안에 끼워넣는다.
        - docs에 있는 topic (dividend 등) → docs 블록 뒤에 report 행 append
        - docs에 없는 topic (BS, auditContract 등) → 해당 chapter에 독립 삽입
        """
        cacheKey = "_sections"
        if cacheKey in self._cache:
            return self._cache[cacheKey]

        sectionsSource = self.docs.sections
        if sectionsSource is None:
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
                    if topic in _REPORT_TOPIC_TO_API_TYPE.values():
                        for k, v in _REPORT_TOPIC_TO_API_TYPE.items():
                            if v == topic:
                                topic = k
                                break
                    chapter = chapterMap.get(topic, "X")
                    topicExtras.setdefault(topic, []).append(
                        _baseExtraRow(chapter=chapter, topic=topic, source="report")
                    )
            except (ValueError, KeyError, AttributeError):
                pass

        if not topicExtras:
            self._cache[cacheKey] = docsSec
            return docsSec

        # topic 순서대로 순회하면서 extra 행을 끼워넣기
        docsTopics = []
        seenTopics: set[str] = set()
        for row in docsSec.iter_rows(named=True):
            t = row["topic"]
            if t not in seenTopics:
                docsTopics.append(t)
                seenTopics.add(t)

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
            from dartlab.engines.dart.docs.sections import reorderPeriodColumns

            result = reorderPeriodColumns(docsSec, descending=True, annualAsQ4=True)
            self._cache[cacheKey] = result
            return result

        merged = pl.concat(result_frames, how="diagonal_relaxed")

        from dartlab.engines.dart.docs.sections import reorderPeriodColumns

        merged = reorderPeriodColumns(merged, descending=True, annualAsQ4=True)
        self._cache[cacheKey] = merged
        return merged

    def _profileTable(self) -> pl.DataFrame | None:
        cacheKey = "_sectionProfileTable"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        from dartlab.engines.dart.docs.sections.artifacts import loadSectionProfileTable

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
            from dartlab.engines.dart.docs.notes import _REGISTRY as _NOTES_REGISTRY

            if topic in _NOTES_REGISTRY:
                return "XI"
        return "XII"

    def _boardTopics(self) -> list[str]:
        cacheKey = "_boardTopics"
        if cacheKey in self._cache:
            return self._cache[cacheKey]

        ordered: list[str] = []
        seen: set[str] = set()

        sections = self.docs.sections
        if sections is not None and "topic" in sections.columns:
            for topic in sections["topic"].to_list():
                if not isinstance(topic, str) or not topic or topic in seen:
                    continue
                ordered.append(topic)
                seen.add(topic)

        # finance topics 추가 (sections는 docs 산출물, finance는 별도)
        if self._hasFinance:
            for ft in ("BS", "IS", "CIS", "CF", "SCE"):
                if ft not in seen:
                    ordered.append(ft)
                    seen.add(ft)
            if self._ratioSeries() is not None and "ratios" not in seen:
                ordered.append("ratios")
                seen.add("ratios")

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
        for name, label in _ALL_PROPERTIES:
            if name == topic:
                return label
        return topic

    def _buildBlockIndex(self, topicRows: pl.DataFrame) -> pl.DataFrame:
        """topic의 블록 목차 DataFrame."""
        from dartlab.engines.common.show import buildBlockIndex

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

    def _showReportTopic(self, topic: str, *, period: str | None = None, raw: bool = False) -> pl.DataFrame | None:
        """report source topic의 실제 데이터 반환."""
        return self._applyPeriodFilter(self._reportFrame(topic, raw=raw), period)

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
        from dartlab.engines.dart._table_horizontalizer import stripUnitHeader

        return stripUnitHeader(sub)

    def _horizontalizeTableBlock(
        self,
        topicFrame: pl.DataFrame,
        blockOrder: int,
        periodCols: list[str],
        period: str | None = None,
    ) -> pl.DataFrame | None:
        """table 블록을 기간 간 수평화 — 항목×기간 매트릭스."""
        from dartlab.engines.dart._table_horizontalizer import horizontalizeTableBlock

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
        from dartlab.engines.dart._report_accessor import reportFrameInner

        return reportFrameInner(self.stockCode, apiType, topic, raw=raw)

    def _applyPeriodFilter(self, payload: Any, period: str | None) -> Any:
        if period is None or not isinstance(payload, pl.DataFrame) or payload.is_empty():
            return payload
        from dartlab.engines.dart.docs.sections import rawPeriod

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

        block=None → 블록 목차 DataFrame (block, type, source, preview)
        block=N → 해당 blockOrder의 실제 데이터 DataFrame

        Args:
            topic: topic 이름 (BS, IS, dividend, companyOverview 등)
            block: blockOrder 인덱스. None이면 블록 목차.
            period: 특정 기간 필터. 리스트면 세로 뷰 (기간 × 항목).
            raw: True면 원본 그대로
        """
        # period가 리스트면 세로 뷰: 먼저 전체 데이터 → transpose
        if isinstance(period, list):
            wide = self.show(topic, block, raw=raw)
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
        from dartlab.engines.common.show import transposeToVertical

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
            merged = df.group_by("계정명", maintain_order=True).agg(
                [pl.col(c).drop_nulls().first().alias(c) for c in periodCols]
            )
            df = merged
        return df

    def trace(self, topic: str, period: str | None = None) -> dict[str, Any] | None:
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
        return self._profileAccessor.trace(topic, period=period)

    def diff(
        self,
        topic: str | None = None,
        fromPeriod: str | None = None,
        toPeriod: str | None = None,
    ) -> pl.DataFrame | None:
        """기간간 텍스트 변경 비교.

        사용법::

            c.diff()                          # 전체 topic 변경 요약
            c.diff("businessOverview")        # 특정 topic 변경 이력
            c.diff("businessOverview", "2024", "2025")  # 줄 단위 diff
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

    def table(
        self,
        topic: str,
        subtopic: str | None = None,
        *,
        numeric: bool = False,
        period: str | None = None,
    ) -> Any:
        """subtopic wide 셀의 markdown table을 구조화 DataFrame으로 파싱.

        Args:
            topic: docs topic 이름
            subtopic: 파싱할 subtopic 이름 (None이면 첫 번째 subtopic)
            numeric: True이면 금액 문자열을 float로 변환
            period: 기간 필터 (예: "2024")

        Returns:
            ParsedSubtopicTable 또는 파싱 불가 시 None

        Example::

            c.table("employee")                    # 첫 번째 subtopic
            c.table("employee", "직원현황")         # 특정 subtopic
            c.table("employee", numeric=True)       # 숫자 변환
        """
        result = self._topicSubtables(topic)
        if result is None:
            return None
        from dartlab.engines.dart.docs.sections import parseSubtopicTable

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
        """topic별 요약 DataFrame (topic, source, blocks, periods)."""
        cacheKey = "_topicsDataFrame"
        if cacheKey in self._cache:
            return self._cache[cacheKey]

        sec = self.sections
        topicOrder = self._boardTopics()

        rows: list[dict] = []
        if sec is not None and "topic" in sec.columns:
            for topic in topicOrder:
                topicRows = sec.filter(pl.col("topic") == topic)
                if topicRows.is_empty():
                    continue

                # source 종류
                sources = sorted(topicRows["source"].unique().to_list()) if "source" in topicRows.columns else ["docs"]

                # block 수
                blocks = topicRows["blockOrder"].n_unique() if "blockOrder" in topicRows.columns else topicRows.height

                # period 수
                periodCols = [c for c in topicRows.columns if _isPeriodColumn(c)]
                periods = len(periodCols)

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
    def sources(self) -> pl.DataFrame:
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
        """현재 공개 Company 구조 인덱스 DataFrame.

        sections 메타데이터 + finance/report 존재 확인만으로 구성.
        개별 파서를 호출하지 않아 빠르다 (lazy).
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
            from dartlab.engines.common.finance.ratios import RATIO_CATEGORIES

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
        rows: list[dict[str, Any]] = []
        sec = self.docs.sections
        if sec is None or "topic" not in sec.columns:
            return rows

        from dartlab.engines.dart.docs.sections import displayPeriod, formatPeriodRange, sortPeriods

        periodCols = sortPeriods([c for c in sec.columns if _isPeriodColumn(c)], descending=True)
        periodRange = formatPeriodRange(periodCols, descending=True, annualAsQ4=True)
        existingPeriods = [c for c in periodCols if c in sec.columns]

        # topic 순서: Polars unique (iter_rows 제거)
        topicOrder = sec.get_column("topic").drop_nulls().unique(maintain_order=True).to_list()

        # nonNull 계산: group_by + agg (벡터화)
        nonNullMap: dict[str, int] = {}
        if existingPeriods:
            nonNullExprs = [pl.col(c).is_not_null().any().cast(pl.Int8).alias(c) for c in existingPeriods]
            nonNullDf = sec.group_by("topic", maintain_order=True).agg(nonNullExprs)
            for row in nonNullDf.iter_rows(named=True):
                nonNullMap[row["topic"]] = sum(1 for c in existingPeriods if row.get(c, 0))

        # preview: group_by first non-null (벡터화)
        previewMap: dict[str, str] = {}
        if existingPeriods:
            firstExprs = [pl.col(c).drop_nulls().first().alias(c) for c in existingPeriods]
            previewDf = sec.group_by("topic", maintain_order=True).agg(firstExprs)
            for row in previewDf.iter_rows(named=True):
                for col in existingPeriods:
                    val = row.get(col)
                    if val is not None:
                        text = str(val).replace("\n", " ").strip()[:80]
                        previewMap[row["topic"]] = f"{displayPeriod(col, annualAsQ4=True)}: {text}"
                        break

        # chapter: group_by first
        chapterMap: dict[str, str | None] = {}
        if "chapter" in sec.columns:
            chapterDf = sec.group_by("topic", maintain_order=True).agg(pl.col("chapter").first().alias("chapter"))
            for row in chapterDf.iter_rows(named=True):
                chapterMap[row["topic"]] = row["chapter"]

        for rowIdx, topic in enumerate(topicOrder):
            nonNull = nonNullMap.get(topic, 0)
            preview = previewMap.get(topic, "-")
            chapterVal = chapterMap.get(topic)
            chapter = chapterVal if isinstance(chapterVal, str) and chapterVal else self._chapterForTopic(topic)
            chapterNum = _CHAPTER_ORDER.get(chapter, 12)
            rows.append(
                {
                    "chapter": _CHAPTER_TITLES.get(chapter, chapter),
                    "topic": topic,
                    "label": self._topicLabel(topic),
                    "kind": "docs",
                    "source": "docs",
                    "periods": periodRange,
                    "shape": f"{nonNull}기간",
                    "preview": preview,
                    "_sortKey": (chapterNum, 100 + rowIdx),
                }
            )
        return rows

    def _indexReportRows(self, *, existingTopics: set[str] | None = None) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        if not self._hasReport:
            return rows

        from dartlab.engines.dart.report.types import API_TYPE_LABELS, API_TYPES

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
        """docs spine + finance/report merge layer."""
        return self._profileAccessor

    @property
    def retrievalBlocks(self) -> pl.DataFrame | None:
        """원문 markdown 보존 retrieval block DataFrame."""
        return self.docs.retrievalBlocks

    @property
    def contextSlices(self) -> pl.DataFrame | None:
        """LLM 투입용 context slice DataFrame."""
        return self.docs.contextSlices

    # ── financeEngine (숫자 재무 데이터) ──

    def _ensureFinanceLoaded(self) -> None:
        """lazy finance: 첫 접근 시 buildTimeseries 실행."""
        if self._financeChecked:
            return
        self._financeChecked = True
        if not self._hasFinanceParquet:
            return
        from dartlab.engines.dart.finance.pivot import buildTimeseries

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

        from dartlab.engines.dart.finance.pivot import buildAnnual, buildCumulative, buildTimeseries

        builders = {"q": buildTimeseries, "y": buildAnnual, "cum": buildCumulative}
        builder = builders.get(period, buildTimeseries)
        result = builder(self.stockCode, fsDivPref=fsDivPref)
        self._cache[cacheKey] = result
        return result

    def getTimeseries(self, period: str = "q", fsDivPref: str = "CFS"):
        """재무 시계열 조회.

        Args:
            period: "q" (분기별 standalone), "y" (연도별), "cum" (분기별 누적).
            fsDivPref: "CFS" (연결) 또는 "OFS" (별도).

        Returns:
            (series, periods) 또는 None.
            series = {"BS": {"snakeId": [값...]}, "IS": {...}, "CF": {...}}
            periods = ["2016-Q1", ...] (q/cum) 또는 ["2016", ...] (y)

        Example::

            c = Company("005930")
            series, periods = c.getTimeseries("y")
            series, periods = c.getTimeseries("q", fsDivPref="OFS")
        """
        return self._getFinanceBuild(period, fsDivPref)

    def getRatios(self, fsDivPref: str = "CFS"):
        """재무비율 계산.

        Args:
            fsDivPref: "CFS" (연결) 또는 "OFS" (별도).

        Returns:
            RatioResult dataclass.

        Example::

            c = Company("005930")
            c.getRatios().roe
            c.getRatios("OFS").debtRatio
        """
        cacheKey = f"_ratios_{fsDivPref}"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        from dartlab.engines.common.finance.ratios import calcRatios

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
        """재무비율 시계열 (분류/항목 × 기간 DataFrame).

        Example::

            c = Company("005930")
            c.ratios  # 분류 | 항목 | 2025Q3 | 2025Q2 | ...
        """
        rs = self._ratioSeries()
        if rs is None:
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

        Returns:
            (series, periods) 또는 None.
            series = {"BS": {"snakeId": [값...]}, "IS": {...}, "CF": {...}}
            periods = ["2016-Q1", "2016-Q2", ..., "2024-Q4"]

        Example::

            c = Company("005930")
            series, periods = c.timeseries
            series["IS"]["sales"]  # 분기별 매출 시계열
        """
        return self.finance.timeseries

    @property
    def annual(self):
        """연도별 시계열 (연결 기준).

        Returns:
            (series, years) 또는 None.

        Example::

            c = Company("005930")
            series, years = c.annual
            series["IS"]["sales"]  # 연도별 매출 시계열
        """
        return self.finance.annual

    @property
    def cumulative(self):
        """분기별 누적 시계열 (연결 기준).

        Returns:
            (series, periods) 또는 None.

        Example::

            c = Company("005930")
            series, periods = c.cumulative
        """
        return self.finance.cumulative

    @property
    def sceMatrix(self):
        """자본변동표 연도별 매트릭스 (연결 기준).

        Returns:
            (matrix, years) 또는 None.
            matrix[year][cause][detail] = 금액
            years = ["2016", ..., "2024"]

        Example::

            c = Company("005930")
            matrix, years = c.sceMatrix
            matrix["2024"]["net_income"]["retained_earnings"]
        """
        return self.finance.sceMatrix

    @property
    def sce(self):
        """자본변동표 DataFrame (연결 기준).

        Returns:
            계정명 × 연도 컬럼 DataFrame 또는 None.

        Example::

            c = Company("005930")
            c.sce
        """
        return self.finance.sce

    @property
    def SCE(self):
        """자본변동표 DataFrame (대문자 alias)."""
        return self.finance.SCE

    @property
    def ratioSeries(self):
        """재무비율 연도별 시계열 (IS/BS/CF와 동일한 dict 구조).

        Returns:
            ({"RATIO": {snakeId: [v1, v2, ...]}}, years) 또는 None.

        Example::

            c = Company("005930")
            series, years = c.ratioSeries
            series["RATIO"]["roe"]  # [8.69, 13.20, 16.55, ...]
        """
        return self.finance.ratioSeries

    # ── 섹터 분류 ──

    @property
    def sector(self):
        """WICS 투자 섹터 분류 (KIND 업종 + 키워드 기반).

        Returns:
            SectorInfo (sector, industryGroup, confidence, source).

        Example::

            c = Company("005930")
            c.sector              # SectorInfo(IT/반도체와반도체장비, conf=1.00, src=override)
            c.sector.sector       # Sector.IT
            c.sector.industryGroup  # IndustryGroup.SEMICONDUCTOR
        """
        cacheKey = "_sector"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        from dartlab.engines.sector import classify

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

        Returns:
            SectorParams (discountRate, growthRate, perMultiple, ...).

        Example::

            c = Company("005930")
            c.sectorParams.perMultiple   # 15
            c.sectorParams.discountRate  # 13.0
        """
        cacheKey = "_sectorParams"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        from dartlab.engines.sector import getParams

        result = getParams(self.sector)
        self._cache[cacheKey] = result
        return result

    # ── 규모 랭크 ──

    @property
    def rank(self):
        """전체 시장 + 섹터 내 규모 순위 (매출/자산/성장률).

        스냅샷이 없으면 None 반환. buildSnapshot()으로 사전 빌드 필요.

        Returns:
            RankInfo 또는 스냅샷 미빌드 시 None.

        Example::

            from dartlab.engines.insight import buildSnapshot
            buildSnapshot()

            c = Company("005930")
            c.rank                    # RankInfo(삼성전자, 매출 2/2192, 섹터 2/467, large)
            c.rank.revenueRank        # 2
            c.rank.revenueRankInSector # 2
            c.rank.sizeClass          # "large"
        """
        cacheKey = "_rank"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        from dartlab.engines.rank.rank import getRank

        result = getRank(self.stockCode)
        self._cache[cacheKey] = result
        return result

    # ── 인사이트 분석 ──

    @property
    def insights(self):
        """종합 인사이트 분석 (7영역 등급 + 이상치 + 요약).

        Returns:
            AnalysisResult 또는 finance 데이터 없으면 None.

        Example::

            c = Company("005930")
            c.insights.grades()       # {'performance': 'A', ...}
            c.insights.summary        # "삼성전자는 실적, 재무건전성 등..."
            c.insights.anomalies      # [Anomaly(...), ...]
            c.insights.profile        # "premium"
        """
        if not self._hasFinance:
            return None
        cacheKey = "_insights"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        from dartlab.engines.insight import analyze

        result = analyze(self.stockCode, company=self)
        self._cache[cacheKey] = result
        return result

    @property
    def market(self) -> str:
        """시장 코드."""
        return "KR"

    @property
    def currency(self) -> str:
        """통화 코드."""
        return "KRW"

    # ── network (관계 지도) ──────────────────────────────────

    def _ensureNetwork(self) -> tuple[dict, dict] | None:
        """network 파이프라인 캐싱 → (data, full)."""
        if "_network_data" not in self._cache:
            from dartlab.engines.dart.scan.network import build_graph, export_full

            data = build_graph(verbose=False)
            self._cache["_network_data"] = data
            self._cache["_network_full"] = export_full(data)
        return self._cache["_network_data"], self._cache["_network_full"]

    def network(self, view: str | None = None, *, hops: int = 1):
        """관계 네트워크.

        Args:
            view: None이면 시각화(NetworkView), "members"/"edges"/"cycles"/"peers"이면 DataFrame
            hops: peers/시각화 뷰에서 홉 수

        Example::

            c = Company("005930")
            c.network()              # → NetworkView (.show()로 브라우저)
            c.network().show()       # 브라우저 오픈
            c.network("members")     # 같은 그룹 계열사 DataFrame
            c.network("edges")       # 출자/지분 연결 DataFrame
            c.network("cycles")      # 순환출자 경로 DataFrame
            c.network("peers")       # 이 회사 중심 서브그래프 DataFrame
        """
        result = self._ensureNetwork()
        if result is None:
            return None
        data, full = result
        code = self.stockCode
        group = data["code_to_group"].get(code, self.corpName or code)

        if view is None:
            from dartlab.engines.dart.scan.network import export_ego
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
        from dartlab.engines.dart.scan.network import export_ego

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
            from dartlab.engines.dart.scan.governance import scan_governance

            self._cache["_governance"] = scan_governance(verbose=False)
        return self._cache["_governance"]

    def governance(self, view: str | None = None) -> pl.DataFrame | None:
        """지배구조 분석.

        Args:
            view: None → 이 회사 행, "all" → 전체, "market" → 시장별 요약

        Example::

            c = Company("005930")
            c.governance()           # 삼성전자 거버넌스
            c.governance("all")      # 전체 상장사
        """
        return self._scanView(self._ensureGovernance(), view)

    # ── workforce (인력) ───────────────────────────────────

    def _ensureWorkforce(self) -> pl.DataFrame | None:
        if "_workforce" not in self._cache:
            from dartlab.engines.dart.scan.workforce import scan_workforce

            self._cache["_workforce"] = scan_workforce(verbose=False)
        return self._cache["_workforce"]

    def workforce(self, view: str | None = None) -> pl.DataFrame | None:
        """인력/급여 분석.

        Args:
            view: None → 이 회사 행, "all" → 전체, "market" → 시장별 요약

        Example::

            c = Company("005930")
            c.workforce()            # 삼성전자 인력 현황
            c.workforce("all")       # 전체 상장사
        """
        return self._scanView(self._ensureWorkforce(), view)

    # ── capital (주주환원) ─────────────────────────────────

    def _ensureCapital(self) -> pl.DataFrame | None:
        if "_capital" not in self._cache:
            from dartlab.engines.dart.scan.capital import scan_capital

            self._cache["_capital"] = scan_capital(verbose=False)
        return self._cache["_capital"]

    def capital(self, view: str | None = None) -> pl.DataFrame | None:
        """주주환원 분석.

        Args:
            view: None → 이 회사 행, "all" → 전체, "market" → 시장별 요약

        Example::

            c = Company("005930")
            c.capital()              # 삼성전자 주주환원
            c.capital("all")         # 전체 상장사
        """
        return self._scanView(self._ensureCapital(), view)

    # ── debt (부채 구조) ──────────────────────────────────

    def _ensureDebt(self) -> pl.DataFrame | None:
        if "_debt" not in self._cache:
            from dartlab.engines.dart.scan.debt import scan_debt

            self._cache["_debt"] = scan_debt(verbose=False)
        return self._cache["_debt"]

    def debt(self, view: str | None = None) -> pl.DataFrame | None:
        """부채 구조 분석.

        Args:
            view: None → 이 회사 행, "all" → 전체, "market" → 시장별 요약

        Example::

            c = Company("005930")
            c.debt()                 # 삼성전자 부채 구조
            c.debt("all")            # 전체 상장사
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
        from dartlab.engines.dart.scan._helpers import load_listing

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

        Example::

            c = Company("005930")
            c.view()
        """
        from dartlab.engines.common.viewer import launchViewer

        launchViewer(self.stockCode, port=port)
