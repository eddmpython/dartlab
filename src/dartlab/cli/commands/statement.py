"""`dartlab statement` command."""

from __future__ import annotations

import polars as pl

from dartlab.cli.services.errors import CLIError
from dartlab.cli.services.runtime import configure_dartlab

_STATEMENTS = ("BS", "IS", "CIS", "CF", "SCE")

_LABELS = {
    "BS": "재무상태표",
    "IS": "손익계산서",
    "CIS": "포괄손익계산서",
    "CF": "현금흐름표",
    "SCE": "자본변동표",
}


def configure_parser(subparsers) -> None:
    parser = subparsers.add_parser("statement", help="재무제표/자본변동표 출력")
    parser.add_argument("company", help="종목코드 (005930) 또는 회사명 (삼성전자)")
    parser.add_argument("name", choices=_STATEMENTS, help="BS | IS | CIS | CF | SCE")
    parser.set_defaults(handler=run)


def run(args) -> int:
    from dartlab.cli.services.output import get_console, print_dataframe

    dartlab = configure_dartlab()
    console = get_console()

    try:
        company = dartlab.Company(args.company)
    except (ValueError, OSError) as exc:
        raise CLIError(str(exc)) from exc

    label = _LABELS.get(args.name, args.name)
    console.print(f"\n  [bold]{company.corpName}[/] ({company.stockCode}) — {label}\n")

    value = getattr(company, args.name)
    if value is None:
        console.print(f"[dim]{company.corpName} {label} 데이터가 없습니다.[/]")
        return 0
    if isinstance(value, pl.DataFrame):
        print_dataframe(value, title=label)
        return 0
    console.print(str(value))
    return 0
