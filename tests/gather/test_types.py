"""dartlab.gather.types mirror 슬롯 — smoke import (P-G7.2).

룰 7 (src↔tests 1:1 mirror) 만족용 placeholder. 본격 단위 테스트는 후속.
"""

from __future__ import annotations

import importlib

import pytest

pytestmark = pytest.mark.unit


def test_smoke_import() -> None:
    """``dartlab.gather.types`` 모듈 import 가능 — 모듈 구조 회귀 차단."""
    importlib.import_module("dartlab.gather.types")


def testOptionalSourceErrorRecursesThroughExceptionGroups() -> None:
    """AnyIO의 중첩 그룹이 모두 네트워크 실패일 때만 선택 입력으로 강등한다."""
    from dartlab.core.offlineGuard import OfflineViolation
    from dartlab.gather.types import SourceUnavailableError, isOptionalSourceError

    optional = ExceptionGroup(
        "network candidates",
        [OfflineViolation("blocked"), ExceptionGroup("fallback", [SourceUnavailableError("down")])],
    )
    mixed = ExceptionGroup("mixed", [OfflineViolation("blocked"), ValueError("bad local data")])

    assert isOptionalSourceError(optional) is True
    assert isOptionalSourceError(mixed) is False
