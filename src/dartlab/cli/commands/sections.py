"""`dartlab sections` command."""

from __future__ import annotations

import polars as pl

from dartlab.cli.services.errors import CLIError
from dartlab.cli.services.runtime import configure_dartlab


def configure_parser(subparsers) -> None:
    """sections 서브커맨드 등록 — pure docs 수평화 sections 출력."""
    parser = subparsers.add_parser("sections", help="pure docs 수평화 sections 출력")
    parser.add_argument("company", help="종목코드 (005930) 또는 회사명 (삼성전자)")
    parser.set_defaults(handler=run)


def run(args) -> int:
    """docs.sections DataFrame을 콘솔에 출력한다."""
    from dartlab.cli.services.output import get_console, print_dataframe

    dartlab = configure_dartlab()
    console = get_console()

    try:
        company = dartlab.Company(args.company)
    except (ValueError, OSError) as exc:
        raise CLIError(str(exc)) from exc

    console.print(f"\n  [bold]{company.corpName}[/] ({company.stockCode})\n")

    sections = company.docs.sections
    if sections is None:
        console.print(f"[dim]{company.corpName} sections 데이터가 없습니다.[/]")
        return 0
    if not isinstance(sections, pl.DataFrame):
        console.print("[bold red]오류:[/] sections 데이터 형식이 올바르지 않습니다.")
        return 1
    print_dataframe(sections, title="Sections")
    return 0
