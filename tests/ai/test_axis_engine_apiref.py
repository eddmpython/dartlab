"""gather 표준 {engine}.{axis} apiRef — 카탈로그 등록 + EngineCall 통합 디스패치.

axis-engine(gather/scan/macro/industry/quant/credit) 의 축이 ``{engine}.{axis}`` 점 호출명으로
capability 카탈로그에 균질 등록되고, EngineCall 이 동일 경로로 실행한다(gather.price·industry.theme
모두 — 옛날엔 gather.{axis} 가 카탈로그-only 였음).
"""

from __future__ import annotations

import pytest

from dartlab.ai.tools.engineCall import engineCall
from dartlab.reference.capability import loadCapabilities


def test_axis_engines_registered_uniformly():
    """전 axis-engine 축이 {engine}.{axis} 로 카탈로그 등록."""
    caps = loadCapabilities()
    for ref in (
        "gather.price",
        "scan.growth",
        "industry.theme",
        "industry.summary",
        "credit.grade",
        "quant.indicators",
    ):
        assert ref in caps, f"{ref} 미등록"


@pytest.mark.requires_data
def test_engine_call_dispatches_axis_uniformly():
    """EngineCall {engine}.{axis} 통합 디스패치 — industry.theme·gather.price 모두 실행."""
    r1 = engineCall({"apiRef": "industry.theme", "args": {"stockCode": "051910"}})
    assert r1.ok and r1.data.get("rowCount") is not None

    r2 = engineCall({"apiRef": "industry.summary", "args": {"target": "semiconductor"}})
    assert r2.ok

    r3 = engineCall({"apiRef": "gather.price", "args": {"target": "005930"}})
    assert r3.ok  # 옛날엔 unsupported 였던 gather.{axis} 가 이제 실행


def test_analysis_axis_passes_target_as_stockcode_keyword(monkeypatch):
    import dartlab
    from dartlab.ai.tools.engineCall import _axisEngineCall

    captured = {}

    def fakeAnalysis(axis, **kwargs):
        captured["axis"] = axis
        captured["kwargs"] = kwargs
        return {"status": "usable", "value": 1}

    monkeypatch.setattr(dartlab, "analysis", fakeAnalysis)
    result = _axisEngineCall("analysis", "profitability", {"target": "005930"})

    assert result.ok is True
    assert captured == {"axis": "profitability", "kwargs": {"stockCode": "005930"}}


def test_analysis_axis_rejects_calc_list_instead_of_claiming_execution(monkeypatch):
    import polars as pl

    import dartlab
    from dartlab.ai.tools.engineCall import _axisEngineCall

    monkeypatch.setattr(dartlab, "analysis", lambda axis, **kwargs: pl.DataFrame({"항목": [axis]}))

    result = _axisEngineCall("analysis", "profitability", {"target": "005930"})

    assert result.ok is False
    assert result.error == "analysis_not_executed"
