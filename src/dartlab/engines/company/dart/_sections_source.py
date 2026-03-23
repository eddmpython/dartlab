"""sections source-of-truth accessor.

company.py에서 분리된 accessor 클래스.
raw DataFrame를 감싸되, 같은 경로에서 cadence/semantic 파생표를 바로 꺼낼 수 있게 한다.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import polars as pl

if TYPE_CHECKING:
    from dartlab.engines.company.dart.company import Company


class _SectionsSource:
    """sections source-of-truth accessor.

    raw DataFrame를 감싸되, 같은 경로에서 cadence/semantic 파생표를 바로 꺼낼 수 있게 한다.
    일반 DataFrame 연산은 내부 raw DataFrame으로 위임한다.
    """

    def __init__(self, company: "Company"):
        self._company = company

    @property
    def raw(self) -> pl.DataFrame | None:
        return self._company._get_primary("sections")

    @property
    def frame(self) -> pl.DataFrame | None:
        return self.raw

    def topics(self) -> list[str]:
        return self._company._docsSectionTopics()

    def outline(self, topic: str | None = None) -> pl.DataFrame | None:
        return self._company._docsTopicOutline(topic=topic)

    def periods(self, *, recentFirst: bool = True, annualAsQ4: bool = True) -> list[str]:
        frame = self.raw
        if frame is None:
            return []
        from dartlab.engines.company.dart.docs.sections import periodColumns

        return periodColumns(frame.columns, descending=recentFirst, annualAsQ4=annualAsQ4)

    def ordered(self, *, recentFirst: bool = True, annualAsQ4: bool = True) -> pl.DataFrame | None:
        return self._company._docsSectionsOrdered(recentFirst=recentFirst, annualAsQ4=annualAsQ4)

    def coverage(
        self,
        *,
        topic: str | None = None,
        recentFirst: bool = True,
        annualAsQ4: bool = True,
    ) -> pl.DataFrame | None:
        return self._company._docsSectionsCoverage(
            topic=topic,
            recentFirst=recentFirst,
            annualAsQ4=annualAsQ4,
        )

    def cadence(self, cadenceScope: str, *, includeMixed: bool = True) -> pl.DataFrame | None:
        return self._company._docsSectionsCadence(cadenceScope, includeMixed=includeMixed)

    def semanticRegistry(
        self,
        *,
        topic: str | None = None,
        cadenceScope: str = "all",
        includeMixed: bool = True,
    ) -> pl.DataFrame | None:
        return self._company._docsSectionsSemanticRegistry(
            topic=topic,
            cadenceScope=cadenceScope,
            includeMixed=includeMixed,
            collisionsOnly=False,
        )

    def semanticCollisions(
        self,
        *,
        topic: str | None = None,
        cadenceScope: str = "all",
        includeMixed: bool = True,
    ) -> pl.DataFrame | None:
        return self._company._docsSectionsSemanticRegistry(
            topic=topic,
            cadenceScope=cadenceScope,
            includeMixed=includeMixed,
            collisionsOnly=True,
        )

    def structureRegistry(
        self,
        *,
        topic: str | None = None,
        cadenceScope: str = "all",
        includeMixed: bool = True,
        nodeType: str | None = None,
    ) -> pl.DataFrame | None:
        return self._company._docsSectionsStructureRegistry(
            topic=topic,
            cadenceScope=cadenceScope,
            includeMixed=includeMixed,
            collisionsOnly=False,
            nodeType=nodeType,
        )

    def structureCollisions(
        self,
        *,
        topic: str | None = None,
        cadenceScope: str = "all",
        includeMixed: bool = True,
        nodeType: str | None = None,
    ) -> pl.DataFrame | None:
        return self._company._docsSectionsStructureRegistry(
            topic=topic,
            cadenceScope=cadenceScope,
            includeMixed=includeMixed,
            collisionsOnly=True,
            nodeType=nodeType,
        )

    def structureEvents(
        self,
        *,
        topic: str | None = None,
        cadenceScope: str = "all",
        includeMixed: bool = True,
        changedOnly: bool = True,
        nodeType: str | None = None,
    ) -> pl.DataFrame | None:
        return self._company._docsSectionsStructureEvents(
            topic=topic,
            cadenceScope=cadenceScope,
            includeMixed=includeMixed,
            changedOnly=changedOnly,
            nodeType=nodeType,
        )

    def structureSummary(
        self,
        *,
        topic: str | None = None,
        cadenceScope: str = "all",
        includeMixed: bool = True,
        nodeType: str | None = None,
    ) -> pl.DataFrame | None:
        return self._company._docsSectionsStructureSummary(
            topic=topic,
            cadenceScope=cadenceScope,
            includeMixed=includeMixed,
            nodeType=nodeType,
        )

    def structureChanges(
        self,
        *,
        topic: str | None = None,
        cadenceScope: str = "all",
        includeMixed: bool = True,
        nodeType: str | None = None,
        latestOnly: bool = True,
        changedOnly: bool = True,
    ) -> pl.DataFrame | None:
        return self._company._docsSectionsStructureChanges(
            topic=topic,
            cadenceScope=cadenceScope,
            includeMixed=includeMixed,
            nodeType=nodeType,
            latestOnly=latestOnly,
            changedOnly=changedOnly,
        )

    def __getattr__(self, name: str) -> Any:
        frame = self.raw
        if frame is None:
            raise AttributeError(name)
        return getattr(frame, name)

    def __getitem__(self, key: Any) -> Any:
        frame = self.raw
        if frame is None:
            raise KeyError(key)
        return frame[key]

    def __len__(self) -> int:
        frame = self.raw
        return 0 if frame is None else len(frame)

    def __repr__(self) -> str:
        frame = self.raw
        if frame is None:
            return "SectionsSource(missing)"
        return (
            "SectionsSource("
            "shape="
            f"{frame.shape}, methods=[raw, topics(), outline(), periods(), ordered(), coverage(), cadence(), semanticRegistry(), semanticCollisions(), structureRegistry(), structureCollisions(), structureEvents(), structureSummary(), structureChanges()]"
            ")"
        )
