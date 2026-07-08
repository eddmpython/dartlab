"""tableToGrid 범용 격자 primitive 결정적 테스트 (colspan/rowspan 확장·합성헤더).

합성 XML 로 검증 (네트워크·데이터 불요).
"""

from __future__ import annotations

import pytest

from dartlab.providers.dart.panel.build.grid import normLabel, tableToGrid

pytestmark = pytest.mark.unit


def test_simple_single_col():
    g = tableToGrid("<TABLE><TR><TH>수주잔고</TH></TR><TR><TD>100</TD></TR></TABLE>")
    assert g["ncol"] == 1 and g["nrow"] == 2
    assert g["colLabels"] == ["수주잔고"]
    assert g["dense"][1][0] == ("100", False)


def test_colspan_multirow_header_composite():
    xml = (
        "<TABLE><THEAD>"
        '<TR><TH ROWSPAN="2">품목</TH><TH COLSPAN="2">수주잔고</TH></TR>'
        "<TR><TH>수량</TH><TH>금액</TH></TR>"
        "</THEAD><TBODY>"
        "<TR><TD>상선</TD><TD>5</TD><TD>26227035</TD></TR>"
        "</TBODY></TABLE>"
    )
    g = tableToGrid(xml)
    assert g["ncol"] == 3
    # 멀티행 헤더 합성: 품목 / 수주잔고+수량 / 수주잔고+금액
    assert g["colLabels"] == ["품목", "수주잔고수량", "수주잔고금액"]
    # rowspan 으로 품목이 2행 차지 → 데이터행은 3번째
    assert g["dense"][2][2] == ("26227035", False)


def test_total_row_alignment_colspan():
    # 합계행이 앞 컬럼을 병합해 셀 수가 달라도 dense 격자에서 정렬 (한화오션 실제 패턴)
    xml = (
        "<TABLE><THEAD>"
        '<TR><TH ROWSPAN="2">품목</TH><TH ROWSPAN="2">수주일자</TH><TH COLSPAN="2">수주잔고</TH></TR>'
        "<TR><TH>수량</TH><TH>금액</TH></TR></THEAD><TBODY>"
        "<TR><TD>상선</TD><TD>2026</TD><TD>-</TD><TD>26227035</TD></TR>"
        '<TR><TD COLSPAN="2">합 계</TD><TD>-</TD><TD>35374442</TD></TR>'
        "</TBODY></TABLE>"
    )
    g = tableToGrid(xml)
    assert g["colLabels"][3] == "수주잔고금액"
    # 합계행: COLSPAN=2 로 품목/수주일자 병합 → 금액은 여전히 col3
    assert g["dense"][3][3] == ("35374442", False)


def test_empty_and_no_table():
    assert tableToGrid("") is None
    assert tableToGrid("텍스트만 있음") is None
    assert tableToGrid("<TABLE></TABLE>") is None


def test_norm_label():
    assert normLabel("수주잔고 (*1)") == "수주잔고1"
    assert normLabel("  가동률(%) ") == "가동률%"
