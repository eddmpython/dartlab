"""eventDisclosure — KRX 수시공시 본문 파서 회귀 가드.

전수 실측(7,913 공시) 에서 발견한 병합-셀 concatenation 오파싱(b2b 3e14) + 값-정합 가드 박제.
순수 로직 (HTML string in → dict out), 데이터 로드 없음.
"""

from __future__ import annotations

import pytest

from dartlab.providers.dart.eventDisclosure import (
    classifyEarningsFlash,
    classifyEventReport,
    expectedFields,
    parseEarningsFlash,
    parseEventDisclosure,
)
from dartlab.providers.dart.parse.htmlTableParser import flattenTableCells, parseHtmlTables

pytestmark = [pytest.mark.unit]

# 실 잠정실적 본문 표 구조 축약 (tests/_attempts/earningsFlashWatch/diag.py 실측 기반).
_FLASH_OPERATING = (
    "<table><tr><td>안내</td></tr></table>"
    "<table>"
    "<tr><td>구분</td><td>당기실적</td><td>전기실적</td><td>전기대비</td><td>전년동기실적</td><td>전년동기대비</td></tr>"
    "<tr><td>매출액</td><td>당해실적</td><td>50,902</td><td>83,014</td><td>-38.7</td><td>-</td>"
    "<td>147,392</td><td>-65.5</td><td>-</td></tr>"
    "<tr><td>누계실적</td><td>50,902</td><td>-</td><td>-</td><td>-</td><td>147,392</td><td>-65.5</td><td>-</td></tr>"
    "<tr><td>영업이익</td><td>당해실적</td><td>8,456</td><td>1</td><td>2</td><td>-</td><td>3</td><td>-87.9</td><td>-</td></tr>"
    "<tr><td>단위 : 백만원, %</td></tr>"
    "</table>"
)
# 손익구조 변동: 영업손실(음수) 포함, 단위 천원.
_FLASH_STRUCT = (
    "<table>"
    "<tr><td>3. 매출액 또는 손익구조 변동내용(단위:천원)</td><td>당해사업연도</td><td>직전사업연도</td>"
    "<td>증감금액</td><td>증감비율(%)</td><td>흑자적자전환여부</td></tr>"
    "<tr><td>- 매출액</td><td>29,754,399</td><td>29,397,883</td><td>356,516</td><td>1.2</td><td>-</td></tr>"
    "<tr><td>- 영업이익</td><td>-4,131,994</td><td>-3,076,405</td><td>-1,055,589</td><td>-34.3</td><td>-</td></tr>"
    "</table>"
)


def test_flatten_multi_table():
    html = "<table><tr><td>a</td><td>1</td></tr></table><table><tr><td>b</td><td>2</td></tr></table>"
    assert flattenTableCells(html) == ["a", "1", "b", "2"]


def test_parse_clean_contract():
    # 현대건설 양식 — 라벨 다음 단일 숫자 셀
    html = (
        "<table>"
        "<tr><td>계약금액 총액(원)</td><td>853,142,656,380</td></tr>"
        "<tr><td>최근 매출액(원)</td><td>31,062,912,168,499</td></tr>"
        "<tr><td>매출액 대비(%)</td><td>2.7</td></tr>"
        "<tr><td>3. 계약상대</td><td>범천4구역 주택재개발정비사업조합</td></tr>"
        "<tr><td>7. 계약(수주)일자</td><td>2026-06-22</td></tr>"
        "</table>"
    )
    row = parseEventDisclosure(html)
    assert row["contractAmount"] == 853142656380.0
    assert row["recentRevenue"] == 31062912168499.0
    assert row["revenueRatio"] == 2.7
    assert "범천4구역" in row["counterparty"]
    assert row["orderDate"] == "2026-06-22"


def test_merged_cell_not_astronomical():
    # 일부 양식의 '계약내역' 병합 셀 — parseAmount concatenation garbage(천문학적) 차단.
    # 병합 셀 다음에 깨끗한 '계약금액 총액(원)' 행이 따라온다 → 그 값을 채택.
    html = (
        "<table>"
        "<tr><td>2. 계약내역 - 확정 계약금액 - 계약금액 총액(원) - 매출액 대비(%)</td>"
        "<td>- 48,427,000,000 - 48,427,000,000 - 14.34</td></tr>"
        "<tr><td>계약금액 총액(원)</td><td>65,589,000,000</td></tr>"
        "<tr><td>매출액 대비(%)</td><td>19.43</td></tr>"
        "</table>"
    )
    row = parseEventDisclosure(html)
    # 천문학적 concatenation(4.8e24) 이 아니라 깨끗한 총액
    assert row["contractAmount"] == 65589000000.0
    assert row["contractAmount"] < 1e15


def test_value_sanity_guard():
    # 계약금액/최근매출*100 이 신고 매출대비%와 크게 어긋나면 오파싱 → contractAmount None.
    html = (
        "<table>"
        "<tr><td>계약금액 총액(원)</td><td>100</td></tr>"
        "<tr><td>최근 매출액(원)</td><td>100</td></tr>"
        "<tr><td>매출액 대비(%)</td><td>2.7</td></tr>"
        "</table>"
    )
    row = parseEventDisclosure(html)  # implied 100% vs 신고 2.7% → 불일치
    assert row["contractAmount"] is None
    assert row.get("amountSuspect") is True


def test_value_sanity_passes_consistent():
    html = (
        "<table>"
        "<tr><td>계약금액 총액(원)</td><td>270</td></tr>"
        "<tr><td>최근 매출액(원)</td><td>10000</td></tr>"
        "<tr><td>매출액 대비(%)</td><td>2.7</td></tr>"
        "</table>"
    )
    row = parseEventDisclosure(html)  # implied 2.7% == 신고 2.7%
    assert row["contractAmount"] == 270.0
    assert row.get("amountSuspect") is None


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("단일판매ㆍ공급계약체결", "contract"),
        ("[기재정정]단일판매ㆍ공급계약체결", "amend"),
        ("단일판매ㆍ공급계약해지", "cancel"),
        ("연결재무제표기준영업(잠정)실적", "other"),
    ],
)
def test_classify_report(name, expected):
    assert classifyEventReport(name) == expected


def test_expected_fields():
    fields = expectedFields("supplyContract")
    assert "contractAmount" in fields
    assert "recentRevenue" in fields
    assert "revenueRatio" in fields


# ── 잠정실적 파서 ──────────────────────────────────────────────────
def test_parse_html_tables_multi():
    ts = parseHtmlTables("<table><tr><td>a</td></tr></table><table><tr><td>b</td></tr></table>")
    assert len(ts) == 2
    assert ts[0].rows[0].cells[0].text == "a"
    assert ts[1].rows[0].cells[0].text == "b"


@pytest.mark.parametrize(
    ("name", "isFlash", "typ", "basis"),
    [
        ("연결재무제표기준영업(잠정)실적(공정공시)", True, "영업잠정실적", "연결"),
        ("영업(잠정)실적(공정공시)", True, "영업잠정실적", "별도"),
        ("매출액또는손익구조30%(대규모법인은15%)이상변경", True, "손익구조변동", "별도"),
        ("영업(잠정)실적등에대한전망(공정공시)", False, None, None),
        ("결산실적공시예고", False, None, None),
        ("단일판매ㆍ공급계약체결", False, None, None),
    ],
)
def test_classify_earnings_flash(name, isFlash, typ, basis):
    c = classifyEarningsFlash(name)
    assert c["isFlash"] is isFlash
    assert c["type"] == typ
    assert c["basis"] == basis


def test_parse_earnings_flash_operating():
    r = parseEarningsFlash(_FLASH_OPERATING, "연결재무제표기준영업(잠정)실적(공정공시)")
    assert r["type"] == "영업잠정실적" and r["basis"] == "연결"
    assert r["unit"] == "백만원" and r["unitWon"] == 1e6
    # current=당기(idx2), yoyPct=전년동기대비(idx7). 누계실적 행은 스킵.
    assert r["accounts"]["revenue"] == {"current": 50902.0, "yoyPct": -65.5}
    assert r["accounts"]["operatingProfit"] == {"current": 8456.0, "yoyPct": -87.9}


def test_parse_earnings_flash_struct_preserves_negative():
    """손익구조 변동: 영업손실(음수) 부호 보존. 손실을 이익으로 뒤집지 않는다."""
    r = parseEarningsFlash(_FLASH_STRUCT, "매출액또는손익구조30%(대규모법인은15%)이상변경")
    assert r["type"] == "손익구조변동" and r["unit"] == "천원" and r["unitWon"] == 1e3
    assert r["accounts"]["revenue"] == {"current": 29754399.0, "yoyPct": 1.2}
    op = r["accounts"]["operatingProfit"]
    assert op["current"] == -4131994.0 and op["current"] < 0  # 영업손실
    assert op["yoyPct"] == -34.3


def test_parse_earnings_flash_dash_only_skips():
    """값을 대시로만 낸 공시. 조용한 0 대신 계정 부재(폴백 신호)."""
    html = (
        "<table>"
        "<tr><td>매출액</td><td>당해실적</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td></tr>"
        "<tr><td>영업이익</td><td>당해실적</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td></tr>"
        "<tr><td>단위 : 억원</td></tr>"
        "</table>"
    )
    r = parseEarningsFlash(html, "영업(잠정)실적(공정공시)")
    assert r["accounts"] == {}


def test_parse_earnings_flash_no_table():
    r = parseEarningsFlash("본문 없음", "영업(잠정)실적(공정공시)")
    assert r["accounts"] == {} and r["type"] == "영업잠정실적"
