"""salesByProduct 빌더 정규화 단위 테스트 + 실데이터 스모크.

합성 격자로 leaf 합산·총계 배제·판별자·헤더 감지를 검증하고 (데이터 불필요),
requires_data 로 삼성·조선 실 panel 추출을 확인한다.
"""

from __future__ import annotations

import pytest

from dartlab.scan.builders.kr.salesByProduct import (
    _concentration,
    _looksLikeSalesTable,
    _num,
    _pickSalesTable,
    _scanGrid,
    extractSalesByProduct,
)


class TestNum:
    def test_comma_and_triangle_negative(self):
        assert _num("1,290,601") == 1290601.0
        assert _num("△92,697") == -92697.0
        assert _num("(2,573)") == -2573.0

    def test_blank_and_dash(self):
        assert _num("-") is None
        assert _num("") is None
        assert _num("   ") is None


class TestScanGrid:
    def test_year_header_not_treated_as_data(self):
        # 연도 헤더("2024년")가 _num 으로 2024 로 파싱돼 데이터 행이 되면 안 된다.
        grid = [
            ["사업부문", "매출유형", "품목", "2024년", "2023년"],
            ["반도체부문", "제품", "메모리", "1000", "900"],
        ]
        scanned = _scanGrid(grid)
        assert scanned is not None
        headerText, valueCols, dataRows = scanned
        assert valueCols == [3, 4]
        # 헤더 행은 dataRows 에서 제외 (단일 데이터 행만).
        assert len(dataRows) == 1
        assert dataRows[0][0] == "반도체부문"

    def test_no_period_header_returns_none(self):
        grid = [["가", "나"], ["1", "2"]]
        assert _scanGrid(grid) is None


class TestLooksLikeSalesTable:
    def test_requires_segment_and_sales_type(self):
        sales = [
            ["사업부문", "매출유형", "품목", "2024년", "2023년"],
            ["반도체부문", "제품", "메모리", "1000", "900"],
        ]
        assert _looksLikeSalesTable(sales) is True

    def test_volume_table_rejected(self):
        # 현대차형 판매대수 표: 부문 있으나 매출유형 없음 -> 배제.
        volume = [
            ["사업부문", "구분", "구분", "2026년", "2025년"],
            ["차량부문", "국내완성차", "승용", "56436", "56170"],
        ]
        assert _looksLikeSalesTable(volume) is False


class TestConcentration:
    def test_leaf_aggregation_excludes_subtotal_and_negative(self):
        # DS 부문(반도체+DP) leaf 합산 = 부문 계와 일치, 부문 계·합계 행 배제, 음수 기타 제외.
        grid = [
            ["부문", "부문", "매출유형", "품목", "제55기", "제54기"],
            ["CE부문", "CE부문", "제품", "TV 등", "300000", "280000"],
            ["DS부문", "반도체", "제품", "DRAM 등", "417463", "400000"],
            ["DS부문", "DP", "제품", "OLED 등", "137909", "130000"],
            ["DS부문", "부문 계", "부문 계", "부문 계", "555372", "530000"],
            ["기타", "기타", "-", "-", "△92697", "△80000"],
            ["합계", "합계", "합계", "합계", "762741", "730000"],
        ]
        conc = _concentration(grid)
        assert conc is not None
        # 양수 부문: CE(300000) + DS(555372=417463+137909). 기타(음수)·합계·부문 계 제외.
        assert conc["nSegments"] == 2
        assert conc["topSegment"] == "DS부문"
        total = 300000 + 555372
        assert conc["topSharePct"] == round(555372 / total * 100, 1)

    def test_single_segment(self):
        grid = [
            ["사업부문", "매출유형", "품목", "2024년", "2023년"],
            ["반도체부문", "제품", "메모리", "1000", "900"],
            ["합계", "합계", "합계", "1000", "900"],
        ]
        conc = _concentration(grid)
        assert conc is not None
        assert conc["nSegments"] == 1
        assert conc["topSharePct"] == 100.0
        assert conc["hhi"] == 1.0
        assert conc["grade"] == "단일사업"

    def test_export_domestic_subtotal_excluded(self):
        # 조선형: 수출/국내 leaf 합산, 합계 행 배제 (이중계상 방지).
        grid = [
            ["사업부문", "매출유형", "품목", "품목", "2021년", "2020년"],
            ["조선", "제품", "선박", "수출", "5000", "9000"],
            ["조선", "제품", "선박", "국내", "500", "800"],
            ["조선", "제품", "선박", "합계", "5500", "9800"],
            ["기계", "제품", "엔진", "수출", "300", "600"],
            ["기계", "제품", "엔진", "국내", "200", "400"],
            ["기계", "제품", "엔진", "합계", "500", "1000"],
        ]
        conc = _concentration(grid)
        assert conc is not None
        assert conc["nSegments"] == 2
        # 조선 = 5000+500 = 5500, 기계 = 300+200 = 500 (합계 행 미포함)
        assert conc["topSegment"] == "조선"
        assert conc["topSharePct"] == round(5500 / 6000 * 100, 1)


class TestPickSalesTable:
    def test_prefers_sales_over_volume(self):
        volume = [
            ["사업부문", "구분", "구분", "2024년", "2023년"],
            ["차량부문", "국내", "승용", "99999", "99999"],
        ]
        sales = [
            ["사업부문", "매출유형", "품목", "2024년", "2023년"],
            ["A부문", "제품", "x", "100", "90"],
            ["B부문", "제품", "y", "50", "40"],
        ]
        picked = _pickSalesTable([volume, sales])
        assert picked is sales


@pytest.mark.requires_data
class TestRealPanel:
    def test_samsung_segment_mix(self):
        m = extractSalesByProduct("005930")
        assert m is not None
        assert m["nSegments"] >= 3
        assert "DS" in m["segments"] or "DX" in m["segments"]
        assert 0 < m["topSharePct"] <= 100

    def test_shipbuilder_segment_mix(self):
        m = extractSalesByProduct("009540")
        assert m is not None
        assert m["topSegment"].startswith("조선") or "조선" in m["segments"]
