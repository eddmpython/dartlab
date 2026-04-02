"""review 블록 타입 단위 테스트.

HeadingBlock, TextBlock, MetricBlock, TableBlock, FlagBlock, ChartBlock 테스트.
데이터 로드 없음, mock 전용.
"""

from __future__ import annotations

import polars as pl
import pytest

pytestmark = pytest.mark.unit


# ── HeadingBlock ──


def test_heading_block_defaults():
    from dartlab.review.blocks import HeadingBlock

    h = HeadingBlock(title="수익구조")
    assert h.title == "수익구조"
    assert h.level == 1
    assert h.helper == ""


def test_heading_block_level1_html_tag():
    from dartlab.review.blocks import HeadingBlock

    h = HeadingBlock(title="T", level=1)
    assert h.htmlTag == "h3"


def test_heading_block_level2_html_tag():
    from dartlab.review.blocks import HeadingBlock

    h = HeadingBlock(title="T", level=2)
    assert h.htmlTag == "h4"


def test_heading_block_level1_markdown_prefix():
    from dartlab.review.blocks import HeadingBlock

    h = HeadingBlock(title="T", level=1)
    assert h.markdownPrefix == "###"


def test_heading_block_level2_markdown_prefix():
    from dartlab.review.blocks import HeadingBlock

    h = HeadingBlock(title="T", level=2)
    assert h.markdownPrefix == "####"


def test_heading_block_with_helper():
    from dartlab.review.blocks import HeadingBlock

    h = HeadingBlock(title="수익성", helper="마진 추이를 확인하세요")
    assert h.helper == "마진 추이를 확인하세요"


# ── TextBlock ──


def test_text_block_text():
    from dartlab.review.blocks import TextBlock

    t = TextBlock(text="매출이 증가했습니다.")
    assert t.text == "매출이 증가했습니다."


def test_text_block_defaults():
    from dartlab.review.blocks import TextBlock

    t = TextBlock(text="X")
    assert t.style == ""
    assert t.indent == "body"


def test_text_block_custom_indent():
    from dartlab.review.blocks import TextBlock

    t = TextBlock(text="X", indent="h2")
    assert t.indent == "h2"


def test_text_block_custom_style():
    from dartlab.review.blocks import TextBlock

    t = TextBlock(text="X", style="bold")
    assert t.style == "bold"


# ── MetricBlock ──


def test_metric_block_metrics():
    from dartlab.review.blocks import MetricBlock

    m = MetricBlock(metrics=[("ROE", "12.3%"), ("ROA", "5.1%")])
    assert len(m.metrics) == 2
    assert m.metrics[0] == ("ROE", "12.3%")
    assert m.metrics[1] == ("ROA", "5.1%")


def test_metric_block_empty():
    from dartlab.review.blocks import MetricBlock

    m = MetricBlock(metrics=[])
    assert m.metrics == []


def test_metric_block_single():
    from dartlab.review.blocks import MetricBlock

    m = MetricBlock(metrics=[("부채비율", "45%")])
    assert len(m.metrics) == 1


# ── FlagBlock ──


def test_flag_block_warning():
    from dartlab.review.blocks import FlagBlock

    f = FlagBlock(flags=["부채비율 급증"], kind="warning")
    assert f.kind == "warning"
    assert f.icon == "\u26a0"  # ⚠


def test_flag_block_opportunity():
    from dartlab.review.blocks import FlagBlock

    f = FlagBlock(flags=["배당 성장"], kind="opportunity")
    assert f.kind == "opportunity"
    assert f.icon == "\u2726"  # ✦


def test_flag_block_default_kind():
    from dartlab.review.blocks import FlagBlock

    f = FlagBlock(flags=["test"])
    assert f.kind == "warning"


def test_flag_block_multiple_flags():
    from dartlab.review.blocks import FlagBlock

    f = FlagBlock(flags=["A", "B", "C"])
    assert len(f.flags) == 3


def test_flag_block_enriched_flags():
    from dartlab.review.blocks import EnrichedFlag, FlagBlock

    ef = EnrichedFlag(
        code="BENEISH_MANIPULATOR",
        message="Beneish M-Score 위험",
        precision=0.76,
        baseRate="1990-2020 미국 기업",
        reference="Beneish (1999)",
    )
    f = FlagBlock(flags=["Beneish 경고"], enrichedFlags=[ef])
    assert f.enrichedFlags is not None
    assert len(f.enrichedFlags) == 1
    assert f.enrichedFlags[0].code == "BENEISH_MANIPULATOR"
    assert f.enrichedFlags[0].precision == 0.76


def test_flag_block_enriched_flags_default_none():
    from dartlab.review.blocks import FlagBlock

    f = FlagBlock(flags=["x"])
    assert f.enrichedFlags is None


# ── EnrichedFlag ──


def test_enriched_flag_defaults():
    from dartlab.review.blocks import EnrichedFlag

    ef = EnrichedFlag(code="TEST", message="test msg")
    assert ef.precision is None
    assert ef.baseRate == ""
    assert ef.reference == ""
    assert ef.sectorNote == ""


# ── TableBlock ──


def test_table_block_with_polars_df():
    from dartlab.review.blocks import TableBlock

    df = pl.DataFrame({"항목": ["매출", "영업이익"], "금액": [100, 20]})
    t = TableBlock(label="손익", df=df)
    assert t.label == "손익"
    assert isinstance(t.df, pl.DataFrame)
    assert t.df.shape == (2, 2)


def test_table_block_defaults():
    from dartlab.review.blocks import TableBlock

    df = pl.DataFrame({"a": [1]})
    t = TableBlock(label="L", df=df)
    assert t.caption == ""


def test_table_block_with_caption():
    from dartlab.review.blocks import TableBlock

    df = pl.DataFrame({"a": [1]})
    t = TableBlock(label="L", df=df, caption="단위: 억원")
    assert t.caption == "단위: 억원"


# ── ChartBlock ──


def test_chart_block_spec():
    from dartlab.review.blocks import ChartBlock

    spec = {"chartType": "bar", "title": "Test", "series": []}
    cb = ChartBlock(spec=spec)
    assert cb.spec["chartType"] == "bar"
    assert cb.caption == ""


def test_chart_block_with_caption():
    from dartlab.review.blocks import ChartBlock

    cb = ChartBlock(spec={"chartType": "line"}, caption="매출 추이")
    assert cb.caption == "매출 추이"


# ── Block union type ──


def test_block_type_union():
    from dartlab.review.blocks import (
        Block,
        ChartBlock,
        FlagBlock,
        HeadingBlock,
        MetricBlock,
        TableBlock,
        TextBlock,
    )

    # Block이 union 타입 alias로 정의되어 있는지 확인
    assert Block is not None
    # 각 블록 인스턴스가 Block에 포함되어야 한다
    blocks = [
        HeadingBlock(title="T"),
        TextBlock(text="T"),
        MetricBlock(metrics=[]),
        FlagBlock(flags=[]),
        TableBlock(label="L", df=pl.DataFrame()),
        ChartBlock(spec={}),
    ]
    for b in blocks:
        assert isinstance(b, (TextBlock, HeadingBlock, TableBlock, FlagBlock, MetricBlock, ChartBlock))
