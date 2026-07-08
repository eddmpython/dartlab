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
