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
    hasDocs = getattr(company, "_hasDocs", False)
    hasFin = getattr(company, "_hasFinanceParquet", False)
    hasRpt = getattr(company, "_hasReport", False)
    lines.append(
        f"  데이터: docs {_checkMark(hasDocs)}  "
        f"finance {_checkMark(hasFin)}  "
        f"report {_checkMark(hasRpt)}"
    )

    # 기간 범위 (sections 캐시된 경우에만)
    cache = getattr(company, "_cache", {})
    sectionsKey = "_lazyMergedSections"
    if sectionsKey in cache:
        sections = cache[sectionsKey]
        periodCols = [c for c in sections.columns if c[:4].isdigit()]
        if periodCols:
            sortedPeriods = sorted(periodCols)
            lines.append(f"  기간: {sortedPeriods[0]} ~ {sortedPeriods[-1]} ({len(sortedPeriods)}기)")

        topics = sections.get_column("topic").unique()
        chapters = sections.get_column("chapter").unique()
        lines.append(f"  sections: {len(topics)} topics · {len(chapters)} chapters")

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
