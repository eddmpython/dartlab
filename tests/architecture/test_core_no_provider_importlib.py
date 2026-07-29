"""core의 provider 문자열 우회를 포함한 concrete 상향 import 회귀."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIT_ROOT = REPO_ROOT / "tests" / "audit"
if str(AUDIT_ROOT) not in sys.path:
    sys.path.insert(0, str(AUDIT_ROOT))

from guard.indexer import buildIndex  # noqa: E402
from guard.rules import checkCoreImportBoundary  # noqa: E402


def test_core_no_concrete_upper_import() -> None:
    """정적·리터럴·상수·미해결 동적 상향 경로를 단일 규칙으로 차단한다."""
    assert checkCoreImportBoundary(buildIndex(REPO_ROOT)) == []
