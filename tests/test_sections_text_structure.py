from __future__ import annotations

import polars as pl
import pytest

from dartlab import Company

pytestmark = pytest.mark.integration
from dartlab.engines.company.dart.docs.sections import (
    displayPeriod,
    pipeline,
    rawPeriod,
    reorderPeriodColumns,
    textStructure,
)
from dartlab.engines.company.dart.docs.sections.textStructure import parseTextStructure, parseTextStructureWithState

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
    assert [row["textLevel"] for row in rows] == [3, 4, 4, 4, 4]
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
        "1. 사업의 개요\n2. 사업의 내용\n가. 사업부문별 현황\n당사는 DX와 DS 부문을 운영합니다.",
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


def test_parse_text_structure_normalizes_safe_audit_system_aliases(monkeypatch):
    def fake_map_section_title(title: str) -> str:
        normalized = title.replace(" ", "")
        if normalized in {"감사및감사위원회", "감사위원회", "감사위원회에관한사항"}:
            return "auditSystem"
        return normalized

    monkeypatch.setattr(textStructure, "mapSectionTitle", fake_map_section_title)

    first = parseTextStructure(
        "1. 감사 및 감사위원회\n가. 감사위원회\n(1) 감사위원 현황\n감사위원 현황입니다.",
        sourceBlockOrder=0,
        topic="auditSystem",
    )
    second = parseTextStructure(
        "1. 감사 및 감사위원회\n가. 감사위원회에 관한 사항\n(1) 감사위원 현황\n감사위원 현황입니다.",
        sourceBlockOrder=0,
        topic="auditSystem",
    )

    firstBody = next(row for row in first if row["textNodeType"] == "body")
    secondBody = next(row for row in second if row["textNodeType"] == "body")

    assert second[1]["text"] == "가. 감사위원회에 관한 사항"
    assert firstBody["textPathKey"] != secondBody["textPathKey"]
    assert firstBody["textSemanticPathKey"] == "@topic:auditSystem > 감사위원회 > 감사위원현황"
    assert secondBody["textSemanticPathKey"] == "@topic:auditSystem > 감사위원회 > 감사위원현황"


def test_period_helpers_support_q4_display_and_recent_first_ordering():
    df = pl.DataFrame(
        {
            "topic": ["companyOverview"],
            "2024Q1": ["q1"],
            "2025": ["annual"],
            "2024": ["prevAnnual"],
            "2025Q3": ["q3"],
        }
    )

    ordered = reorderPeriodColumns(df, descending=True, annualAsQ4=True)
    periodCols = [col for col in ordered.columns if col.startswith("20")]

    assert rawPeriod("2025Q4") == "2025"
    assert displayPeriod("2025", annualAsQ4=True) == "2025Q4"
    assert periodCols == ["2025Q4", "2025Q3", "2024Q4", "2024Q1"]


def test_sections_horizontalize_numbering_changes_into_same_row(monkeypatch):
    def fake_map_section_title(_title: str) -> str:
        return "companyOverview"

    def fake_iter_period_subsets(_stockCode: str, *, sinceYear: int = 2016):
        assert sinceYear == 2016
        schema = {
            "section_order": pl.Int64,
            "section_title": pl.Categorical,
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


def test_sections_preserve_pending_chapter_content_when_subitems_exist(monkeypatch):
    def fake_map_section_title(title: str) -> str:
        normalized = title.replace(" ", "")
        if normalized.endswith("사업의내용") or normalized.endswith("사업의개요"):
            return "businessOverview"
        return normalized

    def fake_iter_period_subsets(_stockCode: str, *, sinceYear: int = 2016):
        assert sinceYear == 2016
        schema = {
            "section_order": pl.Int64,
            "section_title": pl.Categorical,
            "section_content": pl.Utf8,
        }
        yield (
            "2025",
            "annual",
            "section_content",
            pl.DataFrame(
                [
                    {
                        "section_order": 1,
                        "section_title": "II. 사업의 내용",
                        "section_content": (
                            "1. 사업의 개요\n"
                            "가. 총괄\n"
                            "총괄 설명입니다.\n"
                            "나. 추가 설명\n"
                            "장 제목에만 남아 있는 설명입니다."
                        ),
                    },
                    {
                        "section_order": 2,
                        "section_title": "1. 사업의 개요",
                        "section_content": ("가. 총괄\n총괄 설명입니다."),
                    },
                ],
                schema=schema,
            ),
        )

    monkeypatch.setattr(pipeline, "mapSectionTitle", fake_map_section_title)
    monkeypatch.setattr(pipeline, "iterPeriodSubsets", fake_iter_period_subsets)

    df = pipeline.sections("TEST")

    assert df is not None
    bodyRows = df.filter((pl.col("topic") == "businessOverview") & (pl.col("textNodeType") == "body"))

    payloads = [value for value in bodyRows.get_column("2025").to_list() if isinstance(value, str)]

    assert bodyRows.height >= 2
    assert len(payloads) >= 2
    assert any("장 제목에만 남아 있는 설명" in value for value in payloads)


def test_sections_horizontalize_same_path_when_source_block_order_shifts(monkeypatch):
    def fake_map_section_title(_title: str) -> str:
        return "companyOverview"

    def fake_iter_period_subsets(_stockCode: str, *, sinceYear: int = 2016):
        assert sinceYear == 2016
        schema = {
            "section_order": pl.Int64,
            "section_title": pl.Categorical,
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
            "section_title": pl.Categorical,
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
            "section_title": pl.Categorical,
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
            "section_title": pl.Categorical,
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
            "section_title": pl.Categorical,
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
    assert first["textComparablePathKey"] == second["textComparablePathKey"]
    assert first["2024"] is None or first["2025"] is None
    assert second["2024"] is None or second["2025"] is None

    collisions = pipeline.structureCollisions(df, topic="businessOverview")
    assert collisions.height >= 1
    target = collisions.filter(pl.col("textComparablePathKey") == first["textComparablePathKey"])
    assert target.height >= 1
    targetRow = target.row(0, named=True)
    assert "reassigned" in set(target["structurePattern"].to_list())
    assert targetRow["activePeriodCount"] == 2
    assert targetRow["activePathCounts"] == [1, 1]
    assert targetRow["multiPathPeriods"] == []


def test_structure_registry_distinguishes_variant_split_merge_and_parallel():
    df = pl.DataFrame(
        {
            "topic": ["businessOverview"] * 8,
            "blockType": ["text"] * 8,
            "textStructural": [True] * 8,
            "textNodeType": ["body"] * 8,
            "textLevel": [1] * 8,
            "cadenceScope": ["annual"] * 8,
            "textComparablePathKey": [
                "매출",
                "매출",
                "매출 > 판매경로및판매방법",
                "매출 > 판매경로및판매방법",
                "생산및설비 > 생산능력생산실적가동률",
                "생산및설비 > 생산능력생산실적가동률",
                "시장위험과위험관리",
                "시장위험과위험관리",
            ],
            "textComparableParentPathKey": [
                None,
                None,
                "매출",
                "매출",
                "생산및설비",
                "생산및설비",
                None,
                None,
            ],
            "textSemanticPathKey": [
                "매출",
                "매출및수주상황",
                "매출 > 판매경로",
                "매출 > 판매전략",
                "생산및설비 > 생산실적",
                "생산및설비 > 가동률",
                "시장위험과위험관리",
                "위험관리및파생거래",
            ],
            "textSemanticParentPathKey": [
                None,
                None,
                "매출",
                "매출",
                "생산및설비",
                "생산및설비",
                None,
                None,
            ],
            "segmentKey": [f"s{i}" for i in range(8)],
            "sourceBlockOrder": list(range(8)),
            "latestAnnualPeriod": ["2025"] * 8,
            "latestQuarterlyPeriod": [None] * 8,
            "2024": ["a", None, "a", None, "a", "b", "a", "b"],
            "2025": [None, "a", "a", "b", "a", None, "a", "b"],
        }
    )

    registry = pipeline.structureRegistry(df, topic="businessOverview")

    variant = registry.filter(pl.col("textComparablePathKey") == "매출")
    assert variant.height == 1
    variantRow = variant.row(0, named=True)
    assert variantRow["structurePattern"] == "variant"
    assert variantRow["activePathCounts"] == [1, 1]

    split = registry.filter(pl.col("textComparablePathKey") == "매출 > 판매경로및판매방법")
    assert split.height == 1
    splitRow = split.row(0, named=True)
    assert splitRow["structurePattern"] == "split"
    assert splitRow["activePathCounts"] == [1, 2]
    assert splitRow["multiPathPeriods"] == ["2025"]

    merge = registry.filter(pl.col("textComparablePathKey") == "생산및설비 > 생산능력생산실적가동률")
    assert merge.height == 1
    mergeRow = merge.row(0, named=True)
    assert mergeRow["structurePattern"] == "merge"
    assert mergeRow["activePathCounts"] == [2, 1]
    assert mergeRow["multiPathPeriods"] == ["2024"]

    parallel = registry.filter(pl.col("textComparablePathKey") == "시장위험과위험관리")
    assert parallel.height == 1
    parallelRow = parallel.row(0, named=True)
    assert parallelRow["structurePattern"] == "parallel"
    assert parallelRow["activePathCounts"] == [2, 2]
    assert parallelRow["multiPathPeriods"] == ["2024", "2025"]

    bodyOnly = pipeline.structureRegistry(df, topic="businessOverview", nodeType="body")
    assert bodyOnly.height == registry.height
    assert set(bodyOnly["textNodeType"].unique().to_list()) == {"body"}


def test_structure_registry_marks_same_leaf_multi_parent_concurrency_as_parallel():
    df = pl.DataFrame(
        {
            "topic": ["businessOverview", "businessOverview"],
            "blockType": ["text", "text"],
            "textStructural": [True, True],
            "textNodeType": ["body", "body"],
            "textLevel": [2, 2],
            "cadenceScope": ["annual", "annual"],
            "textComparablePathKey": ["사업부문현황 > 산업의특성", "사업부문현황 > 산업의특성"],
            "textComparableParentPathKey": ["사업부문현황", "사업부문현황"],
            "textSemanticPathKey": [
                "@topic:businessOverview > DX부문 > 산업의특성",
                "@topic:businessOverview > CE부문 > 산업의특성",
            ],
            "textSemanticParentPathKey": [
                "@topic:businessOverview > DX부문",
                "@topic:businessOverview > CE부문",
            ],
            "segmentKey": ["p0", "p1"],
            "sourceBlockOrder": [0, 1],
            "latestAnnualPeriod": ["2025", "2025"],
            "latestQuarterlyPeriod": [None, None],
            "2024": ["a", "b"],
            "2025": ["a", "b"],
        }
    )

    registry = pipeline.structureRegistry(df, topic="businessOverview", nodeType="body")
    assert registry.height == 1
    row = registry.row(0, named=True)
    assert row["structurePattern"] == "parallel"
    assert row["activePathCounts"] == [2, 2]
    assert row["latestPathCount"] == 2


def test_structure_events_capture_transition_types():
    df = pl.DataFrame(
        {
            "topic": ["businessOverview"] * 8,
            "blockType": ["text"] * 8,
            "textStructural": [True] * 8,
            "textNodeType": ["body"] * 8,
            "textLevel": [1] * 8,
            "cadenceScope": ["annual"] * 8,
            "textComparablePathKey": [
                "매출",
                "매출",
                "매출 > 판매경로및판매방법",
                "매출 > 판매경로및판매방법",
                "생산및설비 > 생산능력생산실적가동률",
                "생산및설비 > 생산능력생산실적가동률",
                "시장위험과위험관리",
                "시장위험과위험관리",
            ],
            "textComparableParentPathKey": [
                None,
                None,
                "매출",
                "매출",
                "생산및설비",
                "생산및설비",
                None,
                None,
            ],
            "textSemanticPathKey": [
                "매출",
                "매출및수주상황",
                "매출 > 판매경로",
                "매출 > 판매전략",
                "생산및설비 > 생산실적",
                "생산및설비 > 가동률",
                "시장위험과위험관리",
                "위험관리및파생거래",
            ],
            "textSemanticParentPathKey": [
                None,
                None,
                "매출",
                "매출",
                "생산및설비",
                "생산및설비",
                None,
                None,
            ],
            "segmentKey": [f"e{i}" for i in range(8)],
            "sourceBlockOrder": list(range(8)),
            "latestAnnualPeriod": ["2025"] * 8,
            "latestQuarterlyPeriod": [None] * 8,
            "2024": ["a", None, "a", None, "a", "b", "a", "b"],
            "2025": [None, "a", "a", "b", "a", None, "a", "b"],
        }
    )

    events = pipeline.structureEvents(df, topic="businessOverview")
    assert events.height == 3

    variant = events.filter(pl.col("textComparablePathKey") == "매출").row(0, named=True)
    assert variant["periodLane"] == "annual"
    assert variant["eventType"] == "variant"
    assert variant["fromPathCount"] == 1
    assert variant["toPathCount"] == 1
    assert variant["addedPaths"] == ["매출및수주상황"]
    assert variant["removedPaths"] == ["매출"]

    split = events.filter(pl.col("textComparablePathKey") == "매출 > 판매경로및판매방법").row(0, named=True)
    assert split["periodLane"] == "annual"
    assert split["eventType"] == "split"
    assert split["fromPathCount"] == 1
    assert split["toPathCount"] == 2
    assert split["addedPaths"] == ["매출 > 판매전략"]

    merge = events.filter(pl.col("textComparablePathKey") == "생산및설비 > 생산능력생산실적가동률").row(0, named=True)
    assert merge["periodLane"] == "annual"
    assert merge["eventType"] == "merge"
    assert merge["fromPathCount"] == 2
    assert merge["toPathCount"] == 1
    assert merge["removedPaths"] == ["생산및설비 > 가동률"]

    bodyOnly = pipeline.structureEvents(df, topic="businessOverview", nodeType="body")
    assert bodyOnly.height == events.height
    assert set(bodyOnly["textNodeType"].unique().to_list()) == {"body"}


def test_structure_events_capture_reassigned_transition(monkeypatch):
    def fake_map_section_title(_title: str) -> str:
        return "businessOverview"

    def fake_iter_period_subsets(_stockCode: str, *, sinceYear: int = 2016):
        assert sinceYear == 2016
        schema = {
            "section_order": pl.Int64,
            "section_title": pl.Categorical,
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

    events = pipeline.structureEvents(df, topic="businessOverview")
    target = events.filter(
        (pl.col("textComparablePathKey") == "@topic:businessOverview > 사업부문현황")
        & (pl.col("textNodeType") == "body")
    )
    assert target.height == 1
    row = target.row(0, named=True)
    assert row["periodLane"] == "annual"
    assert row["eventType"] == "reassigned"
    assert row["fromPeriod"] == "2024"
    assert row["toPeriod"] == "2025"
    assert row["addedPaths"] == ["@topic:businessOverview > 사업부문현황 > CE부문"]
    assert row["removedPaths"] == ["@topic:businessOverview > 사업부문현황 > DX부문"]

    bodyOnly = pipeline.structureEvents(df, topic="businessOverview", nodeType="body")
    assert bodyOnly.height == 1
    assert bodyOnly.item(0, "eventType") == "reassigned"


def test_structure_events_do_not_compare_cross_cadence_transitions():
    df = pl.DataFrame(
        {
            "topic": ["businessOverview", "businessOverview"],
            "blockType": ["text", "text"],
            "textStructural": [True, True],
            "textNodeType": ["body", "body"],
            "textLevel": [1, 1],
            "cadenceScope": ["mixed", "mixed"],
            "textComparablePathKey": ["매출", "매출"],
            "textComparableParentPathKey": [None, None],
            "textSemanticPathKey": ["매출", "매출및수주상황"],
            "textSemanticParentPathKey": [None, None],
            "segmentKey": ["cross1", "cross2"],
            "sourceBlockOrder": [0, 1],
            "latestAnnualPeriod": ["2024", "2024"],
            "latestQuarterlyPeriod": ["2024Q1", "2024Q1"],
            "2024Q1": ["a", None],
            "2024": [None, "a"],
        }
    )

    events = pipeline.structureEvents(df, topic="businessOverview")
    assert events.height == 0


def test_structure_helpers_respect_requested_cadence_lane_on_mixed_rows():
    df = pl.DataFrame(
        {
            "topic": ["businessOverview", "businessOverview"],
            "blockType": ["text", "text"],
            "textStructural": [True, True],
            "textNodeType": ["body", "body"],
            "textLevel": [1, 1],
            "cadenceScope": ["mixed", "mixed"],
            "textComparablePathKey": ["매출", "매출"],
            "textComparableParentPathKey": [None, None],
            "textSemanticPathKey": ["매출", "매출및수주상황"],
            "textSemanticParentPathKey": [None, None],
            "segmentKey": ["lane1", "lane2"],
            "sourceBlockOrder": [0, 1],
            "latestAnnualPeriod": ["2023", "2024"],
            "latestQuarterlyPeriod": ["2023Q1", "2024Q1"],
            "2023Q1": ["a", None],
            "2024Q1": [None, "a"],
            "2023": ["a", None],
            "2024": [None, "a"],
        }
    )

    quarterlySummary = pipeline.structureSummary(
        df, topic="businessOverview", cadenceScope="quarterly", nodeType="body"
    )
    assert quarterlySummary.height == 1
    quarterlyRow = quarterlySummary.row(0, named=True)
    assert quarterlyRow["latestPeriod"] == "2024Q1"
    assert quarterlyRow["latestPeriodLane"] == "q1"
    assert quarterlyRow["eventCount"] == 1
    assert quarterlyRow["latestEventType"] == "variant"
    assert quarterlyRow["latestEventLane"] == "q1"

    quarterlyEvents = pipeline.structureEvents(df, topic="businessOverview", cadenceScope="quarterly", nodeType="body")
    assert quarterlyEvents.height == 1
    assert quarterlyEvents.item(0, "periodLane") == "q1"
    assert quarterlyEvents.item(0, "fromPeriod") == "2023Q1"
    assert quarterlyEvents.item(0, "toPeriod") == "2024Q1"

    annualSummary = pipeline.structureSummary(df, topic="businessOverview", cadenceScope="annual", nodeType="body")
    assert annualSummary.height == 1
    annualRow = annualSummary.row(0, named=True)
    assert annualRow["latestPeriod"] == "2024"
    assert annualRow["latestPeriodLane"] == "annual"
    assert annualRow["latestEventLane"] == "annual"


def test_structure_summary_combines_registry_and_latest_event():
    df = pl.DataFrame(
        {
            "topic": ["businessOverview"] * 8,
            "blockType": ["text"] * 8,
            "textStructural": [True] * 8,
            "textNodeType": ["body"] * 8,
            "textLevel": [1] * 8,
            "cadenceScope": ["annual"] * 8,
            "textComparablePathKey": [
                "매출",
                "매출",
                "매출 > 판매경로및판매방법",
                "매출 > 판매경로및판매방법",
                "생산및설비 > 생산능력생산실적가동률",
                "생산및설비 > 생산능력생산실적가동률",
                "시장위험과위험관리",
                "시장위험과위험관리",
            ],
            "textComparableParentPathKey": [
                None,
                None,
                "매출",
                "매출",
                "생산및설비",
                "생산및설비",
                None,
                None,
            ],
            "textSemanticPathKey": [
                "매출",
                "매출및수주상황",
                "매출 > 판매경로",
                "매출 > 판매전략",
                "생산및설비 > 생산실적",
                "생산및설비 > 가동률",
                "시장위험과위험관리",
                "위험관리및파생거래",
            ],
            "textSemanticParentPathKey": [
                None,
                None,
                "매출",
                "매출",
                "생산및설비",
                "생산및설비",
                None,
                None,
            ],
            "segmentKey": [f"sum{i}" for i in range(8)],
            "sourceBlockOrder": list(range(8)),
            "latestAnnualPeriod": ["2025"] * 8,
            "latestQuarterlyPeriod": [None] * 8,
            "2024": ["a", None, "a", None, "a", "b", "a", "b"],
            "2025": [None, "a", "a", "b", "a", None, "a", "b"],
        }
    )

    summary = pipeline.structureSummary(df, topic="businessOverview", nodeType="body")
    assert summary.height == 4

    variant = summary.filter(pl.col("textComparablePathKey") == "매출").row(0, named=True)
    assert variant["structurePattern"] == "variant"
    assert variant["latestPeriod"] == "2025"
    assert variant["latestPeriodLane"] == "annual"
    assert variant["latestPathCount"] == 1
    assert variant["eventCount"] == 1
    assert variant["latestEventType"] == "variant"
    assert variant["latestEventToPeriod"] == "2025"

    split = summary.filter(pl.col("textComparablePathKey") == "매출 > 판매경로및판매방법").row(0, named=True)
    assert split["structurePattern"] == "split"
    assert split["eventCount"] == 1
    assert split["latestEventType"] == "split"

    merge = summary.filter(pl.col("textComparablePathKey") == "생산및설비 > 생산능력생산실적가동률").row(0, named=True)
    assert merge["structurePattern"] == "merge"
    assert merge["latestEventType"] == "merge"

    parallel = summary.filter(pl.col("textComparablePathKey") == "시장위험과위험관리").row(0, named=True)
    assert parallel["structurePattern"] == "parallel"
    assert parallel["latestEventType"] is None
    assert parallel["eventCount"] == 0


def test_structure_changes_focuses_latest_changed_rows():
    df = pl.DataFrame(
        {
            "topic": ["businessOverview"] * 10,
            "blockType": ["text"] * 10,
            "textStructural": [True] * 10,
            "textNodeType": ["body"] * 10,
            "textLevel": [1] * 10,
            "cadenceScope": ["annual"] * 10,
            "textComparablePathKey": [
                "매출",
                "매출",
                "매출 > 판매경로및판매방법",
                "매출 > 판매경로및판매방법",
                "생산및설비 > 생산능력생산실적가동률",
                "생산및설비 > 생산능력생산실적가동률",
                "시장위험과위험관리",
                "시장위험과위험관리",
                "안정항목",
                "안정항목",
            ],
            "textComparableParentPathKey": [
                None,
                None,
                "매출",
                "매출",
                "생산및설비",
                "생산및설비",
                None,
                None,
                None,
                None,
            ],
            "textSemanticPathKey": [
                "매출",
                "매출및수주상황",
                "매출 > 판매경로",
                "매출 > 판매전략",
                "생산및설비 > 생산실적",
                "생산및설비 > 가동률",
                "시장위험과위험관리",
                "위험관리및파생거래",
                "안정항목",
                "안정항목",
            ],
            "textSemanticParentPathKey": [
                None,
                None,
                "매출",
                "매출",
                "생산및설비",
                "생산및설비",
                None,
                None,
                None,
                None,
            ],
            "segmentKey": [f"chg{i}" for i in range(10)],
            "sourceBlockOrder": list(range(10)),
            "latestAnnualPeriod": ["2025"] * 10,
            "latestQuarterlyPeriod": [None] * 10,
            "2024": ["a", None, "a", None, "a", "b", "a", "b", "x", "x"],
            "2025": [None, "a", "a", "b", "a", None, "a", "b", "x", "x"],
        }
    )

    changes = pipeline.structureChanges(df, topic="businessOverview", nodeType="body")
    assert changes.height == 3
    assert changes["textComparablePathKey"].to_list() == [
        "매출 > 판매경로및판매방법",
        "생산및설비 > 생산능력생산실적가동률",
        "매출",
    ]
    assert changes["isLatest"].to_list() == [True, True, True]
    assert changes["anchorPeriod"].to_list() == ["2025", "2025", "2025"]
    assert changes["latestEventType"].to_list() == ["split", "merge", "variant"]

    allLatest = pipeline.structureChanges(df, topic="businessOverview", nodeType="body", changedOnly=False)
    assert allLatest.height == 5
    assert allLatest["textComparablePathKey"].to_list() == [
        "매출 > 판매경로및판매방법",
        "생산및설비 > 생산능력생산실적가동률",
        "매출",
        "시장위험과위험관리",
        "안정항목",
    ]


def test_sections_adds_cadence_scope_metadata(monkeypatch):
    def fake_map_section_title(_title: str) -> str:
        return "businessOverview"

    def fake_iter_period_subsets(_stockCode: str, *, sinceYear: int = 2016):
        assert sinceYear == 2016
        schema = {
            "section_order": pl.Int64,
            "section_title": pl.Categorical,
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


@pytest.mark.requires_data
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
        "textComparablePathKey",
        "textComparableParentPathKey",
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
