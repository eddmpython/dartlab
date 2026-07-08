"""narrativeMetric 서술 지표 추출 결정적 테스트 (수주잔고 amount·가동률 rate·confidence·sanity).

합성 표 XML 로 resolver 를 검증하고, requires_data 로 실 panel E2E(한화오션 수주잔고·삼성 가동률).
"""

from __future__ import annotations

import pytest

from dartlab.providers.dart.panel.build.grid import tableToGrid
from dartlab.providers.dart.panel.narrativeMetric import (
    METRIC_DEFS,
    _resolveAmount,
    _resolveRate,
    metricCatalog,
    readMetric,
)

pytestmark = pytest.mark.unit

_SUJU_XML = (
    "<TABLE><THEAD>"
    '<TR><TH ROWSPAN="2">품목</TH><TH COLSPAN="2">수주총액</TH><TH COLSPAN="2">수주잔고</TH></TR>'
    "<TR><TH>수량</TH><TH>금액</TH><TH>수량</TH><TH>금액</TH></TR></THEAD><TBODY>"
    "<TR><TD>상선</TD><TD>-</TD><TD>28,896,786</TD><TD>-</TD><TD>26,227,035</TD></TR>"
    '<TR><TD COLSPAN="1">합 계</TD><TD>-</TD><TD>38,552,496</TD><TD>-</TD><TD>35,374,442</TD></TR>'
    "</TBODY></TABLE>"
)


def test_resolve_amount_backlog_total_row_high_conf():
    g = tableToGrid(_SUJU_XML)
    res = _resolveAmount(g, _SUJU_XML, METRIC_DEFS["backlog"], 1e6)  # leaf 단위 백만원
    assert res is not None
    assert res["value"] == 35_374_442 * 1e6  # 합계행 수주잔고금액 (수주총액 아님)
    assert res["confidence"] == "high"  # 단위확정 + 합계행


def test_resolve_amount_low_conf_without_unit():
    g = tableToGrid(_SUJU_XML)
    res = _resolveAmount(g, _SUJU_XML, METRIC_DEFS["backlog"], None)  # 단위 모호
    assert res["value"] == 35_374_442 * 1e6  # 기본 백만원, 값은 동일
    assert res["confidence"] == "mid"  # 합계행은 있으나 단위 미확정


def test_resolve_amount_sanity_cut():
    # 값 x scale 이 1000조 초과면 None (단위 오선택 방어)
    g = tableToGrid("<TABLE><TR><TH>수주잔고</TH></TR><TR><TD>합계</TD></TR><TR><TD>50,000,000</TD></TR></TABLE>")
    res = _resolveAmount(g, "", METRIC_DEFS["backlog"], 1e8)  # 5천만 x 억 = 5e15 > 1e15
    assert res is None


def test_resolve_rate_direct():
    g = tableToGrid("<TABLE><TR><TH>구분</TH><TH>가동률</TH></TR><TR><TD>반도체</TD><TD>82.9</TD></TR></TABLE>")
    res = _resolveRate(g)
    assert res["value"] == 82.9 and res["confidence"] == "high" and res["unit"] == "%"


def test_resolve_rate_compute_from_components():
    g = tableToGrid(
        "<TABLE><TR><TH>가동가능시간</TH><TH>실제가동시간</TH></TR><TR><TD>1,000</TD><TD>800</TD></TR></TABLE>"
    )
    res = _resolveRate(g)
    assert res["value"] == 80.0 and res["confidence"] == "mid"


def test_resolve_rate_out_of_range_gap():
    g = tableToGrid("<TABLE><TR><TH>가동률</TH></TR><TR><TD>999</TD></TR></TABLE>")
    assert _resolveRate(g) is None  # 150% 초과 = 정직 gap


def test_readMetric_unknown_raises():
    with pytest.raises(ValueError, match="미등록 metricId"):
        readMetric("005930", "존재하지않는지표")


def test_metricCatalog():
    ids = {m["metricId"] for m in metricCatalog()}
    assert "backlog" in ids and "utilizationRate" in ids


@pytest.mark.requires_data
@pytest.mark.heavy
class TestRealPanel:
    def test_backlog_shipbuilder_high_conf(self):
        r = readMetric("042660", "backlog")  # 한화오션
        assert r is not None
        assert r["confidence"] == "high"
        assert 20e12 < r["value"] < 60e12  # 수주잔고 20~60조 범위 (35.4조)

    def test_utilization_samsung(self):
        r = readMetric("005930", "utilizationRate")  # 삼성전자
        assert r is not None
        assert 50 <= r["value"] <= 120 and r["unit"] == "%"

    def test_service_company_gap(self):
        # 서비스사는 가동률 표 없음 = 정직 gap
        assert readMetric("097520", "utilizationRate") is None
