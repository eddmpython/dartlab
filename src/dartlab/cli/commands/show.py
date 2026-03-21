"""`dartlab show` command — topic 기반 데이터 조회."""

from __future__ import annotations

import polars as pl

from dartlab.cli.services.errors import CLIError
from dartlab.cli.services.runtime import configure_dartlab


def configure_parser(subparsers) -> None:
    parser = subparsers.add_parser(
        "show",
        help="topic 데이터 조회 (show(topic) 인터페이스)",
    )
    parser.add_argument("company", help="종목코드 (005930) 또는 회사명 (삼성전자)")
    parser.add_argument("topic", nargs="?", default=None, help="topic 이름 (BS, IS, dividend, companyOverview ...)")
    parser.add_argument("--block", "-b", type=int, default=None, help="blockOrder 인덱스 (생략 시 블록 목차 또는 자동)")
    parser.add_argument("--period", "-p", nargs="+", default=None, help="기간 필터 (2024 또는 2024Q4 2023Q4)")
    parser.add_argument("--trace", "-t", metavar="TOPIC", help="topic 출처 추적 (source, periods, hasText/Table)")
    parser.add_argument("--raw", action="store_true", help="원본 그대로 출력")
    parser.set_defaults(handler=run)


def _print_result(result, title: str | None = None, *, context: str = "") -> int:
    from dartlab.cli.services.output import get_console, print_dataframe

    console = get_console()
    if result is None:
        label = f"{context} " if context else ""
        console.print(f"[dim]{label}데이터가 없습니다.[/]")
        return 0
    if isinstance(result, pl.DataFrame):
        print_dataframe(result, title=title)
        return 0
    if isinstance(result, dict):
        from rich.table import Table

        table = Table(show_header=False, padding=(0, 2))
        table.add_column("항목", style="bold")
        table.add_column("값")
        for k, v in result.items():
            table.add_row(str(k), str(v) if v is not None else "")
        console.print(table)
        return 0
    console.print(str(result))
    return 0


def run(args) -> int:
    dartlab = configure_dartlab()

    try:
        company = dartlab.Company(args.company)
    except (ValueError, OSError) as exc:
        raise CLIError(str(exc)) from exc

    from dartlab.cli.services.output import get_console

    console = get_console()
    console.print(f"\n  [bold]{company.corpName}[/] ({company.stockCode})\n")

    # trace 모드
    if args.trace:
        return _print_result(
            company.trace(args.trace),
            context=f"{company.corpName} trace({args.trace})",
        )

    # topic 미지정 → index (전체 topic 목차)
    if args.topic is None:
        return _print_result(company.index, context=f"{company.corpName} index")

    # period 처리
    period = args.period
    if period is not None and len(period) == 1:
        period = period[0]

    result = company.show(args.topic, args.block, period=period, raw=args.raw)
    return _print_result(result, context=f"{company.corpName} {args.topic}")
