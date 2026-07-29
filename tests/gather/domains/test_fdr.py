"""dartlab.gather.domains.fdr mirror 슬롯 — smoke import (P-G7.2).

룰 7 (src↔tests 1:1 mirror) 만족용 placeholder. 본격 단위 테스트는 후속.
"""

from __future__ import annotations

import asyncio
import importlib
import sys
import types

import pytest

pytestmark = pytest.mark.unit


def test_smoke_import() -> None:
    """``dartlab.gather.domains.fdr`` 모듈 import 가능 — 모듈 구조 회귀 차단."""
    importlib.import_module("dartlab.gather.domains.fdr")


def test_fetch_history_missing_dependency_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """optional dependency 부재는 정상 빈 데이터가 아니라 source 미가용이다."""
    from dartlab.gather.domains import fdr
    from dartlab.gather.types import SourceUnavailableError

    monkeypatch.setattr(fdr, "_available", lambda: False)

    with pytest.raises(SourceUnavailableError, match="설치되지 않았습니다"):
        asyncio.run(fdr.fetchHistory("AAPL"))


def test_fetch_history_provider_failure_preserves_cause(monkeypatch: pytest.MonkeyPatch) -> None:
    """DataReader 장애 원인을 SourceUnavailableError cause로 보존한다."""
    from dartlab.gather.domains import fdr
    from dartlab.gather.types import SourceUnavailableError

    def failDataReader(*args, **kwargs):
        raise OSError("provider down")

    monkeypatch.setattr(fdr, "_available", lambda: True)
    monkeypatch.setattr(fdr, "_loadCache", lambda *args: None)
    monkeypatch.setitem(sys.modules, "FinanceDataReader", types.SimpleNamespace(DataReader=failDataReader))

    with pytest.raises(SourceUnavailableError) as excInfo:
        asyncio.run(fdr.fetchHistory("AAPL"))

    assert isinstance(excInfo.value.__cause__, OSError)


def test_fetch_history_valid_empty_frame_returns_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    """정상 DataReader 응답의 empty frame은 빈 이력이다."""
    from dartlab.gather.domains import fdr

    emptyFrame = types.SimpleNamespace(empty=True)
    monkeypatch.setattr(fdr, "_available", lambda: True)
    monkeypatch.setattr(fdr, "_loadCache", lambda *args: None)
    monkeypatch.setitem(
        sys.modules,
        "FinanceDataReader",
        types.SimpleNamespace(DataReader=lambda *args, **kwargs: emptyFrame),
    )

    assert asyncio.run(fdr.fetchHistory("AAPL")) == []
