"""EDGAR docs namespace — sections 수평화가 유일한 기초 경로."""

from __future__ import annotations

from typing import TYPE_CHECKING

import polars as pl

if TYPE_CHECKING:
    from dartlab.providers.edgar.company import Company


class _DocsAccessor:
    """EDGAR docs namespace. sections 수평화가 유일한 기초 경로."""

    def __init__(self, company: Company):
        self._company = company

    @property
    def sections(self) -> pl.DataFrame | None:
        key = "_docs_sections"
        if key not in self._company._cache:
            from dartlab.providers.edgar.docs.sections.pipeline import sections

            self._company._cache[key] = sections(self._company.ticker)
        return self._company._cache[key]

    @property
    def retrievalBlocks(self) -> pl.DataFrame | None:
        key = "_docs_retrievalBlocks"
        if key not in self._company._cache:
            from dartlab.providers.edgar.docs.sections.views import retrievalBlocks

            self._company._cache[key] = retrievalBlocks(self._company.ticker)
        return self._company._cache[key]

    @property
    def contextSlices(self) -> pl.DataFrame | None:
        key = "_docs_contextSlices"
        if key not in self._company._cache:
            from dartlab.providers.edgar.docs.sections.views import contextSlices

            self._company._cache[key] = contextSlices(self._company.ticker)
        return self._company._cache[key]

    def notes(self, query: str | None = None) -> pl.DataFrame | None:
        """XBRL TextBlock 주석 검색 (원본). query=None이면 전체 목록."""
        from dartlab.providers.edgar.docs.notes import notes

        return notes(self._company.cik, query)

    def notesByCategory(self, category: str | None = None):
        """카테고리별 구조화 Notes. DART c.notes.inventory 등에 대응.

        category=None이면 데이터 있는 카테고리 dict 반환.
        """
        from dartlab.providers.edgar.docs.notes import notesByCategory

        return notesByCategory(self._company.cik, category)

    def noteCategories(self) -> list[str]:
        """이 기업에서 데이터가 있는 notes 카테고리 목록."""
        from dartlab.providers.edgar.docs.notes import noteCategories

        return noteCategories(self._company.cik)

    def freq(self) -> pl.DataFrame | None:
        key = "_docs_freq"
        if key not in self._company._cache:
            from dartlab.providers.edgar.docs.sections.views import freq

            self._company._cache[key] = freq(self._company.ticker)
        return self._company._cache[key]

    def coverage(self) -> pl.DataFrame | None:
        key = "_docs_coverage"
        if key not in self._company._cache:
            from dartlab.providers.edgar.docs.sections.views import coverage

            self._company._cache[key] = coverage(self._company.ticker)
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
            df.select(available).unique(subset=["accession_no"]).sort("period_key", descending=True, nulls_last=True)
        )
        self._company._cache[key] = result
        return result
