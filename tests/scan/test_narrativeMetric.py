"""scan narrativeMetric 축(reader) 테스트. 빈프레임 스키마·축 등록·no-file 폴백.

파일 부재 시 빈 프레임(축 무회귀) + 라우터 등록을 데이터 없이 검증한다.
"""

from __future__ import annotations

import pytest

from dartlab.scan.narrativeMetric import _READ_SCHEMA, _emptyFrame, scanNarrativeMetric

pytestmark = pytest.mark.unit


def test_empty_frame_schema():
    df = _emptyFrame()
    assert df.height == 0
    assert set(df.columns) == set(_READ_SCHEMA)
    assert "backlog" in df.columns and "utilizationRate_conf" in df.columns


def test_axis_registered():
    from dartlab.scan.router import _AXIS_REGISTRY

    assert "narrativeMetric" in _AXIS_REGISTRY
    entry = _AXIS_REGISTRY["narrativeMetric"]
    assert entry.fn == "scanNarrativeMetric"
    assert entry.module == "dartlab.scan.narrativeMetric"


def test_aliases_resolve():
    from dartlab.scan.router import _ALIASES

    for alias in ("수주잔고", "백로그", "가동률"):
        assert _ALIASES.get(alias) == "narrativeMetric"


def test_no_file_returns_empty(monkeypatch, tmp_path):
    import dartlab.scan.narrativeMetric as m

    def _boom(_scanDir, _rel):
        raise OSError("no file")

    monkeypatch.setattr(m, "_ensureScanData", lambda: tmp_path)
    monkeypatch.setattr(m, "_downloadScanFile", _boom)
    df = scanNarrativeMetric(verbose=False)
    assert df.height == 0
    assert set(df.columns) == set(_READ_SCHEMA)
