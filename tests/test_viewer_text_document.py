import pytest

pytestmark = pytest.mark.unit

import polars as pl

from dartlab.providers.dart.docs.viewer import (
    BlockMeta,
    ChangeSummary,
    ViewerBlock,
    viewerTextDocument,
)


def _text_block(
    block: int,
    text_type: str,
    texts: dict[str, str],
    *,
    summary: ChangeSummary | None = None,
) -> ViewerBlock:
    ordered = sorted(
        texts.keys(),
        key=lambda period: (int(period[:4]), int(period[5]) if "Q" in period else 5),
    )
    row = {period: texts[period] for period in ordered}
    return ViewerBlock(
        block=block,
        kind="text",
        source="docs",
        data=pl.DataFrame([row]),
        meta=BlockMeta(periods=ordered, rowCount=1, colCount=len(ordered)),
        changeSummary=summary,
        textType=text_type,
    )


def test_viewer_text_document_groups_heading_and_builds_timeline_views():
    blocks = [
        _text_block(0, "heading", {"2024": "가. 사업 개요", "2025": "가. 회사의 개요"}),
        _text_block(1, "body", {"2024": "2024 본문", "2025": "2025 본문"}),
    ]

    document = viewerTextDocument("businessOverview", blocks)

    assert document is not None
    assert document.latestPeriod is not None
    assert document.latestPeriod.label == "2025"
    assert document.sectionCount == 1

    section = document.sections[0]
    assert section.bodyBlock == 1
    assert section.headingPath[0].text == "가. 회사의 개요"
    assert section.latest is not None
    assert section.latest.period.label == "2025"
    assert section.latest.body == "2025 본문"
    assert section.latest.prevPeriod is not None
    assert section.latest.prevPeriod.label == "2024"
    assert section.timeline[0].period.label == "2025"
    assert section.timeline[0].prevPeriod is not None
    assert section.timeline[0].prevPeriod.label == "2024"
    assert section.views["2025"].status == "updated"
    assert [chunk.kind for chunk in section.views["2025"].diff] == ["removed", "added"]
    assert section.status == "updated"


def test_viewer_text_document_marks_stale_latest_sections():
    blocks = [
        _text_block(0, "body", {"2024": "최신 본문"}),
        _text_block(1, "body", {"2021": "과거 본문"}),
    ]

    document = viewerTextDocument("companyOverview", blocks)

    assert document is not None
    assert document.latestPeriod is not None
    assert document.latestPeriod.label == "2024"
    assert document.staleCount == 1
    assert [section.status for section in document.sections] == ["new", "stale"]
    assert document.sections[1].latest is not None
    assert document.sections[1].latest.period.label == "2021"


def test_viewer_text_document_uses_same_cadence_for_previous_period():
    blocks = [
        _text_block(
            0,
            "body",
            {
                "2023": "연간 2023",
                "2024Q1": "분기 2024Q1",
                "2025Q1": "분기 2025Q1",
                "2025": "연간 2025",
            },
        ),
    ]

    document = viewerTextDocument("mdna", blocks)

    assert document is not None
    section = document.sections[0]
    assert section.views["2025"].prevPeriod is not None
    assert section.views["2025"].prevPeriod.label == "2023"
    assert section.views["2025Q1"].prevPeriod is not None
    assert section.views["2025Q1"].prevPeriod.label == "2024Q1"


def test_viewer_text_document_preserves_diff_order_in_place():
    blocks = [
        _text_block(
            0,
            "body",
            {
                "2024": "문단 A\n\n문단 B\n\n문단 C",
                "2025": "문단 A\n\n문단 C\n\n문단 D",
            },
        ),
    ]

    document = viewerTextDocument("audit", blocks)

    assert document is not None
    diff = document.sections[0].views["2025"].diff
    assert [(chunk.kind, chunk.paragraphs) for chunk in diff] == [
        ("same", ["문단 A"]),
        ("removed", ["문단 B"]),
        ("same", ["문단 C"]),
        ("added", ["문단 D"]),
    ]
