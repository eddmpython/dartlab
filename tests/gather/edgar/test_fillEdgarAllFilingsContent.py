"""fillEdgarAllFilingsContent.selectDays 계약. forward(최신) + backfill(과거) 미충전일 선정. 순수 함수.

스크립트라 importlib 경유. 네트워크/HF 무관.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

_SCRIPT = Path(__file__).resolve().parents[3] / ".github" / "scripts" / "sync" / "fillEdgarAllFilingsContent.py"


def _selectDays():
    spec = importlib.util.spec_from_file_location("fillEdgarAllFilingsContentForTest", _SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.selectDays


def test_forward_newest_plus_backfill_oldest():
    """최신 forwardDays(피드 신선도) + 오래된 미충전(backfill), 합 maxDays."""
    selectDays = _selectDays()
    allDays = [f"2026010{i}" for i in range(1, 10)]  # 20260101..20260109
    done = {"20260105"}  # 하나만 충전됨
    got = selectDays(allDays, done, maxDays=4, forwardDays=2)
    # forward = 최신 미충전 2일(20260108,20260109), backfill = 오래된 미충전(20260101,20260102)
    assert got == ["20260108", "20260109", "20260101", "20260102"]


def test_empty_when_all_done():
    """전 일자 충전 완료면 빈 리스트."""
    selectDays = _selectDays()
    allDays = ["20260101", "20260102"]
    assert selectDays(allDays, {"20260101", "20260102"}, maxDays=10, forwardDays=3) == []


def test_backfill_only_when_forward_zero():
    """forwardDays=0 이면 오래된 것부터(순수 backfill)."""
    selectDays = _selectDays()
    allDays = ["20260101", "20260102", "20260103"]
    assert selectDays(allDays, set(), maxDays=2, forwardDays=0) == ["20260101", "20260102"]
