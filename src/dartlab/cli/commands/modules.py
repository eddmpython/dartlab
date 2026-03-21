"""dartlab modules — 사용 가능한 모듈 목록."""

from __future__ import annotations


def configure_parser(subparsers) -> None:
    parser = subparsers.add_parser("modules", help="사용 가능한 모듈 목록 보기")
    parser.add_argument("--category", "-c", help="카테고리 필터 (finance, report, notes, disclosure, analysis, raw)")
    parser.add_argument("--search", "-s", help="모듈 이름/설명 검색")
    parser.set_defaults(handler=_run)


def _run(args) -> None:
    from rich.console import Console
    from rich.table import Table

    from dartlab.core.registry import getEntries

    console = Console()
    entries = getEntries()

    # Filter by category
    if args.category:
        entries = [e for e in entries if e.category == args.category]

    # Search
    if args.search:
        q = args.search.lower()
        entries = [
            e
            for e in entries
            if q in e.name.lower() or q in (e.label or "").lower() or q in (e.description or "").lower()
        ]

    if not entries:
        console.print("[yellow]일치하는 모듈이 없습니다.[/]")
        return

    # Group by category
    categories: dict[str, list] = {}
    for e in entries:
        cat = e.category or "other"
        categories.setdefault(cat, []).append(e)

    total = len(entries)
    console.print(f"\n[bold]DartLab Modules[/] — {total}개 모듈\n")

    for cat, items in sorted(categories.items()):
        table = Table(title=f"[bold cyan]{cat}[/] ({len(items)}개)", show_header=True, header_style="bold")
        table.add_column("Module", style="green", min_width=24)
        table.add_column("Label", min_width=20)
        table.add_column("Description", ratio=1)

        for e in sorted(items, key=lambda x: x.name):
            table.add_row(
                e.name,
                e.label or "",
                (e.description or "")[:80],
            )

        console.print(table)
        console.print()

    console.print("[dim]사용법: c = dartlab.Company('005930'); c.show('모듈명')[/]")
