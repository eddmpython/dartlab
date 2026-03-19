"""`dartlab sections` command."""

from __future__ import annotations

import polars as pl

from dartlab.cli.services.errors import CLIError
from dartlab.cli.services.runtime import configure_dartlab


def configure_parser(subparsers) -> None:
    parser = subparsers.add_parser("sections", help="pure docs 수평화 sections 출력")
    parser.add_argument("company", help="종목코드 (005930) 또는 회사명 (삼성전자)")
    parser.set_defaults(handler=run)


def run(args) -> int:
    dartlab = configure_dartlab()

    try:
        company = dartlab.Company(args.company)
    except (ValueError, OSError) as exc:
        raise CLIError(str(exc)) from exc

    sections = company.docs.sections
    if sections is None:
        print("데이터가 없습니다.")
        return 0
    if not isinstance(sections, pl.DataFrame):
        print("sections 데이터 형식 오류")
        return 1
    print(sections)
    return 0
