"""recordForecast write-end : 봉인 저장 roundtrip + 저장 경로 승격(A2) 검증.

scenario-simulator 09 §10.2 P9b/P9c 티켓 게이트. ~/.dartlab ephemeral 폐기 후
DARTLAB_DATA_DIR redirect 가 실제로 동작하고, write→load→evaluate 루프가 닫힘을 고정한다.
"""

from __future__ import annotations

from pathlib import Path

from dartlab.analysis.forecast.forwardTest import evaluate, loadRecords, recordForecast


def test_forwardTestWrite_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("DARTLAB_DATA_DIR", str(tmp_path))
    p = recordForecast(
        stockCode="005930",
        horizon=3,
        projected=[110.0, 120.0, 130.0],
        scenarios={"base": [110.0, 120.0, 130.0], "bull": [125.0, 140.0, 155.0], "bear": [95.0, 100.0, 105.0]},
        sourcesUsed=["timeseries"],
        assumptions=["단위 테스트 봉인"],
        directionProbability=0.7,
        directionPredicted="up",
    )
    assert p == tmp_path / "forwardTests" / "005930.json"  # ~/.dartlab 아님 (A2 redirect)
    records = loadRecords("005930")
    assert len(records) == 1
    r = records[0]
    assert r.projected == [110.0, 120.0, 130.0] and r.directionProbability == 0.7
    ev = evaluate(r, [112.0, 118.0, 131.0])
    assert isinstance(ev, dict) and ev  # 사후 평가 루프 닫힘


def test_default_dir_is_data_not_home(monkeypatch):
    monkeypatch.delenv("DARTLAB_DATA_DIR", raising=False)
    from dartlab.analysis.forecast.forwardTest import _forwardTestDir

    d = _forwardTestDir()
    assert d == Path("data") / "forwardTests"
    assert ".dartlab" not in str(d)
