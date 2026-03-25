"""index DataFrame → Rich Tree 렌더링."""

from __future__ import annotations

import polars as pl
from rich.console import Console
from rich.tree import Tree

_SOURCE_ICON = {
    "finance": "★",
    "docs": "📄",
    "report": "📋",
}


def renderIndex(df: pl.DataFrame, *, corpName: str = "") -> Tree:
    """index DataFrame → Rich Tree 객체."""
    title = f"📋 {corpName} 목차" if corpName else "📋 목차"
    tree = Tree(f"[bold]{title}[/bold]")

    # chapter > topic 계층
    chapters: dict[str, list[dict]] = {}
    for row in df.iter_rows(named=True):
        ch = row.get("chapter", "")
        if ch not in chapters:
            chapters[ch] = []
        chapters[ch].append(row)

    for chapter, rows in chapters.items():
        chLabel = chapter if chapter else "(미분류)"
        branch = tree.add(f"[bold cyan]{chLabel}[/bold cyan]")

        for row in rows:
            topic = row.get("topic", "")
            source = row.get("source", "")
            icon = _SOURCE_ICON.get(source, "")

            # 기간 범위
            periods = row.get("periods", "")
            periodStr = f" ({periods})" if periods else ""

            # kind
            kind = row.get("kind", "")
            kindStr = f" [{kind}]" if kind and kind != "text" else ""

            label = f"{topic}{kindStr}{periodStr} {icon}".strip()
            branch.add(label)

    return tree


def showIndex(df: pl.DataFrame, *, corpName: str = "") -> None:
    """index DataFrame을 Rich Tree로 콘솔 출력."""
    tree = renderIndex(df, corpName=corpName)
    console = Console()
    console.print(tree)
