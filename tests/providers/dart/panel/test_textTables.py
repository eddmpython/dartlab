"""panel 표 읽기 세 함수 단위 가드.

``panelLatestPeriod`` 는 게임 IP 매출 표가 여러 해치로 뒤엉키던 것을 막으려고 둔
헬퍼다. 여러 기간의 표를 한 덩어리로 붙여 놓고 첫 행을 머리로 삼으면 합계가 어긋난다.
"""

from __future__ import annotations

from unittest.mock import patch

import polars as pl
import pytest

pytestmark = pytest.mark.unit

from dartlab.providers.dart.panel.text import (
    gridToRowDicts,
    panelLatestPeriod,
    panelTableRows,
    panelXmlTables,
)

_TABLE_XML = "<TABLE><TR><TD>품목</TD><TD>제30기</TD></TR><TR><TD>리니지</TD><TD>99,826</TD></TR></TABLE>"


def _long(periods: list[str], contents: list[str], leaves: list[str]) -> pl.DataFrame:
    return pl.DataFrame({"period": periods, "contentRaw": contents, "sectionLeaf": leaves})


class TestPanelLatestPeriod:
    def test_picks_max_period(self):
        df = _long(
            ["2024Q4", "2026Q1", "2025Q2"],
            [_TABLE_XML] * 3,
            ["2. 주요 제품 및 서비스"] * 3,
        )
        with patch("dartlab.providers.dart.panel.read.readLong", return_value=df):
            assert panelLatestPeriod("036570", sectionPattern="제품") == "2026Q1"

    def test_section_filter_narrows_periods(self):
        """섹션에 본문이 없는 기간은 후보가 아니다."""
        df = _long(
            ["2026Q1", "2025Q4"],
            [_TABLE_XML] * 2,
            ["4. 매출 및 수주상황", "2. 주요 제품 및 서비스"],
        )
        with patch("dartlab.providers.dart.panel.read.readLong", return_value=df):
            assert panelLatestPeriod("036570", sectionPattern="제품") == "2025Q4"

    def test_no_rows_is_none(self):
        empty = pl.DataFrame({"period": [], "contentRaw": [], "sectionLeaf": []}, schema_overrides=None)
        with patch("dartlab.providers.dart.panel.read.readLong", return_value=empty):
            assert panelLatestPeriod("036570") is None
        with patch("dartlab.providers.dart.panel.read.readLong", return_value=None):
            assert panelLatestPeriod("036570") is None


class TestPanelXmlTables:
    def test_extracts_table_grid(self):
        df = _long(["2026Q1"], [_TABLE_XML], ["2. 주요 제품 및 서비스"])
        with patch("dartlab.providers.dart.panel.read.readLong", return_value=df):
            grids = panelXmlTables("036570", sectionPattern="제품", period="2026Q1")
        assert len(grids) == 1
        assert grids[0][0] == ["품목", "제30기"]
        assert grids[0][1] == ["리니지", "99,826"]

    def test_rows_without_table_markup_are_skipped(self):
        df = _long(["2026Q1"], ["본문 문단이라 표가 없다"], ["2. 주요 제품 및 서비스"])
        with patch("dartlab.providers.dart.panel.read.readLong", return_value=df):
            assert panelXmlTables("036570", sectionPattern="제품") == []


class TestPanelTableRows:
    def test_flattens_by_header(self):
        df = _long(["2026Q1"], [_TABLE_XML], ["2. 주요 제품 및 서비스"])
        with patch("dartlab.providers.dart.panel.read.readLong", return_value=df):
            rows = panelTableRows("036570", sectionPattern="제품", period="2026Q1")
        assert rows == [{"품목": "리니지", "제30기": "99,826"}]

    def test_empty_panel_gives_empty_list(self):
        with patch("dartlab.providers.dart.panel.read.readLong", return_value=None):
            assert panelTableRows("036570") == []


class TestGridToRowDicts:
    def test_header_row_becomes_keys(self):
        grid = [["품목", "매출액"], ["리니지", "99,826"]]
        assert gridToRowDicts(grid) == [{"품목": "리니지", "매출액": "99,826"}]
