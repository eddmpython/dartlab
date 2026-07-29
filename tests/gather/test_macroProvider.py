"""dartlab.gather.macroProvider — smoke import + ``.macro`` 계약 가드.

2026-06-12 회귀: getDefaultGather 가 ``.macro`` 메서드 없는 GatherEntry 를 반환하자
L2 macro 전역(seriesFetch·cycle·quadrant)의 AttributeError 가 도처의 예외 흡수에
삼켜져 "신호부족·quadrant 생략·us cycle 미생성"으로 침묵 사망했다. 본 가드는 그
계약(반환 객체가 호출 가능한 ``.macro`` 보유)을 PR 단계에서 차단한다.
"""

from __future__ import annotations

import importlib

import pytest

pytestmark = pytest.mark.unit


def test_smoke_import() -> None:
    """``dartlab.gather.macroProvider`` 모듈 import 가능 — 모듈 구조 회귀 차단."""
    importlib.import_module("dartlab.gather.macroProvider")


def test_default_gather_has_macro_method() -> None:
    """getDefaultGather 반환 객체는 ``.macro`` 메서드 계약 — L2 macro 침묵 사망 회귀 가드."""
    from dartlab.gather.macroProvider import DefaultMacroProvider

    g = DefaultMacroProvider().getDefaultGather()
    assert hasattr(g, "macro") and callable(g.macro), (
        "getDefaultGather 반환 객체에 .macro 메서드가 없다 — GatherEntry(축 callable)로 "
        "바꾸면 L2 macro(seriesFetch·cycle·quadrant)가 예외 흡수 아래 침묵 사망한다 (2026-06-12 실측)."
    )


def test_apply_as_of_requires_date_column() -> None:
    import polars as pl

    from dartlab.gather.macroProvider import DefaultMacroProvider

    with pytest.raises(KeyError, match="date"):
        DefaultMacroProvider().applyAsOf(pl.DataFrame({"value": [1.0]}), "2026-01-01")


def test_latest_propagates_provider_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    from dartlab.gather.macroProvider import DefaultMacroProvider

    class BrokenGather:
        @staticmethod
        def macro(series_id: str):
            raise RuntimeError(f"{series_id} unavailable")

    provider = DefaultMacroProvider()
    monkeypatch.setattr(provider, "getDefaultGather", lambda: BrokenGather())

    with pytest.raises(RuntimeError, match="GDP unavailable"):
        provider.fetchSeriesLatest("GDP")
