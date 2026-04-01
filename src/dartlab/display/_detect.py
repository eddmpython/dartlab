"""optional 라이브러리 감지."""

from __future__ import annotations


def hasGreatTables() -> bool:
    """great_tables 설치 여부 확인."""
    try:
        import great_tables  # noqa: F401

        return True
    except ImportError:
        return False


def hasItables() -> bool:
    """itables 설치 여부 확인."""
    try:
        import itables  # noqa: F401

        return True
    except ImportError:
        return False
