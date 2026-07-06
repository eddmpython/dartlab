"""저장된 명명 스크린 레지스트리(screens/*.json) 테스트.

JSON SSOT 로드·목록·dispatch·flagship 스키마를 데이터 없이 검증한다.
"""

from __future__ import annotations

import json

import polars as pl
import pytest

from dartlab.scan.screen import _SCREENS_DIR, listScreens, loadScreen, scanScreen

pytestmark = pytest.mark.unit


def test_all_screen_files_valid():
    files = list(_SCREENS_DIR.glob("*.json"))
    assert files, "screens/*.json 없음"
    for p in files:
        d = json.loads(p.read_text(encoding="utf-8"))
        assert d.get("id") == p.stem, f"{p.name}: id 는 파일명과 일치해야 함"
        assert d.get("version"), f"{p.name}: version 필수"
        assert isinstance(d.get("spec"), dict), f"{p.name}: spec dict 필수"


def test_listScreens_includes_flagship():
    ids = {s["id"] for s in listScreens()}
    assert "financialStabilityDrawdown" in ids
    row = next(s for s in listScreens() if s["id"] == "financialStabilityDrawdown")
    assert row["title"] and "safety" in row["tags"]


def test_loadScreen_returns_spec():
    spec = loadScreen("financialStabilityDrawdown")
    assert "netCash" in spec["define"]
    assert isinstance(spec["where"], list) and len(spec["where"]) >= 3
    assert spec["sort"]["field"] == "@netCash"


def test_loadScreen_unknown_raises():
    with pytest.raises(ValueError, match="알 수 없는 저장 스크린"):
        loadScreen("존재하지않는스크린xyz")


def test_scanScreen_none_lists_presets_and_saved():
    df = scanScreen(verbose=False)
    presets = set(df["preset"].to_list())
    assert "value" in presets  # 하드코딩 프리셋 보존
    assert "financialStabilityDrawdown" in presets  # 저장 스크린 노출


def test_scanScreen_saved_id_executes(monkeypatch):
    import dartlab.scan.builders.kr.fields as fmod

    captured = {}

    def fake(spec):
        captured["spec"] = spec
        return pl.DataFrame({"stockCode": ["X"]})

    monkeypatch.setattr(fmod, "executeScreenSpec", fake)
    out = scanScreen("financialStabilityDrawdown", verbose=False)
    assert out.height == 1
    assert "define" in captured["spec"] and "where" in captured["spec"]


def test_scanScreen_unknown_target_raises():
    with pytest.raises(ValueError, match="알 수 없는 저장 스크린"):
        scanScreen("존재하지않는것xyz", verbose=False)
