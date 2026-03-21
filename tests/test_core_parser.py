"""core.tableParser 순수 함수 테스트 (데이터 의존 없음)."""

import pytest

pytestmark = pytest.mark.unit

from dartlab.core.tableParser import detectUnit, parseAmount, parseNotesTable


class TestParseAmount:
    def test_positive(self):
        assert parseAmount("1,234,567") == 1234567.0

    def test_negative_paren(self):
        assert parseAmount("(1,234)") == -1234.0

    def test_dash(self):
        assert parseAmount("-") is None

    def test_empty(self):
        assert parseAmount("") is None

    def test_decimal(self):
        assert parseAmount("12.34") == 12.34

    def test_negative_sign(self):
        # parseAmount는 음수 부호 "-"를 별도 처리하지 않음 (괄호만 음수)
        v = parseAmount("-5,000")
        assert v is not None
        assert v == 5000.0


class TestParseNotesTable:
    def test_pattern_d_single_point(self):
        """기간 마커 없는 단일 시점 테이블 (Pattern D)."""
        section = (
            "| 구분 | 금액 | 비고 |\n"
            "| --- | --- | --- |\n"
            "| 대출약정 | 1,000,000 | 한국산업은행 |\n"
            "| 당좌차월 | 500,000 | 국민은행 |\n"
        )
        result = parseNotesTable(section)
        assert result is not None
        assert result[0]["pattern"] == "D"
        assert result[0]["period"] == "현재"
        assert len(result[0]["items"]) == 2

    def test_pattern_c_with_period(self):
        """당기/전기 열이 있는 테이블 (Pattern C)."""
        section = (
            "| 구분 | 당기말 | 전기말 |\n"
            "| --- | --- | --- |\n"
            "| 원재료 | 100,000 | 90,000 |\n"
            "| 제품 | 200,000 | 180,000 |\n"
        )
        result = parseNotesTable(section)
        assert result is not None
        assert result[0]["pattern"] == "C"

    def test_no_table_returns_none(self):
        section = "이 섹션에는 테이블이 없습니다.\n단순 텍스트만 있습니다."
        assert parseNotesTable(section) is None


class TestDetectUnit:
    def test_million(self):
        assert detectUnit("(단위: 백만원)") == 1.0

    def test_thousand(self):
        assert detectUnit("(단위: 천원)") == 0.001

    def test_won(self):
        assert detectUnit("(단위 : 원)") == 0.000001

    def test_default(self):
        assert detectUnit("테이블 내용만 있음") == 1.0
