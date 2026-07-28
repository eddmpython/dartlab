"""gather/batchProgress.py 미러 . 배치 워커 진행 표 조립."""

from __future__ import annotations

import pytest

from dartlab.gather.batchProgress import buildWorkerTable

pytestmark = pytest.mark.unit


def _render(table) -> str:
    from rich.console import Console

    console = Console(record=True, width=120, legacy_windows=False)
    console.print(table)
    return console.export_text()


def test_rendersOneRowPerWorkerPlusBar() -> None:
    """워커 수만큼 행 + bar 행 하나."""
    text = _render(buildWorkerTable(3, ["a", "b", "c"], 5, 10))
    assert "W0" in text and "W1" in text and "W2" in text
    assert "5/10 (50%)" in text


def test_barIsFiftyCellsWide() -> None:
    """bar 는 항상 50 칸이다."""
    text = _render(buildWorkerTable(1, ["x"], 0, 10))
    assert "░" * 50 in text


def test_zeroTotalDoesNotDivide() -> None:
    """total 이 0 이면 백분율은 0 이고 나눗셈 오류가 없다."""
    text = _render(buildWorkerTable(1, ["x"], 0, 0))
    assert "0/0 (0%)" in text


def test_bothBatchModulesShareOneBuilder() -> None:
    """DART 배치와 EDGAR 배치가 같은 함수 객체를 본다."""
    from dartlab.gather.dart import batch as dartBatch
    from dartlab.gather.edgar import batch as edgarBatch

    assert dartBatch.buildWorkerTable is buildWorkerTable
    assert edgarBatch.buildWorkerTable is buildWorkerTable
