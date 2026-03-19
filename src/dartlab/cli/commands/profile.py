"""`dartlab profile` command — company index / facts."""

from __future__ import annotations

import pprint

import polars as pl

from dartlab.cli.services.errors import CLIError
from dartlab.cli.services.runtime import configure_dartlab


def configure_parser(subparsers) -> None:
    parser = subparsers.add_parser("profile", help="company index 및 facts 출력")
    parser.add_argument("company", help="종목코드 (005930) 또는 회사명 (삼성전자)")
    parser.add_argument(
        "--facts",
        action="store_true",
        help="source-aware facts long table 출력",
    )
    parser.set_defaults(handler=run)


def _print_payload(payload) -> int:
    if payload is None:
        print("데이터가 없습니다.")
        return 0
    if isinstance(payload, pl.DataFrame):
        print(payload)
        return 0
    pprint.pprint(payload, sort_dicts=False, width=120)
    return 0


def run(args) -> int:
    dartlab = configure_dartlab()

    try:
        company = dartlab.Company(args.company)
    except (ValueError, OSError) as exc:
        raise CLIError(str(exc)) from exc

    if args.facts:
        payload = company.profile.facts
    else:
        payload = company.index
    return _print_payload(payload)
