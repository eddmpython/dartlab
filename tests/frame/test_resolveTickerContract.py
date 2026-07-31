"""frame 자연어 종목 해소의 ticker 검증·공백 표기 계약 회귀.

대문자 토큰을 검증 없이 ticker 로 주장하지 않는 것, 그리고 사용자가 공백을 넣어 친
상장명("SK 하이닉스")이 첫 단어("SK")로 잘려 다른 회사가 되지 않는 것을 고정한다.
"""

from __future__ import annotations

import pytest

from dartlab.frame.resolve import resolveStockCodeFromText

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    "text",
    ["ROE 계산법 알려줘", "DCF 설명해줘", "IFRS 기준이 뭐야", "PER 이 뭔가요", "EBIT 정의"],
)
def testFinanceAcronymIsNotClaimedAsTicker(text: str) -> None:
    """실재하지 않는 ticker 인 재무 약어는 회사로 확정되지 않는다 (결함 회귀)."""
    code, remaining = resolveStockCodeFromText(text)
    assert code is None
    assert remaining == text


@pytest.mark.parametrize(
    ("text", "expected", "remaining"),
    [
        ("SK 하이닉스 실적", "000660", "실적"),
        ("LG 화학 주가", "051910", "주가"),
    ],
)
def testSpacedListedNameResolvesToWholeCompany(text: str, expected: str, remaining: str) -> None:
    """공백을 넣어 친 상장명은 첫 단어가 아니라 회사 전체로 해소된다 (결함 회귀)."""
    code, rest = resolveStockCodeFromText(text)
    assert code == expected
    assert rest == remaining


def testStockCodePathUnchanged() -> None:
    """6자리 종목코드 경로는 그대로다 (회귀 가드)."""
    assert resolveStockCodeFromText("005930 매출 어때") == ("005930", "매출 어때")


def testKoreanNamePathUnchanged() -> None:
    """한글 상장명 경로는 그대로다 (회귀 가드)."""
    assert resolveStockCodeFromText("삼성전자 매출 어때") == ("005930", "매출 어때")


def testRealUsTickerStillResolves() -> None:
    """실재하는 US ticker 는 계속 해소된다 (검증 게이트가 정상 경로를 막지 않는다)."""
    code, remaining = resolveStockCodeFromText("AAPL 매출 어때")
    assert code == "AAPL"
    assert remaining == "매출 어때"
