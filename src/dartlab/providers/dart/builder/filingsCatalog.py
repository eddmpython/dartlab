"""DART Company 의 공시 메타·원문 조회 backend.

Company.filings / update / disclosure / liveFilings / readFiling 5 진입점은
DART API + 로컬 parquet 의 공시 메타데이터 + ZIP 원문 처리. Company facade 가
본 모듈의 build* 함수에 thin delegate.

Module-level builders:
    buildFilings      — 로컬 보유 공시 목록 (parquet)
    buildUpdate       — 누락 공시 증분 수집
    buildDisclosure   — OpenDART 공시 목록 (단일 종목)
    buildLiveFilings  — OpenDART 실시간 공시 (정규화)
    buildReadFiling   — 공시 원문 텍스트 / ZIP 섹션
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

import polars as pl

from dartlab.core.dataLoader import DART_VIEWER
from dartlab.core.memory import lookupCache
from dartlab.core.polarsUtil import isEmptyDf
from dartlab.providers._common.filingHelpers import (
    filingRecord,
    filterFilingsByKeyword,
    resolveDateWindow,
    truncateText,
)
from dartlab.providers.dart.panel.text import panelTextRows

if TYPE_CHECKING:
    from dartlab.providers.dart.company import Company


_RCEPT_NO_PATTERN = re.compile(r"[?&]rcpNo=(\d{14})")

_FILINGS_SCHEMA = {
    "year": pl.Utf8,
    "rceptDate": pl.Utf8,
    "rceptNo": pl.Utf8,
    "reportType": pl.Utf8,
    "dartUrl": pl.Utf8,
}


def _emptyFilingsFrame() -> pl.DataFrame:
    return pl.DataFrame(schema=_FILINGS_SCHEMA)


# ── filings (panel provenance) ───────────────────────────────────


def buildFilings(company: Company) -> pl.DataFrame | None:
    """종목의 보유 공시 목록 + DART 뷰어 링크 (panel 기반).

    Capabilities:
        - panel row 의 ``rceptNo`` 기준 unique (한 보고서당 1 row).
        - DART 뷰어 URL 자동 조합 (``DART_VIEWER`` + rceptNo).
        - ``year``/``rceptDate`` 내림차순 정렬 (최신이 먼저).
        - panel artifact 부재 (``_hasPanel=False``) → 빈 schema DataFrame.

    Args:
        company: Company 인스턴스 (Company facade 의 self).

    Returns:
        pl.DataFrame — 컬럼 ``year`` (Utf8) / ``rceptDate`` (Utf8) / ``rceptNo`` (Utf8) /
        ``reportType`` (Utf8) / ``dartUrl`` (Utf8). panel 부재 시 빈 schema DataFrame.

    Example:
        >>> # df = buildFilings(c)
        >>> # df.head()

    Guide:
        - "삼성전자 공시 목록" → ``c.filings()`` → 본 함수.
        - "DART 뷰어로 열기" → ``df.row(0)["dartUrl"]``.
        - "공시 검색 (OpenDART 직접)" → ``buildDisclosure``.

    SeeAlso:
        - ``buildUpdate`` — 본 함수의 누락 공시 증분 수집 자매.
        - ``buildDisclosure`` — OpenDART 직접 호출 (로컬 parquet X).
        - ``Company.filings`` — 본 함수의 facade.
        - ``dartlab.providers.dart.panel.text.panelTextRows`` / ``DART_VIEWER`` — 데이터/URL source.

    Requires:
        - polars — DataFrame.
        - dartlab.core.dataLoader — DART_VIEWER 상수.
        - dartlab.providers.dart.panel.text — panelTextRows.

    AIContext:
        Workbench "이 회사 공시 목록" / "최근 보고서" 질문 entry. 로컬 panel 기반이라 빠름.
        OpenDART rate limit 무관. ``_hasPanel=False`` 회사 (예 비상장/신규 종목) → 빈 결과 →
        caller 는 ``buildDisclosure`` fallback.

    LLM Specifications:
        AntiPatterns:
            - panel artifact 결락 → 빈 schema. caller 는 height 0 검사 후 buildDisclosure 시도.
            - rceptNo 중복 → unique 로 자동 1 개만 유지.
        OutputSchema:
            - 컬럼 5 (year/rceptDate/rceptNo/reportType/dartUrl).
            - 정렬: year + rceptDate 내림차순.
        Prerequisites:
            - gather panel 이 stockCode 수집 완료.
        Freshness:
            - panel 수집 시점 의존. 본 함수 무상태.
        Dataflow:
            - gather → panel parquet → panelTextRows → 본 함수 → AI 답변.
        TargetMarkets:
            - KR (DART) 한정. EDGAR 는 ``edgar`` provider 의 동등 함수.

    Raises:
        없음.
    """
    if not company._hasPanel:
        return _emptyFilingsFrame()

    df = panelTextRows(company.stockCode)
    if df is None or df.is_empty() or "rceptNo" not in df.columns:
        return _emptyFilingsFrame()

    period = pl.col("period").cast(pl.Utf8)
    rcept = pl.col("rceptNo").cast(pl.Utf8)
    filings = (
        df.select(
            period.str.slice(0, 4).alias("year"),
            rcept.str.slice(0, 8).alias("rceptDate"),
            rcept.alias("rceptNo"),
            pl.when(period.str.ends_with("Q4"))
            .then(pl.lit("사업보고서"))
            .when(period.str.ends_with("Q2"))
            .then(pl.lit("반기보고서"))
            .when(period.str.contains(r"Q[13]$"))
            .then(pl.lit("분기보고서"))
            .otherwise(period)
            .alias("reportType"),
        )
        .filter(pl.col("rceptNo").is_not_null() & (pl.col("rceptNo") != ""))
        .unique(subset=["rceptNo"], keep="first")
        .with_columns((pl.lit(DART_VIEWER) + pl.col("rceptNo")).alias("dartUrl"))
        .select(list(_FILINGS_SCHEMA))
        .sort(["year", "rceptDate", "rceptNo"], descending=[True, True, True])
    )
    return filings


# ── update (증분 수집) ───────────────────────────────────────────


def buildUpdate(company: Company, *, categories: list[str] | None = None) -> dict[str, int]:
    """누락 공시 증분 수집 — gather 의 1 회용 보수 (회사 1 종목 한정).

    Capabilities:
        - ``openapi.freshness.collectMissing`` wrapper — 로컬 parquet 와 OpenDART 공시 목록 diff.
        - 누락 row 만 fetch + parquet append.
        - categories 로 영역 한정 (finance / report). panel 은 별도 builder/pipeline 경로.

    Args:
        company: Company 인스턴스.
        categories: 수집 영역 list. None → 전체 영역 (gather 전체 카테고리).

    Returns:
        dict[str, int] — ``{category: 수집된 row 수}``.

    Example:
        >>> # buildUpdate(c, categories=["finance"])
        >>> # {"finance": 3}

    Guide:
        - "삼성전자 최신 재무/정형 공시 따라가기" → ``c.update(categories=["finance", "report"])``.
        - "전체 영역 갱신" → ``c.update()``.
        - 정기 batch update → 운영자가 gather 스크립트 사용 (본 함수는 1 종목 단위).

    SeeAlso:
        - ``buildFilings`` — 갱신 후 결과 조회.
        - ``buildDisclosure`` — 갱신 없이 OpenDART 직접 호출.
        - ``Company.update`` — 본 함수의 facade.
        - ``dartlab.gather.dart.freshness.collectMissing`` — 본 함수 본체.

    Requires:
        - dartlab.gather.dart.freshness — collectMissing.
        - DART_API_KEY 환경변수.

    AIContext:
        AI 가 "이 회사 어제자 공시 있냐" 같은 freshness 질문 받으면 본 함수 우선 호출 →
        buildFilings 재조회. 본문 panel 갱신은 panel builder/pipeline 경로가 담당.

    LLM Specifications:
        AntiPatterns:
            - DART_API_KEY 미설정 → ValueError (collectMissing 내부).
            - OpenDART rate limit 초과 → 일시 차단 (silent retry).
            - categories 가 정의된 카테고리 외 (예 "foobar") → 0.
        OutputSchema:
            - dict[str, int] — 카테고리당 1 키.
        Prerequisites:
            - DART_API_KEY. stockCode 가 KR 종목.
        Freshness:
            - 본 함수 호출 시점 갱신.
        Dataflow:
            - OpenDART → 본 함수 → parquet (append) → 후속 buildFilings 가 갱신 반영.
        TargetMarkets:
            - KR (DART) 한정.

    Raises:
        없음.
    """
    from dartlab.core.dartClient import collectMissing

    return collectMissing(company.stockCode, categories=categories)


# ── disclosure (OpenDART 공시 목록) ──────────────────────────────


def buildDisclosure(
    company: Company,
    start: str | None = None,
    end: str | None = None,
    *,
    days: int = 365,
    type: str | None = None,
    keyword: str | None = None,
    finalOnly: bool = False,
) -> pl.DataFrame:
    """OpenDART 단일 종목 공시 목록 직접 호출 — 로컬 parquet 무관.

    Capabilities:
        - ``openapi.dart.Dart`` 클라이언트 → 종목 단위 공시 목록 호출.
        - type 으로 공시 유형 코드 한정 (A 정기 / B 주요사항 / C 발행 / D 지분 / ...).
        - keyword 로 report_nm/corp_name/flr_nm 컬럼 substring 필터.
        - finalOnly 로 최종 보고서만 (정정 제외).
        - 비어있으면 빈 DataFrame, keyword 매칭 없으면 빈 결과.

    Args:
        company: Company 인스턴스.
        start: 시작일 (YYYYMMDD). None → days 기반.
        end: 종료일 (YYYYMMDD). None → 오늘.
        days: 기간 (start/end 미지정 시). 기본 365.
        type: 공시 유형 1 자 코드 (A/B/C/D/E/F/G/H/I/J).
        keyword: report_nm/corp_name/flr_nm contains 필터 (한국어 substring).
        finalOnly: True → 최종본만. False → 정정 포함.

    Returns:
        pl.DataFrame — OpenDART filings 원본 컬럼 (corp_code/corp_name/stock_code/
        rcept_no/rcept_dt/report_nm 등). 빈 경우 빈 DataFrame.

    Example:
        >>> # df = buildDisclosure(c, days=90, type="A")  # 정기공시 90 일

    Guide:
        - "삼성전자 최근 90 일 정기공시" → ``c.disclosure(days=90, type="A")``.
        - "특정 키워드 공시" → ``c.disclosure(days=365, keyword="배당")``.
        - "로컬 parquet 만으로 충분 (rate limit 회피)" → ``buildFilings``.

    SeeAlso:
        - ``buildFilings`` — 로컬 parquet 기반 (rate limit X).
        - ``buildLiveFilings`` — 정규화된 ``filedAt/title/formType`` schema.
        - ``Company.disclosure`` — 본 함수의 facade.
        - ``dartlab.providers._common.filingHelpers.filterFilingsByKeyword`` — 키워드 필터.

    Requires:
        - polars — DataFrame.
        - dartlab.gather.dart.dart — Dart 클라이언트.
        - DART_API_KEY 환경변수.
        - dartlab.providers._common.filingHelpers — filterFilingsByKeyword.

    AIContext:
        AI 가 "최근 X 일 공시" / "키워드 검색" / "특정 유형 공시" 질문 entry. 로컬 parquet
        (``buildFilings``) 의 freshness 한계 시 본 함수가 OpenDART 실시간 호출. rate limit
        20,000 회/일 — AI 가 여러 회사 batch 호출 시 주의.

    LLM Specifications:
        AntiPatterns:
            - DART_API_KEY 미설정 → ValueError.
            - rate limit 초과 → 일시 차단 (silent 빈 결과).
            - type 코드 오타 (예 "A1") → 빈 결과.
            - keyword 가 매우 짧음 (1~2 글자) → 과도 매칭.
        OutputSchema:
            - OpenDART 원본 컬럼. 컬럼명 snake_case (corp_code, rcept_no, ...).
        Prerequisites:
            - DART_API_KEY.
        Freshness:
            - 호출 시점 OpenDART 데이터.
        Dataflow:
            - OpenDART API → 본 함수 → AI 답변.
        TargetMarkets:
            - KR (DART) 한정. EDGAR 는 별도 provider.

    Raises:
        없음.
    """
    from dartlab.core.dartClient import dartCollector

    d = dartCollector()
    s = d(company.stockCode)
    df = s.filings(start, end, type=type, final=finalOnly)
    if df.is_empty():
        return df
    if keyword:
        df = filterFilingsByKeyword(df, keyword=keyword, columns=["report_nm", "corp_name", "flr_nm"])
    return df


# ── liveFilings (정규화 실시간) ──────────────────────────────────


def buildLiveFilings(
    company: Company,
    start: str | None = None,
    end: str | None = None,
    *,
    days: int | None = None,
    limit: int = 20,
    keyword: str | None = None,
    forms: list[str] | tuple[str, ...] | None = None,
    finalOnly: bool = False,
) -> pl.DataFrame:
    """OpenDART 실시간 공시 + ``docId/filedAt/title/formType/...`` schema 로 정규화.

    Capabilities:
        - ``openapi.dart.OpenDart`` 클라이언트 → 공시 목록 호출 + 정규화.
        - 컬럼 매핑 — rcept_no→docId, rcept_dt→filedAt, report_nm→title/formType/reportNm,
          rcept_no→viewerUrl (DART_VIEWER + rcept_no), market=lit("KR").
        - BoundedCache 사용 — 동일 (start, end, limit, keyword, finalOnly) 키 → cache hit.
        - keyword 필터 = report_nm/corp_name/flr_nm contains.
        - ``forms`` 인자 무시 (DART 에 forms 개념 X). public API liveFilings 시그니처 호환 유지.
        - limit > 0 시 head(limit).

    Args:
        company: Company 인스턴스.
        start: 시작일 (YYYYMMDD). None → days 기반.
        end: 종료일 (YYYYMMDD). None → 오늘.
        days: 기간. None → 기본 days.
        limit: 최대 row 수. 기본 20. 0 이하 → 전체.
        keyword: report_nm/corp_name/flr_nm contains 필터.
        forms: DART 미사용 (시그니처 호환). None.
        finalOnly: True → 최종본만.

    Returns:
        pl.DataFrame — 13 컬럼 ``docId/filedAt/title/formType/docUrl/indexUrl/market/
        corpName/stockCode/rceptNo/reportNm/viewerUrl/corpCls``. 빈 경우 빈 schema DataFrame.

    Example:
        >>> # buildLiveFilings(c, days=30, limit=10)

    Guide:
        - "삼성전자 최근 30 일 공시 (정규화)" → ``c.liveFilings(days=30, limit=10)``.
        - "정규화 X, OpenDART raw" → ``buildDisclosure``.
        - "로컬 parquet 만 사용" → ``buildFilings``.
        - cross-provider 호환 (edgar.liveFilings 와 동일 schema) → 본 함수.

    SeeAlso:
        - ``buildFilings`` / ``buildDisclosure`` — 다른 schema 의 동등 함수.
        - ``Company.liveFilings`` — 본 함수의 facade.
        - ``dartlab.gather.dart.dart.OpenDart`` — 본 함수 본체.
        - ``dartlab.providers._common.filingHelpers.resolveDateWindow`` — 날짜 윈도우 정규화.

    Requires:
        - polars — DataFrame.
        - dartlab.gather.dart.dart — OpenDart.
        - dartlab.providers._common.filingHelpers — filterFilingsByKeyword + resolveDateWindow.
        - dartlab.core.dataLoader — DART_VIEWER 상수.
        - dartlab.core.messaging — progress (사용자 알림).
        - DART_API_KEY.

    AIContext:
        Cross-provider 통합 코드 (예 KR + US 함께 공시 검색) 에서 본 함수 사용. dart/edgar
        의 liveFilings 가 동일 schema 라 ``pl.concat`` 으로 통합 가능. AI 가 "오늘자 공시"
        질문 처리 시 entry.

    LLM Specifications:
        AntiPatterns:
            - DART_API_KEY 미설정 → ValueError.
            - cache hit → OpenDART 무호출 (의도된 동작, freshness 의 양면).
            - forms 인자 사용 → 무시 (silent). caller 가 dart 한정으로 인지.
        OutputSchema:
            - 13 정규화 컬럼.
            - 정렬: OpenDART 원본 (대체로 최신순).
        Prerequisites:
            - DART_API_KEY. stockCode 가 KR 종목.
        Freshness:
            - cache TTL 내면 stale 가능. fresh 보장 시 cache key 변경 필요.
        Dataflow:
            - OpenDART → 본 함수 (정규화) → cache → AI 답변.
        TargetMarkets:
            - KR (DART). cross-provider schema = edgar.liveFilings 와 동일.

    Raises:
        없음.
    """
    del forms

    startDate, endDate = resolveDateWindow(start, end, days=days)
    cacheKey = f"liveFilings:{startDate}:{endDate}:{limit}:{keyword}:{finalOnly}"
    cacheHit, cached = lookupCache(company._cache, cacheKey)
    if cacheHit:
        return cached

    from dartlab.core.dartClient import openDart
    from dartlab.core.messaging import progress

    progress(f"{company.corpName} 최신 공시 목록 조회 중... (OpenDART, {startDate}~{endDate})")
    df = openDart().filings(
        company.stockCode,
        startDate,
        endDate,
        final=finalOnly,
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
                "corpName": pl.Utf8,
                "stockCode": pl.Utf8,
                "rceptNo": pl.Utf8,
                "reportNm": pl.Utf8,
                "viewerUrl": pl.Utf8,
                "corpCls": pl.Utf8,
            }
        )
        company._cache[cacheKey] = result
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
    company._cache[cacheKey] = result
    return result


# ── readFiling (원문 텍스트) ──────────────────────────


def buildReadFiling(
    company: Company,
    filing: Any,
    *,
    maxChars: int | None = None,
) -> dict[str, Any]:
    """공시 원문 텍스트 읽기 — rceptNo / liveFilings row / viewer URL 입력 자동 인식.

    Capabilities:
        - filing 입력 3 종 지원: 14 자리 숫자 str (rceptNo) / dict-like (Series/dict) /
          DART viewer URL (rcpNo query param 자동 추출).
        - dict 입력 시 ``rceptNo``/``docId``/``viewerUrl`` 키 우선순위 시도.
        - maxChars 로 본문 truncate (긴 보고서의 메모리 보호).

    Args:
        company: Company 인스턴스.
        filing: 14 자리 rceptNo (str) / liveFilings row (dict|Series) / DART viewer URL.
        maxChars: 본문 최대 글자 수. None → 무제한 (긴 보고서는 위험).

    Returns:
        dict[str, Any] — ``docId``/``market``/``title``/``docUrl``/``viewerUrl``/``text``.

    Raises:
        ValueError: rceptNo 추출 실패 (14 자리 숫자도, viewer URL 의 ``rcpNo`` query 도 없음).

    Example:
        >>> # buildReadFiling(c, "20240315000123", maxChars=5000)
        >>> # buildReadFiling(c, row)  # liveFilings row 그대로

    Guide:
        - "특정 공시 본문 보기" → ``c.readFiling(rceptNo)``.
        - "긴 보고서 일부만" → ``maxChars=5000``.
        - "정기보고서 topic 비교" → ``c.panel(topic)``.
        - liveFilings 결과 row 그대로 → ``buildReadFiling(c, df.row(0, named=True))``.

    SeeAlso:
        - ``buildLiveFilings`` — 본 함수의 filing 입력 source.
        - ``Company.readFiling`` — 본 함수의 facade.
        - ``dartlab.providers._common.filingHelpers.filingRecord`` / ``truncateText`` — 입력/출력 헬퍼.

    Requires:
        - polars (입력 Series 처리) + dartlab.providers._common.filingHelpers — filingRecord / truncateText.
        - dartlab.core.dataLoader — DART_VIEWER.
        - DART_API_KEY (documentText 호출 시).

    AIContext:
        AI 가 "X 공시 본문 요약" 질문 받으면 본 함수로 텍스트 fetch → 토큰 한계 내에서 요약.
        긴 정기보고서 topic 분석은 panel catalog 와 ``c.panel(topic)`` 으로 처리.

    LLM Specifications:
        AntiPatterns:
            - rceptNo 추출 실패 → ValueError (raise). caller 가 try/except.
            - maxChars=None 인데 본문이 수십만 자 → 토큰 폭증.
            - 정기보고서 topic 분석을 readFiling 원문 분해로 우회.
        OutputSchema:
            - dict — 키 ``docId``/``market``/``title``/``docUrl``/``viewerUrl`` + ``text``.
        Prerequisites:
            - rceptNo 유효 (DART 에 실제 등록). DART_API_KEY.
        Freshness:
            - DART 등록 후 즉시 (rate limit 외).
        Dataflow:
            - rceptNo → DART API → 본 함수 (정규화) → AI 답변.
        TargetMarkets:
            - KR (DART) 한정. EDGAR 의 readFiling 은 별도 implementation.
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

    from dartlab.core.dartClient import openDart
    from dartlab.core.messaging import progress

    progress(f"{company.corpName} 공시 원문 다운로드 중... ({rceptNo})")
    rawText = openDart().documentText(rceptNo)
    progress(f"{company.corpName} 공시 원문 정리 중... ({rceptNo})")
    normalizedText = _normalizeDocumentText(rawText)
    textPreview, truncated = truncateText(normalizedText, maxChars=maxChars)
    rawPreview, _ = truncateText(rawText, maxChars=maxChars)
    return {
        "docId": rceptNo,
        "market": "KR",
        "title": record.get("title") or record.get("reportNm") or "",
        "docUrl": viewerUrl or f"{DART_VIEWER}{rceptNo}",
        "viewerUrl": viewerUrl or f"{DART_VIEWER}{rceptNo}",
        "raw": rawPreview,
        "text": textPreview,
        "truncated": truncated,
    }


def _normalizeDocumentText(rawText: str) -> str:
    if "<" not in rawText or ">" not in rawText:
        return rawText
    try:
        from dartlab.core.dartClient import dartHtmlToText

        normalized = dartHtmlToText(rawText)
    except (ImportError, ValueError, AttributeError):
        # HTML 파서 실패 (malformed input 등) — raw text 반환.
        normalized = ""
    return normalized or rawText
