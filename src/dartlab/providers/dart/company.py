"""DART 엔진 내부 Company 본체.

사용법::

    from dartlab.providers.dart.company import Company

    c = Company("005930")         # 한국 (DART)
    c = Company("삼성전자")        # 한국 (회사명)
    c.panel("BS")                  # 재무상태표 DataFrame (분기 연결 기본)
    c.panel("IS", freq="Y")        # 손익계산서 (연간 합산)
    c.panel("ratios")              # 재무비율
    c.insights                    # 인사이트 등급
"""

from __future__ import annotations

import re
from typing import Any

import polars as pl

pl.Config.set_fmt_str_lengths(80)
pl.Config.set_tbl_width_chars(200)

from dartlab.core.dataLoader import (
    buildIndex,
    extractCorpName,
    loadData,
)
from dartlab.core.logger import getLogger
from dartlab.core.polarsUtil import isEmptyDf

_log = getLogger(__name__)

# ── 모듈 레지스트리 (core/registry.py에서 자동 생성) ──
# (모듈 import 경로, 함수명, 한글 라벨, primary DataFrame 추출)
# fsSummary/statements는 내부 디스패치 전용 (BS/IS/CF property가 statements를 호출)
from dartlab.core.registry import getModuleEntries as _getModuleEntries


# listing 함수는 ListingResolver registry 경유 (정공법 B - DIP).
# providers/dart 가 gather/listing 직접 import 0 (cycle 회피).
def _listingResolver():
    """ListingResolver lazy resolver - auto-discovery 가 gather/listing register."""
    from dartlab.core.listingResolver import getListingResolver

    resolver = getListingResolver()
    if resolver is None:
        raise RuntimeError("ListingResolver 미등록 - dartlab.gather.krx.listing 모듈 로드 실패")
    return resolver


def codeToName(stockCode):
    """ListingResolver 경유 stockCode → 회사명.

    Args:
        stockCode: 종목코드 (6자리).

    Returns:
        회사명 또는 None.

    Raises:
        없음.

    Example:
        >>> codeToName("005930")

    LLM Specifications:
        AntiPatterns:
            - 4 자리 / 7 자리 코드 호출 → None. KR stockCode 는 6 자리 strict.
            - 회사명으로 호출 X - 반대 매핑은 ``nameToCode``.
        OutputSchema:
            - str 회사명 또는 None.
        Prerequisites:
            - ListingResolver origin (KRX kind 목록 cache).
        Freshness:
            - KIND 갱신 시점 (일 단위).
        Dataflow:
            - stockCode → ListingResolver → kind dict → 본 함수.
        TargetMarkets:
            - KR (KOSPI/KOSDAQ/KONEX).
    """
    return _listingResolver().codeToName(stockCode)


def nameToCode(corpName):
    """ListingResolver 경유 회사명 → stockCode.

    Args:
        corpName: 회사명.

    Returns:
        종목코드 또는 None.

    Raises:
        없음.

    Example:
        >>> nameToCode("삼성전자")

    LLM Specifications:
        AntiPatterns:
            - 영문명 호출 → None. KIND 는 한국어 정식 회사명 기반.
            - 정확 매치만 - 부분 매칭은 ``searchName``.
        OutputSchema:
            - str 6 자리 종목코드 또는 None.
        Prerequisites:
            - ListingResolver origin (KRX kind 목록).
        Freshness:
            - KIND 갱신 시점.
        Dataflow:
            - corpName → ListingResolver → name 인덱스 → 본 함수.
        TargetMarkets:
            - KR.
    """
    return _listingResolver().nameToCode(corpName)


def getKindList(*, forceRefresh: bool = False):
    """ListingResolver 경유 KIND 상장법인 목록.

    Args:
        forceRefresh: 캐시 무시.

    Returns:
        상장법인 DataFrame.

    Raises:
        없음.

    Example:
        >>> getKindList(forceRefresh=False)

    LLM Specifications:
        AntiPatterns:
            - forceRefresh=True 빈번 호출 → KRX 부하. 일 1 회 충분.
            - 전체 DataFrame 그대로 LLM 컨텍스트 → 2000+ row 토큰 폭증. searchName 활용.
        OutputSchema:
            - pl.DataFrame - 컬럼 [stockCode, corpName, market, sector, ...].
        Prerequisites:
            - 인터넷 + KRX KIND endpoint.
        Freshness:
            - 호출 시점 또는 cache (forceRefresh=False).
        Dataflow:
            - KRX KIND → ListingResolver.kindList → 본 함수.
        TargetMarkets:
            - KR (KOSPI + KOSDAQ + KONEX 전체 상장).
    """
    return _listingResolver().kindList(forceRefresh=forceRefresh)


def searchName(keyword, *, limit: int | None = None):
    """ListingResolver 경유 회사명 검색.

    Args:
        keyword: 회사명 substring.
        limit: 최대 행 수. None 이면 무제한 (룰 8 - None 은 keyword 만족용 explicit opt-out).

    Returns:
        매칭 DataFrame 또는 None.

    Example:
        >>> searchName("삼성", limit=10)

    Raises:
        없음.

    SeeAlso:
        - ``nameToCode`` - 정확 매치.
        - ``iterName`` - 같은 결과의 row-level generator.
        - ``Company.search`` - Company 라우터 패리티 인터페이스.

    Requires:
        - dartlab
        - polars

    Capabilities:
        - corpName 컬럼에 keyword substring 매칭하는 row 반환. KRX KIND 의 전체 상장사 대상.
          정확 매칭 없으면 부분 매칭 fallback.

    Guide:
        - "삼성 들어간 회사 다 찾기" → ``searchName("삼성")``.
        - "상위 10 건만" → ``searchName("삼성", limit=10)``.

    AIContext:
        AI 가 사용자 "○○ 회사" 모호 입력 받았을 때 후보 추출. limit 명시로 토큰 절약 의무.

    LLM Specifications:
        AntiPatterns:
            - limit 없이 짧은 keyword ("주") → 수백 row 반환. 항상 limit 명시.
            - 영문 keyword → KIND 가 한국어 corpName origin 이라 매치 X.
        OutputSchema:
            - pl.DataFrame [stockCode, corpName, market, sector, ...] 또는 None.
        Prerequisites:
            - ListingResolver origin (KIND kindList cache).
        Freshness:
            - KIND 갱신 시점.
        Dataflow:
            - keyword → ListingResolver.search → kindList substring filter → head(limit).
        TargetMarkets:
            - KR.
    """
    df = _listingResolver().search(keyword)
    if df is not None and limit is not None:
        df = df.head(limit)
    return df


def iterName(keyword, *, limit: int | None = None):
    """``searchName`` 의 iterator pair (룰 10) - row-level 스트리밍.

    Args:
        keyword: 회사명 substring.
        limit: 최대 행 수. None 이면 무제한.

    Yields:
        row dict.

    Raises:
        없음 (ListingResolver 부재 시 빈 generator).

    Example:
        >>> for row in iterName("삼성", limit=10):
        ...     print(row["corp_name"])

    SeeAlso:
        - ``searchName`` - 같은 결과의 DataFrame 버전.

    Requires:
        - dartlab
        - polars

    Capabilities:
        - ``searchName`` 결과를 row dict 단위 generator 로 streaming. 대량 회사 looping 시 메모리 절약.

    Guide:
        - "대량 회사 순차 처리" → ``for row in iterName(kw):``.

    AIContext:
        AI 의 자동 batch 처리 - 결과 row 하나씩 회사 분석 dispatch. searchName 보다 lazy.

    LLM Specifications:
        AntiPatterns:
            - generator 소진 후 재호출 → 새 generator (정상 동작).
            - generator → list() 즉시 변환 시 searchName 과 동등. iterName 의 streaming 이점 사라짐.
        OutputSchema:
            - generator[dict] - row dict 시리즈.
        Prerequisites:
            - ``searchName`` 과 동일.
        Freshness:
            - ``searchName`` 과 동일.
        Dataflow:
            - searchName(keyword, limit) → df.iter_rows(named=True) → 본 generator.
        TargetMarkets:
            - KR.
    """
    df = searchName(keyword, limit=limit)
    if df is None:
        return
    yield from df.iter_rows(named=True)


from dartlab.providers.dart.accessor.financeAccessor import _FinanceAccessor
from dartlab.providers.dart.accessor.profileAccessor import _ProfileAccessor
from dartlab.providers.dart.accessor.reportAccessor import _ReportAccessor
from dartlab.providers.dart.checks import (
    _ensureAllData,
    _importAndCall,
    _isPeriodColumn,
    _shapeString,
)
from dartlab.providers.dart.financeMappers import (
    _RATIO_TEMPLATE_FIELDS,
    _ratioArchetypeOverrideForIndustryGroup,
    _ratioResultHasHeadlineSignal,
    _ratioSeriesToDataFrame,
    _ratioTemplateKeyForIndustryGroup,
    _shouldFallbackToAnnualRatios,
)
from dartlab.providers.dart.notes import Notes

# 플러그인 등록 후 재구축 가능하도록 lazy 초기화
_MODULE_REGISTRY: list[tuple[str, str, str, Any]] | None = None
_MODULE_INDEX: dict[str, int] | None = None
_ALL_PROPERTIES: list[tuple[str, str]] | None = None


def _getModuleRegistry() -> list[tuple[str, str, str, Any]]:
    """lazy 모듈 레지스트리 - 최초 접근 시 구축."""
    global _MODULE_REGISTRY, _MODULE_INDEX
    if _MODULE_REGISTRY is None:
        _MODULE_REGISTRY = [
            # finance 재무제표 - panel-only 전환 후 finance/ 경로가 XBRL 재무 SSOT.
            ("dartlab.providers.dart.finance.statements", "statements", "재무제표", None),
        ] + [(e.modulePath, e.funcName, e.label, e.extractor) for e in _getModuleEntries()]
        _MODULE_INDEX = {entry[1]: i for i, entry in enumerate(_MODULE_REGISTRY)}
    return _MODULE_REGISTRY


def _getModuleIndex() -> dict[str, int]:
    """lazy 모듈 인덱스 - 최초 접근 시 구축."""
    global _MODULE_INDEX
    if _MODULE_INDEX is None:
        _getModuleRegistry()
    return _MODULE_INDEX  # type: ignore[return-value]


def _getAllProperties() -> list[tuple[str, str]]:
    """lazy all() 순서 목록 - 최초 접근 시 구축."""
    global _ALL_PROPERTIES
    if _ALL_PROPERTIES is None:
        _ALL_PROPERTIES = [
            ("BS", "재무상태표"),
            ("IS", "손익계산서"),
            ("CF", "현금흐름표"),
        ]
        for entry in _getModuleRegistry():
            name = entry[1]
            if name in ("fsSummary", "statements", "companyOverview"):
                continue
            _ALL_PROPERTIES.append((name, entry[2]))
    return _ALL_PROPERTIES


def rebuildModuleRegistry() -> None:
    """플러그인 등록 후 호출 - 모듈 레지스트리 캐시 무효화.

    Raises:
        없음.

    Example:
        >>> rebuildModuleRegistry()

    SeeAlso:
        - ``_getModuleRegistry`` - 실 lazy 재구축 함수.
        - ``listExportModules`` / ``iterExportModules`` - registry 소비자.

    Requires:
        - dartlab
        - polars

    Capabilities:
        - 외부 플러그인 (skill / new docs module) 등록 후 ``_MODULE_REGISTRY`` / ``_MODULE_INDEX`` /
          ``_ALL_PROPERTIES`` 3 캐시 invalidate. 다음 호출부터 새 module 인지.

    Guide:
        - "새 플러그인 추가 후 즉시 인식" → 본 함수 호출 후 ``c.panel(newTopic)``.

    AIContext:
        AI 가 새 module 추가 후 즉시 c.show 호출 시 본 함수 자동 호출 의무. 자동 dispatch 회로.
    """
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


# Q1.1 (2026-04-21): `_REPORT_TOPIC_TO_API_TYPE` / `_API_TYPE_TO_TOPIC` 하드코딩
# dict 제거. registry DataEntry.apiType 필드로 단일 출처화.
# topic ↔ DART API apiType 변환은 아래 두 헬퍼 하나로.


def _apiTypeForTopic(topic: str) -> str:
    """topic → DART API apiType. registry entry 의 apiType 이 있으면 그걸, 없으면 topic 그대로."""
    from dartlab.core.registry import getEntry

    entry = getEntry(topic)
    if entry is not None and entry.apiType:
        return entry.apiType
    return topic


def _topicForApiType(apiType: str) -> str:
    """DART API apiType → user-facing topic. registry 에서 역탐색.

    registry 에서 apiType 필드가 매치되는 entry 찾아 name 리턴. 없으면 apiType 그대로.
    """
    from dartlab.core.registry import getModuleEntries

    for e in getModuleEntries():
        if e.apiType and e.apiType == apiType:
            return e.name
    return apiType


# ── 재무제표 약칭 (AI-친화 layer) ──────────────────────────────────
# AI 가 흔히 시도하는 영문 lower-case / 복수형 / 합성어 → canonical 재무제표 topic.
# Business alias (board/pay/tangible 등 → 해당 topic) 는 registry.resolveAlias() 로
# 이관 (2026-04-21 Q1.4). 여기는 핵심 4 재무제표의 case-insensitive 변형만 유지.
_AI_CASE_ALIAS: dict[str, str] = {
    "cashflow": "CF",
    "cashflows": "CF",
    "cf": "CF",
    "incomestatement": "IS",
    "is": "IS",
    "pl": "IS",
    "profitloss": "IS",
    "balancesheet": "BS",
    "bs": "BS",
    "comprehensiveincome": "CIS",
    "cis": "CIS",
    "equitychanges": "SCE",
    "sce": "SCE",
}


def _resolveTopic(topic: str) -> str:
    """topic 또는 alias → canonical topic name.

    순서: (1) AI-친화 lowercase 변형, (2) registry business alias, (3) 그대로.
    """
    if topic in _AI_CASE_ALIAS:
        return _AI_CASE_ALIAS[topic]
    from dartlab.core.registry import resolveAlias

    return resolveAlias(topic)


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


def _filterPeriodColumnsByAsOf(df: "pl.DataFrame", asOf: str) -> "pl.DataFrame":
    """asOf 이후 fiscal period 컬럼/행 drop - look-ahead bias 방지.

    DART 재무제표 finance topic 의 horizontal view 는 컬럼명이 fiscal period
    (예: "2025Q4", "2024", "2023Q3"). 사용자가 시점 X 분석 재현 시 X 이후
    컬럼은 미래 정보 누설.

    asOf 형식: "YYYY-MM-DD" / "YYYYQn" / "YYYY". 컬럼 헤더가 fiscal period
    pattern 이면 비교, 아니면 그대로 유지 (snakeId / 항목 같은 metadata 컬럼).
    """
    asof_year, asof_quarter = _parseAsof(asOf)
    if asof_year is None:
        return df
    keepCols: list[str] = []
    for col in df.columns:
        col_year, col_quarter = _parseAsof(col)
        if col_year is None:
            keepCols.append(col)
            continue
        if col_year < asof_year:
            keepCols.append(col)
        elif col_year == asof_year and (col_quarter is None or asof_quarter is None or col_quarter <= asof_quarter):
            keepCols.append(col)
    return df.select(keepCols) if len(keepCols) < len(df.columns) else df


def _parseAsof(value: str) -> tuple[int | None, int | None]:
    """fiscal period or ISO date → (year, quarter or None). 미인식 → (None, None)."""
    import re as _re

    raw = str(value or "").strip()
    if not raw:
        return None, None
    m = _re.match(r"^(\d{4})[Qq]([1-4])$", raw)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = _re.match(r"^(\d{4})-(\d{1,2})-\d{1,2}$", raw)
    if m:
        month = int(m.group(2))
        return int(m.group(1)), (month - 1) // 3 + 1
    m = _re.match(r"^(\d{4})$", raw)
    if m:
        return int(m.group(1)), None
    return None, None


def listExportModules(*, limit: int | None = None) -> list[tuple[str, str]]:
    """Excel/export 용 DART 공개 모듈 목록.

    Args:
        limit: 최대 항목 수. None 이면 무제한.

    Returns:
        ``(prop, label)`` 튜플 리스트 - Excel export 컬럼명 생성용. prop 은 Company
        속성명 (예 ``"businessOverview"``), label 은 사용자 표시용 한글 라벨.

    Example:
        >>> listExportModules(limit=20)

    Raises:
        없음.

    SeeAlso:
        - ``iterExportModules`` - 같은 결과 generator pair.
        - ``rebuildModuleRegistry`` - registry 캐시 갱신.

    Requires:
        - dartlab
        - polars

    Capabilities:
        - ``_ALL_PROPERTIES`` (BS/IS/CF + docs/report module 명) 전체 list 반환. AI 가 사용자에게
          "이 회사 어떤 데이터 가능" 카탈로그 답변 시 origin.

    Guide:
        - "사용 가능 module 목록" → ``listExportModules()``.

    AIContext:
        workbench introspection - Company 이 가진 attribute (BS/IS/dividend/employee 등) 카탈로그.

    LLM Specifications:
        AntiPatterns:
            - limit 없이 노출 → 30+ 항목, 토큰 부담. UI 한정 표시.
            - registry 변경 직후 호출 → 캐시 stale 가능. rebuildModuleRegistry 선행 의무.
        OutputSchema:
            - list[tuple[str, str]] - (propName, 한국어 라벨) pair.
        Prerequisites:
            - _MODULE_REGISTRY 초기화 완료.
        Freshness:
            - registry 변경 시점 (플러그인 등록 시).
        Dataflow:
            - _getAllProperties → 본 함수 → head(limit).
        TargetMarkets:
            - KR (DART 정기보고서 module 라벨).
    """
    items = list(_getAllProperties())
    if limit is not None:
        items = items[:limit]
    return items


def iterExportModules(*, limit: int | None = None):
    """``listExportModules`` 의 iterator pair (룰 10).

    Args:
        limit: 최대 항목 수. None 이면 무제한.

    Yields:
        ``(prop, label)`` 튜플.

    Raises:
        없음.

    Example:
        >>> for prop, label in iterExportModules(limit=20):
        ...     print(prop, label)

    SeeAlso:
        - ``listExportModules`` - 같은 결과 list 버전.

    Requires:
        - dartlab
        - polars

    Capabilities:
        - ``_ALL_PROPERTIES`` 의 streaming generator. 대량 module 순회 시 list 적재 없이 lazy.

    Guide:
        - "module 별 처리 streaming" → ``for prop, label in iterExportModules():``.

    AIContext:
        AI 의 자동 module-by-module dispatch 시 메모리 절약 - 한 번에 1 module 처리.

    LLM Specifications:
        AntiPatterns:
            - list() 즉시 변환 → listExportModules 와 동등. streaming 이점 없어짐.
        OutputSchema:
            - generator[tuple[str, str]].
        Prerequisites:
            - ``listExportModules`` 와 동일.
        Freshness:
            - ``listExportModules`` 와 동일.
        Dataflow:
            - _getAllProperties → enumerate + limit → 본 generator.
        TargetMarkets:
            - KR.
    """
    for i, item in enumerate(_getAllProperties()):
        if limit is not None and i >= limit:
            return
        yield item


class Company:
    """DART 기반 한국 상장기업 분석.

    기본 사용 모델은 index / show / trace다.

    - ``index``: sections 뼈대 위에 finance/report가 채워진 수평화 보드
    - ``show(topic)``: 특정 topic의 실제 payload(DataFrame)
    - ``trace(topic, period)``: 선택 source와 provenance

    3개 데이터 소스를 강점 기반으로 선별하여 제공:

    - **finance** (XBRL 정규화): BS/IS/CIS/CF/SCE, timeseries, annual, ratios
    - **report** (DART API 정형): 28개 apiType 체계, 현재 가용 항목 중심 structured disclosure
    - **panel** (공시 수평화): 서술형(business, mdna), K-IFRS 주석(notes), 거버넌스, 리스크 등

    소스 우선순위:
    - panel 수평화가 구조의 spine
    - finance가 숫자 재무 authoritative source
    - report가 정형 공시 authoritative source
    - Company는 이 세 source를 merged board로 제공한다

    Example::

        c = Company("005930")           # 삼성전자
        c.index                          # 전체 수평화 보드
        c.panel("BS")                     # 재무상태표
        c.panel("salesOrder")             # sections 기반 subtopic DataFrame
        c.panel("costByNature")           # sections/detailTopic 우선 + legacy fallback
        c.trace("dividend")              # source provenance
        c.panel("CIS")                    # 포괄손익계산서
        c.panel("SCE")                    # 자본변동표
        c.panel("treasuryStock")          # 정형 공시
        c.panel("sections")              # panel source view

    Notes
    -----
    **첫 호출 시간** - Company(stockCode) 최초 호출은 해당 종목의 panel /
    finance / report parquet 를 HuggingFace 에서 자동 다운로드한다 (총
    ~수MB ~ 수십MB). 네트워크 속도에 따라 **30~60초** 소요. 2회째부터는
    로컬 캐시 사용 - 즉시 반환.

    Company 편의성 3원칙 (CLAUDE.md) 중 "속도 - 첫 호출 5초 이내" 는 캐시
    적중 기준. cold start (캐시 없음) 는 다운로드 시간 포함이며 진행 상황
    은 기본 INFO 레벨 logger 로 출력 (silence: ``logging.getLogger("dartlab").setLevel(WARNING)``).
    """

    @staticmethod
    def canHandle(code: str) -> bool:
        """DART 종목코드(6자) 또는 한글 회사명이면 처리 가능.

        Parameters
        ----------
        code : str
            종목코드 또는 회사명 후보.

        Returns
        -------
        bool
            True 면 DART provider 로 처리. 6자리 alphanumeric (KR 종목코드)
            또는 한글 포함 문자열이면 True.

        Raises:
            없음.

        Example:
            >>> Company("005930").canHandle()

        Args:
            code: 종목코드/회사명 후보 문자열.

        Returns:
            bool - DART 처리 가능 여부.

        SeeAlso:
            - ``edgar.Company.canHandle`` - US ticker 패리티.
            - ``priority`` - 라우터 정렬 SSOT.

        Requires:
            - dartlab
            - polars

        Capabilities:
            - 6 자리 alphanumeric (KR stockCode) 또는 한글 (회사명) 매칭. EDGAR 의 5 자리 영문 ticker
              와 disjoint - 라우터 정확 dispatch.

        Guide:
            - "DART 처리 가능 코드냐" → 본 함수.

        AIContext:
            Company 팩토리 내부. AI 가 직접 호출 X - Company() 가 자동 dispatch.

        LLM Specifications:
            AntiPatterns:
                - 영문 5 자 ticker (예 "AAPL") → False - EDGAR 가 처리.
                - 빈 문자열 → False (re.match 실패).
                - 6 자리지만 영문 only (예 "ABCDEF") → True 가능 - KRX KIND lookup 시 실 매치 필요.
            OutputSchema:
                - bool.
            Prerequisites:
                - 입력이 str.
            Freshness:
                - 정적 패턴.
            Dataflow:
                - 사용자 입력 → Company() → 본 함수 → DART 분기 결정.
            TargetMarkets:
                - KR (KOSPI/KOSDAQ/KONEX).
        """
        if re.match(r"^[0-9A-Za-z]{6}$", code):
            return True
        if any("\uac00" <= ch <= "\ud7a3" for ch in code):
            return True
        return False

    @staticmethod
    def priority() -> int:
        """낮을수록 먼저 시도. DART=10 (기본 provider).

        Returns
        -------
        int
            provider 우선순위. DART 는 10 - EDGAR (20) 보다 먼저 시도.

        Raises:
            없음.

        Example:
            >>> Company("005930").priority()

        Returns:
            int 상수 10 (DART = primary).

        LLM Specifications:
            AntiPatterns:
                - 본 상수 외부에서 hard-code 비교 - 라우터 순서 변경 시 회귀.
            OutputSchema:
                - int 상수 10.
            Prerequisites:
                - 없음.
            Freshness:
                - 라우터 SSOT 변경 시.
            Dataflow:
                - Company 팩토리 → 본 함수 → provider 우선순위 정렬.
            TargetMarkets:
                - KR - primary provider.
        """
        return 10

    def __init__(self, stockCode: str):
        """DART KR Company 인스턴스 초기화 - stockCode 해석 + parquet 캐시 + accessor 5 종 셋업.

        Args:
            stockCode: 6 자리 종목코드 (``"005930"``) 또는 한글 회사명 (``"삼성전자"``).
                회사명은 ``nameToCode`` 가 KIND 매핑으로 6 자리 코드로 해석. 6 자리
                ``[0-9A-Za-z]`` 직매칭이 우선이며, 그 외 입력은 회사명 path 로 fallback.

        Returns:
            None (생성자).

        Raises:
            ValueError: ``stockCode`` 가 KIND 매핑/parquet 어디에도 없을 때
                (``"'X'에 해당하는 종목을 찾을 수 없음"``) 또는 panel/finance/report
                parquet 셋 다 부재 시 ``emit("error:no_data", raiseAs=ValueError)``.

        Example:
            >>> from dartlab.providers.dart.company import Company
            >>> c = Company("005930")
            >>> c.corpName
            '삼성전자'

        SeeAlso:
            - ``nameToCode`` - 한글명 → 6 자리 코드 매핑 (ListingResolver).
            - ``__enter__`` / ``__exit__`` - context manager + OomTripwire + cleanupCache.
            - ``_ensureAllData`` - panel/finance/report parquet 셋 verify.

        Requires:
            - polars
            - dartlab.core.memory.BoundedCache (30 entry cap)
            - dartlab.providers.dart.accessor.* (Notes/Profile/Finance/Report)
            - dartlab.core.dataLoader.loadData (corpName 추출)

        Capabilities:
            - 단일 한국 상장사 facade 진입점 - panel/finance/report 통합 access.
            - lazy finance - 첫 ``c.finance.*`` 접근 시 parquet load.
            - pyodide-aware - emscripten 에선 corpName 을 stockCode 로 폴백 (네트워크 비용 회피).

        Guide:
            - "삼성전자 분석" → ``Company("005930")``.
            - "회사명만 알 때" → ``Company("삼성전자")``.
            - "다종목 순회" → ``with Company(code) as c: ...`` 패턴 강제 (OomTripwire).

        AIContext:
            Ask Workbench Company facade - LLM 이 첫 호출하는 KR provider 엔트리.
            ``co.panel(topic)`` / ``co.search(query)`` 등 모든 후속 호출의 self.

        LLM Specifications:
            AntiPatterns:
                - 4 자리/7 자리/8 자리 코드 호출 → ValueError. KR stockCode 는 6 자리 strict.
                - ``Company(code)`` 한 인스턴스로 다종목 처리 시도 - 종목당 신규 Company 강제.
                - ``with`` 누락 다종목 루프 → Polars Rust heap 누적 → OOM (cleanupCache 미호출).
                - 한글 외 다국어 회사명 (Samsung/サムスン) → KIND 미매치 → ValueError.
            OutputSchema:
                - Company 인스턴스 - ``stockCode`` (str 6 upper) / ``corpName`` (str)
                  / ``_cache`` (BoundedCache 30) / ``_hasPanel/_hasFinanceParquet/_hasReport`` (bool).
                - 내부 accessor: ``_finance`` (FinanceAccessor)
                  / ``_report`` (ReportAccessor) / ``_profileAccessor`` / ``_notesAccessor`` (panel 있을 때만).
            Prerequisites:
                - KIND 룩업 캐시 또는 HuggingFace origin 다운로드 권한 (cold start 가능).
                - ``_ensureAllData`` 가 panel/finance/report parquet 확인 - 하나라도 있으면 통과.
            Freshness:
                - 초기화 wall-clock ≥ 2.0s 시 INFO log (HF cold start 추적).
                - panel freshness 는 ``_checkDartDocsFreshness`` 가 trailing date 와 비교 후
                  stale 시 ``_freshnessResult`` 에 warning record.
                - KIND 매핑은 ListingResolver TTL (일 단위).
            Dataflow:
                - stockCode (raw) → ``nameToCode`` (회사명 path) → 6 자리 정규화
                - → ``_ensureAllData`` (panel/finance/report parquet existence check)
                - → BoundedCache(30) + 5 accessor 인스턴스화 → Company.
            TargetMarkets:
                - KR (DART) - KOSPI/KOSDAQ/KONEX 등록 종목 한정. 비상장/외국주 X.
        """
        import time as _time

        _initStart = _time.perf_counter()

        normalized = stockCode.strip()
        if re.match(r"^[0-9A-Za-z]{6}$", normalized):
            self.stockCode = normalized.upper()
        else:
            code = nameToCode(normalized)
            if code is None:
                raise ValueError(f"'{normalized}'에 해당하는 종목을 찾을 수 없음")
            self.stockCode = code
        from dartlab.core.memory import BoundedCache

        self._cache: BoundedCache = BoundedCache(maxEntries=30)

        _dataStatus = _ensureAllData(self.stockCode)
        self._hasPanel = _dataStatus.get("panel", False)
        self._freshnessResult = None
        self._hasFinanceParquet = _dataStatus.get("finance", False)
        self._hasReport = _dataStatus.get("report", False)

        import sys

        corpName = None if sys.platform == "emscripten" else codeToName(self.stockCode)
        if corpName:
            self.corpName = corpName
        elif sys.platform == "emscripten":
            # pyodide: panel 선행 fetch 회피 - 사용자가 요청한 카테고리만 lazy fetch.
            # 진짜 corpName 이 필요하면 show/select 가 나중에 panel 을 가져옴.
            self.corpName = self.stockCode
        else:
            self.corpName = self.stockCode

        # finance는 lazy - 첫 접근 시 _ensureFinanceLoaded()에서 검증
        self._financeChecked = False

        if not self._hasPanel and not self._hasFinanceParquet and not self._hasReport:
            from dartlab.core.messaging import emit

            emit("error:no_data", stockCode=self.stockCode, raiseAs=ValueError)

        self._hintedKeys: set[str] = set()  # 동일 안내 반복 방지

        self._notesAccessor = Notes(self) if self._hasPanel else None
        # public namespace 모두 제거 (P3a/b/c/d)
        self._profileAccessor = _ProfileAccessor(self)
        # private 백엔드 - 내부 compute 전용 (story/credit/valuation 등). panel-only로 docs accessor 은퇴.
        self._finance = _FinanceAccessor(self)
        self._report = _ReportAccessor(self)

        # 초기화 wall-clock - 2초 이상이면 사용자에게 총 시간 보고 (cold start
        # 시 HF 다운로드 포함. Company 편의성 3원칙 "첫 호출 5초 이내" 감시).
        _initElapsed = _time.perf_counter() - _initStart
        if _initElapsed >= 2.0:
            _log.info("Company('%s') 준비 완료 (%.1fs)", self.stockCode, _initElapsed)

    def __repr__(self):
        from dartlab.core.htmlRenderer import getHtmlRenderer

        renderer = getHtmlRenderer()
        if renderer is not None:
            text = renderer.renderCompany(self)
            if text is not None:
                return text
        return f"Company({self.stockCode}, {self.corpName})"

    @property
    def report(self):
        """정형 report accessor 하위호환 alias.

        Returns:
            _ReportAccessor: DART 정형 report accessor.

        Raises:
            없음.

        Example:
            >>> c = Company("005930")
            >>> c.report is not None
            True
        """
        return self._report

    def _hintOnce(self, key: str, prop: str, category: str = "panel") -> None:
        """동일 안내를 세션 내 1회만 출력."""
        if key in self._hintedKeys:
            return
        self._hintedKeys.add(key)
        from dartlab.core.messaging import emit

        emit(f"hint:no_{category}", stockCode=self.stockCode, prop=prop)

    def _financeProperty(self, name: str):
        """finance accessor 위임 + hint."""
        result = getattr(self._finance, name)
        if result is None:
            self._hintOnce(name, name, "finance")
        return result

    # ── P7: Company context manager + 메모리-safe surface (룰 11 + MemorySafeProvider) ──

    def __enter__(self) -> "Company":
        """context manager 진입 - OomTripwire 시작 + self 반환.

        M5: OomTripwire 가 background watcher 로 RSS 폴링,
        EMERGENCY 초과 시 kernel OOM-kill 전에 graceful 종료.

        Example:
            with Company("005930") as c:
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

        룰 11 만족. Polars 네이티브 힙 누수 차단.

        Args:
            excType: 예외 type (정상 종료 시 None).
            excVal: 예외 인스턴스.
            excTb: traceback.

        Raises:
            없음 (cleanup 실패 silent).
        """
        try:
            tw = getattr(self, "_oomTripwire", None)
            if tw is not None:
                tw.stop()
        except (AttributeError, RuntimeError):
            pass  # tripwire 정지 실패 silent
        try:
            self.cleanupCache()
        except (AttributeError, KeyError, RuntimeError):
            pass  # cleanup 실패는 silent - 정상 종료 우선

    def cleanupCache(self) -> int:
        """BoundedCache 전체 evict + cleanupBetweenCompanies 실행.

        MemorySafeProvider Protocol 구현. with Company(c) 종료 시 자동 호출.

        Returns:
            evict 된 cache entry 수.

        Example:
            >>> c = Company("005930")
            >>> c.panel("IS")
            >>> n = c.cleanupCache()
            >>> print(f"evicted {n} entries")

        Raises:
            없음 (cleanupBetweenCompanies 가 내부 silent).

        SeeAlso:
            - ``memorySnapshot`` - 호출 전/후 RSS 비교.
            - ``__exit__`` - context manager 종료 시 본 함수 자동 호출.
            - ``dartlab.core.memory.cleanupBetweenCompanies`` - Polars Rust heap 회수.

        Requires:
            - dartlab
            - polars

        Capabilities:
            - 인스턴스 ``self._cache`` (BoundedCache) 의 모든 entry evict + Polars 네이티브 힙
              ``cleanupBetweenCompanies`` 호출. KR multi-company loop 사이 회수.

        Guide:
            - "다음 종목 진입 전 메모리 회수" → 본 함수 또는 ``with Company(c):`` 컨텍스트.

        AIContext:
            AI 가 다종목 batch (50+ 종목 분석) 안 본 함수 의무 호출. 누락 시 Rust heap 누적 OOM.

        LLM Specifications:
            AntiPatterns:
                - 호출 없이 다종목 순회 → Polars 힙 누적 → OOM.
                - ``gc.collect()`` 만 호출 → Rust heap 회수 X. 본 함수 필수.
            OutputSchema:
                - int - evict 된 entry 수.
            Prerequisites:
                - 인스턴스 활성 상태.
            Freshness:
                - 호출 시점 즉시.
            Dataflow:
                - self._cache → clear → cleanupBetweenCompanies(label) → Rust heap.
            TargetMarkets:
                - KR - 본 클래스 인스턴스.
        """
        from dartlab.core.memory import cleanupBetweenCompanies

        evicted = len(self._cache)
        self._cache.clear()
        cleanupBetweenCompanies(label=f"{self.stockCode}_exit")
        return evicted

    def memorySnapshot(self) -> dict[str, int]:
        """캐시 size + 현 RSS snapshot.

        MemorySafeProvider Protocol 구현.

        Returns:
            keys: "cacheSize" (BoundedCache entry 수), "rssMb" (현 RSS MB).

        Example:
            >>> c = Company("005930")
            >>> c.memorySnapshot()
            {'cacheSize': 12, 'rssMb': 450}

        Raises:
            없음.

        SeeAlso:
            - ``cleanupCache`` - 본 함수가 보여준 RSS 회수.
            - ``dartlab.core.memory.getMemoryMb`` - psutil 기반 RSS.

        Requires:
            - dartlab
            - polars

        Capabilities:
            - ``self._cache`` entry 수 + 현 프로세스 RSS (MB) dict 합산. MemorySafeProvider Protocol entry.

        Guide:
            - "이 회사가 메모리 얼마 쓰나" → 본 함수.
            - "cleanupCache 효과 확인" → 호출 전/후 비교.

        AIContext:
            OOM tripwire 발동 직전 본 함수로 회사별 메모리 분포 보고 + AI 가 cleanup 결정.

        LLM Specifications:
            AntiPatterns:
                - RSS 절대값 환경 간 비교 X (Windows vs WSL 차이) - 동일 환경 내 추세만.
                - cacheSize 0 == 메모리 정리 완료 X. Polars Rust heap 별도 영역.
            OutputSchema:
                - dict {"cacheSize": int, "rssMb": int}.
            Prerequisites:
                - psutil (getMemoryMb 의존).
            Freshness:
                - 호출 시점.
            Dataflow:
                - psutil RSS + self._cache len → 본 함수.
            TargetMarkets:
                - KR - 본 클래스 인스턴스 추적.
        """
        from dartlab.core.memory import getMemoryMb

        return {"cacheSize": len(self._cache), "rssMb": int(getMemoryMb())}

    def topicSummaries(self) -> dict[str, str]:
        """토픽별 요약 dict - AI가 경로 탐색에 사용.

        각 panel text topic의 최신 기간 첫 텍스트에서 200자 요약을 추출한다.
        finance topic은 고정 설명을 반환한다.

        Returns
        -------
        dict[str, str]
            키 = topic 이름 (예: "BS", "IS", "dividend", "companyOverview")
            값 = 200자 요약 텍스트

        Raises:
            없음.

        Returns:
            dict[str, str] - topic → 200 자 요약 텍스트.

        SeeAlso:
            - ``topics`` - DataFrame 카탈로그.
            - ``index`` - topic 메타 보드.
            - ``panel`` - 공시 본문/표 원본 격자.

        Requires:
            - dartlab
            - polars

        Capabilities:
            - finance 6 topic 은 고정 한국어 설명 + panel text topic 은 최신 본문 첫 200 자 요약 합산.
              AI 가 topic 라우팅 결정 시 (어느 topic 사용자 질문에 해당?) 의 origin.

        Guide:
            - "이 회사 어떤 데이터 어떤 내용 담고 있나" → 본 함수.

        AIContext:
            workbench query routing - 사용자 자연어 → topic 선택 시 본 dict 으로 후보 좁힘.

        LLM Specifications:
            AntiPatterns:
                - 200 자 cap → 본문 전체 가정 X - 자세히는 show() 호출 의무.
                - 본 함수 결과는 cache - 새 보고서 업데이트 시 새 인스턴스 만들어야.
            OutputSchema:
                - dict[str, str] - topic 이름 → 한국어 요약 (≤ 200 자).
            Prerequisites:
                - panel text (선택) + finance topic 카탈로그.
            Freshness:
                - 인스턴스 cache - 동일 인스턴스 lifetime 동안 고정.
            Dataflow:
                - finance summaries (고정) + panel latest text 200 자 합산.
            TargetMarkets:
                - KR.
        """
        cacheKey = "_topicSummaries"
        if cacheKey in self._cache:
            return self._cache[cacheKey]

        summaries: dict[str, str] = {}

        # finance 고정 설명
        _FINANCE_SUMMARIES = {
            "BS": "재무상태표 - 자산, 부채, 자본 잔액",
            "IS": "손익계산서 - 매출, 영업이익, 당기순이익",
            "CIS": "포괄손익계산서 - 기타포괄손익 포함",
            "CF": "현금흐름표 - 영업/투자/재무 활동 현금",
            "SCE": "자본변동표 - 자본 구성요소별 변동",
            "ratios": "재무비율 - 수익성/안정성/성장성/효율성/밸류에이션",
        }
        summaries.update(_FINANCE_SUMMARIES)

        # panel topic 요약 - 최신 기간 첫 텍스트 200자
        textWide = self._panelTextWide() if self._hasPanel else None
        if textWide is not None and not textWide.is_empty():
            periodCols = sorted(
                [c for c in textWide.columns if _isPeriodColumn(c)],
                reverse=True,
            )
            topicCol = "topic" if "topic" in textWide.columns else "sectionLeaf"
            if topicCol in textWide.columns and periodCols:
                seen: set[str] = set()
                for row in textWide.iter_rows(named=True):
                    topic = str(row.get(topicCol) or "").strip()
                    if not topic or topic in seen or topic in summaries:
                        continue
                    for periodCol in periodCols:
                        content = str(row.get(periodCol) or "").strip()
                        if not content:
                            continue
                        preview = content.replace("\n", " ").replace("  ", " ")[:200].strip()
                        if preview:
                            summaries[topic] = preview
                            seen.add(topic)
                        break

        self._cache[cacheKey] = summaries
        return summaries

    @property
    def _hasFinance(self) -> bool:
        """finance 사용 가능 여부 - lazy check 포함."""
        self._ensureFinanceLoaded()
        return self._hasFinanceParquet

    # ── 내부 호출 ──

    def _callModule(self, name: str, **kwargs) -> Any:
        """모듈 호출 + 캐싱. Notes에서도 사용."""
        if not self._hasPanel:
            return None
        cacheKey = f"{name}:{sorted(kwargs.items())}" if kwargs else name
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        idx = _getModuleIndex()[name]
        entry = _getModuleRegistry()[idx]
        result = _importAndCall(entry[0], entry[1], self.stockCode, **kwargs)
        self._cache[cacheKey] = result
        return result

    def _getPrimary(self, name: str, **kwargs) -> Any:
        """모듈 호출 후 primary DataFrame 추출."""
        import dartlab.config as config

        cacheKey = f"{name}:{sorted(kwargs.items())}" if kwargs else name
        idx = _getModuleIndex()[name]
        entry = _getModuleRegistry()[idx]
        label = entry[2]

        if config.verbose and cacheKey not in self._cache:
            _log.info("  ▶ %s · %s", self.corpName, label)

        result = self._callModule(name, **kwargs)
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
            pl.DataFrame - code, name, market, sector 등.

        Requires:
            데이터: listing (자동 다운로드)

        Raises:
            없음.

        Example:
            >>> Company("005930").listing()

        LLM Specifications:
            AntiPatterns:
                - forceRefresh=True 빈번 호출 → KRX 부하.
                - 전체 ~2500 row 그대로 LLM → 토큰 폭증. search 활용.
            OutputSchema:
                - pl.DataFrame - [code, name, market, sector, ...].
            Prerequisites:
                - 인터넷 + KRX KIND endpoint.
            Freshness:
                - KIND 갱신 시점 (일 단위).
            Dataflow:
                - getKindList(forceRefresh) → 본 staticmethod.
            TargetMarkets:
                - KR (KOSPI + KOSDAQ + KONEX).
        """
        return getKindList(forceRefresh=forceRefresh)

    @staticmethod
    def search(keyword: str, *, limit: int | None = None) -> pl.DataFrame:
        """회사명 부분 검색 (KIND 목록 기준).

        Args:
            keyword: 검색어 (부분 일치).
            limit: 최대 행 수. None 이면 무제한.

        Returns:
            pl.DataFrame - 매칭 종목 목록.

        Example:
            >>> Company.search("삼성", limit=10)

        Raises:
            없음.

        LLM Specifications:
            AntiPatterns:
                - limit 없이 흔한 keyword → 수십~수백 row.
                - 영문 keyword → 매치 X (KIND 한국어 origin).
            OutputSchema:
                - pl.DataFrame [stockCode, corpName, market, sector, ...].
            Prerequisites:
                - ListingResolver origin.
            Freshness:
                - KIND 갱신 시점.
            Dataflow:
                - searchName(keyword, limit) → 본 staticmethod.
            TargetMarkets:
                - KR.
        """
        return searchName(keyword, limit=limit)

    @staticmethod
    def resolve(stockCode: str) -> str | None:
        """종목코드 또는 회사명 → 종목코드 변환.

        Args:
            stockCode: 종목코드 ("005930") 또는 종목명 ("삼성전자").

        Returns:
            str | None - 6자리 종목코드. 못 찾으면 None.

        Raises:
            없음.

        Example:
            >>> Company("005930").resolve()

        SeeAlso:
            - ``codeName`` - 반대 (code → name).
            - ``nameToCode`` - module-level 등가.

        Requires:
            - dartlab
            - polars

        Capabilities:
            - 입력이 6 자리 alphanumeric 이면 그대로 (대문자화), 한국어 회사명이면 nameToCode 위임.
              사용자 입력 표준화 entry - KR 종목코드 또는 회사명 양쪽 받는 헬퍼.

        Guide:
            - "사용자 모호 입력 → 표준 종목코드" → 본 함수.

        AIContext:
            AI 가 사용자 발화 "삼성전자" / "005930" 모두 처리 - 일관 stockCode 반환.

        LLM Specifications:
            AntiPatterns:
                - 영문 5 자 → 6 자리 매칭 X → nameToCode 시도 → None. EDGAR 코드는 다른 provider.
                - 회사명 정확 매치만 - 부분 매치는 ``searchName``.
            OutputSchema:
                - str (6 자 대문자) 또는 None.
            Prerequisites:
                - ListingResolver origin.
            Freshness:
                - KIND 갱신 시점.
            Dataflow:
                - 입력 → regex 6 자 검사 → 통과 시 upper, 실패 시 nameToCode.
            TargetMarkets:
                - KR.
        """
        normalized = stockCode.strip()
        if re.match(r"^[0-9A-Za-z]{6}$", normalized):
            return normalized.upper()
        return nameToCode(normalized)

    @staticmethod
    def codeName(stockCode: str) -> str | None:
        """종목코드 → 회사명 변환.

        Args:
            stockCode: 6자리 종목코드.

        Returns:
            str | None - 회사명. 못 찾으면 None.

        Raises:
            없음.

        Example:
            >>> Company("005930").codeName()

        LLM Specifications:
            AntiPatterns:
                - 회사명 입력 → None (반대 방향은 nameToCode).
            OutputSchema:
                - str 회사명 또는 None.
            Prerequisites:
                - ListingResolver origin.
            Freshness:
                - KIND 갱신 시점.
            Dataflow:
                - codeToName(stockCode) → 본 staticmethod.
            TargetMarkets:
                - KR.
        """
        return codeToName(stockCode)

    @staticmethod
    def status() -> pl.DataFrame:
        """로컬에 보유한 전체 종목 인덱스.

        Capabilities:
            - 로컬 데이터 현황 (종목별 panel/finance/report 보유 여부)
            - 최종 업데이트 일시

        Returns:
            pl.DataFrame - 종목코드, 회사명, panel/finance/report 유무, 최종일시.

        Raises:
            없음.

        Example:
            >>> Company("005930").status()

        LLM Specifications:
            AntiPatterns:
                - 전체 status DataFrame LLM 컨텍스트 → 수천 row.
                - 보유 == 최신 가정 X - update() 미실행 시 stale 가능.
            OutputSchema:
                - pl.DataFrame [stockCode, corpName, panel:bool, finance:bool, report:bool, lastUpdated].
            Prerequisites:
                - 로컬 data/ 디렉토리 인덱스 build.
            Freshness:
                - 호출 시점 디스크 스캔.
            Dataflow:
                - data/{docs,finance,report}/*.parquet → buildIndex → 본 staticmethod.
            TargetMarkets:
                - KR - 로컬 보유 종목 카탈로그.
        """
        return buildIndex()

    def filings(self) -> pl.DataFrame | None:
        """공시 문서 목록 + DART 뷰어 링크.

        Capabilities:
            - 로컬에 보유한 공시 문서 목록
            - 기간별, 문서유형별 정리
            - DART 뷰어 링크 포함

        Returns:
            pl.DataFrame | None - year, rceptDate, rceptNo, reportNm, viewerUrl 등.

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
            데이터: panel (자동 다운로드)

        LLM Specifications:
            AntiPatterns:
                - 실시간 공시 확인용으로 사용 (filings 는 local cache - 실시간은 disclosure/liveFilings)
                - readFiling 호출 전 filings 결과의 컬럼명 추측 (rceptNo 사용)
            OutputSchema:
                - rceptNo : str - 공시 접수번호 (readFiling 입력용)
                - filedAt : str - 공시 일자
                - title : str - 공시 제목
                - viewerUrl : str - DART 뷰어 링크
            Freshness:
                local cache 기반. c.update() 호출 시점이 기준.

        Raises:
            없음.

        Example:
            >>> Company("005930").filings()
        """
        from dartlab.providers.dart.builder.filingsCatalog import buildFilings

        return buildFilings(self)

    def update(self, *, categories: list[str] | None = None) -> dict[str, int]:
        """누락된 최신 공시를 증분 수집.

        Capabilities:
            - DART API로 최신 공시 확인 후 누락분만 수집
            - 카테고리별 선택 수집

        Args:
            categories: ["finance", "docs", "report"]. None이면 전체.

        Returns:
            dict - {카테고리: 수집 건수}.

        AIContext:
            - 데이터 최신성 유지에 활용 - 분석 전 자동 갱신 트리거 가능

        Guide:
            - "최신 공시 반영해줘" → c.update()
            - "데이터 업데이트" → c.update()로 증분 수집

        SeeAlso:
            - filings: 현재 보유 공시 목록 확인
            - disclosure: OpenDART 전체 공시 조회

        Requires:
            API 키: DART_API_KEY

        LLM Specifications:
            AntiPatterns:
                - 분석 전 무조건 update() 호출 (이미 최신이면 불필요한 비용)
                - categories 에 "all" 같은 값 (None 또는 list[str] 만)
            OutputSchema:
                - finance : int - 추가 수집된 finance 건수
                - docs : int - 추가 수집된 docs 건수
                - report : int - 추가 수집된 report 건수
            Freshness:
                호출 시점에 DART API 와 비교해 누락만 수집. 매 호출 시점 = 최신 기준.

        Raises:
            없음.

        Example:
            >>> Company("005930").update()
        """
        from dartlab.providers.dart.builder.filingsCatalog import buildUpdate

        return buildUpdate(self, categories=categories)

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
        """**[단일 종목 전용]** OpenDART 공시 목록 조회. **stockCode 필수**.

        ⚠ AI 사용 분기 - 절대 헷갈리지 마라:
            - "**삼성전자** 최근 공시" → ``c.disclosure(stockCode="005930")`` ✅
            - "**최근 자사주 매입 공시 낸 회사**" → ``dartlab.search("자사주 취득")`` (전종목 검색)
            - "**전종목 정기공시 5건**" → ``dartlab.search("사업보고서")`` (전종목 검색)
            - 전종목 검색에 disclosure 호출 금지. stockCode 없이는 실패한다.

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
            pl.DataFrame -- docId, filedAt, title, formType 등 공시 목록 (이 종목 한정).

        Requires:
            API 키: DART_API_KEY

        Example::

            c = Company("005930")
            c.disclosure()                  # 최근 1년 전체 공시
            c.disclosure(days=30)           # 최근 30일
            c.disclosure(type="A")          # 정기공시만
            c.disclosure(keyword="사업보고서")

        AIContext:
            - 특정 종목의 공시 빈도/유형 패턴 → 이벤트 감지
            - 단일 종목 분석 시 최근 공시 컨텍스트 보강용

        Guide:
            - 단일 종목: "삼성전자 최근 공시 뭐 나왔어?" → c.disclosure(days=30)
            - 전종목: "최근 어떤 회사들이 자사주 매입했어?" → dartlab.search("자기주식 취득")

        SeeAlso:
            - dartlab.search: **전종목 공시 검색 - 키워드 기반 (이 함수 대안)**
            - liveFilings: 실시간 최신 공시 (정규화된 포맷, 단일 종목)
            - readFiling: 공시 원문 텍스트 읽기
            - filings: 로컬 보유 공시 목록 (단일 종목)

        LLM Specifications:
            AntiPatterns:
                - 전종목 disclosure() (단일 종목 전용 - 전종목은 dartlab.search())
                - days 와 start/end 동시 (start/end 우선)
            OutputSchema:
                - rceptNo : str - 공시 접수번호 (readFiling 입력용)
                - filedAt : str - 공시 일자 (YYYY-MM-DD)
                - title : str - 공시 제목
                - formType : str - 공시 유형 (정기/주요사항/지분 등)
            Freshness:
                DART API 실시간 (분 단위). filings() 와 다름 (filings 는 local cache).

        Raises:
            없음.
        """
        from dartlab.providers.dart.builder.filingsCatalog import buildDisclosure

        return buildDisclosure(self, start, end, days=days, type=type, keyword=keyword, finalOnly=finalOnly)

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

        LLM Specifications:
            AntiPatterns:
                - 종목코드 외 ticker 전달 (KR DART 전용)
                - keyword 정규식 입력 (단순 substring 만 지원)
            OutputSchema:
                - rceptNo : str - 공시 접수번호 (readFiling 입력용)
                - filedAt : str - 공시 일자
                - title : str - 공시 제목
                - importance : float - 중요도 점수
            Freshness:
                DART API 실시간 (분 단위).
            TargetMarkets:
                - KR

        Raises:
            없음.
        """
        from dartlab.providers.dart.builder.filingsCatalog import buildLiveFilings

        return buildLiveFilings(
            self,
            start,
            end,
            days=days,
            limit=limit,
            keyword=keyword,
            forms=forms,
            finalOnly=finalOnly,
        )

    def readFiling(
        self,
        filing: Any,
        *,
        maxChars: int | None = None,
    ) -> dict[str, Any]:
        """접수번호 또는 liveFilings row로 공시 원문을 읽는다.

        Capabilities:
            - 접수번호(str) 직접 지정 또는 DataFrame row 자동 파싱
            - 전문 텍스트 반환
            - 텍스트 길이 제한 (truncation) 지원

        Args:
            filing: 접수번호(str) 또는 disclosure()/liveFilings() row.
            maxChars: 텍스트 최대 길이.

        Returns:
            dict -- rceptNo, viewerUrl, text 등 원문 정보.

        Requires:
            API 키: DART_API_KEY

        Example::

            c = Company("005930")
            result = c.readFiling("20240315000123")

        AIContext:
            - 공시 원문 텍스트를 LLM 컨텍스트에 주입하여 심층 분석 수행
            - 정기보고서의 topic 단위 분석은 panel catalog 와 c.panel(topic)을 사용

        Guide:
            - "이 공시 내용 보여줘" → c.readFiling(접수번호)
            - "공시 원문 분석해줘" → c.readFiling()으로 원문 확보 후 ask()로 분석
            - "사업보고서 topic 비교" → c.panel(topic)

        SeeAlso:
            - liveFilings: 최신 공시 목록에서 접수번호 확인
            - disclosure: 과거 공시 목록에서 접수번호 확인

        LLM Specifications:
            AntiPatterns:
                - 종목 이름 (str) 을 filing 인자로 전달 (rceptNo 또는 row 만)
                - 정기보고서 topic 분석을 readFiling 원문 분해로 우회
            OutputSchema:
                - rceptNo : str - 공시 접수번호
                - viewerUrl : str - DART 뷰어 링크
                - text : str - 공시 본문
            Freshness:
                DART API 실시간. 단 본문 캐시 없음 - 매 호출 = 새 download.

        Raises:
            없음.
        """
        from dartlab.providers.dart.builder.filingsCatalog import buildReadFiling

        return buildReadFiling(self, filing, maxChars=maxChars)

    # ── 원본 데이터 (property) ──

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
            - XBRL 정규화 전 원본 구조 파악 - 매핑 검증에 활용

        Guide:
            - "원본 재무 데이터 보여줘" → c.rawFinance
            - "XBRL 원본 확인" → c.rawFinance

        SeeAlso:
            - BS: 가공된 재무상태표
            - IS: 가공된 손익계산서
            - panel: 공시 본문/표 원본 격자

        LLM Specifications:
            AntiPatterns:
                - 분석 답변에 raw parquet 직접 인용 (panel("BS") 등 가공본 우선)
                - 매 호출 reload (캐시 - 1 회면 충분)
            OutputSchema:
                - XBRL 정규화 전 원본 - bsns_year / sj_div / account_id / amount 등
            Freshness:
                HuggingFace finance parquet 다운로드 시점.

        Raises:
            없음.
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
            - 정기보고서 API 원본 확인 - report topic 매핑 검증에 활용

        Guide:
            - "원본 보고서 데이터 보여줘" → c.rawReport
            - "정기보고서 원본 확인" → c.rawReport

        SeeAlso:
            - panel: 공시 본문/표 원본 격자
            - rawFinance: 재무제표 원본
            - show: 가공된 topic 데이터 조회

        LLM Specifications:
            AntiPatterns:
                - report 원본을 본문 답변에 직접 인용 (show / story 가공본 우선)
                - 매 호출 reload (캐시 - 1 회면 충분)
            OutputSchema:
                - 정기보고서 API 원본 - 컬럼은 보고서 form 별로 다름
            Freshness:
                HuggingFace report parquet 다운로드 시점.

        Raises:
            없음.
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

    # c.notes property 제거 (Plan v10 P2) - 12 sub-property 모두 c.panel("inventory") 등으로 통합.
    # Notes 클래스는 _notesAccessor (private) 로 유지, show() topic dispatch 가 호출.

    def _safePrimary(self, name: str) -> pl.DataFrame | None:
        try:
            payload = self._getPrimary(name)
        except (KeyError, ValueError, TypeError, FileNotFoundError, AttributeError):
            import logging

            logging.getLogger(__name__).debug("_safePrimary(%s) failed", name, exc_info=True)
            return None
        return payload if isinstance(payload, pl.DataFrame) else None

    def _sceMatrix(self):
        from dartlab.providers.dart.builder.financeStatementBuilder import sceMatrix

        return sceMatrix(self)

    def _sceSeriesAnnual(self):
        from dartlab.providers.dart.builder.financeStatementBuilder import sceSeriesAnnual

        return sceSeriesAnnual(self)

    def _sce(self) -> pl.DataFrame | None:
        from dartlab.providers.dart.builder.financeStatementBuilder import sce

        return sce(self)

    def _financeCisAnnual(self):
        from dartlab.providers.dart.builder.financeStatementBuilder import financeCisAnnual

        return financeCisAnnual(self)

    def _financeCisQuarterly(self):
        from dartlab.providers.dart.builder.financeStatementBuilder import financeCisQuarterly

        return financeCisQuarterly(self)

    def _ratioSeries(self):
        from dartlab.providers.dart.builder.financeStatementBuilder import ratioSeries

        return ratioSeries(self)

    def _financeOrDocsStatement(
        self, sjDiv: str, *, freq: str = "Q", scope: str = "consolidated"
    ) -> pl.DataFrame | None:
        from dartlab.providers.dart.builder.financeStatementBuilder import financeOrDocsStatement

        return financeOrDocsStatement(self, sjDiv, freq=freq, scope=scope)

    # ── 재무제표 (property) ──
    # finance(XBRL) 우선 → docs fallback

    @staticmethod
    def _aggregateCisAnnual(qDf: pl.DataFrame) -> pl.DataFrame | None:
        from dartlab.providers.dart.builder.financeStatementBuilder import aggregateCisAnnual

        return aggregateCisAnnual(qDf)

    def _financeStmt(self, sjDiv: str, *, freq: str = "Q", scope: str = "consolidated") -> pl.DataFrame | None:
        from dartlab.providers.dart.builder.financeStatementBuilder import financeStmt

        return financeStmt(self, sjDiv, freq=freq, scope=scope)

    # c.BS / c.IS / c.CF / c.CIS property 제거 (Plan v10 P0 - api-contract).
    # 사용자는 c.panel("IS") / c.panel("IS", freq="Y", scope="separate") 사용.

    def _panelTextWide(self) -> pl.DataFrame | None:
        """panel text wide view for internal catalog/diff/trace consumers."""
        from dartlab.providers.dart.panel.text import panelTextWide

        return panelTextWide(self.stockCode)

    # docs profile 농장(docsProfileBuilder) 은퇴 - chapter/label 메타는 panel section 카탈로그가 표면.
    # 하위호환 graceful stub: profileTable=None, chapterMap={}, chapter="", label=topic 그대로.
    def _profileTable(self) -> pl.DataFrame | None:
        return None

    def _chapterMap(self) -> dict[str, str]:
        return {}

    def _chapterForTopic(self, topic: str) -> str:
        return ""

    def _topicLabel(self, topic: str) -> str:
        return topic

    def _showFinanceTopic(
        self,
        topic: str,
        *,
        period: str | None = None,
        freq: str = "Q",
        scope: str = "consolidated",
    ) -> pl.DataFrame | None:
        from dartlab.providers.dart.builder.dataDispatcher import showFinanceTopic

        return showFinanceTopic(self, topic, period=period, freq=freq, scope=scope)

    def _traceFinanceTopic(self, topic: str, *, period: str | None = None) -> dict[str, Any] | None:
        from dartlab.providers.dart.builder.dataDispatcher import traceFinanceTopic

        return traceFinanceTopic(self, topic, period=period)

    def _showReportTopic(self, topic: str, *, period: str | None = None, raw: bool = False) -> pl.DataFrame | None:
        from dartlab.providers.dart.builder.dataDispatcher import showReportTopic

        return showReportTopic(self, topic, period=period, raw=raw)

    def _applyPeriodFilter(self, payload: Any, period: str | None) -> Any:
        from dartlab.providers.dart.builder.dataShapeUtils import applyPeriodFilter

        return applyPeriodFilter(payload, period)

    def simulate(
        self,
        *,
        scenario: str = "baseline",
        horizon: int = 3,
        asOf: str | None = None,
    ) -> Any:
        """이 회사에 시나리오 하나를 결정론적으로 돌려 경로·가치를 낸다 (시뮬레이터 엔진).

        매크로 프리셋(baseline/adverse/...) 하나로 ``macro.path -> rev.path -> proforma -> dcf``
        결정론 드라이버 시트를 평가해 시나리오-조건부 매출·마진·FCF 경로 + dcf 주당가치 +
        노드별 근거(provenance/refs/품질/asOf)를 담은 `SimulationResult` 를 낸다. honest-gap:
        결손 leaf·부재 base 지표는 0 이 아니라 None 으로 두고 노드 품질을 ``partial`` 로
        낮춘다. 결정론: 같은 시나리오·asOf 재실행 시 inputsHash 동일.

        Args:
            scenario: 시나리오 id - ``synth.scenario.getPresetScenarios("KR")`` 의 키
                (``"baseline"`` / ``"adverse"`` / ``"severelyAdverse"`` 등).
            horizon: 예측 연수 (기본 3). 프리셋의 실제 경로 길이를 넘길 수 없다.
            asOf: 명시 재무 기간(YYYY 또는 YYYY-Qn). 기간 단위 PIT이며 접수일 vintage 복원 미지원.

        Returns:
            ``SimulationResult`` - 시나리오 경로 + dcf 주당가치 + 노드별 audit + 전체 품질
            (``"ok"`` / ``"partial"``).

        Raises:
            TypeError: scenario 또는 horizon 타입이 잘못됐을 때.
            ValueError: scenario/horizon/asOf 가 지원 범위 밖이거나 시트 배선이 잘못됐을 때.

        Example:
            >>> c = Company("005930")
            >>> r = c.simulate(scenario="baseline")              # doctest: +SKIP
            >>> r.scenarioName, len(r.revenuePath)               # doctest: +SKIP
            ('baseline', 3)
            >>> c.simulate(scenario="adverse").revenuePath[-1] < r.revenuePath[-1]  # doctest: +SKIP
            True

        SeeAlso:
            - ``dartlab.simulate``: 같은 동작의 톱레벨 verb (``dartlab.simulate(code, scenario=...)``).
            - ``dartlab.simulate.run.runScenario``: 내부 end-to-end 드라이버.
            - ``dartlab.synth.scenario.getPresetScenarios``: 유효한 시나리오 id.

        Requires:
            proforma 노드가 ``partial`` 이 아니려면 IS/BS/CF 가 ~3 년 이상인 재무 시계열이 필요.

        Capabilities:
            - 한 회사의 시나리오-조건부 결정론 경로·가치를 Company 흐름에서 바로 얻는다.

        Guide:
            - 시나리오 비교는 시나리오마다 한 번씩 호출 (baseline vs adverse 는 매크로만 다름).
              결과는 audit 객체 - 노드 provenance/refs 로 숫자를 설명.

        AIContext:
            - 출력은 예측이 아니라 고정 가정의 결정론 변환 - 시나리오 id·노드 provenance/refs·asOf
              를 같이 노출. ``partial`` 은 데이터 갭(None)이지 0 아님. 대표 렌즈의 가정과
              시나리오는 ``assumptionLedger``에 맥락으로 보존하며 DriverSheet 입력을 바꾸지 않음.

        When:
            - 한 회사의 시나리오-조건부 경로·가치가 Company 흐름에서 필요할 때.

        How:
            - self → simulate.run.runScenario(self, scenario, horizon, asOf).

        LLM Specifications:
            AntiPatterns:
                - ``dcfPerShare`` 를 목표주가로 인용 - 시나리오-조건부 변환이다.
                - None ``revenuePath`` 를 0 으로 취급 - 정직한 base 매출 갭.
            OutputSchema:
                - ``SimulationResult`` (paths + dcf + 노드 audit + 품질).
            Prerequisites:
                - 재무 시계열을 가진 KR Company.
            Freshness:
                - 회사 최신 재무 기간을 asOf/latestAsOf 로 상속.
            Dataflow:
                - self -> snapshot -> sheet -> evaluateSheet -> SimulationResult.
            TargetMarkets:
                - KR (getPresetScenarios("KR") + KR elasticity).
        """
        from dartlab.simulate.run import runScenario
        from dartlab.story.lensProducts import collectLensProducts

        lensBundle = collectLensProducts(
            self,
            engines=("analysis", "credit", "quant", "macro"),
            basePeriod=asOf,
        )
        return runScenario(
            self,
            scenario=scenario,
            horizon=horizon,
            asOf=asOf,
            lensBundle=lensBundle,
        )

    @property
    def panel(self):
        """공시 수평화 보드 - 잡는 순간 항목 × 기간 wide DataFrame (panel 엔진).

        DART 공시 본문(재무제표·주석·서술)을 native canonicalKey(정부 표준 ACLASS scope-strip)로
        수평 정렬한 wide. ``c.panel`` 은 그 자체가 ``pl.DataFrame``(Panel subclass) - shape/filter
        등 polars 연산 그대로. ``c.panel("재고")`` 로 섹션 행 검색, ``c.panel("IS")`` 같은 강한 소스는
        ``show`` 의 finance/report 를 끼워넣어 위임(더 강한 정규화 숫자·정형 공시). 사전빌드 artifact
        lazy read (콜드 <1s). 기본 plain(태그 strip), ``Panel(code, tag=True)`` 면 원본 XML 무손실.

        Args:
            없음 (property - self.stockCode 사용).

        Returns:
            ``Panel`` 인스턴스(= wide ``pl.DataFrame``). ``c.panel`` 자체가 wide, ``c.panel(key)`` 로
            섹션 검색 / 강한 소스 주입.

        Raises:
            없음 - artifact 부재 시 빈 DataFrame.

        Example:
            >>> c = Company("005930")
            >>> c.panel.shape                          # wide (항목 × period) - DataFrame 그대로
            >>> c.panel("재고")                        # 섹션명/canonicalKey 행 (raw 공시)
            >>> c.panel("재고", tag=True)              # 원본 XML 행
            >>> c.panel("IS")                          # 강한 소스 - finance 주입 (show 위임)
            >>> c.panel("재고", source="raw")          # 강제 raw 공시

        SeeAlso:
            - ``providers.dart.panel.Panel`` - 반환 본체 (pl.DataFrame subclass + __call__).
            - ``show`` - 강한 소스(finance/report/notes) dispatch - c.panel 이 주입 재사용.

        Requires:
            - data/dart/panel/{code}/*.parquet (사전빌드 artifact).

        Capabilities:
            - 한 회사 공시를 항목 × 기간 wide 로 - 잡는 순간 DataFrame, callable 로 섹션·강한 소스 라우팅.

        Guide:
            - `c.panel.board()` 로 가용 canonicalKey 확인 후 `c.panel(key)`. 회사간은 모듈
              레벨 `compare` (`dartlab.compare(codes, topic=...)`, 회사 단위 facade 밖).

        AIContext:
            - 상태 없는 lazy read - 매 접근 새 Panel (누적 0). contentRaw 는 외부 untrusted.

        When:
            - 한 회사의 공시 수평화 보드가 Company 흐름에서 필요할 때.

        How:
            - self.stockCode → Panel(stockCode, marketNs="kr") lazy 인스턴스.

        LLM Specifications:
            AntiPatterns:
                - c.panel 결과 캐싱 강제 금지 - 상태 없는 lazy(누적 0).
                - canonicalKey 추측 금지 - board 로 확인 후 show.
            OutputSchema:
                - ``Panel`` (board/show/wide/long/periods 메서드).
            Prerequisites:
                - panel artifact.
            Freshness:
                - 매 접근 read.
            Dataflow:
                - self.stockCode → Panel(wide) + _showFn/_strongFn 주입.
            TargetMarkets:
                - KR (DART). US 는 marketNs="us" (EDGAR panel, 후속).
        """
        from dartlab.providers.dart.builder.dataDispatcher import isStrongTopic
        from dartlab.providers.dart.panel import Panel as _Panel

        p = _Panel(self.stockCode, marketNs="kr")
        # facade 주입 - c.panel("IS") 강한 소스는 finance/report 모듈(_showImpl 내부 dispatch)에 직접
        # 붙는다(공개 c.show property 우회). finance 모듈은 삭제 대상이 아님 - panel 이 그 표면이 된다.
        # panel 패키지는 finance 를 import 안 함 - 주입된 callable 만 호출(layer 격리, cycle 0).
        p._showFn = self._showImpl
        p._strongFn = isStrongTopic
        return p

    def _showImpl(
        self,
        topic: str,
        block: int | None = None,
        *,
        period: str | list[str] | None = None,
        freq: str = "Q",
        scope: str = "consolidated",
        raw: bool = False,
        asOf: str | None = None,
    ) -> pl.DataFrame | None:
        """topic 의 데이터를 반환 - 내부 구현 (사용자는 ``c.show`` 호출).

        ``operation.apiContract`` 의 "단일 진입점 + 파라미터 계약" 규칙에 따라
        모든 topic 접근은 ``c.panel(topic, ...)`` 로 통합한다.
        ``c.panel("BS")``, ``c.panel("ratios")``, ``c.panel("dividend")`` 등.

        Capabilities:
            - 120+ topic 접근 (재무제표, 사업내용, 지배구조, 임원현황 등)
            - 기간 / 주기 / 범위 / 블록 / 세로뷰 모두 파라미터 토글
            - panel / finance / report 3 source 자동 통합

        Args:
            topic: topic 이름. ``"BS"`` ``"IS"`` ``"CF"`` ``"CIS"`` ``"SCE"`` ``"ratios"``
                같은 finance topic 또는 ``"dividend"`` ``"companyOverview"`` 같은 panel/report
                topic. 주요주주/최대주주 topic은 ``"majorHolder"`` 이며
                ``"majorShareholder"`` 가 아니다. 전체 목록은 ``c.topics``.
            block: 블록 인덱스. None 이면 블록 목차 (1개면 바로 데이터).
            period: 단일 기간 필터 (``"2023"``, ``"2024Q2"``) 또는 리스트 (세로 비교 뷰).
            freq: 시계열 주기 - ``"Q"`` (분기, 기본) / ``"Y"`` (연간 strict 합) /
                ``"YTD"`` (year-to-date 누적). pandas 관용 코드. **finance topic 한정**.
            scope: 재무제표 범위 - ``"consolidated"`` (연결, 기본) / ``"separate"`` (별도).
                **finance topic 한정**.
            raw: True 면 원본 그대로 (정제 없이).

        Returns
        -------
        pl.DataFrame | None
            finance topic (IS/BS/CF/CIS/SCE):
                snakeId : str - 계정 식별자 (영문 snake_case)
                항목 : str - 계정명 (한글)
                2025Q4, 2025Q3, ... : float - 분기별 값 (원 단위, freq="Q" 기본)
                2025, 2024, ... : float - 연간 합산 값 (원 단위, freq="Y")
            ratios topic:
                항목 : str - 비율명
                2025Q4, 2025Q3, ... : float - 비율값 (%, 배)
            notes topic (inventory, borrowings 등):
                항목 : str - 세부 항목명
                당기, 전기 또는 연도 컬럼 : float - 금액 (원 단위)
            docs/report topic (dividend, employee 등):
                topic별 컬럼 구조 - c.panel(topic) 실행으로 확인
            블록 미지정 + 멀티블록 topic:
                block : int - 블록 번호
                title : str - 블록 제목
            데이터 없으면 None.

        Requires:
            데이터: panel (자동 다운로드). finance topic 은 finance parquet 도 필요.

        AIContext:
            - 120+ topic 단일 접근점 - LLM 이 데이터 조회 핵심 도구
            - finance topic 은 freq/scope 토글로 분기/연간/연결/별도 자유 전환

        Guide:
            - "분기 손익" → ``c.panel("IS")``
            - "연간 손익" → ``c.panel("IS", freq="Y")``
            - "별도 재무상태표" → ``c.panel("BS", scope="separate")``
            - "2023년 손익" → ``c.panel("IS", period="2023")``
            - "배당 정보" → ``c.panel("dividend")``
            - "주요주주/최대주주" → ``c.panel("majorHolder")``

        SeeAlso:
            - select: show() 결과에서 행/열 필터 + 차트
            - trace: 데이터 출처 추적
            - topics: 사용 가능한 topic 전체 목록

        Example::

            c = dartlab.Company("005930")
            c.panel("IS")                              # 분기 연결 (기본)
            c.panel("IS", freq="Y")                    # 연간 연결
            c.panel("IS", scope="separate")            # 분기 별도
            c.panel("IS", freq="Y", scope="separate")  # 연간 별도
            c.panel("IS", period="2023")               # 2023년 필터
            c.panel("dividend")                        # 배당
            c.panel("majorHolder")                     # 주요주주/최대주주

        LLM Specifications:
            AntiPatterns:
                - 분기 컬럼명을 "Q4_2025" 로 추측 (실제는 "2025Q4")
                - freq="M" 같은 미지원 값 (Q/Y/YTD 만)
                - finance topic 에 raw=True 후 비율 계산 (정제 단계 누락)
            OutputSchema:
                - snakeId : str - 영문 snake_case 계정 식별자 (finance 한정)
                - 항목 : str - 한글 계정명
                - 2025Q4, 2025Q3, ... : float - 분기 값 (원 단위, freq="Q" 기본)
                - 2025, 2024, ... : float - 연간 합산 (원 단위, freq="Y")
            Freshness:
                분기 마감 후 45일 (DART 공시 마감일). c.update() 로 증분 갱신.
        """
        from dartlab.providers.dart.builder.dataDispatcher import showImpl

        result = showImpl(self, topic, block, period=period, freq=freq, scope=scope, raw=raw)
        if asOf is None or result is None:
            return result
        return _filterPeriodColumnsByAsOf(result, asOf)

    @staticmethod
    def _warnUnknownTopic(topic: str, sec: pl.DataFrame) -> None:
        from dartlab.providers.dart.builder.dataShapeUtils import warnUnknownTopic

        warnUnknownTopic(topic, sec)

    @staticmethod
    def _transposeToVertical(wide: pl.DataFrame, periods: list[str]) -> pl.DataFrame | None:
        from dartlab.providers.dart.builder.dataShapeUtils import transposeToVertical

        return transposeToVertical(wide, periods)

    @staticmethod
    def _cleanFinanceDataFrame(df: pl.DataFrame, sjDiv: str) -> pl.DataFrame:
        from dartlab.providers.dart.builder.dataShapeUtils import cleanFinanceDataFrame

        return cleanFinanceDataFrame(df, sjDiv)

    _FINANCE_TOPICS = frozenset({"BS", "IS", "CF", "CIS", "SCE"})

    @property
    def select(self):
        """``show()`` 결과에서 행/열 필터 - dual access proxy.

        Returns:
            ``CallableAccessor`` - call/attr form 둘 다 ``_selectImpl`` 호출. ``SelectResult``
            반환 (filtered DataFrame + meta). 상세는 ``_selectImpl`` docstring.

        Example:
            >>> c = Company("005930")
            >>> c.select("IS", ["매출액"])           # call form
            >>> c.select.IS(["매출액"])              # attr form
            >>> c.select.IS(["매출액"], freq="Y")    # attr + kwargs

        Raises:
            없음 (해당 topic 부재 시 ``_selectImpl`` 이 None 반환).

        SeeAlso:
            - ``_selectImpl`` - 실제 필터 구현.
            - ``show`` - 본 함수의 입력 source.
            - ``dartlab.frame.select.SelectResult`` - 반환 객체 + ``.chart()`` 체이닝.

        Requires:
            - dartlab
            - polars

        Capabilities:
            - show() 결과의 indList (행/계정) × colList (열/기간) 동시 필터. SelectResult 로 감싸
              ``.chart()`` 체이닝 + export. strict=True 시 매치 0 면 ValueError.

        Guide:
            - "매출액만 2024" → ``c.select("IS", "매출액", "2024")``.
            - "여러 계정 + 여러 연도" → ``c.select("IS", ["매출액", "당기순이익"], ["2024", "2023"])``.

        AIContext:
            show() 전체 노출 비용 회피 - 필요 행/열만 정밀 추출 후 LLM 컨텍스트 주입.
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
        """show() 결과에서 행(indList) + 열(colList) 필터 - 내부 구현.

        ``c.panel()`` 와 동일한 freq/scope 파라미터를 받는다 (api-contract).

        Args:
            topic: IS, BS, CF, CIS, SCE 또는 docs topic.
            indList: 행 필터. 한글 항목/snakeId/항목명. 단일 str 도 가능.
            colList: 열(기간) 필터. 단일 str 도 가능.
            freq: 시계열 주기 - ``"Q"`` (분기, 기본) / ``"Y"`` (연간) / ``"YTD"`` (누적).
            scope: 재무제표 범위 - ``"consolidated"`` (연결, 기본) / ``"separate"`` (별도).

        Returns
        -------
        SelectResult
            show()와 동일 컬럼 구조에서 indList/colList로 필터된 행/열.
            .chart() 체이닝으로 시각화 가능.
            내부 DataFrame 접근: result.df (pl.DataFrame).
            finance topic 예시 (c.select("IS", ["매출액"])):
                snakeId : str - 계정 식별자
                항목 : str - 계정명
                2025Q4, 2025Q3, ... : float - 분기별 값 (원 단위)
            행 매칭 실패 시 ValueError.

        Example::

            c.select("IS", ["매출액", "영업이익"])
            c.select("IS", ["매출액"], freq="Y")              # 연간 매출
            c.select("BS", ["자본총계"], scope="separate")    # 별도 자본
            c.select("IS", ["매출액"]).chart()
        """
        from dartlab.frame.select import SelectResult
        from dartlab.providers._common.show import selectFromShow

        # 생존 엔진 _showImpl 직접 호출 (공개 show API 은퇴, panel 이 표면). ValueError propagate.
        try:
            df = self._showImpl(topic, freq=freq, scope=scope)
        except (ValueError, KeyError):
            if strict:
                raise
            return None
        if df is None or not isinstance(df, pl.DataFrame):
            if not strict:
                return None
            # show 가 정상 None 반환한 경우 (raw 모드 등) - ValueError 대신 명확한 안내
            raise ValueError(
                f"'{topic}' topic 의 데이터를 가져올 수 없습니다. "
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
                "필터링할 항목을 1개 이상 전달하세요. 예: c.select('IS', ['매출액'])"
            )

        # _showImpl 은 finance 통계표만 반환(공개 show + panel-only) - block-index 경로 소멸.
        filtered = selectFromShow(df, indList, colList)
        if filtered is None:
            if not strict:
                return None
            # indList 가 dataframe 에 매치 안 되면 silent None 대신 명시적 에러
            available = []
            try:
                # 첫 컬럼이 보통 항목
                if df.width > 0:
                    first_col = df.columns[0]
                    available = df[first_col].drop_nulls().to_list()[:15]
            except (AttributeError, IndexError, TypeError):
                pass
            ind_str = indList if indList else colList
            hint = f"\n  사용 가능한 행 일부: {', '.join(str(a) for a in available)}" if available else ""
            raise ValueError(
                f"'{topic}' topic 에서 {ind_str} 를 찾을 수 없습니다.{hint}\n"
                f"  c.panel('{topic}') 로 전체 행을 확인하세요."
            )
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
        """topic 데이터의 출처 (panel/finance/report) 와 선택 근거 추적.

        Capabilities:
            - topic 별 데이터 출처 확인 (panel, finance, report)
            - 출처 선택 이유 (우선순위, fallback 경로)
            - 각 출처별 데이터 행 수, 기간 수, 커버리지

        Args:
            topic: topic 이름.
            period: 특정 기간. None 이면 전체.

        Returns:
            dict - primarySource, fallbackSources, whySelected, availableSources 등.
            topic 미존재 시 None.

        Raises:
            없음 (데이터 부재 시 None 반환).

        Requires:
            데이터: panel + finance + report (보유한 것만 추적)

        Example:
            >>> c.trace("BS")           # 재무상태표 출처
            >>> c.trace("dividend")     # 배당 데이터 출처

        AIContext:
            - 데이터 출처 신뢰도 판단 - finance > report > docs 우선순위 확인
            - 분석 결과의 근거 투명성 확보

        Guide:
            - "이 데이터 어디서 온 거야?" → c.trace("BS")
            - "데이터 출처 확인" → c.trace(topic)

        SeeAlso:
            - show: topic 데이터 조회 (trace로 출처 확인 후 열람)
            - sources: 3개 source 전체 가용 현황

        LLM Specifications:
            AntiPatterns:
                - 결과 없이 show() 인용 → AI 환각 위험. trace 결과 source 명시 의무.
                - period 인자는 metadata 만 - 실 row 필터는 show() 가 처리.
            OutputSchema:
                - dict {topic, period, primarySource, fallbackSources, selectedPayloadRef,
                  availableSources:list, whySelected, template?, rowCount?, yearCount?, coverage?} 또는 None.
            Prerequisites:
                - panel/finance/report origin 중 최소 1 보유.
            Freshness:
                - 호출 시점 (panel + finance index 기준).
            Dataflow:
                - topic → resolveTopic → ratios/finance/panel 분기 → source priority 결정 → 본 dict.
            TargetMarkets:
                - KR (DART provenance).
        """
        topic = _resolveTopic(topic)
        if topic == "panelStatus" and not self._hasPanel:
            return {
                "topic": topic,
                "period": period,
                "primarySource": "panel",
                "fallbackSources": [],
                "selectedPayloadRef": None,
                "availableSources": [],
                "whySelected": "panel unavailable",
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
            pl.DataFrame | None - 변경 요약, 히스토리, 또는 줄 단위 diff.

        Requires:
            데이터: panel (2개 이상 기간 필요)

        Example::

            c.diff()                                    # 전체 변경 요약
            c.diff("businessOverview")                  # 사업개요 변경 이력
            c.diff("businessOverview", "2023", "2024")  # 줄 단위 diff

        AIContext:
            - 기간간 공시 변경 감지 - 사업 방향 전환, 리스크 요인 변화 탐지
            - watch()보다 세밀한 줄 단위 변경 추적

        Guide:
            - "공시에서 뭐가 바뀌었어?" → c.diff()
            - "사업개요 변경 이력" → c.diff("businessOverview")
            - "2023 vs 2024 차이" → c.diff("businessOverview", "2023", "2024")

        SeeAlso:
            - watch: 변화 중요도 스코어링 (diff보다 요약적)
            - keywordTrend: 키워드 빈도 추이 (텍스트 변화의 다른 관점)
            - show: 특정 기간 원문 조회

        Raises:
            없음.

        LLM Specifications:
            AntiPatterns:
                - 줄 단위 diff (3 인자) 결과를 그대로 LLM → 거대 본문 토큰 폭증. 변경 줄만.
                - period 형식 변형 ("2023Q4" vs "2023") → panel text 컬럼명 매칭 X.
            OutputSchema:
                - 호출 모드별 - (1) 전체 요약 (2) topic 히스토리 (3) 줄 단위 diff DataFrame.
            Prerequisites:
                - panel text wide (2 기간 이상).
            Freshness:
                - panel 갱신 시점.
            Dataflow:
                - panel text wide → 모드 별 diff (summary/history/lineDiff) → 본 함수.
            TargetMarkets:
                - KR (DART 정기보고서 변경).
        """
        if topic is not None:
            topic = _resolveTopic(topic)
        # panel 섹션 topic×period text wide SSOT.
        from dartlab.providers._common.diff import (
            diffSummaryDataFrame,
            lineDiffDataFrame,
            sectionsDiff,
            topicHistoryDataFrame,
        )
        from dartlab.providers.dart.panel.text import panelTextWide

        docsSections = panelTextWide(self.stockCode)
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
            pl.DataFrame | None - topic x period x keyword 빈도.

        Requires:
            데이터: panel

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

        Raises:
            없음.

        LLM Specifications:
            AntiPatterns:
                - 짧은 keyword ("AI") → 단어 경계 무시 매칭 ("RAID" 도 hit). 정확 매칭 시 정규식.
                - 빈도 절대값 비교 X - 본문 길이 차이 무시. 정규화 별도.
            OutputSchema:
                - pl.DataFrame [topic, period, keyword, count] 또는 None.
            Prerequisites:
                - panel text wide.
            Freshness:
                - panel 갱신 시점.
            Dataflow:
                - panel text wide + keywords → keywordFrequency → 본 DF.
            TargetMarkets:
                - KR (DART 정기보고서 텍스트).
        """
        from dartlab.providers._common.diff import keywordFrequency
        from dartlab.providers.dart.panel.text import panelTextWide

        docsSections = panelTextWide(self.stockCode)
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
            pl.DataFrame - title, date, source, link.

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

        Raises:
            없음.

        LLM Specifications:
            AntiPatterns:
                - 본문 그대로 인용 → external untrusted 룰 위반. wrap_external_in_result 마커 후.
                - days 큰 값 (>90) → 외부 API 부하/pagination 비용.
            OutputSchema:
                - pl.DataFrame [title, date, source, link] 또는 None.
            Prerequisites:
                - 인터넷 + 뉴스 origin (gatherProvider - Naver/Google).
            Freshness:
                - 외부 origin 실시간.
            Dataflow:
                - getGatherProvider().news(corpName, market="KR", days) → 본 함수.
            TargetMarkets:
                - KR (한국어 뉴스 위주).
        """
        from dartlab.core.gatherProvider import getGatherProvider

        provider = getGatherProvider()
        return provider.news(self.corpName, market="KR", days=days) if provider else None

    def watch(
        self,
        topic: str | None = None,
    ) -> pl.DataFrame | None:
        """공시 변화 감지 - 중요도 스코어링 기반 변화 요약.

        Capabilities:
            - 전체 topic 변화 중요도 스코어링
            - 텍스트 변화량 + 재무 영향 통합 평가
            - 특정 topic 상세 변화 내역

        Args:
            topic: topic 이름. None이면 전체 중요도 순 요약.

        Returns:
            pl.DataFrame | None - topic, score, changeType, details 등.

        Requires:
            데이터: panel (자동 다운로드)

        Example::

            c.watch()                    # 전체 중요도 순
            c.watch("riskManagement")    # 특정 topic

        AIContext:
            - 공시 변화 중요도 자동 평가 - 분석 우선순위 결정에 활용
            - 텍스트 변화량 + 재무 영향 통합 스코어

        Guide:
            - "뭐가 크게 바뀌었어?" → c.watch()
            - "리스크 관련 변화" → c.watch("riskManagement")

        SeeAlso:
            - diff: 줄 단위 상세 변경 비교 (watch보다 세밀)
            - keywordTrend: 키워드 빈도 추이

        Raises:
            없음.

        LLM Specifications:
            AntiPatterns:
                - score 임계 hard-code 후 "큰 변화" 결론 X - 회사별 base score 분포 다름.
                - 결과 None ≠ "변화 없음" - sections 부재로 분석 불가일 수 있음.
            OutputSchema:
                - pl.DataFrame [topic, score, changeType, fromPeriod, toPeriod, details] 또는 None.
            Prerequisites:
                - panel text wide (정기보고서 본문 2 기간+).
            Freshness:
                - sections 갱신 시점.
            Dataflow:
                - scan.watch.scanner.scanCompany(self, topic) → toDataframe → 본 함수.
            TargetMarkets:
                - KR (DART 정기보고서 변경 감지).
        """
        import importlib

        scanner = importlib.import_module("dartlab.scan.watch.scanner")
        result = scanner.scanCompany(self, topic=topic)
        if result is None:
            return None
        return result.toDataframe()

    @property
    def reportModel(self):
        """전문 리포트 계약 모델 - story 블록 + de-gate 밸류에이션을 thesis-led ReportModel(dict).

        story 가 합산한 분석 섹션을 계약 ReportBlock 으로 매핑하고, 밸류에이션 de-gate
        (내재가치 bridge·시나리오)와 구조화 thesis 를 pro 블록으로 합성한다. 랜딩 /report 가
        **동일 계약**(contracts/reportModel.ts)을 소비하는 SSOT. self-calc 0 - 숫자는 L2 엔진.

        Guide:
            - "전문 리포트" → c.reportModel()
            - "밸류에이션 관점 리포트" → c.reportModel("valuation")

        Returns:
            CallableAccessor: 호출 시 ``_reportModelImpl`` 이 ReportModel dict
            (contracts/reportModel.ts conform, schemaVersion=2) 반환. 데이터 부족 시
            {"skipped": True, ...}. dual-access proxy (story 패턴).

        Raises:
            없음 - 데이터 부족·빌드 실패는 skipped dict 로 반환.

        Example:
            >>> Company("005930").reportModel("valuation")["schemaVersion"]
            2

        SeeAlso:
            - ``dartlab.story.report.buildReportModel`` - backend SSOT.
            - ``story`` - 레거시 Story dataclass(CLI/렌더용, 공존).

        Requires:
            - dartlab
            - polars

        Capabilities:
            - thesis-led 전문 리포트 계약 emitter. Python·랜딩 TS 가 둘 다 conform 하는
              단일 ReportModel 문법(18 블록)으로 직렬화. 관점별(full/valuation/credit/...) 아크.

        AIContext:
            ``ask`` 가 본 결과(계약 dict)를 받아 답변 합성 가능. story 보다 구조화·결론선행.
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
        """5엔진 결과 조립 보고서 - 11 reportType × 7 template. 느림(60~80초). dual access.

        Guide:
            - "보고서" → c.story()
            - "신용 보고서" → c.story(type="credit")
            - "수익성 블록만" → c.story("수익성")
            - "사이클 관점" → c.story(type="full", template="사이클")

        실제 동작은 ``_storyImpl`` 참조.

        Returns
        -------
        CallableAccessor
            dual-access proxy. 호출 시 ``_storyImpl`` 이 ``Story`` 객체 반환
            (blocks / toMarkdown() / toHtml()). 상세는 ``_storyImpl`` docstring.

        Raises:
            없음.

        Example:
            >>> Company("005930").story()

        SeeAlso:
            - ``_storyImpl`` - 실제 구현 + 14 섹션 + preset/template 옵션.
            - ``analysis`` - 14축 raw 분석 (story 가 합산).
            - ``dartlab.story.registry.buildStory`` - backend SSOT.

        Requires:
            - dartlab
            - polars

        Capabilities:
            - 14 섹션 (수익구조~재무정합성) 통합 보고서 dual-access proxy. preset 5 종 + template 7 종
              조합으로 톤/관점 조절. call + attr 양식 모두 backend dispatch.

        AIContext:
            ``ask`` 가 본 함수 결과를 tool 결과로 받아 AI 답변 합성. 단일 섹션 호출이 토큰 효율.
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
        """재무제표 구조화 보고서 - 기업이야기꾼의 대본 (내부 구현).

        Capabilities:
            - 14개 섹션 전체 보고서 (수익구조~재무정합성)
            - 단일 섹션 지정 가능
            - 4개 출력 형식 (rich, html, markdown, json)
            - 섹션간 순환 서사 자동 감지
            - 프리셋 지원 (executive/audit/credit/growth/valuation)
            - 스토리 템플릿 (사이클/프랜차이즈/턴어라운드/성장/자본집약/지주/현금부자)
            - detail=False로 요약만 표시
            - 레이아웃 커스텀

        AIContext:
            - ask() (dartlab.ask) 가 이 결과를 tool 로 소비해 AI 해석 생성
            - ask()에서 재무분석 컨텍스트로 활용

        Args:
            section: 섹션명 ("수익구조" 등). None이면 전체.
            layout: StoryLayout 커스텀. None이면 기본.
            helper: True면 해석 힌트 텍스트 포함. None이면 자동.
            preset: 프리셋명 ("executive"/"audit"/"credit"/"growth"/"valuation"). None이면 전체.
            template: 스토리 템플릿 ("성장"/"자본집약"/"지주" 등). "auto"면 자동 판별.
            detail: True면 전체 블록, False면 섹션 요약만. None이면 preset 기본값 또는 True.

        Returns:
            Story - 구조화 보고서.

        Requires:
            데이터: finance + report (자동 다운로드)

        Example::

            c.story()                        # 전체 검토서
            c.story("수익구조")                # 특정 섹션
            c.story(preset="audit")          # 감사/회계 검토용
            c.story(template="auto")         # 스토리 자동 판별
            c.story(template="성장")          # 성장 템플릿 적용
            c.story(detail=False)            # 전 섹션 요약만

        Guide:
            When: 구조화된 보고서가 필요할 때. 사용자가 "보고서" 명시 시에만.
            How: 무인자 = 전체 보고서. section 으로 개별 섹션. type 으로 보고서 타입.
            - "재무 검토서 만들어줘" -> c.story()
            - "수익구조 분석" -> c.story("수익구조")
            - "감사용 리뷰" -> c.story(preset="audit")
            - "이 회사 스토리는?" -> c.story(template="auto")
            - "요약만 보여줘" -> c.story(detail=False)
            - "AI 가 해석한 보고서" -> dartlab.ask("005930 보고서 작성해줘") (AI 가 story tool 호출)
            Verified:
                - credit 타입 → 신용 종합 보고서 (observed via credit ai-ask, 2026-04-25 - 정식 Phase P 판정 아님)
                - audit 타입 → 분식회계 가능성 판정 보고서 (observed via ai-ask, 2026-04-25 - 정식 Phase P 판정 아님)
                - governance 타입 → 지배구조 점검 보고서 (observed via ai-ask, 2026-04-25 - 정식 Phase P 판정 아님)
                - dividend 타입 → 배당 매력 종합 보고서 (observed via ai-ask, 2026-04-25 - 정식 Phase P 판정 아님)

        SeeAlso:
            - dartlab.ask: AI 자율 분석 (분석 질문은 여기로)
            - analysis: 14축 개별 분석 (story가 내부적으로 소비)
            - insights: 7영역 등급 + 이상치 요약

        LLM Specifications:
            AntiPatterns:
                - story() 무인자 호출 후 결과 dict 전체를 답변 본문에 dump (사용자 부담)
                - section 추측 (정확한 한글 섹션명 - c.topics 또는 가이드 확인 후)
                - preset / template 잘못 매핑 (executive/audit/credit/growth/valuation 만)
            OutputSchema:
                - Story 객체 - 14 섹션 dict + 메타 (basePeriod, prefset, template)
                - section 지정 시: 단일 섹션 dict
                - .toMarkdown() 메서드로 markdown 문자열 변환
            Prerequisites:
                - finance + report 데이터 (자동 다운로드, 첫 호출 시간 소요)
            Freshness:
                finance/report 데이터의 c.update() 시점.
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
        """재무제표 완전 분석 - 22축 (5 group), 6막 인과 구조. dual access (api-contract).

        Guide:
            - "분석해줘" → c.analysis() (가이드 반환)
            - "수익성" → c.analysis("financial", "수익성")
            - "가치평가" → c.analysis("valuation", "가치평가")
            - "override 재계산" → c.analysis("가치평가", overrides={"wacc": 9.0})

        실제 동작은 ``_analysisImpl`` 참조.

        Returns
        -------
        CallableAccessor
            dual-access proxy. 호출 시 ``_analysisImpl`` 이
            ``pl.DataFrame | dict`` 반환 (axis=None → 가이드 DataFrame, axis
            지정 → 축별 dict). 상세는 ``_analysisImpl`` docstring.

        Raises:
            없음.

        Example:
            >>> Company("005930").analysis()

        SeeAlso:
            - ``_analysisImpl`` - 실 dispatch (22 축 5 group).
            - ``story`` - analysis 결과를 보고서로 합산.
            - ``dartlab.analysis.financial.Analysis`` - backend SSOT.

        Requires:
            - dartlab
            - polars

        Capabilities:
            - 5 그룹 22 축 (financial 14 + valuation 1 + governance 3 + forecast 2 + macro 2) 개별
              분석 dispatch dual-access. axis 미지정 시 카탈로그. self 자동 바인딩.

        AIContext:
            workbench 분석 도구 entry - 축 미지정 호출로 capability 확인 후 정확 dispatch.
        """
        from dartlab.core.dualAccess import CallableAccessor

        if "_analysisAccessor" not in self._cache:
            self._cache["_analysisAccessor"] = CallableAccessor(self._analysisImpl, name="analysis")
        return self._cache["_analysisAccessor"]

    def _analysisImpl(self, axis: str | None = None, sub: str | None = None, **kwargs):
        """재무제표 완전 분석 - 22축, 단일 종목 심층 (내부 구현).

        Capabilities:
            - 22축 분석 (5 group)
              - financial (14): 수익구조, 자금조달, 자산구조, 현금흐름, 수익성, 성장성, 안정성, 효율성, 종합평가, 이익품질, 비용구조, 자본배분, 투자효율, 재무정합성
              - valuation (1): 가치평가
              - governance (3): 지배구조, 공시변화, 비교분석
              - forecast (2): 매출전망, 예측신호
              - macro (2): 매크로민감도, 밸류에이션밴드
            - 축 없이 호출 시 22축 가이드 반환
            - 개별 축 분석 시 Company 바인딩 (self 자동 전달)
            - 2-level 호출: c.analysis("financial", "수익성"), c.analysis("valuation", "가치평가")

        AIContext:
            - ask()/chat()에서 분석 결과를 컨텍스트로 주입
            - story가 내부적으로 analysis 결과를 소비

        Args:
            axis: 그룹 이름 ("financial", "valuation", "governance", "forecast", "macro") 또는 축 이름. None이면 가이드 반환.
            sub: 그룹 내 하위 축 이름 ("수익성", "가치평가", "매출전망", "지배구조", "매크로민감도" 등).
            **kwargs: 축별 추가 옵션.

        Returns:
            pl.DataFrame | dict - axis=None이면 가이드 DataFrame (axis/label/description/example/group/items).
            axis 지정 시 dict:
                {calcName} : dict - 축별 계산 결과
                    history : list[dict] - 시계열 ({period, ...지표})
                    displayHints : dict - core 컬럼 목록
                    turningPoints : list - 전환점 (있으면)
                {calcName}Flags : list[str] - 경고 플래그
                dataAsOf : dict - latestPeriod, retrievedAt
            _summary (autoEnrich 자동 주입) - 핵심 지표 요약 + [엔진가정] 블록.
            assumptions - 엔진 가정 (overrides 재호출용).

        Requires:
            데이터: finance (자동 다운로드)

        Example::

            c = Company("005930")
            c.analysis()                            # 전체 가이드 (22축)
            c.analysis("financial", "수익구조")       # 수익구조 분석
            c.analysis("valuation", "가치평가")       # 가치평가
            c.analysis("governance", "지배구조")      # 지배구조
            c.analysis("forecast", "매출전망")        # 매출전망
            c.analysis("macro", "매크로민감도")        # 매크로 민감도

        Guide:
            AI 역할: AI는 analysis를 단일 기업 재무·가치·리스크 해석 엔진으로 보고 axis/subaxis와 필요한 재무 evidence를 선택한다.
            When: 특정 종목의 재무 심층 분석이 필요할 때.
            How: axis 로 분석 영역, sub 로 세부 축 지정.
            - "22축 분석 뭐가 있어?" → c.analysis() (가이드 반환)
            - "수익구조 분석해줘" → c.analysis("financial", "수익구조")
            - "안정성 분석" → c.analysis("financial", "안정성")
            - "가치평가 해줘" → c.analysis("valuation", "가치평가")
            - "매출전망" → c.analysis("forecast", "매출전망")
            Verified:
                - 수익성 단독 → 마진 시계열 + 전환점 + 반도체 사이클 인과 (observed via ai-ask, 2026-04-25 - 정식 Phase P 판정 아님)
                - 이익품질 + 재무정합성 → 분식회계 가능성 판정 (observed via ai-ask, 2026-04-25 - 정식 Phase P 판정 아님)
                - 가치평가 → 적정주가 범위 + 현재가 대비 판정 (observed via ai-ask, 2026-04-25 - 정식 Phase P 판정 아님)
                - 자본배분 + 현금흐름 → 배당 매력 종합 판단 (observed via ai-ask, 2026-04-25 - 정식 Phase P 판정 아님)
                - 지배구조 → 이사회 독립성 + 지배력 집중 점검 (observed via ai-ask, 2026-04-25 - 정식 Phase P 판정 아님)

        SeeAlso:
            - story: 22축 분석을 섹션별 보고서로 조합
            - insights: 7영역 등급 요약 (analysis보다 요약적)
            - ratios: 재무비율 시계열 (analysis의 입력 데이터)

        LLM Specifications:
            AntiPatterns:
                - axis 만 주고 sub 없이 호출 (그룹 가이드만 반환, 실제 분석 X)
                - 그룹명 ("financial") 을 axis 로, 축명 ("수익성") 을 sub 로 - 순서 헷갈림
                - sub 에 영문 ("profitability") 사용 (실제는 한글)
            OutputSchema:
                - history : list[dict] - 시계열 (period + 지표들)
                - displayHints : dict - core 컬럼 목록
                - turningPoints : list - 전환점
                - dataAsOf : dict - latestPeriod, retrievedAt
                - assumptions : dict - 엔진 가정 (overrides 재호출용)
            Freshness:
                finance 데이터 기준 - 분기 마감 후 45일.
        """
        from dartlab.analysis.financial import Analysis

        _analysis = Analysis()
        if axis is None:
            return _analysis()
        if sub is not None:
            return _analysis(axis, sub, company=self, **kwargs)
        return _analysis(axis, company=self, **kwargs)

    def validateStory(self, overrides: dict | None = None) -> dict:
        """Damodaran 스토리 검증 - Possible / Plausible / Probable 3 테스트 통합.

        *Narrative and Numbers* (2017) 의 핵심: 밸류에이션의 타당성은
        (1) 과거 유사 사례, (2) 피어 분포 내 위치, (3) 수학·경제 첫 원칙
        3 층의 검증을 통과해야 한다.

        Capabilities:
            - calcStoryPrecedents (scan peer + KnowledgeDB insights)
            - calcPlausibilityBand (섹터 피어 분포 percentile)
            - calcValuationSins (정합성 규칙 위반)
            - overrides 로 AI 개입 (lifeCyclePhase, terminalGrowth 등)

        Args:
            overrides: 검증 기준 조율 (VALUATION_KEYS).

        Returns:
            dict
                precedents : dict - Possible Test 결과
                plausibility : dict - Plausible Test 결과
                rules : dict - Probable Test 결과
                overall : str - "info" | "warn" | "critical"

        Example::

            c = Company("005930")
            r = c.validateStory()
            for f in r["rules"]["flags"]:
                print(f['severity'], f['reason'])

        Raises:
            없음.

        SeeAlso:
            - ``storyTree`` / ``causalWeights`` - 검증 대상 story.
            - ``dartlab.analysis.financial.storyValidation`` - 3 테스트 backend.

        Requires:
            - dartlab
            - polars

        Guide:
            - "이 가정 그럴듯하나" → 본 함수 결과 plausibility band.
            - "valuation 의 위험 신호" → result["rules"] severity = "critical".

        AIContext:
            AI 가 사용자 valuation 가정 reality check 시 본 함수. critical 이면 강한 경고 의무.

        LLM Specifications:
            AntiPatterns:
                - overall "info" 결과를 "안전" 결론 → severity 는 룰 위반 부재일 뿐 valuation 정답 아님.
                - precedents 자동 선정 - 사용자 명시 시 다른 결과 가능.
            OutputSchema:
                - dict {"precedents": dict, "plausibility": dict, "rules": dict, "overall": str}.
            Prerequisites:
                - storyTree base + 동종 universe.
            Freshness:
                - 호출 시점.
            Dataflow:
                - precedents+band+sins 3 분석 → severity 종합 → 본 함수.
            TargetMarkets:
                - KR (DART valuation 검증).
        """
        from dartlab.analysis.financial.storyValidation import (
            calcPlausibilityBand,
            calcStoryPrecedents,
            calcValuationSins,
        )

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
        """dartlab 독립 신용평가 (dCR-AAA~D). 7축 - 채무상환/자본구조/유동성/현금흐름/사업안정성/재무신뢰성/공시리스크.

        Guide:
            - "신용등급" → c.credit("등급")
            - "채무 감당되나" → c.credit("채무상환")
            - "전체 평가" → c.credit(detail=True)
            - "속성 접근" → c.credit.유동성()

        실제 동작은 ``_creditImpl`` 참조.

        Returns
        -------
        CallableAccessor
            dual-access proxy. 호출 시 ``_creditImpl`` 이 dict 반환 (grade,
            score (점), healthScore (점), axes, outlook). 상세는 ``_creditImpl``.

        Raises:
            없음.

        Example:
            >>> Company("005930").credit()

        SeeAlso:
            - ``_creditImpl`` - 실 구현 (dCR 20 단계 + 7 축).
            - ``analysis("financial", "안정성")`` - credit 보완 입력.
            - ``story(preset="credit")`` - credit 결과 보고서 합성.

        Requires:
            - dartlab
            - polars

        Capabilities:
            - dartlab 독립 dCR 등급 (AAA→D 20 단계) dual-access. 7 축 (채무상환/자본구조/유동성/
              현금흐름/사업안정성/재무신뢰성/공시리스크) 정량 합산. KIS/NICE 외부 등급과 비교 가능.

        AIContext:
            외부 신용평가 미상장 회사도 동일 척도. AI 가 부도위험 답변 시 본 결과 + analysis 결합.
        """
        from dartlab.core.dualAccess import CallableAccessor

        if "_creditAccessor" not in self._cache:
            self._cache["_creditAccessor"] = CallableAccessor(self._creditImpl, name="credit")
        return self._cache["_creditAccessor"]

    def _creditImpl(
        self,
        axis: str | None = None,
        *,
        detail: bool = False,
        basePeriod: str | None = None,
        overrides: dict | None = None,
    ):
        """독립 신용평가 - dCR 20단계 등급 (내부 구현).

        dartlab 독립 신용평가 엔진(credit/)이 산출하는 dCR 등급.
        7축 정량 스코어링 + 업종별 차등 + 시계열 안정화.

        Args:
            axis: 축 이름 ("채무상환", "자본구조" 등). None이면 등급 종합.
            detail: True이면 7축 상세 + 지표 시계열 포함.
            basePeriod: 분석 기준 기간. None이면 최신.
            overrides: AI/사용자가 엔진 계산 가정을 직접 교체하는 dict.
                키: debtRatio, interestCoverage, currentRatio, quickRatio, ocfToDebt,
                fcfToDebt, scenarioStress. 상세: core/overrides.py.

        Returns:
            dict | None: 등급 결과. axis 지정 시 해당 축만.

        Example::

            c.credit()              # → {"grade": "dCR-AA", "score": 6.6, ...}
            c.credit("채무상환")     # → {"axis": "채무상환능력", "score": 2.7, ...}
            c.credit(detail=True)   # → 7축 상세 + metricsHistory
            c.credit(overrides={"debtRatio": 150, "interestCoverage": 2.5})  # 스트레스 시나리오

        Guide:
            When: 부도 위험·신용등급·채무상환능력 판단이 필요할 때.
            How: 무인자 호출로 종합 등급, axis 로 개별 축, detail=True 로 시계열.
            Verified:
                - credit 단독 → dCR 등급 + 7축 위험점수 분해 + PD 추정 (observed via ai-ask, 2026-04-25 - 정식 Phase P 판정 아님)
                - credit + analysis(안정성,현금흐름) → 부도 위험 종합 진단 (observed via ai-ask, 2026-04-25 - 정식 Phase P 판정 아님)

        SeeAlso:
            - story("신용평가"): 보고서 형식으로 렌더링
            - analysis("financial", "신용평가"): analysis 축으로 접근

        LLM Specifications:
            AntiPatterns:
                - axis 와 detail=True 동시 (개별 축에 detail 효과 없음)
                - overrides 키 추측 (validateOverrides 가 검증, 미지원 키는 차단)
            OutputSchema:
                - grade : str - dCR 등급 (예: dCR-AA, dCR-BBB)
                - score : float - 종합 점수 (0~10)
                - healthScore : float - 재무 건전성 점수
                - axes : dict - 7축 위험 점수 (axis 미지정 시)
                - outlook : str - 등급 전망
            Freshness:
                finance 데이터 기준 - 분기 마감 후 45일.
        """
        from dartlab.credit import creditCompany
        from dartlab.synth.overrides import validateOverrides

        clean = validateOverrides(overrides, engine="credit")
        kwargs: dict = {}
        if clean:
            kwargs["overrides"] = clean
        return creditCompany(self, axis=axis, detail=detail, basePeriod=basePeriod, **kwargs)

    def gather(self, axis: str | None = None, target: str | None = None, **kwargs):
        """외부 시장 데이터 수집 - 4축 (price/flow/macro/news).

        Args:
            axis: 데이터 축. price/flow/macro/news/sector/insider/peers/ownership.
            target: 축별 부가 인자.
                - axis='news' 일 때: 검색어 (예: '한국 경제', '반도체 수출 동향').
                  시장 레벨 뉴스 조회. 비우면 종목 기반 fallback.
                - axis='macro' 일 때: 시리즈 이름 또는 시나리오.
                - axis='sector'/'peers' 일 때: 비교 대상 sector/종목.
            **kwargs: market, days, start, end 등 축별 옵션.

        Capabilities:
            - price: OHLCV 주가 시계열 (KR Naver / US Yahoo)
            - flow: 외국인/기관 수급 동향 (KR 전용)
            - macro: ECOS(KR) / FRED(US) 거시지표 시계열 (기본 HF 벌크)
            - news: Google News RSS 뉴스 수집
            - 자동 fallback 체인, circuit breaker, TTL 캐시

        AIContext:
            - ask()/chat()에서 주가/수급/거시 데이터를 컨텍스트로 주입
            - 기업 분석 시 시장 데이터 보충 자료로 활용

        Args:
            axis: 축 이름 ("price", "flow", "macro", "news"). None이면 가이드 반환.
            **kwargs: market, start, end, days 등 축별 옵션.

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
                open : float - 시가 (원)
                high : float - 고가 (원)
                low : float - 저가 (원)
                close : float - 종가 (원)
                volume : int - 거래량
            axis="flow":
                date : date - 날짜
                외국인순매수 : int - 외국인 순매수량
                기관순매수 : int - 기관 순매수량
                (KR 전용. EDGAR ticker는 None 반환)
            axis="macro":
                date : date - 날짜
                지표별 컬럼 : float - ECOS/FRED 거시지표 값
            axis="news":
                title : str - 뉴스 제목
                link : str - 기사 URL
                pubDate : str - 발행일
            데이터 없으면 None.

        Requires:
            price/flow/news: 없음 (공개 API)
            macro: 불필요 -- apiKey 명시 시 ECOS/FRED 직접 API 호출

        Example::

            c = Company("005930")
            c.gather()                 # 4축 가이드
            c.gather("price")          # 주가 시계열
            c.gather("news")           # 뉴스

        Guide:
            When: 주가·수급·거시지표·뉴스 원본 데이터가 필요할 때.
            How: axis 로 데이터 종류 지정. 무인자 = 가이드.
            - "주가 데이터" → c.gather("price")
            - "외국인/기관 수급" → c.gather("flow")
            - "거시경제 지표" → c.gather("macro")
            - "뉴스 수집" → c.gather("news") 또는 c.news()
            Verified:
                - gather("news") → 뉴스 목록 + 헤드라인 해석 (observed via ai-ask, 2026-04-25 - 정식 Phase P 판정 아님)

        SeeAlso:
            - news: 뉴스 전용 단축 메서드
            - ask: gather 데이터를 컨텍스트로 활용한 AI 분석

        LLM Specifications:
            AntiPatterns:
                - axis="all" 같은 미지원 값 (price/flow/macro/news/sector/insider/peers/ownership 만)
                - flow 를 EDGAR ticker (US) 에 호출 (KR 전용)
                - news 의 target 비워두고 종목 무관 결과 기대 (종목 fallback 발생)
            OutputSchema:
                - price: date / open / high / low / close / volume (원, 정수)
                - flow: date / 외국인순매수 / 기관순매수 (KR 전용, 정수)
                - macro: date / 지표별 컬럼 (float)
                - news: title / link / pubDate (string)
            Freshness:
                price/flow: T+1 (전일 종가). macro: ECOS/FRED 갱신 주기. news: 실시간 RSS.

        Raises:
            없음.
        """
        from dartlab.core.gatherProvider import getGatherProvider

        provider = getGatherProvider()
        if provider is None:
            return None
        return provider.entry(axis, self.stockCode, **kwargs)

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
            데이터: panel (자동 다운로드)

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

        Raises:
            없음.

        LLM Specifications:
            AntiPatterns:
                - numeric=True 후 변환 실패 row 가 None - caller 가 null 분기 의무.
                - subtopic 이름 추측 - 정확 이름은 sections 본문 또는 show(topic) 확인.
            OutputSchema:
                - ParsedSubtopicTable {df: pl.DataFrame, subtopic: str, columns: list} 또는 None.
            Prerequisites:
                - panel 본 회사 보유 + 해당 topic 의 markdown table 본문.
            Freshness:
                - panel 갱신 시점.
            Dataflow:
                - panel table rows → parseSubtopicTable(numeric) → period filter → 본 함수.
            TargetMarkets:
                - KR (DART 정기보고서 표).
        """
        # subtopic markdown 표 농장 은퇴(§영구소실) - 정형 표는 panel/공통파서(panelXmlTables)
        # 또는 c.panel raw 공시 검색 사용. 본 API 는 None 반환.
        _ = (topic, subtopic, numeric, period)
        return None

    @property
    def topics(self) -> pl.DataFrame:
        """topic별 요약 DataFrame -- 전체 데이터 지도.

        Capabilities:
            - panel/finance/report 모든 source의 topic을 하나의 DataFrame으로 통합
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
            - panel: topic x period 전체 지도 (topics보다 상세)
            - index: 전체 구조 메타데이터 목차

        Returns:
            pl.DataFrame -- 컬럼: order, chapter, topic, source, blocks, periods, latestPeriod

        Requires:
            데이터: panel/finance/report 중 하나 이상 (자동 다운로드)

        Example::

            c = Company("005930")
            c.topics                   # 전체 topic 요약
            c.topics.filter(pl.col("source") == "finance")  # finance만

        LLM Specifications:
            AntiPatterns:
                - 매 호출마다 c.topics 재호출 (캐시 - 1 회면 충분)
                - topics 결과로 추측한 토픽명을 show() 에 잘못 매핑 (정확한 topic 문자열 필요)
            OutputSchema:
                - order : int - chapter 순서
                - chapter : str - 장 이름
                - topic : str - topic 식별자 (show 호출 키)
                - source : str - panel / finance / report
                - blocks : int - 블록 수
                - periods : int - 기간 수
                - latestPeriod : str - 최신 기간
            Freshness:
                panel/finance/report 각각의 c.update() 시점.

        Raises:
            없음.
        """
        cacheKey = "_topicsDataFrame"
        if cacheKey in self._cache:
            return self._cache[cacheKey]

        # panel topic catalog - panel text wide 에서 유도 (docs topicManifest 은퇴).
        textWide = self._panelTextWide()
        rows: list[dict[str, Any]] = []
        seen: set[str] = set()
        if textWide is not None and not textWide.is_empty():
            topicCol = next((c for c in ("topic", "sectionLeaf") if c in textWide.columns), None)
            metaCols = {"chapter", "sectionLeaf", "blockLeaf", "topic", "source", "disclosureKey", "scope"}
            periodCols = [c for c in textWide.columns if c not in metaCols]
            if topicCol is not None:
                for row in textWide.iter_rows(named=True):
                    topic = row.get(topicCol)
                    if not isinstance(topic, str) or not topic.strip() or topic in seen:
                        continue
                    seen.add(topic)
                    nPeriods = sum(1 for pc in periodCols if row.get(pc) not in (None, ""))
                    chapterRaw = str(row.get("chapter") or "").strip()
                    chapter = chapterRaw.split(".", 1)[0].split()[0] if chapterRaw else ""
                    rows.append(
                        {
                            "order": len(rows),
                            "chapter": chapter,
                            "topic": topic,
                            "source": "panel",
                            "blocks": 1,
                            "periods": nPeriods,
                            "latestPeriod": None,
                        }
                    )

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
            result = pl.DataFrame(
                schema={
                    "order": pl.Int64,
                    "chapter": pl.Utf8,
                    "topic": pl.Utf8,
                    "source": pl.Utf8,
                    "blocks": pl.Int64,
                    "periods": pl.Int64,
                    "latestPeriod": pl.Utf8,
                }
            )
        else:
            result = (
                pl.DataFrame(combined, strict=False)
                .with_columns(
                    pl.col("chapter").replace(_CHAPTER_ORDER).cast(pl.Int64, strict=False).alias("_chapterOrder")
                )
                .sort(["_chapterOrder", "order", "topic"])
                .drop("_chapterOrder")
            )
        self._cache[cacheKey] = result
        return result

    @property
    def sources(self) -> pl.DataFrame:
        """panel/finance/report 3개 source의 가용 현황 요약.

        Capabilities:
            - 3개 데이터 source(panel, finance, report) 존재 여부/규모 한눈에 확인
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
            - 데이터 가용성 사전 점검 - 분석 가능 범위 판단의 기초

        Guide:
            - "데이터 뭐가 있어?" → c.sources
            - "panel/finance/report 상태" → c.sources

        SeeAlso:
            - topics: topic 단위 상세 데이터 지도
            - trace: 특정 topic의 출처 추적

        LLM Specifications:
            AntiPatterns:
                - 매 분석마다 c.sources 호출 (캐시 - 1 회면 충분)
                - sources 결과로 분석 결정 (가용성만 확인, 실제 분석은 show)
            OutputSchema:
                - source : str - panel / finance / report
                - available : bool - 데이터 보유 여부
                - rows : int | None - 행 수
                - cols : int | None - 컬럼 수
                - shape : str - "rows × cols" 표기
            Freshness:
                panel / rawFinance / rawReport 의 다운로드 시점 기준.

        Raises:
            없음.
        """
        rows = []
        panel = self.panel
        for source, raw in (
            ("panel", panel if not panel.is_empty() else None),
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
            - panel + finance + report 전체를 하나의 목차로 통합
            - 각 항목의 chapter, topic, label, kind, source, periods, shape, preview 제공
            - panel text 메타데이터 + 존재 확인만으로 구성 (파서 미호출, lazy)
            - viewer/렌더러가 소비하는 메타데이터 원천

        AIContext:
            - LLM이 Company 전체 구조를 파악하는 핵심 진입점
            - ask()에서 어떤 데이터를 참조할지 결정하는 기초 정보

        Guide:
            - "전체 목차 보여줘" → c.index
            - "어떤 데이터가 있는지 구조적으로" → c.index

        SeeAlso:
            - topics: topic 단위 요약 (index보다 간결)
            - panel: 전체 topic 지도 (index의 원본)
            - profile: 통합 프로필 접근자

        Returns:
            pl.DataFrame - 컬럼: chapter, topic, label, kind, source, periods, shape, preview.

        Raises:
            없음 (데이터 부재 시 빈 DataFrame).

        Requires:
            데이터: panel/finance/report 중 하나 이상 (자동 다운로드).

        Example:
            >>> c = Company("005930")
            >>> c.index                    # 전체 구조 목차
            c.index.filter(pl.col("source") == "panel")  # panel 항목만

        LLM Specifications:
            AntiPatterns:
                - index 결과 전체를 답변 본문에 dump (50+ 행)
                - chapter / kind 추측 (panel / finance / report 중 source 컬럼 확인 후)
            OutputSchema:
                - chapter : str - I / II / III ... (보고서 장)
                - topic : str - topic 식별자 (show 호출 키)
                - label : str - 사람용 라벨
                - kind : str - table / text / notice
                - source : str - panel / finance / report
                - periods : str - 보유 기간 표기
                - shape : str - "rows × cols"
                - preview : str - 첫 줄 미리보기
            Freshness:
                panel / finance / report 다운로드 시점.
        """
        cacheKey = "_lazyIndex"
        if cacheKey in self._cache:
            return self._cache[cacheKey]

        rows: list[dict[str, Any]] = []

        if not self._hasPanel:
            rows.append(
                {
                    "chapter": "안내",
                    "topic": "panelStatus",
                    "label": "사업보고서",
                    "kind": "notice",
                    "source": "panel",
                    "periods": "-",
                    "shape": "missing",
                    "preview": "현재 사업보고서 부재",
                    "_sortKey": (0, 0),
                }
            )

        # panel 카탈로그에서 index 행 유도.
        seenTopics = {r["topic"] for r in rows}
        topicsDf = self.topics
        if topicsDf is not None and not topicsDf.is_empty():
            for tr in topicsDf.iter_rows(named=True):
                topic = tr.get("topic")
                if not isinstance(topic, str) or topic in seenTopics:
                    continue
                seenTopics.add(topic)
                isFinance = tr.get("source") == "finance"
                from dartlab.providers.dart.topicStandard import chapterLabelKr, labelFor

                rows.append(
                    {
                        "chapter": chapterLabelKr(str(tr.get("chapter") or "")),
                        "topic": topic,
                        "label": labelFor(topic, fallback=topic),
                        "kind": "statement" if isFinance else "section",
                        "source": str(tr.get("source") or ""),
                        "periods": str(tr.get("periods") or "-"),
                        "shape": "-",
                        "preview": "",
                        "_sortKey": (int(tr.get("order") or 99), 0),
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
    def facts(self) -> pl.DataFrame | None:
        """topic × period 형태의 통합 facts 테이블 (sections + finance + report merge).

        Returns
        -------
        pl.DataFrame | None
            topic : str - 데이터 소스 topic
            period : str - 기간 (예: "2025Q4")
            value : str - 해당 topic/period 의 텍스트 또는 숫자 요약
            데이터 없으면 None.

        LLM Specifications:
            AntiPatterns:
                - facts 결과를 그대로 답변 본문에 dump (수백 행)
                - value 가 텍스트일 때 숫자 계산 시도 (numeric 파싱 별도)
            OutputSchema:
                - topic : str - topic 식별자
                - period : str - 기간 (2025Q4 형식)
                - value : str - 텍스트 또는 숫자 요약
            Freshness:
                sections / finance / report 의 c.update() 시점.

        Raises:
            없음.

        Returns:
            pl.DataFrame [topic, period, value] 또는 None.
        """
        return self._profileAccessor.facts

    # ── financeEngine (숫자 재무 데이터) ──

    def _ensureFinanceLoaded(self) -> None:
        """lazy finance: 첫 접근 시 buildTimeseries 실행."""
        if self._financeChecked:
            return
        self._financeChecked = True
        if not self._hasFinanceParquet:
            return
        from dartlab.providers.dart.finance.pivot import buildTimeseries

        try:
            ts = buildTimeseries(self.stockCode)
        except (OSError, ValueError, KeyError, RuntimeError, pl.exceptions.ComputeError) as e:  # noqa: BLE001
            # finance parquet 로딩/파싱 실패 → 이유 노출 후 docs fallback 허용.
            # silent 실패 시 panel("IS") 가 docs 기반으로 잘못된 결과 반환하는 사례 방지.
            # (IO / 형식 오류 / 컬럼 부재 / polars 변환 실패 - 다양한 정상 fallback 분기)
            import warnings

            warnings.warn(
                f"finance parquet 로딩 실패 ({self.stockCode}): {type(e).__name__}: {e}. "
                f"docs fallback 으로 전환됩니다 - 수치 정합성이 떨어질 수 있습니다.",
                stacklevel=2,
            )
            ts = None
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

    def _getRatiosInternal(self, fsDivPref: str = "CFS"):
        """내부용 재무비율 계산 (deprecation 없음)."""
        cacheKey = f"_ratios_{fsDivPref}"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        from dartlab.analysis.financial.ratios import calcRatios

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

    def _buildRatios(self) -> pl.DataFrame | None:
        """[INTERNAL] 재무비율 DataFrame 빌더.

        사용자는 ``c.panel("ratios")`` 호출. show() 가 finance topic dispatch 에서
        이 빌더를 호출.
        """
        from dartlab.providers.dart.builder.financeStatementBuilder import buildRatios

        return buildRatios(self)

    def _buildFinanceSeries(self, *, freq: str = "Q", scope: str = "consolidated"):
        """[INTERNAL] finance series-tuple 빌더.

        사용자는 직접 호출하지 않는다. 사용자 진입점은 ``c.panel("IS", freq=, scope=)``
        / ``c.select("IS", [...], freq=, scope=)`` 만이다 (api-contract).

        analysis / forecast / valuation / credit / story 등 calc 모듈이
        ``(series, periods)`` 튜플 형태가 필요할 때만 호출한다.

        Args:
            freq: ``"Q"`` (분기, 기본) / ``"Y"`` (연간) / ``"YTD"`` (누적).
            scope: ``"consolidated"`` (연결, 기본) / ``"separate"`` (별도).

        Returns:
            ``(series, periods)`` 또는 None.
        """
        from dartlab.providers.dart.builder.financeStatementBuilder import buildFinanceSeries

        return buildFinanceSeries(self, freq=freq, scope=scope)

    # c.SCE / c.sceMatrix / c.ratios / c.ratioSeries property 제거 (Plan v10 P1).
    # 사용자는 c.panel("SCE") / c.panel("sceMatrix") / c.panel("ratios") /
    # c.panel("ratioSeries") 사용. ratioSeries 는 dict 구조라 show 에서 dict topic 으로 처리.

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
            - sectorParams: 섹터별 밸류에이션 파라미터 (할인율, PER 등)
            - rank: 섹터 내 규모 순위
            - insights: 섹터 기준 등급 평가

        LLM Specifications:
            AntiPatterns:
                - sector 결과를 sector 컬럼 (str) 만 인용 (industryGroup 도 함께)
                - confidence 무시하고 단정 (1.0 = override, 0.5~0.9 = 키워드 매칭)
            OutputSchema:
                - sector : Sector enum - IT / Materials / Industrials / ...
                - industryGroup : IndustryGroup enum - SEMICONDUCTOR / AUTOMOBILE / ...
                - confidence : float - 0.0~1.0 (1.0 = override, 0.5+ = 키워드 매칭)
                - source : str - override / keyword / industry
            Freshness:
                KIND 상장사 목록 시점.
            TargetMarkets:
                - KR

        Raises:
            없음.
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

        Raises:
            없음.
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
            - 시장/섹터 내 상대 위치 파악 - 피어 비교 분석의 기초
            - sizeClass로 대형/중형/소형주 분류

        Guide:
            - "이 회사 순위는?" → c.rank
            - "시장에서 몇 등이야?" → c.rank.revenueRank
            - "대형주야?" → c.rank.sizeClass

        SeeAlso:
            - sector: 섹터 분류 (rank의 기준 그룹)
            - insights: 종합 등급 평가

        LLM Specifications:
            AntiPatterns:
                - rank 단독 노출 (sizeClass + sector 함께)
                - rank 결과를 절대 평가로 인용 (시장 전체 / 섹터 내 모두 표시)
            OutputSchema:
                - revenueRank : int - 매출 기준 시장 순위
                - revenueRankInSector : int - 매출 기준 섹터 순위
                - sizeClass : str - large / mid / small
                - sectorTotal : int - 섹터 종목 수
            Freshness:
                scan 데이터 기준 - 분기 마감 후 갱신.
            TargetMarkets:
                - KR

        Raises:
            없음.
        """
        cacheKey = "_rank"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        import importlib

        getRank = importlib.import_module("dartlab.scan.screen.rank").getRank
        result = getRank(self.stockCode)
        self._cache[cacheKey] = result
        return result

    # insights는 analysis 내부 - c.analysis("financial", "종합평가")로 접근

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

        Returns
        -------
        dict
            opinion : str - 감사의견 ("적정", "한정", "부적정", "의견거절")
            auditorChanges : list[dict] - 감사인 변경 이력 (year, from, to, reason)
            goingConcern : bool - 계속기업 불확실성 존재 여부
            kam : list[str] - 핵심감사사항 목록
            internalControl : str - 내부회계관리제도 검토의견

        Requires:
            데이터: panel + report (자동 다운로드)

        Example::

            c = Company("005930")
            c.audit()

        AIContext:
            - 감사 리스크 종합 평가 - 투자 의사결정의 핵심 안전장치
            - 감사의견 변경, 계속기업 불확실성은 최고 경고 수준

        Guide:
            - "감사의견 확인" → c.audit()
            - "감사인 바뀌었어?" → c.audit()["auditorChanges"]
            - "계속기업 의문은?" → c.audit()["goingConcern"]

        SeeAlso:
            - governance: 지배구조 분석 (감사위원회 구성 포함)
            - insights: 종합 등급 (감사 리스크도 반영)
            - story: 재무정합성 섹션에서 감사 결과 활용

        LLM Specifications:
            AntiPatterns:
                - "한정/부적정" 같은 무거운 결과를 답변 본문에 단정 노출 (출처 + 연도 함께)
                - audit() 결과를 매 분석마다 호출 (캐시 - 1 회면 충분)
            OutputSchema:
                - opinion : str - 감사의견 (적정 / 한정 / 부적정 / 의견거절)
                - auditorChanges : list[dict] - 감사인 변경 이력 (year, from, to, reason)
                - goingConcern : bool - 계속기업 불확실성 존재 여부
                - kam : list[str] - 핵심감사사항
                - internalControl : str - 내부회계관리제도 검토의견
            Freshness:
                report 데이터 기준 - 정기보고서 마감 후 30~45 일.

        Raises:
            없음.
        """
        from dartlab.analysis.financial.insight.pipeline import analyzeAudit

        return analyzeAudit(self)

    def executivePay(self):
        """임원 보수 ≥ 5억 원 individual 공개 (자본시장법 §159, 2013-11-29 시행).

        Capabilities:
            - 임원 보수 ≥ 5억 원 individual 공개 추출 (US proxy NEO-5 와 달리 *전원* 공개)
            - 등기/미등기/퇴직 분리
            - 급여/상여/주식매수선택권 행사이익/기타 근로소득/퇴직소득 분해
            - 회사별 상위 보수 임원 list

        Args:
            없음 (self 바인딩).

        Returns:
            pl.DataFrame 또는 None - panel native 임원보수 섹션 행(항목 × period).
            구조화 payByType/topPay(개인별 시계열)는 농장 은퇴로 드롭 - 본문 텍스트만.

        Requires:
            panel artifact (임원보수 섹션 contentRaw).

        Example::

            c = Company("005930")
            pay = c.executivePay()
            print(pay.payByType)   # 등기/미등기/퇴직 분해
            print(pay.topPay)      # 상위 보수 list

        AIContext:
            - 한국 unique disclosure - US proxy 가 숨기는 미등기/퇴직 임원 보수 노출
            - 산정기준 narrative 가 보수 메커니즘 추적 가능 (스톡옵션 행사 timing 등)
            - 회사별 보수 top 1~3 의 직위 변경 = 인사 리스크 신호

        Guide:
            - "삼성전자 임원 보수" → c.executivePay()
            - "5억 이상 임원 명단" → c.executivePay().topPay
            - "퇴직 임원 보수" → c.executivePay().payByType.filter(구분="퇴직")

        SeeAlso:
            - governance: 이사회 구성 + 사외이사 비율
            - relatedPartyTx: 관계자 거래 (executive 와 회사 사이 거래)

        LLM Specifications:
            AntiPatterns:
                - topPay 전체 dump 답변 본문에 (수십 행 - 상위 5~10 명만 인용)
                - 산정기준 narrative 생략 후 보수 총액만 인용 (메커니즘 불명)
                - 직책 정규화 없이 회사 간 비교 (대표이사 vs 부회장 vs 사장 의미 차이)
            OutputSchema:
                - pl.DataFrame | None - panel native 임원보수 섹션 행(텍스트, 구조화 드롭).
            Prerequisites:
                - panel artifact 박힘
            Freshness:
                정기보고서 마감 후 30~45 일.
            TargetMarkets:
                - KR (DART · 자본시장법 §159)

        Raises:
            없음.
        """
        # docs.finance.executivePay(개인별 구조화 파싱) 은퇴 → panel native 보수 섹션 텍스트.
        # 개인별 시계열(payByType/topPay)은 정부 native 태깅 없어 복원 불가 - 섹션 본문만.
        p = self.panel
        hit = p("보수")
        return hit if hit is not None else p.search("보수총액")

    def relatedPartyTx(self):
        """관계자 거래 (RPT) - 공정거래법 §26 chaebol disclosure 100억 원 threshold (2024-01-01 시행).

        Capabilities:
            - K-IFRS 1024 footnote 의 특수관계자 거래 line-item 추출
            - 공정거래법 §26 의 대규모기업집단현황공시 100억 원 threshold rows
            - 보증/대여/매출/매입/자산 양수도 분류
            - chaebol inter-affiliate 거래 graph 의 raw input

        Args:
            없음 (self 바인딩).

        Returns:
            RelatedPartyTxResult 또는 None - guarantees / revenue / etc DataFrame list 보유.

        Requires:
            DART 사업보고서 본문 (관계자거래 섹션 자동 파싱).

        Example::

            c = Company("005930")
            rpt = c.relatedPartyTx()
            print(rpt.guarantees)   # 지급보증 list
            print(rpt.revenue)      # 매출 거래 list

        AIContext:
            - 2024-01-01 부터 threshold 100억 원 (이전 10억 원 X - 룰 변경 주의)
            - 2025 FTC 데이터: top-10 chaebol = 193 조 원 = 전체 disclosed RPT 의 70%
            - chaebol RPT graph 구축 시 affiliateGroup 와 join 필수 (회사 단독 X)

        Guide:
            - "삼성전자 관계자 거래" → c.relatedPartyTx()
            - "삼성그룹 RPT 흐름" → affiliateGroup × relatedPartyTx 모든 계열사 join
            - "100억 이상 RPT" → 본 method 의 결과 자체 (threshold 이상만 disclosed)

        SeeAlso:
            - governance: 이사회 의결 RPT (board-approved)
            - executivePay: 임원 개인 보수 (RPT 와 별도)

        LLM Specifications:
            AntiPatterns:
                - threshold 10억 원으로 답변 (구 룰 - 2024-01-01 부터 100억)
                - 단일 회사 RPT 만 인용 + chaebol 전체 흐름 무시 (RPT 의 핵심 = inter-affiliate)
                - RPT 본문 narrative 생략 + 금액만 인용 (목적 + 조건 빠짐)
            OutputSchema:
                - guarantees : DataFrame [거래상대방, 거래종류, 금액, 기간, 조건]
                - revenue : DataFrame [거래상대방, 거래종류, 금액]
                - 등 거래 분류 별 DataFrame
            Prerequisites:
                - 사업보고서 박힘 (자동 다운로드)
            Freshness:
                정기보고서 마감 후 30~45 일.
            TargetMarkets:
                - KR (DART · 공정거래법 §26)

        Raises:
            없음.
        """
        # docs.finance.relatedPartyTx(구조화 파싱) 은퇴 → panel native 특수관계자 섹션 텍스트.
        # guaranteeDf/assetTxDf/revenueTxDf 구조화는 정부 native 태깅 없어 드롭 - 본문만.
        p = self.panel
        hit = p("특수관계자")
        return hit if hit is not None else p.search("특수관계자")

    def notesDetail(self, keyword: str, period: str = "y"):
        """K-IFRS 주석 세부항목 (리스 약정 · 우발채무 · 퇴직급여 가정 · 파생 등) 추출.

        Capabilities:
            - K-IFRS 주석 표 본문 파싱 (NOTES_KEYWORDS 23 종 - 리스/우발/퇴직/파생/금융자산 등)
            - 연간/분기/반기 분기
            - 최근 5 년 historical panel
            - audit-grade citation 의 핵심 evidence layer

        Args:
            keyword: 주석 키워드 (NOTES_KEYWORDS 23 종 중 하나 - 리스 · 우발채무 · 퇴직급여 · 파생 등)
            period: "y" 연간 · "q" 분기 · "h" 반기 (default "y").

        Returns:
            pl.DataFrame 또는 None - panel native 주석 행(항목 × period wide).
            keyword 가 disclosureKey/sectionLeaf/blockLeaf 에 매칭되는 주석 블록.

        Requires:
            panel artifact (정부 native NT_ 주석 정렬 - ``read.alignNotes``).

        Example::

            c = Company("005930")
            lease = c.notesDetail("리스")           # 리스 약정 native 주석 wide
            contingent = c.notesDetail("우발", "y") # 우발채무 주석 행

        AIContext:
            - footnote-grade Q&A 의 raw 데이터 (Bloomberg/FactSet 미보유 영역)
            - "LG energy 의 리스 약정 중 중국 비중" 같은 질문은 본 method 의 답 source
            - 주석 양식이 분기별로 미세 변경 - narrative 비교 시 변경 가능성 인지

        Guide:
            - "삼성전자 리스 약정" → c.notesDetail("리스")
            - "셀트리온 우발채무" → c.notesDetail("우발")
            - "LG화학 퇴직급여 가정" → c.notesDetail("퇴직급여")
            - "현대차 파생금융상품" → c.notesDetail("파생")

        SeeAlso:
            - audit: 감사보고서 (KAM 와 주석은 보완)
            - governance: 지배구조 본문

        LLM Specifications:
            AntiPatterns:
                - keyword 미지원 (NOTES_KEYWORDS 23 종 밖 - 직접 호출 X)
                - 연간 답변에 분기 비교 (period 인자 무시)
                - 5 년 panel 전체 dump (답변 본문 상위 3~5 년만 인용)
            OutputSchema:
                - pl.DataFrame | None - panel native 주석 wide (항목 × period).
            Prerequisites:
                - panel artifact 박힘 (online/bulk 빌드)
                - keyword 가 주석 제목/disclosureKey 에 매칭
            Freshness:
                정기보고서 마감 후 30~45 일.
            TargetMarkets:
                - KR (K-IFRS 1701/1019/1024)

        Raises:
            없음.
        """
        # docs.finance.notesDetail(regex 파싱) 은퇴 → panel native NT_ 주석(read.alignNotes) 직접.
        # period 는 wide 주석 검색에 미사용(panel 은 전 기간 행 반환) - 시그니처 호환 유지.
        # 제목 매칭(__call__) 우선, 없으면 본문 전문검색(search) fallback - 옛 본문기반 parity.
        p = self.panel
        hit = p(keyword)
        return hit if hit is not None else p.search(keyword)

    def flow(self):
        """KRX 외국인/기관 일별 net-buy (Company.gather("flow") wrapper).

        Capabilities:
            - 외국인 net-buy 일별
            - 기관 net-buy 일별
            - 개인 net-buy 일별

        Args:
            없음 (self 바인딩). 백필/프록시 옵션은 공개 엔진
            ``dartlab.gather("flow", ...)`` 경유만 지원.

        Returns:
            pl.DataFrame - 외국인/기관/개인 net-buy 시계열. 빈 결과면 빈 DataFrame.

        Requires:
            Naver flow API (KR 시장 한정). 외 시장 빈 결과.

        Example::

            c = Company("005930")
            f = c.flow()           # 일별 외국인/기관/개인 순매수

        AIContext:
            - KOSPI/KOSDAQ 외국인 수급의 가장 중요한 daily signal
            - 외국인 net-buy 누적 추세 + 기관 동조/역행 패턴이 단기 시세 driver
            - 한국 unique - 외국인/기관/개인 종목별 일별 net-buy 가 공개 (US 시장은 없음)

        Guide:
            - "삼성전자 외국인 매수세" → c.flow()
            - "005930 기관 vs 외국인 추세" → c.flow()
            - "외국인 순매수 누적" → c.flow() + cumsum

        SeeAlso:
            - gather("flow") : 동일 본체 - flow axis 직접 호출
            - krx : KRX 시장 전체 axis (시장 평균과 비교)

        LLM Specifications:
            AntiPatterns:
                - 일별 raw flow 전체 dump (답변 본문 - 최근 5~30 일 + 누적 비중만)
                - 외국인 net-buy 단독 신호 해석 (기관 동조/역행 context 동반 필수)
                - KR 외 시장에 호출 (빈 결과 정상 - 시장 제한 명시)
            OutputSchema:
                - date : Date
                - foreignNet : Int64 (단위 = 주)
                - institutionNet : Int64 (단위 = 주)
                - individualNet : Int64 (단위 = 주)
            Prerequisites:
                - KR 시장 + Naver flow API 박힘
            Freshness:
                EOD (T+1).
            TargetMarkets:
                - KR (Naver 한정)

        Raises:
            없음.
        """
        return self.gather("flow")

    @property
    def market(self) -> str:
        """시장 코드 (DART 제공자는 항상 KR).

        SeeAlso:
            - currency: 통화 코드

        Returns:
            str - "KR".

        Example::

            c = Company("005930")
            c.market  # "KR"

        Raises:
            없음.

        LLM Specifications:
            AntiPatterns:
                - 시장 세분화 (KOSPI vs KOSDAQ) 필요 시 본 값 부족 - listing 메타에서.
            OutputSchema:
                - 고정 str "KR".
            Prerequisites:
                - 없음 (상수).
            Freshness:
                - 정적.
            Dataflow:
                - 본 property → "KR".
            TargetMarkets:
                - KR - DART provider 통합 라벨.
        """
        return "KR"

    @property
    def fiscalYearEnd(self) -> str:
        """회계연도 종료 월-일 (한국 종목은 12-31 표준).

        EDGAR 와의 fiscal year-end 비교를 위한 metadata.
        한국 회계 관습 상 거의 모든 상장사가 12월말 결산 - 상수 반환.

        Returns:
            "12-31".

        Raises:
            없음.

        Example:
            >>> Company("005930").fiscalYearEnd()

        LLM Specifications:
            AntiPatterns:
                - 모든 KR 회사 12-31 단정 X - 드물지만 다른 회계년도 존재 가능 (실 종목 결산월 확인).
            OutputSchema:
                - 고정 str "12-31".
            Prerequisites:
                - 없음 (관습 상수).
            Freshness:
                - 정적.
            Dataflow:
                - 본 property → "12-31".
            TargetMarkets:
                - KR - 한국 회계 관습 표준.
        """
        return "12-31"

    @property
    def currency(self) -> str:
        """통화 코드 (DART 제공자는 항상 KRW).

        SeeAlso:
            - market: 시장 코드

        Returns:
            str - "KRW".

        Example::

            c = Company("005930")
            c.currency  # "KRW"

        Raises:
            없음.

        LLM Specifications:
            AntiPatterns:
                - 외화 결산 회사 (드물지만 가능) 도 본 함수 "KRW" 반환 - 실 보고통화 별도 확인.
            OutputSchema:
                - 고정 str "KRW".
            Prerequisites:
                - 없음 (상수).
            Freshness:
                - 정적.
            Dataflow:
                - 본 property → "KRW".
            TargetMarkets:
                - KR - 한국 표준 통화.
        """
        return "KRW"

    # ── network (관계 지도) ──────────────────────────────────

    # ── scan-related 5 진입점 (network/governance/workforce/capital/debt) ──
    # 구현은 dartlab.providers.dart.builder.scanAggregator 모듈에 위임. facade 는
    # docstring + thin delegate 만 유지.

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
            - 그룹 계열사/출자 구조 파악 - 지배구조 분석의 기초 데이터
            - 순환출자 탐지로 거버넌스 리스크 감지

        Guide:
            - "계열사 관계도" → c.network() 또는 c.network().show()
            - "같은 그룹 계열사" → c.network("members")
            - "출자/지분 구조" → c.network("edges")
            - "순환출자 있어?" → c.network("cycles")

        SeeAlso:
            - governance: 이사회/감사위원/최대주주 분석
            - capital: 주주환원 분석

        LLM Specifications:
            AntiPatterns:
                - view 미지정 시 NetworkView 객체 - 답변 본문에 dump X (.show() 로 별도)
                - hops > 2 (네트워크 폭주, 메모리 부담)
                - "순환출자 = 분식" 단정 X (한국 그룹 일반)
            OutputSchema:
                - view="members": 종목코드 / 종목명 / 그룹 / 지분율
                - view="edges": from / to / 지분율 / 출자유형
                - view="cycles": cycle 경로 (list[stockCode])
                - view="peers": ego 서브그래프 노드
            Freshness:
                대량보유/임원 공시 기준.

        Raises:
            없음.
        """
        from dartlab.providers.dart.builder.scanAggregator import buildScanNetwork

        return buildScanNetwork(self, view, hops=hops)

    def governance(self, view: str | None = None) -> pl.DataFrame | None:
        """지배구조 분석 (이사회, 감사위원, 최대주주).

        Capabilities:
            - 사외이사 비율 + 감사위원회 구성
            - 최대주주 지분율 + 특수관계인
            - 시장 전체 거버넌스 횡단 비교

        Args:
            view: None → 이 회사 행, "all" → 전체, "market" → 시장별 요약.

        Returns
        -------
        pl.DataFrame | None
            종목코드 : str - 6자리 종목코드
            종목명 : str - 회사명
            최대주주지분율 : float - 최대주주 + 특수관계인 지분율 (%)
            사외이사비율 : float - 사외이사 비율 (%)
            감사위원회 : str - 감사위원회 설치 여부
            종합점수 : float - 거버넌스 종합 점수 (100점 만점)
            등급 : str - A/B/C/D/E 등급
            데이터 없으면 None.

        Requires:
            데이터: DART 정기보고서 (자동 수집)

        Example::

            c = Company("005930")
            c.governance()           # 삼성전자 거버넌스
            c.governance("all")      # 전체 상장사

        AIContext:
            - 지배구조 리스크 평가 - 사외이사/감사위원/최대주주 정량 데이터
            - 시장 횡단 비교로 상대적 거버넌스 수준 판단

        Guide:
            - "지배구조 분석" → c.governance()
            - "사외이사 비율은?" → c.governance()
            - "전체 상장사 거버넌스 비교" → c.governance("all")

        SeeAlso:
            - network: 출자/계열사 관계 (거버넌스의 다른 관점)
            - audit: 감사 리스크 (감사위원회와 연관)

        LLM Specifications:
            AntiPatterns:
                - view="all" 호출 후 전체 결과를 답변 본문에 dump (수천 행)
                - 종합점수 단독 노출 (사외이사 비율 + 최대주주 지분율 함께)
            OutputSchema:
                - 종목코드 : str - 6 자리
                - 종목명 : str
                - 최대주주지분율 : float - % (특수관계인 포함)
                - 사외이사비율 : float - %
                - 감사위원회 : str - 설치 여부
                - 종합점수 : float - 100 점 만점
                - 등급 : str - A/B/C/D/E
            Freshness:
                정기보고서 마감 후 30~45 일.
            TargetMarkets:
                - KR (DART)

        Raises:
            없음.

        Returns:
            pl.DataFrame [종목코드, 종목명, 최대주주지분율, 사외이사비율, 감사위원회, 종합점수, 등급] 또는 None.
        """
        from dartlab.providers.dart.builder.scanAggregator import buildScanGovernance

        return buildScanGovernance(self, view)

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
            - 인력 효율성/근무환경 정량 평가 - 1인당 매출, 급여 수준 비교
            - 시장 횡단 비교로 인적자원 경쟁력 판단

        Guide:
            - "직원 현황" → c.workforce()
            - "평균 급여는?" → c.workforce()
            - "전체 상장사 인력 비교" → c.workforce("all")

        SeeAlso:
            - governance: 이사회/감사위원 구성 (인력의 다른 관점)
            - show: c.panel("employee")로 docs 기반 직원 상세

        LLM Specifications:
            AntiPatterns:
                - 평균 급여 단독 노출 (1 인당 매출 + 평균 근속 함께)
                - "고임금 = 위험" 단정 X (생산성 함께)
            OutputSchema:
                - 종목코드 : str
                - 직원수 : int - 정규/비정규 합계
                - 평균근속 : float - 년
                - 1인당매출 : float - 억원
            Freshness:
                정기보고서 마감 후 30~45 일.
            TargetMarkets:
                - KR

        Raises:
            없음.
        """
        from dartlab.providers.dart.builder.scanAggregator import buildScanWorkforce

        return buildScanWorkforce(self, view)

    def capital(self, view: str | None = None) -> pl.DataFrame | None:
        """주주환원 분석 (배당, 자사주, 총환원율).

        Capabilities:
            - 배당수익률 + 배당성향 추이
            - 자사주 매입/소각 이력
            - 총주주환원율 (배당 + 자사주)
            - 시장 전체 주주환원 횡단 비교

        Args:
            view: None → 이 회사 행, "all" → 전체, "market" → 시장별 요약.

        Returns
        -------
        pl.DataFrame | None
            종목코드 : str - 6자리 종목코드
            종목명 : str - 회사명
            배당수익률 : float - 배당수익률 (%)
            배당성향 : float - 배당성향 (%)
            자사주매입 : int - 자사주 매입 주수 (주)
            총환원율 : float - (배당 + 자사주) / 시가총액 (%)
            분류 : str - 환원형/중립/희석형
            데이터 없으면 None.

        Requires:
            데이터: DART 정기보고서 (자동 수집)

        Example::

            c = Company("005930")
            c.capital()              # 삼성전자 주주환원
            c.capital("all")         # 전체 상장사

        AIContext:
            - 주주환원 정책 평가 - 배당수익률/성향/자사주 정량 데이터
            - 시장 횡단 비교로 상대적 환원 수준 판단

        Guide:
            - "배당 정보" → c.capital() 또는 c.panel("dividend")
            - "주주환원율은?" → c.capital()
            - "전체 상장사 배당 비교" → c.capital("all")

        SeeAlso:
            - show: c.panel("dividend")로 docs 기반 배당 상세
            - sceMatrix: 자본변동표 (배당/자사주가 자본에 미치는 영향)
            - debt: 부채 구조 (자본 정책의 다른 면)

        LLM Specifications:
            AntiPatterns:
                - 배당수익률 단독 노출 (배당성향 + 자사주 함께)
                - "환원형" 단정 X (총환원율 + 분류 + 시계열 함께)
            OutputSchema:
                - 종목코드 : str
                - 배당수익률 : float - %
                - 배당성향 : float - %
                - 자사주매입 : int - 주
                - 총환원율 : float - % ((배당 + 자사주) / 시가총액)
                - 분류 : str - 환원형 / 중립 / 희석형
            Freshness:
                정기보고서 마감 후 30~45 일.
            TargetMarkets:
                - KR

        Raises:
            없음.

        Returns:
            pl.DataFrame [종목코드, 종목명, 배당수익률, 배당성향, 자사주매입, 총환원율, 분류] 또는 None.
        """
        from dartlab.providers.dart.builder.scanAggregator import buildScanCapital

        return buildScanCapital(self, view)

    def debt(self, view: str | None = None) -> pl.DataFrame | None:
        """부채 구조 분석 (차입금, 부채비율, 만기 구조).

        Capabilities:
            - 총차입금 + 순차입금 규모
            - 부채비율 + 차입금의존도
            - 단기/장기 차입금 비율
            - 시장 전체 부채 구조 횡단 비교

        Args:
            view: None → 이 회사 행, "all" → 전체, "market" → 시장별 요약.

        Returns
        -------
        pl.DataFrame | None
            종목코드 : str - 6자리 종목코드
            종목명 : str - 회사명
            부채비율 : float - 부채비율 (%)
            차입금의존도 : float - 차입금의존도 (%)
            ICR : float - 이자보상배율 (배)
            위험등급 : str - 안전/주의/경고/위험
            데이터 없으면 None.

        Requires:
            데이터: DART 정기보고서 (자동 수집)

        Example::

            c = Company("005930")
            c.debt()                 # 삼성전자 부채 구조
            c.debt("all")            # 전체 상장사

        AIContext:
            - 부채 구조/건전성 정량 평가 - 차입금 의존도, 만기 구조
            - 시장 횡단 비교로 상대적 재무 안정성 판단

        Guide:
            - "부채 구조 분석" → c.debt()
            - "부채비율은?" → c.debt() 또는 c.panel("ratios")
            - "전체 상장사 부채 비교" → c.debt("all")

        SeeAlso:
            - BS: 재무상태표 (부채 원본 데이터)
            - ratios: 재무비율 (부채비율 포함)
            - capital: 주주환원 (자본 정책의 다른 면)

        LLM Specifications:
            AntiPatterns:
                - 부채비율 단독 노출 (ICR + 의존도 함께)
                - "위험" 단정 X (위험등급 + 절대값 + peer median 함께)
            OutputSchema:
                - 종목코드 : str
                - 부채비율 : float - %
                - 차입금의존도 : float - %
                - ICR : float - 배 (이자보상배율)
                - 위험등급 : str - 안전 / 주의 / 경고 / 위험
            Freshness:
                정기보고서 마감 후 30~45 일.
            TargetMarkets:
                - KR

        Raises:
            없음.

        Returns:
            pl.DataFrame [종목코드, 부채비율, 차입금의존도, ICR, 위험등급] 또는 None.
        """
        from dartlab.providers.dart.builder.scanAggregator import buildScanDebt

        return buildScanDebt(self, view)

    @property
    def quant(self):
        """주가 기술적 분석 (31축). 기술지표/벤치마크/팩터/감성/최적화. dual access.

        Guide:
            - "차트 판단" → c.quant("판단")
            - "모멘텀" → c.quant("모멘텀")
            - "지표 DF" → c.quant("지표")
            - "베타" → c.quant("베타")
            - "섹터 베타" → c.quant("베타", benchmarkMode="sector")

        실제 동작은 ``_quantImpl`` 참조.

        Returns
        -------
        CallableAccessor
            dual-access proxy. 호출 시 ``_quantImpl`` 이 axis 따라
            ``pl.DataFrame`` (지표 시계열) 또는 dict (판단/팩터 등) 반환.
            상세는 ``_quantImpl`` docstring.

        Raises:
            없음.

        Example:
            >>> Company("005930").quant()

        SeeAlso:
            - ``_quantImpl`` - 실 구현 (31 축 dispatch).
            - ``dartlab.quant.Quant`` - backend SSOT.
            - ``edgar.Company.quant`` - US 패리티 (Naver vs Yahoo origin 차이).

        Requires:
            - dartlab
            - polars

        Capabilities:
            - 31 축 기술 분석 (기술지표/벤치마크/팩터/감성/최적화) dual-access. self.stockCode
              자동 바인딩. axis 미지정 시 카탈로그 + 한글 axis 한정.

        AIContext:
            주가 기반 기술 판단 entry - 재무 (analysis) 와 분리. ``c.quant("판단")`` 종합 verdict.
        """
        from dartlab.core.dualAccess import CallableAccessor

        if "_quantAccessor" not in self._cache:
            self._cache["_quantAccessor"] = CallableAccessor(self._quantImpl, name="quant")
        return self._cache["_quantAccessor"]

    def _quantImpl(self, axis=None, *, overrides: dict | None = None, metric=None, **kwargs):
        """주가 기술적 분석 - 30축 (내부 구현).

        Args:
            axis: 축 이름. None이면 30축 가이드 DataFrame.
                  (Phase 8 A1: 기존 `metric=` 은 호환 alias)
            overrides: 기술 분석 파라미터 교체. 키: window/threshold/period/benchmark.
            **kwargs: 축별 추가 파라미터.

        Returns:
            axis=None → DataFrame (30축 가이드)
            axis="종합" → dict (verdict, RSI, ADX, SMA 등)
            axis="지표" → DataFrame (45개 지표)

        Guide:
            When: 주가 기반 기술적 판단이 필요할 때.
            How: axis 로 분석 영역 지정. 무인자 = 가이드.
            Verified:
                - quant("판단") → RSI/ADX/MACD/볼린저/상대강도 + 종합 판정 (observed via ai-ask, 2026-04-25 - 정식 Phase P 판정 아님)

        LLM Specifications:
            AntiPatterns:
                - 영문 axis ("momentum") 사용 (실제는 한글 "모멘텀")
                - metric= 인자 사용 (Phase 8 deprecated alias - axis= 사용)
                - overrides 키 추측 (window/threshold/period/benchmark 만)
            OutputSchema:
                - axis="판단": dict - verdict (str) + RSI/ADX/SMA/MACD 등 핵심 지표
                - axis="지표": DataFrame - 45 개 기술 지표 컬럼
                - axis="베타": dict - beta 값 + benchmark + window
            Freshness:
                price 데이터 기준 - T+1 (전일 종가).
        """
        from dartlab.quant import Quant
        from dartlab.synth.overrides import validateOverrides

        if axis is None and metric is not None:
            axis = metric
        clean = validateOverrides(overrides, engine="quant")
        merged = {**clean, **kwargs}
        q = Quant()
        if axis is None:
            return q()
        result = q(axis, self.stockCode, **merged)
        if isinstance(result, dict):
            from dartlab.synth.overrides import buildAssumptions

            enriched = {
                **result,
                **{k: v for k, v in merged.items() if k in ("window", "threshold", "period", "benchmark")},
            }
            assumptions = buildAssumptions(enriched, engine="quant", overrides=clean)
            if assumptions:
                result.setdefault("assumptions", assumptions)
        return result

    def macro(self, axis=None, target=None, *, overrides: dict | None = None, **kwargs):
        """시장 매크로 (6막 인과 - 사이클/재고/기업/정책/유동성/심리/시나리오). KR 자동 위임.

        Returns
        -------
        pl.DataFrame | dict
            axis=None: 가이드 DataFrame (axis/label/description/example/group).
            axis 지정: dict - 축별 매크로 분석 결과 (indicators, narrative 포함).

        Guide:
            When: 거시경제 환경·사이클 판단이 필요할 때.
            How: axis 로 분석 영역 지정. 무인자 = 가이드.
            - "매크로" → c.macro()
            - "경기 사이클" → c.macro("사이클")
            - "위기 진단" → c.macro("위기")
            - "2008 시나리오" → c.macro("시나리오", "2008 금융위기")
            Verified:
                - macro("사이클") → CLI + 사분면 + 금리 + 유동성 + 심리 6축 (observed via ai-ask, 2026-04-25 - 정식 Phase P 판정 아님)
                - macro + analysis → 경제 고려한 종목 분석 (observed via thesis ai-ask, 2026-04-25 - 정식 Phase P 판정 아님)

        LLM Specifications:
            AntiPatterns:
                - axis 추측 (한글 - 사이클 / 위기 / 시나리오 / 유동성 / 심리)
                - 종목 매크로 = 시장 매크로 혼동 (이건 c.macro = 시장 KR 자동)
            OutputSchema:
                - axis="사이클": dict - quadrant + indicators + narrative
                - axis="시나리오": dict - historical analogue + projection
                - axis 미지정: 가이드 DataFrame
            Freshness:
                ECOS / FRED 갱신 주기 (월 / 분기).

        Raises:
            없음.

        Example:
            >>> Company("005930").macro()

        Args:
            axis: 매크로 축 (한글 - "사이클" / "위기" / "시나리오" / "유동성" / "심리"). None 이면 가이드.
            target: axis="시나리오" 시 시나리오 이름 (예 "2008 금융위기").
            overrides: 매크로 가정 교체 dict.
            **kwargs: 축별 추가 인자.

        SeeAlso:
            - ``dartlab.macro.Macro`` - 매크로 backend SSOT.
            - ``edgar.Company.macro`` - US 패리티.

        Requires:
            - dartlab
            - polars

        Capabilities:
            - KR 시장 매크로 (ECOS + KRX 데이터) 자동 위임. market="KR" 자동 주입. KR 회사 매크로 영향
              분석 entry - US 회사는 edgar.macro 별도.

        AIContext:
            거시환경 회사 영향 답변 시 본 함수. axis 미지정 시 가이드 반환 - AI 가 카탈로그 먼저 확인.
        """
        from dartlab.macro import Macro

        return Macro()(axis, target, market="KR", overrides=overrides, company=self, **kwargs)

    # ── Phase 10 H2: story 2차 가공 직접 노출 (AI tool 자동 수집 대상) ──

    def causalWeights(self) -> list[dict]:
        """6막 인과 가중치 - 수익구조→수익성→현금흐름→자금조달→자산배치→가치평가 amplify/dampen/neutral.

        Guide:
            - "인과 체인" → c.causalWeights()
            - "어느 막이 약해" → 결과의 direction='dampen' 필터

        Returns:
            list[dict] - from_act/to_act/metric_from/metric_to/delta_from/delta_to/weight/direction

        LLM Specifications:
            AntiPatterns:
                - direction 단독 인용 (weight + metric 함께)
                - 6 막 인과는 종목 분석 한정 - 매크로 / 산업 분석에는 부적합
            OutputSchema:
                - from_act : str - 출발 막
                - to_act : str - 도착 막
                - metric_from : str - 출발 지표
                - metric_to : str - 도착 지표
                - delta_from / delta_to : float - 변화율
                - weight : float - 영향 강도
                - direction : str - amplify / dampen / neutral
            Freshness:
                finance 시계열 시점.

        Raises:
            없음.

        Example:
            >>> Company("005930").causalWeights()

        SeeAlso:
            - ``valuationImpact`` - 본 가중치를 DCF override 로 변환.
            - ``storyTree`` - 본 가중치 적용한 3 trajectory.
            - ``dartlab.story.narrative.buildCausalWeights`` - implementation.

        Requires:
            - dartlab
            - polars

        Capabilities:
            - 6 막 (수익구조→수익성→현금흐름→자금조달→자산배치→가치평가) 의 인과 가중치 (amplify/
              dampen/neutral) 계산. 매 막 출발/도착 지표 + delta + weight + direction.

        AIContext:
            AI 가 "이 회사 핵심 인과 chain" 답변 시 본 함수 결과 인용 - 단일 지표가 아닌 chain 구조.
        """
        import importlib

        buildCausalWeights = importlib.import_module("dartlab.story.narrative").buildCausalWeights

        return buildCausalWeights(self, {})

    def valuationImpact(self) -> dict:
        """인과 체인에서 DCF override 힌트 - narrative → 숫자 피드백.

        Guide:
            - "WACC 조정 어떻게" → c.valuationImpact()['waccAdj']
            - "override 근거" → c.valuationImpact()['narrative']

        Returns:
            dict - terminalGrowthAdj/waccAdj/narrative/overrides

        LLM Specifications:
            AntiPatterns:
                - waccAdj 단독 노출 (narrative 근거 함께)
                - DCF 직접 override 적용 X (overrides 는 힌트, 사용자 판단 후 적용)
            OutputSchema:
                - terminalGrowthAdj : float - terminal growth 가산 (% 포인트)
                - waccAdj : float - WACC 가산 (% 포인트)
                - narrative : str - 조정 근거 (인과 체인)
                - overrides : dict - analysis(valuation, overrides=...) 호출용
            Freshness:
                story 인과 체인 기준 - finance 데이터 시점.

        Raises:
            없음.

        Example:
            >>> Company("005930").valuationImpact()

        SeeAlso:
            - ``causalWeights`` - 본 함수의 입력 chain.
            - ``storyTree`` - 본 override 적용 3 시나리오.
            - ``analysis("valuation")`` - 본 overrides 직접 주입 가능.

        Requires:
            - dartlab
            - polars

        Capabilities:
            - causalWeights chain → DCF 파라미터 (terminalGrowth/WACC) 가산 + narrative 근거.
              narrative → 숫자 피드백 - AI 가 직접 override 적용 가능한 hint dict.

        AIContext:
            narrative 가 valuation 어떻게 바꾸나 답변 시 본 함수. base/adjusted 비교 의무.
        """
        import importlib

        _narrative = importlib.import_module("dartlab.story.narrative")
        buildCausalWeights = _narrative.buildCausalWeights
        buildValuationImpact = _narrative.buildValuationImpact

        chains = buildCausalWeights(self, {})
        return buildValuationImpact(chains)

    def storyTree(self, *, basePeriod: str | None = None) -> dict:
        """Damodaran 3P - possible(낙관)/plausible(중도)/probable(보수) 3 DCF + 민감도.

        Guide:
            - "3 시나리오 가치" → c.storyTree()
            - "서사 민감도" → c.storyTree()['summary']['spreadPct']

        Returns:
            dict - possible/plausible/probable + summary {min/max/spread/spreadPct/mean}

        LLM Specifications:
            AntiPatterns:
                - 단일 시나리오 (예: probable) 만 인용 (3 시나리오 + 분포 함께)
                - spreadPct 가 작으면 "확실" 단정 X (가정 강도와 함께)
            OutputSchema:
                - possible : dict - 낙관 시나리오 DCF 결과
                - plausible : dict - 중도 시나리오
                - probable : dict - 보수 시나리오
                - summary : dict - min / max / spread / spreadPct / mean
            Freshness:
                finance 시계열 시점.

        Raises:
            없음.

        Args:
            basePeriod: 기준 fiscal period. None 이면 최신 분기.

        SeeAlso:
            - ``causalWeights`` / ``valuationImpact`` - 본 함수의 입력 시나리오.
            - ``validateStory`` - 본 결과의 plausibility 검증.

        Requires:
            - dartlab
            - polars

        Capabilities:
            - possible (낙관) / plausible (중도) / probable (보수) 3 DCF 계산 + spread/mean 요약.
              Damodaran 3P 방법론.

        AIContext:
            AI 가 "이 회사 가치 시나리오" 답변 시 본 함수 3 trajectory 인용. 단일 값 X.
        """
        import importlib

        buildStoryTree = importlib.import_module("dartlab.story.storyTree").buildStoryTree

        return buildStoryTree(self, basePeriod=basePeriod)

    def narrativeDiff(self, *, claims: list[str] | None = None) -> list[dict]:
        """각 claim 제거 시 dFV 변화 - Thought Anchors 기반 정량 기여도.

        Guide:
            - "가치 기여도" → c.narrativeDiff()
            - "낮은WACC 기여 몇%" → 결과 필터 claim='낮은WACC'

        Returns:
            list[dict] - claim/dFV_neutral/delta_abs/delta_pct/contribution

        LLM Specifications:
            AntiPatterns:
                - contribution 단독 인용 (delta_abs + delta_pct 함께)
                - claim 추측 (default 또는 명시 list 만)
            OutputSchema:
                - claim : str - narrative claim 식별자
                - dFV_neutral : float - 중립 시나리오 가치
                - delta_abs : float - claim 제거 시 절대 변화
                - delta_pct : float - % 변화
                - contribution : float - 기여도 (정규화)
            Freshness:
                story 인과 체인 시점.

        Raises:
            없음.

        Example:
            >>> Company("005930").narrativeDiff()

        Args:
            claims: 영향 분석 대상 claim 리스트. None 이면 전체 default claims.

        SeeAlso:
            - ``storyTree`` - base trajectory.
            - ``causalWeights`` - claim 가중치.
            - ``dartlab.story.narrativeDiff.computeImpact`` - implementation.

        Requires:
            - dartlab
            - polars

        Capabilities:
            - 각 claim 제거 후 FV 재계산 → contribution 측정. Thought Anchors 기반 정량 기여도.

        AIContext:
            AI 가 "이 valuation 핵심 가정" 답변 시 본 함수 결과 contribution 큰 순 인용.
        """
        import importlib

        computeImpact = importlib.import_module("dartlab.story.narrativeDiff").computeImpact

        return computeImpact(self, claims=claims)

    def industry(self) -> dict:
        """이 회사의 밸류체인 산업 내 위치를 분석한다.

        Returns:
            dict | None: 산업 내 위치 정보.
                chainId, chainName, stage, stageLabel, confidence, matches, products, peers.
                매칭 실패 시 None.

        Example::

            c = Company("005930")
            pos = c.industry()
            # {'chainId': 'semiconductor', 'stage': 'fab', 'stageLabel': '전공정(FAB)', ...}

        LLM Specifications:
            AntiPatterns:
                - sector 와 industry 혼동 (sector = 11 대 분류, industry = 가치 사슬 위치)
                - peers 추측 (industry().peers 가 실제 매칭된 종목)
                - confidence 무시하고 단정 (낮으면 매칭 신뢰도 낮음)
            OutputSchema:
                - chainId : str - 산업 체인 ID (semiconductor / automobile / ...)
                - chainName : str - 한글 산업명
                - stage : str - upstream / midstream / downstream / fab / equipment / ...
                - stageLabel : str - 한글 단계 레이블
                - confidence : float - 0.0~1.0 매칭 신뢰도
                - peers : list[str] - 같은 stage 종목코드
            Freshness:
                산업 지도 정의 시점 - 운영자 수동 업데이트.

        Raises:
            없음.

        SeeAlso:
            - ``sector`` - WICS 11 대 섹터 분류 (industry 와 다른 차원).
            - ``sectorParams`` - 섹터별 valuation 파라미터.
            - ``dartlab.industry.calcs.companyCalcs.calcChainPosition`` - 본 함수 backend.

        Requires:
            - dartlab
            - polars

        Capabilities:
            - 회사의 산업 밸류체인 내 위치 (upstream/midstream/downstream/fab/equipment 등) 분류 +
              같은 stage peer 종목코드 list 반환. sector vs industry 분리 - 후자는 가치사슬 차원.

        Guide:
            - "이 회사 가치사슬 어디" → 본 함수.
            - "같은 stage peer" → result["peers"].

        AIContext:
            동종 비교 시 sector (11 대) 보다 chain stage 가 더 정밀 - AI 가 peer 선정에 본 함수 활용.
        """
        from dartlab.industry.calcs.companyCalcs import companyIndustryResult

        return companyIndustryResult(self)

    def view(self, *, port: int = 8400) -> None:
        """브라우저에서 공시 뷰어를 엽니다.

        Capabilities:
            - 로컬 서버 기반 공시 뷰어 실행
            - 브라우저에서 panel/index 탐색

        Args:
            port: 로컬 서버 포트. 기본 8400.

        Returns:
            None

        Requires:
            데이터: panel parquet (자동 다운로드)

        Example::

            c = Company("005930")
            c.view()

        AIContext:
            - 시각적 탐색 인터페이스 - 사용자가 브라우저에서 직접 데이터 탐색

        Guide:
            - "공시 뷰어 열어줘" → c.view()
            - "브라우저에서 보기" → c.view()

        SeeAlso:
            - index: 뷰어가 소비하는 메타데이터 (프로그래밍 접근)
            - panel: 뷰어의 원본 데이터

        Raises:
            없음.

        LLM Specifications:
            AntiPatterns:
                - headless 환경 (CI/docker) 호출 → 브라우저 launch 실패. notebooks/JupyterLab 전용.
                - 점유된 포트 → OSError. caller port 변경 의무.
            OutputSchema:
                - None - side effect (브라우저 자동 open).
            Prerequisites:
                - 로컬 표시 가능 환경 + dartlab.providers._common.viewer.
            Freshness:
                - 호출 시점 (서버 데이터 별도 fetch X).
            Dataflow:
                - self.stockCode → launchViewer → FastAPI 서버 + 브라우저 open.
            TargetMarkets:
                - KR (DART 정기보고서 viewer).
        """
        from dartlab.providers._common.viewer import launchViewer

        launchViewer(self.stockCode, port=port)

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
            str - LLM 응답 텍스트. ``stream=True`` 면 ``Generator[str]``.

        Raises:
            ValueError: provider/model 미설정 + 환경변수 키 부재.
            RuntimeError: LLM API 호출 실패 (네트워크/quota).

        Requires:
            API 키: LLM provider API 키 (``OPENAI_API_KEY`` 등).

        Example:
            >>> c = Company("005930")
            >>> c.ask("영업이익률 추세는?")
            >>> c.ask("핵심 리스크 3가지", provider="codex")

            # 스트리밍
            for chunk in c.ask("배당 분석해줘", stream=True):
                print(chunk, end="")

        Guide:
            - "영업이익률 분석해줘" → c.ask("영업이익률 추세는?")
            - "AI한테 질문하고 싶어" → c.ask("질문")
            - "스트리밍으로 답변받기" → c.ask("질문", stream=True)

        SeeAlso:
            - chat: 에이전트 모드 (tool calling 기반 심화 분석)
            - ask: AI 종합 분석 (자연어 대화)
            - story: AI 없는 데이터 검토서

        LLM Specifications:
            AntiPatterns:
                - 응답 직접 외부 인용 → AI 환각 검증 의무. dartlab tool 결과만 신뢰.
                - reflect=True 항상 정확 X - 시간/토큰 2 배.
                - stream=True 결과 list() 즉시 변환 → stream 의미 사라짐.
            OutputSchema:
                - str (stream=False) 또는 Generator[str] (stream=True).
            Prerequisites:
                - LLM API 키 (OPENAI_API_KEY / ANTHROPIC_API_KEY 환경변수).
            Freshness:
                - LLM 응답 + 본 회사 데이터 freshness 의 min.
            Dataflow:
                - question + self.stockCode → ai.kernel.ask → tool calling → 본 함수.
            TargetMarkets:
                - KR (DART) - workbench evidence + ask 인터페이스.
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

    def calendar(self, *, horizonDays: int = 30) -> "pl.DataFrame":
        """다가오는 정기공시 catalyst 일정 추론 (Korea 시장).

        본 회사 disclosure history 를 수집해 providers/dart/calendar 에 위임.
        intra-package import 라 cycle 0 (gather 의존 X).

        Args:
            horizonDays: 미래 horizon (기본 30 일).

        Returns:
            catalyst DataFrame.

        Raises:
            없음.

        Example:
            >>> Company("005930").calendar()

        SeeAlso:
            - ``dartlab.providers.dart.ops.calendar.predictCalendar`` - backend cycle 추론.
            - ``edgar.Company.calendar`` - US 패리티 (현재 미구현 stub).

        Requires:
            - dartlab
            - polars

        Capabilities:
            - 본 회사 disclosure history (최근 400 일 정기공시) → predictCalendar 위임 → 정기보고서
              cycle 추론 (분기/반기/사업보고서 패턴). horizonDays 내 예상 공시일 리스트.

        Guide:
            - "다음 정기공시 언제" → 본 함수.

        AIContext:
            AI 가 "다음 공시 catalyst" 답변 시 본 함수 결과 인용. 예상일 ± 며칠 명시 의무.

        LLM Specifications:
            AntiPatterns:
                - history 부재 회사 (신규 상장) → 빈 DataFrame. caller 분기 의무.
                - horizon 큰 값 (>180) → 예측 정확도 낮음 - 분기 1 회 cycle 한정.
            OutputSchema:
                - pl.DataFrame (OUTPUT_SCHEMA) - [stockCode, expectedDate, reportType, confidence].
            Prerequisites:
                - disclosure history (최근 400 일).
            Freshness:
                - 호출 시점 (disclosure() API 실시간).
            Dataflow:
                - disclosure(days=400, type="A") → predictCalendar(history, horizonDays) → 본 함수.
            TargetMarkets:
                - KR (DART 정기공시 cycle).
        """
        from dartlab.providers.dart.ops.calendar import OUTPUT_SCHEMA, predictCalendar

        history = self.disclosure(days=400, type="A")
        if history is None or history.is_empty():
            return pl.DataFrame(schema=OUTPUT_SCHEMA)
        return predictCalendar({self.stockCode: history}, horizonDays=horizonDays)


# ── DisclosureFetcher 구현 + register (정공법 B - DIP) ─────────────


class _DartDisclosureFetcher:
    """gather/Calendar 가 사용할 DART 공시 수집 어댑터."""

    def fetch(self, stockCode, *, days=400, type="A", limit: int | None = None):
        """단일 종목 공시 history 반환. 실패 시 None.

        Args:
            stockCode: 종목코드.
            days: 조회 일수.
            type: 공시 타입 (A=정기·B=수시 등).
            limit: 최대 행 수. None 이면 무제한 (단건 컨텍스트라 통상 미사용).

        Returns:
            DataFrame 또는 None.

        Example:
            >>> _DartDisclosureFetcher().fetch("005930", days=90, limit=10)

        Raises:
            없음.

        SeeAlso:
            - ``Company.disclosure`` - 본 함수가 호출하는 backend.
            - ``dartlab.core.disclosureFetcher.registerDisclosureFetcher`` - gather/Calendar 의존성 주입.

        Requires:
            - dartlab
            - polars

        Capabilities:
            - gather/Calendar 의 DisclosureFetcher 어댑터 - Company.disclosure() 위임 + 예외 silent.
              DIP (정공법 B) 패턴 - Calendar 가 직접 Company import 회피.

        Guide:
            - 자동 등록 (import 시점) - 직접 호출 X.

        AIContext:
            본 어댑터는 인프라 layer - AI 가 직접 사용 X. gather/calendar 가 내부 사용.

        LLM Specifications:
            AntiPatterns:
                - 본 클래스 직접 인스턴스화 → 무의미. registerDisclosureFetcher 가 자동 등록.
                - 예외 silent (None 반환) → caller 가 None 분기 의무.
            OutputSchema:
                - pl.DataFrame 또는 None (예외 시).
            Prerequisites:
                - Company.disclosure 가용 (DART_API_KEY).
            Freshness:
                - Company.disclosure 와 동일 (DART API 실시간).
            Dataflow:
                - stockCode → Company(stockCode).disclosure(days, type) → head(limit) → 본 어댑터.
            TargetMarkets:
                - KR (DART).
        """
        try:
            df = Company(stockCode).disclosure(days=days, type=type)
        except (OSError, ValueError, RuntimeError):
            return None
        if df is not None and limit is not None:
            df = df.head(limit)
        return df


def _registerDartDisclosureFetcher() -> None:
    """import 시점 등록."""
    from dartlab.core.disclosureFetcher import registerDisclosureFetcher

    registerDisclosureFetcher(_DartDisclosureFetcher())


_registerDartDisclosureFetcher()
