"""`dartlab update` command -- 로컬 데이터를 HuggingFace 최신으로 갱신.

사용 예시::

    dartlab update                   # finance+report 갱신 (기본)
    dartlab update --all             # finance+report+docs 전부
    dartlab update -c finance        # finance만
    dartlab update 005930            # 특정 종목만 갱신
    dartlab update 005930 -c docs    # 특정 종목 docs만
"""

from __future__ import annotations


def configure_parser(subparsers) -> None:
    """update 서브커맨드 등록."""
    parser = subparsers.add_parser(
        "update",
        help="로컬 데이터를 HuggingFace 최신으로 갱신",
    )
    parser.add_argument(
        "codes",
        nargs="*",
        help="종목코드 (생략 시 전체 갱신)",
    )
    parser.add_argument(
        "--categories",
        "-c",
        type=str,
        default=None,
        help="카테고리 (쉼표 구분: finance,report,docs)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="docs 포함 전체 갱신 (기본은 finance+report만)",
    )
    parser.set_defaults(handler=run)


def run(args) -> int:
    """로컬 데이터를 HF 최신으로 갱신."""
    from dartlab.cli.services.output import get_console

    console = get_console()

    if args.codes:
        return _updateCodes(console, args)
    return _updateAll(console, args)


def _updateCodes(console, args) -> int:
    """특정 종목 데이터를 HF에서 최신으로 갱신."""
    from dartlab.core.dataLoader import loadData

    cats = _parseCategories(args)
    updated = 0

    for code in args.codes:
        for cat in cats:
            console.print(f"  {code}/{cat}: 확인 중...")
            try:
                loadData(code, cat, refresh="force_check")
                console.print(f"  {code}/{cat}: OK")
                updated += 1
            except (RuntimeError, FileNotFoundError, ValueError) as e:
                console.print(f"  {code}/{cat}: [red]{e}[/]")

    console.print(f"\n확인 완료: {updated}건")
    return 0


def _updateAll(console, args) -> int:
    """전체 카테고리를 HF 최신으로 갱신."""
    from dartlab.core.dataLoader import downloadAll

    cats = _parseCategories(args)

    for cat in cats:
        console.print(f"[bold]{cat}[/] 갱신 중...")
        try:
            downloadAll(cat, forceUpdate=True)
            console.print(f"[bold]{cat}[/] 갱신 완료")
        except ImportError:
            console.print(f"[red]{cat}: huggingface_hub 필요 (pip install dartlab[hf])[/]")
            return 1
        except RuntimeError as e:
            console.print(f"[red]{cat}: {e}[/]")
            return 1

    return 0


def _parseCategories(args) -> list[str]:
    """카테고리 파싱."""
    if args.categories:
        return [c.strip() for c in args.categories.split(",")]
    if getattr(args, "all", False):
        return ["finance", "report", "docs"]
    return ["finance", "report"]
