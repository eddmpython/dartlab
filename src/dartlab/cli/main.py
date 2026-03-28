"""DartLab CLI entrypoint."""

from __future__ import annotations

import io
import sys

from dartlab.cli.context import EXIT_INTERRUPTED, EXIT_OK, EXIT_RUNTIME, EXIT_USAGE
from dartlab.cli.parser import build_parser
from dartlab.cli.services.errors import CLIError
from dartlab.cli.services.output import print_error, print_warning


def _ensure_utf8() -> None:
    """Force UTF-8 console output on Windows cp949 shells."""
    if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def _looksLikeCompany(token: str) -> bool:
    """종목코드(6자리 숫자) 또는 한글 회사명처럼 보이는지."""
    if token.isdigit() and len(token) == 6:
        return True
    if any("\uac00" <= ch <= "\ud7a3" for ch in token):
        return True
    return False


def main(argv: list[str] | None = None) -> int:
    """CLI 메인 함수 -- 인자 파싱 후 서브커맨드 실행."""
    _ensure_utf8()

    raw = argv if argv is not None else sys.argv[1:]

    # dartlab 005930 → dartlab review 005930
    # dartlab 005930 자산구조 → dartlab review 005930 자산구조
    if raw and _looksLikeCompany(raw[0]):
        raw = ["review"] + raw

    parser = build_parser()
    try:
        args = parser.parse_args(raw)
    except SystemExit as exc:
        if exc.code in (0, None):
            raise
        print_error(str(exc))
        return EXIT_USAGE

    handler = getattr(args, "handler", None)
    if handler is None:
        if sys.stdin.isatty():
            from dartlab.cli.tui import run as tuiRun

            args.company = None
            args.provider = None
            args.model = None
            args.base_url = None
            args.api_key = None
            args.cont = False
            handler = tuiRun
        else:
            parser.print_help()
            return EXIT_OK

    try:
        return int(handler(args) or EXIT_OK)
    except CLIError as exc:
        print_error(str(exc))
        return exc.exit_code
    except KeyboardInterrupt:
        print_warning("사용자가 작업을 중단했습니다.")
        return EXIT_INTERRUPTED
    except BrokenPipeError:
        return EXIT_OK
    except Exception as exc:  # noqa: BLE001 — CLI 진입점 최종 catch-all
        print_error(f"예상하지 못한 오류가 발생했습니다: {exc}")
        return EXIT_RUNTIME


if __name__ == "__main__":
    raise SystemExit(main())
