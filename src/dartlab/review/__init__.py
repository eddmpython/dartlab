"""dartlab.review — 분석 리뷰 패키지.

c.review() 하나로 분석 보고서 생성 + 렌더링.
AI reviewer는 이 위에 올라간다.

사용법::

    # 1. 블록 사전
    from dartlab.review import blocks
    b = blocks(company)
    b["segmentComposition"]           # 바로 렌더링

    # 2. 자유 조립
    from dartlab.review import Review
    Review([b["segmentComposition"], b["growth"], c.select("IS", ["매출액"])])

    # 3. 템플릿
    c.review()                        # 전체
    c.review("수익구조")               # 수익구조 템플릿
"""

from __future__ import annotations

from dataclasses import dataclass, field

from dartlab.review.blocks import (
    Block,
    FlagBlock,
    HeadingBlock,
    MetricBlock,
    TableBlock,
    TextBlock,
)
from dartlab.review.layout import DEFAULT_LAYOUT, ReviewLayout
from dartlab.review.registry import buildBlocks, buildReview
from dartlab.review.renderer import renderReview
from dartlab.review.section import Section
from dartlab.review.utils import fmtAmt, fmtAmtScale, isTerminal, unifyTableScale


def blocks(company) -> dict:
    """블록 사전 — analysis 계산 결과를 블록으로 변환해서 사전에 담는다.

    사용법::

        import dartlab
        from dartlab.review import blocks

        c = dartlab.Company("005930")
        b = blocks(c)
        print(list(b.keys()))
        print(b["segmentComposition"])
    """
    return buildBlocks(company)


def _flattenItems(items) -> list:
    """리스트/SelectResult 혼합을 flat하게 펼친다."""
    flat = []
    for item in items:
        if isinstance(item, list):
            flat.extend(item)
        elif item is not None:
            flat.append(item)
    return flat


@dataclass
class Review:
    """분석 리뷰 — AnalysisReport + core/Report 통합.

    생성 방법:
    1. buildReview(company) → 템플릿 기반 자동 생성
    2. Review([blocks...]) → 자유 조립 (리스트 전달)
    3. Review(stockCode=..., corpName=..., sections=[...]) → 직접 구성
    """

    stockCode: str = ""
    corpName: str = ""
    sections: list[Section] = field(default_factory=list)
    layout: ReviewLayout = field(default_factory=ReviewLayout)
    aiNote: str | None = None  # AI 미설정 시 안내 메시지

    def __init__(
        self,
        itemsOrStockCode=None,
        /,
        stockCode: str = "",
        corpName: str = "",
        sections: list[Section] | None = None,
        layout: ReviewLayout | None = None,
        aiNote: str | None = None,
    ):
        """리스트 전달 시 자유 조립, 아니면 일반 생성."""
        if isinstance(itemsOrStockCode, list):
            # 자유 조립: Review([block1, block2, ...])
            self.stockCode = stockCode
            self.corpName = corpName
            flat = _flattenItems(itemsOrStockCode)
            self.sections = (
                [
                    Section(
                        key="custom",
                        partId="",
                        title="",
                        blocks=flat,
                    )
                ]
                if flat
                else []
            )
            self.layout = layout or ReviewLayout()
            self.aiNote = aiNote
        elif isinstance(itemsOrStockCode, str):
            # Review("005930", corpName=..., ...)
            self.stockCode = itemsOrStockCode
            self.corpName = corpName
            self.sections = sections or []
            self.layout = layout or ReviewLayout()
            self.aiNote = aiNote
        else:
            # Review(stockCode=..., corpName=..., ...)
            self.stockCode = stockCode
            self.corpName = corpName
            self.sections = sections or []
            self.layout = layout or ReviewLayout()
            self.aiNote = aiNote

    def render(self, fmt: str = "rich") -> str:
        """통합 렌더러."""
        if fmt == "rich":
            return self._renderRich()
        if fmt == "html":
            from dartlab.review.formats import renderHtml

            return renderHtml(self)
        if fmt == "markdown":
            from dartlab.review.formats import renderMarkdown

            return renderMarkdown(self)
        if fmt == "json":
            from dartlab.review.formats import renderJson

            return renderJson(self)
        raise ValueError(f"지원하지 않는 렌더링 형식: {fmt}")

    def __repr__(self) -> str:
        from rich.console import Console

        console = Console(highlight=False, force_terminal=True)
        with console.capture() as capture:
            renderReview(console, self)
        return capture.get()

    def _repr_html_(self) -> str:
        """Jupyter / Colab / Marimo HTML 렌더링."""
        from rich.console import Console

        console = Console(record=True, force_jupyter=True, width=120)
        renderReview(console, self)
        return console.export_html(inline_styles=True)

    def _renderRich(self) -> str:
        """Rich Console capture → 텍스트."""
        from rich.console import Console

        console = Console(highlight=False, force_terminal=True)
        with console.capture() as capture:
            renderReview(console, self)
        return capture.get()

    # ── 편의 메서드 ──

    def toHtml(self) -> str:
        return self.render("html")

    def toMarkdown(self) -> str:
        return self.render("markdown")

    def toJson(self) -> str:
        return self.render("json")


__all__ = [
    "Review",
    "ReviewLayout",
    "Section",
    "Block",
    "TextBlock",
    "HeadingBlock",
    "TableBlock",
    "FlagBlock",
    "MetricBlock",
    "blocks",
    "buildBlocks",
    "buildReview",
    "renderReview",
    "fmtAmt",
    "fmtAmtScale",
    "unifyTableScale",
    "isTerminal",
    "DEFAULT_LAYOUT",
]
