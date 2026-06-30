"""DART panel text helper tests."""

from __future__ import annotations

import re

import polars as pl
import pytest

from dartlab.providers.dart.panel import text as textMod
from dartlab.providers.dart.panel.text import gridToRowDicts, parsePanelXmlTables

# ROWSPAN=2 COLSPAN=2 "부문" + 후속 행이 셀 부족 → 기존 zip 이 밀리던 패턴 재현.
_RAW_SPAN = """
<TABLE>
<THEAD><TR>
<TH COLSPAN="2">부문</TH><TH>품목</TH><TH>매입액</TH><TH>비중</TH><TH>매입처</TH>
</TR></THEAD>
<TBODY>
<TR>
<TD ROWSPAN="2" COLSPAN="2">CE부문</TD><TD>디스플레이</TD><TD>21,647</TD><TD>10.2%</TD><TD>CSOT 등</TD>
</TR>
<TR>
<TD>메모리</TD><TD>19,930</TD><TD>9.4%</TD><TD>Micron 등</TD>
</TR>
</TBODY>
</TABLE>
"""


def test_parse_panel_xml_tables_extracts_cell_text() -> None:
    content = """
    <TABLE>
      <TR><TH>계정</TH><TH>금액</TH></TR>
      <TR><TD>매출액</TD><TD>100</TD></TR>
    </TABLE>
    """

    assert textMod.parsePanelXmlTables(content) == [[["계정", "금액"], ["매출액", "100"]]]


def test_panel_text_wide_reads_panel_long(monkeypatch) -> None:
    df = pl.DataFrame(
        {
            "sectionLeaf": ["사업의 개요", "사업의 개요"],
            "contentRaw": ["<P>첫 문장</P>", "<P>둘째 문장</P>"],
            "period": ["2024Q4", "2024Q4"],
            "chapter": ["II. 사업의 내용", "II. 사업의 내용"],
            "disclosureKey": [None, None],
            "blockOrder": [1, 2],
            "rceptNo": ["202503310001", "202503310001"],
        }
    )

    def fakeReadLong(code: str, *, marketNs: str, periods: list[str] | None = None) -> pl.DataFrame:
        assert code == "005930"
        assert marketNs == "kr"
        assert periods == ["2024Q4"]
        return df

    monkeypatch.setattr("dartlab.providers.dart.panel.read.readLong", fakeReadLong)

    wide = textMod.panelTextWide("005930", periods=["2024Q4"])

    assert wide is not None
    assert wide.select("topic").to_series().to_list() == ["사업의 개요"]
    assert wide.select("source").to_series().to_list() == ["panel"]
    assert "첫 문장" in wide.select("2024Q4").item()


@pytest.mark.unit
class TestSpanGrid:
    def test_rectangular_no_ragged(self) -> None:
        grids = parsePanelXmlTables(_RAW_SPAN)
        assert len(grids) == 1
        assert len({len(r) for r in grids[0]}) == 1  # 직사각 (밀림 0)

    def test_alignment_fix(self) -> None:
        rows = gridToRowDicts(parsePanelXmlTables(_RAW_SPAN)[0])
        assert len(rows) == 2
        r2 = rows[1]  # "메모리" 행. 기존 버그면 매입액/비중/매입처가 한 칸씩 밀림
        assert r2["부문"] == "CE부문"  # rowspan forward-fill
        assert r2["품목"] == "메모리"
        assert r2["매입액"] == "19,930"
        assert r2["비중"] == "9.4%"  # 밀렸으면 "Micron 등" 이 들어옴
        assert r2["매입처"] == "Micron 등"

    def test_grid_to_row_dicts_collapse(self) -> None:
        assert gridToRowDicts([["부문", "부문", "품목"], ["CE", "CE", "A"]]) == [{"부문": "CE", "품목": "A"}]

    def test_header_row_param(self) -> None:
        g = [["(단위: 억원)", "(단위: 억원)"], ["품목", "매입액"], ["A", "10"]]
        assert gridToRowDicts(g, headerRow=1) == [{"품목": "A", "매입액": "10"}]

    def test_empty_and_broken(self) -> None:
        assert parsePanelXmlTables("") == []
        assert parsePanelXmlTables("<TABLE><TR><TD>x</TD></TR></TABLE>") == []  # 1행 = 표 아님
        assert gridToRowDicts([]) == []


@pytest.mark.requires_data
class TestSpanGridRealPanel:
    def test_samsung_rawmaterial_alignment(self) -> None:
        """실 005930 원재료 표. 격자전개로 직사각 정렬 + 매입액 열 숫자 확인."""
        from dartlab.providers.dart.panel.read import readLong

        df = readLong("005930", marketNs="kr")
        df = df.filter(pl.col("sectionLeaf").fill_null("").str.contains("원재료|생산"))

        target = None
        for cr in df["contentRaw"].to_list():
            if cr and "매입액" in cr and "비중" in cr and re.search(r"(?i)rowspan", cr):
                target = cr
                break
        assert target is not None, "원재료 매입 표(rowspan) 미발견"

        grids = parsePanelXmlTables(target)
        assert grids, "표 전개 실패"
        for g in grids:
            assert len({len(r) for r in g}) == 1, "ragged 잔존"

        rows = gridToRowDicts(grids[0])
        assert rows, "row dict 변환 실패"
        assert len({frozenset(r) for r in rows}) == 1, "행마다 키 다름(밀림 잔존)"
        amtKey = next((k for k in rows[0] if "매입액" in k), None)
        assert amtKey, f"매입액 헤더 부재: {list(rows[0])}"
        numeric = sum(1 for r in rows if re.fullmatch(r"[\d,]+", (r[amtKey] or "").strip()))
        assert numeric >= len(rows) // 2, f"매입액 열 숫자 적음(밀림 의심): {[r[amtKey] for r in rows]}"
