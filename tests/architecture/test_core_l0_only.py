"""core L0 import 경계의 얇은 Guard Index 접점."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIT_ROOT = REPO_ROOT / "tests" / "audit"
if str(AUDIT_ROOT) not in sys.path:
    sys.path.insert(0, str(AUDIT_ROOT))

from guard.indexer import buildIndex  # noqa: E402
from guard.rules import checkCoreImportBoundary  # noqa: E402


def test_core_l0_only_no_upper_import() -> None:
    """core의 정적·동적 concrete 상향 import가 모두 없어야 한다."""
    assert checkCoreImportBoundary(buildIndex(REPO_ROOT)) == []
