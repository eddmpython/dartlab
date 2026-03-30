"""review rich 렌더러."""

from __future__ import annotations

from dartlab.review.blocks import (
    FlagBlock,
    HeadingBlock,
    MetricBlock,
    TableBlock,
    TextBlock,
)
from dartlab.review.layout import ReviewLayout
from dartlab.review.section import Section
from dartlab.review.utils import padLabel


def renderReview(console, review) -> None:
    """rich Console에 전체 리뷰 출력."""
    ly = review.layout

    # 헤더
    console.print()
    console.print(f"  [bold white]{review.corpName}[/]  [dim]{review.stockCode}[/]")
    console.print(f"[dim]{'─' * ly.separatorWidth}[/]")
    console.print("[dim]  dartlab review[/]")

    # 요약 카드 (summaryCard가 있으면 circulationSummary 위에 표시)
    if review.summaryCard:
        _renderSummaryCard(console, review.summaryCard, ly)

    # 순환 서사 요약
    if review.circulationSummary:
        _renderCirculationSummary(console, review.circulationSummary, ly)

    for section in review.sections:
        _renderSection(console, section, ly)

    # AI 미설정 안내
    if review.aiNote:
        console.print()
        console.print(f"[dim]      {review.aiNote}[/]")

    console.print()


def _renderSummaryCard(console, card, ly) -> None:
    """최상단 요약 카드 렌더링."""
    from rich.padding import Padding
    from rich.panel import Panel
    from rich.text import Text

    lines = Text()

    if card.conclusion:
        lines.append(card.conclusion, style="bold white")
        lines.append("\n")

    if card.grades:
        gradeStr = " | ".join(f"{k} {v}" for k, v in card.grades.items())
        lines.append(gradeStr, style="dim")
        lines.append("\n")

    if card.strengths:
        lines.append("\n")
        for s in card.strengths:
            lines.append(f"  + {s}\n", style="green")

    if card.warnings:
        for w in card.warnings:
            lines.append(f"  - {w}\n", style="yellow")

    console.print()
    panel = Panel(
        lines,
        border_style="bold",
        padding=(0, 2),
    )
    console.print(Padding(panel, (0, 0, 0, ly.indentH2)))


def _renderCirculationSummary(console, summary: str, ly) -> None:
    """순환 서사 요약 박스."""
    from rich.padding import Padding
    from rich.panel import Panel
    from rich.text import Text

    console.print()
    panel = Panel(
        Text(summary),
        title="[bold]재무 순환 서사[/]",
        border_style="dim",
        padding=(0, 2),
    )
    console.print(Padding(panel, (0, 0, 0, ly.indentH2)))


def _renderSection(console, section: Section, ly: ReviewLayout) -> None:
    """한 섹션 렌더링."""
    from rich.padding import Padding
    from rich.text import Text

    h1 = " " * ly.indentH1

    # detail=False: summary만 표시
    if not ly.detail:
        if section.title:
            console.print()
            console.print(f"{h1}[bold cyan]■ {section.title}[/]")
        if section.summary:
            console.print(Padding(Text(section.summary, style="dim"), (0, 0, 0, ly.indentH2)))
        return

    prevBlockType = None
    helperRendered = False

    h2 = " " * ly.indentH2
    body = " " * ly.indentBody

    # 섹션 타이틀 (H1 역할)
    if section.title:
        console.print()
        console.print(f"{h1}[bold cyan]■ {section.title}[/]")
        if section.aiOpinion:
            console.print()
            console.print(f"{h2}[bold cyan]AI 분석 요약[/]")
            for aiLine in section.aiOpinion.split("\n"):
                if aiLine.strip():
                    console.print(
                        Padding(
                            Text(aiLine.strip(), style="cyan"),
                            (0, 0, 0, ly.indentH2),
                        )
                    )
        # 순환 서사 threads
        if section.threads:
            _renderSectionThreads(console, section.threads, ly)
        if section.helper:
            console.print()
            for line in section.helper.split("\n"):
                if line.strip():
                    console.print(f"{h2}[dim italic]{line}[/]")
            console.print()
            helperRendered = True

    for block in section.blocks:
        if isinstance(block, HeadingBlock):
            if block.level == 1:
                console.print()
                console.print(f"{h1}[bold cyan]■ {block.title}[/]")
                # AI 의견: 대제목 바로 아래 (reviewer가 채움)
                if section.aiOpinion:
                    console.print()
                    console.print(f"{h2}[bold cyan]AI 분석 요약[/]")
                    for aiLine in section.aiOpinion.split("\n"):
                        if aiLine.strip():
                            console.print(
                                Padding(
                                    Text(aiLine.strip(), style="cyan"),
                                    (0, 0, 0, ly.indentH2),
                                )
                            )
                # 헬퍼 텍스트: H2 들여쓰기, 위아래 빈줄
                if section.helper and not helperRendered:
                    console.print()
                    for line in section.helper.split("\n"):
                        if line.strip():
                            console.print(f"{h2}[dim italic]{line}[/]")
                    console.print()
                    helperRendered = True
                else:
                    for _ in range(ly.gapAfterH1):
                        console.print()
            else:
                if prevBlockType is not None:
                    for _ in range(ly.gapBetween):
                        console.print()
                console.print(f"{h2}[bold white]▸ {block.title}[/]")
                for _ in range(ly.gapAfterH2):
                    console.print()

        elif isinstance(block, TextBlock):
            if prevBlockType is not None and prevBlockType is not HeadingBlock:
                console.print()
            style = block.style or ""
            ind = ly.indentH2 if block.indent == "h2" else ly.indentBody
            console.print(
                Padding(
                    Text(block.text, style=style),
                    (0, 0, 0, ind),
                )
            )

        elif isinstance(block, MetricBlock):
            if prevBlockType is MetricBlock:
                console.print()
            for label, value in block.metrics:
                padded = padLabel(label, 22)
                console.print(f"{body}[dim]{padded}[/] {value}")

        elif isinstance(block, TableBlock):
            console.print()
            _renderDataFrame(console, block, indent=ly.indentBody)

        elif isinstance(block, FlagBlock):
            if prevBlockType is not None and not isinstance(prevBlockType, FlagBlock):
                console.print()
            icon = "⚠" if block.kind == "warning" else "✦"
            color = "yellow" if block.kind == "warning" else "green"
            for f in block.flags:
                console.print(f"{body}[{color}]{icon} {f}[/]")

        elif hasattr(block, "render"):
            # SelectResult / ChartResult — render("rich") 위임
            rendered = block.render("rich")
            if rendered:
                console.print(Padding(Text.from_ansi(rendered), (0, 0, 0, ly.indentBody)))

        prevBlockType = type(block)


def _renderSectionThreads(console, threads, ly) -> None:
    """섹션에 연결된 인과 서사 -- title만 표시 (story는 상단 순환 서사에서 1회)."""
    h2 = " " * ly.indentH2

    console.print()
    for t in threads:
        colorMap = {
            "critical": "bold red",
            "warning": "yellow",
            "positive": "green",
            "neutral": "dim",
        }
        color = colorMap.get(t.severity, "dim")
        console.print(f"{h2}[{color}]>> {t.title}[/]")


def _renderDataFrame(console, block: TableBlock, indent: int = 6) -> None:
    """Polars DataFrame을 rich Table로 렌더링."""
    import polars as pl
    from rich import box
    from rich.padding import Padding
    from rich.table import Table

    df = block.df
    if not isinstance(df, pl.DataFrame) or df.is_empty():
        return

    pad = " " * indent
    if block.label:
        console.print(f"{pad}[dim]{block.label}[/]")

    table = Table(
        box=box.SIMPLE_HEAD,
        padding=(0, 2),
        show_edge=False,
        pad_edge=True,
    )

    for i, col in enumerate(df.columns):
        isFirstCol = i == 0
        justify = "left" if isFirstCol else "right"
        table.add_column(col, justify=justify)

    for row in df.iter_rows():
        table.add_row(*(str(v) if v is not None else "-" for v in row))

    console.print(Padding(table, (0, 0, 0, indent)))
    if block.caption:
        console.print(f"{pad}[dim italic]{block.caption}[/]")
