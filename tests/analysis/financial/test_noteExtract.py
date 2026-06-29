"""noteExtract.extractNoteView — 제네릭 노트 추출(composition/lineitem) 검증.

순수 피벗 로직은 _noteCellsFromPanel 을 monkeypatch fixture 로 unit. 실 panel 은 requires_data.
"""

from __future__ import annotations

import polars as pl
import pytest

from dartlab.analysis.financial.noteExtract import _isTotal, _memberName, extractNoteView


class _Co:
    def __init__(self, code: str = "005930", market: str = "KR") -> None:
        self.stockCode = code
        self.market = market


def _patchCells(monkeypatch, rows: list[dict]) -> None:
    df = pl.DataFrame(rows) if rows else pl.DataFrame()
    monkeypatch.setattr("dartlab.providers.dart.panel.cell._noteCellsFromPanel", lambda code, ck: df)


@pytest.mark.unit
class TestPure:
    def test_member_name(self) -> None:
        assert _memberName("ConsolidatedMember|entity001_DxDivisionMemberOfX") == "DxDivision"
        assert _memberName("ConsolidatedMember|PlanAssetsMember") == "PlanAssets"
        assert _memberName("ConsolidatedMember") is None
        assert _memberName(None) is None

    def test_is_total(self) -> None:
        assert _isTotal("합계")
        assert _isTotal("매출 합계")
        assert _isTotal("소계")
        assert not _isTotal("미국")


@pytest.mark.unit
class TestExtract:
    def test_lineitem_shares_and_total_drop(self, monkeypatch) -> None:
        rows = [
            {
                "scope": "consolidated",
                "axisPath": "ConsolidatedMember",
                "label": "미국",
                "ctxYear": 2025,
                "valueRaw": "60",
            },
            {
                "scope": "consolidated",
                "axisPath": "ConsolidatedMember",
                "label": "중국",
                "ctxYear": 2025,
                "valueRaw": "40",
            },
            {
                "scope": "consolidated",
                "axisPath": "ConsolidatedMember",
                "label": "합계",
                "ctxYear": 2025,
                "valueRaw": "100",
            },
        ]
        _patchCells(monkeypatch, rows)
        v = extractNoteView(_Co(), "NT_D831150", shape="lineitem")
        assert v is not None
        assert v["categories"] == ["미국", "중국"]  # 합계 드롭, 최신 비중 desc
        assert v["points"][0]["shares"] == [60.0, 40.0]
        assert v["points"][0]["period"] == "2025Q4"

    def test_composition_member_pivot_and_scope_filter(self, monkeypatch) -> None:
        rows = [
            {
                "scope": "consolidated",
                "axisPath": "ConsolidatedMember|entity1_AlphaMemberOfX",
                "label": "매출",
                "ctxYear": 2025,
                "valueRaw": "70",
            },
            {
                "scope": "consolidated",
                "axisPath": "ConsolidatedMember|entity1_BetaMemberOfX",
                "label": "매출",
                "ctxYear": 2025,
                "valueRaw": "30",
            },
            {
                "scope": "standalone",
                "axisPath": "ConsolidatedMember|entity1_AlphaMemberOfX",
                "label": "매출",
                "ctxYear": 2025,
                "valueRaw": "999",
            },
        ]
        _patchCells(monkeypatch, rows)
        v = extractNoteView(_Co(), "NT_D818000", shape="composition")
        assert v is not None
        assert v["categories"] == ["Alpha", "Beta"]  # 별도(standalone) 제외
        assert v["points"][0]["shares"] == [70.0, 30.0]

    def test_unsupported_shape_none(self) -> None:
        assert extractNoteView(_Co(), "NT_D822100", shape="movement") is None
        assert extractNoteView(_Co(), "NT_D822100", shape="flat") is None

    def test_us_market_none(self) -> None:
        assert extractNoteView(_Co(market="US"), "NT_D831150", shape="lineitem") is None

    def test_empty_cells_none(self, monkeypatch) -> None:
        _patchCells(monkeypatch, [])
        assert extractNoteView(_Co(), "NT_D831150", shape="lineitem") is None


@pytest.mark.requires_data
class TestRealData:
    def test_region_revenue_real(self) -> None:
        import dartlab

        v = extractNoteView(dartlab.Company("005930"), "NT_D831150", shape="lineitem")
        assert v is not None
        assert v["categories"]  # 지역(미국/중국/유럽…) 비공백
        assert all(0 <= s <= 100 for s in v["points"][-1]["shares"])
