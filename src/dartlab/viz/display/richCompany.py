"""Company → Rich Panel 렌더링."""

from __future__ import annotations

from typing import Any


def _checkMark(ok: bool) -> str:
    return "[green]✓[/green]" if ok else "[dim]✗[/dim]"


def renderCompany(company: Any) -> str:
    """Company 객체 → Rich Panel 문자열."""
    from rich.console import Console
    from rich.panel import Panel

    lines: list[str] = []

    # 시장 + 통화
    market = getattr(company, "market", "KR")
    currency = getattr(company, "currency", "KRW")
    lines.append(f"  시장: {market}   통화: {currency}")

    # 데이터 보유 현황
    hasPanel = getattr(company, "_hasPanel", False)
    hasFin = getattr(company, "_hasFinanceParquet", False)
    hasRpt = getattr(company, "_hasReport", False)
    lines.append(f"  데이터: panel {_checkMark(hasPanel)}  finance {_checkMark(hasFin)}  report {_checkMark(hasRpt)}")

    # 기간 범위 (panel text cache가 있는 경우에만)
    cache = getattr(company, "_cache", {})
    panelKey = "_panelTextWide"
    if panelKey in cache:
        panel = cache[panelKey]
        periodCols = [c for c in panel.columns if c[:4].isdigit()]
        if periodCols:
            sortedPeriods = sorted(periodCols)
            lines.append(f"  기간: {sortedPeriods[0]} ~ {sortedPeriods[-1]} ({len(sortedPeriods)}기)")

        topics = panel.get_column("topic").unique()
        chapters = panel.get_column("chapter").unique()
        lines.append(f"  panel: {len(topics)} topics · {len(chapters)} chapters")

    # guide 힌트 (데이터 보완, freshness 등)
    try:
        from dartlab.core.messagingHandlers import nextSteps, onCompanyCreated

        hints = onCompanyCreated(company)
        if hints:
            lines.append("")
            for h in hints:
                lines.append(f"  [dim yellow]{h}[/dim yellow]")

        steps = nextSteps(company)
        if steps:
            lines.append("")
            for s in steps:
                lines.append(f"  [dim]{s}[/dim]")
    except ImportError:
        pass

    body = "\n".join(lines)
    corpName = getattr(company, "corpName", "")
    stockCode = getattr(company, "stockCode", "") or getattr(company, "ticker", "")

    panel = Panel(
        body,
        title=f"[bold]{corpName}[/bold] ({stockCode})",
        border_style="bright_red",
        expand=False,
        padding=(0, 1),
    )

    console = Console(record=True, width=60)
    console.print(panel)
    return console.export_text()
