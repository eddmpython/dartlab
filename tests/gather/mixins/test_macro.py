"""dartlab.gather.mixins.macro real unit test (A 트랙 O3).

_GatherMacroMixin 의 _macroKR / _macroUS emit wrap 검증.
"""

from __future__ import annotations

import importlib

import pytest

pytestmark = pytest.mark.unit


def test_smoke_import() -> None:
    """``dartlab.gather.mixins.macro`` 모듈 import 가능 — 모듈 구조 회귀 차단."""
    importlib.import_module("dartlab.gather.mixins.macro")


def test_macroKR_propagates_failure_and_emits(monkeypatch: pytest.MonkeyPatch) -> None:
    """_macroKR 는 HF 실패를 전파하면서도 telemetry 를 발행한다."""
    from dartlab.gather.bulkData import macroHf as macroHfMod
    from dartlab.gather.engine import Gather
    from dartlab.gather.infra import telemetry as telemetryMod

    captured: list = []
    monkeypatch.setattr(telemetryMod, "_coreEmit", lambda k, **kw: captured.append((k, kw)))

    def boom(*a, **kw):
        raise RuntimeError("HF fail")

    monkeypatch.setattr(macroHfMod, "fetchMulti", boom)

    g = Gather()
    with pytest.raises(RuntimeError, match="HF fail"):
        g.macro("KR")

    axes = [kw["axis"] for k, kw in captured if k == "gather:fetch:done"]
    assert "macroKR" in axes or "macro" in axes


def test_macroUS_propagates_hf_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    from dartlab.gather.bulkData import macroHf
    from dartlab.gather.engine import Gather

    monkeypatch.setattr(macroHf, "fetchSeries", lambda *args, **kwargs: (_ for _ in ()).throw(OSError("offline")))

    with pytest.raises(OSError, match="offline"):
        Gather().macro("US", "GDP")


def test_macroGlobal_rejects_unknown_provider_prefix() -> None:
    from dartlab.gather.engine import Gather

    with pytest.raises(ValueError, match="prefix"):
        Gather().macro("GLOBAL", "UNKNOWN_SERIES")
