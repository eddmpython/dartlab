"""Expectation ledger IO : append-only invariants on tmp_path (pure unit, no network).

Covers:
- roundtrip: sealed spec rows survive parquet flatten/rehydrate byte-faithfully (specFromRow).
- append-only: a duplicate expectationId raises ValueError; score re-append is allowed.
- unscoredOnly: scored rows drop out of the due list.
- ledgerDir resolution: explicit baseDir wins over env / default.
"""

from __future__ import annotations

import pytest

from dartlab.simulate.expectationLedger import (
    appendExpectations,
    appendScores,
    ledgerDir,
    readExpectations,
    readScores,
    specFromRow,
)
from dartlab.synth.expectationSpec import ExpectationSpec, scoreExpectation

Q = {5: 1.0, 25: 2.0, 50: 3.0, 75: 4.0, 95: 5.0}


def makeSpec(eid: str = "macro.KR.TEST.M1@20260703T0900") -> ExpectationSpec:
    return ExpectationSpec(
        expectationId=eid,
        domain="macro",
        variable="KR.TEST",
        unit="level",
        freq="M",
        horizon=1,
        targetPeriod="2026-08",
        issuedAt="2026-07-03T09:00",
        issuedLive=False,
        asOf="2026-07-03",
        engine="macro.simulate.simulateMacro",
        engineVersion="bvar-v1",
        kind="quantiles",
        quantiles=dict(Q),
        baselines={"randomWalk": {5: 0.0, 25: 1.5, 50: 3.0, 75: 4.5, 95: 6.0}, "seasonalNaive": 3.5},
        sourceRefs=("hf://macro/ecos/CPI",),
        warnings=("backfill",),
    )


def test_roundtrip_and_rehydrate(tmp_path):
    spec = makeSpec()
    appendExpectations([spec], baseDir=tmp_path)
    df = readExpectations(baseDir=tmp_path)
    assert df is not None and df.height == 1
    back = specFromRow(df.row(0, named=True))
    assert back == spec  # frozen dataclass 동등성 = 봉인 내용 무손실


def test_duplicate_expectation_id_raises(tmp_path):
    spec = makeSpec()
    appendExpectations([spec], baseDir=tmp_path)
    with pytest.raises(ValueError, match="append-only"):
        appendExpectations([spec], baseDir=tmp_path)
    assert readExpectations(baseDir=tmp_path).height == 1  # 실패 append 는 흔적 0


def test_unscored_only_and_score_reappend(tmp_path):
    a, b = makeSpec("id.a@20260703T0900"), makeSpec("id.b@20260703T0900")
    appendExpectations([a, b], baseDir=tmp_path)
    s = scoreExpectation(a, 3.2, scoredAt="2026-08-05T00:00", actualAsOf="2026-08-05")
    appendScores([s], baseDir=tmp_path)
    due = readExpectations(baseDir=tmp_path, unscoredOnly=True)
    assert due.height == 1 and due.row(0, named=True)["expectationId"] == b.expectationId
    # 재채점(수정치 도착) = 새 행 append 허용
    appendScores([s], baseDir=tmp_path)
    assert readScores(baseDir=tmp_path).height == 2


def test_ledger_dir_resolution(tmp_path, monkeypatch):
    assert ledgerDir(tmp_path) == tmp_path
    monkeypatch.setenv("DARTLAB_DATA_DIR", str(tmp_path))
    assert ledgerDir() == tmp_path / "expectations"
    monkeypatch.delenv("DARTLAB_DATA_DIR")
    assert str(ledgerDir()).endswith("expectations")
