"""`dartlab profile` command — company index / facts."""

from __future__ import annotations

import polars as pl

from dartlab.cli.services.errors import CLIError
from dartlab.cli.services.runtime import configure_dartlab


def configure_parser(subparsers) -> None:
    """profile 서브커맨드 등록 — Company index/facts 출력."""
    parser = subparsers.add_parser("profile", help="company index 및 facts 출력")
    parser.add_argument("company", help="종목코드 (005930) 또는 회사명 (삼성전자)")
    parser.add_argument(
        "--facts",
        action="store_true",
        help="source-aware facts long table 출력",
    )
    parser.set_defaults(handler=run)


def run(args) -> int:
    """Company index 또는 facts 테이블을 콘솔에 출력한다."""
    from dartlab.cli.services.output import get_console, print_dataframe

    dartlab = configure_dartlab()
    console = get_console()

    from dartlab.guide.integration import cliCompany

    company = cliCompany(args.company)

    console.print(f"\n  [bold]{company.corpName}[/] ({company.stockCode})\n")

    mode = "facts" if args.facts else "index"
    payload = company.profile.facts if args.facts else company.index

    if payload is None:
        console.print(f"[dim]{company.corpName} {mode} 데이터가 없습니다.[/]")
        return 0
    if isinstance(payload, pl.DataFrame):
        print_dataframe(payload, title=mode.capitalize())
        return 0
    if isinstance(payload, dict):
        from rich.table import Table

        table = Table(show_header=False, padding=(0, 2))
        table.add_column("항목", style="bold")
        table.add_column("값")
        for k, v in payload.items():
            table.add_row(str(k), str(v) if v is not None else "")
        console.print(table)
        return 0
    console.print(str(payload))
    return 0
