"""서사 문장이 자기 입력과 어긋나던 것에 대한 회귀.

세 자리에서 문장이 데이터를 뒤집었다.

첫째, 추세 판정이 등호를 포함하고 개선을 먼저 확인해서 값이 하나도 안 움직인 계열이
"개선" 으로 나왔다. 부채비율 100% 가 네 기 내내 그대로인 회사가 "부채가 지속적으로
증가하는 추세" 였고, 영업이익률은 한 문장 안에서 "(보합)" 이라 적고 곧바로 "4기 연속
개선 중" 이라 적었다.

둘째, 영업현금흐름을 순이익으로 나눈 비율만 보고 판정해서, 순손실을 낸 회사가 현금을
잘 벌어도 "영업현금흐름이 적자다" 로 읽혔다. 진짜 영업적자와 구분도 되지 않았다.

셋째, 데이터가 없을 때 통과를 주는 검증기가 있었다. 지표를 하나도 못 구한 회사가
Damodaran 3-test 한 칸을 공짜로 가져갔고, 스무 검사가 전부 예외로 죽어도 보고서에는
"20개 경제학 불변량 전부 통과" 가 찍혔다.
"""

from __future__ import annotations

from dartlab.story.narrate import _detectTrend, narrateCashQuality, narrateLeverage, narrateMargin
from dartlab.story.validators.validators import _INVARIANTS, _commonSenseTest


def _flatHistory(periods: int = 4) -> dict:
    return {"history": [{"debtRatio": 100.0, "operatingMargin": 12.0} for _ in range(periods)]}


def testUnchangedSeriesIsNotATrend() -> None:
    """결함의 뿌리다. 움직이지 않은 것은 개선도 악화도 아니다."""

    assert _detectTrend([100.0, 100.0, 100.0, 100.0]) == "flat"


def testDirectionalTrendsStillWork() -> None:
    """평탄 판정을 넣느라 진짜 추세를 놓치면 안 된다. 최신이 앞이다."""

    assert _detectTrend([15.0, 12.0, 10.0, 8.0]) == "improving"
    assert _detectTrend([8.0, 10.0, 12.0, 15.0]) == "declining"
    assert _detectTrend([10.0, 14.0, 9.0, 12.0]) == "mixed"


def testFlatDebtIsNotCalledRising() -> None:
    """부채가 그대로인데 늘고 있다고 적으면 안 된다."""

    text = narrateLeverage(_flatHistory())

    assert text is not None
    assert "증가하는 추세" not in text
    assert "줄이고 있다" not in text


def testFlatMarginDoesNotContradictItself() -> None:
    """같은 문장이 보합이라 적고 개선 중이라 적으면 안 된다."""

    text = narrateMargin(_flatHistory())

    assert text is not None
    assert "연속 개선" not in text
    assert "연속 악화" not in text


def testPositiveCashFlowUnderALossIsNotCalledADeficit() -> None:
    """순손실이라 비율이 음수인 것과 현금이 마른 것은 다른 사건이다."""

    text = narrateCashQuality({"history": [{"ocfToNi": -200.0, "ocf": 2.0e10}]})

    assert text is not None
    assert "영업현금흐름이 적자다" not in text


def testGenuineOperatingDeficitIsStillCalledOut() -> None:
    """진짜 영업적자는 그대로 적자라고 말해야 한다."""

    text = narrateCashQuality({"history": [{"ocfToNi": -200.0, "ocf": -2.0e10}]})

    assert text is not None
    assert "영업현금흐름이 적자다" in text


def testAbsentMetricsDoNotEarnAPass() -> None:
    """검사할 자료가 없는 것은 통과가 아니다."""

    assert _commonSenseTest(None, {}).passed is False
    assert _commonSenseTest(None, {"관계없는키": 1}).passed is False


def testReportCountsOnlyTheChecksThatRan() -> None:
    """스무 개를 등록했다고 스무 개를 검사한 것이 아니다."""

    result = _commonSenseTest(None, {"opm": 12.0, "roe": 15.0})

    assert result.passed is True
    assert f"{len(_INVARIANTS)}개 경제학 불변량 전부 통과" not in result.detail
    assert "미검사" in result.detail


def testDistressCheckStaysOnAtZeroInterestCoverage() -> None:
    """이자를 한 푼도 못 갚는 상태가 이 검사가 잡아야 할 최악이다."""

    result = _commonSenseTest(None, {"debtRatio": 500.0, "interestCoverage": 0.0})

    assert result.passed is False
    assert "재무위기" in result.detail


def testNormalRetailerIsNotFlaggedAsAnInvariantViolation() -> None:
    """마진 3%, ROE 15% 는 분모가 다를 뿐 평범한 회사다."""

    result = _commonSenseTest(None, {"opm": 3.0, "roe": 15.0})

    assert result.passed is True
