"""panel build/cell mirror — ACONTEXT 분해 + XBRL/옛 표 셀 추출 (인라인 합성 contentRaw, 데이터 0).

``build/cell.py`` 의 ``decodeAcontext``/``_parseAmount``/``_detectUnit``/``cellsFromContent``(XBRL+옛
분기). 실 panel.parquet contentRaw 라운드트립은 tests/panel (requires_data) 담당.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def test_decode_acontext_deterministic() -> None:
    """ACONTEXT period 토큰 → (year, flow, quarter, mode) 결정론 분해 (전 분기 marker)."""
    from dartlab.providers.dart.panel.build.cell import decodeAcontext

    base = "_ifrs-full_X_ifrs-full_ConsolidatedMember"
    assert decodeAcontext("CFY2025dFY" + base) == (2025, "d", 4, "Y", "ConsolidatedMember")
    assert decodeAcontext("BPFY2023eFY" + base) == (2023, "e", 4, "Y", "ConsolidatedMember")
    assert decodeAcontext("CFY2025dTQA" + base) == (2025, "d", 3, "A", "ConsolidatedMember")
    assert decodeAcontext("CFY2025dTQQ" + base) == (2025, "d", 3, "Q", "ConsolidatedMember")
    assert decodeAcontext("CFY2025dFQA" + base) == (2025, "d", 1, "A", "ConsolidatedMember")
    assert decodeAcontext("CFY2025dFQQ" + base) == (2025, "d", 1, "Q", "ConsolidatedMember")
    assert decodeAcontext("CFY2025dHYA" + base) == (2025, "d", 2, "A", "ConsolidatedMember")
    assert decodeAcontext("PFY2024eFQ" + base) == (2024, "e", 1, "P", "ConsolidatedMember")
    assert decodeAcontext("garbage") is None
    assert decodeAcontext("") is None


def test_marker_to_quarter_mode() -> None:
    """marker → (분기, 모드). FQ=1·HY=2·TQ=3·FY=연간(4), 접미 A/Q, bare=P."""
    from dartlab.providers.dart.panel.build.cell import _markerToQuarterMode

    assert _markerToQuarterMode("FY") == (4, "Y")
    assert _markerToQuarterMode("FQA") == (1, "A")
    assert _markerToQuarterMode("FQQ") == (1, "Q")
    assert _markerToQuarterMode("FQ") == (1, "P")
    assert _markerToQuarterMode("HYA") == (2, "A")
    assert _markerToQuarterMode("TQQ") == (3, "Q")
    assert _markerToQuarterMode("TQ") == (3, "P")


def test_axis_members_strip_standard_prefix() -> None:
    """축 멤버에서 ifrs-full_/dart_ prefix 벗기고 entity 는 보존."""
    from dartlab.providers.dart.panel.build.cell import _axisMembers

    segs = "ifrs-full_ConsolidatedAndSeparateFinancialStatementsAxis_ifrs-full_ConsolidatedMember".split("_")
    assert _axisMembers(segs) == ["ConsolidatedMember"]
    segs2 = "ifrs-full_Ax_entity00126380_FooClassMemberOfBarTableOfMember".split("_")
    assert _axisMembers(segs2) == ["entity00126380_FooClassMemberOfBarTableOfMember"]


def test_parse_amount() -> None:
    """금액 파싱 — △/괄호 음수, 콤마, (주N)/비숫자 None."""
    from dartlab.providers.dart.panel.build.cell import _parseAmount

    assert _parseAmount("200,653,482") == 200653482.0
    assert _parseAmount("△500") == -500.0
    assert _parseAmount("(1,234)") == -1234.0
    assert _parseAmount("(주30)") is None
    assert _parseAmount("매출액") is None
    assert _parseAmount("") is None


def test_detect_unit() -> None:
    """단위 감지 — 백만원/천원/원, 미발견 백만원 기본."""
    from dartlab.providers.dart.panel.build.cell import _detectUnit

    assert _detectUnit("(단위 : 백만원)") == 1_000_000
    assert _detectUnit("단위:천원") == 1_000
    assert _detectUnit("단위 : 원") == 1
    assert _detectUnit("매출액 표") == 1_000_000


# XBRL era contentRaw (ACONTEXT 박힘) — 한 5표 row 의 표 XML
_XBRL_CONTENT = """<TITLE>연결 손익계산서</TITLE><TABLE><TR>
  <TE>매출액 (주30)</TE>
  <TE ACODE="ifrs-full_Revenue" ACONTEXT="CFY2025dFY_ifrs-full_Ax_ifrs-full_ConsolidatedMember">100</TE>
  <TE ACODE="ifrs-full_Revenue" ACONTEXT="PFY2024dFY_ifrs-full_Ax_ifrs-full_ConsolidatedMember">90</TE>
</TR></TABLE>"""

# 옛 era contentRaw (ACONTEXT 없음, TD 표) — 첫 셀 항목명 + 당기/전기/전전기
_OLD_CONTENT = """<TABLE><TR>
  <TD><P>제 47 기</P></TD></TR><TR>
  <TD><P>수익(매출액)</P></TD>
  <TD ALIGN="RIGHT"><P>200,653,482</P></TD>
  <TD ALIGN="RIGHT"><P>206,205,987</P></TD>
  <TD ALIGN="RIGHT"><P>228,692,667</P></TD>
</TR></TABLE>"""


def test_cells_from_content_xbrl() -> None:
    """ACONTEXT 있는 contentRaw → XBRL 정밀 셀 (acode, label 동거, ctxYear)."""
    from dartlab.providers.dart.panel.build.cell import cellsFromContent

    rows = list(
        cellsFromContent(
            _XBRL_CONTENT, statement="IS2", scope="consolidated", period="2025Q4", code="005930", rcept="R1"
        )
    )
    rev = [r for r in rows if r["acode"] == "ifrs-full_Revenue"]
    assert len(rev) == 2  # CFY 2025 + PFY 2024
    assert all(r["label"] == "매출액 (주30)" for r in rev)
    assert {r["ctxYear"] for r in rev} == {2025, 2024}
    assert rev[0]["valueRaw"] == "100"


def test_parse_old_statement_table() -> None:
    """ACONTEXT 없는 옛 표 → 위치 파싱 (당기/전기/전전기 = ctxYear, acode=None)."""
    from dartlab.providers.dart.panel.build.cell import cellsFromContent

    rows = list(
        cellsFromContent(
            _OLD_CONTENT, statement="IS2", scope="consolidated", period="2015Q4", code="005930", rcept="R0"
        )
    )
    assert all(r["acode"] is None for r in rows)  # 태그 없음
    byYear = {r["ctxYear"]: r["valueRaw"] for r in rows if r["label"] == "수익(매출액)"}
    assert byYear == {2015: "200,653,482", 2014: "206,205,987", 2013: "228,692,667"}  # 당기/전기/전전기
    assert all(r["ctxMode"] == "Y" and r["ctxFlow"] == "d" for r in rows)  # 사업보고서 연간, IS=흐름
    # 헤더 행(제 47 기)은 데이터 아님 → 제외
    assert "제 47 기" not in {r["label"] for r in rows}


def test_malformed_content_logs_source_provenance(caplog) -> None:
    """recover 파싱도 조용히 삼키지 않고 종목·기간·statement·접수번호를 남긴다."""
    from dartlab.providers.dart.panel.build.cell import cellsFromContent

    list(
        cellsFromContent(
            "<TABLE><TR><TD>",
            statement="IS2",
            scope="consolidated",
            period="2025Q1",
            code="005930",
            rcept="R-BAD",
        )
    )

    assert "panel cell XML recovered" in caplog.text
    assert "code=005930 period=2025Q1 statement=IS2 rcept=R-BAD" in caplog.text


# 주석 옛표 — 총계행이 rowspan 으로 `합계|라벨|값` 3+셀 병합(naive 5표파서면 라벨=합계·값 한칸밀림 phantom)
_NOTE_MERGED_CONTENT = """<TABLE><TR>
  <TD><P>원재료 등의 사용액</P></TD>
  <TD ALIGN="RIGHT"><P>1,000</P></TD>
  <TD ALIGN="RIGHT"><P>900</P></TD></TR><TR>
  <TD><P>합계</P></TD>
  <TD><P>매출원가와 판매관리비</P></TD>
  <TD ALIGN="RIGHT"><P>5,000</P></TD>
  <TD ALIGN="RIGHT"><P>4,500</P></TD>
</TR></TABLE>"""


def test_parse_old_note_table_merged_row_guard() -> None:
    """주석 옛표 병합행 가드 — `합계|라벨|값` 에서 라벨=중간셀, 값=당기(우측정렬). ctxYear phantom 차단."""
    from dartlab.providers.dart.panel.build.cell import _parseFragment, _parseOldNoteTable

    root = _parseFragment(_NOTE_MERGED_CONTENT)
    rows = list(
        _parseOldNoteTable(
            root, statement="NT_D834300", scope="consolidated", period="2024Q4", code="000270", rcept="R0"
        )
    )
    # 일반 행: 원재료 당기(2024)/전기(2023)
    raw = {r["ctxYear"]: r["valueRaw"] for r in rows if r["label"].replace(" ", "") == "원재료등의사용액"}
    assert raw == {2024: "1,000", 2023: "900"}
    # 병합 총계행: 라벨=중간셀(합계 아님), 값 당기=2024 (naive 면 2023 phantom)
    tot = [r for r in rows if r["valueRaw"] == "5,000"]
    assert len(tot) == 1 and tot[0]["ctxYear"] == 2024
    assert "합계" not in tot[0]["label"] and tot[0]["acode"] is None
    assert tot[0]["axisPath"] == "ConsolidatedMember" and tot[0]["ctxMode"] == "Y"
