"""`dartlab excel` command."""

from __future__ import annotations

from dartlab.cli.services.errors import CLIError
from dartlab.cli.services.runtime import configure_dartlab


def configure_parser(subparsers) -> None:
    parser = subparsers.add_parser("excel", help="Excel 파일로 내보내기")
    parser.add_argument("company", help="종목코드 (005930) 또는 회사명 (삼성전자)")
    parser.add_argument("-o", "--output", default=None, help="출력 경로 (기본: {종목코드}_{회사명}.xlsx)")
    parser.add_argument("--modules", nargs="+", default=None, help="포함할 시트 (IS BS CF ratios 등)")
    parser.set_defaults(handler=run)


def run(args) -> int:
    dartlab = configure_dartlab()

    try:
        company = dartlab.Company(args.company)
    except (ValueError, OSError) as exc:
        raise CLIError(str(exc)) from exc

    from dartlab.export.excel import exportToExcel

    try:
        path = exportToExcel(company, outputPath=args.output, modules=args.modules)
    except (OSError, ValueError, RuntimeError) as exc:
        raise CLIError(str(exc)) from exc

    print(f"  {company.corpName} ({company.stockCode}) → {path}")
    return 0
