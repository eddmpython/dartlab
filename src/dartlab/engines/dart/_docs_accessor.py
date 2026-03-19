"""docs source namespace accessor.

company.py에서 분리된 accessor 클래스.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import polars as pl

from dartlab.engines.dart._sections_source import _SectionsSource

if TYPE_CHECKING:
    from dartlab.engines.dart.company import Company


class _DocsAccessor:
    """docs source namespace."""

    def __init__(self, company: "Company"):
        self._company = company
        self._sectionsAccessor = _SectionsSource(company)

    @property
    def raw(self) -> pl.DataFrame | None:
        return self._company.rawDocs

    def filings(self) -> pl.DataFrame:
        return self._company._filings()

    @property
    def sections(self) -> "_SectionsSource | None":
        return self._sectionsAccessor if self._sectionsAccessor.raw is not None else None

    def sectionsOrdered(self, *, recentFirst: bool = True, annualAsQ4: bool = True) -> pl.DataFrame | None:
        sections = self.sections
        return None if sections is None else sections.ordered(recentFirst=recentFirst, annualAsQ4=annualAsQ4)

    def sectionsCoverage(
        self,
        *,
        topic: str | None = None,
        recentFirst: bool = True,
        annualAsQ4: bool = True,
    ) -> pl.DataFrame | None:
        sections = self.sections
        return (
            None if sections is None else sections.coverage(topic=topic, recentFirst=recentFirst, annualAsQ4=annualAsQ4)
        )

    def sectionsCadence(self, cadenceScope: str, *, includeMixed: bool = True) -> pl.DataFrame | None:
        sections = self.sections
        return None if sections is None else sections.cadence(cadenceScope, includeMixed=includeMixed)

    def sectionsSemanticRegistry(
        self,
        *,
        topic: str | None = None,
        cadenceScope: str = "all",
        includeMixed: bool = True,
    ) -> pl.DataFrame | None:
        sections = self.sections
        return (
            None
            if sections is None
            else sections.semanticRegistry(topic=topic, cadenceScope=cadenceScope, includeMixed=includeMixed)
        )

    def sectionsSemanticCollisions(
        self,
        *,
        topic: str | None = None,
        cadenceScope: str = "all",
        includeMixed: bool = True,
    ) -> pl.DataFrame | None:
        sections = self.sections
        return (
            None
            if sections is None
            else sections.semanticCollisions(topic=topic, cadenceScope=cadenceScope, includeMixed=includeMixed)
        )

    def sectionsStructureRegistry(
        self,
        *,
        topic: str | None = None,
        cadenceScope: str = "all",
        includeMixed: bool = True,
        nodeType: str | None = None,
    ) -> pl.DataFrame | None:
        sections = self.sections
        return (
            None
            if sections is None
            else sections.structureRegistry(
                topic=topic,
                cadenceScope=cadenceScope,
                includeMixed=includeMixed,
                nodeType=nodeType,
            )
        )

    def sectionsStructureCollisions(
        self,
        *,
        topic: str | None = None,
        cadenceScope: str = "all",
        includeMixed: bool = True,
        nodeType: str | None = None,
    ) -> pl.DataFrame | None:
        sections = self.sections
        return (
            None
            if sections is None
            else sections.structureCollisions(
                topic=topic,
                cadenceScope=cadenceScope,
                includeMixed=includeMixed,
                nodeType=nodeType,
            )
        )

    def sectionsStructureEvents(
        self,
        *,
        topic: str | None = None,
        cadenceScope: str = "all",
        includeMixed: bool = True,
        changedOnly: bool = True,
        nodeType: str | None = None,
    ) -> pl.DataFrame | None:
        sections = self.sections
        return (
            None
            if sections is None
            else sections.structureEvents(
                topic=topic,
                cadenceScope=cadenceScope,
                includeMixed=includeMixed,
                changedOnly=changedOnly,
                nodeType=nodeType,
            )
        )

    def sectionsStructureSummary(
        self,
        *,
        topic: str | None = None,
        cadenceScope: str = "all",
        includeMixed: bool = True,
        nodeType: str | None = None,
    ) -> pl.DataFrame | None:
        sections = self.sections
        return (
            None
            if sections is None
            else sections.structureSummary(
                topic=topic,
                cadenceScope=cadenceScope,
                includeMixed=includeMixed,
                nodeType=nodeType,
            )
        )

    def sectionsStructureChanges(
        self,
        *,
        topic: str | None = None,
        cadenceScope: str = "all",
        includeMixed: bool = True,
        nodeType: str | None = None,
        latestOnly: bool = True,
        changedOnly: bool = True,
    ) -> pl.DataFrame | None:
        sections = self.sections
        return (
            None
            if sections is None
            else sections.structureChanges(
                topic=topic,
                cadenceScope=cadenceScope,
                includeMixed=includeMixed,
                nodeType=nodeType,
                latestOnly=latestOnly,
                changedOnly=changedOnly,
            )
        )

    @property
    def retrievalBlocks(self) -> pl.DataFrame | None:
        return self._company._retrievalBlocks()

    @property
    def contextSlices(self) -> pl.DataFrame | None:
        return self._company._contextSlices()

    @property
    def notes(self):
        return self._company._notesAccessor

    @property
    def business(self):
        import warnings

        warnings.warn("docs.business → show('business') 경로 권장", DeprecationWarning, stacklevel=2)
        return self._company._get_primary("business")

    @property
    def mdna(self):
        import warnings

        warnings.warn("docs.mdna → show('mdna') 경로 권장", DeprecationWarning, stacklevel=2)
        return self._company._get_primary("mdna")

    @property
    def rawMaterial(self):
        import warnings

        warnings.warn("docs.rawMaterial → show('rawMaterial') 경로 권장", DeprecationWarning, stacklevel=2)
        return self._company._sectionsSubtopicWide("rawMaterial") or self._company._safePrimary("rawMaterial")

    def subtables(self, topic: str, *, raw: bool = False) -> pl.DataFrame | None:
        return self._company._sectionsSubtopicLong(topic) if raw else self._company._sectionsSubtopicWide(topic)
