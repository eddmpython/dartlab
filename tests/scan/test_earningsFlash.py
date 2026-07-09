"""scan("earningsFlash"). 잠정실적 횡단 축 회귀 가드.

라우터 등록·별칭 + _parseRow 추출/원 환산(본문 fetch 는 mock). 라이브 DART 불요.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from dartlab.scan.earningsFlash import _OUTPUT_SCHEMA, _parseRow, scanEarningsFlash
from dartlab.scan.router import _resolveAxis

pytestmark = [pytest.mark.unit]

_FLASH_OPERATING = (
    "<table>"
    "<tr><td>구분</td><td>당기실적</td><td>전기실적</td><td>전기대비</td><td>전년동기실적</td><td>전년동기대비</td></tr>"
    "<tr><td>매출액</td><td>당해실적</td><td>50,902</td><td>83,014</td><td>-38.7</td><td>-</td>"
    "<td>147,392</td><td>-65.5</td><td>-</td></tr>"
    "<tr><td>영업이익</td><td>당해실적</td><td>8,456</td><td>1</td><td>2</td><td>-</td><td>3</td><td>-87.9</td><td>-</td></tr>"
    "<tr><td>단위 : 백만원, %</td></tr>"
    "</table>"
)


def test_axis_registered_and_aliased():
    assert _resolveAxis("earningsFlash") == "earningsFlash"
    assert _resolveAxis("잠정실적") == "earningsFlash"
    assert _resolveAxis("어닝") == "earningsFlash"


def test_output_schema_columns():
    for col in ("revenue", "revenueYoy", "operatingProfit", "netProfit", "type", "basis", "unit", "stockCode"):
        assert col in _OUTPUT_SCHEMA


def test_parse_row_normalizes_to_won():
    meta = {
        "corp_name": "한미반도체",
        "corp_code": "042700",
        "stock_code": "042700",
        "rcept_no": "20260515801516",
        "rcept_dt": "20260515",
        "report_nm": "연결재무제표기준영업(잠정)실적(공정공시)",
        "_type": "영업잠정실적",
        "_basis": "연결",
    }
    with patch("dartlab.gather.dart.allFilingsCollector._collectOneRaw", return_value=(_FLASH_OPERATING, "ok")):
        row = _parseRow(client=None, meta=meta, asOf="20260515")
    assert row["corpName"] == "한미반도체" and row["stockCode"] == "042700"
    assert row["type"] == "영업잠정실적" and row["basis"] == "연결"
    assert row["unit"] == "백만원"
    assert row["revenue"] == 50902.0 * 1e6  # 백만원 원 환산
    assert row["revenueYoy"] == -65.5
    assert row["operatingProfit"] == 8456.0 * 1e6
    assert row["operatingProfitYoy"] == -87.9


def test_parse_row_fetch_fail_meta_only():
    meta = {
        "corp_name": "X",
        "corp_code": "1",
        "stock_code": "005930",
        "rcept_no": "r",
        "rcept_dt": "20260101",
        "report_nm": "영업(잠정)실적(공정공시)",
        "_type": "영업잠정실적",
        "_basis": "별도",
    }
    with patch("dartlab.gather.dart.allFilingsCollector._collectOneRaw", return_value=(None, "error")):
        row = _parseRow(client=None, meta=meta, asOf="20260101")
    assert row["corpName"] == "X" and row["stockCode"] == "005930"
    assert "revenue" not in row  # deep 실패 시 메타만


def test_scan_empty_when_no_flash():
    with patch("dartlab.scan.earningsFlash._discover", return_value=([], "20260101")):
        df = scanEarningsFlash()
    assert df.height == 0
    assert "revenue" in df.columns and "type" in df.columns
