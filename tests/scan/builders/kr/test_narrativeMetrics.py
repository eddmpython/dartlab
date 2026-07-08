"""buildNarrativeMetrics 프리빌드 테스트. panel 부재 폴백·Safe wrapper 예외흡수.

데이터 없이 빌더의 무회귀 경로(panel 없음 None, Safe 흡수)를 검증한다.
"""

from __future__ import annotations

import pytest

import dartlab.scan.builders.kr.narrativeMetrics as b

pytestmark = pytest.mark.unit


def test_no_panel_dir_returns_none(monkeypatch, tmp_path):
    monkeypatch.setattr(b, "_panelDir", lambda: tmp_path / "does_not_exist")
    assert b.buildNarrativeMetrics(verbose=False) is None


def test_empty_panel_dir_returns_none(monkeypatch, tmp_path):
    (tmp_path / "panel").mkdir()
    monkeypatch.setattr(b, "_panelDir", lambda: tmp_path / "panel")
    assert b.buildNarrativeMetrics(verbose=False) is None


def test_safe_wrapper_absorbs_error(monkeypatch):
    def _boom(*a, **k):
        raise OSError("build failed")

    monkeypatch.setattr(b, "buildNarrativeMetrics", _boom)
    assert b.buildNarrativeMetricsSafe(verbose=False) is None


def test_safe_wrapper_passthrough(monkeypatch):
    monkeypatch.setattr(b, "buildNarrativeMetrics", lambda *, verbose=True: "OK")
    assert b.buildNarrativeMetricsSafe(verbose=False) == "OK"


def test_drop_absurd_backlog(monkeypatch):
    import importlib

    import polars as pl

    sa = importlib.import_module("dartlab.providers.dart.finance.scanAccount")
    # 매출 1조 종목. A=500조(단위오류 이상치), B=3조(정상 조선급)
    monkeypatch.setattr(
        sa, "scanAccount", lambda name, freq="Y": pl.DataFrame({"stockCode": ["A", "B"], "2024": [1e12, 1e12]})
    )
    df = pl.DataFrame({"stockCode": ["A", "B"], "backlog": [5e14, 3e12], "backlog_conf": ["high", "high"]})
    out = b._dropAbsurdBacklog(df, verbose=False)
    d = {r["stockCode"]: (r["backlog"], r["backlog_conf"]) for r in out.iter_rows(named=True)}
    assert d["A"] == (None, None)  # 500조 > 매출 1조 x 30 -> gap
    assert d["B"] == (3e12, "high")  # 3조 < 매출 1조 x 30 -> 유지


def test_drop_absurd_no_sales_keeps(monkeypatch):
    import importlib

    import polars as pl

    sa = importlib.import_module("dartlab.providers.dart.finance.scanAccount")
    # 매출 부재 -> 검증 불가 -> 보존
    monkeypatch.setattr(sa, "scanAccount", lambda name, freq="Y": pl.DataFrame({"stockCode": [], "2024": []}))
    df = pl.DataFrame({"stockCode": ["A"], "backlog": [5e14], "backlog_conf": ["mid"]})
    out = b._dropAbsurdBacklog(df, verbose=False)
    assert out["backlog"][0] == 5e14
