"""core/market 종목코드 판정 회귀 가드.

KRX 단축코드는 6자리 숫자만이 아니다. 신형 발행분은 영문을 섞는다
(에스엔시스 0008Z0 · 삼성에피스홀딩스 0126Z0 · SK우 03473K).
2026-07 기준 상장 2,873 종목 중 79 종목이 영숫자다.

옛 "알파벳 포함이면 US" 규칙이 이들을 전부 US 로 흘려 보내 공시뷰어가
edgar/panel/{code}.parquet 404 로 죽었다. 본 파일은 그 회귀를 막는다.
"""

from __future__ import annotations

import pytest

from dartlab.core.market import (
    KR_STOCK_CODE_TEXT_RE,
    detectMarket,
    isKrStockCode,
    normalizeKrCode,
    resolveMarket,
)

# 실재 상장 종목 (data/krxList/corpList.parquet 실측)
ALNUM_CODES = ["0008Z0", "0126Z0", "0015N0", "03473K", "00104K", "37550L"]


@pytest.mark.unit
class TestIsKrStockCode:
    """KRX 단축코드 모양 판정."""

    @pytest.mark.parametrize("code", ["005930", "000660", "035720"])
    def test_numeric_codes(self, code: str) -> None:
        assert isKrStockCode(code) is True

    @pytest.mark.parametrize("code", ALNUM_CODES)
    def test_alphanumeric_codes(self, code: str) -> None:
        assert isKrStockCode(code) is True

    def test_lowercase_input_accepted(self) -> None:
        assert isKrStockCode("0008z0") is True

    @pytest.mark.parametrize(
        "value",
        ["AAPL", "GOOGL", "BRK.B", "Z00080", "00593", "0059300", "삼성전자", "", "  "],
    )
    def test_rejects_non_codes(self, value: str) -> None:
        assert isKrStockCode(value) is False

    def test_first_char_must_be_digit(self) -> None:
        # US 티커는 숫자로 시작하지 않는다. 그래서 이 규칙이 티커와 충돌하지 않는다.
        assert isKrStockCode("A0008Z") is False


@pytest.mark.unit
class TestNormalizeKrCode:
    """표기 정규화."""

    def test_strips_and_uppercases(self) -> None:
        assert normalizeKrCode(" 0008z0 ") == "0008Z0"

    def test_numeric_code_unchanged(self) -> None:
        assert normalizeKrCode("005930") == "005930"

    def test_empty_input(self) -> None:
        assert normalizeKrCode("") == ""


@pytest.mark.unit
class TestDetectMarketAlphanumeric:
    """영숫자 코드 시장 분기 회귀 가드."""

    @pytest.mark.parametrize("code", ALNUM_CODES)
    def test_alphanumeric_code_is_kr(self, code: str) -> None:
        assert detectMarket(code) == "KR"

    @pytest.mark.parametrize("code", ALNUM_CODES)
    def test_resolve_with_kr_default_stays_kr(self, code: str) -> None:
        assert resolveMarket(code, "KR") == "KR"

    def test_explicit_us_override_still_wins(self) -> None:
        assert resolveMarket("0008Z0", "US") == "US"

    @pytest.mark.parametrize("code", ["005930", "000660"])
    def test_numeric_codes_unchanged(self, code: str) -> None:
        assert detectMarket(code) == "KR"

    @pytest.mark.parametrize("ticker", ["AAPL", "MSFT", "GOOGL"])
    def test_us_tickers_unchanged(self, ticker: str) -> None:
        assert detectMarket(ticker) == "US"

    def test_korean_company_name_unchanged(self) -> None:
        assert detectMarket("삼성전자") == "KR"


@pytest.mark.unit
class TestStockCodeTextPattern:
    """자유 텍스트 추출 패턴. 기간 문자열 오탐 배제가 핵심."""

    def test_extracts_alphanumeric_code(self) -> None:
        assert KR_STOCK_CODE_TEXT_RE.findall("0008Z0 분석해줘") == ["0008Z0"]

    def test_extracts_numeric_code(self) -> None:
        assert KR_STOCK_CODE_TEXT_RE.findall("삼성전자 005930 매출") == ["005930"]

    def test_extracts_multiple(self) -> None:
        assert KR_STOCK_CODE_TEXT_RE.findall("0008Z0와 005930 비교") == ["0008Z0", "005930"]

    @pytest.mark.parametrize("text", ["2026Q1 실적은?", "2025Q4 대비 2026Q1"])
    def test_period_string_is_not_a_code(self, text: str) -> None:
        # "2026Q1" 은 6자 영숫자라 순진한 패턴이면 종목코드로 잡힌다.
        assert KR_STOCK_CODE_TEXT_RE.findall(text) == []

    def test_date_is_not_a_code(self) -> None:
        assert KR_STOCK_CODE_TEXT_RE.findall("20260101 공시") == []

    def test_substring_of_longer_token_ignored(self) -> None:
        assert KR_STOCK_CODE_TEXT_RE.findall("abc0008Z0def") == []
