"""EDGAR docs namespace — sections 수평화가 유일한 기초 경로."""

from __future__ import annotations

from typing import TYPE_CHECKING

import polars as pl

from dartlab.core.memory import lookupCache
from dartlab.core.polarsUtil import isEmptyDf

if TYPE_CHECKING:
    from dartlab.providers.edgar.company import Company


class _DocsAccessor:
    """EDGAR docs namespace. sections 수평화가 유일한 기초 경로.

    lazy-build 는 atomic 패턴 — ``lookupCache(cache, key)`` 로 한 번만 cache 접
    근, 결과는 로컬 var 에 저장. ``cache[key] = val`` 직후 BoundedCache 의 FATAL/
    EMERGENCY clear 가 발동해 evict 되어도 ``return val`` 은 영향 없음. R9 인텔 audit
    의 ``KeyError: '_docs_sections'`` 결함 (2026-04-27) 의 근본 fix.
    """

    def __init__(self, company: Company):
        self._company = company

    @property
    def sections(self) -> pl.DataFrame | None:
        """sections wide DataFrame — 10-K/10-Q section_title × period.

        Returns:
            sections DataFrame 또는 None (docs parquet 부재).

        Raises:
            없음.

        Example:
            >>> c._docs.sections.head()

        SeeAlso:
            - ``providers.edgar.docs.sections.pipeline.sections`` — 본 namespace 의 backend.
            - ``Company.panel`` — public surface.

        Requires:
            - dartlab
            - polars

        Capabilities:
            - SEC 10-K/10-Q sections wide DataFrame 의 _DocsAccessor namespace. atomic cache pattern
              (cache.get + 로컬 var) — BoundedCache evict 안전.

        Guide:
            - 사용자 API 는 ``c.panel("10-K::item...")`` — 본 namespace 직접 호출 X.

        AIContext:
            internal accessor — AI 가 직접 호출 X. Company facade 가 본 메서드 위임.

        LLM Specifications:
            AntiPatterns:
                - docs 부재 회사 (신규 IPO 등) → None. caller None 분기 의무.
                - 본 namespace 직접 호출 X — 사용자 API 는 ``c.panel()``.
            OutputSchema:
                - pl.DataFrame 또는 None.
            Prerequisites:
                - 본 회사 SEC 10-K/10-Q docs parquet 보유.
            Freshness:
                - SEC EDGAR 갱신 시점.
            Dataflow:
                - docs parquet → pipeline.sections → 본 namespace.
            TargetMarkets:
                - US (SEC EDGAR) 한정.
        """
        key = "_docs_sections"
        cacheHit, val = lookupCache(self._company._cache, key)
        if not cacheHit:
            from dartlab.providers.edgar.docs.sections.pipeline import sections

            val = sections(self._company.ticker)
            self._company._cache[key] = val
        return val

    @property
    def retrievalBlocks(self) -> pl.DataFrame | None:
        """retrieval 용 chunk 블록 — RAG 검색 표면.

        Returns:
            ``block_id/text/topic/period`` 컬럼 DataFrame 또는 None.

        Raises:
            없음.

        Example:
            >>> c._docs.retrievalBlocks.head()

        SeeAlso:
            - ``providers.edgar.docs.sections.pipeline.sections`` — 본 namespace 의 backend.
            - ``Company.panel`` — public surface.

        Requires:
            - dartlab
            - polars

        Capabilities:
            - SEC 10-K/10-Q sections wide DataFrame 의 _DocsAccessor namespace. atomic cache pattern
              (cache.get + 로컬 var) — BoundedCache evict 안전.

        Guide:
            - 사용자 API 는 ``c.panel("10-K::item...")`` — 본 namespace 직접 호출 X.

        AIContext:
            internal accessor — AI 가 직접 호출 X. Company facade 가 본 메서드 위임.

        LLM Specifications:
            AntiPatterns:
                - docs 부재 회사 (신규 IPO 등) → None. caller None 분기 의무.
                - 본 namespace 직접 호출 X — 사용자 API 는 ``c.panel()``.
            OutputSchema:
                - pl.DataFrame 또는 None.
            Prerequisites:
                - 본 회사 SEC 10-K/10-Q docs parquet 보유.
            Freshness:
                - SEC EDGAR 갱신 시점.
            Dataflow:
                - docs parquet → pipeline.sections → 본 namespace.
            TargetMarkets:
                - US (SEC EDGAR) 한정.
        """
        key = "_docs_retrievalBlocks"
        cacheHit, val = lookupCache(self._company._cache, key)
        if not cacheHit:
            from dartlab.providers.edgar.docs.sections.views import retrievalBlocks

            val = retrievalBlocks(self._company.ticker)
            self._company._cache[key] = val
        return val

    @property
    def contextSlices(self) -> pl.DataFrame | None:
        """context window 단위 슬라이스 — LLM 입력 최적화.

        Returns:
            슬라이스 DataFrame 또는 None.

        Raises:
            없음.

        Example:
            >>> c._docs.contextSlices.head()

        SeeAlso:
            - ``providers.edgar.docs.sections.pipeline.sections`` — 본 namespace 의 backend.
            - ``Company.panel`` — public surface.

        Requires:
            - dartlab
            - polars

        Capabilities:
            - SEC 10-K/10-Q sections wide DataFrame 의 _DocsAccessor namespace. atomic cache pattern
              (cache.get + 로컬 var) — BoundedCache evict 안전.

        Guide:
            - 사용자 API 는 ``c.panel("10-K::item...")`` — 본 namespace 직접 호출 X.

        AIContext:
            internal accessor — AI 가 직접 호출 X. Company facade 가 본 메서드 위임.

        LLM Specifications:
            AntiPatterns:
                - docs 부재 회사 (신규 IPO 등) → None. caller None 분기 의무.
                - 본 namespace 직접 호출 X — 사용자 API 는 ``c.panel()``.
            OutputSchema:
                - pl.DataFrame 또는 None.
            Prerequisites:
                - 본 회사 SEC 10-K/10-Q docs parquet 보유.
            Freshness:
                - SEC EDGAR 갱신 시점.
            Dataflow:
                - docs parquet → pipeline.sections → 본 namespace.
            TargetMarkets:
                - US (SEC EDGAR) 한정.
        """
        key = "_docs_contextSlices"
        cacheHit, val = lookupCache(self._company._cache, key)
        if not cacheHit:
            from dartlab.providers.edgar.docs.sections.views import contextSlices

            val = contextSlices(self._company.ticker)
            self._company._cache[key] = val
        return val

    def notes(self, query: str | None = None) -> pl.DataFrame | None:
        """XBRL TextBlock 주석 검색 (원본). ``query=None`` 이면 전체 목록.

        Args:
            query: 검색어 (None 이면 전체 주석).

        Returns:
            주석 DataFrame 또는 None.

        Raises:
            없음.

        Example:
            >>> c._docs.notes("inventory")

        SeeAlso:
            - ``providers.edgar.docs.sections.pipeline.sections`` — 본 namespace 의 backend.
            - ``Company.panel`` — public surface.

        Requires:
            - dartlab
            - polars

        Capabilities:
            - SEC 10-K/10-Q sections wide DataFrame 의 _DocsAccessor namespace. atomic cache pattern
              (cache.get + 로컬 var) — BoundedCache evict 안전.

        Guide:
            - 사용자 API 는 ``c.panel("10-K::item...")`` — 본 namespace 직접 호출 X.

        AIContext:
            internal accessor — AI 가 직접 호출 X. Company facade 가 본 메서드 위임.

        LLM Specifications:
            AntiPatterns:
                - docs 부재 회사 (신규 IPO 등) → None. caller None 분기 의무.
                - 본 namespace 직접 호출 X — 사용자 API 는 ``c.panel()``.
            OutputSchema:
                - pl.DataFrame 또는 None.
            Prerequisites:
                - 본 회사 SEC 10-K/10-Q docs parquet 보유.
            Freshness:
                - SEC EDGAR 갱신 시점.
            Dataflow:
                - docs parquet → pipeline.sections → 본 namespace.
            TargetMarkets:
                - US (SEC EDGAR) 한정.
        """
        from dartlab.providers.edgar.docs.notes import notes

        return notes(self._company.cik, query)

    def notesByCategory(self, category: str | None = None):
        """카테고리별 구조화 Notes — DART ``c.panel("inventory")`` 대응.

        ``category=None`` 이면 데이터 있는 카테고리 dict 반환.

        Args:
            category: 특정 카테고리 (None 이면 전체).

        Returns:
            DataFrame 또는 카테고리 dict 또는 None.

        Raises:
            없음.

        Example:
            >>> c._docs.notesByCategory("inventory")

        SeeAlso:
            - ``providers.edgar.docs.sections.pipeline.sections`` — 본 namespace 의 backend.
            - ``Company.panel`` — public surface.

        Requires:
            - dartlab
            - polars

        Capabilities:
            - SEC 10-K/10-Q sections wide DataFrame 의 _DocsAccessor namespace. atomic cache pattern
              (cache.get + 로컬 var) — BoundedCache evict 안전.

        Guide:
            - 사용자 API 는 ``c.panel("10-K::item...")`` — 본 namespace 직접 호출 X.

        AIContext:
            internal accessor — AI 가 직접 호출 X. Company facade 가 본 메서드 위임.

        LLM Specifications:
            AntiPatterns:
                - docs 부재 회사 (신규 IPO 등) → None. caller None 분기 의무.
                - 본 namespace 직접 호출 X — 사용자 API 는 ``c.panel()``.
            OutputSchema:
                - pl.DataFrame 또는 None.
            Prerequisites:
                - 본 회사 SEC 10-K/10-Q docs parquet 보유.
            Freshness:
                - SEC EDGAR 갱신 시점.
            Dataflow:
                - docs parquet → pipeline.sections → 본 namespace.
            TargetMarkets:
                - US (SEC EDGAR) 한정.
        """
        from dartlab.providers.edgar.docs.notes import notesByCategory

        return notesByCategory(self._company.cik, category)

    def noteCategories(self) -> list[str]:
        """이 기업에서 데이터가 있는 notes 카테고리 목록.

        Returns:
            카테고리 str 리스트.

        Raises:
            없음.

        Example:
            >>> c._docs.noteCategories()

        SeeAlso:
            - ``providers.edgar.docs.sections.pipeline.sections`` — 본 namespace 의 backend.
            - ``Company.panel`` — public surface.

        Requires:
            - dartlab
            - polars

        Capabilities:
            - SEC 10-K/10-Q sections wide DataFrame 의 _DocsAccessor namespace. atomic cache pattern
              (cache.get + 로컬 var) — BoundedCache evict 안전.

        Guide:
            - 사용자 API 는 ``c.panel("10-K::item...")`` — 본 namespace 직접 호출 X.

        AIContext:
            internal accessor — AI 가 직접 호출 X. Company facade 가 본 메서드 위임.

        LLM Specifications:
            AntiPatterns:
                - docs 부재 회사 (신규 IPO 등) → None. caller None 분기 의무.
                - 본 namespace 직접 호출 X — 사용자 API 는 ``c.panel()``.
            OutputSchema:
                - pl.DataFrame 또는 None.
            Prerequisites:
                - 본 회사 SEC 10-K/10-Q docs parquet 보유.
            Freshness:
                - SEC EDGAR 갱신 시점.
            Dataflow:
                - docs parquet → pipeline.sections → 본 namespace.
            TargetMarkets:
                - US (SEC EDGAR) 한정.
        """
        from dartlab.providers.edgar.docs.notes import noteCategories

        return noteCategories(self._company.cik)

    def freq(self) -> pl.DataFrame | None:
        """sections 빈도 집계.

        Returns:
            빈도 DataFrame 또는 None.

        Raises:
            없음.

        Example:
            >>> c._docs.freq()

        SeeAlso:
            - ``providers.edgar.docs.sections.pipeline.sections`` — 본 namespace 의 backend.
            - ``Company.panel`` — public surface.

        Requires:
            - dartlab
            - polars

        Capabilities:
            - SEC 10-K/10-Q sections wide DataFrame 의 _DocsAccessor namespace. atomic cache pattern
              (cache.get + 로컬 var) — BoundedCache evict 안전.

        Guide:
            - 사용자 API 는 ``c.panel("10-K::item...")`` — 본 namespace 직접 호출 X.

        AIContext:
            internal accessor — AI 가 직접 호출 X. Company facade 가 본 메서드 위임.

        LLM Specifications:
            AntiPatterns:
                - docs 부재 회사 (신규 IPO 등) → None. caller None 분기 의무.
                - 본 namespace 직접 호출 X — 사용자 API 는 ``c.panel()``.
            OutputSchema:
                - pl.DataFrame 또는 None.
            Prerequisites:
                - 본 회사 SEC 10-K/10-Q docs parquet 보유.
            Freshness:
                - SEC EDGAR 갱신 시점.
            Dataflow:
                - docs parquet → pipeline.sections → 본 namespace.
            TargetMarkets:
                - US (SEC EDGAR) 한정.
        """
        key = "_docs_freq"
        cacheHit, val = lookupCache(self._company._cache, key)
        if not cacheHit:
            from dartlab.providers.edgar.docs.sections.views import freq

            val = freq(self._company.ticker)
            self._company._cache[key] = val
        return val

    def coverage(self) -> pl.DataFrame | None:
        """topic × period 커버리지 — 결손 식별.

        Returns:
            커버리지 DataFrame 또는 None.

        Raises:
            없음.

        Example:
            >>> c._docs.coverage()

        SeeAlso:
            - ``providers.edgar.docs.sections.pipeline.sections`` — 본 namespace 의 backend.
            - ``Company.panel`` — public surface.

        Requires:
            - dartlab
            - polars

        Capabilities:
            - SEC 10-K/10-Q sections wide DataFrame 의 _DocsAccessor namespace. atomic cache pattern
              (cache.get + 로컬 var) — BoundedCache evict 안전.

        Guide:
            - 사용자 API 는 ``c.panel("10-K::item...")`` — 본 namespace 직접 호출 X.

        AIContext:
            internal accessor — AI 가 직접 호출 X. Company facade 가 본 메서드 위임.

        LLM Specifications:
            AntiPatterns:
                - docs 부재 회사 (신규 IPO 등) → None. caller None 분기 의무.
                - 본 namespace 직접 호출 X — 사용자 API 는 ``c.panel()``.
            OutputSchema:
                - pl.DataFrame 또는 None.
            Prerequisites:
                - 본 회사 SEC 10-K/10-Q docs parquet 보유.
            Freshness:
                - SEC EDGAR 갱신 시점.
            Dataflow:
                - docs parquet → pipeline.sections → 본 namespace.
            TargetMarkets:
                - US (SEC EDGAR) 한정.
        """
        key = "_docs_coverage"
        cacheHit, val = lookupCache(self._company._cache, key)
        if not cacheHit:
            from dartlab.providers.edgar.docs.sections.views import coverage

            val = coverage(self._company.ticker)
            self._company._cache[key] = val
        return val

    def filings(self) -> pl.DataFrame | None:
        """공시 목록 — 10-K/10-Q form_type 메타.

        Returns:
            ``period_key/form_type/accession_no/filed_date`` 컬럼 DataFrame 또는 None.

        Raises:
            없음.

        Example:
            >>> c._docs.filings().head()

        SeeAlso:
            - ``providers.edgar.docs.sections.pipeline.sections`` — 본 namespace 의 backend.
            - ``Company.panel`` — public surface.

        Requires:
            - dartlab
            - polars

        Capabilities:
            - SEC 10-K/10-Q sections wide DataFrame 의 _DocsAccessor namespace. atomic cache pattern
              (cache.get + 로컬 var) — BoundedCache evict 안전.

        Guide:
            - 사용자 API 는 ``c.panel("10-K::item...")`` — 본 namespace 직접 호출 X.

        AIContext:
            internal accessor — AI 가 직접 호출 X. Company facade 가 본 메서드 위임.

        LLM Specifications:
            AntiPatterns:
                - docs 부재 회사 (신규 IPO 등) → None. caller None 분기 의무.
                - 본 namespace 직접 호출 X — 사용자 API 는 ``c.panel()``.
            OutputSchema:
                - pl.DataFrame 또는 None.
            Prerequisites:
                - 본 회사 SEC 10-K/10-Q docs parquet 보유.
            Freshness:
                - SEC EDGAR 갱신 시점.
            Dataflow:
                - docs parquet → pipeline.sections → 본 namespace.
            TargetMarkets:
                - US (SEC EDGAR) 한정.
        """
        key = "_docs_filings"
        cacheHit, cached = lookupCache(self._company._cache, key)
        if cacheHit:
            return cached

        from dartlab.core.dataLoader import loadData

        df = loadData(self._company.ticker, category="edgarDocs")
        if isEmptyDf(df):
            self._company._cache[key] = None
            return None

        cols = ["period_key", "form_type", "accession_no", "filed_date"]
        available = [c for c in cols if c in df.columns]
        result = (
            df.select(available).unique(subset=["accession_no"]).sort("period_key", descending=True, nulls_last=True)
        )
        self._company._cache[key] = result
        return result
