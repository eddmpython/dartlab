"""optional 라이브러리 감지."""

from __future__ import annotations


def hasGreatTables() -> bool:
    try:
        import great_tables  # noqa: F401

        return True
    except ImportError:
        return False


def hasItables() -> bool:
    try:
        import itables  # noqa: F401

        return True
    except ImportError:
        return False


def hasAltair() -> bool:
    try:
        import altair  # noqa: F401

        return True
    except ImportError:
        return False
