"""sections 구조 분석 — Company에서 분리.

docs parquet 기반 topic manifest, outline, cadence, coverage,
semantic/structure registry 등 sections 파생표 생성을 담당한다.
Company는 이 클래스를 lazy 초기화하여 위임한다.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import polars as pl

if TYPE_CHECKING:
    from dartlab.providers.dart.company import Company


class SectionsAnalyzer:
    """sections 구조 분석기."""

    def __init__(self, company: Company):
        self._company = company

    # ── helpers ──

    @property
    def _stockCode(self) -> str:
        return self._company.stockCode

    @property
    def _hasDocs(self) -> bool:
        return self._company._hasDocs

    @property
    def _cache(self):
        return self._company._cache

    # ── topic manifest ──

    def topicManifest(self) -> pl.DataFrame:
        """전체 topic 카탈로그 (chapter, topic, source, blocks, periods)."""
        cacheKey = "_docsTopicManifest"
        if cacheKey in self._cache:
            return self._cache[cacheKey]

        empty = _emptyTopicManifest()
        if not self._hasDocs:
            self._cache[cacheKey] = empty
            return empty

        from dartlab.core.dataLoader import loadData

        raw = loadData(
            self._stockCode,
            category="docs",
            sinceYear=2016,
            columns=["year", "report_type", "rcept_date", "section_order", "section_title"],
        )
        requiredCols = {"year", "report_type", "section_order", "section_title"}
        if raw is None or raw.is_empty() or not requiredCols.issubset(set(raw.columns)):
            self._cache[cacheKey] = empty
            return empty

        from dartlab.core.reportSelector import selectReport
        from dartlab.providers.dart.docs.sections._common import REPORT_KINDS, periodOrderValue
        from dartlab.providers.dart.docs.sections.chunker import parseMajorNum
        from dartlab.providers.dart.docs.sections.mapper import mapSectionTitle
        from dartlab.providers.dart.docs.sections.runtime import chapterFromMajorNum

        years = sorted({str(year) for year in raw["year"].drop_nulls().to_list()}, reverse=True)
        catalog: dict[str, dict[str, Any]] = {}

        for year in years:
            for reportKind, suffix in REPORT_KINDS:
                report = selectReport(raw, year, reportKind=reportKind)
                if report is None or report.is_empty():
                    continue

                periodKey = f"{year}{suffix}"
                scoped = (
                    report.select(["section_order", "section_title"])
                    .filter(pl.col("section_title").is_not_null())
                    .sort("section_order")
                )
                if scoped.is_empty():
                    continue

                currentChapter: str | None = None
                periodCounts: dict[str, int] = {}
                periodOrders: dict[str, int] = {}
                periodChapters: dict[str, str] = {}

                for row in scoped.iter_rows(named=True):
                    rawTitle = str(row.get("section_title") or "").strip()
                    if not rawTitle:
                        continue
                    majorNum = parseMajorNum(rawTitle)
                    if majorNum is not None:
                        currentChapter = chapterFromMajorNum(majorNum)
                    topic = mapSectionTitle(rawTitle)
                    if not topic:
                        continue
                    sectionOrder = int(row.get("section_order") or 0)
                    periodCounts[topic] = periodCounts.get(topic, 0) + 1
                    periodOrders.setdefault(topic, sectionOrder)
                    if currentChapter and topic not in periodChapters:
                        periodChapters[topic] = currentChapter

                for topic, blockCount in periodCounts.items():
                    chapter = periodChapters.get(topic) or "XII"
                    sectionOrder = periodOrders.get(topic, 0)
                    latestKey = periodOrderValue(periodKey)
                    entry = catalog.get(topic)
                    if entry is None:
                        catalog[topic] = {
                            "order": sectionOrder,
                            "chapter": chapter,
                            "topic": topic,
                            "source": "docs",
                            "blocks": blockCount,
                            "periods": 1,
                            "latestPeriod": periodKey,
                            "_periods": {periodKey},
                            "_latestKey": latestKey,
                        }
                        continue

                    entry["order"] = min(int(entry["order"]), sectionOrder)
                    if chapter != "XII" and entry.get("chapter") == "XII":
                        entry["chapter"] = chapter
                    entry["blocks"] = max(int(entry["blocks"]), blockCount)
                    if periodKey not in entry["_periods"]:
                        entry["_periods"].add(periodKey)
                        entry["periods"] = len(entry["_periods"])
                    if latestKey > int(entry["_latestKey"]):
                        entry["latestPeriod"] = periodKey
                        entry["_latestKey"] = latestKey

        rows = [
            {
                "order": int(entry["order"]),
                "chapter": str(entry["chapter"]),
                "topic": str(entry["topic"]),
                "source": str(entry["source"]),
                "blocks": int(entry["blocks"]),
                "periods": int(entry["periods"]),
                "latestPeriod": str(entry["latestPeriod"]),
            }
            for entry in catalog.values()
        ]
        if not rows:
            self._cache[cacheKey] = empty
            return empty

        from dartlab.providers.dart.company import _CHAPTER_ORDER

        result = (
            pl.DataFrame(rows, strict=False)
            .with_columns(pl.col("chapter").replace(_CHAPTER_ORDER).cast(pl.Int64).alias("_chapterOrder"))
            .sort(["_chapterOrder", "order", "topic"])
            .drop("_chapterOrder")
        )
        self._cache[cacheKey] = result
        return result

    def sectionTopics(self) -> list[str]:
        """topic 이름 목록."""
        manifest = self.topicManifest()
        if manifest.is_empty() or "topic" not in manifest.columns:
            return []
        return [topic for topic in manifest["topic"].to_list() if isinstance(topic, str) and topic]

    # ── topic outline ──

    def topicOutline(self, topic: str | None = None) -> pl.DataFrame:
        """topic별 block outline (period, block, type, title, preview)."""
        if topic is None:
            return self.topicManifest()

        normalizedTopic = str(topic).strip()
        cacheKey = f"_docsTopicOutline:{normalizedTopic}"
        if cacheKey in self._cache:
            return self._cache[cacheKey]

        empty = _emptyTopicOutline()
        if not normalizedTopic or not self._hasDocs:
            self._cache[cacheKey] = empty
            return empty

        from dartlab.core.dataLoader import loadData

        raw = loadData(
            self._stockCode,
            category="docs",
            sinceYear=2016,
            columns=[
                "year",
                "report_type",
                "rcept_date",
                "section_order",
                "section_title",
                "section_content",
                "content",
            ],
        )
        requiredCols = {"year", "report_type", "section_order", "section_title"}
        if raw is None or raw.is_empty() or not requiredCols.issubset(set(raw.columns)):
            self._cache[cacheKey] = empty
            return empty

        from dartlab.core.reportSelector import selectReport
        from dartlab.providers.dart.docs.sections._common import REPORT_KINDS, detectContentCol, periodOrderValue
        from dartlab.providers.dart.docs.sections.mapper import mapSectionTitle
        from dartlab.providers.dart.docs.sections.views import splitMarkdownBlocks

        contentCol = detectContentCol(raw)
        years = sorted({str(year) for year in raw["year"].drop_nulls().to_list()}, reverse=True)
        rows: list[dict[str, Any]] = []

        for year in years:
            for reportKind, suffix in REPORT_KINDS:
                report = selectReport(raw, year, reportKind=reportKind)
                if report is None or report.is_empty() or contentCol not in report.columns:
                    continue

                periodKey = f"{year}{suffix}"
                blockIndex = 0
                scoped = (
                    report.select(["section_order", "section_title", contentCol])
                    .filter(pl.col("section_title").is_not_null())
                    .sort("section_order")
                )
                for row in scoped.iter_rows(named=True):
                    rawTitle = str(row.get("section_title") or "").strip()
                    if not rawTitle or mapSectionTitle(rawTitle) != normalizedTopic:
                        continue

                    content = str(row.get(contentCol) or "").strip()
                    sectionOrder = int(row.get("section_order") or 0)
                    blocks = splitMarkdownBlocks(content) if content else []
                    if not blocks:
                        rows.append(
                            {
                                "period": periodKey,
                                "sectionOrder": sectionOrder,
                                "block": blockIndex,
                                "type": "text",
                                "title": rawTitle,
                                "preview": "",
                                "_periodOrder": periodOrderValue(periodKey),
                            }
                        )
                        blockIndex += 1
                        continue

                    visibleBlocks = [block for block in blocks if str(block.get("blockType") or "text") != "heading"]
                    if not visibleBlocks:
                        visibleBlocks = blocks

                    for block in visibleBlocks:
                        label = str(block.get("blockLabel") or "").strip()
                        previewSource = block.get("blockText") or ""
                        rows.append(
                            {
                                "period": periodKey,
                                "sectionOrder": sectionOrder,
                                "block": blockIndex,
                                "type": str(block.get("blockType") or "text"),
                                "title": label if label and label != "(root)" else rawTitle,
                                "preview": _previewText(previewSource),
                                "_periodOrder": periodOrderValue(periodKey),
                            }
                        )
                        blockIndex += 1

        if not rows:
            self._cache[cacheKey] = empty
            return empty

        result = (
            pl.DataFrame(rows, strict=False)
            .sort(["_periodOrder", "sectionOrder", "block"], descending=[True, False, False])
            .drop("_periodOrder")
        )
        self._cache[cacheKey] = result
        return result

    # ── cadence / ordered / coverage ──

    def sectionsCadence(self, cadenceScope: str, *, includeMixed: bool = True) -> pl.DataFrame | None:
        """cadence 범위별 sections 투영."""
        if not self._hasDocs:
            return None
        normalizedScope = str(cadenceScope).strip().lower()
        cacheKey = f"_docsSectionsCadence:{normalizedScope}:{int(includeMixed)}"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        sectionsFrame = self._company.docs.sections
        if sectionsFrame is None:
            self._cache[cacheKey] = None
            return None
        from dartlab.providers.dart.docs.sections import projectCadenceRows

        result = projectCadenceRows(sectionsFrame, cadenceScope=normalizedScope, includeMixed=includeMixed)
        self._cache[cacheKey] = result
        return result

    def sectionsOrdered(
        self,
        *,
        recentFirst: bool = True,
        annualAsQ4: bool = True,
    ) -> pl.DataFrame | None:
        """기간 정렬된 sections."""
        if not self._hasDocs:
            return None
        cacheKey = f"_docsSectionsOrdered:{int(recentFirst)}:{int(annualAsQ4)}"
        if cacheKey in self._cache:
            return self._cache[cacheKey]

        sectionsFrame = self._company.docs.sections
        if sectionsFrame is None:
            self._cache[cacheKey] = None
            return None

        from dartlab.providers.dart.docs.sections import reorderPeriodColumns

        result = reorderPeriodColumns(sectionsFrame.raw, descending=recentFirst, annualAsQ4=annualAsQ4)
        self._cache[cacheKey] = result
        return result

    def sectionsCoverage(
        self,
        *,
        topic: str | None = None,
        recentFirst: bool = True,
        annualAsQ4: bool = True,
    ) -> pl.DataFrame | None:
        """topic별 기간 커버리지 매트릭스."""
        if not self._hasDocs:
            return None
        topicKey = topic or "*"
        cacheKey = f"_docsSectionsCoverage:{topicKey}:{int(recentFirst)}:{int(annualAsQ4)}"
        if cacheKey in self._cache:
            return self._cache[cacheKey]

        sectionsFrame = self._company.docs.sections
        if sectionsFrame is None:
            self._cache[cacheKey] = None
            return None

        from dartlab.providers.dart._utils import _isPeriodColumn
        from dartlab.providers.dart.docs.sections import displayPeriod, sortPeriods

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

    # ── semantic registry ──

    def sectionsSemanticRegistry(
        self,
        *,
        topic: str | None = None,
        cadenceScope: str = "all",
        includeMixed: bool = True,
        collisionsOnly: bool = False,
    ) -> pl.DataFrame | None:
        """semantic registry / collisions."""
        if not self._hasDocs:
            return None
        normalizedScope = str(cadenceScope).strip().lower()
        topicKey = topic or "*"
        cacheKey = (
            f"_docsSectionsSemanticRegistry:{topicKey}:{normalizedScope}:{int(includeMixed)}:{int(collisionsOnly)}"
        )
        if cacheKey in self._cache:
            return self._cache[cacheKey]

        sectionsFrame = self._company.docs.sections
        if sectionsFrame is None:
            self._cache[cacheKey] = None
            return None

        from dartlab.providers.dart.docs.sections import semanticCollisions, semanticRegistry

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

    # ── structure registry ──

    def sectionsStructureRegistry(
        self,
        *,
        topic: str | None = None,
        cadenceScope: str = "all",
        includeMixed: bool = True,
        collisionsOnly: bool = False,
        nodeType: str | None = None,
    ) -> pl.DataFrame | None:
        """structure registry / collisions."""
        if not self._hasDocs:
            return None
        normalizedScope = str(cadenceScope).strip().lower()
        normalizedNodeType = str(nodeType).strip().lower() if isinstance(nodeType, str) and nodeType.strip() else "*"
        topicKey = topic or "*"
        cacheKey = f"_docsSectionsStructureRegistry:{topicKey}:{normalizedScope}:{int(includeMixed)}:{int(collisionsOnly)}:{normalizedNodeType}"
        if cacheKey in self._cache:
            return self._cache[cacheKey]

        sectionsFrame = self._company.docs.sections
        if sectionsFrame is None:
            self._cache[cacheKey] = None
            return None

        from dartlab.providers.dart.docs.sections import structureCollisions, structureRegistry

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

    # ── structure events / summary / changes ──

    def sectionsStructureEvents(
        self,
        *,
        topic: str | None = None,
        cadenceScope: str = "all",
        includeMixed: bool = True,
        changedOnly: bool = True,
        nodeType: str | None = None,
    ) -> pl.DataFrame | None:
        """structure events."""
        if not self._hasDocs:
            return None
        normalizedScope = str(cadenceScope).strip().lower()
        normalizedNodeType = str(nodeType).strip().lower() if isinstance(nodeType, str) and nodeType.strip() else "*"
        topicKey = topic or "*"
        cacheKey = f"_docsSectionsStructureEvents:{topicKey}:{normalizedScope}:{int(includeMixed)}:{int(changedOnly)}:{normalizedNodeType}"
        if cacheKey in self._cache:
            return self._cache[cacheKey]

        sectionsFrame = self._company.docs.sections
        if sectionsFrame is None:
            self._cache[cacheKey] = None
            return None

        from dartlab.providers.dart.docs.sections import structureEvents

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

    def sectionsStructureSummary(
        self,
        *,
        topic: str | None = None,
        cadenceScope: str = "all",
        includeMixed: bool = True,
        nodeType: str | None = None,
    ) -> pl.DataFrame | None:
        """structure summary."""
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

        sectionsFrame = self._company.docs.sections
        if sectionsFrame is None:
            self._cache[cacheKey] = None
            return None

        from dartlab.providers.dart.docs.sections import structureSummary

        result = structureSummary(
            sectionsFrame,
            topic=topic,
            cadenceScope=normalizedScope,
            includeMixed=includeMixed,
            nodeType=nodeType,
        )
        self._cache[cacheKey] = result
        return result

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
        """structure changes."""
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

        sectionsFrame = self._company.docs.sections
        if sectionsFrame is None:
            self._cache[cacheKey] = None
            return None

        from dartlab.providers.dart.docs.sections import structureChanges

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

    # ── subtables ──

    def topicSubtables(self, topic: str):
        """topic subtable (wide + long)."""
        cacheKey = f"_topicSubtables:{topic}"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        blocks = self._company._retrievalBlocks()
        if blocks is None or blocks.is_empty():
            self._cache[cacheKey] = None
            return None
        from dartlab.providers.dart.docs.sections import topicSubtables

        result = topicSubtables(blocks, topic)
        self._cache[cacheKey] = result
        return result

    def subtopicWide(self, topic: str) -> pl.DataFrame | None:
        """subtable wide pivot."""
        result = self.topicSubtables(topic)
        return None if result is None else result.wide

    def subtopicLong(self, topic: str) -> pl.DataFrame | None:
        """subtable long format."""
        result = self.topicSubtables(topic)
        return None if result is None else result.long


# ── module-level helpers ──


def _emptyTopicManifest() -> pl.DataFrame:
    return pl.DataFrame(
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


def _emptyTopicOutline() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "period": pl.Utf8,
            "sectionOrder": pl.Int64,
            "block": pl.Int64,
            "type": pl.Utf8,
            "title": pl.Utf8,
            "preview": pl.Utf8,
        }
    )


def _previewText(value: Any, limit: int = 160) -> str:
    text = str(value or "").replace("\r", " ").replace("\n", " ").strip()
    if len(text) <= limit:
        return text
    return text[: max(limit - 3, 0)].rstrip() + "..."
