"""RatioResult → Rich Table 렌더링."""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.table import Table


def renderRatio(result: Any) -> Table:
    """RatioResult → Rich Table 객체."""
    table = Table(
        title="재무비율",
        show_header=True,
        header_style="bold cyan",
        expand=False,
    )
    table.add_column("지표", style="bold", no_wrap=True, max_width=28)
    table.add_column("값", justify="right", no_wrap=True)

    for group, fields in result._DISPLAY_GROUPS:
        hasData = False
        rows: list[tuple[str, str]] = []
        for f in fields:
            v = getattr(result, f, None)
            if v is None:
                continue
            hasData = True
            label = result._LABELS.get(f, f)
            if isinstance(v, float) and abs(v) >= 1e12:
                formatted = f"{v / 1e12:,.1f}조"
            elif isinstance(v, float) and abs(v) >= 1e8:
                formatted = f"{v / 1e8:,.0f}억"
            elif isinstance(v, float):
                formatted = f"{v:,.2f}"
            else:
                formatted = str(v)
            rows.append((label, formatted))

        if hasData:
            table.add_row(f"[bold yellow]── {group} ──[/bold yellow]", "")
            for label, formatted in rows:
                table.add_row(f"  {label}", formatted)

    if getattr(result, "warnings", None):
        table.add_row("[red]⚠ 경고[/red]", ", ".join(result.warnings))

    return table


def showRatio(result: Any) -> None:
    """RatioResult를 Rich Table로 콘솔 출력."""
    table = renderRatio(result)
    console = Console()
    console.print(table)
