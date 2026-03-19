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
from collections import OrderedDict
from pathlib import Path
from typing import Any

import polars as pl

pl.Config.set_fmt_str_lengths(80)
pl.Config.set_tbl_width_chars(200)

from dartlab.core.dataLoader import (
    DART_VIEWER,
    _dataDir,
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
    _buildTopicEvidence,
    _canonicalBlockRecord,
    _matchTopicBlocks,
    _normalizeTextCell,
    _stableFingerprint,
    _summarizeTopicChange,
    _tableMetrics,
    _textSimilarity,
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

_CHAPTER_TITLES: OrderedDict[str, str] = OrderedDict(
    [
        ("I", "I. 회사의 개요"),
        ("II", "II. 사업의 내용"),
        ("III", "III. 재무에 관한 사항"),
        ("IV", "IV. 이사의 경영진단 및 분석의견"),
        ("V", "V. 감사인의 감사의견등"),
        ("VI", "VI. 이사회등회사의기관및계열회사에관한사항"),
        ("VII", "VII. 주주에 관한 사항"),
        ("VIII", "VIII. 임원 및 직원 등에 관한 사항"),
        ("IX", "IX. 이해관계자와의 거래내용"),
        ("X", "X. 그 밖에 투자자 보호를 위하여 필요한 사항"),
        ("XI", "XI. 재무제표등"),
        ("XII", "XII. 상세표 및 부속명세서"),
    ]
)

_CHAPTER_ORDER: dict[str, int] = {chapter: idx for idx, chapter in enumerate(_CHAPTER_TITLES, start=1)}
_REPORT_TOPIC_TO_API_TYPE: dict[str, str] = {
    "audit": "auditOpinion",
}
# OpenDART 개발가이드 공식 한글 컬럼 매핑 (https://opendart.fss.or.kr/guide/)
_REPORT_COL_KR: dict[str, str] = {
    # 증자(감자) 현황 — apiId=2019004
    "isu_dcrs_de": "주식발행(감소)일자",
    "isu_dcrs_stle": "발행(감소)형태",
    "isu_dcrs_stock_knd": "발행(감소)주식종류",
    "isu_dcrs_qy": "발행(감소)수량",
    "isu_dcrs_mstvdv_fval_amount": "주당액면가액",
    "isu_dcrs_mstvdv_amount": "주당가액",
    # 자기주식 취득/처분 — apiId=2019006
    "stock_knd": "주식종류",
    "acqs_mth1": "취득방법(대)",
    "acqs_mth2": "취득방법(중)",
    "acqs_mth3": "취득방법(소)",
    "bsis_qy": "기초수량",
    "change_qy_acqs": "변동수량(취득)",
    "change_qy_dsps": "변동수량(처분)",
    "change_qy_incnr": "변동수량(소각)",
    "trmend_qy": "기말수량",
    # 주식총수 현황 — apiId=2020002
    "se": "구분",
    "isu_stock_totqy": "발행할주식총수",
    "now_to_isu_stock_totqy": "현재까지발행주식총수",
    "now_to_dcrs_stock_totqy": "현재까지감소주식총수",
    "redc": "감자",
    "profit_incnr": "이익소각",
    "rdmstk_repy": "상환주식상환",
    "etc": "기타",
    "istc_totqy": "발행주식총수",
    "tesstk_co": "자기주식수",
    "distb_stock_co": "유통주식수",
    # 타법인 출자 현황 — apiId=2019015
    "inv_prm": "법인명",
    "frst_acqs_de": "최초취득일자",
    "invstmnt_purps": "출자목적",
    "frst_acqs_amount": "최초취득금액",
    "bsis_blce_qy": "기초잔액(수량)",
    "bsis_blce_qota_rt": "기초잔액(지분율)",
    "bsis_blce_acntbk_amount": "기초잔액(장부가액)",
    "incrs_dcrs_acqs_dsps_qy": "증감(취득처분)(수량)",
    "incrs_dcrs_acqs_dsps_amount": "증감(취득처분)(금액)",
    "incrs_dcrs_evl_lstmn": "증감(평가손액)",
    "trmend_blce_qy": "기말잔액(수량)",
    "trmend_blce_qota_rt": "기말잔액(지분율)",
    "trmend_blce_acntbk_amount": "기말잔액(장부가액)",
    "recent_bsns_year_fnnr_sttus_tot_assets": "최근사업연도재무현황(총자산)",
    "recent_bsns_year_fnnr_sttus_thstrm_ntpf": "최근사업연도재무현황(당기순이익)",
    # 최대주주 변동현황 — apiId=2019008
    "change_on": "변동일",
    "mxmm_shrholdr_nm": "최대주주명",
    "posesn_stock_co": "소유주식수",
    "qota_rt": "지분율",
    "change_cause": "변동원인",
    # 소액주주 현황 — apiId=2019009
    "shrholdr_co": "주주수",
    "shrholdr_tot_co": "전체주주수",
    "shrholdr_rate": "주주비율",
    "hold_stock_co": "보유주식수",
    "stock_tot_co": "총발행주식수",
    "hold_stock_rate": "보유주식비율",
    # 사외이사 현황 — apiId=2020012
    "drctr_co": "이사의수",
    "otcmp_drctr_co": "사외이사수",
    "apnt": "사외이사변동(선임)",
    "rlsofc": "사외이사변동(해임)",
    "mdstrm_resig": "사외이사변동(중도퇴임)",
    # 공모자금 사용내역 — apiId=2020016
    "se_nm": "구분",
    "tm": "회차",
    "pay_de": "납입일",
    "pay_amount": "납입금액",
    "on_dclrt_cptal_use_plan": "신고서상자금사용계획",
    "real_cptal_use_sttus": "실제자금사용현황",
    "rs_cptal_use_plan_useprps": "증권신고서자금사용계획(용도)",
    "rs_cptal_use_plan_prcure_amount": "증권신고서자금사용계획(조달금액)",
    "real_cptal_use_dtls_cn": "실제자금사용내역(내용)",
    "real_cptal_use_dtls_amount": "실제자금사용내역(금액)",
    "dffrnc_occrrnc_resn": "차이발생사유",
    # 사모자금 사용내역 — apiId=2020017
    "cptal_use_plan": "자금사용계획",
    "mtrpt_cptal_use_plan_useprps": "주요사항보고서자금사용계획(용도)",
    "mtrpt_cptal_use_plan_prcure_amount": "주요사항보고서자금사용계획(조달금액)",
    # 회사채 미상환 잔액 — apiId=2020006
    "sm": "합계",
    "remndr_exprtn1": "잔여만기(대분류)",
    "remndr_exprtn2": "잔여만기(소분류)",
    "yy1_below": "1년이하",
    "yy1_excess_yy2_below": "1년초과2년이하",
    "yy2_excess_yy3_below": "2년초과3년이하",
    "yy3_excess_yy4_below": "3년초과4년이하",
    "yy4_excess_yy5_below": "4년초과5년이하",
    "yy5_excess_yy10_below": "5년초과10년이하",
    "yy10_excess": "10년초과",
    # 단기사채 미상환 잔액 — apiId=2020005
    "de10_below": "10일이하",
    "de10_excess_de30_below": "10일초과30일이하",
    "de30_excess_de90_below": "30일초과90일이하",
    "de90_excess_de180_below": "90일초과180일이하",
    "de180_excess_yy1_below": "180일초과1년이하",
    "isu_lmt": "발행한도",
    "remndr_lmt": "잔여한도",
    # 감사용역 체결현황 — apiId=2020010
    "bsns_year": "사업연도",
    "adtor": "감사인",
    "cn": "내용",
    "mendng": "보수",
    "tot_reqre_time": "총소요시간",
    "adt_cntrct_dtls_mendng": "감사계약내역(보수)",
    "adt_cntrct_dtls_time": "감사계약내역(시간)",
    "real_exc_dtls_mendng": "실제수행내역(보수)",
    "real_exc_dtls_time": "실제수행내역(시간)",
    # 비감사 용역 계약현황 — apiId=2020011
    "cntrct_cncls_de": "계약체결일",
    "servc_cn": "용역내용",
    "servc_exc_pd": "용역수행기간",
    "servc_mendng": "용역보수",
    # 이사·감사 보수현황 — apiId=2019013
    "nmpr": "인원수",
    "mendng_totamt": "보수총액",
    "jan_avrg_mendng_am": "1인평균보수액",
    # 개인별 보수현황 — apiId=2019012, 2019014
    "nm": "이름",
    "ofcps": "직위",
    "mendng_totamt_ct_incls_mendng": "보수총액비포함보수",
    # 미등기임원 보수현황 — apiId=2020013
    "fyer_salary_totamt": "연간급여총액",
    "jan_salary_am": "1인평균급여액",
    # 공통
    "rm": "비고",
}
_DOCS_TOPIC_HINTS: dict[str, tuple[str, ...]] = {
    "costByNature": ("비용의 성격별 분류", "비용의성격별분류", "제조원가", "감가상각비"),
    "tangibleAsset": ("유형자산", "감가상각비"),
}
_DOCS_TITLE_HINTS: dict[str, tuple[str, ...]] = {
    "costByNature": ("비용의 성격별 분류", "비용의성격별분류", "제조원가명세서"),
    "tangibleAsset": ("유형자산",),
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


from dartlab.engines.common.types import ShowResult


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

    # subtopic 자동 수평화를 건너뛰는 topic (이미 다른 경로에서 처리되거나 subtopic 과다)
    _AUTO_SUBTOPIC_SKIP: frozenset[str] = frozenset(
        {
            # 이미 명시적 subtopic 경로
            "salesOrder",
            "riskDerivative",
            "segments",
            "rawMaterial",
            "costByNature",
            # 재무제표 — finance 엔진이 authoritative
            "BS",
            "IS",
            "CIS",
            "CF",
            "SCE",
            "ratios",
            # fsSummary — subtopic 800+ (과다)
            "fsSummary",
            # 주석 — 너무 방대하여 subtopic 세분화 비효율
            "consolidatedNotes",
            "financialNotes",
        }
    )

    _AUTO_SUBTOPIC_MAX = 100  # subtopic이 이 수를 넘으면 text fallback

    def _autoSubtopicWide(self, topic: str, *, raw: bool = False) -> pl.DataFrame | None:
        """table-heavy docs topic을 자동으로 subtopic wide 수평화."""
        if topic in self._AUTO_SUBTOPIC_SKIP:
            return None
        result = self._topicSubtables(topic)
        if result is None:
            return None
        if result.wide.height > self._AUTO_SUBTOPIC_MAX:
            return None
        return result.long if raw else result.wide

    def _safePrimary(self, name: str) -> pl.DataFrame | None:
        try:
            payload = self._get_primary(name)
        except (KeyError, ValueError, TypeError, ImportError, FileNotFoundError, AttributeError):
            return None
        return payload if isinstance(payload, pl.DataFrame) else None

    def _hasDocsTopicHint(self, topic: str) -> bool:
        cacheKey = f"_hasDocsTopicHint:{topic}"
        if cacheKey in self._cache:
            return bool(self._cache[cacheKey])
        keywords = _DOCS_TOPIC_HINTS.get(topic)
        if not self._hasDocs or not keywords:
            self._cache[cacheKey] = False
            return False
        raw = self.rawDocs
        if raw is None or raw.is_empty():
            self._cache[cacheKey] = False
            return False
        matched = False
        for keyword in keywords:
            subset = raw.filter(
                pl.col("section_title").str.contains(keyword, literal=True, strict=False)
                | pl.col("section_content").str.contains(keyword, literal=True, strict=False)
            )
            if not subset.is_empty():
                matched = True
                break
        self._cache[cacheKey] = matched
        return matched

    def _hasSectionTitleHint(self, topic: str) -> bool:
        cacheKey = f"_hasSectionTitleHint:{topic}"
        if cacheKey in self._cache:
            return bool(self._cache[cacheKey])
        keywords = _DOCS_TITLE_HINTS.get(topic)
        if not self._hasDocs or not keywords:
            self._cache[cacheKey] = False
            return False
        path = Path(_dataDir("docs")) / f"{self.stockCode}.parquet"
        if not path.exists():
            self._cache[cacheKey] = False
            return False
        matched = False
        for keyword in keywords:
            subset = (
                pl.scan_parquet(path)
                .select("section_title")
                .filter(pl.col("section_title").str.contains(keyword, literal=True, strict=False))
                .limit(1)
                .collect()
            )
            if subset.height > 0:
                matched = True
                break
        self._cache[cacheKey] = matched
        return matched

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
        periodCols = [c for c in topicRows.columns if _isPeriodColumn(c)]
        rows = []
        seen: set[int] = set()
        for row in topicRows.iter_rows(named=True):
            bo = row.get("blockOrder", 0)
            if bo in seen:
                continue
            seen.add(bo)
            bt = row.get("blockType", "text")
            source = row.get("source", "docs")
            # preview
            preview = ""
            if source in ("finance", "report"):
                preview = f"({source})"
            else:
                for p in reversed(periodCols):
                    val = row.get(p)
                    if val:
                        preview = str(val)[:50]
                        break
            rows.append(
                {
                    "block": bo,
                    "type": bt,
                    "source": source,
                    "preview": preview,
                }
            )
        return pl.DataFrame(rows)

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

    def _sectionTopicRaw(self, topic: str) -> pl.DataFrame | None:
        """sections에서 topic의 원본 수평 행(text+table) 반환."""
        docsSections = self.docs.sections
        if docsSections is not None and "topic" in docsSections.columns:
            topicFrame = docsSections.filter(pl.col("topic") == topic)
            if not topicFrame.is_empty():
                return topicFrame
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
        """단위행/기준일행이 헤더인 서브테이블 → 단위행 제거 + 나머지 반환.

        패턴: | (단위:천원) | | | → sep → 실제헤더 → 데이터
        다중컬럼: | (기준일 : | 2018년 03월 31일 | ) | (단위 : 주) |
        반환: 실제헤더 행부터의 서브테이블 (기존 파서가 그대로 동작).
        해당하지 않으면 None.
        """
        # 단위행 변형: (단위:천원), (원화단위:백만원, 외화단위:천USD),
        # [단위 : 백만원], <당분기> (단위: 원), （단위: 천원) 등
        _UNIT_ONLY_RE = re.compile(
            r"^[\(\[\（<〈]?\s*"
            r"(?:<[^>]+>\s*)?"  # <당분기> 같은 앞쪽 태그
            r"[\(\[\（]?\s*"
            r"(?:단위|원화\s*단위|외화\s*단위|금액\s*단위)"
            r".*$",
            re.IGNORECASE,
        )
        _DATE_ONLY_RE = re.compile(r"^\(?\s*기준일\s*:")

        # 첫 번째 비-separator 행 찾기
        firstRow = None
        for line in sub:
            cells = [c.strip() for c in line.strip("|").split("|")]
            if all(set(c.strip()) <= {"-", ":"} for c in cells if c.strip()):
                continue
            firstRow = [c for c in cells if c.strip()]
            break

        if firstRow is None:
            return None

        # 단일 컬럼: 기존 방식
        if len(firstRow) == 1:
            h = firstRow[0].strip()
            if not (_UNIT_ONLY_RE.match(h) or _DATE_ONLY_RE.match(h)):
                return None
        else:
            # 다중 컬럼: 셀을 합쳐서 단위/기준일 패턴 검사
            joined = " ".join(c.strip() for c in firstRow)
            hasUnit = bool(re.search(r"단위\s*[:/]", joined))
            hasDate = bool(re.search(r"기준일\s*[:/]", joined))
            if not (hasUnit or hasDate):
                return None

        # 첫 separator 이후의 행들을 새 서브테이블로 반환
        sepIdx = -1
        for i, line in enumerate(sub):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if all(set(c.strip()) <= {"-", ":"} for c in cells if c.strip()):
                sepIdx = i
                break

        if sepIdx < 0 or sepIdx + 1 >= len(sub):
            return None

        remainder = sub[sepIdx + 1 :]
        if not remainder:
            return None

        # 나머지에 separator가 있으면 그대로 반환 (정상적인 2-separator 구조)
        hasSep = any(
            all(set(c.strip()) <= {"-", ":"} for c in line.strip("|").split("|") if c.strip()) for line in remainder
        )
        if hasSep:
            return remainder

        # separator가 없으면 실제 헤더 + 인조 separator + 데이터 행으로 구성
        if len(remainder) >= 2:
            headerLine = remainder[0]
            colCount = len(headerLine.strip("|").split("|"))
            sepLine = "| " + " | ".join(["---"] * colCount) + " |"
            return [headerLine, sepLine] + remainder[1:]

        return None

    def _horizontalizeTableBlock(
        self,
        topicFrame: pl.DataFrame,
        blockOrder: int,
        periodCols: list[str],
        period: str | None = None,
    ) -> pl.DataFrame | None:
        """table 블록을 기간 간 수평화 — 항목×기간 매트릭스."""
        from dartlab.engines.dart.docs.sections.tableParser import (
            _classifyStructure,
            _dataRows,
            _headerCells,
            _isJunk,
            splitSubtables,
        )

        boRow = topicFrame.filter((pl.col("blockOrder") == blockOrder) & (pl.col("blockType") == "table"))
        if boRow.is_empty():
            return None

        from dartlab.engines.dart.docs.sections.tableParser import (
            _parseKeyValueOrMatrix,
            _parseMultiYear,
        )

        _SUFFIX_RE = re.compile(r"(사업)?부문$")
        # 기수+상대기(당기/전기 등): 제76기(당기) → 당기, 제2기1분기(당분기) → 당분기
        _KISU_RE = re.compile(
            r"제\d+기\s*(?:\d*분기|반기|말)?\s*"
            r"\(?(당기|전기|전전기|당반기|전반기|당분기|전분기)\)?"
        )

        _NOTE_REF_RE = re.compile(r"\(\*\d*(?:,\d+)*\)")  # (*), (*1), (*1,2) 등

        def _normalizeItem(name: str) -> str:
            name = _SUFFIX_RE.sub("", name).strip()
            name = _NOTE_REF_RE.sub("", name).strip()  # 주석번호 제거
            # 기수+상대기 → 상대기명으로 치환
            m = _KISU_RE.search(name)
            if m:
                return m.group(1)
            return name

        def _collectMultiYear(sub: list[str], pYear: int, p: str) -> None:
            triples, _ = _parseMultiYear(sub, pYear)
            for rawItem, year, val in triples:
                item = _normalizeItem(rawItem)
                if year == str(pYear):
                    if item not in seenItems:
                        allItems.append(item)
                        seenItems.add(item)
                    if item not in periodItemVal:
                        periodItemVal[item] = {}
                    periodItemVal[item][p] = val

        def _collectKvMatrix(sub: list[str], p: str) -> None:
            rows, headerNames, _ = _parseKeyValueOrMatrix(sub)
            for rawItem, vals in rows:
                item = _normalizeItem(rawItem)
                nonEmptyVals = [v for v in vals if v.strip()]
                if len(headerNames) >= 2 and len(nonEmptyVals) >= 2 and len(nonEmptyVals) <= len(headerNames):
                    # matrix: 헤더별 개별 항목으로 분리 (vals와 headerNames 수가 맞을 때만)
                    for hi, hname in enumerate(headerNames):
                        v = vals[hi].strip() if hi < len(vals) else ""
                        if not v or v == "-":
                            continue
                        compoundItem = f"{item}_{hname}"
                        if compoundItem not in seenItems:
                            allItems.append(compoundItem)
                            seenItems.add(compoundItem)
                        if compoundItem not in periodItemVal:
                            periodItemVal[compoundItem] = {}
                        periodItemVal[compoundItem][p] = v
                else:
                    # key_value 또는 vals > headerNames: 전체 값 합침
                    val = " | ".join(v for v in vals if v.strip()).strip()
                    if val:
                        if item not in seenItems:
                            allItems.append(item)
                            seenItems.add(item)
                        if item not in periodItemVal:
                            periodItemVal[item] = {}
                        periodItemVal[item][p] = val

        from dartlab.engines.dart.docs.sections.tableParser import _normalizeHeader

        _PERIOD_KW_RE = re.compile(r"\d*분기|반기|당기|전기|전전기|당반기|전반기|당분기|전분기|당기말|전기말")

        def _groupHeader(hc: list[str]) -> str:
            """그룹핑용 헤더 시그니처 — 기간 키워드까지 제거."""
            h = _normalizeHeader(hc)
            h = _PERIOD_KW_RE.sub("", h)
            h = re.sub(r"\| *\|", "|", h)  # 빈 파이프 정리
            h = re.sub(r"\s+", " ", h).strip()
            return h

        # ── 1단계: 기간별 서브테이블의 헤더 시그니처 수집 ──
        _headerGroups: dict[str, list[str]] = {}  # normHeader → [periods]
        for p in periodCols:
            md = boRow[p][0] if p in boRow.columns else None
            if md is None:
                continue
            for sub in splitSubtables(str(md)):
                hc = _headerCells(sub)
                if _isJunk(hc):
                    continue
                dr = _dataRows(sub)
                if not dr:
                    # 데이터 없음 → 단위/기준일 헤더 strip 시도
                    fixed = self._stripUnitHeader(sub)
                    if fixed is not None:
                        fixedHc = _headerCells(fixed)
                        fixedDr = _dataRows(fixed)
                        if fixedHc and not _isJunk(fixedHc) and fixedDr:
                            sub = fixed
                            hc = fixedHc
                            dr = fixedDr
                        else:
                            continue
                    else:
                        continue
                structType = _classifyStructure(hc)
                if structType == "skip":
                    fixed = self._stripUnitHeader(sub)
                    if fixed is not None:
                        fixedHc = _headerCells(fixed)
                        fixedDr = _dataRows(fixed)
                        if fixedHc and not _isJunk(fixedHc) and fixedDr:
                            hc = fixedHc
                gh = _groupHeader(hc)
                if gh not in _headerGroups:
                    _headerGroups[gh] = []
                if p not in _headerGroups[gh]:
                    _headerGroups[gh].append(p)

        # 가장 많은 기간을 커버하는 헤더 그룹 선택
        if _headerGroups:
            bestHeader = max(_headerGroups, key=lambda k: len(_headerGroups[k]))
            bestPeriods = set(_headerGroups[bestHeader])
        else:
            bestPeriods = set(periodCols)

        # ── 2단계: 선택된 그룹의 기간에서만 수평화 ──
        allItems: list[str] = []
        seenItems: set[str] = set()
        periodItemVal: dict[str, dict[str, str]] = {}

        for p in periodCols:
            if p not in bestPeriods:
                continue
            md = boRow[p][0] if p in boRow.columns else None
            if md is None:
                continue
            m = re.match(r"\d{4}", p)
            if m is None:
                continue
            pYear = int(m.group())

            for sub in splitSubtables(str(md)):
                hc = _headerCells(sub)
                if _isJunk(hc):
                    continue
                dr = _dataRows(sub)
                if not dr:
                    # 데이터 없음 → 단위/기준일 헤더 strip 시도
                    fixed = self._stripUnitHeader(sub)
                    if fixed is not None:
                        fixedHc = _headerCells(fixed)
                        fixedDr = _dataRows(fixed)
                        if fixedHc and not _isJunk(fixedHc) and fixedDr:
                            sub = fixed
                            hc = fixedHc
                            dr = fixedDr
                        else:
                            continue
                    else:
                        continue

                structType = _classifyStructure(hc)

                # 단위/기준일 헤더 → 실제 헤더로 재분류
                if structType == "skip":
                    fixed = self._stripUnitHeader(sub)
                    if fixed is not None:
                        fixedHc = _headerCells(fixed)
                        fixedDr = _dataRows(fixed)
                        if fixedHc and not _isJunk(fixedHc) and fixedDr:
                            structType = _classifyStructure(fixedHc)
                            hc = fixedHc
                            sub = fixed  # 이후 파서에 strip된 서브테이블 전달

                # 선택된 헤더 그룹의 서브테이블만 수집
                gh = _groupHeader(hc)
                if gh != bestHeader:
                    continue

                if structType == "multi_year":
                    beforeLen = len(allItems)
                    _collectMultiYear(sub, pYear, p)
                    # multi_year 파싱 실패 → kv/matrix fallback
                    if len(allItems) == beforeLen and len(hc) >= 2:
                        _collectKvMatrix(sub, p)

                elif structType in ("key_value", "matrix"):
                    _collectKvMatrix(sub, p)

        if not allItems:
            return None

        # 품질 필터: 숫자만 항목명 제거
        def _isJunkItem(name: str) -> bool:
            stripped = re.sub(r"[,.\-\s]", "", name)
            return stripped.isdigit() or not stripped

        allItems = [item for item in allItems if not _isJunkItem(item)]
        if not allItems:
            return None

        # 이력형 감지: 기간 간 항목 겹침률이 낮으면 수평화 부적합
        periodItemSets = {}
        for item in allItems:
            for p in periodItemVal.get(item, {}):
                if p not in periodItemSets:
                    periodItemSets[p] = set()
                periodItemSets[p].add(item)
        if len(periodItemSets) >= 2:
            sets = list(periodItemSets.values())
            totalOverlap = 0
            totalPairs = 0
            for i in range(len(sets)):
                for j in range(i + 1, min(i + 4, len(sets))):  # 인접 기간만
                    union = len(sets[i] | sets[j])
                    inter = len(sets[i] & sets[j])
                    if union > 0:
                        totalOverlap += inter / union
                        totalPairs += 1
            avgOverlap = totalOverlap / totalPairs if totalPairs else 0
            if avgOverlap < 0.3 and len(allItems) > 5:
                # 이력형 → 수평화 스킵
                return None

        # 목록형 감지: 항목 수가 과다하면 수평화 부적합
        if len(allItems) > 50:
            return None

        # DataFrame 구성
        usedPeriods = [p for p in periodCols if any(p in periodItemVal.get(item, {}) for item in allItems)]
        if not usedPeriods:
            return None

        # sparse 감지: 항목이 많고 대부분이 소수 기간에서만 값 → 수평화 부적합
        # (기간별 서브테이블 구조가 다른 경우, 예: 이사 변동 + 사업조직 변경 혼재)
        if len(usedPeriods) >= 3 and len(allItems) > 15:
            totalCells = len(allItems) * len(usedPeriods)
            filledCells = sum(1 for item in allItems for p in usedPeriods if periodItemVal.get(item, {}).get(p))
            fillRate = filledCells / totalCells if totalCells > 0 else 0
            if fillRate < 0.5:
                return None

        schema = {"항목": pl.Utf8}
        for p in usedPeriods:
            schema[p] = pl.Utf8

        rows = []
        for item in allItems:
            if not any(periodItemVal.get(item, {}).get(p) for p in usedPeriods):
                continue
            row: dict[str, str | None] = {"항목": item}
            for p in usedPeriods:
                row[p] = periodItemVal.get(item, {}).get(p)
            rows.append(row)

        if not rows:
            return None

        df = pl.DataFrame(rows, schema=schema)
        return self._applyPeriodFilter(df, period)

    @staticmethod
    def _cleanSubtopicWide(df: pl.DataFrame) -> pl.DataFrame:
        """subtopic wide에서 메타 컬럼 제거 + subtopic→항목 통일 + 내부 topic명 한글화."""
        _DROP_META = {"topic", "sourceTopic", "subtopicOrder", "semanticTopic", "detailTopic"}
        dropCols = [c for c in df.columns if c in _DROP_META]
        if dropCols:
            df = df.drop(dropCols)
        if "subtopic" in df.columns:
            df = df.rename({"subtopic": "항목"})
        # 내부 topic명을 한글로 치환
        if "항목" in df.columns:
            df = df.with_columns(pl.col("항목").replace(_TOPIC_LABELS).alias("항목"))
        return df

    @staticmethod
    def _ensurePeriodAscending(df: pl.DataFrame) -> pl.DataFrame:
        """기간 컬럼을 오름차순으로 정렬."""
        nonPeriodCols = [c for c in df.columns if not _isPeriodColumn(c)]
        periodCols = [c for c in df.columns if _isPeriodColumn(c)]
        if len(periodCols) < 2:
            return df
        sortedPeriods = sorted(periodCols)
        if periodCols == sortedPeriods:
            return df
        return df.select([*nonPeriodCols, *sortedPeriods])

    @staticmethod
    def _dropOldPeriodColumns(df: pl.DataFrame, minYear: int) -> pl.DataFrame:
        """기간 컬럼 중 minYear 미만 연도를 제거."""
        keepCols = []
        for c in df.columns:
            if _isPeriodColumn(c) and int(c[:4]) < minYear:
                continue
            keepCols.append(c)
        if len(keepCols) == len(df.columns):
            return df
        return df.select(keepCols)

    def _trimOldPeriods(self, result: Any) -> Any:
        """show() 반환값에서 _MIN_YEAR 이전 기간 제거."""
        if result is None:
            return None
        minYear = self._MIN_YEAR
        if isinstance(result, ShowResult):
            text = self._dropOldPeriodColumns(result.text, minYear) if result.text is not None else None
            table = self._dropOldPeriodColumns(result.table, minYear) if result.table is not None else None
            # 기간 컬럼이 모두 제거된 경우
            if text is not None:
                hasPeriod = any(_isPeriodColumn(c) for c in text.columns)
                if not hasPeriod:
                    text = None
            if table is not None:
                hasPeriod = any(_isPeriodColumn(c) for c in table.columns)
                if not hasPeriod:
                    table = None
            if text is None and table is None:
                return None
            return ShowResult(text=text, table=table)
        if isinstance(result, pl.DataFrame):
            trimmed = self._dropOldPeriodColumns(result, minYear)
            # 기간 컬럼이 있었는데 모두 제거된 경우 → None
            hadPeriod = any(_isPeriodColumn(c) for c in result.columns)
            hasPeriod = any(_isPeriodColumn(c) for c in trimmed.columns)
            if hadPeriod and not hasPeriod:
                return None
            return trimmed
        return result

    @staticmethod
    def _unpivotTopicRows(topicFrame: pl.DataFrame) -> pl.DataFrame:
        """topic × period 수평 행을 세로로 전환. blockType 유지."""
        metaCols = {"chapter", "topic", "blockType", "blockOrder"}
        periodCols = [c for c in topicFrame.columns if c not in metaCols]
        hasBlockType = "blockType" in topicFrame.columns
        hasBlockOrder = "blockOrder" in topicFrame.columns
        rows: list[dict[str, str | None]] = []
        for i in range(topicFrame.height):
            ch = topicFrame["chapter"][i] if "chapter" in topicFrame.columns else None
            tp = topicFrame["topic"][i] if "topic" in topicFrame.columns else None
            bt = topicFrame["blockType"][i] if hasBlockType else None
            bo = topicFrame["blockOrder"][i] if hasBlockOrder else None
            for col in periodCols:
                val = topicFrame[col][i]
                if val is not None and str(val).strip():
                    rows.append(
                        {
                            "chapter": ch,
                            "topic": tp,
                            "blockType": bt,
                            "blockOrder": bo,
                            "period": col,
                            "content": str(val),
                        }
                    )
        if not rows:
            return pl.DataFrame(
                {"chapter": [], "topic": [], "blockType": [], "blockOrder": [], "period": [], "content": []}
            )
        return pl.DataFrame(rows)

    def _topicBlocks(self, topic: str) -> pl.DataFrame | None:
        blocks = self._retrievalBlocks()
        if blocks is None or blocks.is_empty():
            return None
        topicBlocks = blocks.filter(pl.col("topic") == topic)
        if topicBlocks.is_empty():
            return None
        return topicBlocks

    def _topicChangeLedger(self, topic: str) -> pl.DataFrame | None:
        cacheKey = f"_topicLedger:{topic}"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        blocks = self._topicBlocks(topic)
        result = _buildTopicChangeLedger(blocks)
        self._cache[cacheKey] = result
        return result

    def _topicEvidence(self, topic: str, period: str) -> pl.DataFrame:
        from dartlab.engines.dart.docs.sections import rawPeriod

        normalizedPeriod = rawPeriod(period)
        cacheKey = f"_topicEvidence:{topic}:{normalizedPeriod}"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        blocks = self._topicBlocks(topic)
        result = _buildTopicEvidence(blocks, normalizedPeriod)
        self._cache[cacheKey] = result
        return result

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
        from dartlab.engines.dart.report.extract import extractClean

        df = extractClean(self.stockCode, apiType)
        if df is None or df.is_empty():
            return None

        # 2015년 제외 (sections/finance와 통일)
        df = df.filter(pl.col("year") != 2015)
        if df.is_empty():
            return None

        # stock_knd 필터 (보통주 우선)
        if "stock_knd" in df.columns:
            common = df.filter(pl.col("stock_knd") == "보통주")
            if not common.is_empty():
                df = common

        # se(항목) 컬럼이 있으면 se × period 수평화
        if "se" in df.columns:
            return self._reportPivotBySe(df, raw=raw)

        # se 없는 apiType → 행 기반 반환
        _META_COLS = {"stlm_dt", "apiType", "stockCode", "year", "quarter", "quarterNum", "stock_knd"}
        dropCols = [c for c in df.columns if c in _META_COLS]
        if dropCols:
            df = df.drop(dropCols)
        if not raw:
            renameMap = {c: _REPORT_COL_KR[c] for c in df.columns if c in _REPORT_COL_KR}
            if renameMap:
                existing = set(df.columns)
                renameMap = {k: v for k, v in renameMap.items() if v not in existing or k == v}
                if renameMap:
                    df = df.rename(renameMap)
        return df

    def _reportPivotBySe(self, df: pl.DataFrame, *, raw: bool = False) -> pl.DataFrame | None:
        """report se(항목) × period 수평화. 분기별 전체 데이터."""
        df = df.with_columns((pl.col("year").cast(pl.Utf8) + "Q" + pl.col("quarterNum").cast(pl.Utf8)).alias("_period"))
        # null-only 행 제외
        if "thstrm" in df.columns:
            df = df.filter(pl.col("thstrm").is_not_null())
        if df.is_empty():
            return None

        pivoted = df.pivot(on="_period", index="se", values="thstrm", aggregate_function="first")

        # period 컬럼 역순 정렬
        periodCols = [c for c in pivoted.columns if c != "se"]
        periodCols.sort(key=lambda p: (int(p[:4]), int(p[-1])), reverse=True)
        result = pivoted.select(["se"] + periodCols)
        if not raw:
            result = result.rename({"se": "항목"})
        return result

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

    _MIN_YEAR = 2016

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
        """수평화 DataFrame에서 요청 기간 컬럼만 추출.

        wide: 항목(계정명/항목) | 2025Q3 | 2025Q2 | ... 형태
        periods: ["2024Q4", "2023Q4"] 등 비교할 기간 리스트
        Returns: 항목 | 2024Q4 | 2023Q4 형태 (기존 수평화와 동일 방향, 기간만 필터)
        """
        labelCol = wide.columns[0]
        periodCols = [c for c in wide.columns if _isPeriodColumn(c)]

        # 요청된 period 매칭 (Q4 alias 포함)
        matched: list[str] = []
        for p in periods:
            if p in periodCols:
                matched.append(p)
            elif "Q" not in p and f"{p}Q4" in periodCols:
                matched.append(f"{p}Q4")
        if not matched:
            return None

        return wide.select([labelCol] + matched)

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

    def _showCore(
        self,
        topic: str,
        *,
        block: int | None = None,
        period: str | None = None,
        raw: bool = False,
    ) -> Any:
        if topic == "docsStatus":
            return None

        # block이 명시되면 sections 경로 우선 (blockOrder별 접근)
        if block is not None:
            topicFrame = self._sectionTopicRaw(topic)
            if topicFrame is not None:
                return self._showSectionBlock(topicFrame, block=block, period=period)

        if topic in {"BS", "IS", "CIS", "CF", "SCE"}:
            return self._applyPeriodFilter(getattr(self, topic), period)

        if topic == "ratios":
            ratioSeries = self._ratioSeries()
            if ratioSeries is None:
                return None
            series, years = ratioSeries
            templateKey = _ratioTemplateKeyForIndustryGroup(getattr(self.sector, "industryGroup", None))
            fieldNames = _RATIO_TEMPLATE_FIELDS.get(templateKey)
            ratioFrame = _ratioSeriesToDataFrame(series, years, fieldNames=fieldNames)
            return self._applyPeriodFilter(ratioFrame, period)

        if topic in {"salesOrder", "riskDerivative", "segments", "rawMaterial", "costByNature"}:
            if topic == "costByNature" and not self._hasSectionTitleHint("costByNature"):
                return None
            if raw:
                subtopicFrame = self._sectionsSubtopicLong(topic)
                if subtopicFrame is not None:
                    return self._applyPeriodFilter(subtopicFrame, period)
            else:
                subtopicFrame = self._sectionsSubtopicWide(topic)
                if subtopicFrame is not None:
                    subtopicFrame = self._cleanSubtopicWide(subtopicFrame)
                    return self._applyPeriodFilter(subtopicFrame, period)
            fallback_payload = {
                "salesOrder": self._safePrimary("salesOrder"),
                "riskDerivative": self._safePrimary("riskDerivative"),
                "segments": self._safePrimary("segments"),
                "rawMaterial": self._safePrimary("rawMaterial"),
                "costByNature": self._safePrimary("costByNature") if self._hasDocsTopicHint("costByNature") else None,
            }[topic]
            if fallback_payload is not None:
                payload = self._ensurePeriodAscending(fallback_payload)
                # account/subtopic 등 → 항목 통일
                if "account" in payload.columns:
                    payload = payload.rename({"account": "항목"})
                elif "subtopic" in payload.columns:
                    payload = payload.rename({"subtopic": "항목"})
                return self._applyPeriodFilter(payload, period)
            return None

        reportFrame = self._reportFrame(topic, raw=raw)
        if reportFrame is not None:
            return self._applyPeriodFilter(reportFrame, period)

        if self.notes is not None:
            from dartlab.engines.dart.docs.notes import _REGISTRY as _NOTES_REGISTRY

            if topic in _NOTES_REGISTRY:
                return self._applyPeriodFilter(self.notes._get(topic), period)

        # docs topic — sections에서 blockOrder별 text/table 반환
        topicFrame = self._sectionTopicRaw(topic)
        if topicFrame is not None:
            return self._showSectionBlock(topicFrame, block=block, period=period)

        return None

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
        from dartlab.engines.common.docs.diff import sectionsDiff, topicDiff

        docsSections = self.docs.sections
        if docsSections is None:
            return None

        # 줄 단위 상세 diff (인터리빙 순서로 맥락 유지)
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

        sec = self.docs.sections
        if sec is not None and "topic" in sec.columns:
            from dartlab.engines.dart.docs.sections import displayPeriod, formatPeriodRange, sortPeriods

            periodCols = sortPeriods([c for c in sec.columns if _isPeriodColumn(c)], descending=True)
            periodRange = formatPeriodRange(periodCols, descending=True, annualAsQ4=True)
            topicOrder: list[str] = []
            seenTopics: set[str] = set()
            for row in sec.iter_rows(named=True):
                topic = row.get("topic")
                if isinstance(topic, str) and topic and topic not in seenTopics:
                    seenTopics.add(topic)
                    topicOrder.append(topic)
            for rowIdx, topic in enumerate(topicOrder):
                topicFrame = sec.filter(pl.col("topic") == topic)
                if topicFrame.is_empty():
                    continue
                nonNull = sum(
                    1 for c in periodCols if c in topicFrame.columns and topicFrame.get_column(c).drop_nulls().len() > 0
                )
                preview = "-"
                for row in topicFrame.iter_rows(named=True):
                    for col in periodCols:
                        val = row.get(col)
                        if val is not None:
                            text = _normalizeTextCell(val)[:80]
                            preview = f"{displayPeriod(col, annualAsQ4=True)}: {text}"
                            break
                    if preview != "-":
                        break
                chapterVal = topicFrame.item(0, "chapter") if "chapter" in topicFrame.columns else None
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

        if self._hasReport:
            from dartlab.engines.dart.report.types import API_TYPE_LABELS, API_TYPES

            existingTopics = {r["topic"] for r in rows}
            for rIdx, apiType in enumerate(API_TYPES):
                if apiType in existingTopics:
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
            from dartlab.engines.dart.affiliate import build_graph, export_full

            data = build_graph(verbose=False)
            self._cache["_network_data"] = data
            self._cache["_network_full"] = export_full(data)
        return self._cache["_network_data"], self._cache["_network_full"]

    def network(self, view: str | None = None, *, hops: int = 1) -> pl.DataFrame | None:
        """관계 네트워크.

        Args:
            view: None이면 요약, "members"/"edges"/"cycles"/"peers" 중 택
            hops: peers 뷰에서 홉 수

        Example::

            c = Company("005930")
            c.network()            # 요약
            c.network("members")   # 같은 그룹 계열사
            c.network("edges")     # 출자/지분 연결
            c.network("cycles")    # 순환출자 경로
            c.network("peers")     # 이 회사 중심 서브그래프
        """
        result = self._ensureNetwork()
        if result is None:
            return None
        data, full = result
        code = self.stockCode
        group = data["code_to_group"].get(code, self.corpName or code)

        if view is None:
            return self._networkOverview(data, full, code, group)
        if view == "members":
            return self._networkMembers(data, code, group)
        if view == "edges":
            return self._networkEdges(full, code)
        if view == "cycles":
            return self._networkCycles(data, code)
        if view == "peers":
            return self._networkPeers(data, full, code, hops=hops)
        return None

    def _networkOverview(self, data: dict, full: dict, code: str, group: str) -> pl.DataFrame:
        """요약 테이블."""
        from collections import Counter

        gc = Counter(data["code_to_group"][n] for n in data["all_node_ids"])
        member_count = gc.get(group, 1)
        is_independent = member_count == 1

        # 직접 연결 수
        direct = sum(
            1 for e in full["edges"]
            if e["type"] != "person_shareholder"
            and (e["source"] == code or e["target"] == code)
        )
        outgoing = sum(
            1 for e in full["edges"]
            if e["type"] == "investment" and e["source"] == code
        )
        incoming = sum(
            1 for e in full["edges"]
            if e["type"] != "person_shareholder" and e["target"] == code
        )
        my_cycles = [
            cy for cy in data["cycles"] if code in cy
        ]

        rows = [
            ("그룹", group if not is_independent else f"{group} (독립)"),
            ("계열사", f"{member_count}개"),
            ("직접 연결", f"{direct}개사"),
            ("출자 (→)", f"{outgoing}개"),
            ("피출자 (←)", f"{incoming}개"),
            ("순환출자", f"{len(my_cycles)}개 경로"),
            ("업종", data["listing_meta"].get(code, {}).get("industry", "")),
        ]
        return pl.DataFrame({"항목": [r[0] for r in rows], "값": [r[1] for r in rows]})

    def _networkMembers(self, data: dict, code: str, group: str) -> pl.DataFrame:
        """같은 그룹 계열사 목록."""
        members = [
            n for n in data["all_node_ids"]
            if data["code_to_group"].get(n) == group
        ]
        rows = []
        for m in sorted(members):
            meta = data["listing_meta"].get(m, {})
            rows.append({
                "종목코드": m,
                "회사명": meta.get("name", m),
                "시장": meta.get("market", ""),
                "업종": meta.get("industry", ""),
                "자기": m == code,
            })
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
                rows.append({
                    "종목코드": target,
                    "회사명": node["label"] if node else target,
                    "유형": e["type"],
                    "방향": "출자 →",
                    "목적": e.get("purpose", ""),
                    "지분율": e.get("ownershipPct"),
                    "그룹": node["group"] if node else "",
                })
            elif e["target"] == code:
                source = e["source"]
                node = node_map.get(source)
                rows.append({
                    "종목코드": source,
                    "회사명": node["label"] if node else source,
                    "유형": e["type"],
                    "방향": "← 피출자",
                    "목적": e.get("purpose", ""),
                    "지분율": e.get("ownershipPct"),
                    "그룹": node["group"] if node else "",
                })
        if not rows:
            return pl.DataFrame(schema={"종목코드": pl.Utf8, "회사명": pl.Utf8, "유형": pl.Utf8, "방향": pl.Utf8, "목적": pl.Utf8, "지분율": pl.Float64, "그룹": pl.Utf8})
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
        from dartlab.engines.dart.affiliate import export_ego

        ego = export_ego(data, full, code, hops=hops)
        rows = []
        for n in ego["nodes"]:
            if n["type"] != "company":
                continue
            rows.append({
                "종목코드": n["id"],
                "회사명": n["label"],
                "그룹": n["group"],
                "업종": n.get("industry", ""),
                "연결수": n["degree"],
                "자기": n["id"] == code,
            })
        if not rows:
            return pl.DataFrame(schema={"종목코드": pl.Utf8, "회사명": pl.Utf8, "그룹": pl.Utf8, "업종": pl.Utf8, "연결수": pl.Int64, "자기": pl.Boolean})
        df = pl.DataFrame(rows)
        return df.sort("연결수", descending=True)

    def view(self, *, port: int = 8400) -> None:
        """브라우저에서 공시 뷰어를 엽니다.

        로컬 서버를 자동으로 띄우고 브라우저를 열어서
        이 회사의 전체 공시를 DART 스타일로 탐색할 수 있습니다.

        Example::

            c = Company("005930")
            c.view()
        """
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
            # 서버 준비 대기
            for _ in range(30):
                if _is_port_in_use(port):
                    break
                time.sleep(0.1)

        url = f"http://127.0.0.1:{port}/?company={self.stockCode}"
        webbrowser.open(url)
