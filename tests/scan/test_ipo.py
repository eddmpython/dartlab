"""scan("ipo") — 신규상장 IPO 횡단 축 회귀 가드.

라우터 등록·별칭 + _parseRow 추출(본문 fetch 는 mock). 라이브 DART 불요(순수 로직).
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from dartlab.scan.ipo import _OUTPUT_SCHEMA, _parseRow, scanIpo
from dartlab.scan.router import _resolveAxis

pytestmark = [pytest.mark.unit]

# 항등식이 닫히는 합성 본문 (offering + 인수인 의견 밸류표)
_FIXTURE = """<DOCUMENT>
<TITLE>1. 공모개요</TITLE>
<P>희망공모가액은 80,000원 ~ 90,000원입니다.</P>
<TABLE><TR><TD>증권의 종류</TD><TD>증권수량</TD><TD>모집(매출)가액</TD><TD>모집(매출)총액</TD></TR>
<TR><TD>보통주</TD><TD>1,000,000</TD><TD>80,000</TD><TD>80,000,000,000</TD></TR></TABLE>
<TABLE><TR><TD>청약기일</TD><TD>납입기일</TD></TR><TR><TD>2026.09.01 ~ 2026.09.02</TD><TD>2026.09.04</TD></TR></TABLE>
<TITLE>IV. 인수인의 의견(분석기관의 평가의견)</TITLE>
<TABLE>
<TR><TD>평가방법</TD><TD>상대가치법</TD></TR>
<TR><TD>평가모형</TD><TD>PER</TD></TR>
<TR><TD>적용근거</TD><TD>①</TD><TD>당기순이익</TD><TD>5,000백만원</TD><TD>참고</TD></TR>
<TR><TD>적용근거</TD><TD>②</TD><TD>유사기업 PER</TD><TD>20배</TD><TD>참고</TD></TR>
<TR><TD>적용근거</TD><TD>③</TD><TD>주식수</TD><TD>1,000,000주</TD><TD>참고</TD></TR>
<TR><TD>적용근거</TD><TD>주당 평가가액</TD><TD>주당 평가가액</TD><TD>100,000원</TD><TD>①x②÷③</TD></TR>
<TR><TD>적용근거</TD><TD>④</TD><TD>할인율</TD><TD>20% ~ 10%</TD><TD>참고</TD></TR>
<TR><TD>적용근거</TD><TD>공모가 산정 결과</TD><TD>공모가 산정 결과</TD><TD>80,000원 ~ 90,000원</TD><TD>참고</TD></TR>
</TABLE>
<TITLE>1. 요약재무정보</TITLE>
<TABLE><TR><TD>구분</TD><TD>2025년</TD></TR>
<TR><TD>자산총계</TD><TD>1,000</TD></TR><TR><TD>부채총계</TD><TD>600</TD></TR><TR><TD>자본총계</TD><TD>400</TD></TR></TABLE>
</DOCUMENT>"""


def test_axis_registered_and_aliased():
    assert _resolveAxis("ipo") == "ipo"
    assert _resolveAxis("신규상장") == "ipo"
    assert _resolveAxis("공모") == "ipo"


def test_output_schema_columns():
    assert "appliedPer" in _OUTPUT_SCHEMA
    assert "priceBandLow" in _OUTPUT_SCHEMA
    assert "chainOk" in _OUTPUT_SCHEMA


def test_parse_row_extracts_key_fields():
    meta = {
        "corp_name": "테스트",
        "corp_code": "00000000",
        "rcept_no": "20260101000001",
        "rcept_dt": "20260101",
        "_isSpac": False,
    }
    with patch("dartlab.gather.dart.allFilingsCollector._collectOneRaw", return_value=(_FIXTURE, "ok")):
        row = _parseRow(client=None, meta=meta, asOf="20260101")
    assert row["corpName"] == "테스트"
    assert row["priceBandLow"] == 80000.0 and row["priceBandHigh"] == 90000.0
    assert row["appliedPer"] == 20.0
    assert row["perShareValue"] == 100000.0
    assert row["shares"] == 1_000_000  # 항등식 복구
    assert row["chainOk"] is True
    assert row["financialsOk"] is True


def test_parse_row_fetch_fail_meta_only():
    meta = {"corp_name": "X", "corp_code": "1", "rcept_no": "r", "rcept_dt": "20260101", "_isSpac": True}
    with patch("dartlab.gather.dart.allFilingsCollector._collectOneRaw", return_value=(None, "error")):
        row = _parseRow(client=None, meta=meta, asOf="20260101")
    assert row["corpName"] == "X" and row["isSpac"] is True
    assert "priceBandLow" not in row  # deep 실패 — 메타만


def test_scan_ipo_empty_when_no_ipo():
    with patch("dartlab.scan.ipo._latestFullProspectuses", return_value=([], "20260101")):
        df = scanIpo()
    assert df.height == 0
    assert "appliedPer" in df.columns
