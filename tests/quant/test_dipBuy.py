"""Dip buy style의 Signal key 계약 회귀 테스트."""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np


def testDipBuyUsesRegisteredSnakeCaseSignalKeys(monkeypatch):
    from dartlab.quant.strategy.styles import dipBuy

    close = np.linspace(100.0, 180.0, 140)
    monkeypatch.setattr(dipBuy, "getArrays", lambda company: {"close": close})
    monkeypatch.setattr(dipBuy, "_regimeSeries", lambda values: {"state": np.full(len(values), 2)})

    rule = dipBuy.build(SimpleNamespace(stockCode="005930"))

    assert len(rule.entry_expr) == len(close)
    assert len(rule.exit_expr) == len(close)
    assert rule.meta["style"] == "dipBuy"
