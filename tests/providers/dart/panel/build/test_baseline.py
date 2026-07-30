"""``providers/dart/panel/build/baseline.py``의 공개 기준선 mirror."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def test_build_panel_baseline_is_public() -> None:
    """기준선 오케스트레이터는 build 패키지 공개표면에서 노출된다."""

    from dartlab.providers.dart.panel.build import buildPanelBaseline

    assert callable(buildPanelBaseline)
