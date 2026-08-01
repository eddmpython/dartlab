"""story catalog + formats 단위 테스트.

catalog.py — SECTIONS, _BLOCKS, _meta, resolveKey, keysForSection.
formats.py — renderMarkdown, renderHtml, renderJson.
데이터 로드 없음, mock 전용.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

pytestmark = pytest.mark.unit


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# catalog.py tests
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def test_sections_list_not_empty():
    from dartlab.story.catalog import SECTIONS

    assert len(SECTIONS) > 10


def test_sections_have_required_fields():
    from dartlab.story.catalog import SECTIONS

    for s in SECTIONS:
        assert s.key, f"Section missing key: {s}"
        assert s.partId, f"Section missing partId: {s}"
        assert s.title, f"Section missing title: {s}"


def test_sections_keys_are_unique():
    from dartlab.story.catalog import SECTIONS

    keys = [s.key for s in SECTIONS]
    assert len(keys) == len(set(keys)), f"Duplicate section keys: {[k for k in keys if keys.count(k) > 1]}"


def test_sections_includes_expected():
    from dartlab.story.catalog import SECTIONS

    keys = {s.key for s in SECTIONS}
    expected = {"수익구조", "수익성", "현금흐름", "안정성", "종합평가", "가치평가", "신용평가"}
    assert expected.issubset(keys)


def test_blocks_list_not_empty():
    from dartlab.story.catalog import _BLOCKS

    assert len(_BLOCKS) > 50


def test_blocks_have_required_fields():
    from dartlab.story.catalog import _BLOCKS

    for b in _BLOCKS:
        assert b.key, f"Block missing key: {b}"
        assert b.label, f"Block missing label: {b}"
        assert b.section, f"Block missing section: {b}"
        assert b.description, f"Block missing description: {b}"


def test_blocks_keys_are_unique():
    from dartlab.story.catalog import _BLOCKS

    keys = [b.key for b in _BLOCKS]
    assert len(keys) == len(set(keys)), f"Duplicate block keys: {[k for k in keys if keys.count(k) > 1]}"


def test_blocks_labels_are_unique():
    from dartlab.story.catalog import _BLOCKS

    labels = [b.label for b in _BLOCKS]
    assert len(labels) == len(set(labels)), "Duplicate block labels"


def test_block_section_references_valid_section():
    """모든 블록의 section이 SECTIONS에 존재해야 한다."""
    from dartlab.story.catalog import _BLOCKS, SECTIONS

    section_keys = {s.key for s in SECTIONS}
    for b in _BLOCKS:
        assert b.section in section_keys, f"Block '{b.key}' references unknown section '{b.section}'"


# ── getBlockMeta / resolveKey ──


def test_get_block_meta_valid_key():
    from dartlab.story.catalog import getBlockMeta

    meta = getBlockMeta("profile")
    assert meta is not None
    assert meta.key == "profile"
    assert meta.label == "기업 개요"


def test_get_block_meta_invalid_key():
    from dartlab.story.catalog import getBlockMeta

    assert getBlockMeta("nonexistent_key_xyz") is None


def test_resolve_key_by_key():
    from dartlab.story.catalog import resolveKey

    assert resolveKey("growth") == "growth"
    assert resolveKey("profile") == "profile"


def test_resolve_key_by_label():
    from dartlab.story.catalog import resolveKey

    assert resolveKey("기업 개요") == "profile"
    assert resolveKey("매출 성장률") == "growth"


def test_resolve_key_unknown():
    from dartlab.story.catalog import resolveKey

    assert resolveKey("존재하지않는라벨") is None


# ── listBlocks / keysForSection / listSections ──


def test_list_blocks_all():
    from dartlab.story.catalog import _BLOCKS, listBlocks

    all_blocks = listBlocks()
    assert len(all_blocks) == len(_BLOCKS)


def test_list_blocks_by_section():
    from dartlab.story.catalog import listBlocks

    revenue_blocks = listBlocks("수익구조")
    assert len(revenue_blocks) > 0
    assert all(b.section == "수익구조" for b in revenue_blocks)


def test_list_blocks_unknown_section():
    from dartlab.story.catalog import listBlocks

    assert listBlocks("없는섹션") == []


def test_keys_for_section():
    from dartlab.story.catalog import keysForSection

    keys = keysForSection("수익구조")
    assert "profile" in keys
    assert "growth" in keys


def test_keys_for_section_unknown():
    from dartlab.story.catalog import keysForSection

    assert keysForSection("없는섹션") == []


def test_list_sections():
    from dartlab.story.catalog import SECTIONS, listSections

    result = listSections()
    assert len(result) == len(SECTIONS)
    assert result[0].key == SECTIONS[0].key


def test_get_section_meta():
    from dartlab.story.catalog import getSectionMeta

    meta = getSectionMeta("수익구조")
    assert meta is not None
    assert meta.partId == "1"

    assert getSectionMeta("없는키") is None


# ── _suggest ──


def test_suggest_returns_suggestion_for_typo():
    from dartlab.story.catalog import _suggest

    result = _suggest("growtx")
    assert "growth" in result


def test_suggest_empty_for_unrelated():
    from dartlab.story.catalog import _suggest

    result = _suggest("zzzzzzzzzzzzzzz")
    assert result == ""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# formats.py tests — renderMarkdown, renderHtml, renderJson
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@dataclass
class _FakeLayout:
    detail: bool = True


@dataclass
class _FakeSummaryCard:
    conclusion: str = ""
    strengths: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    grades: dict = field(default_factory=dict)


@dataclass
class _FakeReview:
    corpName: str = "테스트기업"
    stockCode: str = "000000"
    sections: list = field(default_factory=list)
    summaryCard: object = None
    circulationSummary: str = ""
    layout: object = field(default_factory=_FakeLayout)
    actTransitions: dict = field(default_factory=dict)


@dataclass
class _FakeSection:
    key: str = "수익구조"
    title: str = "수익 구조"
    blocks: list = field(default_factory=list)
    threads: list = field(default_factory=list)
    summary: str = ""


# ── renderMarkdown ──


def test_render_markdown_empty_review():
    from dartlab.story.formats import renderMarkdown

    story = _FakeReview()
    md = renderMarkdown(story)
    assert "테스트기업" in md
    assert "000000" in md


def test_render_markdown_heading_block():
    from dartlab.story.blocks import HeadingBlock
    from dartlab.story.formats import renderMarkdown

    section = _FakeSection(blocks=[HeadingBlock(title="테스트 제목", level=1)])
    story = _FakeReview(sections=[section])
    md = renderMarkdown(story)
    assert "### 테스트 제목" in md


def test_render_markdown_heading_level2():
    from dartlab.story.blocks import HeadingBlock
    from dartlab.story.formats import renderMarkdown

    section = _FakeSection(blocks=[HeadingBlock(title="하위 제목", level=2)])
    story = _FakeReview(sections=[section])
    md = renderMarkdown(story)
    assert "#### 하위 제목" in md


def test_render_markdown_text_block():
    from dartlab.story.blocks import TextBlock
    from dartlab.story.formats import renderMarkdown

    section = _FakeSection(blocks=[TextBlock(text="분석 내용입니다.")])
    story = _FakeReview(sections=[section])
    md = renderMarkdown(story)
    assert "분석 내용입니다." in md


def test_render_markdown_flag_block_warning():
    from dartlab.story.blocks import FlagBlock
    from dartlab.story.formats import renderMarkdown

    section = _FakeSection(blocks=[FlagBlock(flags=["부채비율 200% 초과"], kind="warning")])
    story = _FakeReview(sections=[section])
    md = renderMarkdown(story)
    assert "⚠" in md
    assert "부채비율 200% 초과" in md


def test_render_markdown_flag_block_opportunity():
    from dartlab.story.blocks import FlagBlock
    from dartlab.story.formats import renderMarkdown

    section = _FakeSection(blocks=[FlagBlock(flags=["배당 성장 지속"], kind="opportunity")])
    story = _FakeReview(sections=[section])
    md = renderMarkdown(story)
    assert "✦" in md
    assert "배당 성장 지속" in md


def test_render_markdown_metric_block():
    from dartlab.story.blocks import MetricBlock
    from dartlab.story.formats import renderMarkdown

    section = _FakeSection(blocks=[MetricBlock(metrics=[("ROE", "12.5%"), ("부채비율", "85%")])])
    story = _FakeReview(sections=[section])
    md = renderMarkdown(story)
    assert "**ROE**: 12.5%" in md
    assert "**부채비율**: 85%" in md


def test_render_markdown_summary_card():
    from dartlab.story.formats import renderMarkdown

    card = _FakeSummaryCard(
        conclusion="양호",
        strengths=["현금흐름 우수"],
        warnings=["부채 증가"],
    )
    story = _FakeReview(summaryCard=card)
    md = renderMarkdown(story)
    assert "**양호**" in md
    assert "[+] 현금흐름 우수" in md
    assert "[-] 부채 증가" in md


def test_render_markdown_circulation_summary():
    from dartlab.story.formats import renderMarkdown

    story = _FakeReview(circulationSummary="매출 증가 → 영업이익 개선")
    md = renderMarkdown(story)
    assert "재무 순환 서사" in md
    assert "매출 증가" in md


def test_render_markdown_chart_block():
    from dartlab.story.blocks import ChartBlock
    from dartlab.story.formats import renderMarkdown

    section = _FakeSection(blocks=[ChartBlock(spec={"title": "매출 추이"})])
    story = _FakeReview(sections=[section])
    md = renderMarkdown(story)
    assert "[chart: 매출 추이]" in md


def test_render_markdown_detail_false():
    """detail=False 모드에서는 블록 대신 summary만 표시."""
    from dartlab.story.formats import renderMarkdown

    section = _FakeSection(title="수익 구조", summary="매출 구성이 다양함")
    story = _FakeReview(sections=[section], layout=_FakeLayout(detail=False))
    md = renderMarkdown(story)
    assert "수익 구조" in md
    assert "매출 구성이 다양함" in md


# ── renderHtml ──


def test_render_html_basic():
    from dartlab.story.formats import renderHtml

    story = _FakeReview()
    html = renderHtml(story)
    assert "<h2" in html
    assert "테스트기업" in html


def test_render_html_heading_block():
    from dartlab.story.blocks import HeadingBlock
    from dartlab.story.formats import renderHtml

    section = _FakeSection(blocks=[HeadingBlock(title="수익성", level=1)])
    story = _FakeReview(sections=[section])
    html = renderHtml(story)
    assert "<h3>수익성</h3>" in html


def test_render_html_heading_level2():
    from dartlab.story.blocks import HeadingBlock
    from dartlab.story.formats import renderHtml

    section = _FakeSection(blocks=[HeadingBlock(title="세부", level=2)])
    story = _FakeReview(sections=[section])
    html = renderHtml(story)
    assert "<h4>세부</h4>" in html


def test_render_html_text_block():
    from dartlab.story.blocks import TextBlock
    from dartlab.story.formats import renderHtml

    section = _FakeSection(blocks=[TextBlock(text="본문 텍스트")])
    story = _FakeReview(sections=[section])
    html = renderHtml(story)
    assert "<p>본문 텍스트</p>" in html


def test_render_html_flag_block():
    from dartlab.story.blocks import FlagBlock
    from dartlab.story.formats import renderHtml

    section = _FakeSection(blocks=[FlagBlock(flags=["위험 경고"], kind="warning")])
    story = _FakeReview(sections=[section])
    html = renderHtml(story)
    assert "⚠" in html
    assert "위험 경고" in html


def test_render_html_metric_block():
    from dartlab.story.blocks import MetricBlock
    from dartlab.story.formats import renderHtml

    section = _FakeSection(blocks=[MetricBlock(metrics=[("PER", "15.2")])])
    story = _FakeReview(sections=[section])
    html = renderHtml(story)
    assert "<table>" in html
    assert "PER" in html
    assert "15.2" in html


def test_render_html_summary_card():
    from dartlab.story.formats import renderHtml

    card = _FakeSummaryCard(
        conclusion="결론 텍스트",
        strengths=["강점1"],
        warnings=["약점1"],
        grades={"수익성": "A", "안정성": "B"},
    )
    story = _FakeReview(summaryCard=card)
    html = renderHtml(story)
    assert "결론 텍스트" in html
    assert "강점1" in html
    assert "약점1" in html
    assert "수익성 A" in html


def test_render_html_detail_false():
    from dartlab.story.formats import renderHtml

    section = _FakeSection(title="수익 구조", summary="요약")
    story = _FakeReview(sections=[section], layout=_FakeLayout(detail=False))
    html = renderHtml(story)
    assert "<h3>수익 구조</h3>" in html
    assert "요약" in html


def test_render_html_escapes_all_story_strings_and_chart_attribute():
    import html as html_lib
    import json
    import re
    from types import SimpleNamespace

    from dartlab.story import Story
    from dartlab.story.blocks import ChartBlock, FlagBlock, HeadingBlock, MetricBlock, TableBlock, TextBlock
    from dartlab.story.formats import renderHtml
    from dartlab.story.narrative import NarrativeThread
    from dartlab.story.section import Section
    from dartlab.story.summary import SummaryCard

    payload = "'><img src=x onerror=alert(1)>"

    class UnsafeFrame:
        columns = [payload]

        @staticmethod
        def iter_rows():
            return iter([[payload]])

        @staticmethod
        def _repr_html_():
            return payload

    section = Section(
        key="unsafe",
        partId="1",
        title=payload,
        blocks=[
            HeadingBlock(payload),
            TextBlock(payload),
            MetricBlock([(payload, payload)]),
            TableBlock(payload, UnsafeFrame()),
            ChartBlock({"title": payload, "payload": payload}),
            FlagBlock([payload]),
        ],
        threads=[NarrativeThread(threadId="x", title=payload, story=payload)],
    )
    story = Story(
        stockCode=payload,
        corpName=payload,
        sections=[section],
        summaryCard=SummaryCard(
            conclusion=payload,
            strengths=[payload],
            warnings=[payload],
            grades={payload: payload},
        ),
    )
    story.circulationSummary = payload
    story.lensGaps = [{"engine": "analysis", "status": "blocked", "reason": payload, "sourceRef": payload}]

    rendered = renderHtml(story)

    assert payload not in rendered
    assert "&lt;img src=x onerror=alert(1)&gt;" in rendered
    attribute = re.search(r"data-spec='([^']+)'", rendered)
    assert attribute is not None
    decoded = json.loads(html_lib.unescape(attribute.group(1)))
    assert decoded["title"] == payload
    assert story._repr_html_() == rendered

    compact = SimpleNamespace(
        corpName=payload,
        stockCode=payload,
        summaryCard=None,
        circulationSummary="",
        lensGaps=[],
        sections=[SimpleNamespace(title=payload, summary=payload)],
        layout=_FakeLayout(detail=False),
    )
    compactHtml = renderHtml(compact)
    assert payload not in compactHtml


# ── renderJson ──


def test_render_json_basic():
    import json

    from dartlab.story.formats import renderJson

    story = _FakeReview()
    result = json.loads(renderJson(story))
    assert result["stockCode"] == "000000"
    assert result["corpName"] == "테스트기업"
    assert isinstance(result["sections"], list)


def test_render_json_with_blocks():
    import json

    from dartlab.story.blocks import HeadingBlock, MetricBlock, TextBlock
    from dartlab.story.formats import renderJson

    section = _FakeSection(
        blocks=[
            HeadingBlock(title="제목", level=1),
            TextBlock(text="내용"),
            MetricBlock(metrics=[("ROE", "10%")]),
        ]
    )
    story = _FakeReview(sections=[section])
    result = json.loads(renderJson(story))
    blocks = result["sections"][0]["blocks"]
    assert blocks[0]["type"] == "heading"
    assert blocks[0]["title"] == "제목"
    assert blocks[1]["type"] == "text"
    assert blocks[2]["type"] == "metrics"


def test_render_json_with_flag_block():
    import json

    from dartlab.story.blocks import FlagBlock
    from dartlab.story.formats import renderJson

    section = _FakeSection(blocks=[FlagBlock(flags=["경고1", "경고2"], kind="warning")])
    story = _FakeReview(sections=[section])
    result = json.loads(renderJson(story))
    flag_item = result["sections"][0]["blocks"][0]
    assert flag_item["type"] == "flags"
    assert flag_item["kind"] == "warning"
    assert "경고1" in flag_item["flags"]


def test_render_json_with_summary_card():
    import json

    from dartlab.story.formats import renderJson

    card = _FakeSummaryCard(conclusion="좋음", strengths=["s1"], warnings=["w1"], grades={"A": "1"})
    story = _FakeReview(summaryCard=card)
    result = json.loads(renderJson(story))
    assert result["summaryCard"]["conclusion"] == "좋음"
    assert "s1" in result["summaryCard"]["strengths"]


def test_render_json_detail_false():
    import json

    from dartlab.story.formats import renderJson

    section = _FakeSection(key="수익구조", title="수익 구조", summary="요약 텍스트")
    story = _FakeReview(sections=[section], layout=_FakeLayout(detail=False))
    result = json.loads(renderJson(story))
    sec = result["sections"][0]
    assert sec["key"] == "수익구조"
    assert sec["summary"] == "요약 텍스트"
    assert "blocks" not in sec


def test_render_json_with_chart_block():
    import json

    from dartlab.story.blocks import ChartBlock
    from dartlab.story.formats import renderJson

    section = _FakeSection(blocks=[ChartBlock(spec={"title": "차트"}, caption="설명")])
    story = _FakeReview(sections=[section])
    result = json.loads(renderJson(story))
    chart = result["sections"][0]["blocks"][0]
    assert chart["type"] == "chart"
    assert chart["spec"]["title"] == "차트"
    assert chart["caption"] == "설명"


def test_render_json_rejects_opaque_object_repr_fallback():
    from dartlab.story.blocks import ChartBlock
    from dartlab.story.formats import renderJson

    section = _FakeSection(blocks=[ChartBlock(spec={"opaque": object()})])
    story = _FakeReview(sections=[section])

    with pytest.raises(TypeError, match="cannot encode"):
        renderJson(story)
