"""Company 클래스 기본 테스트."""

import polars as pl
import pytest

from tests.conftest import SAMSUNG, requires_samsung

pytestmark = pytest.mark.integration


def _topicBlocksFrame(topic: str, rows: list[dict[str, object]]) -> pl.DataFrame:
    records: list[dict[str, object]] = []
    for idx, row in enumerate(rows):
        records.append(
            {
                "stockCode": "TEST",
                "period": row["period"],
                "periodOrder": row["periodOrder"],
                "sectionOrder": row.get("sectionOrder", 1),
                "rawTitle": row.get("rawTitle", topic),
                "topic": topic,
                "sourceTopic": row.get("sourceTopic", topic),
                "cellKey": f"TEST:{row['period']}:{topic}",
                "blockIdx": idx,
                "blockType": row.get("blockType", "text"),
                "blockLabel": row.get("blockLabel", "(root)"),
                "blockText": row.get("blockText", ""),
                "chars": len(str(row.get("blockText", ""))),
                "tableLines": row.get("tableLines", 0),
                "semanticTopic": row.get("semanticTopic"),
                "detailTopic": row.get("detailTopic"),
                "isBoilerplate": False,
                "isPlaceholder": row.get("isPlaceholder", False),
                "blockPriority": row.get("blockPriority", 3),
            }
        )
    return pl.DataFrame(records, strict=False)


def _legacyIndexDocsRows(company) -> list[dict[str, object]]:
    sec = company.docs.sections
    if sec is None or "topic" not in sec.columns:
        return []

    from dartlab.providers.dart.company import _CHAPTER_ORDER, _CHAPTER_TITLES
    from dartlab.providers.dart.docs.sections import displayPeriod, formatPeriodRange, sortPeriods

    periodCols = sortPeriods([column for column in sec.columns if str(column).startswith("20")], descending=True)
    periodRange = formatPeriodRange(periodCols, descending=True, annualAsQ4=True)
    existingPeriods = [column for column in periodCols if column in sec.columns]

    topicOrder = sec.get_column("topic").drop_nulls().unique(maintain_order=True).to_list()

    nonNullMap: dict[str, int] = {}
    if existingPeriods:
        nonNullExprs = [pl.col(column).is_not_null().any().cast(pl.Int8).alias(column) for column in existingPeriods]
        nonNullDf = sec.group_by("topic", maintain_order=True).agg(nonNullExprs)
        nonNullTopics = nonNullDf["topic"].to_list()
        nonNullData = {column: nonNullDf[column].to_list() for column in existingPeriods}
        for idx, topic in enumerate(nonNullTopics):
            nonNullMap[topic] = sum(1 for column in existingPeriods if nonNullData[column][idx])

    previewMap: dict[str, str] = {}
    if existingPeriods:
        firstExprs = [pl.col(column).drop_nulls().first().alias(column) for column in existingPeriods]
        previewDf = sec.group_by("topic", maintain_order=True).agg(firstExprs)
        previewTopics = previewDf["topic"].to_list()
        previewData = {column: previewDf[column].to_list() for column in existingPeriods}
        for idx, topic in enumerate(previewTopics):
            for column in existingPeriods:
                value = previewData[column][idx]
                if value is not None:
                    text = str(value).replace("\n", " ").strip()[:80]
                    previewMap[topic] = f"{displayPeriod(column, annualAsQ4=True)}: {text}"
                    break

    chapterMap: dict[str, str | None] = {}
    if "chapter" in sec.columns:
        chapterDf = sec.group_by("topic", maintain_order=True).agg(pl.col("chapter").first().alias("chapter"))
        chapterTopics = chapterDf["topic"].to_list()
        chapterVals = chapterDf["chapter"].to_list()
        for idx, topic in enumerate(chapterTopics):
            chapterMap[topic] = chapterVals[idx]

    rows: list[dict[str, object]] = []
    for rowIdx, topic in enumerate(topicOrder):
        chapterVal = chapterMap.get(topic)
        chapter = chapterVal if isinstance(chapterVal, str) and chapterVal else company._chapterForTopic(topic)
        chapterNum = _CHAPTER_ORDER.get(chapter, 12)
        rows.append(
            {
                "chapter": _CHAPTER_TITLES.get(chapter, chapter),
                "topic": topic,
                "label": company._topicLabel(topic),
                "kind": "docs",
                "source": "docs",
                "periods": periodRange,
                "shape": f"{nonNullMap.get(topic, 0)}기간",
                "preview": previewMap.get(topic, "-"),
                "_sortKey": (chapterNum, 100 + rowIdx),
            }
        )
    return rows


def _legacyIndexFrame(company) -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    if not company._hasDocs:
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

    rows.extend(company._indexFinanceRows())
    rows.extend(_legacyIndexDocsRows(company))
    rows.extend(company._indexReportRows(existingTopics={str(row["topic"]) for row in rows if row.get("topic")}))
    rows.sort(key=lambda row: row.get("_sortKey", (99, 999)))
    for row in rows:
        row.pop("_sortKey", None)
    return pl.DataFrame(rows, strict=False)


class TestProfileChangeLedgerHelpers:
    def test_change_point_collapses_repeated_periods(self):
        from dartlab.providers.dart.company import _buildTopicChangeLedger

        blocks = _topicBlocksFrame(
            "companyOverview",
            [
                {"period": "2024Q1", "periodOrder": 20241, "blockText": "회사는 반도체를 생산한다."},
                {"period": "2024Q2", "periodOrder": 20242, "blockText": "회사는 반도체를 생산한다."},
                {"period": "2024Q3", "periodOrder": 20243, "blockText": "회사는 반도체와 모바일 기기를 생산한다."},
            ],
        )

        ledger = _buildTopicChangeLedger(blocks)

        assert ledger.height == 2
        assert set(ledger["period"].to_list()) == {"2024Q1", "2024Q3"}

    def test_restated_text_is_separated_from_edited_text(self):
        from dartlab.providers.dart.company import _buildTopicChangeLedger

        blocks = _topicBlocksFrame(
            "companyOverview",
            [
                {"period": "2024Q1", "periodOrder": 20241, "blockText": "회사는 반도체를 생산한다."},
                {"period": "2024Q2", "periodOrder": 20242, "blockText": "회사는 반도체를 생산한다"},
            ],
        )

        ledger = _buildTopicChangeLedger(blocks)

        assert ledger.height == 2
        latest = ledger.filter(pl.col("period") == "2024Q2")
        assert latest.item(0, "changeType") == "restated"

    def test_table_structure_change_is_not_treated_as_value_edit(self):
        from dartlab.providers.dart.company import _buildTopicChangeLedger

        blocks = _topicBlocksFrame(
            "salesOrder",
            [
                {
                    "period": "2024Q1",
                    "periodOrder": 20241,
                    "blockType": "table",
                    "blockLabel": "(root)",
                    "blockText": "| 항목 | 값 |\n| --- | --- |\n| A | 1 |\n| B | 2 |",
                    "tableLines": 4,
                },
                {
                    "period": "2024Q2",
                    "periodOrder": 20242,
                    "blockType": "table",
                    "blockLabel": "(root)",
                    "blockText": "| 항목 | 값 |\n| --- | --- |\n| A | 1 |\n| B | 2 |\n| C | 3 |",
                    "tableLines": 5,
                },
            ],
        )

        ledger = _buildTopicChangeLedger(blocks)

        latest = ledger.filter(pl.col("period") == "2024Q2")
        assert latest.item(0, "changeType") == "added"

    def test_placeholder_is_tracked_with_own_change_type(self):
        from dartlab.providers.dart.company import _buildTopicChangeLedger

        blocks = _topicBlocksFrame(
            "companyOverview",
            [
                {"period": "2024Q1", "periodOrder": 20241, "blockText": "회사는 반도체를 생산한다."},
                {
                    "period": "2024Q2",
                    "periodOrder": 20242,
                    "blockText": "기업공시서식 작성기준에 따라 분기보고서에 기재하지 않습니다.",
                    "isPlaceholder": True,
                },
            ],
        )

        ledger = _buildTopicChangeLedger(blocks)

        latest = ledger.filter(pl.col("period") == "2024Q2")
        assert latest.item(0, "changeType") == "placeholder"


@requires_samsung
class TestCompany:
    @classmethod
    def setup_class(cls):
        from dartlab import Company

        cls.c = Company(SAMSUNG)

    def test_init_by_code(self):
        c = self.c
        assert c.stockCode == SAMSUNG
        assert c.corpName == "삼성전자"

    def test_repr(self):
        import dartlab

        dartlab.verbose = False
        c = self.c
        assert "005930" in repr(c)
        assert "삼성전자" in repr(c)
        dartlab.verbose = True

    def test_filings(self):
        c = self.c
        filings = c.filings()
        assert isinstance(filings, pl.DataFrame)
        assert len(filings) > 0
        assert "dartUrl" in filings.columns

    def test_invalid_name_raises(self):
        from dartlab import Company

        with pytest.raises(ValueError):
            Company("존재하지않는회사명zzz")

    def test_alphanumeric_dart_codes_are_routed_and_resolved(self):
        from dartlab import Company
        from dartlab.providers.dart.company import Company as DartEngineCompany

        c = Company("0009K0")
        assert isinstance(c, DartEngineCompany)
        assert c.stockCode == "0009K0"
        assert DartEngineCompany.resolve("0009K0") == "0009K0"
        payload = c.show("rawMaterial")
        assert payload is None or isinstance(payload, pl.DataFrame)

    def test_source_namespaces(self):
        from dartlab.providers.dart.report.types import PREFERRED_QUARTER

        c = self.c
        assert c.docs is not None
        assert c.finance is not None
        assert c.report is not None
        assert c.index is not None
        assert c.profile is not None
        assert isinstance(c.index, pl.DataFrame)
        assert len(c.report.apiTypes) == 28
        status = c.report.status()
        assert isinstance(status, pl.DataFrame)
        assert set(["apiType", "label", "preferredQuarter", "isPivot", "available"]).issubset(status.columns)
        assert (
            status.filter(pl.col("apiType") == "dividend").item(0, "preferredQuarter") == PREFERRED_QUARTER["dividend"]
        )

    def test_sections_includes_docs_and_finance(self):
        c = self.c
        assert c.sections is not None
        assert c.docs.sections is not None
        # sections ⊇ docs.sections (finance/report 행이 추가됨)
        assert c.sections.height >= c.docs.sections.height
        topics = c.sections["topic"].to_list()
        assert "BS" in topics
        assert "companyOverview" in topics
        assert "source" in c.sections.columns

    def test_first_layer_dataframe_contracts(self):
        c = self.c
        assert isinstance(c.filings(), pl.DataFrame)
        assert c.docs.sections is not None
        assert isinstance(c.docs.sections.raw, pl.DataFrame)
        assert isinstance(c.sections, pl.DataFrame)
        assert isinstance(c.sources, pl.DataFrame)
        assert isinstance(c.finance.BS, pl.DataFrame)
        assert isinstance(c.finance.IS, pl.DataFrame)
        assert isinstance(c.finance.CIS, pl.DataFrame)
        assert isinstance(c.finance.CF, pl.DataFrame)
        assert isinstance(c.finance.SCE, pl.DataFrame)

    def test_docs_sections_projection_and_semantic_registry_accessors(self):
        c = self.c
        ordered = c.docs.sectionsOrdered()
        coverage = c.docs.sectionsCoverage(topic="businessOverview")
        annual = c.docs.sectionsCadence("annual")
        registry = c.docs.sectionsSemanticRegistry(topic="mdna")
        collisions = c.docs.sectionsSemanticCollisions(topic="mdna")
        structureRegistry = c.docs.sectionsStructureRegistry(topic="businessOverview")
        structureCollisions = c.docs.sectionsStructureCollisions(topic="businessOverview")
        structureEvents = c.docs.sectionsStructureEvents(topic="businessOverview")
        structureSummary = c.docs.sectionsStructureSummary(topic="businessOverview")
        structureChanges = c.docs.sectionsStructureChanges(topic="businessOverview", nodeType="body")
        bodyStructureRegistry = c.docs.sectionsStructureRegistry(topic="businessOverview", nodeType="body")
        bodyStructureEvents = c.docs.sectionsStructureEvents(topic="businessOverview", nodeType="body")
        bodyStructureSummary = c.docs.sectionsStructureSummary(topic="businessOverview", nodeType="body")
        bodyStructureChanges = c.docs.sectionsStructureChanges(topic="businessOverview", nodeType="body")
        accessorPeriods = c.docs.sections.periods()
        accessorOrdered = c.docs.sections.ordered()
        accessorCoverage = c.docs.sections.coverage(topic="businessOverview")
        accessorAnnual = c.docs.sections.cadence("annual")
        accessorRegistry = c.docs.sections.semanticRegistry(topic="mdna")
        accessorCollisions = c.docs.sections.semanticCollisions(topic="mdna")
        accessorStructureRegistry = c.docs.sections.structureRegistry(topic="businessOverview")
        accessorStructureCollisions = c.docs.sections.structureCollisions(topic="businessOverview")
        accessorStructureEvents = c.docs.sections.structureEvents(topic="businessOverview")
        accessorStructureSummary = c.docs.sections.structureSummary(topic="businessOverview")
        accessorStructureChanges = c.docs.sections.structureChanges(topic="businessOverview", nodeType="body")
        accessorBodyStructureRegistry = c.docs.sections.structureRegistry(topic="businessOverview", nodeType="body")
        accessorBodyStructureEvents = c.docs.sections.structureEvents(topic="businessOverview", nodeType="body")
        accessorBodyStructureSummary = c.docs.sections.structureSummary(topic="businessOverview", nodeType="body")
        accessorBodyStructureChanges = c.docs.sections.structureChanges(topic="businessOverview", nodeType="body")

        assert isinstance(ordered, pl.DataFrame)
        assert isinstance(coverage, pl.DataFrame)
        assert isinstance(annual, pl.DataFrame)
        assert isinstance(registry, pl.DataFrame)
        assert isinstance(collisions, pl.DataFrame)
        assert isinstance(structureRegistry, pl.DataFrame)
        assert isinstance(structureCollisions, pl.DataFrame)
        assert isinstance(structureEvents, pl.DataFrame)
        assert isinstance(structureSummary, pl.DataFrame)
        assert isinstance(structureChanges, pl.DataFrame)
        assert isinstance(bodyStructureRegistry, pl.DataFrame)
        assert isinstance(bodyStructureEvents, pl.DataFrame)
        assert isinstance(bodyStructureSummary, pl.DataFrame)
        assert isinstance(bodyStructureChanges, pl.DataFrame)
        assert isinstance(accessorPeriods, list)
        assert isinstance(accessorOrdered, pl.DataFrame)
        assert isinstance(accessorCoverage, pl.DataFrame)
        assert isinstance(accessorAnnual, pl.DataFrame)
        assert isinstance(accessorRegistry, pl.DataFrame)
        assert isinstance(accessorCollisions, pl.DataFrame)
        assert isinstance(accessorStructureRegistry, pl.DataFrame)
        assert isinstance(accessorStructureCollisions, pl.DataFrame)
        assert isinstance(accessorStructureEvents, pl.DataFrame)
        assert isinstance(accessorStructureSummary, pl.DataFrame)
        assert isinstance(accessorStructureChanges, pl.DataFrame)
        assert isinstance(accessorBodyStructureRegistry, pl.DataFrame)
        assert isinstance(accessorBodyStructureEvents, pl.DataFrame)
        assert isinstance(accessorBodyStructureSummary, pl.DataFrame)
        assert isinstance(accessorBodyStructureChanges, pl.DataFrame)
        assert annual.height <= c.docs.sections.height
        orderedPeriodCols = [c for c in ordered.columns if c.startswith("20")]
        assert orderedPeriodCols == accessorPeriods
        assert orderedPeriodCols[0].endswith("Q4")
        assert {"topic", "period", "rawPeriod", "rowCount", "nonNullRows", "coverageRatio"}.issubset(
            set(coverage.columns)
        )
        assert ordered.equals(accessorOrdered)
        assert coverage.equals(accessorCoverage)
        assert {"textSemanticPathKey", "rawPathCount", "rawPaths", "hasCollision"}.issubset(set(registry.columns))
        assert {"textSemanticPathKey", "rawPathCount", "rawPaths", "hasCollision"}.issubset(set(collisions.columns))
        assert {
            "textComparablePathKey",
            "rawSemanticPathCount",
            "rawSemanticPaths",
            "activePeriodCount",
            "activePathCounts",
            "multiPathPeriods",
            "structurePattern",
            "hasCollision",
        }.issubset(set(structureRegistry.columns))
        assert {
            "textComparablePathKey",
            "periodLane",
            "fromPeriod",
            "toPeriod",
            "fromPathCount",
            "toPathCount",
            "addedPaths",
            "removedPaths",
            "eventType",
        }.issubset(set(structureEvents.columns))
        assert {
            "textComparablePathKey",
            "structurePattern",
            "latestPeriod",
            "latestPeriodLane",
            "latestPathCount",
            "eventCount",
            "latestEventType",
        }.issubset(set(structureSummary.columns))
        assert {
            "textComparablePathKey",
            "anchorPeriod",
            "isLatest",
            "isStale",
            "latestEventType",
        }.issubset(set(structureChanges.columns))
        assert annual.equals(accessorAnnual)
        assert registry.equals(accessorRegistry)
        assert collisions.equals(accessorCollisions)
        assert structureRegistry.equals(accessorStructureRegistry)
        assert structureCollisions.equals(accessorStructureCollisions)
        assert structureEvents.equals(accessorStructureEvents)
        assert structureSummary.equals(accessorStructureSummary)
        assert structureChanges.equals(accessorStructureChanges)
        assert bodyStructureRegistry.equals(accessorBodyStructureRegistry)
        assert bodyStructureEvents.equals(accessorBodyStructureEvents)
        assert bodyStructureSummary.equals(accessorBodyStructureSummary)
        assert bodyStructureChanges.equals(accessorBodyStructureChanges)
        assert bodyStructureRegistry.height <= structureRegistry.height
        assert bodyStructureEvents.height <= structureEvents.height
        assert bodyStructureSummary.height <= structureSummary.height
        assert bodyStructureChanges.height <= bodyStructureSummary.height
        assert set(bodyStructureRegistry["textNodeType"].unique().to_list()) == {"body"}
        assert set(bodyStructureEvents["textNodeType"].unique().to_list()) == {"body"}
        assert set(bodyStructureSummary["textNodeType"].unique().to_list()) == {"body"}
        assert set(bodyStructureChanges["textNodeType"].unique().to_list()) == {"body"}

    def test_docs_sections_structure_helpers_return_valid_dataframes(self):
        c = self.c
        registry = c.docs.sections.structureRegistry(topic="businessOverview", nodeType="body")
        events = c.docs.sections.structureEvents(topic="businessOverview", nodeType="body")
        summary = c.docs.sections.structureSummary(topic="businessOverview", nodeType="body")
        changes = c.docs.sections.structureChanges(topic="businessOverview", nodeType="body")

        assert isinstance(registry, pl.DataFrame)
        assert isinstance(events, pl.DataFrame)
        assert isinstance(summary, pl.DataFrame)
        assert isinstance(changes, pl.DataFrame)

    def test_show_accepts_q4_alias_for_annual_sections_period(self):
        c = self.c
        annual = c.show("companyOverview", 0, period="2025")
        annualQ4 = c.show("companyOverview", 0, period="2025Q4")

        assert isinstance(annual, pl.DataFrame)
        assert isinstance(annualQ4, pl.DataFrame)
        assert "2025" in annual.columns
        assert "2025Q4" in annualQ4.columns
        assert annual.item(0, "2025") == annualQ4.item(0, "2025Q4")

    def test_show_period_filter_handles_finance_exact_q4_and_annual_alias(self):
        c = self.c
        exactQ4 = c.show("BS", period="2024Q4")
        annualAlias = c.show("BS", period="2024")

        assert isinstance(exactQ4, pl.DataFrame)
        assert isinstance(annualAlias, pl.DataFrame)
        assert exactQ4.columns == ["계정명", "2024Q4"]
        assert annualAlias.columns == ["계정명", "2024"]
        assert exactQ4["계정명"].to_list() == annualAlias["계정명"].to_list()

    def test_profile_facts_include_docs_source(self):
        c = self.c
        facts = c.profile.facts
        assert facts is not None
        assert "source" in facts.columns
        assert "docs" in set(facts["source"].unique().to_list())

    def test_profile_trace_for_docs_topic(self):
        c = self.c
        traced = c.profile.trace("riskDerivative")
        assert traced is not None
        assert traced["primarySource"] == "docs"

    def test_finance_cis_and_sce_are_exposed(self):
        c = self.c
        assert isinstance(c.finance.CIS, pl.DataFrame)
        assert isinstance(c.CIS, pl.DataFrame)
        assert isinstance(c.finance.SCE, pl.DataFrame)
        assert isinstance(c.SCE, pl.DataFrame)

    def test_sections_contain_docs_topics(self):
        c = self.c
        sections = c.sections
        assert sections is not None
        topics = sections["topic"].to_list()
        # sections는 docs 수평화 결과 — docs topic이 포함되어야 함
        for topic in ["dividend", "employee", "majorHolder", "audit"]:
            assert topic in topics

    def test_sections_hide_raw_source_topics(self):
        c = self.c
        sections = c.sections
        assert sections is not None
        topics = set(sections["topic"].to_list())
        assert "주요제품및원재료등" not in topics
        assert "파생상품등에관한사항" not in topics
        assert "I.회사의개황" not in topics

    def test_profile_trace_for_finance_and_report_topics(self):
        c = self.c
        assert c.profile.trace("dividend")["primarySource"] == "report"
        assert c.profile.trace("BS")["primarySource"] == "finance"
        assert c.profile.trace("CIS")["primarySource"] == "finance"
        ratioTrace = c.trace("ratios")
        assert ratioTrace["primarySource"] == "finance"
        assert ratioTrace["template"] == "general"
        assert ratioTrace["coverage"] in {"full", "partial"}
        assert ratioTrace["rowCount"] is not None
        assert ratioTrace["yearCount"] is not None

    def test_index_and_profile_accessor(self):
        c = self.c
        assert c.index.height > 0
        assert set(["chapter", "topic", "kind", "source", "periods", "shape", "preview"]).issubset(set(c.index.columns))
        assert c.sections is not None
        assert isinstance(c.sections, pl.DataFrame)
        assert c.profile.facts is not None
        assert isinstance(c.profile.facts, pl.DataFrame)

    def test_profile_trace_returns_provenance(self):
        c = self.c
        traced = c.profile.trace("BS")
        assert traced is not None
        assert traced["primarySource"] == "finance"
        traced_docs = c.profile.trace("companyOverview")
        assert traced_docs is not None
        assert traced_docs["primarySource"] == "docs"

    def test_report_available_api_types_matches_extract_without_extract_caches(self):
        from dartlab.providers.dart.company import Company as DartCompany
        from dartlab.providers.dart.report.types import API_TYPES

        fastCompany = DartCompany(SAMSUNG)
        available = fastCompany.report.availableApiTypes

        reportCacheKeys = set(fastCompany.report._cache._store.keys())
        assert "_availableApiTypes" in reportCacheKeys
        assert not any(key.startswith("_extract_") for key in reportCacheKeys)

        baselineCompany = DartCompany(SAMSUNG)
        expected = [name for name in API_TYPES if baselineCompany.report.extract(name) is not None]
        assert available == expected

    def test_finance_trace_fast_path_matches_profile_trace_without_heavy_caches(self):
        from dartlab.providers.dart.company import Company as DartCompany

        for topic in ("BS", "IS", "CF", "CIS", "SCE"):
            fastCompany = DartCompany(SAMSUNG)
            traced = fastCompany.trace(topic, period="2024")

            assert traced is not None
            assert traced["primarySource"] == "finance"
            cacheKeys = set(fastCompany._cache._store.keys())
            assert "_profileFacts" not in cacheKeys
            assert "retrievalBlocks" not in cacheKeys
            assert "sections" not in cacheKeys
            assert "_sections" not in cacheKeys

            baselineCompany = DartCompany(SAMSUNG)
            assert traced == baselineCompany.profile.trace(topic, period="2024")

    def test_show_finance_fast_path_avoids_sections(self):
        from dartlab.providers.dart.company import Company as DartCompany

        for topic in ("BS", "IS", "CF", "CIS", "SCE", "ratios"):
            fastCompany = DartCompany(SAMSUNG)
            result = fastCompany.show(topic)

            assert result is not None
            assert isinstance(result, pl.DataFrame)
            assert fastCompany.show(topic, 0).equals(result, null_equal=True)
            cacheKeys = set(fastCompany._cache._store.keys())
            assert "sections" not in cacheKeys
            assert "_sections" not in cacheKeys

            baselineCompany = DartCompany(SAMSUNG)
            sections = baselineCompany.sections
            assert sections is not None
            topicRows = sections.filter(pl.col("topic") == topic)
            blockIndex = baselineCompany._buildBlockIndex(topicRows)
            assert blockIndex.height == 1
            expected = baselineCompany._showFinanceTopic(topic)
            assert expected is not None
            if topic in {"BS", "IS", "CF", "CIS", "SCE"}:
                expected = baselineCompany._cleanFinanceDataFrame(expected, topic)
            assert result.equals(expected, null_equal=True)

    def test_index_docs_fast_path_matches_legacy_sections_without_heavy_caches(self):
        from dartlab.providers.dart.company import Company as DartCompany

        fastCompany = DartCompany(SAMSUNG)
        result = fastCompany._indexDocsRows()

        cacheKeys = set(fastCompany._cache._store.keys())
        assert "sections" not in cacheKeys
        assert "_sections" not in cacheKeys
        assert "_profileFacts" not in cacheKeys
        assert "retrievalBlocks" not in cacheKeys

        baselineCompany = DartCompany(SAMSUNG)
        expected = _legacyIndexDocsRows(baselineCompany)
        assert result == expected

    def test_index_fast_path_matches_legacy_index_without_sections(self):
        from dartlab.providers.dart.company import Company as DartCompany

        fastCompany = DartCompany(SAMSUNG)
        result = fastCompany.index

        cacheKeys = set(fastCompany._cache._store.keys())
        assert "sections" not in cacheKeys
        assert "_sections" not in cacheKeys
        assert "_profileFacts" not in cacheKeys
        assert "retrievalBlocks" not in cacheKeys

        baselineCompany = DartCompany(SAMSUNG)
        expected = _legacyIndexFrame(baselineCompany)
        assert result.equals(expected, null_equal=True)

    def test_open_and_topics_surface_company_payloads(self):
        c = self.c
        topicList = c.topics["topic"].to_list()
        assert "BS" in topicList
        assert "ratios" in topicList
        assert isinstance(c.show("BS"), pl.DataFrame)
        assert isinstance(c.show("BS", raw=True), pl.DataFrame)
        assert isinstance(c.show("ratios"), pl.DataFrame)
        assert isinstance(c.show("dividend"), pl.DataFrame)
        assert isinstance(c.show("riskDerivative", raw=False), pl.DataFrame)

    def test_show_topic_returns_block_index(self):
        c = self.c
        idx = c.show("salesOrder")
        assert isinstance(idx, pl.DataFrame)
        assert {"block", "type", "source"}.issubset(set(idx.columns))
        # block=1 접근하면 실제 데이터
        table = c.show("salesOrder", 1)
        assert table is None or isinstance(table, pl.DataFrame)

    def test_show_block_returns_data(self):
        c = self.c
        # docs text
        text = c.show("companyOverview", 0)
        assert text is None or isinstance(text, pl.DataFrame)
        # docs table
        table = c.show("companyOverview", 1)
        assert table is None or isinstance(table, pl.DataFrame)
        # finance
        bs = c.show("BS", 0)
        assert bs is None or isinstance(bs, pl.DataFrame)

    def test_report_result_surface_is_unified(self):
        from dartlab.providers.dart.report.types import ReportResult

        c = self.c
        dividend = c.report.result("dividend")
        treasury = c.report.result("treasuryStock")

        assert dividend is not None
        assert hasattr(dividend, "df")
        assert isinstance(dividend.df, pl.DataFrame)

        assert treasury is None or isinstance(treasury, ReportResult)
        if treasury is not None:
            assert isinstance(treasury.df, pl.DataFrame)

    def test_index_includes_finance_ratio_series(self):
        c = self.c
        ratios = c.index.filter(pl.col("topic") == "ratios")
        assert ratios.height == 1
        assert ratios.item(0, "chapter") == "III. 재무에 관한 사항"
        assert ratios.item(0, "source") == "finance"
        assert ratios.item(0, "label") == "재무비율"

    def test_public_index_show_trace_surface(self):
        c = self.c
        assert isinstance(c.index, pl.DataFrame)
        assert c.index.height > 0
        overview = c.show("companyOverview")
        assert overview is None or isinstance(overview, pl.DataFrame)
        traced = c.trace("dividend")
        assert traced is not None
        assert traced["primarySource"] == "report"

    def test_show_returns_block_index_for_docs_topic(self):
        c = self.c
        overview = c.show("companyOverview")
        assert overview is not None
        assert isinstance(overview, pl.DataFrame)
        assert {"block", "type", "source"}.issubset(set(overview.columns))
