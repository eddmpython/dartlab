"""fillEdgarAllFilingsContent.selectDays 계약. forward(최신) + backfill(과거) 미충전일 선정. 순수 함수.

스크립트라 importlib 경유. 네트워크/HF 무관.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

_SCRIPT = Path(__file__).resolve().parents[3] / ".github" / "scripts" / "sync" / "fillEdgarAllFilingsContent.py"


def _module():
    spec = importlib.util.spec_from_file_location("fillEdgarAllFilingsContentForTest", _SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _selectDays():
    return _module().selectDays


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


# ─── 시간 예산 (2026-09-01: 매 run 이 timeout cancelled 로 끝나 감시에 실패로 보이던 것) ───


def test_fill_days_stops_starting_new_days_after_budget():
    """예산이 지나면 새 날짜를 시작하지 않는다. 시작한 날짜는 끝까지 간다."""
    fillDays = _module().fillDays
    now = [0.0]
    filled: list[str] = []

    def fillDay(day: str) -> None:
        filled.append(day)
        now[0] += 30.0  # 하루치 30 초

    done = fillDays(["d1", "d2", "d3", "d4"], fillDay, budgetSeconds=50.0, clock=lambda: now[0])
    # 0s: d1 시작(예산 안) -> 30s: d2 시작(예산 안) -> 60s: 예산 초과, d3 미착수
    assert done == ["d1", "d2"]
    assert filled == ["d1", "d2"]


def test_fill_days_finishes_all_when_budget_remains():
    """예산이 남으면 todo 를 전부 처리한다."""
    fillDays = _module().fillDays
    assert fillDays(["a", "b"], lambda day: None, budgetSeconds=60.0) == ["a", "b"]


def test_workflow_passes_budget_below_job_timeout():
    """workflow 의 예산(분) + 실측 최장 하루치가 job timeout 안에 들어야 timeout cancelled 가 사라진다."""
    import re

    workflow = (_SCRIPT.parents[2] / "workflows" / "edgarFilingsContentSync.yml").read_text(encoding="utf-8")
    timeout = int(re.search(r"timeout-minutes:\s*(\d+)", workflow).group(1))
    budget = float(re.search(r"--budget-minutes\s+(\d+)", workflow).group(1))
    longestDayMinutes = 55  # 2026-08-31 run 실측 최장 53.5 분(20251202) + 여유
    assert budget + longestDayMinutes < timeout, f"예산 {budget} + 하루치 {longestDayMinutes} >= timeout {timeout}"
