"""screen 프리셋 테스트."""

import pytest

pytestmark = pytest.mark.unit

from dartlab.analysis.comparative.rank.screen import PRESETS, presets


class TestPresets:
    def test_presets_not_empty(self):
        p = presets()
        assert len(p) >= 7

    def test_presets_returns_description(self):
        p = presets()
        for name, desc in p.items():
            assert isinstance(name, str)
            assert isinstance(desc, str)
            assert len(desc) > 0

    def test_known_presets_exist(self):
        p = presets()
        assert "가치주" in p
        assert "성장주" in p
        assert "현금부자" in p

    def test_preset_structure(self):
        for name, preset in PRESETS.items():
            assert "label" in preset, f"{name}에 label 없음"
            assert "description" in preset, f"{name}에 description 없음"
            assert "conditions" in preset, f"{name}에 conditions 없음"
            assert isinstance(preset["conditions"], list)
            assert len(preset["conditions"]) > 0

    def test_preset_labels_unique(self):
        labels = [p["label"] for p in PRESETS.values()]
        assert len(labels) == len(set(labels))
