"""lensSummary 투영 단위 가드 (순수 함수, 데이터 불요)."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit

from dartlab.story.lensProducts import lensSummary


def _product() -> dict:
    return {
        "status": "ok",
        "conclusion": {"label": "양호", "summary": "현금흐름이 이익을 따라간다"},
        "confidence": {"level": "high", "score": 0.82},
        "time": {"asOf": "2026-07-28", "dataAsOf": "2026-03-31", "period": "2026Q1"},
    }


class TestLensSummary:
    def test_projects_direct_fields(self):
        rows = lensSummary({"analysis": _product()})
        assert len(rows) == 1
        row = rows[0]
        assert row["engine"] == "analysis"
        assert row["status"] == "ok"
        assert row["label"] == "양호"
        assert row["summary"] == "현금흐름이 이익을 따라간다"
        assert row["confidenceLevel"] == "high"
        assert row["confidenceScore"] == pytest.approx(0.82)
        assert row["asOf"] == "2026-07-28"
        assert row["period"] == "2026Q1"

    def test_missing_nested_blocks_become_none(self):
        """결론·신뢰도·시점 블록이 없어도 행은 나오고 값만 빈다."""
        rows = lensSummary({"analysis": {"status": "empty"}})
        assert rows[0]["status"] == "empty"
        assert rows[0]["label"] is None
        assert rows[0]["confidenceScore"] is None
        assert rows[0]["asOf"] is None

    def test_non_dict_input_is_empty(self):
        assert lensSummary(None) == []
        assert lensSummary([]) == []
        assert lensSummary({"analysis": "not a dict"}) == []

    def test_engine_order_is_stable(self):
        """행 순서는 입력 dict 순서가 아니라 엔진 정렬 순서다."""
        rows = lensSummary({"credit": _product(), "analysis": _product()})
        engines = [r["engine"] for r in rows]
        assert engines == sorted(engines, key=lambda e: engines.index(e))
        assert set(engines) == {"credit", "analysis"}
        assert len(rows) == 2
