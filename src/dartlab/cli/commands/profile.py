"""`dartlab profile` command."""

from __future__ import annotations

import pprint

import polars as pl

from dartlab.cli.services.errors import CLIError
from dartlab.cli.services.runtime import configure_dartlab


def configure_parser(subparsers) -> None:
    parser = subparsers.add_parser("profile", help="company index / topic inspection 진입점")
    parser.add_argument("company", help="종목코드 (005930) 또는 회사명 (삼성전자)")
    parser.add_argument(
        "--facts",
        action="store_true",
        help="legacy source-aware facts long table 출력",
    )
    parser.add_argument(
        "--index",
        action="store_true",
        help="legacy alias: 현재 기본 출력과 동일한 구조 index DataFrame 출력",
    )
    parser.add_argument(
        "--show",
        metavar="TOPIC",
        help='topic payload 출력 예: --show BS, --show dividend, --show companyOverview',
    )
    parser.add_argument(
        "--trace",
        metavar="TOPIC",
        help='topic source trace 출력 예: --trace dividend',
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

    if args.trace:
        payload = company.trace(args.trace)
    elif args.show:
        payload = company.show(args.show)
    elif args.facts:
        payload = company.profile.facts
    else:
        payload = company.index
    return _print_payload(payload)
