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


def main(argv: list[str] | None = None) -> int:
    _ensure_utf8()

    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        if exc.code in (0, None):
            raise
        print_error(str(exc))
        return EXIT_USAGE

    handler = getattr(args, "handler", None)
    if handler is None:
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
    except Exception as exc:
        print_error(f"예상하지 못한 오류가 발생했습니다: {exc}")
        return EXIT_RUNTIME


if __name__ == "__main__":
    raise SystemExit(main())
