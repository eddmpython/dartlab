"""`dartlab statement` command."""

from __future__ import annotations

import polars as pl

from dartlab.cli.services.errors import CLIError
from dartlab.cli.services.runtime import configure_dartlab

_STATEMENTS = ("BS", "IS", "CIS", "CF", "SCE")


def configure_parser(subparsers) -> None:
    parser = subparsers.add_parser("statement", help="재무제표/자본변동표 출력")
    parser.add_argument("company", help="종목코드 (005930) 또는 회사명 (삼성전자)")
    parser.add_argument("name", choices=_STATEMENTS, help="BS | IS | CIS | CF | SCE")
    parser.set_defaults(handler=run)


def _print_statement(value) -> int:
    if value is None:
        print("데이터가 없습니다.")
        return 0
    if isinstance(value, pl.DataFrame):
        print(value)
        return 0
    print(value)
    return 0


def run(args) -> int:
    dartlab = configure_dartlab()

    try:
        company = dartlab.Company(args.company)
    except (ValueError, OSError) as exc:
        raise CLIError(str(exc)) from exc

    return _print_statement(getattr(company, args.name))
