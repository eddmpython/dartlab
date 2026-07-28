"""`dartlab statement` command."""

from __future__ import annotations

import re

import polars as pl

from dartlab.cli.services.errors import CLIError
from dartlab.cli.services.runtime import configureDartlab
from dartlab.core.logger import getLogger

_log = getLogger(__name__)
_STATEMENTS = ("BS", "IS", "CIS", "CF", "SCE")
_PERIOD_RE = re.compile(r"\d{4}(Q[1-4])?")

_LABELS = {
    "BS": "재무상태표",
    "IS": "손익계산서",
    "CIS": "포괄손익계산서",
    "CF": "현금흐름표",
    "SCE": "자본변동표",
}


def configureParser(subparsers) -> None:
    """statement 서브커맨드 등록 — 재무제표 출력."""
    parser = subparsers.add_parser("statement", help="재무제표/자본변동표 출력")
    parser.add_argument("company", help="종목코드 (005930) 또는 회사명 (삼성전자)")
    parser.add_argument("name", choices=_STATEMENTS, help="BS | IS | CIS | CF | SCE")
    parser.add_argument("--periods", "-n", type=int, default=6, help="표시할 최근 기간 수 (기본 6, 0 이면 전체)")
    parser.set_defaults(handler=run)


def run(args) -> int:
    """지정 재무제표(BS/IS/CIS/CF/SCE)를 콘솔에 출력한다."""
    from dartlab.cli.services.output import getConsole, printDataframe

    dartlab = configureDartlab()
    console = getConsole()

    try:
        company = dartlab.Company(args.company)
    except (ValueError, FileNotFoundError, OSError, RuntimeError) as exc:
        from dartlab.cli.services.errors import wrapError

        raise CLIError(wrapError(exc, stockCode=args.company)) from exc

    label = _LABELS.get(args.name, args.name)
    console.print(f"\n  [bold]{company.corpName}[/] ({company.stockCode}) — {label}\n")

    # 예전에는 `company.BS` 처럼 속성으로 읽었다. 그 이름들은 공개 계약에서 빠졌고 지금은
    # 존재하지 않아 AttributeError 로 죽었다. 제목 두 줄만 찍히고 표가 안 나왔다.
    try:
        value = company.panel(args.name)
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        _log.debug("재무제표 %s 조회 실패: %s", args.name, exc)
        value = None
    if value is None:
        console.print(f"[dim]{company.corpName} {label} 데이터가 없습니다.[/]")
        return 0
    if isinstance(value, pl.DataFrame):
        # panel 은 기간 열을 마흔 개 넘게 준다. 콘솔 폭에 다 밀어 넣으면 열이 전부 뭉개져
        # 숫자가 한 자도 안 보인다. 기본은 최근 여섯 기간만 보이고 `-n 0` 이면 전체다.
        periodCols = [c for c in value.columns if _PERIOD_RE.fullmatch(c)]
        keep = int(getattr(args, "periods", 6) or 0)
        if keep and len(periodCols) > keep:
            # `snakeId` 는 내부 식별자다. 화면에서는 사람이 읽는 `항목` 만 남긴다.
            meta = [c for c in value.columns if c not in periodCols and c != "snakeId"]
            value = value.select(meta + sorted(periodCols, reverse=True)[:keep])
        printDataframe(value, title=label)
        return 0
    console.print(str(value))
    return 0
