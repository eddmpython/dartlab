from __future__ import annotations

import polars as pl

from dartlab import Company
from dartlab.engines.dart.docs.sections import pipeline, textStructure
from dartlab.engines.dart.docs.sections.textStructure import parseTextStructure, parseTextStructureWithState

SAMSUNG = "005930"


def test_parse_text_structure_splits_levels_and_bodies():
    text = (
        "1. 회사의 개요\n"
        "가. 회사의 법적ㆍ상업적 명칭\n"
        "당사의 명칭은 삼성전자주식회사입니다.\n"
        "나. 본점소재지\n"
        "본점은 경기도 수원시에 있습니다."
    )

    rows = parseTextStructure(text, sourceBlockOrder=0)

    assert [row["textNodeType"] for row in rows] == ["heading", "heading", "body", "heading", "body"]
    assert [row["textLevel"] for row in rows] == [1, 2, 2, 2, 2]
    assert rows[1]["textPathKey"] == "회사의개요 > 회사의법적상업적명칭"
    assert rows[2]["textPathKey"] == "회사의개요 > 회사의법적상업적명칭"


def test_parse_text_structure_carries_heading_state_across_blocks():
    first, stack = parseTextStructureWithState(
        "3. 재무상태 및 영업실적(연결 기준)\n가. 재무상태",
        sourceBlockOrder=0,
    )
    second, _stack2 = parseTextStructureWithState(
        "제56기 당사 자산은 전년 대비 증가하였습니다.\n나. 영업실적\n매출액은 증가하였습니다.",
        sourceBlockOrder=1,
        initialHeadings=stack,
    )

    assert first[-1]["textPathKey"] == "재무상태및영업실적연결기준 > 재무상태"
    assert second[0]["textNodeType"] == "body"
    assert second[0]["textPathKey"] == "재무상태및영업실적연결기준 > 재무상태"
    assert second[1]["textNodeType"] == "heading"
    assert second[1]["textPathKey"] == "재무상태및영업실적연결기준 > 영업실적"


def test_parse_text_structure_uses_topic_canonical_key_for_root_alias(monkeypatch):
    def fake_map_section_title(title: str) -> str:
        normalized = title.replace(" ", "")
        if normalized in {"사업의개요", "사업의내용"}:
            return "businessOverview"
        return normalized

    monkeypatch.setattr(textStructure, "mapSectionTitle", fake_map_section_title)

    rows = parseTextStructure(
        "1. 사업의 내용\n가. 사업부문별 현황\n당사는 DX와 DS 부문을 운영합니다.",
        sourceBlockOrder=0,
        topic="businessOverview",
    )

    assert rows[0]["textPathKey"] == "@topic:businessOverview"
    assert rows[1]["textPathKey"] == "@topic:businessOverview > 사업부문별현황"
    assert rows[2]["textPathKey"] == "@topic:businessOverview > 사업부문별현황"


def test_parse_text_structure_preserves_temporal_marker_without_polluting_path():
    rows = parseTextStructure(
        "[2021년 12월]\n마. 환율변동 영향\n환율 리스크를 관리합니다.",
        sourceBlockOrder=0,
        topic="mdna",
    )

    assert rows[0]["textNodeType"] == "heading"
    assert rows[0]["textPathKey"] == "@marker:2021년12월"
    assert rows[1]["textPathKey"] == "환율변동영향"
    assert rows[2]["textPathKey"] == "환율변동영향"


def test_parse_text_structure_demotes_redundant_topic_root_alias(monkeypatch):
    def fake_map_section_title(title: str) -> str:
        normalized = title.replace(" ", "")
        if normalized in {"사업의개요", "사업의내용"}:
            return "businessOverview"
        return normalized

    monkeypatch.setattr(textStructure, "mapSectionTitle", fake_map_section_title)

    rows = parseTextStructure(
        "1. 사업의 개요\nII. 사업의 내용\n가. 사업부문별 현황\n당사는 DX와 DS 부문을 운영합니다.",
        sourceBlockOrder=0,
        topic="businessOverview",
    )

    assert rows[0]["textStructural"] is True
    assert rows[0]["textPathKey"] == "@topic:businessOverview"
    assert rows[1]["textStructural"] is False
    assert rows[1]["textPathKey"] == "@alias:사업의내용"
    assert rows[2]["textPathKey"] == "@topic:businessOverview > 사업부문별현황"
    assert rows[3]["textPathKey"] == "@topic:businessOverview > 사업부문별현황"


def test_parse_text_structure_adds_semantic_path_keys_for_alias_headings():
    rows = parseTextStructure(
        "3. 재무상태 및 영업실적(연결 기준)\n가. 조직개편\n조직이 개편되었습니다.",
        sourceBlockOrder=0,
        topic="mdna",
    )

    assert rows[0]["textPathKey"] == "재무상태및영업실적연결기준"
    assert rows[0]["textSemanticPathKey"] == "재무상태및영업실적"
    assert rows[1]["textPathKey"] == "재무상태및영업실적연결기준 > 조직개편"
    assert rows[1]["textSemanticPathKey"] == "재무상태및영업실적 > 조직변경"
    assert rows[2]["textSemanticPathKey"] == "재무상태및영업실적 > 조직변경"


def test_parse_text_structure_normalizes_safe_business_overview_aliases(monkeypatch):
    def fake_map_section_title(title: str) -> str:
        normalized = title.replace(" ", "")
        if normalized in {"사업의개요", "사업의내용"}:
            return "businessOverview"
        return normalized

    monkeypatch.setattr(textStructure, "mapSectionTitle", fake_map_section_title)

    first = parseTextStructure(
        "1. 사업의 개요\n가. 생산 및 설비에 관한 사항\n생산 능력을 설명합니다.",
        sourceBlockOrder=0,
        topic="businessOverview",
    )
    second = parseTextStructure(
        "1. 사업의 내용\n가. 생산 및 설비\n생산 능력을 설명합니다.",
        sourceBlockOrder=0,
        topic="businessOverview",
    )

    firstBody = next(row for row in first if row["textNodeType"] == "body")
    secondBody = next(row for row in second if row["textNodeType"] == "body")

    assert firstBody["textPathKey"] != secondBody["textPathKey"]
    assert firstBody["textSemanticPathKey"] == "@topic:businessOverview > 생산및설비"
    assert secondBody["textSemanticPathKey"] == "@topic:businessOverview > 생산및설비"


def test_sections_horizontalize_numbering_changes_into_same_row(monkeypatch):
    def fake_map_section_title(_title: str) -> str:
        return "companyOverview"

    def fake_iter_period_subsets(_stockCode: str, *, sinceYear: int = 2016):
        assert sinceYear == 2016
        schema = {
            "section_order": pl.Int64,
            "section_title": pl.Utf8,
            "section_content": pl.Utf8,
        }
        yield (
            "2024",
            "annual",
            "section_content",
            pl.DataFrame(
                [
                    {"section_order": 1, "section_title": "I. 회사의 개요", "section_content": "장 소개"},
                    {
                        "section_order": 2,
                        "section_title": "1. 회사의 개요",
                        "section_content": (
                            "가. 회사의 법적ㆍ상업적 명칭\n"
                            "당사의 명칭은 삼성전자주식회사입니다.\n"
                            "나. 본점소재지\n"
                            "본점은 경기도 수원시에 있습니다."
                        ),
                    },
                ],
                schema=schema,
            ),
        )
        yield (
            "2025",
            "annual",
            "section_content",
            pl.DataFrame(
                [
                    {"section_order": 1, "section_title": "I. 회사의 개요", "section_content": "장 소개"},
                    {
                        "section_order": 2,
                        "section_title": "1. 회사의 개요",
                        "section_content": (
                            "나. 회사의 법적ㆍ상업적 명칭\n"
                            "당사의 명칭은 삼성전자주식회사입니다.\n"
                            "다. 본점소재지\n"
                            "본점은 경기도 수원시에 있습니다."
                        ),
                    },
                ],
                schema=schema,
            ),
        )

    monkeypatch.setattr(pipeline, "mapSectionTitle", fake_map_section_title)
    monkeypatch.setattr(pipeline, "iterPeriodSubsets", fake_iter_period_subsets)

    df = pipeline.sections("TEST")

    assert df is not None
    assert {
        "sourceBlockOrder",
        "textNodeType",
        "textLevel",
        "textPathKey",
        "segmentKey",
        "segmentOrder",
        "segmentOccurrence",
    }.issubset(set(df.columns))

    topic = df.filter(pl.col("topic") == "companyOverview")
    legal_heading = topic.filter(
        (pl.col("textNodeType") == "heading")
        & pl.col("2024").str.contains("법적", literal=True)
        & pl.col("2025").str.contains("법적", literal=True)
    )
    assert legal_heading.height == 1
    assert legal_heading.item(0, "2024") == "가. 회사의 법적ㆍ상업적 명칭"
    assert legal_heading.item(0, "2025") == "나. 회사의 법적ㆍ상업적 명칭"

    legal_body = topic.filter(
        (pl.col("textNodeType") == "body")
        & pl.col("2024").str.contains("삼성전자주식회사", literal=True)
        & pl.col("2025").str.contains("삼성전자주식회사", literal=True)
    )
    assert legal_body.height == 1
    assert "삼성전자주식회사" in legal_body.item(0, "2024")
    assert "삼성전자주식회사" in legal_body.item(0, "2025")
    assert legal_body.item(0, "segmentOccurrence") == 1


def test_sections_horizontalize_same_path_when_source_block_order_shifts(monkeypatch):
    def fake_map_section_title(_title: str) -> str:
        return "companyOverview"

    def fake_iter_period_subsets(_stockCode: str, *, sinceYear: int = 2016):
        assert sinceYear == 2016
        schema = {
            "section_order": pl.Int64,
            "section_title": pl.Utf8,
            "section_content": pl.Utf8,
        }
        yield (
            "2024",
            "annual",
            "section_content",
            pl.DataFrame(
                [
                    {"section_order": 1, "section_title": "I. 회사의 개요", "section_content": "장 소개"},
                    {
                        "section_order": 2,
                        "section_title": "1. 회사의 개요",
                        "section_content": (
                            "가. 회사의 법적ㆍ상업적 명칭\n"
                            "당사의 명칭은 삼성전자주식회사입니다.\n"
                            "나. 본점소재지\n"
                            "본점은 경기도 수원시에 있습니다."
                        ),
                    },
                ],
                schema=schema,
            ),
        )
        yield (
            "2025",
            "annual",
            "section_content",
            pl.DataFrame(
                [
                    {"section_order": 1, "section_title": "I. 회사의 개요", "section_content": "장 소개"},
                    {
                        "section_order": 2,
                        "section_title": "1. 회사의 개요",
                        "section_content": (
                            "가. 회사의 법적ㆍ상업적 명칭\n"
                            "당사의 명칭은 삼성전자주식회사입니다.\n\n"
                            "| 구분 | 값 |\n"
                            "| --- | --- |\n"
                            "| 예시 | 1 |\n\n"
                            "나. 본점소재지\n"
                            "본점은 경기도 수원시에 있습니다."
                        ),
                    },
                ],
                schema=schema,
            ),
        )

    monkeypatch.setattr(pipeline, "mapSectionTitle", fake_map_section_title)
    monkeypatch.setattr(pipeline, "iterPeriodSubsets", fake_iter_period_subsets)

    df = pipeline.sections("TEST")

    assert df is not None
    topic = df.filter(pl.col("topic") == "companyOverview")
    location_body = topic.filter(
        (pl.col("textNodeType") == "body")
        & pl.col("2024").str.contains("경기도 수원시", literal=True)
        & pl.col("2025").str.contains("경기도 수원시", literal=True)
    )
    assert location_body.height == 1
    assert location_body.item(0, "segmentOccurrence") == 1


def test_sections_horizontalize_semantic_alias_headings_into_same_row(monkeypatch):
    def fake_map_section_title(_title: str) -> str:
        return "mdna"

    def fake_iter_period_subsets(_stockCode: str, *, sinceYear: int = 2016):
        assert sinceYear == 2016
        schema = {
            "section_order": pl.Int64,
            "section_title": pl.Utf8,
            "section_content": pl.Utf8,
        }
        yield (
            "2024",
            "annual",
            "section_content",
            pl.DataFrame(
                [
                    {"section_order": 1, "section_title": "III. 재무상태 및 영업실적", "section_content": "장 소개"},
                    {
                        "section_order": 2,
                        "section_title": "3. 재무상태 및 영업실적",
                        "section_content": ("3. 재무상태 및 영업실적(연결 기준)\n가. 조직개편\n조직이 개편되었습니다."),
                    },
                ],
                schema=schema,
            ),
        )
        yield (
            "2025",
            "annual",
            "section_content",
            pl.DataFrame(
                [
                    {"section_order": 1, "section_title": "III. 재무상태 및 영업실적", "section_content": "장 소개"},
                    {
                        "section_order": 2,
                        "section_title": "3. 재무상태 및 영업실적",
                        "section_content": ("3. 재무상태 및 영업실적\n가. 조직의 변경\n조직이 개편되었습니다."),
                    },
                ],
                schema=schema,
            ),
        )

    monkeypatch.setattr(pipeline, "mapSectionTitle", fake_map_section_title)
    monkeypatch.setattr(textStructure, "mapSectionTitle", fake_map_section_title)
    monkeypatch.setattr(pipeline, "iterPeriodSubsets", fake_iter_period_subsets)

    df = pipeline.sections("TEST")

    assert df is not None
    heading = df.filter(
        (pl.col("topic") == "mdna")
        & (pl.col("textNodeType") == "heading")
        & (pl.col("textSemanticPathKey") == "@topic:mdna > 조직변경")
    )
    assert heading.height == 1
    assert heading.item(0, "2024") == "가. 조직개편"
    assert heading.item(0, "2025") == "가. 조직의 변경"
    assert heading.item(0, "textPathKey") == "@topic:mdna > 조직의변경"
    assert heading.item(0, "textPathVariantCount") == 2
    assert set(heading.item(0, "textPathVariants")) == {"@topic:mdna > 조직개편", "@topic:mdna > 조직의변경"}

    body = df.filter(
        (pl.col("topic") == "mdna")
        & (pl.col("textNodeType") == "body")
        & (pl.col("textSemanticPathKey") == "@topic:mdna > 조직변경")
    )
    assert body.height == 1
    assert "조직이 개편되었습니다." in body.item(0, "2024")
    assert "조직이 개편되었습니다." in body.item(0, "2025")
    assert body.item(0, "textPathVariantCount") == 2


def test_sections_semantic_registry_tracks_raw_path_variants(monkeypatch):
    def fake_map_section_title(_title: str) -> str:
        return "mdna"

    def fake_iter_period_subsets(_stockCode: str, *, sinceYear: int = 2016):
        assert sinceYear == 2016
        schema = {
            "section_order": pl.Int64,
            "section_title": pl.Utf8,
            "section_content": pl.Utf8,
        }
        yield (
            "2024",
            "annual",
            "section_content",
            pl.DataFrame(
                [
                    {"section_order": 1, "section_title": "III. 재무상태 및 영업실적", "section_content": "장 소개"},
                    {
                        "section_order": 2,
                        "section_title": "3. 재무상태 및 영업실적",
                        "section_content": "3. 재무상태 및 영업실적(연결 기준)\n가. 조직개편\n조직이 개편되었습니다.",
                    },
                ],
                schema=schema,
            ),
        )
        yield (
            "2025",
            "annual",
            "section_content",
            pl.DataFrame(
                [
                    {"section_order": 1, "section_title": "III. 재무상태 및 영업실적", "section_content": "장 소개"},
                    {
                        "section_order": 2,
                        "section_title": "3. 재무상태 및 영업실적",
                        "section_content": "3. 재무상태 및 영업실적\n가. 조직의 변경\n조직이 개편되었습니다.",
                    },
                ],
                schema=schema,
            ),
        )

    monkeypatch.setattr(pipeline, "mapSectionTitle", fake_map_section_title)
    monkeypatch.setattr(textStructure, "mapSectionTitle", fake_map_section_title)
    monkeypatch.setattr(pipeline, "iterPeriodSubsets", fake_iter_period_subsets)

    df = pipeline.sections("TEST")
    assert df is not None

    registry = pipeline.semanticRegistry(df, topic="mdna")
    body = registry.filter(
        (pl.col("textNodeType") == "body") & (pl.col("textSemanticPathKey") == "@topic:mdna > 조직변경")
    )
    assert body.height == 1
    assert body.item(0, "rawPathCount") == 2
    assert set(body.item(0, "rawPaths")) == {"@topic:mdna > 조직개편", "@topic:mdna > 조직의변경"}
    assert body.item(0, "hasCollision") is True

    collisions = pipeline.semanticCollisions(df, topic="mdna")
    assert collisions.filter(pl.col("textSemanticPathKey") == "@topic:mdna > 조직변경").height == 2


def test_sections_horizontalize_root_alias_children_into_same_row(monkeypatch):
    def fake_map_section_title(title: str) -> str:
        normalized = title.replace(" ", "")
        if normalized in {"사업의개요", "사업의내용"}:
            return "businessOverview"
        return normalized

    def fake_iter_period_subsets(_stockCode: str, *, sinceYear: int = 2016):
        assert sinceYear == 2016
        schema = {
            "section_order": pl.Int64,
            "section_title": pl.Utf8,
            "section_content": pl.Utf8,
        }
        yield (
            "2024",
            "annual",
            "section_content",
            pl.DataFrame(
                [
                    {"section_order": 1, "section_title": "II. 사업의 개요", "section_content": "장 소개"},
                    {
                        "section_order": 2,
                        "section_title": "1. 사업의 개요",
                        "section_content": ("1. 사업의 개요\n가. 사업부문별 현황\n당사는 DX와 DS 부문을 운영합니다."),
                    },
                ],
                schema=schema,
            ),
        )
        yield (
            "2025",
            "annual",
            "section_content",
            pl.DataFrame(
                [
                    {"section_order": 1, "section_title": "II. 사업의 내용", "section_content": "장 소개"},
                    {
                        "section_order": 2,
                        "section_title": "1. 사업의 내용",
                        "section_content": ("1. 사업의 내용\n가. 사업부문별 현황\n당사는 DX와 DS 부문을 운영합니다."),
                    },
                ],
                schema=schema,
            ),
        )

    monkeypatch.setattr(pipeline, "mapSectionTitle", fake_map_section_title)
    monkeypatch.setattr(textStructure, "mapSectionTitle", fake_map_section_title)
    monkeypatch.setattr(pipeline, "iterPeriodSubsets", fake_iter_period_subsets)

    df = pipeline.sections("TEST")

    assert df is not None
    child_body = df.filter(
        (pl.col("topic") == "businessOverview")
        & (pl.col("textNodeType") == "body")
        & (pl.col("textPathKey") == "@topic:businessOverview > 사업부문별현황")
    )
    assert child_body.height == 1
    assert "DX와 DS 부문" in child_body.item(0, "2024")
    assert "DX와 DS 부문" in child_body.item(0, "2025")


def test_sections_do_not_merge_distinct_business_unit_segments(monkeypatch):
    def fake_map_section_title(_title: str) -> str:
        return "businessOverview"

    def fake_iter_period_subsets(_stockCode: str, *, sinceYear: int = 2016):
        assert sinceYear == 2016
        schema = {
            "section_order": pl.Int64,
            "section_title": pl.Utf8,
            "section_content": pl.Utf8,
        }
        yield (
            "2024",
            "annual",
            "section_content",
            pl.DataFrame(
                [
                    {"section_order": 1, "section_title": "II. 사업의 개요", "section_content": "장 소개"},
                    {
                        "section_order": 2,
                        "section_title": "1. 사업의 개요",
                        "section_content": ("1. 사업의 개요\n가. 사업부문별 현황\n(1) DX부문\nDX 설명입니다."),
                    },
                ],
                schema=schema,
            ),
        )
        yield (
            "2025",
            "annual",
            "section_content",
            pl.DataFrame(
                [
                    {"section_order": 1, "section_title": "II. 사업의 개요", "section_content": "장 소개"},
                    {
                        "section_order": 2,
                        "section_title": "1. 사업의 개요",
                        "section_content": ("1. 사업의 개요\n가. 사업부문별 현황\n(1) CE부문\nCE 설명입니다."),
                    },
                ],
                schema=schema,
            ),
        )

    monkeypatch.setattr(pipeline, "mapSectionTitle", fake_map_section_title)
    monkeypatch.setattr(textStructure, "mapSectionTitle", fake_map_section_title)
    monkeypatch.setattr(pipeline, "iterPeriodSubsets", fake_iter_period_subsets)

    df = pipeline.sections("TEST")

    assert df is not None
    unitBodies = df.filter(
        (pl.col("topic") == "businessOverview")
        & (pl.col("textNodeType") == "body")
        & (pl.col("textSemanticParentPathKey") == "@topic:businessOverview > 사업부문현황")
    ).sort("textSemanticPathKey")
    assert unitBodies.height == 2

    first = unitBodies.row(0, named=True)
    second = unitBodies.row(1, named=True)
    assert first["textSemanticPathKey"] != second["textSemanticPathKey"]
    assert first["2024"] is None or first["2025"] is None
    assert second["2024"] is None or second["2025"] is None


def test_sections_adds_cadence_scope_metadata(monkeypatch):
    def fake_map_section_title(_title: str) -> str:
        return "businessOverview"

    def fake_iter_period_subsets(_stockCode: str, *, sinceYear: int = 2016):
        assert sinceYear == 2016
        schema = {
            "section_order": pl.Int64,
            "section_title": pl.Utf8,
            "section_content": pl.Utf8,
        }
        yield (
            "2024Q1",
            "q1",
            "section_content",
            pl.DataFrame(
                [
                    {"section_order": 1, "section_title": "II. 사업의 개요", "section_content": "장 소개"},
                    {
                        "section_order": 2,
                        "section_title": "1. 사업의 개요",
                        "section_content": (
                            "1. 사업의 개요\n가. 공통 항목\n공통 내용입니다.\n나. 분기 항목\n분기 전용 내용입니다."
                        ),
                    },
                ],
                schema=schema,
            ),
        )
        yield (
            "2024",
            "annual",
            "section_content",
            pl.DataFrame(
                [
                    {"section_order": 1, "section_title": "II. 사업의 개요", "section_content": "장 소개"},
                    {
                        "section_order": 2,
                        "section_title": "1. 사업의 개요",
                        "section_content": (
                            "1. 사업의 개요\n가. 공통 항목\n공통 내용입니다.\n다. 연간 항목\n연간 전용 내용입니다."
                        ),
                    },
                ],
                schema=schema,
            ),
        )

    monkeypatch.setattr(pipeline, "mapSectionTitle", fake_map_section_title)
    monkeypatch.setattr(textStructure, "mapSectionTitle", fake_map_section_title)
    monkeypatch.setattr(pipeline, "iterPeriodSubsets", fake_iter_period_subsets)

    df = pipeline.sections("TEST")

    assert df is not None
    assert {
        "cadenceKey",
        "cadenceScope",
        "annualPeriodCount",
        "quarterlyPeriodCount",
        "latestAnnualPeriod",
        "latestQuarterlyPeriod",
    }.issubset(set(df.columns))

    common_body = df.filter(
        (pl.col("topic") == "businessOverview")
        & (pl.col("textNodeType") == "body")
        & (pl.col("textPathKey") == "@topic:businessOverview > 공통항목")
    )
    assert common_body.height == 1
    assert common_body.item(0, "cadenceScope") == "mixed"
    assert common_body.item(0, "cadenceKey") == "annual,q1"
    assert common_body.item(0, "annualPeriodCount") == 1
    assert common_body.item(0, "quarterlyPeriodCount") == 1
    assert common_body.item(0, "latestAnnualPeriod") == "2024"
    assert common_body.item(0, "latestQuarterlyPeriod") == "2024Q1"

    annual_body = df.filter(
        (pl.col("topic") == "businessOverview")
        & (pl.col("textNodeType") == "body")
        & (pl.col("textPathKey") == "@topic:businessOverview > 연간항목")
    )
    assert annual_body.height == 1
    assert annual_body.item(0, "cadenceScope") == "annual"
    assert annual_body.item(0, "latestAnnualPeriod") == "2024"
    assert annual_body.item(0, "latestQuarterlyPeriod") is None

    quarter_body = df.filter(
        (pl.col("topic") == "businessOverview")
        & (pl.col("textNodeType") == "body")
        & (pl.col("textPathKey") == "@topic:businessOverview > 분기항목")
    )
    assert quarter_body.height == 1
    assert quarter_body.item(0, "cadenceScope") == "quarterly"
    assert quarter_body.item(0, "cadenceKey") == "q1"
    assert quarter_body.item(0, "latestAnnualPeriod") is None
    assert quarter_body.item(0, "latestQuarterlyPeriod") == "2024Q1"

    annualView = pipeline.projectCadenceRows(df, cadenceScope="annual")
    assert annualView.filter(pl.col("textPathKey") == "@topic:businessOverview > 공통항목").height == 2
    assert annualView.filter(pl.col("textPathKey") == "@topic:businessOverview > 연간항목").height == 2
    assert annualView.filter(pl.col("textPathKey") == "@topic:businessOverview > 분기항목").height == 0

    quarterlyView = pipeline.projectCadenceRows(df, cadenceScope="quarterly")
    assert quarterlyView.filter(pl.col("textPathKey") == "@topic:businessOverview > 공통항목").height == 2
    assert quarterlyView.filter(pl.col("textPathKey") == "@topic:businessOverview > 연간항목").height == 0
    assert quarterlyView.filter(pl.col("textPathKey") == "@topic:businessOverview > 분기항목").height == 2


def test_company_sections_preserve_structured_text_columns():
    c = Company(SAMSUNG)
    sec = c.sections

    assert sec is not None
    assert {
        "source",
        "sourceBlockOrder",
        "textNodeType",
        "textStructural",
        "textLevel",
        "textPath",
        "textPathKey",
        "textPathVariantCount",
        "textPathVariants",
        "textParentPathVariants",
        "textSemanticPathKey",
        "textSemanticParentPathKey",
        "textSemanticPathVariants",
        "textSemanticParentPathVariants",
        "segmentKey",
        "segmentOccurrence",
        "cadenceKey",
        "cadenceScope",
        "annualPeriodCount",
        "quarterlyPeriodCount",
        "latestAnnualPeriod",
        "latestQuarterlyPeriod",
    }.issubset(set(sec.columns))

    overview = sec.filter((pl.col("topic") == "companyOverview") & (pl.col("source") == "docs"))
    assert overview.filter(pl.col("textNodeType") == "heading").height > 0
    assert overview.filter(pl.col("textNodeType") == "body").height > 0
