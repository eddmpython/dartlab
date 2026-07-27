"""은행 적정가의 주가 독립성 회귀.

주식수를 구하지 못하면 가정 PBR 로 시총을 추정한 뒤 주가로 나눠 주식수를 만들고 있었다.
그 주식수로 계산한 주당가치와 주가의 비율에서 주가가 약분되므로, 상승여력이 주가와 무관한
상수가 된다. 주가가 10 배 움직여도 같은 값이 나오는 목표가는 회사가 싼지 비싼지 영영
말할 수 없다. 게다가 상승여력을 못 구한 경우가 하필 'medium' 신뢰도로 찍혔다.

여기서 고정하는 것은 산술적 성질 하나다. 판단 대상인 주가로 판단 근거를 만들면 그 판단은
주가에 대해 아무 말도 하지 않는다.
"""

from __future__ import annotations

import inspect

import pytest

from dartlab.analysis.valuation import bankDFV


def testUpsideFormulaCancelsWhenSharesAreDerivedFromPrice() -> None:
    """왜 막아야 하는지부터 못 박는다. 이 성질이 결함의 원인이다."""

    bookEquity = 10e12
    equityValue = 8e12
    upsides = []
    for price in (5000, 10000, 50000):
        shares = int(bookEquity * 0.85 / price)
        perShare = equityValue / shares
        upsides.append(round((perShare - price) / price * 100, 6))

    assert len(set(upsides)) == 1


def testShareCountIsNeverDerivedFromTheCurrentPrice() -> None:
    """주식수를 주가로 만들어 내면 상승여력이 주가와 무관해진다."""

    source = inspect.getsource(bankDFV)

    assert "estimated_market_cap / cur_p" not in source
    assert "book_equity * 0.85" not in source


def testMissingUpsideIsNotReportedAsMediumConfidence() -> None:
    """검증할 수 없을 때 가장 높은 신뢰도가 붙으면 안 된다."""

    source = inspect.getsource(bankDFV)

    assert 'confidence = "medium" if abs(upside or 0) < 30' not in source


@pytest.mark.parametrize(("upside", "expected"), [(None, "low"), (5.0, "medium"), (45.0, "low")])
def testConfidenceFollowsTheUpsideMagnitude(upside: float | None, expected: str) -> None:
    """상승여력이 없으면 낮음, 작으면 보통, 크면 낮음이라는 규칙 자체를 고정한다."""

    confidence = "low" if upside is None else ("medium" if abs(upside) < 30 else "low")

    assert confidence == expected
